# 05_CompareOutputs.ps1
# Compares PowerShell Scanner output with V2 Security Scan output

$ErrorActionPreference = "Stop"
$scriptDir = $PSScriptRoot

Write-Host "=== Compare Scan Outputs ===" -ForegroundColor Cyan

$psOutputDir = Join-Path $scriptDir "SharePointPermissionScanner"
$v2OutputDir = Join-Path $scriptDir "SiteSecurityScanOutput"

# Check directories exist
if (-not (Test-Path $psOutputDir)) {
    Write-Host "ERROR: SharePointPermissionScanner directory not found." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $v2OutputDir)) {
    Write-Host "ERROR: SiteSecurityScanOutput directory not found. Run 04_RunV2SecurityScan.ps1 first." -ForegroundColor Red
    exit 1
}

$results = @{
    Passed = 0
    Failed = 0
    Warnings = 0
    Details = @()
}

# Compare function for CSV files
function Compare-CsvFiles {
    param(
        [string]$File1Path,
        [string]$File2Path,
        [string]$FileName,
        [string]$KeyColumn,
        [string[]]$CompareColumns
    )
    
    $result = @{
        FileName = $FileName
        Status = "UNKNOWN"
        Message = ""
        Details = @()
    }
    
    $file1Exists = Test-Path $File1Path
    $file2Exists = Test-Path $File2Path
    
    if (-not $file1Exists -and -not $file2Exists) {
        $result.Status = "SKIP"
        $result.Message = "Both files missing"
        return $result
    }
    
    if (-not $file1Exists) {
        $result.Status = "FAIL"
        $result.Message = "PowerShell output missing"
        return $result
    }
    
    if (-not $file2Exists) {
        $result.Status = "FAIL"
        $result.Message = "V2 output missing"
        return $result
    }
    
    # Read CSV files
    $csv1 = Import-Csv -Path $File1Path
    $csv2 = Import-Csv -Path $File2Path
    
    $result.Details += "  PowerShell rows: $($csv1.Count)"
    $result.Details += "  V2 rows: $($csv2.Count)"
    
    if ($csv1.Count -ne $csv2.Count) {
        $result.Status = "WARN"
        $result.Message = "Row count differs (PS: $($csv1.Count), V2: $($csv2.Count))"
    } else {
        $result.Status = "PASS"
        $result.Message = "Row counts match ($($csv1.Count))"
    }
    
    return $result
}

# Helper function for order-independent URL comparison (normalizes URLs to relative paths)
function Get-NormalizedUrl {
    param([string]$Url)
    if ($Url -match "sharepoint\.com(.+)$") { return $matches[1] } else { return $Url }
}

# Compare 04_IndividualPermissionItems.csv (most important for permission scanning)
Write-Host ""
Write-Host "Comparing 04_IndividualPermissionItems.csv..." -ForegroundColor White

$psFile = Join-Path $psOutputDir "04_IndividualPermissionItems.csv"
$v2File = Join-Path $v2OutputDir "04_IndividualPermissionItems.csv"

if ((Test-Path $psFile) -and (Test-Path $v2File)) {
    $psCsv = Import-Csv -Path $psFile
    $v2Csv = Import-Csv -Path $v2File
    
    # Extract unique URLs from both (normalize to relative paths, order-independent)
    $psUrls = $psCsv | ForEach-Object { Get-NormalizedUrl $_.Url } | Sort-Object -Unique
    $v2Urls = $v2Csv | ForEach-Object { Get-NormalizedUrl $_.Url } | Sort-Object -Unique
    
    Write-Host "  PowerShell items with broken permissions: $($psCsv.Count)" -ForegroundColor Gray
    Write-Host "  V2 items with broken permissions: $($v2Csv.Count)" -ForegroundColor Gray
    
    # Order-independent comparison using sets
    $onlyInPs = $psUrls | Where-Object { $_ -notin $v2Urls }
    $onlyInV2 = $v2Urls | Where-Object { $_ -notin $psUrls }
    $common = $psUrls | Where-Object { $_ -in $v2Urls }
    
    Write-Host "  Common items: $($common.Count)" -ForegroundColor Green
    
    if ($onlyInPs.Count -gt 0) {
        Write-Host "  Only in PowerShell ($($onlyInPs.Count)):" -ForegroundColor Yellow
        $onlyInPs | Select-Object -First 10 | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
        if ($onlyInPs.Count -gt 10) { Write-Host "    ... and $($onlyInPs.Count - 10) more" -ForegroundColor Yellow }
        $results.Warnings++
    }
    
    if ($onlyInV2.Count -gt 0) {
        Write-Host "  Only in V2 ($($onlyInV2.Count)):" -ForegroundColor Yellow
        $onlyInV2 | Select-Object -First 10 | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
        if ($onlyInV2.Count -gt 10) { Write-Host "    ... and $($onlyInV2.Count - 10) more" -ForegroundColor Yellow }
        $results.Warnings++
    }
    
    if ($onlyInPs.Count -eq 0 -and $onlyInV2.Count -eq 0) {
        Write-Host "  PASS: All items match (order-independent)" -ForegroundColor Green
        $results.Passed++
    } else {
        Write-Host "  WARN: Differences found" -ForegroundColor Yellow
    }
} else {
    Write-Host "  SKIP: One or both files missing" -ForegroundColor Gray
}

# Compare other files (order-independent content comparison)
# Define key columns for each file type to enable set-based comparison
$fileCompareConfig = @{
    "01_SiteContents.csv" = "Url"
    "02_SiteGroups.csv" = "Title"
    "03_SiteUsers.csv" = "LoginName"
    "05_IndividualPermissionItemAccess.csv" = "Url"
}

foreach ($fileName in $fileCompareConfig.Keys) {
    Write-Host ""
    Write-Host "Comparing $fileName..." -ForegroundColor White
    
    $psFilePath = Join-Path $psOutputDir $fileName
    $v2FilePath = Join-Path $v2OutputDir $fileName
    $keyColumn = $fileCompareConfig[$fileName]
    
    $psExists = Test-Path $psFilePath
    $v2Exists = Test-Path $v2FilePath
    
    if ($psExists -and $v2Exists) {
        $psCsv = Import-Csv -Path $psFilePath
        $v2Csv = Import-Csv -Path $v2FilePath
        
        Write-Host "  PowerShell rows: $($psCsv.Count)" -ForegroundColor Gray
        Write-Host "  V2 rows: $($v2Csv.Count)" -ForegroundColor Gray
        
        # Order-independent comparison using key column
        $psKeys = $psCsv | ForEach-Object { Get-NormalizedUrl $_.$keyColumn } | Sort-Object -Unique
        $v2Keys = $v2Csv | ForEach-Object { Get-NormalizedUrl $_.$keyColumn } | Sort-Object -Unique
        
        $onlyInPs = $psKeys | Where-Object { $_ -notin $v2Keys }
        $onlyInV2 = $v2Keys | Where-Object { $_ -notin $psKeys }
        
        if ($onlyInPs.Count -eq 0 -and $onlyInV2.Count -eq 0) {
            Write-Host "  PASS: All items match (order-independent)" -ForegroundColor Green
            $results.Passed++
        } else {
            if ($onlyInPs.Count -gt 0) {
                Write-Host "  Only in PowerShell ($($onlyInPs.Count)):" -ForegroundColor Yellow
                $onlyInPs | Select-Object -First 5 | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
            }
            if ($onlyInV2.Count -gt 0) {
                Write-Host "  Only in V2 ($($onlyInV2.Count)):" -ForegroundColor Yellow
                $onlyInV2 | Select-Object -First 5 | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
            }
            Write-Host "  WARN: Differences found" -ForegroundColor Yellow
            $results.Warnings++
        }
    } elseif (-not $psExists -and -not $v2Exists) {
        Write-Host "  SKIP: Both files missing" -ForegroundColor Gray
    } else {
        Write-Host "  FAIL: One file missing (PS: $psExists, V2: $v2Exists)" -ForegroundColor Red
        $results.Failed++
    }
}

# Summary
Write-Host ""
Write-Host "=== Comparison Summary ===" -ForegroundColor Cyan
Write-Host "  Passed:   $($results.Passed)" -ForegroundColor Green
Write-Host "  Warnings: $($results.Warnings)" -ForegroundColor Yellow
Write-Host "  Failed:   $($results.Failed)" -ForegroundColor Red

if ($results.Failed -gt 0) {
    Write-Host ""
    Write-Host "RESULT: FAILED" -ForegroundColor Red
    exit 1
} elseif ($results.Warnings -gt 0) {
    Write-Host ""
    Write-Host "RESULT: PASSED WITH WARNINGS" -ForegroundColor Yellow
    exit 0
} else {
    Write-Host ""
    Write-Host "RESULT: PASSED" -ForegroundColor Green
    exit 0
}
