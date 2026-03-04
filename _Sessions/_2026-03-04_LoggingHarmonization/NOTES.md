# Session Notes

**Doc ID**: LOG-NOTES
**Started**: 2026-03-04
**Goal**: Harmonize logging rules across Python and PowerShell with unified design goals

## Current Phase

**Phase**: EXPLORE
**Workflow**: /write-strut
**Assessment**: Python analysis complete, patterns documented

## Session Info

**Objective**: Create unified logging rules document covering:
1. General logging rules (language-agnostic)
2. User-facing logging (progress, feedback)
3. App-level logging (debugging, tracing)
4. Test-level logging (QA, verification)

**Design Goals** (from user):
- Test-level: All failure info in logs without analyzing additional I/O data
- App-level: Human-readable without knowing full architecture; nested, spelled out, START/END markers
- App-level: Parsable with reasonable effort
- User-facing: Progress indication via indentation, numbering, totals
- User-facing: Feedback every ~10 seconds, START/END markers, final result

## Python Logging Analysis (Complete)

### Infrastructure Files

**V2 Logging** (`common_logging_functions_v2.py`):
- `MiddlewareLogger` dataclass with request-scoped state
- `UNKNOWN = '[UNKNOWN]'` constant for missing values
- `format_milliseconds()` for duration formatting
- Methods: `log_function_header()`, `log_function_output()`, `log_function_footer()`
- Optional SSE streaming via `stream_job_writer` parameter
- Auto-indentation based on nesting depth (2 spaces per level)
- Console format: `[timestamp,process PID,request N,function_name] message`

**V1 Logging** (`common_logging_functions_v1.py`):
- Standalone functions (not class-based)
- Same console format as V2
- `sanitize_queries_and_responses()` for PII redaction

### Pattern Categories Found

**1. Function Boundaries (START/END)**
```python
logger.log_function_header("function_name()")
# ... work ...
logger.log_function_footer()
```
Output: `START: function_name()...` and `END: function_name() (duration).`

**2. Code Section Markers**
```python
# ----------------------------------------- START: Topic Name -----
# ----------------------------------------- END: Topic Name -------
```
127 chars total, consistent across all files.

**3. Progress Iteration Format**
```python
logger.log_function_output(f"[ {i+1} / {total} ] Downloading '{filename}'...")
```
Pattern: `[ x / n ]` with spaces around numbers.

**4. Status Keywords**
```python
logger.log_function_output("  OK.")
logger.log_function_output(f"  ERROR: {error}")
logger.log_function_output(f"  WARNING: {message}")
logger.log_function_output(f"  FAIL: {message}")
```
Always indented with 2 spaces, on separate line.

**5. Result Summaries (Numbers First)**
```python
logger.log_function_output(f"  {len(changes.added)} added, {len(changes.changed)} changed, {len(changes.removed)} removed, {len(changes.unchanged)} unchanged.")
logger.log_function_output(f"  {result.downloaded} downloaded, {result.skipped} skipped, {result.errors} error{'' if result.errors == 1 else 's'}.")
```

**6. Singular/Plural Handling**
```python
f"{count} file{'' if count == 1 else 's'}"
f"{count} item{'' if count == 1 else 's'}"
f"{count} error{'' if count == 1 else 's'}"
```

**7. Error Chain Format**
```python
logger.log_function_output(f"ERROR: {context} -> {error}")
logger.log_function_output(f"ERROR: Crawl failed -> {str(e)}")
```

**8. Property Format**
```python
logger.log_function_output(f"Library: '{lib_title}' (ID={lib_id})")
logger.log_function_output(f"Download source '{source_id}' (type={source_type}, mode={mode}, dry_run={dry_run})")
```

**9. Test Output Format**
```python
print(f"  OK: {test_name}")
print(f"  FAIL: {test_name}" + (f" -> {details}" if details else ""))
```
Test sections use `===` separators:
```python
print(f"\n{'=' * 60}\n{section_name}\n{'=' * 60}")
```

**10. Test Summary Format**
```python
print(f"SUMMARY: {pass_count}/{test_count} tests passed")
print(f"OK: {ok_count}, FAIL: {fail_count}")
```

### Files Analyzed (36 Python files)

**High logging usage (>40 matches)**:
- `router_crawler_functions_v1.py` (115)
- `routers_v1/crawler.py` (69)
- `test_sharepoint_access_with_app_registration.py` (61)
- `common_sharepoint_functions_v2.py` (58)
- `routers_v2/crawler.py` (50)

**Logging infrastructure**:
- `common_logging_functions_v1.py`
- `common_logging_functions_v2.py`

**Test files**:
- `common_report_functions_v2_test.py`
- `common_sharepoint_functions_v2_test.py`

### Consistency Assessment

**Consistent Patterns**:
- 2-space indentation
- `[ x / n ]` progress format (with spaces)
- `START:/END:` function markers
- `OK./ERROR:/WARNING:` status keywords
- Singular/plural via ternary expression
- Numbers first in result summaries
- `UNKNOWN = '[UNKNOWN]'` constant

**Minor Variations**:
- Some test files use `print()` directly instead of logger
- Section separators: `===` (60 chars) in tests vs `---` (127 chars) in code
- Test summaries: `OK: x, FAIL: y` vs `PASSED: x, FAILED: y`

## PowerShell Logging Analysis (Complete)

### Infrastructure

**Common Include Pattern:** All scripts load `_includes.ps1` with shared functions including `Write-ScriptHeader`, `Write-ScriptFooter`, `Get-DisplayFileSize`.

**Write-Host with Colors:** Primary logging mechanism using `-ForegroundColor` and `-BackgroundColor`.

### Pattern Categories Found

**1. Progress Iteration Format** - Same as Python: `[ x / n ]`
```powershell
Write-Host "Job [ $($jobIndex+1) / $($jobCount) ] '$($url)'"
```

**2. Status Colors:**
- Green = Success/OK
- Yellow = Warning/Empty
- Red = Error (foreground)
- White-on-Red = Critical error
- Cyan = Info/File operations

**3. Section Markers:**
```powershell
#################### START: TOPIC ####################
#################### END: TOPIC ######################
```

**4. Script Header/Footer:**
```
================================================== START: SCRIPT TITLE ==================================================
=================================================== END: SCRIPT TITLE ===================================================
2026-03-04 14:35:23 (5 mins 23 secs)
```

**5. Indentation:** 2 spaces (consistent with Python)

### Files Analyzed (5 PowerShell files, ~3685 lines)

- `SharePointPermissionScanner.ps1` (1034 lines) - Reference
- `ScanOrDeleteFileVersions.ps1` (607 lines)
- `ProcessScanfiles.ps1` (591 lines)
- `ScanSharePointLibrariesFromFile.ps1` (354 lines)
- `01_CopyAndUploadFilesDEV.ps1` (1099 lines)

### Cross-Language Consistency

**Consistent:**
- `[ x / n ]` progress format
- 2-space indentation
- `START:/END:` markers
- `ERROR:/WARNING:` prefixes

**Different:**
- PowerShell uses colors instead of `OK./FAIL:` text
- Duration format: "X mins Y secs" vs Python ms formatting
- Section markers: `#####` vs `# ---`

## IMPORTANT: Cascade Agent Instructions

1. Read `LOGGING-RULES.md` before making changes
2. Maintain backward compatibility with existing MiddlewareLogger
3. Use STRUT plan in PROGRESS.md for execution tracking
4. Document all design decisions

## Document History

**[2026-03-04 14:40]**
- Added PowerShell logging analysis (5 files, ~3685 lines)
- Documented cross-language consistency assessment
- Created _INFO_POWERSHELL_LOGGING_PRACTICES.md [LOG-IN02]

**[2026-03-04 14:25]**
- Completed comprehensive Python logging analysis
- Documented 10 pattern categories with examples
- Created _INFO_V2_LOGGING_PRACTICES.md [LOG-IN01]

**[2026-03-04 14:20]**
- Initial session created
- Created STRUT plan in PROGRESS.md
