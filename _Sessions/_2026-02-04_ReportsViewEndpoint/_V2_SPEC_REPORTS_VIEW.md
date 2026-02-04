# SPEC: V2 Reports View

**Doc ID**: RPTV-SP01
**Goal**: Provide a split-panel UI for viewing report archive contents with file tree and CSV table display
**Target file**: `/src/routers_v2/reports.py`

**Depends on:**
- `_V2_SPEC_REPORTS.md [V2RP-SP01]` for report structure and existing endpoints
- `_V2_SPEC_REPORTS_UI.md [V2RP-SP02]` for UI patterns
- `_V2_SPEC_COMMON_UI_FUNCTIONS.md [V2UI-SP01]` for common UI components

**Does not depend on:**
- Temp folder extraction (uses existing `/v2/reports/file` endpoint)

## MUST-NOT-FORGET

- Use existing `/v2/reports/get` to fetch report metadata including `files[]` array
- Use existing `/v2/reports/file` to load CSV content on demand
- Build tree from flat `files[]` array by parsing `file_path` components
- Non-CSV files visible but disabled (greyed out, not clickable)
- Auto-select first CSV file on page load
- Horizontal resizable divider same pattern as console vertical resize
- Always URL-encode `report_id` in client-side fetch URLs (contains `/`)

## Table of Contents

1. Scenario
2. Design Decisions
3. Functional Requirements
4. Implementation Guarantees
5. Endpoint Specification
6. UI Layout
7. Tree Component
8. Table Component
9. Resizable Divider
10. CSS Styles
11. JavaScript Functions

## Scenario

**Problem:** Users want to inspect report contents (CSV files) without downloading and extracting the ZIP archive manually. The existing "Result" button shows raw JSON metadata which is not user-friendly for viewing tabular data.

**Solution:** A dedicated view endpoint that displays:
- Left panel: hierarchical file tree of archive contents
- Right panel: table view of selected CSV file
- Horizontal resizable divider between panels

**What we don't want:**
- Server-side temp folder extraction (use existing endpoints)
- Complex file editing capabilities (read-only view)
- Support for non-CSV file viewing (future enhancement)
- Pagination for large CSV files (client handles reasonable sizes)

## Design Decisions

**RPTV-DD-01:** No temp extraction. Use existing `/v2/reports/file` endpoint to load CSV content on demand via client-side fetch.

**RPTV-DD-02:** Tree data from report.json. Server fetches metadata via `get_report_metadata()` and embeds `files[]` array in page. Client uses this embedded data (no additional fetch needed).

**RPTV-DD-03:** Hierarchical tree. Build folder structure from flat file paths. Folders are collapsible nodes.

**RPTV-DD-04:** CSV-only interaction. Show all files in tree but disable (grey out) non-CSV files. Only `.csv` files are clickable.

**RPTV-DD-05:** Horizontal resizable divider. Same look/feel as console's vertical resize handle. Drag to adjust tree/table width ratio.

**RPTV-DD-06:** Auto-select first CSV. On page load, find and select the first CSV file alphabetically by path, display its contents immediately.

**RPTV-DD-07:** Self-documentation. Bare GET (no params) returns endpoint documentation per DD-E001.

## Functional Requirements

**RPTV-FR-01: File Tree Display**
- Build hierarchical tree from `files[]` array
- Folders collapsible, CSV files clickable, non-CSV disabled

**RPTV-FR-02: CSV Table View**
- Load CSV via `/v2/reports/file` endpoint
- Parse comma-delimited with header row
- Display as HTML table with sticky headers
- Download button in table header to download current CSV file

**RPTV-FR-03: Resizable Panels**
- Horizontal drag handle between tree and table
- Min width: 150px tree, 300px table

**RPTV-FR-04: Navigation**
- Standard nav bar: Back to Main Page | Domains | Sites | Crawler | Jobs | Reports
- Report metadata header (title, type, created, status)

**RPTV-FR-05: Auto-Selection**
- Select first CSV file on page load
- Display its contents immediately

## Implementation Guarantees

**RPTV-IG-01:** Tree reflects actual archive contents from `files[]` array
**RPTV-IG-02:** CSV parsing handles standard comma-delimited format with header row
**RPTV-IG-03:** Non-CSV files cannot be selected (click disabled)
**RPTV-IG-04:** Panel width persists during browser session (not across page reloads)

## Endpoint Specification

### GET /v2/reports/view

View report archive contents with split-panel UI.

**Parameters:**
- `report_id` (required) - Report identifier (e.g., `crawls/2024-01-15_...`)
- `format=ui` (required) - Only UI format supported

**Behavior:**
- Bare GET (no params): Return self-documentation (plain text)
- Missing `report_id`: Return error JSON
- `format` not `ui`: Return error JSON ("Only format=ui supported")
- Valid request: Return HTML page with viewer UI

**Response (format=ui):** Full HTML page with:
- Navigation bar (back to reports)
- Report metadata header
- Split-panel layout (tree | table)
- Embedded CSS and JavaScript

**Error Response:**
```json
{"ok": false, "error": "Missing 'report_id' parameter.", "data": {}}
```

## UI Layout

```
+------------------------------------------------------------------+
| Report Viewer                                                    |
| Back to Main Page | Domains | Sites | Crawler | Jobs | Reports   |
+------------------------------------------------------------------+
| Title: "AiSearchTest01 incremental crawl"  Type: crawl           |
| Created: 2026-02-04 07:09:16 UTC            Status: OK           |
+------------------------------------------------------------------+
|                    |                                             |
|  [File Tree]       |  [CSV Table]                                |
|                    |                                             |
|  > 01_files/       |  | Col1 | Col2 | Col3 | ...                 |
|    > DocLib01/     |  |------|------|------|                     |
|      sharepoint_   |  | val  | val  | val  |                     |
|      files_map.csv |  | val  | val  | val  |                     |
|      vectorstore_  |  | ...  | ...  | ...  |                     |
|    > DocLib02/     |                                             |
|  > 02_lists/       |                                             |
|  v report.json     |                                             |
|                    |                                             |
+--------------------+---------------------------------------------+
                     ^
                     | Drag handle (horizontal resize)
```

## Tree Component

### Data Structure

Build tree from flat `files[]` array:

```javascript
// Input: files[] from report.json
[
  {"file_path": "01_files/DocLib01/sharepoint_map.csv", ...},
  {"file_path": "01_files/DocLib01/files_map.csv", ...},
  {"file_path": "report.json", ...}
]

// Output: nested tree structure
{
  "01_files": {
    "_isFolder": true,
    "DocLib01": {
      "_isFolder": true,
      "sharepoint_map.csv": {"_isFile": true, "path": "01_files/DocLib01/sharepoint_map.csv"},
      "files_map.csv": {"_isFile": true, "path": "01_files/DocLib01/files_map.csv"}
    }
  },
  "report.json": {"_isFile": true, "path": "report.json"}
}
```

### Tree Rendering

- Folders: Collapsible with `>` / `v` indicator
- CSV files: Clickable, normal text color
- Non-CSV files: Greyed out, cursor: not-allowed
- Selected file: Highlighted background
- Indentation: 16px per level

### Tree HTML Structure

```html
<div class="file-tree">
  <div class="tree-node folder expanded" data-path="01_files">
    <span class="folder-toggle">v</span>
    <span class="folder-name">01_files</span>
    <div class="tree-children">
      <div class="tree-node folder" data-path="01_files/DocLib01">
        <span class="folder-toggle">></span>
        <span class="folder-name">DocLib01</span>
        <div class="tree-children" style="display:none">
          <div class="tree-node file csv" data-path="01_files/DocLib01/sharepoint_map.csv">
            <span class="file-name">sharepoint_map.csv</span>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="tree-node file disabled" data-path="report.json">
    <span class="file-name">report.json</span>
  </div>
</div>
```

## Table Component

### CSV Loading

```javascript
async function loadCsvFile(filePath) {
  const url = `${routerPrefix}/reports/file?report_id=${encodeURIComponent(reportId)}&file_path=${encodeURIComponent(filePath)}&format=raw`;
  const response = await fetch(url);
  const csvText = await response.text();
  renderCsvTable(csvText);
}
```

**Error handling**: On fetch failure, display error message in table panel instead of CSV content.

### CSV Parsing

- Split by newlines, then by commas
- First row is header
- Handle quoted values with commas inside
- Escape HTML in cell values

### Table HTML Structure

```html
<div class="csv-table-container">
  <table class="csv-table">
    <thead>
      <tr>
        <th>Column1</th>
        <th>Column2</th>
        ...
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>value1</td>
        <td>value2</td>
        ...
      </tr>
    </tbody>
  </table>
</div>
```

## Resizable Divider

### Behavior

- Vertical bar between tree and table panels
- Mouse drag adjusts width ratio
- Minimum width: 150px for tree, 300px for table
- Cursor changes to `col-resize` on hover/drag

### Implementation Pattern

Reuse console resize pattern from `_V2_SPEC_COMMON_UI_FUNCTIONS.md`:

```javascript
let isResizing = false;
let startX, startTreeWidth;

resizeHandle.addEventListener('mousedown', (e) => {
  isResizing = true;
  startX = e.clientX;
  startTreeWidth = treePanel.offsetWidth;
  document.body.style.cursor = 'col-resize';
});

document.addEventListener('mousemove', (e) => {
  if (!isResizing) return;
  const delta = e.clientX - startX;
  const newWidth = Math.max(150, Math.min(startTreeWidth + delta, window.innerWidth - 300));
  treePanel.style.width = newWidth + 'px';
});

document.addEventListener('mouseup', () => {
  isResizing = false;
  document.body.style.cursor = '';
});
```

## CSS Styles

**Layout classes:**
- `.viewer-container` - Flex container, full viewport height minus header
- `.tree-panel` - Left panel, 280px default, min 150px, light gray background
- `.resize-handle` - 5px drag handle, darkens on hover, `col-resize` cursor
- `.table-panel` - Right panel, flex:1, min 300px, scrollable

**Tree classes:**
- `.tree-node.folder` - Collapsible folder with toggle indicator
- `.tree-node.file` - Clickable file, blue hover highlight
- `.tree-node.file.selected` - Light blue background
- `.tree-node.file.disabled` - Gray text, `not-allowed` cursor
- `.tree-children` - 16px left indent per level

**Table classes:**
- `.csv-table` - Collapsed borders, 12px font, nowrap
- `.csv-table th` - Sticky header, gray background
- `.csv-table tr:hover` - Light hover highlight

## JavaScript Functions

**Initialization:**
- `DOMContentLoaded` -> render tree, select first CSV, init resize

**Tree functions:**
- `buildTreeStructure(files)` - Convert flat `files[]` to nested object
- `renderFileTree()` - Generate tree HTML with folders and files
- `renderTreeNode(node, path)` - Recursive node rendering
- `toggleFolder(node)` - Expand/collapse folder children

**File functions:**
- `selectFile(element)` - Highlight and load CSV content
- `selectFirstCsvFile()` - Find first `.csv` node, call selectFile
- `loadCsvFile(filePath)` - Fetch via `/v2/reports/file`, call parseCsv
- `parseCsv(text)` - Handle quoted values, return array of arrays
- `renderCsvTable(data)` - Generate `<table>` HTML with thead/tbody

**Resize functions:**
- `initPanelResize()` - mousedown/mousemove/mouseup handlers for drag

**Utilities:**
- `escapeHtml(str)` - Escape `<`, `>`, `&`, `"`

## Document History

**[2026-02-04 08:35]**
- Added: URL encoding note to MUST-NOT-FORGET (RV-06)
- Changed: DD-02 clarified server embeds metadata (RV-04)
- Added: Error handling note to CSV Loading (RV-05)

**[2026-02-04 08:24]**
- Changed: Reduced CSS/JS sections to outlines per SPEC-CT-01, SPEC-CT-02
- Changed: FR format to use sub-bullets per SPEC-RQ-01

**[2026-02-04 08:20]**
- Initial specification created
