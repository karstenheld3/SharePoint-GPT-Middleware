# IMPL: Add/Remove Computer as Arc-Enabled Server Script

**Doc ID**: AZARC-IP01
**Feature**: ARC_SERVER_MANAGEMENT
**Goal**: Implement PowerShell script to add or remove the local computer as an Azure Arc-enabled server
**Timeline**: Created 2026-03-15

**Target files**:
- `AddRemoveComputerAsArcEnabledServer.ps1` (NEW ~250 lines)

**Depends on:**
- `_SPEC_ADD_REMOVE_COMPUTER_AS_ARC_ENABLED_SERVER_SCRIPT.md [AZARC-SP01]` for requirements

## MUST-NOT-FORGET

- Requires Administrator privileges
- Disconnect BEFORE uninstall (order matters)
- Use `--use-device-code` for all azcmagent auth operations
- Single-action workflow (no loop)

## Table of Contents

1. [File Structure](#1-file-structure)
2. [Edge Cases](#2-edge-cases)
3. [Implementation Steps](#3-implementation-steps)
4. [Test Cases](#4-test-cases)
5. [Verification Checklist](#5-verification-checklist)
6. [Document History](#6-document-history)

## 1. File Structure

```
[WORKSPACE]/
└── AddRemoveComputerAsArcEnabledServer.ps1  # Main script (~250 lines) [NEW]
```

## 2. Edge Cases

- **AZARC-IP01-EC-01**: No internet connection -> Fail gracefully with network error message
- **AZARC-IP01-EC-02**: Not running as admin -> Exit with "Run as Administrator" message
- **AZARC-IP01-EC-03**: Agent download fails -> Show download URL for manual installation
- **AZARC-IP01-EC-04**: Device code auth timeout -> Show timeout message, suggest retry
- **AZARC-IP01-EC-05**: Invalid subscription/RG/location -> Show azcmagent error, don't crash
- **AZARC-IP01-EC-06**: Agent already connected -> Show status, offer disconnect options
- **AZARC-IP01-EC-07**: Uninstall without disconnect -> Block with error message

## 3. Implementation Steps

### AZARC-IP01-IS-01: Script Header and Admin Check

**Location**: `AddRemoveComputerAsArcEnabledServer.ps1` > top of file

**Action**: Add script header, admin privilege check

**Code**:
```powershell
# AddRemoveComputerAsArcEnabledServer.ps1
# Manages Azure Arc-enabled server connection for this computer

function Test-AdminPrivilege { ... }
# Check admin, exit if not elevated
```

### AZARC-IP01-IS-02: Status Detection Function

**Location**: `AddRemoveComputerAsArcEnabledServer.ps1` > after admin check

**Action**: Add Get-ArcStatus function

**Code**:
```powershell
function Get-ArcStatus {
    # Check if azcmagent.exe exists
    # If exists, run azcmagent show --json
    # Return hashtable with Status, ResourceName, ResourceGroup, etc.
}
```

### AZARC-IP01-IS-03: Display Functions

**Location**: `AddRemoveComputerAsArcEnabledServer.ps1` > after Get-ArcStatus

**Action**: Add Show-Header, Show-Status, Show-Menu functions

**Code**:
```powershell
function Show-Header { ... }     # Display banner
function Show-Status { ... }     # Display current connection status
function Show-Menu { ... }       # Display options based on status, return selection
```

### AZARC-IP01-IS-04: Agent Installation Function

**Location**: `AddRemoveComputerAsArcEnabledServer.ps1` > after display functions

**Action**: Add Install-ArcAgent function

**Code**:
```powershell
function Install-ArcAgent {
    # Download from https://aka.ms/azcmagent-windows
    # Execute installer
    # Verify with azcmagent version
}
```

### AZARC-IP01-IS-05: Connection Functions

**Location**: `AddRemoveComputerAsArcEnabledServer.ps1` > after install function

**Action**: Add Prompt-ConnectionParams, Connect-ToArc functions

**Code**:
```powershell
function Prompt-ConnectionParams { ... }  # Prompt for subscription, RG, location, name
function Connect-ToArc { ... }            # Execute azcmagent connect --use-device-code
```

### AZARC-IP01-IS-06: Disconnection Function

**Location**: `AddRemoveComputerAsArcEnabledServer.ps1` > after connection functions

**Action**: Add Disconnect-FromArc function with confirmation

**Code**:
```powershell
function Disconnect-FromArc {
    # Show warning about what will be deleted
    # Prompt Y/N confirmation
    # Execute azcmagent disconnect --use-device-code
    # Verify disconnection
}
```

### AZARC-IP01-IS-07: Uninstall Function

**Location**: `AddRemoveComputerAsArcEnabledServer.ps1` > after disconnect function

**Action**: Add Uninstall-ArcAgent function

**Code**:
```powershell
function Uninstall-ArcAgent {
    # Find product GUID in registry
    # Execute msiexec /x {GUID} /qn
    # Verify agent path no longer exists
}
```

### AZARC-IP01-IS-08: Main Script Logic

**Location**: `AddRemoveComputerAsArcEnabledServer.ps1` > bottom of file

**Action**: Add main execution flow

**Code**:
```powershell
# Main
Test-AdminPrivilege  # Exit if not admin
$status = Get-ArcStatus
Show-Header
Show-Status -Status $status
$choice = Show-Menu -Status $status
# Handle choice: Install+Connect, Connect, Disconnect, Uninstall, Quit
```

## 4. Test Cases

### Manual Testing (N/A for automated tests - requires Azure subscription)

- **AZARC-IP01-TC-01**: Run without admin -> Shows "Run as Administrator" message
- **AZARC-IP01-TC-02**: Run with no agent -> Shows NOT INSTALLED, offers Install option
- **AZARC-IP01-TC-03**: Install agent -> Downloads and installs successfully
- **AZARC-IP01-TC-04**: Connect to Azure -> Device code flow works, shows CONNECTED status
- **AZARC-IP01-TC-05**: Disconnect -> Removes Azure resource, shows DISCONNECTED status
- **AZARC-IP01-TC-06**: Uninstall -> Removes agent, shows NOT INSTALLED status

## 5. Verification Checklist

### Prerequisites
- [ ] **AZARC-IP01-VC-01**: AZARC-SP01 spec read and understood
- [ ] **AZARC-IP01-VC-02**: Azure subscription available for testing

### Implementation
- [ ] **AZARC-IP01-VC-03**: IS-01 Admin check implemented
- [ ] **AZARC-IP01-VC-04**: IS-02 Status detection implemented
- [ ] **AZARC-IP01-VC-05**: IS-03 Display functions implemented
- [ ] **AZARC-IP01-VC-06**: IS-04 Agent installation implemented
- [ ] **AZARC-IP01-VC-07**: IS-05 Connection functions implemented
- [ ] **AZARC-IP01-VC-08**: IS-06 Disconnection implemented
- [ ] **AZARC-IP01-VC-09**: IS-07 Uninstall implemented
- [ ] **AZARC-IP01-VC-10**: IS-08 Main logic implemented

### Validation
- [ ] **AZARC-IP01-VC-11**: Script runs without syntax errors
- [ ] **AZARC-IP01-VC-12**: Admin check works correctly
- [ ] **AZARC-IP01-VC-13**: Status detection works for all states
- [ ] **AZARC-IP01-VC-14**: Menu displays correct options per state

## 6. Implementation Findings

### 6.1 Azure CLI Token Cache Corruption

**Error:**
```
Decryption failed: [WinError -2146893813] Key not valid for use in specified state.
App developer may consider this guidance: https://github.com/AzureAD/microsoft-authentication-extensions-for-python/wiki/PersistenceDecryptionError
```

**Root cause:** MSAL token cache files become corrupted on Windows.

**Solution:** Delete cache files before `az login`:
```powershell
$azureDir = Join-Path $env:USERPROFILE ".azure"
$cacheFiles = @("msal_token_cache.bin", "msal_token_cache.json", "accessTokens.json", "service_principal_entries.json")
foreach ($file in $cacheFiles) {
    $path = Join-Path $azureDir $file
    if (Test-Path $path) { Remove-Item $path -Force }
}
```

### 6.2 connectedmachine Extension Permission Issues

**Error:** When running `az connectedmachine show` or `az connectedmachine update`:
```
ERROR: [WinError 5] Access is denied: 'C:\Users\User\.azure\cliextensions\connectedmachine\connectedmachine-1.0.0.dist-info'
```

**Root cause:** Extension installed as admin has wrong permissions for regular user.

**Solution:** Use `az rest` with direct REST API calls instead:
```powershell
# GET machine details
az rest --method GET --url "https://management.azure.com/subscriptions/.../providers/Microsoft.HybridCompute/machines/YOURPC?api-version=2024-07-10"
```

### 6.3 Subscription Selection After Login

**Problem:** After `az login`, wrong subscription selected by default when user has multiple subscriptions.

**Solution:** Always run `az account set` after login:
```powershell
az account set --subscription "your-subscription-id"
```

### 6.4 REST API Content-Type Header

**Error:**
```
ERROR: Unsupported Media Type({"error":{"code":"UnsupportedMediaType","message":"The content media type '<null>' is not supported. Only 'application/json' is supported."}})
```

**Solution:** Add Content-Type header to PATCH requests:
```powershell
az rest --method PATCH --url $apiUrl --headers "Content-Type=application/json" --body "@$tempFile"
```

### 6.5 JSON Body Escaping Issues

**Error:**
```
ERROR: Bad Request({"error":{"code":"InvalidRequestContent","message":"The request content was invalid and could not be deserialized: 'Unexpected character encountered while parsing value: S. Path 'identity.type', line 1, position 16.'"}})
```

**Root cause:** PowerShell command-line escaping corrupts JSON when passed to `az rest --body`.

**Solution:** Write JSON to temp file and use `@filename` syntax:
```powershell
$bodyJson | Out-File -FilePath $tempFile -Encoding utf8 -NoNewline
az rest --method PATCH --url $apiUrl --body "@$tempFile"
Remove-Item $tempFile -Force
```

### 6.6 User-Assigned MI Preview Limitation

**Error:**
```
ERROR: Bad Request({"error":{"code":"HCRP400","message":"User assigned identity is currently in preview and not allowed for this subscription."}})
```

**Status:** BLOCKED - Feature in preview, not available for all subscriptions.

**Workaround:** Use only system-assigned managed identity (automatically created on Arc connect).

**Impact:** Cannot share a single MI across multiple Arc machines. Each gets its own system-assigned MI.

### 6.7 Working Flow

What works today:
1. Install Azure Connected Machine agent
2. Connect to Azure Arc (`azcmagent connect --use-device-code`)
3. System-assigned MI is created automatically
4. Query MI details via `az rest` API (principal_id = object_id)
5. Assign RBAC roles to the system-assigned MI's principal_id
6. Application uses `http://localhost:40342/metadata/identity/oauth2/token` endpoint

## 7. Document History

**[2026-03-15 21:59]**
- Added: Section 6 - Implementation Findings with all error messages and solutions
- Added: 6.1 Token cache corruption fix
- Added: 6.2 connectedmachine extension workaround
- Added: 6.3 Subscription selection fix
- Added: 6.4 Content-Type header fix
- Added: 6.5 JSON body escaping fix
- Added: 6.6 User-assigned MI preview limitation (HCRP400)
- Added: 6.7 Working flow summary

**[2026-03-15 19:26]**
- Initial implementation plan created
