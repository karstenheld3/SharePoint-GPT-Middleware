# SPEC: Add/Remove Crawler Sites Script - Managed Identity Client ID Support

**Doc ID**: ARCS-SP01
**Feature**: CRAWLER_SITES_MI_SUPPORT
**Goal**: Extend AddRemoveCrawlerSharePointSites.ps1 to manage Sites.Selected permissions for both Service Principal Client ID and Managed Identity Client ID
**Timeline**: Created 2026-03-15

**Target file**: `AddRemoveCrawlerSharePointSites.ps1`

**Depends on:**
- `_V2_SPEC_SHAREPOINT_AUTHENTICATION.md [SPAUTH-SP01]` for authentication architecture

## MUST-NOT-FORGET

- `CRAWLER_MANAGED_IDENTITY_OBJECT_ID` is optional in .env (script must handle absence gracefully)
- Target selection menu (1-Both, 2-Cert, 3-MI) appears for BOTH add AND remove operations
- Discovery phase always scans BOTH apps if both are configured
- Sites.Selected permission grant uses `Grant-PnPAzureADAppSitePermission -AppId`
- Managed Identity (MI) uses its **Object ID** (Principal ID) for `Grant-PnPAzureADAppSitePermission -AppId` [VERIFIED]

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

**Problem:** The crawler now supports two authentication methods: Certificate-based App Registration and Managed Identity Client ID. Both require Sites.Selected permissions granted per-site. The current script only manages permissions for `CRAWLER_CLIENT_ID`. Administrators need to grant/revoke permissions to both identities efficiently.

**Solution:**
- Extend script to read `CRAWLER_MANAGED_IDENTITY_OBJECT_ID` from .env
- Add target selection menu (Both, Certificate only, MI only) for add/remove operations
- Discovery phase scans both apps, shows side-by-side permission status
- Standard use case: grant to BOTH with single operation

**What we don't want:**
- Separate scripts for Certificate vs MI (duplication, divergence risk)
- Always requiring both IDs (MI is optional for local-only setups)
- Hidden/automatic target selection (admin must explicitly choose)

## 2. Context

The script `AddRemoveCrawlerSharePointSites.ps1` manages SharePoint Sites.Selected permissions for the crawler application. It:
- Reads configuration from `.env` file
- Connects to SharePoint Admin Center via PnP PowerShell
- Discovers existing permissions by scanning all sites
- Provides menu to add new sites or remove existing permissions

With the introduction of Managed Identity Client ID authentication (`CRAWLER_USE_MANAGED_IDENTITY=true`), the same Sites.Selected permissions must be granted to the Managed Identity Client ID's service principal. This script extension enables managing permissions for both identities.

## 3. Domain Objects

### Target

A **Target** represents an Azure AD identity (App Registration or Managed Identity Client ID) that needs Sites.Selected permissions.

**Types:**
- `service_principal` - App Registration identified by `CRAWLER_CLIENT_ID`
- `managed_identity` - Managed Identity Client ID identified by `CRAWLER_MANAGED_IDENTITY_OBJECT_ID`
- `both` - Both targets (default for standard operations)

### TargetConfig

A **TargetConfig** holds the identifiers and display names for a target.

**Properties:**
- `id` - Client ID (Service Principal or Managed Identity)
- `displayName` - From `CRAWLER_CLIENT_NAME` or derived
- `type` - `service_principal` or `managed_identity`
- `configured` - Boolean, whether the ID is present in .env

### SitePermissionStatus

A **SitePermissionStatus** represents the permission state for a site across both targets.

**Properties:**
- `url` - SharePoint site URL
- `title` - Site title
- `certificateAppRoles` - Permission roles for Service Principal Client ID (read, write, fullcontrol, or null)
- `managedIdentityRoles` - Permission roles for Managed Identity Client ID (read, write, fullcontrol, or null)
- `certificateAppPermissionId` - PnP permission ID for revocation
- `managedIdentityPermissionId` - PnP permission ID for revocation

## 4. Functional Requirements

**ARCS-FR-01: Configuration Validation**
- Read `CRAWLER_CLIENT_ID` from .env (required)
- Read `CRAWLER_MANAGED_IDENTITY_OBJECT_ID` from .env (optional)
- If MI ID not configured, skip MI-related menu options and operations
- Display which targets are configured at startup

**ARCS-FR-02: Discovery Phase**
- Prompt user before scanning:
  ```
  1 - Scan for existing sites in Sites.Selected
  2 - Skip (proceed directly to add new site)
  ```
- If scan selected: scan all SharePoint sites for permissions granted to BOTH identities (if both configured)
- Build merged list of sites with permission status per target
- Display side-by-side status: `Service Principal Client ID: write  MI: (none)`
- If skip selected: proceed to add menu only (no remove options available)

**ARCS-FR-03: Action Menu**
- Option 1: Add new site
- Options 2-N: Remove site (one per discovered site)
- Option Q: Quit
- Show target summary in menu header
- Loop back to menu after each operation until user selects Quit

**ARCS-FR-04: Target Selection for Add**
- After entering site URL and permission level, prompt for target
- Options: 1-Both (default), 2-Service Principal Client ID only, 3-Managed Identity Client ID only
- Option 1 shown only if both IDs configured
- Option 3 shown only if MI ID configured
- Execute grant for selected target(s)

**ARCS-FR-05: Target Selection for Remove**
- After selecting site to remove, prompt for target
- Options: 1-Both (default), 2-Service Principal Client ID only, 3-Managed Identity Client ID only
- Option availability based on which targets have permissions on that site
- Execute revoke for selected target(s)

**ARCS-FR-06: Per-Target Operation Results**
- Show success/failure per target: `Service Principal Client ID: OK  Managed Identity Client ID: FAIL: [error]`
- Continue with remaining targets even if one fails
- Summary at end: all succeeded, partial, all failed

**ARCS-FR-07: Access Test**
- Test access for BOTH identities when possible
- Service Principal: Always testable via certificate authentication
- Managed Identity: Testable only when running in Azure (VM, App Service, etc.)
- Detect MI runtime availability via Azure Instance Metadata Service (IMDS) endpoint
- Show explicit certificate details before testing:
  ```
  Testing Service Principal access...
    Client ID:   6e2f7cac-37d7-496f-b72e-347de0aa3999
    Certificate: E:\Dev\SharePoint-GPT-Middleware\.localstorage\...\SharePoint-GPT-Crawler.pfx
  ```
- Output format per site:
  ```
  [1] https://contoso.sharepoint.com/sites/Site1
      Service Principal: fullcontrol  ACCESS=OK (5 lists, 8 libraries)
      Managed Identity:  fullcontrol  ACCESS=OK (5 lists, 8 libraries)
  ```
- When MI runtime not available:
  ```
      Managed Identity:  fullcontrol  ACCESS=SKIP (no MI runtime)
  ```

**ARCS-FR-08: MI Runtime Detection**
- Check Azure IMDS endpoint: `http://169.254.169.254/metadata/identity/oauth2/token`
- Timeout: 2 seconds (fast fail on non-Azure machines)
- If available: use `Connect-PnPOnline -ManagedIdentity` for MI access tests
- If unavailable: skip MI access test, show permission status only

## 5. Design Decisions

**ARCS-DD-01:** Target selection per-operation, not per-session. Rationale: Allows mixed operations (add to both, remove from one) without restarting script.

**ARCS-DD-02:** Default target is "Both" when both IDs configured. Rationale: Standard use case is granting to both; reduces clicks for common case.

**ARCS-DD-03:** Discovery always scans both targets if configured. Rationale: Admin needs full visibility regardless of intended operation.

**ARCS-DD-04:** MI ID is optional in .env. Rationale: Local development setups may not have MI configured; script should remain functional.

**ARCS-DD-05:** Use same `Grant-PnPAzureADAppSitePermission` cmdlet for both targets. Rationale: PnP PowerShell supports granting to any Azure AD application by AppId, including Managed Identity Client ID service principals.

## 6. Implementation Guarantees

**ARCS-IG-01:** If `CRAWLER_MANAGED_IDENTITY_OBJECT_ID` is not set, all MI menu options are hidden. Script behaves identically to current version.

**ARCS-IG-02:** Existing Service Principal Client ID functionality unchanged. Same validation, same error handling, same output format.

**ARCS-IG-03:** Operations are independent per target. Failure on Service Principal Client ID does not prevent attempt on MI, and vice versa.

**ARCS-IG-04:** Menu numbering is consistent: 1=Both, 2=Service Principal, 3=MI. Never changes based on configuration. Selecting unavailable option shows error and re-prompts.

## 7. Key Mechanisms

### Target Configuration Detection

```powershell
$hasCertificateApp = -not [string]::IsNullOrWhiteSpace($config.CRAWLER_CLIENT_ID)
$hasManagedIdentity = -not [string]::IsNullOrWhiteSpace($config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID)
$hasBothTargets = $hasCertificateApp -and $hasManagedIdentity
```

### Target Selection Menu

```powershell
function Get-TargetSelection {
    param(
        [bool]$HasBoth,
        [bool]$HasMI,
        [string]$DefaultChoice = "1"
    )
    
    Write-Host "Select target:"
    if ($HasBoth) {
        Write-Host "  1 - Both: Service Principal Client ID + Managed Identity Client ID (default)"
    } else {
        Write-Host "  1 - Service Principal Client ID (default)"
    }
    Write-Host "  2 - Service Principal Client ID only"
    if ($HasMI) {
        Write-Host "  3 - Managed Identity Client ID only"
    } else {
        Write-Host "  3 - Managed Identity Client ID only [not configured]"
    }
    
    $choice = Read-Host "Enter choice (1-3, default: $DefaultChoice)"
    if ([string]::IsNullOrWhiteSpace($choice)) { $choice = $DefaultChoice }
    
    return $choice
}
```

### Permission Grant to Multiple Targets

```powershell
function Grant-SitePermissionToTargets {
    param(
        [string]$SiteUrl,
        [string]$Role,
        [string[]]$Targets  # "service_principal", "managed_identity", or both
    )
    
    $results = @{}
    
    foreach ($target in $Targets) {
        $appId = if ($target -eq "service_principal") { 
            $config.CRAWLER_CLIENT_ID 
        } else { 
            $config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID 
        }
        $displayName = if ($target -eq "service_principal") {
            $config.CRAWLER_CLIENT_NAME
        } else {
            "Managed Identity Client ID"
        }
        
        try {
            Grant-PnPAzureADAppSitePermission -AppId $appId -DisplayName $displayName -Site $SiteUrl -Permissions $Role -ErrorAction Stop
            $results[$target] = @{ success = $true; error = $null }
        }
        catch {
            $results[$target] = @{ success = $false; error = $_.Exception.Message }
        }
    }
    
    return $results
}
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
│   ├─> "Service Principal Client ID: [CRAWLER_CLIENT_ID]"
│   └─> "Managed Identity Client ID: [MI_ID]" or "Managed Identity Client ID: not configured"
└─> Connect to SharePoint Admin
```

### Discovery

```
Discovery phase
├─> Scan for Service Principal Client ID permissions (always)
├─> Scan for Managed Identity Client ID permissions (if configured)
├─> Merge results by site URL
│   └─> For each site, record:
│       ├─> certificateAppRoles
│       ├─> managedIdentityRoles
│       └─> permissionIds for revocation
└─> Display merged list with side-by-side status
```

### Add Operation

```
User selects "Add new site"
├─> Prompt: Enter site URL
├─> Prompt: Select permission level (1-Read, 2-Write, 3-FullControl)
├─> Prompt: Select target (1-Both, 2-Cert, 3-MI)
├─> For each selected target:
│   ├─> Attempt Grant-PnPAzureADAppSitePermission
│   ├─> On success: "Service Principal Client ID: OK"
│   └─> On failure: "Service Principal Client ID: FAIL: [error]"
│       └─> Try direct site connection method
└─> Display summary
```

### Remove Operation

```
User selects "Remove site X"
├─> Display current permissions for site X
│   ├─> "Service Principal Client ID: write"
│   └─> "Managed Identity Client ID: read"
├─> Prompt: Select target (1-Both, 2-Cert, 3-MI)
├─> For each selected target:
│   ├─> Get permission ID from discovery data
│   ├─> Attempt Revoke-PnPAzureADAppSitePermission
│   ├─> On success: "Service Principal Client ID: OK"
│   └─> On failure: "Service Principal Client ID: FAIL: [error]"
└─> Display summary
```

## 9. Menu Flow

```
┌───────────────────────────────────────────────────────────────┐
│ STARTUP                                                       │
├───────────────────────────────────────────────────────────────┤
│ Managing SharePoint site permissions                          │
│ Service Principal: abc123-... (SharePoint-GPT-Crawler)        │
│ Managed Identity:  def456-... (configured)                    │
│   -or-                                                        │
│ Managed Identity:  not configured                             │
│                                                               │
│ Connecting to SharePoint Admin...                             │
│   Connected successfully                                      │
└───────────────────────────────────────────────────────────────┘
                              │
                              v
┌───────────────────────────────────────────────────────────────┐
│ SCAN PROMPT                                                   │
├───────────────────────────────────────────────────────────────┤
│ Site Discovery                                                │
│   1 - Scan for existing sites in Sites.Selected               │
│   2 - Skip (proceed directly to add new site)                 │
│                                                               │
│ Select option [1]: _                                          │
└───────────────────────────────────────────────────────────────┘
                              │
                              v
┌───────────────────────────────────────────────────────────────┐
│ DISCOVERY (if scan selected)                                  │
├───────────────────────────────────────────────────────────────┤
│ Discovering sites with app permissions...                     │
│                                                               │
│ Testing Service Principal access...                           │
│   Client ID:   abc123-...                                     │
│   Certificate: E:\Dev\...\SharePoint-GPT-Crawler.pfx          │
│                                                               │
│ Currently configured sites:                                   │
│   [1] https://contoso.sharepoint.com/sites/hr                 │
│       SP: write   MI: write   ACCESS=OK (5 lists, 3 libs)     │
│   [2] https://contoso.sharepoint.com/sites/finance            │
│       SP: read    MI: (none)  ACCESS=OK (2 lists, 1 lib)      │
│   [3] https://contoso.sharepoint.com/sites/legal              │
│       SP: (none)  MI: read    ACCESS=SKIP (no SP permission)  │
└───────────────────────────────────────────────────────────────┘
                              │
                              v
┌───────────────────────────────────────────────────────────────┐
│ ACTION MENU                                                   │
├───────────────────────────────────────────────────────────────┤
│ ========================================                      │
│ SharePoint Site Permission Management                         │
│ ========================================                      │
│   1 - Add new site                                            │
│   2 - Remove: .../sites/hr                                    │
│   3 - Remove: .../sites/finance                               │
│   4 - Remove: .../sites/legal                                 │
│   5 - Exit                                                    │
│                                                               │
│ Enter choice (1-5): _                                         │
└───────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              v                               v
┌───────────────────────────┐   ┌───────────────────────────────┐
│ ADD SITE                  │   │ REMOVE SITE                   │
├───────────────────────────┤   ├───────────────────────────────┤
│ Enter site URL: _         │   │ Removing: .../sites/hr        │
│                           │   │                               │
│ Select permission level:  │   │ Current permissions:          │
│   1 - Read (default)      │   │   SP: write   MI: write       │
│   2 - Write               │   │                               │
│   3 - Full Control        │   │ Select target:                │
│                           │   │   1 - Both (default)          │
│ Select target:            │   │   2 - Service Principal only  │
│   1 - Both (default)      │   │   3 - Managed Identity only   │
│   2 - Service Principal   │   │                               │
│   3 - Managed Identity    │   │ Revoking permissions...       │
│                           │   │   Service Principal: OK       │
│ Granting write...         │   │   Managed Identity:  OK       │
│   Service Principal: OK   │   │                               │
│   Managed Identity:  OK   │   │ SUCCESS: Permissions revoked  │
│                           │   │                               │
│ SUCCESS: Permission       │   │                               │
│ granted to both targets!  │   │                               │
└───────────────────────────┘   └───────────────────────────────┘
              │                               │
              └───────────────┬───────────────┘
                              v
                   ┌──────────────────┐
                   │ Loop back to     │
                   │ ACTION MENU      │
                   └────────┬─────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
            v                               v
     (Continue)                    (User selects Exit)
            │                               │
            │                               v
            │              ┌────────────────────────────────────┐
            │              │ COMPLETION                         │
            │              ├────────────────────────────────────┤
            │              │ Exiting...                         │
            │              └────────────────────────────────────┘
            │
            └─────> (back to SCAN PROMPT)
```

## 10. Implementation Details

### New .env Variable

```
CRAWLER_MANAGED_IDENTITY_OBJECT_ID=<the_managed_identity_client_id_to_access_sharepoint>
```

### Modified Validation Block

```powershell
# Required
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_CLIENT_ID)) { 
    throw "CRAWLER_CLIENT_ID is required in .env file" 
}

# Optional - Managed Identity Client ID
$hasManagedIdentity = -not [string]::IsNullOrWhiteSpace($config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID)

# Display configuration
Write-Host "Service Principal Client ID: $($config.CRAWLER_CLIENT_ID)" -ForegroundColor Cyan
if ($hasManagedIdentity) {
    Write-Host "Managed Identity Client ID: $($config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID)" -ForegroundColor Cyan
} else {
    Write-Host "Managed Identity Client ID: not configured" -ForegroundColor Gray
}
```

### New Functions Required

- `Get-TargetSelection` - Display target menu, return selection
- `Get-TargetsFromSelection` - Convert selection (1,2,3) to target array
- `Grant-SitePermissionToTargets` - Grant to multiple targets with per-target results
- `Revoke-SitePermissionFromTargets` - Revoke from multiple targets with per-target results
- `Get-MergedSitePermissions` - Scan both apps, merge results by URL

### Function Signatures

```powershell
function Get-TargetSelection {
    param(
        [Parameter(Mandatory=$true)] [bool]$HasBothTargets,
        [Parameter(Mandatory=$true)] [bool]$HasManagedIdentity,
        [string]$DefaultChoice = "1"
    )
    # Returns: "1", "2", or "3"
}

function Get-TargetsFromSelection {
    param(
        [Parameter(Mandatory=$true)] [string]$Selection,
        [Parameter(Mandatory=$true)] [bool]$HasManagedIdentity
    )
    # Returns: @("service_principal"), @("managed_identity"), or @("service_principal", "managed_identity")
}

function Grant-SitePermissionToTargets {
    param(
        [Parameter(Mandatory=$true)] [string]$SiteUrl,
        [Parameter(Mandatory=$true)] [string]$Role,
        [Parameter(Mandatory=$true)] [string[]]$Targets,
        [Parameter(Mandatory=$true)] [hashtable]$Config
    )
    # Returns: @{ "service_principal" = @{success=$true}; "managed_identity" = @{success=$false; error="..."} }
}

function Revoke-SitePermissionFromTargets {
    param(
        [Parameter(Mandatory=$true)] [string]$SiteUrl,
        [Parameter(Mandatory=$true)] [string[]]$Targets,
        [Parameter(Mandatory=$true)] [hashtable]$SitePermissionStatus,
        [Parameter(Mandatory=$true)] [hashtable]$Config
    )
    # Returns: @{ "service_principal" = @{success=$true}; "managed_identity" = @{success=$true} }
}

function Get-MergedSitePermissions {
    param(
        [Parameter(Mandatory=$true)] [string]$CertificateAppId,
        [string]$ManagedIdentityId,
        [Parameter(Mandatory=$true)] [string]$AdminUrl
    )
    # Returns: array of SitePermissionStatus objects
}
```

## 11. Document History

**[2026-03-15 19:23]**
- Changed: Menu Flow recreated with cleaner formatting (shorter SP/MI labels)
- Added: SCAN PROMPT step to Menu Flow diagram
- Added: Certificate details in DISCOVERY section

**[2026-03-15 19:20]**
- Changed: Target type `certificate` renamed to `service_principal` for consistency with ARCP-SP01
- Added: ARCS-FR-03 - Loop behavior and Quit option

**[2026-03-15 19:08]**
- Added: ARCS-FR-02 - Scan confirmation prompt (1=Scan, 2=Skip)

**[2026-03-15 18:38]**
- Changed: ARCS-FR-07 - Added explicit certificate path/name in access test logs

**[2026-03-15 18:37]**
- Added: ARCS-FR-08 - MI runtime detection via Azure IMDS
- Changed: ARCS-FR-07 - Dual-identity access testing (SP + MI when in Azure)

**[2026-03-15 18:20]**
- Changed: `CRAWLER_MANAGED_IDENTITY_CLIENT_ID` renamed to `CRAWLER_MANAGED_IDENTITY_OBJECT_ID` (accurate name)

**[2026-03-15 18:15]**
- Fixed: MI uses Object ID (Principal ID), not Client ID for PnP cmdlet [VERIFIED via Microsoft Q&A]

**[2026-03-15 18:11]**
- Fixed: MI acronym expanded on first use
- Fixed: Clarified behavior when selecting unavailable option

**[2026-03-15 18:05]**
- Initial specification created
- Menu flow with per-operation target selection
- Discovery shows side-by-side permission status
