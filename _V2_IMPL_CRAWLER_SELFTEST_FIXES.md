# Crawler Selftest Fixes Tracking

**Goal**: Track fixes, progress and tried solutions for crawler selftest issues
**Related spec**: `_V2_IMPL_CRAWLER_SELFTEST_B.md`

## Current Issues

### Issue 1: Site Pages Creation (403 Access Denied)

**Status**: INVESTIGATING

**Problem**: Cannot create site pages using app-only authentication (certificate-based). All upload methods return 403 Access Denied.

**Error**:
```
'-2147024891, System.UnauthorizedAccessException', 'Access denied.'
403 Client Error: Forbidden for url: .../getFolderByServerRelativeUrl('SitePages')/Files/add(...)
```

**Tried Solutions**:

1. **Method: folder.upload_file()** - FAILED
   ```python
   folder = ctx.web.get_folder_by_server_relative_url("SitePages")
   folder.upload_file(page_name, content).execute_query()
   ```
   Result: 403 Access Denied

2. **Method: folder.upload_file() with full path** - FAILED
   ```python
   folder = ctx.web.get_folder_by_server_relative_url("/sites/AiSearchTest01/SitePages")
   folder.upload_file(page_name, content).execute_query()
   ```
   Result: 403 Access Denied

3. **Method: list.root_folder.upload_file()** - FAILED
   ```python
   site_pages_list = ctx.web.lists.get_by_title("Site Pages")
   root_folder = site_pages_list.root_folder
   root_folder.upload_file(page_name, content).execute_query()
   ```
   Result: 403 Access Denied

4. **Method: list.add_item()** - FAILED
   ```python
   site_pages = ctx.web.lists.get_by_title("Site Pages")
   site_pages.add_item(item_data).execute_query()
   ```
   Result: 500 "To add an item to a document library, use SPFileCollection.Add()"

**Research Findings**:

1. **Microsoft Graph API** (`POST /sites/{site-id}/pages`)
   - Requires `Sites.ReadWrite.All` application permission
   - Creates modern site pages with full control over layout
   - More complex request body required
   - May work with app-only auth

2. **SharePoint REST API** (`/_api/sitepages/pages`)
   - `SavePageAsDraft` method to create/update pages
   - `/_api/SitePages/Pages(id)/CheckoutPage` to check out
   - `/_api/web/GetFileByServerRelativeUrl(...)/Publish()` to publish
   - May have same permission restrictions

3. **Template-based approach** (from SharePointCass)
   - Copy existing template: `/_api/web/GetFileByServerRelativePath('...Template.aspx')/copyTo('...NewPage.aspx')`
   - Requires a template page to exist first

4. **Key insight**: Site Pages library has special restrictions for app-only auth
   - Even with FullControl, some operations require user context
   - This is a SharePoint security feature, not a permission issue

**Additional Methods Tested (2026-01-03 14:00)**:

5. **GET /_api/sitepages/pages** - SUCCESS (200)
   - Can list existing pages
   - Returns empty array (no pages exist)

6. **POST /_api/sitepages/pages** - FAILED (400 Bad Request)
   ```python
   body = {"@odata.type": "#SP.Publishing.SitePage", "Name": "test.aspx", "Title": "Test", "PageLayoutType": "Article"}
   ```

7. **POST /_api/sitepages/pages/AddPage** - FAILED (404 Not Found)
8. **POST /_api/sitepages/pages/CreatePage** - FAILED (404 Not Found)
9. **POST /_api/SitePages/Pages/AddTemplateFile** - FAILED (404 Not Found)

**Conclusion (SharePoint REST API)**: Site Pages creation is blocked for app-only authentication via SharePoint REST API.

**Microsoft Graph API Testing (2026-01-03 14:07)**:

10. **GET Graph token with certificate** - SUCCESS
    - MSAL with certificate auth works for Graph API
    - Token acquired successfully

11. **GET /sites/{hostname}:{path}** - SUCCESS
    - Site ID retrieved: `whizzyapps.sharepoint.com,4a728323-...`

12. **POST /sites/{site-id}/pages** - FAILED (403)
    - Error: "Caller does not have required permissions for this API"
    - Root cause: App has SharePoint permissions but lacks Graph API permissions

**Required for Graph Site Pages API**:
- Add permission: Microsoft Graph → Application → `Sites.ReadWrite.All` (or `Sites.Selected`)
- Grant admin consent
- If using Sites.Selected: Grant site-specific permission via `/sites/{siteId}/permissions`

**Current Status**: 
- SharePoint REST API: Cannot create site pages (security restriction)
- Microsoft Graph API: Would work but requires additional Azure AD app permissions

**Resolution (2026-01-03 14:10)**: Option B selected - skip site pages testing.

**Changes Made**:
1. Updated `_V2_IMPL_CRAWLER_SELFTEST.md`:
   - Removed site pages from SharePoint Artifacts section
   - Emptied sitepage_sources in Domain Configuration
   - Updated snapshot definitions to exclude sitepages
   - Removed site pages from Phase 3, 10, 11, 19 steps
   - Updated test count from 57 to ~45

2. Updated `crawler.py`:
   - Removed sitepages from SNAP_* constants
   - Emptied sitepage_sources in domain config
   - Removed site pages creation from Phase 3
   - Removed site pages deletion from Phase 2 (pre-cleanup) and Phase 19 (cleanup)
   - Added notes explaining why site pages are skipped

## Resolved Issues

### Issue: Library/List names with leading underscore

**Status**: RESOLVED

**Problem**: SharePoint doesn't allow leading underscore in library/list names

**Fix**: Changed constants:
- `SELFTEST_LIBRARY_URL`: `"/_SELFTEST_DOCS"` -> `"/SELFTEST_DOCS"`
- `SELFTEST_LIST_NAME`: `"_SELFTEST_LIST"` -> `"SELFTEST_LIST"`

### Issue: Logging numbers don't add up

**Status**: RESOLVED

**Problem**: Summary showed Tests run: 4, OK: 3, FAIL: 2, SKIP: 1 (doesn't add up)

**Root cause**: 
1. Exception handler incremented `fail_count` without incrementing `test_num`
2. Setup phases incorrectly used `check_ok()`/`check_fail()` instead of `log()`

**Fix**:
1. Removed `fail_count += 1` from exception handler
2. Changed summary to show: `{total} tests executed (of {TOTAL_TESTS} planned)`
3. Setup phases (2, 3, 4, 10) now use `log("  OK. ...")` instead of `check_ok()`

### Issue: List crawl not implemented

**Status**: RESOLVED

**Problem**: `step_download_source` had no handler for `list_sources`, causing "No sources configured" and 0 items downloaded.

**Fix**:
1. Added `get_list_items_as_sharepoint_files()` in `common_sharepoint_functions_v2.py`
2. Added `elif source_type == "list_sources":` handler in `step_download_source`
3. Added `_export_list_item_to_csv()` helper for list item download
4. Fixed `AttributeError: 'ListSource' object has no attribute 'sharepoint_url_part'` by using `filename` directly for lists

### Issue: Domain sources not saved

**Status**: RESOLVED

**Problem**: Selftest created domain but sources were empty because API expected `sources_json` string, not direct fields.

**Fix**: Wrapped sources in `json.dumps(sources)` and passed as `sources_json` field.

## Changelog

- 2026-01-03 14:38: All Phase 6 tests passing (8 OK, 0 FAIL, 4 SKIP)
- 2026-01-03 14:35: Fixed list crawl implementation
- 2026-01-03 14:21: Fixed domain sources_json format
- 2026-01-03 14:10: Skipped site pages (app-only auth blocked)
- 2026-01-03 13:55: Created fixes tracking file
- 2026-01-03 13:42: Fixed library/list names (removed leading underscore)
- 2026-01-03 13:35: Fixed logging numbers (summary now adds up correctly)
