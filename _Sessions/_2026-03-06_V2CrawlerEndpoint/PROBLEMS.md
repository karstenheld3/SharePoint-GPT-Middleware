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

## Resolved

## Deferred
