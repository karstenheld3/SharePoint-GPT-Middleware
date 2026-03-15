# SPEC: Add/Remove Computer as Arc-Enabled Server Script

**Doc ID**: AZARC-SP01
**Feature**: ARC_SERVER_MANAGEMENT
**Goal**: PowerShell script to add or remove the local computer as an Azure Arc-enabled server with managed identity
**Timeline**: Created 2026-03-15
**Target file**: `AddRemoveComputerAsArcEnabledServer.ps1`

**Depends on:**
- `_INFO_MANAGED_IDENTITY_PRIVATE_LAPTOP.md [MGID-IN01]` for Azure Arc research findings

## MUST-NOT-FORGET

- Agent installation requires admin privileges
- Disconnect BEFORE uninstall (cleanup order matters)
- Use device code login for interactive auth (works across accounts)
- Check existing connection status before any operation
- Windows client OS (10/11) supported only for "server-like" scenarios
- Portal Identity blade NOT available for Arc servers - use CLI/PowerShell only
- Script must be idempotent - safe to run multiple times
- Only consecutive numbers in menus starting with 1

## Table of Contents

1. [Scenario](#1-scenario)
2. [Context](#2-context)
3. [Domain Objects](#3-domain-objects)
4. [Functional Requirements](#4-functional-requirements)
5. [Design Decisions](#5-design-decisions)
6. [Implementation Guarantees](#6-implementation-guarantees)
7. [Key Mechanisms](#7-key-mechanisms)
8. [Action Flow](#8-action-flow)
9. [Console Output Examples](#9-console-output-examples)
10. [Implementation Details](#10-implementation-details)
11. [Document History](#11-document-history)

## 1. Scenario

**Problem:** Developer needs managed identity on private laptop for local development against Azure resources. Managed identities cannot be assigned to physical devices directly - they require Azure Arc onboarding.

**Solution:**
- Single PowerShell script to add OR remove Arc connection
- Interactive menu-driven approach (similar to AddRemoveCrawlerSharePointSites.ps1)
- Support both installation and cleanup workflows
- Show current status before prompting for action

**What we don't want:**
- Automated/unattended installation (too risky for personal device)
- Service principal authentication (requires secret management)
- Partial cleanup (agent installed but not connected, or connected but not disconnected)
- User must enter letters when navigating menu. Only numbers starting with 1.

## 2. Context

Azure Arc extends Azure management to machines outside Azure. When a computer is onboarded as an Arc-enabled server:
- Azure creates a system-assigned managed identity
- Applications can request tokens via local IMDS endpoint (`http://localhost:40342`)
- Computer appears as a resource in Azure Portal under Azure Arc > Machines

The Azure Connected Machine agent (`azcmagent`) handles:
- Registration with Azure (`azcmagent connect`)
- Disconnection (`azcmagent disconnect`)
- Status checking (`azcmagent show`)

## 3. Domain Objects

### ArcConnectionStatus

Represents the current state of Azure Arc connection on this computer.

**Key properties:**
- `AgentInstalled` - Whether azcmagent.exe exists
- `AgentVersion` - Version string if installed
- `ConnectionStatus` - Connected, Disconnected, or NotInstalled
- `ResourceName` - Name in Azure (usually hostname)
- `ResourceGroup` - Azure resource group
- `SubscriptionId` - Azure subscription
- `TenantId` - Entra ID tenant
- `Location` - Azure region
- `UserAssignedMIAttached` - Whether configured user-assigned MI is attached

### ArcConfiguration

Parameters needed for Arc onboarding.

**Key properties:**
- `SubscriptionId` - Target Azure subscription (GUID or name)
- `ResourceGroup` - Target resource group name
- `Location` - Azure region (e.g., westeurope)
- `ResourceName` - Optional custom name (defaults to hostname)
- `Tags` - Optional Azure tags

## 4. Functional Requirements

**AZARC-FR-01: Idempotent Execution (Run Multiple Times)**
- Script checks ALL preconditions at startup
- Only applies steps that are not yet complete
- Safe to run multiple times - skips already-completed steps
- Precondition checks:
  1. Agent installed? → if no, install
  2. Connected to Arc? → if no, connect
  3. User-assigned MI attached? → if no and configured, attach
- Each check displays current state before action

**AZARC-FR-02: Status Detection**
- Check if Azure Connected Machine agent is installed
- If installed, retrieve current connection status via `azcmagent show --json`
- If connected, check if user-assigned MI is already attached
- Display comprehensive status summary at startup

**AZARC-FR-03: Main Menu**
- Show current status prominently with checklist format:
  ```
  Status:
    [x] Agent installed (v1.61)
    [x] Connected to Azure Arc (DESKTOP-7QNJLDI)
    [ ] User-assigned MI attached
  ```
- Provide options based on current state:
  - All complete: `1 - Disconnect`, `2 - Disconnect and Uninstall`, `3 - Quit`
  - Missing steps: `1 - Complete Setup`, `2 - Quit`
  - Partial (agent only): `1 - Complete Setup`, `2 - Uninstall Agent`, `3 - Quit`
- Quit is always the last numbered option

**AZARC-FR-04: Install Agent**
- Skip if already installed (show "Agent already installed")
- Download installer from `https://aka.ms/azcmagent-windows`
- Execute `install_windows_azcmagent.ps1`
- Verify installation by checking `azcmagent version`

**AZARC-FR-05: Configuration Loading**
- Load defaults from `.env` file in workspace root (via `$workspaceRoot`)
- If `.env` file does not exist, continue without defaults (no error)
- Supported config keys:
  - `AZURE_SUBSCRIPTION_ID` - Azure subscription
  - `AZURE_RESOURCE_GROUP` - Resource group for Arc machine
  - `AZURE_LOCATION` - Azure region
  - `AZURE_TENANT_ID` - Entra ID tenant
  - `CRAWLER_MANAGED_IDENTITY_OBJECT_ID` - User-assigned MI to attach after connect
  - `CRAWLER_MANAGED_IDENTITY_NAME` - Display name for the MI

**AZARC-FR-06: Connect to Azure**
- Skip if already connected (show "Already connected to Azure Arc")
- Display current values (from .env or empty) in numbered menu
- User can select which parameter to change, or confirm all
- Menu format (consistent with other scripts):
  ```
  Current configuration:
    1 - Subscription:   [value or (not set)]
    2 - Resource Group: [value or (not set)]
    3 - Location:       [value or (not set)]
    4 - Tenant:         [value or (not set)]
    5 - Resource Name:  [hostname]
    6 - Confirm and Connect
    7 - Cancel
  ```
- Selecting a number allows overwriting that specific value
- All values except Resource Name are required before confirm
- Execute `azcmagent connect` with device code authentication
- Pass `--tenant-id` if tenant is configured

**AZARC-FR-07: Assign User-Assigned Managed Identity**
- Skip if MI already attached (show "Managed identity already attached")
- Skip if `CRAWLER_MANAGED_IDENTITY_OBJECT_ID` not configured
- Check current identity assignments via Az.ConnectedMachine
- If not attached, prompt user with numbered menu: `1 - Yes, attach MI` / `2 - No, skip`
- Use Az.ConnectedMachine PowerShell module to assign:
  ```powershell
  Update-AzConnectedMachine -Name $resourceName -ResourceGroupName $resourceGroup `
    -IdentityType "SystemAssigned,UserAssigned" `
    -IdentityUserAssignedIdentity @{$miResourceId = @{}}
  ```
- Requires: Az.ConnectedMachine module, Azure authentication
- Display success/failure status

**AZARC-FR-08: Disconnect from Azure**
- Execute `azcmagent disconnect` with device code authentication
- Confirm disconnection via `azcmagent show`

**AZARC-FR-09: Uninstall Agent**
- Prerequisite: Must be disconnected first (AZARC-FR-08)
- Uninstall via MSI: find product code in registry, run `msiexec /x {GUID} /qn`
- Verify uninstallation

**AZARC-FR-10: Error Handling**
- Display clear error messages for failures
- Suggest remediation steps where possible
- Exit gracefully on unrecoverable errors

**AZARC-FR-11: Admin Check**
- Verify script runs with administrator privileges
- Exit with message if not admin

## 5. Design Decisions

**AZARC-DD-01:** Use device code authentication instead of interactive browser. Rationale: Device code works when admin account differs from Azure account.

**AZARC-DD-02:** Menu-driven interactive flow. Rationale: Matches existing scripts in workspace, safer for destructive operations.

**AZARC-DD-03:** Download and run official Microsoft installer script. Rationale: Ensures compatibility, handles edge cases, maintained by Microsoft.

**AZARC-DD-04:** Require explicit disconnect before uninstall. Rationale: Prevents orphaned Azure resources and ensures clean state.

**AZARC-DD-05:** No service principal support. Rationale: Personal laptop scenario - don't want credential management complexity.

**AZARC-DD-06:** Idempotent execution. Rationale: Script can be run multiple times safely - checks state before each action, skips completed steps.

**AZARC-DD-07:** Portal not used for MI assignment. Rationale: Arc servers don't have Identity blade in Portal UI - must use Az.ConnectedMachine PowerShell module.

## 6. Implementation Guarantees

**AZARC-IG-01:** Script will not modify system if user quits at any prompt.

**AZARC-IG-02:** All operations display confirmation before execution.

**AZARC-IG-03:** Current status is always shown before any action prompt.

**AZARC-IG-04:** Agent uninstall only proceeds if disconnect confirmed successful.

**AZARC-IG-05:** Running script multiple times is safe - completed steps are skipped with status message.

## 7. Key Mechanisms

### Status Detection

```powershell
function Get-ArcStatus {
    $agentPath = "$env:ProgramFiles\AzureConnectedMachineAgent\azcmagent.exe"
    if (-not (Test-Path $agentPath)) {
        return @{ Status = "NotInstalled" }
    }
    $json = & $agentPath show --json 2>$null | ConvertFrom-Json
    return @{
        Status = $json.status  # "Connected" or "Disconnected"
        ResourceName = $json.resourceName
        ResourceGroup = $json.resourceGroup
        SubscriptionId = $json.subscriptionId
        TenantId = $json.tenantId
        Location = $json.location
        AgentVersion = $json.agentVersion
    }
}
```

### Device Code Authentication

The `--use-device-code` flag triggers device code flow:
1. Agent prints URL and code
2. User opens URL in any browser
3. User enters code and authenticates
4. Agent completes operation after authentication

### IMDS Endpoint (Post-Connection)

After successful connection, managed identity tokens available via:
- Endpoint: `http://localhost:40342/metadata/identity/oauth2/token`
- Environment variable: `$env:IDENTITY_ENDPOINT`

## 8. Action Flow

### Idempotent Setup Flow (Complete Setup)

```
Script Start
├─> Check-AdminPrivilege
│   └─> If not admin: Exit with error
├─> Load-Configuration (.env file, optional)
├─> Get-FullStatus
│   ├─> Check agent installed?
│   ├─> Check connected to Arc?
│   └─> Check user-assigned MI attached?
├─> Display-Checklist (shows [x] / [ ] for each step)
├─> Show-Menu
│   └─> User selects "1 - Complete Setup"
├─> For each incomplete step:
│   ├─> Step 1: Install Agent (if not installed)
│   │   ├─> Download install_windows_azcmagent.ps1
│   │   ├─> Execute installer
│   │   └─> Verify: azcmagent version
│   ├─> Step 2: Connect to Arc (if not connected)
│   │   ├─> Show parameter menu (numbered, editable)
│   │   ├─> Execute: azcmagent connect --use-device-code
│   │   └─> Verify connection: azcmagent show
│   └─> Step 3: Attach MI (if configured and not attached)
│       ├─> Authenticate to Azure (Connect-AzAccount)
│       ├─> Update-AzConnectedMachine with user-assigned MI
│       └─> Verify: MI appears in identity list
└─> Display final status (all [x] checked)
```

### Disconnect and Uninstall Flow

```
Script Start
├─> Check-AdminPrivilege
├─> Get-ArcStatus
│   └─> Display: Connected to [ResourceName]
├─> Show-Menu (status: Connected)
│   └─> User selects "2 - Disconnect and Uninstall"
├─> Disconnect-FromArc
│   ├─> Execute: azcmagent disconnect --use-device-code
│   ├─> Wait for user to authenticate
│   └─> Verify: azcmagent show (status: Disconnected)
├─> Uninstall-ArcAgent
│   ├─> Find product GUID in registry
│   ├─> Execute: msiexec /x {GUID} /qn
│   └─> Verify: agent path no longer exists
└─> Display success
```

## 9. Console Output Examples

### Startup - Setup Incomplete (Checklist Format)

```
================================================================================
  Azure Arc-Enabled Server Management
================================================================================

Status:
  [ ] Agent installed
  [ ] Connected to Azure Arc
  [ ] User-assigned MI attached (your-managed-identity-id)

--------------------------------------------------------------------------------
Options:
  1 - Complete Setup (install, connect, attach MI)
  2 - Quit

Select option:
```

### Startup - Partial Setup (Agent Installed, Not Connected)

```
================================================================================
  Azure Arc-Enabled Server Management
================================================================================

Status:
  [x] Agent installed (v1.61.03319.2737)
  [ ] Connected to Azure Arc
  [ ] User-assigned MI attached

--------------------------------------------------------------------------------
Options:
  1 - Complete Setup (connect, attach MI)
  2 - Uninstall Agent
  3 - Quit

Select option:
```

### Startup - All Complete

```
================================================================================
  Azure Arc-Enabled Server Management
================================================================================

Status:
  [x] Agent installed (v1.61.03319.2737)
  [x] Connected to Azure Arc (DESKTOP-7QNJLDI)
  [x] User-assigned MI attached (your-managed-identity-id)

Connection Details:
  Resource Group: your-resource-group
  Subscription:   aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
  Location:       westeurope

Token Endpoint: http://localhost:40342/metadata/identity/oauth2/token

--------------------------------------------------------------------------------
Options:
  1 - Disconnect from Azure
  2 - Disconnect and Uninstall Agent
  3 - Quit

Select option:
```

### Connection Parameters Menu

```
--------------------------------------------------------------------------------
  Connect to Azure Arc
--------------------------------------------------------------------------------

Configuration (from .env):
  1 - Subscription:   aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
  2 - Resource Group: your-resource-group
  3 - Location:       westeurope
  4 - Tenant:         xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  5 - Resource Name:  YOURPC

  6 - Confirm and Connect
  7 - Cancel

Select option: 6

Connecting with device code authentication...

To sign in, use a web browser to open the page https://microsoft.com/devicelogin
and enter the code ABC123XYZ to authenticate.

Waiting for authentication...
```

### Connection Parameters Menu (No .env)

```
--------------------------------------------------------------------------------
  Connect to Azure Arc
--------------------------------------------------------------------------------

Configuration:
  1 - Subscription:   (not set)
  2 - Resource Group: (not set)
  3 - Location:       (not set)
  4 - Tenant:         (not set)
  5 - Resource Name:  YOURPC

  6 - Confirm and Connect
  7 - Cancel

Select option: 1
Enter Subscription ID: aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee

Configuration:
  1 - Subscription:   aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
  2 - Resource Group: (not set)
  ...
```

### Disconnect Confirmation

```
--------------------------------------------------------------------------------
  Disconnect from Azure Arc
--------------------------------------------------------------------------------

WARNING: This will:
  - Delete the Azure resource for this computer
  - Remove the managed identity
  - Keep the agent installed (can reconnect later)

1 - Yes, disconnect
2 - No, cancel

Select option: 1

Disconnecting with device code authentication...

To sign in, use a web browser to open the page https://microsoft.com/devicelogin
and enter the code DEF456UVW to authenticate.

Waiting for authentication...
Disconnected successfully.
```

## 10. Implementation Details

### File Structure

Single script file: `AddRemoveComputerAsArcEnabledServer.ps1`

### Function Signatures

```powershell
function Test-AdminPrivilege { }                    # Returns $true if admin
function Get-ArcStatus { }                          # Returns status hashtable
function Show-Status { param($Status) }             # Displays formatted status
function Show-Menu { param($Status) }               # Returns user selection
function Install-ArcAgent { }                       # Downloads and installs agent
function Prompt-ConnectionParams { }                # Returns params hashtable
function Connect-ToArc { param($Params) }           # Connects with device code
function Disconnect-FromArc { }                     # Disconnects with device code
function Uninstall-ArcAgent { }                     # Removes agent via MSI
```

### External Dependencies

- PowerShell 5.1+ (Windows built-in)
- Internet access to `https://aka.ms/azcmagent-windows`
- Internet access to Azure endpoints for authentication
- Administrator privileges

### Registry Path for Uninstall

```
HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*
DisplayName = "Azure Connected Machine Agent"
```

### azcmagent Commands Used

- `azcmagent version` - Verify installation
- `azcmagent show --json` - Get connection status
- `azcmagent connect --subscription-id X --resource-group Y --location Z --use-device-code` - Connect
- `azcmagent disconnect --use-device-code` - Disconnect

## 11. Document History

**[2026-03-15 21:00]**
- Fixed: FR-03 menu options now consecutive (1,2 or 1,2,3 based on state)
- Fixed: FR-06 Cancel option 7 (was duplicate 3 conflicting with Location)
- Fixed: FR-07 Y/n prompt changed to numbered menu (1-Yes, 2-No)
- Fixed: Console example "Setup Incomplete" uses 1,2 not 1,3

**[2026-03-15 20:55]**
- Added: MUST-NOT-FORGET items (Portal limitation, idempotent requirement)
- Added: UserAssignedMIAttached to ArcConnectionStatus domain object
- Added: AZARC-DD-06 (Idempotent execution), AZARC-DD-07 (Portal not used for MI)
- Added: AZARC-IG-05 (Multiple runs safe)
- Changed: Console output examples to checklist format matching FR-03
- Changed: Action Flow to "Idempotent Setup Flow" with step-by-step checks

**[2026-03-15 20:50]**
- Added: AZARC-FR-01 - Idempotent execution (run multiple times, only apply missing steps)
- Changed: FR-02 Status Detection - check if MI already attached
- Changed: FR-03 Main Menu - checklist format showing completion status
- Changed: FR-04 Install Agent - skip if already installed
- Changed: FR-06 Connect - skip if already connected
- Changed: FR-07 Assign MI - skip if already attached
- Changed: Renumbered all FRs (FR-01 to FR-11)

**[2026-03-15 20:49]**
- Added: AZARC-FR-06 - Assign user-assigned managed identity after connect
- Added: CRAWLER_MANAGED_IDENTITY_OBJECT_ID and CRAWLER_MANAGED_IDENTITY_NAME to FR-04 config keys
- Changed: Renumbered FR-06 to FR-07, FR-07 to FR-08, FR-08 to FR-09, FR-09 to FR-10

**[2026-03-15 20:46]**
- Added: AZARC-FR-04 - Configuration loading from .env (optional, no failure if missing)
- Added: AZARC-FR-05 - Numbered menu for parameter selection with override capability
- Changed: Renumbered FR-05 to FR-06, FR-06 to FR-07, FR-07 to FR-08, FR-08 to FR-09
- Added: Console output examples for numbered parameter menu (with and without .env)

**[2026-03-15 19:25]**
- Changed: Doc ID from ARCS-SP01 to AZARC-SP01 (collision with Sites script)
- Added: Missing console output example for DISCONNECTED state
- Added: AZARC-FR-02 - Explicit no-loop behavior (single-action workflow)

**[2026-03-15 19:20]**
- Initial specification created
- Based on Azure Arc research in MGID-IN01
