# Jobs Router V2 - Job monitoring and control UI
# Spec: L(jhu)G(jh)D(j): /v2/jobs
# Implements _V2_SPEC_JOBS_UI.md specification

import textwrap
from dataclasses import asdict
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, StreamingResponse

from routers_v2.common_ui_functions_v2 import generate_router_docs_page, generate_endpoint_docs, json_result, html_result, generate_html_head, generate_toast_container, generate_modal_structure, generate_console_panel, generate_core_js, generate_console_js, generate_form_js
from routers_v2.common_logging_functions_v2 import MiddlewareLogger
from routers_v2.common_job_functions_v2 import list_jobs, find_job_by_id, read_job_log, read_job_result, create_control_file, delete_job, JobMetadata

router = APIRouter()
config = None
router_prefix = None
router_name = "jobs"
main_page_nav_html = '<a href="/">Back to Main Page</a>'
example_item_json = """
{
  "job_id": "jb_42",
  "state": "completed",
  "source_url": "/v2/crawler/crawl?domain_id=DOMAIN01&format=stream",
  "monitor_url": "/v2/jobs/monitor?job_id=jb_42&format=stream",
  "started_utc": "2025-01-15T14:20:30.000000Z",
  "finished_utc": "2025-01-15T14:25:45.000000Z",
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
    tbody.innerHTML = '<tr><td colspan="9" class="empty-state">No jobs found</td></tr>';
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
  
  const actions = renderJobActions(job);
  const rowId = escapeHtml(job.job_id.replace(/[^a-zA-Z0-9_]/g, '_'));
  
  return '<tr id="job-' + rowId + '">' +
    '<td><input type="checkbox" class="item-checkbox" data-item-id="' + escapeHtml(job.job_id) + '" onchange="updateSelectedCount()"></td>' +
    '<td>' + escapeHtml(job.job_id) + '</td>' +
    '<td>' + escapeHtml(parsed.router) + '</td>' +
    '<td>' + escapeHtml(parsed.endpoint) + '</td>' +
    '<td>' + objectsHtml + '</td>' +
    '<td>' + escapeHtml(job.state) + '</td>' +
    '<td>' + escapeHtml(started) + '</td>' +
    '<td>' + escapeHtml(finished) + '</td>' +
    '<td class="actions">' + actions + '</td>' +
    '</tr>';
}}

function renderJobActions(job) {{
  const jobId = job.job_id;
  const state = job.state;
  let actions = [];
  
  if (state === 'completed' || state === 'cancelled') {{
    actions.push('<button class="btn-small" onclick="showJobResult(\\'' + jobId + '\\')">Result</button>');
  }}
  
  actions.push('<button class="btn-small" onclick="monitorJob(\\'' + jobId + '\\')">Monitor</button>');
  
  if (state === 'running') {{
    actions.push('<button class="btn-small" data-url="{router_prefix}/{router_name}/control?job_id=' + jobId + '&action=pause" onclick="callJobControl(this, \\'' + jobId + '\\')">Pause</button>');
    actions.push('<button class="btn-small btn-delete" onclick="if(confirm(\\'Cancel job ' + jobId + '?\\')) callJobControl(this, \\'' + jobId + '\\')" data-url="{router_prefix}/{router_name}/control?job_id=' + jobId + '&action=cancel">Cancel</button>');
  }} else if (state === 'paused') {{
    actions.push('<button class="btn-small" data-url="{router_prefix}/{router_name}/control?job_id=' + jobId + '&action=resume" onclick="callJobControl(this, \\'' + jobId + '\\')">Resume</button>');
    actions.push('<button class="btn-small btn-delete" onclick="if(confirm(\\'Cancel job ' + jobId + '?\\')) callJobControl(this, \\'' + jobId + '\\')" data-url="{router_prefix}/{router_name}/control?job_id=' + jobId + '&action=cancel">Cancel</button>');
  }}
  
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
// TIMESTAMP FORMATTING
// ============================================
function formatTimestamp(ts) {{
  if (!ts) return '-';
  try {{
    const date = new Date(ts);
    const pad = (n) => String(n).padStart(2, '0');
    return date.getFullYear() + '-' + pad(date.getMonth() + 1) + '-' + pad(date.getDate()) + ' ' + pad(date.getHours()) + ':' + pad(date.getMinutes()) + ':' + pad(date.getSeconds());
  }} catch (e) {{
    return '-';
  }}
}}

// ============================================
// JOB MONITORING
// ============================================
function monitorJob(jobId) {{
  const url = '{router_prefix}/{router_name}/monitor?job_id=' + jobId + '&format=stream';
  currentJobId = jobId;
  connectStream(url, {{ reloadOnFinish: false, showResult: 'none', clearConsole: true }});
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
  body.innerHTML = '<h3>Control Action Failed</h3>' +
    '<p><strong>Action:</strong> ' + escapeHtml(response.data?.action || 'unknown') + '</p>' +
    '<p><strong>Job:</strong> ' + escapeHtml(response.data?.job_id || 'unknown') + '</p>' +
    '<p style="color: #dc3545;"><strong>Error:</strong> ' + escapeHtml(response.error) + '</p>' +
    '<div class="form-actions"><button type="button" class="btn-primary" onclick="closeModal()">OK</button></div>';
  openModal();
}}

// ============================================
// SELECTION & BULK DELETE
// ============================================
const ROW_ID_PREFIX = 'job';
const DELETE_ENDPOINT = '{router_prefix}/{router_name}/delete?job_id={{itemId}}';

function updateSelectedCount() {{
  const selected = document.querySelectorAll('.item-checkbox:checked');
  const total = document.querySelectorAll('.item-checkbox');
  const btn = document.getElementById('btn-delete-selected');
  const countEl = document.getElementById('selected-count');
  if (countEl) countEl.textContent = selected.length;
  if (btn) btn.disabled = selected.length === 0;
  const selectAll = document.getElementById('select-all');
  if (selectAll) selectAll.checked = total.length > 0 && selected.length === total.length;
}}

function toggleSelectAll() {{
  const selectAll = document.getElementById('select-all');
  const checkboxes = document.querySelectorAll('.item-checkbox');
  checkboxes.forEach(cb => cb.checked = selectAll.checked);
  updateSelectedCount();
}}

function getSelectedJobIds() {{
  const selected = document.querySelectorAll('.item-checkbox:checked');
  return Array.from(selected).map(cb => cb.dataset.itemId);
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
        showToast('Job Deleted', jobId, 'success');
        deleted++;
      }} else {{
        showToast('Delete Failed', jobId + ': ' + result.error, 'error');
        failed++;
      }}
    }} catch (e) {{
      failed++;
    }}
  }}
  
  renderAllJobs();
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
      {"path": "/delete", "desc": "Delete job file (DELETE/GET)", "formats": []}
    ]
    return HTMLResponse(generate_router_docs_page(
      title="Jobs Router",
      description="Monitor and control long-running streaming jobs.",
      router_prefix=f"{router_prefix}/{router_name}",
      endpoints=endpoints,
      navigation_html=main_page_nav_html
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
    return html_result("Jobs", jobs_data, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html}')
  
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
  router_js = get_router_specific_js()
  
  return f"""<!doctype html><html lang="en">
{head}
<body class="has-console">
  {toast_container}
  {modal}
  
  <div class="container">
    <div class="page-header">
      <h1>Jobs (<span id="item-count">0</span>)</h1>
      <button onclick="refreshJobs()" class="btn-small">Reload</button>
    </div>
    
    <p>{main_page_nav_html}</p>
    
    <div class="toolbar">
      <button id="btn-delete-selected" class="btn-primary btn-delete" onclick="bulkDelete()" disabled>Delete (<span id="selected-count">0</span>)</button>
    </div>
    
    <table>
      <thead>
        <tr>
          <th><input type="checkbox" id="select-all" onchange="toggleSelectAll()"></th>
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
      <tbody id="items-tbody">
        <tr><td colspan="9" class="empty-state">Loading...</td></tr>
      </tbody>
    </table>
  </div>
  
  {console}
  
  <script>
{core_js}
{console_js}
{form_js}
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
    if format_param == "html": return html_result("Error", {"error": "Missing 'job_id' parameter."}, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html}')
    return json_result(False, "Missing 'job_id' parameter.", {})
  
  job = find_job_by_id(get_persistent_storage_path(), job_id)
  if job is None:
    logger.log_function_footer()
    if format_param == "html": return html_result("Not Found", {"error": f"Job '{job_id}' not found."}, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html}')
    return JSONResponse({"ok": False, "error": f"Job '{job_id}' not found.", "data": {}}, status_code=404)
  
  job_data = _job_to_dict(job)
  
  if format_param == "json":
    logger.log_function_footer()
    return json_result(True, "", job_data)
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Job: {job_id}", job_data, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html}')
  
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
  - format: Response format - json, html, stream (default)
  
  Examples:
  {router_prefix}/{router_name}/monitor?job_id=jb_42&format=stream
  {router_prefix}/{router_name}/monitor?job_id=jb_42&format=json
  {router_prefix}/{router_name}/monitor?job_id=jb_42&format=html
  
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
  format_param = request_params.get("format", "stream")
  
  if not job_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'job_id' parameter.", {})
  
  job = find_job_by_id(get_persistent_storage_path(), job_id)
  if job is None:
    logger.log_function_footer()
    if format_param == "html": return html_result("Not Found", {"error": f"Job '{job_id}' does not exist."}, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html}')
    return JSONResponse({"ok": False, "error": f"Job '{job_id}' does not exist.", "data": {}}, status_code=404)
  
  log_content = read_job_log(get_persistent_storage_path(), job_id)
  
  if format_param == "stream":
    logger.log_function_footer()
    async def stream_log():
      yield log_content if log_content else ""
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
    return html_result(f"Monitor: {job_id}", job_data, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html}')
  
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
  
  Examples:
  {router_prefix}/{router_name}/control?job_id=jb_42&action=pause
  {router_prefix}/{router_name}/control?job_id=jb_42&action=resume
  {router_prefix}/{router_name}/control?job_id=jb_42&action=cancel
  
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
    if format_param == "html": return html_result("Error", {"error": "Missing 'job_id' parameter."}, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html}')
    return json_result(False, "Missing 'job_id' parameter.", {})
  
  job = find_job_by_id(get_persistent_storage_path(), job_id)
  if job is None:
    logger.log_function_footer()
    if format_param == "html": return html_result("Not Found", {"error": f"Job '{job_id}' not found."}, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html}')
    return JSONResponse({"ok": False, "error": f"Job '{job_id}' not found.", "data": {}}, status_code=404)
  
  if job.state not in ["completed", "cancelled"]:
    logger.log_function_footer()
    if format_param == "html": return html_result("Results Not Available", {"error": f"Results not available. Job '{job_id}' state is '{job.state}'."}, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html}')
    return json_result(False, f"Results not available. Job '{job_id}' state is '{job.state}'.", {})
  
  result_data = job.result if job.result else {"ok": False, "error": "No result available", "data": {}}
  
  if format_param == "json":
    logger.log_function_footer()
    return json_result(True, "", result_data)
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Result: {job_id}", result_data, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html}')
  
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
  
  Examples:
  DELETE {router_prefix}/{router_name}/delete?job_id=jb_42
  GET {router_prefix}/{router_name}/delete?job_id=jb_42
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
  
  if not job_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'job_id' parameter.", {})
  
  job = find_job_by_id(get_persistent_storage_path(), job_id)
  if job is None:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": f"Job '{job_id}' not found.", "data": {}}, status_code=404)
  
  if job.state in ["running", "paused"]:
    logger.log_function_footer()
    return json_result(False, f"Cannot delete active job '{job_id}' (state: {job.state}). Cancel it first.", {"job_id": job_id, "state": job.state})
  
  success = delete_job(get_persistent_storage_path(), job_id)
  if not success:
    logger.log_function_footer()
    return json_result(False, f"Failed to delete job '{job_id}'.", {"job_id": job_id})
  
  logger.log_function_footer()
  return json_result(True, "", {"job_id": job_id})

# ----------------------------------------- END: D(j) - Delete -------------------------------------------------------------
