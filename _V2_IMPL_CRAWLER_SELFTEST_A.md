# Crawler Selftest Implementation Plan (Option A)

**Goal**: Implement a self-contained crawler selftest that creates, modifies, and deletes SharePoint content to fully test all crawler functionality including incremental crawl scenarios.

**Target file**: `/src/routers_v2/crawler.py`

**Depends on:**
- `_V2_SPEC_CRAWLER.md` for crawler functionality
- `domains.py` selftest pattern for implementation style
- `CRAWLER_SELFTEST_SHAREPOINT_SITE` config parameter for target SharePoint site
- `common_map_file_functions_v2.py` for map file column definitions
- Office365-REST-Python-Client for SharePoint write operations

## Table of Contents

1. Overview
2. Scenario
3. Configuration
4. Test Phases
5. SharePoint Setup Operations
6. Domain Configuration
7. Test Cases by Phase
8. Implementation Details
9. Edge Cases
10. Implementation Verification Checklist

## Scenario

**Problem:** Testing incremental crawl requires controlled SharePoint content changes. Manual setup is error-prone and doesn't cover edge cases like file deletion, rename, or content modification.

**Solution:** Selftest creates its own temporary SharePoint artifacts (document library, list, site pages), runs full crawl tests, modifies content, tests incremental crawl, then cleans up everything.

**What we don't want:**
- Tests that depend on pre-existing SharePoint content
- Tests that leave orphan artifacts in SharePoint or vector store
- Missing edge cases for incremental crawl (add/modify/delete/rename)
- Flaky tests due to SharePoint API timing issues
- Tests that skip filter validation

## Overview

The selftest is **fully self-contained**:
1. Creates temporary SharePoint artifacts (library, list, pages)
2. Creates temporary domain config at `/domains/_SELFTEST/`
3. Creates temporary vector store in OpenAI
4. Runs all crawl tests
5. Modifies SharePoint content to test incremental crawl
6. Cleans up everything (SharePoint, local files, vector store)

## Configuration

**Required config:**
```python
CRAWLER_SELFTEST_SHAREPOINT_SITE: Optional[str]  # e.g. "https://contoso.sharepoint.com/sites/TestSite"
```

**Pre-requisites:**
1. `CRAWLER_SELFTEST_SHAREPOINT_SITE` must be set
2. SharePoint credentials valid (`CRAWLER_CLIENT_ID`, `CRAWLER_TENANT_ID`, `CRAWLER_CLIENT_CERTIFICATE_*`)
3. App registration has permissions: Sites.ReadWrite.All (to create libraries/lists)
4. OpenAI credentials valid for vector store creation

**Constants:**
```python
SELFTEST_DOMAIN_ID = "_SELFTEST"
SELFTEST_LIBRARY_NAME = "_CrawlerSelftest_Docs"
SELFTEST_LIST_NAME = "_CrawlerSelftest_List"
SELFTEST_VECTOR_STORE_NAME = "_CrawlerSelftest_VS"
```

## Test Phases

### Phase 0: Pre-flight Validation
- Verify config exists
- Verify SharePoint connectivity
- Verify OpenAI connectivity

### Phase 1: SharePoint Setup (Initial State)
- Create document library `_CrawlerSelftest_Docs`
- Upload test files (with filter-testable names)
- Create list `_CrawlerSelftest_List` with test items
- Create test site pages (if permissions allow)

### Phase 2: Domain Setup
- Create `/domains/_SELFTEST/domain.json` with sources + filters
- Create temporary vector store in OpenAI

### Phase 3: Download Step Tests (Full Mode)
- Test download_data with mode=full
- Verify filters work (some files excluded)
- Verify map files created correctly

### Phase 4: All Steps Tests (Full Mode)
- Test process_data for each scope
- Test embed_data with mode=full
- Test full crawl with all scopes
- Verify reports generated

### Phase 5: SharePoint Modifications (Incremental State)
- Add new files
- Modify existing files (content + metadata)
- Rename files
- Delete files
- Modify list items
- Update site pages

### Phase 6: Incremental Crawl Tests
- Test download_data with mode=incremental
- Verify added files downloaded
- Verify modified files re-downloaded
- Verify renamed files handled correctly
- Verify deleted files detected
- Test embed_data with mode=incremental
- Verify vector store updated correctly
- Verify files_metadata.json updated
- Verify reports show correct changes

### Phase 7: SharePoint Deletion (Empty State)
- Delete all files from library
- Delete all list items
- Delete site pages

### Phase 8: Empty State Crawl Tests
- Test incremental crawl on empty state
- Verify all files removed from vector store
- Test full crawl on empty state
- Verify domain vector store is empty

### Phase 9: Cleanup
- Delete SharePoint library
- Delete SharePoint list
- Delete site pages
- Delete vector store from OpenAI
- Delete local `/domains/_SELFTEST/` folder
- Delete crawl reports

## SharePoint Setup Operations

### New Helper Functions Required

```python
# In common_sharepoint_functions_v2.py or new file

async def create_document_library(ctx: ClientContext, library_name: str) -> DocumentLibrary:
  """Create a new document library. Returns library object."""
  
async def delete_document_library(ctx: ClientContext, library_name: str) -> bool:
  """Delete a document library and all contents."""

async def upload_file_to_sharepoint(ctx: ClientContext, library_name: str, folder_path: str, filename: str, content: bytes) -> File:
  """Upload a file to SharePoint library."""

async def update_file_in_sharepoint(ctx: ClientContext, library_name: str, file_path: str, new_content: bytes) -> File:
  """Update existing file content."""

async def delete_file_from_sharepoint(ctx: ClientContext, library_name: str, file_path: str) -> bool:
  """Delete a file from SharePoint."""

async def rename_file_in_sharepoint(ctx: ClientContext, library_name: str, old_path: str, new_name: str) -> File:
  """Rename a file in SharePoint."""

async def create_list(ctx: ClientContext, list_name: str, columns: list[dict]) -> List:
  """Create a new SharePoint list with specified columns."""

async def delete_list(ctx: ClientContext, list_name: str) -> bool:
  """Delete a SharePoint list."""

async def add_list_item(ctx: ClientContext, list_name: str, item_data: dict) -> ListItem:
  """Add item to SharePoint list."""

async def update_list_item(ctx: ClientContext, list_name: str, item_id: int, item_data: dict) -> ListItem:
  """Update existing list item."""

async def delete_list_item(ctx: ClientContext, list_name: str, item_id: int) -> bool:
  """Delete list item."""
```

### Initial SharePoint State

**Document Library: `_CrawlerSelftest_Docs`**
```
_CrawlerSelftest_Docs/
  ├── include_file_A.txt          # Should be included (matches filter)
  ├── include_file_B.docx         # Should be included (embeddable)
  ├── include_file_C.md           # Should be included (embeddable)
  ├── exclude_SKIP_file.txt       # Should be excluded by filter "*SKIP*"
  ├── subfolder/
  │   ├── include_nested.txt      # Should be included
  │   └── exclude_SKIP_nested.txt # Should be excluded by filter
  └── non_embeddable.zip          # Should be downloaded but not embedded
```

**List: `_CrawlerSelftest_List`**
```
Columns: Title (text), Description (text), Status (choice), Priority (number)
Items:
  - { Title: "Item 1", Description: "First test item", Status: "Active", Priority: 1 }
  - { Title: "Item 2", Description: "Second test item", Status: "Pending", Priority: 2 }
  - { Title: "Item 3", Description: "Third test item", Status: "Active", Priority: 3 }
```

### Modified SharePoint State (for incremental tests)

**Document Library Changes:**
```
_CrawlerSelftest_Docs/
  ├── include_file_A.txt          # UNCHANGED
  ├── include_file_B.docx         # MODIFIED (content changed)
  ├── include_file_C_renamed.md   # RENAMED from include_file_C.md
  ├── include_file_D_new.txt      # ADDED
  ├── subfolder/
  │   ├── include_nested.txt      # DELETED
  │   └── exclude_SKIP_nested.txt # UNCHANGED (still excluded)
  └── non_embeddable.zip          # UNCHANGED
```

**List Changes:**
```
Items:
  - { Title: "Item 1", ... }           # UNCHANGED
  - { Title: "Item 2 Modified", ... }  # MODIFIED
  - { Title: "Item 4 New", ... }       # ADDED
  # Item 3 DELETED
```

## Domain Configuration

**Generated `/domains/_SELFTEST/domain.json`:**
```json
{
  "domain_id": "_SELFTEST",
  "name": "Crawler Selftest Domain",
  "description": "Auto-generated for selftest",
  "vector_store_id": "{generated_vs_id}",
  "vector_store_name": "_CrawlerSelftest_VS",
  "file_sources": [
    {
      "source_id": "selftest_files",
      "site_url": "{CRAWLER_SELFTEST_SHAREPOINT_SITE}",
      "sharepoint_url_part": "/_CrawlerSelftest_Docs",
      "filter": "!*SKIP*"
    }
  ],
  "list_sources": [
    {
      "source_id": "selftest_list",
      "site_url": "{CRAWLER_SELFTEST_SHAREPOINT_SITE}",
      "list_name": "_CrawlerSelftest_List",
      "view_name": "",
      "filter": ""
    }
  ],
  "sitepage_sources": []
}
```

**Filter test: `!*SKIP*`**
- Files with "SKIP" in name are excluded
- Verifies filter functionality works

## Test Cases by Phase

### Phase 0: Pre-flight (3 tests)

**P0-1. Config validation**
- Check `CRAWLER_SELFTEST_SHAREPOINT_SITE` is set
- Expected: Proceed or return error with setup instructions

**P0-2. SharePoint connectivity**
- Connect to site using credentials
- Expected: Connection succeeds or clear error

**P0-3. OpenAI connectivity**
- List vector stores (simple API call)
- Expected: API responds or clear error

### Phase 1: SharePoint Setup (6 tests)

**P1-1. Create document library**
- Create `_CrawlerSelftest_Docs`
- Expected: Library created, accessible

**P1-2. Upload test files**
- Upload 6 files (4 included, 2 excluded by filter)
- Expected: All files uploaded successfully

**P1-3. Verify file upload**
- List files in library
- Expected: 6 files visible

**P1-4. Create list**
- Create `_CrawlerSelftest_List` with columns
- Expected: List created

**P1-5. Add list items**
- Add 3 test items
- Expected: Items created

**P1-6. Verify list items**
- List items in list
- Expected: 3 items visible

### Phase 2: Domain Setup (4 tests)

**P2-1. Create vector store**
- Create `_CrawlerSelftest_VS` in OpenAI
- Expected: Vector store created, ID obtained

**P2-2. Create domain folder**
- Create `/domains/_SELFTEST/`
- Expected: Folder exists

**P2-3. Write domain.json**
- Write domain config with sources and filter
- Expected: File written, valid JSON

**P2-4. Verify domain loadable**
- Call `load_domain("_SELFTEST")`
- Expected: Domain loads without error

### Phase 3: Download Tests - Full Mode (8 tests)

**P3-1. download_data full mode - files scope**
- `GET /v2/crawler/download_data?domain_id=_SELFTEST&mode=full&scope=files&format=stream`
- Expected: ok=true, 4 files downloaded (2 excluded by filter)

**P3-2. Verify filter exclusion**
- Check that `*SKIP*` files not in files_map.csv
- Expected: Only 4 files in map

**P3-3. Verify sharepoint_map.csv**
- Check structure (10 columns)
- Expected: Valid structure, 4 rows

**P3-4. Verify files_map.csv**
- Check structure (13 columns)
- Expected: Valid structure, 4 rows

**P3-5. Verify files on disk**
- Check `02_embedded/` folder
- Expected: 4 files present

**P3-6. download_data full mode - lists scope**
- `GET /v2/crawler/download_data?domain_id=_SELFTEST&mode=full&scope=lists&format=stream`
- Expected: ok=true, list exported to CSV

**P3-7. Verify list CSV**
- Check CSV in `01_originals/`
- Expected: 3 rows + header

**P3-8. download_data with source_id filter**
- `GET /v2/crawler/download_data?domain_id=_SELFTEST&source_id=selftest_files&format=stream`
- Expected: Only file_sources processed

### Phase 4: All Steps Tests - Full Mode (12 tests)

**P4-1. process_data - files scope (skip)**
- Expected: Skipped (file_sources don't need processing)

**P4-2. process_data - lists scope**
- Expected: CSV converted to MD

**P4-3. Verify processed list file**
- Check MD in `02_embedded/`
- Expected: MD file exists with correct content

**P4-4. embed_data full mode - files scope**
- Expected: 3 embeddable files uploaded (exclude .zip)

**P4-5. Verify vectorstore_map.csv**
- Check structure (19 columns)
- Expected: 3 rows for embeddable files

**P4-6. Verify files_metadata.json**
- Check domain folder
- Expected: Contains openai_file_ids

**P4-7. Verify vector store file count**
- Query OpenAI API
- Expected: 3 files in vector store

**P4-8. embed_data full mode - lists scope**
- Expected: 1 MD file embedded

**P4-9. Verify vector store after list embed**
- Expected: 4 files total (3 docs + 1 list MD)

**P4-10. Full crawl - all scopes**
- `GET /v2/crawler/crawl?domain_id=_SELFTEST&mode=full&scope=all&format=stream`
- Expected: ok=true, all steps complete

**P4-11. Verify crawl report**
- Check `/reports/crawls/`
- Expected: Report zip exists

**P4-12. Verify report content**
- Extract and check report.json
- Expected: Valid structure with correct counts

### Phase 5: SharePoint Modifications (6 operations, not tests)

Operations performed (logged but not counted as tests):
1. Modify `include_file_B.docx` content
2. Rename `include_file_C.md` to `include_file_C_renamed.md`
3. Add `include_file_D_new.txt`
4. Delete `subfolder/include_nested.txt`
5. Modify list item 2
6. Delete list item 3, add item 4

### Phase 6: Incremental Crawl Tests (16 tests)

**P6-1. download_data incremental - files scope**
- Expected: Detects 1 added, 1 modified, 1 renamed, 1 deleted

**P6-2. Verify added file downloaded**
- `include_file_D_new.txt` in files_map.csv
- Expected: Present with downloaded_utc

**P6-3. Verify modified file re-downloaded**
- `include_file_B.docx` has new downloaded_utc
- Expected: Timestamp updated

**P6-4. Verify renamed file handled**
- Old path removed, new path present
- Expected: `include_file_C_renamed.md` in map

**P6-5. Verify deleted file detected**
- `subfolder/include_nested.txt` not in new map
- Expected: Not present

**P6-6. download_data incremental - lists scope**
- Expected: Detects modified item, added item, deleted item

**P6-7. process_data - lists scope**
- Expected: Re-processes list

**P6-8. embed_data incremental - files scope**
- Expected: 1 new embedded, 1 re-embedded, 1 removed from VS

**P6-9. Verify vector store updated**
- Query OpenAI API
- Expected: Correct file count (3 docs still, but different set)

**P6-10. Verify deleted file removed from VS**
- Check `subfolder/include_nested.txt` not in VS
- Expected: openai_file_id removed

**P6-11. Verify files_metadata.json updated**
- Check entries reflect changes
- Expected: Updated entries, removed entries gone

**P6-12. embed_data incremental - lists scope**
- Expected: List MD re-embedded

**P6-13. Full incremental crawl - all scopes**
- Expected: ok=true, changes detected and processed

**P6-14. Verify incremental report**
- Expected: Report shows correct added/modified/deleted counts

**P6-15. Verify report change summary**
- Check report.json `changes` section
- Expected: Accurate change breakdown

**P6-16. Compare pre/post vector store state**
- Expected: Files match expected state after incremental

### Phase 7: SharePoint Deletion (3 operations)

Operations performed:
1. Delete all files from `_CrawlerSelftest_Docs`
2. Delete all items from `_CrawlerSelftest_List`

### Phase 8: Empty State Tests (8 tests)

**P8-1. download_data incremental on empty**
- Expected: All files marked as deleted

**P8-2. Verify files_map.csv reflects deletion**
- Expected: Empty or all marked removed

**P8-3. embed_data incremental on empty**
- Expected: All files removed from vector store

**P8-4. Verify vector store empty**
- Query OpenAI API
- Expected: 0 files in vector store

**P8-5. download_data full on empty**
- Expected: ok=true, 0 files

**P8-6. embed_data full on empty**
- Expected: ok=true, 0 files embedded

**P8-7. Full crawl on empty - all scopes**
- Expected: ok=true, empty state

**P8-8. Verify final vector store state**
- Expected: Vector store exists but empty

### Phase 9: Cleanup (5 tests)

**P9-1. Delete SharePoint library**
- Delete `_CrawlerSelftest_Docs`
- Expected: Library deleted

**P9-2. Delete SharePoint list**
- Delete `_CrawlerSelftest_List`
- Expected: List deleted

**P9-3. Delete vector store**
- Delete `_CrawlerSelftest_VS` from OpenAI
- Expected: Vector store deleted

**P9-4. Delete domain folder**
- Delete `/domains/_SELFTEST/`
- Expected: Folder removed

**P9-5. Delete crawl reports**
- Delete reports for domain_id=_SELFTEST
- Expected: Reports removed

## Implementation Details

### Endpoint Signature

```python
@router.get(f"/{router_name}/selftest")
async def crawler_selftest(request: Request):
  """
  Comprehensive self-test for crawler operations.
  
  Creates temporary SharePoint content, runs all tests, cleans up.
  Requires CRAWLER_SELFTEST_SHAREPOINT_SITE to be configured.
  
  WARNING: This test takes several minutes and makes many API calls.
  
  Example:
  GET /v2/crawler/selftest?format=stream
  
  Optional parameters:
  - skip_cleanup=true - Keep SharePoint artifacts after test (for debugging)
  - phase=N - Run only up to phase N (1-9)
  
  Result (end_json event):
  {
    "ok": true,
    "error": "",
    "data": {
      "passed": 71,
      "failed": 0,
      "skipped": 0,
      "phases_completed": 9,
      "passed_tests": [...],
      "failed_tests": []
    }
  }
  """
```

### Test Helpers

```python
async def sp_create_library(ctx, name: str) -> tuple[bool, str]:
  """Create library, return (success, error_msg)."""

async def sp_upload_file(ctx, library: str, path: str, content: bytes) -> tuple[bool, str]:
  """Upload file, return (success, error_msg)."""

async def sp_modify_file(ctx, library: str, path: str, new_content: bytes) -> tuple[bool, str]:
  """Modify file content, return (success, error_msg)."""

async def sp_rename_file(ctx, library: str, old_path: str, new_name: str) -> tuple[bool, str]:
  """Rename file, return (success, error_msg)."""

async def sp_delete_file(ctx, library: str, path: str) -> tuple[bool, str]:
  """Delete file, return (success, error_msg)."""

async def sp_create_list(ctx, name: str, columns: list) -> tuple[bool, str]:
  """Create list with columns, return (success, error_msg)."""

async def sp_add_list_item(ctx, list_name: str, data: dict) -> tuple[bool, str, int]:
  """Add list item, return (success, error_msg, item_id)."""

async def openai_create_vector_store(name: str) -> tuple[bool, str, str]:
  """Create VS, return (success, error_msg, vs_id)."""

async def openai_delete_vector_store(vs_id: str) -> tuple[bool, str]:
  """Delete VS, return (success, error_msg)."""

async def openai_count_vs_files(vs_id: str) -> int:
  """Count files in vector store."""
```

### Test File Content

```python
TEST_FILES = {
  "include_file_A.txt": b"Test file A content for crawler selftest.\nLine 2.",
  "include_file_B.docx": generate_minimal_docx("Test document B content"),
  "include_file_C.md": b"# Test Markdown\n\nContent for file C.",
  "exclude_SKIP_file.txt": b"This should be excluded by filter.",
  "subfolder/include_nested.txt": b"Nested file content.",
  "subfolder/exclude_SKIP_nested.txt": b"Nested excluded file.",
  "non_embeddable.zip": generate_minimal_zip()
}

MODIFIED_CONTENT = {
  "include_file_B.docx": generate_minimal_docx("MODIFIED document B content"),
  "include_file_D_new.txt": b"New file D added during incremental test."
}
```

## Edge Cases

### SharePoint API Timing
- After upload, file may not be immediately visible
- Solution: Add small delay (1-2s) after write operations, retry on listing

### Vector Store Processing Time
- After adding file to VS, embedding takes time
- Solution: Use `wait_for_vector_store_ready()` before counting files

### Rename vs Delete+Add
- SharePoint rename changes `sharepoint_unique_file_id` or not?
- Test verifies actual behavior and documents it

### Filter Edge Cases
- Filter `!*SKIP*` should exclude files with SKIP anywhere in path
- Test includes nested excluded file to verify

### Empty Library/List
- Some SharePoint APIs behave differently on empty containers
- Phase 8 specifically tests this

### Cleanup on Failure
- If test fails mid-way, cleanup should still run
- `finally` block ensures cleanup even on exception

## Test Summary

| Phase | Description | Test Count |
|-------|-------------|------------|
| P0 | Pre-flight | 3 |
| P1 | SharePoint Setup | 6 |
| P2 | Domain Setup | 4 |
| P3 | Download Tests (Full) | 8 |
| P4 | All Steps Tests (Full) | 12 |
| P5 | SharePoint Modifications | 0 (operations only) |
| P6 | Incremental Crawl Tests | 16 |
| P7 | SharePoint Deletion | 0 (operations only) |
| P8 | Empty State Tests | 8 |
| P9 | Cleanup | 5 |
| **Total** | | **62** |

## Implementation Verification Checklist

### Phase 0: Pre-flight
- [ ] Returns error if CRAWLER_SELFTEST_SHAREPOINT_SITE not set
- [ ] Verifies SharePoint connectivity
- [ ] Verifies OpenAI connectivity

### Phase 1: SharePoint Setup
- [ ] Creates document library with correct name
- [ ] Uploads all test files including nested
- [ ] Creates list with correct columns
- [ ] Adds list items

### Phase 2: Domain Setup
- [ ] Creates vector store in OpenAI
- [ ] Creates domain folder
- [ ] Writes valid domain.json with filter
- [ ] Domain loads without error

### Phase 3: Download Tests
- [ ] Full download excludes filtered files
- [ ] sharepoint_map.csv has 10 columns
- [ ] files_map.csv has 13 columns
- [ ] Files present on disk
- [ ] source_id filter works

### Phase 4: All Steps Tests
- [ ] process_data skips file_sources
- [ ] process_data converts list CSV to MD
- [ ] embed_data uploads embeddable files only
- [ ] vectorstore_map.csv has 19 columns
- [ ] files_metadata.json created
- [ ] Vector store has correct file count
- [ ] Full crawl generates report
- [ ] Report has valid structure

### Phase 6: Incremental Tests
- [ ] Detects added files
- [ ] Detects modified files
- [ ] Detects renamed files
- [ ] Detects deleted files
- [ ] Updates vector store correctly
- [ ] Removes deleted files from vector store
- [ ] Updates files_metadata.json
- [ ] Report shows change counts

### Phase 8: Empty State Tests
- [ ] Incremental crawl removes all from vector store
- [ ] Full crawl on empty succeeds
- [ ] Vector store ends empty

### Phase 9: Cleanup
- [ ] Deletes SharePoint library
- [ ] Deletes SharePoint list
- [ ] Deletes vector store
- [ ] Deletes domain folder
- [ ] Deletes reports
- [ ] Cleanup runs even on test failure

### Code Quality
- [ ] Uses httpx.AsyncClient with appropriate timeouts
- [ ] Has finally block for cleanup
- [ ] Follows domains.py selftest pattern
- [ ] Handles SharePoint API timing issues
- [ ] Logs each phase clearly
- [ ] Reports detailed failure messages

## Spec Changes

**[2026-01-02 13:15]**
- Complete rewrite for self-contained test approach
- Uses CRAWLER_SELFTEST_SHAREPOINT_SITE instead of CRAWLER_SELFTEST_DOMAIN_ID
- Selftest creates/modifies/deletes SharePoint content
- 9 test phases covering full lifecycle
- Tests filter functionality
- Tests incremental crawl with all change types (add/modify/rename/delete)
- Tests empty state behavior
- 62 total tests
