# IMPL: V2 Reports Router

**Doc ID**: V2RP-IP02
**Goal**: Implement reports router with endpoints and UI for managing report archives

**Target files**:
- `/src/routers_v2/reports.py` (NEW ~720 lines)
- `/src/routers_v2/common_report_functions_v2.py` (DONE ~230 lines)

**Depends on:**
- `_V2_SPEC_REPORTS.md [V2RP-SP01]` for endpoint specification
- `_V2_SPEC_REPORTS_UI.md [V2RP-SP02]` for UI specification
- `common_ui_functions_v2.py` for UI generation

## MUST-NOT-FORGET

- Use `#items-tbody` not `#reports-tbody` (common UI pattern)
- Use `.item-checkbox` not `.report-checkbox` (common UI pattern)
- Use string concatenation, NOT template literals for row rendering with onclick
- Do NOT redefine `updateSelectedCount()`, `toggleSelectAll()`, `getSelectedIds()` - use common functions
- Always `escapeHtml()` user content before inserting into HTML

## Table of Contents

1. Implementation Status
2. File Structure
3. Router Setup
4. Endpoints Implementation
5. UI Implementation
6. JavaScript Functions
7. Final Checks

## Implementation Status

**Status: COMPLETE** - All endpoints and UI implemented.

**Helper functions (DONE):**
- [x] `common_report_functions_v2.py` - 68 tests passing
- [x] `create_report()` with dry_run and logger
- [x] `list_reports()` with logger
- [x] `get_report_metadata()` with logger
- [x] `get_report_file()` with logger
- [x] `delete_report()` with dry_run and logger
- [x] `get_report_archive_path()`
- [x] Long path support for Windows

**Router (DONE):**
- [x] `/v2/reports` - List endpoint
- [x] `/v2/reports/get` - Get metadata endpoint
- [x] `/v2/reports/file` - Get file endpoint
- [x] `/v2/reports/download` - Download ZIP endpoint
- [x] `/v2/reports/delete` - Delete endpoint
- [x] `/v2/reports/create_demo_reports` - Demo report creation (streaming)
- [x] UI page generation with `generate_ui_page()`

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

### GET /v2/reports/create_demo_reports

**Spec:** V2RP-DD-03 exception (demo/test endpoint)

```python
@router.get(f'/{router_name}/create_demo_reports')
async def create_demo_reports_endpoint(request: Request):
  """
  Create demo reports for testing purposes. Streaming only.
  
  Parameters:
  - format=stream (required)
  - count: Number of reports (default: 5, max: 20)
  - report_type: crawl or site_scan (default: crawl)
  - delay_ms: Delay per report (default: 300, max: 5000)
  """
  # Uses StreamingJobWriter for SSE output
  # Emits start_json, log events, end_json
  # Creates reports via create_report() helper
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

**Reference:** See `get_router_specific_js()` in `reports.py` for actual implementation.

The router-specific JS follows the Critical Implementation Patterns above. Key points:

### State Management

```javascript
const reportsState = new Map();  // Router-specific state
```

### Functions Provided by Common UI (DO NOT REDEFINE)

- `formatTimestamp(ts)` - Format ISO timestamp
- `formatResultOkFail(ok)` - Format boolean to -, OK, FAIL
- `sanitizeId(id)` - Sanitize for row ID attribute
- `updateSelectedCount()` - Update count + button state
- `toggleSelectAll()` - Toggle all checkboxes
- `getSelectedIds()` - Get checked `data-item-id` values
- `escapeHtml(text)` - XSS prevention

### Router-Specific Functions

- `reloadItems()` - Standard name, calls API and re-renders
- `renderAllReports()` - Render all rows to `#items-tbody`
- `renderReportRow(report)` - **Uses string concatenation, NOT template literals**
- `showReportResult(reportId)` - Direct modal body manipulation
- `downloadReport(btn)` - Uses `btn.dataset.url`
- `deleteReport(reportId, title)` - With confirm dialog
- `bulkDelete()` - Loop through selected
- `getSelectedReportIds()` - Wrapper: `return getSelectedIds();`
- `showCreateDemoReportsForm()` - Modal form for demo creation

### Row Rendering Pattern (String Concatenation)

```javascript
// CORRECT - string concatenation with escaped quotes
return '<tr id="report-' + escapedId + '">' +
  '<td><input type="checkbox" class="item-checkbox" data-item-id="' + reportId + '" onchange="updateSelectedCount()"></td>' +
  '<td>' + escapeHtml(report.type) + '</td>' +
  // ... more cells ...
  '<td class="actions">' +
    '<button class="btn-small" onclick="showReportResult(\\'' + reportId + '\\')">Result</button> ' +
    '<button class="btn-small btn-delete" onclick="if(confirm(\\'Delete?\\')) deleteReport(\\'' + reportId + '\\')">Delete</button>' +
  '</td>' +
'</tr>';
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
- [x] **V2RP-IP02-VC-01**: V2RP-FR-01 - List all reports, sorted by created_utc desc
- [x] **V2RP-IP02-VC-02**: V2RP-FR-02 - Filter by type
- [x] **V2RP-IP02-VC-03**: V2RP-FR-03 - Get single report metadata
- [x] **V2RP-IP02-VC-04**: V2RP-FR-04 - Get file from archive
- [x] **V2RP-IP02-VC-05**: V2RP-FR-05 - Download as ZIP
- [x] **V2RP-IP02-VC-06**: V2RP-FR-06 - Delete single report
- [x] **V2RP-IP02-VC-07**: V2RP-DD-05 - Result pattern (-, OK, FAIL)
- [x] **V2RP-IP02-VC-08**: DD-E001 - Self-documentation on bare GET
- [x] **V2RP-IP02-VC-09**: DD-E010 - GET allowed for /delete
- [x] **V2RP-IP02-VC-10**: DD-E017 - Delete returns full object

**From _V2_SPEC_REPORTS_UI.md:**
- [x] **V2RP-IP02-VC-11**: Single-page UI with reports table
- [x] **V2RP-IP02-VC-12**: Console panel hidden by default
- [x] **V2RP-IP02-VC-13**: Bulk delete support
- [x] **V2RP-IP02-VC-14**: Result dialog modal
- [x] **V2RP-IP02-VC-15**: Navigation links (Back, Jobs, Crawler, etc.)
- [x] **V2RP-IP02-VC-16**: Row styling for failed reports
- [x] **V2RP-IP02-VC-17**: Empty state message
- [x] **V2RP-IP02-VC-18**: Timestamp formatting
- [x] **V2RP-IP02-VC-19**: Create Demo Reports streaming endpoint

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

## Cross-Router Integration

### Sites Router Integration

The sites router uses the reports endpoint to display security scan results:

1. **Storage**: `site.json` stores `last_security_scan_report_id` after each security scan
2. **UI Links**: Sites table Security column renders:
   - "View Results" -> `/v2/reports/get?report_id=...&format=html`
   - "Download Zip" -> `/v2/reports/download?report_id=...`

**Implementation in sites.py:**
```javascript
function renderSecurityCell(item) {
  const summary = item.security_scan_result || '-';
  const reportId = item.last_security_scan_report_id || '';
  if (!reportId) return summary;
  const viewUrl = '/v2/reports/get?report_id=' + encodeURIComponent(reportId) + '&format=html';
  const downloadUrl = '/v2/reports/download?report_id=' + encodeURIComponent(reportId);
  return summary + '<br><a href="' + viewUrl + '">View Results</a> | <a href="' + downloadUrl + '">Download Zip</a>';
}
```

## Document History

**[2026-02-04 07:37]**
- Changed: Title to `# IMPL: V2 Reports Router` per template
- Changed: `Plan ID` to `Doc ID` per template
- Added: MUST-NOT-FORGET section with critical patterns
- Changed: Implementation Status - all items now marked DONE
- Added: `/v2/reports/create_demo_reports` endpoint section
- Fixed: JavaScript Functions section - removed contradictory code, references actual impl
- Changed: Verification checklist - all items checked
- Added: VC-19 for create_demo_reports endpoint

**[2026-02-03 23:15]**
- Added: Cross-Router Integration section documenting sites router usage

**[2024-12-30 10:50]**
- Added: Plan ID V2RP-IP02 to header block
- Changed: Spec Compliance Checklist now uses IDs V2RP-IP02-VC-01 to VC-18 (18 items)
- Changed: Test Scenarios now use IDs V2RP-IP02-TST-01 to TST-26 (26 items)
