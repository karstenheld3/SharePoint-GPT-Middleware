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

## 6. Document History

**[2026-03-15 19:26]**
- Initial implementation plan created
