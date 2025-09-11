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

Clear-Host

$deployZipFilename = "deploy.zip"
$envPath = Join-Path $PSScriptRoot  ".env"
if (!(Test-Path $envPath)) { throw "File '$($envPath)' not found."  }
$config = Read-EnvFile -Path ($envPath)

$ignoreFilesAndFoldersForDeployment = @('.git', '*.bat', '*.ps1', $deployZipFilename, '.vscode', '__pycache__','.venv', '.env', 'LICENSE', '.gitignore')

# https://learn.microsoft.com/en-us/azure/app-service/configure-language-python
# "BUILD_FLAGS=UseExpressBuild" -> will use fast deployment
$appServiceSettings = @("SCM_DO_BUILD_DURING_DEPLOYMENT=1", "BUILD_FLAGS=UseExpressBuild")
# Exclude deployment variables from .env file to NOT being set in Azure App Service
$excludeVarsFromEnvFile = @( "AZURE_SUBSCRIPTION_ID", "AZURE_RESOURCE_GROUP", "AZURE_LOCATION", "AZURE_APP_SERVICE_NAME", "AZURE_PYTHON_VERSION", "AZURE_APP_SERVICE_PLAN", "LOCAL_PERSISTENT_STORAGE_PATH")
$appServiceStartupCommand = 'python -m uvicorn app:app --host 0.0.0.0 --port 8000 --workers 2 --log-level info --access-log --proxy-headers --forwarded-allow-ips=*'

### Overwrite .env variables if needed
# $config.AZURE_OPENAI_ENDPOINT = ""
# $config.AZURE_OPENAI_API_KEY = ""
# $config.AZURE_TENANT_ID = ""
# $config.AZURE_CLIENT_ID = ""
# $config.AZURE_CLIENT_SECRET = ""

# === Check for required tools ===
# Check Az PowerShell module
if (-not (Get-Module -Name Az -ListAvailable)) {
  Write-Host "Installing Az module..."
  Install-Module -Name Az -Scope CurrentUser -Force -AllowClobber
}

# Make sure Azure CLI is installed
try { $null = az --version }
catch {
  Write-Host "Installing Azure CLI..."
  $installerUrl = "https://aka.ms/installazurecliwindows"
  $installerPath = "$env:TEMP\AzureCLI.msi"  
  # Download the installer
  Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath
  # Install Azure CLI
  Start-Process msiexec.exe -Wait -ArgumentList "/I $installerPath /quiet"
  # Clean up
  Remove-Item $installerPath
  # Verify installation
  $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
  try { $null = az --version; Write-Host "Azure CLI installation successful"}
  catch {
    Write-Error "Azure CLI installation failed. Please install manually from: $installerUrl" -ForegroundColor White -BackgroundColor Red
    exit 1
  }
}

# === Login to Azure ===
Write-Host "Connecting to Azure..."
# Clear any existing contexts first
Clear-AzContext -Force

# Connect with both tenant and subscription in one command
$errorMessage = "ERROR: Failed to connect to Azure subscription '$($config.AZURE_SUBSCRIPTION_ID)'"
try {$subscription = Connect-AzAccount -Tenant "$($config.AZURE_TENANT_ID)" -Subscription "$($config.AZURE_SUBSCRIPTION_ID)"}
catch {throw "$($_.Exception.Message)"}
if ($null -eq $subscription) { throw $errorMessage }

# Set the Azure PowerShell subscription context
Set-AzContext -Subscription "$($config.AZURE_SUBSCRIPTION_ID)"

Set-Location $PSScriptRoot

# Check if app service exists
Write-Host "Checking if app service '$($config.AZURE_APP_SERVICE_NAME)' exists..."
$errorMessage = "ERROR: Web app not found '$($config.AZURE_APP_SERVICE_NAME)'"
try { $webAppCheck = Get-AzWebApp -ResourceGroupName $config.AZURE_RESOURCE_GROUP -Name $config.AZURE_APP_SERVICE_NAME }
catch {throw "$($_.Exception.Message)"}
if ($null -eq $webAppCheck) { throw $errorMessage }

Write-Host "Access the app service here:"
Write-Host "   https://$($config.AZURE_APP_SERVICE_NAME).azurewebsites.net" -ForegroundColor Cyan
Write-Host "Access the deployment tools and docker logs:"
Write-Host "   https://$($config.AZURE_APP_SERVICE_NAME).scm.azurewebsites.net" -ForegroundColor Cyan
Write-Host "   https://$($config.AZURE_APP_SERVICE_NAME).scm.azurewebsites.net/deploymentlogs/" -ForegroundColor Cyan
Write-Host "   https://$($config.AZURE_APP_SERVICE_NAME).scm.azurewebsites.net/api/logs/docker/zip" -ForegroundColor Cyan

# Stop the script if any command fails
$ErrorActionPreference = 'Stop'

# Configure the app service settings and environment variables
Write-Host "Configuring app service settings and environment variables..."

$envVarsToSet = $appServiceSettings.Clone()
# Set environment variables from .env file
Write-Host "Getting environment variables from .env file:"
foreach ($key in $config.Keys | Sort-Object) {
    if ($key -notin $excludeVarsFromEnvFile) {
        $envVarsToSet += "$key=$($config[$key])"
    }
}

if ($envVarsToSet.Count -gt 0) {
    Write-Host "Setting Azure App Service environment variables..."    
    # Convert array of "key=value" strings to hashtable for PowerShell
    $settingsHashtable = @{}
    $envVarsToSet | ForEach-Object {
        $equalIndex = $_.IndexOf('=')
        if ($equalIndex -gt 0) {
            $name = $_.Substring(0, $equalIndex)
            $value = $_.Substring($equalIndex + 1)
            $settingsHashtable[$name] = $value
        }
    }
    
    # Set the app settings using PowerShell
    $retVal = Set-AzWebAppSlot -ResourceGroupName $config.AZURE_RESOURCE_GROUP -Name $config.AZURE_APP_SERVICE_NAME -AppSettings $settingsHashtable -Slot "production"

    # Verify the settings were set
    Write-Host "Verifying environment variables in Azure App Service:"
    $currentSettings = az webapp config appsettings list `
        --name $config.AZURE_APP_SERVICE_NAME `
        --resource-group $config.AZURE_RESOURCE_GROUP | ConvertFrom-Json 
        
    # Convert $envVarsToSet into a hashtable for easier lookup
    $expectedVars = @{}
    $envVarsToSet | ForEach-Object {
        $equalIndex = $_.IndexOf('=')
        if ($equalIndex -gt 0) {
            $name = $_.Substring(0, $equalIndex)
            $value = $_.Substring($equalIndex + 1)
            $expectedVars[$name] = $value
        }
    }

    foreach ($name in $expectedVars.Keys) {
        $setting = $currentSettings | Where-Object { $_.name -eq $name }
        if ($setting) {
            if ($setting.value -eq $expectedVars[$name]) {
                Write-Host "  ✓ $name = $($setting.value)" -ForegroundColor Green
            } else {
                Write-Host "  ⚠ $name has different value. Expected: '$($expectedVars[$name])', Actual: '$($setting.value)'" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  ✗ $name is missing from Azure" -ForegroundColor Red
        }
    }
}

Write-Host "Setting startup command to '$($appServiceStartupCommand)'..."
# Get current web app configuration
$webApp = Get-AzWebApp -ResourceGroupName $config.AZURE_RESOURCE_GROUP -Name $config.AZURE_APP_SERVICE_NAME
$webApp.SiteConfig.AppCommandLine = $appServiceStartupCommand
$retVal = Set-AzWebApp -WebApp $webApp

Write-Host "Configuring logging..."
# Enable application logging using PowerShell
$retVal = Set-AzWebApp -ResourceGroupName $config.AZURE_RESOURCE_GROUP -Name $config.AZURE_APP_SERVICE_NAME -AppServicePlan $config.AZURE_APP_SERVICE_PLAN -HttpLoggingEnabled $true -RequestTracingEnabled $true

# Delete old zip file if it exists
If (Test-Path "$PSScriptRoot\$deployZipFilename") { Remove-Item "$PSScriptRoot\$deployZipFilename" -Force }

# Deploy the application using zip deploy for more reliable deployment
Write-Host "Creating deployment package..."
# Create deployment package excluding unnecessary files
$sourcePath = Join-Path $PSScriptRoot "src"
$zipPath = Join-Path $PSScriptRoot $deployZipFilename
$items = Get-ChildItem -Path $sourcePath -Exclude $ignoreFilesAndFoldersForDeployment
$rootReq = Join-Path $PSScriptRoot 'requirements.txt'
if (Test-Path $rootReq) { $items = @($items) + $rootReq }
Compress-Archive -Path $items -DestinationPath $zipPath -Force

Write-Host "Deploying application..."
# Deploy using PowerShell - Publish-AzWebApp
$retVal = Publish-AzWebApp -ResourceGroupName $config.AZURE_RESOURCE_GROUP -Name $config.AZURE_APP_SERVICE_NAME -ArchivePath $zipPath -Force

Write-Host "Deleting '$zipPath'..."
if (Test-Path "$PSScriptRoot\$deployZipFilename") { Remove-Item "$PSScriptRoot\$deployZipFilename" -Force }

# https://learn.microsoft.com/en-us/cli/azure/webapp/log?view=azure-cli-latest
# az webapp log tail --name $config.AZURE_APP_SERVICE_NAME --resource-group $config.AZURE_RESOURCE_GROUP
