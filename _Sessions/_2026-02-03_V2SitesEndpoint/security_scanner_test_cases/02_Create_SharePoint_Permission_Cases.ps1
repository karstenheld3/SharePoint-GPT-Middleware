# 02_Create_SharePoint_Permission_Cases.ps1
# Creates SharePoint permission test cases for security scan testing
# Part of SCAN-TP01 test plan
# Requires: PnP.PowerShell module

# === Configuration ===
$customGroupName = "ScanTest Custom Group"
$testFolderPrefix = "TestFolder"
$testSubsiteName = "ScanTestSubsite"

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
Write-Host "Security Scan Test Data Setup - Phase 2: SharePoint Objects" -ForegroundColor Cyan
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

# Load created Entra ID objects
$entraObjectsPath = Join-Path $PSScriptRoot "created_entra_objects.json"
if (!(Test-Path $entraObjectsPath)) {
    throw "Entra ID objects file not found. Run 01_Create_EntraID_UsersAnd_Groups.ps1 first."
}
$entraObjects = Get-Content $entraObjectsPath | ConvertFrom-Json
Write-Status "Loaded Entra ID objects from: $entraObjectsPath"

# Validate required config
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_SELFTEST_SHAREPOINT_SITE)) { 
    throw "CRAWLER_SELFTEST_SHAREPOINT_SITE is required in .env file" 
}
if ([string]::IsNullOrWhiteSpace($config.PNP_CLIENT_ID)) { throw "PNP_CLIENT_ID is required" }

$siteUrl = $config.CRAWLER_SELFTEST_SHAREPOINT_SITE
$domain = $config.CRAWLER_SHAREPOINT_TENANT_NAME + ".onmicrosoft.com"
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_SHAREPOINT_TENANT_NAME)) { throw "CRAWLER_SHAREPOINT_TENANT_NAME is required" }

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

# === Create Custom SharePoint Group ===
Write-Host "`n--- Creating Custom SharePoint Group ---" -ForegroundColor Cyan

$existingGroup = Get-PnPGroup -Identity $customGroupName -ErrorAction SilentlyContinue

if ($existingGroup) {
    Write-Status "Custom group already exists: $customGroupName" "SKIP"
}
else {
    try {
        $newGroup = New-PnPGroup -Title $customGroupName -Description "Test group for security scan testing"
        Write-Status "Created SharePoint group: $customGroupName" "OK"
        
        # Set group permissions to Full Control
        Set-PnPGroupPermissions -Identity $customGroupName -AddRole "Full Control"
        Write-Status "Set Full Control permission for $customGroupName" "OK"
    }
    catch {
        Write-Status "Failed to create group: $($_.Exception.Message)" "ERROR"
    }
}

# === Add Entra ID Security Group to Custom SP Group ===
Write-Host "`n--- Adding Entra ID Group to SharePoint Group ---" -ForegroundColor Cyan

# Get the security group ID
$securityGroupId = $entraObjects.Groups.ScanTest_SecurityGroup01
if ($securityGroupId) {
    try {
        # Add security group to SP group using login name format
        $securityGroupLoginName = "c:0t.c|tenant|$securityGroupId"
        Add-PnPGroupMember -Group $customGroupName -LoginName $securityGroupLoginName -ErrorAction SilentlyContinue
        Write-Status "Added ScanTest_SecurityGroup01 to $customGroupName" "OK"
    }
    catch {
        Write-Status "Failed to add security group: $($_.Exception.Message)" "WARN"
    }
}
else {
    Write-Status "SecurityGroup01 ID not found in Entra objects" "ERROR"
}

# === Add M365 Group to Custom SP Group ===
$m365GroupId = $entraObjects.Groups.ScanTest_M365Group01
if ($m365GroupId) {
    try {
        $m365GroupLoginName = "c:0o.c|federateddirectoryclaimprovider|$m365GroupId"
        Add-PnPGroupMember -Group $customGroupName -LoginName $m365GroupLoginName -ErrorAction SilentlyContinue
        Write-Status "Added ScanTest_M365Group01 to $customGroupName" "OK"
    }
    catch {
        Write-Status "Failed to add M365 group: $($_.Exception.Message)" "WARN"
    }
}

# === Add Direct User to Site ===
Write-Host "`n--- Adding Direct User Assignment ---" -ForegroundColor Cyan

$directUserUpn = "scantest_user1@$domain"
try {
    # Add user directly to site with Read permission
    Set-PnPWebPermission -User $directUserUpn -AddRole "Read" -ErrorAction SilentlyContinue
    Write-Status "Added direct user $directUserUpn with Read permission" "OK"
}
catch {
    Write-Status "Failed to add direct user: $($_.Exception.Message)" "WARN"
}

# === Add User to Site Members Group (TC-07, TC-11) ===
Write-Host "`n--- Adding User to Site Members Group ---" -ForegroundColor Cyan

$membersUserUpn = "scantest_user2@$domain"
try {
    # Get Site Members group and add user
    $membersGroup = Get-PnPGroup | Where-Object { $_.Title -like "*Members*" -and $_.Title -notlike "*Owners*" } | Select-Object -First 1
    if ($membersGroup) {
        Add-PnPGroupMember -Group $membersGroup.Title -LoginName $membersUserUpn -ErrorAction SilentlyContinue
        Write-Status "Added $membersUserUpn to $($membersGroup.Title)" "OK"
    }
    else {
        Write-Status "Site Members group not found" "WARN"
    }
}
catch {
    Write-Status "Failed to add user to Site Members: $($_.Exception.Message)" "WARN"
}

# === Create Folders with Broken Inheritance ===
Write-Host "`n--- Creating Folders with Broken Inheritance ---" -ForegroundColor Cyan

# Get or create Documents library
$docLibrary = Get-PnPList -Identity "Documents" -ErrorAction SilentlyContinue
if (-not $docLibrary) {
    $docLibrary = Get-PnPList -Identity "Shared Documents" -ErrorAction SilentlyContinue
}
if (-not $docLibrary) {
    Write-Status "Documents library not found" "ERROR"
}
else {
    $libraryName = $docLibrary.Title
    Write-Status "Using library: $libraryName"
    
    # Folder 1: Direct share to user
    $folder1Name = "${testFolderPrefix}_DirectShare"
    try {
        $folder1 = Add-PnPFolder -Name $folder1Name -Folder $libraryName -ErrorAction SilentlyContinue
        if (-not $folder1) {
            $folder1 = Get-PnPFolder -Url "$libraryName/$folder1Name" -ErrorAction SilentlyContinue
        }
        
        if ($folder1) {
            # Break inheritance and add user directly
            $folderItem = Get-PnPListItem -List $libraryName -Query "<View><Query><Where><Eq><FieldRef Name='FileLeafRef'/><Value Type='Text'>$folder1Name</Value></Eq></Where></Query></View>"
            if ($folderItem) {
                Set-PnPListItemPermission -List $libraryName -Identity $folderItem.Id -InheritPermissions:$false
                Set-PnPListItemPermission -List $libraryName -Identity $folderItem.Id -User $directUserUpn -AddRole "Edit"
                Write-Status "Created folder with direct share: $folder1Name" "OK"
            }
        }
    }
    catch {
        Write-Status "Failed to create folder $folder1Name : $($_.Exception.Message)" "WARN"
    }
    
    # Folder 2: Shared with custom group
    $folder2Name = "${testFolderPrefix}_GroupShare"
    try {
        $folder2 = Add-PnPFolder -Name $folder2Name -Folder $libraryName -ErrorAction SilentlyContinue
        if (-not $folder2) {
            $folder2 = Get-PnPFolder -Url "$libraryName/$folder2Name" -ErrorAction SilentlyContinue
        }
        
        if ($folder2) {
            $folderItem = Get-PnPListItem -List $libraryName -Query "<View><Query><Where><Eq><FieldRef Name='FileLeafRef'/><Value Type='Text'>$folder2Name</Value></Eq></Where></Query></View>"
            if ($folderItem) {
                Set-PnPListItemPermission -List $libraryName -Identity $folderItem.Id -InheritPermissions:$false
                Set-PnPListItemPermission -List $libraryName -Identity $folderItem.Id -Group $customGroupName -AddRole "Edit"
                Write-Status "Created folder with group share: $folder2Name" "OK"
            }
        }
    }
    catch {
        Write-Status "Failed to create folder $folder2Name : $($_.Exception.Message)" "WARN"
    }
    
    # Folder 3: Sharing link (organization-wide)
    $folder3Name = "${testFolderPrefix}_SharingLink"
    try {
        $folder3 = Add-PnPFolder -Name $folder3Name -Folder $libraryName -ErrorAction SilentlyContinue
        if (-not $folder3) {
            $folder3 = Get-PnPFolder -Url "$libraryName/$folder3Name" -ErrorAction SilentlyContinue
        }
        
        if ($folder3) {
            $folderItem = Get-PnPListItem -List $libraryName -Query "<View><Query><Where><Eq><FieldRef Name='FileLeafRef'/><Value Type='Text'>$folder3Name</Value></Eq></Where></Query></View>"
            if ($folderItem) {
                Set-PnPListItemPermission -List $libraryName -Identity $folderItem.Id -InheritPermissions:$false
                Write-Status "Created folder for sharing link: $folder3Name (manually create sharing link)" "OK"
            }
        }
    }
    catch {
        Write-Status "Failed to create folder $folder3Name : $($_.Exception.Message)" "WARN"
    }
}

# === Create List Item with Broken Inheritance ===
Write-Host "`n--- Creating List with Broken Inheritance Item ---" -ForegroundColor Cyan

$testListName = "ScanTestList"
try {
    $existingList = Get-PnPList -Identity $testListName -ErrorAction SilentlyContinue
    
    if (-not $existingList) {
        $newList = New-PnPList -Title $testListName -Template GenericList
        Write-Status "Created test list: $testListName" "OK"
    }
    else {
        Write-Status "Test list already exists: $testListName" "SKIP"
    }
    
    # Add item with broken inheritance
    $testItem = Add-PnPListItem -List $testListName -Values @{ "Title" = "TestItem_BrokenInherit" }
    if ($testItem) {
        Set-PnPListItemPermission -List $testListName -Identity $testItem.Id -InheritPermissions:$false
        Set-PnPListItemPermission -List $testListName -Identity $testItem.Id -User $directUserUpn -AddRole "Contribute"
        Write-Status "Created list item with broken inheritance" "OK"
    }
}
catch {
    Write-Status "Failed to create test list/item: $($_.Exception.Message)" "WARN"
}

# === Create Subsite ===
Write-Host "`n--- Creating Subsite ---" -ForegroundColor Cyan

try {
    $existingSubsite = Get-PnPSubWeb -Identity $testSubsiteName -ErrorAction SilentlyContinue
    
    if ($existingSubsite) {
        Write-Status "Subsite already exists: $testSubsiteName" "SKIP"
    }
    else {
        $newSubsite = New-PnPWeb -Title $testSubsiteName -Url $testSubsiteName -Template "STS#3" -InheritPermissions:$false
        Write-Status "Created subsite: $testSubsiteName" "OK"
        
        # Add unique permission to subsite
        # Connect to subsite to set permissions
        $subsiteUrl = "$siteUrl/$testSubsiteName"
        Connect-PnPOnline -Url $subsiteUrl -Interactive -ClientId $config.PNP_CLIENT_ID -ErrorAction Stop
        
        Set-PnPWebPermission -User $directUserUpn -AddRole "Full Control"
        Write-Status "Added direct user to subsite with Full Control" "OK"
        
        # Reconnect to parent site
        Connect-PnPOnline -Url $siteUrl -Interactive -ClientId $config.PNP_CLIENT_ID -ErrorAction Stop
    }
}
catch {
    Write-Status "Failed to create subsite: $($_.Exception.Message)" "WARN"
}

# === Summary ===
Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

Write-Host "`nCreated SharePoint Objects:" -ForegroundColor White
Write-Host "  - Custom SP Group: $customGroupName"
Write-Host "    +-- Contains: ScanTest_SecurityGroup01 (Entra ID)"
Write-Host "    +-- Contains: ScanTest_M365Group01 (M365)"
Write-Host "  - Direct user assignment: $directUserUpn (Read)"
Write-Host "  - Site Members user: $membersUserUpn"
Write-Host "  - Folder with direct share: ${testFolderPrefix}_DirectShare"
Write-Host "  - Folder with group share: ${testFolderPrefix}_GroupShare"
Write-Host "  - Folder for sharing link: ${testFolderPrefix}_SharingLink"
Write-Host "  - Test list with item: $testListName"
Write-Host "  - Subsite: $testSubsiteName"

# Save created objects for cleanup
$outputPath = Join-Path $PSScriptRoot "created_sharepoint_objects.json"
$outputData = @{
    SiteUrl = $siteUrl
    CustomGroup = $customGroupName
    DirectUser = $directUserUpn
    MembersUser = $membersUserUpn
    TestFolders = @("${testFolderPrefix}_DirectShare", "${testFolderPrefix}_GroupShare", "${testFolderPrefix}_SharingLink")
    TestList = $testListName
    Subsite = $testSubsiteName
    CreatedAt = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
}
$outputData | ConvertTo-Json -Depth 3 | Out-File $outputPath -Encoding UTF8
Write-Status "`nSaved object info to: $outputPath" "OK"

# === Verification ===
Write-Host "`n--- Verifying SharePoint Objects ---" -ForegroundColor Cyan

$verificationPassed = $true

# Verify custom group exists
$verifyGroup = Get-PnPGroup -Identity $customGroupName -ErrorAction SilentlyContinue
if ($verifyGroup) {
    Write-Status "Custom SP group verified: $customGroupName" "OK"
    
    # Verify group members (Entra groups in SP group)
    $groupMembers = Get-PnPGroupMember -Group $customGroupName -ErrorAction SilentlyContinue
    $memberCount = ($groupMembers | Measure-Object).Count
    Write-Status "  Group has $memberCount members" "OK"
    
    # Check for security group
    $secGroupFound = $groupMembers | Where-Object { $_.LoginName -like "*$securityGroupId*" }
    if ($secGroupFound) {
        Write-Status "  ScanTest_SecurityGroup01 found in group" "OK"
    }
    else {
        Write-Status "  ScanTest_SecurityGroup01 NOT found in group" "FAIL"
        $verificationPassed = $false
    }
    
    # Check for M365 group
    $m365Found = $groupMembers | Where-Object { $_.LoginName -like "*$m365GroupId*" }
    if ($m365Found) {
        Write-Status "  ScanTest_M365Group01 found in group" "OK"
    }
    else {
        Write-Status "  ScanTest_M365Group01 NOT found in group" "FAIL"
        $verificationPassed = $false
    }
}
else {
    Write-Status "Custom SP group NOT found: $customGroupName" "FAIL"
    $verificationPassed = $false
}

# Verify test list
$verifyList = Get-PnPList -Identity $testListName -ErrorAction SilentlyContinue
if ($verifyList) {
    Write-Status "Test list verified: $testListName" "OK"
}
else {
    Write-Status "Test list NOT found: $testListName" "FAIL"
    $verificationPassed = $false
}

# Verify test folders
foreach ($folderSuffix in @("DirectShare", "GroupShare", "SharingLink")) {
    $folderName = "${testFolderPrefix}_$folderSuffix"
    $verifyFolder = Get-PnPFolder -Url "Shared Documents/$folderName" -ErrorAction SilentlyContinue
    if ($verifyFolder) {
        Write-Status "Test folder verified: $folderName" "OK"
    }
    else {
        Write-Status "Test folder NOT found: $folderName" "FAIL"
        $verificationPassed = $false
    }
}

# Verify subsite
$subsiteUrl = "$siteUrl/$testSubsiteName"
try {
    Connect-PnPOnline -Url $subsiteUrl -Interactive -ClientId $config.PNP_CLIENT_ID -ErrorAction Stop
    Write-Status "Subsite verified: $testSubsiteName" "OK"
    Connect-PnPOnline -Url $siteUrl -Interactive -ClientId $config.PNP_CLIENT_ID -ErrorAction Stop
}
catch {
    Write-Status "Subsite NOT accessible: $testSubsiteName" "FAIL"
    $verificationPassed = $false
}

# Final verification status
Write-Host ""
if ($verificationPassed) {
    Write-Host "=== ALL VERIFICATIONS PASSED ===" -ForegroundColor Green
    Write-Host "`nPhase 2 complete. Permission test cases are ready." -ForegroundColor Green
    Write-Host "Run the security scan to test, then use 03/04 scripts to clean up." -ForegroundColor Yellow
}
else {
    Write-Host "=== VERIFICATION FAILED ===" -ForegroundColor Red
    Write-Host "Some objects could not be verified. Check errors above." -ForegroundColor Yellow
    Write-Host "The Entra groups may not have been added to the SP group correctly." -ForegroundColor Yellow
}

# Disconnect
Disconnect-PnPOnline
