# Test Summary Report

**Generated**: 2024-12-30
**Overall Result**: FAIL
**Total Files**: 2
**Passed**: 1
**Failed**: 1

## 1. Summary

- **Overall**: FAIL - 1 file(s) failed
- **Files tested**: 2
- **Files passed**: 1
- **Files failed**: 1
- **Total tests**: 102
- **Tests passed**: 100
- **Tests failed**: 2
- **Tests skipped**: 2

### Passed Files

- `src/routers_v2/common_report_functions_v2_test.py` - 68 tests passed

### Failed Files

- `src/routers_v2/common_sharepoint_functions_v2_test.py` - 32 passed, 2 failed, 2 skipped

## 2. Proposed Action Items

Based on test failures, suggest fixes:

- **common_sharepoint_functions_v2_test.py**: `try_get_document_library()` failed due to network connection reset error (ConnectionResetError 10054) -> This appears to be a transient network/SharePoint connectivity issue. The remote SharePoint server forcibly closed the connection. Suggested actions:
  1. Retry the test to see if it's intermittent
  2. Check SharePoint service status/availability
  3. Consider adding retry logic with exponential backoff in `try_get_document_library()` for production resilience
  4. Verify the SharePoint site `/sites/AiSearchTest01/Shared Documents` is accessible

## 3. Detailed Test Report

### common_report_functions_v2_test.py

**Result**: PASS
**Tests**: 68 passed, 0 failed

**Output**:
```
============================================================
common_report_functions_v2.py - Test Suite
============================================================

Test directory: C:\Users\User\AppData\Local\Temp\report_test_fli63hnp

============================================================
Type/Folder Conversion
============================================================
  OK: crawl -> crawls
  OK: site_scan -> site_scans
  OK: custom -> customs
  OK: crawls -> crawl
  OK: site_scans -> site_scan
  OK: customs -> custom

============================================================
create_report()
============================================================
  OK: C1: Valid inputs returns report_id
  OK: C1: Archive file created
  OK: C1: report_id in metadata
  OK: C1: created_utc in metadata
  OK: C1: title preserved
  OK: C1: files inventory exists
  OK: C1: files inventory has 2 items
  OK: C2: Empty files - only report.json
  OK: C3: Nested paths preserved
  OK: C4: Flattened - file1.csv at root
  OK: C4: Flattened - file2.csv at root
  OK: C4: Flattened - no nested paths
  OK: C6: Unknown type - folder created
  OK: C8: Folder doesn't exist before
  OK: C8: Folder auto-created
  OK: C11: Binary content preserved
  OK: C12: Empty file exists
  OK: C12: Empty file is 0 bytes

============================================================
list_reports()
============================================================
  OK: L1: No reports - returns []
  OK: L2: All reports returned
  OK: L2: Sorted newest first
  OK: L3: Filter crawl - 2 results
  OK: L3: Filter site_scan - 1 result
  OK: L4: Non-existent type - returns []
  OK: L5: Corrupt zip skipped
  OK: L6: Zip without report.json skipped
  OK: L7: Invalid JSON skipped

============================================================
get_report_metadata()
============================================================
  OK: M1: Valid report_id returns dict
  OK: M1: Title correct
  OK: M2: Non-existent returns None
  OK: M3: Invalid format returns None
  OK: M4: Corrupt zip returns None
  OK: M5: Missing report.json returns None

============================================================
get_report_file()
============================================================
  OK: F1: Valid file returns bytes
  OK: F2: Non-existent file returns None
  OK: F3: Non-existent report returns None
  OK: F4: report.json readable
  OK: F4: report.json valid JSON
  OK: F5: Binary file content correct

============================================================
delete_report()
============================================================
  OK: D1: Report exists before delete
  OK: D1: Delete returns metadata
  OK: D1: Returned title correct
  OK: D1: Archive file removed
  OK: D2: Non-existent returns None

============================================================
dry_run tests
============================================================
  OK: DR1: create_report dry_run returns report_id
  OK: DR1: create_report dry_run does NOT create file
  OK: DR2: Report created for delete test
  OK: DR2: delete_report dry_run returns metadata
  OK: DR2: delete_report dry_run title correct
  OK: DR2: delete_report dry_run does NOT delete file
  OK: DR2: Cleanup - file now deleted

============================================================
get_report_archive_path()
============================================================
  OK: P1: Returns Path object
  OK: P1: Path is correct
  OK: P2: Non-existent returns None
  OK: P3: Invalid format returns None

============================================================
Long path support (Windows)
============================================================
  OK: LP1: create_report with long path succeeds
  OK: LP2: get_report_metadata with long path works
  OK: LP2: Title correct
  OK: LP3: get_report_file with long path works
  OK: LP4: list_reports finds long path report
  OK: LP5: delete_report with long path works
  OK: LP6: Report actually deleted

============================================================
SUMMARY: 68/68 tests passed
============================================================

Cleaned up: C:\Users\User\AppData\Local\Temp\report_test_fli63hnp
```

### common_sharepoint_functions_v2_test.py

**Result**: FAIL
**Tests**: 32 passed, 2 failed, 2 skipped

**Output**:
```
======================================================================
common_sharepoint_functions_v2.py Test Suite
======================================================================

Test domain: AiSearchTest01
Persistent storage: E:\dev\RAGFiles2\AzureOpenAiProject

Credentials from environment variables:
  CRAWLER_CLIENT_ID: 6e2f7cac...
  CRAWLER_TENANT_ID: 6722551d...
  CRAWLER_CLIENT_CERTIFICATE_PFX_FILE: SharePoint-GPT-Crawler.pfx
  Cert full path: E:\dev\RAGFiles2\AzureOpenAiProject\SharePoint-GPT-Crawler.pfx
    OK: Certificate file exists.
Cleared existing test output directory: E:\dev\RAGFiles2\AzureOpenAiProject\crawler\_common_sharepoint_functions_v2_test
Test output directory: E:\dev\RAGFiles2\AzureOpenAiProject\crawler\_common_sharepoint_functions_v2_test
======================================================================
[ 1 / 12 ] SharePointFile Dataclass
  OK: Instance created
  OK: sharepoint_listitem_id correct
  OK: filename correct
  OK: file_type correct
  OK: file_size correct
  OK: asdict works
  OK: asdict has 10 keys
[ 2 / 12 ] get_or_create_pem_from_pfx()
  OK: Returns pem_file path
  OK: Returns thumbprint
  OK: PEM file created
  OK: Idempotent - same pem_file
  OK: Idempotent - same thumbprint
[ 3 / 12 ] Load Domain Configuration
  START: load_domain()...
  Loading domain 'AiSearchTest01' from 'E:\dev\RAGFiles2\AzureOpenAiProject\domains\AiSearchTest01\domain.json'
  Domain loaded: domain_id='AiSearchTest01'
  END: load_domain() (20 ms).
  OK: Domain loaded
    Domain: 'AiSearchTest01'
    3 file sources.
    1 list source.
    1 site page source.
  Using file source: source_id='SharedDocuments'
    Site: site_url='https://whizzyapps.sharepoint.com/sites/AiSearchTest01'
    Library: sharepoint_url_part='/Shared Documents'
[ 4 / 12 ] connect_to_site_using_client_id_and_certificate()
  OK: Context created
  OK: Connection works - web title retrieved
    Connected to: 'AiSearchTest01'
[ 5 / 12 ] try_get_document_library()
  FAIL: Valid library - returns library -> Failed to get document library at '/sites/AiSearchTest01/Shared Documents': ('Connection aborted.', ConnectionResetError(10054, 'An existing connection was forcibly closed by the remote host', None, 10054, None))
  FAIL: Valid library - no error
  OK: Invalid library - returns None
  OK: Invalid library - returns error
[ 6 / 12 ] get_document_library_files()
  SKIP: Get files test -> No context or library available
[ 7 / 12 ] download_file_from_sharepoint()
  SKIP: Download test -> No context or files available
[ 8 / 12 ] get_list_items()
  START: get_list_items()...
  6 list items retrieved so far...
  6 list items retrieved.
  END: get_list_items() (5.0 secs).
  OK: Returns list
    6 list items retrieved.
  OK: Items are dictionaries
    First item keys: ['ParentList', 'FileSystemObjectType', 'Id', 'ServerRedirectedEmbedUri', 'ServerRedirectedEmbedUrl']...
[ 9 / 12 ] export_list_to_csv()
  START: export_list_to_csv()...
    START: get_list_items()...
    6 list items retrieved so far...
    6 list items retrieved.
    END: get_list_items() (13.0 secs).
  6 items exported to 'E:\dev\RAGFiles2\AzureOpenAiProject\crawler\_common_sharepoint_functions_v2_test\02_lists\Security training catalog.csv'.
  END: export_list_to_csv() (13.0 secs).
  OK: Export succeeds
  OK: CSV file created
  OK: CSV has header
    7 CSV lines.
  START: export_list_to_csv()...
    START: get_list_items()...
    6 list items retrieved so far...
    6 list items retrieved.
    END: get_list_items() (3.7 secs).
  END: export_list_to_csv() (3.7 secs).
  OK: dry_run succeeds
  OK: dry_run does not create file
[ 10 / 12 ] get_site_pages()
  START: get_site_pages()...
    START: get_document_library_files()...
    Library: 'Site Pages' (ID=a2e96c6a-66f5-44ea-9e43-4aa493f62833)
    1 item retrieved so far...
    1 file retrieved.
    1 file converted to SharePointFile objects.
    END: get_document_library_files() (3.0 secs).
  END: get_site_pages() (9.4 secs).
  OK: Returns list
    1 site page retrieved.
  OK: Pages are SharePointFile
    First page: 'Home.aspx'
  START: get_site_pages()...
    START: get_document_library_files()...
    Library: 'Site Pages' (ID=a2e96c6a-66f5-44ea-9e43-4aa493f62833)
    END: get_document_library_files() (561 ms).
  END: get_site_pages() (3.6 secs).
  OK: dry_run returns empty list
[ 11 / 12 ] download_site_page_html()
  START: download_site_page_html()...
  Site page downloaded to 'E:\dev\RAGFiles2\AzureOpenAiProject\crawler\_common_sharepoint_functions_v2_test\03_sitepages\Home.aspx'.
  END: download_site_page_html() (35.3 secs).
  OK: Download succeeds
  OK: File exists
  OK: File has content
  START: download_site_page_html()...
  END: download_site_page_html() (6.8 secs).
  OK: dry_run succeeds
  OK: dry_run does not create file

Cleanup
======================================================================
  Keeping test output directory: E:\dev\RAGFiles2\AzureOpenAiProject\crawler\_common_sharepoint_functions_v2_test

TEST SUMMARY
======================================================================
  Sections: 11 / 12
  Tests:    34 total, 32 passed, 2 failed, 2 skipped

Failed tests (2):
  - Valid library - returns library -> Failed to get document library at '/sites/AiSearchTest01/Shared Documents': ('Connection aborted.', ConnectionResetError(10054, 'An existing connection was forcibly closed by the remote host', None, 10054, None))
  - Valid library - no error

Skipped tests (2):
  - Get files test -> No context or library available
  - Download test -> No context or files available
======================================================================

RESULT: FAIL (2 test(s) failed)
```
