# Common functions for SharePoint security scanning
# Implements permission scanning per _V2_SPEC_SITES_SECURITY_SCAN.md [SITE-SP03]
# V2 version using MiddlewareLogger and Office365-REST-Python-Client

import asyncio, datetime, json, os, re, requests, tempfile
from typing import Any, AsyncGenerator, Optional
from azure.identity import CertificateCredential
from msgraph import GraphServiceClient
from office365.sharepoint.client_context import ClientContext
from hardcoded_config import CRAWLER_HARDCODED_CONFIG
from routers_v2.common_logging_functions_v2 import MiddlewareLogger, UNKNOWN
from routers_v2.common_sharepoint_functions_v2 import connect_to_site_using_client_id_and_certificate

# ----------------------------------------- START: Constants ------------------------------------------------------------------

MAX_NESTING_LEVEL = 5
BATCH_SIZE = 2000  # Reduced from 5000 to avoid SharePoint list view threshold errors
PROGRESS_INTERVAL_SECONDS = 5

# Built-in list templates to include (Generic List, Document Library, Site Pages)
INCLUDED_TEMPLATES = [100, 101, 119]

# CSV Column Definitions (EXACT order - must match PowerShell scanner)
# All CSVs start with Job,SiteUrl prefix
CSV_COLUMNS_SITE_CONTENTS = ["Job", "SiteUrl", "Id", "Type", "Title", "Url"]
CSV_COLUMNS_SITE_GROUPS = ["Job", "SiteUrl", "Id", "Role", "Title", "PermissionLevel", "Owner"]
CSV_COLUMNS_SITE_USERS = ["Job", "SiteUrl", "Id", "LoginName", "DisplayName", "Email", "PermissionLevel", "IsGuest", "ViaGroup", "ViaGroupId", "ViaGroupType", "AssignmentType", "NestingLevel", "ParentGroup"]
CSV_COLUMNS_INDIVIDUAL_ITEMS = ["Job", "SiteUrl", "Id", "Type", "Title", "Url"]
CSV_COLUMNS_INDIVIDUAL_ACCESS = ["Job", "SiteUrl", "Id", "Type", "Url", "LoginName", "DisplayName", "Email", "PermissionLevel", "IsGuest", "SharedDateTime", "SharedByDisplayName", "SharedByLoginName", "ViaGroup", "ViaGroupId", "ViaGroupType", "AssignmentType", "NestingLevel", "ParentGroup"]

# ----------------------------------------- END: Constants --------------------------------------------------------------------


# ----------------------------------------- START: CSV Functions --------------------------------------------------------------

def csv_escape(value, is_numeric: bool = False) -> str:
  """Escape value for CSV output, matching PowerShell scanner format.
  
  Args:
    value: The value to escape
    is_numeric: If True, don't quote even if empty (PowerShell doesn't quote numeric IDs)
  """
  if value is None: return ''
  value = str(value)
  if not value:
    return '' if is_numeric else '""'
  # Quote only if contains special chars (comma, quote, newline)
  if ',' in value or '"' in value or '\n' in value:
    return '"' + value.replace('"', '""') + '"'
  return value

# Columns that should not be quoted (numeric/boolean values)
NUMERIC_COLUMNS = {"Job", "Id", "NestingLevel", "IsGuest"}

def csv_row(row: dict, columns: list) -> str:
  """Convert dict to CSV row string with proper escaping."""
  parts = []
  for col in columns:
    val = row.get(col, '')
    is_numeric = col in NUMERIC_COLUMNS
    parts.append(csv_escape(val, is_numeric=is_numeric))
  return ','.join(parts)

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

def normalize_login_name(login_name: str) -> str:
  """Normalize login name to email format (strip claims prefix to match PowerShell scanner)."""
  if not login_name: return ""
  # Strip common claims prefixes: i:0#.f|membership|user@domain.com -> user@domain.com
  if login_name.startswith("i:0#.f|membership|"):
    return login_name[18:]  # len("i:0#.f|membership|") = 18
  # Strip other common prefixes
  if "|" in login_name and login_name.startswith("i:"):
    parts = login_name.split("|")
    if len(parts) >= 2:
      return parts[-1]
  return login_name

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
          "IsGuest": "false",
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
      is_guest = "true" if "#ext#" in login_name.lower() else "false"
      members.append({
        "Id": str(user.id) if user.id else "",
        "LoginName": normalize_login_name(login_name),
        "DisplayName": user.title or "",
        "Email": user.email or "",
        "IsGuest": is_guest,
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

async def scan_site_contents(ctx: ClientContext, output_folder: str, writer, logger: MiddlewareLogger, current_step: int, total_steps: int, settings: dict = None, site_url: str = "") -> AsyncGenerator[str, None]:
  """Scan lists/libraries and write 01_SiteContents.csv. Yields SSE events. Sets writer._step_result with stats."""
  stats = {"lists_scanned": 0}
  contents_file = os.path.join(output_folder, "01_SiteContents.csv")
  
  # Extract ignore_lists from settings and tenant URL
  if settings is None: settings = {}
  ignore_lists = set(settings.get("ignore_lists", []))
  tenant_url = site_url.split("/sites/")[0] if "/sites/" in site_url else site_url.rsplit("/", 1)[0]
  
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
    if lst.title in ignore_lists: continue
    
    stats["lists_scanned"] += 1
    
    # Type casing: List, Library, SitePages (match PowerShell)
    list_type = "List" if lst.base_template == 100 else "Library"
    if lst.base_template == 119: list_type = "SitePages"
    
    # Get root folder URL from expanded property - use full URL
    try:
      server_rel_url = lst.root_folder.properties.get("ServerRelativeUrl", "") if lst.root_folder else ""
      url = f"{tenant_url}{server_rel_url}" if server_rel_url else ""
    except:
      url = ""
    
    rows.append({
      "Job": 1,
      "SiteUrl": site_url,
      "Id": str(lst.id),
      "Type": list_type,
      "Title": lst.title,
      "Url": url
    })
  
  append_csv_rows(contents_file, rows, CSV_COLUMNS_SITE_CONTENTS)
  ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  yield writer.emit_log(f"[{ts}]   {stats['lists_scanned']} list(s)/libraries found.".replace("(s)", "s" if stats['lists_scanned'] != 1 else ""))
  writer._step_result = stats

async def scan_site_groups(ctx: ClientContext, storage_path: str, output_folder: str, graph_client: Optional[GraphServiceClient], writer, logger: MiddlewareLogger, current_step: int, total_steps: int, settings: dict = None, site_url: str = "", skip_users_csv: bool = False) -> AsyncGenerator[str, None]:
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
        is_guest = "true" if "#ext#" in login_name.lower() else "false"
        direct_user_rows.append({
          "Job": 1,
          "SiteUrl": site_url,
          "Id": str(member.id) if member.id else "",
          "LoginName": normalize_login_name(login_name),
          "DisplayName": member.title or "",
          "Email": member.email or "" if hasattr(member, 'email') else "",
          "PermissionLevel": perm_name,
          "IsGuest": is_guest,
          "ViaGroup": "",
          "ViaGroupId": "",
          "ViaGroupType": "",
          "AssignmentType": "User",
          "NestingLevel": 0,
          "ParentGroup": ""
        })
      elif member.principal_type == 4:  # Direct Security Group (Entra ID group) assignment
        login_name = member.login_name or ""
        # Skip ignored accounts from settings
        if any(ignored in login_name for ignored in ignore_accounts): continue
        group_display_name = member.title or ""
        # Check if group should not be resolved - add group entry but don't resolve members
        if group_display_name in do_not_resolve_these_groups:
          ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          yield writer.emit_log(f"[{ts}]       NOT resolving Entra group: '{group_display_name}' in do_not_resolve_these_groups (adding group entry)")
          direct_user_rows.append({
            "Job": 1,
            "SiteUrl": site_url,
            "Id": "",
            "LoginName": normalize_login_name(login_name),
            "DisplayName": group_display_name,
            "Email": "",
            "PermissionLevel": perm_name,
            "IsGuest": "false",
            "ViaGroup": "",
            "ViaGroupId": "",
            "ViaGroupType": "",
            "AssignmentType": "Group",
            "NestingLevel": 0,
            "ParentGroup": ""
          })
          continue
        # Resolve Entra ID group members if Graph client available
        if is_entra_id_group(login_name) and graph_client:
          group_id = extract_group_id_from_login(login_name)
          if group_id:
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            yield writer.emit_log(f"[{ts}]       Resolving Entra group '{group_display_name}' via Graph API...")
            nested_members = await resolve_entra_group_members(storage_path, graph_client, group_id, group_display_name, 1, "", writer, logger)
            for nm in nested_members:
              nm["Job"] = 1
              nm["SiteUrl"] = site_url
              nm["PermissionLevel"] = perm_name
              nm["ViaGroup"] = group_display_name
              nm["ViaGroupId"] = group_id
              nm["ViaGroupType"] = "EntraGroup"
              direct_user_rows.append(nm)
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            yield writer.emit_log(f"[{ts}]       OK. {len(nested_members)} member(s) resolved from '{group_display_name}'".replace("(s)", "s" if len(nested_members) != 1 else ""))
        else:
          # Can't resolve, add as-is
          direct_user_rows.append({
            "Job": 1,
            "SiteUrl": site_url,
            "Id": "",
            "LoginName": normalize_login_name(login_name),
            "DisplayName": group_display_name,
            "Email": "",
            "PermissionLevel": perm_name,
            "IsGuest": "false",
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
  
  # Track seen users to avoid duplicates (match PowerShell behavior)
  seen_users = set()
  for row in direct_user_rows:
    login = row.get("LoginName", "")
    if login: seen_users.add(login)
  
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
      "Job": 1,
      "SiteUrl": site_url,
      "Id": str(group.id),
      "Role": role,
      "Title": group.title,
      "PermissionLevel": perm_level,
      "Owner": group.owner_title or ""
    })
    
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    yield writer.emit_log(f"[{ts}]     ( {idx} / {total_groups} ) SharePointGroup: group_title='{group.title}'...")
    
    # Groups in do_not_resolve_these_groups: add group entry but don't resolve members
    if group.title in do_not_resolve_these_groups:
      ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      yield writer.emit_log(f"[{ts}]       NOT resolving members: Group in do_not_resolve_these_groups (adding group entry)")
      # Add the group itself as an entry (not resolved to individual members)
      user_rows.append({
        "Job": 1,
        "SiteUrl": site_url,
        "Id": "",
        "LoginName": group.title,  # Use group title as LoginName
        "DisplayName": group.title,
        "Email": "",
        "PermissionLevel": perm_level,
        "IsGuest": "false",
        "ViaGroup": "",
        "ViaGroupId": "",
        "ViaGroupType": "",
        "AssignmentType": "Group",
        "NestingLevel": 0,
        "ParentGroup": ""
      })
      stats["users_found"] += 1
      continue
    
    # Resolve members
    members = await resolve_sharepoint_group_members(ctx, group, storage_path, graph_client, writer, 1, "", logger, settings)
    for member in members:
      login_name = member.get("LoginName", "")
      # Skip duplicates (match PowerShell behavior)
      if login_name in seen_users:
        continue
      if login_name:
        seen_users.add(login_name)
      member["Job"] = 1
      member["SiteUrl"] = site_url
      member["PermissionLevel"] = perm_level
      stats["users_found"] += 1
      # Track external users (contain #ext# in login)
      if "#ext#" in login_name.lower():
        stats["external_users_found"] += 1
      user_rows.append(member)
  
  append_csv_rows(groups_file, group_rows, CSV_COLUMNS_SITE_GROUPS)
  if not skip_users_csv:
    append_csv_rows(users_file, user_rows, CSV_COLUMNS_SITE_USERS)
  
  ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  yield writer.emit_log(f"[{ts}]   {stats['groups_found']} group(s), {stats['users_found']} user(s) found.".replace("(s)", "s" if stats['groups_found'] != 1 else "", 1).replace("(s)", "s" if stats['users_found'] != 1 else "", 1))
  writer._step_result = stats

async def scan_broken_inheritance_items(ctx: ClientContext, storage_path: str, output_folder: str, graph_client: Optional[GraphServiceClient], writer, logger: MiddlewareLogger, current_step: int, total_steps: int, settings: dict = None, site_url: str = "") -> AsyncGenerator[str, None]:
  """Scan items with broken inheritance and write 04/05 CSVs. Yields SSE events. Sets writer._step_result with stats."""
  stats = {"items_scanned": 0, "items_with_individual_permissions": 0, "items_shared_with_everyone": 0}
  items_shared_with_everyone_items = set()  # Track unique items shared with everyone
  if settings is None: settings = {}
  tenant_url = site_url.split("/sites/")[0] if "/sites/" in site_url else site_url.rsplit("/", 1)[0]
  
  # Extract settings
  ignore_lists = set(settings.get("ignore_lists", []))
  ignore_permission_levels = set(settings.get("ignore_permission_levels", ["Limited Access"]))
  ignore_accounts = set(settings.get("ignore_accounts", []))
  do_not_resolve_these_groups = set(settings.get("do_not_resolve_these_groups", []))
  
  items_file = os.path.join(output_folder, "04_IndividualPermissionItems.csv")
  access_file = os.path.join(output_folder, "05_IndividualPermissionItemAccess.csv")
  
  # Only write headers when called from main scan (step > 0), not from subsite scanning
  if current_step > 0:
    write_csv_header(items_file, CSV_COLUMNS_INDIVIDUAL_ITEMS)
    write_csv_header(access_file, CSV_COLUMNS_INDIVIDUAL_ACCESS)
  
  ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  if current_step > 0:
    yield writer.emit_log(f"[{ts}] [ {current_step} / {total_steps} ] Scanning items with broken inheritance...")
  
  all_lists = ctx.web.lists.get().select(["Id", "Title", "BaseTemplate", "Hidden", "DefaultViewUrl"]).execute_query()
  
  # Debug: log all lists and why they pass/fail filtering
  ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  yield writer.emit_log(f"[{ts}]   DEBUG: Found {len(all_lists)} total lists, filtering...")
  for lst in all_lists:
    template = lst.base_template
    hidden = lst.properties.get("Hidden", False)
    title = lst.title
    in_ignore = title in ignore_lists
    passes = template in INCLUDED_TEMPLATES and not hidden and not in_ignore
    if not passes and template in INCLUDED_TEMPLATES:
      yield writer.emit_log(f"[{ts}]   DEBUG: SKIPPED '{title}' template={template} hidden={hidden} in_ignore={in_ignore}")
  
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
    
    # Try SDK first, fall back to REST API for large libraries (>5000 items)
    last_id = 0
    batch_num = 0
    list_items_with_perms = []  # Items with broken permissions (as dicts)
    use_rest_api = False
    
    while True:
      try:
        items = lst.items.filter(f"ID gt {last_id}").select(
          ["ID", "FileRef", "FileLeafRef", "FSObjType", "HasUniqueRoleAssignments"]
        ).top(BATCH_SIZE).get().execute_query()
        
        if len(items) == 0: break
        
        batch_num += 1
        for item in items:
          stats["items_scanned"] += 1
          if item.properties.get("HasUniqueRoleAssignments"):
            list_items_with_perms.append({
              "ID": item.properties.get("ID"),
              "FileRef": item.properties.get("FileRef", ""),
              "FileLeafRef": item.properties.get("FileLeafRef", ""),
              "FSObjType": item.properties.get("FSObjType", 0),
              "sdk_item": item  # Keep SDK item reference for role assignments
            })
          last_id = item.properties.get("ID", 0)
        
        if batch_num % 2 == 0:
          ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          yield writer.emit_log(f"[{ts}]       Scanned {stats['items_scanned']} items, {len(list_items_with_perms)} with broken permissions...")
        
        if len(items) < BATCH_SIZE: break
        
      except Exception as e:
        error_str = str(e)
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if "SPQueryThrottledException" in error_str or "list view threshold" in error_str.lower():
          yield writer.emit_log(f"[{ts}]       SDK throttled - switching to REST API for large library...")
          use_rest_api = True
        else:
          yield writer.emit_log(f"[{ts}]   ERROR: Failed to get items from '{lst.title}' -> {e}")
        break
    
    # If SDK was throttled, use REST API with odata.nextLink pagination via SDK's request mechanism
    if use_rest_api:
      from office365.runtime.http.request_options import RequestOptions
      list_items_with_perms = []  # Reset
      stats["items_scanned"] -= batch_num * BATCH_SIZE  # Adjust count
      batch_num = 0
      
      site_url = ctx.web.url
      list_id = lst.id
      next_url = f"{site_url}/_api/web/lists(guid'{list_id}')/items?$select=ID,FileRef,FileLeafRef,FSObjType,HasUniqueRoleAssignments&$top=5000"
      
      while next_url:
        try:
          # Use SDK's authenticated request mechanism
          request = RequestOptions(next_url)
          request.set_header("Accept", "application/json;odata=verbose")
          response = ctx.pending_request().execute_request_direct(request)
          
          if response.status_code != 200:
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            yield writer.emit_log(f"[{ts}]   ERROR: REST API returned {response.status_code}")
            break
          
          data = response.json()
          items_data = data.get("d", {}).get("results", [])
          
          for item_data in items_data:
            stats["items_scanned"] += 1
            if item_data.get("HasUniqueRoleAssignments"):
              list_items_with_perms.append({
                "ID": item_data.get("ID"),
                "FileRef": item_data.get("FileRef", ""),
                "FileLeafRef": item_data.get("FileLeafRef", ""),
                "FSObjType": item_data.get("FSObjType", 0),
                "sdk_item": None  # Will fetch SDK item when needed
              })
          
          batch_num += 1
          if batch_num % 2 == 0:
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            yield writer.emit_log(f"[{ts}]       REST: Fetched {stats['items_scanned']} items, {len(list_items_with_perms)} with broken permissions...")
          
          # Handle pagination
          next_link = data.get("d", {}).get("__next", "")
          next_url = next_link if next_link else None
          
        except Exception as e:
          ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          yield writer.emit_log(f"[{ts}]   ERROR: REST API failed -> {e}")
          break
      
      ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      yield writer.emit_log(f"[{ts}]       REST API complete: {len(list_items_with_perms)} items with broken permissions")
    
    if len(list_items_with_perms) == 0:
      continue  # Skip to next list
    
    # Process items with broken permissions
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    yield writer.emit_log(f"[{ts}]       Found {len(list_items_with_perms)} items with broken permissions")
    
    for item_data in list_items_with_perms:
      stats["items_with_individual_permissions"] += 1
      item_id = item_data.get("ID", 0)
      file_ref = item_data.get("FileRef", "")
      file_name = item_data.get("FileLeafRef", "")
      fs_obj_type = item_data.get("FSObjType", 0)
      sdk_item = item_data.get("sdk_item")  # May be None for REST API items
      
      # Match PowerShell scanner Type values: File, Folder, Item
      if fs_obj_type == 1:
        item_type = "Folder"
      elif lst.base_template == 101:  # Document Library
        item_type = "File"
      else:
        item_type = "Item"
      
      # Build full URL - PowerShell uses different formats for lists vs libraries
      if lst.base_template == 100:  # List - use DefaultViewUrl with filter
        default_view_url = lst.properties.get("DefaultViewUrl", "") or ""
        if not default_view_url:
          default_view_url = file_ref  # Fallback to FileRef
        full_url = f"{tenant_url}{default_view_url}?FilterField1=ID&FilterValue1={item_id}"
      else:  # Library/SitePages - use FileRef
        full_url = f"{tenant_url}{file_ref}" if file_ref.startswith("/") else file_ref
      
      item_rows.append({
        "Job": 1,
        "SiteUrl": site_url,
        "Id": str(item_id),
        "Type": item_type,
        "Title": file_name,
        "Url": full_url
      })
      
      # Get role assignments for this item
      try:
        # For REST API items, fetch SDK item first
        if sdk_item is None:
          sdk_item = lst.items.get_by_id(item_id)
        role_assignments = sdk_item.role_assignments.get()
        role_assignments.expand(["Member", "RoleDefinitionBindings"]).execute_query()
        ra_list = list(role_assignments)
        
        for ra in ra_list:
          member = ra.member
          bindings_list = list(ra.role_definition_bindings) if ra.role_definition_bindings else []
          for binding in bindings_list:
            perm_name = binding.properties.get('Name', '')
            if perm_name == "Limited Access": continue
            
            member_title = member.title or ""
            if "Everyone except external users" in member_title:
              items_shared_with_everyone_items.add(item_id)
            
            # Skip groups that should not be resolved (match PowerShell behavior)
            if member_title in do_not_resolve_these_groups:
              continue
            
            login_name = member.login_name or ""
            is_guest = "true" if "#ext#" in login_name.lower() else "false"
            access_rows.append({
              "Job": 1,
              "SiteUrl": site_url,
              "Id": str(item_id),
              "Type": item_type,
              "Url": full_url,
              "LoginName": normalize_login_name(login_name),
              "DisplayName": member_title,
              "Email": member.email or "" if hasattr(member, 'email') else "",
              "PermissionLevel": perm_name,
              "IsGuest": is_guest,
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
    
    # Get parent site URL for Job/SiteUrl columns
    parent_site_url = parent_ctx.web.url
    
    # Add subsite to 01_SiteContents.csv
    append_csv_rows(contents_file, [{
      "Job": 1,
      "SiteUrl": parent_site_url,
      "Id": str(subsite_id),
      "Type": "Subsite",
      "Title": subsite_title,
      "Url": subsite_url
    }], CSV_COLUMNS_SITE_CONTENTS)
    
    # Check if subsite has broken inheritance - add to 04_IndividualPermissionItems.csv
    has_unique = subweb.properties.get("HasUniqueRoleAssignments", False)
    if has_unique:
      items_file = os.path.join(output_folder, "04_IndividualPermissionItems.csv")
      append_csv_rows(items_file, [{
        "Job": 1,
        "SiteUrl": parent_site_url,
        "Id": str(subsite_id),
        "Type": "Subsite",
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
      async for sse in scan_site_contents(sub_ctx, output_folder, writer, logger, 0, 0, settings, site_url=parent_site_url):
        pass  # Execute generator but don't yield SSE events for subsite scanning
      
      # Scan subsite groups (skip_users_csv=True to match PowerShell - only main site users in 03_SiteUsers.csv)
      async for sse in scan_site_groups(sub_ctx, storage_path, output_folder, graph_client, writer, logger, 0, 0, settings, site_url=parent_site_url, skip_users_csv=True):
        pass  # Execute generator but don't yield SSE events for subsite scanning
      group_stats = writer._step_result or {"groups_found": 0, "users_found": 0, "external_users_found": 0}
      stats["groups_found"] += group_stats["groups_found"]
      stats["users_found"] += group_stats["users_found"]
      stats["external_users_found"] += group_stats.get("external_users_found", 0)
      
      # Scan subsite broken inheritance items
      ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      writer.emit_log(f"[{ts}]     Scanning subsite items with broken inheritance...")
      async for sse in scan_broken_inheritance_items(sub_ctx, storage_path, output_folder, graph_client, writer, logger, 0, 0, settings, site_url=parent_site_url):
        pass  # Execute generator but don't yield SSE events for subsite scanning
      item_stats = writer._step_result or {"items_scanned": 0, "items_with_individual_permissions": 0}
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
      async for sse in scan_site_contents(ctx, output_folder, writer, logger, current_step, total_steps, settings, site_url=site_url):
        yield sse
      content_stats = writer._step_result or {}
      stats["lists_scanned"] = content_stats.get("lists_scanned", 0)
    
    if scope in ["all", "site"]:
      current_step += 1
      async for sse in scan_site_groups(ctx, storage_path, output_folder, graph_client, writer, logger, current_step, total_steps, settings, site_url=site_url):
        yield sse
      group_stats = writer._step_result or {}
      stats["groups_found"] = group_stats.get("groups_found", 0)
      stats["users_found"] = group_stats.get("users_found", 0)
      stats["external_users_found"] = group_stats.get("external_users_found", 0)
    
    if scope in ["all", "items"]:
      current_step += 1
      async for sse in scan_broken_inheritance_items(ctx, storage_path, output_folder, graph_client, writer, logger, current_step, total_steps, settings, site_url=site_url):
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
      stats["subsites_scanned"] += subsite_stats["subsites_scanned"]
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
