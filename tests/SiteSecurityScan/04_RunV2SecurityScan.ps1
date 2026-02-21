# 04_RunV2SecurityScan.ps1
# Checks if local server is running, starts it if needed, calls V2 security scan API, and extracts report

param(
    [string]$SiteUrl = "",
    [string]$ServerUrl = "http://127.0.0.1:8000",
    [int]$StartupWaitSeconds = 10
)

$ErrorActionPreference = "Stop"
$scriptDir = $PSScriptRoot
$workspaceRoot = (Resolve-Path "$scriptDir\..\..").Path

Write-Host "=== Run V2 Security Scan ===" -ForegroundColor Cyan

# Read site URL from .env if not provided
if ([string]::IsNullOrEmpty($SiteUrl)) {
    $envFile = Join-Path $workspaceRoot ".env"
    if (Test-Path $envFile) {
        $envContent = Get-Content $envFile
        foreach ($line in $envContent) {
            if ($line -match "^CRAWLER_SELFTEST_SHAREPOINT_SITE=(.+)$") {
                $SiteUrl = $matches[1].Trim()
                break
            }
        }
    }
}

if ([string]::IsNullOrEmpty($SiteUrl)) {
    Write-Host "ERROR: No SiteUrl provided and CRAWLER_SELFTEST_SHAREPOINT_SITE not found in .env" -ForegroundColor Red
    exit 1
}

# Extract site ID from URL (last segment)
$siteId = $SiteUrl.Split("/")[-1]
Write-Host "  Site URL: $SiteUrl"
Write-Host "  Site ID: $siteId"

# Check if server is running (try root endpoint or docs)
function Test-ServerRunning {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -Uri "$Url/docs" -Method GET -TimeoutSec 5 -ErrorAction Stop
        return $response.StatusCode -eq 200
    } catch {
        # Try root as fallback
        try {
            $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 5 -ErrorAction Stop
            return $true
        } catch {
            return $false
        }
    }
}

$serverRunning = Test-ServerRunning -Url $ServerUrl
if (-not $serverRunning) {
    Write-Host "  Server not running. Starting uvicorn..." -ForegroundColor Yellow
    
    # Start the server in background
    $venvPython = Join-Path $workspaceRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        Write-Host "ERROR: Python venv not found at $venvPython" -ForegroundColor Red
        exit 1
    }
    
    $startInfo = @{
        FilePath = $venvPython
        ArgumentList = "-m", "uvicorn", "app:app", "--app-dir", "src", "--host", "127.0.0.1", "--port", "8000"
        WorkingDirectory = $workspaceRoot
        WindowStyle = "Minimized"
    }
    
    Start-Process @startInfo
    
    Write-Host "  Waiting $StartupWaitSeconds seconds for server to start..."
    Start-Sleep -Seconds $StartupWaitSeconds
    
    $serverRunning = Test-ServerRunning -Url $ServerUrl
    if (-not $serverRunning) {
        Write-Host "ERROR: Server failed to start" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Server started successfully" -ForegroundColor Green
    $script:ServerWasStarted = $true
} else {
    Write-Host "  Server already running" -ForegroundColor Green
    $script:ServerWasStarted = $false
}

# Call security scan API (uses SSE streaming with format=stream)
Write-Host ""
Write-Host "  Calling security scan API..."
$apiUrl = "$ServerUrl/v2/sites/security_scan?site_id=$siteId&scope=all&include_subsites=true&format=stream"
Write-Host "  URL: $apiUrl"

try {
    # Use streaming request - the API returns SSE events
    $response = Invoke-WebRequest -Uri $apiUrl -Method GET -TimeoutSec 600 -ErrorAction Stop
    
    if ($response.StatusCode -ne 200) {
        Write-Host "ERROR: API returned status $($response.StatusCode)" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "  Scan completed successfully" -ForegroundColor Green
    
} catch {
    Write-Host "ERROR: API call failed - $_" -ForegroundColor Red
    exit 1
}

# Find the latest report ZIP file
Write-Host ""
Write-Host "  Finding latest report..."

$reportsDir = Join-Path $workspaceRoot ".localstorage\AzureOpenAiProject\reports\site_scans"

# Get most recent ZIP file containing the site ID
$latestZip = Get-ChildItem -Path $reportsDir -File -Filter "*.zip" | 
    Where-Object { $_.Name -like "*$siteId*" } |
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 1

if ($null -eq $latestZip) {
    Write-Host "ERROR: No report ZIP found for site $siteId" -ForegroundColor Red
    exit 1
}

Write-Host "  Found: $($latestZip.Name)"

# Extract to output folder
$outputDir = Join-Path $scriptDir "SiteSecurityScanOutput"

# Ensure output directory exists
if (-not (Test-Path $outputDir)) {
    New-Item -Path $outputDir -ItemType Directory | Out-Null
}

# Remove only CSV and JSON files from output directory (preserve directory structure)
Get-ChildItem -Path $outputDir -File | Where-Object { $_.Extension -in ".csv",".json" } | Remove-Item -Force

Write-Host "  Extracting to: $outputDir"
Expand-Archive -LiteralPath $latestZip.FullName -DestinationPath $outputDir -Force

$extractedFiles = Get-ChildItem -Path $outputDir -File | Where-Object { $_.Extension -in ".csv",".json" }
Write-Host "  Extracted $($extractedFiles.Count) files" -ForegroundColor Green

Write-Host ""
Write-Host "=== V2 Security Scan Complete ===" -ForegroundColor Cyan
