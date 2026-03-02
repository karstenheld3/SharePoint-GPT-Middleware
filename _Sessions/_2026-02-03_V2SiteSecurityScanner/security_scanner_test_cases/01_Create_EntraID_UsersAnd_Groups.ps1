# 01_Create_EntraID_UsersAnd_Groups.ps1
# Creates Entra ID users and groups for security scan testing
# Part of SSCSCN-TP01 test plan

# === Configuration ===
$testUserPassword = "P@ssw0rd123!"  # Temporary password, user must change on first login

# Test users to create
$testUsers = @(
    @{ Name = "scantest_user1"; DisplayName = "ScanTest User 1"; Description = "Direct assignment test user" }
    @{ Name = "scantest_user2"; DisplayName = "ScanTest User 2"; Description = "SP group member test user" }
    @{ Name = "scantest_user3"; DisplayName = "ScanTest User 3"; Description = "Security group member test user" }
    @{ Name = "scantest_user4"; DisplayName = "ScanTest User 4"; Description = "Nested group member (level 2)" }
    @{ Name = "scantest_user5"; DisplayName = "ScanTest User 5"; Description = "Deeply nested member (level 3)" }
    @{ Name = "scantest_user6"; DisplayName = "ScanTest User 6"; Description = "M365 group member test user" }
)

# Security groups to create (order matters for nesting)
$securityGroups = @(
    @{ Name = "ScanTest_SecurityGroup03"; DisplayName = "ScanTest Security Group 03"; Description = "Innermost nested group - contains user5"; Members = @("scantest_user5") }
    @{ Name = "ScanTest_SecurityGroup02"; DisplayName = "ScanTest Security Group 02"; Description = "Middle nested group - contains user4 and SecurityGroup03"; Members = @("scantest_user4"); NestedGroups = @("ScanTest_SecurityGroup03") }
    @{ Name = "ScanTest_SecurityGroup01"; DisplayName = "ScanTest Security Group 01"; Description = "Outer group - contains user3 and SecurityGroup02"; Members = @("scantest_user3"); NestedGroups = @("ScanTest_SecurityGroup02") }
)

# M365 group to create
$m365Group = @{
    Name = "ScanTest_M365Group01"
    DisplayName = "ScanTest M365 Group 01"
    Description = "M365 group for testing - contains user6"
    Members = @("scantest_user6")
}

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

function Write-Log {
    # Logging following Python PYTHON-LG-* conventions
    param(
        [string]$Message,
        [string]$Indent = "",  # LG-01: Sub-action indentation
        [int]$Current = 0,     # LG-05: Iteration [ x / n ]
        [int]$Total = 0
    )
    $prefix = if ($Current -gt 0 -and $Total -gt 0) { "[ $Current / $Total ] " } else { "" }
    Write-Host "$Indent$prefix$Message"
}

function Write-Status {
    # LG-03: Status keywords on separate indented line
    param([string]$Status, [string]$Message = "", [string]$Indent = "  ")
    $statusColors = @{ "OK" = "Green"; "SKIP" = "Yellow"; "ERROR" = "Red"; "WARNING" = "Yellow"; "FAIL" = "Red" }
    $color = if ($statusColors.ContainsKey($Status)) { $statusColors[$Status] } else { "White" }
    $text = if ($Message) { "$Status : $Message" } else { "$Status" }
    Write-Host "$Indent$text" -ForegroundColor $color
}

# === Main Script ===

Clear-Host
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Security Scan Test Data Setup - Phase 1: Entra ID Objects" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Load configuration from .env (same pattern as AddRemoveCrawlerPermissions.ps1)
$envPath = Join-Path $PSScriptRoot "..\..\..\.env"
if (!(Test-Path $envPath)) { throw "File '$($envPath)' not found. Run from _Sessions folder." }
$config = Read-EnvFile -Path $envPath
Write-Host "Configuration loaded from '$envPath'" -ForegroundColor Green

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

# === Check and install required modules ===
$requiredModules = @("Az.Accounts", "Az.Resources", "Microsoft.Graph.Authentication", "Microsoft.Graph.Users", "Microsoft.Graph.Groups")
$missingModules = @()

foreach ($moduleName in $requiredModules) {
    $installed = Get-Module -Name $moduleName -ListAvailable
    if ($installed) {
        Write-Host "[OK] $moduleName v$($installed[0].Version)" -ForegroundColor Green
    } else {
        Write-Host "[MISSING] $moduleName" -ForegroundColor Yellow
        $missingModules += $moduleName
    }
}

if ($missingModules.Count -gt 0) {
    Write-Host "`nAttempting to install missing modules..." -ForegroundColor Cyan
    foreach ($moduleName in $missingModules) {
        Write-Host "[INSTALLING] $moduleName..." -ForegroundColor Yellow
        try {
            Install-Module -Name $moduleName -Scope CurrentUser -Force -AllowClobber -ErrorAction Stop
            Write-Host "  Installed successfully" -ForegroundColor Green
        } catch {
            Write-Host "`nERROR: Could not install $moduleName automatically." -ForegroundColor Red
            Write-Host "Please install missing modules manually (run as Administrator):" -ForegroundColor Yellow
            Write-Host "  Install-Module $($missingModules -join ', ') -Scope CurrentUser -Force" -ForegroundColor White
            throw "Required modules missing. See above for installation instructions."
        }
    }
}

# Import modules
Import-Module Az.Accounts -ErrorAction SilentlyContinue
Import-Module Az.Resources -ErrorAction SilentlyContinue
Import-Module Microsoft.Graph.Authentication -ErrorAction SilentlyContinue
Import-Module Microsoft.Graph.Users -ErrorAction SilentlyContinue
Import-Module Microsoft.Graph.Groups -ErrorAction SilentlyContinue
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

# === Create Test Users ===
Write-Host "`n--- Creating Test Users ---" -ForegroundColor Cyan

$createdUsers = @{}

foreach ($user in $testUsers) {
    $upn = "$($user.Name)@$domain"
    
    # Check if user exists
    $existingUser = Get-MgUser -Filter "userPrincipalName eq '$upn'" -ErrorAction SilentlyContinue
    
    if ($existingUser) {
        Write-Status "User already exists: $upn" "SKIP"
        $createdUsers[$user.Name] = $existingUser.Id
    }
    else {
        try {
            $passwordProfile = @{
                Password = $testUserPassword
                ForceChangePasswordNextSignIn = $true
            }
            
            $newUser = New-MgUser -UserPrincipalName $upn `
                -DisplayName $user.DisplayName `
                -MailNickname $user.Name `
                -AccountEnabled:$true `
                -PasswordProfile $passwordProfile `
                -UsageLocation "US"
            
            Write-Status "Created user: $upn (ID: $($newUser.Id))" "OK"
            $createdUsers[$user.Name] = $newUser.Id
        }
        catch {
            Write-Status "Failed to create user $upn : $($_.Exception.Message)" "ERROR"
        }
    }
}

# === Create Security Groups ===
Write-Host "`n--- Creating Security Groups ---" -ForegroundColor Cyan

$createdGroups = @{}

foreach ($group in $securityGroups) {
    # Check if group exists
    $existingGroup = Get-MgGroup -Filter "displayName eq '$($group.DisplayName)'" -ErrorAction SilentlyContinue
    
    if ($existingGroup) {
        Write-Status "Security group already exists: $($group.DisplayName)" "SKIP"
        $createdGroups[$group.Name] = $existingGroup.Id
    }
    else {
        try {
            $newGroup = New-MgGroup -DisplayName $group.DisplayName `
                -MailEnabled:$false `
                -MailNickname $group.Name `
                -SecurityEnabled:$true `
                -Description $group.Description
            
            Write-Status "Created security group: $($group.DisplayName) (ID: $($newGroup.Id))" "OK"
            $createdGroups[$group.Name] = $newGroup.Id
            
            # Wait for group to be available
            Start-Sleep -Seconds 2
        }
        catch {
            Write-Status "Failed to create security group $($group.Name): $($_.Exception.Message)" "ERROR"
        }
    }
}

# === Add Members to Security Groups ===
Write-Host "`n--- Adding Members to Security Groups ---" -ForegroundColor Cyan

foreach ($group in $securityGroups) {
    $groupId = $createdGroups[$group.Name]
    if (-not $groupId) { 
        Write-Status "Group not found: $($group.Name)" "ERROR"
        continue 
    }
    
    # Add user members
    foreach ($memberName in $group.Members) {
        $userId = $createdUsers[$memberName]
        if (-not $userId) {
            Write-Status "User not found for membership: $memberName" "ERROR"
            continue
        }
        
        try {
            # Check if already a member
            $members = Get-MgGroupMember -GroupId $groupId -All
            if ($members.Id -contains $userId) {
                Write-Status "User $memberName already in $($group.Name)" "SKIP"
            }
            else {
                New-MgGroupMember -GroupId $groupId -DirectoryObjectId $userId
                Write-Status "Added user $memberName to $($group.Name)" "OK"
            }
        }
        catch {
            Write-Status "Failed to add $memberName to $($group.Name): $($_.Exception.Message)" "ERROR"
        }
    }
    
    # Add nested group members
    if ($group.NestedGroups) {
        foreach ($nestedGroupName in $group.NestedGroups) {
            $nestedGroupId = $createdGroups[$nestedGroupName]
            if (-not $nestedGroupId) {
                Write-Status "Nested group not found: $nestedGroupName" "ERROR"
                continue
            }
            
            try {
                $members = Get-MgGroupMember -GroupId $groupId -All
                if ($members.Id -contains $nestedGroupId) {
                    Write-Status "Group $nestedGroupName already in $($group.Name)" "SKIP"
                }
                else {
                    New-MgGroupMember -GroupId $groupId -DirectoryObjectId $nestedGroupId
                    Write-Status "Added nested group $nestedGroupName to $($group.Name)" "OK"
                }
            }
            catch {
                Write-Status "Failed to add $nestedGroupName to $($group.Name): $($_.Exception.Message)" "ERROR"
            }
        }
    }
}

# === Create M365 Group ===
Write-Host "`n--- Creating M365 Group ---" -ForegroundColor Cyan

# Check for soft-deleted M365 group (30-day retention period)
Write-Host "  Checking for soft-deleted M365 groups..." -ForegroundColor Gray
try {
    $deletedGroup = Get-MgDirectoryDeletedItemAsGroup -Filter "displayName eq '$($m365Group.DisplayName)'" -ErrorAction SilentlyContinue
    if ($deletedGroup) {
        Write-Host "  Found soft-deleted M365 group - restoring..." -ForegroundColor Yellow
        Restore-MgDirectoryDeletedItem -DirectoryObjectId $deletedGroup.Id -ErrorAction Stop
        Write-Status "Restored M365 group from soft-delete: $($m365Group.DisplayName)" "OK"
        Start-Sleep -Seconds 3  # Wait for restoration to propagate
    }
}
catch {
    Write-Host "  Could not check/restore soft-deleted groups: $($_.Exception.Message)" -ForegroundColor Yellow
}

$existingM365 = Get-MgGroup -Filter "displayName eq '$($m365Group.DisplayName)'" -ErrorAction SilentlyContinue

if ($existingM365) {
    Write-Status "M365 group already exists: $($m365Group.DisplayName)" "SKIP"
    $createdGroups[$m365Group.Name] = $existingM365.Id
}
else {
    try {
        $newM365Group = New-MgGroup -DisplayName $m365Group.DisplayName `
            -MailEnabled:$true `
            -MailNickname $m365Group.Name `
            -SecurityEnabled:$true `
            -GroupTypes @("Unified") `
            -Description $m365Group.Description
        
        Write-Status "Created M365 group: $($m365Group.DisplayName) (ID: $($newM365Group.Id))" "OK"
        $createdGroups[$m365Group.Name] = $newM365Group.Id
        
        # Wait for group to be available
        Start-Sleep -Seconds 3
        
        # Add members
        foreach ($memberName in $m365Group.Members) {
            $userId = $createdUsers[$memberName]
            if ($userId) {
                try {
                    New-MgGroupMember -GroupId $newM365Group.Id -DirectoryObjectId $userId
                    Write-Status "Added $memberName to M365 group" "OK"
                }
                catch {
                    Write-Status "Failed to add $memberName to M365 group: $($_.Exception.Message)" "ERROR"
                }
            }
        }
    }
    catch {
        Write-Status "Failed to create M365 group: $($_.Exception.Message)" "ERROR"
    }
}

# === Summary ===
Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

Write-Host "`nCreated Users:" -ForegroundColor White
foreach ($key in $createdUsers.Keys) {
    Write-Host "  - $key : $($createdUsers[$key])"
}

Write-Host "`nCreated Groups:" -ForegroundColor White
foreach ($key in $createdGroups.Keys) {
    Write-Host "  - $key : $($createdGroups[$key])"
}

Write-Host "`nGroup Nesting Structure:" -ForegroundColor White
Write-Host "  ScanTest_SecurityGroup01 (contains user3)"
Write-Host "    +-- ScanTest_SecurityGroup02 (contains user4)"
Write-Host "          +-- ScanTest_SecurityGroup03 (contains user5)"
Write-Host "  ScanTest_M365Group01 (contains user6)"

# Save created object IDs to file for cleanup script
$outputPath = Join-Path $PSScriptRoot "created_entra_objects.json"
$outputData = @{
    Users = $createdUsers
    Groups = $createdGroups
    CreatedAt = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
}
$outputData | ConvertTo-Json -Depth 3 | Out-File $outputPath -Encoding UTF8
Write-Status "`nSaved object IDs to: $outputPath" "OK"

# === Verification ===
Write-Host "`n--- Verifying Created Objects ---" -ForegroundColor Cyan

$verificationPassed = $true

# Verify users
foreach ($user in $testUsers) {
    $upn = "$($user.Name)@$domain"
    $verifyUser = Get-MgUser -Filter "userPrincipalName eq '$upn'" -ErrorAction SilentlyContinue
    if ($verifyUser) {
        Write-Status "User verified: $upn" "OK"
    }
    else {
        Write-Status "User NOT found: $upn" "FAIL"
        $verificationPassed = $false
    }
}

# Verify security groups and their members
foreach ($group in $securityGroups) {
    $verifyGroup = Get-MgGroup -Filter "displayName eq '$($group.DisplayName)'" -ErrorAction SilentlyContinue
    if ($verifyGroup) {
        $members = Get-MgGroupMember -GroupId $verifyGroup.Id -All
        $memberCount = ($members | Measure-Object).Count
        Write-Status "Security group verified: $($group.DisplayName) ($memberCount members)" "OK"
        
        # Verify expected members
        foreach ($memberName in $group.Members) {
            $userId = $createdUsers[$memberName]
            if ($members.Id -contains $userId) {
                Write-Status "  Member $memberName present" "OK"
            }
            else {
                Write-Status "  Member $memberName MISSING" "FAIL"
                $verificationPassed = $false
            }
        }
        
        # Verify nested groups
        if ($group.NestedGroups) {
            foreach ($nestedGroupName in $group.NestedGroups) {
                $nestedGroupId = $createdGroups[$nestedGroupName]
                if ($members.Id -contains $nestedGroupId) {
                    Write-Status "  Nested group $nestedGroupName present" "OK"
                }
                else {
                    Write-Status "  Nested group $nestedGroupName MISSING" "FAIL"
                    $verificationPassed = $false
                }
            }
        }
    }
    else {
        Write-Status "Security group NOT found: $($group.DisplayName)" "FAIL"
        $verificationPassed = $false
    }
}

# Verify M365 group
if ($createdGroups[$m365Group.Name]) {
    $verifyM365 = Get-MgGroup -GroupId $createdGroups[$m365Group.Name] -ErrorAction SilentlyContinue
    if ($verifyM365) {
        $members = Get-MgGroupMember -GroupId $verifyM365.Id -All
        $memberCount = ($members | Measure-Object).Count
        Write-Status "M365 group verified: $($m365Group.DisplayName) ($memberCount members)" "OK"
    }
    else {
        Write-Status "M365 group NOT found: $($m365Group.DisplayName)" "FAIL"
        $verificationPassed = $false
    }
}
else {
    Write-Status "M365 group was not created (soft-delete issue?)" "WARNING"
}

# Final verification status
Write-Host ""
if ($verificationPassed) {
    Write-Host "=== ALL VERIFICATIONS PASSED ===" -ForegroundColor Green
    Write-Host "`nPhase 1 complete. Run 02_Create_SharePoint_Permission_Cases.ps1 next." -ForegroundColor Green
}
else {
    Write-Host "=== VERIFICATION FAILED ===" -ForegroundColor Red
    Write-Host "Some objects could not be verified. Check errors above before proceeding." -ForegroundColor Yellow
}
