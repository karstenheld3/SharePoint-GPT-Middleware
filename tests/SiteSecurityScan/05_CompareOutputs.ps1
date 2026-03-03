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
}

# Special detailed comparison for 05_IndividualPermissionItemAccess.csv
Write-Host ""
Write-Host "Comparing 05_IndividualPermissionItemAccess.csv (DETAILED)..." -ForegroundColor White

$psFile05 = Join-Path $psOutputDir "05_IndividualPermissionItemAccess.csv"
$v2File05 = Join-Path $v2OutputDir "05_IndividualPermissionItemAccess.csv"

if ((Test-Path $psFile05) -and (Test-Path $v2File05)) {
    $psCsv05 = Import-Csv -Path $psFile05
    $v2Csv05 = Import-Csv -Path $v2File05
    
    Write-Host "  PowerShell rows: $($psCsv05.Count)" -ForegroundColor Gray
    Write-Host "  V2 rows: $($v2Csv05.Count)" -ForegroundColor Gray
    
    # Analyze structure differences
    Write-Host ""
    Write-Host "  === Structure Analysis ===" -ForegroundColor Cyan
    
    # Check LoginName patterns - are they user emails or group names?
    $psLoginNames = $psCsv05 | ForEach-Object { $_.LoginName } | Sort-Object -Unique
    $v2LoginNames = $v2Csv05 | ForEach-Object { $_.LoginName } | Sort-Object -Unique
    
    $psUserEmails = $psLoginNames | Where-Object { $_ -match "@" }
    $psGroupNames = $psLoginNames | Where-Object { $_ -notmatch "@" -and $_ -ne "" }
    $v2UserEmails = $v2LoginNames | Where-Object { $_ -match "@" }
    $v2GroupNames = $v2LoginNames | Where-Object { $_ -notmatch "@" -and $_ -ne "" }
    
    Write-Host "  PowerShell LoginName patterns:" -ForegroundColor White
    Write-Host "    User emails (@): $($psUserEmails.Count)" -ForegroundColor Gray
    Write-Host "    Group names:     $($psGroupNames.Count)" -ForegroundColor Gray
    if ($psUserEmails.Count -gt 0) {
        Write-Host "    Sample emails:   $($psUserEmails | Select-Object -First 3 | Join-String -Separator ', ')" -ForegroundColor Gray
    }
    if ($psGroupNames.Count -gt 0) {
        Write-Host "    Sample groups:   $($psGroupNames | Select-Object -First 3 | Join-String -Separator ', ')" -ForegroundColor Gray
    }
    
    Write-Host "  V2 LoginName patterns:" -ForegroundColor White
    Write-Host "    User emails (@): $($v2UserEmails.Count)" -ForegroundColor Gray
    Write-Host "    Group names:     $($v2GroupNames.Count)" -ForegroundColor Gray
    if ($v2UserEmails.Count -gt 0) {
        Write-Host "    Sample emails:   $($v2UserEmails | Select-Object -First 3 | Join-String -Separator ', ')" -ForegroundColor Gray
    }
    if ($v2GroupNames.Count -gt 0) {
        Write-Host "    Sample groups:   $($v2GroupNames | Select-Object -First 3 | Join-String -Separator ', ')" -ForegroundColor Gray
    }
    
    # Check NestingLevel distribution
    Write-Host ""
    Write-Host "  NestingLevel distribution:" -ForegroundColor White
    $psNesting = $psCsv05 | Group-Object -Property NestingLevel | Sort-Object { [int]$_.Name }
    $v2Nesting = $v2Csv05 | Group-Object -Property NestingLevel | Sort-Object { [int]$_.Name }
    
    Write-Host "    PowerShell: $($psNesting | ForEach-Object { "Level$($_.Name)=$($_.Count)" } | Join-String -Separator ', ')" -ForegroundColor Gray
    Write-Host "    V2:         $($v2Nesting | ForEach-Object { "Level$($_.Name)=$($_.Count)" } | Join-String -Separator ', ')" -ForegroundColor Gray
    
    # Check AssignmentType distribution
    Write-Host ""
    Write-Host "  AssignmentType distribution:" -ForegroundColor White
    $psAssign = $psCsv05 | Group-Object -Property AssignmentType | Sort-Object Name
    $v2Assign = $v2Csv05 | Group-Object -Property AssignmentType | Sort-Object Name
    
    Write-Host "    PowerShell: $($psAssign | ForEach-Object { "$($_.Name)=$($_.Count)" } | Join-String -Separator ', ')" -ForegroundColor Gray
    Write-Host "    V2:         $($v2Assign | ForEach-Object { "$($_.Name)=$($_.Count)" } | Join-String -Separator ', ')" -ForegroundColor Gray
    
    # Check ViaGroup usage
    Write-Host ""
    Write-Host "  ViaGroup usage:" -ForegroundColor White
    $psViaGroupFilled = ($psCsv05 | Where-Object { $_.ViaGroup -ne "" }).Count
    $v2ViaGroupFilled = ($v2Csv05 | Where-Object { $_.ViaGroup -ne "" }).Count
    
    Write-Host "    PowerShell: $psViaGroupFilled rows with ViaGroup populated" -ForegroundColor Gray
    Write-Host "    V2:         $v2ViaGroupFilled rows with ViaGroup populated" -ForegroundColor Gray
    
    # Composite key comparison: Url + LoginName + PermissionLevel
    Write-Host ""
    Write-Host "  === Composite Key Comparison (Url+LoginName+PermissionLevel) ===" -ForegroundColor Cyan
    
    $psCompositeKeys = $psCsv05 | ForEach-Object { 
        $normalizedUrl = if ($_.Url -match "sharepoint\.com(.+)$") { $matches[1] } else { $_.Url }
        "$normalizedUrl|$($_.LoginName)|$($_.PermissionLevel)"
    } | Sort-Object -Unique
    
    $v2CompositeKeys = $v2Csv05 | ForEach-Object { 
        $normalizedUrl = if ($_.Url -match "sharepoint\.com(.+)$") { $matches[1] } else { $_.Url }
        "$normalizedUrl|$($_.LoginName)|$($_.PermissionLevel)"
    } | Sort-Object -Unique
    
    $onlyInPs05 = $psCompositeKeys | Where-Object { $_ -notin $v2CompositeKeys }
    $onlyInV205 = $v2CompositeKeys | Where-Object { $_ -notin $psCompositeKeys }
    $common05 = $psCompositeKeys | Where-Object { $_ -in $v2CompositeKeys }
    
    Write-Host "  Unique composite keys - PowerShell: $($psCompositeKeys.Count), V2: $($v2CompositeKeys.Count)" -ForegroundColor Gray
    Write-Host "  Common entries: $($common05.Count)" -ForegroundColor Green
    
    if ($onlyInPs05.Count -gt 0) {
        Write-Host "  Only in PowerShell ($($onlyInPs05.Count)):" -ForegroundColor Yellow
        $onlyInPs05 | Select-Object -First 10 | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
        if ($onlyInPs05.Count -gt 10) { Write-Host "    ... and $($onlyInPs05.Count - 10) more" -ForegroundColor Yellow }
    }
    
    if ($onlyInV205.Count -gt 0) {
        Write-Host "  Only in V2 ($($onlyInV205.Count)):" -ForegroundColor Yellow
        $onlyInV205 | Select-Object -First 10 | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
        if ($onlyInV205.Count -gt 10) { Write-Host "    ... and $($onlyInV205.Count - 10) more" -ForegroundColor Yellow }
    }
    
    # Determine result based on composite key match AND structure
    $structureMismatch = $false
    $structureIssues = @()
    
    # Critical: V2 should have user emails, not just group names (for resolved access)
    if ($v2UserEmails.Count -eq 0 -and $psUserEmails.Count -gt 0) {
        $structureMismatch = $true
        $structureIssues += "V2 has no user emails in LoginName (PS has $($psUserEmails.Count))"
    }
    
    # Critical: ViaGroup should be populated when NestingLevel > 0
    if ($v2ViaGroupFilled -eq 0 -and $psViaGroupFilled -gt 0) {
        $structureMismatch = $true
        $structureIssues += "V2 has no ViaGroup values (PS has $psViaGroupFilled)"
    }
    
    # Critical: NestingLevel distribution should be similar
    $psLevel1Count = ($psNesting | Where-Object { $_.Name -eq "1" }).Count
    $v2Level1Count = ($v2Nesting | Where-Object { $_.Name -eq "1" }).Count
    if ($psLevel1Count -gt 0 -and $v2Level1Count -eq 0) {
        $structureMismatch = $true
        $structureIssues += "V2 has no NestingLevel=1 entries (PS has $($psLevel1Count))"
    }
    
    Write-Host ""
    if ($structureMismatch) {
        Write-Host "  FAIL: Structure mismatch detected!" -ForegroundColor Red
        foreach ($issue in $structureIssues) {
            Write-Host "    - $issue" -ForegroundColor Red
        }
        $results.Failed++
    } elseif ($onlyInPs05.Count -gt 0 -or $onlyInV205.Count -gt 0) {
        Write-Host "  WARN: Content differences found" -ForegroundColor Yellow
        $results.Warnings++
    } else {
        Write-Host "  PASS: All entries match" -ForegroundColor Green
        $results.Passed++
    }
} elseif (-not (Test-Path $psFile05) -and -not (Test-Path $v2File05)) {
    Write-Host "  SKIP: Both files missing" -ForegroundColor Gray
} else {
    Write-Host "  FAIL: One file missing" -ForegroundColor Red
    $results.Failed++
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
