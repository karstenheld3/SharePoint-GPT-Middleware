# Reads an .env file and returns a hashtable of key-value pairs
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

Clear-Host

$envPath = Join-Path $PSScriptRoot  ".env"
if (!(Test-Path $envPath)) { throw "File '$($envPath)' not found." }
$config = Read-EnvFile -Path ($envPath)

# === Check for required tools ===
if (-not (Get-Module -Name Az -ListAvailable)) {
  Write-Host "Installing Az module..."
  Install-Module -Name Az -Scope CurrentUser -Force -AllowClobber
}

# Make sure Azure CLI is installed
# Check known installation paths first (more reliable than Get-Command which depends on PATH)
$azCliPaths = @(
  "${env:ProgramFiles}\Microsoft SDKs\Azure\CLI2\wbin",      # 64-bit
  "${env:ProgramFiles(x86)}\Microsoft SDKs\Azure\CLI2\wbin"  # 32-bit
)
$azCliInstalled = $false
$azCliPath = $null

foreach ($path in $azCliPaths) {
  if (Test-Path (Join-Path $path "az.cmd")) {
    $azCliInstalled = $true
    $azCliPath = $path
    break
  }
}

if ($azCliInstalled) {
  # Ensure az is in PATH for this session
  if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Host "Azure CLI found at '$azCliPath', adding to PATH..."
    $env:Path = "$azCliPath;$env:Path"
  }
  Write-Host "Azure CLI is installed."
} else {
  Write-Host "Installing Azure CLI..."
  $installerUrl = "https://aka.ms/installazurecliwindows"
  $installerPath = "$env:TEMP\AzureCLI.msi"  
  Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath
  Start-Process msiexec.exe -Wait -ArgumentList "/I $installerPath /quiet"
  Remove-Item $installerPath
  
  # Add the CLI path to current session (use 64-bit path as default)
  $newCliPath = "${env:ProgramFiles}\Microsoft SDKs\Azure\CLI2\wbin"
  if (Test-Path (Join-Path $newCliPath "az.cmd")) {
    $env:Path = "$newCliPath;$env:Path"
    Write-Host "Azure CLI installation successful"
  } else {
    Write-Error "Azure CLI installation failed. Please install manually from: $installerUrl"
    exit 1
  }
}

# === Login to Azure ===
Write-Host "Connecting to Azure..."
Clear-AzContext -Force
$subscription = Connect-AzAccount -Tenant "$($config.AZURE_TENANT_ID)" -Subscription "$($config.AZURE_SUBSCRIPTION_ID)"
if ($null -eq $subscription) { throw "ERROR: Failed to connect to Azure subscription: '$($config.AZURE_SUBSCRIPTION_ID)'" }
az account set --subscription "$($config.AZURE_SUBSCRIPTION_ID)"

# === Delete App Service ===
Write-Host "Deleting app service '$($config.AZURE_APP_SERVICE_NAME)'..."
try {
  Remove-AzWebApp -ResourceGroupName $config.AZURE_RESOURCE_GROUP -Name $config.AZURE_APP_SERVICE_NAME -Force -ErrorAction Stop
  Write-Host "Web app '$($config.AZURE_APP_SERVICE_NAME)' deleted successfully." -ForegroundColor Green
} catch {
  Write-Warning "Web app '$($config.AZURE_APP_SERVICE_NAME)' could not be deleted or does not exist. $_"
}

# === Delete App Service Plan ===
Write-Host "Deleting app service plan '$($config.AZURE_APP_SERVICE_PLAN)'..."
try {
  Remove-AzAppServicePlan -ResourceGroupName $config.AZURE_RESOURCE_GROUP -Name $config.AZURE_APP_SERVICE_PLAN -Force -ErrorAction Stop
  Write-Host "App service plan '$($config.AZURE_APP_SERVICE_PLAN)' deleted successfully." -ForegroundColor Green
} catch {
  Write-Warning "App service plan '$($config.AZURE_APP_SERVICE_PLAN)' could not be deleted or does not exist. $_"
}

Write-Host "Deletion process completed."
