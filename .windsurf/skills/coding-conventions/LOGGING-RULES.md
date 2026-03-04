# Logging Rules

Language-agnostic output rules for Python, PowerShell, and future languages.

## Table of Contents

1. [Overview](#overview)
2. [Logging Philosophy](#logging-philosophy)
3. [Philosophy-to-Rules Mapping](#philosophy-to-rules-mapping)
4. [Related Documents](#related-documents)
5. [General Rules (LOG-GN)](#general-rules-log-gn)

## Overview

Four logging types serve distinct audiences with specific patterns.

**Logging Types:**
- **General (GN)** - Rules applying to all output types
- **User-Facing (UF)** - End users monitoring progress via console or Server-Sent Events (SSE) stream
- **App-Level (AP)** - Technical staff debugging and auditing via server logs
- **Test-Level (TS)** - Quality Assurance (QA) verifying correctness via selftest output

## Logging Philosophy

Each logging type has a specific goal that drives its rules.

### Principle of Least Surprise

**Logging should be predictable across all solutions.**

A developer familiar with one codebase should immediately understand logs from another. Same patterns, same formats, same structure. No variations "just because" - consistency enables faster debugging and onboarding.

### Principle of Full Disclosure

**Each log line should be understandable without context.**

Every descriptive line should read like a complete sentence. Include the subject (what), the action (verb), and the target (where/which). A reader scanning logs should not need to look at previous lines to understand the current one.

### Principle of Two-Level Errors (User-Facing)

**Error messages have two parts: defensive summary + exact system message.**

1. **Defensive summary** - Non-technical, no jumping to conclusions. Describes what happened without blaming user or assuming cause.
2. **Exact error** - The actual system error message for technical follow-up, separated by ` -> `.

*BAD:*
```
Could not save user - a user with this email already exists.
Could not save user. Error: A user with this email already exists.
```

*GOOD:*
```
Could not save user -> A user with this email already exists.
Could not connect to site -> (401) Unauthorized
An error occurred while processing the file -> Connection reset by peer
```

### Arrow Convention

**Use ` -> ` as the universal separator for:**
- Error chains: `context -> nested error -> root cause`
- Two-level errors: `summary -> exact error`
- Transformations: `'old_value' -> 'new_value'`

Never use `-`, `:`, or other separators for these patterns.

### Test-Level Goal

**All failure information must be in the logs.**

A QA engineer should understand what failed and why without analyzing additional files, databases, or external data sources. The log output alone must be sufficient to diagnose the problem.

**This goal drives:**
- No timestamps (deterministic output for diff comparison)
- Explicit status markers (`[ok]`, `[fail]`, `[equal]`, `[different]`)
- Complete error context with test case IDs
- Summary with pass/fail counts

### App-Level Goal

**Logs must be human-readable AND machine-parseable.**

A developer unfamiliar with the codebase should understand what happened by reading the logs. Scripts should be able to parse logs with reasonable effort.

**This goal drives:**
- Extended timestamps with process ID and request correlation
- START/END markers showing execution flow
- Nested indentation matching call depth
- Consistent `key='value'` property format
- Error chains preserving full context

### User-Facing Goal

**Users must always know what is happening.**

Progress indication via iteration counters, running totals, and feedback every ~10 seconds for long operations. Users should never wonder if the system is stuck.

**This goal drives:**
- Simple timestamps without technical noise
- Iteration progress `[ x / n ]` at line start
- Running counts during long operations
- Color-coded status (green=OK, red=error)
- Plain language, no jargon

## Philosophy-to-Rules Mapping

Shows how each philosophy goal maps to specific rules.

### Test-Level: "All failure info in logs"

| Goal Requirement | Rule |
|------------------|------|
| Deterministic output | LOG-TS-01: No timestamps |
| Clear pass/fail | LOG-TS-04: Status markers `[ok]`, `[fail]` |
| Traceable failures | LOG-TS-03: Test case IDs (`TC-01:`, `M1:`) |
| Self-contained results | LOG-TS-07: Summary with counts |

### App-Level: "Human-readable AND machine-parseable"

| Goal Requirement | Rule |
|------------------|------|
| Trace requests | LOG-AP-01: Extended timestamp with PID, request N |
| Understand flow | LOG-AP-04: START/END execution boundaries |
| Parse programmatically | LOG-GN-02: `key='value'` property format |
| Debug failures | LOG-AP-05: Error chains with full context |

### User-Facing: "Users always know what is happening"

| Goal Requirement | Rule |
|------------------|------|
| Show progress | LOG-UF-02: Iteration `[ x / n ]`, running counts |
| Feedback timing | LOG-UF-05: Emit every ~10 seconds |
| Clear status | LOG-UF-04: Color conventions (green/red/yellow) |
| Plain language | LOG-UF-03: No jargon, actionable errors |

## Related Documents

- `LOGGING-RULES-USER-FACING.md` - LOG-UF-01 to LOG-UF-06 (6 rules)
- `LOGGING-RULES-APP-LEVEL.md` - LOG-AP-01 to LOG-AP-05 (5 rules)
- `LOGGING-RULES-TEST-LEVEL.md` - LOG-TS-01 to LOG-TS-07 (7 rules)

## General Rules (LOG-GN)

11 rules that apply to ALL logging types. These ensure consistency across user-facing, app-level, and test-level output.

**Rule Index:**
- LOG-GN-01: Indentation (2-space per level)
- LOG-GN-02: Quote paths, names, IDs with single quotes
- LOG-GN-03: Numbers first in result messages
- LOG-GN-04: Duration format (ms, secs, mins, hours)
- LOG-GN-05: Singular/plural correctness
- LOG-GN-06: Property format `key='value'`
- LOG-GN-07: UNKNOWN constant for missing values
- LOG-GN-08: Error formatting (chains, rename, parentheses)
- LOG-GN-09: Log before execution
- LOG-GN-10: Ellipsis usage
- LOG-GN-11: Line endings

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

### LOG-GN-04: Duration Format

Use consistent duration formatting. Measure and report duration for any process >30 seconds.

**Formats:**
- Milliseconds: `245 ms`
- Seconds: `1.5 secs`
- Minutes: `2 mins 30 secs`
- Hours: `1 hour 15 mins`

*BAD*:
```
Completed in 90000ms
Duration: 1.5 minutes
Time: 90 seconds
```

*GOOD*:
```
Completed in 1 min 30 secs.
END: process_batch() (1 min 30 secs).
Duration: 2 hours 15 mins.
```

### LOG-GN-05: Singular/Plural

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

### LOG-GN-06: Property Format

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

### LOG-GN-07: UNKNOWN Constant

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

### LOG-GN-08: Error Formatting

Concatenate nested errors with ` -> `. Include context (paths, IDs) to trace the failure. Also use ` -> ` for rename/transform operations.

**Error chains:**

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

**Rename/transform operations:**
```
Renaming 'site_001' -> 'site_001_archived'...
Moving 'old_folder' -> 'archive/old_folder'...
```

**Additional info in parentheses:**
```
Library 'Documents' (ID=045229b3-57de)
Downloading file 'report.pdf' (size=2.4MB, modified=2026-01-15)
```

### LOG-GN-09: Log Before Execution

Always log what will happen BEFORE starting code that could hang or take long. If it hangs, the last log line shows where.

*BAD*:
```
[nothing logged, then hangs]
Connection established.
```

*GOOD*:
```
Connecting to 'https://sharepoint.com/sites/ProjectA'...
  OK. Connected in 1.2 secs.
Downloading file 'report.pdf' (size=2.4MB)...
  OK.
```

### LOG-GN-10: Ellipsis Usage

Use ellipsis (`...`) for ongoing actions. Never use ellipsis on result lines.

*BAD*:
```
5 files found...
Processing complete...
```

*GOOD*:
```
Processing files...
5 files found.
Processing complete.
```

### LOG-GN-11: Line Endings

Result lines end with period. Ongoing actions end with ellipsis.

*BAD*:
```
Connecting to server
5 files retrieved...
Processing
```

*GOOD*:
```
Connecting to server...
5 files retrieved.
Processing complete.
```

## Complete Example

Showing multiple general rules applied together:

```
Connecting to 'https://sharepoint.com/sites/ProjectA'...
  OK.
Loading libraries...
  3 libraries found.
[ 1 / 3 ] Processing library 'Documents'...
  Scanning files...
  100 items retrieved so far...
  200 items retrieved so far...
  342 files retrieved.
  12 added, 3 changed, 0 removed.
  OK.
[ 2 / 3 ] Processing library 'Reports'...
  Scanning files...
  45 files retrieved.
  ERROR: Failed to process file 'budget.xlsx' -> Access denied -> User lacks read permission
  44 added, 0 changed, 1 error.
[ 3 / 3 ] Processing library 'Archive'...
  Library empty.
  SKIP: No files to process.
Renaming 'site_backup' -> 'site_backup_2026-03-04'...
  OK.
3 libraries processed. 56 added, 3 changed, 1 error.
```
