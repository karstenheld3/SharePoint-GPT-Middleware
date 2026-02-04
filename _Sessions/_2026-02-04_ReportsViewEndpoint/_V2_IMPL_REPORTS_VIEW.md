# IMPL: V2 Reports View Endpoint

**Doc ID**: RPTV-IP01
**Goal**: Implement `/v2/reports/view` endpoint with split-panel UI for viewing report CSV files

**Target file**: `/src/routers_v2/reports.py`

**Depends on:**
- `_V2_SPEC_REPORTS_VIEW.md [RPTV-SP01]` for specification
- `_V2_IMPL_REPORTS.md [V2RP-IP02]` for existing reports router patterns

## MUST-NOT-FORGET

- Use string concatenation for JS, NOT template literals (per V2RP-IP02)
- Always `escapeHtml()` user content before inserting into HTML
- Bare GET returns self-documentation (DD-E001)
- Use existing endpoints: `/v2/reports/get` for metadata, `/v2/reports/file` for CSV content
- Non-CSV files disabled in tree (greyed, not clickable)
- Auto-select first CSV on page load
- Always URL-encode `report_id` in client-side fetch URLs (contains `/`)
- Use `main_page_nav_html.replace("{router_prefix}", router_prefix)` for navigation (per jobs.py pattern)
- Custom pages use inline CSS/JS (not shared generate_ui_page) per jobs.py pattern

## Table of Contents

1. Implementation Status
2. Implementation Steps
3. Endpoint Implementation
4. UI Page Generation
5. JavaScript Functions
6. CSS Styles
7. Add View Button to Reports UI
8. Verification Checklist

## Implementation Status

**Status: PENDING**

- [ ] RPTV-IP01-IS-01: Add `/v2/reports/view` endpoint
- [ ] RPTV-IP01-IS-02: Create `generate_report_view_page()` function
- [ ] RPTV-IP01-IS-03: Implement tree building JavaScript
- [ ] RPTV-IP01-IS-04: Implement CSV loading and table rendering
- [ ] RPTV-IP01-IS-05: Implement resizable divider
- [ ] RPTV-IP01-IS-06: Add CSS styles
- [ ] RPTV-IP01-IS-07: Add [View] button to reports list UI

## Implementation Steps

### RPTV-IP01-IS-01: Add Endpoint

Add after `/v2/reports/delete` endpoint section in `reports.py`:

```python
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
  
  # Fetch report metadata
  metadata = get_report_metadata(report_id, logger=logger)
  if metadata is None:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": f"Report '{report_id}' not found.", "data": {}}, status_code=404)
  
  logger.log_function_footer()
  return HTMLResponse(generate_report_view_page(report_id, metadata))
```

### RPTV-IP01-IS-02: Page Generation Function

Add after `generate_reports_ui_page()`. Pattern follows `_generate_jobs_ui_page()` in jobs.py:

```python
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
    <div class="nav-links">{nav_links} | <a href="{router_prefix}/{router_name}?format=ui">Reports</a></div>
    <h1>Report Viewer</h1>
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
      <div class="panel-header" id="table-header">Select a CSV file</div>
      <div class="csv-table-container" id="csv-container">
        <div class="empty-state">Click a CSV file in the tree to view its contents</div>
      </div>
    </div>
  </div>
  
  <script>
const reportId = '{report_id}';
const routerPrefix = '{router_prefix}';
const routerName = '{router_name}';
const filesData = {files_json};

{get_report_view_js()}
  </script>
</body>
</html>'''
```

### RPTV-IP01-IS-03: CSS Function

```python
def get_report_view_css() -> str:
  return """
/* Base */
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; }
a { color: #0066cc; text-decoration: none; }
a:hover { text-decoration: underline; }

/* Page Header */
.page-header { padding: 12px 16px; border-bottom: 1px solid #ddd; background: #f8f9fa; }
.page-header h1 { margin: 8px 0 0 0; font-size: 1.4em; }
.nav-links { font-size: 0.9em; }

/* Report Header */
.report-header { display: flex; gap: 32px; padding: 12px 16px; background: #fff; border-bottom: 1px solid #ddd; }
.report-info { display: flex; flex-direction: column; gap: 4px; font-size: 0.9em; }
.status-ok { color: #28a745; font-weight: 600; }
.status-fail { color: #dc3545; font-weight: 600; }

/* Viewer Container */
.viewer-container { display: flex; height: calc(100vh - 140px); }

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
.resize-handle { width: 5px; background: #ddd; cursor: col-resize; flex-shrink: 0; }
.resize-handle:hover, .resize-handle.active { background: #bbb; }

/* Table Panel */
.table-panel { flex: 1; min-width: 300px; display: flex; flex-direction: column; overflow: hidden; }
.csv-table-container { flex: 1; overflow: auto; padding: 0; }
.empty-state { padding: 24px; color: #666; text-align: center; }

/* CSV Table */
.csv-table { border-collapse: collapse; font-size: 12px; white-space: nowrap; }
.csv-table th, .csv-table td { border: 1px solid #ddd; padding: 4px 8px; text-align: left; max-width: 300px; overflow: hidden; text-overflow: ellipsis; }
.csv-table th { background: #f5f5f5; font-weight: 600; position: sticky; top: 0; z-index: 1; }
.csv-table tr:nth-child(even) { background: #fafafa; }
.csv-table tr:hover { background: #f0f7ff; }

/* Loading */
.loading { padding: 24px; color: #666; text-align: center; }
"""
```

### RPTV-IP01-IS-04: JavaScript Function

```python
def get_report_view_js() -> str:
  return """
// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
  renderFileTree();
  initPanelResize();
  selectFirstCsvFile();
});

// ============================================
// TREE BUILDING
// ============================================
function buildTreeStructure(files) {
  const tree = {};
  files.forEach(file => {
    const parts = file.file_path.split('/');
    let current = tree;
    parts.forEach((part, idx) => {
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
  const tree = buildTreeStructure(filesData);
  const container = document.getElementById('file-tree');
  container.innerHTML = renderTreeNode(tree, '');
}

function renderTreeNode(node, path) {
  let html = '';
  const entries = Object.entries(node).filter(([k]) => !k.startsWith('_')).sort((a, b) => {
    const aIsFolder = a[1]._isFolder;
    const bIsFolder = b[1]._isFolder;
    if (aIsFolder && !bIsFolder) return -1;
    if (!aIsFolder && bIsFolder) return 1;
    return a[0].localeCompare(b[0]);
  });
  
  entries.forEach(([name, value]) => {
    if (value._isFolder) {
      const folderPath = path ? path + '/' + name : name;
      html += '<div class="tree-node folder" data-path="' + escapeHtml(folderPath) + '">';
      html += '<div class="folder-row" onclick="toggleFolder(this.parentNode)">';
      html += '<span class="folder-toggle">v</span>';
      html += '<span class="folder-name">' + escapeHtml(name) + '</span>';
      html += '</div>';
      html += '<div class="tree-children">' + renderTreeNode(value, folderPath) + '</div>';
      html += '</div>';
    } else if (value._isFile) {
      const isCsv = name.toLowerCase().endsWith('.csv');
      const fileClass = isCsv ? 'file csv' : 'file disabled';
      const onclick = isCsv ? ' onclick="selectFile(this)"' : '';
      html += '<div class="tree-node ' + fileClass + '" data-path="' + escapeHtml(value.path) + '"' + onclick + '>';
      html += '<span class="file-name">' + escapeHtml(name) + '</span>';
      html += '</div>';
    }
  });
  return html;
}

function toggleFolder(node) {
  const children = node.querySelector('.tree-children');
  const toggle = node.querySelector('.folder-toggle');
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
  document.querySelectorAll('.tree-node.file.selected').forEach(el => el.classList.remove('selected'));
  element.classList.add('selected');
  const filePath = element.dataset.path;
  loadCsvFile(filePath);
}

function selectFirstCsvFile() {
  const firstCsv = document.querySelector('.tree-node.file.csv');
  if (firstCsv) selectFile(firstCsv);
}

// ============================================
// CSV LOADING
// ============================================
async function loadCsvFile(filePath) {
  const filenameEl = document.getElementById('table-filename');
  const downloadBtn = document.getElementById('download-btn');
  const container = document.getElementById('csv-container');
  
  const filename = filePath.split('/').pop();
  filenameEl.textContent = filename;
  container.innerHTML = '<div class="loading">Loading...</div>';
  
  // Update download button
  const url = routerPrefix + '/' + routerName + '/file?report_id=' + encodeURIComponent(reportId) + '&file_path=' + encodeURIComponent(filePath) + '&format=raw';
  downloadBtn.href = url;
  downloadBtn.download = filename;
  downloadBtn.style.display = 'inline-block';
  
  try {
    const url = routerPrefix + '/' + routerName + '/file?report_id=' + encodeURIComponent(reportId) + '&file_path=' + encodeURIComponent(filePath) + '&format=raw';
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to load file');
    const csvText = await response.text();
    const data = parseCsv(csvText);
    renderCsvTable(data);
  } catch (e) {
    container.innerHTML = '<div class="empty-state">Error loading file: ' + escapeHtml(e.message) + '</div>';
  }
}

function parseCsv(text) {
  const lines = text.split(/\\r?\\n/).filter(line => line.trim());
  return lines.map(line => {
    const result = [];
    let current = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
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
  const container = document.getElementById('csv-container');
  if (data.length === 0) {
    container.innerHTML = '<div class="empty-state">Empty file</div>';
    return;
  }
  
  let html = '<table class="csv-table"><thead><tr>';
  data[0].forEach(header => { html += '<th>' + escapeHtml(header) + '</th>'; });
  html += '</tr></thead><tbody>';
  
  for (let i = 1; i < data.length; i++) {
    html += '<tr>';
    data[i].forEach(cell => { html += '<td title="' + escapeHtml(cell) + '">' + escapeHtml(cell) + '</td>'; });
    html += '</tr>';
  }
  html += '</tbody></table>';
  container.innerHTML = html;
}

// ============================================
// PANEL RESIZE
// ============================================
function initPanelResize() {
  const handle = document.getElementById('resize-handle');
  const treePanel = document.getElementById('tree-panel');
  let isResizing = false;
  let startX, startWidth;
  
  handle.addEventListener('mousedown', (e) => {
    isResizing = true;
    startX = e.clientX;
    startWidth = treePanel.offsetWidth;
    handle.classList.add('active');
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    e.preventDefault();
  });
  
  document.addEventListener('mousemove', (e) => {
    if (!isResizing) return;
    const delta = e.clientX - startX;
    const newWidth = Math.max(150, Math.min(startWidth + delta, window.innerWidth - 350));
    treePanel.style.width = newWidth + 'px';
  });
  
  document.addEventListener('mouseup', () => {
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
```

### RPTV-IP01-IS-07: Add View Button to Reports UI

Add View button to `renderReportRow()` function in `get_router_specific_js()`. Insert before Result button:

```javascript
// In renderReportRow() function, update the actions cell:
'<td class="actions">' +
  '<button class="btn-small" onclick="window.location=\'' + routerPrefix + '/' + routerName + '/view?report_id=' + encodeURIComponent(reportId) + '&format=ui\'">View</button> ' +
  '<button class="btn-small" onclick="showReportResult(\'' + reportId + '\')">Result</button> ' +
  // ... rest of buttons
```

**Location in reports.py**: Around line 121-126 in `renderReportRow()` function.

## Verification Checklist

- [ ] **RPTV-IP01-VC-01**: Bare GET returns self-documentation
- [ ] **RPTV-IP01-VC-02**: Missing report_id returns error
- [ ] **RPTV-IP01-VC-03**: Invalid report_id returns 404
- [ ] **RPTV-IP01-VC-04**: format != ui returns error
- [ ] **RPTV-IP01-VC-05**: Tree displays all files from report
- [ ] **RPTV-IP01-VC-06**: Folders are collapsible
- [ ] **RPTV-IP01-VC-07**: CSV files clickable, non-CSV disabled
- [ ] **RPTV-IP01-VC-08**: First CSV auto-selected on load
- [ ] **RPTV-IP01-VC-09**: CSV content displays in table
- [ ] **RPTV-IP01-VC-10**: Resize handle adjusts panel widths
- [ ] **RPTV-IP01-VC-11**: View button appears in reports list
- [ ] **RPTV-IP01-VC-12**: View button opens viewer page

## Document History

**[2026-02-04 08:25]**
- Initial implementation plan created
