# Reports Router V2 - Report archive management UI
# Spec: _V2_SPEC_REPORTS.md, _V2_SPEC_REPORTS_UI.md
# Endpoints: L(j)G(jh)F(jr)D(z)X(jh): /v2/reports

import asyncio, random, textwrap, uuid
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, FileResponse, Response, StreamingResponse

from routers_v2.common_report_functions_v2 import list_reports, get_report_metadata, get_report_file, delete_report, get_report_archive_path, create_report
from routers_v2.common_report_functions_v2 import set_config as set_report_functions_config
from routers_v2.common_logging_functions_v2 import MiddlewareLogger
from routers_v2.common_ui_functions_v2 import generate_ui_page, generate_router_docs_page, generate_endpoint_docs, json_result, html_result
from routers_v2.common_job_functions_v2 import StreamingJobWriter, ControlAction

router = APIRouter()
config = None
router_prefix = None
router_name = "reports"
main_page_nav_html = '<a href="/">Back to Main Page</a> | <a href="{router_prefix}/domains?format=ui">Domains</a> | <a href="{router_prefix}/crawler?format=ui">Crawler</a> | <a href="{router_prefix}/jobs?format=ui">Jobs</a> | <a href="{router_prefix}/reports?format=ui">Reports</a>'
example_item_json = """
{
  "report_id": "crawls/2024-01-15_14-25-00_TEST01_all_full",
  "title": "TEST01 full crawl",
  "type": "crawl",
  "created_utc": "2024-01-15T14:30:00.000000Z",
  "ok": true,
  "error": "",
  "files": [...]
}
"""

def set_config(app_config, prefix):
  global config, router_prefix
  config = app_config
  router_prefix = prefix
  set_report_functions_config(app_config)

def get_persistent_storage_path() -> str:
  return getattr(config, 'LOCAL_PERSISTENT_STORAGE_PATH', None) or ''


# ----------------------------------------- START: Router-specific JS ----------------------------------------------------

def get_router_specific_js() -> str:
  return f"""
// ============================================
// REPORTS STATE MANAGEMENT
// ============================================
const reportsState = new Map();

// ============================================
// PAGE INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', async () => {{
  await reloadItems();
  initConsoleResize();
}});

// ============================================
// REPORTS LOADING
// ============================================
async function reloadItems() {{
  try {{
    const response = await fetch('{router_prefix}/{router_name}?format=json');
    const result = await response.json();
    if (result.ok) {{
      reportsState.clear();
      result.data.forEach(r => reportsState.set(r.report_id, r));
      renderAllReports();
      updateHeaderCount();
    }} else {{
      showToast('Load Failed', result.error, 'error');
    }}
  }} catch (e) {{
    showToast('Load Failed', e.message, 'error');
  }}
}}

function updateHeaderCount() {{
  const countEl = document.getElementById('item-count');
  if (countEl) countEl.textContent = reportsState.size;
}}

// ============================================
// REPORTS RENDERING
// ============================================
function renderAllReports() {{
  const tbody = document.getElementById('items-tbody');
  if (!tbody) return;
  
  if (reportsState.size === 0) {{
    tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No reports found</td></tr>';
    updateSelectedCount();
    return;
  }}
  
  tbody.innerHTML = '';
  reportsState.forEach(report => {{
    tbody.innerHTML += renderReportRow(report);
  }});
  updateSelectedCount();
}}

function renderReportRow(report) {{
  const rowClass = report.ok === false ? 'row-cancel-or-fail' : '';
  const result = formatResultOkFail(report.ok);
  const created = formatTimestamp(report.created_utc);
  const escapedId = sanitizeId(report.report_id);
  const escapedTitle = escapeHtml(report.title || '').replace(/'/g, "\\\\'");
  const reportId = report.report_id;
  
  return '<tr id="report-' + escapedId + '"' + (rowClass ? ' class="' + rowClass + '"' : '') + '>' +
    '<td><input type="checkbox" class="item-checkbox" data-item-id="' + reportId + '" onchange="updateSelectedCount()"></td>' +
    '<td>' + escapeHtml(report.type || '-') + '</td>' +
    '<td>' + escapeHtml(report.title || '-') + '</td>' +
    '<td>' + created + '</td>' +
    '<td>' + result + '</td>' +
    '<td class="actions">' +
      '<button class="btn-small" onclick="showReportResult(\\'' + reportId + '\\')">Result</button> ' +
      '<button class="btn-small" data-url="{router_prefix}/{router_name}/download?report_id=' + encodeURIComponent(reportId) + '" onclick="downloadReport(this)">Download</button> ' +
      '<button class="btn-small btn-delete" onclick="if(confirm(\\'Delete report ' + escapedTitle + '?\\')) deleteReport(\\'' + reportId + '\\', \\'' + escapedTitle + '\\')">Delete</button>' +
    '</td>' +
  '</tr>';
}}

// ============================================
// REPORT ACTIONS
// ============================================
async function showReportResult(reportId) {{
  try {{
    const response = await fetch(`{router_prefix}/{router_name}/get?report_id=${{encodeURIComponent(reportId)}}&format=json`);
    const result = await response.json();
    if (result.ok) {{
      const data = result.data;
      const status = data.ok === null || data.ok === undefined ? '-' : (data.ok ? 'OK' : 'FAIL');
      const body = document.querySelector('#modal .modal-body');
      body.innerHTML = `
        <div class="modal-header"><h3>Result (${{status}}) - '${{escapeHtml(data.title || reportId)}}'</h3></div>
        <div class="modal-scroll">
          <pre class="result-output">${{escapeHtml(JSON.stringify(data, null, 2))}}</pre>
        </div>
        <div class="modal-footer"><button type="button" class="btn-primary" onclick="closeModal()">OK</button></div>
      `;
      openModal();
    }} else {{
      showToast('Error', result.error, 'error');
    }}
  }} catch (e) {{
    showToast('Error', e.message, 'error');
  }}
}}

function downloadReport(btn) {{
  window.location = btn.dataset.url;
}}

async function deleteReport(reportId, title) {{
  try {{
    const response = await fetch(`{router_prefix}/{router_name}/delete?report_id=${{encodeURIComponent(reportId)}}`, {{ method: 'DELETE' }});
    const result = await response.json();
    if (result.ok) {{
      reportsState.delete(reportId);
      renderAllReports();
      updateHeaderCount();
      showToast('Deleted', `Report '${{title}}' deleted.`, 'success');
    }} else {{
      showToast('Error', result.error, 'error');
    }}
  }} catch (e) {{
    showToast('Error', e.message, 'error');
  }}
}}

async function bulkDelete() {{
  const ids = getSelectedReportIds();
  if (ids.length === 0) return;
  
  let successCount = 0;
  for (const id of ids) {{
    try {{
      const response = await fetch(`{router_prefix}/{router_name}/delete?report_id=${{encodeURIComponent(id)}}`, {{ method: 'DELETE' }});
      const result = await response.json();
      if (result.ok) {{
        reportsState.delete(id);
        successCount++;
      }}
    }} catch (e) {{
      // Continue with next
    }}
  }}
  renderAllReports();
  updateHeaderCount();
  const msg = successCount === 1 ? '1 report deleted.' : `${{successCount}} reports deleted.`;
  showToast('Deleted', msg, successCount === ids.length ? 'success' : 'warning');
}}

// ============================================
// SELECTION
// ============================================
function getSelectedReportIds() {{
  return getSelectedIds();
}}

// ============================================
// CREATE DEMO REPORTS FORM
// ============================================
function showCreateDemoReportsForm() {{
  const body = document.querySelector('#modal .modal-body');
  body.innerHTML = `
    <div class="modal-header"><h3>Create Demo Reports</h3></div>
    <div class="modal-scroll">
      <form id="create-demo-reports-form">
        <div class="form-group">
          <label>Number of reports</label>
          <input type="number" name="count" value="5" min="1" max="20">
        </div>
        <div class="form-group">
          <label>Report type</label>
          <select name="report_type">
            <option value="crawl">crawl</option>
            <option value="site_scan">site_scan</option>
          </select>
        </div>
        <div class="form-group">
          <label>Delay per report (ms)</label>
          <input type="number" name="delay_ms" value="300" min="0" max="5000">
        </div>
      </form>
    </div>
    <div class="modal-footer">
      <p class="modal-error"></p>
      <button type="button" class="btn-primary" onclick="submitCreateDemoReportsForm()">Create</button>
      <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
    </div>
  `;
  openModal();
}}

function submitCreateDemoReportsForm() {{
  const form = document.getElementById('create-demo-reports-form');
  const formData = new FormData(form);
  const count = formData.get('count') || '5';
  const reportType = formData.get('report_type') || 'crawl';
  const delayMs = formData.get('delay_ms') || '300';
  
  closeModal();
  showConsole();
  
  const url = `{router_prefix}/{router_name}/create_demo_reports?format=stream&count=${{count}}&report_type=${{reportType}}&delay_ms=${{delayMs}}`;
  connectStream(url, {{ reloadOnFinish: true, showResult: 'toast' }});
}}
"""

# ----------------------------------------- END: Router-specific JS ------------------------------------------------------


# ----------------------------------------- START: UI Page Generation ----------------------------------------------------

def generate_reports_ui_page(reports: list) -> str:
  nav_links = main_page_nav_html.replace("{router_prefix}", router_prefix)
  
  columns = [
    {"field": "type", "header": "Type", "default": "-"},
    {"field": "title", "header": "Title", "default": "-"},
    {"field": "created_utc", "header": "Created", "js_format": "formatTimestamp(item.created_utc)"},
    {"field": "ok", "header": "Result", "js_format": "formatResult(item.ok)"},
    {
      "field": "actions",
      "header": "Actions",
      "buttons": [
        {"text": "Result", "onclick": "showReportResult('{itemId}')", "class": "btn-small"},
        {"text": "Download", "onclick": "downloadReport('{itemId}')", "class": "btn-small"},
        {
          "text": "Delete",
          "data_url": f"{router_prefix}/{router_name}/delete?report_id={{itemId}}",
          "data_method": "DELETE",
          "data_format": "json",
          "confirm_message": "Delete report '{itemId}'?",
          "class": "btn-small btn-delete"
        }
      ]
    }
  ]
  
  toolbar_buttons = [
    {"text": "Create Demo Reports", "onclick": "showCreateDemoReportsForm()", "class": "btn-primary"}
  ]
  
  return generate_ui_page(
    title="Reports",
    router_prefix=router_prefix,
    items=reports,
    columns=columns,
    row_id_field="report_id",
    row_id_prefix="report",
    navigation_html=nav_links,
    toolbar_buttons=toolbar_buttons,
    enable_selection=True,
    enable_bulk_delete=True,
    console_initially_hidden=True,
    list_endpoint=f"{router_prefix}/{router_name}?format=json",
    delete_endpoint=f"{router_prefix}/{router_name}/delete?report_id={{itemId}}",
    jobs_control_endpoint=f"{router_prefix}/jobs/control",
    additional_js=get_router_specific_js()
  )

# ----------------------------------------- END: UI Page Generation ------------------------------------------------------


# ----------------------------------------- START: /reports endpoint (List) ----------------------------------------------

@router.get(f"/{router_name}")
async def list_reports_endpoint(request: Request):
  """Reports Router - Report archive management"""
  logger = MiddlewareLogger.create()
  logger.log_function_header("list_reports_endpoint()")
  request_params = dict(request.query_params)
  
  # DD-E001: Self-documentation on bare GET - return HTML docs page
  if len(request_params) == 0:
    logger.log_function_footer()
    endpoints = [
      {"path": "", "desc": "List all reports", "formats": ["json", "html", "ui"]},
      {"path": "/get", "desc": "Get report metadata", "formats": ["json", "html"]},
      {"path": "/file", "desc": "Get file from archive", "formats": ["raw", "json", "html"]},
      {"path": "/download", "desc": "Download archive as ZIP", "formats": []},
      {"path": "/delete", "desc": "Delete report (DELETE/GET)", "formats": []},
      {"path": "/create_demo_reports", "desc": "Create demo reports", "formats": ["stream"]}
    ]
    return HTMLResponse(generate_router_docs_page(
      title="Reports",
      description=f"Report archive management. Storage: PERSISTENT_STORAGE_PATH/reports/",
      router_prefix=f"{router_prefix}/{router_name}",
      endpoints=endpoints,
      navigation_html=main_page_nav_html
    ))
  
  format_param = request_params.get("format", "json")
  type_filter = request_params.get("type", None)
  reports = list_reports(type_filter=type_filter, logger=logger)
  
  if format_param == "ui":
    logger.log_function_footer()
    return HTMLResponse(generate_reports_ui_page(reports))
  elif format_param == "html":
    logger.log_function_footer()
    return html_result("Reports", reports, main_page_nav_html)
  
  logger.log_function_footer()
  return json_result(True, "", reports)

# ----------------------------------------- END: /reports endpoint (List) ------------------------------------------------


# ----------------------------------------- START: /reports/get endpoint -------------------------------------------------

@router.get(f"/{router_name}/get")
async def get_report_endpoint(request: Request):
  """
  Get report metadata (report.json content).
  
  Parameters:
  - report_id: Report identifier (required)
  - format: Response format (json, html)
  
  Examples:
  /v2/reports/get?report_id=crawls/2024-01-15_14-25-00_TEST01_all_full
  /v2/reports/get?report_id=crawls/2024-01-15_14-25-00_TEST01_all_full&format=html
  """
  logger = MiddlewareLogger.create()
  logger.log_function_header("get_report_endpoint()")
  request_params = dict(request.query_params)
  
  # DD-E001: Self-documentation on bare GET
  if len(request_params) == 0:
    logger.log_function_footer()
    doc = textwrap.dedent(get_report_endpoint.__doc__)
    return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")
  
  format_param = request_params.get("format", "json")
  report_id = request_params.get("report_id", None)
  
  if not report_id:
    logger.log_function_footer()
    if format_param == "html": return html_result("Error", {"error": "Missing 'report_id' parameter."}, main_page_nav_html)
    return json_result(False, "Missing 'report_id' parameter.", {})
  
  metadata = get_report_metadata(report_id, logger=logger)
  if metadata is None:
    logger.log_function_footer()
    if format_param == "html": return html_result("Not Found", {"error": f"Report '{report_id}' not found."}, main_page_nav_html)
    return JSONResponse({"ok": False, "error": f"Report '{report_id}' not found.", "data": {}}, status_code=404)
  
  logger.log_function_footer()
  if format_param == "html": return html_result(f"Report: {metadata.get('title', report_id)}", metadata, main_page_nav_html)
  return json_result(True, "", metadata)

# ----------------------------------------- END: /reports/get endpoint ---------------------------------------------------


# ----------------------------------------- START: /reports/file endpoint ------------------------------------------------

def get_content_type(file_path: str) -> str:
  if file_path.endswith('.json'): return 'application/json'
  if file_path.endswith('.csv'): return 'text/csv'
  if file_path.endswith('.txt'): return 'text/plain'
  if file_path.endswith('.html'): return 'text/html'
  if file_path.endswith('.xml'): return 'application/xml'
  if file_path.endswith('.zip'): return 'application/zip'
  return 'application/octet-stream'

@router.get(f"/{router_name}/file")
async def get_file_endpoint(request: Request):
  """
  Get specific file from report archive.
  
  Parameters:
  - report_id: Report identifier (required)
  - file_path: File path within archive (required)
  - format: Response format (raw, json, html) - default: raw
  
  Examples:
  /v2/reports/file?report_id=crawls/...&file_path=report.json
  /v2/reports/file?report_id=crawls/...&file_path=01_files/source01/sharepoint_map.csv
  """
  logger = MiddlewareLogger.create()
  logger.log_function_header("get_file_endpoint()")
  request_params = dict(request.query_params)
  
  # DD-E001: Self-documentation on bare GET
  if len(request_params) == 0:
    logger.log_function_footer()
    doc = textwrap.dedent(get_file_endpoint.__doc__)
    return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")
  
  format_param = request_params.get("format", "raw")
  report_id = request_params.get("report_id", None)
  file_path = request_params.get("file_path", None)
  
  if not report_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'report_id' parameter.", {})
  
  if not file_path:
    logger.log_function_footer()
    return json_result(False, "Missing 'file_path' parameter.", {})
  
  content = get_report_file(report_id, file_path, logger=logger)
  if content is None:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": f"File '{file_path}' not found in report '{report_id}'.", "data": {}}, status_code=404)
  
  logger.log_function_footer()
  
  if format_param == "raw":
    content_type = get_content_type(file_path)
    return Response(content=content, media_type=content_type)
  elif format_param == "json":
    try:
      text_content = content.decode('utf-8')
      return json_result(True, "", {"file_path": file_path, "content": text_content})
    except UnicodeDecodeError:
      return json_result(False, "File is binary, cannot return as JSON.", {"file_path": file_path})
  else:
    try:
      text_content = content.decode('utf-8')
      return html_result(f"File: {file_path}", {"content": text_content}, main_page_nav_html)
    except UnicodeDecodeError:
      return html_result("Error", {"error": "File is binary, cannot display as HTML."}, main_page_nav_html)

# ----------------------------------------- END: /reports/file endpoint --------------------------------------------------


# ----------------------------------------- START: /reports/download endpoint --------------------------------------------

@router.get(f"/{router_name}/download")
async def download_report_endpoint(request: Request):
  """
  Download report archive as ZIP.
  
  Parameters:
  - report_id: Report identifier (required)
  
  Examples:
  /v2/reports/download?report_id=crawls/2024-01-15_14-25-00_TEST01_all_full
  """
  logger = MiddlewareLogger.create()
  logger.log_function_header("download_report_endpoint()")
  request_params = dict(request.query_params)
  
  # DD-E001: Self-documentation on bare GET
  if len(request_params) == 0:
    logger.log_function_footer()
    doc = textwrap.dedent(download_report_endpoint.__doc__)
    return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")
  
  report_id = request_params.get("report_id", None)
  
  if not report_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'report_id' parameter.", {})
  
  archive_path = get_report_archive_path(report_id)
  if archive_path is None:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": f"Report '{report_id}' not found.", "data": {}}, status_code=404)
  
  # Extract filename for Content-Disposition
  filename = archive_path.name
  
  logger.log_function_footer()
  return FileResponse(path=str(archive_path), filename=filename, media_type='application/zip')

# ----------------------------------------- END: /reports/download endpoint ----------------------------------------------


# ----------------------------------------- START: /reports/delete endpoint ----------------------------------------------

@router.api_route(f"/{router_name}/delete", methods=["GET", "DELETE"])
async def delete_report_endpoint(request: Request):
  """
  Delete report archive. Returns deleted report metadata (DD-E017).
  
  Parameters:
  - report_id: Report identifier (required)
  
  Examples:
  DELETE /v2/reports/delete?report_id=crawls/2024-01-15_14-25-00_TEST01_all_full
  GET /v2/reports/delete?report_id=crawls/2024-01-15_14-25-00_TEST01_all_full
  """
  logger = MiddlewareLogger.create()
  logger.log_function_header("delete_report_endpoint()")
  request_params = dict(request.query_params)
  
  # DD-E001: Self-documentation on bare GET (only for GET method)
  if request.method == "GET" and len(request_params) == 0:
    logger.log_function_footer()
    doc = textwrap.dedent(delete_report_endpoint.__doc__)
    return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")
  
  report_id = request_params.get("report_id", None)
  
  if not report_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'report_id' parameter.", {})
  
  # DD-E017: Delete returns full object
  deleted_metadata = delete_report(report_id, logger=logger)
  if deleted_metadata is None:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": f"Report '{report_id}' not found.", "data": {}}, status_code=404)
  
  logger.log_function_footer()
  return json_result(True, "", deleted_metadata)

# ----------------------------------------- END: /reports/delete endpoint ------------------------------------------------


# ----------------------------------------- START: /reports/create_demo_reports endpoint ---------------------------------

@router.get(f"/{router_name}/create_demo_reports")
async def create_demo_reports_endpoint(request: Request):
  """
  Create demo reports for testing purposes.
  
  Only supports format=stream.
  
  Parameters:
  - count: Number of reports to create (default: 5, max: 20)
  - report_type: Type of report - crawl or site_scan (default: crawl)
  - delay_ms: Delay per report in milliseconds (default: 300)
  
  Examples:
  GET /v2/reports/create_demo_reports?format=stream
  GET /v2/reports/create_demo_reports?format=stream&count=3&report_type=site_scan
  """
  request_params = dict(request.query_params)
  
  if len(request_params) == 0:
    doc = textwrap.dedent(create_demo_reports_endpoint.__doc__)
    return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")
  
  format_param = request_params.get("format", "")
  if format_param != "stream":
    return json_result(False, "This endpoint only supports format=stream", {})
  
  try:
    count = int(request_params.get("count", "5"))
  except ValueError:
    return json_result(False, "Invalid 'count' parameter. Must be integer.", {})
  
  try:
    delay_ms = int(request_params.get("delay_ms", "300"))
  except ValueError:
    return json_result(False, "Invalid 'delay_ms' parameter. Must be integer.", {})
  
  report_type = request_params.get("report_type", "crawl")
  if report_type not in ["crawl", "site_scan"]:
    return json_result(False, "'report_type' must be 'crawl' or 'site_scan'.", {})
  
  if count < 1 or count > 20:
    return json_result(False, "'count' must be between 1 and 20.", {})
  
  if delay_ms < 0 or delay_ms > 5000:
    return json_result(False, "'delay_ms' must be between 0 and 5000.", {})
  
  writer = StreamingJobWriter(
    persistent_storage_path=get_persistent_storage_path(),
    router_name=router_name,
    action="create_demo_reports",
    object_id=None,
    source_url=str(request.url),
    router_prefix=router_prefix
  )
  stream_logger = MiddlewareLogger.create(stream_job_writer=writer)
  stream_logger.log_function_header("create_demo_reports_endpoint")
  
  async def stream_create_demo_reports():
    import datetime
    created_reports = []
    failed_reports = []
    batch_id = uuid.uuid4().hex[:8]
    
    # Randomly select at least 1 index to be a failed report (if count > 1)
    fail_indices = set()
    if count > 1:
      fail_indices.add(random.randint(0, count - 1))  # At least 1 failed
      # Optionally add more failures (20% chance per remaining report)
      for idx in range(count):
        if idx not in fail_indices and random.random() < 0.2:
          fail_indices.add(idx)
    
    try:
      yield writer.emit_start()
      
      sse = stream_logger.log_function_output(f"Creating {count} demo report(s) (batch='{batch_id}', type='{report_type}', delay={delay_ms}ms)...")
      if sse: yield sse
      
      for i in range(count):
        now = datetime.datetime.now(datetime.timezone.utc)
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{timestamp}_demo_{batch_id}_{i+1:02d}"
        is_failed = i in fail_indices
        title = f"Demo {report_type} report {i+1}"
        
        sse = stream_logger.log_function_output(f"[ {i+1} / {count} ] Creating report '{filename}'...")
        if sse: yield sse
        
        await asyncio.sleep(delay_ms / 1000.0)
        
        control_action = None
        async for item in writer.check_control():
          if isinstance(item, ControlAction):
            control_action = item
          else:
            yield item
        
        if control_action == ControlAction.CANCEL:
          sse = stream_logger.log_function_output(f"Cancelled after creating {len(created_reports)} report(s).")
          if sse: yield sse
          stream_logger.log_function_footer()
          yield writer.emit_end(ok=False, error="Cancelled by user.", data={"created": len(created_reports), "reports": created_reports}, cancelled=True)
          return
        
        try:
          # Create demo report with sample data (some randomly marked as failed)
          metadata = {
            "title": title,
            "type": report_type,
            "ok": not is_failed,
            "error": "Simulated failure for demo purposes" if is_failed else "",
            "demo": True,
            "batch_id": batch_id
          }
          files = [
            ("sample_data.csv", f"id,name,value\n1,demo_{i+1}_a,100\n2,demo_{i+1}_b,200\n".encode('utf-8'))
          ]
          report_id = create_report(report_type, filename, files, metadata)
          created_reports.append(report_id)
          sse = stream_logger.log_function_output("  OK." if not is_failed else "  OK (marked as failed report).")
          if sse: yield sse
        except Exception as e:
          failed_reports.append({"filename": filename, "error": str(e)})
          sse = stream_logger.log_function_output(f"  FAIL: {str(e)}")
          if sse: yield sse
      
      sse = stream_logger.log_function_output("")
      if sse: yield sse
      sse = stream_logger.log_function_output(f"Completed: {len(created_reports)} created, {len(failed_reports)} failed.")
      if sse: yield sse
      
      stream_logger.log_function_footer()
      
      ok = len(failed_reports) == 0
      yield writer.emit_end(
        ok=ok,
        error="" if ok else f"{len(failed_reports)} report(s) failed.",
        data={"batch_id": batch_id, "created": len(created_reports), "failed": len(failed_reports), "reports": created_reports}
      )
      
    except Exception as e:
      sse = stream_logger.log_function_output(f"ERROR: {type(e).__name__}: {str(e)}")
      if sse: yield sse
      stream_logger.log_function_footer()
      yield writer.emit_end(ok=False, error=str(e), data={"created": len(created_reports), "reports": created_reports})
    finally:
      writer.finalize()
  
  return StreamingResponse(stream_create_demo_reports(), media_type="text/event-stream")

# ----------------------------------------- END: /reports/create_demo_reports endpoint -----------------------------------
