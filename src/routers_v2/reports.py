# Reports Router V2 - Report archive management UI
# Spec: _V2_SPEC_REPORTS.md, _V2_SPEC_REPORTS_UI.md
# Endpoints: L(j)G(jh)F(jr)D(z)X(jh): /v2/reports

import asyncio, random, textwrap, uuid
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, FileResponse, Response, StreamingResponse

from routers_v2.common_report_functions_v2 import list_reports, get_report_metadata, get_report_file, delete_report, get_report_archive_path, create_report
from routers_v2.common_report_functions_v2 import set_config as set_report_functions_config
from routers_v2.common_logging_functions_v2 import MiddlewareLogger, UNKNOWN
from routers_v2.common_ui_functions_v2 import generate_ui_page, generate_router_docs_page, generate_endpoint_docs, json_result, html_result
from routers_v2.common_job_functions_v2 import StreamingJobWriter, ControlAction

router = APIRouter()
config = None
router_prefix = None
router_name = "reports"
main_page_nav_html = '<a href="/">Back to Main Page</a> | <a href="{router_prefix}/domains?format=ui">Domains</a> | <a href="{router_prefix}/sites?format=ui">Sites</a> | <a href="{router_prefix}/crawler?format=ui">Crawler</a> | <a href="{router_prefix}/jobs?format=ui">Jobs</a> | <a href="{router_prefix}/reports?format=ui">Reports</a>'
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

def get_persistent_storage_path(request: Request) -> str:
  """Get persistent storage path from system_info (works in Azure where path is computed)."""
  if hasattr(request.app.state, 'system_info') and request.app.state.system_info:
    return getattr(request.app.state.system_info, 'PERSISTENT_STORAGE_PATH', None) or ''
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
      '<button class="btn-small" onclick="window.location=\\'{router_prefix}/{router_name}/view?report_id=' + encodeURIComponent(reportId) + '&format=ui\\'">View</button> ' +
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
    const endpointUrl = `{router_prefix}/{router_name}/get?report_id=${{encodeURIComponent(reportId)}}&format=json`;
    const response = await fetch(endpointUrl);
    const result = await response.json();
    if (result.ok) {{
      const data = result.data;
      const status = data.ok === null || data.ok === undefined ? '-' : (data.ok ? 'OK' : 'FAIL');
      const body = document.querySelector('#modal .modal-body');
      body.innerHTML = `
        <div class="modal-header">
          <h3>Result (${{status}}) - '${{escapeHtml(data.title || reportId)}}'</h3>
          <div style="font-size: 0.8em; color: #666; margin-top: 4px;"><a href="${{endpointUrl}}" target="_blank" style="color: #0066cc;">${{endpointUrl}}</a></div>
        </div>
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
  if (!confirm('Delete ' + ids.length + ' selected reports?')) return;
  
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


# ----------------------------------------- START: Report View Page Generation --------------------------------------------

def get_report_view_css() -> str:
  return """
/* Base - Full viewport */
html, body { height: 100%; margin: 0; padding: 0; overflow: hidden; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; flex-direction: column; }
a { color: #0066cc; text-decoration: none; }
a:hover { text-decoration: underline; }

/* Page Header */
.page-header { padding: 12px 16px; border-bottom: 1px solid #ddd; background: #f8f9fa; flex-shrink: 0; }
.page-header h1 { margin: 0 0 8px 0; }
.nav-links { }

/* Report Header */
.report-header { display: flex; gap: 32px; padding: 12px 16px; background: #fff; border-bottom: 1px solid #ddd; flex-shrink: 0; }
.report-info { display: flex; flex-direction: column; gap: 4px; font-size: 0.9em; }
.status-ok { color: #28a745; font-weight: 600; }
.status-fail { color: #dc3545; font-weight: 600; }

/* Viewer Container - Fill remaining space */
.viewer-container { display: flex; flex: 1; min-height: 0; }

/* Tree Panel */
.tree-panel { width: 280px; min-width: 150px; display: flex; flex-direction: column; background: #fafafa; border-right: 1px solid #ddd; }
.panel-header { padding: 8px 12px; font-weight: 600; font-size: 0.85em; background: #f0f0f0; border-bottom: 1px solid #ddd; }
.file-tree { flex: 1; overflow: auto; padding: 8px; font-size: 0.85em; }

/* Tree Nodes */
.tree-node { user-select: none; }
.tree-node.folder > .folder-row { display: flex; align-items: center; padding: 3px 0; cursor: pointer; }
.tree-node.folder > .folder-row:hover { background: #e8e8e8; }
.folder-toggle { width: 16px; text-align: center; font-size: 0.8em; color: #666; }
.folder-name { font-weight: 500; }
.tree-children { padding-left: 16px; }
.tree-children.collapsed { display: none; }

.tree-node.file { padding: 3px 0 3px 20px; cursor: pointer; }
.tree-node.file:hover { background: #e8f4fc; }
.tree-node.file.selected { background: #cce5ff; }
.tree-node.file.disabled { color: #999; cursor: not-allowed; }
.tree-node.file.disabled:hover { background: transparent; }

/* Resize Handle */
.resize-handle { width: 5px; background: #ddd; cursor: col-resize; flex-shrink: 0; transition: background 0.2s; }
.resize-handle:hover, .resize-handle.active { background: #0090F1; }

/* Table Panel */
.table-panel { flex: 1; min-width: 300px; display: flex; flex-direction: column; overflow: hidden; background: #fff; }
.panel-header { display: flex; justify-content: space-between; align-items: center; }
.btn-download { padding: 2px 8px; font-size: 11px; background: #6c757d; color: #fff; border-radius: 3px; text-decoration: none; }
.btn-download:hover { background: #5a6268; text-decoration: none; }
.csv-table-container { flex: 1; overflow: auto; padding: 0; background: #fff; border: 1px solid #ddd; border-top: none; }
.empty-state { padding: 24px; color: #666; text-align: center; background: #fff; }

/* CSV Table */
.csv-table { border-collapse: collapse; font-size: 12px; white-space: nowrap; width: 100%; background: #fff; }
.csv-table th, .csv-table td { border: 1px solid #ddd; padding: 6px 10px; text-align: left; max-width: 400px; overflow: hidden; text-overflow: ellipsis; }
.csv-table th { background: #f5f5f5; font-weight: 600; position: sticky; top: 0; z-index: 1; }
.csv-table tr:nth-child(even) { background: #fafafa; }
.csv-table tr:hover { background: #f0f7ff; }
.csv-table tbody tr:last-child td { border-bottom: none; }

/* Loading */
.loading { padding: 24px; color: #666; text-align: center; }
"""

def get_report_view_js() -> str:
  return """
// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', function() {
  renderFileTree();
  initPanelResize();
  selectFirstCsvFile();
});

// ============================================
// TREE BUILDING
// ============================================
function buildTreeStructure(files) {
  var tree = {};
  files.forEach(function(file) {
    var parts = file.file_path.split('/');
    var current = tree;
    parts.forEach(function(part, idx) {
      if (idx === parts.length - 1) {
        current[part] = { _isFile: true, path: file.file_path, size: file.file_size };
      } else {
        if (!current[part]) current[part] = { _isFolder: true };
        current = current[part];
      }
    });
  });
  return tree;
}

function renderFileTree() {
  var tree = buildTreeStructure(filesData);
  var container = document.getElementById('file-tree');
  container.innerHTML = renderTreeNode(tree, '');
}

function renderTreeNode(node, path) {
  var html = '';
  var entries = Object.keys(node).filter(function(k) { return !k.startsWith('_'); }).sort(function(a, b) {
    var aIsFolder = node[a]._isFolder;
    var bIsFolder = node[b]._isFolder;
    if (aIsFolder && !bIsFolder) return -1;
    if (!aIsFolder && bIsFolder) return 1;
    return a.localeCompare(b);
  });
  
  entries.forEach(function(name) {
    var value = node[name];
    if (value._isFolder) {
      var folderPath = path ? path + '/' + name : name;
      html += '<div class="tree-node folder" data-path="' + escapeHtml(folderPath) + '">';
      html += '<div class="folder-row" onclick="toggleFolder(this.parentNode)">';
      html += '<span class="folder-toggle">v</span>';
      html += '<span class="folder-name">' + escapeHtml(name) + '</span>';
      html += '</div>';
      html += '<div class="tree-children">' + renderTreeNode(value, folderPath) + '</div>';
      html += '</div>';
    } else if (value._isFile) {
      var isCsv = name.toLowerCase().endsWith('.csv');
      var fileClass = isCsv ? 'file csv' : 'file disabled';
      var onclick = isCsv ? ' onclick="selectFile(this)"' : '';
      html += '<div class="tree-node ' + fileClass + '" data-path="' + escapeHtml(value.path) + '"' + onclick + '>';
      html += '<span class="file-name">' + escapeHtml(name) + '</span>';
      html += '</div>';
    }
  });
  return html;
}

function toggleFolder(node) {
  var children = node.querySelector('.tree-children');
  var toggle = node.querySelector('.folder-toggle');
  if (children.classList.contains('collapsed')) {
    children.classList.remove('collapsed');
    toggle.textContent = 'v';
  } else {
    children.classList.add('collapsed');
    toggle.textContent = '>';
  }
}

// ============================================
// FILE SELECTION
// ============================================
function selectFile(element) {
  var selected = document.querySelectorAll('.tree-node.file.selected');
  for (var i = 0; i < selected.length; i++) {
    selected[i].classList.remove('selected');
  }
  element.classList.add('selected');
  var filePath = element.dataset.path;
  loadCsvFile(filePath);
}

function selectFirstCsvFile() {
  var firstCsv = document.querySelector('.tree-node.file.csv');
  if (firstCsv) selectFile(firstCsv);
}

// ============================================
// CSV LOADING
// ============================================
function loadCsvFile(filePath) {
  var filenameEl = document.getElementById('table-filename');
  var downloadBtn = document.getElementById('download-btn');
  var container = document.getElementById('csv-container');
  
  var filename = filePath.split('/').pop();
  filenameEl.textContent = filename;
  container.innerHTML = '<div class="loading">Loading...</div>';
  
  var url = routerPrefix + '/' + routerName + '/file?report_id=' + encodeURIComponent(reportId) + '&file_path=' + encodeURIComponent(filePath) + '&format=raw';
  downloadBtn.href = url;
  downloadBtn.download = filename;
  downloadBtn.style.display = 'inline-block';
  fetch(url)
    .then(function(response) {
      if (!response.ok) throw new Error('Failed to load file');
      return response.text();
    })
    .then(function(csvText) {
      var data = parseCsv(csvText);
      renderCsvTable(data);
    })
    .catch(function(e) {
      container.innerHTML = '<div class="empty-state">Error loading file: ' + escapeHtml(e.message) + '</div>';
    });
}

function parseCsv(text) {
  var lines = text.split(/\\r?\\n/).filter(function(line) { return line.trim(); });
  return lines.map(function(line) {
    var result = [];
    var current = '';
    var inQuotes = false;
    for (var i = 0; i < line.length; i++) {
      var char = line[i];
      if (char === '"') {
        if (inQuotes && line[i+1] === '"') {
          current += '"';
          i++;
        } else {
          inQuotes = !inQuotes;
        }
      } else if (char === ',' && !inQuotes) {
        result.push(current);
        current = '';
      } else {
        current += char;
      }
    }
    result.push(current);
    return result;
  });
}

function renderCsvTable(data) {
  var container = document.getElementById('csv-container');
  if (data.length === 0) {
    container.innerHTML = '<div class="empty-state">Empty file</div>';
    return;
  }
  
  var html = '<table class="csv-table"><thead><tr>';
  data[0].forEach(function(header) { html += '<th>' + escapeHtml(header) + '</th>'; });
  html += '</tr></thead><tbody>';
  
  for (var i = 1; i < data.length; i++) {
    html += '<tr>';
    data[i].forEach(function(cell) { html += '<td title="' + escapeHtml(cell) + '">' + escapeHtml(cell) + '</td>'; });
    html += '</tr>';
  }
  html += '</tbody></table>';
  container.innerHTML = html;
}

// ============================================
// PANEL RESIZE
// ============================================
function initPanelResize() {
  var handle = document.getElementById('resize-handle');
  var treePanel = document.getElementById('tree-panel');
  var isResizing = false;
  var startX, startWidth;
  
  handle.addEventListener('mousedown', function(e) {
    isResizing = true;
    startX = e.clientX;
    startWidth = treePanel.offsetWidth;
    handle.classList.add('active');
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    e.preventDefault();
  });
  
  document.addEventListener('mousemove', function(e) {
    if (!isResizing) return;
    var delta = e.clientX - startX;
    var newWidth = Math.max(150, Math.min(startWidth + delta, window.innerWidth - 350));
    treePanel.style.width = newWidth + 'px';
  });
  
  document.addEventListener('mouseup', function() {
    if (isResizing) {
      isResizing = false;
      handle.classList.remove('active');
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }
  });
}

// ============================================
// UTILITIES
// ============================================
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
"""

def generate_report_view_page(report_id: str, metadata: dict) -> str:
  """Generate HTML page for report viewer with tree and table panels."""
  import html
  import json
  
  nav_links = main_page_nav_html.replace("{router_prefix}", router_prefix)
  
  title = html.escape(metadata.get("title", report_id))
  report_type = html.escape(metadata.get("type", "-"))
  created = metadata.get("created_utc", "-")
  ok = metadata.get("ok")
  status = "-" if ok is None else ("OK" if ok else "FAIL")
  status_class = "" if ok is None else ("status-ok" if ok else "status-fail")
  
  # Serialize files array for JavaScript (server embeds, client uses directly)
  files_json = json.dumps(metadata.get("files", []))
  
  return f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Report Viewer - {title}</title>
  <style>
{get_report_view_css()}
  </style>
</head>
<body>
  <div class="page-header">
    <h1>Report Viewer</h1>
    <div class="nav-links">{nav_links}</div>
  </div>
  
  <div class="report-header">
    <div class="report-info">
      <div><strong>Title:</strong> {title}</div>
      <div><strong>Type:</strong> {report_type}</div>
    </div>
    <div class="report-info">
      <div><strong>Created:</strong> {created}</div>
      <div><strong>Status:</strong> <span class="{status_class}">{status}</span></div>
    </div>
  </div>
  
  <div class="viewer-container">
    <div class="tree-panel" id="tree-panel">
      <div class="panel-header">Files</div>
      <div class="file-tree" id="file-tree"></div>
    </div>
    <div class="resize-handle" id="resize-handle"></div>
    <div class="table-panel" id="table-panel">
      <div class="panel-header" id="table-header"><span id="table-filename">Select a CSV file</span><a id="download-btn" class="btn-download" style="display:none;" download>Download</a></div>
      <div class="csv-table-container" id="csv-container">
        <div class="empty-state">Click a CSV file in the tree to view its contents</div>
      </div>
    </div>
  </div>
  
  <script>
var reportId = '{report_id}';
var routerPrefix = '{router_prefix}';
var routerName = '{router_name}';
var filesData = {files_json};

{get_report_view_js()}
  </script>
</body>
</html>'''

# ----------------------------------------- END: Report View Page Generation ----------------------------------------------


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


# ----------------------------------------- START: /reports/view endpoint -------------------------------------------------

@router.get(f"/{router_name}/view")
async def view_report_endpoint(request: Request):
  """
  View report archive contents with split-panel UI.
  
  Parameters:
  - report_id: Report identifier (required)
  - format: Response format (ui only)
  
  Examples:
  /v2/reports/view?report_id=crawls/2024-01-15_14-25-00_TEST01_all_full&format=ui
  """
  logger = MiddlewareLogger.create()
  logger.log_function_header("view_report_endpoint()")
  request_params = dict(request.query_params)
  
  # DD-E001: Self-documentation on bare GET
  if len(request_params) == 0:
    logger.log_function_footer()
    doc = textwrap.dedent(view_report_endpoint.__doc__)
    return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")
  
  format_param = request_params.get("format", "")
  report_id = request_params.get("report_id", None)
  
  if not report_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'report_id' parameter.", {})
  
  if format_param != "ui":
    logger.log_function_footer()
    return json_result(False, "This endpoint only supports format=ui", {})
  
  # Fetch report metadata (server-side, embedded in page per RPTV-DD-02)
  metadata = get_report_metadata(report_id, logger=logger)
  if metadata is None:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": f"Report '{report_id}' not found.", "data": {}}, status_code=404)
  
  logger.log_function_footer()
  return HTMLResponse(generate_report_view_page(report_id, metadata))

# ----------------------------------------- END: /reports/view endpoint ---------------------------------------------------


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
    persistent_storage_path=get_persistent_storage_path(request),
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
          sse = stream_logger.log_function_output(f"{len(created_reports)} report{'' if len(created_reports) == 1 else 's'} created before cancel.")
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
      sse = stream_logger.log_function_output(f"{len(created_reports)} created, {len(failed_reports)} failed.")
      if sse: yield sse
      
      stream_logger.log_function_footer()
      
      ok = len(failed_reports) == 0
      yield writer.emit_end(
        ok=ok,
        error="" if ok else f"{len(failed_reports)} report(s) failed.",
        data={"batch_id": batch_id, "created": len(created_reports), "failed": len(failed_reports), "reports": created_reports}
      )
      
    except Exception as e:
      sse = stream_logger.log_function_output(f"ERROR: Report creation failed -> {type(e).__name__}: {str(e)}")
      if sse: yield sse
      stream_logger.log_function_footer()
      yield writer.emit_end(ok=False, error=str(e), data={"created": len(created_reports), "reports": created_reports})
    finally:
      writer.finalize()
  
  return StreamingResponse(stream_create_demo_reports(), media_type="text/event-stream")

# ----------------------------------------- END: /reports/create_demo_reports endpoint -----------------------------------
