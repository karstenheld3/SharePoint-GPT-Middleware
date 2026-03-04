# 05_CompareOutputs.ps1
# Compares PowerShell Scanner output with V2 Security Scan output

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Global indentation setting
$INDENT = "  "

# Logging functions (compact output, only show OK/WARNING/FAIL prefixes)
function Write-Log {
    param(
        [string]$Level,
        [string]$Message,
        [int]$Indent = 0
    )
    $prefix = $script:INDENT * $Indent
    $levelColors = @{
        "INFO" = "White"
        "DEBUG" = "Gray"
        "WARN" = "Yellow"
        "ERROR" = "Red"
        "PASS" = "Green"
        "FAIL" = "Red"
        "SKIP" = "DarkGray"
    }
    $levelPrefixes = @{
        "PASS" = "OK:"
        "WARN" = "WARNING:"
        "FAIL" = "FAIL:"
        "ERROR" = "FAIL:"
        "SKIP" = "SKIP:"
    }
    $color = $levelColors[$Level]
    if (-not $color) { $color = "White" }
    # Only show prefix for actionable levels
    if ($levelPrefixes.ContainsKey($Level)) {
        Write-Host "$($levelPrefixes[$Level]) $Message" -ForegroundColor $color
    } else {
        Write-Host "$prefix$Message" -ForegroundColor $color
    }
}

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "========== $Title ==========" -ForegroundColor White
}

function Write-Metric {
    param(
        [string]$Label,
        [string]$PsValue,
        [string]$V2Value,
        [int]$Indent = 1,
        [switch]$IsColumnName
    )
    $prefix = $script:INDENT * $Indent
    $match = if ($PsValue -eq $V2Value) { "[equal]" } else { "[different]" }
    $color = if ($PsValue -eq $V2Value) { "Green" } else { "Yellow" }
    $labelText = if ($IsColumnName) { "'$Label'" } else { $Label }
    Write-Host "$prefix$match $labelText  PowerShell=$PsValue  Python=$V2Value" -ForegroundColor $color
}

$startTime = Get-Date
Write-Section "Compare Scan Outputs"
Write-Log "INFO" "PowerShell output: SharePointPermissionScanner/"
Write-Log "INFO" "Python output: SiteSecurityScanOutput/"

$psOutputDir = Join-Path $scriptDir "SharePointPermissionScanner"
$v2OutputDir = Join-Path $scriptDir "SiteSecurityScanOutput"

# Check directories exist
if (-not (Test-Path $psOutputDir)) {
    Write-Log "ERROR" "SharePointPermissionScanner directory not found."
    exit 1
}

if (-not (Test-Path $v2OutputDir)) {
    Write-Log "ERROR" "SiteSecurityScanOutput directory not found. Run 04_RunV2SecurityScan.ps1 first."
    exit 1
}

$results = @{
    Passed = 0
    Failed = 0
    Warnings = 0
    PassedFiles = @()
    FailedFiles = @()
    WarningFiles = @()
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

# Helper function to import CSV with line numbers (line 1 = header, line 2 = first data row)
function Import-CsvWithLineNumbers {
    param([string]$Path)
    $lineNum = 1  # Start at 1 for header
    Import-Csv -Path $Path | ForEach-Object {
        $lineNum++
        $_ | Add-Member -NotePropertyName "_LineNum" -NotePropertyValue $lineNum -PassThru
    }
}

# Helper function to get line numbers for a key value
function Get-LineNumbersForKey {
    param($CsvData, [string]$KeyColumn, [string]$KeyValue)
    $lines = $CsvData | Where-Object { (Get-NormalizedUrl $_.$KeyColumn) -eq $KeyValue } | ForEach-Object { $_._LineNum }
    return ($lines -join ",")
}

# File comparison config - ordered list for sequential comparison
$fileCompareConfig = @(
    @{ FileName = "01_SiteContents.csv"; KeyColumn = "Url"; Description = "Site Contents (Lists/Libraries)"; Explanation = "Comparing row count and unique 'Url' values to verify both scanners found the same lists and libraries." }
    @{ FileName = "02_SiteGroups.csv"; KeyColumn = "Title"; Description = "Site Groups"; Explanation = "Comparing row count and unique 'Title' values to verify both scanners found the same SharePoint groups." }
    @{ FileName = "03_SiteUsers.csv"; KeyColumn = "LoginName"; Description = "Site Users"; Explanation = "Comparing row count and unique 'LoginName' values to verify both scanners found the same users." }
)

# Compare 01, 02, 03 files (simple key-based comparison)
foreach ($config in $fileCompareConfig) {
    $fileName = $config.FileName
    $keyColumn = $config.KeyColumn
    $desc = $config.Description
    $explanation = $config.Explanation
    
    Write-Section "$fileName ($desc)"
    Write-Host $explanation -ForegroundColor Gray
    
    $psFilePath = Join-Path $psOutputDir $fileName
    $v2FilePath = Join-Path $v2OutputDir $fileName
    
    $psExists = Test-Path $psFilePath
    $v2Exists = Test-Path $v2FilePath
    
    if ($psExists -and $v2Exists) {
        $psCsv = Import-CsvWithLineNumbers -Path $psFilePath
        $v2Csv = Import-CsvWithLineNumbers -Path $v2FilePath
        
        Write-Metric "Row count" $psCsv.Count $v2Csv.Count
        
        $psKeys = $psCsv | ForEach-Object { Get-NormalizedUrl $_.$keyColumn } | Sort-Object -Unique
        $v2Keys = $v2Csv | ForEach-Object { Get-NormalizedUrl $_.$keyColumn } | Sort-Object -Unique
        
        Write-Metric "Unique '$keyColumn'" $psKeys.Count $v2Keys.Count
        
        $onlyInPs = $psKeys | Where-Object { $_ -notin $v2Keys }
        $onlyInV2 = $v2Keys | Where-Object { $_ -notin $psKeys }
        $common = $psKeys | Where-Object { $_ -in $v2Keys }
        
        # Show comparison result
        if ($onlyInPs.Count -eq 0 -and $onlyInV2.Count -eq 0) {
            Write-Log "PASS" "All $($common.Count) items match" 1
            $results.Passed++
            $results.PassedFiles += $fileName
        } else {
            Write-Metric "Common" $common.Count $common.Count
            if ($onlyInPs.Count -gt 0) {
                $itemWord = if ($onlyInPs.Count -eq 1) { "item" } else { "items" }
                Write-Log "DEBUG" "$($onlyInPs.Count) $itemWord only in PowerShell (missing in Python):" 1
                $onlyInPs | ForEach-Object { 
                    $lineNums = Get-LineNumbersForKey $psCsv $keyColumn $_
                    Write-Log "DEBUG" "Line $lineNums`: '$_'" 2 
                }
            }
            if ($onlyInV2.Count -gt 0) {
                $itemWord = if ($onlyInV2.Count -eq 1) { "item" } else { "items" }
                Write-Log "DEBUG" "$($onlyInV2.Count) $itemWord only in Python (missing in PowerShell):" 1
                $onlyInV2 | ForEach-Object { 
                    $lineNums = Get-LineNumbersForKey $v2Csv $keyColumn $_
                    Write-Log "DEBUG" "Line $lineNums`: '$_'" 2 
                }
            }
            Write-Log "WARN" "$($common.Count) common, $($onlyInPs.Count) only in PowerShell, $($onlyInV2.Count) only in Python" 1
            $results.Warnings++
            $results.WarningFiles += $fileName
        }
    } elseif (-not $psExists -and -not $v2Exists) {
        Write-Log "SKIP" "Both files missing" 1
    } else {
        Write-Log "FAIL" "One file missing (PowerShell: $psExists, Python: $v2Exists)" 1
        $results.Failed++
        $results.FailedFiles += $fileName
    }
}

# Compare 04_IndividualPermissionItems.csv (items with broken inheritance)
Write-Section "04_IndividualPermissionItems.csv (Items with Broken Inheritance)"
Write-Host "Comparing items (files, folders, list items) that have unique permissions different from their parent." -ForegroundColor Gray

$psFile = Join-Path $psOutputDir "04_IndividualPermissionItems.csv"
$v2File = Join-Path $v2OutputDir "04_IndividualPermissionItems.csv"

if ((Test-Path $psFile) -and (Test-Path $v2File)) {
    $psCsv = Import-CsvWithLineNumbers -Path $psFile
    $v2Csv = Import-CsvWithLineNumbers -Path $v2File
    
    $psUrls = $psCsv | ForEach-Object { Get-NormalizedUrl $_.Url } | Sort-Object -Unique
    $v2Urls = $v2Csv | ForEach-Object { Get-NormalizedUrl $_.Url } | Sort-Object -Unique
    
    Write-Metric "Row count" $psCsv.Count $v2Csv.Count
    Write-Metric "Unique 'Url'" $psUrls.Count $v2Urls.Count
    
    $onlyInPs = $psUrls | Where-Object { $_ -notin $v2Urls }
    $onlyInV2 = $v2Urls | Where-Object { $_ -notin $psUrls }
    $common = $psUrls | Where-Object { $_ -in $v2Urls }
    
    # Show comparison result
    if ($onlyInPs.Count -eq 0 -and $onlyInV2.Count -eq 0) {
        Write-Log "PASS" "All $($common.Count) items match" 1
        $results.Passed++
        $results.PassedFiles += "04_IndividualPermissionItems.csv"
    } else {
        Write-Metric "Common" $common.Count $common.Count
        if ($onlyInPs.Count -gt 0) {
            $itemWord = if ($onlyInPs.Count -eq 1) { "item" } else { "items" }
            Write-Log "DEBUG" "$($onlyInPs.Count) $itemWord only in PowerShell (missing in Python):" 1
            $onlyInPs | ForEach-Object { 
                $lineNums = Get-LineNumbersForKey $psCsv "Url" $_
                Write-Log "DEBUG" "Line $lineNums`: '$_'" 2 
            }
        }
        if ($onlyInV2.Count -gt 0) {
            $itemWord = if ($onlyInV2.Count -eq 1) { "item" } else { "items" }
            Write-Log "DEBUG" "$($onlyInV2.Count) $itemWord only in Python (missing in PowerShell):" 1
            $onlyInV2 | ForEach-Object { 
                $lineNums = Get-LineNumbersForKey $v2Csv "Url" $_
                Write-Log "DEBUG" "Line $lineNums`: '$_'" 2 
            }
        }
        Write-Log "WARN" "$($common.Count) common, $($onlyInPs.Count) only in PowerShell, $($onlyInV2.Count) only in Python" 1
        $results.Warnings++
        $results.WarningFiles += "04_IndividualPermissionItems.csv"
    }
} else {
    Write-Log "SKIP" "One or both files missing" 1
}

# Special detailed comparison for 05_IndividualPermissionItemAccess.csv
Write-Section "05_IndividualPermissionItemAccess.csv (User Access Details)"
Write-Host "Comparing which users have access to items with broken inheritance, including how they got access (direct or via groups)." -ForegroundColor Gray

$psFile05 = Join-Path $psOutputDir "05_IndividualPermissionItemAccess.csv"
$v2File05 = Join-Path $v2OutputDir "05_IndividualPermissionItemAccess.csv"

if ((Test-Path $psFile05) -and (Test-Path $v2File05)) {
    $psCsv05 = Import-CsvWithLineNumbers -Path $psFile05
    $v2Csv05 = Import-CsvWithLineNumbers -Path $v2File05
    
    Write-Metric "Row count" $psCsv05.Count $v2Csv05.Count
    
    # Analyze structure differences
    Write-Log "INFO" "Structure Analysis:" 1
    
    # Check LoginName patterns - are they user emails or group names?
    $psLoginNames = $psCsv05 | ForEach-Object { $_.LoginName } | Sort-Object -Unique
    $v2LoginNames = $v2Csv05 | ForEach-Object { $_.LoginName } | Sort-Object -Unique
    
    $psUserEmails = $psLoginNames | Where-Object { $_ -match "@" }
    $psGroupNames = $psLoginNames | Where-Object { $_ -notmatch "@" -and $_ -ne "" }
    $v2UserEmails = $v2LoginNames | Where-Object { $_ -match "@" }
    $v2GroupNames = $v2LoginNames | Where-Object { $_ -notmatch "@" -and $_ -ne "" }
    
    Write-Metric "Distinct 'LoginName' emails" $psUserEmails.Count $v2UserEmails.Count 2
    Write-Metric "Distinct 'LoginName' group names" $psGroupNames.Count $v2GroupNames.Count 2
    
    # Show only differences in emails between outputs
    $emailsOnlyInPs = $psUserEmails | Where-Object { $_ -notin $v2UserEmails }
    $emailsOnlyInV2 = $v2UserEmails | Where-Object { $_ -notin $psUserEmails }
    $commonEmails = $psUserEmails | Where-Object { $_ -in $v2UserEmails }
    
    Write-Log "DEBUG" "$($commonEmails.Count) emails found in both outputs" 2
    if ($emailsOnlyInPs.Count -gt 0) {
        Write-Log "DEBUG" "$($emailsOnlyInPs.Count) emails only in PowerShell (missing in Python):" 2
        $emailsOnlyInPs | ForEach-Object { 
            $lineNums = Get-LineNumbersForKey $psCsv05 "LoginName" $_
            Write-Log "DEBUG" "Line $lineNums`: '$_'" 3 
        }
    }
    if ($emailsOnlyInV2.Count -gt 0) {
        Write-Log "DEBUG" "$($emailsOnlyInV2.Count) emails only in Python (missing in PowerShell):" 2
        $emailsOnlyInV2 | ForEach-Object { 
            $lineNums = Get-LineNumbersForKey $v2Csv05 "LoginName" $_
            Write-Log "DEBUG" "Line $lineNums`: '$_'" 3 
        }
    }
    if ($v2GroupNames.Count -gt 0) {
        Write-Log "DEBUG" "$($v2GroupNames.Count) group names found in Python output:" 2
        $v2GroupNames | ForEach-Object { 
            $lineNums = Get-LineNumbersForKey $v2Csv05 "LoginName" $_
            Write-Log "DEBUG" "Line $lineNums`: '$_'" 3 
        }
    }
    
    # How do users get access? Direct or through groups?
    # Create composite keys for comparison using tab delimiter (LoginNames can contain pipes)
    $psAccessKeys = $psCsv05 | ForEach-Object { 
        $normalizedUrl = if ($_.Url -match "sharepoint\.com(.+)$") { $matches[1] } else { $_.Url }
        "$($_.LoginName)`t$normalizedUrl`t$($_.NestingLevel)"
    }
    $v2AccessKeys = $v2Csv05 | ForEach-Object { 
        $normalizedUrl = if ($_.Url -match "sharepoint\.com(.+)$") { $matches[1] } else { $_.Url }
        "$($_.LoginName)`t$normalizedUrl`t$($_.NestingLevel)"
    }
    
    $accessOnlyInPs = $psAccessKeys | Where-Object { $_ -notin $v2AccessKeys }
    $accessOnlyInV2 = $v2AccessKeys | Where-Object { $_ -notin $psAccessKeys }
    
    Write-Log "DEBUG" "How users get access to items:" 2
    if ($accessOnlyInPs.Count -eq 0 -and $accessOnlyInV2.Count -eq 0) {
        Write-Log "DEBUG" "All access entries match between outputs" 3
    } else {
        if ($accessOnlyInPs.Count -gt 0) {
            Write-Log "DEBUG" "$($accessOnlyInPs.Count) access entries only in PowerShell:" 3
            $accessOnlyInPs | ForEach-Object {
                $parts = $_ -split "`t"
                $row = $psCsv05 | Where-Object { $_.LoginName -eq $parts[0] -and (Get-NormalizedUrl $_.Url) -eq $parts[1] -and $_.NestingLevel -eq $parts[2] } | Select-Object -First 1
                Write-Log "DEBUG" "Line $($row._LineNum): LoginName='$($parts[0])' NestingLevel=$($parts[2])" 4
            }
        }
        if ($accessOnlyInV2.Count -gt 0) {
            Write-Log "DEBUG" "$($accessOnlyInV2.Count) access entries only in Python:" 3
            $accessOnlyInV2 | ForEach-Object {
                $parts = $_ -split "`t"
                $row = $v2Csv05 | Where-Object { $_.LoginName -eq $parts[0] -and (Get-NormalizedUrl $_.Url) -eq $parts[1] -and $_.NestingLevel -eq $parts[2] } | Select-Object -First 1
                Write-Log "DEBUG" "Line $($row._LineNum): LoginName='$($parts[0])' NestingLevel=$($parts[2])" 4
            }
        }
    }
    
    # What type of permissions are assigned?
    # Create composite keys for comparison using tab delimiter
    $psAssignKeys = $psCsv05 | ForEach-Object { 
        $normalizedUrl = if ($_.Url -match "sharepoint\.com(.+)$") { $matches[1] } else { $_.Url }
        "$($_.LoginName)`t$normalizedUrl`t$($_.AssignmentType)"
    }
    $v2AssignKeys = $v2Csv05 | ForEach-Object { 
        $normalizedUrl = if ($_.Url -match "sharepoint\.com(.+)$") { $matches[1] } else { $_.Url }
        "$($_.LoginName)`t$normalizedUrl`t$($_.AssignmentType)"
    }
    
    $assignOnlyInPs = $psAssignKeys | Where-Object { $_ -notin $v2AssignKeys }
    $assignOnlyInV2 = $v2AssignKeys | Where-Object { $_ -notin $psAssignKeys }
    
    Write-Log "DEBUG" "How permissions are assigned:" 2
    if ($assignOnlyInPs.Count -eq 0 -and $assignOnlyInV2.Count -eq 0) {
        Write-Log "DEBUG" "All assignment entries match between outputs" 3
    } else {
        if ($assignOnlyInPs.Count -gt 0) {
            Write-Log "DEBUG" "$($assignOnlyInPs.Count) assignment entries only in PowerShell:" 3
            $assignOnlyInPs | ForEach-Object {
                $parts = $_ -split "`t"
                $row = $psCsv05 | Where-Object { $_.LoginName -eq $parts[0] -and (Get-NormalizedUrl $_.Url) -eq $parts[1] -and $_.AssignmentType -eq $parts[2] } | Select-Object -First 1
                Write-Log "DEBUG" "Line $($row._LineNum): LoginName='$($parts[0])' AssignmentType='$($parts[2])'" 4
            }
        }
        if ($assignOnlyInV2.Count -gt 0) {
            Write-Log "DEBUG" "$($assignOnlyInV2.Count) assignment entries only in Python:" 3
            $assignOnlyInV2 | ForEach-Object {
                $parts = $_ -split "`t"
                $row = $v2Csv05 | Where-Object { $_.LoginName -eq $parts[0] -and (Get-NormalizedUrl $_.Url) -eq $parts[1] -and $_.AssignmentType -eq $parts[2] } | Select-Object -First 1
                Write-Log "DEBUG" "Line $($row._LineNum): LoginName='$($parts[0])' AssignmentType='$($parts[2])'" 4
            }
        }
    }
    
    # Composite key comparison: Url + LoginName + PermissionLevel
    # Use tab as delimiter since LoginNames can contain pipes
    Write-Log "INFO" "Composite Key Comparison (Url + LoginName + PermissionLevel):" 1
    
    $psCompositeKeys = $psCsv05 | ForEach-Object { 
        $normalizedUrl = if ($_.Url -match "sharepoint\.com(.+)$") { $matches[1] } else { $_.Url }
        "$normalizedUrl`t$($_.LoginName)`t$($_.PermissionLevel)"
    } | Sort-Object -Unique
    
    $v2CompositeKeys = $v2Csv05 | ForEach-Object { 
        $normalizedUrl = if ($_.Url -match "sharepoint\.com(.+)$") { $matches[1] } else { $_.Url }
        "$normalizedUrl`t$($_.LoginName)`t$($_.PermissionLevel)"
    } | Sort-Object -Unique
    
    $onlyInPs05 = $psCompositeKeys | Where-Object { $_ -notin $v2CompositeKeys }
    $onlyInV205 = $v2CompositeKeys | Where-Object { $_ -notin $psCompositeKeys }
    $common05 = $psCompositeKeys | Where-Object { $_ -in $v2CompositeKeys }
    
    Write-Metric "Unique composite keys" $psCompositeKeys.Count $v2CompositeKeys.Count 2
    Write-Log "DEBUG" "Common entries: $($common05.Count)" 2
    $matchPct = if ($psCompositeKeys.Count -gt 0) { [math]::Round(($common05.Count / $psCompositeKeys.Count) * 100, 1) } else { 0 }
    Write-Log "DEBUG" "Match rate: $matchPct% ($($common05.Count)/$($psCompositeKeys.Count))" 2
    
    Write-Metric "Common" $common05.Count $common05.Count 2
    if ($onlyInPs05.Count -gt 0) {
        Write-Log "DEBUG" "$($onlyInPs05.Count) keys only in PowerShell (missing in Python):" 2
        $onlyInPs05 | ForEach-Object { 
            $key = $_
            $parts = $key -split "`t"
            $lineNums = ($psCsv05 | Where-Object { 
                $normalizedUrl = if ($_.Url -match "sharepoint\.com(.+)$") { $matches[1] } else { $_.Url }
                $normalizedUrl -eq $parts[0] -and $_.LoginName -eq $parts[1] -and $_.PermissionLevel -eq $parts[2]
            })._LineNum -join ","
            $displayKey = "$($parts[0]) | $($parts[1]) | $($parts[2])"
            Write-Log "DEBUG" "Line $lineNums`: '$displayKey'" 3 
        }
    }
    
    if ($onlyInV205.Count -gt 0) {
        Write-Log "DEBUG" "$($onlyInV205.Count) keys only in Python (missing in PowerShell):" 2
        $onlyInV205 | ForEach-Object { 
            $key = $_
            $parts = $key -split "`t"
            $lineNums = ($v2Csv05 | Where-Object { 
                $normalizedUrl = if ($_.Url -match "sharepoint\.com(.+)$") { $matches[1] } else { $_.Url }
                $normalizedUrl -eq $parts[0] -and $_.LoginName -eq $parts[1] -and $_.PermissionLevel -eq $parts[2]
            })._LineNum -join ","
            $displayKey = "$($parts[0]) | $($parts[1]) | $($parts[2])"
            Write-Log "DEBUG" "Line $lineNums`: '$displayKey'" 3 
        }
    }
    
    # Determine result based on composite key match AND structure
    $structureMismatch = $false
    $structureIssues = @()
    
    # Critical: Python should have user emails, not just group names (for resolved access)
    if ($v2UserEmails.Count -eq 0 -and $psUserEmails.Count -gt 0) {
        $structureMismatch = $true
        $structureIssues += "Python has no user emails in LoginName (PowerShell has $($psUserEmails.Count))"
    }
    
    # Critical: ViaGroup should be populated when NestingLevel > 0
    if ($v2ViaGroupFilled -eq 0 -and $psViaGroupFilled -gt 0) {
        $structureMismatch = $true
        $structureIssues += "Python has no ViaGroup values (PowerShell has $psViaGroupFilled)"
    }
    
    # Critical: NestingLevel distribution should be similar
    $psLevel1Count = ($psNesting | Where-Object { $_.Name -eq "1" }).Count
    $v2Level1Count = ($v2Nesting | Where-Object { $_.Name -eq "1" }).Count
    if ($psLevel1Count -gt 0 -and $v2Level1Count -eq 0) {
        $structureMismatch = $true
        $structureIssues += "Python has no NestingLevel=1 entries (PowerShell has $($psLevel1Count))"
    }
    
    if ($structureMismatch) {
        Write-Log "FAIL" "Structure mismatch detected!" 1
        foreach ($issue in $structureIssues) {
            Write-Log "ERROR" "  $issue" 2
        }
        $results.Failed++
        $results.FailedFiles += "05_IndividualPermissionItemAccess.csv"
    } elseif ($onlyInPs05.Count -gt 0 -or $onlyInV205.Count -gt 0) {
        Write-Log "WARN" "Content differences: $matchPct% match ($($common05.Count)/$($psCompositeKeys.Count) common)" 1
        $results.Warnings++
        $results.WarningFiles += "05_IndividualPermissionItemAccess.csv"
    } else {
        Write-Log "PASS" "All $($common05.Count) entries match" 1
        $results.Passed++
        $results.PassedFiles += "05_IndividualPermissionItemAccess.csv"
    }
} elseif (-not (Test-Path $psFile05) -and -not (Test-Path $v2File05)) {
    Write-Log "SKIP" "Both files missing" 1
} else {
    Write-Log "FAIL" "One file missing" 1
    $results.Failed++
    $results.FailedFiles += "05_IndividualPermissionItemAccess.csv"
}

# Summary
Write-Section "Comparison Summary"
$total = $results.Passed + $results.Warnings + $results.Failed
$duration = (Get-Date) - $startTime

# Format file lists with single quotes
$allFiles = ($results.PassedFiles + $results.WarningFiles + $results.FailedFiles) | Sort-Object -Unique
$allFilesStr = ($allFiles | ForEach-Object { "'$_'" }) -join ", "
$passedFilesStr = ($results.PassedFiles | ForEach-Object { "'$_'" }) -join ", "
$warningFilesStr = ($results.WarningFiles | ForEach-Object { "'$_'" }) -join ", "
$failedFilesStr = ($results.FailedFiles | ForEach-Object { "'$_'" }) -join ", "

Write-Log "INFO" "$total files compared ($allFilesStr)"
if ($results.Passed -gt 0) { Write-Log "PASS" "$($results.Passed) passed ($passedFilesStr)" }
if ($results.Warnings -gt 0) { Write-Log "WARN" "$($results.Warnings) with warnings ($warningFilesStr)" }
if ($results.Failed -gt 0) { Write-Log "FAIL" "$($results.Failed) failed ($failedFilesStr)" }
Write-Log "INFO" "Duration: $([math]::Round($duration.TotalSeconds, 1))s"

if ($results.Failed -gt 0) {
    Write-Host "RESULT: FAILED" -ForegroundColor Red
    exit 1
} elseif ($results.Warnings -gt 0) {
    Write-Host "RESULT: PASSED WITH WARNINGS" -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "RESULT: PASSED" -ForegroundColor Green
    exit 0
}
