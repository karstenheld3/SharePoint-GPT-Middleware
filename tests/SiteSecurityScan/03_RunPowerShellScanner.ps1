# 03_RunPowerShellScanner.ps1
# Runs SharePointPermissionScanner - output stays in SharePointPermissionScanner folder
# REQUIRES: PowerShell 7+ (pwsh) - PnP.PowerShell module is installed there

# Check if running in PowerShell 7+
if ($PSVersionTable.PSVersion.Major -lt 7) {
    Write-Host "ERROR: This script requires PowerShell 7+ (pwsh). Current version: $($PSVersionTable.PSVersion)" -ForegroundColor Red
    Write-Host "Run with: pwsh -ExecutionPolicy Bypass -File `"$($MyInvocation.MyCommand.Path)`"" -ForegroundColor Yellow
    exit 1
}

$ErrorActionPreference = "Stop"
$scriptDir = $PSScriptRoot

Write-Host "=== Run PowerShell Permission Scanner ===" -ForegroundColor Cyan

$scannerDir = Join-Path $scriptDir "SharePointPermissionScanner"
$scannerScript = Join-Path $scannerDir "SharePointPermissionScanner.ps1"

# Check if input file exists
$inputFile = Join-Path $scannerDir "SharePointPermissionScanner-In.csv"
if (-not (Test-Path $inputFile)) {
    Write-Host "ERROR: Input file not found. Run 02_SetupSharePointPermissionScanner.ps1 first." -ForegroundColor Red
    exit 1
}

# Clean old output CSV files
Get-ChildItem -Path $scannerDir -Filter "*.csv" | Where-Object { $_.Name -ne "SharePointPermissionScanner-In.csv" } | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "  Running scanner (this requires browser authentication)..."
Write-Host ""

# Run the scanner
Push-Location $scannerDir
try {
    & $scannerScript
} finally {
    Pop-Location
}

Write-Host ""

# Verify output files
$csvFiles = @("01_SiteContents.csv", "02_SiteGroups.csv", "03_SiteUsers.csv", "04_IndividualPermissionItems.csv", "05_IndividualPermissionItemAccess.csv")
$foundCount = 0
foreach ($file in $csvFiles) {
    if (Test-Path (Join-Path $scannerDir $file)) {
        $foundCount++
        Write-Host "  Created: $file" -ForegroundColor Green
    } else {
        Write-Host "  Missing: $file" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== PowerShell Scanner Complete ($foundCount files) ===" -ForegroundColor Cyan
