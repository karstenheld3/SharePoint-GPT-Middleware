# Job State Event Implementation Plan

**Goal**: Emit `state_json` SSE events when job state changes, enabling JavaScript UI to update console buttons and job table rows reactively.

**Target files**:
- `src/routers_v2/common_job_functions_v2.py` - Core implementation (emit_state, check_control)
- `src/routers_v2/common_ui_functions_v2.py` - JavaScript handlers (handleSSEData, handleStateChange)
- `src/routers_v2/jobs.py` - Jobs-specific row updates (onJobStateChange)

**Depends on:**
- `_V2_SPEC_ROUTERS.md` for SSE event format
- `_V2_SPEC_COMMON_UI_FUNCTIONS.md` for console JS patterns

## Table of Contents

1. Overview
2. SSE Protocol Extension
3. Python Implementation Changes
4. JavaScript Implementation Changes
5. Router-Specific Changes
6. Implementation Steps
7. Corner Cases and Handling
8. Verification Checklist

## 1. Overview

### Current Behavior

When a job is paused/resumed/cancelled via `check_control()`:
1. A `log` event is emitted: `[2025-12-27 14:14:32] Pause requested, pausing...`
2. Job file is renamed (`.running` -> `.paused`)
3. JavaScript has no structured way to detect state change
4. Console buttons remain in previous state until manual refresh

### Target Behavior

When a job state changes:
1. A `state_json` event is emitted with structured data
2. A `log` event is emitted (unchanged, for human readability)
3. JavaScript parses `state_json` and updates:
   - Console Pause/Resume button state
   - Console Cancel button state (disabled after cancel)
   - Job table row (jobs router only)

## 2. SSE Protocol Extension

### New Event Type: `state_json`

**Format:**
```
event: state_json
data: {"state": "paused", "job_id": "jb_28"}

```

**States:**
- `running` - Job is actively processing (emitted on resume)
- `paused` - Job is paused, waiting for resume or cancel
- `cancelled` - Job was cancelled by user

**Fields:**
- `state` (required): Current job state
- `job_id` (required): Job identifier (e.g., `jb_28`)

**Emission points:**
- Pause detected: emit `state_json` with `state: "paused"` before entering pause loop
- Resume detected: emit `state_json` with `state: "running"` after exiting pause loop
- Cancel detected: emit `state_json` with `state: "cancelled"` before returning CANCEL action

**Event ordering:**
```
event: state_json
data: {"state": "paused", "job_id": "jb_28"}

event: log
data: [2025-12-27 14:14:32] Pause requested, pausing...

```

The `state_json` event is emitted BEFORE the corresponding `log` event so UI updates before log appears.

## 3. Python Implementation Changes

### 3.1 StreamingJobWriter (common_job_functions_v2.py)

**Add new method:**
```python
def emit_state(self, state: str) -> str:
  """
  Emit state_json event for UI synchronization.
  Writes to job file (for reconnect replay) and returns SSE-formatted string.
  """
  data = {"state": state, "job_id": self._job_id}
  sse = self._format_sse_event("state_json", json.dumps(data))
  self._write_immediate(sse)  # Write to file so reconnect can replay
  return sse
```

**Note:** Uses `_write_immediate()` not `_write_buffered()` because state changes are critical events that must persist immediately.

**Modify check_control() async generator:**

Current flow:
```python
# On pause
yield sse  # log event only

# On resume  
yield sse  # log event only

# On cancel
yield ControlAction.CANCEL
```

New flow:
```python
# On pause
yield self.emit_state("paused")  # NEW: state event first
yield sse  # log event

# On resume
yield self.emit_state("running")  # NEW: state event first
yield sse  # log event

# On cancel (from running state)
yield self.emit_state("cancelled")  # NEW: state event before action
yield ControlAction.CANCEL
# Note: No separate log event for cancel - the end_json will contain "cancelled by user"

# On cancel (from pause loop)
yield self.emit_state("cancelled")  # NEW: state event
yield ControlAction.CANCEL
```

**Design Decision DD-01:** Cancel does not emit a separate log event like pause/resume. The `state_json` event provides immediate UI feedback, and the `end_json` event (emitted by caller after receiving `ControlAction.CANCEL`) contains the final result message.

### 3.2 Caller Pattern (all streaming routers)

No changes needed to caller pattern - the async generator already yields all items:
```python
async for item in writer.check_control():
  if isinstance(item, ControlAction):
    control_action = item
  else:
    yield item  # Yields both state_json and log events
```

## 4. JavaScript Implementation Changes

### 4.1 Console JS (common_ui_functions_v2.py > generate_console_js)

**Add state_json handler in handleSSEData():**

Current:
```javascript
function handleSSEData(eventType, data) {
  if (eventType === 'start_json') { ... }
  else if (eventType === 'log') { ... }
  else if (eventType === 'end_json') { ... }
}
```

New:
```javascript
function handleSSEData(eventType, data) {
  if (eventType === 'start_json') { ... }
  else if (eventType === 'state_json') {
    try {
      const state = JSON.parse(data);
      handleStateChange(state);
    } catch (e) {
      console.error('Failed to parse state_json:', e);
    }
  }
  else if (eventType === 'log') { ... }
  else if (eventType === 'end_json') { ... }
}
```

**Add handleStateChange() function (do NOT modify updatePauseResumeButton):**

Keep existing `updatePauseResumeButton()` unchanged (it reads from `isPaused` flag).
The new `handleStateChange()` updates the `isPaused` flag and then calls existing function:

```javascript
function handleStateChange(stateData) {
  // Update isPaused flag based on state
  if (stateData.state === 'paused') {
    isPaused = true;
  } else if (stateData.state === 'running') {
    isPaused = false;
  } else if (stateData.state === 'cancelled') {
    isPaused = false;
  }
  
  // Update buttons using existing function
  updatePauseResumeCancelButtons();
  
  // Disable cancel button if cancelled
  const cancelBtn = document.getElementById('btn-cancel');
  if (cancelBtn && stateData.state === 'cancelled') {
    cancelBtn.disabled = true;
  }
  
  // Notify router-specific handler if exists
  if (typeof onJobStateChange === 'function') {
    onJobStateChange(stateData.job_id, stateData.state);
  }
}
```

**Rationale:** Keeps backward compatibility with existing no-arg calls to `updatePauseResumeButton()`.

### 4.2 Jobs Router JS (jobs.py > get_router_specific_js)

**Add onJobStateChange() callback:**
```javascript
function onJobStateChange(jobId, state) {
  // Update job in local state
  const job = jobsState.get(jobId);
  if (job) {
    job.state = state;
    // Re-render just this row for efficiency
    const rowId = 'job-' + sanitizeId(jobId);
    const row = document.getElementById(rowId);
    if (row) {
      row.outerHTML = renderJobRow(job);
    }
    // Update count display
    updateSelectedCount();
  }
}
```

### 4.3 Other Routers (demorouter1, demorouter2, reports)

These routers do not display job lists, so no `onJobStateChange()` callback is needed. The default console button updates from `handleStateChange()` are sufficient.

## 5. Router-Specific Changes

### 5.1 common_job_functions_v2.py

| Location | Change |
|----------|--------|
| `StreamingJobWriter` class | Add `emit_state(state: JobState) -> str` method |
| `check_control()` pause branch | Yield `emit_state("paused")` before log |
| `check_control()` resume branch | Yield `emit_state("running")` before log |
| `check_control()` cancel branch | Yield `emit_state("cancelled")` before ControlAction |

### 5.2 common_ui_functions_v2.py

| Location | Change |
|----------|--------|
| `generate_console_js()` | Add `state_json` case in `handleSSEData()` with try/catch |
| `generate_console_js()` | Add `handleStateChange(stateData)` function after `updatePauseResumeButton()` |

### 5.3 jobs.py

| Location | Change |
|----------|--------|
| `get_router_specific_js()` | Add `onJobStateChange(jobId, state)` function |

### 5.4 demorouter1.py, demorouter2.py, reports.py

- **demorouter1.py**: Has own copy of console JS. Left unchanged (acceptable: buttons won't auto-update on state change, but still functional).
- **demorouter2.py, reports.py**: Use `generate_console_js()` from common_ui_functions_v2.py - automatically get updates.

## 6. Implementation Steps

### Step 1: Add emit_state() to StreamingJobWriter
- File: `common_job_functions_v2.py`
- Add `emit_state(state: JobState) -> str` method
- Uses existing `_format_sse_event()` helper

### Step 2: Modify check_control() to yield state events
- File: `common_job_functions_v2.py`
- Pause branch: yield state before log
- Resume branch: yield state before log
- Cancel branch: yield state before ControlAction

### Step 3: Add state_json handler to console JS
- File: `common_ui_functions_v2.py`
- Add `state_json` case in `handleSSEData()` with try/catch
- Add `handleStateChange(stateData)` function (do NOT modify `updatePauseResumeButton()`)

### Step 4: Add onJobStateChange callback to jobs router
- File: `jobs.py`
- Add `onJobStateChange(jobId, state)` in router-specific JS
- Updates job state and re-renders affected row

### Step 5: Test all streaming endpoints
- Test pause/resume/cancel on each router
- Verify console buttons update correctly
- Verify jobs table row updates (jobs router only)

## 7. Corner Cases and Handling

### 7.1 Timing and Race Conditions

| Corner Case | Scenario | Handling |
|-------------|----------|----------|
| **Rapid pause/resume** | User clicks Pause then Resume within 100ms | Each click creates control file; `check_control()` processes them in order; UI receives both `state_json` events sequentially; final state is correct |
| **Pause during iteration** | Pause requested mid-loop, between `check_control()` calls | Current item completes, pause detected on next `check_control()` call; no partial processing |
| **Cancel during pause loop** | Job is paused, user clicks Cancel | Cancel file detected inside pause loop; `state_json(cancelled)` emitted; `ControlAction.CANCEL` returned |
| **Double cancel click** | User clicks Cancel twice quickly | First click creates control file; job processes it and deletes file; second click has no file to create (job already exiting); no duplicate events |
| **Button click during network lag** | User clicks Pause but SSE stream is delayed | Control file created immediately; job pauses; `state_json` eventually arrives; UI may show stale state for 0-2 seconds |

### 7.2 Stream Connection Issues

| Corner Case | Scenario | Handling |
|-------------|----------|----------|
| **Stream disconnects mid-pause** | Browser loses connection while job is paused | Job continues waiting in pause loop; reconnecting via Monitor shows current file content (no live `state_json`); buttons reflect file extension state on page load |
| **Reconnect after state change** | User reconnects after pause/resume occurred | Monitor endpoint streams full file content including past `state_json` events; JS replays all events; final button state is correct |
| **Multiple tabs monitoring** | Two browser tabs monitoring same job | Both receive `state_json` via their own streams; both UIs update; control from either tab affects job |
| **Tab monitors wrong job** | User starts monitoring jb_28, then clicks control for jb_29 in table | `currentJobId` tracks console job; control buttons use `currentJobId`; table row buttons use their own `data-url`; no cross-contamination |

### 7.3 Job State Edge Cases

| Corner Case | Scenario | Handling |
|-------------|----------|----------|
| **Monitor completed job** | User clicks Monitor on already-completed job | Stream returns full file content ending with `end_json`; no `state_json` emitted (job not running); buttons disabled after `end_json` |
| **Monitor cancelled job** | User clicks Monitor on already-cancelled job | Same as completed; `end_json` with `cancelled` state; buttons disabled |
| **Pause on stalled job** | Job is stalled (not calling `check_control()`), user clicks Pause | Control file created but never processed; job remains stalled; UI shows Pause requested but no `state_json` arrives; user must Force Cancel |
| **Force cancel stalled job** | Job stalled, user clicks Force Cancel | `force_cancel_job()` renames file directly; no `state_json` emitted (no active stream); table row updates via JSON response; console shows no change (stream is dead) |
| **Job ends while paused** | Impossible scenario | Job cannot end while paused; pause loop blocks until resume or cancel; not a valid state |

### 7.4 UI State Edge Cases

| Corner Case | Scenario | Handling |
|-------------|----------|----------|
| **Console hidden during state change** | User hides console, state changes, user shows console | Buttons updated in DOM regardless of visibility; correct state when shown |
| **No Pause/Resume buttons** | Console panel rendered without `include_pause_resume_cancel=False` | `handleStateChange()` checks `getElementById()` returns null; no error; graceful no-op |
| **Job row not in table** | `onJobStateChange()` called for job not in `jobsState` Map | `jobsState.get(jobId)` returns undefined; function exits early; no error |
| **Job row not rendered** | Job in `jobsState` but DOM row missing (scroll virtualization future) | `getElementById()` returns null; state updated in Map but DOM not touched; next full render will be correct |
| **Page refresh during pause** | User refreshes page while job is paused | Fresh page load; job list fetched via JSON; row shows "paused" from file extension; Monitor reconnects and receives file content |

### 7.5 Protocol Edge Cases

| Corner Case | Scenario | Handling |
|-------------|----------|----------|
| **Malformed state_json** | Bug causes invalid JSON in `state_json` data | `JSON.parse()` throws; wrap in try/catch; log error to console; skip state update; UI remains in previous state |
| **Unknown state value** | Future state like "queued" sent | `handleStateChange()` doesn't match any case; buttons unchanged; graceful degradation |
| **Missing job_id field** | Bug omits `job_id` from `state_json` | `onJobStateChange()` called with undefined; `jobsState.get(undefined)` returns undefined; no row update; console buttons still update |
| **state_json before start_json** | Bug in event ordering | Should not happen; if it does, `currentJobId` may be null; `onJobStateChange()` receives null; graceful no-op |
| **Duplicate state_json** | Same state emitted twice | UI receives both; second one is no-op (button already in correct state); no harm |

### 7.6 Jobs Router Specific

| Corner Case | Scenario | Handling |
|-------------|----------|----------|
| **Monitor job not in current list** | User monitors old job not in visible table | `onJobStateChange()` finds no job in `jobsState`; console buttons update; no table row update; correct behavior |
| **Bulk delete includes monitored job** | User deletes job while monitoring it | Job file deleted; stream ends abruptly (read error or EOF); `end_json` may not arrive; buttons remain in last state; next action will fail gracefully |
| **Row checkbox during state change** | Checkbox selected, state changes, row re-renders | `renderJobRow()` creates fresh checkbox (unchecked); selection lost; acceptable trade-off for simplicity |
| **Concurrent monitors** | User monitors jb_28 in console, then clicks Monitor on jb_29 | `connectStream()` replaces current stream; `currentJobId` updated to jb_29; old stream closed; buttons now track jb_29 |

### 7.7 Summary: Error Handling Strategy

**JavaScript errors:**
- Wrap `JSON.parse()` in try/catch
- Check `getElementById()` return value before use
- Check `jobsState.get()` return value before use
- Use `typeof onJobStateChange === 'function'` before calling

**Python errors:**
- `emit_state()` uses same `_format_sse_event()` as other events (proven code)
- `check_control()` already handles file operations with error tolerance
- No new error paths introduced

**Recovery strategy:**
- UI in wrong state -> User clicks button -> Control file created -> Next `check_control()` fixes state
- Stream dies -> User clicks Monitor again -> Full replay corrects UI
- Worst case -> User refreshes page -> Fresh state from server

## 8. Verification Checklist

### Protocol Verification

- [ ] `state_json` event emitted BEFORE `log` event on pause
- [ ] `state_json` event emitted BEFORE `log` event on resume
- [ ] `state_json` event emitted BEFORE `ControlAction.CANCEL` on cancel
- [ ] `state_json` data contains `state` field with correct value
- [ ] `state_json` data contains `job_id` field matching current job
- [ ] Event format follows SSE spec: `event:` line, `data:` line, blank line

### Console UI Verification (all routers)

- [ ] **Pause**: Click Pause -> button changes to "Resume" immediately
- [ ] **Resume**: Click Resume -> button changes to "Pause" immediately
- [ ] **Cancel**: Click Cancel -> Pause button disabled, Cancel button disabled
- [ ] **End of job**: Buttons reset to initial state after `end_json`

### Jobs Router Table Verification

- [ ] **Pause from console**: Job row State column updates to "paused"
- [ ] **Resume from console**: Job row State column updates to "running"
- [ ] **Cancel from console**: Job row State column updates to "cancelled"
- [ ] **Action buttons**: Row action buttons update (Pause->Resume, etc.)

### Router Test Matrix

| Router | Endpoint | Pause | Resume | Cancel | Row Update |
|--------|----------|-------|--------|--------|------------|
| demorouter1 | /create_demo_items | [ ] | [ ] | [ ] | N/A |
| demorouter2 | /create_demo_items | [ ] | [ ] | [ ] | N/A |
| reports | /create_demo_reports | [ ] | [ ] | [ ] | N/A |
| jobs | /monitor (monitoring any job) | [ ] | [ ] | [ ] | [ ] |

### Edge Cases

- [ ] Rapid pause/resume clicks do not cause UI desync
- [ ] State events work when monitoring completed/cancelled jobs (no-op)
- [ ] Multiple browser tabs monitoring same job receive state updates
- [ ] Console panel hidden during state change -> buttons correct when shown

### File Modification Summary

| File | Lines Changed (est.) | Type |
|------|---------------------|------|
| `common_job_functions_v2.py` | ~20 | Core logic (emit_state + check_control) |
| `common_ui_functions_v2.py` | ~25 | JavaScript (handleSSEData + handleStateChange) |
| `jobs.py` | ~15 | Router JS (onJobStateChange) |
| **Total** | ~60 | |

## Spec Changes

- 2025-12-27: Initial implementation plan created
- 2025-12-27: Review fixes applied:
  - Added `_write_immediate()` to `emit_state()` for reconnect replay
  - Added try/catch to `state_json` handler in JS
  - Fixed `handleStateChange()` to update `isPaused` flag instead of changing `updatePauseResumeButton()` signature
  - Added DD-01 design decision for cancel not emitting log event
  - demorouter1.py left unchanged (has own JS copy, acceptable degraded behavior)
