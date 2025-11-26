# V2 Streaming UI Implementation

## Overview

This document describes how to implement a streaming console UI for endpoints that return `<start_json>`, `<log>`, and `<end_json>` tagged output.

**Approach**: HTMX handles table/button interactions. JavaScript `fetch()` with `ReadableStream` handles streaming responses, parsing chunks and routing to console/toasts.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  HTMX Table UI (format=ui)                                  │
│  ┌─────────┬─────────┬─────────┬─────────────────────────┐  │
│  │ SJ_ID   │ State   │ Router  │ Actions                 │  │
│  ├─────────┼─────────┼─────────┼─────────────────────────┤  │
│  │ 42      │ running │ crawler │ [Monitor] [Pause] [Cancel]│
│  └─────────┴─────────┴─────────┴─────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Console Output                                    [Clear]││
│  │ ─────────────────────────────────────────────────────── ││
│  │ [ 1 / 20 ] Processing 'document_001.pdf'...             ││
│  │   OK.                                                   ││
│  │ [ 2 / 20 ] Processing 'document_002.pdf'...             ││
│  │   OK.                                                   ││
│  │ █                                                       ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 🟢 Job 42 started | Total: 20 files           [dismiss] ││ ← Toast
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## HTML Structure

### Page Template Addition

Add to `generate_ui_table_page()` or as a separate includable component:

```html
<!-- Toast Container (top-right, stacked) -->
<div id="toast-container"></div>

<!-- Console Panel (bottom of page, collapsible) -->
<div id="console-panel" class="console-panel">
  <div class="console-header">
    <span id="console-title">Console Output</span>
    <div class="console-controls">
      <button onclick="clearConsole()" class="btn-small">Clear</button>
      <button onclick="toggleConsole()" class="btn-small">_</button>
    </div>
  </div>
  <pre id="console-output" class="console-output"></pre>
</div>
```

---

## CSS Additions

Add to `/static/css/styles.css`:

```css
/* ============================================
   STREAMING CONSOLE & TOASTS
   ============================================ */

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
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-left: 4px solid #0078d4;
  padding: 0.75rem 1rem;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  animation: slideIn 0.3s ease-out;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.toast.toast-info { border-left-color: #0078d4; }
.toast.toast-success { border-left-color: #4caf50; }
.toast.toast-error { border-left-color: #f44336; }
.toast.toast-warning { border-left-color: #ff9800; }

.toast-content {
  flex: 1;
  font-size: 0.875rem;
}

.toast-title {
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.toast-dismiss {
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 0;
  font-size: 1.25rem;
  line-height: 1;
}

.toast-dismiss:hover { color: #fff; }

@keyframes slideIn {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

@keyframes fadeOut {
  from { opacity: 1; }
  to { opacity: 0; }
}

/* Console Panel */
.console-panel {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #1a1a1a;
  border-top: 1px solid #3c3c3c;
  z-index: 900;
  max-height: 232px;  /* 32px header + 200px content */
  transition: max-height 0.2s ease;
}

.console-panel.collapsed {
  max-height: 32px;
}

.console-panel.collapsed .console-output {
  display: none;
}

.console-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  background: #252525;
  border-bottom: 1px solid #3c3c3c;
  font-size: 0.875rem;
  font-weight: 500;
}

.console-controls {
  display: flex;
  gap: 0.5rem;
}

.console-output {
  height: 200px;
  overflow-y: auto;
  padding: 0.75rem 1rem;
  margin: 0;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.8125rem;
  line-height: 1.4;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* Add padding to main content so console doesn't overlap */
body.console-visible main {
  padding-bottom: 250px;
}
```

---

## JavaScript Implementation

Add to `/static/js/streaming.js` (new file) or inline in template:

```javascript
// ============================================
// STREAMING UI - Console & Toasts
// ============================================

// State
let activeStreamController = null;
let activeJobId = null;

// ----------------------------------------
// TOAST FUNCTIONS
// ----------------------------------------

function showToast(title, message, type = 'info', autoDismiss = 5000) {
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

  return toast;
}

function showJobStartToast(jobData) {
  const msg = `ID: ${jobData.sj_id} | Total: ${jobData.total} items`;
  showToast('Job Started', msg, 'info');
}

function showJobEndToast(jobData) {
  const type = jobData.result === 'OK' ? 'success' : 
               jobData.result === 'CANCELED' ? 'warning' : 'error';
  const msg = `ID: ${jobData.sj_id} | Result: ${jobData.result}`;
  showToast('Job Finished', msg, type);
}

// ----------------------------------------
// CONSOLE FUNCTIONS
// ----------------------------------------

function setActiveJob(sjId) {
  activeJobId = sjId;
  const title = document.getElementById('console-title');
  if (title) title.textContent = sjId ? `Console Output (Job ${sjId})` : 'Console Output';
}

function appendToConsole(text) {
  const output = document.getElementById('console-output');
  if (!output) return;
  
  output.textContent += text;
  
  // Limit buffer to ~50KB to prevent memory bloat on long jobs
  const MAX_LENGTH = 50000;
  if (output.textContent.length > MAX_LENGTH) {
    output.textContent = '...[truncated]\n' + output.textContent.slice(-MAX_LENGTH);
  }
  
  output.scrollTop = output.scrollHeight; // Auto-scroll
}

function clearConsole() {
  const output = document.getElementById('console-output');
  if (output) output.textContent = '';
  setActiveJob(null);
}

function toggleConsole() {
  const panel = document.getElementById('console-panel');
  if (panel) panel.classList.toggle('collapsed');
}

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
  streamRequest(button);
}

// Convenience alias for start job buttons
function streamStart(button) {
  streamRequest(button);
}

// ----------------------------------------
// UTILITY
// ----------------------------------------

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
```

---

## Integration with Existing UI

### Button Pattern: `data-stream-url` Attribute

Server generates full URL in button; JavaScript reads from `data-stream-url` attribute.

**Python - button config in `get_job_action_buttons()`:**

```python
# Monitor button - streams existing job log
{'text': 'Monitor', 
 'onclick': 'streamMonitor(this)',
 'data_stream_url': f"/testrouter2/monitor?sj_id={sj_id}",
 'button_class': 'btn-small btn-stream'}

# Start button - starts new streaming job
{'text': 'Start Job', 
 'onclick': 'streamStart(this)',
 'data_stream_url': '/testrouter2/streaming01?format=stream&files=10',
 'button_class': 'btn-small btn-stream'}
```

**Update `generate_action_button()` in `common_ui_functions.py`:**

```python
def generate_action_button(button_config: dict) -> str:
    # ... existing code ...
    
    # Add data-stream-url attribute if present
    data_stream_url = button_config.get('data_stream_url', '')
    data_attr = f' data-stream-url="{data_stream_url}"' if data_stream_url else ''
    
    return f'<button class="{button_class}"{onclick}{hx_attrs}{data_attr}>{text}</button>'
```

**Generated HTML:**

```html
<button class="btn-small btn-stream" 
        onclick="streamMonitor(this)" 
        data-stream-url="/testrouter2/monitor?sj_id=42">Monitor</button>
```

---

## File Changes Required

1. **`/static/css/styles.css`** - Add console/toast styles (with `.toast-info`, `max-height` transition)
2. **`/static/js/streaming.js`** (new) - All JS functions above
3. **`common_ui_functions.py`**:
   - Update `generate_action_button()` to support `data_stream_url` attribute
   - Update `generate_ui_table_page()` to include console panel, toast container, and script tag
4. **`testrouter2.py`** - Update `get_job_action_buttons()` to use `data_stream_url` pattern

---

## Usage Examples

### Start a New Streaming Job
```html
<button class="btn-stream" 
        onclick="streamStart(this)" 
        data-stream-url="/testrouter2/streaming01?format=stream&files=20">
  Start Processing
</button>
```

### Monitor an Existing Job
```html
<button class="btn-stream" 
        onclick="streamMonitor(this)" 
        data-stream-url="/testrouter2/monitor?sj_id=42">
  Monitor Job 42
</button>
```

### From HTMX Table Row (generated by Python)
```html
<button class="btn-small btn-stream" 
        onclick="streamMonitor(this)" 
        data-stream-url="/testrouter2/monitor?sj_id=42">Monitor</button>
```

---

## Future Enhancements

1. **Multiple Console Tabs** - Track multiple jobs in separate tabs
2. **Console History** - Store last N job outputs in localStorage
3. **Progress Bar** - Parse `[ X / Y ]` pattern to show visual progress
4. **Sound Notifications** - Beep on job complete/error
5. **Keyboard Shortcuts** - Ctrl+K to clear console, Escape to minimize

---

## Testing Checklist

- [ ] Toast appears on job start with correct info
- [ ] Log content streams to console in real-time
- [ ] Toast appears on job end with correct result type
- [ ] Console auto-scrolls during streaming
- [ ] Clear button works (also resets title to "Console Output")
- [ ] Collapse/expand animates smoothly
- [ ] Canceling stream (via control endpoint) shows message
- [ ] Multiple rapid job starts don't break parser
- [ ] Chunked tag boundaries handled correctly (e.g., `</lo` + `g>`)
- [ ] Console header shows active job ID (e.g., "Console Output (Job 42)")
- [ ] `[Connecting...]` shows before first chunk arrives
- [ ] Table row state updates when job completes
- [ ] Table row action buttons update when job completes (only Monitor remains)
- [ ] Long jobs (~1000+ items) don't freeze browser (buffer truncation works)
- [ ] `data-stream-url` attribute works for buttons from any router
