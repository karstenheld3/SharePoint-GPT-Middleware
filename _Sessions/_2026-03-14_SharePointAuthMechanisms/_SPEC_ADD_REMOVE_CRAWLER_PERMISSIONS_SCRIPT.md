# SPEC: Add/Remove Crawler Permissions Script - Dual Target Support

**Doc ID**: ARCP-SP01
**Feature**: CRAWLER_PERMISSIONS_DUAL_TARGET
**Goal**: Extend AddRemoveCrawlerPermissions.ps1 to manage API permissions for both Service Principal and Managed Identity
**Timeline**: Created 2026-03-15

**Target file**: `AddRemoveCrawlerPermissions.ps1`

**Depends on:**
- `_V2_SPEC_SHAREPOINT_AUTHENTICATION.md [SPAUTH-SP01]` for authentication architecture
- `_SPEC_ADD_REMOVE_CRAWLER_SITES_SCRIPT.md [ARCS-SP01]` for dual-target pattern

## MUST-NOT-FORGET

- `CRAWLER_MANAGED_IDENTITY_OBJECT_ID` is optional in .env (script must handle absence gracefully)
- Service Principal uses `Update-AzADApplication` for API permissions
- Managed Identity uses `New-MgServicePrincipalAppRoleAssignment` for API permissions (different mechanism)
- Menu numbering: 1=Both, 2=SP only, 3=MI only (consistent with ARCS-SP01)
- Admin consent URL differs between SP and MI

## Table of Contents

1. [Scenario](#1-scenario)
2. [Context](#2-context)
3. [Domain Objects](#3-domain-objects)
4. [Functional Requirements](#4-functional-requirements)
5. [Design Decisions](#5-design-decisions)
6. [Implementation Guarantees](#6-implementation-guarantees)
7. [Key Mechanisms](#7-key-mechanisms)
8. [Action Flow](#8-action-flow)
9. [Menu Flow](#9-menu-flow)
10. [Implementation Details](#10-implementation-details)
11. [Document History](#11-document-history)

## 1. Scenario

**Problem:** The current `AddRemoveCrawlerPermissions.ps1` only manages API permissions for the Service Principal (`CRAWLER_CLIENT_ID`). With Managed Identity support, we need to also grant SharePoint `Sites.Selected` permission to the Managed Identity. Currently there's no script to do this.

**Solution:**
- Extend script to read `CRAWLER_MANAGED_IDENTITY_OBJECT_ID` from .env
- Add target selection menu (Both, SP only, MI only) consistent with ARCS-SP01
- Check and display permission status for both targets
- Grant/revoke permissions for selected target(s)
- Provide admin consent URLs for both targets

**What we don't want:**
- Separate scripts for SP vs MI (duplication, divergence risk)
- Always requiring MI ID (local-only setups may not have MI)
- Different menu patterns than ARCS-SP01 (consistency matters)
- Silent failures when MI permission grant fails

## 2. Context

The script `AddRemoveCrawlerPermissions.ps1` manages Azure AD API permissions for the crawler application. It:
- Configures Microsoft Graph permissions (Group.Read.All, GroupMember.Read.All, User.Read.All)
- Configures SharePoint permission (Sites.Selected)
- Uses Azure PowerShell (`Az.Resources`) to update app registration

For Managed Identity, API permissions work differently:
- MI doesn't have an "app registration" to update
- Permissions are granted via `New-MgServicePrincipalAppRoleAssignment`
- Only SharePoint Sites.Selected is needed (Graph permissions are for the app, not MI)

## 3. Domain Objects

### Target

A **Target** represents an Azure AD identity that needs API permissions.

**Types:**
- `service_principal` - App Registration identified by `CRAWLER_CLIENT_ID`
- `managed_identity` - Managed Identity identified by `CRAWLER_MANAGED_IDENTITY_OBJECT_ID`
- `both` - Both targets (default for standard operations)

### PermissionSet

A **PermissionSet** defines required API permissions per target.

**Service Principal permissions:**
- Microsoft Graph: Group.Read.All, GroupMember.Read.All, User.Read.All
- SharePoint: Sites.Selected

**Managed Identity permissions:**
- SharePoint: Sites.Selected (only this is needed)

### PermissionStatus

A **PermissionStatus** represents the current state of a permission.

**Properties:**
- `name` - Permission name (e.g., "Sites.Selected")
- `id` - Permission GUID
- `resourceId` - Resource app ID (Graph or SharePoint)
- `configured` - Boolean, whether permission is in app manifest
- `granted` - Boolean, whether admin consent is granted

## 4. Functional Requirements

**ARCP-FR-01: Configuration Validation**
- Read `CRAWLER_CLIENT_ID` from .env (required)
- Read `CRAWLER_MANAGED_IDENTITY_OBJECT_ID` from .env (optional)
- Display which targets are configured at startup
- If MI ID not configured, hide MI-related menu options

**ARCP-FR-02: Azure Connection**
- Connect to Azure using `Connect-AzAccount`
- Validate tenant and subscription access
- Import required modules: Az.Accounts, Az.Resources, Microsoft.Graph

**ARCP-FR-03: Permission Status Check**
- For Service Principal: check Graph + SharePoint permissions via `Get-AzADApplication`
- For Managed Identity: check SharePoint Sites.Selected via `Get-MgServicePrincipalAppRoleAssignment`
- Display side-by-side status with OK/MISSING indicators

**ARCP-FR-04: Action Menu**
- Option 1: Add missing permissions
- Option 2: Remove permissions
- Option 3: Exit
- Show count of missing permissions in menu
- After each operation: re-check permissions, refresh status display
- Loop back to menu until user selects Exit

**ARCP-FR-05: Target Selection**
- After action selection, prompt for target
- Options: 1-Both (default), 2-Service Principal only, 3-Managed Identity only
- Option 1 shown only if both targets configured
- Option 3 shown only if MI configured
- Consistent with ARCS-SP01 numbering

**ARCP-FR-06: Add Permissions**
- For Service Principal: use `Update-AzADApplication -RequiredResourceAccess`
- For Managed Identity: use `New-MgServicePrincipalAppRoleAssignment`
- Show per-target success/failure results
- Provide admin consent URLs after adding

**ARCP-FR-07: Remove Permissions**
- For Service Principal: remove from RequiredResourceAccess, revoke assignments
- For Managed Identity: use `Remove-MgServicePrincipalAppRoleAssignment`
- Confirm before removing
- Show per-target results

**ARCP-FR-08: Admin Consent URLs**
- Display admin consent URL for Service Principal (existing behavior)
- Display admin consent URL for Managed Identity (different URL format)
- Clear instructions on what to do next

## 5. Design Decisions

**ARCP-DD-01:** Target selection per-operation, not per-session. Rationale: Consistent with ARCS-SP01 pattern.

**ARCP-DD-02:** Default target is "Both" when both configured. Rationale: Standard use case is configuring both; reduces clicks.

**ARCP-DD-03:** MI only needs Sites.Selected, not Graph permissions. Rationale: Graph permissions are for app-level operations; MI only needs SharePoint access.

**ARCP-DD-04:** Use Microsoft.Graph module for MI permissions. Rationale: `Az.Resources` doesn't support MI app role assignments directly.

**ARCP-DD-05:** Menu numbering 1=Both, 2=SP, 3=MI matches ARCS-SP01. Rationale: Consistency across scripts reduces user confusion.

## 6. Implementation Guarantees

**ARCP-IG-01:** If `CRAWLER_MANAGED_IDENTITY_OBJECT_ID` is not set, all MI menu options are hidden. Script behaves identically to current version.

**ARCP-IG-02:** Existing Service Principal functionality unchanged. Same validation, error handling, output format.

**ARCP-IG-03:** Operations are independent per target. Failure on SP does not prevent attempt on MI, and vice versa.

**ARCP-IG-04:** Menu numbering is consistent: 1=Both, 2=SP, 3=MI. Unavailable options shown as disabled with explanation.

## 7. Key Mechanisms

### Permission IDs

```powershell
# Resource IDs
$graphResourceId      = "00000003-0000-0000-c000-000000000000"  # Microsoft Graph
$sharepointResourceId = "00000003-0000-0ff1-ce00-000000000000"  # SharePoint

# Microsoft Graph permissions (Application)
$graphPermissions = @{
  "Group.Read.All"       = "5b567255-7703-4780-807c-7be8301ae99b"
  "GroupMember.Read.All" = "98830695-27a2-44f7-8c18-0c3ebc9698f6"
  "User.Read.All"        = "df021288-bdef-4463-88db-98f22de89214"
}

# SharePoint permission (Application)
$sharepointSitesSelected = "20d37865-089c-4dee-8c41-6967602d4ac8"
```

### MI Permission Grant Mechanism

```powershell
# Get SharePoint service principal
$sharepointSp = Get-MgServicePrincipal -Filter "appId eq '00000003-0000-0ff1-ce00-000000000000'"

# Grant Sites.Selected to Managed Identity
$params = @{
  PrincipalId = $managedIdentityObjectId
  ResourceId  = $sharepointSp.Id
  AppRoleId   = "20d37865-089c-4dee-8c41-6967602d4ac8"  # Sites.Selected
}
New-MgServicePrincipalAppRoleAssignment -ServicePrincipalId $managedIdentityObjectId -BodyParameter $params
```

### MI Permission Check Mechanism

```powershell
# Get current app role assignments for MI
$assignments = Get-MgServicePrincipalAppRoleAssignment -ServicePrincipalId $managedIdentityObjectId

# Check if Sites.Selected is assigned
$hasSitesSelected = $assignments | Where-Object { $_.AppRoleId -eq "20d37865-089c-4dee-8c41-6967602d4ac8" }
```

## 8. Action Flow

### Startup

```
Script starts
├─> Read .env file
├─> Validate CRAWLER_CLIENT_ID (required)
├─> Check CRAWLER_MANAGED_IDENTITY_OBJECT_ID (optional)
│   ├─> Present: $hasManagedIdentity = $true
│   └─> Absent: $hasManagedIdentity = $false
├─> Display configuration summary
│   ├─> "Service Principal: [CRAWLER_CLIENT_ID]"
│   └─> "Managed Identity: [MI_ID]" or "not configured"
└─> Connect to Azure (Az + Microsoft.Graph)
```

### Permission Check

```
Check permissions
├─> For Service Principal:
│   ├─> Get-AzADApplication -ApplicationId
│   ├─> Check Graph permissions (Group.Read.All, etc.)
│   └─> Check SharePoint Sites.Selected
├─> For Managed Identity (if configured):
│   ├─> Get-MgServicePrincipalAppRoleAssignment
│   └─> Check SharePoint Sites.Selected
└─> Display status with OK/MISSING indicators
```

### Add Operation

```
User selects "Add missing permissions"
├─> Prompt: Select target (1-Both, 2-SP, 3-MI)
├─> For Service Principal:
│   ├─> Update-AzADApplication -RequiredResourceAccess
│   └─> Show result: "Service Principal: OK" or "FAIL: [error]"
├─> For Managed Identity:
│   ├─> New-MgServicePrincipalAppRoleAssignment
│   └─> Show result: "Managed Identity: OK" or "FAIL: [error]"
└─> Display admin consent URLs
```

### Remove Operation

```
User selects "Remove permissions"
├─> Prompt: Confirm removal (yes/no)
├─> Prompt: Select target (1-Both, 2-SP, 3-MI)
├─> For Service Principal:
│   ├─> Remove from RequiredResourceAccess
│   ├─> Remove-AzADServicePrincipalAppRoleAssignment
│   └─> Show result
├─> For Managed Identity:
│   ├─> Remove-MgServicePrincipalAppRoleAssignment
│   └─> Show result
└─> Display summary
```

## 9. Menu Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ STARTUP                                                         │
├─────────────────────────────────────────────────────────────────┤
│ ========================================                        │
│ API Permission Management                                       │
│ ========================================                        │
│ Service Principal: 6e2f7cac-... (SharePoint-GPT-Crawler)        │
│ Managed Identity:  abc12345-... (configured)                    │
│   -or-                                                          │
│ Managed Identity:  not configured                               │
│                                                                 │
│ Connecting to Azure...                                          │
│   Connected successfully to tenant: whizzyapps.onmicrosoft.com  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────────┐
│ PERMISSION STATUS                                               │
├─────────────────────────────────────────────────────────────────┤
│ Checking current permissions...                                 │
│                                                                 │
│ Service Principal:                                              │
│   Microsoft Graph:                                              │
│     OK: Group.Read.All                                          │
│     OK: GroupMember.Read.All                                    │
│     OK: User.Read.All                                           │
│   SharePoint:                                                   │
│     OK: Sites.Selected                                          │
│                                                                 │
│ Managed Identity:                                               │
│   SharePoint:                                                   │
│     MISSING: Sites.Selected                                     │
│                                                                 │
│ Summary: 1 missing permission(s)                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────────┐
│ ACTION MENU                                                     │
├─────────────────────────────────────────────────────────────────┤
│ ========================================                        │
│ Permission Management Menu                                      │
│ ========================================                        │
│ Please select an option:                                        │
│   1 - Add missing permissions (1 missing)                       │
│   2 - Remove permissions                                        │
│   3 - Exit                                                      │
│                                                                 │
│ Select option [1]: _                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              v               │               v
┌─────────────────────────────┐   ┌─────────────────────────────────┐
│ ADD PERMISSIONS             │   │ REMOVE PERMISSIONS              │
├─────────────────────────────┤   ├─────────────────────────────────┤
│ Select target:              │   │ WARNING: This will remove API   │
│   1 - Both (default)        │   │ permissions from selected       │
│   2 - Service Principal     │   │ target(s).                      │
│   3 - Managed Identity      │   │                                 │
│                             │   │ Are you sure? (yes/no) [no]: _  │
│ Select target [1]: _        │   │                                 │
│                             │   │ Select target:                  │
│ Adding permissions...       │   │   1 - Both (default)            │
│   Service Principal:        │   │   2 - Service Principal         │
│     All already configured  │   │   3 - Managed Identity          │
│   Managed Identity:         │   │                                 │
│     Adding Sites.Selected...│   │ Removing permissions...         │
│     OK: Sites.Selected      │   │   Service Principal: OK         │
│                             │   │   Managed Identity: OK          │
└─────────────────────────────┘   └─────────────────────────────────┘
              │                               │
              v                               v
┌─────────────────────────────┐   ┌─────────────────────────────────┐
│ ADMIN CONSENT (Add only)    │   │                                 │
├─────────────────────────────┤   │                                 │
│ Service Principal URL:      │   │                                 │
│ https://login.../{tenant}/  │   │                                 │
│   adminconsent?client_id=   │   │                                 │
│   {sp_client_id}            │   │                                 │
│                             │   │                                 │
│ Managed Identity URL:       │   │                                 │
│ https://login.../{tenant}/  │   │                                 │
│   adminconsent?client_id=   │   │                                 │
│   {mi_object_id}            │   │                                 │
└─────────────────────────────┘   └─────────────────────────────────┘
              │                               │
              └───────────────┬───────────────┘
                              v
                   ┌──────────────────┐
                   │ Re-check perms   │
                   │ (refresh status) │
                   └────────┬─────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
            v                               v
     (Loop back to               (User selects Exit)
      PERMISSION STATUS)                    │
            │                               v
            │              ┌─────────────────────────────────────────┐
            │              │ COMPLETION                              │
            │              ├─────────────────────────────────────────┤
            │              │ Permission configuration completed!     │
            │              └─────────────────────────────────────────┘
            │
            └─────────────────> (back to PERMISSION STATUS box above)
```

## 10. Implementation Details

### Module Requirements

```powershell
# Required modules
Import-Module Az.Accounts
Import-Module Az.Resources
Import-Module Microsoft.Graph.Applications  # For MI operations
```

### Function Signatures

```powershell
# Check SP permissions (existing)
function Get-AppPermissions {
  param(
    [Parameter(Mandatory=$true)] [string]$ClientId,
    [Parameter(Mandatory=$true)] [string]$ResourceId
  )
  # Returns: array of permission GUIDs
}

# Check MI permissions (new)
function Get-ManagedIdentityPermissions {
  param(
    [Parameter(Mandatory=$true)] [string]$ObjectId
  )
  # Returns: array of app role assignment objects
}

# Add permission to MI (new)
function Add-ManagedIdentityPermission {
  param(
    [Parameter(Mandatory=$true)] [string]$ObjectId,
    [Parameter(Mandatory=$true)] [string]$ResourceAppId,
    [Parameter(Mandatory=$true)] [string]$AppRoleId
  )
  # Returns: success/failure
}

# Remove permission from MI (new)
function Remove-ManagedIdentityPermission {
  param(
    [Parameter(Mandatory=$true)] [string]$ObjectId,
    [Parameter(Mandatory=$true)] [string]$AssignmentId
  )
  # Returns: success/failure
}

# Target selection menu (new, matches ARCS-SP01 pattern)
function Get-TargetSelection {
  param(
    [bool]$HasBothTargets,
    [bool]$HasManagedIdentity
  )
  # Returns: "1", "2", or "3"
}
```

## 11. Document History

**[2026-03-15 19:19]**
- Fixed: Removed duplicate COMPLETION box from Menu Flow
- Fixed: Clarified loop flow with permission status refresh step
- Added: ARCP-FR-04 requirement to re-check permissions after each operation

**[2026-03-15 19:17]**
- Added: ARCP-FR-04 loop behavior - menu repeats until Exit selected
- Changed: Menu Flow diagram to show loop back to ACTION MENU

**[2026-03-15 19:15]**
- Added: Action Flow section (section 8)
- Changed: Menu Flow to use ASCII box diagrams matching ARCS-SP01 style

**[2026-03-15 19:12]**
- Fixed: Target selection menu numbering when MI not configured (keep 1/2/3 pattern)

**[2026-03-15 19:11]**
- Initial specification created
- Menu flow designed to match ARCS-SP01 consistency
- Dual-target support for SP + MI
