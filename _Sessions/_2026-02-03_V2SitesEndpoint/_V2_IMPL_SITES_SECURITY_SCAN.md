# IMPL: Sites Security Scan

**Doc ID**: SCAN-IP01
**Goal**: Implement security scan endpoint for scanning SharePoint site permissions and generating CSV reports.
**Timeline**: Created 2026-02-03, Updated 2 times (2026-02-03 - 2026-02-03)
**Target files**:
- `src/routers_v2/sites.py` (EXTEND +400 lines)
- `src/routers_v2/common_security_scan_functions_v2.py` (NEW ~600 lines)

**Depends on:**
- `_V2_SPEC_SITES_SECURITY_SCAN.md [SITE-SP03]` for functional requirements
- `_V2_SPEC_REPORTS.md` for report archive creation
- `_POC_PERMISSION_SCANNER_RESULTS.md [PSCP-RS01]` for validated API patterns

## MUST-NOT-FORGET

- CSV output MUST match PowerShell scanner format exactly (column order, escaping, UTF-8 no BOM)
- Use `ID gt {last_id}` for pagination, NOT `skip()` (SharePoint ignores skip)
- Entra ID group resolution max 5 levels to prevent infinite loops
- Filter out "Limited Access" permission level
- Entra ID cache in `_entra_group_cache/` folder (underscore prefix = ignored by sites list)
- SharePoint groups NOT cached (resolved fresh each scan)
- Honor 429 throttling with Retry-After and exponential backoff
- Load `security_scan_settings.json` before scan; create with defaults if missing

## Table of Contents

1. [File Structure](#1-file-structure)
2. [Edge Cases](#2-edge-cases)
3. [Implementation Steps](#3-implementation-steps)
4. [Test Cases](#4-test-cases)
5. [Verification Checklist](#5-verification-checklist)
6. [Document History](#6-document-history)

## 1. File Structure

```
src/routers_v2/
├── sites.py                              # [EXTEND +400 lines] Add security_scan endpoint + JS
├── common_security_scan_functions_v2.py  # [NEW ~600 lines] Core scanning logic
└── common_report_functions_v2.py         # [EXISTING] Use create_report_archive()

PERSISTENT_STORAGE_PATH/
├── sites/
│   ├── _entra_group_cache/               # [NEW] Entra ID group member cache
│   │   └── {group_id}.json               # One file per group
│   ├── security_scan_settings.json       # [NEW] Scanner settings (see SPEC Section 9)
│   └── {site_id}/
│       └── site.json                     # Updated with security_scan_result
└── reports/
    └── site_scans/                       # [NEW] Security scan reports
        └── {timestamp}_{site_id}_security.zip
```

## 2. Edge Cases

### Input Validation

- **SCAN-IP01-EC-01**: Missing site_id -> Return 400 "Missing 'site_id' parameter"
- **SCAN-IP01-EC-02**: Non-existent site_id -> Return 404 "Site not found"
- **SCAN-IP01-EC-03**: Invalid scope value -> Return 400 "Invalid scope. Use: all, site, lists, items"

### SharePoint Connectivity

- **SCAN-IP01-EC-04**: Site connection fails -> Emit error event, abort scan
- **SCAN-IP01-EC-05**: Authentication expired mid-scan -> Attempt reconnect, fail after 3 retries
- **SCAN-IP01-EC-06**: 429 throttling response -> Honor Retry-After header, exponential backoff

### Data Anomalies

- **SCAN-IP01-EC-07**: Empty site (no groups, no lists) -> Generate valid CSVs with headers only
- **SCAN-IP01-EC-08**: Group with circular reference -> Skip and log warning after max nesting
- **SCAN-IP01-EC-09**: Item access denied -> Log warning, continue with other items
- **SCAN-IP01-EC-10**: Corrupt group member data -> Skip member, log warning

### Cache Operations

- **SCAN-IP01-EC-11**: Cache folder doesn't exist -> Create on first write
- **SCAN-IP01-EC-12**: Corrupt cache file -> Delete and re-fetch from API
- **SCAN-IP01-EC-13**: delete_caches with no cache folder -> Succeed silently

### Cancellation

- **SCAN-IP01-EC-14**: User cancels mid-scan -> Clean up temp files, no report created
- **SCAN-IP01-EC-15**: Connection lost mid-stream -> Job marked failed, partial data discarded

## 3. Implementation Steps

### SCAN-IP01-IS-01: Create common_security_scan_functions_v2.py

**Location**: `src/routers_v2/common_security_scan_functions_v2.py` (NEW)

**Action**: Create new module with core scanning functions

**Note**: Office365-REST-Python-Client is synchronous. The `execute_query()` method blocks. This is acceptable for SSE streaming - progress events are yielded between blocking API calls. Do not attempt async wrappers unless performance issues are observed.

**Structure**:
```python
# Imports
from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext
from msgraph import GraphServiceClient  # For Entra ID group resolution
# ... other imports

# Constants
MAX_NESTING_LEVEL = 5
BATCH_SIZE = 5000
PROGRESS_INTERVAL_SECONDS = 5

# CSV Column Definitions (EXACT order from SPEC Section 14 - must match PowerShell)
CSV_COLUMNS_SITE_CONTENTS = ["Id", "Type", "Title", "Url"]
CSV_COLUMNS_SITE_GROUPS = ["Id", "Role", "Title", "PermissionLevel", "Owner"]
CSV_COLUMNS_SITE_USERS = ["Id", "LoginName", "DisplayName", "Email", "PermissionLevel", "ViaGroup", "ViaGroupId", "ViaGroupType", "AssignmentType", "NestingLevel", "ParentGroup"]
CSV_COLUMNS_INDIVIDUAL_ITEMS = ["Id", "Type", "Title", "Url"]
CSV_COLUMNS_INDIVIDUAL_ACCESS = ["Id", "Type", "Url", "LoginName", "DisplayName", "Email", "PermissionLevel", "SharedDateTime", "SharedByDisplayName", "SharedByLoginName", "ViaGroup", "ViaGroupId", "ViaGroupType", "AssignmentType", "NestingLevel", "ParentGroup"]

# Settings Functions
def get_default_scanner_settings() -> dict: ...
def load_scanner_settings(storage_path: str) -> dict: ...
def save_scanner_settings(storage_path: str, settings: dict) -> None: ...

# Cache Functions
def get_entra_cache_folder(storage_path: str) -> str: ...
def load_entra_group_cache(storage_path: str, group_id: str) -> dict | None: ...
def save_entra_group_cache(storage_path: str, group_id: str, data: dict) -> None: ...
def delete_all_entra_caches(storage_path: str) -> int: ...

# CSV Functions
def csv_escape(value: str) -> str: ...
def write_csv_header(file_path: str, columns: list) -> None: ...
def append_csv_rows(file_path: str, rows: list[dict], columns: list) -> None: ...

# SharePoint Connection
def connect_to_sharepoint(site_url: str, client_id: str, client_secret: str, tenant: str) -> ClientContext: ...

# Group Resolution
def is_entra_id_group(member) -> bool: ...
def resolve_sharepoint_group_members(ctx, group, nesting_level=1, parent_group="") -> list: ...
def resolve_entra_group_members(storage_path, group_id, nesting_level, parent_group) -> list: ...

# Scanning Functions
def scan_site_groups(ctx, storage_path, output_folder, writer) -> dict: ...
def scan_site_contents(ctx, output_folder, writer) -> dict: ...
def scan_broken_inheritance_items(ctx, output_folder, writer) -> dict: ...

# Main Scanner
async def run_security_scan(params: dict, writer: StreamingJobWriter) -> AsyncGenerator: ...
```

### SCAN-IP01-IS-02: Implement CSV escaping function

**Location**: `common_security_scan_functions_v2.py` > `csv_escape()`

**Action**: Add CSV escape function matching PowerShell scanner

**Code**:
```python
import re

def csv_escape(value) -> str:
    """Escape value for CSV output, matching PowerShell scanner format (SPEC Section 9)."""
    if value is None:
        return ''
    value = str(value)
    if not value:
        return '""'
    # Match SPEC regex exactly: formula chars, date/number patterns, or special chars
    if re.match(r'^([+\-=\/]*[\.\d\s\/\:]*|.*[\,\"\n].*|[\n]*)$', value):
        return '"' + value.replace('"', '""') + '"'
    return value
```

### SCAN-IP01-IS-03: Implement Entra ID group cache functions

**Location**: `common_security_scan_functions_v2.py` > cache functions

**Action**: Add cache read/write/delete functions

**Code**:
```python
def get_entra_cache_folder(storage_path: str) -> str:
    return os.path.join(storage_path, 
        CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_SITES_SUBFOLDER,
        "_entra_group_cache")

def load_entra_group_cache(storage_path: str, group_id: str) -> dict | None:
    cache_path = os.path.join(get_entra_cache_folder(storage_path), f"{group_id}.json")
    if not os.path.exists(cache_path):
        return None
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def save_entra_group_cache(storage_path: str, group_id: str, data: dict) -> None:
    cache_folder = get_entra_cache_folder(storage_path)
    os.makedirs(cache_folder, exist_ok=True)
    cache_path = os.path.join(cache_folder, f"{group_id}.json")
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def delete_all_entra_caches(storage_path: str) -> int:
    cache_folder = get_entra_cache_folder(storage_path)
    if not os.path.exists(cache_folder):
        return 0
    count = 0
    for f in os.listdir(cache_folder):
        if f.endswith('.json'):
            os.remove(os.path.join(cache_folder, f))
            count += 1
    return count
```

### SCAN-IP01-IS-04: Implement Scanner Settings Functions

**Location**: `common_security_scan_functions_v2.py` > settings functions

**Action**: Add settings load/save functions with defaults

**Code**:
```python
SCANNER_SETTINGS_FILENAME = "security_scan_settings.json"

def get_default_scanner_settings() -> dict:
    """Return default scanner settings matching PowerShell scanner configuration.
    See SPEC Section 9 'Scanner Settings Configuration' for full schema."""
    return {
        "do_not_resolve_these_groups": [...],  # See SPEC for defaults
        "ignore_accounts": [...],
        "ignore_permission_levels": ["Limited Access"],
        "ignore_sharepoint_groups": [],
        "max_group_nesting_level": 5,
        "built_in_lists": [...],  # 48 system lists - see SPEC
        "fields_to_load": ["SharedWithUsers", "SharedWithDetails"],
        "ignore_fields": [...],  # 47 system fields - see SPEC
        "output_columns": [...]  # 13 columns - see SPEC
    }

def get_scanner_settings_path(storage_path: str) -> str:
    """Get path to scanner settings file."""
    return os.path.join(storage_path, 
        CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_SITES_SUBFOLDER,
        SCANNER_SETTINGS_FILENAME)

def load_scanner_settings(storage_path: str) -> dict:
    """Load scanner settings from file; create with defaults if missing."""
    settings_path = get_scanner_settings_path(storage_path)
    if not os.path.exists(settings_path):
        defaults = get_default_scanner_settings()
        save_scanner_settings(storage_path, defaults)
        return defaults
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        # Invalid JSON - log warning and return defaults
        return get_default_scanner_settings()

def save_scanner_settings(storage_path: str, settings: dict) -> None:
    """Save scanner settings to file."""
    settings_path = get_scanner_settings_path(storage_path)
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2)
```

### SCAN-IP01-IS-05: Implement SharePoint connection function

**Location**: `common_security_scan_functions_v2.py` > `connect_to_sharepoint()`

**Action**: Add connection function using Office365-REST-Python-Client

**Code**:
```python
def connect_to_sharepoint(site_url: str, client_id: str, client_secret: str, tenant: str) -> ClientContext:
    """Connect to SharePoint site using app-only authentication."""
    credentials = ClientCredential(client_id, client_secret)
    ctx = ClientContext(site_url).with_credentials(credentials)
    # Test connection
    web = ctx.web.get().execute_query()
    return ctx
```

### SCAN-IP01-IS-04B: Initialize Microsoft Graph client for Entra ID resolution

**Location**: `common_security_scan_functions_v2.py` > `get_graph_client()`

**Action**: Add Graph client initialization for Entra ID group member resolution

**Code**:
```python
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient

_graph_client = None

def get_graph_client(tenant_id: str, client_id: str, client_secret: str) -> GraphServiceClient:
    """Get or create Graph client for Entra ID group resolution."""
    global _graph_client
    if _graph_client is None:
        credential = ClientSecretCredential(tenant_id, client_id, client_secret)
        _graph_client = GraphServiceClient(credential)
    return _graph_client

def resolve_entra_group_members(storage_path: str, group_id: str, nesting_level: int, parent_group: str) -> list:
    """Resolve Entra ID group members using Graph API with caching."""
    if nesting_level > MAX_NESTING_LEVEL:
        return []
    
    # Check cache first
    cached = load_entra_group_cache(storage_path, group_id)
    if cached:
        return cached.get("members", [])
    
    # Fetch from Graph API using transitive members (async SDK)
    graph_client = get_graph_client(...)  # Pass credentials from config
    members_response = await graph_client.groups.by_group_id(group_id).transitive_members.get()
    
    members = []
    for member in members_response.value:
        if member.odata_type == "#microsoft.graph.user":
            members.append({
                "login_name": member.user_principal_name,
                "display_name": member.display_name,
                "email": member.mail or "",
                "nesting_level": nesting_level,
                "parent_group": parent_group,
                "via_group_id": group_id,
                "via_group_type": "SecurityGroup"
            })
    
    # Cache result
    save_entra_group_cache(storage_path, group_id, {
        "group_id": group_id,
        "cached_utc": datetime.utcnow().isoformat() + "Z",
        "member_count": len(members),
        "members": members
    })
    
    return members
```

**Note**: Requires `GroupMember.Read.All` permission. Use same app registration as SharePoint or separate Graph-only app.

### SCAN-IP01-IS-05: Implement group resolution functions

**Location**: `common_security_scan_functions_v2.py` > group resolution

**Action**: Add functions to resolve SP and Entra ID group members

**Code**:
```python
def is_entra_id_group(member) -> bool:
    """Check if member is an Entra ID (Azure AD) group."""
    login_name = member.login_name or ""
    # Entra ID groups have c:0t.c|tenant|{guid} or c:0-.f|rolemanager|{guid} format
    return "|" in login_name and ("c:0t.c" in login_name or "c:0-.f" in login_name)

def extract_group_id_from_login(login_name: str) -> str | None:
    """Extract Entra ID group GUID from login name."""
    # Format: c:0t.c|tenant|{guid} or similar
    parts = login_name.split("|")
    if len(parts) >= 3:
        return parts[-1]
    return None

def resolve_sharepoint_group_members(ctx, group, storage_path, nesting_level=1, parent_group="") -> list:
    """Resolve all members of a SharePoint group, including nested Entra ID groups."""
    if nesting_level > MAX_NESTING_LEVEL:
        return []
    
    members = []
    group.users.get().execute_query()
    
    for user in group.users:
        if is_entra_id_group(user):
            group_id = extract_group_id_from_login(user.login_name)
            if group_id:
                nested = resolve_entra_group_members(
                    storage_path, group_id, nesting_level + 1, group.title)
                members.extend(nested)
        else:
            members.append({
                "login_name": user.login_name,
                "display_name": user.title,
                "email": user.email or "",
                "nesting_level": nesting_level,
                "parent_group": parent_group,
                "via_group": group.title,
                "via_group_id": str(group.id),
                "via_group_type": "SharePointGroup"
            })
    return members
```

### SCAN-IP01-IS-06: Implement site groups scanning

**Location**: `common_security_scan_functions_v2.py` > `scan_site_groups()`

**Action**: Add function to scan site groups and write CSVs

**Code**:
```python
async def scan_site_groups(ctx, storage_path, output_folder, writer) -> dict:
    """Scan site groups and write 02_SiteGroups.csv and 03_SiteUsers.csv."""
    stats = {"groups_found": 0, "users_found": 0}
    
    groups_file = os.path.join(output_folder, "02_SiteGroups.csv")
    users_file = os.path.join(output_folder, "03_SiteUsers.csv")
    
    write_csv_header(groups_file, CSV_COLUMNS_SITE_GROUPS)
    write_csv_header(users_file, CSV_COLUMNS_SITE_USERS)
    
    # Load site groups with role assignments to get permission levels (POC TC-06 pattern)
    role_assignments = ctx.web.role_assignments.get().expand(
        ["Member", "RoleDefinitionBindings"]).execute_query()
    
    # Build group -> permission level mapping
    group_permissions = {}
    for ra in role_assignments:
        member = ra.member
        for binding in ra.role_definition_bindings:
            perm_name = binding.properties.get('Name', '')
            # FILTER: Skip "Limited Access" per MUST-NOT-FORGET
            if perm_name == "Limited Access":
                continue
            if member.principal_type == 8:  # SharePoint Group
                group_permissions[member.id] = perm_name
    
    # Load all site groups
    groups = ctx.web.site_groups.get().execute_query()
    
    group_rows = []
    user_rows = []
    
    for group in groups:
        # Skip if group only has Limited Access (filtered out above)
        perm_level = group_permissions.get(group.id, "")
        if not perm_level:
            continue
        
        stats["groups_found"] += 1
        
        # Determine role
        role = "Custom"
        if "Owner" in group.title:
            role = "SiteOwners"
        elif "Member" in group.title:
            role = "SiteMembers"
        elif "Visitor" in group.title:
            role = "SiteVisitors"
        
        group_rows.append({
            "Id": group.id,
            "Role": role,
            "Title": group.title,
            "PermissionLevel": perm_level,
            "Owner": group.owner_title or ""
        })
        
        # Resolve members
        members = resolve_sharepoint_group_members(ctx, group, storage_path)
        for member in members:
            member["PermissionLevel"] = perm_level  # Add permission level to member
            stats["users_found"] += 1
            user_rows.append(member)
        
        # Emit progress
        yield writer.emit_progress(f"Resolving group '{group.title}'...", stats["groups_found"])
    
    append_csv_rows(groups_file, group_rows, CSV_COLUMNS_SITE_GROUPS)
    append_csv_rows(users_file, user_rows, CSV_COLUMNS_SITE_USERS)
    
    return stats
```

**Note**: Uses `$expand` pattern from POC TC-06 to get permission level names. Filters out "Limited Access" entries per MUST-NOT-FORGET.

### SCAN-IP01-IS-07: Implement list/library scanning

**Location**: `common_security_scan_functions_v2.py` > `scan_site_contents()`

**Action**: Add function to enumerate lists and write 01_SiteContents.csv

**Code**:
```python
# Built-in list templates to include
INCLUDED_TEMPLATES = [100, 101, 119]  # Generic List, Document Library, Site Pages

async def scan_site_contents(ctx, output_folder, writer) -> dict:
    """Scan lists/libraries and write 01_SiteContents.csv."""
    stats = {"lists_scanned": 0}
    
    contents_file = os.path.join(output_folder, "01_SiteContents.csv")
    write_csv_header(contents_file, CSV_COLUMNS_SITE_CONTENTS)
    
    lists = ctx.web.lists.get().execute_query()
    
    rows = []
    for lst in lists:
        if lst.base_template not in INCLUDED_TEMPLATES:
            continue
        if lst.hidden:
            continue
        
        stats["lists_scanned"] += 1
        
        list_type = "LIST" if lst.base_template == 100 else "LIBRARY"
        if lst.base_template == 119:
            list_type = "SITEPAGES"
        
        rows.append({
            "Id": lst.id,
            "Type": list_type,
            "Title": lst.title,
            "Url": lst.root_folder.server_relative_url
        })
    
    append_csv_rows(contents_file, rows, CSV_COLUMNS_SITE_CONTENTS)
    return stats
```

### SCAN-IP01-IS-08: Implement broken inheritance item scanning

**Location**: `common_security_scan_functions_v2.py` > `scan_broken_inheritance_items()`

**Action**: Add function to find and scan items with broken inheritance

**Code**:
```python
async def scan_broken_inheritance_items(ctx, storage_path, output_folder, writer) -> dict:
    """Scan items with broken inheritance and write 04/05 CSVs."""
    stats = {"items_scanned": 0, "broken_inheritance": 0}
    
    items_file = os.path.join(output_folder, "04_IndividualPermissionItems.csv")
    access_file = os.path.join(output_folder, "05_IndividualPermissionItemAccess.csv")
    
    write_csv_header(items_file, CSV_COLUMNS_INDIVIDUAL_ITEMS)
    write_csv_header(access_file, CSV_COLUMNS_INDIVIDUAL_ACCESS)
    
    lists = ctx.web.lists.get().execute_query()
    
    for lst in lists:
        if lst.base_template not in INCLUDED_TEMPLATES or lst.hidden:
            continue
        
        # Paginate through items
        last_id = 0
        while True:
            items = lst.items.get().filter(f"ID gt {last_id}").select(
                ["ID", "FileRef", "FileLeafRef", "FSObjType", "HasUniqueRoleAssignments"]
            ).top(BATCH_SIZE).execute_query()
            
            if not items:
                break
            
            for item in items:
                stats["items_scanned"] += 1
                
                if item.properties.get("HasUniqueRoleAssignments"):
                    stats["broken_inheritance"] += 1
                    # Process broken item... (write to CSVs)
            
            last_id = max(item.properties.get("ID") for item in items)
            
            yield writer.emit_progress(
                f"Scanning items [{stats['items_scanned']}]...",
                progress=50 + (stats["items_scanned"] % 50),
                items_scanned=stats["items_scanned"],
                broken_found=stats["broken_inheritance"]
            )
    
    return stats
```

### SCAN-IP01-IS-08B: Implement subsite scanning

**Location**: `common_security_scan_functions_v2.py` > `scan_subsites()`

**Action**: Add function to recursively scan subsites when include_subsites=true

**Code**:
```python
async def scan_subsites(ctx, storage_path, output_folder, writer, depth=0) -> dict:
    """Recursively scan subsites if include_subsites=true."""
    stats = {"subsites_scanned": 0}
    
    if depth > 5:  # Max subsite depth
        return stats
    
    webs = ctx.web.webs.get().execute_query()
    
    for subweb in webs:
        stats["subsites_scanned"] += 1
        
        # Add to 01_SiteContents.csv
        append_csv_rows(os.path.join(output_folder, "01_SiteContents.csv"), [{
            "Id": subweb.id,
            "Type": "SUBSITE",
            "Title": subweb.title,
            "Url": subweb.url
        }], CSV_COLUMNS_SITE_CONTENTS)
        
        # Create new context for subsite
        sub_ctx = ClientContext(subweb.url).with_credentials(ctx.credentials)
        
        # Scan subsite groups and items
        yield writer.emit_progress(f"Scanning subsite '{subweb.title}'...")
        async for sse in scan_site_groups(sub_ctx, storage_path, output_folder, writer):
            yield sse
        async for sse in scan_broken_inheritance_items(sub_ctx, storage_path, output_folder, writer):
            yield sse
        
        # Recurse into sub-subsites
        async for sse in scan_subsites(sub_ctx, storage_path, output_folder, writer, depth + 1):
            yield sse
    
    return stats
```

### SCAN-IP01-IS-09: Implement main security_scan endpoint

**Location**: `sites.py` > add new endpoint

**Action**: Add GET /v2/sites/security_scan endpoint

**Code**:
```python
@router.get(f"/{router_name}/security_scan")
async def sites_security_scan(request: Request):
    """
    Scan SharePoint site permissions.
    
    Parameters:
    - site_id: Site to scan (required)
    - scope: all (default), site, lists, items
    - include_subsites: true/false (default: false)
    - delete_caches: true/false (default: false)
    - format: stream (required)
    """
    # Implementation uses StreamingJobWriter and common_security_scan_functions_v2
    ...
```

### SCAN-IP01-IS-10: Add Security Scan dialog JavaScript

**Location**: `sites.py` > `get_router_specific_js()`

**Action**: Add showSecurityScanDialog() function

**Code**:
```javascript
function showSecurityScanDialog(siteId) {
    const body = document.querySelector('#modal .modal-body');
    body.innerHTML = `
        <div class="modal-header"><h3>Security Scan: ${escapeHtml(siteId)}</h3></div>
        <div class="modal-scroll">
            <form id="security-scan-form" onsubmit="return startSecurityScan(event)">
                <input type="hidden" name="site_id" value="${escapeHtml(siteId)}">
                <div class="form-group">
                    <label>Scope</label>
                    <select name="scope" onchange="updateSecurityScanPreview()">
                        <option value="all" selected>All (site + lists + items)</option>
                        <option value="site">Site only (groups, users)</option>
                        <option value="lists">Site + Lists</option>
                        <option value="items">Items with broken inheritance</option>
                    </select>
                </div>
                <div class="form-group">
                    <label><input type="checkbox" name="include_subsites" onchange="updateSecurityScanPreview()"> Include subsites</label>
                </div>
                <div class="form-group">
                    <label><input type="checkbox" name="delete_caches" onchange="updateSecurityScanPreview()"> Delete cached Entra ID group members</label>
                </div>
                <div class="form-group">
                    <label>Endpoint Preview:</label>
                    <pre id="security-scan-preview" style="background: #f5f5f5; padding: 8px;">...</pre>
                </div>
            </form>
        </div>
        <div class="modal-footer">
            <button type="submit" form="security-scan-form" class="btn-primary">OK</button>
            <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
        </div>
    `;
    openModal('600px');
    updateSecurityScanPreview();
}

function updateSecurityScanPreview() { ... }
function startSecurityScan(event) { ... }
```

### SCAN-IP01-IS-11: Update action buttons in sites UI

**Location**: `sites.py` > `sites_root()` columns definition

**Action**: Change Security Scan button from disabled placeholder to functional

**Code**:
```python
{"text": "Security Scan", "onclick": "showSecurityScanDialog(\"{itemId}\")", "class": "btn-small btn-primary"}
```

### SCAN-IP01-IS-12: Implement security_scan selftest endpoint

**Location**: `sites.py` > add selftest endpoint

**Action**: Add GET /v2/sites/security_scan/selftest

**Code**:
```python
@router.get(f"/{router_name}/security_scan/selftest")
async def sites_security_scan_selftest(request: Request):
    """
    Self-test for security scan functionality.
    Requires: CRAWLER_SELFTEST_SHAREPOINT_SITE environment variable
    """
    # TC-01 through TC-07 as specified
    ...
```

### SCAN-IP01-IS-13: Create report archive on completion

**Location**: `common_security_scan_functions_v2.py` > `run_security_scan()`

**Action**: Use `create_report()` from `common_report_functions_v2.py` to package results

**Code**:
```python
from routers_v2.common_report_functions_v2 import create_report

# At end of scan - read CSV files as bytes
def read_file_bytes(path: str) -> bytes:
    with open(path, 'rb') as f:
        return f.read()

# Build files list: (archive_path, content_bytes)
files = [
    ("01_SiteContents.csv", read_file_bytes(contents_csv_path)),
    ("02_SiteGroups.csv", read_file_bytes(groups_csv_path)),
    ("03_SiteUsers.csv", read_file_bytes(users_csv_path)),
    ("04_IndividualPermissionItems.csv", read_file_bytes(items_csv_path)),
    ("05_IndividualPermissionItemAccess.csv", read_file_bytes(access_csv_path)),
]

# Create report archive
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filename = f"{timestamp}_{site_id}_security"
report_id = create_report(
    report_type="site_scan",
    filename=filename,
    files=files,
    metadata={
        "title": f"Security scan: {site_id}",
        "ok": True,
        "error": "",
        "site_id": site_id,
        "site_url": site_url,
        "scope": scope,
        "include_subsites": include_subsites,
        "stats": stats
    },
    logger=logger
)
```

**Note**: Function is `create_report()` not `create_report_archive()`. Signature takes `(report_type, filename, files, metadata, ...)`.

### SCAN-IP01-IS-14: Update site.security_scan_result on completion

**Location**: `run_security_scan()` after report creation

**Action**: Update site.json with report_id

**Code**:
```python
# Update site.json
site = load_site(storage_path, site_id)
site.security_scan_result = report_id
save_site_to_file(storage_path, site)
```

## 4. Test Cases

### Category 1: Input Validation (4 tests)

- **SCAN-IP01-TC-01**: Missing site_id -> ok=false, "Missing 'site_id' parameter"
- **SCAN-IP01-TC-02**: Non-existent site_id -> ok=false, 404, "Site not found"
- **SCAN-IP01-TC-03**: Invalid scope value -> ok=false, "Invalid scope"
- **SCAN-IP01-TC-04**: Valid params -> ok=true, scan starts

### Category 2: CSV Output Format (5 tests)

- **SCAN-IP01-TC-05**: CSV headers match PowerShell format -> exact column order
- **SCAN-IP01-TC-06**: CSV escaping matches PowerShell -> quotes, commas, newlines
- **SCAN-IP01-TC-07**: UTF-8 encoding without BOM -> first bytes not EF BB BF
- **SCAN-IP01-TC-08**: Empty values rendered correctly -> "" or empty
- **SCAN-IP01-TC-09**: Nesting levels correct -> 0=direct, 1=via group, 2+=nested

### Category 3: Group Resolution (4 tests)

- **SCAN-IP01-TC-10**: SharePoint group members resolved -> users listed
- **SCAN-IP01-TC-11**: Entra ID nested groups resolved -> up to 5 levels
- **SCAN-IP01-TC-12**: Circular reference handled -> stops at max level
- **SCAN-IP01-TC-13**: Cache used on second scan -> faster, same results

### Category 4: Report Archive (3 tests)

- **SCAN-IP01-TC-14**: Report ZIP created in correct location
- **SCAN-IP01-TC-15**: report.json contains correct metadata
- **SCAN-IP01-TC-16**: site.security_scan_result updated

### Category 5: Selftest (7 tests)

- **SCAN-IP01-TC-17**: TC-01 Connect to selftest site
- **SCAN-IP01-TC-18**: TC-02 Enumerate site groups
- **SCAN-IP01-TC-19**: TC-03 Resolve group members
- **SCAN-IP01-TC-20**: TC-04 Query lists with HasUniqueRoleAssignments
- **SCAN-IP01-TC-21**: TC-05 Resolve item role assignments
- **SCAN-IP01-TC-22**: TC-06 Create report archive
- **SCAN-IP01-TC-23**: TC-07 Verify CSV output format

## 5. Verification Checklist

### Prerequisites

- [ ] **SCAN-IP01-VC-01**: `_V2_SPEC_SITES_SECURITY_SCAN.md` read and understood
- [ ] **SCAN-IP01-VC-02**: `_POC_PERMISSION_SCANNER_RESULTS.md` patterns reviewed
- [ ] **SCAN-IP01-VC-03**: PowerShell CSV output format documented

### Implementation

- [ ] **SCAN-IP01-VC-04**: IS-01 common_security_scan_functions_v2.py created
- [ ] **SCAN-IP01-VC-05**: IS-02 CSV escaping function implemented
- [ ] **SCAN-IP01-VC-06**: IS-03 Entra ID cache functions implemented
- [ ] **SCAN-IP01-VC-07**: IS-04 SharePoint connection function implemented
- [ ] **SCAN-IP01-VC-07B**: IS-04B Graph client for Entra ID resolution implemented
- [ ] **SCAN-IP01-VC-08**: IS-05 Group resolution functions implemented
- [ ] **SCAN-IP01-VC-09**: IS-06 Site groups scanning implemented
- [ ] **SCAN-IP01-VC-10**: IS-07 List/library scanning implemented
- [ ] **SCAN-IP01-VC-11**: IS-08 Broken inheritance scanning implemented
- [ ] **SCAN-IP01-VC-11B**: IS-08B Subsite scanning implemented
- [ ] **SCAN-IP01-VC-12**: IS-09 security_scan endpoint implemented
- [ ] **SCAN-IP01-VC-13**: IS-10 Security Scan dialog JS implemented
- [ ] **SCAN-IP01-VC-14**: IS-11 Action buttons updated
- [ ] **SCAN-IP01-VC-15**: IS-12 Selftest endpoint implemented
- [ ] **SCAN-IP01-VC-16**: IS-13 Report archive creation implemented
- [ ] **SCAN-IP01-VC-17**: IS-14 Site update on completion implemented

### Validation

- [ ] **SCAN-IP01-VC-18**: All test cases pass
- [ ] **SCAN-IP01-VC-19**: Selftest passes 7/7
- [ ] **SCAN-IP01-VC-20**: CSV output matches PowerShell scanner exactly
- [ ] **SCAN-IP01-VC-21**: Manual UI verification complete
- [ ] **SCAN-IP01-VC-22**: Report visible in /v2/reports?type=site_scan

## 6. Document History

**[2026-02-03 16:15]**
- Fixed: IS-04B Graph SDK syntax - uses `await` and no `.execute()` (Python msgraph-sdk is async)
- Fixed: IS-02 CSV escape regex now matches SPEC Section 9 exactly

**[2026-02-03 16:05]**
- Added: IS-04B for Microsoft Graph client initialization (Entra ID group resolution)
- Added: Exact CSV column order to IS-01 from SPEC Section 14
- Added: Note about sync library with async endpoints in IS-01
- Changed: IS-06 now uses `$expand` pattern from POC TC-06 for permission levels
- Changed: IS-06 now filters out "Limited Access" per MUST-NOT-FORGET
- Fixed: IS-13 uses `create_report()` not `create_report_archive()`
- Added: VC-07B for Graph client verification
- Updated: Timeline field to reflect updates

**[2026-02-03 15:55]**
- Fixed: Timeline field added (was missing)
- Fixed: IS-11 onclick uses escaped double quotes per SITE-LN-001

**[2026-02-03 15:52]**
- Initial implementation plan created
- 16 implementation steps defined (IS-01 to IS-14, plus IS-04B and IS-08B)
- 23 test cases identified
- 24 verification checklist items

