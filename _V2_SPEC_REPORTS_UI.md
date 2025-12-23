# V2 Reports UI Specification

**Goal**: Provide UI for viewing, downloading, and managing report archives
**Target file**: `/src/routers_v2/reports.py`

**Depends on:**
- `_V2_SPEC_REPORTS.md` for report domain objects and archive structure
- `_V2_SPEC_ROUTERS.md` for endpoint design and JSON result format
- `_V2_SPEC_COMMON_UI_FUNCTIONS.md` for UI generation functions

## Table of Contents

1. Overview
2. Scenario
3. User Actions
4. UX Design
5. Key Mechanisms
6. Action Flow
7. Implementation Notes

## Overview

The `/v2/reports?format=ui` endpoint provides management interface for report archives. Each archive contains operation results with metadata and report-specific files.

**Key characteristics:**
- Single-page UI with reports table
- Console panel hidden by default (no streaming operations)
- Bulk delete support via checkboxes
- View action opens modal with report.json content
- Result column shows OK/FAIL status (same pattern as Jobs UI)

## Scenario

**Real-world problem:**
Users need to review historical operation results (crawls, site scans) for auditing and debugging. They may need to download archives or clean up old reports.

**What we don't want:**
- Complex filtering or search (type filter only)
- Inline editing of reports
- Automatic cleanup (user controls deletion)
- Elaborate UI components

## User Actions

- **Result** - Click [Result] button -> Open modal dialog with report.json content
- **Download** - Click [Download] button -> Download report archive as ZIP
- **Delete** - Click [Delete] button -> Delete single report
- **Bulk Delete** - Select rows + click [Delete (n)] -> Delete multiple reports
- **Reload** - Click [Reload] link -> Reload reports table

## UX Design

### Main Layout

```
+------------------------------------------------------------------------------------------------------------------+
| Reports (12) [Reload]                                                                                            |
|                                                                                                                  |
| Back to Main Page                                                                                                |
|                                                                                                                  |
| [Delete (0)]                                                                                                     |
|                                                                                                                  |
| +---+-----------+------------------------------+---------------------+--------+--------------------------------+ |
| |   | Type      | Title                        | Created             | Result | Actions                        | |
| +---+-----------+------------------------------+---------------------+--------+--------------------------------+ |
| |[ ]| crawl     | TEST01 full crawl            | 2024-01-15 14:30:00 | OK     | [Result] [Download] [Delete]   | |
| |[ ]| crawl     | TEST01 files incremental     | 2024-01-15 14:26:30 | FAIL   | [Result] [Download] [Delete]   | |
| |[ ]| site_scan | '/sites/HR' Security Scan    | 2025-03-12 10:15:00 | OK     | [Result] [Download] [Delete]   | |
| +---+-----------+------------------------------+---------------------+--------+--------------------------------+ |
|                                                                                                                  |
| +----------------------------------------------------------------------------------------------------------------+
| | [Resize Handle - Draggable]                                                                           (hidden) |
| | Console Output                                                                                         [Clear] |
| +----------------------------------------------------------------------------------------------------------------+
|                                                                                                                  |
+------------------------------------------------------------------------------------------------------------------+
```

### Table Columns

- **Checkbox** - For bulk selection
- **Type** - `report.type`, report type: `crawl`, `site_scan`
- **Title** - `report.title`, human readable title
- **Created** - `report.created_utc`, format: `YYYY-MM-DD HH:MM:SS`
- **Result** - `report.ok`: `-` (null), `OK` (true), `FAIL` (false)
- **Actions** - [Result] [Download] [Delete]

### Result Column Logic

Same pattern as Jobs UI:
- `-` if `report.ok` is null/undefined
- `OK` if `report.ok === true`
- `FAIL` if `report.ok === false`

### Row Styling

Rows with `ok === false` get class `row-cancel-or-fail`:
```css
tr.row-cancel-or-fail { color: #b03030; }
```

### Toolbar

- **Delete (0)** - No selection -> Disabled
- **Delete (n)** - n items selected -> Enabled, triggers bulk delete

### Navigation Links

- **Back to Main Page** - `/` root endpoint
- **Jobs** - `/v2/jobs?format=ui`
- **Crawler** - `/v2/crawler?format=ui`

### Result Dialog (Modal)

Shows report.json content in formatted view (same pattern as Jobs UI Result dialog):

```
+---------------------------------------------------------------+
| Result (OK) - 'TEST01 full crawl'                        [x]  |
+---------------------------------------------------------------+
| Report ID:  crawls/2024-01-15_14-25-00_TEST01_all_full        |
| Type:       crawl                                             |
| Created:    2024-01-15 14:30:00                               |
|                                                               |
| +-----------------------------------------------------------+ |
| | {                                                         | |
| |   "report_id": "crawls/2024-01-15...",                    | |
| |   "title": "TEST01 full crawl",                           | |
| |   "type": "crawl",                                        | |
| |   ...                                                     | |
| | }                                                         | |
| +-----------------------------------------------------------+ |
|                                                               |
|                                                         [OK]  |
+---------------------------------------------------------------+
```

### Empty State

When no reports exist:
```html
<tr><td colspan="6" class="empty-state">No reports found</td></tr>
```

## Key Mechanisms

### Console Panel (Hidden)

- Hidden by default (no streaming operations in this UI)
- Can be shown manually if needed for future features
- Same resize/clear behavior as other UIs

### Timestamp Formatting

Convert `created_utc` to local timezone with fixed format:
```javascript
function formatTimestamp(ts) {
  if (!ts) return '-';
  const date = new Date(ts);
  const pad = (n) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}
```

### Bulk Selection

- Header checkbox toggles all rows
- Individual checkboxes toggle single rows
- Toolbar button updates count: `Delete (<span id="selected-count">0</span>)`
- Count of 0 disables button

### Download Action

Direct link to download endpoint:
```javascript
function downloadReport(reportId) {
  window.location = `/v2/reports/download?report_id=${encodeURIComponent(reportId)}`;
}
```

## Action Flow

### View Report Result

```
User clicks [Result]
  -> showReportResult(reportId)
  -> GET /v2/reports/get?report_id={id}&format=json
  -> showResultModal(data)
```

### Download Report

```
User clicks [Download]
  -> window.location = `/v2/reports/download?report_id={id}`
  -> Browser downloads ZIP file
```

### Delete Single Report

```
User clicks [Delete]
  -> DELETE /v2/reports/delete?report_id={id}
  -> showToast("Report deleted", "success")
  -> Remove row from table
```

### Bulk Delete Reports

```
User selects multiple rows
  -> Toolbar shows "Delete (n)"
User clicks [Delete (n)]
  -> For each: DELETE /v2/reports/delete?report_id={id}
  -> showToast("n reports deleted", "success") or warning if partial fail
  -> reloadReports()
```

## Implementation Notes

### Page Load

1. Server returns HTML page with empty `<tbody id="items-tbody">`
2. On `DOMContentLoaded`, JavaScript fetches `/v2/reports?format=json`
3. JavaScript renders report rows into tbody

### Router-Specific JavaScript

```javascript
// State
const reportsState = new Map();

// Page init - use reloadItems() name for common UI compatibility
document.addEventListener('DOMContentLoaded', () => {
  reloadItems();
  initConsoleResize();
});

async function reloadItems() { /* fetch and render */ }
function renderAllReports() { /* render all rows */ }
function renderReportRow(report) { /* USE STRING CONCATENATION, NOT TEMPLATE LITERALS */ }
async function showReportResult(reportId) { /* direct modal body manipulation */ }
function downloadReport(btn) { /* declarative: btn.dataset.url */ }
async function deleteReport(reportId, title) { /* with confirm() */ }
async function bulkDelete() { /* with confirm() */ }
function updateSelectedCount() { /* MUST reset select-all checkbox */ }
function toggleSelectAll() { ... }
function getSelectedReportIds() { /* use .item-checkbox, data-item-id */ }
function formatResult(ok) { /* -, OK, FAIL */ }
```

### Dependencies

- `common_ui_functions_v2.py` for page generation, table, modal, console, toast
- Archive storage path from `hardcoded_config.py`

### CSS Classes

Uses existing classes from `/static/css/routers_v2.css`:
- `.row-cancel-or-fail` for failed reports
- `.empty-state` for empty table message
- Modal, toast, console classes from common UI
