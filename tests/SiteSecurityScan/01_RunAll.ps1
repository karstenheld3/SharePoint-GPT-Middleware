# 01_RunAll.ps1
# Orchestrates the full Site Security Scan test workflow

param(
    [switch]$SkipPowerShellScan,
    [switch]$SkipV2Scan,
    [switch]$SkipComparison
)

$ErrorActionPreference = "Stop"
$scriptDir = $PSScriptRoot
$startTime = Get-Date

Write-Host ""
Write-Host "########################################################" -ForegroundColor Cyan
Write-Host "#         Site Security Scan Test Framework            #" -ForegroundColor Cyan
Write-Host "########################################################" -ForegroundColor Cyan
Write-Host ""
Write-Host "Started: $startTime"
Write-Host ""

# Step 1: Setup
Write-Host "[Step 1/4] Setting up SharePoint Permission Scanner..." -ForegroundColor White
Write-Host "-----------------------------------------------------------"
& "$scriptDir\02_SetupSharePointPermissionScanner.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Setup failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 2: Run PowerShell Scanner
if (-not $SkipPowerShellScan) {
    Write-Host "[Step 2/4] Running PowerShell Permission Scanner..." -ForegroundColor White
    Write-Host "-----------------------------------------------------------"
    Write-Host "NOTE: This requires browser authentication" -ForegroundColor Yellow
    & "$scriptDir\03_RunPowerShellScanner.ps1"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "PowerShell scanner failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[Step 2/4] SKIPPED: PowerShell Permission Scanner" -ForegroundColor Gray
}
Write-Host ""

# Step 3: Run V2 Security Scan
if (-not $SkipV2Scan) {
    Write-Host "[Step 3/4] Running V2 Security Scan API..." -ForegroundColor White
    Write-Host "-----------------------------------------------------------"
    & "$scriptDir\04_RunV2SecurityScan.ps1"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "V2 security scan failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[Step 3/4] SKIPPED: V2 Security Scan" -ForegroundColor Gray
}
Write-Host ""

# Step 4: Compare Outputs
if (-not $SkipComparison) {
    Write-Host "[Step 4/4] Comparing Outputs..." -ForegroundColor White
    Write-Host "-----------------------------------------------------------"
    & "$scriptDir\05_CompareOutputs.ps1"
    $comparisonResult = $LASTEXITCODE
} else {
    Write-Host "[Step 4/4] SKIPPED: Comparison" -ForegroundColor Gray
    $comparisonResult = 0
}
Write-Host ""

# Summary
$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host "########################################################" -ForegroundColor Cyan
Write-Host "#                    Test Complete                     #" -ForegroundColor Cyan
Write-Host "########################################################" -ForegroundColor Cyan
Write-Host ""
Write-Host "Duration: $([math]::Round($duration.TotalSeconds, 1)) seconds"
Write-Host "Finished: $endTime"
Write-Host ""

if ($comparisonResult -eq 0) {
    Write-Host "Overall Result: SUCCESS" -ForegroundColor Green
} else {
    Write-Host "Overall Result: FAILED" -ForegroundColor Red
}

exit $comparisonResult
