#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Manages Azure Arc-enabled server connection for this computer.

.DESCRIPTION
    This script allows you to:
    - Install the Azure Connected Machine agent
    - Connect this computer to Azure Arc (gets system-assigned managed identity)
    - Disconnect from Azure Arc
    - Uninstall the Azure Connected Machine agent

.NOTES
    Requires: Administrator privileges
    Author: SharePoint-GPT-Middleware
    Version: 1.0.0
#>

$ErrorActionPreference = "Stop"

# =============================================================================
# Configuration
# =============================================================================

$script:AgentPath = "$env:ProgramFiles\AzureConnectedMachineAgent\azcmagent.exe"
$script:DownloadUrl = "https://aka.ms/azcmagent-windows"
$script:InstallerPath = "$env:TEMP\install_windows_azcmagent.ps1"

# Workspace root is parent of scripts/ folder
$script:WorkspaceRoot = Split-Path $PSScriptRoot -Parent

# Configuration loaded from .env (populated in main)
$script:Config = @{}

# =============================================================================
# Helper Functions
# =============================================================================

# Reads an .env file and returns a hashtable of key-value pairs
function Read-EnvFile {
  param([Parameter(Mandatory=$true)] [string]$Path)
  $envVars = @{}
  if (!(Test-Path $Path)) { return $envVars }
  Get-Content $Path | ForEach-Object {
    if ($_ -match '^(?!#)([^=]+)=([^#]*)(?:#.*)?$') {
      $key = $matches[1].Trim(); $value = $matches[2].Trim()
      $envVars[$key] = $value
    }
  }
  return $envVars
}

function Test-AdminPrivilege {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-ArcStatus {
    $result = @{
        AgentInstalled = $false
        Connected = $false
        UserAssignedMIAttached = $false
        AgentVersion = $null
        ResourceName = $null
        ResourceGroup = $null
        SubscriptionId = $null
        TenantId = $null
        Location = $null
        # System-assigned managed identity info
        SystemMIName = $null
        SystemMIClientId = $null
        SystemMIPrincipalId = $null
    }
    
    # Check agent installed
    if (-not (Test-Path $script:AgentPath)) {
        return $result
    }
    $result.AgentInstalled = $true
    
    # Check connection status
    try {
        $jsonOutput = & $script:AgentPath show --json 2>$null
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($jsonOutput)) {
            $result.AgentVersion = (& $script:AgentPath version 2>$null)
            return $result
        }
        
        $info = $jsonOutput | ConvertFrom-Json
        $result.Connected = ($info.status -eq "Connected")
        $result.AgentVersion = $info.agentVersion
        $result.ResourceName = $info.resourceName
        $result.ResourceGroup = $info.resourceGroup
        $result.SubscriptionId = $info.subscriptionId
        $result.TenantId = $info.tenantId
        $result.Location = $info.location
    }
    catch {
        $result.AgentVersion = "Unknown"
        return $result
    }
    
    # NOTE: MI info retrieval moved to separate function called after menu display
    # to avoid blocking the UI. See Get-ExtendedMIInfo
    
    # User-assigned MI check also deferred to avoid blocking
    
    return $result
}

function Get-SystemAssignedMIInfo {
    param([hashtable]$Status)
    
    try {
        $azCmd = Get-Command az -ErrorAction SilentlyContinue
        if (-not $azCmd) { return $null }
        
        $machineJson = az connectedmachine show `
            --name $Status.ResourceName `
            --resource-group $Status.ResourceGroup `
            --output json `
            2>$null
        
        if ($LASTEXITCODE -ne 0 -or -not $machineJson) { return $null }
        
        $machine = $machineJson | ConvertFrom-Json
        
        return @{
            Name = $Status.ResourceName
            ClientId = $machine.identity.principalId  # Note: For Arc, principalId is the client ID
            PrincipalId = $machine.identity.principalId
        }
    }
    catch {
        return $null
    }
}

function Test-UserAssignedMIAttached {
    param([hashtable]$Status)
    
    $miObjectId = $script:Config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID
    if (-not $miObjectId) { return $false }
    if (-not $Status.Connected) { return $false }
    
    try {
        # Use Azure CLI to check machine identity
        $azCmd = Get-Command az -ErrorAction SilentlyContinue
        if (-not $azCmd) { return $false }
        
        $machineJson = az connectedmachine show `
            --name $Status.ResourceName `
            --resource-group $Status.ResourceGroup `
            --query "identity" `
            2>$null
        
        if ($LASTEXITCODE -ne 0 -or -not $machineJson) { return $false }
        
        # Check if user-assigned MI is in the identity
        return $machineJson -match $miObjectId
    }
    catch {
        return $false
    }
}

# =============================================================================
# Display Functions
# =============================================================================

function Show-Header {
    Clear-Host
    Write-Host "==================================== START: AZURE ARC SERVER MANAGEMENT ====================================" -ForegroundColor Cyan
    Write-Host ""
}

function Show-Footer {
    param([string]$Duration = $null)
    Write-Host ""
    if ($Duration) {
        Write-Host "===================================== END: AZURE ARC SERVER MANAGEMENT =====================================" -ForegroundColor Cyan
        Write-Host "Duration: $Duration"
    } else {
        Write-Host "===================================== END: AZURE ARC SERVER MANAGEMENT =====================================" -ForegroundColor Cyan
    }
}

function Show-Checklist {
    param([hashtable]$Status)
    
    Write-Host "Status:"
    
    # Agent installed (LOG-GN-02: quote version)
    if ($Status.AgentInstalled) {
        Write-Host "  [" -NoNewline
        Write-Host "x" -ForegroundColor Green -NoNewline
        Write-Host "] Agent installed (version='$($Status.AgentVersion)')"
    } else {
        Write-Host "  [ ] Agent installed"
    }
    
    # Connected to Arc (LOG-GN-02: quote resource name)
    if ($Status.Connected) {
        Write-Host "  [" -NoNewline
        Write-Host "x" -ForegroundColor Green -NoNewline
        Write-Host "] Connected to Azure Arc (name='$($Status.ResourceName)')"
    } else {
        Write-Host "  [ ] Connected to Azure Arc"
    }
    
    # User-assigned MI configured (status checked on-demand via Azure CLI)
    $miId = $script:Config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID
    $miName = $script:Config.CRAWLER_MANAGED_IDENTITY_NAME
    if ($miId) {
        $miDisplay = if ($miName) { "name='$miName'" } else { "id='$miId'" }
        Write-Host "  [?] User-assigned MI configured ($miDisplay)" -ForegroundColor Gray
    }
    
    Write-Host ""
    
    # Show connection details if connected (LOG-GN-06: property format)
    if ($Status.Connected) {
        Write-Host "Connection Details:"
        Write-Host "  resource_group='$($Status.ResourceGroup)'"
        Write-Host "  subscription='$($Status.SubscriptionId)'"
        Write-Host "  location='$($Status.Location)'"
        Write-Host ""
        Write-Host "Token Endpoint: " -NoNewline
        Write-Host "http://localhost:40342/metadata/identity/oauth2/token" -ForegroundColor Cyan
        Write-Host ""
    }
}

function Show-Menu {
    param([hashtable]$Status)
    
    Write-Host "--------------------------------------------------------------------------------"
    Write-Host "Options:"
    
    # Determine state - don't check user-assigned MI here (requires Azure CLI)
    $miConfigured = [bool]$script:Config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID
    $allComplete = $Status.AgentInstalled -and $Status.Connected
    
    if ($allComplete) {
        # Connected - show MI info, offer attachment or disconnect
        Write-Host "  1 - Show System-Assigned MI Details"
        if ($miConfigured) {
            Write-Host "  2 - Attach User-Assigned MI"
            Write-Host "  3 - Disconnect from Azure"
            Write-Host "  4 - Disconnect and Uninstall Agent"
            Write-Host "  5 - Quit"
        } else {
            Write-Host "  2 - Disconnect from Azure"
            Write-Host "  3 - Disconnect and Uninstall Agent"
            Write-Host "  4 - Quit"
        }
    }
    elseif ($Status.AgentInstalled -and -not $Status.Connected) {
        # Agent installed but not connected
        Write-Host "  1 - Complete Setup (connect, attach MI)"
        Write-Host "  2 - Uninstall Agent"
        Write-Host "  3 - Quit"
    }
    else {
        # Nothing installed - full setup needed
        Write-Host "  1 - Complete Setup (install, connect, attach MI)"
        Write-Host "  2 - Quit"
    }
    
    Write-Host ""
    $choice = Read-Host "Select option"
    return $choice
}

# =============================================================================
# Agent Installation
# =============================================================================

function Install-ArcAgent {
    # LOG-GN-09: Announce before execution
    Write-Host ""
    Write-Host "Installing Azure Connected Machine Agent..."
    
    try {
        # Track: Download
        Write-Host "  Downloading from '$script:DownloadUrl'..."
        Invoke-WebRequest -Uri $script:DownloadUrl -OutFile $script:InstallerPath -UseBasicParsing
        Write-Host "  Running installer..."
        & $script:InstallerPath
        
        # Report: Success or failure
        if (Test-Path $script:AgentPath) {
            $version = & $script:AgentPath version 2>$null
            Write-Host "  OK. Agent installed (version='$version')." -ForegroundColor Green
            return $true
        }
        else {
            # LOG-GN-08: Error format
            Write-Host "  FAIL: Agent not found at expected path -> Installation may have failed." -ForegroundColor Red
            return $false
        }
    }
    catch {
        # LOG-GN-08: Error chain format
        Write-Host "  FAIL: Could not install agent -> $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        Write-Host "HINT: Try manual installation:"
        Write-Host "  1. Download from '$script:DownloadUrl'"
        Write-Host "  2. Run the downloaded script as Administrator"
        return $false
    }
    finally {
        if (Test-Path $script:InstallerPath) {
            Remove-Item $script:InstallerPath -Force -ErrorAction SilentlyContinue
        }
    }
}

# =============================================================================
# Connection Functions
# =============================================================================

function Read-ConnectionParams {
    # Initialize with defaults from config
    $params = @{
        SubscriptionId = $script:Config.AZURE_SUBSCRIPTION_ID
        ResourceGroup = $script:Config.AZURE_RESOURCE_GROUP
        Location = $script:Config.AZURE_LOCATION
        TenantId = $script:Config.AZURE_TENANT_ID
        ResourceName = $env:COMPUTERNAME
    }
    
    while ($true) {
        Write-Host ""
        Write-Host "--------------------------------------------------------------------------------"
        Write-Host "  Connect to Azure Arc"
        Write-Host "--------------------------------------------------------------------------------"
        Write-Host ""
        
        $hasEnv = [bool]$script:Config.AZURE_SUBSCRIPTION_ID
        if ($hasEnv) {
            Write-Host "Configuration (from .env):"
        } else {
            Write-Host "Configuration:"
        }
        
        $subDisplay = if ($params.SubscriptionId) { $params.SubscriptionId } else { "(not set)" }
        $rgDisplay = if ($params.ResourceGroup) { $params.ResourceGroup } else { "(not set)" }
        $locDisplay = if ($params.Location) { $params.Location } else { "(not set)" }
        $tenDisplay = if ($params.TenantId) { $params.TenantId } else { "(not set)" }
        
        Write-Host "  1 - Subscription:   $subDisplay"
        Write-Host "  2 - Resource Group: $rgDisplay"
        Write-Host "  3 - Location:       $locDisplay"
        Write-Host "  4 - Tenant:         $tenDisplay"
        Write-Host "  5 - Resource Name:  $($params.ResourceName)"
        Write-Host ""
        Write-Host "  6 - Confirm and Connect"
        Write-Host "  7 - Cancel"
        Write-Host ""
        
        $choice = Read-Host "Select option"
        
        switch ($choice) {
            "1" {
                $value = Read-Host "Enter Subscription ID"
                if (-not [string]::IsNullOrWhiteSpace($value)) {
                    $params.SubscriptionId = $value
                }
            }
            "2" {
                $value = Read-Host "Enter Resource Group"
                if (-not [string]::IsNullOrWhiteSpace($value)) {
                    $params.ResourceGroup = $value
                }
            }
            "3" {
                $value = Read-Host "Enter Location (e.g., westeurope)"
                if (-not [string]::IsNullOrWhiteSpace($value)) {
                    $params.Location = $value
                }
            }
            "4" {
                $value = Read-Host "Enter Tenant ID"
                if (-not [string]::IsNullOrWhiteSpace($value)) {
                    $params.TenantId = $value
                }
            }
            "5" {
                $value = Read-Host "Enter Resource Name"
                if (-not [string]::IsNullOrWhiteSpace($value)) {
                    $params.ResourceName = $value
                }
            }
            "6" {
                # Validate required fields
                if (-not $params.SubscriptionId) {
                    Write-Host "ERROR: Subscription ID is required." -ForegroundColor Red
                    continue
                }
                if (-not $params.ResourceGroup) {
                    Write-Host "ERROR: Resource Group is required." -ForegroundColor Red
                    continue
                }
                if (-not $params.Location) {
                    Write-Host "ERROR: Location is required." -ForegroundColor Red
                    continue
                }
                return $params
            }
            "7" {
                return $null
            }
            default {
                Write-Host "Invalid option." -ForegroundColor Yellow
            }
        }
    }
}

function Connect-ToArc {
    param([hashtable]$Params)
    
    # LOG-GN-09: Announce before execution
    Write-Host ""
    Write-Host "Connecting to Azure Arc (resource_name='$($Params.ResourceName)')..."
    Write-Host "  Using device code authentication..."
    
    try {
        $arguments = @(
            "connect"
            "--subscription-id", $Params.SubscriptionId
            "--resource-group", $Params.ResourceGroup
            "--location", $Params.Location
            "--resource-name", $Params.ResourceName
            "--use-device-code"
        )
        
        if (-not [string]::IsNullOrWhiteSpace($Params.TenantId)) {
            $arguments += @("--tenant-id", $Params.TenantId)
        }
        
        & $script:AgentPath @arguments
        
        # Report
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  OK. Connected to Azure Arc." -ForegroundColor Green
            Write-Host "  System-assigned MI created."
            Write-Host "  Token endpoint: http://localhost:40342/metadata/identity/oauth2/token"
            return $true
        }
        else {
            Write-Host "  FAIL: Connection failed -> Check error messages above." -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "  FAIL: Could not connect -> $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# =============================================================================
# Disconnection Functions
# =============================================================================

function Disconnect-FromArc {
    Write-Host ""
    Write-Host "WARNING: Disconnect will:" -ForegroundColor Yellow
    Write-Host "  - Delete the Azure resource for this computer"
    Write-Host "  - Remove the managed identity"
    Write-Host "  - Keep the agent installed (can reconnect later)"
    Write-Host ""
    Write-Host "1 - Yes, disconnect"
    Write-Host "2 - No, cancel"
    Write-Host ""
    
    $confirm = Read-Host "Select option"
    if ($confirm -ne "1") {
        Write-Host "SKIP: Disconnect cancelled." -ForegroundColor Gray
        return $false
    }
    
    # LOG-GN-09: Announce before execution
    Write-Host ""
    Write-Host "Disconnecting from Azure Arc..."
    Write-Host "  Using device code authentication..."
    
    try {
        & $script:AgentPath disconnect --use-device-code
        
        # Report
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  OK. Disconnected from Azure Arc." -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "  FAIL: Disconnection failed -> Check error messages above." -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "  FAIL: Could not disconnect -> $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# =============================================================================
# Managed Identity Functions
# =============================================================================

function Show-SystemAssignedMI {
    param([hashtable]$Status)
    
    Write-Host ""
    Write-Host "Querying system-assigned managed identity..."
    
    # Check Azure CLI
    $azCmd = Get-Command az -ErrorAction SilentlyContinue
    if (-not $azCmd) {
        Write-Host "  FAIL: Azure CLI (az) is not installed." -ForegroundColor Red
        return
    }
    
    # Check connectedmachine extension
    $extCheck = az extension list --query "[?name=='connectedmachine'].name" -o tsv 2>$null
    if (-not $extCheck) {
        Write-Host "  Installing 'connectedmachine' extension..."
        az extension add --name connectedmachine --yes 2>$null
    }
    
    try {
        $machineJson = az connectedmachine show `
            --name $Status.ResourceName `
            --resource-group $Status.ResourceGroup `
            --output json `
            2>$null
        
        if ($LASTEXITCODE -ne 0 -or -not $machineJson) {
            Write-Host "  FAIL: Could not query machine details." -ForegroundColor Red
            return
        }
        
        $machine = $machineJson | ConvertFrom-Json
        
        Write-Host ""
        Write-Host "System-Assigned Managed Identity:" -ForegroundColor Cyan
        Write-Host "  name='$($Status.ResourceName)'"
        Write-Host "  principal_id='$($machine.identity.principalId)'"
        Write-Host "  tenant_id='$($machine.identity.tenantId)'"
        Write-Host "  type='$($machine.identity.type)'"
        Write-Host ""
        Write-Host "Use principal_id for RBAC role assignments."
        Write-Host ""
    }
    catch {
        Write-Host "  FAIL: Could not query MI -> $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Attach-UserAssignedMI {
    param([hashtable]$Status)
    
    $miObjectId = $script:Config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID
    $miName = $script:Config.CRAWLER_MANAGED_IDENTITY_NAME
    
    if (-not $miObjectId) {
        Write-Host "SKIP: No user-assigned MI configured in .env." -ForegroundColor Gray
        return $false
    }
    
    Write-Host ""
    $miDisplay = if ($miName) { "name='$miName' (id='$miObjectId')" } else { "id='$miObjectId'" }
    Write-Host "User-Assigned MI: $miDisplay"
    Write-Host ""
    Write-Host "1 - Yes, attach MI"
    Write-Host "2 - No, skip"
    Write-Host ""
    
    $confirm = Read-Host "Select option"
    if ($confirm -ne "1") {
        Write-Host "SKIP: MI attachment cancelled." -ForegroundColor Gray
        return $false
    }
    
    # Check if Azure CLI is available
    $azCmd = Get-Command az -ErrorAction SilentlyContinue
    if (-not $azCmd) {
        Write-Host "FAIL: Azure CLI (az) is not installed." -ForegroundColor Red
        Write-Host "HINT: Install from 'https://docs.microsoft.com/en-us/cli/azure/install-azure-cli'"
        return $false
    }
    
    # Check Azure CLI authentication first
    Write-Host ""
    Write-Host "Checking Azure CLI authentication..."
    $accountJson = az account show 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $accountJson) {
        Write-Host "  Not logged in. Running 'az login'..."
        az login
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  FAIL: Azure CLI login failed." -ForegroundColor Red
            return $false
        }
    } else {
        $account = $accountJson | ConvertFrom-Json
        Write-Host "  OK. Logged in as '$($account.user.name)' (subscription='$($account.name)')." -ForegroundColor Green
    }
    
    # Check if connectedmachine extension is installed
    Write-Host "Checking Azure CLI 'connectedmachine' extension..."
    $extCheck = az extension list --query "[?name=='connectedmachine'].name" -o tsv 2>$null
    if (-not $extCheck) {
        Write-Host "  Extension not installed. Installing..."
        az extension add --name connectedmachine --yes
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  FAIL: Could not install connectedmachine extension." -ForegroundColor Red
            return $false
        }
        Write-Host "  OK. Extension installed." -ForegroundColor Green
    } else {
        Write-Host "  OK. Extension already installed." -ForegroundColor Green
    }
    
    # LOG-GN-09: Announce before execution
    Write-Host ""
    Write-Host "Attaching user-assigned MI to Arc machine..."
    
    try {
        $subscriptionId = $Status.SubscriptionId
        $resourceGroup = $Status.ResourceGroup
        
        $miResourceGroup = $script:Config.CRAWLER_MANAGED_IDENTITY_RESOURCE_GROUP
        if (-not $miResourceGroup) {
            $miResourceGroup = $resourceGroup
        }
        
        if (-not $miName) {
            Write-Host "  WARNING: CRAWLER_MANAGED_IDENTITY_NAME not set in .env." -ForegroundColor Yellow
            $miName = Read-Host "  Enter MI name"
        }
        
        $miResourceId = "/subscriptions/$subscriptionId/resourceGroups/$miResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/$miName"
        
        Write-Host "  mi_resource_id='$miResourceId'"
        Write-Host "  Calling Azure CLI (may require authentication)..."
        
        $result = az connectedmachine update `
            --name $Status.ResourceName `
            --resource-group $resourceGroup `
            --identity-type "SystemAssigned,UserAssigned" `
            --user-assigned-identities $miResourceId `
            2>&1
        
        # Report
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  OK. User-assigned MI attached." -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "  FAIL: Could not attach MI -> $result" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "  FAIL: Could not attach MI -> $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# =============================================================================
# Uninstall Functions
# =============================================================================

function Uninstall-ArcAgent {
    # Check if still connected
    $status = Get-ArcStatus
    if ($status.Connected) {
        Write-Host "FAIL: Cannot uninstall while connected to Azure." -ForegroundColor Red
        Write-Host "HINT: Disconnect first using option 1."
        return $false
    }
    
    # LOG-GN-09: Announce before execution
    Write-Host ""
    Write-Host "Uninstalling Azure Connected Machine Agent..."
    Write-Host "  Finding agent in registry..."
    
    try {
        $uninstallKey = Get-ChildItem -Path "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall" |
            Get-ItemProperty |
            Where-Object { $_.DisplayName -eq "Azure Connected Machine Agent" }
        
        if (-not $uninstallKey) {
            Write-Host "  WARNING: Agent not found in registry. May already be uninstalled." -ForegroundColor Yellow
            return $true
        }
        
        $productCode = $uninstallKey.PSChildName
        Write-Host "  Running msiexec (product_code='$productCode')..."
        
        Start-Process -FilePath "msiexec.exe" -ArgumentList "/x `"$productCode`" /qn" -Wait -PassThru | Out-Null
        Start-Sleep -Seconds 2
        
        # Report
        if (-not (Test-Path $script:AgentPath)) {
            Write-Host "  OK. Agent uninstalled." -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "  WARNING: Uninstall completed but agent path still exists." -ForegroundColor Yellow
            return $true
        }
    }
    catch {
        Write-Host "  FAIL: Could not uninstall -> $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# =============================================================================
# Idempotent Setup Flow
# =============================================================================

function Invoke-CompleteSetup {
    param([hashtable]$Status)
    
    # LOG-UF-02: Use [ x / n ] format for steps
    
    # Step 1: Install agent if not installed
    if (-not $Status.AgentInstalled) {
        Write-Host ""
        Write-Host "[ 1 / 3 ] Installing agent..."
        if (-not (Install-ArcAgent)) {
            Write-Host "FAIL: Setup incomplete." -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host ""
        Write-Host "[ 1 / 3 ] SKIP: Agent already installed." -ForegroundColor Gray
    }
    
    # Step 2: Connect to Arc if not connected
    if (-not $Status.Connected) {
        Write-Host ""
        Write-Host "[ 2 / 3 ] Connecting to Azure Arc..."
        $params = Read-ConnectionParams
        if (-not $params) {
            Write-Host "SKIP: Connection cancelled." -ForegroundColor Gray
            return $false
        }
        if (-not (Connect-ToArc -Params $params)) {
            Write-Host "FAIL: Setup incomplete." -ForegroundColor Red
            return $false
        }
        # Refresh status after connection
        $Status = Get-ArcStatus
    } else {
        Write-Host ""
        Write-Host "[ 2 / 3 ] SKIP: Already connected to Azure Arc." -ForegroundColor Gray
    }
    
    # Step 3: Attach user-assigned MI if configured
    $miConfigured = [bool]$script:Config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID
    if ($miConfigured) {
        Write-Host ""
        Write-Host "[ 3 / 3 ] Attaching user-assigned MI..."
        Attach-UserAssignedMI -Status $Status
    } else {
        Write-Host ""
        Write-Host "[ 3 / 3 ] SKIP: No user-assigned MI configured." -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "OK. Setup complete." -ForegroundColor Green
    return $true
}

# =============================================================================
# Main Script
# =============================================================================

# Check admin privileges
if (-not (Test-AdminPrivilege)) {
    Write-Host "FAIL: This script requires Administrator privileges." -ForegroundColor Red
    Write-Host "HINT: Run PowerShell as Administrator and try again."
    exit 1
}

# Load configuration from .env
$envPath = Join-Path $script:WorkspaceRoot ".env"
$script:Config = Read-EnvFile -Path $envPath

# Get current status
$status = Get-ArcStatus

# Display UI
Show-Header
Show-Checklist -Status $status
$choice = Show-Menu -Status $status

# Determine state and handle choice
$miConfigured = [bool]$script:Config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID
$allComplete = $status.AgentInstalled -and $status.Connected

if ($allComplete) {
    # Connected - handle based on MI config
    if ($miConfigured) {
        switch ($choice) {
            "1" { Show-SystemAssignedMI -Status $status }
            "2" { Attach-UserAssignedMI -Status $status }
            "3" { Disconnect-FromArc }
            "4" {
                if (Disconnect-FromArc) {
                    Uninstall-ArcAgent
                }
            }
            "5" { Write-Host "Goodbye."; exit 0 }
            default { Write-Host "Invalid option." -ForegroundColor Yellow }
        }
    } else {
        switch ($choice) {
            "1" { Show-SystemAssignedMI -Status $status }
            "2" { Disconnect-FromArc }
            "3" {
                if (Disconnect-FromArc) {
                    Uninstall-ArcAgent
                }
            }
            "4" { Write-Host "Goodbye."; exit 0 }
            default { Write-Host "Invalid option." -ForegroundColor Yellow }
        }
    }
}
elseif ($status.AgentInstalled -and -not $status.Connected) {
    # Agent installed but not connected
    switch ($choice) {
        "1" { Invoke-CompleteSetup -Status $status }
        "2" { Uninstall-ArcAgent }
        "3" { Write-Host "Goodbye."; exit 0 }
        default { Write-Host "Invalid option." -ForegroundColor Yellow }
    }
}
else {
    # Nothing installed - full setup
    switch ($choice) {
        "1" { Invoke-CompleteSetup -Status $status }
        "2" { Write-Host "Goodbye."; exit 0 }
        default { Write-Host "Invalid option." -ForegroundColor Yellow }
    }
}

# LOG-UF-06: Show footer
Show-Footer

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
