# 04_Remove_EntraID_UsersAnd_Groups.ps1
# Removes Entra ID users and groups created by script 01
# Part of SCAN-TP01 test plan

# === Default objects to remove (if tracking file not found) ===
$defaultUsers = @(
    "scantest_user1",
    "scantest_user2",
    "scantest_user3",
    "scantest_user4",
    "scantest_user5",
    "scantest_user6"
)

$defaultGroups = @(
    "ScanTest_SecurityGroup01",
    "ScanTest_SecurityGroup02",
    "ScanTest_SecurityGroup03",
    "ScanTest_M365Group01"
)

# === Helper Functions ===

function Read-EnvFile {
  param([Parameter(Mandatory=$true)] [string]$Path)
  $envVars = @{}  
  if (!(Test-Path $Path)) { throw "File '$($Path)' not found."  }
  Get-Content $Path | ForEach-Object {
    # ([^=]+)=([^#]*) captures key-value pairs separated by '=' in group 1 and 2
    # (?:#.*)?$ optionally matches comments after '#' in group 3
    if ($_ -match '^(?!#)([^=]+)=([^#]*)(?:#.*)?$') {
      $key = $matches[1].Trim(); $value = $matches[2].Trim()
      $envVars[$key] = $value
    }
  }
  return $envVars
}

function Write-Status {
    param([string]$Message, [string]$Status = "INFO", [string]$Color = "White")
    $statusColors = @{ "OK" = "Green"; "SKIP" = "Yellow"; "ERROR" = "Red"; "INFO" = "Cyan"; "WARN" = "Yellow" }
    if ($statusColors.ContainsKey($Status)) { $Color = $statusColors[$Status] }
    Write-Host "[$Status] $Message" -ForegroundColor $Color
}

# === Main Script ===

Clear-Host
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Security Scan Test Data Cleanup - Phase 4: Entra ID Objects" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Load configuration from .env
$envPath = Join-Path $PSScriptRoot "..\..\..\.env"
if (!(Test-Path $envPath)) {
    $envPath = Join-Path $PSScriptRoot "..\..\.env"
}
if (!(Test-Path $envPath)) {
    throw "Could not find .env file. Searched: $envPath"
}
$config = Read-EnvFile -Path $envPath
Write-Status "Loaded configuration from: $envPath"

# Validate required config
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_CLIENT_ID)) { throw "CRAWLER_CLIENT_ID is required in .env file" }
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_TENANT_ID)) { throw "CRAWLER_TENANT_ID is required in .env file" }
if ([string]::IsNullOrWhiteSpace($config.AZURE_SUBSCRIPTION_ID)) { throw "AZURE_SUBSCRIPTION_ID is required in .env file" }

$tenantId = $config.CRAWLER_TENANT_ID
$domain = $config.CRAWLER_SHAREPOINT_TENANT_NAME + ".onmicrosoft.com"
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_SHAREPOINT_TENANT_NAME)) {
    throw "CRAWLER_SHAREPOINT_TENANT_NAME is required in .env file"
}

Write-Host "Tenant ID: $tenantId" -ForegroundColor Gray
Write-Host "Domain: $domain" -ForegroundColor Gray

# Load created Entra ID objects
$entraObjectsPath = Join-Path $PSScriptRoot "created_entra_objects.json"
$useTrackingFile = $false

if (Test-Path $entraObjectsPath) {
    $entraObjects = Get-Content $entraObjectsPath | ConvertFrom-Json
    $useTrackingFile = $true
    Write-Status "Loaded Entra ID objects from: $entraObjectsPath"
}
else {
    Write-Status "Entra objects file not found, using default names" "WARN"
    $entraObjects = $null
}

# === Import required modules ===
Import-Module Az.Accounts -ErrorAction SilentlyContinue
Import-Module Az.Resources -ErrorAction SilentlyContinue
Import-Module Microsoft.Graph.Authentication -ErrorAction SilentlyContinue
Import-Module Microsoft.Graph.Users -ErrorAction SilentlyContinue
Import-Module Microsoft.Graph.Groups -ErrorAction SilentlyContinue

# Verify Graph module is available
if (-not (Get-Command "Get-MgUser" -ErrorAction SilentlyContinue)) {
    throw "Microsoft.Graph module is required. Install with: Install-Module Microsoft.Graph -Scope CurrentUser -Force"
}
Write-Host "Modules loaded" -ForegroundColor Green

# === Login to Azure (same pattern as AddRemoveCrawlerPermissions.ps1) ===
Write-Host "`nConnecting to Azure..." -ForegroundColor Cyan
Clear-AzContext -Force -ErrorAction SilentlyContinue

try {
    $null = Connect-AzAccount -Tenant $tenantId -Subscription $config.AZURE_SUBSCRIPTION_ID -WarningAction SilentlyContinue -InformationAction SilentlyContinue -ErrorAction Stop
    $context = Get-AzContext
    if ($null -eq $context) { throw "Failed to connect to Azure" }
    Write-Host "  Connected to Azure tenant: $($context.Tenant.Id)" -ForegroundColor Green
}
catch {
    throw "Failed to connect to Azure: $($_.Exception.Message)"
}

# === Connect to Microsoft Graph ===
Write-Host "`nConnecting to Microsoft Graph..." -ForegroundColor Cyan

$scopes = @(
    "User.ReadWrite.All",
    "Group.ReadWrite.All",
    "Directory.ReadWrite.All"
)

try {
    Disconnect-MgGraph -ErrorAction SilentlyContinue
    Connect-MgGraph -Scopes $scopes -TenantId $tenantId -NoWelcome
    
    $mgContext = Get-MgContext
    if ($null -eq $mgContext) { throw "Failed to connect to Microsoft Graph" }
    Write-Host "  Connected to Graph as: $($mgContext.Account)" -ForegroundColor Green
}
catch {
    throw "Failed to connect to Microsoft Graph: $($_.Exception.Message)"
}

# === Remove M365 Group First (has external dependencies) ===
Write-Host "`n--- Removing M365 Group ---" -ForegroundColor Cyan

$m365GroupName = "ScanTest M365 Group 01"
try {
    $m365Group = Get-MgGroup -Filter "displayName eq '$m365GroupName'" -ErrorAction SilentlyContinue
    if ($m365Group) {
        Remove-MgGroup -GroupId $m365Group.Id
        Write-Status "Removed M365 group: $m365GroupName" "OK"
    }
    else {
        Write-Status "M365 group not found: $m365GroupName" "SKIP"
    }
}
catch {
    Write-Status "Failed to remove M365 group: $($_.Exception.Message)" "WARN"
}

# === Remove Security Groups (reverse order due to nesting) ===
Write-Host "`n--- Removing Security Groups ---" -ForegroundColor Cyan

# Remove in reverse order: 01, 02, 03 (outer to inner)
$groupsToRemove = @(
    "ScanTest Security Group 01",
    "ScanTest Security Group 02",
    "ScanTest Security Group 03"
)

foreach ($groupName in $groupsToRemove) {
    try {
        $group = Get-MgGroup -Filter "displayName eq '$groupName'" -ErrorAction SilentlyContinue
        if ($group) {
            Remove-MgGroup -GroupId $group.Id
            Write-Status "Removed security group: $groupName" "OK"
        }
        else {
            Write-Status "Security group not found: $groupName" "SKIP"
        }
    }
    catch {
        Write-Status "Failed to remove security group $groupName : $($_.Exception.Message)" "WARN"
    }
}

# === Remove Test Users ===
Write-Host "`n--- Removing Test Users ---" -ForegroundColor Cyan

$usersToRemove = $defaultUsers
if ($useTrackingFile -and $entraObjects.Users) {
    $usersToRemove = $entraObjects.Users.PSObject.Properties.Name
}

foreach ($userName in $usersToRemove) {
    $upn = "$userName@$domain"
    try {
        $user = Get-MgUser -Filter "userPrincipalName eq '$upn'" -ErrorAction SilentlyContinue
        if ($user) {
            Remove-MgUser -UserId $user.Id
            Write-Status "Removed user: $upn" "OK"
        }
        else {
            Write-Status "User not found: $upn" "SKIP"
        }
    }
    catch {
        Write-Status "Failed to remove user $upn : $($_.Exception.Message)" "WARN"
    }
}

# === Summary ===
Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

Write-Host "`nRemoved Entra ID Objects:" -ForegroundColor White
Write-Host "  - M365 Group: $m365GroupName"
Write-Host "  - Security Groups: $($groupsToRemove -join ', ')"
Write-Host "  - Users: $($usersToRemove -join ', ')"

# Remove the tracking file
if ($useTrackingFile -and (Test-Path $entraObjectsPath)) {
    Remove-Item $entraObjectsPath -Force
    Write-Status "`nRemoved tracking file: $entraObjectsPath" "OK"
}

Write-Host "`nPhase 4 complete. All test data has been cleaned up." -ForegroundColor Green

# Disconnect
Disconnect-MgGraph -ErrorAction SilentlyContinue
