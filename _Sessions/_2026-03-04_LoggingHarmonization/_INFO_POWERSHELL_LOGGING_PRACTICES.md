# INFO: PowerShell Logging Practices

**Doc ID**: LOG-IN02
**Goal**: Document actual PowerShell logging patterns extracted from codebase analysis
**Timeline**: Created 2026-03-04, Updated 1 time

## Summary

**Four Logging Categories:**
1. **General** - Language-agnostic rules (indentation, format, keywords)
2. **User-Facing** - Progress indication, console feedback, color-coded status
3. **App-Level** - Debugging, script boundaries, error handling
4. **Test-Level** - N/A (PowerShell scripts don't have structured selftests)

**Core Patterns:**
- **Progress format**: `[ x / n ]` with spaces (same as Python) [VERIFIED]
- **Status colors**: Green=OK, Yellow=Warning, Red=Error, Cyan=Info [VERIFIED]
- **Section markers**: `===` lines with `START:` and `END:` keywords [VERIFIED]
- **Indentation**: 2 spaces consistent with Python [VERIFIED]

## Table of Contents

1. [General Logging Rules](#1-general-logging-rules)
2. [User-Facing Logging](#2-user-facing-logging)
3. [App-Level Logging](#3-app-level-logging)
4. [Complete Examples](#4-complete-examples)
5. [Consistency Assessment](#5-consistency-assessment)
6. [Sources](#6-sources)
7. [Document History](#7-document-history)

## 1. General Logging Rules

Language-agnostic patterns that apply to all PowerShell scripts.

### 1.1 Indentation

**Rule:** 2-space indentation for nested context.

```
Job [ 1 / 5 ] 'https://contoso.sharepoint.com/sites/ProjectA'
  Connecting to 'https://contoso.sharepoint.com/sites/ProjectA'...
  Loading subsites...
    4 lists found.
      Processing broken items [ 1 / 10 ]...
```

### 1.2 Progress Format

**Rule:** Spaces around numbers: `[ 1 / 5 ]` not `[1/5]`

```
Job [ 1 / 5 ] 'https://contoso.sharepoint.com/sites/ProjectA'
  Subsite [ 2 / 3 ] 'https://contoso.sharepoint.com/sites/ProjectA/TeamB'...
  List [ 1 / 4 ] 'https://contoso.sharepoint.com/sites/ProjectA'...
[ 15 / 42 ] Folder 'https://contoso.sharepoint.com/sites/Docs/Shared'...
```

### 1.3 Status Keywords with Colors

**Rule:** Status indicated by color, with optional text prefix.

**Success (Green):**
```
  OK: File 'Scanfile-001.csv' written                    [GREEN]
This script will NOT delete versions (testrun).          [GREEN]
```

**Warning (Yellow):**
```
WARNING: Cannot resume because 'Summary.csv' not found.  [YELLOW]
    List empty.                                          [YELLOW]
```

**Error (Red or White-on-Red):**
```
ERROR: Include file not found!                           [RED]
ERROR: Get-PnPGroupMember -Group 'Site Members'          [WHITE on RED]
```

**Info (Cyan):**
```
  Writing 'Summary.csv'...                               [CYAN]
  SUMMARY: 1250 files with 3420 versions...              [CYAN]
```

### 1.4 Result Summaries

**Rule:** Numbers precede labels.

```
  12 subsites found.
  8 groups found in site collection.
    4 lists found.
    5420 items found, 127 with broken permissions.
42 jobs found.
```

### 1.5 Property Format

**Rule:** Single quotes for names/URLs.

```
Job [ 1 / 5 ] 'https://contoso.sharepoint.com/sites/ProjectA'
Library '/sites/ProjectA/Shared Documents'
```

## 2. User-Facing Logging

Console output for end users running scripts interactively.

### 2.1 Color Conventions

**Standard Color Mapping:**
- **Green** - Success, OK, safe operations
- **Yellow** - Warnings, empty results, non-critical issues
- **Red** - Errors (foreground only for recoverable)
- **White-on-Red** - Critical errors, destructive warnings
- **Cyan** - Info messages, file operations, summaries
- **Gray** - Version info, debug output
- **White-on-Blue** - Important notices

### 2.2 Progress Iteration with Status

**Example: Permission scan with mixed results**

```
Job [ 1 / 5 ] 'https://contoso.sharepoint.com/sites/ProjectA'
  Connecting to 'https://contoso.sharepoint.com/sites/ProjectA'...
  Loading subsites...
  3 subsites found.
  Loading site groups...
  8 groups found in site collection.
    4 lists found.
    5420 items found, 127 with broken permissions.
      Processing broken items [ 50 / 127 ]...
      Processing broken items [ 100 / 127 ]...
    152 lines written to: '01_SiteContents.csv'          [CYAN]
  OK: File '02_SiteGroups.csv' written                   [GREEN]
Job [ 2 / 5 ] 'https://contoso.sharepoint.com/sites/ProjectB'
  Connecting to 'https://contoso.sharepoint.com/sites/ProjectB'...
  ERROR: (401) Unauthorized                              [RED]
```

### 2.3 File Operation Messages

```
  Writing 152 lines to '01_SiteContents.csv'...          [CYAN]
  Writing 'Summary.csv'...                               [CYAN]
  OK: File 'Scanfile-001.csv' written                    [GREEN]
```

### 2.4 Summary Format

```
  SUMMARY: 1250 files with 3420 versions, 892 can be deleted. Size is 4.2 GB in total (38.5% in versions) 1.1 GB (26.2%) can be deleted.    [CYAN]
```

### 2.5 Important Notices

**Info notice (White on Blue):**
```
$performDelete is $true but all delete options are $false. Script will not delete anything.    [WHITE on BLUE]
```

**Critical warning (White on Red):**
```
IMPORTANT: This script will permanently DELETE all versions
- except for the newest version
- except if the time to the next version is more than 15 minutes    [WHITE on RED]
Press any key to continue...
```

## 3. App-Level Logging

Debugging and tracing for script developers.

### 3.1 Script Boundaries (START/END)

**Rule:** Every script logs START and END with duration.

```
2026-03-04 14:30:00
================================================== START: SHAREPOINT PERMISSION SCANNER ==================================================
PowerShell: 7.4.1 | PnP.PowerShell: 2.4.0                [GRAY]
...
=================================================== END: SHAREPOINT PERMISSION SCANNER ===================================================
2026-03-04 14:35:23 (5 mins 23 secs)
```

**Duration format:** "X hours Y mins Z secs"

**Infrastructure:** `Write-ScriptHeader` and `Write-ScriptFooter` functions in `_includes.ps1`

### 3.2 Error Handling

**Recoverable error (Red foreground):**
```
  ERROR: URL must start with 'https://' and contain '/sites/'!    [RED]
  ERROR: '$siteUrl' not a list or subsite! Check URL.             [RED]
    ERROR: File size can't be determined!                         [RED]
```

**Critical error (White on Red background):**
```
ERROR: Get-PnPGroupMember -Group 'Site Members'                   [WHITE on RED]
Cannot find group with identity 'Site Members'
```

**Error with context chain:**
```
ERROR: Couldn't write to 'errorlog.csv'.                          [WHITE on RED]
  Access denied.
```

### 3.3 Code Section Markers

**Rule:** `#####` markers for code organization (not runtime output).

```powershell
#################### START: LOAD INCLUDE AND GET CREDENTIALS ####################
# ... code ...
#################### END: LOAD INCLUDE AND GET CREDENTIALS ######################
```

### 3.4 Infrastructure Functions

**Common Include Pattern:**
```powershell
$includeFile1 = (SearchFileInFolderOrAnyParentFolder -path $PSScriptRoot -filename "_includes.ps1")
if ($includeFile1 -eq ""){Write-Host "ERROR: Include file not found!" -ForegroundColor Red; exit}
. $includeFile1
```

**Write-Host2 Wrapper (dual console + file logging):**
```powershell
function Write-Host2 {
    param($Object, $ForegroundColor, $BackgroundColor)
    Write-Host -Object $Object -ForegroundColor $ForegroundColor
    [System.IO.File]::AppendAllLines($logFileFullName, @($Object))
}
```

## 4. Complete Examples

### 4.1 Full Script Execution

**SharePoint Permission Scanner:**
```
2026-03-04 14:30:00
================================================== START: SHAREPOINT PERMISSION SCANNER ==================================================
PowerShell: 7.4.1 | PnP.PowerShell: 2.4.0                [GRAY]
Reading 'SharePointPermissionScanner-In.csv'...
5 jobs found.
Job [ 1 / 5 ] 'https://contoso.sharepoint.com/sites/ProjectA'
  Connecting to 'https://contoso.sharepoint.com/sites/ProjectA'...
  Loading subsites...
  3 subsites found.
  Loading site groups...
  8 groups found in site collection.
  Loading site contents...
    4 lists found.
    Scanning library '/sites/ProjectA/Documents'...
    Loading items with bulk REST query...
    5420 items found, 127 with broken permissions.
      Processing broken items [ 50 / 127 ]...
      Processing broken items [ 100 / 127 ]...
    152 lines written to: '01_SiteContents.csv'          [CYAN]
  OK: File '02_SiteGroups.csv' written                   [GREEN]
Job [ 2 / 5 ] 'https://contoso.sharepoint.com/sites/ProjectB'
  Connecting to 'https://contoso.sharepoint.com/sites/ProjectB'...
  ERROR: (401) Unauthorized                              [RED]
Job [ 3 / 5 ] 'https://contoso.sharepoint.com/sites/ProjectC'
  ...
=================================================== END: SHAREPOINT PERMISSION SCANNER ===================================================
2026-03-04 14:35:23 (5 mins 23 secs)
```

### 4.2 File Version Scanner

**ScanOrDeleteFileVersions script:**
```
2026-03-04 10:00:00
================================================== START: SCAN OR DELETE FILE VERSIONS ==================================================
This script will NOT delete versions (testrun).          [GREEN]
Reading 'ScanOrDeleteFileVersions-In.csv'...
3 jobs found.
Job [ 1 / 3 ] 'https://contoso.sharepoint.com/sites/Archive'
  Connecting to 'https://contoso.sharepoint.com/sites/Archive'...
  Loading document libraries...
  2 libraries found.
  [ 1 / 2 ] Scanning 'Documents'...
    Loading items...
    500 items retrieved so far...
    1000 items retrieved so far...
    1250 files retrieved.
    Scanning versions...
      [ 100 / 1250 ] Processing 'report_2024.xlsx'...
      [ 200 / 1250 ] Processing 'budget_final.xlsx'...
      ...
  SUMMARY: 1250 files with 3420 versions, 892 can be deleted. Size is 4.2 GB in total (38.5% in versions) 1.1 GB (26.2%) can be deleted.    [CYAN]
=================================================== END: SCAN OR DELETE FILE VERSIONS ===================================================
2026-03-04 10:15:45 (15 mins 45 secs)
```

## 5. Consistency Assessment

### 5.1 Consistent with Python

- 2-space indentation
- `[ x / n ]` progress format with spaces
- `START:/END:` section markers
- `ERROR:`/`WARNING:` prefixes
- Count messages: "X items found."

### 5.2 PowerShell-Specific Patterns

- **Color-based status** instead of `OK./FAIL:` text suffixes
- **Background colors** for critical messages (White-on-Red)
- **`Write-ScriptHeader/Footer`** instead of `log_function_header/footer`
- **Duration format**: "X hours Y mins Z secs" vs Python ms formatting
- **Section markers**: `#####` vs Python `# ---`

### 5.3 Variations Between Scripts

- Some scripts use `Write-Host2` wrapper, others use `Write-Host` directly
- Error display varies: `-ForegroundColor Red` vs `-f white -b red`
- Summary messages vary in structure (not standardized)

## 6. Sources

**Primary Sources:**
- `LOG-IN02-SC-SPPS-MAIN`: `SharePointPermissionScanner.ps1` - Reference implementation (1034 lines) [VERIFIED]
- `LOG-IN02-SC-FVSD-MAIN`: `ScanOrDeleteFileVersions.ps1` - Verbose logging patterns (607 lines) [VERIFIED]
- `LOG-IN02-SC-PSFN-MAIN`: `ProcessScanfiles.ps1` - File scanning patterns (591 lines) [VERIFIED]
- `LOG-IN02-SC-SSPL-MAIN`: `ScanSharePointLibrariesFromFile.ps1` - SharePoint connection logging (354 lines) [VERIFIED]
- `LOG-IN02-SC-DCUF-MAIN`: `01_CopyAndUploadFilesDEV.ps1` - Write-Host2 wrapper, error logging (1099 lines) [VERIFIED]

**Analysis Scope:**
- 5 PowerShell files analyzed
- Total ~3685 lines of PowerShell code
- Patterns extracted via manual analysis

## 7. Document History

**[2026-03-04 15:10]**
- Restructured with 4-category classification:
  1. General Logging Rules (language-agnostic)
  2. User-Facing Logging (progress, feedback)
  3. App-Level Logging (debugging, tracing)
  4. Complete Examples
- Added File Version Scanner example

**[2026-03-04 14:40]**
- Initial INFO document created from PowerShell codebase analysis
- 10 pattern categories documented with examples
- Color conventions documented
- Consistency assessment completed
