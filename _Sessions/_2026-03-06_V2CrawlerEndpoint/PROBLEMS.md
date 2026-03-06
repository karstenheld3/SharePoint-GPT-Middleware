# Session Problems

**Doc ID**: 2026-03-06_V2CrawlerEndpoint-PROBLEMS

## Open

### V2CR-PR-001: SharePoint List Crawling Needs Improvement

- **Status**: Open (Analysis Complete)
- **Description**: SharePoint list crawling must capture more information in a human-readable format
- **Goal**: Maximize captured information while maintaining readability
- **Root Cause**: `get_list_items_as_sharepoint_files()` discards all column data - only keeps ID, Title, Modified
- **Solution**: See `_INFO_SHAREPOINT_LIST_COLUMN_TYPES.md [V2CR-IN01]` for conversion specs
- **Next**: Implement Python conversion function and update crawler flow

### V2CR-PR-002: List Crawl files_map.csv Missing CSV File Entry

- **Status**: Open
- **Description**: After crawling lists, files_map.csv should contain entries for both CSV and MD files, but currently only MD file is listed
- **Expected**: files_map.csv contains two entries per list: `[list_name].csv` and `[list_name].md`
- **Actual**: files_map.csv contains only MD file entry
- **Impact**: CSV backup file exists but is not tracked in files_map

### V2CR-PR-005: Reports Not Visible on Azure After Crawl

- **Status**: Resolved
- **Description**: After running crawl on Azure, reports not showing in /v2/reports?format=ui
- **Root Cause**: `common_report_functions_v2.py` used `config.LOCAL_PERSISTENT_STORAGE_PATH` directly, but on Azure the path comes from `request.app.state.system_info.PERSISTENT_STORAGE_PATH`
- **Solution**: Added `storage_path` parameter to all report functions, updated reports.py to pass `get_persistent_storage_path(request)`
- **Files Modified**: `common_report_functions_v2.py`, `reports.py`

### V2CR-PR-004: Domain Crawler Closes Dialog and Console After Completion

- **Status**: Resolved
- **Description**: When running domain crawler from Domains UI, the result dialog and console close automatically after crawl completes
- **Expected**: Dialog stays open with results, console remains visible
- **Actual**: Both close automatically, user cannot review results
- **Root Cause**: `startCrawl()` used `reloadOnFinish: true, showResult: 'toast'`
- **Solution**: Changed to `reloadOnFinish: false, showResult: 'modal'` in domains.py:485
- **Related**: V2FX-PR-003 (same pattern in selftest buttons)

### V2CR-PR-003: Crawler Selftest Needs List Field Type Coverage

- **Status**: Open
- **Description**: Crawler selftest lacks comprehensive test cases for list field type conversions
- **Required Test Data**:
  - Lists with all supported user field types
  - All cases of user data: empty fields, single values, multi-value (1 item vs many items)
- **Verification Required**:
  - All values exported correctly?
  - Correct format per field type?
  - Correct number of fields in MD and CSV?
  - Correct order of fields (CSV: ID, Title, alphabetical, Created, Modified)?
  - Title first in Markdown body?

## Resolved

## Deferred
