# SPEC: Sites Security Scan

**Doc ID**: SITE-SP03
**Goal**: Specify the security scan feature for scanning SharePoint site permissions and generating CSV reports.
**Target file**: `/src/routers_v2/sites.py`

**Depends on:**
- `_V2_SPEC_SITES.md [SITE-SP01]` for site data model and storage
- `_V2_SPEC_SITES_UI.md [SITE-SP02]` for UI patterns and modal design
- `_SPEC_SHAREPOINT_PERMISSION_INSIGHTS_SCANNER.md [SPAPI-SP01]` for output format and permission model
- `_POC_PERMISSION_SCANNER_RESULTS.md [PSCP-RS01]` for validated API patterns

**Does not depend on:**
- File scan feature (parallel implementation)

## MUST-NOT-FORGET

- Output CSV files MUST match PowerShell scanner format exactly (column order, escaping, UTF-8 no BOM)
- Use `ID gt {last_id}` for pagination, NOT `skip()` (SharePoint ignores skip)
- Entra ID group resolution has max nesting level (default: 5)
- Filter out "Limited Access" permission level by default
- Streaming endpoint with SSE progress updates

## Table of Contents

1. [Scenario](#1-scenario)
2. [Context](#2-context)
3. [Domain Objects](#3-domain-objects)
4. [Scan Scope Options](#4-scan-scope-options)
5. [Endpoint Specification](#5-endpoint-specification)
6. [Functional Requirements](#6-functional-requirements)
7. [Design Decisions](#7-design-decisions)
8. [Implementation Guarantees](#8-implementation-guarantees)
9. [Key Mechanisms](#9-key-mechanisms)
10. [Action Flow](#10-action-flow)
11. [Data Structures](#11-data-structures)
12. [User Actions](#12-user-actions)
13. [UX Design](#13-ux-design)
14. [Example CSV Output (Anonymized)](#14-example-csv-output-anonymized)

## 1. Scenario

**Problem:** Administrators need visibility into SharePoint permissions across sites, libraries, and individual items. The existing PowerShell scanner works but requires manual execution and PowerShell expertise.

**Solution:**
- Add Security Scan button to Sites UI with scope options dialog
- Streaming endpoint that scans permissions and reports progress
- Generate CSV output files identical to PowerShell scanner format
- Store results as report archive (viewable/downloadable via `/v2/reports`)

**What we don't want:**
- Different output format than PowerShell scanner (must be identical)
- Blocking requests (must stream progress)
- Memory-intensive scanning (write CSV incrementally)

## 2. Context

The security scan feature builds on:
- POC-validated Office365-REST-Python-Client patterns
- Existing sites router UI with modal dialogs
- PowerShell scanner output format as authoritative reference

## 3. Domain Objects

### ScanScope

A **ScanScope** defines what to scan.

**Properties:**
- `scope` - Scan depth: `all` (default), `site`, `lists`, `items`
- `include_subsites` - Scan subsites recursively (boolean, default: false)

**Scope values:**
- `all` - Full scan: site groups, lists, items with broken inheritance
- `site` - Site-level only: groups, users, direct assignments
- `lists` - Site + lists/libraries (no item-level permissions)
- `items` - Items with broken inheritance only

### ScanResult (Report Archive)

A **ScanResult** is stored as a report archive following `_V2_SPEC_REPORTS.md`.

**Type:** `site_scan` -> folder `site_scans`
**Storage:** `PERSISTENT_STORAGE_PATH/reports/site_scans/{timestamp}_{site_id}_security.zip`
**Example:** `reports/site_scans/2026-02-03_14-30-00_site01_security.zip`

**Archive contents:**
- `report.json` - Mandatory metadata with scan stats
- `01_SiteContents.csv` - Sites, subsites, lists, libraries
- `02_SiteGroups.csv` - SharePoint permission groups
- `03_SiteUsers.csv` - Users with site-level access
- `04_IndividualPermissionItems.csv` - Items with broken inheritance
- `05_IndividualPermissionItemAccess.csv` - Who has access to broken items

**report.json schema (site_scan type):**
```json
{
  "report_id": "site_scans/2026-02-03_14-30-00_site01_security",
  "title": "Security scan: site01",
  "type": "site_scan",
  "created_utc": "2026-02-03T14:30:00.000000Z",
  "ok": true,
  "error": "",
  "files": [
    {"filename": "report.json", "file_path": "report.json", "file_size": 1024},
    {"filename": "01_SiteContents.csv", "file_path": "01_SiteContents.csv", "file_size": 3112},
    {"filename": "02_SiteGroups.csv", "file_path": "02_SiteGroups.csv", "file_size": 185},
    {"filename": "03_SiteUsers.csv", "file_path": "03_SiteUsers.csv", "file_size": 1845},
    {"filename": "04_IndividualPermissionItems.csv", "file_path": "04_IndividualPermissionItems.csv", "file_size": 1440},
    {"filename": "05_IndividualPermissionItemAccess.csv", "file_path": "05_IndividualPermissionItemAccess.csv", "file_size": 12314}
  ],
  "site_id": "site01",
  "site_url": "https://contoso.sharepoint.com/sites/testsite",
  "scope": "all",
  "include_subsites": false,
  "started_utc": "2026-02-03T14:25:00.000000Z",
  "finished_utc": "2026-02-03T14:30:00.000000Z",
  "stats": {
    "sites_scanned": 1,
    "groups_found": 5,
    "users_found": 23,
    "lists_scanned": 3,
    "items_scanned": 500,
    "broken_inheritance": 12,
    "errors": 0
  }
}
```

### CSV Output Schemas

**01_SiteContents.csv:**
- `Id` - SharePoint object ID
- `Type` - Web, List, Library
- `Title` - Display name
- `Url` - Full URL

**02_SiteGroups.csv:**
- `Id` - SharePoint group ID
- `Role` - Owners, Members, Visitors, (custom)
- `Title` - Group display name
- `PermissionLevel` - Full Control, Edit, Read, etc.
- `Owner` - Group owner

**03_SiteUsers.csv:**
- `Id` - SharePoint user ID (empty for nested group members)
- `LoginName` - User principal name
- `DisplayName` - Display name
- `Email` - Email address
- `PermissionLevel` - Permission level(s), comma-separated
- `ViaGroup` - Group name if access is via group
- `ViaGroupId` - Group ID (SharePoint ID or Entra ID GUID)
- `ViaGroupType` - SharePointGroup, SecurityGroup, M365Group
- `AssignmentType` - User, Group, SharingLink, Direct
- `NestingLevel` - 0=direct, 1=via group, 2+=nested group
- `ParentGroup` - Parent group if nested

**04_IndividualPermissionItems.csv:**
- `Id` - Item ID
- `Type` - ITEM, FILE, FOLDER
- `Title` - Item title or filename
- `Url` - Full URL to item

**05_IndividualPermissionItemAccess.csv:**
- `Id` - Item ID
- `Type` - ITEM, FILE, FOLDER
- `Url` - Full URL to item
- `LoginName` - User principal name
- `DisplayName` - Display name
- `Email` - Email address
- `PermissionLevel` - Permission level(s)
- `SharedDateTime` - When shared (if via sharing link)
- `SharedByDisplayName` - Who shared (if via sharing link)
- `SharedByLoginName` - Who shared login
- `ViaGroup` - Group name if access is via group
- `ViaGroupId` - Group ID
- `ViaGroupType` - SharePointGroup, SecurityGroup, M365Group
- `AssignmentType` - User, Group, SharingLink, Direct
- `NestingLevel` - Nesting depth
- `ParentGroup` - Parent group if nested

## 4. Scan Scope Options

The `scope` parameter controls what to scan (matches crawler pattern):

**Scopes:**
- `scope=all` (default) - Full scan: site groups, lists, items with broken inheritance
- `scope=site` - Site-level only: groups, users, direct assignments
- `scope=lists` - Site + lists/libraries (no item-level permissions)
- `scope=items` - Items with broken inheritance only

**Optional modifier:**
- `include_subsites=true` - Recursively scan all subsites (default: false)

**Scope behavior:**
- `all`: Scans site groups, enumerates lists, scans items with broken inheritance
- `site`: Quick overview - only site-level access (02_SiteGroups.csv, 03_SiteUsers.csv)
- `lists`: Site + structure - adds 01_SiteContents.csv
- `items`: Focus on broken inheritance - adds 04/05 CSVs

## 5. Endpoint Specification

### Shorthand Notation

Follows `_V2_SPEC_ROUTERS.md` conventions:
- `X(s)` = Custom action, stream format only
- `L(jhs)` = List action supporting json, html, stream formats

### Endpoints

**X(s): `/v2/sites/security_scan`** - Scan site permissions

**Endpoint:** `GET /v2/sites/security_scan`
**Format:** stream (SSE only)
**Job:** Creates streaming job (`jb_*`) that can be monitored, paused, resumed, or cancelled

**Query params:**
- `site_id` (required) - Site to scan
- `scope` (optional) - `all` (default), `site`, `lists`, `items`
- `include_subsites` (optional) - true/false, default: false
- `delete_caches` (optional) - true/false, default: false. Deletes cached Entra ID group members before scan.

**Job lifecycle:**
1. Job created with `jb_*` ID, state=`running`
2. SSE stream starts with `start_json` event
3. Progress events sent during scan
4. On completion: report archive created, `end_json` event with result
5. Job can be monitored via `/v2/jobs/monitor?job_id=jb_*`

**SSE Events:**

```
event: progress
data: {"step": "Connecting to site...", "progress": 0}

event: progress
data: {"step": "Scanning site groups...", "progress": 10, "groups": 5}

event: progress
data: {"step": "Scanning library 'Documents' [ 1 / 3 ]...", "progress": 30, "library": "Documents"}

event: progress
data: {"step": "Scanning items [ 150 / 500 ]...", "progress": 60, "items_scanned": 150, "broken_found": 5}

event: end_json
data: {"job_id": "jb_42", "state": "completed", "result": {"ok": true, "data": {...}}}
```

**Result on completion (`end_json.result`):**
```json
{
  "ok": true,
  "error": "",
  "data": {
    "report_id": "site_scans/2026-02-03_14-30-00_site01_security",
    "site_id": "site01",
    "stats": {
      "sites_scanned": 1,
      "groups_found": 5,
      "users_found": 23,
      "items_scanned": 500,
      "broken_inheritance": 12,
      "duration_seconds": 45
    }
  }
}
```

**Report archive:** See [ScanResult (Report Archive)](#scanresult-report-archive) in Section 3 for:
- Archive location: `reports/site_scans/{timestamp}_{site_id}_security.zip`
- `report.json` schema with stats, scope, timestamps
- CSV files included (01-05)

Report accessible via:
- `/v2/reports?type=site_scan` - List all site scan reports
- `/v2/reports/get?report_id={report_id}` - Get report metadata
- `/v2/reports/download?report_id={report_id}` - Download ZIP

### Selftest (X(s): `/v2/sites/security_scan/selftest`)

**Endpoint:** `GET /v2/sites/security_scan/selftest`
**Format:** stream (SSE only)
**Requires:** `CRAWLER_SELFTEST_SHAREPOINT_SITE` environment variable

**Tests:**
- TC-01: Connect to selftest site
- TC-02: Enumerate site groups
- TC-03: Resolve group members
- TC-04: Query lists with HasUniqueRoleAssignments
- TC-05: Resolve item role assignments
- TC-06: Create report archive
- TC-07: Verify CSV output format

**Result:**
```json
{
  "ok": true,
  "error": "",
  "data": {
    "passed": 7,
    "failed": 0,
    "passed_tests": ["TC-01", "TC-02", ...],
    "failed_tests": []
  }
}
```

## 6. Functional Requirements

**SCAN-FR-01: Pre-Scan Dialog**
- [Security Scan] button opens modal with scope dropdown and subsites checkbox
- Scope defaults to `all`, subsites unchecked
- Endpoint preview updates dynamically based on selections
- [OK] button initiates scan with selected options

**SCAN-FR-02: Job Lifecycle**
- Creates streaming job (`jb_*`) on scan start
- SSE stream with `start_json`, progress events, `end_json`
- Job visible in `/v2/jobs` list during and after execution
- User can pause/resume/cancel via `/v2/jobs/control`
- Report archive created on successful completion (not on cancel)

**SCAN-FR-03: Site-Level Scanning**
- Enumerate all SharePoint groups (Owners, Members, Visitors, custom)
- Resolve group members including nested Entra ID groups
- Record direct user assignments at site level
- Output to 02_SiteGroups.csv and 03_SiteUsers.csv

**SCAN-FR-04: List-Level Scanning**
- Enumerate lists and libraries (BaseTemplate 100, 101, 119)
- Skip built-in lists (48 system lists)
- Record list metadata to 01_SiteContents.csv

**SCAN-FR-05: Item-Level Scanning**
- Query items with HasUniqueRoleAssignments=true
- Use pagination with `ID gt {last_id}` filter
- Resolve role assignments for broken inheritance items
- Output to 04_IndividualPermissionItems.csv and 05_IndividualPermissionItemAccess.csv

**SCAN-FR-06: Subsite Scanning**
- If `include_subsites=true`, recursively scan all subsites
- Each subsite follows same scan logic as root site
- All output aggregated to same CSV files
- Subsites added to 01_SiteContents.csv with Type=SUBSITE

**SCAN-FR-07: CSV Output Generation**
- UTF-8 encoding without BOM
- CSV-escape values containing quotes, commas, newlines
- Write incrementally (batch every 100 lines)
- Column order must match PowerShell scanner exactly

**SCAN-FR-08: Report Archive Creation**
- Create report archive using `common_report_functions_v2.create_report()`
- Store in `PERSISTENT_STORAGE_PATH/reports/site_scans/`
- Filename: `{timestamp}_{site_id}_security.zip`
- Update site.security_scan_result field with report_id
- Report viewable/downloadable via `/v2/reports` endpoints

**SCAN-FR-09: Error Handling**
- Continue on individual item errors (log and skip)
- Abort on authentication or connection errors
- Report final error count in completion event

## 7. Design Decisions

**SCAN-DD-01:** Use Office365-REST-Python-Client for SharePoint access. Rationale: POC validated this library supports all required operations.

**SCAN-DD-02:** Stream progress via SSE, not WebSocket. Rationale: Matches existing middleware patterns (crawler, selftest).

**SCAN-DD-03:** Store results as report archive per `_V2_SPEC_REPORTS.md`. Rationale: Consistent with other V2 routers, enables viewing/download via `/v2/reports`.

**SCAN-DD-04:** Match PowerShell CSV format exactly. Rationale: Enables comparison, existing tooling compatibility, user familiarity.

**SCAN-DD-05:** No dry_run parameter. Rationale: Scan is read-only operation, no destructive actions to preview.

**SCAN-DD-06:** Default to not including subsites. Rationale: Subsite scanning can be very slow on large site collections.

**SCAN-DD-07:** Cache Entra ID group members persistently across scans. Rationale: Tenant group memberships rarely change; caching avoids redundant Graph API calls and reduces throttling risk. Based on PowerShell scanner pattern from `_SPEC_SHAREPOINT_PERMISSION_INSIGHTS_SCANNER.md [SPAPI-SP01]`.

## 8. Implementation Guarantees

**SCAN-IG-01:** CSV output is byte-for-byte compatible with PowerShell scanner format (same columns, order, escaping).

**SCAN-IG-02:** All users with access are captured regardless of assignment path (direct, SP group, Entra ID group, nested).

**SCAN-IG-03:** Progress events sent at least every 5 seconds during long operations.

**SCAN-IG-04:** Scan can be interrupted without corrupting partial output files.

**SCAN-IG-05:** Entra ID group nesting resolved up to 5 levels to prevent infinite loops.

**SCAN-IG-06:** Honor SharePoint throttling: implement Retry-After header handling and exponential backoff on 429 responses.

**SCAN-IG-07:** Group member caches persist across scanning sessions until explicitly deleted via `delete_caches=true`.

## 9. Key Mechanisms

### CSV Escaping

Match PowerShell scanner escaping:
```python
def csv_escape(value: str) -> str:
    if not value:
        return '""'
    # Escape if contains: + - = / , " \n or looks like date/number
    if re.match(r'^([+\-=\/]*[\.\d\s\/\:]*|.*[\,\"\n].*|[\n]*)$', value):
        return '"' + value.replace('"', '""') + '"'
    return value
```

### Pagination with ID Filter

```python
# First page
items = library.items.get().select(["ID", "FileRef", "HasUniqueRoleAssignments"]).top(5000).execute_query()
last_id = max(item.properties.get('ID') for item in items)

# Next pages
while True:
    items = library.items.get().filter(f"ID gt {last_id}").top(5000).execute_query()
    if not items:
        break
    last_id = max(item.properties.get('ID') for item in items)
```

### Group Resolution

```python
def resolve_group_members(group, nesting_level=1, parent_group=""):
    members = []
    for member in group.users:
        if is_entra_id_group(member):
            # Recursive resolution
            nested = resolve_entra_group(member.login_name, nesting_level + 1, group.title)
            members.extend(nested)
        else:
            members.append({
                "login_name": member.login_name,
                "nesting_level": nesting_level,
                "parent_group": parent_group,
                ...
            })
    return members
```

### Group Member Caching

**Storage:** `LOCAL_PERSISTENT_STORAGE_PATH/sites/_entra_group_cache/`

One JSON file per Entra ID group, using group ID as filename.

**Example:** `_entra_group_cache/3b7af3f4-c9d6-4118-bfe5-52a4b08e7c6b.json`

**Cache file structure:**
```json
{
  "group_id": "3b7af3f4-c9d6-4118-bfe5-52a4b08e7c6b",
  "group_display_name": "NestedSecurityGroup01",
  "group_type": "SecurityGroup",
  "cached_utc": "2026-02-03T14:00:00Z",
  "member_count": 5,
  "members": [
    {"login_name": "user1@contoso.com", "display_name": "User One", "email": "user1@contoso.com"},
    {"login_name": "user2@contoso.com", "display_name": "User Two", "email": "user2@contoso.com"}
  ]
}
```

**Behavior:**
- Entra ID groups cached by group ID (tenant-wide, persists across all scans)
- SharePoint groups NOT cached (site-specific, resolved fresh each scan)
- `delete_caches=true` deletes all files in `_entra_group_cache/` folder before scan
- Cache lookup before Graph API call; cache miss triggers API call and stores result

## 10. Action Flow

```
User clicks [Security Scan] on site row
├─> showSecurityScanDialog(siteId)
│   ├─> Render modal with scope checkboxes
│   └─> User adjusts options, clicks [Start Scan]
│
├─> callStreamingEndpoint('/v2/sites/security_scan?site_id=...')
│   ├─> Show progress panel
│   └─> Process SSE events
│
Server-side:
├─> Connect to SharePoint site
├─> Create output folder
│
├─> If scope in (all, site, lists, items):
│   ├─> Load site groups (Owners, Members, Visitors, custom)
│   ├─> For each group:
│   │   ├─> Resolve members (recursive for Entra ID)
│   │   └─> Write to 02_SiteGroups.csv, 03_SiteUsers.csv
│   └─> Load direct role assignments
│
├─> If scope in (all, lists):
│   ├─> Load lists (filter by template, exclude built-in)
│   └─> Write to 01_SiteContents.csv
│
├─> If scope in (all, items):
│   ├─> For each list:
│   │   ├─> Query items with HasUniqueRoleAssignments
│   │   ├─> For each broken item:
│   │   │   ├─> Load role assignments
│   │   │   └─> Write to 04, 05 CSVs
│   │   └─> Send progress event
│   └─> Send progress event per list
│
├─> If include_subsites:
│   └─> Recursively process each subsite
│
├─> Update site.security_scan_result
└─> Send complete event
```

## 11. Data Structures

### Request

```
GET /v2/sites/security_scan?site_id=site01&scope=all&include_subsites=false
```

### SSE Response Stream

```
event: progress
data: {"step": "Connecting to site...", "progress": 0}

event: progress
data: {"step": "Loading site groups...", "progress": 5, "groups": 0}

event: progress
data: {"step": "Resolving group 'Site Owners' [ 1 / 5 ]...", "progress": 10}

event: progress
data: {"step": "Scanning library 'Documents' [ 1 / 3 ]...", "progress": 30}

event: progress
data: {"step": "Scanning items [ 250 / 500 ]...", "progress": 65, "items_scanned": 250, "broken_found": 8}

event: complete
data: {"ok": true, "data": {"files": [...], "stats": {...}}}
```

## 12. User Actions

- **Open Security Scan Dialog**: Click [Security Scan] button on site row
- **Configure Scope**: Select scope from dropdown in dialog
- **Start Scan**: Click [Start Scan] to begin scanning
- **Monitor Progress**: View progress bar and step description
- **Cancel Scan**: Click [Cancel] to abort (best-effort)
- **View Results**: After completion, results stored in site folder

## 13. UX Design

```
Modal (Security Scan):
+---------------------------------------------------------------+
|                                                          [x]  |
| Security Scan: site01                                         |
|                                                               |
| Scope: [all v]                                                |
|        +------------------+                                   |
|        | all              |                                   |
|        | site             |                                   |
|        | lists            |                                   |
|        | items            |                                   |
|        +------------------+                                   |
|                                                               |
| [ ] Include subsites                                          |
| [ ] Delete cached Entra ID group members                      |
|                                                               |
| Endpoint Preview:                                             |
| +-----------------------------------------------------------+ |
| | /v2/sites/security_scan?site_id=site01&scope=all&...      | |
| +-----------------------------------------------------------+ |
|                                                               |
|                                          [OK] [Cancel]        |
+---------------------------------------------------------------+
```

Completion (shown in console log, link to report):
```
Security scan complete.
  Scanned: 1 site, 3 libraries, 500 items
  Found: 5 groups, 23 users, 12 items with broken inheritance
  Duration: 45 seconds
  Report: site_scans/2026-02-03_14-30-00_site01_security
  View report: /v2/reports?format=ui (filter by site_scan)
```

### Updated Table Columns Configuration

```python
columns = [
  {"field": "site_id", "header": "Site ID"},
  {"field": "name", "header": "Name", "default": "-"},
  {"field": "site_url", "header": "Site URL", "default": "-"},
  {"field": "file_scan_result", "header": "Files", "default": "-"},
  {"field": "security_scan_result", "header": "Security", "default": "-"},
  {
    "field": "actions",
    "header": "Actions",
    "buttons": [
      {"text": "Edit", "onclick": "showEditSiteForm('{itemId}')", "class": "btn-small"},
      {"text": "Delete", ...},
      {"text": "File Scan", "onclick": "showNotImplemented('File Scan')", "class": "btn-small btn-disabled"},
      {"text": "Security Scan", "onclick": "showSecurityScanDialog('{itemId}')", "class": "btn-small btn-primary"}
    ]
  }
]
```

## 14. Example CSV Output (Anonymized)

Reference output from PowerShell scanner showing exact format to match.

### 01_SiteContents.csv

```csv
Id,Type,Title,Url
22e298f9-bf09-4e81-96f2-75f44d998726,LIST,Areas,https://contoso.sharepoint.com/sites/testsite/Lists/Areas
0df3c997-a8c1-4090-bb4b-322a213c1232,LIBRARY,Documents,https://contoso.sharepoint.com/sites/testsite/Shared Documents
5c1aafce-d6cf-423d-be0b-060771d2c5e8,SITEPAGES,Site Pages,https://contoso.sharepoint.com/sites/testsite/SitePages
f4babe71-0864-497a-9a48-bdfe1bc81fe5,SUBSITE,BrokenInheritanceSubsite01,https://contoso.sharepoint.com/sites/testsite/BrokenInheritanceSubsite01
8b06e4f4-0380-42a6-8e96-bcadd0c69501,LIBRARY,Documents,https://contoso.sharepoint.com/sites/testsite/BrokenInheritanceSubsite01/Shared Documents
```

### 02_SiteGroups.csv

```csv
Id,Role,Title,PermissionLevel,Owner
3,SiteOwners,TestSite Owners,Full Control,
5,SiteMembers,TestSite Members,Edit,
4,SiteVisitors,TestSite Visitors,Read,
31,Custom,Custom Group,Full Control,
```

### 03_SiteUsers.csv

```csv
Id,LoginName,DisplayName,Email,PermissionLevel,ViaGroup,ViaGroupId,ViaGroupType,AssignmentType,NestingLevel,ParentGroup
6,user1@contoso.com,User One,user1@contoso.com,Full Control,TestSite Owners,3,SharePointGroup,Group,1,""
10,user2@contoso.com,User Two,user2@contoso.com,Full Control,TestSite Owners,3,SharePointGroup,Group,1,""
,member1@contoso.com,Member One,,Full Control,NestedSecurityGroup01,3b7af3f4-c9d6-4118-bfe5-52a4b08e7c6b,SecurityGroup,Group,2,TestSite Owners
,user2@contoso.com,User Two,user2@contoso.com,Full Control,SecurityGroup01,22208125-d314-4e34-93f7-8979ecf6fc1f,SecurityGroup,Group,3,NestedSecurityGroup01
11,user3@contoso.com,User Three,user3@contoso.com,Read,TestSite Visitors,4,SharePointGroup,Group,1,""
,user3@contoso.com,User Three,user3@contoso.com,Full Control,M365Group01,d70680c7-4a6c-47a1-a751-da63b5df6093,SecurityGroup,Group,2,Custom Group
11,user3@contoso.com,User Three,user3@contoso.com,"","",,,User,0,""
```

### 04_IndividualPermissionItems.csv

```csv
Id,Type,Title,Url
22e298f9-bf09-4e81-96f2-75f44d998726,LIST,testsite,https://contoso.sharepoint.com/sites/testsite/Lists/Areas
1,ITEM,ItemTitle,https://contoso.sharepoint.com/sites/testsite/Lists/Areas/AllItems.aspx?FilterField1=ID&FilterValue1=1
0df3c997-a8c1-4090-bb4b-322a213c1232,LIBRARY,testsite,https://contoso.sharepoint.com/sites/testsite/Shared Documents
5,FOLDER,SharedByRequest,https://contoso.sharepoint.com/sites/testsite/Shared Documents/SharedByRequest
3,FOLDER,SharedDirectlyWithPerson,https://contoso.sharepoint.com/sites/testsite/Shared Documents/SharedDirectlyWithPerson
4,FOLDER,SharedWithCustomGroup,https://contoso.sharepoint.com/sites/testsite/Shared Documents/SharedWithCustomGroup
f4babe71-0864-497a-9a48-bdfe1bc81fe5,SUBSITE,BrokenInheritanceSubsite01,https://contoso.sharepoint.com/sites/testsite/BrokenInheritanceSubsite01
```

### 05_IndividualPermissionItemAccess.csv

```csv
Id,Type,Url,LoginName,DisplayName,Email,PermissionLevel,SharedDateTime,SharedByDisplayName,SharedByLoginName,ViaGroup,ViaGroupId,ViaGroupType,AssignmentType,NestingLevel,ParentGroup
5,FOLDER,https://contoso.sharepoint.com/sites/testsite/Shared Documents/SharedByRequest,user4@contoso.com,User Four,user4@contoso.com,Edit,,"",,"",,,User,0,""
5,FOLDER,https://contoso.sharepoint.com/sites/testsite/Shared Documents/SharedByRequest,user1@contoso.com,User One,user1@contoso.com,Full Control,,"",,TestSite Owners,3,SharePointGroup,Group,1,""
5,FOLDER,https://contoso.sharepoint.com/sites/testsite/Shared Documents/SharedByRequest,member1@contoso.com,Member One,,Full Control,,"",,NestedSecurityGroup01,3b7af3f4-c9d6-4118-bfe5-52a4b08e7c6b,SecurityGroup,Group,2,TestSite Owners
5,FOLDER,https://contoso.sharepoint.com/sites/testsite/Shared Documents/SharedByRequest,user2@contoso.com,User Two,user2@contoso.com,Full Control,,"",,SecurityGroup01,22208125-d314-4e34-93f7-8979ecf6fc1f,SecurityGroup,Group,3,NestedSecurityGroup01
5,FOLDER,https://contoso.sharepoint.com/sites/testsite/Shared Documents/SharedByRequest,user3@contoso.com,User Three,user3@contoso.com,Read,,"",,TestSite Visitors,4,SharePointGroup,Group,1,""
3,FOLDER,https://contoso.sharepoint.com/sites/testsite/Shared Documents/SharedDirectlyWithPerson,user1@contoso.com,User One,user1@contoso.com,Read,2023-04-02T22:07:33,User One,user1@contoso.com,SharingLinks.013c7d3f-dd22-4e04-afec-f80006c19e26.OrganizationView.71839de1-afcb-46c9-89f7-ef9e4a460a78,36,SharePointGroup,SharingLink,1,""
3,FOLDER,https://contoso.sharepoint.com/sites/testsite/Shared Documents/SharedDirectlyWithPerson,user1@contoso.com,User One,user1@contoso.com,Full Control,2023-04-02T22:07:33,User One,user1@contoso.com,TestSite Owners,3,SharePointGroup,Group,1,""
```

**Key observations from examples:**
- Empty values shown as `""` (quoted empty string) or empty (no quotes)
- Nested group members have empty `Id` field
- `NestingLevel` starts at 0 for direct, 1 for via group, 2+ for nested
- `ViaGroupType` values: `SharePointGroup`, `SecurityGroup` (includes M365 groups)
- `AssignmentType` values: `User`, `Group`, `SharingLink`, `Direct`
- Sharing links show in `SharedDateTime`, `SharedByDisplayName`, `SharedByLoginName`

## Document History

**[2026-02-03 16:15]**
- Fixed: SCAN-FR-08 function name `create_report_archive()` -> `create_report()` (synced from IMPL)

**[2026-02-03 15:45]**
- Changed: Cache folder renamed to `_entra_group_cache/` (underscore prefix)
- Added: Rule in `_V2_SPEC_SITES.md` that folders starting with `_` are ignored by sites endpoints

**[2026-02-03 15:33]**
- Changed: Cache now uses one JSON file per Entra ID group (not single file)
- Changed: Storage path to `LOCAL_PERSISTENT_STORAGE_PATH/sites/_entra_group_cache/`
- Added: Metadata fields to cache JSON (group_display_name, group_type, member_count)
- Changed: All "Azure AD" references renamed to "Entra ID" throughout
- Changed: SharePoint groups NOT cached (resolved fresh each scan)

**[2026-02-03 15:30]**
- Changed: SharePoint groups NOT cached (resolved fresh each scan)

**[2026-02-03 15:26]**
- Added: `delete_caches` query param for clearing cached group members
- Added: SCAN-DD-07 for persistent group member caching
- Added: SCAN-IG-07 for cache persistence guarantee
- Added: Group Member Caching section in Key Mechanisms
- Changed: Dialog now includes "Delete cached Entra ID group members" checkbox

**[2026-02-03 15:19]**
- Fixed: Action flow now uses `scope in (all, site, lists, items)` instead of old booleans
- Fixed: Request example uses `scope=all` param
- Fixed: SCAN-DD-03 now references report archive storage
- Fixed: User Actions uses "Select scope from dropdown"
- Added: SCAN-IG-06 for SharePoint throttling handling

**[2026-02-03 15:06]**
- Changed: Consolidated 4 scope params into single `scope` param (matches crawler pattern)
- Added: Selftest endpoint `X(s): /v2/sites/security_scan/selftest`
- Added: Job lifecycle documentation (jb_*, start_json, end_json, monitor)
- Added: Shorthand notation section per `_V2_SPEC_ROUTERS.md`
- Changed: SCAN-FR-02 now documents job lifecycle instead of progress UI
- Changed: Modal now uses scope dropdown instead of checkboxes

**[2026-02-03 15:00]**
- Changed: Output now stored as report archive per `_V2_SPEC_REPORTS.md`
- Added: report.json schema for site_scan type
- Changed: Completion shows in console log with link to reports UI
- Removed: Progress panel (users see console log directly)

**[2026-02-03 14:55]**
- Added: Section 14 with anonymized CSV example output
- Verified: Column order matches PowerShell scanner exactly

**[2026-02-03 14:50]**
- Initial specification created
- Based on POC results and PowerShell scanner format
