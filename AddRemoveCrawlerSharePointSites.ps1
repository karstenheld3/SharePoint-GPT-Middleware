# Manages SharePoint site permissions for the crawler app using Sites.Selected permission
# CLIENT ID will be read from variable CRAWLER_CLIENT_ID in .env file in the same folder 

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

# Gets permissions for a specific site using PnP
function Get-SitePermissionsForApp {
  param(
    [Parameter(Mandatory=$true)] [string]$SiteUrl,
    [Parameter(Mandatory=$true)] [string]$ClientId
  )
  
  try {
    # Use -AppIdentity to get specific app permissions with roles populated
    $permissions = Get-PnPAzureADAppSitePermission -Site $SiteUrl -AppIdentity $ClientId -ErrorAction SilentlyContinue
    
    return $permissions
  }
  catch {
    return @()
  }
}

# Discovers all sites that have granted permissions to the app
function Get-SitesWithAppPermissions {
  param(
    [Parameter(Mandatory=$true)] [string]$ClientId,
    [Parameter(Mandatory=$true)] [string]$AdminUrl
  )
  
  Write-Host "  Scanning SharePoint sites for app permissions..." -ForegroundColor Gray
  
  $sitesWithPermissions = @()
  
  try {
    # Get all site collections
    $allSites = Get-PnPTenantSite -ErrorAction Stop
    
    Write-Host "  Found $($allSites.Count) sites in tenant, checking permissions..." -ForegroundColor Gray
    
    $checkedCount = 0
    foreach ($site in $allSites) {
      $checkedCount++
      if ($checkedCount % 10 -eq 0) {
        Write-Host "    Checked $checkedCount/$($allSites.Count) sites..." -ForegroundColor DarkGray
      }
      
      $permissions = Get-SitePermissionsForApp -SiteUrl $site.Url -ClientId $ClientId
      
      if ($null -ne $permissions) {
        # Check if permissions is an array or single object
        $permObj = if ($permissions -is [array]) { $permissions[0] } else { $permissions }
        
        if ($permObj -and $permObj.Id) {
          # Debug: Show what we found
          Write-Host "    Found permission at $($site.Url): ID=$($permObj.Id), Roles=$($permObj.Roles)" -ForegroundColor DarkGray
          
          $rolesStr = if ($permObj.Roles) { $permObj.Roles -join ", " } else { "Unknown" }
          
          $sitesWithPermissions += [PSCustomObject]@{
            url = $site.Url
            title = $site.Title
            roles = $rolesStr
            permissionId = $permObj.Id
          }
        }
      }
    }
  }
  catch {
    Write-Host "    Warning: Could not retrieve sites - $($_.Exception.Message)"
  }
  
  return $sitesWithPermissions
}

Clear-Host

$envPath = Join-Path $PSScriptRoot ".env"
if (!(Test-Path $envPath)) { throw "File '$($envPath)' not found."  }
$config = Read-EnvFile -Path ($envPath)

# === Validate required configuration ===
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_CLIENT_ID)) { throw "CRAWLER_CLIENT_ID is required in .env file" }
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_TENANT_ID)) { throw "CRAWLER_TENANT_ID is required in .env file" }
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_SHAREPOINT_TENANT_NAME)) { throw "CRAWLER_SHAREPOINT_TENANT_NAME is required in .env file" }
if ([string]::IsNullOrWhiteSpace($config.PNP_CLIENT_ID)) { throw "PNP_CLIENT_ID is required in .env file" }

Write-Host "Managing SharePoint site permissions for App: $($config.CRAWLER_CLIENT_ID)" -ForegroundColor Cyan

# === Check for required tools ===
# Check PnP PowerShell module
if (-not (Get-Module -Name PnP.PowerShell -ListAvailable)) {
  Write-Host "Installing PnP.PowerShell module..."
  Install-Module -Name PnP.PowerShell -Scope CurrentUser -Force -AllowClobber
}

# Import PnP PowerShell
Import-Module PnP.PowerShell -ErrorAction SilentlyContinue

# === Connect to SharePoint Admin ===
$adminUrl = "https://$($config.CRAWLER_SHAREPOINT_TENANT_NAME)-admin.sharepoint.com"

Write-Host "`nConnecting to SharePoint Online..."
Write-Host "Admin URL: $adminUrl" -ForegroundColor Gray
Write-Host "A browser window will open for authentication" -ForegroundColor Gray

try {
  # Use Interactive login with PnP Management Shell app
  Connect-PnPOnline -Url $adminUrl -Interactive -ClientId $config.PNP_CLIENT_ID -ErrorAction Stop
  Write-Host "  Connected successfully to SharePoint Admin" -ForegroundColor Green
}
catch {
  throw "Failed to connect to SharePoint Admin: $($_.Exception.Message)"
}

# === Discover sites with app permissions ===
Write-Host "`nDiscovering sites with app permissions..."
$sitesWithPermissions = Get-SitesWithAppPermissions -ClientId $config.CRAWLER_CLIENT_ID -AdminUrl $adminUrl

Write-Host "`nCurrently configured sites:"
if ($sitesWithPermissions.Count -eq 0) {
  Write-Host "  No sites configured" -ForegroundColor Gray
}
else {
  for ($i = 0; $i -lt $sitesWithPermissions.Count; $i++) {
    $site = $sitesWithPermissions[$i]
    Write-Host "  [$($i + 1)] $($site.url) - Permissions: $($site.roles)" -ForegroundColor Green
  }
}

# === Menu ===
Write-Host "`n========================================"
Write-Host "SharePoint Site Permission Management"
Write-Host "========================================"
Write-Host "App Registration ID: $($config.CRAWLER_CLIENT_ID)"
Write-Host "Please select an option:"
Write-Host "  1 - Add new site to Sites.Selected"

# Dynamically add remove options for each site
for ($i = 0; $i -lt $sitesWithPermissions.Count; $i++) {
  $site = $sitesWithPermissions[$i]
  Write-Host "  $($i + 2) - Remove site: $($site.url)"
}

Write-Host ""
$maxChoice = $sitesWithPermissions.Count + 1
$choice = Read-Host "Enter your choice (1-$maxChoice)"

# Validate choice
if (-not ($choice -match '^\d+$') -or [int]$choice -lt 1 -or [int]$choice -gt $maxChoice) {
  Write-Host "`nInvalid choice. Exiting." -ForegroundColor Red
  exit 1
}

$choiceNum = [int]$choice

if ($choiceNum -eq 1) {
  # === Add new site ===
  Write-Host "`nAdd new SharePoint site"
  Write-Host "========================================"
  
  $siteUrl = Read-Host "Enter the SharePoint site URL (e.g., https://contoso.sharepoint.com/sites/sitename)"
  
  if ([string]::IsNullOrWhiteSpace($siteUrl)) {
    Write-Host "Site URL cannot be empty. Exiting." -ForegroundColor Red
    exit 1
  }
  
  # Ask for permission level
  Write-Host "`nSelect permission level:"
  Write-Host "  1 - Read (default)"
  Write-Host "  2 - Write"
  Write-Host "  3 - Full Control"
  $permChoice = Read-Host "Enter your choice (1-3, default: 1)"
  
  $role = "read"
  switch ($permChoice) {
    "2" { $role = "write" }
    "3" { $role = "fullcontrol" }
    default { $role = "read" }
  }
  
  Write-Host "`nGranting $role permission to site..."
  
  try {
    Grant-PnPAzureADAppSitePermission -AppId $config.CRAWLER_CLIENT_ID -DisplayName "Crawler App" -Site $siteUrl -Permissions $role -ErrorAction Stop
    Write-Host "  OK: Permission granted successfully" -ForegroundColor Green
  }
  catch {
    Write-Host "  FAIL: Failed to grant permission - $($_.Exception.Message)" -ForegroundColor White -BackgroundColor Red
  }
}
else {
  # === Remove site ===
  $siteIndex = $choiceNum - 2
  $siteToRemove = $sitesWithPermissions[$siteIndex]
  
  Write-Host "`nRemoving site: $($siteToRemove.url)"
  Write-Host "========================================"
  
  Write-Host "Revoking permission..."
  
  try {
    Revoke-PnPAzureADAppSitePermission -PermissionId $siteToRemove.permissionId -Site $siteToRemove.url -Force -ErrorAction Stop
    Write-Host "  OK: Permission revoked successfully" -ForegroundColor Green
  }
  catch {
    Write-Host "  WARNING: Could not revoke permission - $($_.Exception.Message)"
  }
}

Write-Host "`n========================================"
Write-Host "Operation completed!"
Write-Host "========================================"
