# Session Notes

**Doc ID**: 2026-02-04_ReportsViewEndpoint-NOTES

## Session Info

- **Started**: 2026-02-04
- **Goal**: Add `/reports/view` endpoint to view report contents with tabbed CSV viewer UI

## Current Phase

**Phase**: EXPLORE
**Workflow**: BUILD
**Assessment**: COMPLEXITY-MEDIUM (multiple files, UI work, follows existing patterns)

## User Prompt (Verbatim)

I want to extend the `/reports` endpoint with a `/reports/view` endpoint.
Params:
- report_id -> id of report
- format=ui -> no other format supported, without format -> self documentation

The goal is to add a new [View] button in the reports endpoint ui for each report. This button links to the view endpoint (via declarative pattern) with report id.

The view endpoint displays report contents with:
- Treeview of archive files on the left (horizontal resizable divider)
- Table view of selected CSV file on the right
- Uses existing `/v2/reports/file` endpoint to load CSV content (no temp extraction)

## Key Decisions

### DD-VIEW-01: No Temp Extraction

Use existing `/v2/reports/file` endpoint to load CSV content on demand via AJAX. No temp folder extraction needed.

### DD-VIEW-02: Tree Data Source

Use `files[]` array from `report.json` (fetched via `/v2/reports/get`). Contains `file_path` for each file in archive.

### DD-VIEW-03: Full Hierarchical Tree

Display full folder structure with collapsible nodes. Crawl reports have meaningful hierarchy (`01_files/`, `02_lists/`, etc.).

### DD-VIEW-04: Non-CSV Files Disabled

Show all files in tree but disable (grey out) non-CSV files. User sees full contents but can only click CSV files.

### DD-VIEW-05: Horizontal Resizable Divider

Tree on left, table on right. Horizontal drag handle between panels (same look/feel as console's vertical resize).

### DD-VIEW-06: Auto-Select First CSV

On page load, automatically select and display the first CSV file for immediate content display.

## Important Findings

### Existing Patterns

- Reports router: `@/src/routers_v2/reports.py`
- Helper functions: `@/src/routers_v2/common_report_functions_v2.py`
- UI generation: `generate_ui_page()` from `common_ui_functions_v2.py`
- Report archives stored in: `PERSISTENT_STORAGE_PATH/reports/[folder]/`
- Report ID format: `[folder]/[filename]` (e.g., `crawls/2024-01-15_14-25-00_TEST01_all_full`)
- Declarative button pattern in columns: `{"text": "...", "onclick": "..."}`

### Report Archive Structures

**Crawl reports** (hierarchical):
```
report.json
01_files/[source]/*.csv
02_lists/[source]/*.csv
03_sitepages/[source]/*.csv
```

**Site scan reports** (flat):
```
report.json
01_SiteContents.csv
02_SiteGroups.csv
...
```

## IMPORTANT: Cascade Agent Instructions

1. **Report Type Naming**: Use singular form for `report_type` parameter (see `!NOTES.md`)
2. **Dependencies**: Run `InstallAndCompileDependencies.bat` after adding new imports
3. **Self-documentation**: Bare GET returns docs (DD-E001 pattern)
4. **Delete returns full object**: Per DD-E017

## Files to Read on Session Load

- `docs/routers_v2/_V2_SPEC_ROUTERS.md` [ROUT-SP01] - Endpoint patterns, design decisions
- `docs/routers_v2/_V2_SPEC_REPORTS.md` [V2RP-SP01] - Reports specification
- `docs/routers_v2/_V2_SPEC_REPORTS_UI.md` [V2RP-SP02] - Reports UI specification
- `docs/routers_v2/_V2_SPEC_COMMON_UI_FUNCTIONS.md` [V2UI-SP01] - Common UI functions
- `docs/routers_v2/_V2_IMPL_REPORTS.md` [V2RP-IP02] - Reports implementation plan

## Workflows to Run on Resume

1. `/recap` - Analyze context and current status
2. `/continue` - Execute next items on plan
