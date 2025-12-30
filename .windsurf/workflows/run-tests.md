---
description: Run all test files and generate test summary report
---

# Run Tests Workflow

Discovers and runs all test files (Python + HTTP selftests), generates a timestamped test summary report.

## Prerequisites

1. Working directory is workspace root
2. Python virtual environment available at `.venv/`

## Workflow Steps

### Step 0: Server Setup

**0.1 Extract server URL from `.vscode/launch.json`:**

Read the launch.json and extract `--host` and `--port` from the args array:

```powershell
$launchJson = Get-Content ".vscode/launch.json" | ConvertFrom-Json
$args = $launchJson.configurations[0].args

# Find --host and --port values
$hostIndex = [array]::IndexOf($args, "--host")
$portIndex = [array]::IndexOf($args, "--port")
$HOST = if ($hostIndex -ge 0) { $args[$hostIndex + 1] } else { "127.0.0.1" }
$PORT = if ($portIndex -ge 0) { $args[$portIndex + 1] } else { "8000" }

$BASE_URL = "http://${HOST}:${PORT}"
# Example result: http://127.0.0.1:8000
```

**All subsequent commands must use `$BASE_URL`, `$HOST`, and `$PORT` variables - never hardcode.**

**0.2 Check if server is already running:**

```powershell
# Method 1: Use curl with dynamic URL
curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/openapi.json"
# Returns "200" if running, connection error if not

# Method 2: Use Test-NetConnection with dynamic host/port
Test-NetConnection -ComputerName $HOST -Port $PORT -InformationLevel Quiet
# Returns $true if port is open, $false if not
```

**IMPORTANT**: The check must be **blocking** and return a clear result before proceeding. Do NOT run discovery in parallel with server check.

**0.3 If not running, start the server:**

Start uvicorn using the same host/port from launch.json:

```bash
# Start server in background with extracted host/port
.venv/Scripts/python -m uvicorn app:app --app-dir src --host $HOST --port $PORT &

# Wait up to 10 seconds for server to start
for i in {1..10}; do
  curl -s "${BASE_URL}/openapi.json" > /dev/null && break
  sleep 1
done
```

**0.4 Verify server is responding:**

```bash
curl -s -f "${BASE_URL}/openapi.json" > /dev/null || echo "ERROR: Server not responding at ${BASE_URL}"
```

### Step 1: Discover Test Files

Find all project test files (excluding virtual environments):

```bash
find . \( -path "./.venv" -o -path "./venv" -o -path "./.env" -o -path "./env" \) -prune -o \( -name "*_test.py" -o -name "*_test_fix*.py" \) -print | grep -v __pycache__ | sort
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
$openapi = (Invoke-WebRequest -Uri "$BASE_URL/openapi.json").Content | ConvertFrom-Json
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

**Expected output format from test files:**
- Lines containing `PASS` or `OK` indicate passing tests
- Lines containing `FAIL` or `ERROR` indicate failing tests
- Final line should summarize: `X tests passed, Y failed`

### Step 2.5: Run Selftest Endpoints

For each discovered selftest endpoint:

**2.5.1 Call the endpoint with `format=stream`:**
```powershell
$url = "$BASE_URL$endpoint`?format=stream"
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

### Step 3: Generate Summary Report

Create report file: `.test-summaries/[YYYY-MM-DD_HH-MM]_TEST_SUMMARY.md`

Create `.test-summaries/` directory if it doesn't exist.

**Report structure (minimal, failures-first):**

```markdown
# Test Summary: [OK | FAIL]

[YYYY-MM-DD HH:MM] - [N] Python files, [M] selftest endpoints

## Action Required

(Only if failures exist - this section is the most important)

- **[test_file.py]**: [Root cause] -> [Fix action]
- **[/v2/jobs/selftest]**: [Root cause] -> [Fix action]

## Failed Tests

(Only if failures exist - show failing output immediately)

### [failing_test.py] - FAIL ([N] passed, [M] failed)

```
[Only the failing test output lines, not full stdout]
```

### /v2/jobs/selftest - FAIL ([N] passed, [M] failed)

```
[Only FAIL/ERROR lines from SSE log events]
```

## All Results

### Python Test Files
- OK: `path/to/passing_test1.py` ([N] tests)
- FAIL: `path/to/failing_test.py` ([N] passed, [M] failed)

### Selftest Endpoints
- OK: `/v2/domains/selftest` ([N] tests)
- FAIL: `/v2/jobs/selftest` ([N] passed, [M] failed)
```

**Design principles:**
- Failures at top, not buried after passing tests
- No redundant counts (one summary line is enough)
- Action items immediately visible
- Failed test output shown inline, passing tests just listed
- Full stdout only for failed tests, truncated if >50 lines

### Step 4: Server Cleanup

If we started the server in Step 0:
```powershell
if ($weStartedServer -and $serverProcess) {
  Stop-Process -Id $serverProcess.Id -Force -ErrorAction SilentlyContinue
}
```

### Step 5: Save and Report

1. Create `.test-summaries/` directory if needed
2. Generate filename with FULL timestamp (date AND time):
   ```powershell
   $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm"
   $filename = "${timestamp}_TEST_SUMMARY.md"
   # Example: 2024-12-30_11-45_TEST_SUMMARY.md
   ```
3. **VERIFY filename format** before saving:
   - Must match pattern: `YYYY-MM-DD_HH-MM_TEST_SUMMARY.md`
   - Must contain underscore between date and time: `_HH-MM_`
   - INVALID: `2024-12-30_TEST_SUMMARY.md` (missing time)
   - VALID: `2024-12-30_11-45_TEST_SUMMARY.md`
4. Save report to: `.test-summaries/$filename`
5. Print summary to console
6. Return overall pass/fail status

## Output File

**Directory**: `.test-summaries/`
**Filename format**: `YYYY-MM-DD_HH-MM_TEST_SUMMARY.md`
**Full path example**: `.test-summaries/2024-12-30_11-00_TEST_SUMMARY.md`

## Execution Notes

**Running individual test files:**
```bash
python src/routers_v2/common_report_functions_v2_test.py
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

## Quality Criteria

The report is complete when:
1. **Comprehensive**: All Python test files AND selftest endpoints discovered and run
2. **Accurate**: Pass/fail status correctly determined from exit codes and SSE responses
3. **Actionable**: Failed tests have suggested fixes
4. **Timestamped**: Report filename includes execution time
5. **Formatted**: No tables - all data in list format
6. **Server managed**: Server started if needed, stopped after tests
