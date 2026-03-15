# Manages API permissions for both Service Principal and Managed Identity
# Supports dual-target operations: SP only, MI only, or both
# Configuration read from .env file: CRAWLER_CLIENT_ID (required), CRAWLER_MANAGED_IDENTITY_OBJECT_ID (optional)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Resource IDs
$graphResourceId        = "00000003-0000-0000-c000-000000000000"  # Microsoft Graph
$sharepointResourceId   = "00000003-0000-0ff1-ce00-000000000000"  # SharePoint

# Microsoft Graph permissions (Application)
$graphPermissions = @{
  "Group.Read.All"       = "5b567255-7703-4780-807c-7be8301ae99b"
  "GroupMember.Read.All" = "98830695-27a2-44f7-8c18-0c3ebc9698f6"
  "User.Read.All"        = "df021288-bdef-4463-88db-98f22de89214"
}

# SharePoint permissions (Application)
$sharepointPermissions = @{
  "Sites.Selected"       = "20d37865-089c-4dee-8c41-6967602d4ac8"
}

# All required permission IDs (for MI operations)
$script:allRequiredPermissions = @(
  @{ Name = "Group.Read.All"; Id = "5b567255-7703-4780-807c-7be8301ae99b"; ResourceId = $graphResourceId },
  @{ Name = "GroupMember.Read.All"; Id = "98830695-27a2-44f7-8c18-0c3ebc9698f6"; ResourceId = $graphResourceId },
  @{ Name = "User.Read.All"; Id = "df021288-bdef-4463-88db-98f22de89214"; ResourceId = $graphResourceId },
  @{ Name = "Sites.Selected"; Id = "20d37865-089c-4dee-8c41-6967602d4ac8"; ResourceId = $sharepointResourceId }
)

# ============================================================================
# FUNCTIONS
# ============================================================================

function Read-EnvFile {
  param([Parameter(Mandatory=$true)] [string]$Path)
  $envVars = @{}
  if (!(Test-Path $Path)) { throw "File '$($Path)' not found." }
  Get-Content $Path | ForEach-Object {
    if ($_ -match '^(?!#)([^=]+)=([^#]*)(?:#.*)?$') {
      $key = $matches[1].Trim(); $value = $matches[2].Trim()
      $envVars[$key] = $value
    }
  }
  return $envVars
}

# Gets current API permissions for an app registration (Service Principal)
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
    Write-Host "    Warning: Could not retrieve permissions - $($_.Exception.Message)" -ForegroundColor Yellow
  }
  return $currentPermissions
}

# Gets current app role assignments for Managed Identity
function Get-ManagedIdentityPermissions {
  param([Parameter(Mandatory=$true)] [string]$ObjectId)
  
  $assignments = @()
  try {
    $assignments = Get-MgServicePrincipalAppRoleAssignment -ServicePrincipalId $ObjectId -ErrorAction Stop
  }
  catch {
    Write-Host "    Warning: Could not retrieve MI permissions - $($_.Exception.Message)" -ForegroundColor Yellow
  }
  return $assignments
}

# Adds a permission to Managed Identity
function Add-ManagedIdentityPermission {
  param(
    [Parameter(Mandatory=$true)] [string]$ManagedIdentityObjectId,
    [Parameter(Mandatory=$true)] [string]$ResourceAppId,
    [Parameter(Mandatory=$true)] [string]$AppRoleId
  )
  
  try {
    # Get the resource service principal
    $resourceSp = Get-MgServicePrincipal -Filter "appId eq '$ResourceAppId'" -ErrorAction Stop
    if (-not $resourceSp) {
      return @{ success = $false; error = "Resource service principal not found" }
    }
    
    $params = @{
      PrincipalId = $ManagedIdentityObjectId
      ResourceId  = $resourceSp.Id
      AppRoleId   = $AppRoleId
    }
    
    New-MgServicePrincipalAppRoleAssignment -ServicePrincipalId $ManagedIdentityObjectId -BodyParameter $params -ErrorAction Stop | Out-Null
    return @{ success = $true; error = $null }
  }
  catch {
    # Check if already exists
    if ($_.Exception.Message -match "already exists") {
      return @{ success = $true; error = $null; alreadyExists = $true }
    }
    return @{ success = $false; error = $_.Exception.Message }
  }
}

# Removes a permission from Managed Identity
function Remove-ManagedIdentityPermission {
  param(
    [Parameter(Mandatory=$true)] [string]$ManagedIdentityObjectId,
    [Parameter(Mandatory=$true)] [string]$AssignmentId
  )
  
  try {
    Remove-MgServicePrincipalAppRoleAssignment -ServicePrincipalId $ManagedIdentityObjectId -AppRoleAssignmentId $AssignmentId -ErrorAction Stop
    return @{ success = $true; error = $null }
  }
  catch {
    return @{ success = $false; error = $_.Exception.Message }
  }
}

# Target selection menu (matches ARCS-SP01 pattern)
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
    Write-Host "  3 - Managed Identity only [not configured]" -ForegroundColor Gray
  }
  
  while ($true) {
    $choice = Read-Host "Enter choice (1-3, default: $DefaultChoice)"
    if ([string]::IsNullOrWhiteSpace($choice)) { $choice = $DefaultChoice }
    
    if ($choice -eq "3" -and -not $HasManagedIdentity) {
      Write-Host "  Managed Identity is not configured. Please choose 1 or 2." -ForegroundColor Yellow
      continue
    }
    if ($choice -match '^[123]$') {
      return $choice
    }
    Write-Host "  Invalid choice. Please enter 1, 2, or 3." -ForegroundColor Yellow
  }
}

# Converts target selection to array of target names
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

# Check and display permission status for both targets
function Show-PermissionStatus {
  param(
    [Parameter(Mandatory=$true)] [hashtable]$Config,
    [Parameter(Mandatory=$true)] [bool]$HasManagedIdentity
  )
  
  $status = @{
    spMissing = @()
    miMissing = @()
    spTotal = 0
    miTotal = 0
  }
  
  # Check Service Principal permissions
  Write-Host "`nService Principal:" -ForegroundColor Cyan
  $existingGraphPerms = Get-AppPermissions -ClientId $Config.CRAWLER_CLIENT_ID -ResourceId $graphResourceId
  $existingSPPerms = Get-AppPermissions -ClientId $Config.CRAWLER_CLIENT_ID -ResourceId $sharepointResourceId
  
  Write-Host "  Microsoft Graph:"
  foreach ($permName in $graphPermissions.Keys) {
    $permId = $graphPermissions[$permName]
    if ($existingGraphPerms -contains $permId) {
      Write-Host "    OK: $permName" -ForegroundColor Green
    }
    else {
      Write-Host "    MISSING: $permName" -ForegroundColor Yellow
      $status.spMissing += @{ Name = $permName; Id = $permId; ResourceId = $graphResourceId }
    }
  }
  
  Write-Host "  SharePoint:"
  foreach ($permName in $sharepointPermissions.Keys) {
    $permId = $sharepointPermissions[$permName]
    if ($existingSPPerms -contains $permId) {
      Write-Host "    OK: $permName" -ForegroundColor Green
    }
    else {
      Write-Host "    MISSING: $permName" -ForegroundColor Yellow
      $status.spMissing += @{ Name = $permName; Id = $permId; ResourceId = $sharepointResourceId }
    }
  }
  $status.spTotal = $status.spMissing.Count
  
  # Check Managed Identity permissions
  if ($HasManagedIdentity) {
    Write-Host "`nManaged Identity:" -ForegroundColor Cyan
    $miAssignments = Get-ManagedIdentityPermissions -ObjectId $Config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID
    $miPermIds = @($miAssignments | ForEach-Object { $_.AppRoleId })
    
    Write-Host "  Microsoft Graph:"
    foreach ($permName in $graphPermissions.Keys) {
      $permId = $graphPermissions[$permName]
      if ($miPermIds -contains $permId) {
        Write-Host "    OK: $permName" -ForegroundColor Green
      }
      else {
        Write-Host "    MISSING: $permName" -ForegroundColor Yellow
        $status.miMissing += @{ Name = $permName; Id = $permId; ResourceId = $graphResourceId }
      }
    }
    
    Write-Host "  SharePoint:"
    foreach ($permName in $sharepointPermissions.Keys) {
      $permId = $sharepointPermissions[$permName]
      if ($miPermIds -contains $permId) {
        Write-Host "    OK: $permName" -ForegroundColor Green
      }
      else {
        Write-Host "    MISSING: $permName" -ForegroundColor Yellow
        $status.miMissing += @{ Name = $permName; Id = $permId; ResourceId = $sharepointResourceId }
      }
    }
    $status.miTotal = $status.miMissing.Count
  }
  
  $totalMissing = $status.spTotal + $status.miTotal
  Write-Host "`nSummary: $totalMissing missing permission(s)" -ForegroundColor $(if ($totalMissing -eq 0) { "Green" } else { "Yellow" })
  
  return $status
}

# Add permissions to Service Principal
function Add-ServicePrincipalPermissions {
  param(
    [Parameter(Mandatory=$true)] [hashtable]$Config,
    [Parameter(Mandatory=$true)] [array]$MissingPermissions
  )
  
  if ($MissingPermissions.Count -eq 0) {
    Write-Host "  Service Principal: All permissions already configured" -ForegroundColor Green
    return @{ success = $true }
  }
  
  try {
    $app = Get-AzADApplication -ApplicationId $Config.CRAWLER_CLIENT_ID -ErrorAction Stop
    
    # Build complete resource access list
    $resourceAccessList = @()
    
    # Keep existing permissions from other resources
    foreach ($resource in $app.RequiredResourceAccess) {
      if ($resource.ResourceAppId -ne $graphResourceId -and $resource.ResourceAppId -ne $sharepointResourceId) {
        $resourceAccessList += $resource
      }
    }
    
    # Add all Graph permissions
    $graphResourceAccess = @()
    foreach ($permName in $graphPermissions.Keys) {
      $graphResourceAccess += @{ Id = $graphPermissions[$permName]; Type = "Role" }
    }
    $resourceAccessList += @{ ResourceAppId = $graphResourceId; ResourceAccess = $graphResourceAccess }
    
    # Add all SharePoint permissions
    $spResourceAccess = @()
    foreach ($permName in $sharepointPermissions.Keys) {
      $spResourceAccess += @{ Id = $sharepointPermissions[$permName]; Type = "Role" }
    }
    $resourceAccessList += @{ ResourceAppId = $sharepointResourceId; ResourceAccess = $spResourceAccess }
    
    # Update the application
    Update-AzADApplication -ApplicationId $Config.CRAWLER_CLIENT_ID -RequiredResourceAccess $resourceAccessList -ErrorAction Stop
    
    foreach ($perm in $MissingPermissions) {
      Write-Host "  Service Principal: Added $($perm.Name)" -ForegroundColor Green
    }
    return @{ success = $true }
  }
  catch {
    Write-Host "  Service Principal: FAIL - $($_.Exception.Message)" -ForegroundColor Red
    return @{ success = $false; error = $_.Exception.Message }
  }
}

# Add permissions to Managed Identity
function Add-ManagedIdentityPermissions {
  param(
    [Parameter(Mandatory=$true)] [hashtable]$Config,
    [Parameter(Mandatory=$true)] [array]$MissingPermissions
  )
  
  if ($MissingPermissions.Count -eq 0) {
    Write-Host "  Managed Identity: All permissions already configured" -ForegroundColor Green
    return @{ success = $true }
  }
  
  $allSuccess = $true
  foreach ($perm in $MissingPermissions) {
    $result = Add-ManagedIdentityPermission -ManagedIdentityObjectId $Config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID -ResourceAppId $perm.ResourceId -AppRoleId $perm.Id
    
    if ($result.success) {
      if ($result.alreadyExists) {
        Write-Host "  Managed Identity: $($perm.Name) already exists" -ForegroundColor Green
      }
      else {
        Write-Host "  Managed Identity: Added $($perm.Name)" -ForegroundColor Green
      }
    }
    else {
      Write-Host "  Managed Identity: FAIL $($perm.Name) - $($result.error)" -ForegroundColor Red
      $allSuccess = $false
    }
  }
  
  return @{ success = $allSuccess }
}

# Remove permissions from Service Principal
function Remove-ServicePrincipalPermissions {
  param([Parameter(Mandatory=$true)] [hashtable]$Config)
  
  try {
    $app = Get-AzADApplication -ApplicationId $Config.CRAWLER_CLIENT_ID -ErrorAction Stop
    $sp = Get-AzADServicePrincipal -ApplicationId $Config.CRAWLER_CLIENT_ID -ErrorAction SilentlyContinue
    
    # Step 1: Revoke granted permissions
    if ($sp) {
      $graphSp = Get-AzADServicePrincipal -Filter "appId eq '$graphResourceId'" -ErrorAction SilentlyContinue
      $sharepointSp = Get-AzADServicePrincipal -Filter "appId eq '$sharepointResourceId'" -ErrorAction SilentlyContinue
      $assignments = Get-AzADServicePrincipalAppRoleAssignment -ServicePrincipalId $sp.Id -ErrorAction SilentlyContinue
      
      if ($assignments) {
        foreach ($assignment in $assignments) {
          $shouldRemove = ($graphSp -and $assignment.ResourceId -eq $graphSp.Id) -or ($sharepointSp -and $assignment.ResourceId -eq $sharepointSp.Id)
          if ($shouldRemove) {
            Remove-AzADServicePrincipalAppRoleAssignment -ServicePrincipalId $sp.Id -AppRoleAssignmentId $assignment.Id -ErrorAction SilentlyContinue
          }
        }
      }
    }
    
    # Step 2: Remove from app registration
    $updatedResourceAccess = @()
    foreach ($resource in $app.RequiredResourceAccess) {
      if ($resource.ResourceAppId -ne $graphResourceId -and $resource.ResourceAppId -ne $sharepointResourceId) {
        $updatedResourceAccess += $resource
      }
    }
    
    Update-AzADApplication -ApplicationId $Config.CRAWLER_CLIENT_ID -RequiredResourceAccess $updatedResourceAccess -ErrorAction Stop
    Write-Host "  Service Principal: OK" -ForegroundColor Green
    return @{ success = $true }
  }
  catch {
    Write-Host "  Service Principal: FAIL - $($_.Exception.Message)" -ForegroundColor Red
    return @{ success = $false; error = $_.Exception.Message }
  }
}

# Remove permissions from Managed Identity
function Remove-ManagedIdentityPermissions {
  param([Parameter(Mandatory=$true)] [hashtable]$Config)
  
  try {
    $assignments = Get-MgServicePrincipalAppRoleAssignment -ServicePrincipalId $Config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID -ErrorAction Stop
    
    $graphSp = Get-MgServicePrincipal -Filter "appId eq '$graphResourceId'" -ErrorAction SilentlyContinue
    $sharepointSp = Get-MgServicePrincipal -Filter "appId eq '$sharepointResourceId'" -ErrorAction SilentlyContinue
    
    $removedCount = 0
    foreach ($assignment in $assignments) {
      $shouldRemove = ($graphSp -and $assignment.ResourceId -eq $graphSp.Id) -or ($sharepointSp -and $assignment.ResourceId -eq $sharepointSp.Id)
      if ($shouldRemove) {
        Remove-MgServicePrincipalAppRoleAssignment -ServicePrincipalId $Config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID -AppRoleAssignmentId $assignment.Id -ErrorAction SilentlyContinue
        $removedCount++
      }
    }
    
    Write-Host "  Managed Identity: OK ($removedCount removed)" -ForegroundColor Green
    return @{ success = $true }
  }
  catch {
    Write-Host "  Managed Identity: FAIL - $($_.Exception.Message)" -ForegroundColor Red
    return @{ success = $false; error = $_.Exception.Message }
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

# Validate required configuration
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_CLIENT_ID)) { throw "CRAWLER_CLIENT_ID is required in .env file" }
if ([string]::IsNullOrWhiteSpace($config.CRAWLER_TENANT_ID)) { throw "CRAWLER_TENANT_ID is required in .env file" }

# Target detection (ARCP-FR-01)
$hasManagedIdentity = -not [string]::IsNullOrWhiteSpace($config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID)
$hasBothTargets = $hasManagedIdentity

# Display header
Write-Host "========================================"
Write-Host "API Permission Management"
Write-Host "========================================"

# Check for required modules
if (-not (Get-Module -Name Az -ListAvailable)) {
  Write-Host "`nInstalling Az module..."
  Install-Module -Name Az -Scope CurrentUser -Force -AllowClobber
}
Import-Module Az.Accounts -ErrorAction SilentlyContinue
Import-Module Az.Resources -ErrorAction SilentlyContinue

# Microsoft.Graph module for MI operations
if ($hasManagedIdentity) {
  if (-not (Get-Module -Name Microsoft.Graph.Applications -ListAvailable)) {
    Write-Host "Installing Microsoft.Graph.Applications module..."
    Install-Module -Name Microsoft.Graph.Applications -Scope CurrentUser -Force -AllowClobber
  }
  Import-Module Microsoft.Graph.Applications -ErrorAction SilentlyContinue
}

# Connect to Azure
Write-Host "`nConnecting to Azure..."
Clear-AzContext -Force -ErrorAction SilentlyContinue

try {
  $null = Connect-AzAccount -Tenant "$($config.CRAWLER_TENANT_ID)" -Subscription "$($config.AZURE_SUBSCRIPTION_ID)" -WarningAction SilentlyContinue -InformationAction SilentlyContinue -ErrorAction Stop
  $context = Get-AzContext
  if ($null -eq $context) { throw "Failed to connect" }
  Write-Host "  Connected successfully to tenant: $($context.Tenant.Id)" -ForegroundColor Green
}
catch {
  throw "Failed to connect to Azure: $($_.Exception.Message)"
}

$null = Set-AzContext -Subscription "$($config.AZURE_SUBSCRIPTION_ID)"

# Look up service principal name
$spName = "UNKNOWN"
try {
  $sp = Get-AzADServicePrincipal -ApplicationId $config.CRAWLER_CLIENT_ID -ErrorAction SilentlyContinue
  if ($sp) { $spName = $sp.DisplayName }
}
catch { }
Write-Host "`nCRAWLER_CLIENT_ID: $($config.CRAWLER_CLIENT_ID) ($spName)" -ForegroundColor Cyan
if ($hasManagedIdentity) {
  Write-Host "CRAWLER_MANAGED_IDENTITY_OBJECT_ID: $($config.CRAWLER_MANAGED_IDENTITY_OBJECT_ID) ($($config.CRAWLER_MANAGED_IDENTITY_NAME))" -ForegroundColor Cyan
}

# Connect to Microsoft Graph for MI operations
if ($hasManagedIdentity) {
  Write-Host "Connecting to Microsoft Graph..."
  try {
    $null = Connect-MgGraph -TenantId $config.CRAWLER_TENANT_ID -Scopes "Application.ReadWrite.All", "AppRoleAssignment.ReadWrite.All" -NoWelcome -ErrorAction Stop
    Write-Host "  Connected to Microsoft Graph" -ForegroundColor Green
  }
  catch {
    Write-Host "  Warning: Could not connect to Microsoft Graph - MI operations may fail" -ForegroundColor Yellow
  }
}

# Main Menu Loop (ARCP-FR-04)
$exitRequested = $false

while (-not $exitRequested) {
  # Check and display permission status
  Write-Host "`n========================================"
  Write-Host "Checking current permissions..."
  $status = Show-PermissionStatus -Config $config -HasManagedIdentity $hasManagedIdentity
  
  $totalMissing = $status.spTotal + $status.miTotal
  
  # Action Menu
  Write-Host "`n========================================"
  Write-Host "Permission Management Menu"
  Write-Host "========================================"
  Write-Host "  1 - Add missing permissions ($totalMissing missing)"
  Write-Host "  2 - Remove permissions"
  Write-Host "  3 - Exit"
  Write-Host ""
  
  $choice = Read-Host "Select option [1]"
  if ([string]::IsNullOrWhiteSpace($choice)) { $choice = "1" }
  
  switch ($choice) {
    "1" {
      # Add missing permissions
      if ($totalMissing -eq 0) {
        Write-Host "`nAll permissions are already configured." -ForegroundColor Green
        continue
      }
      
      $targetChoice = Get-TargetSelection -HasBothTargets $hasBothTargets -HasManagedIdentity $hasManagedIdentity
      $targets = Get-TargetsFromSelection -Selection $targetChoice -HasManagedIdentity $hasManagedIdentity
      
      Write-Host "`nAdding permissions..."
      
      foreach ($target in $targets) {
        if ($target -eq "service_principal") {
          Add-ServicePrincipalPermissions -Config $config -MissingPermissions $status.spMissing | Out-Null
        }
        elseif ($target -eq "managed_identity") {
          Add-ManagedIdentityPermissions -Config $config -MissingPermissions $status.miMissing | Out-Null
        }
      }
      
      # Show admin consent URLs
      Write-Host "`n========================================"
      Write-Host "Admin Consent Required"
      Write-Host "========================================"
      if ($targets -contains "service_principal") {
        Write-Host "`nService Principal admin consent URL:"
        Write-Host "https://login.microsoftonline.com/$($config.CRAWLER_TENANT_ID)/adminconsent?client_id=$($config.CRAWLER_CLIENT_ID)" -ForegroundColor Cyan
      }
      if ($targets -contains "managed_identity" -and $hasManagedIdentity) {
        Write-Host "`nManaged Identity: Admin consent is granted automatically via Microsoft Graph."
        Write-Host "No manual consent URL needed for Managed Identity." -ForegroundColor Gray
      }
    }
    "2" {
      # Remove permissions
      $targetChoice = Get-TargetSelection -HasBothTargets $hasBothTargets -HasManagedIdentity $hasManagedIdentity
      $targets = Get-TargetsFromSelection -Selection $targetChoice -HasManagedIdentity $hasManagedIdentity
      
      Write-Host "`nRemoving permissions..."
      
      foreach ($target in $targets) {
        if ($target -eq "service_principal") {
          Remove-ServicePrincipalPermissions -Config $config | Out-Null
        }
        elseif ($target -eq "managed_identity") {
          Remove-ManagedIdentityPermissions -Config $config | Out-Null
        }
      }
    }
    "3" {
      $exitRequested = $true
      continue  # Skip to while condition check
    }
    default {
      Write-Host "Invalid choice. Please select 1, 2, or 3." -ForegroundColor Yellow
    }
  }
}

Write-Host "`n========================================"
Write-Host "Exiting..."
Write-Host "========================================"
