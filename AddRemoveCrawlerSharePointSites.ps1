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

# Tests access to a site by attempting to retrieve all lists and libraries
# Uses certificate-based authentication to verify the crawler app has proper access
function Test-SiteAccess {
  param(
    [Parameter(Mandatory=$true)] [string]$SiteUrl,
    [Parameter(Mandatory=$true)] [string]$ClientId,
    [Parameter(Mandatory=$true)] [string]$TenantId,
    [Parameter(Mandatory=$true)] [string]$CertPath,
    [Parameter(Mandatory=$true)] [securestring]$CertPassword
  )
  
  $testResult = [PSCustomObject]@{
    success = $false
    listsCount = 0
    librariesCount = 0
    listNames = @()
    error = $null
  }
  
  try {
    # Connect using certificate-based authentication
    Connect-PnPOnline -Url $SiteUrl -ClientId $ClientId -Tenant $TenantId -CertificatePath $CertPath -CertificatePassword $CertPassword -ErrorAction Stop -WarningAction SilentlyContinue
    
    # Get all lists and libraries
    $lists = Get-PnPList -ErrorAction Stop
    
    if ($lists) {
      $libraries = $lists | Where-Object { $_.BaseTemplate -eq 101 }
      $regularLists = $lists | Where-Object { $_.BaseTemplate -ne 101 -and -not $_.Hidden }
      
      $testResult.success = $true
      $testResult.listsCount = $regularLists.Count
      $testResult.librariesCount = $libraries.Count
      $testResult.listNames = ($lists | Where-Object { -not $_.Hidden } | Select-Object -ExpandProperty Title) -join ", "
    }
    else {
      $testResult.success = $true
      $testResult.listNames = "No lists found"
    }
  }
  catch {
    $testResult.error = $_.Exception.Message
  }
  
  return $testResult
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
    # Get all site collections (without detailed properties for speed)
    Write-Host "  Retrieving site list from tenant (this may take a moment)..." -ForegroundColor Gray
    $allSites = Get-PnPTenantSite -ErrorAction Stop
    
    if ($null -eq $allSites -or $allSites.Count -eq 0) {
      Write-Host "  No sites found in tenant" -ForegroundColor Yellow
      return @()
    }
    
    Write-Host "  Found $($allSites.Count) sites in tenant, checking permissions..." -ForegroundColor Gray
    
    $checkedCount = 0
    foreach ($site in $allSites) {
      $checkedCount++
      if ($checkedCount % 10 -eq 0) {
        Write-Host "    Checked [ $checkedCount / $($allSites.Count) ] sites..." -ForegroundColor DarkGray
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
    Write-Host "    Warning: Could not retrieve sites - $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "    Error details: $($_.Exception.GetType().FullName)" -ForegroundColor DarkGray
  }
  
  return $sitesWithPermissions
}

Clear-Host

$envPath = Join-Path $PSScriptRoot ".env"
if (!(Test-Path $envPath)) { throw "File '$($envPath)' not found."  }
$config = Read-EnvFile -Path ($envPath)

# === Validate required configuration ===
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_CLIENT_ID)) { throw "CRAWLER_CLIENT_ID is required in .env file" }
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_CLIENT_NAME)) { throw "CRAWLER_CLIENT_NAME is required in .env file" }
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_TENANT_ID)) { throw "CRAWLER_TENANT_ID is required in .env file" }
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_SHAREPOINT_TENANT_NAME)) { throw "CRAWLER_SHAREPOINT_TENANT_NAME is required in .env file" }
if ([string]::IsNullOrWhiteSpace($config.PNP_CLIENT_ID)) { throw "PNP_CLIENT_ID is required in .env file" }
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_CLIENT_CERTIFICATE_PFX_FILE)) { throw "CRAWLER_CLIENT_CERTIFICATE_PFX_FILE is required in .env file" }
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_CLIENT_CERTIFICATE_PASSWORD)) { throw "CRAWLER_CLIENT_CERTIFICATE_PASSWORD is required in .env file" }

# === Validate certificate file ===
# Determine certificate path based on LOCAL_PERSISTENT_STORAGE_PATH
$certPath = if ([string]::IsNullOrWhiteSpace($config.LOCAL_PERSISTENT_STORAGE_PATH)) {
  # If LOCAL_PERSISTENT_STORAGE_PATH is not set, use script root
  Join-Path $PSScriptRoot $config.CRAWLER_CLIENT_CERTIFICATE_PFX_FILE
} else {
  # Use LOCAL_PERSISTENT_STORAGE_PATH
  Join-Path $config.LOCAL_PERSISTENT_STORAGE_PATH $config.CRAWLER_CLIENT_CERTIFICATE_PFX_FILE
}

if (-not (Test-Path $certPath)) {
  Write-Host "ERROR: Certificate file not found!" -ForegroundColor Red
  Write-Host "Expected location: $certPath" -ForegroundColor Yellow
  Write-Host ""
  Write-Host "Please ensure:" -ForegroundColor Yellow
  Write-Host "  1. CRAWLER_CLIENT_CERTIFICATE_PFX_FILE is set correctly in .env file" -ForegroundColor White
  Write-Host "  2. The certificate file exists at the specified location" -ForegroundColor White
  Write-Host "  3. LOCAL_PERSISTENT_STORAGE_PATH is set correctly (or leave empty to use script folder)" -ForegroundColor White
  throw "Certificate file not found: $certPath"
}

Write-Host "Using certificate: $certPath" -ForegroundColor Gray
$certPasswordSecure = ConvertTo-SecureString $config.CRAWLER_CLIENT_CERTIFICATE_PASSWORD -AsPlainText -Force

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

# === Test access to each site ===
if ($sitesWithPermissions.Count -gt 0) {
  Write-Host "`nTesting access to sites (using certificate authentication)..."
  
  for ($i = 0; $i -lt $sitesWithPermissions.Count; $i++) {
    $site = $sitesWithPermissions[$i]
    Write-Host "  Testing $($site.url)..." -ForegroundColor Gray
    
    # Test using certificate authentication to verify the crawler app has access
    $testResult = Test-SiteAccess -SiteUrl $site.url -ClientId $config.CRAWLER_CLIENT_ID -TenantId $config.CRAWLER_TENANT_ID -CertPath $certPath -CertPassword $certPasswordSecure
    
    # Add test results to the site object
    $sitesWithPermissions[$i] | Add-Member -MemberType NoteProperty -Name "testSuccess" -Value $testResult.success -Force
    $sitesWithPermissions[$i] | Add-Member -MemberType NoteProperty -Name "listsCount" -Value $testResult.listsCount -Force
    $sitesWithPermissions[$i] | Add-Member -MemberType NoteProperty -Name "librariesCount" -Value $testResult.librariesCount -Force
    $sitesWithPermissions[$i] | Add-Member -MemberType NoteProperty -Name "listNames" -Value $testResult.listNames -Force
    $sitesWithPermissions[$i] | Add-Member -MemberType NoteProperty -Name "testError" -Value $testResult.error -Force
    
    if ($testResult.success) {
      Write-Host "    OK: Found $($testResult.listsCount) lists, $($testResult.librariesCount) libraries" -ForegroundColor Green
    }
    else {
      Write-Host "    FAIL: $($testResult.error)" -ForegroundColor Red
    }
  }
}

Write-Host "`nCurrently configured sites:"
if ($sitesWithPermissions.Count -eq 0) {
  Write-Host "  No sites configured" -ForegroundColor Gray
}
else {
  for ($i = 0; $i -lt $sitesWithPermissions.Count; $i++) {
    $site = $sitesWithPermissions[$i]
    Write-Host "  [$($i + 1)] $($site.url)" -ForegroundColor Green
    Write-Host "      Permissions: $($site.roles)" -ForegroundColor Gray
    
    # Display test results if available
    if ($null -ne $site.testSuccess) {
      if ($site.testSuccess) {
        Write-Host "      Access Test: PASSED - $($site.listsCount) lists, $($site.librariesCount) libraries" -ForegroundColor Green
        if ($site.listNames) {
          Write-Host "      Lists/Libraries: $($site.listNames)" -ForegroundColor DarkGray
        }
      }
      else {
        Write-Host "      Access Test: FAILED - $($site.testError)" -ForegroundColor Red
      }
    }
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
  Write-Host "  Note: This grants permission for both Microsoft Graph and SharePoint REST API access" -ForegroundColor Gray
  
  try {
    # Grant permission - this automatically works for both Graph and SharePoint APIs
    # The PnP cmdlet creates the permission that works with both APIs
    Grant-PnPAzureADAppSitePermission -AppId $config.CRAWLER_CLIENT_ID -DisplayName $config.CRAWLER_CLIENT_NAME -Site $siteUrl -Permissions $role -ErrorAction Stop
    Write-Host "  OK: Permission granted successfully" -ForegroundColor Green
    Write-Host "      This permission works with both Microsoft Graph and SharePoint REST APIs" -ForegroundColor Gray
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
  
  Write-Host "Revoking permissions from both APIs..."
  
  try {
    # Reconnect to admin center with interactive auth to perform admin operations
    Connect-PnPOnline -Url $adminUrl -Interactive -ClientId $config.PNP_CLIENT_ID -ErrorAction Stop
    
    # Get all permissions for this app on this site
    $allPermissions = Get-PnPAzureADAppSitePermission -Site $siteToRemove.url -AppIdentity $config.CRAWLER_CLIENT_ID -ErrorAction SilentlyContinue
    
    if ($allPermissions) {
      $revokedCount = 0
      $failedCount = 0
      
      # Handle both single permission and array of permissions
      $permissionsArray = if ($allPermissions -is [array]) { $allPermissions } else { @($allPermissions) }
      
      Write-Host "  Found $($permissionsArray.Count) permission(s) to revoke" -ForegroundColor Gray
      
      foreach ($perm in $permissionsArray) {
        try {
          Write-Host "  Revoking permission ID: $($perm.Id)..." -ForegroundColor Gray
          Revoke-PnPAzureADAppSitePermission -PermissionId $perm.Id -Site $siteToRemove.url -Force -ErrorAction Stop
          Write-Host "    OK: Permission revoked" -ForegroundColor Green
          $revokedCount++
        }
        catch {
          Write-Host "    FAIL: Could not revoke - $($_.Exception.Message)" -ForegroundColor Red
          $failedCount++
        }
      }
      
      # Summary
      if ($revokedCount -eq $permissionsArray.Count) {
        Write-Host "`n  SUCCESS: All permissions revoked!" -ForegroundColor Green
      }
      elseif ($revokedCount -gt 0) {
        Write-Host "`n  PARTIAL: $revokedCount of $($permissionsArray.Count) permissions revoked" -ForegroundColor Yellow
      }
      else {
        Write-Host "`n  FAIL: Could not revoke any permissions" -ForegroundColor Red
      }
    }
    else {
      Write-Host "  WARNING: No permissions found for this app on this site" -ForegroundColor Yellow
    }
  }
  catch {
    Write-Host "  FAIL: Could not revoke permissions - $($_.Exception.Message)" -ForegroundColor Red
  }
}

Write-Host "`n========================================"
Write-Host "Operation completed!"
Write-Host "========================================"
