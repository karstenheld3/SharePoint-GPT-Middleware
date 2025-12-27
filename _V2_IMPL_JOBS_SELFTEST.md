# Implementation Plan: Jobs Selftest Endpoint

**Goal**: Add exhaustive selftest endpoint for jobs router that tests all CRUD operations, job state transitions, control actions, and SSE stream verification
**Target file**: `src/routers_v2/jobs.py`

**Depends on:**
- `_V2_SPEC_JOBS_UI.md` for jobs UI specification
- `_V2_SPEC_ROUTERS.md` for streaming job infrastructure and SSE format
- `common_job_functions_v2.py` for StreamingJobWriter and job management functions

**Does not depend on:**
- Domain-specific selftests (this is self-contained)

## Table of Contents

1. Overview
2. Test Data and Setup
3. Test Cases by Category
4. State Transition Verification
5. SSE Stream Verification
6. Job File Verification
7. Implementation Structure
8. Changes Required
9. Verification Checklist

## Overview

The jobs selftest validates all endpoints and job lifecycle operations. Unlike domain/demorouter selftests that test CRUD on data items, jobs selftest must:

1. **Create jobs** - Trigger a streaming job via internal helper (not external router)
2. **Test state transitions** - Verify pause/resume/cancel control actions
3. **Verify SSE events** - Check that state_json events appear in stream
4. **Verify job files** - Confirm file extension changes with state
5. **Test cleanup** - Delete completed/cancelled jobs

**Endpoint**: `GET /v2/jobs/selftest?format=stream`
**Response**: SSE stream with test progress and final summary

## Test Data and Setup

### Internal Job Creator

Create a minimal streaming job within jobs.py for testing purposes:

```python
async def _create_test_job(persistent_storage_path: str, router_prefix: str, delay_seconds: float = 0.5, item_count: int = 5) -> tuple[StreamingJobWriter, AsyncGenerator]:
  """Create a minimal test job that yields SSE events. Returns (writer, generator)."""
  writer = StreamingJobWriter(
    persistent_storage_path=persistent_storage_path,
    router_name=router_name,
    action="test_job",
    object_id=None,
    source_url=f"{router_prefix}/{router_name}/selftest",
    router_prefix=router_prefix
  )
  
  async def job_generator():
    yield writer.emit_start()
    for i in range(item_count):
      await asyncio.sleep(delay_seconds)
      yield writer.emit_log(f"[ {i+1} / {item_count} ] Processing item {i+1}...")
      # Check for control
      async for control_event in writer.check_control():
        if isinstance(control_event, ControlAction):
          if control_event == ControlAction.CANCEL:
            yield writer.emit_end(ok=False, error="Cancelled", data={}, cancelled=True)
            return
        else:
          yield control_event
    yield writer.emit_end(ok=True, data={"items_processed": item_count})
  
  return writer, job_generator
```

### Test Variables

```python
test_job_id = None  # Set after job creation
test_job_id_2 = None  # For pause/resume test
test_job_id_cancel = None  # For cancel test
```

## Test Cases by Category

### Category 1: Error Cases (10 tests)

| # | Test | Expected | HTTP |
|---|------|----------|------|
| 1 | GET /get without job_id | ok=false, "Missing 'job_id'" | 200 |
| 2 | GET /get with non-existent job_id | ok=false | 404 |
| 3 | GET /monitor without job_id | ok=false | 200 |
| 4 | GET /monitor with non-existent job_id | ok=false | 404 |
| 5 | GET /control without job_id | ok=false | 200 |
| 6 | GET /control without action | ok=false | 200 |
| 7 | GET /control with invalid action | ok=false | 200 |
| 8 | GET /control with non-existent job_id | ok=false | 404 |
| 9 | GET /results without job_id | ok=false | 200 |
| 10 | DELETE /delete without job_id | ok=false | 200 |

### Category 2: Job Creation and Basic Get (5 tests)

| # | Test | Expected |
|---|------|----------|
| 11 | Create test job via internal helper | Job file created with .running extension |
| 12 | Wait for job completion | Job file has .completed extension |
| 13 | GET /get?job_id={id} | ok=true, state="completed" |
| 14 | GET /?format=json | job_id in list, state="completed" |
| 15 | GET /results?job_id={id} | ok=true, result data present |

### Category 3: Monitor Endpoint (4 tests)

| # | Test | Expected |
|---|------|----------|
| 16 | GET /monitor?job_id={id}&format=json | ok=true, includes "log" field |
| 17 | GET /monitor?job_id={id}&format=html | HTML response |
| 18 | GET /monitor?job_id={id}&format=stream | SSE stream with events |
| 19 | Verify stream contains start_json, log, end_json events | Events present in order |

### Category 4: Control - Pause/Resume with Error Cases (10 tests)

Tests reordered to validate error cases while job is in correct state.

| # | Test | Job State | Expected |
|---|------|-----------|----------|
| 20 | Create slow test job (10 items × 1s) | running | Job file .running |
| 21 | GET /control?action=resume (while running) | running | ok=false, "Cannot resume" |
| 22 | GET /control?action=pause | running→paused | ok=true |
| 23 | Verify job file extension is .paused | paused | File renamed |
| 24 | GET /get?job_id={id} | paused | state="paused" |
| 25 | Verify SSE contains state_json state="paused" | paused | Event present |
| 26 | GET /control?action=pause (while paused) | paused | ok=false, "Cannot pause" |
| 27 | GET /control?action=resume | paused→running | ok=true |
| 28 | Verify job file extension is .running | running | File renamed back |
| 29 | Verify SSE contains state_json state="running" | running | Event present |

### Category 5: Control - Cancel (5 tests)

| # | Test | Expected |
|---|------|----------|
| 30 | Create another slow test job | Job file .running |
| 31 | GET /control?job_id={id}&action=cancel | ok=true |
| 32 | Wait for job to process cancel | Short delay |
| 33 | Verify job file extension is .cancelled | File renamed |
| 34 | Verify SSE stream contains state_json with state="cancelled" | Event present |

### Category 6: Control Error Cases - Completed/Cancelled (4 tests)

| # | Test | Job Used | Expected |
|---|------|----------|----------|
| 35 | GET /control?job_id={completed_id}&action=pause | completed_job_id | ok=false, "already completed" |
| 36 | GET /control?job_id={cancelled_id}&action=resume | cancel_job_id | ok=false, "already cancelled" |
| 37 | Force cancel job (after cancelling background task) | pause_resume_job_id | ok=true |
| 38 | GET /get after force cancel | pause_resume_job_id | state="cancelled" |

Note: Before Test 37, cancel Job 2's background task to release file handle (Windows can't rename open files).

### Category 7: Delete Tests (8 tests)

| # | Test | Job Used | Expected |
|---|------|----------|----------|
| 39 | Create slow job for delete test | running_for_delete_id | Job file .running |
| 40 | DELETE /delete?job_id={running_id} | running_for_delete_id | ok=false, "Cannot delete active job" |
| 41 | DELETE /delete?job_id={completed_id} | completed_job_id | ok=true |
| 42 | GET /get?job_id={completed_id} | completed_job_id | 404 |
| 43 | DELETE /delete?job_id={cancelled_id} | cancel_job_id | ok=true |
| 44 | GET /?format=json | - | Neither job in list |
| 45 | DELETE /delete?job_id={force_cancelled_id} | pause_resume_job_id | ok=true |
| 46 | DELETE /delete same job again | pause_resume_job_id | 404 |

**Total: 46 tests**

## Execution Timeline

```
Selftest SSE Stream
════════════════════════════════════════════════════════════════════════════════════════════════

Cat 1: Error Cases (Tests 1-10)
│ No jobs created - tests error responses on missing/invalid params
│
├─ Test 10b: /results non-existent → 404
├─ Test 10c: /results running job → needs running job (use Job 2 from Cat 4 later, or skip)
│
▼
Cat 2: Job Creation (Tests 11-15)
│
│  ┌─ Job 1 (completed_job_id) ─────────────────────────────────────────────────────────────┐
│  │ _run_test_job_to_completion()                                                          │
│  │ [start] ██████ [end]                                                                   │
│  │         ~0.3s                                                                          │
│  └────────────────────────────────────────────────────────────────────────────────────────┘
│  │
│  ├─ Test 11: Create job
│  ├─ Test 12: Wait for completion
│  ├─ Test 13: GET /get → completed
│  ├─ Test 14: GET / → in list
│  └─ Test 15: GET /results → has data
│
▼
Cat 3: Monitor Endpoint (Tests 16-19)
│ Uses Job 1 (completed)
│
▼
Cat 4: Pause/Resume + Error Cases (Tests 20-29)
│
│  ┌─ Job 2 (pause_resume_job_id) ──────────────────────────────────────────────────────────┐
│  │ _run_slow_test_job_in_background(delay=1.0, items=30)                                  │
│  │ [start] ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
│  │              ↑         ↑                   ↑         ↑                                 │
│  │              │         │                   │         └─ Test 27: resume                │
│  │              │         │                   └─ Test 26: pause paused fails              │
│  │              │         └─ Test 22: pause                                               │
│  │              └─ Test 21: resume running fails                                          │
│  └────────────────────────────────────────────────────────────────────────────────────────┘
│  │
│  ├─ Test 20: Create slow job
│  ├─ Test 21: Resume running → fails (job is running, not paused)
│  ├─ Test 22: Pause → ok
│  │     └─ Job 2 enters pause loop, file renamed to .paused
│  ├─ Tests 23-25: Verify paused state
│  ├─ Test 26: Pause paused → fails (already paused)
│  ├─ Test 27: Resume → ok
│  │     └─ Job 2 exits pause loop, file renamed to .running
│  └─ Tests 28-29: Verify running state
│
│  [Job 2 continues running in background...]
│
▼
Cat 5: Cancel (Tests 30-34)
│
│  ┌─ Job 3 (cancel_job_id) ────────────────────────────────────────────────────────────────┐
│  │ _run_slow_test_job_in_background(delay=1.0, items=30)                                  │
│  │ [start] ████ ╳                                                                         │
│  │              ↑                                                                         │
│  │              └─ Test 31: cancel                                                        │
│  └────────────────────────────────────────────────────────────────────────────────────────┘
│  │
│  ├─ Test 30: Create slow job
│  ├─ Test 31: Cancel → ok
│  │     └─ Job 3 receives cancel, emits end_json(cancelled=true), file renamed .cancelled
│  └─ Tests 32-34: Verify cancelled state
│
▼
Cat 6: Control Error Cases (Tests 35-38)
│
│  ├─ Test 35: Pause completed → fails (Job 1 completed)
│  ├─ Test 36: Resume cancelled → fails (Job 3 cancelled)
│  ├─ [Cancel Job 2 background task to release file handle]
│  ├─ Test 37: Force cancel → ok (Job 2)
│  │     └─ Job 2 file renamed .cancelled directly
│  └─ Test 38: GET /get → cancelled
│
▼
Cat 7: Delete Tests (Tests 39-46)
│
│  ┌─ Job 4 (running_for_delete_id) ────────────────────────────────────────────────────────┐
│  │ _run_slow_test_job_in_background(delay=1.0, items=30)                                  │
│  │ [start] ████████████████████████████████████████████████████████████████████████░░░░░  │
│  │         ↑                                                                              │
│  │         └─ Test 40: DELETE → fails (running)                                           │
│  └────────────────────────────────────────────────────────────────────────────────────────┘
│  │
│  ├─ Test 39: Create slow job (Job 4)
│  ├─ Test 40: DELETE running → fails
│  ├─ Test 41: DELETE completed (Job 1) → ok
│  ├─ Test 42: GET /get Job 1 → 404
│  ├─ Test 43: DELETE cancelled (Job 3) → ok
│  ├─ Test 44: GET / → neither in list
│  ├─ Test 45: DELETE force_cancelled (Job 2) → ok
│  └─ Test 46: DELETE Job 2 again → 404
│
▼
[CLEANUP]
│
│  ├─ Cancel Job 4 (still running)
│  ├─ Force cancel any remaining running/paused jobs
│  └─ Delete all test job files
│
▼
[emit end_json with results]

════════════════════════════════════════════════════════════════════════════════════════════════
```

### Job Summary

| Job | Variable | Created | Final State | Used In |
|-----|----------|---------|-------------|---------|
| 1 | completed_job_id | Cat 2 | completed | Cat 2-3, Cat 6 Test 35, Cat 7 Test 41-42 |
| 2 | pause_resume_job_id | Cat 4 | force_cancelled | Cat 4, Cat 6 Tests 37-38, Cat 7 Tests 45-46 |
| 3 | cancel_job_id | Cat 5 | cancelled | Cat 5, Cat 6 Test 36, Cat 7 Test 43 |
| 4 | running_for_delete_id | Cat 7 | cleanup | Cat 7 Tests 39-40, cleanup |

## State Transition Verification

### Valid State Transitions

```
running --> paused    (via pause control)
running --> cancelled (via cancel control)
running --> completed (job finishes normally)
paused  --> running   (via resume control)
paused  --> cancelled (via cancel control)
```

### Job File Extension Changes

| State | Extension |
|-------|-----------|
| running | .running |
| paused | .paused |
| completed | .completed |
| cancelled | .cancelled |

### Verification Logic

```python
def verify_job_file_extension(persistent_storage_path: str, job_id: str, expected_extension: str) -> bool:
  """Check if job file has expected extension."""
  from routers_v2.common_job_functions_v2 import find_job_file
  filepath = find_job_file(persistent_storage_path, job_id)
  if not filepath: return False
  return filepath.endswith(f".{expected_extension}")
```

## SSE Stream Verification

### Events to Verify

For each job, the SSE stream (in job file) should contain:

1. `event: start_json` - At beginning, contains job_id, state="running"
2. `event: log` - Multiple, contains progress messages
3. `event: state_json` - On pause/resume/cancel, contains new state
4. `event: end_json` - At end, contains result

### Stream Parsing Helper

```python
def parse_sse_events(sse_content: str) -> list[dict]:
  """Parse SSE content into list of {event_type, data} dicts."""
  events = []
  current_event = None
  current_data = []
  
  for line in sse_content.split('\n'):
    if line.startswith('event: '):
      if current_event:
        events.append({"event": current_event, "data": '\n'.join(current_data)})
      current_event = line[7:]
      current_data = []
    elif line.startswith('data: '):
      current_data.append(line[6:])
    elif line == '' and current_event:
      events.append({"event": current_event, "data": '\n'.join(current_data)})
      current_event = None
      current_data = []
  
  return events

def has_state_event(events: list[dict], expected_state: str) -> bool:
  """Check if events contain state_json with expected state."""
  for e in events:
    if e["event"] == "state_json":
      try:
        data = json.loads(e["data"])
        if data.get("state") == expected_state:
          return True
      except: pass
  return False
```

## Job File Verification

### File Naming Pattern

`[TIMESTAMP]_[[ACTION]]_[[JB_ID]]_[[OBJECT_ID]].[state]`

Example: `2025-12-27_14-30-00_[test_job]_[jb_42].running`

### Verification Points

1. **After creation**: File exists with .running extension
2. **After pause**: File renamed to .paused extension
3. **After resume**: File renamed back to .running extension
4. **After cancel**: File renamed to .cancelled extension
5. **After completion**: File renamed to .completed extension
6. **After delete**: File no longer exists

## Implementation Structure

### New Helper Function (add before selftest endpoint)

```python
import asyncio, textwrap, uuid
import httpx

async def _run_test_job_to_completion(delay_seconds: float = 0.1, item_count: int = 3) -> str:
  """Run a quick test job to completion. Returns job_id."""
  writer = StreamingJobWriter(
    persistent_storage_path=get_persistent_storage_path(),
    router_name=router_name,
    action="selftest",
    object_id=None,
    source_url=f"{router_prefix}/{router_name}/selftest",
    router_prefix=router_prefix
  )
  job_id = writer.job_id
  try:
    writer.emit_start()
    for i in range(item_count):
      await asyncio.sleep(delay_seconds)
      writer.emit_log(f"[ {i+1} / {item_count} ] Test item {i+1}")
    writer.emit_end(ok=True, data={"items": item_count})
  finally:
    writer.finalize()
  return job_id

async def _run_slow_test_job_in_background(delay_seconds: float = 1.0, item_count: int = 30) -> tuple[str, asyncio.Task]:
  """Start a slow test job in background. Returns (job_id, task)."""
  writer = StreamingJobWriter(
    persistent_storage_path=get_persistent_storage_path(),
    router_name=router_name,
    action="selftest",
    object_id=None,
    source_url=f"{router_prefix}/{router_name}/selftest",
    router_prefix=router_prefix
  )
  job_id = writer.job_id
  
  async def run_job():
    try:
      writer.emit_start()
      for i in range(item_count):
        await asyncio.sleep(delay_seconds)
        writer.emit_log(f"[ {i+1} / {item_count} ] Slow test item {i+1}")
        async for control_event in writer.check_control():
          if isinstance(control_event, ControlAction):
            if control_event == ControlAction.CANCEL:
              writer.emit_end(ok=False, error="Cancelled", data={}, cancelled=True)
              return
      writer.emit_end(ok=True, data={"items": item_count})
    finally:
      writer.finalize()
  
  task = asyncio.create_task(run_job())
  await asyncio.sleep(0.3)
  return job_id, task
```

### Selftest Endpoint Docstring

```python
@router.get(f"/{router_name}/selftest")
async def jobs_selftest(request: Request):
  """
  Self-test for jobs router operations.
  
  Only supports format=stream.
  
  Tests:
  1. Error cases (missing params, non-existent jobs)
  2. Job creation and basic get
  3. Monitor endpoint (json, html, stream)
  4. Control actions (pause/resume/cancel)
  5. State transition verification
  6. SSE stream event verification
  7. Job file extension verification
  8. Delete operations
  
  Example:
  GET {router_prefix}/{router_name}/selftest?format=stream
  
  Result (end_json event):
  {
    "ok": true,
    "error": "",
    "data": {
      "passed": 44,
      "failed": 0,
      "passed_tests": ["Test 1 description", ...],
      "failed_tests": []
    }
  }
  """
```

### Helper Functions (inside run_selftest)

```python
def verify_job_file_extension(job_id: str, expected_ext: str) -> bool:
  filepath = find_job_file(get_persistent_storage_path(), job_id)
  if not filepath: return False
  return filepath.endswith(f".{expected_ext}")

def parse_sse_events(sse_content: str) -> list[dict]:
  events = []
  current_event = None
  current_data = []
  for line in sse_content.split('\n'):
    if line.startswith('event: '):
      if current_event:
        events.append({"event": current_event, "data": '\n'.join(current_data)})
      current_event = line[7:]
      current_data = []
    elif line.startswith('data: '):
      current_data.append(line[6:])
    elif line == '' and current_event:
      events.append({"event": current_event, "data": '\n'.join(current_data)})
      current_event = None
      current_data = []
  return events

def has_state_event(events: list[dict], expected_state: str) -> bool:
  for e in events:
    if e["event"] == "state_json":
      try:
        data = json.loads(e["data"])
        if data.get("state") == expected_state: return True
      except: pass
  return False
```

### Cleanup

```python
finally:
  # Cancel any running tasks
  for task in background_tasks:
    if not task.done():
      task.cancel()
      try: await task
      except asyncio.CancelledError: pass
  
  # Delete all test jobs
  for job_id in test_job_ids:
    try:
      # Force cancel if still running
      job = find_job_by_id(get_persistent_storage_path(), job_id)
      if job and job.state in ["running", "paused"]:
        force_cancel_job(get_persistent_storage_path(), job_id)
      delete_job(get_persistent_storage_path(), job_id)
    except: pass
  
  writer.finalize()
```

## Changes Required

### 1. Add imports at top of jobs.py

```python
import asyncio, textwrap, uuid
import httpx
from routers_v2.common_ui_functions_v2 import ..., generate_endpoint_caller_js
from routers_v2.common_job_functions_v2 import ..., find_job_file, StreamingJobWriter, ControlAction
```

### 2. Add selftest to router docs endpoint list (in jobs_root)

```python
{"path": "/selftest", "desc": "Self-test", "formats": ["stream"]}
```

### 3. Add "Run Selftest" button to UI toolbar (in _generate_jobs_ui_page)

Add to toolbar section:
```html
<button class="btn-primary" data-url="{router_prefix}/{router_name}/selftest?format=stream" data-format="stream" data-show-result="modal" data-reload-on-finish="true" onclick="callEndpoint(this)">Run Selftest</button>
```

### 4. Add helper functions

- `_run_test_job_to_completion()` - Quick job for basic tests
- `_run_slow_test_job_in_background()` - Slow job for control tests
- Inside selftest (local functions):
  - `verify_job_file_extension()` - Check job file has expected extension
  - `wait_for_extension()` - Async retry loop for extension check
  - `parse_sse_events()` - Parse SSE content from job file
  - `has_state_event()` - Check for state_json event with expected state

### 5. Implement selftest endpoint

Full async generator pattern following domains.py selftest

## Verification Checklist

### Prerequisites

- [x] jobs.py has all required endpoints implemented
- [x] common_job_functions_v2.py has all functions: find_job_by_id, find_job_file, read_job_log, create_control_file, delete_job, force_cancel_job

### Implementation

- [x] Add imports: `asyncio`, `textwrap`, `uuid`, `httpx`, `generate_endpoint_caller_js`, `StreamingJobWriter`, `ControlAction`, `find_job_file`
- [x] Add selftest to router docs endpoint list
- [x] Add "Run Selftest" button to UI toolbar
- [x] Implement `_run_test_job_to_completion()` helper
- [x] Implement `_run_slow_test_job_in_background()` helper
- [x] Implement `jobs_selftest` endpoint:
  - [x] Bare GET returns docstring documentation
  - [x] format != stream returns error
  - [x] StreamingJobWriter setup
  - [x] run_selftest() async generator
  - [x] StreamingResponse return

### Test Cases (46 total) ✓ ALL PASS

**Error Cases (10):**
- [x] Test 1-10: All error cases pass

**Job Creation and Basic Get (5):**
- [x] Test 11-15: All job creation tests pass

**Monitor Endpoint (4):**
- [x] Test 16-19: All monitor tests pass

**Control - Pause/Resume + Error Cases (10):**
- [x] Test 20-29: All pause/resume tests pass

**Control - Cancel (5):**
- [x] Test 30-34: All cancel tests pass

**Control Error Cases - Completed/Cancelled (4):**
- [x] Test 35-38: All control error cases pass

**Delete Tests (8):**
- [x] Test 39-46: All delete tests pass

### Final Verification

- [x] Run selftest via UI
- [x] Verify all 46 tests pass
- [x] Verify 4 jobs created during test
- [x] Verify cleanup removes all test jobs
- [x] Verify no orphan job files remain
- [ ] Test pause/resume visually in UI (manual)
- [ ] Test cancel visually in UI (manual)

## Known Issues and Fixes

### Issue 1: Background job pause handling

The `_run_slow_test_job_in_background` must fully consume `check_control()` generator to handle pause loop correctly. The pause loop runs inside `check_control()` and only returns after resume or cancel.

**Fixed code:**
```python
async for control_event in writer.check_control():
  if isinstance(control_event, ControlAction):
    if control_event == ControlAction.CANCEL:
      writer.emit_end(ok=False, error="Cancelled", data={}, cancelled=True)
      return
  # SSE events (state_json, log) already written to file by emit_* methods
```

### Issue 2: Race conditions on file extension checks

After control action, add retry loop before checking extension:
```python
async def wait_for_extension(job_id: str, expected_ext: str, max_wait: float = 2.0) -> bool:
  for _ in range(int(max_wait / 0.2)):
    if verify_job_file_extension(job_id, expected_ext): return True
    await asyncio.sleep(0.2)
  return False
```

### Issue 3: Job lifecycle tracking

Track all job IDs for cleanup:
```python
test_job_ids = []  # All created job IDs
background_tasks = []  # All background tasks

# After each job creation:
test_job_ids.append(job_id)
```

### Issue 4: Test 35-36 require specific states ✓ RESOLVED

**Solution**: Merged control error cases into Cat 4. Tests 21 (resume running) and 26 (pause paused) now execute while Job 2 is in correct state.

### Issue 5: Test 43 needs running job ✓ RESOLVED

**Solution**: Cat 7 now creates Job 4 specifically for "DELETE running job fails" test.

### Issue 6: Missing /results error cases

**Status**: Not added to test table - can be added as Tests 10b/10c if needed, or skip since `/results` behavior on running job is implementation-dependent (may return partial result or null).

### Issue 7: SSE verification during pause

To verify SSE contains state_json events, read job file content after state change:
```python
log_content = read_job_log(get_persistent_storage_path(), job_id)
events = parse_sse_events(log_content)
has_paused = has_state_event(events, "paused")
```

File is flushed before state change in `check_control()`, so content should be available.

### Issue 8: Multi-worker safety ✓ NOT AN ISSUE

**Analysis**: `StreamingJobWriter._create_job_file()` uses `os.O_CREAT | os.O_EXCL` which is atomic at the OS level. Two workers getting the same job number results in one succeeding and one retrying. No additional isolation needed.

**Concurrent selftest runs**: Each selftest tracks its own `test_job_ids[]` list in its own async generator scope. No cross-contamination. Each run cleans up only the jobs it created.

### Issue 9: Glob pattern bug in _find_control_file ✓ FIXED

**Problem**: Pattern `*[{job_id}]*.{control_type}` treated `[jb_33]` as a character class, causing jb_33 to pick up jb_34's cancel file.

**Fix in `common_job_functions_v2.py`:**
```python
# Escape [ and ] in glob pattern: [[] matches literal [, []] matches literal ]
pattern = os.path.join(self._jobs_folder, f"*[[]{self._job_id}[]]*.{control_type}")
```

### Issue 10: Force cancel fails on Windows with open file handle ✓ FIXED

**Problem**: `force_cancel_job()` tries to rename an open file. On Windows, files can't be renamed while open. The background task has the file handle open while paused.

**Fix in selftest**: Cancel background task first to release file handle, then call `force_cancel_job()` directly:
```python
if task2 and not task2.done():
  task2.cancel()
  try: await task2
  except asyncio.CancelledError: pass

force_ok = force_cancel_job(get_persistent_storage_path(), pause_resume_job_id)
```

## Spec Changes

**[2025-12-27 15:15]** Implementation completed
- Added: `generate_endpoint_caller_js` import for "Run Selftest" button
- Fixed: Glob pattern bug in `_find_control_file()` - brackets must be escaped: `[[]` and `[]]`
- Fixed: Force cancel test - must cancel background task first to release file handle (Windows)
- Changed: Cat 6 Test 37 now cancels task2, then calls `force_cancel_job()` directly

**[2025-12-27 15:10]**
- Added: Issue 8 - verified multi-worker safety is NOT AN ISSUE (O_EXCL handles it)
- Removed: Over-engineered Issues 9-11 - standard cleanup pattern is sufficient

**[2025-12-27 15:05]**
- Added: "Execution Timeline" ASCII diagram showing job concurrency
- Added: "Job Summary" table (4 jobs: completed, pause_resume, cancel, running_for_delete)
- Changed: Merged Cat 4 + Cat 6 control error cases (Tests 21, 26 now in Cat 4)
- Changed: Cat 4 renamed to "Control - Pause/Resume with Error Cases" (10 tests)
- Changed: Cat 6 reduced to 4 tests, Cat 7 expanded to 8 tests
- Fixed: Issues 4, 5 marked as RESOLVED

**[2025-12-27 15:00]**
- Added: "Known Issues and Fixes" section
- Fixed: Background job pause handling
- Added: Race condition mitigation with retry loops
- Changed: Reordered Cat 4/6 tests for proper state setup
- Added: Missing /results error cases (Test 10b, 10c)
- Changed: Test count 44 -> 46

**[2025-12-27 14:50]**
- Initial specification created
