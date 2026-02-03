# 03_Remove_SharePoint_Permission_Cases.ps1
# Removes SharePoint permission test cases created by script 02
# Part of SCAN-TP01 test plan
# Requires: PnP.PowerShell module

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
Write-Host "Security Scan Test Data Cleanup - Phase 3: SharePoint Objects" -ForegroundColor Cyan
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

# Load created SharePoint objects
$spObjectsPath = Join-Path $PSScriptRoot "created_sharepoint_objects.json"
if (!(Test-Path $spObjectsPath)) {
    Write-Status "SharePoint objects file not found: $spObjectsPath" "WARN"
    Write-Status "Will attempt to clean up using default names" "INFO"
    $spObjects = @{
        SiteUrl = $config.CRAWLER_SELFTEST_SHAREPOINT_SITE
        CustomGroup = "ScanTest Custom Group"
        DirectUser = "scantest_user1@" + $config.CRAWLER_TENANT_DOMAIN
        TestFolders = @("TestFolder_DirectShare", "TestFolder_GroupShare", "TestFolder_SharingLink")
        TestList = "ScanTestList"
        Subsite = "ScanTestSubsite"
    }
}
else {
    $spObjects = Get-Content $spObjectsPath | ConvertFrom-Json
    Write-Status "Loaded SharePoint objects from: $spObjectsPath"
}

# Validate required config
if ([string]::IsNullOrWhiteSpace($config.PNP_CLIENT_ID)) { throw "PNP_CLIENT_ID is required" }

$siteUrl = $spObjects.SiteUrl
if ([string]::IsNullOrWhiteSpace($siteUrl)) {
    $siteUrl = $config.CRAWLER_SELFTEST_SHAREPOINT_SITE
}

Write-Status "Target site: $siteUrl"

# === Connect to SharePoint via PnP ===
Write-Host "`nConnecting to SharePoint..." -ForegroundColor Cyan

# Import PnP.PowerShell module (must be pre-installed)
Import-Module PnP.PowerShell -ErrorAction Stop

try {
    # Use Interactive login with PnP Management Shell app (same as AddRemoveCrawlerSharePointSites.ps1)
    Connect-PnPOnline -Url $siteUrl -Interactive -ClientId $config.PNP_CLIENT_ID -ErrorAction Stop
    Write-Status "Connected to SharePoint site" "OK"
}
catch {
    throw "Failed to connect to SharePoint: $($_.Exception.Message)"
}

# === Remove Subsite First ===
Write-Host "`n--- Removing Subsite ---" -ForegroundColor Cyan

if ($spObjects.Subsite) {
    try {
        $subsite = Get-PnPSubWeb -Identity $spObjects.Subsite -ErrorAction SilentlyContinue
        if ($subsite) {
            Remove-PnPWeb -Identity $spObjects.Subsite -Force
            Write-Status "Removed subsite: $($spObjects.Subsite)" "OK"
        }
        else {
            Write-Status "Subsite not found: $($spObjects.Subsite)" "SKIP"
        }
    }
    catch {
        Write-Status "Failed to remove subsite: $($_.Exception.Message)" "WARN"
    }
}

# === Remove Test List ===
Write-Host "`n--- Removing Test List ---" -ForegroundColor Cyan

if ($spObjects.TestList) {
    try {
        $list = Get-PnPList -Identity $spObjects.TestList -ErrorAction SilentlyContinue
        if ($list) {
            Remove-PnPList -Identity $spObjects.TestList -Force
            Write-Status "Removed test list: $($spObjects.TestList)" "OK"
        }
        else {
            Write-Status "Test list not found: $($spObjects.TestList)" "SKIP"
        }
    }
    catch {
        Write-Status "Failed to remove test list: $($_.Exception.Message)" "WARN"
    }
}

# === Remove Test Folders ===
Write-Host "`n--- Removing Test Folders ---" -ForegroundColor Cyan

$docLibrary = Get-PnPList -Identity "Documents" -ErrorAction SilentlyContinue
if (-not $docLibrary) {
    $docLibrary = Get-PnPList -Identity "Shared Documents" -ErrorAction SilentlyContinue
}

if ($docLibrary) {
    $libraryName = $docLibrary.Title
    
    foreach ($folderName in $spObjects.TestFolders) {
        try {
            $folderUrl = "$libraryName/$folderName"
            $folder = Get-PnPFolder -Url $folderUrl -ErrorAction SilentlyContinue
            if ($folder) {
                Remove-PnPFolder -Name $folderName -Folder $libraryName -Force
                Write-Status "Removed folder: $folderName" "OK"
            }
            else {
                Write-Status "Folder not found: $folderName" "SKIP"
            }
        }
        catch {
            Write-Status "Failed to remove folder $folderName : $($_.Exception.Message)" "WARN"
        }
    }
}
else {
    Write-Status "Documents library not found" "WARN"
}

# === Remove Direct User Permission ===
Write-Host "`n--- Removing Direct User Permission ---" -ForegroundColor Cyan

if ($spObjects.DirectUser) {
    try {
        Set-PnPWebPermission -User $spObjects.DirectUser -RemoveRole "Read" -ErrorAction SilentlyContinue
        Write-Status "Removed direct user permission: $($spObjects.DirectUser)" "OK"
    }
    catch {
        Write-Status "Failed to remove direct user permission: $($_.Exception.Message)" "WARN"
    }
}

# === Remove User from Site Members Group ===
Write-Host "`n--- Removing User from Site Members Group ---" -ForegroundColor Cyan

if ($spObjects.MembersUser) {
    try {
        $membersGroup = Get-PnPGroup | Where-Object { $_.Title -like "*Members*" -and $_.Title -notlike "*Owners*" } | Select-Object -First 1
        if ($membersGroup) {
            Remove-PnPGroupMember -Group $membersGroup.Title -LoginName $spObjects.MembersUser -ErrorAction SilentlyContinue
            Write-Status "Removed $($spObjects.MembersUser) from $($membersGroup.Title)" "OK"
        }
    }
    catch {
        Write-Status "Failed to remove user from Site Members: $($_.Exception.Message)" "WARN"
    }
}

# === Remove Custom SharePoint Group ===
Write-Host "`n--- Removing Custom SharePoint Group ---" -ForegroundColor Cyan

if ($spObjects.CustomGroup) {
    try {
        $group = Get-PnPGroup -Identity $spObjects.CustomGroup -ErrorAction SilentlyContinue
        if ($group) {
            Remove-PnPGroup -Identity $spObjects.CustomGroup -Force
            Write-Status "Removed SharePoint group: $($spObjects.CustomGroup)" "OK"
        }
        else {
            Write-Status "SharePoint group not found: $($spObjects.CustomGroup)" "SKIP"
        }
    }
    catch {
        Write-Status "Failed to remove SharePoint group: $($_.Exception.Message)" "WARN"
    }
}

# === Summary ===
Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

Write-Host "`nRemoved SharePoint Objects:" -ForegroundColor White
Write-Host "  - Subsite: $($spObjects.Subsite)"
Write-Host "  - Test list: $($spObjects.TestList)"
Write-Host "  - Test folders: $($spObjects.TestFolders -join ', ')"
Write-Host "  - Direct user permission: $($spObjects.DirectUser)"
Write-Host "  - Custom SP Group: $($spObjects.CustomGroup)"

# Remove the tracking file
if (Test-Path $spObjectsPath) {
    Remove-Item $spObjectsPath -Force
    Write-Status "`nRemoved tracking file: $spObjectsPath" "OK"
}

Write-Host "`nPhase 3 complete. Run 04_Remove_EntraID_UsersAnd_Groups.ps1 next." -ForegroundColor Green

# Disconnect
Disconnect-PnPOnline
