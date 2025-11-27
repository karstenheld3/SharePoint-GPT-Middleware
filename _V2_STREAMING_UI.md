# V3 Streaming UI Implementation

## Overview

This document describes the streaming console UI implementation as demonstrated in `testrouter3.py`. The implementation is **self-contained** with all CSS and JavaScript inline, avoiding pollution of shared modules.

**Approach**: 
- **Reactive rendering**: JavaScript `Map` for job state management with full table re-rendering
- **Streaming**: `fetch()` with `ReadableStream` parses `<start_json>`, `<log>`, and `<end_json>` tags
- **Console**: Fixed bottom panel with resize handle and auto-scroll
- **Toasts**: Top-right notifications for job start/end events

---

## Scenario

This middleware exposes endpoints that can potentially run for hours. For example crawling multiple SharePoint sites with thousands of files. 

**Problems:**
- Firewalls and proxies might terminate network connections
- The Fronend might crash or the user might accidently navigate away before the endpoint delivers the result 
- Once an endpoint call is interrupted or lost, there is no way to retrieve the final result and errors

**Solutions:**
- Endpoints should stream activity by default using media_type="text/event-stream; charset=utf-8"
- Standardized endpoints are used to pause, resume, cancel jobs retrieve the final output

**What we don't want:**
- HTMX Server-Side-Events

## Domain Object Model

- **StreamingJob**: Dataclass representing a job with id, router, endpoint, state, timestamps, total/current progress, result
- **jobsState**: Client-side JavaScript `Map<id, job>` storing all jobs for reactive rendering
- **Job States**: `running`, `paused`, `completed`, `canceled`
- **Control Files**: Filesystem-based signaling via `pause_requested`, `resume_requested`, `cancel_requested` files
- **Log Files**: Persistent storage of streaming output with structured tags (`<start_json>`, `<log>`, `<end_json>`)

### Endpoints Overview

- **`/testrouter3/streaming01?format=stream`** (GET) - Start new streaming job
  - `files` - number of files to process (default: 20)
  - Returns: `text/event-stream; charset=utf-8`

- **`/testrouter3/streaming01?format=ui`** (GET) - Show job list page with console UI
  - Returns: HTML page with jobs table and console

- **`/testrouter3/monitor?id={id}`** (GET) - Monitor/replay existing job logs
  - `id` - streaming job ID (required)
  - Returns: `text/event-stream; charset=utf-8`

- **`/testrouter3/control?id={id}&action={action}`** (GET) - Control running job
  - `id` - job ID (required)
  - `action` - pause/resume/cancel (required)
  - Returns: JSON `{"success": true, "id": 42, "action": "pause", "message": "..."}`

- **`/testrouter3/jobs?format=ui`** (GET) - List all jobs with console UI (default)
  - `router` - filter by router name (optional)
  - `endpoint` - filter by endpoint name (optional)
  - `state` - filter by state: running/paused/completed/canceled (optional)
  - Returns: HTML page with jobs table and console

- **`/testrouter3/jobs?format=json`** (GET) - List all jobs as JSON
  - `router` - filter by router name (optional)
  - `endpoint` - filter by endpoint name (optional)
  - `state` - filter by state: running/paused/completed/canceled (optional)
  - Returns: JSON `{"jobs": [...], "count": 5}`

### Example Stream
```
<start_json>
{"id": 42, "router": "testrouter3", "endpoint": "streaming01", "state": "running", "total": 3, "started": "2025-11-27T11:30:00"}
</start_json>
<log>
[ 1 / 3 ] Processing 'doc_001.pdf'...
  OK.
[ 2 / 3 ] Processing 'doc_002.pdf'...
  OK.
[ 3 / 3 ] Processing 'doc_003.pdf'...
  OK.
</log>
<end_json>
{"id": 42, "state": "completed", "result": "ok", "finished": "2025-11-27T11:30:15"}
</end_json>
```



**Event Flow (Pause → Resume → Complete):**
```
1. Job starts
   └─> Server: Create job file "42_running_20251127113000.log"
   └─> Client: Receive <start_json>, add job to jobsState, show toast

2. User clicks [Pause]
   └─> Client: POST /control?id=42&action=pause
   └─> Server: Create "42_pause_requested_20251127113000.txt"
   └─> Client: Optimistically update jobsState → state='paused', renderAllJobs()

3. Server detects pause_requested
   └─> Stream: Yield "  Pause requested, pausing...\n"
   └─> Server: Delete pause_requested file, rename job file to "42_paused_20251127113000.log"
   └─> Server: Enter pause loop (await asyncio.sleep)

4. User clicks [Resume]
   └─> Client: POST /control?id=42&action=resume
   └─> Server: Create "42_resume_requested_20251127113000.txt"
   └─> Client: Optimistically update jobsState → state='running', renderAllJobs()

5. Server detects resume_requested
   └─> Stream: Yield "  Resume requested, resuming...\n"
   └─> Server: Delete resume_requested file, rename job file to "42_running_20251127113000.log"
   └─> Server: Exit pause loop, continue processing

6. Job completes
   └─> Stream: Yield <end_json> with state='completed', result='ok'
   └─> Client: Parse end_json, update jobsState, show completion toast
   └─> Server: Rename job file to "42_completed_20251127113000.log"
```

## User Actions

- **Start Job**: Initiate new streaming job, clear console, enable toasts, show real-time logs
- **Monitor Job**: Replay existing job logs, disable toasts, no auto-scroll (historical view)
- **Pause Job**: Request job to pause at next checkpoint, button changes to "Resume"
- **Resume Job**: Request paused job to continue processing
- **Cancel Job**: Request job termination with confirmation dialog
- **Refresh Page**: Reload job list from server
- **Clear Console**: Empty console output and reset title
- **Resize Console**: Drag handle to adjust console panel height

## UX Design

```
Main HTML:
┌───────────────────────────────────────────────────────────────────────────────┐
│  Streaming Jobs (2)                                                           │
│                                                                               │
│  [Start Job]  [Refresh]                                 [Toasts appear here]  │
│                                                                               │
│  ┌────┬─────────┬──────────┬─────────┬─────────────────────────────────────┐  │
│  │ ID │ Router  │ Endpoint │ State   │ Actions                             │  │
│  ├────┼─────────┼──────────┼─────────┼─────────────────────────────────────┤  │
│  │ 42 │ crawler │ update   │ running │ [Monitor] [Pause / Resume] [Cancel] │  │
│  │ 41 │ crawler │ update   │ done    │ [Monitor]                           │  │
│  └────┴─────────┴──────────┴─────────┴─────────────────────────────────────┘  │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │ [Resize Handle - Draggable]                                             │  │
│  │ Console Output                                                  [Clear] │  │
│  │ ────────────────────────────────────────────────────────────────────────│  │
│  │ [ 1 / 20 ] Processing 'document_001.pdf'...                             │  │
│  │   OK.                                                                   │  │
│  │ [ 2 / 20 ] Processing 'document_002.pdf'...                             │  │
│  │   OK.                                                                   │  │
│  │ █                                                                       │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘

Toast:
┌───────────────────────────────────────────────┐
│ Job Started | ID: 42 | Total: 20 items   [×]  │
└───────────────────────────────────────────────┘
```

---

## Key Mechanisms and Design Decisions

**Reactive Rendering**: `jobsState` Map → `renderAllJobs()` → full `<tbody>` replacement
**Stream Parser**: Stateful buffering handles split tags across chunks, emits partial `<log>` content
**Toast Suppression**: `suppressToasts` flag prevents duplicates when monitoring historical logs
**Auto-scroll**: `appendToConsole(text, autoScroll)` - enabled for new streams, disabled for monitoring
**Button Pattern**: `data-stream-url` attribute → `streamStart()/streamMonitor()` → `startStreamingRequest()`


---

## Action Flow

### Page Load
```
Script execution (inline)
  ├─> Initialize jobsState Map from server-injected JSON
  ├─> initialJobs.forEach() → jobsState.set(job.id, job)
  └─> renderAllJobs()
      └─> renderJobRow() for each job
          └─> renderJobActions() based on job.state

DOMContentLoaded
  └─> initConsoleResize()
      └─> Setup console resize listeners (mousedown/mousemove/mouseup)
```

### [Start Job] Button Click
```
User clicks [Start Job]
  └─> streamStart(button)
      ├─> Check if isCurrentlyStreaming (alert if true, return)
      ├─> suppressToasts = false           # Enable toasts for new job
      └─> streamRequest(button)
          ├─> Read data-stream-url attribute
          ├─> clearConsole()
          │   └─> setActiveJob(null)
          ├─> document.body.classList.add('console-visible')
          └─> startStreamingRequest(url)
              ├─> isCurrentlyStreaming = true
              └─> fetch(url) with ReadableStream
                  └─> StreamParser.parse(chunk)
                      ├─> onStartJson(data)
                      │   ├─> setActiveJob(data.id)
                      │   ├─> showJobStartToast(data)  # Checks suppressToasts
                      │   │   └─> showToast()
                      │   └─> addJob(data)
                      │       └─> renderAllJobs()
                      ├─> onLog(content)
                      │   └─> appendToConsole(content, autoScroll=!suppressToasts)
                      └─> onEndJson(data)
                          ├─> foundEndJson = true
                          ├─> showJobEndToast(data)  # Checks suppressToasts
                          │   └─> showToast()
                          └─> updateJob(data.id, updates)
                              └─> renderAllJobs()
              └─> finally: isCurrentlyStreaming = false
```

### [Monitor] Button Click
```
User clicks [Monitor]
  └─> streamMonitor(button)
      ├─> suppressToasts = true            # Disable toasts (historical logs)
      └─> streamRequest(button)
          ├─> Read data-stream-url attribute
          ├─> clearConsole()
          │   └─> setActiveJob(null)
          ├─> document.body.classList.add('console-visible')
          └─> startStreamingRequest(url)
              ├─> isCurrentlyStreaming = true
              └─> fetch(url) with ReadableStream
                  └─> StreamParser.parse(chunk)
                      ├─> onStartJson(data)
                      │   ├─> setActiveJob(data.id)
                      │   └─> showJobStartToast(data)  # Suppressed (returns early)
                      ├─> onLog(content)
                      │   └─> appendToConsole(content, autoScroll=false)
                      └─> onEndJson(data)
                          ├─> foundEndJson = true
                          ├─> showJobEndToast(data)    # Suppressed (returns early)
                          └─> updateJob(data.id, updates)
                              └─> renderAllJobs()
              └─> finally: 
                  ├─> If !foundEndJson: suppressToasts = false  # Re-enable
                  └─> isCurrentlyStreaming = false
```

### [Pause] / [Resume] Button Click
```
User clicks [Pause] or [Resume]
  └─> controlJob(jobId, 'pause' | 'resume')
      └─> fetch(`/testrouter3/control?id=${id}&action=${action}`)
          └─> On success (data.success):
              └─> Optimistically updateJob(jobId, { state: 'paused' | 'running' })
                  └─> renderAllJobs()
                      └─> renderJobActions() # Button changes to Resume/Pause
```

### [Cancel] Button Click
```
User clicks [Cancel]
  └─> controlJob(jobId, 'cancel')
      ├─> confirm() dialog (return if cancelled)
      └─> fetch(`/testrouter3/control?id=${id}&action=cancel`)
          └─> On success (data.success):
              └─> Optimistically updateJob(jobId, { state: 'canceled' })
                  └─> renderAllJobs()
                      └─> renderJobActions() # Removes Pause/Cancel buttons
```

### [Refresh] Button Click
```
User clicks [Refresh]
  └─> location.reload()
      └─> Full page reload (re-fetches job list from server)
```

### [Clear] Button Click (Console)
```
User clicks [Clear]
  └─> clearConsole()
      ├─> Clear console output text
      └─> setActiveJob(null)
          └─> Reset console title to "Console Output"
```

### Console Resize Handle Drag
```
User drags resize handle
  └─> mousedown on .console-resize-handle
      ├─> isResizing = true
      ├─> Store startY, startHeight
      ├─> handle.classList.add('dragging')
      ├─> document.body.style.cursor = 'ns-resize'
      └─> mousemove (while isResizing)
          ├─> Calculate deltaY = startY - e.clientY
          ├─> Calculate newHeight = startHeight + deltaY
          ├─> Clamp: Math.max(MIN_CONSOLE_HEIGHT, Math.min(newHeight, MAX_CONSOLE_HEIGHT))
          └─> Apply panel.style.height
      └─> mouseup
          ├─> isResizing = false
          ├─> handle.classList.remove('dragging')
          └─> Reset document.body.style.cursor
```

---

## HTML Structure

### Complete Page Structure (from `generate_streaming_ui_page()`)

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset='utf-8'>
  <title>Jobs (5)</title>
  <link rel='stylesheet' href='/static/css/styles.css'>
  <script src='/static/js/htmx.js'></script>
  <style>
    /* Inline CSS for console and toasts */
  </style>
</head>
<body>
  <!-- Toast Container (top-right, stacked) -->
  <div id="toast-container"></div>
  
  <!-- Main Content -->
  <div class="container">
    <h1>Jobs <span id="job-count">(5)</span></h1>
    
    <div class="toolbar">
      <button class="btn-primary" onclick="streamStart(this)" 
              data-stream-url="/testrouter3/streaming01?format=stream&files=20">
        Start New Job (20 files)
      </button>
      <button onclick="location.reload()" class="btn-small">Refresh</button>
    </div>
    
    <table>
      <thead>
        <tr>
          <th>ID</th><th>Router</th><th>Endpoint</th>
          <th>State</th><th>Started</th><th>Finished</th><th>Actions</th>
        </tr>
      </thead>
      <tbody id="jobs-tbody">
        <!-- Rendered by JavaScript renderAllJobs() -->
      </tbody>
    </table>
  </div>
  
  <!-- Console Panel (fixed bottom, resizable) -->
  <div id="console-panel" class="console-panel">
    <div class="console-resize-handle"></div>
    <div class="console-header">
      <span id="console-title">Console Output</span>
      <div class="console-controls">
        <button onclick="clearConsole()" class="btn-small">Clear</button>
      </div>
    </div>
    <pre id="console-output" class="console-output"></pre>
  </div>
  
  <script>
    /* Inline JavaScript */
  </script>
</body>
</html>
```

### Button HTML

**Start Job Button** (triggers new streaming job):
```html
<button class="btn-primary" onclick="streamStart(this)" data-stream-url="/testrouter3/streaming01?format=stream&files=20"> Start New Job (20 files) </button>
```

**Pause Button** (requests job pause):
```html
<button class="btn-small" onclick="controlJob(42, 'pause')"> Pause </button>
```

**Resume Button** (requests job resume):
```html
<button class="btn-small" onclick="controlJob(42, 'resume')"> Resume </button>
```

**Cancel Button** (requests job cancellation with confirmation):
```html
<button class="btn-small btn-danger" onclick="controlJob(42, 'cancel')"> Cancel </button>
```

**Refresh Button** (reloads page):
```html
<button onclick="location.reload()" class="btn-small"> Refresh </button>
```

**Clear Console Button**:
```html
<button onclick="clearConsole()" class="btn-small"> Clear </button>
```

---

## CSS Styles (Inline in `<style>` tag)

```css
#toast-container { /* Fixed top-right container for stacked toasts */ }

.toast { /* Individual toast notification with light theme */ }
.toast.toast-info { /* Blue left border */ }
.toast.toast-success { /* Green left border */ }
.toast.toast-error { /* Red left border */ }
.toast.toast-warning { /* Yellow left border */ }

.toast-content { /* Toast message area */ }
.toast-title { /* Bold toast title */ }
.toast-dismiss { /* × close button */ }

@keyframes slideIn { /* Toast entrance animation (slide from right) */ }
@keyframes fadeOut { /* Toast exit animation (fade out) */ }

.console-panel { /* Fixed bottom panel, 232px height, flexbox layout, dark blue background */ }

.console-resize-handle { /* 4px draggable bar at top, gray → blue on hover/drag */ }
.console-resize-handle:hover { /* Blue on hover */ }
.console-resize-handle.dragging { /* Blue while dragging */ }

.console-header { /* Light gray header with title and controls */ }
.console-controls { /* Button container in header */ }

.console-output { /* Scrollable monospace output area, flex:1 takes remaining space */ }

body.console-visible main { /* Add bottom padding to prevent console overlap */ }
```

---

## JavaScript Functions (Inline in `<script>` tag)

```javascript
// ============================================
// STATE MANAGEMENT
// ============================================

const jobsState = new Map();  // Global job storage: Map<id, job>

function addJob(job) {
  // Add new job to state and trigger table re-render
}

function updateJob(id, updates) {
  // Update existing job in state and trigger table re-render
}

function renderAllJobs() {
  // Re-render entire <tbody> from jobsState Map
}

function renderJobRow(job) {
  // Generate <tr> HTML for single job
}

function renderJobActions(job) {
  // Generate action buttons HTML based on job state (running/paused/done)
}

// ============================================
// STREAMING
// ============================================

function streamStart(button) {
  // Start new job: enable toasts, clear console, read data-stream-url, start stream
}

function streamMonitor(button) {
  // Monitor existing job: disable toasts, clear console, read data-stream-url, start stream
}

async function startStreamingRequest(url) {
  // Fetch URL with ReadableStream, parse chunks with StreamParser
}

class StreamParser {
  // Stateful parser for <start_json>, <log>, <end_json> tags
  
  parse(chunk) {
    // Buffer chunks, detect tags, emit to handlers
  }
  
  onStartJson(jsonStr) {
    // Parse start_json, show toast, add job to state
  }
  
  onLog(content) {
    // Append log content to console
  }
  
  onEndJson(jsonStr) {
    // Parse end_json, show toast, update job state
  }
}

// ============================================
// UI UPDATES
// ============================================

function showToast(title, message, type, autoDismiss) {
  // Create toast DOM element, auto-dismiss after N seconds
}

function showJobStartToast(jobData) {
  // Show "Job Started" toast with job details
}

function showJobEndToast(jobData) {
  // Show "Job Finished" toast with result (success/warning/error)
}

function appendToConsole(text, autoScroll) {
  // Append text to console, optionally auto-scroll to bottom
}

function clearConsole() {
  // Clear console text and reset title
}

function setActiveJob(jobId) {
  // Update console title with job ID
}

// ============================================
// CONSOLE RESIZE
// ============================================

// mousedown on .console-resize-handle
//   → mousemove adjusts panel height
//   → mouseup stops dragging

// ============================================
// CONTROL
// ============================================

async function controlJob(jobId, action) {
  // POST to /control endpoint with action (pause/resume/cancel)
  // Update job state in table on success
}
```

---

## Spec Changes

**[2025-11-27 14:41]**
- Added: Implementation specification rules compliance
- Verified: All sections match implementation in testrouter3.py
- Verified: Rules compliance (Python rules, specification rules)

**[2025-11-27 11:14]**
- Changed: Complete rewrite to match actual implementation in testrouter3.py
- Added: Reactive rendering with JavaScript Map for job state management
- Added: Toast suppression mechanism (suppressToasts flag) for monitoring vs starting jobs
- Added: Auto-scroll control based on streaming mode (active vs historical)
- Added: Console resize functionality with drag handle
- Added: StreamParser class with stateful buffering for split chunks
- Added: Complete action flow diagrams for all user interactions
- Changed: Job state management from simple table updates to full reactive re-rendering
- Changed: Stream parser from simple tag detection to stateful multi-phase parser
- Changed: Button pattern to use data-stream-url attribute
- Added: Control job function with optimistic state updates
- Added: Confirmation dialog for cancel action
- Added: Complete HTML structure section with all components
- Added: Complete CSS styles section with all classes
- Added: Complete JavaScript functions section with all handlers
- Removed: Integration with common_ui_functions.py (self-contained approach)
- Removed: External streaming.js file (inline JavaScript)

**[2025-11-26 17:42]**
- Initial design: V2 Streaming UI specification
- Added: Basic console panel concept with collapse/expand
- Added: Toast notification system (info/success/error/warning types)
- Added: Stream parser for <start_json>, <log>, <end_json> tags
- Added: Button pattern with data-stream-url attribute
- Added: Table row update function for job completion
- Added: Basic streaming fetch with AbortController
- Planned: Integration with common_ui_functions.py (later changed to self-contained)
- Planned: External /static/js/streaming.js file (later changed to inline)
