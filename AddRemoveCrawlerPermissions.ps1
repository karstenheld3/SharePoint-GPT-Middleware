# CLIENT ID will be read from variable CRAWLER_CLIENT_ID in .env file in the same folder 

# === Resource IDs ===
$graphResourceId = "00000003-0000-0000-c000-000000000000"  # Microsoft Graph
$sharepointResourceId = "00000003-0000-0ff1-ce00-000000000000"  # SharePoint

# === Define required permissions ===
# Permission IDs for Microsoft Graph API (Application permissions)
$graphPermissions = @{
  "Sites.Selected"     = "883ea226-0bf2-4a8f-9f9d-92c9162a727d"  # Access selected sites
  "Group.Read.All"     = "5b567255-7703-4780-807c-7be8301ae99b"  # Read all groups
  "GroupMember.Read.All" = "98830695-27a2-44f7-8c18-0c3ebc9698f6"  # Read group memberships
  "User.Read.All"      = "df021288-bdef-4463-88db-98f22de89214"  # Read all users
}

# Permission IDs for SharePoint API (Application permissions)
$sharepointPermissions = @{
  "Sites.Selected"     = "20d37865-089c-4dee-8c41-6967602d4ac8"  # Access selected sites (required for PnP with certificate auth)
}

# Reads an .env file and returns a hashtable of key-value pairs
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

# Gets current API permissions for an app registration
function Get-AppPermissions {
  param(
    [Parameter(Mandatory=$true)] [string]$ClientId,
    [Parameter(Mandatory=$true)] [string]$ResourceId
  )
  
  $currentPermissions = @()
  
  try {
    $app = Get-AzADApplication -ApplicationId $ClientId -ErrorAction Stop
    
    foreach ($requiredResource in $app.RequiredResourceAccess) {
      if ($requiredResource.ResourceAppId -eq $ResourceId) {
        foreach ($access in $requiredResource.ResourceAccess) {
          $currentPermissions += $access.Id
        }
      }
    }
  }
  catch {
    Write-Host "    Warning: Could not retrieve permissions - $($_.Exception.Message)"
  }
  
  return $currentPermissions
}

Clear-Host

$envPath = Join-Path $PSScriptRoot ".env"
if (!(Test-Path $envPath)) { throw "File '$($envPath)' not found."  }
$config = Read-EnvFile -Path ($envPath)

# === Validate required configuration ===
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_CLIENT_ID)) { throw "CRAWLER_CLIENT_ID is required in .env file" }
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_TENANT_ID)) { throw "CRAWLER_TENANT_ID is required in .env file" }

Write-Host "Configuring permissions for App Registration: $($config.CRAWLER_CLIENT_ID)" -ForegroundColor Cyan

# === Check for required tools ===
# Check Az PowerShell module
if (-not (Get-Module -Name Az -ListAvailable)) {
  Write-Host "Installing Az module..."
  Install-Module -Name Az -Scope CurrentUser -Force -AllowClobber
}

# Import required Az modules
Import-Module Az.Accounts -ErrorAction SilentlyContinue
Import-Module Az.Resources -ErrorAction SilentlyContinue

# === Login to Azure ===
Write-Host "Connecting to Azure..."
# Clear any existing contexts first
Clear-AzContext -Force -ErrorAction SilentlyContinue

# Connect with both tenant and subscription in one command
$errorMessage = "ERROR: Failed to connect to Azure subscription '$($config.AZURE_SUBSCRIPTION_ID)'"
try {
  # Suppress all output from Connect-AzAccount
  $null = Connect-AzAccount -Tenant "$($config.CRAWLER_TENANT_ID)" -Subscription "$($config.AZURE_SUBSCRIPTION_ID)" -WarningAction SilentlyContinue -InformationAction SilentlyContinue -ErrorAction Stop
  
  # Get the context to verify connection
  $context = Get-AzContext
  if ($null -eq $context) { throw $errorMessage }
  Write-Host "  Connected successfully to tenant: $($context.Tenant.Id)" -ForegroundColor Green
}
catch {throw "$($_.Exception.Message)"}

# Set the Azure PowerShell subscription context
$null = Set-AzContext -Subscription "$($config.AZURE_SUBSCRIPTION_ID)"


# === Check existing permissions ===
Write-Host "`nChecking existing API permissions..."

# Get existing Microsoft Graph permissions
$existingGraphPermissions = Get-AppPermissions -ClientId $config.CRAWLER_CLIENT_ID -ResourceId $graphResourceId
Write-Host "  Found $($existingGraphPermissions.Count) existing Microsoft Graph permissions" -ForegroundColor Gray

# Get existing SharePoint permissions
$existingSharePointPermissions = Get-AppPermissions -ClientId $config.CRAWLER_CLIENT_ID -ResourceId $sharepointResourceId
Write-Host "  Found $($existingSharePointPermissions.Count) existing SharePoint permissions" -ForegroundColor Gray

# Display current status
Write-Host "`nMicrosoft Graph:" -ForegroundColor Cyan
$missingGraphPermissions = @()
foreach ($permissionName in $graphPermissions.Keys) {
  $permissionId = $graphPermissions[$permissionName]
  if ($existingGraphPermissions -contains $permissionId) { 
    Write-Host "  OK: $permissionName" -ForegroundColor Green 
  }
  else {
    Write-Host "  MISSING: $permissionName" -ForegroundColor Yellow
    $missingGraphPermissions += $permissionName
  }
}

Write-Host "`nSharePoint:" -ForegroundColor Cyan
$missingSharePointPermissions = @()
foreach ($permissionName in $sharepointPermissions.Keys) {
  $permissionId = $sharepointPermissions[$permissionName]
  if ($existingSharePointPermissions -contains $permissionId) { 
    Write-Host "  OK: $permissionName" -ForegroundColor Green 
  }
  else {
    Write-Host "  MISSING: $permissionName" -ForegroundColor Yellow
    $missingSharePointPermissions += $permissionName
  }
}

$totalMissing = $missingGraphPermissions.Count + $missingSharePointPermissions.Count

# === Menu ===
Write-Host "`n========================================"
Write-Host "Permission Management Menu"
Write-Host "========================================"
Write-Host "App Registration ID: $($config.CRAWLER_CLIENT_ID)"
Write-Host "Please select an option:"
Write-Host "  1 - Add missing permissions"
Write-Host "  2 - Remove all permissions"
Write-Host ""

$choice = Read-Host "Enter your choice (1 or 2)"

if ($choice -ne "1" -and $choice -ne "2") {
  Write-Host "`nInvalid choice. Exiting." -ForegroundColor Red
  exit 1
}

if ($choice -eq "2") {
  # === Remove all permissions ===
  Write-Host "Removing all Microsoft Graph and SharePoint permissions..."
  
  try {
    $app = Get-AzADApplication -ApplicationId $config.CRAWLER_CLIENT_ID -ErrorAction Stop
    $sp = Get-AzADServicePrincipal -ApplicationId $config.CRAWLER_CLIENT_ID -ErrorAction SilentlyContinue
    
    # Step 1: Remove granted permissions from the service principal
    Write-Host "  Step 1: Revoking granted permissions from service principal..." -ForegroundColor Gray
    
    $removedCount = 0
    if ($sp) {
      # Get Microsoft Graph and SharePoint service principals
      $graphSp = Get-AzADServicePrincipal -Filter "appId eq '$graphResourceId'" -ErrorAction SilentlyContinue
      $sharepointSp = Get-AzADServicePrincipal -Filter "appId eq '$sharepointResourceId'" -ErrorAction SilentlyContinue
      
      # Remove app role assignments (granted permissions)
      $assignments = Get-AzADServicePrincipalAppRoleAssignment -ServicePrincipalId $sp.Id -ErrorAction SilentlyContinue
      
      if ($assignments) {
        foreach ($assignment in $assignments) {
          if (($graphSp -and $assignment.ResourceId -eq $graphSp.Id) -or 
              ($sharepointSp -and $assignment.ResourceId -eq $sharepointSp.Id)) {
            try {
              Remove-AzADServicePrincipalAppRoleAssignment -ServicePrincipalId $sp.Id -AppRoleAssignmentId $assignment.Id -ErrorAction Stop
              Write-Host "    OK: Revoked granted permission: $($assignment.AppRoleId)" -ForegroundColor Green
              $removedCount++
            }
            catch {
              Write-Host "    WARNING: Could not revoke permission: $($_.Exception.Message)"
            }
          }
        }
      }
    }
    
    if ($removedCount -eq 0) {
      Write-Host "    No granted permissions found to revoke" -ForegroundColor Gray
    }
    
    # Step 2: Remove permissions from app registration
    Write-Host "`n  Step 2: Removing permissions from app registration..." -ForegroundColor Gray
    
    # Filter out Microsoft Graph and SharePoint permissions
    $updatedResourceAccess = @()
    $hadGraphPermissions = $false
    $hadSharePointPermissions = $false
    
    foreach ($resource in $app.RequiredResourceAccess) {
      if ($resource.ResourceAppId -eq $graphResourceId) {
        $hadGraphPermissions = $true
      }
      elseif ($resource.ResourceAppId -eq $sharepointResourceId) {
        $hadSharePointPermissions = $true
      }
      else {
        $updatedResourceAccess += $resource
      }
    }
    
    if ($hadGraphPermissions -or $hadSharePointPermissions) {
      # Update the app with filtered permissions
      Update-AzADApplication -ApplicationId $config.CRAWLER_CLIENT_ID -RequiredResourceAccess $updatedResourceAccess -ErrorAction Stop
      if ($hadGraphPermissions) {
        Write-Host "    OK: Removed all Microsoft Graph permissions from app registration" -ForegroundColor Green
      }
      if ($hadSharePointPermissions) {
        Write-Host "    OK: Removed all SharePoint permissions from app registration" -ForegroundColor Green
      }
    }
    else {
      Write-Host "    No permissions found in app registration" -ForegroundColor Gray
    }
    
    # Verify removal
    Write-Host "`nVerifying removal..."
    $remainingGraphPermissions = Get-AppPermissions -ClientId $config.CRAWLER_CLIENT_ID -ResourceId $graphResourceId
    $remainingSharePointPermissions = Get-AppPermissions -ClientId $config.CRAWLER_CLIENT_ID -ResourceId $sharepointResourceId
    
    # Also check for remaining granted permissions
    $remainingGranted = 0
    if ($sp) {
      $assignments = Get-AzADServicePrincipalAppRoleAssignment -ServicePrincipalId $sp.Id -ErrorAction SilentlyContinue
      foreach ($assignment in $assignments) {
        if (($graphSp -and $assignment.ResourceId -eq $graphSp.Id) -or 
            ($sharepointSp -and $assignment.ResourceId -eq $sharepointSp.Id)) {
          $remainingGranted++
        }
      }
    }
    
    if ($remainingGraphPermissions.Count -eq 0 -and $remainingSharePointPermissions.Count -eq 0 -and $remainingGranted -eq 0) {
      Write-Host "  OK: All permissions successfully removed!" -ForegroundColor Green
    }
    else {
      Write-Host "  WARNING: Some permissions may still remain"
      Write-Host "    Microsoft Graph permissions: $($remainingGraphPermissions.Count)" -ForegroundColor Gray
      Write-Host "    SharePoint permissions: $($remainingSharePointPermissions.Count)" -ForegroundColor Gray
      Write-Host "    Granted permissions: $remainingGranted" -ForegroundColor Gray
    }
  }
  catch {
    Write-Host "    FAIL: Failed to remove permissions" -ForegroundColor white -BackgroundColor Red
    Write-Host "    Details: $($_.Exception.Message)" -ForegroundColor DarkGray
  }
  
  Write-Host "`nPermission removal completed." -ForegroundColor Cyan
  exit 0
}

# === Add missing permissions (choice 1) ===
if ($totalMissing -eq 0) {
  Write-Host "`nAll required permissions are already configured." -ForegroundColor Green
}
else {
  Write-Host "`nAdding $totalMissing missing permission(s)..."
  
  # === Add missing permissions to the app registration ===
  try {
    $app = Get-AzADApplication -ApplicationId $config.CRAWLER_CLIENT_ID -ErrorAction Stop
    
    # Build the resource access list
    $resourceAccessList = @()
    
    # Keep existing permissions from other resources (not Graph or SharePoint)
    foreach ($resource in $app.RequiredResourceAccess) {
      if ($resource.ResourceAppId -ne $graphResourceId -and $resource.ResourceAppId -ne $sharepointResourceId) {
        $resourceAccessList += $resource
      }
    }
    
    # Add all required Microsoft Graph permissions
    $graphResourceAccess = @()
    foreach ($permissionName in $graphPermissions.Keys) {
      $permissionId = $graphPermissions[$permissionName]
      $graphResourceAccess += @{
        Id = $permissionId
        Type = "Role"  # Application permission
      }
    }
    
    # Create the Microsoft Graph resource access object
    $resourceAccessList += @{
      ResourceAppId = $graphResourceId
      ResourceAccess = $graphResourceAccess
    }
    
    # Add all required SharePoint permissions
    $sharepointResourceAccess = @()
    foreach ($permissionName in $sharepointPermissions.Keys) {
      $permissionId = $sharepointPermissions[$permissionName]
      $sharepointResourceAccess += @{
        Id = $permissionId
        Type = "Role"  # Application permission
      }
    }
    
    # Create the SharePoint resource access object
    $resourceAccessList += @{
      ResourceAppId = $sharepointResourceId
      ResourceAccess = $sharepointResourceAccess
    }
    
    # Update the application
    Update-AzADApplication -ApplicationId $config.CRAWLER_CLIENT_ID -RequiredResourceAccess $resourceAccessList -ErrorAction Stop
    
    foreach ($permissionName in $missingGraphPermissions) {
      Write-Host "    OK: Added Microsoft Graph $permissionName" -ForegroundColor Green
    }
    foreach ($permissionName in $missingSharePointPermissions) {
      Write-Host "    OK: Added SharePoint $permissionName" -ForegroundColor Green
    }
  }
  catch {
    Write-Host "    FAIL: Failed to add permissions" -ForegroundColor white -BackgroundColor Red
    Write-Host "    Details: $($_.Exception.Message)" -ForegroundColor DarkGray
  }
  
  # === Verify permissions were added ===
  Write-Host "`nVerifying permissions..."
  
  $currentGraphPermissions = Get-AppPermissions -ClientId $config.CRAWLER_CLIENT_ID -ResourceId $graphResourceId
  $currentSharePointPermissions = Get-AppPermissions -ClientId $config.CRAWLER_CLIENT_ID -ResourceId $sharepointResourceId
  $allPermissionsSet = $true
  
  Write-Host "`nMicrosoft Graph:" -ForegroundColor Cyan
  foreach ($permissionName in $graphPermissions.Keys) {
    $permissionId = $graphPermissions[$permissionName]
    if ($currentGraphPermissions -contains $permissionId) {
      Write-Host "  OK: $permissionName is configured" -ForegroundColor Green
    }
    else {
      Write-Host "  FAIL: $permissionName is MISSING" -ForegroundColor White -BackgroundColor Red
      $allPermissionsSet = $false
    }
  }
  
  Write-Host "`nSharePoint:" -ForegroundColor Cyan
  foreach ($permissionName in $sharepointPermissions.Keys) {
    $permissionId = $sharepointPermissions[$permissionName]
    if ($currentSharePointPermissions -contains $permissionId) {
      Write-Host "  OK: $permissionName is configured" -ForegroundColor Green
    }
    else {
      Write-Host "  FAIL: $permissionName is MISSING" -ForegroundColor White -BackgroundColor Red
      $allPermissionsSet = $false
    }
  }
  
  if (-not $allPermissionsSet) {
    Write-Host "`nERROR: Not all permissions were successfully added!" -ForegroundColor White -BackgroundColor Red
  }
  else {
    Write-Host "`nAll permissions successfully configured!" -ForegroundColor Green
  }
}

# === Grant admin consent ===
# You need to use the consent URL or Azure Portal
Write-Host "`nNOTE: Admin consent must be granted manually. Admin consent URL:"
Write-Host "https://login.microsoftonline.com/$($config.CRAWLER_TENANT_ID)/adminconsent?client_id=$($config.CRAWLER_CLIENT_ID)" -ForegroundColor Cyan
Write-Host "`nPlease open this URL in your browser to grant admin consent."

# === Output Results ===
Write-Host "`n========================================"
Write-Host "Permission configuration completed!"
Write-Host "========================================"
Write-Host "`nApp Registration ID: $($config.CRAWLER_CLIENT_ID)"
Write-Host "Tenant ID: $($config.CRAWLER_TENANT_ID)"
Write-Host "`nConfigured Permissions:"
Write-Host "`nMicrosoft Graph:" -ForegroundColor Cyan
foreach ($permissionName in $graphPermissions.Keys) {
  Write-Host "  - $permissionName" -ForegroundColor Green
}
Write-Host "`nSharePoint:" -ForegroundColor Cyan
foreach ($permissionName in $sharepointPermissions.Keys) {
  Write-Host "  - $permissionName" -ForegroundColor Green
}

Write-Host "`nTo view the app registration in Azure Portal:"
Write-Host "https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Overview/appId/$($config.CRAWLER_CLIENT_ID)" -ForegroundColor Cyan

# Prevent any buffered output from displaying
[System.Console]::Out.Flush()