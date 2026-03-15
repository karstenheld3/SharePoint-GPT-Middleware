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

### ArcConfiguration

Parameters needed for Arc onboarding.

**Key properties:**
- `SubscriptionId` - Target Azure subscription (GUID or name)
- `ResourceGroup` - Target resource group name
- `Location` - Azure region (e.g., westeurope)
- `ResourceName` - Optional custom name (defaults to hostname)
- `Tags` - Optional Azure tags

## 4. Functional Requirements

**AZARC-FR-01: Status Detection**
- Check if Azure Connected Machine agent is installed
- If installed, retrieve current connection status via `azcmagent show --json`
- Display status summary at script startup

**AZARC-FR-02: Main Menu**
- Show current status prominently
- Provide options based on current state:
  - Not installed: `1 - Install and Connect`
  - Installed but disconnected: `1 - Connect`, `2 - Uninstall Agent`
  - Connected: `1 - Disconnect`, `2 - Disconnect and Uninstall`
- Option `Q - Quit` always available
- No loop: script exits after each operation (single-action workflow)

**AZARC-FR-03: Install Agent**
- Download installer from `https://aka.ms/azcmagent-windows`
- Execute `install_windows_azcmagent.ps1`
- Verify installation by checking `azcmagent version`

**AZARC-FR-04: Connect to Azure**
- Prompt for subscription ID (required)
- Prompt for resource group name (required)
- Prompt for Azure region/location (required)
- Prompt for custom resource name (optional, defaults to hostname)
- Execute `azcmagent connect` with device code authentication
- Display device code URL and code for user to authenticate

**AZARC-FR-05: Disconnect from Azure**
- Execute `azcmagent disconnect` with device code authentication
- Confirm disconnection via `azcmagent show`

**AZARC-FR-06: Uninstall Agent**
- Prerequisite: Must be disconnected first (AZARC-FR-05)
- Uninstall via MSI: find product code in registry, run `msiexec /x {GUID} /qn`
- Verify uninstallation

**AZARC-FR-07: Error Handling**
- Display clear error messages for failures
- Suggest remediation steps where possible
- Exit gracefully on unrecoverable errors

**AZARC-FR-08: Admin Check**
- Verify script runs with administrator privileges
- Exit with message if not admin

## 5. Design Decisions

**AZARC-DD-01:** Use device code authentication instead of interactive browser. Rationale: Device code works when admin account differs from Azure account.

**AZARC-DD-02:** Menu-driven interactive flow. Rationale: Matches existing scripts in workspace, safer for destructive operations.

**AZARC-DD-03:** Download and run official Microsoft installer script. Rationale: Ensures compatibility, handles edge cases, maintained by Microsoft.

**AZARC-DD-04:** Require explicit disconnect before uninstall. Rationale: Prevents orphaned Azure resources and ensures clean state.

**AZARC-DD-05:** No service principal support. Rationale: Personal laptop scenario - don't want credential management complexity.

## 6. Implementation Guarantees

**AZARC-IG-01:** Script will not modify system if user quits at any prompt.

**AZARC-IG-02:** All operations display confirmation before execution.

**AZARC-IG-03:** Current status is always shown before any action prompt.

**AZARC-IG-04:** Agent uninstall only proceeds if disconnect confirmed successful.

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

### Install and Connect Flow

```
Script Start
├─> Check-AdminPrivilege
│   └─> If not admin: Exit with error
├─> Get-ArcStatus
│   └─> Display current status
├─> Show-Menu (status: NotInstalled)
│   └─> User selects "1 - Install and Connect"
├─> Install-ArcAgent
│   ├─> Download install_windows_azcmagent.ps1
│   ├─> Execute installer
│   └─> Verify: azcmagent version
├─> Prompt-ConnectionParameters
│   ├─> Read subscription ID
│   ├─> Read resource group
│   ├─> Read location
│   └─> Read resource name (optional)
├─> Connect-ToArc
│   ├─> Execute: azcmagent connect --use-device-code ...
│   ├─> Display device code URL and code
│   ├─> Wait for user to authenticate
│   └─> Verify connection: azcmagent show
└─> Display success + managed identity info
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

### Startup - Not Installed

```
================================================================================
  Azure Arc-Enabled Server Management
================================================================================

Current Status: NOT INSTALLED
  Azure Connected Machine agent is not installed on this computer.

--------------------------------------------------------------------------------
Options:
  1 - Install Agent and Connect to Azure
  Q - Quit

Select option:
```

### Startup - Disconnected (Agent Installed)

```
================================================================================
  Azure Arc-Enabled Server Management
================================================================================

Current Status: DISCONNECTED
  Agent Version: 1.48.02831.1732
  The agent is installed but not connected to Azure.

--------------------------------------------------------------------------------
Options:
  1 - Connect to Azure
  2 - Uninstall Agent
  Q - Quit

Select option:
```

### Startup - Connected

```
================================================================================
  Azure Arc-Enabled Server Management
================================================================================

Current Status: CONNECTED
  Resource Name:  YOURPC
  Resource Group: ArcServers-RG
  Subscription:   aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
  Location:       westeurope
  Agent Version:  1.48.02831.1732

Managed Identity Endpoint: http://localhost:40342/metadata/identity/oauth2/token

--------------------------------------------------------------------------------
Options:
  1 - Disconnect from Azure
  2 - Disconnect and Uninstall Agent
  Q - Quit

Select option:
```

### Connection Parameters Prompt

```
--------------------------------------------------------------------------------
  Connect to Azure Arc
--------------------------------------------------------------------------------

Enter Azure Subscription ID or Name: aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
Enter Resource Group Name: ArcServers-RG
Enter Azure Region (e.g., westeurope): westeurope
Enter Resource Name (press Enter for 'YOURPC'): 

Connecting with device code authentication...

To sign in, use a web browser to open the page https://microsoft.com/devicelogin
and enter the code ABC123XYZ to authenticate.

Waiting for authentication...
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

Are you sure you want to disconnect? (Y/N): Y

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

**[2026-03-15 19:25]**
- Changed: Doc ID from ARCS-SP01 to AZARC-SP01 (collision with Sites script)
- Added: Missing console output example for DISCONNECTED state
- Added: AZARC-FR-02 - Explicit no-loop behavior (single-action workflow)

**[2026-03-15 19:20]**
- Initial specification created
- Based on Azure Arc research in MGID-IN01
