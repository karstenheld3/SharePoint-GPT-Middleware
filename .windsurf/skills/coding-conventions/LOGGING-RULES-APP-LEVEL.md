# App-Level Logging Rules

Rules for system/debug logging used by technical staff for debugging and auditing.

## Philosophy

**Goal: Logs must be human-readable AND machine-parseable.**

A developer unfamiliar with the codebase should understand what happened by reading the logs. Scripts should be able to parse logs with reasonable effort.

**This goal drives all rules in this document:**
- Extended timestamps with process ID and request correlation (LOG-AP-01)
- Standard log levels (LOG-AP-02)
- Consistent execution pattern (LOG-AP-03)
- START/END markers showing execution flow (LOG-AP-04)
- Error chains preserving full context (LOG-AP-05)

## Related Documents

- `LOGGING-RULES.md` - General rules (LOG-GN-01 to LOG-GN-08)
- `LOGGING-RULES-USER-FACING.md` - User-facing rules (LOG-UF-01 to LOG-UF-06)
- `LOGGING-RULES-TEST-LEVEL.md` - Test-level rules (LOG-TS-01 to LOG-TS-07)

## Rules

### LOG-AP-01: Extended Timestamp Format

Include date, time with milliseconds, process ID, and request correlation.

**Format:** `YYYY-MM-DD HH:MM:SS.mmm [PID:XXXX] [request N]`

**Rationale:** Enables log correlation across processes and requests. Scripts can parse timestamps and filter by process or request.

*BAD*:
```
Starting batch process
10:15:23 Loading configuration
INFO: Processing started
```

*GOOD*:
```
2026-03-04 10:15:23.456 [PID:1234] [request 1] Starting batch process
2026-03-04 10:15:23.457 [PID:1234] [request 1] Loading configuration from 'config.json'
2026-03-04 10:15:23.502 [PID:1234] [request 1] 3 items loaded.
```

**Python server format:**
```
[2026-03-04 14:30:00,process 12345,request 1,crawl_site()] START: crawl_site()...
[2026-03-04 14:30:00,process 12345,request 1,crawl_site()] Site: 'https://contoso.sharepoint.com/sites/ProjectA'
[2026-03-04 14:30:04,process 12345,request 1,crawl_site()] END: crawl_site() (4.2 secs).
```

### LOG-AP-02: Log Levels

Use standard log levels consistently.

- **DEBUG** - Detailed technical information for debugging
- **INFO** - Normal operational messages
- **WARN** - Potential issues that don't stop execution
- **ERROR** - Failures that affect functionality
- **FATAL** - Critical failures requiring immediate attention

*Example*:
```
2026-03-04 10:15:23.456 [PID:1234] [DEBUG] Cache lookup for key='user_prefs'
2026-03-04 10:15:23.457 [PID:1234] [INFO] Starting batch process
2026-03-04 10:15:23.502 [PID:1234] [WARN] Cache miss, regenerating
2026-03-04 10:15:23.510 [PID:1234] [ERROR] Failed to connect to database
2026-03-04 10:15:23.511 [PID:1234] [FATAL] Cannot continue without database
```

### LOG-AP-03: Execution Pattern

Log the action BEFORE executing, then log the result on a 2-space indented line.

**Keywords:**
- `OK.` - Action succeeded (period, no colon)
- `ERROR:` - Error occurred (colon, then message)
- `WARNING:` - Non-fatal issue (colon, then message)
- `FAIL:` - Action failed (colon, then message)
- `SKIP:` - Action skipped (colon, then reason)

*BAD*:
```
File deleted successfully
Upload complete
Connection OK
```

*GOOD*:
```
Deleting file 'temp.csv'...
  OK.
Uploading 'report.pdf' to storage...
  OK.
Connecting to database...
  ERROR: Connection refused -> Server not responding
```

**With details after OK:**
```
Loading configuration...
  OK. 3 items loaded.
Validating inputs...
  OK. All 5 inputs valid.
Processing batch...
  WARNING: 2 items skipped due to missing data.
  12 items processed.
```

### LOG-AP-04: Execution Boundaries

Mark function and script entry/exit with START/END markers.

**Functions:** `START: function()...` / `END: function() [duration]`

```
START: get_document_library_files()...
  Connecting to site...
  Loading library contents...
  Processing 42 items...
END: get_document_library_files() (1.5 secs).
```

**Scripts:** Full boundary with timestamp on separate lines.

**Header width:** 127 characters (same as PYTHON-FT-05 function grouping markers).

```
2026-03-04 14:30:00
================================================== START: SHAREPOINT PERMISSION SCANNER ==================================================
PowerShell: 7.4.1 | PnP.PowerShell: 2.4.0

[script content here]

=================================================== END: SHAREPOINT PERMISSION SCANNER ===================================================
2026-03-04 14:35:23 (5 mins 23 secs)
```

**Nesting:** +2 spaces per nesting level.

```
START: process_site()...
  START: get_libraries()...
    3 libraries found.
  END: get_libraries() (0.5 secs).
  [ 1 / 3 ] Processing 'Documents'...
    START: process_library()...
      42 files found.
    END: process_library() (1.2 secs).
  [ 2 / 3 ] Processing 'Reports'...
    START: process_library()...
      18 files found.
    END: process_library() (0.8 secs).
END: process_site() (4.2 secs).
```

**Duration formats:**
- Milliseconds: `245 ms`
- Seconds: `1.5 secs`
- Minutes: `2 mins 30 secs`
- Hours: `1 hour 15 mins`

**Requirement:** Measure and report duration for any process >30 seconds.

### LOG-AP-05: Error Context

Include all identifiers in error messages to trace individual items. Use arrow chain format for nested errors.

**Chain format:** `context -> nested error`

*BAD*:
```
ERROR: Not found
ERROR: Access denied
ERROR: Failed
```

*GOOD*:
```
ERROR: Failed to process library 'Documents' (site='ProjectA', ID='045229b3') -> HTTPError: 403 Forbidden
ERROR: Upload failed for file 'report.pdf' (path='C:\exports\', size=2.4MB) -> Connection reset by peer
ERROR: Crawl failed for site 'ProjectA' -> HTTPError: 401 Unauthorized -> Token expired
```

**Multi-level chain:**
```
ERROR: Batch processing failed -> Item 'doc_123' failed -> File not found -> '/sites/docs/missing.pdf'
```

**With recovery info:**
```
Processing file 'report.pdf'...
  ERROR: Connection timeout -> Retrying in 5 seconds...
  ( 1 / 3 ) Retry...
  ( 2 / 3 ) Retry...
  OK. Recovered on attempt 3.
```

## Complete Examples

### Example 1: Server Request Processing

```
[2026-03-04 14:30:00,process 12345,request 1,crawl_site()] START: crawl_site()...
[2026-03-04 14:30:00,process 12345,request 1,crawl_site()] Site: url='https://contoso.sharepoint.com/sites/ProjectA' (template=TeamSite)
[2026-03-04 14:30:01,process 12345,request 1,crawl_site()] START: get_libraries()...
[2026-03-04 14:30:02,process 12345,request 1,crawl_site()]   3 libraries found.
[2026-03-04 14:30:02,process 12345,request 1,crawl_site()] END: get_libraries() (1.0 secs).
[2026-03-04 14:30:02,process 12345,request 1,crawl_site()] [ 1 / 3 ] Processing library='Documents'...
[2026-03-04 14:30:03,process 12345,request 1,crawl_site()]   START: process_library()...
[2026-03-04 14:30:04,process 12345,request 1,crawl_site()]     342 files found.
[2026-03-04 14:30:04,process 12345,request 1,crawl_site()]     12 added, 3 changed, 0 removed.
[2026-03-04 14:30:04,process 12345,request 1,crawl_site()]   END: process_library() (1.5 secs).
[2026-03-04 14:30:05,process 12345,request 1,crawl_site()] [ 2 / 3 ] Processing library='Reports'...
[2026-03-04 14:30:06,process 12345,request 1,crawl_site()]   START: process_library()...
[2026-03-04 14:30:07,process 12345,request 1,crawl_site()]     45 files found.
[2026-03-04 14:30:07,process 12345,request 1,crawl_site()]   END: process_library() (1.2 secs).
[2026-03-04 14:30:08,process 12345,request 1,crawl_site()] [ 3 / 3 ] Processing library='Archive'...
[2026-03-04 14:30:08,process 12345,request 1,crawl_site()]   SKIP: Library empty.
[2026-03-04 14:30:08,process 12345,request 1,crawl_site()] 2 libraries processed. 57 added, 3 changed.
[2026-03-04 14:30:08,process 12345,request 1,crawl_site()] END: crawl_site() (8.0 secs).
```

### Example 2: PowerShell Script Execution

```
2026-03-04 14:30:00
================================================== START: SHAREPOINT PERMISSION SCANNER ==================================================
PowerShell: 7.4.1 | PnP.PowerShell: 2.4.0

Reading 'SharePointPermissionScanner-In.csv'...
5 jobs found.

Job [ 1 / 5 ] 'https://contoso.sharepoint.com/sites/ProjectA'
  Connecting to 'https://contoso.sharepoint.com/sites/ProjectA'...
    OK.
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
    152 lines written to: '01_SiteContents.csv'
    OK.
  OK: File '02_SiteGroups.csv' written.

Job [ 2 / 5 ] 'https://contoso.sharepoint.com/sites/ProjectB'
  Connecting to 'https://contoso.sharepoint.com/sites/ProjectB'...
    ERROR: (401) Unauthorized -> Token expired for app registration

=================================================== END: SHAREPOINT PERMISSION SCANNER ===================================================
2026-03-04 14:35:23 (5 mins 23 secs)
```

### Example 3: Nested Function Calls with Errors

```
START: sync_all_data()...
  Loading configuration from 'sync_config.json'...
    OK.
  START: connect_sources()...
    Connecting to source='DatabaseA'...
      OK.
    Connecting to source='DatabaseB'...
      ERROR: Connection refused -> Server 'db2.local' not responding
    Connecting to source='DatabaseC'...
      OK.
    2 of 3 sources connected.
  END: connect_sources() (2.3 secs).
  START: process_source() source='DatabaseA'...
    Loading tables...
      5 tables found.
    [ 1 / 5 ] Processing table='users'...
      523 rows synced.
      OK.
    [ 2 / 5 ] Processing table='orders'...
      ERROR: Failed to sync row ID='ord_789' -> Foreign key violation -> Customer 'cust_456' not found
      1247 rows synced, 1 error.
    [ 3 / 5 ] Processing table='products'...
      892 rows synced.
      OK.
    ...
  END: process_source() (45.2 secs).
  START: process_source() source='DatabaseC'...
    ...
  END: process_source() (32.1 secs).
  SUMMARY: 2 sources processed, 1 skipped. 4521 rows synced, 1 error.
END: sync_all_data() (1 min 22 secs).
```

### Example 4: Error Recovery

```
START: upload_batch()...
  5 files to upload.
  [ 1 / 5 ] Uploading file='report.pdf' (size=2.4MB)...
    ERROR: Connection timeout
    Waiting 5 seconds before retry...
    ( 1 / 3 ) Retrying upload...
    ERROR: Connection timeout
    Waiting 10 seconds before retry...
    ( 2 / 3 ) Retrying upload...
    OK. Uploaded on attempt 3.
  [ 2 / 5 ] Uploading file='data.xlsx' (size=1.2MB)...
    OK.
  [ 3 / 5 ] Uploading file='image.png' (size=0.5MB)...
    OK.
  [ 4 / 5 ] Uploading file='archive.zip' (size=150MB)...
    ERROR: File exceeds maximum size (100MB limit)
    SKIP: File too large.
  [ 5 / 5 ] Uploading file='notes.txt' (size=0.01MB)...
    OK.
  4 files uploaded, 1 skipped.
END: upload_batch() (32.5 secs).
```

### Example 5: Function with Nested Calls

```
[2026-03-04 10:15:23,process 1234,request 1,get_user_permissions()] START: get_user_permissions()...
[2026-03-04 10:15:23,process 1234,request 1,get_user_permissions()] user_id='user_123', site_url='https://contoso.sharepoint.com/sites/ProjectA'
[2026-03-04 10:15:23,process 1234,request 1,get_user_permissions()] Cache miss, fetching from API...
[2026-03-04 10:15:23,process 1234,request 1,get_user_permissions()]   START: fetch_permissions_api()...
[2026-03-04 10:15:23,process 1234,request 1,get_user_permissions()]     3 permission levels found.
[2026-03-04 10:15:23,process 1234,request 1,get_user_permissions()]   END: fetch_permissions_api() (287 ms).
[2026-03-04 10:15:23,process 1234,request 1,get_user_permissions()] Caching result (TTL=300s)...
[2026-03-04 10:15:23,process 1234,request 1,get_user_permissions()]   OK.
[2026-03-04 10:15:23,process 1234,request 1,get_user_permissions()] END: get_user_permissions() (338 ms).
```
