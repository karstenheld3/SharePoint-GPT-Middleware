# Logging Rules

## Table of Contents

1. [Overview](#overview)
2. [Rule Index](#rule-index)
3. [General Rules (GN)](#general-rules-gn)
4. [User-Facing Rules (UF)](#user-facing-rules-uf)
5. [App-Level Rules (AP)](#app-level-rules-ap)
6. [Test-Level Rules (TS)](#test-level-rules-ts)

## Overview

Three distinct logging types serve different audiences and purposes.

**Logging Types:**
- **User-Facing** - End users monitoring progress. Simple timestamps, plain language.
- **App-Level** - Technical staff debugging and auditing. Extended prefixes, parsable format.
- **Test-Level** - Quality Assurance (QA) and developers verifying correctness. No timestamps, status-focused.

**Core Goals:**
- **Clarity** - Easy to understand at a glance
- **Scanability** - Consistent structure enables quick scanning
- **Traceability** - Every output can be traced to its source
- **Parseability** - Machine-readable where needed

## Rule Index

**General (GN)** - Apply to all logging types
- **LOG-GN-01**: 2-space indentation per level
- **LOG-GN-02**: Quote paths, names, and IDs with single quotes
- **LOG-GN-03**: Numbers first in result messages
- **LOG-GN-04**: Singular/plural correctness
- **LOG-GN-05**: Property format `property='value'`
- **LOG-GN-06**: UNKNOWN constant for missing values
- **LOG-GN-07**: Error chain concatenation with ` -> `
- **LOG-GN-08**: Additional info in parentheses

**User-Facing (UF)** - End user output
- **LOG-UF-01**: Simple timestamp format
- **LOG-UF-02**: Progress iteration `[ x / n ]`
- **LOG-UF-03**: Retry format `( x / n )` inline or indented
- **LOG-UF-04**: Plain language status messages
- **LOG-UF-05**: Actionable error messages

**App-Level (AP)** - System/debug logging
- **LOG-AP-01**: Extended timestamp with process ID
- **LOG-AP-02**: Log action before execution
- **LOG-AP-03**: Status keywords on separate line
- **LOG-AP-04**: Function boundaries with START/END
- **LOG-AP-05**: Nested function indentation

**Test-Level (TS)** - Test output
- **LOG-TS-01**: No timestamps
- **LOG-TS-02**: Section headers with visual separators
- **LOG-TS-03**: Section explanations in plain English
- **LOG-TS-04**: Status markers `[equal]`/`[different]`
- **LOG-TS-05**: Status prefixes `OK:`/`WARNING:`/`FAIL:`
- **LOG-TS-06**: Item lists with source line numbers
- **LOG-TS-07**: Summary with specific items listed

## General Rules (GN)

Rules that apply to all logging types.

### LOG-GN-01: Indentation

Use 2 spaces per indent level. Define as a global constant for consistency.

```
INDENT = "  "
```

*Example*:
```
Processing batch...
  Loading configuration...
  Validating inputs...
    3 inputs valid
  Starting work...
```

### LOG-GN-02: Quote Paths, Names, and IDs

Surround file paths, resource names, and identifiers with single quotes.

*BAD*:
```
Processing file report.csv
User admin@company.com not found
Deleting folder C:\temp\data
```

*GOOD*:
```
Processing file 'report.csv'
User 'admin@company.com' not found
Deleting folder 'C:\temp\data'
```

### LOG-GN-03: Numbers First

Start result messages with the count, not the action verb.

*BAD*:
```
Retrieved 5 records
Successfully processed 12 items
Found 3 errors in the file
```

*GOOD*:
```
5 records retrieved
12 items processed successfully
3 errors found in file
```

**Exception**: Activity verbs describing ongoing actions go first.

```
Processing 5 items...
Scanning folder '/documents'...
Uploading 12 files to server...
```

### LOG-GN-04: Singular/Plural

Handle singular and plural correctly. Never use `(s)` shortcuts.

*BAD*:
```
3 file(s) found
1 item(s) processed
0 error(s) detected
```

*GOOD*:
```
3 files found
1 item processed
0 errors detected
```

### LOG-GN-05: Property Format

Use `property_name='value'` format for key-value pairs. This makes logs parseable and values unambiguous.

*BAD*:
```
Loading domain AiSearch from: E:\domains\config.json
Site URL: https://example.com/sites/Test
Source: SharedDocuments
```

*GOOD*:
```
Loading domain='AiSearch' from 'E:\domains\config.json'
Site: url='https://example.com/sites/Test'
Source: id='SharedDocuments'
```

### LOG-GN-06: UNKNOWN Constant

Use a constant for missing or unavailable values. Never use arbitrary defaults or leave None/null visible in logs.

```
UNKNOWN = '[UNKNOWN]'
```

*BAD*:
```
User: None
Library: ''
File ID: ?
Title: Unknown
```

*GOOD*:
```
User: '[UNKNOWN]'
Library: '[UNKNOWN]'
File ID: '[UNKNOWN]'
Title: '[UNKNOWN]'
```

### LOG-GN-07: Error Chain Concatenation

Concatenate nested errors with ` -> `. Include context (paths, IDs) to trace the failure.

*BAD*:
```
Error occurred
Connection refused
Failed
```

*GOOD*:
```
Failed to upload file 'report.pdf' -> Connection refused -> Server timeout after 30s
Processing 'config.json' failed -> JSON parse error -> Unexpected token at line 15
```

### LOG-GN-08: Additional Info in Parentheses

Use parentheses for supplementary information. Primary identifiers can be inline.

**Primary identifier inline**:
```
Deleted file ID=file_xyz789
Processing user 'john@company.com'
```

**Additional info in parentheses**:
```
Library 'Documents' (ID=045229b3-57de)
Downloading file 'report.pdf' (size=2.4MB, modified=2026-01-15)
```

## User-Facing Rules (UF)

Rules for end-user visible output. Must be understandable without technical knowledge.

### LOG-UF-01: Simple Timestamp

Use simple `[HH:MM:SS]` format. No process IDs, no milliseconds, no technical metadata.

*BAD*:
```
2026-03-04 10:15:23.456 [PID:1234] [INFO] Starting scan
```

*GOOD*:
```
[10:15:23] Starting scan...
```

### LOG-UF-02: Progress Iteration

Use `[ x / n ]` format at the start of a line for iteration progress.

```
[ 1 / 5 ] Processing 'Document A'...
[ 2 / 5 ] Processing 'Document B'...
[ 3 / 5 ] Processing 'Document C'...
```

### LOG-UF-03: Retry Format

Use `( x / n )` format for retry attempts. Can be inline or on indented subitem lines.

**Inline**:
```
Connecting to server ( 1 / 3 )...
Connecting to server ( 2 / 3 )...
  Connected successfully
```

**Indented subitem**:
```
Uploading file 'report.pdf'...
  ( 1 / 3 ) Connection timeout, retrying...
  ( 2 / 3 ) Connection timeout, retrying...
  ( 3 / 3 ) Upload successful
```

### LOG-UF-04: Plain Language Status

Use clear, action-oriented language. Avoid technical jargon.

*BAD*:
```
HTTP 200 OK response received
SQLException: constraint violation on PK_Users
Thread pool exhausted, queuing request
```

*GOOD*:
```
Scan complete: 156 users found, 12 groups, 3 issues
Could not save user - a user with this email already exists
Server is busy, your request is queued
```

### LOG-UF-05: Actionable Error Messages

Explain what happened AND what the user can do about it.

*BAD*:
```
Error: Connection refused
Error: ENOENT
Error: 403
```

*GOOD*:
```
Cannot connect to server. Check your internet connection and try again.
File not found. Make sure the file exists and the path is correct.
Access denied. You may not have permission to view this resource.
```

## App-Level Rules (AP)

Rules for system/debug logging. Must be parseable by scripts and provide complete traceability.

### LOG-AP-01: Extended Timestamp

Include date, time with milliseconds, process ID, and log level.

```
2026-03-04 10:15:23.456 [PID:1234] [INFO] Starting batch process
2026-03-04 10:15:23.457 [PID:1234] [DEBUG] Loading configuration from 'config.json'
2026-03-04 10:15:23.502 [PID:1234] [WARN] Cache miss for key 'user_prefs'
2026-03-04 10:15:23.510 [PID:1234] [ERROR] Failed to connect to database
```

**Log Levels**:
- **DEBUG** - Detailed technical information for debugging
- **INFO** - Normal operational messages
- **WARN** - Potential issues that don't stop execution
- **ERROR** - Failures that affect functionality
- **FATAL** - Critical failures requiring immediate attention

### LOG-AP-02: Log Before Execution

Log the action description before executing it, then log the result.

*BAD*:
```
File deleted successfully
Upload complete
```

*GOOD*:
```
Deleting file 'temp.csv'...
  OK.
Uploading 'report.pdf' to storage...
  OK.
```

### LOG-AP-03: Status Keywords

Put status keywords on a separate, indented line.

**Keywords**:
- `OK` - Action succeeded
- `ERROR` - Error occurred
- `FAIL` - Action failed even after mitigation
- `WARNING` - Intermediate error that will be retried

*BAD*:
```
Uploading file... SUCCESS
Downloading... FAILED: Connection timeout
```

*GOOD*:
```
Uploading file 'data.csv'...
  OK.
Downloading file 'report.pdf'...
  ERROR: Connection timeout -> Server not responding
```

### LOG-AP-04: Function Boundaries

Mark function entry/exit with START/END headers. Include duration on END.

```
-------- START: sync_all_data() --------
  Loading sources...
  3 sources loaded
  Processing source 'Database A'...
    42 records synced
  Processing source 'Database B'...
    18 records synced
-------- END: sync_all_data() [2.3 secs] --------
```

### LOG-AP-05: Nested Function Indentation

Each nesting level adds 2 spaces. Depth 1 = 2 spaces, Depth 2 = 4 spaces, etc.

```
-------- START: process_batch() --------
  Loading items...
  -------- START: validate_items() --------
    Checking item 'A'...
      OK.
    Checking item 'B'...
      WARNING: Missing optional field
  -------- END: validate_items() [150ms] --------
  5 items validated
-------- END: process_batch() [1.2 secs] --------
```

## Test-Level Rules (TS)

Rules for test output. Must explain what was tested, what was found, and why it passed or failed.

### LOG-TS-01: No Timestamps

Test output should be deterministic. Timestamps add noise and break diff comparisons.

*BAD*:
```
[10:15:23] Running test_user_creation...
[10:15:24] PASSED
```

*GOOD*:
```
Running test_user_creation...
  OK.
```

### LOG-TS-02: Section Headers

Use visual separators to group related tests or comparisons.

```
========== User Authentication Tests ==========

========== Database Connection Tests ==========

========== API Endpoint Tests ==========
```

### LOG-TS-03: Section Explanations

Add plain-English explanation after each header describing what is being tested.

```
========== User Authentication Tests ==========
Verifying login, logout, and session management for all user roles.

========== Data Export Tests ==========
Comparing exported CSV files against expected output to verify data integrity.
```

### LOG-TS-04: Status Markers

Use `[equal]` and `[different]` for comparison results. Use `[pass]` and `[fail]` for assertions.

```
  [equal] Row count  Expected=14  Actual=14
  [different] Column count  Expected=5  Actual=4
  [pass] All required fields present
  [fail] Missing 'created_date' column
```

### LOG-TS-05: Status Prefixes

Use clear prefixes for final results. No trailing spaces after the colon.

```
OK: All 14 tests passed
WARNING: 12 passed, 2 skipped
FAIL: 3 tests failed
SKIP: Test requires database connection
```

### LOG-TS-06: Item Lists with Line Numbers

Show items on separate lines with source references for traceability.

```
  3 items missing from output:
    Line 8: 'user_alpha@example.com'
    Line 15: 'user_beta@example.com'
    Line 22: 'user_gamma@example.com'
```

### LOG-TS-07: Summary with Items Listed

End with a summary that lists specific items per category.

```
========== Test Summary ==========
15 tests executed ('auth', 'database', 'api', 'export', 'validation'...)
OK: 12 passed ('auth', 'database', 'api', 'validation'...)
WARNING: 2 skipped ('export', 'integration')
FAIL: 1 failed ('stress_test')
Duration: 4.2s
RESULT: FAILED
```

## Complete Examples

### User-Facing Example

```
[10:15:23] Starting data export...
[10:15:24] [ 1 / 3 ] Exporting 'Sales Data'...
[10:15:26] [ 2 / 3 ] Exporting 'Customer List'...
[10:15:27] [ 3 / 3 ] Exporting 'Inventory'...
[10:15:28] Export complete: 3 files created, 1,247 records total
```

### App-Level Example

```
2026-03-04 10:15:23.456 [PID:1234] [INFO] -------- START: export_data() --------
2026-03-04 10:15:23.457 [PID:1234] [DEBUG]   Loading export configuration...
2026-03-04 10:15:23.460 [PID:1234] [DEBUG]     OK.
2026-03-04 10:15:23.461 [PID:1234] [INFO]   Exporting table 'sales' (rows=523)...
2026-03-04 10:15:24.102 [PID:1234] [INFO]     OK.
2026-03-04 10:15:24.103 [PID:1234] [INFO]   Exporting table 'customers' (rows=724)...
2026-03-04 10:15:24.890 [PID:1234] [WARN]     WARNING: 3 records skipped due to encoding issues
2026-03-04 10:15:24.891 [PID:1234] [INFO]     721 records exported.
2026-03-04 10:15:24.892 [PID:1234] [INFO] -------- END: export_data() [1.4 secs] --------
```

### Test-Level Example

```
========== Data Export Validation ==========
Comparing exported CSV against expected output to verify field mapping and data integrity.

  [equal] Row count  Expected=523  Actual=523
  [equal] Column count  Expected=8  Actual=8
  [different] Column 'date_created' format  Expected='YYYY-MM-DD'  Actual='MM/DD/YYYY'

  1 format mismatch found:
    Line 1: Column 'date_created' uses 'MM/DD/YYYY' instead of 'YYYY-MM-DD'

WARNING: Data matches but format differs

========== Test Summary ==========
3 validations run ('row_count', 'column_count', 'format_check')
OK: 2 passed ('row_count', 'column_count')
WARNING: 1 with issues ('format_check')
Duration: 0.3s
RESULT: PASSED WITH WARNINGS
```
