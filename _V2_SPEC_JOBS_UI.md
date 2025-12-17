# V2 Jobs UI Specification

This document specifies the HTMX-based User Interface for the `/v2/jobs?format=ui` endpoint.

**Depends on:** `_V2_SPEC_ROUTERS.md` for streaming job infrastructure, SSE format, and job file specifications.

## Overview

A reactive web UI for monitoring and controlling long-running jobs using HTMX SSE extension for real-time streaming updates. The UI displays a job list table with actions and a resizable console panel for viewing job output streams.

**Key Technologies:**
- HTMX core for declarative HTTP interactions
- HTMX SSE extension (`sse.js`) for Server-Sent Events
- Minimal JavaScript for state management and JSON parsing
- CSS for styling (reuses `/static/css/styles.css`)

## Scenario

**Problem:** Administrators need to monitor long-running operations (crawling, vector store operations) without requiring programming skills or external tools.

**Solution:** A browser-based UI that:
- Lists all jobs with their current state
- Allows real-time monitoring of job output via SSE streaming
- Provides pause/resume/cancel controls for active jobs
- Shows toast notifications for job state changes

**What we don't want:**
- Custom JavaScript fetch/streaming implementation (use HTMX SSE instead)
- Polling-based updates (use SSE push)
- Multiple simultaneous job monitors (one console, one active stream)

## Domain Object Model

**Job** (as displayed in UI)
- `job_id` - Unique identifier (e.g., "jb_42")
- `state` - Current state: "running", "paused", "completed", "cancelled"
- `source_url` - Original URL that started the job
- `monitor_url` - URL to monitor this job's stream
- `started_utc` - ISO timestamp when job started
- `finished_utc` - ISO timestamp when job finished (null if running)
- `result` - Result object with `{ok, error, data}` (null if running)

**SSE Event Types**
- `start_json` - Job metadata at stream start (JSON)
- `log` - Log line (plain text)
- `end_json` - Job metadata at stream end (JSON)

**Connection State**
- `disconnected` - No active SSE connection
- `connecting` - SSE connection being established
- `connected` - SSE connection active, receiving events
- `error` - SSE connection failed

## User Actions

1. **View job list** - Page load: server returns HTML with empty table, JavaScript fetches `/v2/jobs?format=json` on DOMContentLoaded and renders rows
2. **Refresh job list** - Click [Refresh] to fetch jobs and re-render table (preserves console connection and output)
3. **Monitor job** - Click [Monitor] to connect SSE stream and show console
4. **Pause job** - Click [Pause] on running job to request pause
5. **Resume job** - Click [Resume] on paused job to request resume
6. **Cancel job** - Click [Cancel] on running/paused job to request cancellation
7. **Disconnect console** - Click [Disconnect] to close SSE connection
8. **Clear console** - Click [Clear] to empty console output
9. **Resize console** - Drag resize handle to adjust console height (min: 45px, max: viewport height - 30px)
10. **Select jobs** - Click checkbox to select jobs for bulk operations
11. **Bulk delete** - Click [Delete Selected] to delete all selected jobs

## UX Design

Note: Started and Finished columns display datetime in ISO format (YYYY-MM-DD HH:MM:SS), shown as "..." below for brevity.

```
main page: /v2/jobs?format=ui
+-------------------------------------------------------------------------------------------------------------------------------------+
| Jobs (4)                                                                                            [Delete Selected (0)] [Refresh] |
| <- Back to main page                                                                                                                |
|                                                                                                                                     |
| +---+-------+-----------+---------------------+----------+-----------+---------+----------+---------------------------------------+ |
| |[ ]| ID    | Router    | Endpoint            | Objects  | State     | Started | Finished | Actions                               | |
| +---+-------+-----------+---------------------+----------+-----------+---------+----------+---------------------------------------+ |
| |[ ]| jb_44 | crawler   | crawl               | DOMAIN01 | running   | ...     | -        | [Monitor] [Pause] [Cancel]            | |
| |[ ]| jb_43 | crawler   | crawl               | DOMAIN02 | paused    | ...     | -        | [Monitor] [Resume] [Cancel]           | |
| |[x]| jb_42 | crawler   | crawl               | DOMAIN01 | completed | ...     | ...      | [View] [Result] [Monitor]             | |
| |[ ]| jb_41 | inventory | vector_stores/files | vs_123   | completed | ...     | ...      | [View] [Result] [Monitor]             | |
| |   |       |           |                     | file_abc |           |         |          |                                       | |
| +---+-------+-----------+---------------------+----------+-----------+---------+----------+---------------------------------------+ |
|                                                                                                                                     |
+-- [Resize Handle] ------------------------------------------------------------------------------------------------------------------+
| Console Output (connected): Job ID='jb_44'                                                                     [Pause] [Clear]  [X] |
|-------------------------------------------------------------------------------------------------------------------------------------+
| [ 1 / 20 ] Processing 'document_001.pdf'...                                                                                         |
|   OK.                                                                                                                               |
| [ 2 / 20 ] Processing 'document_002.pdf'...                                                                                         |
|   OK.                                                                                                                               |
| [ 3 / 20 ] Processing 'document_003.pdf'...                                                                                         |
|                                                                                                                                     |
+-------------------------------------------------------------------------------------------------------------------------------------+

Toast Container (top-right, fixed position):
+-----------------------------------------------+
| Job Started: ID='jb_44'                  [x]  |
+-----------------------------------------------+
```

## Key Mechanisms and Design Decisions

### SSE Format (Server -> Client)

Server sends standard SSE format with named events.

**Multiline Events:** Uses standard SSE multiline format (multiple `data:` lines). HTMX SSE extension automatically joins multiline `data:` lines with newlines. No XML tags.

```
event: start_json
data: {"job_id": "jb_42", "state": "running", "source_url": "...", "monitor_url": "...", "started_utc": "...", "finished_utc": null, "result": null}

event: log
data: [ 1 / 20 ] Processing 'document.pdf'...

event: log
data:   OK.

event: log
data: Summary:
data:   Files processed: 20
data:   Files failed: 2

event: end_json
data: {"job_id": "jb_42", "state": "completed", "source_url": "...", "monitor_url": "...", "started_utc": "...", "finished_utc": "...", "result": {"ok": true, "error": "", "data": {...}}}

```

### HTMX SSE Connection

The console panel uses HTMX SSE extension for connection management:
```html
<div id="sse-container" hx-ext="sse">
  <!-- sse-connect attribute added dynamically when user clicks Monitor -->
  <pre id="console-output" sse-swap="log" hx-swap="beforeend"></pre>
</div>
```

### Connection Lifecycle

1. **Connect** - User clicks [Monitor] -> JavaScript sets `sse-connect` attribute -> HTMX establishes EventSource
2. **Receive** - `log` events automatically appended to console via `sse-swap`
3. **JSON events** - `start_json`/`end_json` intercepted via `htmx:sseBeforeMessage` for parsing
4. **Disconnect** - Any of:
   - User clicks [Disconnect] -> JavaScript removes `sse-connect` attribute
   - `end_json` received -> Auto-disconnect after processing
   - User navigates away -> HTMX cleans up EventSource

### Action Buttons Per State

```
running:   [View] [Monitor] [Pause] [Cancel]
paused:    [View] [Monitor] [Resume] [Cancel]
completed: [View] [Result] [Monitor]
cancelled: [View] [Result] [Monitor]
```

- `[Result]` always available for terminal states (completed/cancelled) - shows JSON from `/v2/jobs/results`
- `[Monitor]` available for all states - shows historical log for completed/cancelled jobs

### Job Table Data Source

**Initial Page Load (Option B):**
1. Server returns HTML page with empty `<tbody id="jobs-tbody">`
2. On `DOMContentLoaded`, JavaScript fetches `/v2/jobs?format=json`
3. JavaScript renders job rows into tbody

`GET /v2/jobs?format=json` returns standard JSON result where `data` is the array of jobs:
```json
{
  "ok": true,
  "error": "",
  "data": [
    {"job_id": "jb_44", "state": "running", "source_url": "...", "monitor_url": "...", "started_utc": "...", "finished_utc": null, "result": null},
    {"job_id": "jb_43", "state": "paused", "source_url": "...", "monitor_url": "...", "started_utc": "...", "finished_utc": null, "result": null},
    {"job_id": "jb_42", "state": "completed", "source_url": "...", "monitor_url": "...", "started_utc": "...", "finished_utc": "...", "result": {"ok": true, "error": "", "data": {...}}}
  ]
}
```

For completed/failed/cancelled jobs, the job object contains `finished_utc` and `result`.
For running/paused jobs, `finished_utc` and `result` are null.

### Job Control via HTMX

Control buttons use standard HTMX GET requests:
```html
<button hx-get="/v2/jobs/control?job_id=jb_44&action=pause" 
        hx-swap="none"
        hx-on::after-request="handleControlResponse(event)">Pause</button>
```

### Toast Notifications

Toasts shown for:
- `start_json` received (info): "Job Started | jb_44"
- `end_json` received (success/error based on result): "Job Completed | jb_44"
- Control action success (info): "Pause requested for jb_44"
- SSE connection error (error): "Connection failed"

**Suppress toasts when monitoring historical job:**
- When clicking [Monitor] on completed/cancelled job, suppress `start_json`/`end_json` toasts
- Prevents toast spam when loading historical logs
- Implementation: `suppressToasts` flag, set `true` on monitor, `false` on live stream

**Security:** Use `escapeHtml()` for toast content:
```javascript
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
```

### Error Handling for Control Actions

When `/v2/jobs/control` returns `ok: false`, show a **modal dialog** (not a toast):
```
+------------------------------------------+
|  Control Action Failed              [x]  |
+------------------------------------------+
|  Action: pause                           |
|  Job: jb_44                              |
|                                          |
|  Error: Job 'jb_44' is already paused.   |
|                                          |
|                              [OK]        |
+------------------------------------------+
```

Modal populated from response JSON:
```json
{"ok": false, "error": "Job 'jb_44' is already paused.", "data": {"job_id": "jb_44", "action": "pause"}}
```

### Modal Dialog Behavior

The `#modal` element is used by [View], [Result] buttons and error dialogs.

**HTML Structure:**
```html
<div id="modal" class="modal-overlay" onclick="closeModalOnBackdrop(event)">
  <div class="modal-content">
    <button class="modal-close" onclick="closeModal()">×</button>
    <div class="modal-body">
      <!-- Content injected by HTMX or JavaScript -->
    </div>
  </div>
</div>
```

**[View] Button Example:**
```html
<button class="btn-small" hx-get="/v2/jobs/get?job_id=jb_44&format=html" hx-target="#modal .modal-body" hx-swap="innerHTML" onclick="openModal()">View</button>
```

**[Result] Button Example:**
```html
<button class="btn-small" hx-get="/v2/jobs/results?job_id=jb_44&format=html" hx-target="#modal .modal-body" hx-swap="innerHTML" onclick="openModal()">Result</button>
```

**JavaScript Functions:**
```javascript
function openModal() {
  document.getElementById('modal').classList.add('visible');
  document.addEventListener('keydown', handleEscapeKey);
}

function closeModal() {
  document.getElementById('modal').classList.remove('visible');
  document.removeEventListener('keydown', handleEscapeKey);
}

function closeModalOnBackdrop(event) {
  if (event.target.classList.contains('modal-overlay')) closeModal();
}

function handleEscapeKey(event) {
  if (event.key === 'Escape') closeModal();
}

// For error modals (control action failures)
function showErrorModal(response) {
  const body = document.querySelector('#modal .modal-body');
  body.innerHTML = `
    <h3>Control Action Failed</h3>
    <p><strong>Action:</strong> ${response.data?.action || 'unknown'}</p>
    <p><strong>Job:</strong> ${response.data?.job_id || 'unknown'}</p>
    <p><strong>Error:</strong> ${response.error}</p>
    <button class="btn-small" onclick="closeModal()">OK</button>
  `;
  openModal();
}
```

**CSS (added to inline styles):**
```css
.modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 1100; }
.modal-overlay.visible { display: flex; justify-content: center; align-items: center; }
.modal-content { background: #fff; padding: 1.5rem; border-radius: 8px; max-width: 600px; max-height: 80vh; overflow: auto; position: relative; }
.modal-close { position: absolute; top: 0.5rem; right: 0.5rem; background: none; border: none; font-size: 1.5rem; cursor: pointer; }
```

### Job Row Updates

Job table rows are updated in two scenarios:

**1. Control action success (pause/resume/cancel)**

When `/v2/jobs/control` returns `ok: true`, optimistically update the row:
```javascript
function handleControlResponse(event) {
  const response = JSON.parse(event.detail.xhr.responseText);
  if (response.ok) {
    const { job_id, action } = response.data;
    // Optimistic state update based on action
    const newState = action === 'pause' ? 'paused' 
                   : action === 'resume' ? 'running' 
                   : action === 'cancel' ? 'cancelled' : null;
    if (newState) {
      updateJob(job_id, { state: newState });
    }
    showToast(`${action} requested`, job_id, 'info');
  } else {
    showErrorModal(response);  // Modal for errors
  }
}
```

Note: This is optimistic - the actual state change happens when the job processes the control file. For cancel, the job may still emit `end_json` with final result before terminating.

**2. Monitored job state change (start_json/end_json received)**

When SSE events arrive, update the corresponding job row:
```javascript
function handleSseEvent(event) {
  const eventType = event.detail.type;  // 'start_json' or 'end_json'
  const data = JSON.parse(event.detail.data);
  
  if (eventType === 'start_json') {
    updateJob(data.job_id, { state: data.state });
    showToast('Job Started', data.job_id, 'info');
  }
  
  if (eventType === 'end_json') {
    updateJob(data.job_id, { 
      state: data.state, 
      finished_utc: data.finished_utc,
      result: data.result 
    });
    showToast('Job Finished', data.job_id, data.result?.ok ? 'success' : 'error');
    disconnectStream();  // Auto-disconnect on completion
  }
}

// Register handler
document.body.addEventListener('htmx:sseBeforeMessage', handleSseEvent);
```

**Row re-rendering on update:**
- `updateJob()` merges new properties into `jobsState` Map entry
- Calls `renderAllJobs()` which re-renders entire table
- Action buttons change based on new state (see "Action Buttons Per State")

### Empty State

When no jobs exist, show message row:
```html
<tr><td colspan="9" class="empty-state">No jobs found</td></tr>
```

### Console Behavior

- Single console panel, one active stream at a time
- Console output truncation: max 1,000,000 characters, prefix with "...[truncated]\n" when exceeded
- Clicking [Monitor] on different job disconnects current stream, connects to new one
- Console title shows connection state and job: "Console Output (connected): Job ID='jb_44'"
- [Clear] empties console but keeps connection
- [Disconnect] closes connection and clears console title (content remains until next [Monitor] click)
- Auto-scroll to bottom on new log lines during active streaming

### Timestamp Formatting

API returns ISO 8601 UTC timestamps (`2025-01-15T14:20:30.000000Z`). UI converts to local timezone with fixed format:

```javascript
function formatTimestamp(ts) {
  if (!ts) return '-';
  const date = new Date(ts);
  const pad = (n) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}
```

**Format:** `YYYY-MM-DD HH:MM:SS` (local timezone, 24-hour)

**Examples (browser in UTC+1):**
- API: `2025-01-15T14:20:30.000000Z` → Display: `2025-01-15 15:20:30`
- Null/empty → Display: `-`

### Parsing source_url for Display

The `source_url` is parsed client-side to extract display columns:

```javascript
function parseSourceUrl(source_url) {
  // Example: "/v2/crawler/crawl?domain_id=DOMAIN01&format=stream"
  // Example: "/v2/inventory/vector_stores/files/delete?vector_store_id=vs_123&file_id=file_abc"
  
  const url = new URL(source_url, window.location.origin);
  const pathParts = url.pathname.split('/').filter(p => p && p !== 'v2');
  
  const router = pathParts[0];                    // "crawler" or "inventory"
  const endpoint = pathParts.slice(1).join('/');  // "crawl" or "vector_stores/files/delete"
  
  // Extract all params ending with _id (except format)
  const objectIds = [];
  for (const [key, value] of url.searchParams) {
    if (key.endsWith('_id') && key !== 'format') {
      objectIds.push(value);
    }
  }
  
  return { router, endpoint, objectIds };
}
```

**Examples:**
- `/v2/crawler/crawl?domain_id=DOMAIN01&format=stream` -> router: `crawler`, endpoint: `crawl`, objects: `[DOMAIN01]`
- `/v2/inventory/vector_stores/files/delete?vector_store_id=vs_123&file_id=file_abc` -> router: `inventory`, endpoint: `vector_stores/files/delete`, objects: `[vs_123, file_abc]`

### Bulk Delete

- Checkboxes in first column allow selecting multiple jobs
- [Delete Selected (N)] button shows count of selected jobs
- Button disabled when N=0
- Click triggers confirmation dialog: "Delete N selected jobs?"
- On confirm: sends DELETE requests sequentially for each selected job_id
- Jobs deleted via `DELETE /v2/jobs/delete?job_id={id}`
- **Error handling:** Failed deletes remain in list with toast error; succeeded deletes removed from table immediately

**Bulk Delete Flow:**
```javascript
async function bulkDelete() {
  const selected = getSelectedJobIds();
  if (selected.length === 0) return;
  if (!confirm(`Delete ${selected.length} selected jobs?`)) return;
  
  for (const jobId of selected) {
    const response = await fetch(`/v2/jobs/delete?job_id=${jobId}`, { method: 'DELETE' });
    const result = await response.json();
    if (result.ok) {
      jobsState.delete(jobId);
      showToast('Job Deleted', jobId, 'success');
    } else {
      showToast('Delete Failed', `${jobId}: ${result.error}`, 'error');
    }
  }
  renderAllJobs();
  updateSelectedCount();
}
```

**Toast Messages:**
- Success: title="Job Deleted", message="{job_id}", type="success"
- Error: title="Delete Failed", message="{job_id}: {error}", type="error"

## Action Flow

### Monitor Job
```
User clicks [Monitor] on job row (job_id = jb_44)
  |-> disconnectCurrentStream() if connected
  |-> Clear console output
  |-> Set console title to "Console Output (connecting): Job ID='jb_44'"
  |-> Set sse-connect="/v2/jobs/monitor?job_id=jb_44&format=stream" on #sse-container
  |-> HTMX SSE extension creates EventSource
      |-> On htmx:sseOpen: Update console title to "Console Output (connected): Job ID='jb_44'"
      |-> On event "log": HTMX appends data to #console-output (via sse-swap)
      |-> On event "start_json": 
          |-> htmx:sseBeforeMessage handler parses JSON
          |-> showToast("Job Started", job_id, "info")
          |-> (data reflected in job row, then discarded)
      |-> On event "end_json":
          |-> htmx:sseBeforeMessage handler parses JSON
          |-> showToast("Job Finished", job_id, result.ok ? "success" : "error")
          |-> (data reflected in job row, then discarded)
          |-> disconnectCurrentStream() - auto-disconnect on completion
      |-> On htmx:sseError: showToast("Connection Error", message, "error")
```

### Pause Job
```
User clicks [Pause] on running job (job_id = jb_44)
  |-> HTMX sends GET /v2/jobs/control?job_id=jb_44&action=pause
  |-> Server creates .pause_requested control file
  |-> Server returns {"ok": true, "error": "", "data": {"job_id": "jb_44", "action": "pause", "message": "Pause requested for job 'jb_44'."}}
  |-> hx-on::after-request handler:
      |-> showToast("Pause Requested", "jb_44", "info")
      |-> Note: Actual state change happens when job processes the request
            and sends updated state via SSE stream
```

### Resume Job
```
User clicks [Resume] on paused job (job_id = jb_43)
  |-> HTMX sends GET /v2/jobs/control?job_id=jb_43&action=resume
  |-> Server creates .resume_requested control file
  |-> Server returns {"ok": true, "error": "", "data": {"job_id": "jb_43", "action": "resume", "message": "Resume requested for job 'jb_43'."}}
  |-> hx-on::after-request handler:
      |-> showToast("Resume Requested", "jb_43", "info")
```

### Cancel Job
```
User clicks [Cancel] on running/paused job (job_id = jb_44)
  |-> Browser shows confirm dialog: "Cancel job jb_44?"
  |-> If confirmed:
      |-> HTMX sends GET /v2/jobs/control?job_id=jb_44&action=cancel
      |-> Server creates .cancel_requested control file
      |-> Server returns {"ok": true, "error": "", "data": {"job_id": "jb_44", "action": "cancel", "message": "Cancel requested for job 'jb_44'."}}
      |-> hx-on::after-request handler:
          |-> showToast("Cancel Requested", "jb_44", "warning")
```

### Disconnect Console
```
User clicks [Disconnect]
  |-> disconnectCurrentStream()
      |-> Remove sse-connect attribute from #sse-container
      |-> HTMX SSE extension closes EventSource
      |-> Set console title to "Console Output (disconnected)"
      |-> Update connection state to "disconnected"
```

## Data Structures

### HTML Structure

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Jobs</title>
  <link rel="stylesheet" href="/static/css/styles.css">
  <script src="/static/js/htmx.js"></script>
  <script src="/static/js/sse.js"></script>
  <style>/* Console and toast styles */</style>
</head>
<body>
  <!-- Toast Container -->
  <div id="toast-container"></div>
  
  <!-- Main Content -->
  <div class="container">
    <h1>Jobs (<span id="job-count">4</span>)</h1>
    
    <div class="toolbar">
      <button id="btn-delete-selected" onclick="bulkDelete()" class="btn-small btn-delete" disabled>Delete Selected (0)</button>
      <button onclick="refreshJobs()" class="btn-small">Refresh</button>
    </div>
    
    <table>
      <thead>
        <tr>
          <th></th>
          <th>ID</th>
          <th>Router</th>
          <th>Endpoint</th>
          <th>Objects</th>
          <th>State</th>
          <th>Started</th>
          <th>Finished</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody id="jobs-tbody">
        <!-- Job rows rendered here -->
      </tbody>
    </table>
    
    <p><a href="/">← Back to main page</a></p>
  </div>
  
  <!-- Modal for View/Result -->
  <div id="modal"></div>
  
  <!-- Console Panel (always visible, fixed bottom) -->
  <div id="console-panel" class="console-panel">
    <div class="console-resize-handle"></div>
    <div class="console-header">
      <span id="console-title">Console Output (disconnected)</span>
      <div class="console-controls">
        <button onclick="disconnectStream()" class="btn-small" id="btn-disconnect" disabled>Disconnect</button>
        <button onclick="clearConsole()" class="btn-small">Clear</button>
      </div>
    </div>
    <div id="sse-container" hx-ext="sse">
      <pre id="console-output" class="console-output" sse-swap="log" hx-swap="beforeend"></pre>
    </div>
  </div>
  
  <script>
// Job state management
const jobsState = new Map();

// Fetch jobs on page load
document.addEventListener('DOMContentLoaded', async () => {
  const response = await fetch('/v2/jobs?format=json');
  const result = await response.json();
  if (result.ok) {
    result.data.forEach(job => jobsState.set(job.job_id, job));
    renderAllJobs();
  }
  initConsoleResize();
});

/* ... other functions: renderAllJobs, renderJobRow, updateJob, showToast, etc. */
</script>
</body>
</html>
```

### Job Row HTML

```html
<tr id="job-jb_44">
  <td><input type="checkbox" class="job-checkbox" data-job-id="jb_44" onchange="updateSelectedCount()"></td>
  <td>jb_44</td>
  <td>crawler</td>
  <td>crawl</td>
  <td>DOMAIN01</td>
  <td>running</td>
  <td>2025-01-15 14:20:30</td>
  <td>-</td>
  <td class="actions">
    <button class="btn-small" hx-get="/v2/jobs/get?job_id=jb_44&format=html" hx-target="#modal" hx-swap="innerHTML">View</button>
    <button class="btn-small" onclick="monitorJob('jb_44')">Monitor</button>
    <button class="btn-small" hx-get="/v2/jobs/control?job_id=jb_44&action=pause" hx-swap="none" hx-on::after-request="handleControlResponse(event)">Pause</button>
    <button class="btn-small btn-delete" hx-get="/v2/jobs/control?job_id=jb_44&action=cancel" hx-swap="none" hx-confirm="Cancel job jb_44?" hx-on::after-request="handleControlResponse(event)">Cancel</button>
  </td>
</tr>
```

### SSE Stream Format

```
event: start_json
data: {"job_id": "jb_44", "state": "running", "source_url": "/v2/crawler/crawl?domain_id=DOMAIN01&format=stream", "monitor_url": "/v2/jobs/monitor?job_id=jb_44&format=stream", "started_utc": "2025-01-15T14:20:30.000000Z", "finished_utc": null, "result": null}

event: log
data: [ 1 / 20 ] Processing 'document_001.pdf'...

event: log
data:   OK.

event: log
data: [ 2 / 20 ] Processing 'document_002.pdf'...

event: log
data:   OK.

event: end_json
data: {"job_id": "jb_44", "state": "completed", "source_url": "/v2/crawler/crawl?domain_id=DOMAIN01&format=stream", "monitor_url": "/v2/jobs/monitor?job_id=jb_44&format=stream", "started_utc": "2025-01-15T14:20:30.000000Z", "finished_utc": "2025-01-15T14:25:45.000000Z", "result": {"ok": true, "error": "", "data": {...}}}

```

## Implementation Details

### Python: SSE Response Generator

```python
# Generate SSE-formatted response for streaming endpoints
async def generate_sse_stream(job_id: str, ...):
  # Emit start_json
  yield f"event: start_json\ndata: {json.dumps(start_data)}\n\n"
  
  # Process items and emit log events
  for item in items:
    yield f"event: log\ndata: [ {i} / {total} ] Processing '{item}'...\n\n"
    # ... process ...
    yield f"event: log\ndata:   OK.\n\n"
  
  # Emit end_json
  yield f"event: end_json\ndata: {json.dumps(end_data)}\n\n"
```

### JavaScript: Core Functions

```javascript
// Connection state
let currentJobId = null;
let isConnected = false;

// Fetch jobs and re-render table (preserves console state)
async function refreshJobs() {
  const response = await fetch('/v2/jobs?format=json');
  const result = await response.json();
  if (result.ok) {
    jobsState.clear();
    result.data.forEach(job => jobsState.set(job.job_id, job));
    renderAllJobs();
  }
}

// Connect to job stream
function monitorJob(jobId) { ... }

// Disconnect current stream
function disconnectStream() { ... }

// Clear console output
function clearConsole() { ... }

// Show toast notification
function showToast(title, message, type = 'info', autoDismiss = 5000) { ... }

// Update job in state Map and re-render table
function updateJob(jobId, updates) {
  const job = jobsState.get(jobId);
  if (job) {
    Object.assign(job, updates);  // Merge updates: state, finished, etc.
    renderAllJobs();              // Re-render entire table
  }
}

// Handle SSE events (htmx:sseBeforeMessage listener)
function handleSseEvent(event) { ... }

// Handle control action response
function handleControlResponse(event) { ... }

// Initialize console resize
function initConsoleResize() { ... }
```

### CSS: Console and Toast Styles

```css
/* Toast container - fixed top-right */
#toast-container { position: fixed; top: 1rem; right: 1rem; z-index: 1000; }

/* Toast notification with colored left border */
.toast { /* Light background, border-left indicates type */ }
.toast.toast-info { border-left-color: #0078d4; }
.toast.toast-success { border-left-color: #28a745; }
.toast.toast-error { border-left-color: #dc3545; }
.toast.toast-warning { border-left-color: #ffc107; }

/* Console panel - fixed bottom, always visible */
.console-panel { position: fixed; bottom: 0; left: 0; right: 0; height: 232px; display: flex; flex-direction: column; }

/* Main content padding to avoid console overlap */
.container { padding-bottom: 250px; }

/* Resize handle */
.console-resize-handle { height: 4px; cursor: ns-resize; }

/* Console output - monospace, dark background */
.console-output { font-family: 'Consolas', monospace; background: #012456; color: #fff; }
```

## Spec Changes

**[2025-12-15 13:57]**
- Added: "Empty State" section - "No jobs found" message row
- Added: Console output truncation (max 1M chars)
- Added: Suppress toasts when monitoring historical job
- Added: `escapeHtml()` security function for toast content
- Added: Console resize bounds (min: 45px, max: viewport - 30px)

**[2025-12-15 13:53]**
- Added: "Timestamp Formatting" section - converts UTC to local timezone with fixed format `YYYY-MM-DD HH:MM:SS` (not locale-dependent)

**[2025-12-15 13:50]**
- Removed: Select-all checkbox from table header (not needed)

**[2025-12-15 13:49]**
- Changed: Console title now shows connection state: "Console Output (disconnected)", "Console Output (connecting): Job ID='jb_44'", "Console Output (connected): Job ID='jb_44'"
- Updated: UX diagram, Console Behavior, Action Flow, HTML Structure to reflect new title format

**[2025-12-15 13:43]**
- Added: Bulk delete flow with `bulkDelete()` function and toast message format specification

**[2025-12-15 13:40]**
- Added: "Modal Dialog Behavior" section with HTML structure, [View]/[Result] button examples, JavaScript functions (open/close/backdrop/escape), CSS styles

**[2025-12-15 13:39]**
- Removed: Auto-scroll toggle mechanism ("can be disabled by scrolling up") - not implemented

**[2025-12-15 13:35]**
- Changed: [Refresh] button now calls `refreshJobs()` instead of `location.reload()`
- Added: `refreshJobs()` function - fetches jobs and re-renders table, preserves console connection and output

**[2025-12-15 13:32]**
- Added: "Job Row Updates" section specifying row update mechanism for:
  - Control action success (optimistic update based on action type)
  - Monitored job state change (update on start_json/end_json events)
- Added: `handleControlResponse()` function with optimistic state mapping
- Added: `handleSseEvent()` function with htmx:sseBeforeMessage handler registration

**[2025-12-15 13:00]**
- Fixed: Added State column to UX diagram and HTML table
- Fixed: Added `hx-on::after-request` handler to control buttons in Job Row HTML
- Fixed: Removed [Result] button from running job example in Job Row HTML
- Fixed: parseSourceUrl examples - removed quotes to match code
- Changed: Started/Finished datetime format note added above UX diagram
- Changed: [Disconnect] clears title only, content remains until next [Monitor] click
- Changed: start_json/end_json events - data reflected in job row then discarded (not persisted)

**[2025-12-15 12:24]**
- Added: Error Handling for Control Actions - modal dialog (not toast) for `ok: false` responses
- Added: Multiline Events documentation - standard SSE multiline format, HTMX joins `data:` lines automatically, no XML tags

**[2025-12-15 12:20]**
- Added: Action Buttons Per State section - documents which buttons appear for each job state
- Added: Initial Page Load (Option B) - empty table, fetch on DOMContentLoaded
- Added: `#modal` element for [View] and [Result] button targets
- Added: `updateJob()` function signature with Object.assign pattern from testrouter3.py
- Changed: Bulk delete error handling - failed items remain, succeeded items removed
- Changed: Console panel always visible with container padding-bottom
- Changed: Removed "failed" from job states (use completed/cancelled with result.ok=false)
- Fixed: `hx-ext="sse"` moved from `<body>` to `#sse-container` for scoped SSE handling
- Fixed: Added `&format=html` to [View] and [Result] button URLs

**[2025-12-15 12:05]**
- Changed: Table columns now: Checkbox, ID, Router, Endpoint, Objects, Started, Finished, Actions
- Added: Parsing of source_url to extract Router, Endpoint, Object IDs for display
- Added: Bulk delete with checkboxes and [Delete Selected (N)] button
- Added: User actions for select jobs and bulk delete

**[2025-12-15 11:55]**
- Changed: Removed router/endpoint/object_id fields from job metadata (kept in source_url, parsed client-side)
- Changed: Added [View] and [Result] action buttons
- Changed: Control response format aligned with _V2_SPEC_ROUTERS.md standard JSON result
- Changed: SSE format aligned with _V2_SPEC_ROUTERS.md job metadata schema

**[2025-12-15 11:20]**
- Initial specification created
- Decided: HTMX SSE extension for event receiving and console updates
- Decided: Plain text log format (not HTML-wrapped)
- Decided: Single console, one job monitored at a time
- Decided: Three disconnect triggers (button, end_json, navigate away)
- Decided: Job list from `/v2/jobs?format=json` returns array with start_json or end_json per job
