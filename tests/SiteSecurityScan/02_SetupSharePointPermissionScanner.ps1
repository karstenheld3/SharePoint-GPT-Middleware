# 02_SetupSharePointPermissionScanner.ps1
# Reads .env file from workspace root and creates SharePointPermissionScanner-In.csv

param(
    [string]$SiteUrl = ""
)

$ErrorActionPreference = "Stop"
$scriptDir = $PSScriptRoot
$workspaceRoot = (Resolve-Path "$scriptDir\..\..").Path

Write-Host "=== Setup SharePoint Permission Scanner ===" -ForegroundColor Cyan

# Read .env file
$envFile = Join-Path $workspaceRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "ERROR: .env file not found at $envFile" -ForegroundColor Red
    exit 1
}

# Parse .env file for CRAWLER_SELFTEST_SHAREPOINT_SITE if no SiteUrl provided
if ([string]::IsNullOrEmpty($SiteUrl)) {
    $envContent = Get-Content $envFile
    foreach ($line in $envContent) {
        if ($line -match "^CRAWLER_SELFTEST_SHAREPOINT_SITE=(.+)$") {
            $SiteUrl = $matches[1].Trim()
            break
        }
    }
}

if ([string]::IsNullOrEmpty($SiteUrl)) {
    Write-Host "ERROR: No SiteUrl provided and CRAWLER_SELFTEST_SHAREPOINT_SITE not found in .env" -ForegroundColor Red
    exit 1
}

Write-Host "  Site URL: $SiteUrl"

# Create input CSV for SharePointPermissionScanner
$inputCsvPath = Join-Path $scriptDir "SharePointPermissionScanner\SharePointPermissionScanner-In.csv"
$csvContent = "Url`n$SiteUrl"
Set-Content -Path $inputCsvPath -Value $csvContent -Encoding UTF8

Write-Host "  Created: $inputCsvPath" -ForegroundColor Green
Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
exit 0
