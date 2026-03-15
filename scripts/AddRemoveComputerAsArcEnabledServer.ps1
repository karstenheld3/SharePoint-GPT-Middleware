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
    if (-not (Test-Path $script:AgentPath)) {
        return @{
            Status = "NotInstalled"
            AgentInstalled = $false
        }
    }
    
    try {
        $jsonOutput = & $script:AgentPath show --json 2>$null
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($jsonOutput)) {
            return @{
                Status = "Disconnected"
                AgentInstalled = $true
                AgentVersion = (& $script:AgentPath version 2>$null)
            }
        }
        
        $info = $jsonOutput | ConvertFrom-Json
        return @{
            Status = if ($info.status -eq "Connected") { "Connected" } else { "Disconnected" }
            AgentInstalled = $true
            AgentVersion = $info.agentVersion
            ResourceName = $info.resourceName
            ResourceGroup = $info.resourceGroup
            SubscriptionId = $info.subscriptionId
            TenantId = $info.tenantId
            Location = $info.location
        }
    }
    catch {
        return @{
            Status = "Disconnected"
            AgentInstalled = $true
            AgentVersion = "Unknown"
        }
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

function Show-Status {
    param([hashtable]$Status)
    
    switch ($Status.Status) {
        "NotInstalled" {
            Write-Host "Current Status: " -NoNewline
            Write-Host "NOT INSTALLED" -ForegroundColor Yellow
            Write-Host "  Azure Connected Machine agent is not installed on this computer."
        }
        "Disconnected" {
            Write-Host "Current Status: " -NoNewline
            Write-Host "DISCONNECTED" -ForegroundColor Yellow
            Write-Host "  Agent Version: $($Status.AgentVersion)"
            Write-Host "  The agent is installed but not connected to Azure."
        }
        "Connected" {
            Write-Host "Current Status: " -NoNewline
            Write-Host "CONNECTED" -ForegroundColor Green
            Write-Host "  Resource Name:  $($Status.ResourceName)"
            Write-Host "  Resource Group: $($Status.ResourceGroup)"
            Write-Host "  Subscription:   $($Status.SubscriptionId)"
            Write-Host "  Location:       $($Status.Location)"
            Write-Host "  Agent Version:  $($Status.AgentVersion)"
            Write-Host ""
            Write-Host "Managed Identity Endpoint: " -NoNewline
            Write-Host "http://localhost:40342/metadata/identity/oauth2/token" -ForegroundColor Cyan
        }
    }
    Write-Host ""
}

function Show-Menu {
    param([hashtable]$Status)
    
    Write-Host "--------------------------------------------------------------------------------"
    Write-Host "Options:"
    
    switch ($Status.Status) {
        "NotInstalled" {
            Write-Host "  1 - Install Agent and Connect to Azure"
            Write-Host "  Q - Quit"
            Write-Host ""
            $choice = Read-Host "Select option"
            return $choice
        }
        "Disconnected" {
            Write-Host "  1 - Connect to Azure"
            Write-Host "  2 - Uninstall Agent"
            Write-Host "  Q - Quit"
            Write-Host ""
            $choice = Read-Host "Select option"
            return $choice
        }
        "Connected" {
            Write-Host "  1 - Disconnect from Azure"
            Write-Host "  2 - Disconnect and Uninstall Agent"
            Write-Host "  Q - Quit"
            Write-Host ""
            $choice = Read-Host "Select option"
            return $choice
        }
    }
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
    Write-Host ""
    Write-Host "--------------------------------------------------------------------------------"
    Write-Host "  Connect to Azure Arc"
    Write-Host "--------------------------------------------------------------------------------"
    Write-Host ""
    
    # Load defaults from .env file
    $envPath = Join-Path $script:WorkspaceRoot ".env"
    $config = Read-EnvFile -Path $envPath
    
    $defaultSubscription = $config.AZURE_SUBSCRIPTION_ID
    $defaultResourceGroup = $config.AZURE_RESOURCE_GROUP
    $defaultLocation = $config.AZURE_LOCATION
    $defaultTenant = $config.AZURE_TENANT_ID
    
    # Show defaults if available
    if ($defaultSubscription) {
        Write-Host "Defaults from .env:" -ForegroundColor Gray
        Write-Host "  Subscription:   $defaultSubscription" -ForegroundColor Gray
        Write-Host "  Resource Group: $defaultResourceGroup" -ForegroundColor Gray
        Write-Host "  Location:       $defaultLocation" -ForegroundColor Gray
        Write-Host "  Tenant:         $defaultTenant" -ForegroundColor Gray
        Write-Host ""
    }
    
    $prompt = if ($defaultSubscription) { "Enter Azure Subscription ID (Enter for '$defaultSubscription')" } else { "Enter Azure Subscription ID or Name" }
    $subscriptionId = Read-Host $prompt
    if ([string]::IsNullOrWhiteSpace($subscriptionId)) {
        if ($defaultSubscription) { $subscriptionId = $defaultSubscription }
        else {
            Write-Host "ERROR: " -NoNewline -ForegroundColor Red
            Write-Host "Subscription ID is required."
            return $null
        }
    }
    
    $prompt = if ($defaultResourceGroup) { "Enter Resource Group Name (Enter for '$defaultResourceGroup')" } else { "Enter Resource Group Name" }
    $resourceGroup = Read-Host $prompt
    if ([string]::IsNullOrWhiteSpace($resourceGroup)) {
        if ($defaultResourceGroup) { $resourceGroup = $defaultResourceGroup }
        else {
            Write-Host "ERROR: " -NoNewline -ForegroundColor Red
            Write-Host "Resource Group is required."
            return $null
        }
    }
    
    $prompt = if ($defaultLocation) { "Enter Azure Region (Enter for '$defaultLocation')" } else { "Enter Azure Region (e.g., westeurope)" }
    $location = Read-Host $prompt
    if ([string]::IsNullOrWhiteSpace($location)) {
        if ($defaultLocation) { $location = $defaultLocation }
        else {
            Write-Host "ERROR: " -NoNewline -ForegroundColor Red
            Write-Host "Location is required."
            return $null
        }
    }
    
    $defaultName = $env:COMPUTERNAME
    $resourceName = Read-Host "Enter Resource Name (Enter for '$defaultName')"
    if ([string]::IsNullOrWhiteSpace($resourceName)) {
        $resourceName = $defaultName
    }
    
    return @{
        SubscriptionId = $subscriptionId
        ResourceGroup = $resourceGroup
        TenantId = $defaultTenant
        Location = $location
        ResourceName = $resourceName
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
    
    $confirm = Read-Host "Are you sure you want to disconnect? (Y/N)"
    if ($confirm -ne "Y" -and $confirm -ne "y") {
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
# Main Script
# =============================================================================

# Check admin privileges
if (-not (Test-AdminPrivilege)) {
    Write-Host "ERROR: " -NoNewline -ForegroundColor Red
    Write-Host "This script requires Administrator privileges."
    Write-Host "Please run PowerShell as Administrator and try again."
    exit 1
}

# Get current status
$status = Get-ArcStatus

# Display UI
Show-Header
Show-Status -Status $status
$choice = Show-Menu -Status $status

# Handle user choice based on current state
switch ($status.Status) {
    "NotInstalled" {
        switch ($choice.ToUpper()) {
            "1" {
                if (Install-ArcAgent) {
                    $params = Read-ConnectionParams
                    if ($params) {
                        Connect-ToArc -Params $params
                    }
                }
            }
            "Q" { Write-Host "Goodbye."; exit 0 }
            default { Write-Host "Invalid option." -ForegroundColor Yellow }
        }
    }
    "Disconnected" {
        switch ($choice.ToUpper()) {
            "1" {
                $params = Read-ConnectionParams
                if ($params) {
                    Connect-ToArc -Params $params
                }
            }
            "2" { Uninstall-ArcAgent }
            "Q" { Write-Host "Goodbye."; exit 0 }
            default { Write-Host "Invalid option." -ForegroundColor Yellow }
        }
    }
    "Connected" {
        switch ($choice.ToUpper()) {
            "1" { Disconnect-FromArc }
            "2" {
                if (Disconnect-FromArc) {
                    Uninstall-ArcAgent
                }
            }
            "Q" { Write-Host "Goodbye."; exit 0 }
            default { Write-Host "Invalid option." -ForegroundColor Yellow }
        }
    }
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
