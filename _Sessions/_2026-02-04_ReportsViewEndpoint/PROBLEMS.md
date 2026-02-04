# Session Problems

**Doc ID**: 2026-02-04_ReportsViewEndpoint-PROBLEMS

## Open

### RPTV-PR-001: Add /reports/view endpoint

- **Status**: Open
- **Type**: Feature
- **Description**: Create new endpoint `/v2/reports/view` with split-panel UI (tree + table)
- **Acceptance**:
  - Endpoint accepts `report_id` param (required)
  - `format=ui` shows viewer UI
  - Bare GET shows self-documentation
  - Left panel: file tree from `report.json.files[]`
  - Right panel: CSV table loaded via `/v2/reports/file`

### RPTV-PR-002: Add View button to reports UI

- **Status**: Open
- **Type**: Feature
- **Description**: Add [View] button to reports list UI that links to `/reports/view` endpoint
- **Acceptance**:
  - Button appears in Actions column for each report
  - Uses declarative pattern (data-url)
  - Links to `/v2/reports/view?report_id={report_id}&format=ui`

### RPTV-PR-003: Implement tree view component

- **Status**: Open
- **Type**: Feature
- **Description**: Build hierarchical tree from flat `files[]` array
- **Acceptance**:
  - Collapsible folder nodes
  - CSV files clickable, non-CSV disabled (greyed)
  - Auto-select first CSV on load

### RPTV-PR-004: Implement horizontal resizable divider

- **Status**: Open
- **Type**: Feature
- **Description**: Drag handle between tree and table panels
- **Acceptance**:
  - Same look/feel as console vertical resize
  - Persists width during session

## Resolved

(None yet)

## Deferred

(None yet)
