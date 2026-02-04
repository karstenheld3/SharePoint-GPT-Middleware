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

**RPTV-DD-02:** Tree data from report.json. Use `files[]` array from report metadata (fetched via `/v2/reports/get`). Each entry has `file_path` property.

**RPTV-DD-03:** Hierarchical tree. Build folder structure from flat file paths. Folders are collapsible nodes.

**RPTV-DD-04:** CSV-only interaction. Show all files in tree but disable (grey out) non-CSV files. Only `.csv` files are clickable.

**RPTV-DD-05:** Horizontal resizable divider. Same look/feel as console's vertical resize handle. Drag to adjust tree/table width ratio.

**RPTV-DD-06:** Auto-select first CSV. On page load, find and select the first CSV file alphabetically by path, display its contents immediately.

**RPTV-DD-07:** Self-documentation. Bare GET (no params) returns endpoint documentation per DD-E001.

## Functional Requirements

**RPTV-FR-01:** Display file tree from report archive contents
**RPTV-FR-02:** Load and display CSV file content as HTML table
**RPTV-FR-03:** Resize tree/table panels via drag handle
**RPTV-FR-04:** Navigate back to reports list
**RPTV-FR-05:** Show report metadata header (title, type, created, status)

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
| [Back to Reports]                              Report Viewer     |
+------------------------------------------------------------------+
| Title: "AiSearchTest01 incremental crawl"  Type: crawl           |
| Created: 2026-02-04 07:09:16 UTC            Status: OK           |
+------------------------------------------------------------------+
|                    |                                             |
|  [File Tree]       |  [CSV Table]                                |
|                    |                                             |
|  > 01_files/       |  | Col1 | Col2 | Col3 | ...               |
|    > DocLib01/     |  |------|------|------|                    |
|      sharepoint_   |  | val  | val  | val  |                    |
|      files_map.csv |  | val  | val  | val  |                    |
|      vectorstore_  |  | ...  | ...  | ...  |                    |
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

```css
/* Layout */
.viewer-container {
  display: flex;
  height: calc(100vh - 120px);
}

.tree-panel {
  width: 280px;
  min-width: 150px;
  overflow: auto;
  border-right: 1px solid #ddd;
  background: #fafafa;
}

.resize-handle {
  width: 5px;
  background: #ddd;
  cursor: col-resize;
}

.resize-handle:hover {
  background: #bbb;
}

.table-panel {
  flex: 1;
  min-width: 300px;
  overflow: auto;
  padding: 8px;
}

/* Tree */
.tree-node {
  padding: 2px 0;
}

.tree-node.folder > .folder-toggle {
  display: inline-block;
  width: 16px;
  cursor: pointer;
}

.tree-node.file {
  padding-left: 16px;
  cursor: pointer;
}

.tree-node.file:hover {
  background: #e8f4fc;
}

.tree-node.file.selected {
  background: #cce5ff;
}

.tree-node.file.disabled {
  color: #999;
  cursor: not-allowed;
}

.tree-node.file.disabled:hover {
  background: transparent;
}

.tree-children {
  padding-left: 16px;
}

/* Table */
.csv-table-container {
  overflow: auto;
  max-height: 100%;
}

.csv-table {
  border-collapse: collapse;
  font-size: 12px;
  white-space: nowrap;
}

.csv-table th, .csv-table td {
  border: 1px solid #ddd;
  padding: 4px 8px;
  text-align: left;
}

.csv-table th {
  background: #f5f5f5;
  font-weight: 600;
  position: sticky;
  top: 0;
}

.csv-table tr:hover {
  background: #f9f9f9;
}
```

## JavaScript Functions

### Page Initialization

```javascript
let reportId = null;
let reportData = null;

document.addEventListener('DOMContentLoaded', async () => {
  reportId = getReportIdFromUrl();
  await loadReportMetadata();
  renderFileTree();
  selectFirstCsvFile();
  initPanelResize();
});
```

### Core Functions

- `loadReportMetadata()` - Fetch report.json via `/v2/reports/get`
- `buildTreeStructure(files)` - Convert flat files[] to nested tree
- `renderFileTree()` - Generate tree HTML from structure
- `toggleFolder(path)` - Expand/collapse folder node
- `selectFile(path)` - Highlight file, load if CSV
- `loadCsvFile(path)` - Fetch CSV via `/v2/reports/file`
- `parseCsv(text)` - Parse CSV text to array of arrays
- `renderCsvTable(data)` - Generate table HTML
- `selectFirstCsvFile()` - Find and select first CSV alphabetically
- `initPanelResize()` - Set up drag handle listeners

## Document History

**[2026-02-04 08:20]**
- Initial specification created
