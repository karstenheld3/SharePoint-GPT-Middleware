# Manages SharePoint site permissions for the crawler app using Sites.Selected permission
# Supports both Service Principal (Certificate App) and Managed Identity targets
# Configuration read from .env file: CRAWLER_CLIENT_ID (required), CRAWLER_MANAGED_IDENTITY_OBJECT_ID (optional)

# ============================================================================
# FUNCTIONS
# ============================================================================

# Reads an .env file and returns a hashtable of key-value pairs
function Read-EnvFile {
  param([Parameter(Mandatory=$true)] [string]$Path)
  $envVars = @{}
  if (!(Test-Path $Path)) { throw "File '$($Path)' not found." }
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

# Gets permissions for a specific site and app identity using PnP
function Get-SitePermissionsForApp {
  param(
    [Parameter(Mandatory=$true)] [string]$SiteUrl,
    [Parameter(Mandatory=$true)] [string]$AppId
  )

  try {
    # Use -AppIdentity to get specific app permissions with roles populated
    $permissions = Get-PnPAzureADAppSitePermission -Site $SiteUrl -AppIdentity $AppId -ErrorAction SilentlyContinue
    return $permissions
  }
  catch {
    return $null
  }
}

# Tests access to a site by attempting to retrieve all lists and libraries
# Uses certificate-based authentication (MI access test not possible from script)
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
    Connect-PnPOnline -Url $SiteUrl -ClientId $ClientId -Tenant $TenantId -CertificatePath $CertPath -CertificatePassword $CertPassword -ErrorAction Stop -WarningAction SilentlyContinue
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

# Discovers all sites with permissions for a given app identity
# Returns array of objects: url, title, roles, permissionId
function Get-SitesWithAppPermissions {
  param(
    [Parameter(Mandatory=$true)] [string]$AppId,
    [Parameter(Mandatory=$true)] [string]$AdminUrl
  )

  $sitesWithPermissions = @()

  try {
    $allSites = Get-PnPTenantSite -ErrorAction Stop

    if ($null -eq $allSites -or $allSites.Count -eq 0) {
      return @()
    }

    $total = $allSites.Count
    $checkedCount = 0
    foreach ($site in $allSites) {
      $checkedCount++
      if ($checkedCount % 10 -eq 0) {
        Write-Host "    ( $checkedCount / $total ) Checking sites..." -ForegroundColor DarkGray
      }

      $permissions = Get-SitePermissionsForApp -SiteUrl $site.Url -AppId $AppId

      if ($null -ne $permissions) {
        $permObj = if ($permissions -is [array]) { $permissions[0] } else { $permissions }

        if ($permObj -and $permObj.Id) {
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
    
    # List all discovered sites explicitly
    $foundCount = $sitesWithPermissions.Count
    if ($foundCount -gt 0) {
      foreach ($site in $sitesWithPermissions) {
        Write-Host "      '$($site.url)' role='$($site.roles)'" -ForegroundColor Gray
      }
      Write-Host "    $foundCount sites with permissions." -ForegroundColor Gray
    } else {
      Write-Host "    0 sites with permissions." -ForegroundColor Gray
    }
  }
  catch {
    Write-Host "    WARNING: Could not retrieve sites -> $($_.Exception.Message)" -ForegroundColor Yellow
  }

  return $sitesWithPermissions
}

# Merges discovery results from both targets into a unified site list
# Returns array of SitePermissionStatus objects with per-target roles and permission IDs
function Get-MergedSitePermissions {
  param(
    [Parameter(Mandatory=$true)] [string]$CertificateAppId,
    [string]$ManagedIdentityObjectId,
    [Parameter(Mandatory=$true)] [string]$AdminUrl
  )

  Write-Host "  Scanning Service Principal..." -ForegroundColor Gray
  $certSites = Get-SitesWithAppPermissions -AppId $CertificateAppId -AdminUrl $AdminUrl

  $miSites = @()
  if (-not [string]::IsNullOrWhiteSpace($ManagedIdentityObjectId)) {
    Write-Host "  Scanning Managed Identity..." -ForegroundColor Gray
    $miSites = Get-SitesWithAppPermissions -AppId $ManagedIdentityObjectId -AdminUrl $AdminUrl
  }

  # Build lookup by URL
  $merged = @{}

  foreach ($site in $certSites) {
    $merged[$site.url] = [PSCustomObject]@{
      url = $site.url
      title = $site.title
      certificateAppRoles = $site.roles
      managedIdentityRoles = $null
      certificateAppPermissionId = $site.permissionId
      managedIdentityPermissionId = $null
      testSuccess = $null
      listsCount = 0
      librariesCount = 0
      listNames = $null
      testError = $null
    }
  }

  foreach ($site in $miSites) {
    if ($merged.ContainsKey($site.url)) {
      $merged[$site.url].managedIdentityRoles = $site.roles
      $merged[$site.url].managedIdentityPermissionId = $site.permissionId
    }
    else {
      $merged[$site.url] = [PSCustomObject]@{
        url = $site.url
        title = $site.title
        certificateAppRoles = $null
        managedIdentityRoles = $site.roles
        certificateAppPermissionId = $null
        managedIdentityPermissionId = $site.permissionId
        testSuccess = $null
        listsCount = 0
        librariesCount = 0
        listNames = $null
        testError = $null
      }
    }
  }

  return @($merged.Values | Sort-Object url)
}

# Displays the target selection menu and returns the choice string ("1", "2", or "3")
# ARCS-IG-04: Menu numbering is always 1=Both, 2=Service Principal, 3=MI
function Get-TargetSelection {
  param(
    [Parameter(Mandatory=$true)] [bool]$HasBothTargets,
    [Parameter(Mandatory=$true)] [bool]$HasManagedIdentity,
    [string]$DefaultChoice = "1"
  )

  Write-Host "`nSelect target:"
  if ($HasBothTargets) {
    Write-Host "  1 - Both: Service Principal + Managed Identity (default)"
  }
  else {
    Write-Host "  1 - Service Principal (default)"
  }
  Write-Host "  2 - Service Principal only"
  if ($HasManagedIdentity) {
    Write-Host "  3 - Managed Identity only"
  }
  else {
    Write-Host "  3 - Managed Identity only [not configured]"
  }

  while ($true) {
    $choice = Read-Host "Enter choice (1-3, default: $DefaultChoice)"
    if ([string]::IsNullOrWhiteSpace($choice)) { $choice = $DefaultChoice }

    if ($choice -eq "3" -and -not $HasManagedIdentity) {
      Write-Host "  Managed Identity not configured. Choose 1 or 2." -ForegroundColor Yellow
      continue
    }
    if ($choice -match '^[123]$') {
      return $choice
    }
    Write-Host "  Invalid. Enter 1, 2, or 3." -ForegroundColor Yellow
  }
}

# Converts a target selection choice to an array of target names
function Get-TargetsFromSelection {
  param(
    [Parameter(Mandatory=$true)] [string]$Selection,
    [Parameter(Mandatory=$true)] [bool]$HasManagedIdentity
  )

  switch ($Selection) {
    "1" {
      if ($HasManagedIdentity) { return @("service_principal", "managed_identity") }
      else { return @("service_principal") }
    }
    "2" { return @("service_principal") }
    "3" { return @("managed_identity") }
    default { return @("service_principal") }
  }
}

# Grants site permission to one or more targets, returns per-target results
function Grant-SitePermissionToTargets {
  param(
    [Parameter(Mandatory=$true)] [string]$SiteUrl,
    [Parameter(Mandatory=$true)] [string]$Role,
    [Parameter(Mandatory=$true)] [string[]]$Targets,
    [Parameter(Mandatory=$true)] [hashtable]$Config,
    [Parameter(Mandatory=$true)] [string]$AdminUrl
  )

  $results = @{}

  foreach ($target in $Targets) {
    $appId = if ($target -eq "service_principal") { $Config.CRAWLER_CLIENT_ID } else { $Config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID }
    $displayName = if ($target -eq "service_principal") { $Config.CRAWLER_CLIENT_NAME } else { "Managed Identity" }
    $targetLabel = if ($target -eq "service_principal") { "Service Principal" } else { "Managed Identity" }

    try {
      # Method 1: Grant via admin site with -Site parameter
      Grant-PnPAzureADAppSitePermission -AppId $appId -DisplayName $displayName -Site $SiteUrl -Permissions $Role -ErrorAction Stop
      Write-Host "  ${targetLabel}: OK" -ForegroundColor Green
      $results[$target] = @{ success = $true; error = $null }
    }
    catch {
      $errorMsg = $_.Exception.Message

      # Check if this is an access denied error (common for group-connected sites)
      if ($errorMsg -match "accessDenied|Access denied") {
        Write-Host "  ${targetLabel}: Access denied via admin. Trying direct site connection..." -ForegroundColor Yellow

        try {
          # Method 2: Connect directly to target site and retry
          Connect-PnPOnline -Url $SiteUrl -Interactive -ClientId $Config.PNP_CLIENT_ID -ErrorAction Stop
          Grant-PnPAzureADAppSitePermission -AppId $appId -DisplayName $displayName -Permissions $Role -ErrorAction Stop
          Write-Host "  ${targetLabel}: OK (via direct site connection)" -ForegroundColor Green
          $results[$target] = @{ success = $true; error = $null }

          # Reconnect to admin site for subsequent operations
          Connect-PnPOnline -Url $AdminUrl -Interactive -ClientId $Config.PNP_CLIENT_ID -ErrorAction SilentlyContinue
        }
        catch {
          Write-Host "  ${targetLabel}: FAIL - $($_.Exception.Message)" -ForegroundColor Red
          $results[$target] = @{ success = $false; error = $_.Exception.Message }
        }
      }
      else {
        Write-Host "  ${targetLabel}: FAIL - $errorMsg" -ForegroundColor Red
        $results[$target] = @{ success = $false; error = $errorMsg }
      }
    }
  }

  return $results
}

# Revokes site permissions from one or more targets, returns per-target results
function Revoke-SitePermissionFromTargets {
  param(
    [Parameter(Mandatory=$true)] [string]$SiteUrl,
    [Parameter(Mandatory=$true)] [string[]]$Targets,
    [Parameter(Mandatory=$true)] [PSCustomObject]$SitePermissionStatus,
    [Parameter(Mandatory=$true)] [hashtable]$Config,
    [Parameter(Mandatory=$true)] [string]$AdminUrl
  )

  $results = @{}

  foreach ($target in $Targets) {
    $targetLabel = if ($target -eq "service_principal") { "Service Principal" } else { "Managed Identity" }
    $permissionId = if ($target -eq "service_principal") { $SitePermissionStatus.certificateAppPermissionId } else { $SitePermissionStatus.managedIdentityPermissionId }

    if ($null -eq $permissionId) {
      Write-Host "  ${targetLabel}: SKIP (no permission found)" -ForegroundColor Gray
      $results[$target] = @{ success = $true; error = $null; skipped = $true }
      continue
    }

    try {
      Revoke-PnPAzureADAppSitePermission -PermissionId $permissionId -Site $SiteUrl -Force -ErrorAction Stop
      Write-Host "  ${targetLabel}: OK" -ForegroundColor Green
      $results[$target] = @{ success = $true; error = $null }
    }
    catch {
      Write-Host "  ${targetLabel}: FAIL - $($_.Exception.Message)" -ForegroundColor Red
      $results[$target] = @{ success = $false; error = $_.Exception.Message }
    }
  }

  return $results
}

# Displays operation result summary with explicit target status (LOG-SC-06, LOG-SC-07)
function Show-OperationSummary {
  param(
    [Parameter(Mandatory=$true)] $Results
  )

  $succeeded = @()
  $skipped = @()
  $failed = @()

  foreach ($key in $Results.Keys) {
    $targetLabel = switch ($key) {
      "service_principal" { "Service Principal" }
      "managed_identity" { "Managed Identity" }
      default { "Unknown target: '$key'" }
    }
    
    if ($Results[$key].skipped) {
      $skipped += $targetLabel
    }
    elseif ($Results[$key].success) {
      $succeeded += $targetLabel
    }
    else {
      $failed += @{ label = $targetLabel; error = $Results[$key].error }
    }
  }

  # Show per-target results
  foreach ($s in $succeeded) {
    Write-Host "  $s`: OK." -ForegroundColor Green
  }
  foreach ($s in $skipped) {
    Write-Host "  $s`: SKIP: No permission to remove." -ForegroundColor Gray
  }
  foreach ($f in $failed) {
    Write-Host "  $($f.label): FAIL: $($f.error)" -ForegroundColor Red
  }
}

# ============================================================================
# MAIN SCRIPT
# ============================================================================

Clear-Host

# Workspace root is parent of scripts/ folder
$workspaceRoot = Split-Path $PSScriptRoot -Parent
$envPath = Join-Path $workspaceRoot ".env"
if (!(Test-Path $envPath)) { throw "File '$($envPath)' not found." }
$config = Read-EnvFile -Path ($envPath)

# === Validate required configuration ===
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_CLIENT_ID)) { throw "CRAWLER_CLIENT_ID is required in .env file" }
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_CLIENT_NAME)) { throw "CRAWLER_CLIENT_NAME is required in .env file" }
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_TENANT_ID)) { throw "CRAWLER_TENANT_ID is required in .env file" }
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_SHAREPOINT_TENANT_NAME)) { throw "CRAWLER_SHAREPOINT_TENANT_NAME is required in .env file" }
if ([string]::IsNullOrWhiteSpace($config.PNP_CLIENT_ID)) { throw "PNP_CLIENT_ID is required in .env file" }
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_CLIENT_CERTIFICATE_PFX_FILE)) { throw "CRAWLER_CLIENT_CERTIFICATE_PFX_FILE is required in .env file" }
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_CLIENT_CERTIFICATE_PASSWORD)) { throw "CRAWLER_CLIENT_CERTIFICATE_PASSWORD is required in .env file" }

# === Target detection (ARCS-FR-01) ===
$hasCertificateApp = -not [string]::IsNullOrWhiteSpace($config.CRAWLER_CLIENT_ID)
$hasManagedIdentity = -not [string]::IsNullOrWhiteSpace($config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID)
$hasBothTargets = $hasCertificateApp -and $hasManagedIdentity

# === Validate certificate file ===
$certPath = if ([string]::IsNullOrWhiteSpace($config.LOCAL_PERSISTENT_STORAGE_PATH)) {
  Join-Path $workspaceRoot $config.CRAWLER_CLIENT_CERTIFICATE_PFX_FILE
} else {
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

$certPasswordSecure = ConvertTo-SecureString $config.CRAWLER_CLIENT_CERTIFICATE_PASSWORD -AsPlainText -Force

# === Display configuration summary (ARCS-FR-01) ===
Write-Host "Managing SharePoint site permissions" -ForegroundColor Cyan
Write-Host "CRAWLER_CLIENT_ID: $($config.CRAWLER_CLIENT_ID) ($($config.CRAWLER_CLIENT_NAME))" -ForegroundColor Cyan
if ($hasManagedIdentity) {
  Write-Host "CRAWLER_MANAGED_IDENTITY_OBJECT_ID: $($config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID) ($($config.CRAWLER_MANAGED_IDENTITY_NAME))" -ForegroundColor Cyan
}
else {
  Write-Host "CRAWLER_MANAGED_IDENTITY_OBJECT_ID: not configured" -ForegroundColor Gray
}
Write-Host "Certificate: $certPath" -ForegroundColor Gray

# === Check for required tools ===
if (-not (Get-Module -Name PnP.PowerShell -ListAvailable)) {
  Write-Host "Installing PnP.PowerShell module..."
  Install-Module -Name PnP.PowerShell -Scope CurrentUser -Force -AllowClobber
}
Import-Module PnP.PowerShell -ErrorAction SilentlyContinue

# === Connect to SharePoint Admin ===
$adminUrl = "https://$($config.CRAWLER_SHAREPOINT_TENANT_NAME)-admin.sharepoint.com"

Write-Host "`nConnecting to $adminUrl..."

try {
  Connect-PnPOnline -Url $adminUrl -Interactive -ClientId $config.PNP_CLIENT_ID -ErrorAction Stop
  Write-Host "  Connected" -ForegroundColor Green
}
catch {
  throw "Failed to connect to SharePoint Admin: $($_.Exception.Message)"
}

# === Main Menu Loop (ARCS-FR-03) ===
$exitRequested = $false
$mergedSites = @()

while (-not $exitRequested) {
  # === Discovery phase (ARCS-FR-02) ===
  Write-Host "`n========================================"
  Write-Host "Site Discovery"
  Write-Host "  1 - Scan for existing sites in Sites.Selected"
  Write-Host "  2 - Skip (proceed directly to add new site)"
  $scanChoice = Read-Host "Select option [1]"
  if ([string]::IsNullOrWhiteSpace($scanChoice)) { $scanChoice = "1" }

  $mergedSites = @()
  $skipScan = ($scanChoice -eq "2")

  if (-not $skipScan) {
    Write-Host "`nDiscovering sites..."
    $mergedSites = Get-MergedSitePermissions -CertificateAppId $config.CRAWLER_CLIENT_ID -ManagedIdentityObjectId $config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID -AdminUrl $adminUrl

    # === Test access to each site (ARCS-FR-07) ===
    if ($mergedSites.Count -gt 0) {
      Write-Host "`nTesting Service Principal access..."

      for ($i = 0; $i -lt $mergedSites.Count; $i++) {
        $site = $mergedSites[$i]

        # Only test if certificate app has permissions on this site
        if ($null -ne $site.certificateAppRoles) {
          Write-Host "  $($site.url)" -ForegroundColor Gray
          $testResult = Test-SiteAccess -SiteUrl $site.url -ClientId $config.CRAWLER_CLIENT_ID -TenantId $config.CRAWLER_TENANT_ID -CertPath $certPath -CertPassword $certPasswordSecure

          $mergedSites[$i].testSuccess = $testResult.success
          $mergedSites[$i].listsCount = $testResult.listsCount
          $mergedSites[$i].librariesCount = $testResult.librariesCount
          $mergedSites[$i].listNames = $testResult.listNames
          $mergedSites[$i].testError = $testResult.error

          if ($testResult.success) {
            Write-Host "    OK ($($testResult.listsCount) lists, $($testResult.librariesCount) libs)" -ForegroundColor Green
          }
          else {
            Write-Host "    FAIL: $($testResult.error)" -ForegroundColor Red
          }
        }
        else {
          Write-Host "  Skipping $($site.url) (no Service Principal permission)" -ForegroundColor DarkGray
        }
      }
    }

    # === Display site list with side-by-side status ===
    Write-Host "`nCurrently configured sites:"
    if ($mergedSites.Count -eq 0) {
      Write-Host "  No sites configured" -ForegroundColor Gray
    }
    else {
      for ($i = 0; $i -lt $mergedSites.Count; $i++) {
        $site = $mergedSites[$i]
        Write-Host "  [$($i + 1)] $($site.url)" -ForegroundColor Green

        # Side-by-side permission status
        $certRoles = if ($null -ne $site.certificateAppRoles) { $site.certificateAppRoles } else { "(none)" }
        $miRoles = if ($null -ne $site.managedIdentityRoles) { $site.managedIdentityRoles } else { "(none)" }
        Write-Host "      Service Principal: $certRoles | Managed Identity: $miRoles" -ForegroundColor Gray

        # Access test results
        if ($null -ne $site.testSuccess) {
          if ($site.testSuccess) {
            Write-Host "      Test: OK ($($site.listsCount) lists, $($site.librariesCount) libs)" -ForegroundColor Green
            if ($site.listNames) {
              Write-Host "      Lists/Libraries: $($site.listNames)" -ForegroundColor DarkGray
            }
          }
          else {
            Write-Host "      Test: FAIL - $($site.testError)" -ForegroundColor Red
          }
        }
        elseif ($null -eq $site.certificateAppRoles) {
          Write-Host "      Test: N/A (no Service Principal permission)" -ForegroundColor DarkGray
        }
      }
    }
  }

  # === Action Menu ===
  Write-Host "`nPlease select an option:"
  Write-Host "  1 - Add new site"

  for ($i = 0; $i -lt $mergedSites.Count; $i++) {
    Write-Host "  $($i + 2) - Remove: $($mergedSites[$i].url)"
  }

  $exitOption = $mergedSites.Count + 2
  Write-Host "  $exitOption - Exit"

  Write-Host ""
  $maxChoice = $exitOption
  $choice = Read-Host "Enter your choice (1-$maxChoice)"

  if (-not ($choice -match '^\d+$') -or [int]$choice -lt 1 -or [int]$choice -gt $maxChoice) {
    Write-Host "`nInvalid choice. Please try again." -ForegroundColor Yellow
    continue
  }

  $choiceNum = [int]$choice

  if ($choiceNum -eq $exitOption) {
    $exitRequested = $true
    continue
  }

  if ($choiceNum -eq 1) {
  # === Add new site (ARCS-FR-04) ===
  Write-Host "`nAdd new SharePoint site"
  Write-Host "========================================"

  $siteUrl = Read-Host "Enter the SharePoint site URL (e.g., https://contoso.sharepoint.com/sites/sitename)"

  if ([string]::IsNullOrWhiteSpace($siteUrl)) {
    Write-Host "Site URL cannot be empty." -ForegroundColor Yellow
    continue
  }

  # Permission level selection
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

  # Target selection
  $targetChoice = Get-TargetSelection -HasBothTargets $hasBothTargets -HasManagedIdentity $hasManagedIdentity
  $targets = Get-TargetsFromSelection -Selection $targetChoice -HasManagedIdentity $hasManagedIdentity

  Write-Host "`nGranting $role permission..."

  # Reconnect to admin (Test-SiteAccess may have changed connection)
  Connect-PnPOnline -Url $adminUrl -Interactive -ClientId $config.PNP_CLIENT_ID -ErrorAction Stop

  $null = Grant-SitePermissionToTargets -SiteUrl $siteUrl -Role $role -Targets $targets -Config $config -AdminUrl $adminUrl
}
else {
  # === Remove site (ARCS-FR-05) ===
  $siteIndex = $choiceNum - 2
  $siteToRemove = $mergedSites[$siteIndex]

  Write-Host "`nRemoving site: $($siteToRemove.url)"
  Write-Host "========================================"

  # Display current permissions for this site
  Write-Host "Current permissions:"
  $certRoles = if ($null -ne $siteToRemove.certificateAppRoles) { $siteToRemove.certificateAppRoles } else { "(none)" }
  $miRoles = if ($null -ne $siteToRemove.managedIdentityRoles) { $siteToRemove.managedIdentityRoles } else { "(none)" }
  Write-Host "  Service Principal: $certRoles" -ForegroundColor Gray
  Write-Host "  Managed Identity: $miRoles" -ForegroundColor Gray

  # Target selection
  $targetChoice = Get-TargetSelection -HasBothTargets $hasBothTargets -HasManagedIdentity $hasManagedIdentity
  $targets = Get-TargetsFromSelection -Selection $targetChoice -HasManagedIdentity $hasManagedIdentity

  Write-Host "`nRevoking permissions..."

  # Reconnect to admin (Test-SiteAccess may have changed connection)
  Connect-PnPOnline -Url $adminUrl -Interactive -ClientId $config.PNP_CLIENT_ID -ErrorAction Stop

  $null = Revoke-SitePermissionFromTargets -SiteUrl $siteToRemove.url -Targets $targets -SitePermissionStatus $siteToRemove -Config $config -AdminUrl $adminUrl
}
} # End of while loop

Write-Host "`n========================================"
Write-Host "Exiting..."
Write-Host "========================================"
