# Jobs Router V2 - Job monitoring and control UI
# Spec: L(jhu)G(jh)D(jh): /v2/jobs
# Implements _V2_SPEC_JOBS_UI.md specification

import asyncio, textwrap, uuid
import httpx
from dataclasses import asdict
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, StreamingResponse

from routers_v2.common_ui_functions_v2 import generate_router_docs_page, generate_endpoint_docs, json_result, html_result, generate_html_head, generate_toast_container, generate_modal_structure, generate_console_panel, generate_core_js, generate_console_js, generate_form_js, generate_endpoint_caller_js
from routers_v2.common_logging_functions_v2 import MiddlewareLogger, UNKNOWN
from routers_v2.common_job_functions_v2 import list_jobs, find_job_by_id, find_job_file, read_job_log, read_job_result, create_control_file, delete_job, force_cancel_job, JobMetadata, StreamingJobWriter, ControlAction

router = APIRouter()
config = None
router_prefix = None
router_name = "jobs"
main_page_nav_html = '<a href="/">Back to Main Page</a> | <a href="{router_prefix}/domains?format=ui">Domains</a> | <a href="{router_prefix}/crawler?format=ui">Crawler</a> | <a href="{router_prefix}/jobs?format=ui">Jobs</a> | <a href="{router_prefix}/reports?format=ui">Reports</a>'
example_item_json = """
{
  "job_id": "jb_42",
  "state": "completed",
  "source_url": "/v2/crawler/crawl?domain_id=DOMAIN01&format=stream",
  "monitor_url": "/v2/jobs/monitor?job_id=jb_42&format=stream",
  "started_utc": "2025-01-15T14:20:30.000000Z",
  "finished_utc": "2025-01-15T14:25:45.000000Z",
  "last_modified_utc": "2025-01-15T14:25:45.000000Z",
  "result": {"ok": true, "error": "", "data": {}}
}
"""

def set_config(app_config, prefix):
  global config, router_prefix
  config = app_config
  router_prefix = prefix

def get_persistent_storage_path() -> str:
  return getattr(config, 'LOCAL_PERSISTENT_STORAGE_PATH', None) or ''

def _job_to_dict(job: JobMetadata) -> dict:
  """Convert JobMetadata dataclass to dict for JSON serialization."""
  return asdict(job)

def _extract_last_log_line(log_content: str) -> str:
  """Extract the last log line data from SSE log content."""
  if not log_content:
    return ""
  lines = log_content.strip().split('\n')
  for line in reversed(lines):
    if line.startswith('data: '):
      return line[6:]
  return ""


# ----------------------------------------- START: Router-specific JS ------------------------------------------------------

def get_router_specific_js() -> str:
  """Jobs-specific JavaScript for job monitoring, control, and rendering."""
  return f"""
// ============================================
// JOB STATE MANAGEMENT
// ============================================
const jobsState = new Map();
const STALE_THRESHOLD_MS = 300000; // 5 minutes

function isStalled(job) {{
  if (job.state !== 'running' && job.state !== 'paused') return false;
  if (!job.last_modified_utc) return false;
  const mtime = new Date(job.last_modified_utc).getTime();
  const age = Date.now() - mtime;
  return age > STALE_THRESHOLD_MS;
}}

function onJobStateChange(jobId, state) {{
  const job = jobsState.get(jobId);
  if (!job) return;
  job.state = state;
  const rowId = 'job-' + sanitizeId(jobId);
  const row = document.getElementById(rowId);
  if (row) {{
    row.outerHTML = renderJobRow(job);
  }}
  updateSelectedCount();
}}

// ============================================
// PAGE INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', async () => {{
  await refreshJobs();
  initConsoleResize();
}});

// ============================================
// JOB LOADING
// ============================================
async function refreshJobs() {{
  try {{
    const response = await fetch('{router_prefix}/{router_name}?format=json');
    const result = await response.json();
    if (result.ok) {{
      jobsState.clear();
      result.data.forEach(job => jobsState.set(job.job_id, job));
      renderAllJobs();
    }} else {{
      showToast('Load Failed', result.error, 'error');
    }}
  }} catch (e) {{
    showToast('Load Failed', e.message, 'error');
  }}
}}

function reloadItems() {{
  refreshJobs();
}}

// ============================================
// JOB RENDERING
// ============================================
function renderAllJobs() {{
  const jobs = Array.from(jobsState.values());
  const tbody = document.getElementById('items-tbody');
  
  if (jobs.length === 0) {{
    tbody.innerHTML = '<tr><td colspan=\"10\" class=\"empty-state\">No jobs found</td></tr>';
  }} else {{
    tbody.innerHTML = jobs.map(job => renderJobRow(job)).join('');
  }}
  
  const countEl = document.getElementById('item-count');
  if (countEl) countEl.textContent = jobs.length;
  updateSelectedCount();
}}

function renderJobRow(job) {{
  const parsed = parseSourceUrl(job.source_url || '');
  const started = formatTimestamp(job.started_utc);
  const finished = formatTimestamp(job.finished_utc);
  const objectsHtml = parsed.objectIds.length > 0 ? escapeHtml(parsed.objectIds.join(', ')) : '-';
  const stalled = isStalled(job);
  const stateDisplay = stalled ? job.state + ' (stalled)' : job.state;
  const resultDisplay = formatResultOkFail(job.result?.ok);
  const isCancelOrFail = job.state === 'cancelled' || (job.result && !job.result.ok);
  const isRunning = job.state === 'running';
  
  const actions = renderJobActions(job, stalled);
  const rowId = sanitizeId(job.job_id);
  const rowClass = isRunning ? 'row-running' : (isCancelOrFail ? 'row-cancel-or-fail' : '');
  
  return '<tr id="job-' + rowId + '"' + (rowClass ? ' class="' + rowClass + '"' : '') + '>' +
    '<td><input type="checkbox" class="item-checkbox" data-item-id="' + escapeHtml(job.job_id) + '" onchange="updateSelectedCount()"></td>' +
    '<td>' + escapeHtml(job.job_id) + '</td>' +
    '<td>' + escapeHtml(parsed.router) + '</td>' +
    '<td>' + escapeHtml(parsed.endpoint) + '</td>' +
    '<td>' + objectsHtml + '</td>' +
    '<td>' + escapeHtml(stateDisplay) + '</td>' +
    '<td>' + escapeHtml(resultDisplay) + '</td>' +
    '<td>' + escapeHtml(started) + '</td>' +
    '<td>' + escapeHtml(finished) + '</td>' +
    '<td class="actions">' + actions + '</td>' +
    '</tr>';
}}

function renderJobActions(job, stalled) {{
  const jobId = job.job_id;
  const state = job.state;
  let actions = [];
  
  if (state === 'completed' || state === 'cancelled') {{
    actions.push('<button class="btn-small" onclick="showJobResult(\\'' + jobId + '\\')">Result</button>');
  }}
  
  actions.push('<button class="btn-small" onclick="monitorJob(\\'' + jobId + '\\')">Monitor</button>');
  
  if (state === 'running') {{
    if (stalled) {{
      actions.push('<button class="btn-small" onclick="if(confirm(\\'Force cancel stalled job ' + jobId + '?\\')) callJobControl(this, \\'' + jobId + '\\')" data-url="{router_prefix}/{router_name}/control?job_id=' + jobId + '&action=cancel&force=true">Force Cancel</button>');
    }} else {{
      actions.push('<button class="btn-small" data-url="{router_prefix}/{router_name}/control?job_id=' + jobId + '&action=pause" onclick="callJobControl(this, \\'' + jobId + '\\')">Pause</button>');
      actions.push('<button class="btn-small" onclick="if(confirm(\\'Cancel job ' + jobId + '?\\')) callJobControl(this, \\'' + jobId + '\\')" data-url="{router_prefix}/{router_name}/control?job_id=' + jobId + '&action=cancel">Cancel</button>');
    }}
  }} else if (state === 'paused') {{
    if (stalled) {{
      actions.push('<button class="btn-small" onclick="if(confirm(\\'Force cancel stalled job ' + jobId + '?\\')) callJobControl(this, \\'' + jobId + '\\')" data-url="{router_prefix}/{router_name}/control?job_id=' + jobId + '&action=cancel&force=true">Force Cancel</button>');
    }} else {{
      actions.push('<button class="btn-small" data-url="{router_prefix}/{router_name}/control?job_id=' + jobId + '&action=resume" onclick="callJobControl(this, \\'' + jobId + '\\')">Resume</button>');
      actions.push('<button class="btn-small" onclick="if(confirm(\\'Cancel job ' + jobId + '?\\')) callJobControl(this, \\'' + jobId + '\\')" data-url="{router_prefix}/{router_name}/control?job_id=' + jobId + '&action=cancel">Cancel</button>');
    }}
  }}
  
  // Delete button - always available
  actions.push('<button class="btn-small btn-delete" onclick="if(confirm(\\'Delete job ' + jobId + '?\\')) deleteJob(\\'' + jobId + '\\')">Delete</button>');
  
  return actions.join(' ');
}}

// ============================================
// SOURCE URL PARSING
// ============================================
function parseSourceUrl(source_url) {{
  if (!source_url) return {{ router: '-', endpoint: '-', objectIds: [] }};
  
  try {{
    const url = new URL(source_url, window.location.origin);
    const pathParts = url.pathname.split('/').filter(p => p && p !== 'v2');
    
    const router = pathParts[0] || '-';
    const endpoint = pathParts.slice(1).join('/') || '-';
    
    const objectIds = [];
    for (const [key, value] of url.searchParams) {{
      if (key.endsWith('_id') && key !== 'format') {{
        objectIds.push(value);
      }}
    }}
    
    return {{ router, endpoint, objectIds }};
  }} catch (e) {{
    return {{ router: '-', endpoint: '-', objectIds: [] }};
  }}
}}

// ============================================
// JOB MONITORING
// ============================================
function monitorJob(jobId) {{
  const url = '{router_prefix}/{router_name}/monitor?job_id=' + jobId + '&format=stream';
  currentJobId = jobId;
  connectStream(url, {{ reloadOnFinish: true, showResult: 'none', clearConsole: true }});
}}

// ============================================
// JOB CONTROL
// ============================================
async function callJobControl(btn, jobId) {{
  const url = btn.dataset.url;
  try {{
    const response = await fetch(url);
    const result = await response.json();
    if (result.ok) {{
      const action = result.data?.action;
      updateJobState(jobId, action);
      showToast(action.charAt(0).toUpperCase() + action.slice(1) + ' requested', jobId, 'info');
    }} else {{
      showErrorModal(result);
    }}
  }} catch (e) {{
    showToast('Error', e.message, 'error');
  }}
}}

function updateJobState(jobId, action) {{
  const newState = action === 'pause' ? 'paused' 
                 : action === 'resume' ? 'running' 
                 : action === 'cancel' ? 'cancelled' : null;
  if (newState) {{
    const job = jobsState.get(jobId);
    if (job) {{
      job.state = newState;
      renderAllJobs();
    }}
  }}
}}

// ============================================
// JOB RESULT
// ============================================
async function showJobResult(jobId) {{
  try {{
    const response = await fetch('{router_prefix}/{router_name}/results?job_id=' + jobId + '&format=json');
    const result = await response.json();
    if (result.ok) {{
      showResultModal(result.data);
    }} else {{
      showToast('Error', result.error, 'error');
    }}
  }} catch (e) {{
    showToast('Error', e.message, 'error');
  }}
}}

// ============================================
// ERROR MODAL
// ============================================
function showErrorModal(response) {{
  const body = document.querySelector('#modal .modal-body');
  body.innerHTML = `
    <div class="modal-header"><h3>Control Action Failed</h3></div>
    <div class="modal-scroll">
      <p><strong>Action:</strong> ${{escapeHtml(response.data?.action || 'unknown')}}</p>
      <p><strong>Job:</strong> ${{escapeHtml(response.data?.job_id || 'unknown')}}</p>
      <p style="color: #dc3545;"><strong>Error:</strong> ${{escapeHtml(response.error)}}</p>
    </div>
    <div class="modal-footer"><button type="button" class="btn-primary" onclick="closeModal()">OK</button></div>
  `;
  openModal();
}}

// ============================================
// SELECTION & BULK DELETE
// ============================================
const ROW_ID_PREFIX = 'job';
const DELETE_ENDPOINT = '{router_prefix}/{router_name}/delete?job_id={{itemId}}';

function getSelectedJobIds() {{
  return getSelectedIds();
}}

async function deleteJob(jobId) {{
  try {{
    const url = DELETE_ENDPOINT.replace('{{itemId}}', jobId);
    const response = await fetch(url, {{ method: 'DELETE' }});
    const result = await response.json();
    if (result.ok) {{
      jobsState.delete(jobId);
      renderAllJobs();
      showToast('Deleted', 'Job ' + jobId + ' deleted.', 'success');
    }} else {{
      showToast('Error', result.error, 'error');
    }}
  }} catch (e) {{
    showToast('Error', e.message, 'error');
  }}
}}

async function bulkDelete() {{
  const jobIds = getSelectedJobIds();
  if (jobIds.length === 0) return;
  if (!confirm('Delete ' + jobIds.length + ' selected jobs?')) return;
  
  let deleted = 0;
  let failed = 0;
  
  for (const jobId of jobIds) {{
    try {{
      const url = DELETE_ENDPOINT.replace('{{itemId}}', jobId);
      const response = await fetch(url, {{ method: 'DELETE' }});
      const result = await response.json();
      if (result.ok) {{
        jobsState.delete(jobId);
        deleted++;
      }} else {{
        failed++;
      }}
    }} catch (e) {{
      failed++;
    }}
  }}
  
  renderAllJobs();
  
  if (failed === 0) {{
    const msg = deleted === 1 ? '1 job deleted' : deleted + ' jobs deleted';
    showToast('Bulk Delete', msg, 'success');
  }} else {{
    showToast('Bulk Delete', deleted + ' deleted, ' + failed + ' failed', 'warning');
  }}
}}
"""

# ----------------------------------------- END: Router-specific JS --------------------------------------------------------


# ----------------------------------------- START: L(jhu) - Router root / List --------------------------------------------

@router.get(f"/{router_name}")
async def jobs_root(request: Request):
  """Jobs Router - Monitor and control long-running jobs"""
  logger = MiddlewareLogger.create()
  logger.log_function_header("jobs_root")
  request_params = dict(request.query_params)
  
  if len(request_params) == 0:
    logger.log_function_footer()
    endpoints = [
      {"path": "", "desc": "List all jobs", "formats": ["json", "html", "ui"]},
      {"path": "/get", "desc": "Get single job metadata", "formats": ["json", "html"]},
      {"path": "/monitor", "desc": "Monitor job output", "formats": ["json", "html", "stream"]},
      {"path": "/control", "desc": "Pause/Resume/Cancel job", "formats": ["json"]},
      {"path": "/results", "desc": "Get job result", "formats": ["json", "html"]},
      {"path": "/delete", "desc": "Delete job file (DELETE/GET)", "formats": []},
      {"path": "/selftest", "desc": "Self-test", "formats": ["stream"]}
    ]
    return HTMLResponse(generate_router_docs_page(
      title="Jobs Router",
      description="Monitor and control long-running streaming jobs.",
      router_prefix=f"{router_prefix}/{router_name}",
      endpoints=endpoints,
      navigation_html=main_page_nav_html.replace("{router_prefix}", router_prefix)
    ))
  
  format_param = request_params.get("format", "json")
  router_filter = request_params.get("router", None)
  state_filter = request_params.get("state", None)
  
  jobs = list_jobs(get_persistent_storage_path(), router_filter, state_filter)
  jobs_data = [_job_to_dict(job) for job in jobs]
  
  if format_param == "json":
    logger.log_function_footer()
    return json_result(True, "", jobs_data)
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result("Jobs", jobs_data, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
  
  if format_param == "ui":
    logger.log_function_footer()
    return HTMLResponse(_generate_jobs_ui_page(jobs_data))
  
  logger.log_function_footer()
  return json_result(False, f"Format '{format_param}' not supported. Use: json, html, ui", {})

def _generate_jobs_ui_page(jobs: list) -> str:
  """Generate the Jobs UI page HTML."""
  head = generate_html_head("Jobs", include_htmx=True, include_v2_css=True)
  toast_container = generate_toast_container()
  modal = generate_modal_structure()
  console = generate_console_panel("Console Output", include_pause_resume_cancel=True)
  
  core_js = generate_core_js()
  console_js = generate_console_js(router_prefix, f"{router_prefix}/{router_name}/control")
  form_js = generate_form_js()
  endpoint_caller_js = generate_endpoint_caller_js()
  router_js = get_router_specific_js()
  
  return f"""<!doctype html><html lang="en">
{head}
<style>
.row-running {{ font-weight: bold; }}
</style>
<body class="has-console">
  {toast_container}
  {modal}
  
  <div class="container">
    <div class="page-header">
      <h1>Jobs (<span id="item-count">0</span>)</h1>
      <button onclick="refreshJobs()" class="btn-small">Reload</button>
    </div>
    
    <p>{main_page_nav_html.replace("{router_prefix}", router_prefix)}</p>
    
    <div class="toolbar">
      <button id="btn-delete-selected" class="btn-primary btn-delete" onclick="bulkDelete()" disabled>Delete (<span id="selected-count">0</span>)</button>
      <button class="btn-primary" data-url="{router_prefix}/{router_name}/selftest?format=stream" data-format="stream" data-show-result="modal" data-reload-on-finish="true" onclick="callEndpoint(this)">Run Selftest</button>
    </div>
    
    <table>
      <thead>
        <tr>
          <th><input type="checkbox" id="select-all" onchange="toggleSelectAll()"></th>
          <th>Job ID</th>
          <th>Router</th>
          <th>Endpoint</th>
          <th>Objects</th>
          <th>State</th>
          <th>Result</th>
          <th>Started</th>
          <th>Finished</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody id="items-tbody">
        <tr><td colspan="10" class="empty-state">Loading...</td></tr>
      </tbody>
    </table>
  </div>
  
  {console}
  
  <script>
{core_js}
{console_js}
{form_js}
{endpoint_caller_js}
{router_js}
  </script>
</body>
</html>"""

# ----------------------------------------- END: L(jhu) - Router root / List ----------------------------------------------


# ----------------------------------------- START: G(jh) - Get single ------------------------------------------------------

@router.get(f"/{router_name}/get")
async def jobs_get(request: Request):
  """
  Get a single job's metadata.
  
  Parameters:
  - job_id: ID of the job (required)
  - format: Response format - json (default), html
  
  Examples:
  {router_prefix}/{router_name}/get?job_id=jb_42
  {router_prefix}/{router_name}/get?job_id=jb_42&format=html
  
  Response (job metadata):
  {example_item_json}
  """
  logger = MiddlewareLogger.create()
  logger.log_function_header("jobs_get")
  
  if len(request.query_params) == 0:
    logger.log_function_footer()
    doc = textwrap.dedent(jobs_get.__doc__).replace("{router_prefix}", router_prefix).replace("{router_name}", router_name).replace("{example_item_json}", example_item_json)
    return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")
  
  request_params = dict(request.query_params)
  job_id = request_params.get("job_id", None)
  format_param = request_params.get("format", "json")
  
  if not job_id:
    logger.log_function_footer()
    if format_param == "html": return html_result("Error", {"error": "Missing 'job_id' parameter."}, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
    return json_result(False, "Missing 'job_id' parameter.", {})
  
  job = find_job_by_id(get_persistent_storage_path(), job_id)
  if job is None:
    logger.log_function_footer()
    if format_param == "html": return html_result("Not Found", {"error": f"Job '{job_id}' not found."}, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
    return JSONResponse({"ok": False, "error": f"Job '{job_id}' not found.", "data": {}}, status_code=404)
  
  job_data = _job_to_dict(job)
  
  if format_param == "json":
    logger.log_function_footer()
    return json_result(True, "", job_data)
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Job: {job_id}", job_data, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
  
  logger.log_function_footer()
  return json_result(False, f"Format '{format_param}' not supported. Use: json, html", {})

# ----------------------------------------- END: G(jh) - Get single --------------------------------------------------------


# ----------------------------------------- START: Monitor endpoint --------------------------------------------------------

@router.get(f"/{router_name}/monitor")
async def jobs_monitor(request: Request):
  """
  Monitor a job's output.
  
  Parameters:
  - job_id: ID of the job to monitor (required)
  - format: Response format - json (default), html, stream
  
  Examples:
  {router_prefix}/{router_name}/monitor?job_id=jb_42
  {router_prefix}/{router_name}/monitor?job_id=jb_42&format=html
  {router_prefix}/{router_name}/monitor?job_id=jb_42&format=stream
  
  Response (json - includes job metadata and last log line):
  {{"ok": true, "error": "", "data": {{"job_id": "jb_42", "state": "running", ..., "log": "[ 15 / 20 ] Processing..."}}}}
  """
  logger = MiddlewareLogger.create()
  logger.log_function_header("jobs_monitor")
  
  if len(request.query_params) == 0:
    logger.log_function_footer()
    doc = textwrap.dedent(jobs_monitor.__doc__).replace("{router_prefix}", router_prefix).replace("{router_name}", router_name)
    return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")
  
  request_params = dict(request.query_params)
  job_id = request_params.get("job_id", None)
  format_param = request_params.get("format", "json")
  
  if not job_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'job_id' parameter.", {})
  
  job = find_job_by_id(get_persistent_storage_path(), job_id)
  if job is None:
    logger.log_function_footer()
    if format_param == "html": return html_result("Not Found", {"error": f"Job '{job_id}' does not exist."}, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
    return JSONResponse({"ok": False, "error": f"Job '{job_id}' does not exist.", "data": {}}, status_code=404)
  
  log_content = read_job_log(get_persistent_storage_path(), job_id)
  
  if format_param == "stream":
    logger.log_function_footer()
    async def stream_log():
      # Yield existing content
      last_len = 0
      if log_content:
        yield log_content
        last_len = len(log_content)
      
      # For running/paused jobs, poll for new content
      while True:
        current_job = find_job_by_id(get_persistent_storage_path(), job_id)
        if current_job is None or current_job.state in ["completed", "cancelled"]:
          # Job finished - yield any remaining content and exit
          final_content = read_job_log(get_persistent_storage_path(), job_id) or ""
          if len(final_content) > last_len:
            yield final_content[last_len:]
          break
        
        # Check for new content
        current_content = read_job_log(get_persistent_storage_path(), job_id) or ""
        if len(current_content) > last_len:
          yield current_content[last_len:]
          last_len = len(current_content)
        
        await asyncio.sleep(0.5)
    
    return StreamingResponse(stream_log(), media_type="text/event-stream")
  
  if format_param == "json":
    job_data = _job_to_dict(job)
    last_log = _extract_last_log_line(log_content) if log_content else ""
    job_data["log"] = last_log
    logger.log_function_footer()
    return json_result(True, "", job_data)
  
  if format_param == "html":
    job_data = _job_to_dict(job)
    last_log = _extract_last_log_line(log_content) if log_content else ""
    job_data["log"] = last_log
    logger.log_function_footer()
    return html_result(f"Monitor: {job_id}", job_data, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
  
  logger.log_function_footer()
  return json_result(False, f"Format '{format_param}' not supported. Use: json, html, stream", {})

# ----------------------------------------- END: Monitor endpoint ----------------------------------------------------------


# ----------------------------------------- START: Control endpoint --------------------------------------------------------

@router.get(f"/{router_name}/control")
async def jobs_control(request: Request):
  """
  Control a running or paused job.
  
  Parameters:
  - job_id: ID of the job (required)
  - action: Control action - pause, resume, cancel (required)
  - force: Force cancel stalled job (optional, only for action=cancel)
  
  Examples:
  {router_prefix}/{router_name}/control?job_id=jb_42&action=pause
  {router_prefix}/{router_name}/control?job_id=jb_42&action=resume
  {router_prefix}/{router_name}/control?job_id=jb_42&action=cancel
  {router_prefix}/{router_name}/control?job_id=jb_42&action=cancel&force=true
  
  Response:
  {{"ok": true, "error": "", "data": {{"job_id": "jb_42", "action": "pause", "message": "Pause requested for job 'jb_42'."}}}}
  """
  logger = MiddlewareLogger.create()
  logger.log_function_header("jobs_control")
  
  if len(request.query_params) == 0:
    logger.log_function_footer()
    doc = textwrap.dedent(jobs_control.__doc__).replace("{router_prefix}", router_prefix).replace("{router_name}", router_name)
    return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")
  
  request_params = dict(request.query_params)
  job_id = request_params.get("job_id", None)
  action = request_params.get("action", None)
  force = request_params.get("force", "false").lower() == "true"
  
  if not job_id:
    logger.log_function_footer()
    return json_result(False, "Param 'job_id' is missing.", {"action": action})
  
  if not action:
    logger.log_function_footer()
    return json_result(False, "Param 'action' is missing.", {"job_id": job_id})
  
  if action not in ["pause", "resume", "cancel"]:
    logger.log_function_footer()
    return json_result(False, f"Invalid value '{action}' for 'action' param.", {"job_id": job_id, "action": action})
  
  job = find_job_by_id(get_persistent_storage_path(), job_id)
  if job is None:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": f"Job '{job_id}' does not exist.", "data": {"job_id": job_id, "action": action}}, status_code=404)
  
  if job.state == "completed":
    logger.log_function_footer()
    return json_result(False, f"Job '{job_id}' is already completed.", {"job_id": job_id, "action": action})
  
  if job.state == "cancelled":
    logger.log_function_footer()
    return json_result(False, f"Job '{job_id}' is already cancelled.", {"job_id": job_id, "action": action})
  
  if action == "pause" and job.state != "running":
    logger.log_function_footer()
    return json_result(False, f"Cannot pause {job.state} job '{job_id}'.", {"job_id": job_id, "action": action})
  
  if action == "resume" and job.state != "paused":
    logger.log_function_footer()
    return json_result(False, f"Cannot resume {job.state} job '{job_id}'.", {"job_id": job_id, "action": action})
  
  if action == "cancel" and job.state not in ["running", "paused"]:
    logger.log_function_footer()
    return json_result(False, f"Cannot cancel {job.state} job '{job_id}'.", {"job_id": job_id, "action": action})
  
  # Force cancel: directly rename .running/.paused -> .cancelled (for stalled jobs)
  if action == "cancel" and force and job.state in ["running", "paused"]:
    success = force_cancel_job(get_persistent_storage_path(), job_id)
    if not success:
      logger.log_function_footer()
      return json_result(False, f"Failed to force cancel job '{job_id}'.", {"job_id": job_id, "action": action, "force": True})
    logger.log_function_footer()
    return json_result(True, "", {"job_id": job_id, "action": action, "force": True, "message": f"Job '{job_id}' force cancelled."})
  
  # Normal control: create control file for running job process to pick up
  success = create_control_file(get_persistent_storage_path(), job_id, action)
  if not success:
    logger.log_function_footer()
    return json_result(False, f"Failed to create control file for job '{job_id}'.", {"job_id": job_id, "action": action})
  
  action_label = action.capitalize()
  logger.log_function_footer()
  return json_result(True, "", {"job_id": job_id, "action": action, "message": f"{action_label} requested for job '{job_id}'."})

# ----------------------------------------- END: Control endpoint ----------------------------------------------------------


# ----------------------------------------- START: Results endpoint --------------------------------------------------------

@router.get(f"/{router_name}/results")
async def jobs_results(request: Request):
  """
  Get a completed job's result JSON from end_json event.
  
  Returns only the 'result' object, not the full job metadata.
  
  Parameters:
  - job_id: ID of the job (required)
  - format: Response format - json (default), html
  
  Examples:
  {router_prefix}/{router_name}/results?job_id=jb_42
  {router_prefix}/{router_name}/results?job_id=jb_42&format=html
  
  Example Response (endpoint returns object):
  {"ok": true, "error": "", "data": {...}}

  Example Response (endpoint returns array):
  {"ok": true, "error": "", "data": [ {...}, {...}, ...]
  """
  logger = MiddlewareLogger.create()
  logger.log_function_header("jobs_results")
  
  if len(request.query_params) == 0:
    logger.log_function_footer()
    doc = textwrap.dedent(jobs_results.__doc__).replace("{router_prefix}", router_prefix).replace("{router_name}", router_name)
    return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")
  
  request_params = dict(request.query_params)
  job_id = request_params.get("job_id", None)
  format_param = request_params.get("format", "json")
  
  if not job_id:
    logger.log_function_footer()
    if format_param == "html": return html_result("Error", {"error": "Missing 'job_id' parameter."}, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
    return json_result(False, "Missing 'job_id' parameter.", {})
  
  job = find_job_by_id(get_persistent_storage_path(), job_id)
  if job is None:
    logger.log_function_footer()
    if format_param == "html": return html_result("Not Found", {"error": f"Job '{job_id}' not found."}, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
    return JSONResponse({"ok": False, "error": f"Job '{job_id}' not found.", "data": {}}, status_code=404)
  
  if job.state not in ["completed", "cancelled"]:
    logger.log_function_footer()
    if format_param == "html": return html_result("Results Not Available", {"error": f"Results not available. Job '{job_id}' state is '{job.state}'."}, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
    return json_result(False, f"Results not available. Job '{job_id}' state is '{job.state}'.", {})
  
  result_data = job.result if job.result else {"ok": False, "error": "No result available", "data": {}}
  
  if format_param == "json":
    logger.log_function_footer()
    return json_result(True, "", result_data)
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Result: {job_id}", result_data, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
  
  logger.log_function_footer()
  return json_result(False, f"Format '{format_param}' not supported. Use: json, html", {})

# ----------------------------------------- END: Results endpoint ----------------------------------------------------------


# ----------------------------------------- START: D(j) - Delete -----------------------------------------------------------

@router.get(f"/{router_name}/delete")
async def jobs_delete_docs(request: Request):
  """
  Delete a job file.
  
  Method: DELETE or GET
  
  Parameters:
  - job_id: ID of the job to delete (required)
  - format: Response format - json (default), html
  
  Examples:
  DELETE {router_prefix}/{router_name}/delete?job_id=jb_42
  GET {router_prefix}/{router_name}/delete?job_id=jb_42&format=html
  """
  if len(request.query_params) == 0:
    doc = textwrap.dedent(jobs_delete_docs.__doc__).replace("{router_prefix}", router_prefix).replace("{router_name}", router_name)
    return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")
  return await jobs_delete_impl(request)

@router.delete(f"/{router_name}/delete")
async def jobs_delete(request: Request):
  return await jobs_delete_impl(request)

async def jobs_delete_impl(request: Request):
  logger = MiddlewareLogger.create()
  logger.log_function_header("jobs_delete")
  
  request_params = dict(request.query_params)
  job_id = request_params.get("job_id", None)
  format_param = request_params.get("format", "json")
  
  if not job_id:
    logger.log_function_footer()
    if format_param == "html": return html_result("Error", {"error": "Missing 'job_id' parameter."}, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
    return json_result(False, "Missing 'job_id' parameter.", {})
  
  job = find_job_by_id(get_persistent_storage_path(), job_id)
  if job is None:
    logger.log_function_footer()
    if format_param == "html": return html_result("Not Found", {"error": f"Job '{job_id}' not found."}, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
    return JSONResponse({"ok": False, "error": f"Job '{job_id}' not found.", "data": {}}, status_code=404)
  
  if job.state in ["running", "paused"]:
    logger.log_function_footer()
    if format_param == "html": return html_result("Cannot Delete", {"error": f"Cannot delete active job '{job_id}' (state: {job.state}). Cancel it first."}, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
    return json_result(False, f"Cannot delete active job '{job_id}' (state: {job.state}). Cancel it first.", {"job_id": job_id, "state": job.state})
  
  success = delete_job(get_persistent_storage_path(), job_id)
  if not success:
    logger.log_function_footer()
    if format_param == "html": return html_result("Delete Failed", {"error": f"Failed to delete job '{job_id}'."}, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
    return json_result(False, f"Failed to delete job '{job_id}'.", {"job_id": job_id})
  
  logger.log_function_footer()
  if format_param == "html": return html_result("Job Deleted", {"job_id": job_id, "message": f"Job '{job_id}' deleted successfully."}, f'<a href="{router_prefix}/{router_name}?format=ui">Back to Jobs</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
  return json_result(True, "", {"job_id": job_id})

# ----------------------------------------- END: D(jh) - Delete ------------------------------------------------------------


# ----------------------------------------- START: Selftest helpers --------------------------------------------------------

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

# ----------------------------------------- END: Selftest helpers ----------------------------------------------------------


# ----------------------------------------- START: Selftest endpoint -------------------------------------------------------

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
      "passed": 46,
      "failed": 0,
      "passed_tests": ["Test 1 description", ...],
      "failed_tests": []
    }
  }
  """
  request_params = dict(request.query_params)
  
  if len(request_params) == 0:
    doc = textwrap.dedent(jobs_selftest.__doc__).replace("{router_prefix}", router_prefix).replace("{router_name}", router_name)
    return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")
  
  format_param = request_params.get("format", "")
  if format_param != "stream":
    return json_result(False, "Selftest only supports format=stream", {})
  
  base_url = str(request.base_url).rstrip("/")
  
  writer = StreamingJobWriter(
    persistent_storage_path=get_persistent_storage_path(),
    router_name=router_name,
    action="selftest",
    object_id="main",
    source_url=str(request.url),
    router_prefix=router_prefix
  )
  stream_logger = MiddlewareLogger.create(stream_job_writer=writer)
  stream_logger.log_function_header("jobs_selftest")
  
  test_job_ids = []
  background_tasks = []
  
  async def run_selftest():
    ok_count = 0
    fail_count = 0
    test_num = 0
    passed_tests = []
    failed_tests = []
    
    completed_job_id = None
    pause_resume_job_id = None
    cancel_job_id = None
    running_for_delete_id = None
    
    def log(msg: str):
      return stream_logger.log_function_output(msg)
    
    def next_test(description: str):
      nonlocal test_num
      test_num += 1
      return log(f"[Test {test_num}] {description}")
    
    def check(condition: bool, ok_msg: str, fail_msg: str):
      nonlocal ok_count, fail_count
      if condition:
        ok_count += 1
        passed_tests.append(ok_msg)
        return log(f"  OK: {ok_msg}")
      else:
        fail_count += 1
        failed_tests.append(fail_msg)
        return log(f"  FAIL: {fail_msg}")
    
    def verify_job_file_extension(job_id: str, expected_ext: str) -> bool:
      filepath = find_job_file(get_persistent_storage_path(), job_id)
      if not filepath: return False
      return filepath.endswith(f".{expected_ext}")
    
    async def wait_for_extension(job_id: str, expected_ext: str, max_wait: float = 3.0) -> bool:
      for _ in range(int(max_wait / 0.2)):
        if verify_job_file_extension(job_id, expected_ext): return True
        await asyncio.sleep(0.2)
      return False
    
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
      import json as json_module
      for e in events:
        if e["event"] == "state_json":
          try:
            data = json_module.loads(e["data"])
            if data.get("state") == expected_state: return True
          except: pass
      return False
    
    try:
      yield writer.emit_start()
      
      async with httpx.AsyncClient(timeout=30.0) as client:
        get_url = f"{base_url}{router_prefix}/{router_name}/get"
        monitor_url = f"{base_url}{router_prefix}/{router_name}/monitor"
        control_url = f"{base_url}{router_prefix}/{router_name}/control"
        results_url = f"{base_url}{router_prefix}/{router_name}/results"
        delete_url = f"{base_url}{router_prefix}/{router_name}/delete"
        list_url = f"{base_url}{router_prefix}/{router_name}?format=json"
        
        # ===== CATEGORY 1: ERROR CASES (10 tests) =====
        sse = next_test("Error cases - GET /get without job_id")
        if sse: yield sse
        r = await client.get(f"{get_url}?format=json")
        sse = check(r.json().get("ok") == False, "GET /get without job_id returns error", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        sse = next_test("Error cases - GET /get non-existent")
        if sse: yield sse
        r = await client.get(f"{get_url}?job_id=nonexistent_jb_999&format=json")
        sse = check(r.status_code == 404, "GET /get non-existent returns 404", f"Expected 404, got: {r.status_code}")
        if sse: yield sse
        
        sse = next_test("Error cases - GET /monitor without job_id")
        if sse: yield sse
        r = await client.get(f"{monitor_url}?format=json")
        sse = check(r.json().get("ok") == False, "GET /monitor without job_id returns error", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        sse = next_test("Error cases - GET /monitor non-existent")
        if sse: yield sse
        r = await client.get(f"{monitor_url}?job_id=nonexistent_jb_999&format=json")
        sse = check(r.status_code == 404, "GET /monitor non-existent returns 404", f"Expected 404, got: {r.status_code}")
        if sse: yield sse
        
        sse = next_test("Error cases - GET /control without job_id")
        if sse: yield sse
        r = await client.get(f"{control_url}?action=pause")
        sse = check(r.json().get("ok") == False, "GET /control without job_id returns error", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        sse = next_test("Error cases - GET /control without action")
        if sse: yield sse
        r = await client.get(f"{control_url}?job_id=jb_1")
        sse = check(r.json().get("ok") == False, "GET /control without action returns error", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        sse = next_test("Error cases - GET /control invalid action")
        if sse: yield sse
        r = await client.get(f"{control_url}?job_id=jb_1&action=invalid")
        sse = check(r.json().get("ok") == False, "GET /control invalid action returns error", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        sse = next_test("Error cases - GET /control non-existent job")
        if sse: yield sse
        r = await client.get(f"{control_url}?job_id=nonexistent_jb_999&action=pause")
        sse = check(r.status_code == 404, "GET /control non-existent returns 404", f"Expected 404, got: {r.status_code}")
        if sse: yield sse
        
        sse = next_test("Error cases - GET /results without job_id")
        if sse: yield sse
        r = await client.get(f"{results_url}?format=json")
        sse = check(r.json().get("ok") == False, "GET /results without job_id returns error", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        sse = next_test("Error cases - DELETE /delete without job_id")
        if sse: yield sse
        r = await client.delete(delete_url)
        sse = check(r.json().get("ok") == False, "DELETE without job_id returns error", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        # ===== CATEGORY 2: JOB CREATION AND BASIC GET (5 tests) =====
        sse = next_test("Create test job (Job 1)")
        if sse: yield sse
        completed_job_id = await _run_test_job_to_completion(delay_seconds=0.05, item_count=3)
        test_job_ids.append(completed_job_id)
        sse = check(completed_job_id is not None, f"Job created with ID '{completed_job_id}'", "Failed to create job")
        if sse: yield sse
        
        sse = next_test("Wait for job completion")
        if sse: yield sse
        ext_ok = await wait_for_extension(completed_job_id, "completed", max_wait=5.0)
        sse = check(ext_ok, "Job file has .completed extension", "Job file not .completed")
        if sse: yield sse
        
        sse = next_test("GET /get for completed job")
        if sse: yield sse
        r = await client.get(f"{get_url}?job_id={completed_job_id}&format=json")
        result = r.json()
        sse = check(result.get("ok") == True and result.get("data", {}).get("state") == "completed", "GET /get returns completed state", f"Got: {result}")
        if sse: yield sse
        
        sse = next_test("GET / - job in list")
        if sse: yield sse
        r = await client.get(list_url)
        jobs_list = r.json().get("data", [])
        job_ids = [j.get("job_id") for j in jobs_list]
        sse = check(completed_job_id in job_ids, f"Job found in list ({len(jobs_list)} total)", "Job NOT found in list")
        if sse: yield sse
        
        sse = next_test("GET /results for completed job")
        if sse: yield sse
        r = await client.get(f"{results_url}?job_id={completed_job_id}&format=json")
        result = r.json()
        sse = check(result.get("ok") == True and result.get("data") is not None, "GET /results returns data", f"Got: {result}")
        if sse: yield sse
        
        # ===== CATEGORY 3: MONITOR ENDPOINT (4 tests) =====
        sse = next_test("GET /monitor format=json")
        if sse: yield sse
        r = await client.get(f"{monitor_url}?job_id={completed_job_id}&format=json")
        result = r.json()
        sse = check(result.get("ok") == True and "log" in result.get("data", {}), "GET /monitor json includes log field", f"Got: {result}")
        if sse: yield sse
        
        sse = next_test("GET /monitor format=html")
        if sse: yield sse
        r = await client.get(f"{monitor_url}?job_id={completed_job_id}&format=html")
        sse = check(r.status_code == 200 and "text/html" in r.headers.get("content-type", ""), "GET /monitor html returns HTML", f"Got status {r.status_code}")
        if sse: yield sse
        
        sse = next_test("GET /monitor format=stream")
        if sse: yield sse
        r = await client.get(f"{monitor_url}?job_id={completed_job_id}&format=stream")
        sse = check(r.status_code == 200, "GET /monitor stream returns 200", f"Got status {r.status_code}")
        if sse: yield sse
        
        sse = next_test("Verify SSE events in job file")
        if sse: yield sse
        log_content = read_job_log(get_persistent_storage_path(), completed_job_id)
        events = parse_sse_events(log_content)
        event_types = [e["event"] for e in events]
        has_start = "start_json" in event_types
        has_log = "log" in event_types
        has_end = "end_json" in event_types
        sse = check(has_start and has_log and has_end, "SSE has start_json, log, end_json events", f"Events: {event_types}")
        if sse: yield sse
        
        # ===== CATEGORY 4: PAUSE/RESUME + ERROR CASES (10 tests) =====
        sse = next_test("Create slow job (Job 2) for pause/resume")
        if sse: yield sse
        pause_resume_job_id, task2 = await _run_slow_test_job_in_background(delay_seconds=1.0, item_count=60)
        test_job_ids.append(pause_resume_job_id)
        background_tasks.append(task2)
        sse = check(pause_resume_job_id is not None, f"Slow job created with ID '{pause_resume_job_id}'", "Failed to create slow job")
        if sse: yield sse
        
        sse = next_test("Resume running job (should fail)")
        if sse: yield sse
        r = await client.get(f"{control_url}?job_id={pause_resume_job_id}&action=resume")
        sse = check(r.json().get("ok") == False, "Resume running job fails", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        sse = next_test("Pause running job")
        if sse: yield sse
        r = await client.get(f"{control_url}?job_id={pause_resume_job_id}&action=pause")
        sse = check(r.json().get("ok") == True, "Pause running job succeeds", f"Got: {r.json()}")
        if sse: yield sse
        
        sse = next_test("Verify .paused extension")
        if sse: yield sse
        ext_ok = await wait_for_extension(pause_resume_job_id, "paused", max_wait=3.0)
        sse = check(ext_ok, "Job file has .paused extension", "Job file not .paused")
        if sse: yield sse
        
        sse = next_test("GET /get shows paused state")
        if sse: yield sse
        r = await client.get(f"{get_url}?job_id={pause_resume_job_id}&format=json")
        state = r.json().get("data", {}).get("state")
        sse = check(state == "paused", f"Job state is 'paused'", f"Got state: {state}")
        if sse: yield sse
        
        sse = next_test("SSE contains state_json paused")
        if sse: yield sse
        log_content = read_job_log(get_persistent_storage_path(), pause_resume_job_id)
        events = parse_sse_events(log_content)
        sse = check(has_state_event(events, "paused"), "SSE has state_json paused event", "No paused state event")
        if sse: yield sse
        
        sse = next_test("Pause paused job (should fail)")
        if sse: yield sse
        r = await client.get(f"{control_url}?job_id={pause_resume_job_id}&action=pause")
        sse = check(r.json().get("ok") == False, "Pause paused job fails", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        sse = next_test("Resume paused job")
        if sse: yield sse
        r = await client.get(f"{control_url}?job_id={pause_resume_job_id}&action=resume")
        sse = check(r.json().get("ok") == True, "Resume paused job succeeds", f"Got: {r.json()}")
        if sse: yield sse
        
        sse = next_test("Verify .running extension")
        if sse: yield sse
        ext_ok = await wait_for_extension(pause_resume_job_id, "running", max_wait=3.0)
        sse = check(ext_ok, "Job file has .running extension", "Job file not .running")
        if sse: yield sse
        
        sse = next_test("SSE contains state_json running")
        if sse: yield sse
        log_content = read_job_log(get_persistent_storage_path(), pause_resume_job_id)
        events = parse_sse_events(log_content)
        sse = check(has_state_event(events, "running"), "SSE has state_json running event", "No running state event")
        if sse: yield sse
        
        # ===== CATEGORY 5: CANCEL (5 tests) =====
        sse = next_test("Create slow job (Job 3) for cancel")
        if sse: yield sse
        cancel_job_id, task3 = await _run_slow_test_job_in_background(delay_seconds=1.0, item_count=60)
        test_job_ids.append(cancel_job_id)
        background_tasks.append(task3)
        sse = check(cancel_job_id is not None, f"Slow job created with ID '{cancel_job_id}'", "Failed to create slow job")
        if sse: yield sse
        
        sse = next_test("Cancel running job")
        if sse: yield sse
        r = await client.get(f"{control_url}?job_id={cancel_job_id}&action=cancel")
        sse = check(r.json().get("ok") == True, "Cancel running job succeeds", f"Got: {r.json()}")
        if sse: yield sse
        
        sse = next_test("Wait for cancel processing")
        if sse: yield sse
        await asyncio.sleep(1.5)
        sse = check(True, "Waited for cancel processing", "")
        if sse: yield sse
        
        sse = next_test("Verify .cancelled extension")
        if sse: yield sse
        ext_ok = await wait_for_extension(cancel_job_id, "cancelled", max_wait=3.0)
        sse = check(ext_ok, "Job file has .cancelled extension", "Job file not .cancelled")
        if sse: yield sse
        
        sse = next_test("SSE contains state_json cancelled")
        if sse: yield sse
        log_content = read_job_log(get_persistent_storage_path(), cancel_job_id)
        events = parse_sse_events(log_content)
        sse = check(has_state_event(events, "cancelled"), "SSE has state_json cancelled event", "No cancelled state event")
        if sse: yield sse
        
        # ===== CATEGORY 6: CONTROL ERROR CASES (4 tests) =====
        sse = next_test("Pause completed job (should fail)")
        if sse: yield sse
        r = await client.get(f"{control_url}?job_id={completed_job_id}&action=pause")
        sse = check(r.json().get("ok") == False, "Pause completed job fails", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        sse = next_test("Resume cancelled job (should fail)")
        if sse: yield sse
        r = await client.get(f"{control_url}?job_id={cancel_job_id}&action=resume")
        sse = check(r.json().get("ok") == False, "Resume cancelled job fails", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        # Cancel Job 2's background task first (releases file handle), then force cancel
        sse = log("Cancelling Job 2 background task for force cancel test...")
        if sse: yield sse
        if task2 and not task2.done():
          task2.cancel()
          try: await task2
          except asyncio.CancelledError: pass
        
        sse = next_test("Force cancel job (Job 2)")
        if sse: yield sse
        force_ok = force_cancel_job(get_persistent_storage_path(), pause_resume_job_id)
        sse = check(force_ok, "Force cancel job succeeds", "Force cancel failed")
        if sse: yield sse
        
        sse = next_test("GET /get after force cancel")
        if sse: yield sse
        r = await client.get(f"{get_url}?job_id={pause_resume_job_id}&format=json")
        state = r.json().get("data", {}).get("state")
        sse = check(state == "cancelled", f"Job state is 'cancelled'", f"Got state: {state}")
        if sse: yield sse
        
        # ===== CATEGORY 7: DELETE TESTS (8 tests) =====
        sse = next_test("Create slow job (Job 4) for delete test")
        if sse: yield sse
        running_for_delete_id, task4 = await _run_slow_test_job_in_background(delay_seconds=1.0, item_count=60)
        test_job_ids.append(running_for_delete_id)
        background_tasks.append(task4)
        sse = check(running_for_delete_id is not None, f"Slow job created with ID '{running_for_delete_id}'", "Failed to create slow job")
        if sse: yield sse
        
        sse = next_test("DELETE running job (should fail)")
        if sse: yield sse
        r = await client.delete(f"{delete_url}?job_id={running_for_delete_id}")
        sse = check(r.json().get("ok") == False, "DELETE running job fails", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        sse = next_test("DELETE completed job (Job 1)")
        if sse: yield sse
        r = await client.delete(f"{delete_url}?job_id={completed_job_id}")
        sse = check(r.json().get("ok") == True, "DELETE completed job succeeds", f"Got: {r.json()}")
        if sse: yield sse
        
        sse = next_test("GET /get deleted job returns 404")
        if sse: yield sse
        r = await client.get(f"{get_url}?job_id={completed_job_id}&format=json")
        sse = check(r.status_code == 404, "GET deleted job returns 404", f"Got status: {r.status_code}")
        if sse: yield sse
        
        sse = next_test("DELETE cancelled job (Job 3)")
        if sse: yield sse
        r = await client.delete(f"{delete_url}?job_id={cancel_job_id}")
        sse = check(r.json().get("ok") == True, "DELETE cancelled job succeeds", f"Got: {r.json()}")
        if sse: yield sse
        
        sse = next_test("GET / excludes deleted jobs")
        if sse: yield sse
        r = await client.get(list_url)
        jobs_list = r.json().get("data", [])
        job_ids = [j.get("job_id") for j in jobs_list]
        neither_in_list = completed_job_id not in job_ids and cancel_job_id not in job_ids
        sse = check(neither_in_list, "Deleted jobs not in list", f"Jobs still in list: {job_ids}")
        if sse: yield sse
        
        sse = next_test("DELETE force_cancelled job (Job 2)")
        if sse: yield sse
        r = await client.delete(f"{delete_url}?job_id={pause_resume_job_id}")
        sse = check(r.json().get("ok") == True, "DELETE force_cancelled job succeeds", f"Got: {r.json()}")
        if sse: yield sse
        
        sse = next_test("DELETE same job again returns 404")
        if sse: yield sse
        r = await client.delete(f"{delete_url}?job_id={pause_resume_job_id}")
        sse = check(r.status_code == 404, "DELETE same job returns 404", f"Got status: {r.status_code}")
        if sse: yield sse
      
      # Summary
      sse = log("")
      if sse: yield sse
      sse = log("===== SELFTEST COMPLETE =====")
      if sse: yield sse
      sse = log(f"OK: {ok_count}, FAIL: {fail_count}")
      if sse: yield sse
      
      stream_logger.log_function_footer()
      
      ok = (fail_count == 0)
      yield writer.emit_end(ok=ok, error="" if ok else f"{fail_count} test(s) failed.", data={"passed": ok_count, "failed": fail_count, "passed_tests": passed_tests, "failed_tests": failed_tests})
      
    except Exception as e:
      sse = log(f"ERROR: Self-test failed -> {type(e).__name__}: {str(e)}")
      if sse: yield sse
      stream_logger.log_function_footer()
      yield writer.emit_end(ok=False, error=str(e), data={"passed": ok_count, "failed": fail_count})
    finally:
      # Cleanup: Cancel background tasks
      for task in background_tasks:
        if not task.done():
          task.cancel()
          try: await task
          except asyncio.CancelledError: pass
      
      # Cleanup: Force cancel and delete remaining test jobs
      for job_id in test_job_ids:
        try:
          job = find_job_by_id(get_persistent_storage_path(), job_id)
          if job and job.state in ["running", "paused"]:
            force_cancel_job(get_persistent_storage_path(), job_id)
          delete_job(get_persistent_storage_path(), job_id)
        except: pass
      
      writer.finalize()
  
  return StreamingResponse(run_selftest(), media_type="text/event-stream")

# ----------------------------------------- END: Selftest endpoint ---------------------------------------------------------
