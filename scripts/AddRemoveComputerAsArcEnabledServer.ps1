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
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "  Azure Arc-Enabled Server Management" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Show-Checklist {
    param([hashtable]$Status)
    
    Write-Host "Status:"
    
    # Agent installed
    if ($Status.AgentInstalled) {
        Write-Host "  [" -NoNewline
        Write-Host "x" -ForegroundColor Green -NoNewline
        Write-Host "] Agent installed (v$($Status.AgentVersion))"
    } else {
        Write-Host "  [ ] Agent installed"
    }
    
    # Connected to Arc
    if ($Status.Connected) {
        Write-Host "  [" -NoNewline
        Write-Host "x" -ForegroundColor Green -NoNewline
        Write-Host "] Connected to Azure Arc ($($Status.ResourceName))"
    } else {
        Write-Host "  [ ] Connected to Azure Arc"
    }
    
    # User-assigned MI configured (status checked on-demand via Azure CLI)
    $miId = $script:Config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID
    $miName = $script:Config.CRAWLER_MANAGED_IDENTITY_NAME
    if ($miId) {
        $miDisplay = if ($miName) { "$miName" } else { $miId }
        Write-Host "  [?] User-assigned MI configured: $miDisplay" -ForegroundColor Gray
    }
    
    Write-Host ""
    
    # Show connection details if connected
    if ($Status.Connected) {
        Write-Host "Connection Details:"
        Write-Host "  Resource Group: $($Status.ResourceGroup)"
        Write-Host "  Subscription:   $($Status.SubscriptionId)"
        Write-Host "  Location:       $($Status.Location)"
        Write-Host ""
        
        # System-assigned MI info shown via "az connectedmachine show" if needed
        Write-Host "System-Assigned MI: " -NoNewline
        Write-Host "(use Azure CLI to query details)" -ForegroundColor Gray
        
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
        # Connected - offer MI attachment (if configured) or disconnect
        if ($miConfigured) {
            Write-Host "  1 - Attach User-Assigned MI"
            Write-Host "  2 - Disconnect from Azure"
            Write-Host "  3 - Disconnect and Uninstall Agent"
            Write-Host "  4 - Quit"
        } else {
            Write-Host "  1 - Disconnect from Azure"
            Write-Host "  2 - Disconnect and Uninstall Agent"
            Write-Host "  3 - Quit"
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
    Write-Host ""
    Write-Host "--------------------------------------------------------------------------------"
    Write-Host "  Installing Azure Connected Machine Agent"
    Write-Host "--------------------------------------------------------------------------------"
    Write-Host ""
    
    try {
        Write-Host "Downloading installer from $script:DownloadUrl ..."
        Invoke-WebRequest -Uri $script:DownloadUrl -OutFile $script:InstallerPath -UseBasicParsing
        
        Write-Host "Running installer..."
        & $script:InstallerPath
        
        if (Test-Path $script:AgentPath) {
            $version = & $script:AgentPath version 2>$null
            Write-Host ""
            Write-Host "SUCCESS: " -NoNewline -ForegroundColor Green
            Write-Host "Azure Connected Machine Agent installed successfully."
            Write-Host "  Version: $version"
            return $true
        }
        else {
            Write-Host "ERROR: " -NoNewline -ForegroundColor Red
            Write-Host "Agent installation may have failed. Agent not found at expected path."
            return $false
        }
    }
    catch {
        Write-Host "ERROR: " -NoNewline -ForegroundColor Red
        Write-Host "Failed to install agent: $($_.Exception.Message)"
        Write-Host ""
        Write-Host "You can try manual installation:"
        Write-Host "  1. Download from: $script:DownloadUrl"
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
    
    Write-Host ""
    Write-Host "Connecting with device code authentication..."
    Write-Host ""
    
    try {
        $arguments = @(
            "connect"
            "--subscription-id", $Params.SubscriptionId
            "--resource-group", $Params.ResourceGroup
            "--location", $Params.Location
            "--resource-name", $Params.ResourceName
            "--use-device-code"
        )
        
        # Add tenant-id if provided
        if (-not [string]::IsNullOrWhiteSpace($Params.TenantId)) {
            $arguments += @("--tenant-id", $Params.TenantId)
        }
        
        & $script:AgentPath @arguments
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "SUCCESS: " -NoNewline -ForegroundColor Green
            Write-Host "Connected to Azure Arc successfully."
            Write-Host ""
            Write-Host "Your computer now has a system-assigned managed identity."
            Write-Host "Token endpoint: http://localhost:40342/metadata/identity/oauth2/token"
            return $true
        }
        else {
            Write-Host ""
            Write-Host "ERROR: " -NoNewline -ForegroundColor Red
            Write-Host "Connection failed. Check the error messages above."
            return $false
        }
    }
    catch {
        Write-Host "ERROR: " -NoNewline -ForegroundColor Red
        Write-Host "Failed to connect: $($_.Exception.Message)"
        return $false
    }
}

# =============================================================================
# Disconnection Functions
# =============================================================================

function Disconnect-FromArc {
    Write-Host ""
    Write-Host "--------------------------------------------------------------------------------"
    Write-Host "  Disconnect from Azure Arc"
    Write-Host "--------------------------------------------------------------------------------"
    Write-Host ""
    Write-Host "WARNING: This will:" -ForegroundColor Yellow
    Write-Host "  - Delete the Azure resource for this computer"
    Write-Host "  - Remove the managed identity"
    Write-Host "  - Keep the agent installed (can reconnect later)"
    Write-Host ""
    Write-Host "1 - Yes, disconnect"
    Write-Host "2 - No, cancel"
    Write-Host ""
    
    $confirm = Read-Host "Select option"
    if ($confirm -ne "1") {
        Write-Host "Cancelled."
        return $false
    }
    
    Write-Host ""
    Write-Host "Disconnecting with device code authentication..."
    Write-Host ""
    
    try {
        & $script:AgentPath disconnect --use-device-code
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "SUCCESS: " -NoNewline -ForegroundColor Green
            Write-Host "Disconnected from Azure Arc."
            return $true
        }
        else {
            Write-Host ""
            Write-Host "ERROR: " -NoNewline -ForegroundColor Red
            Write-Host "Disconnection failed. Check the error messages above."
            return $false
        }
    }
    catch {
        Write-Host "ERROR: " -NoNewline -ForegroundColor Red
        Write-Host "Failed to disconnect: $($_.Exception.Message)"
        return $false
    }
}

# =============================================================================
# User-Assigned Managed Identity Functions
# =============================================================================

function Attach-UserAssignedMI {
    param([hashtable]$Status)
    
    $miObjectId = $script:Config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID
    $miName = $script:Config.CRAWLER_MANAGED_IDENTITY_NAME
    
    if (-not $miObjectId) {
        Write-Host "No user-assigned MI configured in .env" -ForegroundColor Gray
        return $false
    }
    
    Write-Host ""
    Write-Host "--------------------------------------------------------------------------------"
    Write-Host "  Attach User-Assigned Managed Identity"
    Write-Host "--------------------------------------------------------------------------------"
    Write-Host ""
    
    $miDisplay = if ($miName) { "$miName ($miObjectId)" } else { $miObjectId }
    Write-Host "Managed Identity: $miDisplay"
    Write-Host ""
    Write-Host "1 - Yes, attach MI"
    Write-Host "2 - No, skip"
    Write-Host ""
    
    $confirm = Read-Host "Select option"
    if ($confirm -ne "1") {
        Write-Host "Skipped."
        return $false
    }
    
    Write-Host ""
    Write-Host "Attaching user-assigned managed identity..."
    
    # Check if Azure CLI is available
    $azCmd = Get-Command az -ErrorAction SilentlyContinue
    if (-not $azCmd) {
        Write-Host ""
        Write-Host "ERROR: " -NoNewline -ForegroundColor Red
        Write-Host "Azure CLI (az) is not installed."
        Write-Host ""
        Write-Host "Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        return $false
    }
    
    try {
        # Build the MI resource ID
        $subscriptionId = $Status.SubscriptionId
        $resourceGroup = $Status.ResourceGroup
        
        # Check CRAWLER_MANAGED_IDENTITY_RESOURCE_GROUP - MI may be in different RG
        $miResourceGroup = $script:Config.CRAWLER_MANAGED_IDENTITY_RESOURCE_GROUP
        if (-not $miResourceGroup) {
            $miResourceGroup = $resourceGroup
        }
        
        if (-not $miName) {
            Write-Host "WARNING: " -NoNewline -ForegroundColor Yellow
            Write-Host "CRAWLER_MANAGED_IDENTITY_NAME not set in .env"
            Write-Host "Please provide the managed identity name:"
            $miName = Read-Host "MI Name"
        }
        
        $miResourceId = "/subscriptions/$subscriptionId/resourceGroups/$miResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/$miName"
        
        Write-Host "MI Resource ID: $miResourceId"
        Write-Host ""
        Write-Host "Updating Arc machine with user-assigned MI via Azure CLI..."
        Write-Host "(You may need to authenticate)"
        Write-Host ""
        
        # Use Azure CLI to update the machine
        $result = az connectedmachine update `
            --name $Status.ResourceName `
            --resource-group $resourceGroup `
            --identity-type "SystemAssigned,UserAssigned" `
            --user-assigned-identities $miResourceId `
            2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "SUCCESS: " -NoNewline -ForegroundColor Green
            Write-Host "User-assigned managed identity attached."
            return $true
        }
        else {
            Write-Host ""
            Write-Host "ERROR: " -NoNewline -ForegroundColor Red
            Write-Host "Failed to attach MI:"
            Write-Host $result
            return $false
        }
    }
    catch {
        Write-Host ""
        Write-Host "ERROR: " -NoNewline -ForegroundColor Red
        Write-Host "Failed to attach MI: $($_.Exception.Message)"
        return $false
    }
}

# =============================================================================
# Uninstall Functions
# =============================================================================

function Uninstall-ArcAgent {
    Write-Host ""
    Write-Host "--------------------------------------------------------------------------------"
    Write-Host "  Uninstall Azure Connected Machine Agent"
    Write-Host "--------------------------------------------------------------------------------"
    Write-Host ""
    
    # Check if still connected
    $status = Get-ArcStatus
    if ($status.Status -eq "Connected") {
        Write-Host "ERROR: " -NoNewline -ForegroundColor Red
        Write-Host "Cannot uninstall while connected to Azure."
        Write-Host "Please disconnect first using option 1."
        return $false
    }
    
    Write-Host "Finding agent in registry..."
    
    try {
        $uninstallKey = Get-ChildItem -Path "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall" |
            Get-ItemProperty |
            Where-Object { $_.DisplayName -eq "Azure Connected Machine Agent" }
        
        if (-not $uninstallKey) {
            Write-Host "WARNING: " -NoNewline -ForegroundColor Yellow
            Write-Host "Agent not found in registry. It may already be uninstalled."
            return $true
        }
        
        $productCode = $uninstallKey.PSChildName
        Write-Host "Uninstalling (Product Code: $productCode)..."
        
        Start-Process -FilePath "msiexec.exe" -ArgumentList "/x `"$productCode`" /qn" -Wait -PassThru | Out-Null
        
        Start-Sleep -Seconds 2
        
        if (-not (Test-Path $script:AgentPath)) {
            Write-Host ""
            Write-Host "SUCCESS: " -NoNewline -ForegroundColor Green
            Write-Host "Azure Connected Machine Agent uninstalled successfully."
            return $true
        }
        else {
            Write-Host ""
            Write-Host "WARNING: " -NoNewline -ForegroundColor Yellow
            Write-Host "Uninstall completed but agent may still exist. Please verify manually."
            return $true
        }
    }
    catch {
        Write-Host "ERROR: " -NoNewline -ForegroundColor Red
        Write-Host "Failed to uninstall: $($_.Exception.Message)"
        return $false
    }
}

# =============================================================================
# Idempotent Setup Flow
# =============================================================================

function Invoke-CompleteSetup {
    param([hashtable]$Status)
    
    # Step 1: Install agent if not installed
    if (-not $Status.AgentInstalled) {
        Write-Host ""
        Write-Host "Step 1/3: Installing agent..." -ForegroundColor Cyan
        if (-not (Install-ArcAgent)) {
            return $false
        }
    } else {
        Write-Host ""
        Write-Host "Step 1/3: Agent already installed - skipping" -ForegroundColor Gray
    }
    
    # Step 2: Connect to Arc if not connected
    if (-not $Status.Connected) {
        Write-Host ""
        Write-Host "Step 2/3: Connecting to Azure Arc..." -ForegroundColor Cyan
        $params = Read-ConnectionParams
        if (-not $params) {
            Write-Host "Connection cancelled."
            return $false
        }
        if (-not (Connect-ToArc -Params $params)) {
            return $false
        }
        # Refresh status after connection
        $Status = Get-ArcStatus
    } else {
        Write-Host ""
        Write-Host "Step 2/3: Already connected to Azure Arc - skipping" -ForegroundColor Gray
    }
    
    # Step 3: Attach user-assigned MI if configured and not attached
    $miConfigured = [bool]$script:Config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID
    if ($miConfigured -and -not $Status.UserAssignedMIAttached) {
        Write-Host ""
        Write-Host "Step 3/3: Attaching user-assigned MI..." -ForegroundColor Cyan
        Attach-UserAssignedMI -Status $Status
    } elseif ($miConfigured) {
        Write-Host ""
        Write-Host "Step 3/3: User-assigned MI already attached - skipping" -ForegroundColor Gray
    } else {
        Write-Host ""
        Write-Host "Step 3/3: No user-assigned MI configured - skipping" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "Setup complete!" -ForegroundColor Green
    return $true
}

# =============================================================================
# Main Script
# =============================================================================

# Check admin privileges
if (-not (Test-AdminPrivilege)) {
    Write-Host "ERROR: " -NoNewline -ForegroundColor Red
    Write-Host "This script requires Administrator privileges."
    Write-Host "Please run PowerShell as Administrator and try again."
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
            "1" { Attach-UserAssignedMI -Status $status }
            "2" { Disconnect-FromArc }
            "3" {
                if (Disconnect-FromArc) {
                    Uninstall-ArcAgent
                }
            }
            "4" { Write-Host "Goodbye."; exit 0 }
            default { Write-Host "Invalid option." -ForegroundColor Yellow }
        }
    } else {
        switch ($choice) {
            "1" { Disconnect-FromArc }
            "2" {
                if (Disconnect-FromArc) {
                    Uninstall-ArcAgent
                }
            }
            "3" { Write-Host "Goodbye."; exit 0 }
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

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
