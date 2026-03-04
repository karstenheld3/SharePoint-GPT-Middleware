# User-Facing Logging Rules

Rules for end-user visible output via console or Server-Sent Events (SSE) stream.

## Philosophy

**Goal: Users must always know what is happening.**

Progress indication via iteration counters, running totals, and feedback every ~10 seconds for long operations. Users should never wonder if the system is stuck.

**This goal drives all rules in this document:**
- Simple timestamps without technical noise (LOG-UF-01)
- Iteration progress at line start (LOG-UF-02)
- Plain language, no jargon (LOG-UF-03)
- Color-coded status (LOG-UF-04)
- Feedback timing requirements (LOG-UF-05)
- Context hierarchy display (LOG-UF-06)

## Related Documents

- `LOGGING-RULES.md` - General rules (LOG-GN-01 to LOG-GN-08)
- `LOGGING-RULES-APP-LEVEL.md` - App-level rules (LOG-AP-01 to LOG-AP-05)
- `LOGGING-RULES-TEST-LEVEL.md` - Test-level rules (LOG-TS-01 to LOG-TS-07)

## Rules

### LOG-UF-01: Timestamp Format

Use `[YYYY-MM-DD HH:MM:SS]` format. Always include date AND time. No process ID, no milliseconds.

**Rationale:** Date is essential for log files that span multiple days or are reviewed later. Consistency with app-level logging.

*BAD*:
```
[10:15:23] Starting scan...
2026-03-04 10:15:23.456 [PID:1234] [INFO] Starting scan
[2026-03-04T10:15:23.456Z] Connecting...
10:15:23.456 - Processing files
```

*GOOD*:
```
[2026-03-04 10:15:23] Starting scan...
[2026-03-04 10:15:24] Connecting to site...
[2026-03-04 10:15:25]   3 libraries found.
```

**SSE Stream Format:**
```
[2026-03-04 10:15:23] START: crawl_site()...
[2026-03-04 10:15:24] Site: 'https://contoso.sharepoint.com/sites/ProjectA'
[2026-03-04 10:15:25]   3 libraries found.
[2026-03-04 10:15:30] END: crawl_site() (7.2 secs).
```

### LOG-UF-02: Progress Indicators

**Iteration format:** `[ x / n ]` with spaces, at line start.

```
[ 1 / 5 ] Processing 'Document A'...
[ 2 / 5 ] Processing 'Document B'...
[ 3 / 5 ] Processing 'Document C'...
```

**Retry format:** `( x / n )` inline or as indented subitem.

*Inline:*
```
Connecting to 'https://contoso.sharepoint.com/sites/ProjectA' ( 1 / 3 )...
Connecting to 'https://contoso.sharepoint.com/sites/ProjectA' ( 2 / 3 )...
  OK. Connected to 'https://contoso.sharepoint.com/sites/ProjectA'.
```

*Subitem:*
```
Uploading file 'report.pdf'...
  ( 1 / 3 ) Connection timeout, retrying...
  ( 2 / 3 ) Connection timeout, retrying...
  ( 3 / 3 ) Upload successful.
```

**Running count:** For long operations, show progress during retrieval.

```
100 items retrieved so far...
200 items retrieved so far...
300 items retrieved so far...
342 files retrieved.
```

*Or with ratio:*
```
Retrieved ( 100 / 342 ) items so far...
Retrieved ( 200 / 342 ) items so far...
342 files retrieved.
```

**Waiting:** Show delay reason and attempt count.

```
Waiting 30 seconds ( 1 / 3 ) for rate limit...
Waiting 30 seconds ( 2 / 3 ) for rate limit...
Resuming...
```

### LOG-UF-03: Messages and Results

**Plain language:** No technical jargon. Users should understand without developer knowledge.

*BAD*:
```
HTTP 200 OK response received
SQLException: constraint violation on PK_Users
Thread pool exhausted, queuing request
NullReferenceException at line 245
```

*GOOD:*
```
Scan complete: 156 users found.
Could not save user -> A user with this email already exists.
Request queued -> Server busy, retrying in 30 seconds.
An error occurred while processing request -> Internal server error (500).
```

**Actionable errors:** Two-level format - defensive summary + exact error.

*BAD:*
```
Error: Connection refused
Error: ENOENT
Error: 403
```

*GOOD:*
```
Could not connect to server -> Connection refused
File not found -> ENOENT - No such file or directory
Access denied to resource -> (403) Forbidden
```

**Skipping:** Always explain why items are skipped.

```
Skipping 12 files because they are not embeddable.
Skipping 1 file because it exceeds size limit (>100MB).
Skipping: already up to date.
```

**File operations:** Show what is being written.

```
Writing 152 lines to '01_SiteContents.csv'...
  OK: File '01_SiteContents.csv' written.
Writing 'Summary.csv'...
  OK.
```

**Summary:** Always end with counts.

```
3 libraries processed. 56 added, 3 changed, 1 error.
Export complete: 3 files created, 1,247 records total.
Scan finished: 156 users, 12 groups, 3 issues found.
```

**Multi-line warning:** For destructive operations, show details.

```
IMPORTANT: This script will permanently DELETE all versions
- except for the newest version
- except if the time to the next version is more than 15 minutes
Press any key to continue...
```

### LOG-UF-04: Color Conventions

Color communicates status at a glance. Use consistently.

- **Green** - Success, OK, safe operations
- **Yellow** - Warning, empty results, non-critical issues
- **Red** - Error (recoverable)
- **White-on-Red** - Critical error, destructive warning
- **White-on-Blue** - Important notice, info banner
- **Cyan** - Info, file operations, summaries
- **Gray** - Version info, debug output

**Examples:**

```
  OK: File 'Scanfile-001.csv' written                    [GREEN]
This script will NOT delete versions (testrun).          [GREEN]
WARNING: Cannot resume because 'Summary.csv' not found.  [YELLOW]
    List empty.                                          [YELLOW]
ERROR: Include file not found!                           [RED]
ERROR: Get-PnPGroupMember -Group 'Site Members'          [WHITE on RED]
  Writing 'Summary.csv'...                               [CYAN]
  SUMMARY: 1250 files with 3420 versions...              [CYAN]
PowerShell: 7.4.1 | PnP.PowerShell: 2.4.0                [GRAY]
$performDelete is $true but options are $false.          [WHITE on BLUE]
```

### LOG-UF-05: Feedback Timing

**Requirement:** Emit progress at least every ~10 seconds for long operations.

Users should never wonder if the system is stuck. For operations that might take more than 10 seconds, emit intermediate progress.

*BAD (no feedback for 2 minutes):*
```
[2026-03-04 10:15:23] Starting large file download...
[2026-03-04 10:17:45] Download complete.
```

*GOOD (regular feedback):*
```
[2026-03-04 10:15:23] Starting large file download...
[2026-03-04 10:15:33]   10% downloaded (12MB / 120MB)...
[2026-03-04 10:15:43]   20% downloaded (24MB / 120MB)...
[2026-03-04 10:15:53]   30% downloaded (36MB / 120MB)...
...
[2026-03-04 10:17:45] Download complete. 120MB in 2 mins 22 secs.
```

### LOG-UF-06: Context Display

Show hierarchy to help users understand where they are in the operation.

**Format:** Site > Library > Folder

```
Site: 'https://contoso.sharepoint.com/sites/ProjectA'
  Library: 'Shared Documents'
    Folder: 'Reports/2026'
      Processing 42 files...
```

**With iteration:**
```
Job [ 1 / 5 ] 'https://contoso.sharepoint.com/sites/ProjectA'
  Connecting to site...
  Loading subsites...
  3 subsites found.
    Subsite [ 1 / 3 ] 'https://contoso.sharepoint.com/sites/ProjectA/TeamB'
      4 lists found.
```

## Complete Examples

### Example 1: SharePoint Scan

```
[2026-03-04 14:30:00] START: crawl_site()...
[2026-03-04 14:30:00] Site: 'https://contoso.sharepoint.com/sites/ProjectA'
[2026-03-04 14:30:01]   3 libraries found.
[2026-03-04 14:30:01] [ 1 / 3 ] Processing 'Documents'...
[2026-03-04 14:30:02]   100 items retrieved so far...
[2026-03-04 14:30:03]   200 items retrieved so far...
[2026-03-04 14:30:04]   342 files retrieved.
[2026-03-04 14:30:04]   12 added, 3 changed, 0 removed.
[2026-03-04 14:30:04]   OK.
[2026-03-04 14:30:05] [ 2 / 3 ] Processing 'Reports'...
[2026-03-04 14:30:06]   45 files retrieved.
[2026-03-04 14:30:06]   OK.
[2026-03-04 14:30:07] [ 3 / 3 ] Processing 'Archive'...
[2026-03-04 14:30:07]   Library empty.
[2026-03-04 14:30:07]   SKIP: No files to process.
[2026-03-04 14:30:08] 2 libraries processed. 57 added, 3 changed, 0 removed.
[2026-03-04 14:30:08] END: crawl_site() (8.0 secs).
```

### Example 2: File Upload with Retry

```
[2026-03-04 10:00:00] Uploading 5 files to 'Documents'...
[2026-03-04 10:00:01] [ 1 / 5 ] Uploading 'report.pdf'...
[2026-03-04 10:00:02]   ( 1 / 3 ) Connection timeout, retrying...
[2026-03-04 10:00:05]   ( 2 / 3 ) Connection timeout, retrying...
[2026-03-04 10:00:08]   ( 3 / 3 ) Upload successful.
[2026-03-04 10:00:08] [ 2 / 5 ] Uploading 'data.xlsx'...
[2026-03-04 10:00:09]   OK.
[2026-03-04 10:00:10] [ 3 / 5 ] Uploading 'image.png'...
[2026-03-04 10:00:11]   OK.
[2026-03-04 10:00:12] [ 4 / 5 ] Uploading 'archive.zip'...
[2026-03-04 10:00:13]   ERROR: File too large (>100MB). Skipping.
[2026-03-04 10:00:14] [ 5 / 5 ] Uploading 'notes.txt'...
[2026-03-04 10:00:15]   OK.
[2026-03-04 10:00:15] 4 files uploaded, 1 skipped.
```

### Example 3: Permission Scanner

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
    152 lines written to: '01_SiteContents.csv'
  OK: File '02_SiteGroups.csv' written.
Job [ 2 / 5 ] 'https://contoso.sharepoint.com/sites/ProjectB'
  Connecting to 'https://contoso.sharepoint.com/sites/ProjectB'...
  ERROR: (401) Unauthorized
```

### Example 4: Data Export Summary

```
[2026-03-04 10:15:23] Starting data export...
[2026-03-04 10:15:24] [ 1 / 3 ] Exporting 'Sales Data'...
[2026-03-04 10:15:26]   523 records exported.
[2026-03-04 10:15:26] [ 2 / 3 ] Exporting 'Customer List'...
[2026-03-04 10:15:27]   724 records exported.
[2026-03-04 10:15:28] [ 3 / 3 ] Exporting 'Inventory'...
[2026-03-04 10:15:28]   Skipping 3 items because they have no data.
[2026-03-04 10:15:29]   247 records exported.
[2026-03-04 10:15:29] Export complete: 3 files created, 1,494 records total.
```

### Example 5: Destructive Operation Warning

```
================================================== START: DELETE FILE VERSIONS ==================================================
PowerShell: 7.4.1 | PnP.PowerShell: 2.4.0

IMPORTANT: This script will permanently DELETE all versions
- except for the newest version
- except if the time to the next version is more than 15 minutes
Press any key to continue...

Job [ 1 / 3 ] 'https://contoso.sharepoint.com/sites/Archive'
  Connecting to site...
  Loading document libraries...
  2 libraries found.
  [ 1 / 2 ] Scanning 'Documents'...
    1250 files retrieved.
    Scanning versions...
    SUMMARY: 1250 files with 3420 versions, 892 can be deleted.
    Size: 4.2 GB total (38.5% in versions), 1.1 GB (26.2%) can be deleted.
```
