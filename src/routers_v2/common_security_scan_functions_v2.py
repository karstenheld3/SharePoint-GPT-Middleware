# Common functions for SharePoint security scanning
# Implements permission scanning per _V2_SPEC_SITES_SECURITY_SCAN.md [SITE-SP03]
# V2 version using MiddlewareLogger and Office365-REST-Python-Client

import asyncio, datetime, json, os, re, tempfile
from typing import Any, AsyncGenerator, Optional
from azure.identity import CertificateCredential
from msgraph import GraphServiceClient
from office365.sharepoint.client_context import ClientContext
from hardcoded_config import CRAWLER_HARDCODED_CONFIG
from routers_v2.common_logging_functions_v2 import MiddlewareLogger, UNKNOWN
from routers_v2.common_sharepoint_functions_v2 import connect_to_site_using_client_id_and_certificate

# ----------------------------------------- START: Constants ------------------------------------------------------------------

MAX_NESTING_LEVEL = 5
BATCH_SIZE = 5000
PROGRESS_INTERVAL_SECONDS = 5

# Built-in list templates to include (Generic List, Document Library, Site Pages)
INCLUDED_TEMPLATES = [100, 101, 119]

# CSV Column Definitions (EXACT order from SPEC Section 14 - must match PowerShell scanner)
CSV_COLUMNS_SITE_CONTENTS = ["Id", "Type", "Title", "Url"]
CSV_COLUMNS_SITE_GROUPS = ["Id", "Role", "Title", "PermissionLevel", "Owner"]
CSV_COLUMNS_SITE_USERS = ["Id", "LoginName", "DisplayName", "Email", "PermissionLevel", "ViaGroup", "ViaGroupId", "ViaGroupType", "AssignmentType", "NestingLevel", "ParentGroup"]
CSV_COLUMNS_INDIVIDUAL_ITEMS = ["Id", "Type", "Title", "Url"]
CSV_COLUMNS_INDIVIDUAL_ACCESS = ["Id", "Type", "Url", "LoginName", "DisplayName", "Email", "PermissionLevel", "SharedDateTime", "SharedByDisplayName", "SharedByLoginName", "ViaGroup", "ViaGroupId", "ViaGroupType", "AssignmentType", "NestingLevel", "ParentGroup"]

# ----------------------------------------- END: Constants --------------------------------------------------------------------


# ----------------------------------------- START: CSV Functions --------------------------------------------------------------

def csv_escape(value) -> str:
  """Escape value for CSV output, matching PowerShell scanner format (SPEC Section 9)."""
  if value is None: return ''
  value = str(value)
  if not value: return '""'
  # Match SPEC regex exactly: formula chars, date/number patterns, or special chars
  if re.match(r'^([+\-=\/]*[\.\d\s\/\:]*|.*[\,\"\n].*|[\n]*)$', value):
    return '"' + value.replace('"', '""') + '"'
  return value

def csv_row(row: dict, columns: list) -> str:
  """Convert dict to CSV row string with proper escaping."""
  return ','.join(csv_escape(row.get(col, '')) for col in columns)

def write_csv_header(file_path: str, columns: list) -> None:
  """Write CSV header row to file (UTF-8 without BOM)."""
  with open(file_path, 'w', encoding='utf-8', newline='') as f:
    f.write(','.join(columns) + '\n')

def append_csv_rows(file_path: str, rows: list[dict], columns: list) -> None:
  """Append rows to CSV file."""
  if not rows: return
  with open(file_path, 'a', encoding='utf-8', newline='') as f:
    for row in rows:
      f.write(csv_row(row, columns) + '\n')

# ----------------------------------------- END: CSV Functions ----------------------------------------------------------------


# ----------------------------------------- START: Cache Functions ------------------------------------------------------------

def get_entra_cache_folder(storage_path: str) -> str:
  """Get Entra ID group cache folder path."""
  return os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_SITES_SUBFOLDER, "_entra_group_cache")

def load_entra_group_cache(storage_path: str, group_id: str) -> dict | None:
  """Load cached Entra ID group members if available."""
  cache_path = os.path.join(get_entra_cache_folder(storage_path), f"{group_id}.json")
  if not os.path.exists(cache_path): return None
  try:
    with open(cache_path, 'r', encoding='utf-8') as f: return json.load(f)
  except: return None

def save_entra_group_cache(storage_path: str, group_id: str, data: dict) -> None:
  """Save Entra ID group members to cache."""
  cache_folder = get_entra_cache_folder(storage_path)
  os.makedirs(cache_folder, exist_ok=True)
  cache_path = os.path.join(cache_folder, f"{group_id}.json")
  with open(cache_path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2)

def delete_all_entra_caches(storage_path: str) -> int:
  """Delete all Entra ID group caches. Returns count of deleted files."""
  cache_folder = get_entra_cache_folder(storage_path)
  if not os.path.exists(cache_folder): return 0
  count = 0
  for f in os.listdir(cache_folder):
    if f.endswith('.json'):
      os.remove(os.path.join(cache_folder, f))
      count += 1
  return count

# ----------------------------------------- END: Cache Functions --------------------------------------------------------------


# ----------------------------------------- START: Scanner Settings -----------------------------------------------------------

def get_scanner_settings_path(storage_path: str) -> str:
  """Get path to scanner settings file."""
  return os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_SITES_SUBFOLDER, CRAWLER_HARDCODED_CONFIG.SECURITY_SCAN_SETTINGS_FILENAME)

def load_scanner_settings(storage_path: str) -> dict:
  """Load scanner settings from file; create with defaults if missing."""
  settings_path = get_scanner_settings_path(storage_path)
  if not os.path.exists(settings_path):
    defaults = dict(CRAWLER_HARDCODED_CONFIG.DEFAULT_SECURITY_SCAN_SETTINGS)
    save_scanner_settings(storage_path, defaults)
    print(f"[Scanner Settings] Created default settings file: {settings_path}")
    return defaults
  try:
    with open(settings_path, 'r', encoding='utf-8') as f:
      settings = json.load(f)
      print(f"[Scanner Settings] Loaded settings from: {settings_path}")
      return settings
  except Exception as e:
    print(f"[Scanner Settings] ERROR: Failed to load settings from '{settings_path}': {e} - using defaults")
    return dict(CRAWLER_HARDCODED_CONFIG.DEFAULT_SECURITY_SCAN_SETTINGS)

def save_scanner_settings(storage_path: str, settings: dict) -> None:
  """Save scanner settings to file."""
  settings_path = get_scanner_settings_path(storage_path)
  os.makedirs(os.path.dirname(settings_path), exist_ok=True)
  with open(settings_path, 'w', encoding='utf-8') as f:
    json.dump(settings, f, indent=2)
  print(f"[Scanner Settings] Saved settings to: {settings_path}")

# ----------------------------------------- END: Scanner Settings -------------------------------------------------------------


# ----------------------------------------- START: Graph Client ---------------------------------------------------------------

_graph_client = None
_graph_credentials = None

def get_graph_client(tenant_id: str, client_id: str, cert_path: str, cert_password: str) -> GraphServiceClient:
  """Get or create Graph client for Entra ID group resolution using certificate auth."""
  global _graph_client, _graph_credentials
  cred_key = (tenant_id, client_id, cert_path)
  if _graph_client is None or _graph_credentials != cred_key:
    credential = CertificateCredential(tenant_id, client_id, certificate_path=cert_path, password=cert_password)
    _graph_client = GraphServiceClient(credential)
    _graph_credentials = cred_key
  return _graph_client

def reset_graph_client() -> None:
  """Reset Graph client (for testing or credential changes)."""
  global _graph_client, _graph_credentials
  _graph_client = None
  _graph_credentials = None

# ----------------------------------------- END: Graph Client -----------------------------------------------------------------


# ----------------------------------------- START: Group Resolution -----------------------------------------------------------

def is_entra_id_group(login_name: str) -> bool:
  """Check if login name represents an Entra ID (Azure AD) group."""
  if not login_name: return False
  # Entra ID groups have c:0t.c|tenant|{guid} or c:0-.f|rolemanager|{guid} or c:0o.c|federateddirectoryclaimprovider|{guid} format
  return "|" in login_name and any(prefix in login_name for prefix in ["c:0t.c", "c:0-.f", "c:0o.c"])

def extract_group_id_from_login(login_name: str) -> str | None:
  """Extract Entra ID group GUID from login name."""
  # Format: c:0t.c|tenant|{guid} or c:0o.c|federateddirectoryclaimprovider|{guid}_o
  parts = login_name.split("|")
  if len(parts) >= 3:
    group_id = parts[-1]
    # M365 groups have _o suffix that must be stripped for Graph API calls
    if group_id.endswith("_o"): group_id = group_id[:-2]
    return group_id
  return None

async def resolve_entra_group_members(storage_path: str, graph_client: GraphServiceClient, group_id: str, group_name: str, nesting_level: int, parent_group: str, writer, logger: MiddlewareLogger) -> list:
  """Resolve Entra ID group members using Graph API with caching."""
  if nesting_level > MAX_NESTING_LEVEL:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    writer.emit_log(f"[{ts}]           WARNING: Max nesting level ({MAX_NESTING_LEVEL}) reached for group_name='{group_name}'")
    return []
  
  # Check cache first
  cached = load_entra_group_cache(storage_path, group_id)
  if cached:
    member_count = len(cached.get('members', []))
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    writer.emit_log(f"[{ts}]           Using cached {member_count} member(s) for group_name='{group_name}'".replace("(s)", "s" if member_count != 1 else ""))
    return cached.get("members", [])
  
  # Fetch from Graph API using transitive members
  ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  writer.emit_log(f"[{ts}]           Fetching from Graph API for group_name='{group_name}'...")
  members = []
  try:
    members_response = await graph_client.groups.by_group_id(group_id).transitive_members.get()
    
    for member in members_response.value:
      if hasattr(member, 'odata_type') and member.odata_type == "#microsoft.graph.user":
        members.append({
          "Id": "",  # Empty for nested Entra ID members per SPEC
          "LoginName": member.user_principal_name or "",
          "DisplayName": member.display_name or "",
          "Email": member.mail or "",
          "NestingLevel": nesting_level,
          "ParentGroup": parent_group,
          "ViaGroup": group_name,
          "ViaGroupId": group_id,
          "ViaGroupType": "SecurityGroup",
          "AssignmentType": "Group"
        })
    
    # Cache result
    save_entra_group_cache(storage_path, group_id, {
      "group_id": group_id,
      "group_name": group_name,
      "cached_utc": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z",
      "member_count": len(members),
      "members": members
    })
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    writer.emit_log(f"[{ts}]           OK. {len(members)} member(s) resolved and cached.".replace("(s)", "s" if len(members) != 1 else ""))
  except Exception as e:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    writer.emit_log(f"[{ts}]           ERROR: Failed to resolve Entra group_name='{group_name}' -> {e}")
  
  return members

async def resolve_sharepoint_group_members(ctx: ClientContext, group, storage_path: str, graph_client: Optional[GraphServiceClient], writer, nesting_level: int, parent_group: str, logger: MiddlewareLogger, settings: dict = None) -> list:
  """Resolve all members of a SharePoint group, including nested Entra ID groups."""
  if settings is None: settings = {}
  max_nesting = settings.get("max_group_nesting_level", MAX_NESTING_LEVEL)
  ignore_accounts = set(settings.get("ignore_accounts", []))
  do_not_resolve = set(settings.get("do_not_resolve_these_groups", []))
  
  if nesting_level > max_nesting: return []
  
  members = []
  try:
    users = group.users.get().execute_query()
  except Exception as e:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    writer.emit_log(f"[{ts}]       ERROR: Failed to get users for group_title='{group.title}' -> {e}")
    return []
  
  user_count = len(users)
  ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  writer.emit_log(f"[{ts}]       {user_count} member(s) in group_title='{group.title}'".replace("(s)", "s" if user_count != 1 else ""))
  
  for user in users:
    login_name = user.login_name or ""
    # Skip ignored accounts from settings
    if any(ignored in login_name for ignored in ignore_accounts): continue
    
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    writer.emit_log(f"[{ts}]         Member: display_name='{user.title}' login='{login_name[:50]}...'")
    
    if is_entra_id_group(login_name):
      group_id = extract_group_id_from_login(login_name)
      group_display_name = user.title or login_name
      writer.emit_log(f"[{ts}]           -> Entra ID group (group_id={group_id})")
      
      # Check if group should not be resolved (from settings) - still add entry, just skip nested resolution
      if group_display_name in do_not_resolve:
        writer.emit_log(f"[{ts}]           SKIPPED nested resolution: Group in do_not_resolve_these_groups setting")
        # Add entry for the group itself (not resolved)
        members.append({
          "Id": "",
          "LoginName": login_name,
          "DisplayName": group_display_name,
          "Email": "",
          "NestingLevel": nesting_level,
          "ParentGroup": parent_group,
          "ViaGroup": group.title,
          "ViaGroupId": str(group.id),
          "ViaGroupType": "SharePointGroup",
          "AssignmentType": "Group"
        })
        continue
      
      if group_id and graph_client:
        writer.emit_log(f"[{ts}]           Resolving via Graph API...")
        # Resolve Entra ID group members
        nested = await resolve_entra_group_members(
          storage_path, graph_client, group_id, user.title or login_name,
          nesting_level + 1, group.title, writer, logger
        )
        ts2 = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.emit_log(f"[{ts2}]           OK. {len(nested)} nested member(s) resolved.".replace("(s)", "s" if len(nested) != 1 else ""))
        # Update ViaGroup to point to SP group
        for m in nested:
          m["ViaGroup"] = group.title
          m["ViaGroupId"] = str(group.id)
          m["ViaGroupType"] = "SharePointGroup"
        members.extend(nested)
      elif not graph_client:
        writer.emit_log(f"[{ts}]           WARNING: No Graph client, cannot resolve Entra group")
    else:
      members.append({
        "Id": str(user.id) if user.id else "",
        "LoginName": login_name,
        "DisplayName": user.title or "",
        "Email": user.email or "",
        "NestingLevel": nesting_level,
        "ParentGroup": parent_group,
        "ViaGroup": group.title,
        "ViaGroupId": str(group.id),
        "ViaGroupType": "SharePointGroup",
        "AssignmentType": "Group"
      })
  
  return members

# ----------------------------------------- END: Group Resolution -------------------------------------------------------------


# ----------------------------------------- START: Scanning Functions ---------------------------------------------------------

async def scan_site_contents(ctx: ClientContext, output_folder: str, writer, logger: MiddlewareLogger, current_step: int, total_steps: int) -> AsyncGenerator[str, None]:
  """Scan lists/libraries and write 01_SiteContents.csv. Yields SSE events. Sets writer._step_result with stats."""
  stats = {"lists_scanned": 0}
  contents_file = os.path.join(output_folder, "01_SiteContents.csv")
  
  # Only write header when called from main scan (step > 0), not from subsite scanning
  if current_step > 0:
    write_csv_header(contents_file, CSV_COLUMNS_SITE_CONTENTS)
  
  ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  if current_step > 0:
    yield writer.emit_log(f"[{ts}] [ {current_step} / {total_steps} ] Scanning site contents...")
  lists = ctx.web.lists.get().select(["Id", "Title", "BaseTemplate", "Hidden", "RootFolder"]).expand(["RootFolder"]).execute_query()
  
  rows = []
  for lst in lists:
    if lst.base_template not in INCLUDED_TEMPLATES: continue
    if lst.properties.get("Hidden", False): continue
    
    stats["lists_scanned"] += 1
    
    list_type = "LIST" if lst.base_template == 100 else "LIBRARY"
    if lst.base_template == 119: list_type = "SITEPAGES"
    
    # Get root folder URL from expanded property
    try:
      url = lst.root_folder.properties.get("ServerRelativeUrl", "") if lst.root_folder else ""
    except:
      url = ""
    
    rows.append({
      "Id": str(lst.id),
      "Type": list_type,
      "Title": lst.title,
      "Url": url
    })
  
  append_csv_rows(contents_file, rows, CSV_COLUMNS_SITE_CONTENTS)
  ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  yield writer.emit_log(f"[{ts}]   {stats['lists_scanned']} list(s)/libraries found.".replace("(s)", "s" if stats['lists_scanned'] != 1 else ""))
  writer._step_result = stats

async def scan_site_groups(ctx: ClientContext, storage_path: str, output_folder: str, graph_client: Optional[GraphServiceClient], writer, logger: MiddlewareLogger, current_step: int, total_steps: int, settings: dict = None) -> AsyncGenerator[str, None]:
  """Scan site groups and write 02_SiteGroups.csv and 03_SiteUsers.csv. Yields SSE events. Sets writer._step_result with stats."""
  stats = {"groups_found": 0, "users_found": 0, "external_users_found": 0}
  if settings is None: settings = {}
  
  # Extract settings
  ignore_permission_levels = set(settings.get("ignore_permission_levels", ["Limited Access"]))
  ignore_accounts = set(settings.get("ignore_accounts", []))
  ignore_sharepoint_groups = set(settings.get("ignore_sharepoint_groups", []))
  do_not_resolve_these_groups = set(settings.get("do_not_resolve_these_groups", []))
  max_nesting = settings.get("max_group_nesting_level", 5)
  
  groups_file = os.path.join(output_folder, "02_SiteGroups.csv")
  users_file = os.path.join(output_folder, "03_SiteUsers.csv")
  
  # Only write headers when called from main scan (step > 0), not from subsite scanning
  if current_step > 0:
    write_csv_header(groups_file, CSV_COLUMNS_SITE_GROUPS)
    write_csv_header(users_file, CSV_COLUMNS_SITE_USERS)
  
  ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  if current_step > 0:
    yield writer.emit_log(f"[{ts}] [ {current_step} / {total_steps} ] Scanning site groups (graph_client_available={graph_client is not None})...")
  
  # Load site groups with role assignments to get permission levels
  role_assignments = ctx.web.role_assignments.get()
  role_assignments.expand(["Member", "RoleDefinitionBindings"]).execute_query()
  ra_list = list(role_assignments)
  ra_count = len(ra_list)
  ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  yield writer.emit_log(f"[{ts}]   {ra_count} role assignment(s) found.".replace("(s)", "s" if ra_count != 1 else ""))
  
  # Build group -> permission level mapping and collect direct assignments
  group_permissions = {}
  direct_user_rows = []  # Direct user/security group assignments at site level
  
  for ra_idx, ra in enumerate(ra_list, 1):
    member = ra.member
    # Determine assignment type based on principal_type
    if member.principal_type == 1: assign_type = "User"
    elif member.principal_type == 4: assign_type = "SecurityGroup"
    elif member.principal_type == 8: assign_type = "SharePointGroup"
    else: assign_type = f"Unknown({member.principal_type})"
    
    # Get permission levels (skip ignored permission levels from settings)
    perm_levels = [b.properties.get('Name', '') for b in ra.role_definition_bindings if b.properties.get('Name', '') not in ignore_permission_levels]
    perm_str = ', '.join(perm_levels) if perm_levels else "Ignored permission levels only"
    
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    yield writer.emit_log(f"[{ts}]     ( {ra_idx} / {ra_count} ) {assign_type}: '{member.title}' -> {perm_str}")
    
    for binding in ra.role_definition_bindings:
      perm_name = binding.properties.get('Name', '')
      # FILTER: Skip ignored permission levels from settings
      if perm_name in ignore_permission_levels: continue
      
      if member.principal_type == 8:  # SharePoint Group
        group_permissions[member.id] = perm_name
      elif member.principal_type == 1:  # Direct User assignment
        login_name = member.login_name or ""
        # Skip ignored accounts from settings
        if any(ignored in login_name for ignored in ignore_accounts): continue
        direct_user_rows.append({
          "Id": str(member.id) if member.id else "",
          "LoginName": login_name,
          "DisplayName": member.title or "",
          "Email": member.email or "" if hasattr(member, 'email') else "",
          "PermissionLevel": perm_name,
          "ViaGroup": "",
          "ViaGroupId": "",
          "ViaGroupType": "",
          "AssignmentType": "Direct",
          "NestingLevel": 0,
          "ParentGroup": ""
        })
      elif member.principal_type == 4:  # Direct Security Group assignment
        login_name = member.login_name or ""
        # Skip ignored accounts from settings
        if any(ignored in login_name for ignored in ignore_accounts): continue
        direct_user_rows.append({
          "Id": "",
          "LoginName": login_name,
          "DisplayName": member.title or "",
          "Email": "",
          "PermissionLevel": perm_name,
          "ViaGroup": "",
          "ViaGroupId": "",
          "ViaGroupType": "",
          "AssignmentType": "SecurityGroup",
          "NestingLevel": 0,
          "ParentGroup": ""
        })
  
  # Load all site groups and filter to those with permissions (skip ignored SP groups)
  all_groups = ctx.web.site_groups.get().execute_query()
  groups_to_process = [g for g in all_groups if group_permissions.get(g.id, "") and g.title not in ignore_sharepoint_groups]
  total_groups = len(groups_to_process)
  
  ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  yield writer.emit_log(f"[{ts}]   {total_groups} SharePoint group(s) to resolve, {len(direct_user_rows)} direct assignment(s).".replace("(s)", "s" if total_groups != 1 else "", 1).replace("(s)", "s" if len(direct_user_rows) != 1 else "", 1))
  
  group_rows = []
  user_rows = direct_user_rows.copy()  # Start with direct assignments
  stats["users_found"] = len(direct_user_rows)  # Count direct assignments
  
  for idx, group in enumerate(groups_to_process, 1):
    perm_level = group_permissions.get(group.id, "")
    
    stats["groups_found"] += 1
    
    # Determine role
    role = "Custom"
    title_lower = group.title.lower() if group.title else ""
    if "owner" in title_lower: role = "SiteOwners"
    elif "member" in title_lower: role = "SiteMembers"
    elif "visitor" in title_lower: role = "SiteVisitors"
    
    group_rows.append({
      "Id": str(group.id),
      "Role": role,
      "Title": group.title,
      "PermissionLevel": perm_level,
      "Owner": group.owner_title or ""
    })
    
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    yield writer.emit_log(f"[{ts}]     ( {idx} / {total_groups} ) SharePointGroup: group_title='{group.title}'...")
    
    # Resolve members
    members = await resolve_sharepoint_group_members(ctx, group, storage_path, graph_client, writer, 1, "", logger, settings)
    for member in members:
      member["PermissionLevel"] = perm_level
      stats["users_found"] += 1
      # Track external users (contain #ext# in login)
      if "#ext#" in member.get("LoginName", "").lower():
        stats["external_users_found"] += 1
      user_rows.append(member)
  
  append_csv_rows(groups_file, group_rows, CSV_COLUMNS_SITE_GROUPS)
  append_csv_rows(users_file, user_rows, CSV_COLUMNS_SITE_USERS)
  
  ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  yield writer.emit_log(f"[{ts}]   {stats['groups_found']} group(s), {stats['users_found']} user(s) found.".replace("(s)", "s" if stats['groups_found'] != 1 else "", 1).replace("(s)", "s" if stats['users_found'] != 1 else "", 1))
  writer._step_result = stats

async def scan_broken_inheritance_items(ctx: ClientContext, storage_path: str, output_folder: str, graph_client: Optional[GraphServiceClient], writer, logger: MiddlewareLogger, current_step: int, total_steps: int, settings: dict = None) -> AsyncGenerator[str, None]:
  """Scan items with broken inheritance and write 04/05 CSVs. Yields SSE events. Sets writer._step_result with stats."""
  stats = {"items_scanned": 0, "items_with_individual_permissions": 0, "items_shared_with_everyone": 0}
  items_shared_with_everyone_items = set()  # Track unique items shared with everyone
  if settings is None: settings = {}
  
  # Extract settings
  ignore_lists = set(settings.get("ignore_lists", []))
  ignore_permission_levels = set(settings.get("ignore_permission_levels", ["Limited Access"]))
  ignore_accounts = set(settings.get("ignore_accounts", []))
  
  items_file = os.path.join(output_folder, "04_IndividualPermissionItems.csv")
  access_file = os.path.join(output_folder, "05_IndividualPermissionItemAccess.csv")
  
  # Only write headers when called from main scan (step > 0), not from subsite scanning
  if current_step > 0:
    write_csv_header(items_file, CSV_COLUMNS_INDIVIDUAL_ITEMS)
    write_csv_header(access_file, CSV_COLUMNS_INDIVIDUAL_ACCESS)
  
  ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  if current_step > 0:
    yield writer.emit_log(f"[{ts}] [ {current_step} / {total_steps} ] Scanning items with broken inheritance...")
  
  all_lists = ctx.web.lists.get().execute_query()
  # Filter to relevant lists: skip hidden and lists in ignore_lists
  lists_to_scan = [lst for lst in all_lists if lst.base_template in INCLUDED_TEMPLATES and not lst.properties.get("Hidden", False) and lst.title not in ignore_lists]
  total_lists = len(lists_to_scan)
  
  ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  yield writer.emit_log(f"[{ts}]   {total_lists} list(s)/libraries to scan.".replace("(s)", "s" if total_lists != 1 else ""))
  
  item_rows = []
  access_rows = []
  
  for list_idx, lst in enumerate(lists_to_scan, 1):
    # Determine list type for logging
    if lst.base_template == 100: list_type = "List"
    elif lst.base_template == 119: list_type = "SitePages"
    else: list_type = "Library"
    
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    yield writer.emit_log(f"[{ts}]     ( {list_idx} / {total_lists} ) {list_type}: list_title='{lst.title}'...")
    
    # Paginate through items
    last_id = 0
    batch_num = 0
    while True:
      try:
        items = lst.items.filter(f"ID gt {last_id}").select(
          ["ID", "FileRef", "FileLeafRef", "FSObjType", "HasUniqueRoleAssignments"]
        ).top(BATCH_SIZE).get().execute_query()
      except Exception as e:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        yield writer.emit_log(f"[{ts}]   ERROR: Failed to get items from list_title='{lst.title}' -> {e}")
        break
      
      if len(items) == 0: break
      
      # Progress indicator after fetching each batch
      batch_num += 1
      items_with_perms = sum(1 for i in items if i.properties.get("HasUniqueRoleAssignments"))
      if items_with_perms > 0:  # Show progress when there are items to check
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        yield writer.emit_log(f"[{ts}]       Fetched {len(items)} items ({items_with_perms} with unique permissions)...")
      
      for item in items:
        stats["items_scanned"] += 1
        item_id = item.properties.get("ID", 0)
        
        if item.properties.get("HasUniqueRoleAssignments"):
          stats["items_with_individual_permissions"] += 1
          
          file_ref = item.properties.get("FileRef", "")
          file_name = item.properties.get("FileLeafRef", "")
          fs_obj_type = item.properties.get("FSObjType", 0)
          item_type = "FOLDER" if fs_obj_type == 1 else "ITEM"
          
          item_rows.append({
            "Id": str(item_id),
            "Type": item_type,
            "Title": file_name,
            "Url": file_ref
          })
          
          # Get role assignments for this item
          try:
            role_assignments = item.role_assignments.get()
            role_assignments.expand(["Member", "RoleDefinitionBindings"]).execute_query()
            ra_list = list(role_assignments)  # Convert to list once to avoid consuming iterator
            # Debug logging removed - too verbose for SSE
            
            for ra in ra_list:
              member = ra.member
              bindings_list = list(ra.role_definition_bindings) if ra.role_definition_bindings else []
              # Debug logging removed - too verbose for SSE
              for binding in bindings_list:
                perm_name = binding.properties.get('Name', '')
                # Debug logging removed - too verbose for SSE
                if perm_name == "Limited Access": continue
                
                # Track items shared with "Everyone except external users"
                member_title = member.title or ""
                if "Everyone except external users" in member_title:
                  items_shared_with_everyone_items.add(item_id)
                
                access_rows.append({
                  "Id": str(item_id),
                  "Type": item_type,
                  "Url": file_ref,
                  "LoginName": member.login_name or "",
                  "DisplayName": member_title,
                  "Email": member.email or "" if hasattr(member, 'email') else "",
                  "PermissionLevel": perm_name,
                  "SharedDateTime": "",
                  "SharedByDisplayName": "",
                  "SharedByLoginName": "",
                  "ViaGroup": "",
                  "ViaGroupId": "",
                  "ViaGroupType": "",
                  "AssignmentType": "User" if member.principal_type == 1 else "Group",
                  "NestingLevel": 0,
                  "ParentGroup": ""
                })
          except Exception as e:
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            yield writer.emit_log(f"[{ts}]     ERROR: Failed to get permissions for item_id={item_id} -> {e}")
        
        last_id = item_id
      
      if len(items) < BATCH_SIZE: break
  
  append_csv_rows(items_file, item_rows, CSV_COLUMNS_INDIVIDUAL_ITEMS)
  append_csv_rows(access_file, access_rows, CSV_COLUMNS_INDIVIDUAL_ACCESS)
  
  # Update items_shared_with_everyone count
  stats["items_shared_with_everyone"] = len(items_shared_with_everyone_items)
  
  ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  yield writer.emit_log(f"[{ts}]   {stats['items_scanned']} item(s) scanned, {stats['items_with_individual_permissions']} with broken inheritance.".replace("(s)", "s" if stats['items_scanned'] != 1 else ""))
  writer._step_result = stats

# ----------------------------------------- END: Scanning Functions -----------------------------------------------------------


# ----------------------------------------- START: Subsite Scanning -----------------------------------------------------------

async def scan_subsites(
  parent_ctx: ClientContext,
  storage_path: str,
  output_folder: str,
  graph_client,
  writer,
  logger: MiddlewareLogger,
  settings: dict,
  client_id: str,
  tenant_id: str,
  cert_path: str,
  cert_password: str,
  depth: int = 0,
  max_depth: int = 5
) -> dict:
  """Recursively scan subsites when include_subsites=true (SCAN-FR-06)."""
  stats = {"subsites_scanned": 0, "groups_found": 0, "users_found": 0, "external_users_found": 0, "items_scanned": 0, "items_with_individual_permissions": 0, "items_shared_with_everyone": 0}
  
  if depth >= max_depth:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    writer.emit_log(f"[{ts}]   WARNING: Max subsite depth ({max_depth}) reached, skipping deeper subsites")
    return stats
  
  # Get subsites with Url, Title and HasUniqueRoleAssignments properties loaded
  try:
    webs = parent_ctx.web.webs.get().select(["Id", "Title", "Url", "HasUniqueRoleAssignments"]).execute_query()
  except Exception as e:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    writer.emit_log(f"[{ts}]   ERROR: Failed to get subsites -> {e}")
    return stats
  
  subsites = list(webs)
  if not subsites:
    return stats
  
  ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  writer.emit_log(f"[{ts}]   Found {len(subsites)} subsite(s) at depth={depth}".replace("(s)", "s" if len(subsites) != 1 else ""))
  
  contents_file = os.path.join(output_folder, "01_SiteContents.csv")
  
  for idx, subweb in enumerate(subsites, 1):
    stats["subsites_scanned"] += 1
    subsite_url = subweb.url
    subsite_title = subweb.title or "Untitled"
    subsite_id = subweb.id
    
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    writer.emit_log(f"[{ts}]   ( {idx} / {len(subsites)} ) SUBSITE: '{subsite_title}' url='{subsite_url}'")
    
    # Add subsite to 01_SiteContents.csv
    append_csv_rows(contents_file, [{
      "Id": str(subsite_id),
      "Type": "SUBSITE",
      "Title": subsite_title,
      "Url": subsite_url
    }], CSV_COLUMNS_SITE_CONTENTS)
    
    # Check if subsite has broken inheritance - add to 04_IndividualPermissionItems.csv
    has_unique = subweb.properties.get("HasUniqueRoleAssignments", False)
    if has_unique:
      items_file = os.path.join(output_folder, "04_IndividualPermissionItems.csv")
      append_csv_rows(items_file, [{
        "Id": str(subsite_id),
        "Type": "SUBSITE",
        "Title": subsite_title,
        "Url": subsite_url
      }], CSV_COLUMNS_INDIVIDUAL_ITEMS)
      stats["items_with_individual_permissions"] += 1
      ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      writer.emit_log(f"[{ts}]     Subsite has broken inheritance")
    
    # Create new context for subsite using same credentials
    try:
      from routers_v2.common_sharepoint_functions_v2 import connect_to_site_using_client_id_and_certificate
      sub_ctx = connect_to_site_using_client_id_and_certificate(subsite_url, client_id, tenant_id, cert_path, cert_password)
      sub_ctx.web.get().execute_query()
      
      ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      writer.emit_log(f"[{ts}]     Connected to subsite")
      
      # Scan subsite site contents (lists/libraries) - append to same CSV
      contents_stats = scan_site_contents(sub_ctx, output_folder, writer, logger, 0, 0)
      for sse in writer.drain_sse_queue(): pass
      
      # Scan subsite groups
      group_stats = await scan_site_groups(sub_ctx, storage_path, output_folder, graph_client, writer, logger, 0, 0, settings)
      for sse in writer.drain_sse_queue(): pass  # Drain queue but don't yield here
      stats["groups_found"] += group_stats["groups_found"]
      stats["users_found"] += group_stats["users_found"]
      stats["external_users_found"] += group_stats.get("external_users_found", 0)
      
      # Scan subsite broken inheritance items
      ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      writer.emit_log(f"[{ts}]     Scanning subsite items with broken inheritance...")
      loop = asyncio.get_event_loop()
      item_stats = scan_broken_inheritance_items(sub_ctx, storage_path, output_folder, graph_client, writer, logger, loop, 0, 0, settings)
      for sse in writer.drain_sse_queue(): pass
      ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      writer.emit_log(f"[{ts}]     {item_stats['items_scanned']} items scanned, {item_stats['items_with_individual_permissions']} with broken inheritance.")
      stats["items_scanned"] += item_stats["items_scanned"]
      stats["items_with_individual_permissions"] += item_stats["items_with_individual_permissions"]
      stats["items_shared_with_everyone"] += item_stats.get("items_shared_with_everyone", 0)
      
      # Recurse into sub-subsites
      sub_stats = await scan_subsites(sub_ctx, storage_path, output_folder, graph_client, writer, logger, settings, client_id, tenant_id, cert_path, cert_password, depth + 1, max_depth)
      stats["subsites_scanned"] += sub_stats["subsites_scanned"]
      stats["groups_found"] += sub_stats["groups_found"]
      stats["users_found"] += sub_stats["users_found"]
      stats["external_users_found"] += sub_stats.get("external_users_found", 0)
      stats["items_scanned"] += sub_stats["items_scanned"]
      stats["items_with_individual_permissions"] += sub_stats["items_with_individual_permissions"]
      stats["items_shared_with_everyone"] += sub_stats.get("items_shared_with_everyone", 0)
      
    except Exception as e:
      ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      writer.emit_log(f"[{ts}]     ERROR: Failed to scan subsite '{subsite_title}' -> {e}")
  
  return stats

# ----------------------------------------- END: Subsite Scanning -------------------------------------------------------------


# ----------------------------------------- START: Main Scanner ---------------------------------------------------------------

async def run_security_scan(
  site_url: str,
  site_id: str,
  scope: str,
  include_subsites: bool,
  delete_caches: bool,
  storage_path: str,
  client_id: str,
  tenant_id: str,
  cert_path: str,
  cert_password: str,
  writer,  # StreamingJobWriter
  logger: MiddlewareLogger
) -> AsyncGenerator[str, None]:
  """
  Run security scan and yield SSE events.
  
  Args:
    site_url: SharePoint site URL
    site_id: Internal site identifier
    scope: Scan scope (all, site, lists, items)
    include_subsites: Whether to scan subsites
    delete_caches: Whether to delete Entra ID caches before scan
    storage_path: Persistent storage path
    client_id: Azure AD app client ID
    tenant_id: Azure AD tenant ID
    cert_path: Path to certificate for SharePoint and Graph API auth
    cert_password: Certificate password
    writer: StreamingJobWriter for SSE events
    logger: MiddlewareLogger instance
  
  Yields:
    SSE event strings
  """
  
  # Load scanner settings
  settings = load_scanner_settings(storage_path)
  settings_path = get_scanner_settings_path(storage_path)
  ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  yield writer.emit_log(f"[{ts}] Loaded scanner settings from path='{settings_path}'")
  
  # Calculate total steps based on scope
  # Steps: 1=Connect, 2=Graph client, 3=Site contents (if scope), 4=Site groups (if scope), 5=Broken items (if scope), 6=Subsites (if enabled), 7=Create report
  total_steps = 3  # Connect + Graph + Report always
  if scope in ["all", "site", "lists"]: total_steps += 1
  if scope in ["all", "site"]: total_steps += 1
  if scope in ["all", "items"]: total_steps += 1
  if include_subsites: total_steps += 1
  current_step = 0
  
  # Delete caches if requested (step 0 - not counted)
  if delete_caches:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    yield writer.emit_log(f"[{ts}] Deleting cached Entra ID group files...")
    deleted = delete_all_entra_caches(storage_path)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    yield writer.emit_log(f"[{ts}]   {deleted} cache file(s) deleted.".replace("(s)", "s" if deleted != 1 else ""))
  
  # Create temp output folder in storage_path\{TEMP_SUBFOLDER}
  temp_base = os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_TEMP_SUBFOLDER)
  os.makedirs(temp_base, exist_ok=True)
  output_folder = tempfile.mkdtemp(prefix=f"security_scan_{site_id}_", dir=temp_base)
  ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  yield writer.emit_log(f"[{ts}] Created temp folder path='{output_folder}'")
  
  stats = {
    "lists_scanned": 0,
    "groups_found": 0,
    "users_found": 0,
    "external_users_found": 0,
    "items_scanned": 0,
    "items_with_individual_permissions": 0,
    "items_shared_with_everyone": 0,
    "subsites_scanned": 0
  }
  
  try:
    # Step 1: Connect to SharePoint
    current_step += 1
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    yield writer.emit_log(f"[{ts}] [ {current_step} / {total_steps} ] Connecting to SharePoint site_url='{site_url}'...")
    ctx = connect_to_site_using_client_id_and_certificate(site_url, client_id, tenant_id, cert_path, cert_password)
    ctx.web.get().execute_query()
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    yield writer.emit_log(f"[{ts}]   OK. Connected to site_title='{ctx.web.title}'")
    
    # Step 2: Initialize Graph client for Entra ID resolution (using certificate auth)
    current_step += 1
    graph_client = None
    if cert_path and cert_password:
      ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      yield writer.emit_log(f"[{ts}] [ {current_step} / {total_steps} ] Initializing Microsoft Graph client...")
      try:
        graph_client = get_graph_client(tenant_id, client_id, cert_path, cert_password)
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        yield writer.emit_log(f"[{ts}]   OK. Graph client ready.")
      except Exception as e:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        yield writer.emit_log(f"[{ts}]   ERROR: Failed to create Graph client -> {e}")
        graph_client = None
    else:
      ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      yield writer.emit_log(f"[{ts}] [ {current_step} / {total_steps} ] Initializing Microsoft Graph client...")
      yield writer.emit_log(f"[{ts}]   WARNING: No certificate credentials - Graph client not available")
    
    # Scan based on scope - all scan functions are now async generators that yield SSE events
    if scope in ["all", "site", "lists"]:
      current_step += 1
      async for sse in scan_site_contents(ctx, output_folder, writer, logger, current_step, total_steps):
        yield sse
      content_stats = writer._step_result or {}
      stats["lists_scanned"] = content_stats.get("lists_scanned", 0)
    
    if scope in ["all", "site"]:
      current_step += 1
      async for sse in scan_site_groups(ctx, storage_path, output_folder, graph_client, writer, logger, current_step, total_steps, settings):
        yield sse
      group_stats = writer._step_result or {}
      stats["groups_found"] = group_stats.get("groups_found", 0)
      stats["users_found"] = group_stats.get("users_found", 0)
      stats["external_users_found"] = group_stats.get("external_users_found", 0)
    
    if scope in ["all", "items"]:
      current_step += 1
      async for sse in scan_broken_inheritance_items(ctx, storage_path, output_folder, graph_client, writer, logger, current_step, total_steps, settings):
        yield sse
      item_stats = writer._step_result or {}
      stats["items_scanned"] = item_stats.get("items_scanned", 0)
      stats["items_with_individual_permissions"] = item_stats.get("items_with_individual_permissions", 0)
      stats["items_shared_with_everyone"] = item_stats.get("items_shared_with_everyone", 0)
    
    # Scan subsites if requested (SCAN-FR-06)
    if include_subsites:
      current_step += 1
      ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      yield writer.emit_log(f"[{ts}] [ {current_step} / {total_steps} ] Scanning subsites recursively...")
      subsite_stats = await scan_subsites(ctx, storage_path, output_folder, graph_client, writer, logger, settings, client_id, tenant_id, cert_path, cert_password)
      for sse in writer.drain_sse_queue(): yield sse
      ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      yield writer.emit_log(f"[{ts}]   {subsite_stats['subsites_scanned']} subsite(s) scanned.".replace("(s)", "s" if subsite_stats['subsites_scanned'] != 1 else ""))
      # Add subsite stats to totals
      stats["subsites_scanned"] += subsite_stats["subsites_scanned"] + 1  # +1 for this subsite level
      stats["groups_found"] += subsite_stats["groups_found"]
      stats["users_found"] += subsite_stats["users_found"]
      stats["external_users_found"] += subsite_stats.get("external_users_found", 0)
      stats["items_scanned"] += subsite_stats["items_scanned"]
      stats["items_with_individual_permissions"] += subsite_stats["items_with_individual_permissions"]
      stats["items_shared_with_everyone"] += subsite_stats.get("items_shared_with_everyone", 0)
    
    # Final step: Create report archive
    current_step += 1
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    yield writer.emit_log(f"[{ts}] [ {current_step} / {total_steps} ] Creating report archive...")
    
    # Import here to avoid circular dependency
    from routers_v2.common_report_functions_v2 import create_report
    
    # Read CSV files from output folder
    files = []
    for csv_file in os.listdir(output_folder):
      if csv_file.endswith(".csv"):
        file_path = os.path.join(output_folder, csv_file)
        with open(file_path, "rb") as f:
          files.append((csv_file, f.read()))
    
    # Generate filename with timestamp
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{timestamp}_[security_scan]_[{site_id}]"
    
    report_id = create_report(
      report_type="site_scan",
      filename=filename,
      files=files,
      metadata={
        "title": f"Security Scan: {site_id}",
        "type": "site_scan",
        "ok": True,
        "error": "",
        "site_id": site_id,
        "site_url": site_url,
        "scope": scope,
        "include_subsites": include_subsites,
        "stats": stats,
        "scanned_utc": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z"
      },
      logger=logger
    )
    report_path = report_id
    
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    yield writer.emit_log(f"[{ts}]   OK. Report created report_path='{report_path}'")
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    yield writer.emit_log(f"[{ts}] Scan complete. {stats['groups_found']} groups, {stats['users_found']} users, {stats['items_with_individual_permissions']} items with broken inheritance.")
    
    # Return stats for end event
    writer._step_result = {
      "report_path": report_path,
      "stats": stats
    }
    
  except Exception as e:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    yield writer.emit_log(f"[{ts}] ERROR: Security scan failed -> {e}")
    raise
  finally:
    # Cleanup temp folder
    import shutil
    if os.path.exists(output_folder):
      shutil.rmtree(output_folder, ignore_errors=True)

# ----------------------------------------- END: Main Scanner -----------------------------------------------------------------
