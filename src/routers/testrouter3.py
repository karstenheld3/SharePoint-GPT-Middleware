# V3 Streaming Test Router - Self-contained with inline UI (format=ui)
# Replicates testrouter2.py but adds streaming console UI without polluting common modules
import asyncio, datetime, json, random
from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from common_job_functions import StreamingJob, generate_streaming_job_id, create_streaming_job_file, create_streaming_job_control_file, find_streaming_job_file, write_streaming_job_log, rename_streaming_job_file, delete_streaming_job_file, streaming_job_file_exists, get_streaming_job_current_state, find_streaming_job_by_id, list_streaming_jobs
from utils import log_function_footer, log_function_header

router = APIRouter()

# Configuration will be injected from app.py
config = None

ROUTER_NAME = "testrouter3"

# Set the configuration for test router. app_config: Config dataclass with openai_client, persistent_storage_path, etc.
def set_config(app_config):
  global config
  config = app_config


# ============================================
# SELF-CONTAINED UI GENERATION FUNCTIONS
# ============================================

def generate_streaming_ui_page(title: str, jobs: list) -> str:
  """Generate complete HTML page with streaming console UI (reactive rendering)"""
  
  # Convert jobs list to JSON for JavaScript
  jobs_json = json.dumps(jobs)
  
  return f'''<!DOCTYPE html>
<html>
<head>
  <meta charset='utf-8'>
  <title>{title}</title>
  <link rel='stylesheet' href='/static/css/styles.css'>
  <script src='/static/js/htmx.js'></script>
  <style>
/* ============================================
   STREAMING CONSOLE & TOASTS (INLINE)
   ============================================ */

/* Toast Container */
#toast-container {{
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: 400px;
}}

.toast {{
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
}}

.toast.toast-info {{ border-left-color: #0078d4; }}
.toast.toast-success {{ border-left-color: #28a745; }}
.toast.toast-error {{ border-left-color: #dc3545; }}
.toast.toast-warning {{ border-left-color: #ffc107; }}

.toast-content {{
  flex: 1;
  font-size: 0.875rem;
}}

.toast-title {{
  font-weight: 600;
  margin-bottom: 0.25rem;
  color: #212529;
}}

.toast-dismiss {{
  background: none;
  border: none;
  color: #6c757d;
  cursor: pointer;
  padding: 0;
  font-size: 1.25rem;
  line-height: 1;
}}

.toast-dismiss:hover {{ color: #212529; }}

@keyframes slideIn {{
  from {{ transform: translateX(100%); opacity: 0; }}
  to {{ transform: translateX(0); opacity: 1; }}
}}

@keyframes fadeOut {{
  from {{ opacity: 1; }}
  to {{ opacity: 0; }}
}}

/* Console Panel */
.console-panel {{
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #1a1a1a;
  border-top: 1px solid #3c3c3c;
  z-index: 900;
  max-height: 232px;
  transition: max-height 0.2s ease;
}}

.console-panel.collapsed {{
  max-height: 32px;
}}

.console-panel.collapsed .console-output {{
  display: none;
}}

.console-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  background: #252525;
  border-bottom: 1px solid #3c3c3c;
  font-size: 0.875rem;
  font-weight: 500;
  color: #ffffff;
}}

.console-controls {{
  display: flex;
  gap: 0.5rem;
}}

.console-output {{
  height: 200px;
  overflow-y: auto;
  padding: 0.75rem 1rem;
  margin: 0;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.8125rem;
  line-height: 1.4;
  background: #1e1e1e;
  color: #ffffff;
  white-space: pre-wrap;
  word-wrap: break-word;
}}

body.console-visible main {{
  padding-bottom: 250px;
}}
  </style>
</head>
<body>
  <!-- Toast Container -->
  <div id="toast-container"></div>
  
  <!-- Main Content -->
  <div class="container">
    <h1>{title} <span id="job-count">({len(jobs)})</span></h1>
    
    <div class="toolbar">
      <button class="btn-primary" onclick="streamStart(this)" data-stream-url="/testrouter3/streaming01?format=stream&files=20">Start New Job (20 files)</button>
      <button class="btn-primary" onclick="streamStart(this)" data-stream-url="/testrouter3/streaming01?format=stream&files=5">Start New Job (5 files)</button>
      <button onclick="location.reload()" class="btn-small">Refresh</button>
    </div>
    
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Router</th>
          <th>Endpoint</th>
          <th>State</th>
          <th>Started</th>
          <th>Finished</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody id="jobs-tbody">
        <!-- Rendered by JavaScript -->
      </tbody>
    </table>
    
    <p><a href="/">← Back to Main Page</a></p>
  </div>
  
  <!-- Console Panel -->
  <div id="console-panel" class="console-panel collapsed">
    <div class="console-header">
      <span id="console-title">Console Output</span>
      <div class="console-controls">
        <button onclick="clearConsole()" class="btn-small">Clear</button>
        <button onclick="toggleConsole()" class="btn-small">_</button>
      </div>
    </div>
    <pre id="console-output" class="console-output"></pre>
  </div>
  
  <script>
// ============================================
// REACTIVE JOB STATE MANAGEMENT
// ============================================

// Initialize jobs from server
const jobsState = new Map();
const initialJobs = {jobs_json};

// Load initial jobs into state
initialJobs.forEach(job => {{
  jobsState.set(job.id, job);
}});

// Render functions
function renderJobRow(job) {{
  const actions = renderJobActions(job);
  // Format timestamps consistently (replace T with space, trim to 19 chars)
  const started = job.started ? job.started.substring(0, 19).replace('T', ' ') : '';
  const finished = job.finished ? job.finished.substring(0, 19).replace('T', ' ') : '-';
  return `
    <tr id="job-${{job.id}}">
      <td>${{job.id}}</td>
      <td>${{job.router}}</td>
      <td>${{job.endpoint}}</td>
      <td>${{job.state}}</td>
      <td>${{started}}</td>
      <td>${{finished}}</td>
      <td>${{actions}}</td>
    </tr>
  `;
}}

function renderJobActions(job) {{
  let html = `<button class="btn-small" onclick="streamMonitor(this)" data-stream-url="/testrouter3/monitor?sj_id=${{job.id}}">Monitor</button>`;
  
  if (job.state === 'running') {{
    html += ` <button class="btn-small" onclick="controlJob(${{job.id}}, 'pause')">Pause</button>`;
    html += ` <button class="btn-small btn-delete" onclick="controlJob(${{job.id}}, 'cancel')">Cancel</button>`;
  }} else if (job.state === 'paused') {{
    html += ` <button class="btn-small" onclick="controlJob(${{job.id}}, 'resume')">Resume</button>`;
    html += ` <button class="btn-small btn-delete" onclick="controlJob(${{job.id}}, 'cancel')">Cancel</button>`;
  }}
  
  return html;
}}

function renderAllJobs() {{
  const tbody = document.getElementById('jobs-tbody');
  if (!tbody) return;
  
  const jobs = Array.from(jobsState.values()).sort((a, b) => b.id - a.id);
  
  if (jobs.length === 0) {{
    tbody.innerHTML = '<tr class="empty-row"><td colspan="7">No jobs found</td></tr>';
  }} else {{
    tbody.innerHTML = jobs.map(job => renderJobRow(job)).join('');
  }}
  
  // Update count
  const countEl = document.getElementById('job-count');
  if (countEl) countEl.textContent = `(${{jobs.length}})`;
}}

function updateJob(id, updates) {{
  const job = jobsState.get(id);
  console.log('updateJob: Looking for job', id, 'Found:', job);
  if (job) {{
    console.log('Before update:', JSON.stringify(job));
    Object.assign(job, updates);
    console.log('After update:', JSON.stringify(job));
    renderAllJobs();
  }} else {{
    console.error('Job not found in state:', id);
  }}
}}

function addJob(job) {{
  jobsState.set(job.id, job);
  renderAllJobs();
}}

// Control job via fetch
async function controlJob(id, action) {{
  if (action === 'cancel' && !confirm(`Cancel job ${{id}}?`)) return;
  
  try {{
    const response = await fetch(`/testrouter3/control?sj_id=${{id}}&action=${{action}}`);
    const data = await response.json();
    if (data.success) {{
      // Optimistically update state
      if (action === 'pause') updateJob(id, {{ state: 'paused' }});
      if (action === 'cancel') updateJob(id, {{ state: 'canceled' }});
    }}
  }} catch (e) {{
    console.error('Control action failed:', e);
  }}
}}

// Initial render
renderAllJobs();

// ============================================
// STREAMING UI - Console & Toasts
// ============================================

let activeStreamController = null;
let activeJobId = null;
let isCurrentlyStreaming = false;

// ----------------------------------------
// TOAST FUNCTIONS
// ----------------------------------------

function showToast(title, message, type = 'info', autoDismiss = 5000) {{
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${{type}}`;
  toast.innerHTML = `
    <div class="toast-content">
      <div class="toast-title">${{escapeHtml(title)}}</div>
      <div class="toast-message">${{escapeHtml(message)}}</div>
    </div>
    <button class="toast-dismiss" onclick="this.parentElement.remove()">×</button>
  `;

  container.appendChild(toast);

  if (autoDismiss > 0) {{
    setTimeout(() => {{
      toast.style.animation = 'fadeOut 0.3s ease-out forwards';
      setTimeout(() => toast.remove(), 300);
    }}, autoDismiss);
  }}

  return toast;
}}

function showJobStartToast(jobData) {{
  const msg = `ID: ${{jobData.sj_id}} | Total: ${{jobData.total}} items`;
  showToast('Job Started', msg, 'info');
}}

function showJobEndToast(jobData) {{
  const type = jobData.result === 'OK' ? 'success' : 
               jobData.result === 'CANCELED' ? 'warning' : 'error';
  const msg = `ID: ${{jobData.sj_id}} | Result: ${{jobData.result}}`;
  showToast('Job Finished', msg, type);
}}

// ----------------------------------------
// CONSOLE FUNCTIONS
// ----------------------------------------

function setActiveJob(sjId) {{
  activeJobId = sjId;
  const title = document.getElementById('console-title');
  if (title) title.textContent = sjId ? `Console Output (Job ${{sjId}})` : 'Console Output';
}}

function appendToConsole(text) {{
  const output = document.getElementById('console-output');
  if (!output) return;
  
  output.textContent += text;
  
  const MAX_LENGTH = 50000;
  if (output.textContent.length > MAX_LENGTH) {{
    output.textContent = '...[truncated]\\n' + output.textContent.slice(-MAX_LENGTH);
  }}
  
  output.scrollTop = output.scrollHeight;
}}

function clearConsole() {{
  const output = document.getElementById('console-output');
  if (output) output.textContent = '';
  setActiveJob(null);
}}

function toggleConsole() {{
  const panel = document.getElementById('console-panel');
  if (panel) panel.classList.toggle('collapsed');
}}

// ----------------------------------------
// STREAM PARSER
// ----------------------------------------

class StreamParser {{
  constructor() {{
    this.buffer = '';
    this.state = 'idle';
  }}

  parse(chunk) {{
    this.buffer += chunk;
    
    while (this.buffer.length > 0) {{
      if (this.state === 'idle') {{
        if (this.buffer.includes('<start_json>')) {{
          const idx = this.buffer.indexOf('<start_json>');
          this.buffer = this.buffer.slice(idx + '<start_json>'.length);
          this.state = 'in_start_json';
        }} else if (this.buffer.includes('<log>')) {{
          const idx = this.buffer.indexOf('<log>');
          this.buffer = this.buffer.slice(idx + '<log>'.length);
          this.state = 'in_log';
        }} else if (this.buffer.includes('<end_json>')) {{
          const idx = this.buffer.indexOf('<end_json>');
          this.buffer = this.buffer.slice(idx + '<end_json>'.length);
          this.state = 'in_end_json';
        }} else {{
          if (this.buffer.length > 20) {{
            this.buffer = this.buffer.slice(-20);
          }}
          break;
        }}
      }}
      
      else if (this.state === 'in_start_json') {{
        const endIdx = this.buffer.indexOf('</start_json>');
        if (endIdx !== -1) {{
          const jsonStr = this.buffer.slice(0, endIdx).trim();
          this.buffer = this.buffer.slice(endIdx + '</start_json>'.length);
          this.state = 'idle';
          this.onStartJson(jsonStr);
        }} else {{
          break;
        }}
      }}
      
      else if (this.state === 'in_log') {{
        const endIdx = this.buffer.indexOf('</log>');
        if (endIdx !== -1) {{
          const logContent = this.buffer.slice(0, endIdx);
          this.buffer = this.buffer.slice(endIdx + '</log>'.length);
          this.state = 'idle';
          if (logContent) this.onLog(logContent);
        }} else {{
          if (this.buffer.length > 10) {{
            const toEmit = this.buffer.slice(0, -10);
            this.buffer = this.buffer.slice(-10);
            if (toEmit) this.onLog(toEmit);
          }}
          break;
        }}
      }}
      
      else if (this.state === 'in_end_json') {{
        const endIdx = this.buffer.indexOf('</end_json>');
        if (endIdx !== -1) {{
          const jsonStr = this.buffer.slice(0, endIdx).trim();
          this.buffer = this.buffer.slice(endIdx + '</end_json>'.length);
          this.state = 'idle';
          this.onEndJson(jsonStr);
        }} else {{
          break;
        }}
      }}
    }}
  }}

  onStartJson(jsonStr) {{
    try {{
      const data = JSON.parse(jsonStr);
      setActiveJob(data.id);
      showJobStartToast(data);
      
      // Add job to state with started timestamp
      addJob({{
        id: data.id,
        router: data.router,
        endpoint: data.endpoint,
        state: data.state.toLowerCase(),
        started: data.started,
        finished: null
      }});
    }} catch (e) {{
      console.error('Failed to parse start_json:', e);
    }}
  }}

  onLog(content) {{
    appendToConsole(content);
  }}

  onEndJson(jsonStr) {{
    try {{
      const data = JSON.parse(jsonStr);
      console.log('End JSON received:', data);
      showJobEndToast(data);
      
      // Update job state and finished timestamp
      console.log('Updating job', data.id, 'with finished:', data.finished);
      updateJob(data.id, {{
        state: data.state.toLowerCase(),
        finished: data.finished
      }});
    }} catch (e) {{
      console.error('Failed to parse end_json:', e);
    }}
  }}
}}

// ----------------------------------------
// STREAMING FETCH
// ----------------------------------------

async function startStreamingRequest(url, options = {{}}) {{
  if (activeStreamController) {{
    activeStreamController.abort();
  }}

  isCurrentlyStreaming = true;
  activeStreamController = new AbortController();
  const parser = new StreamParser();

  appendToConsole('[Connecting...]\\n');

  try {{
    const response = await fetch(url, {{
      signal: activeStreamController.signal,
      ...options
    }});

    if (!response.ok) {{
      showToast('Error', `Request failed: ${{response.status}}`, 'error');
      return;
    }}

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {{
      const {{ done, value }} = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value, {{ stream: true }});
      parser.parse(chunk);
    }}

  }} catch (e) {{
    if (e.name === 'AbortError') {{
      appendToConsole('\\n[Stream aborted]\\n');
    }} else {{
      showToast('Error', e.message, 'error');
      console.error('Streaming error:', e);
    }}
  }} finally {{
    isCurrentlyStreaming = false;
    activeStreamController = null;
  }}
}}

// ----------------------------------------
// BUTTON HANDLERS
// ----------------------------------------

function streamRequest(button) {{
  const url = button.dataset.streamUrl;
  if (!url) {{
    console.error('No data-stream-url on button');
    return;
  }}
  
  clearConsole();
  document.body.classList.add('console-visible');
  const panel = document.getElementById('console-panel');
  if (panel) panel.classList.remove('collapsed');
  
  startStreamingRequest(url);
}}

function streamMonitor(button) {{
  streamRequest(button);
}}

function streamStart(button) {{
  // Check if this page is currently streaming a job
  if (isCurrentlyStreaming) {{
    alert('Cannot start a new job. This page is already streaming a job. Please wait for it to complete.');
    return;
  }}
  streamRequest(button);
}}

// ----------------------------------------
// UTILITY
// ----------------------------------------

function escapeHtml(text) {{
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}}
  </script>
</body>
</html>'''


def generate_docs_page(endpoint: str, docstring: str) -> str:
  """Generate simple documentation page"""
  return f'''<!DOCTYPE html>
<html>
<head>
  <meta charset='utf-8'>
  <title>Documentation - {endpoint}</title>
  <link rel='stylesheet' href='/static/css/styles.css'>
</head>
<body>
  <div class="container">
    <h1>Documentation: {endpoint}</h1>
    <pre style="white-space: pre-wrap; background: #f5f5f5; padding: 1rem; border-radius: 4px;">{docstring}</pre>
    <p><a href="/">← Back to Main Page</a></p>
  </div>
</body>
</html>'''


# ============================================
# STREAMING ENDPOINT
# ============================================

@router.get('/streaming01')
async def streaming01(request: Request):
  """
  V3 Streaming Test Endpoint - simulates file processing with streaming console UI.
  
  Writes to log file AND streams to client. Supports pause/resume/cancel.
  Multiple clients can monitor the same job via /testrouter3/monitor.
  
  Parameters:
  - format: 'stream' to start streaming response, 'ui' for job list page (default shows docs)
  - files: Number of files to simulate (default: 20)
  
  Examples:
  /testrouter3/streaming01 (shows documentation)
  /testrouter3/streaming01?format=stream&files=20
  /testrouter3/streaming01?format=ui (shows job list with console)
  
  Control:
  - GET /testrouter3/control?sj_id=42&action=pause
  - GET /testrouter3/control?sj_id=42&action=resume
  - GET /testrouter3/control?sj_id=42&action=cancel
  
  Monitor:
  - GET /testrouter3/monitor?sj_id=42
  
  Output format:
  <start_json>
  {"sj_id": 42, "monitor_url": "/testrouter3/monitor?sj_id=42", "total": 20, ...}
  </start_json>
  <log>
  [ 1 / 20 ] Processing 'document_001.pdf'...
    OK.
  ...
  </log>
  <end_json>
  {"result": "OK", "state": "COMPLETED", "sj_id": 42, ...}
  </end_json>
  """
  function_name = 'streaming01()'
  log_data = log_function_header(function_name)
  request_params = dict(request.query_params)

  # Display documentation if no params
  if len(request_params) == 0:
    await log_function_footer(log_data)
    return HTMLResponse(generate_docs_page('/testrouter3/streaming01', streaming01.__doc__))

  response_format = request_params.get('format', 'stream')
  
  # Handle format=ui - show job list with console
  if response_format == 'ui':
    if not config or not config.LOCAL_PERSISTENT_STORAGE_PATH:
      await log_function_footer(log_data)
      return JSONResponse({"error": "LOCAL_PERSISTENT_STORAGE_PATH not configured"}, status_code=500)
    
    storage_path = config.LOCAL_PERSISTENT_STORAGE_PATH
    jobs = list_streaming_jobs(storage_path, router_filter=ROUTER_NAME)
    
    # Convert StreamingJob dataclass instances to dicts for JSON serialization
    jobs_dicts = []
    for job in jobs:
      job_dict = asdict(job)
      # Convert datetime objects to ISO strings
      if job_dict['started']:
        job_dict['started'] = job_dict['started'].isoformat()
      if job_dict['finished']:
        job_dict['finished'] = job_dict['finished'].isoformat()
      jobs_dicts.append(job_dict)
    
    await log_function_footer(log_data)
    return HTMLResponse(generate_streaming_ui_page("Streaming Jobs", jobs_dicts))

  file_count = int(request_params.get('files', '20'))

  if response_format != 'stream':
    await log_function_footer(log_data)
    return JSONResponse({"message": "Use format=stream for streaming response", "files": file_count})

  # Check config
  if not config or not config.LOCAL_PERSISTENT_STORAGE_PATH:
    await log_function_footer(log_data)
    return JSONResponse({"error": "LOCAL_PERSISTENT_STORAGE_PATH not configured"}, status_code=500)

  storage_path = config.LOCAL_PERSISTENT_STORAGE_PATH
  endpoint_name = "streaming01"

  # Generate unique job ID with retry on collision
  max_retries = 3
  sj_id = None
  job_timestamp = None

  for attempt in range(max_retries):
    sj_id = generate_streaming_job_id(storage_path)
    success, job_timestamp = create_streaming_job_file(storage_path, ROUTER_NAME, endpoint_name, sj_id, "running")
    if success: break
    sj_id = None
    job_timestamp = None

  if sj_id is None:
    await log_function_footer(log_data)
    return JSONResponse({"error": "Failed to create streaming job after retries"}, status_code=500)

  source_url = f"{request.url.path}?{request.query_params}" if request.query_params else str(request.url.path)

  async def generate_stream():
    simulated_files = [f"document_{i:03d}.pdf" for i in range(1, file_count + 1)]
    processed_files = []
    failed_files = []

    # Initialize StreamingJob
    job = StreamingJob(
      id=sj_id,
      source_url=source_url,
      monitor_url=f"/testrouter3/monitor?sj_id={sj_id}",
      router=ROUTER_NAME,
      endpoint=endpoint_name,
      state="RUNNING",
      total=file_count,
      current=0,
      started=datetime.datetime.now(),
      finished=None,
      result=None,
      result_data=None
    )

    # ----- HEADER SECTION -----
    header_text = f"<start_json>\n{json.dumps(asdict(job), indent=2, default=str)}\n</start_json>\n"
    write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, header_text)
    yield header_text

    # ----- LOG SECTION START -----
    log_start = "<log>\n"
    write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, log_start)
    yield log_start

    # ----- PROCESS ITEMS -----
    for index, filename in enumerate(simulated_files, start=1):

      # Check for cancel request
      if streaming_job_file_exists(storage_path, ROUTER_NAME, endpoint_name, sj_id, "cancel_requested"):
        cancel_msg = "  Cancel requested, stopping...\n"
        write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, cancel_msg)
        yield cancel_msg
        delete_streaming_job_file(storage_path, ROUTER_NAME, endpoint_name, sj_id, "cancel_requested")
        job.state = "CANCELED"
        job.result = "CANCELED"
        break

      # Check for pause request
      if streaming_job_file_exists(storage_path, ROUTER_NAME, endpoint_name, sj_id, "pause_requested"):
        pause_msg = "  Pause requested, pausing...\n"
        write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, pause_msg)
        yield pause_msg
        delete_streaming_job_file(storage_path, ROUTER_NAME, endpoint_name, sj_id, "pause_requested")
        rename_streaming_job_file(storage_path, ROUTER_NAME, endpoint_name, sj_id, "running", "paused")

      # Wait while paused
      while streaming_job_file_exists(storage_path, ROUTER_NAME, endpoint_name, sj_id, "paused"):
        # Check for cancel while paused
        if streaming_job_file_exists(storage_path, ROUTER_NAME, endpoint_name, sj_id, "cancel_requested"):
          cancel_msg = "  Cancel requested while paused, stopping...\n"
          write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, cancel_msg)
          yield cancel_msg
          delete_streaming_job_file(storage_path, ROUTER_NAME, endpoint_name, sj_id, "cancel_requested")
          delete_streaming_job_file(storage_path, ROUTER_NAME, endpoint_name, sj_id, "paused")
          job.state = "CANCELED"
          job.result = "CANCELED"
          break

        # Check for resume request
        if streaming_job_file_exists(storage_path, ROUTER_NAME, endpoint_name, sj_id, "resume_requested"):
          resume_msg = "  Resume requested, resuming...\n"
          write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, resume_msg)
          yield resume_msg
          delete_streaming_job_file(storage_path, ROUTER_NAME, endpoint_name, sj_id, "resume_requested")
          rename_streaming_job_file(storage_path, ROUTER_NAME, endpoint_name, sj_id, "paused", "running")
          break

        await asyncio.sleep(0.1)

      # Check if we were canceled while paused
      if job.state == "CANCELED": break

      # Process item
      progress_msg = f"[ {index} / {file_count} ] Processing '{filename}'...\n"
      write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, progress_msg)
      yield progress_msg

      await asyncio.sleep(0.2)  # Simulate work

      # Simulate random failures (10% chance)
      if random.random() < 0.1:
        fail_msg = f"  FAIL: Simulated error for '{filename}'\n"
        write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, fail_msg)
        yield fail_msg
        failed_files.append({"filename": filename, "error": "Simulated error"})
      else:
        ok_msg = "  OK.\n"
        write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, ok_msg)
        yield ok_msg
        processed_files.append({"filename": filename, "size_bytes": random.randint(10000, 500000)})

    # ----- LOG SECTION END -----
    log_end = "</log>\n"
    write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, log_end)
    yield log_end

    # ----- FOOTER SECTION -----
    job.current = len(processed_files) + len(failed_files)
    job.finished = datetime.datetime.now()
    
    if job.result != "CANCELED":
      job.state = "COMPLETED"
      job.result = "PARTIAL" if failed_files else "OK"
    
    job.result_data = {
      "processed": len(processed_files),
      "failed": len(failed_files),
      "processed_files": processed_files,
      "failed_files": failed_files
    }

    footer_text = f"<end_json>\n{json.dumps(asdict(job), indent=2, default=str)}\n</end_json>\n"
    write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, footer_text)
    yield footer_text

    # ----- FINALIZE STATE -----
    for current_state in ["running", "paused"]:
      if streaming_job_file_exists(storage_path, ROUTER_NAME, endpoint_name, sj_id, current_state):
        rename_streaming_job_file(storage_path, ROUTER_NAME, endpoint_name, sj_id, current_state, job.state.lower())
        break

    await log_function_footer(log_data)

  return StreamingResponse(generate_stream(), media_type="text/event-stream; charset=utf-8")


# ============================================
# MONITOR ENDPOINT
# ============================================

@router.get('/monitor')
async def monitor_streaming_job(request: Request):
  """
  Monitor a streaming job by tailing its log file.
  
  Can attach to running, completed, or canceled jobs.
  Multiple monitors can attach to the same job simultaneously.
  
  Parameters:
  - sj_id: Streaming job ID to monitor (required)
  
  Examples:
  /testrouter3/monitor?sj_id=42
  """
  function_name = 'monitor_streaming_job()'
  log_data = log_function_header(function_name)
  request_params = dict(request.query_params)

  if len(request_params) == 0:
    await log_function_footer(log_data)
    return HTMLResponse(generate_docs_page('/testrouter3/monitor', monitor_streaming_job.__doc__))

  sj_id_str = request_params.get('sj_id')
  if not sj_id_str:
    await log_function_footer(log_data)
    return JSONResponse({"error": "Missing 'sj_id' parameter"}, status_code=400)

  sj_id = int(sj_id_str)

  if not config or not config.LOCAL_PERSISTENT_STORAGE_PATH:
    await log_function_footer(log_data)
    return JSONResponse({"error": "LOCAL_PERSISTENT_STORAGE_PATH not configured"}, status_code=500)

  storage_path = config.LOCAL_PERSISTENT_STORAGE_PATH

  # Find the job
  job_info = find_streaming_job_by_id(storage_path, sj_id)
  if not job_info:
    await log_function_footer(log_data)
    return JSONResponse({"error": f"Job {sj_id} not found"}, status_code=404)

  router_name = job_info["router_name"]
  endpoint_name = job_info["endpoint_name"]
  file_path = job_info["file_path"]

  async def tail_log_file():
    with open(file_path, 'r', encoding='utf-8') as f:
      while True:
        chunk = f.read(4096)
        if chunk:
          yield chunk
        else:
          # No more data - check if job is still active
          current_state = get_streaming_job_current_state(storage_path, router_name, endpoint_name, sj_id)
          if current_state in ["running", "paused"]:
            await asyncio.sleep(0.1)
            # Re-check file path in case it was renamed
            new_job_info = find_streaming_job_by_id(storage_path, sj_id)
            if new_job_info and new_job_info["file_path"] != file_path:
              break  # File was renamed, reopen would be needed
          else:
            # Job completed/canceled - do final read to catch any remaining content
            final_chunk = f.read()
            if final_chunk:
              yield final_chunk
            break

  await log_function_footer(log_data)
  return StreamingResponse(tail_log_file(), media_type="text/event-stream; charset=utf-8")


# ============================================
# CONTROL ENDPOINT
# ============================================

@router.get('/control')
async def control_streaming_job(request: Request):
  """
  Control a streaming job (pause/resume/cancel).
  
  Parameters:
  - sj_id: Streaming job ID (required)
  - action: One of 'pause', 'resume', 'cancel' (required)
  - format: 'json' or 'ui' (default: 'json')
  
  Examples:
  /testrouter3/control?sj_id=42&action=pause
  /testrouter3/control?sj_id=42&action=resume&format=ui
  /testrouter3/control?sj_id=42&action=cancel
  """
  function_name = 'control_streaming_job()'
  log_data = log_function_header(function_name)
  request_params = dict(request.query_params)

  if len(request_params) == 0:
    await log_function_footer(log_data)
    return HTMLResponse(generate_docs_page('/testrouter3/control', control_streaming_job.__doc__))

  sj_id_str = request_params.get('sj_id')
  action = request_params.get('action')

  if not sj_id_str or not action:
    await log_function_footer(log_data)
    return JSONResponse({"error": "Missing 'sj_id' or 'action' parameter"}, status_code=400)

  sj_id = int(sj_id_str)
  valid_actions = ["pause", "resume", "cancel"]
  if action not in valid_actions:
    await log_function_footer(log_data)
    return JSONResponse({"error": f"Invalid action '{action}'. Must be one of: {valid_actions}"}, status_code=400)

  if not config or not config.LOCAL_PERSISTENT_STORAGE_PATH:
    await log_function_footer(log_data)
    return JSONResponse({"error": "LOCAL_PERSISTENT_STORAGE_PATH not configured"}, status_code=500)

  storage_path = config.LOCAL_PERSISTENT_STORAGE_PATH

  # Find the job
  job_info = find_streaming_job_by_id(storage_path, sj_id)
  if not job_info:
    await log_function_footer(log_data)
    return JSONResponse({"error": f"Job {sj_id} not found"}, status_code=404)

  router_name = job_info["router_name"]
  endpoint_name = job_info["endpoint_name"]
  current_state = job_info["state"]
  job_timestamp = job_info["timestamp"]

  # Validate state for action
  if current_state not in ["running", "paused"]:
    await log_function_footer(log_data)
    return JSONResponse({"error": f"Cannot {action} job {sj_id} - job is {current_state}"}, status_code=400)

  # Create control request file
  control_state = f"{action}_requested"
  success = create_streaming_job_control_file(storage_path, router_name, endpoint_name, sj_id, job_timestamp, control_state)

  await log_function_footer(log_data)

  # Always return JSON - client-side JavaScript handles UI updates
  if success:
    return JSONResponse({"success": True, "sj_id": sj_id, "action": action, "message": f"{action.capitalize()} requested for job {sj_id}"})
  else:
    return JSONResponse({"success": False, "sj_id": sj_id, "action": action, "message": f"{action.capitalize()} already requested for job {sj_id}"})


# ============================================
# LIST JOBS ENDPOINT
# ============================================

@router.get('/jobs')
async def list_jobs(request: Request):
  """
  List all streaming jobs with optional filters.
  
  Parameters:
  - format: Response format ('json', 'ui') - default: 'ui'
  - router: Filter by router name
  - endpoint: Filter by endpoint name
  - state: Filter by state ('running', 'paused', 'completed', 'canceled')
  
  Examples:
  /testrouter3/jobs (shows UI with console)
  /testrouter3/jobs?format=json
  /testrouter3/jobs?state=running
  /testrouter3/jobs?router=testrouter3&state=completed
  """
  function_name = 'list_jobs()'
  log_data = log_function_header(function_name)
  request_params = dict(request.query_params)

  response_format = request_params.get('format', 'ui')
  router_filter = request_params.get('router')
  endpoint_filter = request_params.get('endpoint')
  state_filter = request_params.get('state')

  if not config or not config.LOCAL_PERSISTENT_STORAGE_PATH:
    await log_function_footer(log_data)
    return JSONResponse({"error": "LOCAL_PERSISTENT_STORAGE_PATH not configured"}, status_code=500)

  storage_path = config.LOCAL_PERSISTENT_STORAGE_PATH
  jobs = list_streaming_jobs(storage_path, router_filter=router_filter, endpoint_filter=endpoint_filter, state_filter=state_filter)

  # Convert StreamingJob dataclass instances to dicts for JSON serialization
  jobs_dicts = []
  for job in jobs:
    job_dict = asdict(job)
    # Convert datetime objects to ISO strings
    if job_dict['started']:
      job_dict['started'] = job_dict['started'].isoformat()
    if job_dict['finished']:
      job_dict['finished'] = job_dict['finished'].isoformat()
    jobs_dicts.append(job_dict)

  await log_function_footer(log_data)

  if response_format == "json":
    return JSONResponse({"jobs": jobs_dicts, "count": len(jobs_dicts)})
  else:
    # Default to UI with streaming console
    return HTMLResponse(generate_streaming_ui_page("Streaming Jobs", jobs_dicts))
