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
    
    # Check if user-assigned MI is attached (only if connected and MI configured)
    if ($result.Connected -and $script:Config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID) {
        $result.UserAssignedMIAttached = Test-UserAssignedMIAttached -Status $result
    }
    
    return $result
}

function Test-UserAssignedMIAttached {
    param([hashtable]$Status)
    
    $miObjectId = $script:Config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID
    if (-not $miObjectId) { return $false }
    
    try {
        # Check if Az.ConnectedMachine module is available
        if (-not (Get-Module -ListAvailable -Name Az.ConnectedMachine)) {
            return $false
        }
        
        # Try to get the machine and check identities
        $machine = Get-AzConnectedMachine -Name $Status.ResourceName -ResourceGroupName $Status.ResourceGroup -ErrorAction SilentlyContinue
        if (-not $machine) { return $false }
        
        # Check if user-assigned MI is in the list
        if ($machine.IdentityUserAssignedIdentity) {
            foreach ($key in $machine.IdentityUserAssignedIdentity.Keys) {
                if ($key -match $miObjectId) {
                    return $true
                }
            }
        }
        return $false
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
    
    # User-assigned MI attached
    $miId = $script:Config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID
    $miName = $script:Config.CRAWLER_MANAGED_IDENTITY_NAME
    if ($miId) {
        $miDisplay = if ($miName) { "$miName ($miId)" } else { $miId }
        if ($Status.UserAssignedMIAttached) {
            Write-Host "  [" -NoNewline
            Write-Host "x" -ForegroundColor Green -NoNewline
            Write-Host "] User-assigned MI attached ($miDisplay)"
        } else {
            Write-Host "  [ ] User-assigned MI attached ($miDisplay)"
        }
    }
    
    Write-Host ""
    
    # Show connection details if connected
    if ($Status.Connected) {
        Write-Host "Connection Details:"
        Write-Host "  Resource Group: $($Status.ResourceGroup)"
        Write-Host "  Subscription:   $($Status.SubscriptionId)"
        Write-Host "  Location:       $($Status.Location)"
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
    
    # Determine what steps are missing
    $allComplete = $Status.AgentInstalled -and $Status.Connected
    $miConfigured = [bool]$script:Config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID
    if ($miConfigured) {
        $allComplete = $allComplete -and $Status.UserAssignedMIAttached
    }
    
    if ($allComplete) {
        # All complete - offer disconnect options
        Write-Host "  1 - Disconnect from Azure"
        Write-Host "  2 - Disconnect and Uninstall Agent"
        Write-Host "  3 - Quit"
    }
    elseif ($Status.AgentInstalled -and -not $Status.Connected) {
        # Agent installed but not connected
        Write-Host "  1 - Complete Setup (connect, attach MI)"
        Write-Host "  2 - Uninstall Agent"
        Write-Host "  3 - Quit"
    }
    elseif ($Status.Connected -and $miConfigured -and -not $Status.UserAssignedMIAttached) {
        # Connected but MI not attached
        Write-Host "  1 - Attach User-Assigned MI"
        Write-Host "  2 - Disconnect from Azure"
        Write-Host "  3 - Disconnect and Uninstall Agent"
        Write-Host "  4 - Quit"
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
    
    try {
        # Check if Az.ConnectedMachine module is available
        if (-not (Get-Module -ListAvailable -Name Az.ConnectedMachine)) {
            Write-Host ""
            Write-Host "ERROR: " -NoNewline -ForegroundColor Red
            Write-Host "Az.ConnectedMachine module is not installed."
            Write-Host ""
            Write-Host "To install, run: Install-Module -Name Az.ConnectedMachine -Scope CurrentUser"
            return $false
        }
        
        # Import module
        Import-Module Az.ConnectedMachine -ErrorAction Stop
        
        # Check if connected to Azure
        $azContext = Get-AzContext -ErrorAction SilentlyContinue
        if (-not $azContext) {
            Write-Host "Connecting to Azure..."
            Connect-AzAccount -UseDeviceAuthentication
        }
        
        # Build the MI resource ID
        $subscriptionId = $Status.SubscriptionId
        $miResourceId = "/subscriptions/$subscriptionId/resourceGroups/$($script:Config.AZURE_RESOURCE_GROUP)/providers/Microsoft.ManagedIdentity/userAssignedIdentities/$miName"
        
        # If we don't have the MI name, try to construct from object ID
        if (-not $miName) {
            Write-Host "WARNING: " -NoNewline -ForegroundColor Yellow
            Write-Host "CRAWLER_MANAGED_IDENTITY_NAME not set in .env"
            Write-Host "Please provide the full resource ID of the managed identity:"
            $miResourceId = Read-Host "MI Resource ID"
        }
        
        Write-Host "Updating Arc machine with user-assigned MI..."
        
        Update-AzConnectedMachine -Name $Status.ResourceName -ResourceGroupName $Status.ResourceGroup `
            -IdentityType "SystemAssigned,UserAssigned" `
            -IdentityUserAssignedIdentity @{$miResourceId = @{}}
        
        Write-Host ""
        Write-Host "SUCCESS: " -NoNewline -ForegroundColor Green
        Write-Host "User-assigned managed identity attached."
        return $true
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
$allComplete = $status.AgentInstalled -and $status.Connected
$miConfigured = [bool]$script:Config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID
if ($miConfigured) {
    $allComplete = $allComplete -and $status.UserAssignedMIAttached
}

if ($allComplete) {
    # All complete - disconnect options
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
elseif ($status.AgentInstalled -and -not $status.Connected) {
    # Agent installed but not connected
    switch ($choice) {
        "1" { Invoke-CompleteSetup -Status $status }
        "2" { Uninstall-ArcAgent }
        "3" { Write-Host "Goodbye."; exit 0 }
        default { Write-Host "Invalid option." -ForegroundColor Yellow }
    }
}
elseif ($status.Connected -and $miConfigured -and -not $status.UserAssignedMIAttached) {
    # Connected but MI not attached
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
