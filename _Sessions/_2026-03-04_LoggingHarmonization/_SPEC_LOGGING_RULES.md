# SPEC: Logging Rules Documentation

**Doc ID**: LOG-SP01
**Goal**: Define exhaustive logging output rules for the coding-conventions skill
**Timeline**: Created 2026-03-04, Updated 0 times
**Target files**: `.windsurf/skills/coding-conventions/LOGGING-RULES.md`, `LOGGING-RULES-USER-FACING.md`, `LOGGING-RULES-APP-LEVEL.md`, `LOGGING-RULES-TEST-LEVEL.md`

**Depends on:**
- `_INFO_V2_LOGGING_PRACTICES.md [LOG-IN01]` for Python logging patterns
- `_INFO_POWERSHELL_LOGGING_PRACTICES.md [LOG-IN02]` for PowerShell logging patterns

## MUST-NOT-FORGET

- Output-only rules (no internal implementation details)
- Language-agnostic (Python, PowerShell patterns harmonized)
- Every rule needs BAD/GOOD examples
- Complete examples at end of each document

## Table of Contents

1. [Scenario](#1-scenario)
2. [Logging Philosophy](#2-logging-philosophy)
3. [Domain Objects](#3-domain-objects)
4. [Functional Requirements](#4-functional-requirements)
5. [Design Decisions](#5-design-decisions)
6. [File Structure](#6-file-structure)
7. [Rule Inventory](#7-rule-inventory)
8. [Document History](#8-document-history)

## 1. Scenario

**Problem:** Current `LOGGING-RULES.md` (538 lines) is incomplete and mixes all logging types in one file. Missing patterns discovered in INFO documents:
- OK/FAIL/WARNING status patterns not fully documented
- Expected fail pattern missing
- Phase headers missing
- Test case ID prefixes missing
- Running count progress missing
- Color conventions missing
- Logging philosophy not documented

**Solution:**
- Split into 4 focused documents
- Add all patterns from INFO documents
- Document logging philosophy (WHY behind rules)
- Exhaustive BAD/GOOD examples for each rule
- Complete output examples showing all rules applied

**What we don't want:**
- Internal implementation details (code section markers, function signatures)
- Language-specific implementation (keep rules language-agnostic)
- Markdown tables in examples
- Short examples that don't show edge cases

## 2. Logging Philosophy

**Test-Level Goal:** All failure information must be in the logs. A QA engineer should understand what failed and why without analyzing additional files, databases, or external data sources. The log output alone must be sufficient to diagnose the problem.

**App-Level Goal:** Logs must be human-readable without knowing the full system architecture. A developer unfamiliar with the codebase should understand what happened by reading the logs. Use nested indentation, spelled-out function names, and START/END markers to show execution flow. Logs must also be parseable by scripts with reasonable effort (consistent format, predictable structure).

**User-Facing Goal:** Progress indication via indentation, iteration counters `[ x / n ]`, and running totals. Emit feedback at least every 10 seconds for long operations so users know the system is working. Always show START/END markers and final result summary with counts.

## 3. Domain Objects

### Logging Type

A **Logging Type** defines output for a specific audience.

**Types:**
- `General` - Rules applying to all types
- `User-Facing` - End users monitoring progress
- `App-Level` - Technical staff debugging
- `Test-Level` - QA verifying correctness

### Rule

A **Rule** defines a specific output pattern.

**Properties:**
- `id` - Unique identifier (LOG-GN-01, LOG-UF-01, etc.)
- `title` - Short descriptive name
- `statement` - What the rule requires
- `rationale` - Why this matters
- `bad_examples` - 3-5 incorrect variations
- `good_examples` - 3-5 correct variations
- `edge_cases` - Special situations

### Status Keyword

A **Status Keyword** indicates operation result.

**Keywords:**
- `OK` - Action succeeded (period after)
- `ERROR` - Error occurred (colon, then message)
- `WARNING` - Non-fatal issue (colon, then message)
- `FAIL` - Action failed (colon, then message)
- `SKIP` - Action skipped (colon, then reason)
- `EXPECTED FAIL` - Expected failure occurred (colon, then details)

## 4. Functional Requirements

**LOG-FR-01: File Structure**
- 4 separate files in `coding-conventions` skill folder
- `LOGGING-RULES.md` contains general rules + index to other files
- Type-specific files contain only that type's rules

**LOG-FR-02: Rule Format**
- Every rule has unique ID
- Every rule has BAD examples (minimum 3)
- Every rule has GOOD examples (minimum 3)
- Edge cases documented where applicable

**LOG-FR-03: Complete Examples**
- Each type-specific file ends with complete examples
- Examples show multiple rules applied together
- Examples are realistic (based on actual codebase output)

**LOG-FR-04: Cross-References**
- General rules referenced in type-specific files where relevant
- Rule IDs used consistently across documents

**LOG-FR-05: Output-Only Focus**
- No implementation code in rules
- No function signatures
- No internal patterns (code section markers, etc.)
- Only what appears in console/logs/streams

## 5. Design Decisions

**LOG-DD-01:** Split into 4 files. Rationale: Each logging type has distinct audience and patterns. Single file would be 2000+ lines.

**LOG-DD-02:** Rule IDs use prefix per type (GN, UF, AP, TS). Rationale: Enables cross-referencing and quick identification.

**LOG-DD-03:** BAD examples before GOOD. Rationale: Shows what to avoid first, then correct approach.

**LOG-DD-04:** Complete examples at document end. Rationale: After learning rules, see them applied together.

**LOG-DD-05:** Language-agnostic rules. Rationale: Same output patterns apply to Python, PowerShell, and future languages.

## 6. File Structure

```
.windsurf/skills/coding-conventions/
├── LOGGING-RULES.md (~380 lines)
│   ├── Overview (types, audiences, goals)
│   ├── Logging Philosophy
│   ├── Master Rule Index (all files)
│   └── LOG-GN-01 to LOG-GN-11 (General Rules)
│
├── LOGGING-RULES-USER-FACING.md (~350 lines)
│   ├── Audience description
│   ├── LOG-UF-01 to LOG-UF-06
│   └── Complete Examples (5)
│
├── LOGGING-RULES-APP-LEVEL.md (~350 lines)
│   ├── Audience description
│   ├── LOG-AP-01 to LOG-AP-05
│   └── Complete Examples (5)
│
└── LOGGING-RULES-TEST-LEVEL.md (~400 lines)
    ├── Audience description
    ├── LOG-TS-01 to LOG-TS-07
    └── Complete Examples (7)
```

## 7. Rule Inventory

### General Rules (LOG-GN) - 11 rules

**LOG-GN-01: Indentation**
- 2-space per nesting level
- Consistent across all output

**LOG-GN-02: Value Formatting**
- **Quoting**: Single quotes for user-provided or variable values:
  - File paths: `'C:\reports\data.csv'`
  - File names: `'report.pdf'`
  - URLs: `'https://example.com/sites/ProjectA'`
  - Resource names: `'Shared Documents'`, `'Site Members'`
  - User identifiers: `'admin@company.com'`
  - GUIDs/IDs in context: `'045229b3-57de-49ce'`
  - Column names when referencing data: `'LoginName'`, `'Title'`
- **Properties**: `key='value'` syntax for parseable output
- **Parentheses**: Additional info in parentheses, primary identifier inline
- **UNKNOWN**: Use `'[UNKNOWN]'` for missing values (never None/null/empty)

**LOG-GN-03: Number Formatting**
- **Numbers first**: Result messages start with count (exception: ongoing actions)
- **Singular/plural**: Correct grammar (0 items, 1 item, 2 items), never use `(s)`
- **Counts**: "X items found." / "X items so far..." / "X added, Y changed, Z removed."

**LOG-GN-04: Duration Format**
- Milliseconds: "245 ms"
- Seconds: "1.5 secs"
- Minutes: "2 mins 30 secs"
- Hours: "1 hour 15 mins"
- **Requirement**: Measure and report duration for any process >30 seconds

**LOG-GN-05: Error Formatting**
- **Chain**: Use ` -> ` separator, preserve context through chain
  - Example: `ERROR: Failed to upload 'data.csv' -> Connection timeout -> Server not responding`
  - Example: `ERROR: Crawl failed for site 'ProjectA' -> HTTPError: 401 Unauthorized`
- **Rename/transform**: Use ` -> ` for before/after
  - Example: `Renaming 'site_001' -> 'site_001_archived'...`
- **Self-contained**: Include identifiers (file names, IDs, URLs) in error message
- BAD: "ERROR: Not found"
- GOOD: "ERROR: File 'report.pdf' not found in library 'Documents' (site='ProjectA')"

**LOG-GN-06: Log Before Execution**
- Always log what will happen BEFORE starting code that could hang or take long
- If it hangs, the last log line shows where
- Example: `Connecting to 'https://sharepoint.com/sites/ProjectA'...` (then connect)
- Example: `Downloading file 'report.pdf' (size=2.4MB)...` (then download)

**LOG-GN-07: Ellipsis**
- Ongoing action: "Processing..."
- Never on result lines

**LOG-GN-08: Line Endings**
- Result lines end with period
- Ongoing actions end with ellipsis

### User-Facing Rules (LOG-UF) - 6 rules

**LOG-UF-01: Timestamp Format**
- Simple: `[HH:MM:SS]` (no date, no PID, no milliseconds)
- SSE stream: `[HH:MM:SS]` message (no request context)

**LOG-UF-02: Progress Indicators**
- **Iteration**: `[ x / n ]` with spaces at line start
- **Retry**: `( x / n )` inline or indented
  - Inline: `Connecting to server ( 1 / 3 )...`
  - Subitem: 
    ```
    Uploading file 'report.pdf'...
      ( 1 / 3 ) Connection timeout, retrying...
      ( 2 / 3 ) Connection timeout, retrying...
      ( 3 / 3 ) Upload successful
    ```
- **Running count**: "Retrieved ( x / y ) items so far..." or "X items retrieved so far..."
- **Waiting**: "Waiting X seconds ( 1 / 2 ) for retry..."

**LOG-UF-03: Messages & Results**
- **Plain language**: No technical jargon
- **Actionable errors**: What happened + how to fix
- **Skipping**: "Skipping X items because <reason>."
- **File operations**: "Writing X lines to '...'..." / "OK: File '...' written"
- **Summary**: Always end with counts
- **Multi-line warning**: For destructive operations, show details + "Press any key..."

**LOG-UF-04: Color Conventions**
- Green = Success, OK, safe operations
- Yellow = Warning, empty results, non-critical
- Red = Error (recoverable)
- White-on-Red = Critical error, destructive warning
- White-on-Blue = Important notice, info banner
- Cyan = Info, file operations, summaries
- Gray = Version info, debug output

**LOG-UF-05: Feedback Timing**
- Emit progress every ~10 seconds for long operations

**LOG-UF-06: Context Display**
- Show hierarchy: Site > Library > Folder

### App-Level Rules (LOG-AP) - 5 rules

**LOG-AP-01: Extended Timestamp**
- Format: `YYYY-MM-DD HH:MM:SS.mmm [PID:XXXX]`
- Request correlation: `[request N]` for multi-request tracing

**LOG-AP-02: Log Levels**
- DEBUG, INFO, WARN, ERROR, FATAL

**LOG-AP-03: Execution Pattern**
- Log action before executing
- Status keyword on separate 2-space indented line
- Keywords: `OK.`, `ERROR:`, `WARNING:`, `FAIL:`, `SKIP:`

**LOG-AP-04: Execution Boundaries**
- **Functions**: `START: function()...` / `END: function() [duration]`
- **Scripts**: 
  - Timestamp on separate line before START
  - `===...=== START: TITLE ===...===`
  - Version info after header (e.g., `PowerShell: 7.4.1 | PnP.PowerShell: 2.4.0`)
  - `===...=== END: TITLE ===...===`
  - Timestamp + duration on separate line after END
- **Nesting**: +2 spaces per level

**LOG-AP-05: Error Context**
- Chain format: `context -> nested error`
- Include all identifiers to trace individual items
- Example: `ERROR: Failed to process library 'Documents' (site='ProjectA', ID='045229b3') -> HTTPError: 403 Forbidden`
- Example: `ERROR: Upload failed for file 'report.pdf' (path='C:\exports\', size=2.4MB) -> Connection reset by peer`

### Test-Level Rules (LOG-TS) - 7 rules

**LOG-TS-01: No Timestamps**
- Test output must be deterministic for diff comparison

**LOG-TS-02: Section Structure**
- **Section header**: `========== Title ==========`
- **Phase header**: `===== Phase N: Name =====`
- **Explanation**: Plain English after header

**LOG-TS-03: Test Case IDs**
- Prefix format: `TC-01:`, `M1:`, etc.

**LOG-TS-04: Status Markers**
- Comparison: `[equal]`, `[different]`
- Assertion: `[ok]`, `[fail]`

**LOG-TS-05: Status Patterns**
- `OK.` or `OK. details`
- `FAIL: message` or `FAIL: context -> error`
- `WARNING: message`
- `EXPECTED FAIL: (code) message`
- `SKIP: reason`

**LOG-TS-06: Output Details**
- **Item lists**: `Line X: 'value'`
- **Comparison**: Row/column counts, differences

**LOG-TS-07: Summary & Result**
- **Summary**: `OK: X, FAIL: Y` or `OK: X, EXPECTED FAIL: Y, FAIL: Z`
- **Final**: `RESULT: PASSED` / `PASSED WITH WARNINGS` / `FAILED`

## 8. Document History

**[2026-03-04 15:53]**
- Changed: General rules expanded from 8 to 11 (implementation verification)
- Added: LOG-GN-04 Duration Format
- Added: LOG-GN-09 Log Before Execution
- Added: LOG-GN-10 Ellipsis Usage
- Added: LOG-GN-11 Line Endings

**[2026-03-04 15:39]**
- Added: White-on-Blue color (LOG-UF-04)
- Added: File operation messages (LOG-UF-03)
- Added: Multi-line warning pattern (LOG-UF-03)
- Added: Rename/transform arrow format (LOG-GN-05)
- Changed: Script boundaries with timestamp before/after (LOG-AP-04)

**[2026-03-04 15:27]**
- Changed: Consolidated 51 rules into 26 rules (multi-example format)
- GN: 12 -> 7, UF: 14 -> 7, AP: 10 -> 5, TS: 15 -> 7

**[2026-03-04 15:26]**
- Added: LOG-UF-14 (Waiting/Delay Messages)
- Added: LOG-AP-10 (Script Boundaries)
- Changed: Rule counts (UF: 14, AP: 10, total: 51)

**[2026-03-04 15:23]**
- Removed: Security Goal (not requested by user)
- Changed: Rule counts (GN: 12, UF: 13, total: 49)

**[2026-03-04 15:21]**
- Added: Logging Philosophy section (Test-Level, App-Level, User-Facing goals)
- Added: LOG-GN-12 (Self-Contained Errors)
- Added: LOG-UF-13 (SSE Stream Format)
- Changed: LOG-UF-09 expanded with all color conventions including White-on-Red

**[2026-03-04 15:15]**
- Initial specification created
- 47 rules defined across 4 categories
- File structure defined
