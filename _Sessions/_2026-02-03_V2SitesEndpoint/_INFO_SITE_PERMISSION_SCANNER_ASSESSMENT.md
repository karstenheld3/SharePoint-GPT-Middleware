# INFO: SharePoint Permission Scanner Python Assessment

**Doc ID**: PERM-IN01
**Goal**: Assess feasibility and implementation approach for a Python-based SharePoint permission scanner mirroring the PowerShell solution
**Source material**:
- `_SPEC_SHAREPOINT_PERMISSION_INSIGHTS_SCANNER.md [SPAPI-SP01]`
- `PermissionInsightsScanner.ps1` (822 lines)
- `_includes.ps1` (397 lines)
- `MasteringSharePointPermissions.md` (55 pages transcription)
- Sample output folders with CSV files

## Table of Contents

1. Executive Summary
2. PowerShell Implementation Analysis
3. Permission Cases Catalog
4. API Inventory
5. Python Library Options
6. API Mapping (PnP PowerShell to Python)
7. Feasibility Assessment
8. Implementation Recommendations
9. Output File Schemas
10. Document History

## 1. Executive Summary

**Objective**: Implement exhaustive SharePoint permission scanning in the middleware to produce CSV reports showing 100% of users with access to sites, libraries, folders, and files.

**Key Finding**: Full implementation is **FEASIBLE** using:
- **Office365-REST-Python-Client** for SharePoint REST API access
- **Microsoft Graph SDK for Python** for Azure AD group resolution
- Direct REST API calls where libraries have gaps

**Critical gaps to address**:
- No direct equivalent for `Load-CSOMProperties` (batch property loading)
- Azure AD nested group resolution requires Graph API `/transitiveMembers`
- Some CSOM-specific features need REST API workarounds

## 2. PowerShell Implementation Analysis

### 2.1 Script Architecture

```
PermissionInsightsScanner.ps1
├─> Load _includes.ps1 (utility functions)
├─> Get credentials (encrypted SecureString from AppData)
├─> Connect to Azure AD (optional, for faster group resolution)
├─> Read input CSV (jobs = URLs to scan)
└─> For each job:
    ├─> Detect URL type (SITE/SUBSITE/LIBRARY/FOLDER)
    ├─> Connect to SharePoint site
    ├─> Load subsites (if enabled)
    ├─> Step 4: Export groups, group members, site permissions
    │   ├─> Load SharePoint groups (Owners, Members, Visitors, custom)
    │   ├─> Resolve nested Azure AD groups recursively
    │   └─> Write 02_SiteGroups.csv, 03_SiteUsers.csv
    ├─> Step 5: Scan for broken permission inheritance
    │   ├─> Load lists (filter by template)
    │   ├─> For each item: check HasUniqueRoleAssignments
    │   ├─> If broken: resolve all access entries
    │   └─> Write 04_IndividualPermissionItems.csv, 05_IndividualPermissionItemAccess.csv
    └─> Clear site-specific caches
```

### 2.2 Key Functions

- **`ensureSharePointSiteIsConnected()`** - Connect/reconnect to SharePoint
- **`getSharePointGroupMembers()`** - Resolve SP group members with caching
- **`getAzureGroupMembers()`** - Recursive Azure AD group resolution
- **`addGroupAndGroupMembersToOutputLines()`** - Process group with members
- **`appendToFile()`** - Batch write to CSV with UTF-8 encoding
- **`Load-CSOMProperties()`** - Batch load CSOM properties (custom function)

### 2.3 Caching Strategy

- `$global:azureGroupMemberCache` - Persists across jobs (tenant-wide)
- `$global:sharePointGroupMemberCache` - Cleared per job (site-specific)
- `$global:userDisplayNameCache` - Cleared per job
- `$global:sharePointGroupCache` - Cleared per job

## 3. Permission Cases Catalog

### 3.1 Site-Level Permissions

| Case | Description | Source |
|------|-------------|--------|
| SP-01 | Default SharePoint groups (Owners, Members, Visitors) | `Get-PnPGroup -Associated*Group` |
| SP-02 | Custom SharePoint groups | `Get-PnPGroup` |
| SP-03 | Direct user assignments at site level | `$web.RoleAssignments` where `PrincipalType=User` |
| SP-04 | Azure AD Security Groups in SP groups | `PrincipalType=SecurityGroup` |
| SP-05 | M365 Groups in SP groups | LoginName ends with `_o` |
| SP-06 | Nested Azure AD groups (up to 5 levels) | Recursive `Get-AzureADGroupMember` |
| SP-07 | Site Collection Administrators | `/_api/web/siteusers?$filter=IsSiteAdmin eq true` |

### 3.2 Item-Level Permissions (Broken Inheritance)

| Case | Description | Source |
|------|-------------|--------|
| BI-01 | List/library with broken inheritance | `list.HasUniqueRoleAssignments=True` |
| BI-02 | Folder with broken inheritance | `item.HasUniqueRoleAssignments=True` + `FSObjType=1` |
| BI-03 | File with broken inheritance | `item.HasUniqueRoleAssignments=True` + `FSObjType=0` |
| BI-04 | Subsite with broken inheritance | `web.HasUniqueRoleAssignments=True` |

### 3.3 Sharing Scenarios

| Case | Description | Source |
|------|-------------|--------|
| SH-01 | Sharing links (organization-wide view) | Groups with `SharingLinks.` prefix |
| SH-02 | Sharing links (specific people) | Groups with `SharingLinks.` prefix |
| SH-03 | Direct sharing with external users | `SharedWithUsers` field |
| SH-04 | Sharing metadata (who shared, when) | `SharedWithDetails` JSON field |

### 3.4 Permission Levels

From high risk to low risk:
- **Full Control** - All permissions
- **Design** - Full Control minus subsites, groups
- **Manage Hierarchy** - Full Control minus theming, approval
- **Edit** - Full Control minus site settings
- **Contribute** - Edit minus list settings
- **Approve** - Edit plus approval
- **Read** - View pages, items, download
- **View Only** - Read minus download
- **Restricted Read** - Read minus alerts, versions
- **Limited Access** - Auto-assigned for item-level sharing (usually filtered out)

## 4. API Inventory

### 4.1 PnP PowerShell Cmdlets

| Cmdlet | Purpose | Frequency |
|--------|---------|-----------|
| `Connect-PnPOnline` | Authenticate to site | Per job |
| `Get-PnPContext` | Get CSOM context | Per job |
| `Get-PnPWeb` | Get web with properties | Per site/subsite |
| `Get-PnPSubWeb` | Get subsites recursively | Per SITE/SUBSITE job |
| `Get-PnPFolder` | Get folder for URL detection | Per job |
| `Get-PnPList` | Get all lists | Per site/subsite |
| `Get-PnPListItem` | Get items with paging | Per list |
| `Get-PnPGroup` | Get all SP groups | Per site |
| `Get-PnPGroup -Associated*Group` | Get default groups | Per site |
| `Get-PnPGroupMember` | Get SP group members | Per group |
| `Get-PnPProperty` | Load specific CSOM property | Per item with broken inheritance |
| `Get-PnPAzureADGroup` | Get Azure AD group info | Per Azure group |
| `Get-PnPAzureADGroupMember` | Get Azure AD members | Per Azure group |

### 4.2 Azure AD Cmdlets (Alternative)

| Cmdlet | Purpose |
|--------|---------|
| `Connect-AzureAD` | Authenticate to Azure AD |
| `Get-AzureADGroup` | Get group by ID |
| `Get-AzureADGroupMember` | Get group members |

### 4.3 SharePoint REST API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/_api/contextinfo` | Get context for authentication |
| `/_api/web` | Get web properties |
| `/_api/web/webs` | Get subsites |
| `/_api/web/GetFolderByServerRelativeUrl()` | Get folder |
| `/_api/web/lists` | Get lists |
| `/_api/web/lists/getbytitle()/items` | Get list items |
| `/_api/web/sitegroups` | Get SharePoint groups |
| `/_api/web/sitegroups/getbyid()/users` | Get group members |
| `/_api/web/roleassignments` | Get role assignments |
| `/_api/web/AssociatedOwnerGroup` | Get Owners group |
| `/_api/web/AssociatedMemberGroup` | Get Members group |
| `/_api/web/AssociatedVisitorGroup` | Get Visitors group |

### 4.4 Microsoft Graph API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /groups/{id}` | Get group info |
| `GET /groups/{id}/members` | Get direct members |
| `GET /groups/{id}/transitiveMembers` | Get all nested members (flat) - **Security Groups only** |
| `GET /groups/{id}/members` | Get direct members - **Required for M365 Groups** |

**Note**: M365 Groups cannot have nested groups as members. Use `/members` for M365 Groups, `/transitiveMembers` for Security Groups only. Detect M365 Groups by `_o` suffix in LoginName.

## 5. Python Library Options

### 5.1 Office365-REST-Python-Client

**Repository**: https://github.com/vgrem/Office365-REST-Python-Client

**Pros**:
- Mature library (5k+ GitHub stars)
- Supports SharePoint REST API and CSOM patterns
- Client credentials authentication
- List items, folders, files operations
- Role assignments access

**Cons**:
- Some CSOM features require manual REST calls
- Permission-related features less documented
- No built-in Azure AD integration

**Warning**: GitHub issues (#839, #314) show 401 errors accessing RoleAssignments. Requires `Sites.FullControl.All` permission and proper app-only auth. **Recommend POC validation before full implementation.**

**Example - Role Assignments**:
```python
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.client_credential import ClientCredential

ctx = ClientContext(site_url).with_credentials(
    ClientCredential(client_id, client_secret)
)

# Get role assignments with expansion
role_assignments = ctx.web.role_assignments
ctx.load(role_assignments, ["Member", "RoleDefinitionBindings"])
ctx.execute_query()

for ra in role_assignments:
    principal = ra.member
    bindings = ra.role_definition_bindings
```

### 5.2 Microsoft Graph SDK for Python

**Package**: `msgraph-sdk`

**Pros**:
- Official Microsoft SDK
- Full Graph API coverage
- Transitive member resolution built-in
- Modern async support

**Cons**:
- Does not cover SharePoint-specific APIs
- SharePoint access requires separate REST calls

**Example - Transitive Members**:
```python
from msgraph import GraphServiceClient

client = GraphServiceClient(credentials)

# Get all nested members (flat list)
members = await client.groups.by_group_id(group_id).transitive_members.get()
```

### 5.3 Direct REST API Usage

**Pros**:
- Full control over requests
- No library limitations
- Can use existing middleware auth

**Cons**:
- More code to write
- Must handle pagination manually
- Must handle error cases

**Example**:
```python
import httpx

headers = {"Authorization": f"Bearer {token}"}

# Get role assignments with expansion
response = httpx.get(
    f"{site_url}/_api/web/roleassignments?$expand=Member,RoleDefinitionBindings",
    headers=headers
)
```

## 6. API Mapping (PnP PowerShell to Python)

### 6.1 Connection and Authentication

| PnP Cmdlet | Python Approach |
|------------|-----------------|
| `Connect-PnPOnline -Credentials` | `ClientContext.with_credentials(ClientCredential(...))` |
| `Connect-PnPOnline -Interactive` | MSAL with device code flow |
| `Connect-PnPOnline -CertificatePath` | `ClientContext.with_credentials()` with cert |
| `Get-PnPContext` | Use `ctx` object directly |

### 6.2 Web and Site Operations

| PnP Cmdlet | Python Equivalent |
|------------|-------------------|
| `Get-PnPWeb -Includes X,Y` | `ctx.web.get().select(["X", "Y"]).execute_query()` |
| `Get-PnPSubWeb -Recurse` | `ctx.web.webs.get().execute_query()` + recursion |
| `Get-PnPFolder $url` | `ctx.web.get_folder_by_server_relative_url(url)` |

### 6.3 List and Item Operations

| PnP Cmdlet | Python Equivalent |
|------------|-------------------|
| `Get-PnPList -Includes X` | `ctx.web.lists.get().select(["X"]).execute_query()` |
| `Get-PnPListItem -List $l -PageSize 4995` | `list.items.get().top(4995).execute_query()` |
| `Get-PnPProperty -ClientObject $item -Property X` | `ctx.load(item, ["X"]); ctx.execute_query()` |

### 6.4 Group Operations

| PnP Cmdlet | Python Equivalent |
|------------|-------------------|
| `Get-PnPGroup` | `ctx.web.site_groups.get().execute_query()` |
| `Get-PnPGroup -AssociatedOwnerGroup` | `ctx.web.associated_owner_group.get().execute_query()` |
| `Get-PnPGroupMember -Group $g` | `group.users.get().execute_query()` |

### 6.5 Role Assignment Operations

| PnP Cmdlet | Python Equivalent |
|------------|-------------------|
| `$web.RoleAssignments` | `ctx.web.role_assignments.get().expand(["Member", "RoleDefinitionBindings"]).execute_query()` |
| `$item.RoleAssignments` | `item.role_assignments.get().expand(["Member", "RoleDefinitionBindings"]).execute_query()` |
| `$item.HasUniqueRoleAssignments` | `ctx.load(item, ["HasUniqueRoleAssignments"]); ctx.execute_query()` |

### 6.6 Azure AD Operations

| Azure/PnP Cmdlet | Python Equivalent |
|------------------|-------------------|
| `Connect-AzureAD` | `GraphServiceClient(credentials)` |
| `Get-AzureADGroup -ObjectId $id` | `client.groups.by_group_id(id).get()` |
| `Get-AzureADGroupMember -ObjectId $id -All $true` | `client.groups.by_group_id(id).members.get()` |
| Recursive nesting | `client.groups.by_group_id(id).transitive_members.get()` |

## 7. Feasibility Assessment

### 7.0 Performance Considerations

**Large Site Warning**: `HasUniqueRoleAssignments` requires per-item REST calls (Graph API does not support this property). Expected scan times:
- 1,000 items: ~30 seconds
- 10,000 items: ~5 minutes
- 100,000 items: ~11 minutes (with parallel requests)

Consider parallel requests with rate limiting for large sites.

### 7.1 Fully Supported Features

- Site/web property retrieval
- List and library enumeration
- List item retrieval with paging
- Folder traversal
- SharePoint group enumeration
- SharePoint group member retrieval
- Role assignment retrieval
- Role definition binding retrieval
- Azure AD group info retrieval
- Azure AD transitive member retrieval

### 7.2 Features Requiring Workarounds

| Feature | Challenge | Workaround |
|---------|-----------|------------|
| `Load-CSOMProperties` batch loading | Not available in Python lib | Multiple REST calls with `$expand` |
| `HasUniqueRoleAssignments` check | Must load per item | Batch with `$select=HasUniqueRoleAssignments` in list query |
| `SharedWithDetails` JSON parsing | Field is JSON string | Python `json.loads()` |
| M365 Group detection | LoginName suffix `_o` | Parse LoginName, strip suffix |

### 7.3 Gaps and Limitations

| Gap | Impact | Mitigation |
|-----|--------|------------|
| No CSOM in Python | Can't use some advanced features | Use REST API equivalents |
| Rate limiting | Large scans may hit limits | Implement backoff and batching |
| Permission scope | App needs broad permissions | Document required permissions |

### 7.4 Required Azure AD App Permissions

**SharePoint**:
- `Sites.FullControl.All` (required for RoleAssignments access - Sites.Read.All is insufficient)

**Note**: App-only auth with certificate recommended. Client secret may not work for all permission operations.

**Microsoft Graph**:
- `GroupMember.Read.All` (read group members)
- `Group.Read.All` (read group info)
- `User.Read.All` (read user info)

## 8. Implementation Recommendations

### 8.1 Recommended Architecture

```
middleware/
├─> routers_v2/
│   └─> permission_scanner.py          # Router with endpoints
├─> common_permission_functions_v2.py  # Core scanning logic
└─> common_graph_functions_v2.py       # Azure AD/Graph operations
```

### 8.2 Recommended Libraries

1. **Office365-REST-Python-Client** - SharePoint REST API
2. **msgraph-sdk** - Microsoft Graph API (Azure AD)
3. **httpx** - Direct REST calls where needed

### 8.3 Implementation Phases

**Phase 1: Core Infrastructure**
- Authentication setup (existing middleware patterns)
- Graph client initialization
- Caching layer for groups

**Phase 2: Site-Level Scanning**
- Site group enumeration
- Group member resolution
- Direct user assignments
- Azure AD group resolution with Graph

**Phase 3: Item-Level Scanning**
- List enumeration with filtering
- Item iteration with paging
- Broken inheritance detection
- Per-item access resolution

**Phase 4: Output Generation**
- CSV file generation matching PowerShell output
- UTF-8 encoding without BOM
- Batch writing

### 8.4 Estimated Effort

| Phase | Effort |
|-------|--------|
| Phase 0 (POC) | 2-3 days |
| Phase 1 | 3-4 days |
| Phase 2 | 4-5 days |
| Phase 3 | 5-7 days |
| Phase 4 | 2-3 days |
| Testing | 3-4 days |
| **Total** | **20-30 days** |

**Assumptions**: POC validates library works with required permissions. Does not include performance optimization for sites >100k items.

## 9. Output File Schemas

### 9.1 01_SiteContents.csv

```csv
Id,Type,Title,Url
```

Types: `Web`, `SUBSITE`, `LIST`, `LIBRARY`, `SITEPAGES`

### 9.2 02_SiteGroups.csv

```csv
Id,Role,Title,PermissionLevel,Owner
```

Roles: `SiteOwners`, `SiteMembers`, `SiteVisitors`, `Custom`

### 9.3 03_SiteUsers.csv

```csv
Id,LoginName,DisplayName,Email,PermissionLevel,ViaGroup,ViaGroupId,ViaGroupType,AssignmentType,NestingLevel,ParentGroup
```

ViaGroupType: `SharePointGroup`, `SecurityGroup`, `M365Group`
AssignmentType: `User`, `Group`

### 9.4 04_IndividualPermissionItems.csv

```csv
Id,Type,Title,Url
```

Types: `SUBSITE`, `LIST`, `LIBRARY`, `FOLDER`, `FILE`, `ITEM`

### 9.5 05_IndividualPermissionItemAccess.csv

```csv
Id,Type,Url,LoginName,DisplayName,Email,PermissionLevel,SharedDateTime,SharedByDisplayName,SharedByLoginName,ViaGroup,ViaGroupId,ViaGroupType,AssignmentType,NestingLevel,ParentGroup
```

AssignmentType: `User`, `Group`, `Direct`, `SharingLink`

## 10. Document History

**[2026-02-03 10:20]**
- Added: SP-07 Site Collection Administrators case
- Added: M365 Groups limitation note for transitiveMembers
- Added: Section 7.0 Performance Considerations with scan time estimates
- Added: POC validation warning for Office365-REST-Python-Client
- Changed: Required permission from Sites.Read.All to Sites.FullControl.All
- Changed: Effort estimate from 12-17 days to 20-30 days (added POC phase)

**[2026-02-03 09:55]**
- Initial assessment created
- Analyzed PowerShell implementation (822 lines)
- Cataloged 13 PnP cmdlets and REST equivalents
- Documented 14 permission cases
- Evaluated 3 Python library options
- Created API mapping table
- Feasibility: CONFIRMED with workarounds
