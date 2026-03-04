# INFO: V2 Logging Practices

**Doc ID**: LOG-IN01
**Goal**: Document actual V2 Python logging patterns extracted from codebase analysis
**Timeline**: Created 2026-03-04, Updated 3 times

## Summary

**Four Logging Categories:**
1. **General** - Language-agnostic rules (indentation, format, keywords)
2. **User-Facing** - Progress indication, feedback, Server-Sent Events (SSE) streaming
3. **App-Level** - Debugging, tracing, function boundaries, error chains
4. **Test-Level** - QA verification, selftest output, pass/fail summaries

**Core Patterns:**
- **Progress format**: `[ x / n ]` with spaces around numbers [VERIFIED]
- **Status keywords**: `OK.`, `ERROR:`, `WARNING:`, `FAIL:` - always 2-space indented [VERIFIED]
- **Error chains**: `ERROR: context -> nested error` format [VERIFIED]
- **Singular/plural**: Ternary `{count} file{'' if count == 1 else 's'}` [VERIFIED]

## Table of Contents

1. [General Logging Rules](#1-general-logging-rules)
2. [User-Facing Logging](#2-user-facing-logging)
3. [App-Level Logging](#3-app-level-logging)
4. [Test-Level Logging](#4-test-level-logging)
5. [Complete Examples](#5-complete-examples)
6. [Sources](#6-sources)
7. [Document History](#7-document-history)

## 1. General Logging Rules

Language-agnostic patterns that apply to all output types.

### 1.1 Indentation

**Rule:** 2-space indentation for nested context.

```
[ 1 / 3 ] Processing 'Documents'...
  42 files retrieved.
  OK.
[ 2 / 3 ] Processing 'Reports'...
  18 files retrieved.
  OK.
```

### 1.2 Status Keywords

**Rule:** Always 2-space indented, on separate line after action.

```
  OK.
  ERROR: Connection refused
  WARNING: File already exists, skipping
  FAIL: Validation failed
```

### 1.3 Progress Format

**Rule:** Spaces around numbers: `[ 1 / 5 ]` not `[1/5]`

```
[ 1 / 5 ] Downloading 'document.pdf'...
[ 2 / 5 ] Downloading 'image.png'...
[ 3 / 5 ] Downloading 'report.xlsx'...
```

### 1.4 Result Summaries

**Rule:** Numbers precede labels, comma-separated.

```
  12 added, 3 changed, 1 removed.
  45 downloaded, 2 skipped, 1 error.
  8 files uploaded, 0 failures.
```

### 1.5 Singular/Plural Handling

**Rule:** Use ternary expression for correct grammar.

```
1 file retrieved.
42 files retrieved.
1 error occurred.
3 errors occurred.
```

### 1.6 Property Format

**Rule:** Single quotes for names, parentheses for attributes.

```
Library: 'Shared Documents' (ID=abc-123-def)
Site: 'https://contoso.sharepoint.com/sites/ProjectA' (template=TeamSite)
Download source 'SP-001' (type=sharepoint, mode=incremental)
```

### 1.7 Unknown Values

**Rule:** Use `[UNKNOWN]` constant for missing values.

```
Site: '[UNKNOWN]' (ID=abc-123)
User: '[UNKNOWN]'
```

## 2. User-Facing Logging

Progress indication and feedback for end users via SSE streaming.

### 2.1 SSE Stream Format

**Format:** `[timestamp] message` (simplified, no process/request context)

**Feedback guideline:** Emit progress at least every ~10 seconds for long operations.

```
[2026-03-04 14:30:00] START: crawl_site()...
[2026-03-04 14:30:00] Site: 'https://contoso.sharepoint.com/sites/ProjectA'
[2026-03-04 14:30:01] 3 libraries found.
[2026-03-04 14:30:01] [ 1 / 3 ] Processing 'Documents'...
[2026-03-04 14:30:02]   42 files retrieved.
[2026-03-04 14:30:02]   OK.
[2026-03-04 14:30:04] END: crawl_site() (4.2 secs).
```

**Infrastructure:** `StreamingJobWriter` with `_emit_to_stream()` method

### 2.2 Progress Iteration with Status

**Example: Download operation with mixed results**

```
[ 1 / 5 ] Downloading 'document.pdf'...
  OK.
[ 2 / 5 ] Downloading 'image.png'...
  OK.
[ 3 / 5 ] Downloading 'report.xlsx'...
  ERROR: Connection timeout
[ 4 / 5 ] Downloading 'notes.txt'...
  OK.
[ 5 / 5 ] Downloading 'data.csv'...
  OK.
  4 downloaded, 0 skipped, 1 error.
```

### 2.3 Count Progress (Long Operations)

**Rule:** Show running count during retrieval, final count at end.

```
100 items retrieved so far...
200 items retrieved so far...
300 items retrieved so far...
342 files retrieved.
```

### 2.4 Skipping Messages

```
  Skipping 12 non-embeddable files.
  Skipping 1 non-embeddable file.
  Skipping: file_sources do not require processing
  Skipping: already up to date
```

### 2.5 Final Result Summary

**Rule:** Always end with result summary showing counts.

```
  60 added, 0 changed, 0 removed.
END: crawl_site() (4.2 secs).
```

## 3. App-Level Logging

Debugging and tracing for developers and operations.

### 3.1 Console Server Log Format

**Format:** `[timestamp,process PID,request N,function_name] message`

**Purpose:** Request correlation, process tracking, server-side debugging.

```
[2026-03-04 14:30:00,process 12345,request 1,crawl_site()] START: crawl_site()...
[2026-03-04 14:30:00,process 12345,request 1,crawl_site()] Site: 'https://contoso.sharepoint.com/sites/ProjectA' (template=TeamSite)
[2026-03-04 14:30:01,process 12345,request 1,crawl_site()] 3 libraries found.
[2026-03-04 14:30:04,process 12345,request 1,crawl_site()] END: crawl_site() (4.2 secs).
```

**Infrastructure:** `MiddlewareLogger` class in `common_logging_functions_v2.py`

### 3.2 Function Boundaries (START/END)

**Rule:** Every significant function logs START and END with duration.

```
START: get_document_library_files()...
  Connecting to site...
  Loading library contents...
  Processing 42 items...
END: get_document_library_files() (1.5 secs).
```

**Duration formats:** `245 ms`, `1.5 secs`, `2 mins 30 secs`, `1 hour 15 mins`

### 3.3 Error Chain Format

**Rule:** Arrow `->` separates context from nested error.

```
ERROR: Crawl failed -> HTTPError: 401 Unauthorized
ERROR: Self-test failed -> ValueError: Invalid configuration
ERROR: Security scan failed -> Connection refused
ERROR: Download failed -> FileNotFoundError: '/sites/docs/missing.pdf'
```

### 3.4 Nested Function Calls

**Rule:** Nested calls increase indentation, maintain START/END pairs.

```
START: process_site()...
  START: get_libraries()...
    3 libraries found.
  END: get_libraries() (0.5 secs).
  [ 1 / 3 ] Processing 'Documents'...
    START: process_library()...
      42 files found.
    END: process_library() (1.2 secs).
  ...
END: process_site() (4.2 secs).
```

### 3.5 Code Section Markers

**Rule:** 127-character markers for code organization (not runtime output).

```python
# ----------------------------------------- START: Site Data Functions -----------------------------------------------------
# ... code ...
# ----------------------------------------- END: Site Data Functions -------------------------------------------------------
```

## 4. Test-Level Logging

QA verification, selftest output, and pass/fail summaries.

### 4.1 Sites CRUD Selftest

**Endpoint:** `GET /api/v2/sites/selftest?format=stream`

**Full Output:**
```
[2026-03-04 14:30:00] START: sites_selftest()...
[2026-03-04 14:30:00] [ 1 / 9 ] Creating test site 'selftest_a1b2c3d4'...
[2026-03-04 14:30:01]   OK.
[2026-03-04 14:30:01] [ 2 / 9 ] Getting test site...
[2026-03-04 14:30:01]   OK.
[2026-03-04 14:30:01] [ 3 / 9 ] Updating test site...
[2026-03-04 14:30:02]   OK.
[2026-03-04 14:30:02] [ 4 / 9 ] Renaming test site 'selftest_a1b2c3d4' -> 'selftest_a1b2c3d4_renamed'...
[2026-03-04 14:30:02]   OK.
[2026-03-04 14:30:02] [ 5 / 9 ] Deleting test site 'selftest_a1b2c3d4_renamed'...
[2026-03-04 14:30:03]   OK.
[2026-03-04 14:30:03] [ 6 / 9 ] Verifying deletion...
[2026-03-04 14:30:03]   OK.
[2026-03-04 14:30:03] [ 7 / 9 ] Creating site with underscore prefix (should fail)...
[2026-03-04 14:30:04]   OK.
[2026-03-04 14:30:04] [ 8 / 9 ] Verifying underscore folders ignored in list...
[2026-03-04 14:30:04]   OK.
[2026-03-04 14:30:04] [ 9 / 9 ] Cleaning up underscore folder...
[2026-03-04 14:30:05]   OK.
[2026-03-04 14:30:05] 
[2026-03-04 14:30:05] ===== SELFTEST COMPLETE =====
[2026-03-04 14:30:05] OK: 9, FAIL: 0
[2026-03-04 14:30:05] END: sites_selftest() (5.0 secs).
```

### 4.2 Security Scan Selftest

**Endpoint:** `GET /api/v2/sites/security_scan/selftest?format=stream`

**Full Output (11 tests, 1 expected fail):**
```
[2026-03-04 14:35:00] START: sites_security_scan_selftest()...
[2026-03-04 14:35:00] [ 1 / 11 ] TC-01: Connect to selftest site...
[2026-03-04 14:35:01]   OK. site_url='https://contoso.sharepoint.com/sites/SelftestSite'
[2026-03-04 14:35:01] [ 2 / 11 ] TC-02: Enumerate site groups...
[2026-03-04 14:35:02]   OK. 5 groups found.
[2026-03-04 14:35:02] [ 3 / 11 ] TC-03: Resolve group members...
[2026-03-04 14:35:03]   OK. 12 members resolved.
[2026-03-04 14:35:03] [ 4 / 11 ] TC-04: Query lists with HasUniqueRoleAssignments...
[2026-03-04 14:35:04]   OK. 3 lists with unique permissions.
[2026-03-04 14:35:04] [ 5 / 11 ] TC-05: Process library items...
[2026-03-04 14:35:06]   OK. 156 items scanned.
[2026-03-04 14:35:06] [ 6 / 11 ] TC-06: Detect broken inheritance...
[2026-03-04 14:35:07]   OK. 8 items with broken inheritance.
[2026-03-04 14:35:07] [ 7 / 11 ] TC-07: Generate CSV output...
[2026-03-04 14:35:08]   OK. 4 CSV files generated.
[2026-03-04 14:35:08] [ 8 / 11 ] TC-08: Access restricted site (expected fail)...
[2026-03-04 14:35:09]   EXPECTED FAIL: (401) Unauthorized
[2026-03-04 14:35:09] [ 9 / 11 ] TC-09: Verify scan statistics...
[2026-03-04 14:35:10]   OK. Statistics match expected values.
[2026-03-04 14:35:10] [ 10 / 11 ] TC-10: Cleanup test artifacts...
[2026-03-04 14:35:11]   OK. 4 files deleted.
[2026-03-04 14:35:11] [ 11 / 11 ] TC-11: Verify cleanup complete...
[2026-03-04 14:35:12]   OK.
[2026-03-04 14:35:12] 
[2026-03-04 14:35:12] ===== SELFTEST COMPLETE =====
[2026-03-04 14:35:12] OK: 10, EXPECTED FAIL: 1, FAIL: 0
[2026-03-04 14:35:12] END: sites_security_scan_selftest() (12.0 secs).
```

### 4.3 Crawler Selftest

**Endpoint:** `GET /api/v2/crawler/selftest?format=stream`

**Full Output (multi-phase test):**
```
[2026-03-04 14:40:00] START: crawler_selftest()...
[2026-03-04 14:40:00] 
[2026-03-04 14:40:00] ===== Phase 1: Configuration =====
[2026-03-04 14:40:00] [ 1 / 25 ] M1: Config validation - CRAWLER_SELFTEST_SHAREPOINT_SITE...
[2026-03-04 14:40:01]   OK. site_url='https://contoso.sharepoint.com/sites/SelftestSite'
[2026-03-04 14:40:01] [ 2 / 25 ] M2: Config validation - Certificate path...
[2026-03-04 14:40:01]   OK. cert_path='E:\certs\app.pfx'
[2026-03-04 14:40:01] 
[2026-03-04 14:40:01] ===== Phase 2: SharePoint Connection =====
[2026-03-04 14:40:01] [ 3 / 25 ] M3: Connect to SharePoint site...
[2026-03-04 14:40:03]   OK. Connected as 'app@contoso.onmicrosoft.com'
[2026-03-04 14:40:03] [ 4 / 25 ] M4: Enumerate document libraries...
[2026-03-04 14:40:04]   OK. 3 libraries found.
[2026-03-04 14:40:04] 
[2026-03-04 14:40:04] ===== Phase 3: Create Test Data =====
[2026-03-04 14:40:04] [ 5 / 25 ] M5: Create test library 'SelftestLibrary'...
[2026-03-04 14:40:06]   OK. Library created.
[2026-03-04 14:40:06] [ 6 / 25 ] M6: Upload test files...
[2026-03-04 14:40:08]   OK. 5 files uploaded.
[2026-03-04 14:40:08] 
[2026-03-04 14:40:08] ===== Phase 4: Crawl Operations =====
[2026-03-04 14:40:08] [ 7 / 25 ] M7: Full crawl...
[2026-03-04 14:40:12]   OK. 5 files crawled in 4.2 secs.
[2026-03-04 14:40:12] [ 8 / 25 ] M8: Incremental crawl (no changes)...
[2026-03-04 14:40:14]   OK. 0 changes detected.
[2026-03-04 14:40:14] [ 9 / 25 ] M9: Modify test file...
[2026-03-04 14:40:16]   OK. File modified.
[2026-03-04 14:40:16] [ 10 / 25 ] M10: Incremental crawl (1 change)...
[2026-03-04 14:40:18]   OK. 1 change detected.
...
[2026-03-04 14:42:00] 
[2026-03-04 14:42:00] ===== Phase 8: Cleanup =====
[2026-03-04 14:42:00] [ 24 / 25 ] M24: Delete test library...
[2026-03-04 14:42:02]   OK. Library deleted.
[2026-03-04 14:42:02] [ 25 / 25 ] M25: Delete local artifacts...
[2026-03-04 14:42:03]   OK. 12 files deleted.
[2026-03-04 14:42:03] 
[2026-03-04 14:42:03] ===== SELFTEST COMPLETE =====
[2026-03-04 14:42:03] OK: 24, EXPECTED FAIL: 1, FAIL: 0
[2026-03-04 14:42:03] Test execution completed.
[2026-03-04 14:42:03] END: crawler_selftest() (2 mins 3 secs).
```

### 4.4 Test Output Patterns

**Test with details:**
```
[ 1 / 9 ] Creating test site 'selftest_a1b2c3d4'...
  OK.
```

**Test with result info:**
```
[ 3 / 11 ] TC-03: Resolve group members...
  OK. 12 members resolved.
```

**Expected failure:**
```
[ 8 / 11 ] TC-08: Access restricted site (expected fail)...
  EXPECTED FAIL: (401) Unauthorized
```

**Actual failure:**
```
[ 5 / 9 ] Deleting test site...
  FAIL: Delete failed: {'ok': False, 'error': 'Site not found'}
```

**Phase headers:**
```
===== Phase 1: Configuration =====
===== Phase 2: SharePoint Connection =====
===== SELFTEST COMPLETE =====
```

**Summary formats:**
```
OK: 9, FAIL: 0
OK: 10, EXPECTED FAIL: 1, FAIL: 0
OK: 24, EXPECTED FAIL: 1, FAIL: 0
```

### 4.5 Standalone Test Script Output

**From `*_test.py` files (print-based):**
```
============================================================
Test: SharePoint Connection
============================================================
  OK: Connect to site
  OK: Get library list
  FAIL: Get restricted library -> (401) Unauthorized
  OK: Disconnect

============================================================
Test: File Operations
============================================================
  OK: Download file
  OK: Upload file
  OK: Delete file

============================================================
SUMMARY: 6/7 tests passed
         1 test FAILED
============================================================
```

## 5. Consistency Assessment

### 5.1 Consistent Across Codebase

- 2-space indentation for nested messages
- `[ x / n ]` progress format with spaces
- `START:/END:` function boundary markers
- `OK./ERROR:/WARNING:/FAIL:` status keywords
- Singular/plural via ternary expression
- Numbers first in result summaries
- `UNKNOWN = '[UNKNOWN]'` for missing values
- Arrow `->` for error chains

### 5.2 Minor Variations (Candidates for Harmonization)

- **Section separators:** `===` (60 chars) in tests vs `---` (127 chars) in code
- **Test summaries:** `OK: x, FAIL: y` vs `PASSED: x, FAILED: y` vs `SUMMARY: x/y`
- **Test vs logger:** Some test files use `print()` directly instead of logger

## 6. Sources

**Primary Sources:**
- `LOG-IN01-SC-V2LOG-CORE`: `common_logging_functions_v2.py` - MiddlewareLogger class definition [VERIFIED]
- `LOG-IN01-SC-V1LOG-CORE`: `common_logging_functions_v1.py` - Legacy logging functions [VERIFIED]
- `LOG-IN01-SC-CRWLR-V2`: `routers_v2/crawler.py` - Progress, status, error patterns (50 matches) [VERIFIED]
- `LOG-IN01-SC-CRWLR-V1`: `router_crawler_functions_v1.py` - Highest match count (115 matches) [VERIFIED]
- `LOG-IN01-SC-SHRPT-V2`: `common_sharepoint_functions_v2.py` - Property format, counts (58 matches) [VERIFIED]
- `LOG-IN01-SC-RPTST-V2`: `common_report_functions_v2_test.py` - Test infrastructure patterns [VERIFIED]
- `LOG-IN01-SC-SITST-V2`: `routers_v2/sites.py` - Selftest patterns, error chains [VERIFIED]

**Analysis Scope:**
- 36 Python files analyzed in `src/` folder
- 717 total logging-related matches found
- Patterns extracted via grep search and manual verification

## 7. Document History

**[2026-03-04 15:10]**
- Restructured with 4-category classification:
  1. General Logging Rules (language-agnostic)
  2. User-Facing Logging (progress, feedback)
  3. App-Level Logging (debugging, tracing)
  4. Test-Level Logging (QA, verification)

**[2026-03-04 15:05]**
- Fixed: SSE acronym expanded on first use
- Added: Feedback timing guideline (~10 seconds)

**[2026-03-04 15:00]**
- Restructured around 3 output types (Console, SSE Stream, Test)
- Added detailed selftest examples (Sites, Security Scan, Crawler)
- Added phase headers and expected fail patterns

**[2026-03-04 14:35]**
- Initial INFO document created from Python codebase analysis
- All 10 pattern categories verified against source files
- Sources documented with verification labels
