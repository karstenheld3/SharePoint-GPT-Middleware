
# Run Tests Workflow

Discovers and runs all test files (Python + HTTP selftests), generates a timestamped test summary report.

## Prerequisites

1. Working directory is workspace root
2. Python virtual environment available at `.venv/`

## CRITICAL: No Temporary Files

**NEVER create temporary files of ANY kind:**
- No `.ps1` or `.sh` script files
- No `.json` result files (like `.temp_test_results.json`)
- No intermediate data files

**Store all data in PowerShell variables.** Run all commands inline. Delete any temp files you find.

## Workflow Steps

### Step 0: Server Setup

**0.1 Extract server URL from `.vscode/launch.json`:**

Read the launch.json and extract `--host` and `--port` from the args array:

```powershell
$json = Get-Content ".vscode/launch.json" | ConvertFrom-Json
$argsArray = $json.configurations[0].args

# Find --host and --port values by iterating
$ServerHost = "127.0.0.1"; $ServerPort = "8000"
for ($i = 0; $i -lt $argsArray.Count; $i++) {
  if ($argsArray[$i] -eq "--host") { $ServerHost = $argsArray[$i + 1] }
  if ($argsArray[$i] -eq "--port") { $ServerPort = $argsArray[$i + 1] }
}

$BaseURL = "http://${ServerHost}:${ServerPort}"
# Example result: http://127.0.0.1:8000
```

**All subsequent commands must use `$BaseURL`, `$ServerHost`, and `$ServerPort` variables - never hardcode.**

**0.2 Check if server is already running:**

```powershell
# Fast check using Invoke-WebRequest with 1-second timeout (much faster than Test-NetConnection)
try { 
  $null = Invoke-WebRequest -Uri "$BaseURL/openapi.json" -TimeoutSec 1 -ErrorAction Stop
  $serverRunning = $true
  $serverWasRunning = $true  # Track for cleanup step
} catch { 
  $serverRunning = $false
  $serverWasRunning = $false
}
```

**IMPORTANT**: The check must be **blocking** and return a clear result before proceeding. Do NOT run discovery in parallel with server check.

**0.3 If not running, start the server:**

Start uvicorn using the same host/port from launch.json:

```powershell
# Start server in background with extracted host/port
Start-Process -FilePath ".venv/Scripts/python" -ArgumentList "-m uvicorn app:app --app-dir src --host $ServerHost --port $ServerPort" -NoNewWindow

# Wait up to 10 seconds for server to start
for ($i = 1; $i -le 10; $i++) {
  Start-Sleep -Seconds 1
  try { $null = Invoke-WebRequest -Uri "$BaseURL/openapi.json" -TimeoutSec 1 -ErrorAction Stop; break } catch { }
}
```

**0.4 Verify server is responding:**

```powershell
try { $null = Invoke-WebRequest -Uri "$BaseURL/openapi.json" -TimeoutSec 2 -ErrorAction Stop; Write-Host "OK: Server responding at $BaseURL" } catch { Write-Host "ERROR: Server not responding at $BaseURL" }
```

### Step 1: Discover Test Files

Find all project test files (excluding virtual environments):

```powershell
Get-ChildItem -Path . -Recurse -Filter "*_test*.py" | Where-Object { $_.FullName -notmatch "\\.venv\\|\\venv\\|\\.env\\|\\env\\|__pycache__" } | Where-Object { $_.Name -match "_test\.py$|_test_fix.*\.py$" } | Sort-Object FullName | ForEach-Object { $_.FullName }
```

**Test file patterns:**
- `*_test.py` - Standard test files
- `*_test_fix*.py` - Backward compatibility test files

**Excluded directories:**
- `.venv/`, `venv/` - Python virtual environments
- `.env/`, `env/` - Alternative venv names
- `__pycache__/` - Python cache

### Step 1.5: Discover Selftest Endpoints

**1.5.1 Fetch OpenAPI spec:**
```powershell
$openapi = (Invoke-WebRequest -Uri "$BaseURL/openapi.json").Content | ConvertFrom-Json
```

**1.5.2 Find all /selftest endpoints:**
- Iterate through `$openapi.paths`
- Find paths ending with `/selftest`
- Extract the full endpoint path (e.g., `/v2/jobs/selftest`, `/v2/domains/selftest`)

**1.5.3 Build selftest list:**
```
- /v2/jobs/selftest
- /v2/domains/selftest
- /v2/demorouter1/selftest
- (etc.)
```

### Step 2: Run Python Test Files

For each discovered `*_test.py` file:

1. Run with Python: `python [test_file]`
2. Capture exit code (0 = pass, non-zero = fail)
3. Capture stdout/stderr output
4. Record duration

**Parallel execution (PowerShell 7+, optional speedup):**
```powershell
$testFiles | ForEach-Object -Parallel {
  $output = python $_ 2>&1
  [PSCustomObject]@{ File = $_; Output = $output; ExitCode = $LASTEXITCODE }
} -ThrottleLimit 4
```

**Expected output format from test files:**
- Lines containing `PASS` or `OK` indicate passing tests
- Lines containing `FAIL` or `ERROR` indicate failing tests
- Final line should summarize: `X tests passed, Y failed`

### Step 2.5: Run Selftest Endpoints

For each discovered selftest endpoint:

**2.5.1 Call the endpoint with `format=stream`:**
```powershell
$url = "$BaseURL$endpoint`?format=stream"
```

**2.5.2 Handle SSE response:**
- Selftest endpoints return Server-Sent Events (SSE)
- Parse each `event:` and `data:` line
- Look for `event: end_json` which contains the final result

**2.5.3 Parse end_json for results:**
```json
{"ok": true, "total": 46, "passed": 46, "failed": 0}
```
or
```json
{"ok": false, "total": 46, "passed": 44, "failed": 2, "errors": ["..."]}
```

**2.5.4 Capture log events for failures:**
- If `ok: false`, collect all `event: log` data lines
- Filter to show only lines containing `FAIL` or `ERROR`

**SSE parsing example (PowerShell):**
```powershell
$response = Invoke-WebRequest -Uri $url -Headers @{"Accept"="text/event-stream"}
$lines = $response.Content -split "`n"
foreach ($line in $lines) {
  if ($line -match "^event: (.+)") { $eventType = $Matches[1] }
  if ($line -match "^data: (.+)") { $eventData = $Matches[1] }
}
```

**Parallel selftest execution (PowerShell 7+, optional speedup):**
```powershell
$selftestEndpoints | ForEach-Object -Parallel {
  $url = "$using:BaseURL$_`?format=stream"
  $response = Invoke-WebRequest -Uri $url -Headers @{"Accept"="text/event-stream"}
  # Parse and return results...
  [PSCustomObject]@{ Endpoint = $_; Response = $response.Content }
} -ThrottleLimit 4
```

### Step 3: Generate Summary Report

Create report file: `.test-summaries/[YYYY-MM-DD_HH-MM]_TEST_SUMMARY.md`

Create `.test-summaries/` directory if it doesn't exist.

**Report structure (minimal, failures-first):**

**NOTE**: Use emojis for better readability: ✅=OK, ❌=FAIL, ⚠️=WARNING

```markdown
# Test Summary: [OK ✅ | FAIL ❌]

[YYYY-MM-DD HH:MM] - [N] Python files, [M] selftest endpoints

## All Results

### Python Test Files
- ✅ OK: `path/to/passing_test1.py` (68 tests)
- ❌ FAIL: `path/to/failing_test.py` (65 passed, 3 failed)

### Selftest Endpoints
- ✅ OK: `/v2/domains/selftest` (29 tests)
- ❌ FAIL: `/v2/jobs/selftest` (41 passed, 1 failed)

## Failed Tests

(Only if failures exist - detailed output)

### [failing_test.py] - FAIL ❌ ([N] passed, [M] failed)

```
[Only the failing test output lines, not full stdout]
```

### /v2/jobs/selftest - FAIL ❌ ([N] passed, [M] failed)

```
[Only FAIL/ERROR lines from SSE log events]
```

## Action Required

(Only if failures exist)

Each failure gets a unique ID: `[TIMESTAMP]_TEST_FAIL_[NNN]`

### [TIMESTAMP]_TEST_FAIL_001

- **File -> Test**: `path/to/test_file.py` -> `test_function_name`
- **What is it testing?**: Brief description of what the test validates
- **Why did it fail?**: Root cause analysis from error output
- **Fix Option A (recommended)**: Primary fix suggestion
- **Fix Option B**: Alternative fix if Option A is not feasible

### [TIMESTAMP]_TEST_FAIL_002

- **File -> Test**: `/v2/jobs/selftest` -> `test_case_name`
- **What is it testing?**: What this selftest validates
- **Why did it fail?**: Error from SSE log
- **Fix Option A (recommended)**: Primary fix
- **Fix Option B**: Alternative

(If all tests pass: "No action items - all tests passing ✅")
```

**Action Point ID format**: `YYYY-MM-DD_HH-MM_TEST_FAIL_NNN`
- Example: `2025-12-30_11-55_TEST_FAIL_001`, `2025-12-30_11-55_TEST_FAIL_002`
- Timestamp matches the report filename
- Sequential numbering starting at 001

**Design principles:**
- Summary at top for quick overview
- Action items and detailed failures follow
- No redundant counts (one summary line is enough)
- Failed test output shown inline, passing tests just listed
- Full stdout only for failed tests, truncated if >50 lines

### Step 4: Server Cleanup

**Skip cleanup if server was already running before tests** (uses `$serverWasRunning` from Step 0.2).

**4.1 Stop the server (only if we started it):**
```powershell
if ($serverWasRunning) {
  Write-Host "OK: Server was pre-existing, skipping cleanup"
} else {
  # Find and stop uvicorn process on the configured port
  $uvicornProcess = Get-NetTCPConnection -LocalPort $ServerPort -ErrorAction SilentlyContinue | 
    Select-Object -ExpandProperty OwningProcess -First 1
  if ($uvicornProcess) {
    Stop-Process -Id $uvicornProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
  }
  
  # Quick verify using fast check
  try { 
    $null = Invoke-WebRequest -Uri "$BaseURL/openapi.json" -TimeoutSec 1 -ErrorAction Stop
    Write-Host "WARNING: Server still running - force kill"
    Get-Process -Name python* | Where-Object { $_.CommandLine -match "uvicorn" } | Stop-Process -Force -ErrorAction SilentlyContinue
  } catch { 
    Write-Host "OK: Server stopped"
  }
}
```

### Step 5: Save and Report

1. Create `.test-summaries/` directory if needed
2. **Get current system time first** (run this command to get exact timestamp):
   ```powershell
   Get-Date -Format "yyyy-MM-dd_HH-mm"
   # Output example: 2024-12-30_11-45
   ```
3. Generate filename using the output from step 2:
   ```powershell
   $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm"
   $filename = "${timestamp}_TEST_SUMMARY.md"
   # Example: 2024-12-30_11-45_TEST_SUMMARY.md
   ```
4. **VERIFY filename format** before saving:
   - Must match pattern: `YYYY-MM-DD_HH-MM_TEST_SUMMARY.md`
   - Must contain underscore between date and time: `_HH-MM_`
   - INVALID: `2024-12-30_TEST_SUMMARY.md` (missing time)
   - VALID: `2024-12-30_11-45_TEST_SUMMARY.md`
5. Save report to: `.test-summaries/$filename`
6. Print summary to console
7. Return overall pass/fail status

## Output File

**Directory**: `.test-summaries/`
**Filename format**: `YYYY-MM-DD_HH-MM_TEST_SUMMARY.md`
**Full path example**: `.test-summaries/2024-12-30_11-00_TEST_SUMMARY.md`

## Execution Notes

**Running individual test files:**
```powershell
.venv/Scripts/python src/routers_v2/common_report_functions_v2_test.py
```

**Running individual selftest endpoint:**
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/v2/jobs/selftest?format=stream" -Headers @{"Accept"="text/event-stream"}
```

**Common test output patterns to parse:**
- `[N] tests passed` or `[N] passed`
- `[N] tests failed` or `[N] failed`
- `OK` or `PASS` for individual test success
- `FAIL` or `ERROR` for individual test failure
- Exit code 0 = all tests passed
- Exit code non-zero = at least one test failed

**SSE end_json patterns:**
- `{"ok": true, ...}` = selftest passed
- `{"ok": false, ...}` = selftest failed

### Step 6: Verify Line Endings

Check that all created/modified files use CRLF line endings (Windows requirement).

**6.1 Check for LF-only files in git staging:**
```powershell
git diff --cached --name-only | ForEach-Object {
  $content = Get-Content $_ -Raw -ErrorAction SilentlyContinue
  if ($content -and $content -match "`n" -and $content -notmatch "`r`n") {
    Write-Host "WARNING: LF line endings in: $_"
  }
}
```

**6.2 Fix any LF files:**
```powershell
git add --renormalize .
```

## Quality Criteria

The report is complete when:
1. **Comprehensive**: All Python test files AND selftest endpoints discovered and run
2. **Accurate**: Pass/fail status correctly determined from exit codes and SSE responses
3. **Actionable**: Failed tests have suggested fixes
4. **Timestamped**: Report filename includes execution time
5. **Formatted**: No tables - all data in list format
6. **Server managed**: Server started if needed, stopped after tests
7. **Line endings**: All files use CRLF (no LF-only files)
