# V3 Streaming UI - Implementation Plan

## Overview

Self-contained streaming console UI with inline CSS/JS in `generate_streaming_ui_page()`. No shared module modifications.

**Components**: Reactive job table | Streaming console | Toast notifications | Resize handle

---

## Function Map

### Python (testrouter3.py)

```
generate_streaming_ui_page(title, jobs)
  └─> Returns complete HTML with inline CSS/JS
      └─> Injects jobs as JSON array for JavaScript
```

### JavaScript State Management

```
jobsState (Map<id, job>)          # Global job storage
  ├─> addJob(job)                  # Add new job, trigger render
  ├─> updateJob(id, updates)       # Update job, trigger render
  └─> renderAllJobs()              # Re-render entire <tbody>
      └─> renderJobRow(job)        # Generate <tr> HTML
          └─> renderJobActions(job) # Generate action buttons HTML
```

### JavaScript Streaming

```
streamStart(button) / streamMonitor(button)
  └─> startStreamingRequest(url)
      └─> fetch() + ReadableStream
          └─> StreamParser.parse(chunk)
              ├─> onStartJson(data)    # Show toast, add job to state
              ├─> onLog(content)       # Append to console
              └─> onEndJson(data)      # Show toast, update job state
```

### JavaScript UI Updates

```
Toast:
  showToast(title, msg, type)      # Create toast DOM element
  ├─> showJobStartToast(data)      # Wrapper for job start
  └─> showJobEndToast(data)        # Wrapper for job end

Console:
  appendToConsole(text, autoScroll) # Add text, optionally scroll
  clearConsole()                    # Clear text, reset title
  setActiveJob(id)                  # Update console title

Resize:
  mousedown → mousemove → mouseup   # Drag handle to resize panel

Control:
  controlJob(id, action)            # POST to /control endpoint
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

---

## CSS (Inline in `generate_streaming_ui_page()`)

**Note**: All CSS is embedded inline in the `<style>` tag to keep the implementation self-contained.

```css
/* Toast Container */
#toast-container {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: 400px;
}

.toast {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-left: 4px solid #0078d4;
  padding: 0.75rem 1rem;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  animation: slideIn 0.3s ease-out;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  color: #212529;
}

.toast.toast-info { border-left-color: #0078d4; }
.toast.toast-success { border-left-color: #28a745; }
.toast.toast-error { border-left-color: #dc3545; }
.toast.toast-warning { border-left-color: #ffc107; }

.toast-content {
  flex: 1;
  font-size: 0.875rem;
}

.toast-title {
  font-weight: 600;
  margin-bottom: 0.25rem;
  color: #212529;
}

.toast-dismiss {
  background: none;
  border: none;
  color: #6c757d;
  cursor: pointer;
  padding: 0;
  font-size: 1.25rem;
  line-height: 1;
}

.toast-dismiss:hover { color: #212529; }

@keyframes slideIn {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

@keyframes fadeOut {
  from { opacity: 1; }
  to { opacity: 0; }
}

/* Console Panel - Fixed height with flexbox */
.console-panel {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #012456;
  border-top: none;
  z-index: 900;
  height: 232px;  /* Fixed height */
  display: flex;
  flex-direction: column;
}

/* Resize Handle */
.console-resize-handle {
  height: 4px;
  background: #aaaaaa;
  cursor: ns-resize;
  flex-shrink: 0;
  transition: background 0.2s;
}

.console-resize-handle:hover {
  background: #0090F1;
}

.console-resize-handle.dragging {
  background: #0090F1;
}

.console-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  background: #FAFAFA;
  border-bottom: 1px solid #d0d0d0;
  font-size: 0.875rem;
  font-weight: 500;
  color: #333333;
  flex-shrink: 0;
}

.console-controls {
  display: flex;
  gap: 0.5rem;
}

.console-output {
  flex: 1;  /* Takes remaining space */
  overflow-y: auto;
  padding: 0.75rem 1rem;
  margin: 0;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.9rem;
  line-height: 1rem;
  background: #012456;
  color: #ffffff;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* Add padding to main content so console doesn't overlap */
body.console-visible main {
  padding-bottom: 250px;
}
```

---

## JavaScript Implementation (Inline in `generate_streaming_ui_page()`)

**Note**: All JavaScript is embedded inline in the `<script>` tag. The implementation uses:
- **Reactive state**: `Map` for job storage with `renderAllJobs()` for full re-rendering
- **Stream parser**: Stateful parser for `<start_json>`, `<log>`, `<end_json>` tags
- **Console resize**: Drag handle with mouse events
- **Toast suppression**: Disabled during monitoring to avoid duplicate notifications

```javascript
// ============================================
// REACTIVE JOB STATE MANAGEMENT
// ============================================

const jobsState = new Map();
const initialJobs = /* Server injects JSON array */;

// Load initial jobs
initialJobs.forEach(job => {
  jobsState.set(job.id, job);
});

// Render functions
function renderJobRow(job) {
  const actions = renderJobActions(job);
  const formatTimestamp = (ts) => {
    if (!ts) return '';
    return ts.substring(0, 19).replace('T', ' ');
  };
  const started = formatTimestamp(job.started);
  const finished = job.finished ? formatTimestamp(job.finished) : '-';
  return `
    <tr id="job-${job.id}">
      <td>${job.id}</td>
      <td>${job.router}</td>
      <td>${job.endpoint}</td>
      <td>${job.state}</td>
      <td>${started}</td>
      <td>${finished}</td>
      <td>${actions}</td>
    </tr>
  `;
}

function renderJobActions(job) {
  let html = `<button class="btn-small" onclick="streamMonitor(this)" 
                      data-stream-url="/testrouter3/monitor?id=${job.id}">Monitor</button>`;
  
  if (job.state === 'running') {
    html += ` <button class="btn-small" onclick="controlJob(${job.id}, 'pause')">Pause</button>`;
    html += ` <button class="btn-small btn-delete" onclick="controlJob(${job.id}, 'cancel')">Cancel</button>`;
  } else if (job.state === 'paused') {
    html += ` <button class="btn-small" onclick="controlJob(${job.id}, 'resume')">Resume</button>`;
    html += ` <button class="btn-small btn-delete" onclick="controlJob(${job.id}, 'cancel')">Cancel</button>`;
  }
  
  return html;
}

function renderAllJobs() {
  const tbody = document.getElementById('jobs-tbody');
  if (!tbody) return;
  
  const jobs = Array.from(jobsState.values()).sort((a, b) => b.id - a.id);
  
  if (jobs.length === 0) {
    tbody.innerHTML = '<tr class="empty-row"><td colspan="7">No jobs found</td></tr>';
  } else {
    tbody.innerHTML = jobs.map(job => renderJobRow(job)).join('');
  }
  
  // Update count
  const countEl = document.getElementById('job-count');
  if (countEl) countEl.textContent = `(${jobs.length})`;
}

function updateJob(id, updates) {
  const job = jobsState.get(id);
  if (job) {
    Object.assign(job, updates);
    renderAllJobs();
  }
}

function addJob(job) {
  jobsState.set(job.id, job);
  renderAllJobs();
}

// ----------------------------------------
// TOAST FUNCTIONS
// ----------------------------------------

let suppressToasts = false;

function showToast(title, message, type = 'info', autoDismiss = 5000) {
  if (suppressToasts) return;
  
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div class="toast-content">
      <div class="toast-title">${escapeHtml(title)}</div>
      <div class="toast-message">${escapeHtml(message)}</div>
    </div>
    <button class="toast-dismiss" onclick="this.parentElement.remove()">×</button>
  `;

  container.appendChild(toast);

  if (autoDismiss > 0) {
    setTimeout(() => {
      toast.style.animation = 'fadeOut 0.3s ease-out forwards';
      setTimeout(() => toast.remove(), 300);
    }, autoDismiss);
  }
}

function showJobStartToast(jobData) {
  const msg = `ID: ${jobData.id} | Total: ${jobData.total} items`;
  showToast('Job Started', msg, 'info');
}

function showJobEndToast(jobData) {
  const type = jobData.state === 'done' ? 'success' : 
               jobData.state === 'canceled' ? 'warning' : 'error';
  const msg = `ID: ${jobData.id} | State: ${jobData.state}`;
  showToast('Job Finished', msg, type);
}

// ----------------------------------------
// CONSOLE FUNCTIONS
// ----------------------------------------

let activeJobId = null;
let isCurrentlyStreaming = false;

function setActiveJob(jobId) {
  activeJobId = jobId;
  const title = document.getElementById('console-title');
  if (title) {
    title.textContent = jobId ? `Console Output - Job ${jobId}` : 'Console Output';
  }
}

function appendToConsole(text, autoScroll = true) {
  const output = document.getElementById('console-output');
  if (!output) return;
  
  output.textContent += text;
  
  // Limit console size (1MB)
  const MAX_LENGTH = 1000000;
  if (output.textContent.length > MAX_LENGTH) {
    output.textContent = '...[truncated]\n' + output.textContent.slice(-MAX_LENGTH);
  }
  
  // Only auto-scroll if explicitly requested (during active streaming)
  if (autoScroll) {
    output.scrollTop = output.scrollHeight;
  }
}

function clearConsole() {
  const output = document.getElementById('console-output');
  if (output) output.textContent = '';
  setActiveJob(null);
}

// ----------------------------------------
// CONSOLE RESIZE HANDLER
// ----------------------------------------

let isDragging = false;
let startY = 0;
let startHeight = 0;

document.addEventListener('DOMContentLoaded', () => {
  const handle = document.querySelector('.console-resize-handle');
  const panel = document.getElementById('console-panel');
  
  if (!handle || !panel) return;
  
  handle.addEventListener('mousedown', (e) => {
    isDragging = true;
    startY = e.clientY;
    startHeight = panel.offsetHeight;
    handle.classList.add('dragging');
    e.preventDefault();
  });
  
  document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    
    const deltaY = startY - e.clientY;
    const newHeight = Math.max(100, Math.min(600, startHeight + deltaY));
    panel.style.height = `${newHeight}px`;
  });
  
  document.addEventListener('mouseup', () => {
    if (isDragging) {
      isDragging = false;
      handle.classList.remove('dragging');
    }
  });
});

// ----------------------------------------
// STREAM PARSER
// ----------------------------------------

class StreamParser {
  constructor() {
    this.buffer = '';
    this.state = 'idle'; // idle, in_start_json, in_log, in_end_json
  }

  parse(chunk) {
    this.buffer += chunk;
    
    while (this.buffer.length > 0) {
      if (this.state === 'idle') {
        // Look for opening tags
        if (this.buffer.includes('<start_json>')) {
          const idx = this.buffer.indexOf('<start_json>');
          this.buffer = this.buffer.slice(idx + '<start_json>'.length);
          this.state = 'in_start_json';
        } else if (this.buffer.includes('<log>')) {
          const idx = this.buffer.indexOf('<log>');
          this.buffer = this.buffer.slice(idx + '<log>'.length);
          this.state = 'in_log';
        } else if (this.buffer.includes('<end_json>')) {
          const idx = this.buffer.indexOf('<end_json>');
          this.buffer = this.buffer.slice(idx + '<end_json>'.length);
          this.state = 'in_end_json';
        } else {
          // No complete tag found, wait for more data
          // Keep last 20 chars in case tag is split across chunks
          if (this.buffer.length > 20) {
            this.buffer = this.buffer.slice(-20);
          }
          break;
        }
      }
      
      else if (this.state === 'in_start_json') {
        const endIdx = this.buffer.indexOf('</start_json>');
        if (endIdx !== -1) {
          const jsonStr = this.buffer.slice(0, endIdx).trim();
          this.buffer = this.buffer.slice(endIdx + '</start_json>'.length);
          this.state = 'idle';
          this.onStartJson(jsonStr);
        } else {
          break; // Wait for closing tag
        }
      }
      
      else if (this.state === 'in_log') {
        const endIdx = this.buffer.indexOf('</log>');
        if (endIdx !== -1) {
          const logContent = this.buffer.slice(0, endIdx);
          this.buffer = this.buffer.slice(endIdx + '</log>'.length);
          this.state = 'idle';
          if (logContent) this.onLog(logContent);
        } else {
          // Stream partial log content (don't wait for </log>)
          // Keep last 10 chars in case </log> is split
          if (this.buffer.length > 10) {
            const toEmit = this.buffer.slice(0, -10);
            this.buffer = this.buffer.slice(-10);
            if (toEmit) this.onLog(toEmit);
          }
          break;
        }
      }
      
      else if (this.state === 'in_end_json') {
        const endIdx = this.buffer.indexOf('</end_json>');
        if (endIdx !== -1) {
          const jsonStr = this.buffer.slice(0, endIdx).trim();
          this.buffer = this.buffer.slice(endIdx + '</end_json>'.length);
          this.state = 'idle';
          this.onEndJson(jsonStr);
        } else {
          break; // Wait for closing tag
        }
      }
    }
  }

  onStartJson(jsonStr) {
    try {
      const data = JSON.parse(jsonStr);
      setActiveJob(data.sj_id);
      showJobStartToast(data);
    } catch (e) {
      console.error('Failed to parse start_json:', e);
    }
  }

  onLog(content) {
    appendToConsole(content);
  }

  onEndJson(jsonStr) {
    try {
      const data = JSON.parse(jsonStr);
      showJobEndToast(data);
      updateJobTableRow(data);
    } catch (e) {
      console.error('Failed to parse end_json:', e);
    }
  }
}

// ----------------------------------------
// TABLE ROW UPDATE
// ----------------------------------------

function updateJobTableRow(jobData) {
  const row = document.getElementById(`job-${jobData.sj_id}`);
  if (!row) return;
  
  // Update state cell (adjust nth-child index based on your table structure)
  const stateCell = row.querySelector('td:nth-child(4)');
  if (stateCell) stateCell.textContent = jobData.state.toLowerCase();
  
  // Remove Pause/Resume/Cancel buttons since job is done, keep only Monitor
  const actionsCell = row.querySelector('td:last-child');
  if (actionsCell) {
    const monitorBtn = actionsCell.querySelector('button');
    actionsCell.innerHTML = '';
    if (monitorBtn) actionsCell.appendChild(monitorBtn);
  }
}

// ----------------------------------------
// STREAMING FETCH
// ----------------------------------------

async function startStreamingRequest(url, options = {}) {
  // Cancel any active stream
  if (activeStreamController) {
    activeStreamController.abort();
  }

  activeStreamController = new AbortController();
  const parser = new StreamParser();

  // Show connecting indicator
  appendToConsole('[Connecting...]\n');

  try {
    const response = await fetch(url, {
      signal: activeStreamController.signal,
      ...options
    });

    if (!response.ok) {
      showToast('Error', `Request failed: ${response.status}`, 'error');
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value, { stream: true });
      parser.parse(chunk);
    }

  } catch (e) {
    if (e.name === 'AbortError') {
      appendToConsole('\n[Stream aborted]\n');
    } else {
      showToast('Error', e.message, 'error');
      console.error('Streaming error:', e);
    }
  } finally {
    activeStreamController = null;
  }
}

function cancelActiveStream() {
  if (activeStreamController) {
    activeStreamController.abort();
    activeStreamController = null;
  }
}

// ----------------------------------------
// BUTTON HANDLERS
// ----------------------------------------

// Generic handler for streaming buttons - reads URL from data-stream-url attribute
function streamRequest(button) {
  const url = button.dataset.streamUrl;
  if (!url) {
    console.error('No data-stream-url on button');
    return;
  }
  
  clearConsole();
  document.body.classList.add('console-visible');
  const panel = document.getElementById('console-panel');
  if (panel) panel.classList.remove('collapsed');
  
  startStreamingRequest(url);
}

// Convenience alias for monitor buttons
function streamMonitor(button) {
  suppressToasts = true;  // Disable toasts when monitoring (avoid duplicates)
  streamRequest(button);
}

// Convenience alias for start buttons
function streamStart(button) {
  suppressToasts = false;  // Enable toasts when starting new job
  streamRequest(button);
}

// Job control (pause/resume/cancel)
async function controlJob(jobId, action) {
  try {
    const response = await fetch(`/testrouter3/control?id=${jobId}&action=${action}`, {
      method: 'POST'
    });
    
    if (response.ok) {
      const data = await response.json();
      showToast('Control', `Job ${jobId}: ${action}`, 'info', 3000);
      
      // Update job state in table
      updateJob(jobId, { state: data.state });
    } else {
      showToast('Error', `Failed to ${action} job ${jobId}`, 'error');
    }
  } catch (e) {
    showToast('Error', e.message, 'error');
  }
}

// Helper to escape HTML in toast messages
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  renderAllJobs();
  document.body.classList.add('console-visible');
});
```

---

## Button Configuration Pattern

Buttons use `data-stream-url` attribute to specify streaming endpoint. JavaScript reads this attribute and initiates the stream.

**HTML (generated by `renderJobActions()`):**

```html
<!-- Monitor button -->
<button class="btn-small" 
        onclick="streamMonitor(this)" 
        data-stream-url="/testrouter3/monitor?id=42">
  Monitor
</button>

<!-- Start button -->
<button class="btn-primary" 
        onclick="streamStart(this)" 
        data-stream-url="/testrouter3/streaming01?format=stream&files=20">
  Start New Job (20 files)
</button>

<!-- Control buttons (no streaming) -->
<button class="btn-small" onclick="controlJob(42, 'pause')">Pause</button>
<button class="btn-small btn-delete" onclick="controlJob(42, 'cancel')">Cancel</button>
```

---

## Key Implementation Details

### 1. Reactive Rendering
- **State**: `Map<id, job>` stores all jobs
- **Rendering**: `renderAllJobs()` re-renders entire `<tbody>` on any state change
- **Updates**: `updateJob(id, updates)` modifies state and triggers re-render

### 2. Stream Parser
- **Stateful**: Tracks current parsing state (`idle`, `in_start_json`, `in_log`, `in_end_json`)
- **Buffering**: Keeps last N chars when waiting for closing tags (handles split chunks)
- **Streaming logs**: Emits partial `<log>` content before `</log>` arrives

### 3. Toast Suppression
- **Monitor mode**: `suppressToasts = true` prevents duplicate notifications when viewing historical logs
- **Start mode**: `suppressToasts = false` shows toasts for new job events
- **Auto-restore**: Re-enables toasts if stream ends without `<end_json>` (incomplete monitor)

### 4. Console Resize
- **Drag handle**: 4px bar at top of console panel
- **Mouse events**: `mousedown` → `mousemove` → `mouseup`
- **Bounds**: Min 100px, max 600px height

### 5. Auto-scroll Control
- **Active streaming**: `autoScroll = true` (follows new output)
- **Historical logs**: `autoScroll = false` (preserves scroll position)
- **Determined by**: `!suppressToasts` (toasts disabled = historical)

---

## Implementation Approach

**Self-Contained (testrouter3.py)**:
- ✅ All CSS/JS inline in `generate_streaming_ui_page()`
- ✅ No modifications to shared modules
- ✅ Router-specific implementation
- ✅ Easy to copy/adapt for other routers

**Modular (Future Enhancement)**:
- Extract to `/static/js/streaming.js`
- Extract to `/static/css/styles.css`
- Enhance `common_ui_functions.py` with `generate_streaming_ui_page()`
- Reuse across multiple routers (crawler, domains, etc.)

---

## Testing Checklist

- [ ] Toast appears on job start with correct info
- [ ] Log content streams to console in real-time
- [ ] Toast appears on job end with correct result type
- [ ] Console auto-scrolls during active streaming
- [ ] Console preserves scroll position when monitoring historical logs
- [ ] Clear button works (resets title to "Console Output")
- [ ] Resize handle works (drag up/down to adjust console height)
- [ ] Multiple rapid job starts don't break parser
- [ ] Chunked tag boundaries handled correctly (e.g., `</lo` + `g>`)
- [ ] Console header shows active job ID
- [ ] Table updates reactively when job state changes
- [ ] Action buttons update when job completes (Pause/Cancel removed)
- [ ] Long jobs (~1000+ items) don't freeze browser (buffer truncation works)
- [ ] Toast suppression works (no duplicates when monitoring)
- [ ] Control buttons (Pause/Resume/Cancel) work correctly
