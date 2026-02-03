# SPEC: SharePoint Permission Insights Scanner

**Doc ID**: SPAPI-SP01
**Goal**: Document the architecture and workflow of the SharePoint Permission Insights Scanner PowerShell solution
**Timeline**: Created 2026-01-28, Updated 0 times
**Target file**: `_Input/PermissionInsightsScanner/PermissionInsightsScanner.ps1`

**Source code:**
- `PermissionInsightsScanner.ps1` (822 lines) - Main scanner script
- `ScanForBrokenPermissionInheritance.ps1` (554 lines) - Broken inheritance scanner
- `_includes.ps1` (397 lines) - Shared utility functions

## MUST-NOT-FORGET

- URL type detection order: SITE > SUBSITE > LIBRARY > FOLDER
- Azure AD group resolution has max nesting level (default: 5)
- Some groups must not be resolved (e.g., "Everyone except external users")
- SharePoint group member cache is cleared per job; Azure AD cache persists
- Output files use UTF-8 encoding without Byte Order Mark (BOM)

## Table of Contents

1. Scenario
2. Context
3. SharePoint Permission Model
4. Domain Objects
5. PnP PowerShell API Endpoints
6. Permission Sources
7. Functional Requirements
8. Design Decisions
9. Implementation Guarantees
10. Key Mechanisms
11. Action Flow
12. Data Structures
13. Implementation Details

## 1. Scenario

**Problem:** SharePoint Online permissions are complex and distributed across sites, subsites, libraries, folders, and individual items. Administrators need visibility into:
- Who has access to what (via groups or direct sharing)
- Where permission inheritance is broken
- How permissions flow through nested Azure AD and SharePoint groups

**Solution:**
- Batch-process multiple SharePoint URLs from CSV input
- Auto-detect URL type (site, subsite, library, folder)
- Export comprehensive permission data to structured CSV files
- Resolve nested group memberships recursively
- Track items with broken permission inheritance

**What we don't want:**
- Manual permission auditing through SharePoint UI
- Incomplete group membership resolution (only top-level)
- Losing progress on long-running scans (no resume capability)

## 2. Context

This solution uses:
- **Patterns and Practices (PnP) PowerShell** for SharePoint Online access
- **Azure Active Directory (Azure AD) PowerShell** (optional) for group member resolution
- **Credential files** stored in user's AppData for authentication

The scanner connects to SharePoint Online using stored credentials and iterates through jobs defined in an input CSV file.

## 3. SharePoint Permission Model

SharePoint permissions follow a hierarchical model with four core components:

### Site Objects (Securable Objects)

Objects that can have permissions assigned, forming an inheritance chain:

```
Site Collection
├─> Site (Web)
│   ├─> List / Library
│   │   ├─> Folder
│   │   │   └─> Item / File
│   │   └─> Item / File
│   └─> Subsite
│       └─> (recursive structure)
```

**Inheritance:** By default, child objects inherit permissions from parents. When inheritance is "broken", the object has unique permissions.

### Permission Levels

Named sets of granular permissions. Standard levels (from highest to lowest risk):

**High Risk (Red):**
- **Full Control** - All available permissions
- **Design** - Full Control without subsites, groups
- **Manage Hierarchy** - Full Control without theming, approval

**Medium Risk (Blue):**
- **Edit** - Full Control without subsites, groups, site settings
- **Contribute** - Edit without list/library settings
- **Approve** - Edit and approval without list/library settings

**Low Risk (Grey):**
- **Read** - View pages, list items, download documents
- **View Only** - Read without download (browser only)
- **Restricted Read** - Read without alerts, versions, user info
- **Restricted Interfaces for Translation** - Read without files, items, pages, alerts

**Special:**
- **Limited Access** - Automatically assigned when item-level sharing breaks inheritance. Grants minimal access to navigate to shared item.

### Granular Permissions

Each Permission Level is composed of granular permissions in three categories:

**List Permissions:**
- Manage Lists, Override List Behaviors, Add Items, Edit Items, Delete Items
- View Items, Approve Items, Open Items, View Versions, Delete Versions
- Create Alerts, View Application Pages

**Site Permissions:**
- Manage Permissions, View Web Analytics Data, Create Subsites, Manage Web Site
- Add and Customize Pages, Apply Themes and Borders, Apply Style Sheets
- Create Groups, Browse Directories, Use Self-Service Site Creation
- View Pages, Enumerate Permissions, Browse User Information
- Manage Alerts, Use Remote Interfaces, Use Client Integration Features
- Open, Edit Personal User Information

**Personal Permissions:**
- Manage Personal Views, Add/Remove Personal Web Parts, Update Personal Web Parts

### Groups and Users

**Default SharePoint Groups:**
- **[Site] Owners** - Full Control
- **[Site] Members** - Edit
- **[Site] Visitors** - Read

**Group Types Recognized by Scanner:**
- `SharePointGroup` - Native SharePoint group
- `M365Group` - Microsoft 365 Group (identified by `_o` suffix in login name)
- `SecurityGroup` - Azure AD Security Group

**Principal Types:**
- `User` - Individual user account
- `SharePointGroup` - SharePoint group
- `SecurityGroup` - Azure AD group (includes M365 groups)

## 4. Domain Objects

### Job

A **Job** represents a single URL to scan from the input file.

**Properties:**
- `Url` - SharePoint URL to scan
- `UrlType` - Detected type: SITE, SUBSITE, LIBRARY, FOLDER, ERROR
- `JobNumber` - Sequential index (1-based)
- `OutputFolder` - Destination folder for CSV outputs

### SiteContent

A **SiteContent** represents a web, list, or library within a site.

**CSV columns:** Id, Type, Title, Url

### SiteGroup

A **SiteGroup** represents a SharePoint permission group.

**CSV columns:** Id, Role, Title, PermissionLevel, Owner

**Role values:** Owners, Members, Visitors, (custom)

### SiteUser

A **SiteUser** represents a user or group with site-level permissions.

**CSV columns:** Id, LoginName, DisplayName, Email, PermissionLevel, ViaGroup, ViaGroupId, ViaGroupType, AssignmentType, NestingLevel, ParentGroup

**ViaGroupType values:** SharePointGroup, Microsoft 365 Group (M365Group), SecurityGroup

### IndividualPermissionItem

An **IndividualPermissionItem** represents a list item with broken permission inheritance.

**CSV columns:** Id, Type, Title, Url

### IndividualPermissionItemAccess

An **IndividualPermissionItemAccess** represents who has access to a specific item with broken inheritance.

**CSV columns:** Id, Type, Url, LoginName, DisplayName, Email, PermissionLevel, SharedDateTime, SharedByDisplayName, SharedByLoginName, ViaGroup, ViaGroupId, ViaGroupType, AssignmentType, NestingLevel, ParentGroup

## 5. PnP PowerShell API Endpoints

The scanner uses PnP PowerShell cmdlets that wrap SharePoint REST API and Client-Side Object Model (CSOM) calls:

### Connection and Authentication

- `Connect-PnPOnline` - Establishes connection to SharePoint site
  - REST: `/_api/contextinfo`
  - Used in: `ensureSharePointSiteIsConnected()`

### Site and Web Operations

- `Get-PnPWeb` - Retrieves current web properties
  - REST: `/_api/web`
  - Properties loaded: `HasUniqueRoleAssignments`, `RoleAssignments`

- `Get-PnPSubWeb` - Retrieves subsites recursively
  - REST: `/_api/web/webs`
  - Properties loaded: `HasUniqueRoleAssignments`, `RoleAssignments`

### Folder Operations

- `Get-PnPFolder` - Retrieves folder by server-relative URL
  - REST: `/_api/web/GetFolderByServerRelativeUrl('[url]')`
  - Properties loaded: `ParentFolder`
  - Used for: URL type detection (LIBRARY vs FOLDER)

### List Operations

- `Get-PnPList` - Retrieves all lists in current web
  - REST: `/_api/web/lists`
  - Properties loaded: `HasUniqueRoleAssignments`, `DefaultViewUrl`
  - Filtered by: `BaseTemplate` (100=LIST, 101=LIBRARY, 119=SITEPAGES)

- `Get-PnPListItem` - Retrieves items from a list
  - REST: `/_api/web/lists/getbytitle('[title]')/items`
  - Parameters: `-PageSize 4995` for batch retrieval
  - Fields accessed: `FileRef`, `FileLeafRef`, `FSObjType`, `Title`

### Group Operations

- `Get-PnPGroup` - Retrieves all SharePoint groups
  - REST: `/_api/web/sitegroups`
  - Used to populate `$global:sharePointGroupCache`

- `Get-PnPGroup -AssociatedOwnerGroup` - Default Owners group
  - REST: `/_api/web/AssociatedOwnerGroup`

- `Get-PnPGroup -AssociatedMemberGroup` - Default Members group
  - REST: `/_api/web/AssociatedMemberGroup`

- `Get-PnPGroup -AssociatedVisitorGroup` - Default Visitors group
  - REST: `/_api/web/AssociatedVisitorGroup`

- `Get-PnPGroupMember` - Retrieves members of a SharePoint group
  - REST: `/_api/web/sitegroups/getbyid([id])/users`

### Azure AD Operations

- `Get-PnPAzureADGroup` - Retrieves Azure AD group by ID
  - Graph API: `GET /groups/{id}`
  - Alternative: `Get-AzureADGroup` (Azure AD PowerShell module)

- `Get-PnPAzureADGroupMember` - Retrieves Azure AD group members
  - Graph API: `GET /groups/{id}/members`
  - Alternative: `Get-AzureADGroupMember` (Azure AD PowerShell module)

### Role Assignment Operations

- `Load-CSOMProperties` - Custom function to batch-load CSOM properties
  - Loads: `RoleDefinitionBindings`, `Member`, `PrincipalId`
  - Optimizes API calls by loading multiple properties in single request

- `Get-PnPProperty` - Loads specific properties on CSOM objects
  - Used for: `HasUniqueRoleAssignments` on individual items
  - REST equivalent: `$expand` parameter

### Item-Level Sharing Fields

These list item fields contain sharing information:

- `SharedWithUsers` - Array of users/groups item is shared with
  - Type: User field (lookup)

- `SharedWithDetails` - JSON object with sharing metadata
  - Contains: `DateTime`, `LoginName` of who shared, permission granted
  - Example: `{"user@domain.com": {"DateTime": "2026-01-15T10:30:00", "LoginName": "admin@domain.com"}}`

## 6. Permission Sources

The scanner identifies and tracks different ways users gain access:

### Assignment Types

Tracked in `AssignmentType` column:

**Direct Assignments:**
- `User` - Direct permission grant to individual user at site/list level
- `Direct` - User directly added to item's role assignments

**Group-Based Assignments:**
- `Group` - Access via SharePoint or Azure AD group membership
- `SharingLink` - Access via sharing link (special SharePoint group with `SharingLinks.` prefix)

### Permission Sources by Scope

**Site-Level Sources:**
1. **Site Collection Administrators** - Full control, not visible to site owners in classic UI
2. **Default Groups** (Owners, Members, Visitors) - Associated with site
3. **Custom SharePoint Groups** - Created for specific permission needs
4. **Direct User Assignments** - Users added directly to site's role assignments

**Item-Level Sources (Broken Inheritance):**
1. **Copied Permissions** - When inheritance breaks, parent permissions are copied
2. **Share Dialog** - "Send Link" or "Copy Link" sharing
3. **Manage Access Panel** - Direct permission grants
4. **Programmatic Sharing** - Via API or PowerShell

### Sharing Link Types

When users share via "Send Link" dialog:

- **Anyone with the link** - Anonymous access (if enabled)
- **People in [Organization] with the link** - All authenticated org users
- **People with existing access** - No new permissions, just notification
- **Specific people** - Named users only

Sharing links create special groups prefixed with `SharingLinks.` containing:
- Link type (view/edit)
- Unique identifier (GUID Globally Unique Identifier)
- Permission scope

### Limited Access System Group

When an item is shared with someone who doesn't have site access:

1. User is added to automatic "Limited Access System Group"
2. Group grants `Limited Access` permission level at site and list level
3. Allows user to navigate to shared item without broader site access
4. Scanner filters out `Limited Access` by default (`$ignorePermissionLevels`)

### Group Nesting Hierarchy

```
SharePoint Group
├─> Azure AD Security Group
│   ├─> Nested Azure AD Group (Level 1)
│   │   ├─> Nested Azure AD Group (Level 2)
│   │   │   └─> User (resolved at Level 3)
│   │   └─> User (resolved at Level 2)
│   └─> User (resolved at Level 1)
├─> M365 Group
│   └─> User (group members)
└─> Direct User
```

Scanner resolves up to `$maxGroupNestinglevel` (default: 5) levels.

## 7. Functional Requirements

**SPAPI-FR-01: URL Type Detection**
- Detect SITE, SUBSITE, LIBRARY, FOLDER from input URL
- Handle URL-encoded paths (decode %20, etc.)
- Validate URL starts with `https://` and contains `/sites/`
- Skip invalid URLs with ERROR status

**SPAPI-FR-02: Subsite Loading**
- When URL is SITE or SUBSITE, optionally load all subsites recursively
- Configurable via `$loadSubsites` flag (default: true)
- Known URLs with many subsites can be pre-configured for faster detection

**SPAPI-FR-03: SharePoint Group Resolution**
- Load all SharePoint groups (Owners, Members, Visitors, custom)
- Resolve group members including nested Azure AD groups
- Cache group members per site to avoid duplicate API calls

**SPAPI-FR-04: Azure AD Group Resolution**
- Resolve Azure AD security groups and M365 groups recursively
- Support configurable max nesting level (default: 5)
- Allow specific groups to be excluded from resolution (e.g., "Everyone except external users")
- Distinguish between M365 groups (suffix `_o`) and security groups

**SPAPI-FR-05: Broken Permission Inheritance Scanning**
- For LIBRARY/FOLDER URLs: scan all items for broken inheritance
- For SITE/SUBSITE URLs: scan all lists (except built-in) for broken inheritance
- Record who has access to items with unique permissions

**SPAPI-FR-06: Output File Generation**
- Generate 5 CSV files per job in dedicated output folder
- UTF-8 encoding without BOM
- CSV-escape text values (quotes, commas, newlines)
- Write in batches (configurable: every N lines)

**SPAPI-FR-07: Resume After Interruption**
- Track progress in summary file
- Allow resuming from last successful item on restart
- Configurable via `$resumeAfterInterruption` flag

**SPAPI-FR-08: Permission Level Filtering**
- Ignore specified permission levels (default: "Limited Access")
- Ignore system accounts (SHAREPOINT\system, app@sharepoint)

## 8. Design Decisions

**SPAPI-DD-01:** Use PnP PowerShell over Client-Side Object Model (CSOM). Rationale: PnP provides higher-level cmdlets and better maintenance.

**SPAPI-DD-02:** Store credentials in user's AppData as encrypted SecureString. Rationale: Avoids storing passwords in scripts while enabling unattended execution.

**SPAPI-DD-03:** Separate Azure AD cache from SharePoint cache. Rationale: Azure AD groups are tenant-wide; SharePoint groups are site-specific. Azure cache persists across jobs.

**SPAPI-DD-04:** Output folder naming uses job number + URL part. Rationale: Enables easy identification and sorting of output folders.

**SPAPI-DD-05:** Skip built-in lists during broken inheritance scan. Rationale: Built-in lists have system-level permissions that are not user-manageable.

## 9. Implementation Guarantees

**SPAPI-IG-01:** All users with site access are captured, regardless of assignment type (direct, SharePoint group, Azure AD group, nested group).

**SPAPI-IG-02:** Group nesting is resolved up to configured max level to prevent infinite loops with circular group memberships.

**SPAPI-IG-03:** Output files are valid CSV that can be opened in Excel or Power BI without manual fixes.

**SPAPI-IG-04:** Long-running scans can be resumed without losing already-scanned data.

## 10. Key Mechanisms

### Credential Storage

Passwords stored as encrypted SecureString in `%LOCALAPPDATA%\[username].txt`:
```powershell
"PASSWORD" | ConvertTo-SecureString -AsPlainText -Force | ConvertFrom-SecureString | Out-File "$env:LOCALAPPDATA\user.txt"
```

### URL Type Detection Algorithm

```
Input: URL string
1. If no path after /sites/[name] → SITE
2. Try Get-PnPFolder on path
   2a. If folder's parent is site root → LIBRARY
   2b. Otherwise → FOLDER
3. If Get-PnPFolder fails, check if path matches subsite → SUBSITE
4. Otherwise → ERROR
```

### Group Member Caching

```
$global:azureGroupMemberCache    # Key: Azure group Globally Unique Identifier (GUID), persists across jobs
$global:sharePointGroupMemberCache  # Key: SP group ID, cleared per job
$global:userDisplayNameCache     # Key: login name, cleared per job
$global:sharePointGroupCache     # Key: principal ID, cleared per job
```

### CSV Escaping

Text values are escaped if they contain: `+ - = / , " \n` or look like dates/numbers:
```powershell
function CSV-Escape-Text ($value) {
    if ($value -match '^([+\-=\/]*[\.\d\s\/\:]*|.*[\,\"\n].*|[\n]*)$') {
        return '"' + $value.Replace('"','""') + '"'
    }
    return $value
}
```

## 11. Action Flow

```
User runs PermissionInsightsScanner.ps1
├─> Load _includes.ps1
├─> Get credentials (from file or prompt)
├─> Connect to Azure AD (if $useAzureActiveDirectoryPowerShellModule)
├─> Read input CSV (jobs)
└─> For each job:
    ├─> Detect URL type (SITE/SUBSITE/LIBRARY/FOLDER)
    ├─> Connect to SharePoint site
    ├─> Load subsites (if enabled and SITE/SUBSITE)
    ├─> Create output folder (NNNN [site-url-part])
    │
    ├─> Step 4: Site Groups and Users
    │   ├─> Load site groups (Owners, Members, Visitors, custom)
    │   ├─> For each group:
    │   │   ├─> Get permission level
    │   │   ├─> Get members (recursive if Azure AD)
    │   │   └─> Write to 02_SiteGroups.csv, 03_SiteUsers.csv
    │   └─> Load direct role assignments (non-group users)
    │
    ├─> Step 5: Broken Permission Inheritance
    │   ├─> Load lists (filter by template, exclude built-in)
    │   ├─> For each list item:
    │   │   ├─> Check HasUniqueRoleAssignments
    │   │   ├─> If broken: record item + all access entries
    │   │   └─> Write to 04_IndividualPermissionItems.csv,
    │   │       05_IndividualPermissionItemAccess.csv
    │   └─> Write progress to summary file
    │
    └─> Clear site-specific caches
```

## 12. Data Structures

### Input File

**File:** `PermissionInsightsScanner-In.csv`

```csv
Url
https://tenant.sharepoint.com/sites/site1/
https://tenant.sharepoint.com/sites/site1/Subsite
https://tenant.sharepoint.com/sites/site1/Shared%20Documents
https://tenant.sharepoint.com/sites/site1/Shared%20Documents/Folder
```

### Output Files

**01_SiteContents.csv:**
```csv
Id,Type,Title,Url
1,Web,Site Name,https://tenant.sharepoint.com/sites/site1
2,List,Documents,https://tenant.sharepoint.com/sites/site1/Shared Documents
```

**02_SiteGroups.csv:**
```csv
Id,Role,Title,PermissionLevel,Owner
5,Owners,Site1 Owners,"Full Control",
6,Members,Site1 Members,"Edit",
7,Visitors,Site1 Visitors,"Read",
```

**03_SiteUsers.csv:**
```csv
Id,LoginName,DisplayName,Email,PermissionLevel,ViaGroup,ViaGroupId,ViaGroupType,AssignmentType,NestingLevel,ParentGroup
1,user@tenant.com,John Doe,user@tenant.com,"Full Control",Site1 Owners,5,SharePointGroup,Group,1,
```

**04_IndividualPermissionItems.csv:**
```csv
Id,Type,Title,Url
42,File,Confidential.docx,https://tenant.sharepoint.com/sites/site1/Shared Documents/Confidential.docx
```

**05_IndividualPermissionItemAccess.csv:**
```csv
Id,Type,Url,LoginName,DisplayName,Email,PermissionLevel,SharedDateTime,SharedByDisplayName,SharedByLoginName,ViaGroup,ViaGroupId,ViaGroupType,AssignmentType,NestingLevel,ParentGroup
42,File,https://...,user@tenant.com,John Doe,user@tenant.com,"Edit",2026-01-15T10:30:00,Jane Admin,admin@tenant.com,,,,Direct,0,
```

### Summary File

**File:** `PermissionInsightsScanner-Summary.csv`

```csv
Job,LastLib,LastItem,Type,ScannedItems,BrokenPermissions,Url
  1,  5,   1234,SITE   ,   5000,     42,https://tenant.sharepoint.com/sites/site1
  2,  1,    500,LIBRARY,    500,      3,https://tenant.sharepoint.com/sites/site1/Shared Documents
```

## 13. Implementation Details

### Configuration Variables

**User-configurable:**
- `$writeEveryXLines` - Batch write interval (default: 100)
- `$logEveryXFiles` - Console log interval (default: 50)
- `$doNotResolveTheseGroups` - Groups to skip resolving
- `$ignoreAccounts` - System accounts to exclude
- `$ignorePermissionLevels` - Permission levels to exclude (default: "Limited Access")
- `$loadSubsites` - Enable subsite scanning (default: true)
- `$maxGroupNestinglevel` - Max Azure group nesting (default: 5)
- `$useAzureActiveDirectoryPowerShellModule` - Use AAD module vs PnP (default: true)

**Developer-configurable:**
- `$builtInLists` - Lists to exclude from scanning (48 entries)
- `$loadListIfTemplateMatches` - List templates to include (100=LIST, 101=LIBRARY, 119=SITEPAGES)

### Key Functions

**Main Script:**
- `ensureSharePointSiteIsConnected()` - Connect/reconnect to site
- `GetListUrl()` - Extract list URL from list object
- `addGroupAndGroupMembersToOutputLines()` - Process SharePoint group
- `getSharePointGroupMembers()` - Resolve SP group members
- `getAzureGroupMembers()` - Resolve Azure AD group members (recursive)
- `appendToFile()` - Batch write to CSV file

**Include File:**
- `Get-CredentialsOfUser()` - Load or create credentials
- `CSV-Escape-Text()` - Escape CSV values
- `Write-ScriptHeader()` / `Write-ScriptFooter()` - Execution timing
- `ConvertSharePointFieldToTextOrValueType()` - Convert SP field types

### Dependencies

- PnP.PowerShell module
- AzureAD module (optional, for faster group resolution)
- PowerShell 5.1+

## Document History

**[2026-01-28 16:00]**
- Added: Section 3 "SharePoint Permission Model" with permission levels, granular permissions, groups
- Added: Section 5 "PnP PowerShell API Endpoints" with REST API mappings
- Added: Section 6 "Permission Sources" with assignment types, sharing links, Limited Access
- Updated: Table of Contents to reflect new sections

**[2026-01-28 15:50]**
- Fixed: Expanded acronyms on first use (PnP, Azure AD, CSOM, BOM, M365, GUID)

**[2026-01-28 15:45]**
- Initial specification created from code analysis
- Documented 8 functional requirements
- Documented 5 design decisions
- Documented 4 implementation guarantees
