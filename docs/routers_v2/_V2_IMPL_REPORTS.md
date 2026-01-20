# V2 Reports Router Implementation Plan

**Plan ID**: V2RP-IP02
**Goal**: Implement reports router with endpoints and UI for managing report archives
**Target file**: `/src/routers_v2/reports.py`

**Depends on:**
- `_V2_SPEC_REPORTS.md` for endpoint specification
- `_V2_SPEC_REPORTS_UI.md` for UI specification
- `_V2_COMMON_REPORT_FUNCTIONS_IMPL.md` for helper functions (implemented, tested)
- `common_ui_functions_v2.py` for UI generation

## Table of Contents

1. Implementation Status
2. File Structure
3. Router Setup
4. Endpoints Implementation
5. UI Implementation
6. JavaScript Functions
7. Final Checks

## Implementation Status

**Helper functions (DONE):**
- [x] `common_report_functions_v2.py` - 68 tests passing
- [x] `create_report()` with dry_run and logger
- [x] `list_reports()` with logger
- [x] `get_report_metadata()` with logger
- [x] `get_report_file()` with logger
- [x] `delete_report()` with dry_run and logger
- [x] `get_report_archive_path()`
- [x] Long path support for Windows

**Router (TODO):**
- [ ] `/v2/reports` - List endpoint
- [ ] `/v2/reports/get` - Get metadata endpoint
- [ ] `/v2/reports/file` - Get file endpoint
- [ ] `/v2/reports/download` - Download ZIP endpoint
- [ ] `/v2/reports/delete` - Delete endpoint
- [ ] UI page generation

## File Structure

```
/src/routers_v2/
├── reports.py                      # Router implementation (NEW)
├── common_report_functions_v2.py   # Helper functions (DONE)
└── common_ui_functions_v2.py       # UI helpers (existing)
```

## Router Setup

```python
# reports.py - Report archive management UI
# Spec: _V2_SPEC_REPORTS.md, _V2_SPEC_REPORTS_UI.md

import textwrap
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, FileResponse, Response

from routers_v2.common_report_functions_v2 import list_reports, get_report_metadata, get_report_file, delete_report, get_report_archive_path
from routers_v2.common_report_functions_v2 import set_config as set_report_functions_config
from routers_v2.common_logging_functions_v2 import MiddlewareLogger
from routers_v2.common_ui_functions_v2 import generate_router_docs_page, generate_endpoint_docs, json_result, html_result, generate_html_head, generate_toast_container, generate_modal_structure, generate_console_panel, generate_core_js, generate_console_js

router = APIRouter()
config = None
router_prefix = None
router_name = "reports"
main_page_nav_html = '<a href="/">Back to Main Page</a>'
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
```

## Endpoints Implementation

### GET /v2/reports

**Spec:** V2RP-FR-01, V2RP-FR-02

```python
@router.get(f'/{router_name}')
async def list_reports_endpoint(request: Request):
  """
  List all reports, optionally filtered by type.
  
  Parameters:
  - type: Filter by report type (crawl, site_scan)
  - format: Response format (json, html, ui)
  
  Examples:
  /v2/reports?format=json
  /v2/reports?type=crawl&format=json
  /v2/reports?format=ui
  """
  logger = MiddlewareLogger.create()
  logger.log_function_header("list_reports_endpoint()")
  request_params = dict(request.query_params)
  
  # DD-E001: Self-documentation on bare GET
  if len(request_params) == 0:
    logger.log_function_footer()
    return PlainTextResponse(textwrap.dedent(list_reports_endpoint.__doc__))
  
  format_param = request_params.get("format", "json")
  type_filter = request_params.get("type", None)
  reports = list_reports(type_filter=type_filter, logger=logger)
  
  if format_param == "ui":
    logger.log_function_footer()
    return HTMLResponse(generate_reports_ui_page(reports))
  elif format_param == "html":
    logger.log_function_footer()
    return html_result("Reports", reports, f'{main_page_nav_html}')
  
  logger.log_function_footer()
  return json_result(True, "", reports)
```

### GET /v2/reports/get

**Spec:** V2RP-FR-03

```python
@router.get(f'/{router_name}/get')
async def get_report_endpoint(request: Request):
  """
  Get report metadata (report.json content).
  
  Parameters:
  - report_id: Report identifier (required)
  - format: Response format (json, html)
  
  Examples:
  /v2/reports/get?report_id=crawls/2024-01-15_14-25-00_TEST01_all_full
  """
  # Self-documentation, get report_id, call get_report_metadata()
  # Return 404 if not found
```

### GET /v2/reports/file

**Spec:** V2RP-FR-04

```python
@router.get(f'/{router_name}/file')
async def get_file_endpoint(request: Request):
  """
  Get specific file from report archive.
  
  Parameters:
  - report_id: Report identifier (required)
  - file_path: File path within archive (required)
  - format: Response format (raw, json, html) - default: raw
  
  Examples:
  /v2/reports/file?report_id=crawls/...&file_path=01_files/source01/sharepoint_map.csv
  /v2/reports/file?report_id=crawls/...&file_path=report.json&format=json
  """
  # Self-documentation, get params, call get_report_file()
  # format=raw: Return with Content-Type based on extension:
  #   .json -> application/json
  #   .csv -> text/csv
  #   .txt -> text/plain
  #   .zip -> application/zip
  #   default -> application/octet-stream
  # format=json: Wrap in JSON result (text files only)
  # format=html: Convert to HTML table if CSV/JSON
```

### GET /v2/reports/download

**Spec:** V2RP-FR-05

```python
@router.get(f'/{router_name}/download')
async def download_report_endpoint(request: Request):
  """
  Download report archive as ZIP.
  
  Parameters:
  - report_id: Report identifier (required)
  
  Examples:
  /v2/reports/download?report_id=crawls/2024-01-15_14-25-00_TEST01_all_full
  """
  # Self-documentation, get report_id
  # Get archive path, return FileResponse with Content-Disposition
  # Return 404 if not found
```

### DELETE, GET /v2/reports/delete

**Spec:** V2RP-FR-06, DD-E017 (return full object on delete)

```python
@router.api_route(f'/{router_name}/delete', methods=["GET", "DELETE"])
async def delete_report_endpoint(request: Request):
  """
  Delete report archive.
  
  Parameters:
  - report_id: Report identifier (required)
  
  Examples:
  DELETE /v2/reports/delete?report_id=crawls/2024-01-15_14-25-00_TEST01_all_full
  """
  # Self-documentation on bare GET
  # Call delete_report() - returns full metadata
  # Return deleted report data per DD-E017
  # Return 404 if not found
```

## UI Implementation

### Page Generation

```python
def generate_reports_ui_page(reports: list) -> str:
  """Generate Reports UI HTML page."""
  # Use common_ui_functions_v2.generate_router_page()
  # Include:
  # - Navigation links (Back, Jobs, Crawler)
  # - Toolbar with Delete button
  # - Table with columns: checkbox, Type, Title, Created, Result, Actions
  # - Console panel (hidden)
  # - Router-specific JavaScript
```

### Navigation Links

Per UI spec:
- Back to Main Page: `/`
- Jobs: `/v2/jobs?format=ui`
- Crawler: `/v2/crawler?format=ui`

### Table Structure

```html
<table id="reports-table">
  <thead>
    <tr>
      <th><input type="checkbox" id="select-all" onchange="toggleSelectAll()"></th>
      <th>Type</th>
      <th>Title</th>
      <th>Created</th>
      <th>Result</th>
      <th>Actions</th>
    </tr>
  </thead>
  <tbody id="reports-tbody">
    <!-- Rendered by JavaScript -->
  </tbody>
</table>
```

### Toolbar

```html
<button id="bulk-delete-btn" onclick="bulkDelete()" disabled>
  Delete (<span id="selected-count">0</span>)
</button>
```

## Critical Implementation Patterns

**IMPORTANT:** These patterns were discovered during implementation and must be followed exactly.

### 1. Common UI Element IDs (MUST MATCH)

The `generate_ui_page()` function generates specific element IDs. Custom JS must use these exact IDs:

| Element | Correct ID | Wrong ID |
|---------|-----------|----------|
| Item count | `#item-count` | `#reports-count` |
| Table body | `#items-tbody` | `#reports-tbody` |
| Checkbox class | `.item-checkbox` | `.report-checkbox` |
| Checkbox data attr | `data-item-id` | `data-report-id` |
| Delete button | `#btn-delete-selected` | `#bulk-delete-btn` |
| Select all | `#select-all` | - |

### 2. String Concatenation for Row Rendering (CRITICAL)

**DO NOT use template literals** for `renderRow` functions when onclick handlers contain quotes.

Template literals process escape sequences differently, causing quote escaping to fail.

**BAD (template literal):**
```javascript
return `<tr><td><button onclick="deleteReport('${id}')">Delete</button></td></tr>`;
```

**GOOD (string concatenation - matches jobs.py):**
```javascript
return '<tr><td><button onclick="deleteReport(\\'' + id + '\\')">Delete</button></td></tr>';
```

### 3. Quote Escaping in onclick Handlers

Inside Python f-string that generates JS string concatenation:
- `\\'` produces `\'` which becomes `'` in final HTML onclick
- For confirm dialogs: `if(confirm(\\'Delete ' + title + '?\\'))`
- NO extra quotes around variables in the confirm message

**Pattern:**
```javascript
'<button onclick="if(confirm(\\'Delete report ' + escapedTitle + '?\\')) deleteReport(\\'' + reportId + '\\')">Delete</button>'
```

### 4. Modal Display Pattern

**DO NOT** create custom `showResultModal()` that calls undefined `showModal()`.

**Use direct modal body manipulation (matches jobs.py):**
```javascript
async function showReportResult(reportId) {{
  const response = await fetch(`...`);
  const result = await response.json();
  if (result.ok) {{
    const data = result.data;
    const body = document.querySelector('#modal .modal-body');
    body.innerHTML = `
      <div class="modal-header"><h3>Title</h3></div>
      <div class="modal-scroll"><pre>${{escapeHtml(JSON.stringify(data, null, 2))}}</pre></div>
      <div class="modal-footer"><button onclick="closeModal()">OK</button></div>
    `;
    openModal();
  }}
}}
```

### 5. Use Common Functions (DO NOT REDEFINE)

These functions are provided by `generate_core_js()` in `common_ui_functions_v2.py`. **Do not redefine them in router-specific JS:**

| Function | Purpose | Usage |
|----------|---------|-------|
| `formatTimestamp(ts)` | Format ISO timestamp | `formatTimestamp(report.created_utc)` |
| `formatResultOkFail(ok)` | Format boolean to OK/FAIL | `formatResultOkFail(report.ok)` or `formatResultOkFail(job.result?.ok)` |
| `sanitizeId(id)` | Sanitize for row ID | `sanitizeId(report.report_id)` |
| `updateSelectedCount()` | Update count + reset select-all | Already wired to `.item-checkbox` |
| `toggleSelectAll()` | Toggle all checkboxes | Already wired to `#select-all` |
| `getSelectedIds()` | Get checked item IDs | Returns `data-item-id` values |

**Router-specific wrappers (if needed):**
```javascript
function getSelectedReportIds() {{ return getSelectedIds(); }}
```

### 6. Button Classes

- **Action buttons:** `class="btn-small"` for consistent styling
- **Delete button:** `class="btn-small btn-delete"` for red styling
- **Confirm dialog:** Add `if(confirm('...'))` before destructive actions

### 7. Declarative Button Pattern

For buttons with simple actions, use `data-*` attributes:

```javascript
'<button class="btn-small" data-url="' + downloadUrl + '" onclick="downloadReport(this)">Download</button>'

function downloadReport(btn) {{
  window.location = btn.dataset.url;
}}
```

### 8. XSS Prevention

Always use `escapeHtml()` for user-provided content:
```javascript
const escapedTitle = escapeHtml(report.title || '');
'<td>' + escapeHtml(report.type || '-') + '</td>'
```

### 9. Function Naming Convention

Use `reloadItems()` as the standard name (called by common UI on stream finish):
```javascript
function reloadItems() {{
  // Router-specific reload logic
  reloadReports();  // or inline the logic
}}
```

## JavaScript Functions

### State Management

```javascript
const reportsState = new Map();
```

### Page Init

```javascript
document.addEventListener('DOMContentLoaded', () => {
  reloadReports();
  initConsoleResize();
});
```

### Core Functions

```javascript
async function reloadReports() {
  const response = await fetch('/v2/reports?format=json');
  const result = await response.json();
  if (result.ok) {
    reportsState.clear();
    result.data.forEach(r => reportsState.set(r.report_id, r));
    renderAllReports();
  }
}

function renderAllReports() {
  const tbody = document.getElementById('reports-tbody');
  if (reportsState.size === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No reports found</td></tr>';
    return;
  }
  tbody.innerHTML = '';
  reportsState.forEach(report => {
    tbody.innerHTML += renderReportRow(report);
  });
  updateSelectedCount();
}

function renderReportRow(report) {
  const rowClass = report.ok === false ? 'row-cancel-or-fail' : '';
  const result = formatResult(report.ok);
  const created = formatTimestamp(report.created_utc);
  return `<tr id="report-${encodeId(report.report_id)}" class="${rowClass}">
    <td><input type="checkbox" class="report-checkbox" data-report-id="${report.report_id}" onchange="updateSelectedCount()"></td>
    <td>${report.type}</td>
    <td>${report.title}</td>
    <td>${created}</td>
    <td>${result}</td>
    <td>
      <button onclick="showReportResult('${report.report_id}')">Result</button>
      <button onclick="downloadReport('${report.report_id}')">Download</button>
      <button onclick="deleteReport('${report.report_id}', '${report.title}')">Delete</button>
    </td>
  </tr>`;
}
```

### Actions

```javascript
async function showReportResult(reportId) {
  const response = await fetch(`/v2/reports/get?report_id=${encodeURIComponent(reportId)}&format=json`);
  const result = await response.json();
  if (result.ok) {
    showResultModal(result.data);
  } else {
    showToast('Error', result.error, 'error');
  }
}

function downloadReport(reportId) {
  window.location = `/v2/reports/download?report_id=${encodeURIComponent(reportId)}`;
}

async function deleteReport(reportId, title) {
  const response = await fetch(`/v2/reports/delete?report_id=${encodeURIComponent(reportId)}`, { method: 'DELETE' });
  const result = await response.json();
  if (result.ok) {
    reportsState.delete(reportId);
    renderAllReports();
    showToast('Deleted', `Report '${title}' deleted.`, 'success');
  } else {
    showToast('Error', result.error, 'error');
  }
}

async function bulkDelete() {
  const ids = getSelectedReportIds();
  if (ids.length === 0) return;
  
  let successCount = 0;
  for (const id of ids) {
    const response = await fetch(`/v2/reports/delete?report_id=${encodeURIComponent(id)}`, { method: 'DELETE' });
    const result = await response.json();
    if (result.ok) {
      reportsState.delete(id);
      successCount++;
    }
  }
  renderAllReports();
  showToast('Deleted', `${successCount} report(s) deleted.`, successCount === ids.length ? 'success' : 'warning');
}
```

### Selection

```javascript
function updateSelectedCount() {
  const checkboxes = document.querySelectorAll('.report-checkbox:checked');
  const count = checkboxes.length;
  document.getElementById('selected-count').textContent = count;
  document.getElementById('bulk-delete-btn').disabled = count === 0;
}

function toggleSelectAll() {
  const selectAll = document.getElementById('select-all').checked;
  document.querySelectorAll('.report-checkbox').forEach(cb => cb.checked = selectAll);
  updateSelectedCount();
}

function getSelectedReportIds() {
  return Array.from(document.querySelectorAll('.report-checkbox:checked'))
    .map(cb => cb.dataset.reportId);
}
```

### Helpers

```javascript
function formatResult(ok) {
  if (ok === null || ok === undefined) return '-';
  return ok ? 'OK' : 'FAIL';
}

function formatTimestamp(ts) {
  if (!ts) return '-';
  const date = new Date(ts);
  const pad = (n) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

function encodeId(id) {
  return id.replace(/[^a-zA-Z0-9]/g, '_');
}
```

## Final Checks

### Compliance with _V2_SPEC_ROUTERS.md

| Decision | Description | Compliance |
|----------|-------------|------------|
| DD-E001 | Self-documentation on bare GET | All 5 endpoints return docstring |
| DD-E002 | Action-suffixed endpoints | `/reports`, `/reports/get`, `/reports/file`, `/reports/download`, `/reports/delete` |
| DD-E004 | Format param | json, html, ui, raw supported as appropriate |
| DD-E007 | Semantic identifier names | Uses `report_id` |
| DD-E009 | Plural naming | `/reports` (plural) |
| DD-E010 | GET allowed for /delete | `@router.api_route(..., methods=["GET", "DELETE"])` |
| DD-E011 | Control params via query string | `format`, `type` via query string |
| DD-E013 | /get and /delete receive id via query | `?report_id={id}` |
| DD-E015 | UTF-8 encoding | All text responses use UTF-8 |
| DD-E017 | /delete returns full object | Returns full report metadata |

### Compliance with python-rules.md

| Rule | Compliance |
|------|------------|
| Imports at top | All imports at file top, no local imports |
| 2-space indentation | All code uses 2 spaces |
| Single line for simple statements | Applied where appropriate |
| Function grouping markers | Will use `# --- START/END ---` markers |
| Docstrings for endpoints | Endpoints have docstrings with examples |
| No emojis in code/logs | None used |

### Endpoint Verification

| Endpoint | Method | Self-Doc | Params | Response | Error |
|----------|--------|----------|--------|----------|-------|
| `/v2/reports` | GET | Bare GET | type, format | json/html/ui | - |
| `/v2/reports/get` | GET | Bare GET | report_id, format | json/html | 404 |
| `/v2/reports/file` | GET | Bare GET | report_id, file_path, format | raw/json/html | 404 |
| `/v2/reports/download` | GET | Bare GET | report_id | ZIP file | 404 |
| `/v2/reports/delete` | GET, DELETE | Bare GET | report_id | json (full object) | 404 |

### Spec Compliance Checklist

**From _V2_SPEC_REPORTS.md:**
- [ ] **V2RP-IP02-VC-01**: V2RP-FR-01 - List all reports, sorted by created_utc desc
- [ ] **V2RP-IP02-VC-02**: V2RP-FR-02 - Filter by type
- [ ] **V2RP-IP02-VC-03**: V2RP-FR-03 - Get single report metadata
- [ ] **V2RP-IP02-VC-04**: V2RP-FR-04 - Get file from archive
- [ ] **V2RP-IP02-VC-05**: V2RP-FR-05 - Download as ZIP
- [ ] **V2RP-IP02-VC-06**: V2RP-FR-06 - Delete single report
- [ ] **V2RP-IP02-VC-07**: V2RP-DD-05 - Result pattern (-, OK, FAIL)
- [ ] **V2RP-IP02-VC-08**: DD-E001 - Self-documentation on bare GET
- [ ] **V2RP-IP02-VC-09**: DD-E010 - GET allowed for /delete
- [ ] **V2RP-IP02-VC-10**: DD-E017 - Delete returns full object

**From _V2_SPEC_REPORTS_UI.md:**
- [ ] **V2RP-IP02-VC-11**: Single-page UI with reports table
- [ ] **V2RP-IP02-VC-12**: Console panel hidden by default
- [ ] **V2RP-IP02-VC-13**: Bulk delete support
- [ ] **V2RP-IP02-VC-14**: Result dialog modal
- [ ] **V2RP-IP02-VC-15**: Navigation links (Back, Jobs, Crawler)
- [ ] **V2RP-IP02-VC-16**: Row styling for failed reports
- [ ] **V2RP-IP02-VC-17**: Empty state message
- [ ] **V2RP-IP02-VC-18**: Timestamp formatting

### Test Scenarios

**Endpoint Tests:**
- **V2RP-IP02-TST-01**: List empty - No reports, returns `[]`
- **V2RP-IP02-TST-02**: List all - Returns all reports sorted by created_utc desc
- **V2RP-IP02-TST-03**: List filtered - Returns only matching type
- **V2RP-IP02-TST-04**: List self-doc - Bare GET returns documentation
- **V2RP-IP02-TST-05**: Get metadata - Returns report.json content
- **V2RP-IP02-TST-06**: Get metadata 404 - Returns error for non-existent
- **V2RP-IP02-TST-07**: Get metadata self-doc - Bare GET returns documentation
- **V2RP-IP02-TST-08**: Get file raw - Returns file content with correct Content-Type
- **V2RP-IP02-TST-09**: Get file json - Returns file content wrapped in JSON
- **V2RP-IP02-TST-10**: Get file 404 - Returns error for non-existent
- **V2RP-IP02-TST-11**: Get file self-doc - Bare GET returns documentation
- **V2RP-IP02-TST-12**: Download - Returns ZIP with Content-Disposition header
- **V2RP-IP02-TST-13**: Download 404 - Returns error for non-existent
- **V2RP-IP02-TST-14**: Download self-doc - Bare GET returns documentation
- **V2RP-IP02-TST-15**: Delete - Removes file, returns full metadata (DD-E017)
- **V2RP-IP02-TST-16**: Delete 404 - Returns error for non-existent
- **V2RP-IP02-TST-17**: Delete self-doc - Bare GET returns documentation
- **V2RP-IP02-TST-18**: Delete via GET - Works same as DELETE (DD-E010)

**UI Tests:**
- **V2RP-IP02-TST-19**: UI loads - Page renders with table structure
- **V2RP-IP02-TST-20**: UI reload - Fetches and re-renders reports
- **V2RP-IP02-TST-21**: UI delete - Removes row, shows toast
- **V2RP-IP02-TST-22**: UI bulk delete - Removes multiple, shows toast
- **V2RP-IP02-TST-23**: UI result modal - Shows report.json formatted
- **V2RP-IP02-TST-24**: UI download - Triggers file download
- **V2RP-IP02-TST-25**: UI empty state - Shows 'No reports found'
- **V2RP-IP02-TST-26**: UI row styling - Failed reports have red color

## Spec Changes

**[2024-12-30 10:50]**
- Added: Plan ID V2RP-IP02 to header block
- Changed: Spec Compliance Checklist now uses IDs V2RP-IP02-VC-01 to VC-18 (18 items)
- Changed: Test Scenarios now use IDs V2RP-IP02-TST-01 to TST-26 (26 items)
