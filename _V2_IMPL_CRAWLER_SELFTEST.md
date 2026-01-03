# Crawler Selftest Implementation Plan (Option B)

**Goal**: Full integration selftest with snapshot-based verification for all crawler endpoints
**Target file**: `/src/routers_v2/crawler.py`

**Depends on:**
- `_V2_SPEC_CRAWLER.md` for crawler functionality
- `_V2_SPEC_ROUTERS.md` for endpoint design and job streaming
- `_V2_IMPL_DOMAINS_SELFTEST.md` for selftest pattern
- `common_sharepoint_functions_v2.py` for SharePoint read operations
- `common_crawler_functions_v2.py` for domain dataclasses and source filtering
- `common_map_file_functions_v2.py` for map file structures
- Office365-REST-Python-Client for SharePoint write operations

**Does not depend on:**
- `_V1_SPEC_COMMON_UI_FUNCTIONS.md`
- `_V2_SPEC_COMMON_UI_FUNCTIONS.md`

## Table of Contents

1. Overview
2. Scenario
3. Design Decisions
4. Test Strategy
5. SharePoint Artifacts
6. Domain Configuration
7. Snapshot Definitions
8. Test Matrix
9. Test Phases
10. Helper Functions
11. Implementation Details
12. Cleanup
13. Implementation Checklist

## Overview

The crawler selftest:
1. Creates temporary SharePoint artifacts (document library with custom field, list)
2. Creates `_SELFTEST` domain with multiple sources per type (for filter testing)

**Note**: Site pages creation is skipped because SharePoint blocks app-only authentication for Site Pages library writes. Site pages crawling can still be tested manually with pre-existing pages.
3. Runs tests using **snapshot-based verification**: restore expected state, run crawl, compare actual vs expected
4. Tests all endpoint parameters: `mode`, `scope`, `source_id`, `dry_run`, source `filter`
5. Tests all change types: ADD, REMOVE, CHANGE, RENAME, MOVE
6. Cleans up all artifacts on completion

**Endpoint**: `GET /v2/crawler/selftest?format=stream`
**Optional parameters**:
- `skip_cleanup=true` - Keep artifacts after test (for debugging)
- `phase=N` - Run only up to phase N (for debugging)
**Response**: SSE stream with test progress and final summary

## Scenario

**Problem**: Testing incremental crawl requires controlled SharePoint content changes. Manual setup is error-prone and doesn't cover edge cases.

**Solution**: Selftest creates temporary SharePoint artifacts, runs full/incremental crawl tests with snapshot verification, then cleans up.

**What we don't want:**
- Parallel execution (sequential only for predictability)
- Manual test data setup
- Leftover artifacts after test completion
- Tests that depend on previous test state (use snapshot restore)

## Design Decisions

**CRST-DD-01:** `scope=all + source_id` filters across all source types matching that source_id.

**CRST-DD-02:** Snapshots are actual folder copies, not Python dicts. Created by copying the domain's crawler folder after each significant state.

**CRST-DD-03:** If vector store creation fails, skip embed tests but continue with other tests. Maximize test coverage even on partial failures.

**CRST-DD-04:** After SharePoint mutations, poll every 5 seconds to verify mutation is reflected before continuing. Max wait 60 seconds.

**CRST-DD-07:** After adding files to vector store, wait for embedding completion before verification. Use `wait_for_vector_store_ready()`.

**CRST-DD-05:** Files stored in `02_embedded/` subfolder for file_sources, `01_originals/` for lists/sitepages before processing.

**CRST-DD-06:** List items exported as CSV to `01_originals/`, then converted to `.md` in `02_embedded/`.

## Test Strategy

### Snapshot-Based Verification

Every test follows the same pattern:

```
1. Restore domain folder from snapshot (or clean for first test)
2. Run crawl with specific parameters
3. Compare actual state vs expected snapshot
4. Report pass/fail
```

### Snapshots = Actual Folder Copies

Snapshots are **actual folder copies** created during test execution:
- After full crawl completes, copy crawler folder to `_SNAPSHOT_FULL_ALL/`
- Use `shutil.copytree()` / `shutil.rmtree()` for save/restore
- Compare actual vs expected by comparing folder contents

Snapshot verification checks:
- `sharepoint_map.csv` row count
- `files_map.csv` row count and filenames
- `vectorstore_map.csv` row count
- Local files in `02_embedded/` subfolder

### Core Verification Function

```python
def verify_against_snapshot(actual_path: str, snapshot: dict) -> list[str]:
  """
  Compare actual crawler output against expected snapshot.
  Returns list of failures (empty = all passed).
  
  snapshot = {
    "01_files/files_all": {"sharepoint_map_rows": 6, "files_map_rows": 6, "vectorstore_map_rows": 6, "local_files": ["file1.txt", ...]},
    "01_files/files_crawl1": {"sharepoint_map_rows": 3, "files_map_rows": 3, "vectorstore_map_rows": 3, "local_files": [...]},
    ...
  }
  """
  failures = []
  for source_path, expected in snapshot.items():
    actual_map_path = os.path.join(actual_path, source_path, "files_map.csv")
    if not os.path.exists(actual_map_path):
      if expected["files_map_rows"] > 0:
        failures.append(f"{source_path}: files_map.csv missing")
      continue
    actual_rows = read_files_map(actual_map_path)
    if len(actual_rows) != expected["files_map_rows"]:
      failures.append(f"{source_path}: files_map rows {len(actual_rows)} != {expected['files_map_rows']}")
    # Check local files exist
    for filename in expected.get("local_files", []):
      if not os.path.exists(os.path.join(actual_path, source_path, filename)):
        failures.append(f"{source_path}: missing file '{filename}'")
  return failures
```

## SharePoint Artifacts

### Document Library: `SELFTEST_DOCS`

Custom field `Crawl` (number) for filter testing.

- **file1.txt**: content="Test file 1 content", Crawl=1
- **file2.txt**: content="Test file 2 content", Crawl=1
- **file3.txt**: content="Test file 3 content", Crawl=1
- **file4.txt**: content="Test file 4 content", Crawl=0
- **file5.txt**: content="Test file 5 content", Crawl=0
- **file6.txt**: content="Test file 6 content", Crawl=0
- **non_embeddable.zip**: empty zip file, Crawl=1 (for I5: non-embeddable test)
- **file_测试.txt**: content="Unicode filename test", Crawl=1 (for I6: unicode test)
- **subfolder/file1.txt**: content="Subfolder file content", Crawl=1 (for I7: same filename in subfolder)

### List: `SELFTEST_LIST`

Fields: Title, Status (text), Description

- **Item 1**: Status="Active", Description="Test item 1"
- **Item 2**: Status="Active", Description="Test item 2"
- **Item 3**: Status="Active", Description="Test item 3"
- **Item 4**: Status="Inactive", Description="Test item 4"
- **Item 5**: Status="Inactive", Description="Test item 5"
- **Item 6**: Status="Inactive", Description="Test item 6"

### Site Pages: `/SitePages` (SKIPPED)

**Note**: Site pages creation is skipped. SharePoint blocks app-only authentication for Site Pages library writes. This is a SharePoint security feature, not a permission issue. See `_V2_IMPL_CRAWLER_SELFTEST_FIXES.md` for details.

## Domain Configuration

Domain ID: `_SELFTEST`

```json
{
  "domain_id": "_SELFTEST",
  "name": "Crawler Selftest Domain",
  "description": "Temporary domain for crawler selftest",
  "vector_store_name": "_SELFTEST_VS",
  "vector_store_id": "",
  "file_sources": [
    {
      "source_id": "files_all",
      "site_url": "{SELFTEST_SITE}",
      "sharepoint_url_part": "/SELFTEST_DOCS",
      "filter": ""
    },
    {
      "source_id": "files_crawl1",
      "site_url": "{SELFTEST_SITE}",
      "sharepoint_url_part": "/SELFTEST_DOCS",
      "filter": "Crawl eq 1"
    }
  ],
  "list_sources": [
    {
      "source_id": "lists_all",
      "site_url": "{SELFTEST_SITE}",
      "list_name": "SELFTEST_LIST",
      "filter": ""
    },
    {
      "source_id": "lists_active",
      "site_url": "{SELFTEST_SITE}",
      "list_name": "SELFTEST_LIST",
      "filter": "Status eq 'Active'"
    }
  ],
  "sitepage_sources": []  // Site pages skipped - app-only auth blocked
}
```

## Snapshot Definitions

### Snapshot Constants

```python
# After full crawl with scope=all
# Note: 9 files total (6 original + zip + unicode + subfolder), 5 with Crawl=1
# Site pages excluded - app-only auth blocked
SNAP_FULL_ALL = {
  "01_files/files_all": {"files_map_rows": 9},
  "01_files/files_crawl1": {"files_map_rows": 6},
  "02_lists/lists_all": {"files_map_rows": 6},
  "02_lists/lists_active": {"files_map_rows": 3}
  # "03_sitepages/pages_all" excluded
}

# After full crawl with scope=files
SNAP_FULL_FILES = {
  "01_files/files_all": {"files_map_rows": 9},
  "01_files/files_crawl1": {"files_map_rows": 6},
  "02_lists/lists_all": {"files_map_rows": 0},
  "02_lists/lists_active": {"files_map_rows": 0}
}

# After full crawl with scope=lists
SNAP_FULL_LISTS = {
  "01_files/files_all": {"files_map_rows": 0},
  "01_files/files_crawl1": {"files_map_rows": 0},
  "02_lists/lists_all": {"files_map_rows": 6},
  "02_lists/lists_active": {"files_map_rows": 3}
}

# After full crawl with scope=sitepages - SKIPPED (no sitepages sources)
# SNAP_FULL_PAGES not used - sitepages testing skipped

# After full crawl with source_id=files_crawl1 (filtered)
SNAP_FULL_FILES_CRAWL1 = {
  "01_files/files_all": {"files_map_rows": 0},
  "01_files/files_crawl1": {"files_map_rows": 6},
  "02_lists/lists_all": {"files_map_rows": 0},
  "02_lists/lists_active": {"files_map_rows": 0}
}

# After full crawl with source_id=lists_active (filtered)
SNAP_FULL_LISTS_ACTIVE = {
  "01_files/files_all": {"files_map_rows": 0},
  "01_files/files_crawl1": {"files_map_rows": 0},
  "02_lists/lists_all": {"files_map_rows": 0},
  "02_lists/lists_active": {"files_map_rows": 3}
}

# After download step only (no process/embed)
SNAP_DOWNLOAD_ONLY = {
  "01_files/files_all": {"files_map_rows": 6, "sharepoint_map_rows": 6, "vectorstore_map_rows": 0},
  # ... similar for other sources
}

# After process step only (no embed)
SNAP_PROCESS_ONLY = {
  "01_files/files_all": {"files_map_rows": 6, "sharepoint_map_rows": 6, "vectorstore_map_rows": 0},
  # ... similar for other sources
}

# Empty/unchanged state
SNAP_EMPTY = {
  "01_files/files_all": {"files_map_rows": 0},
  "01_files/files_crawl1": {"files_map_rows": 0},
  "02_lists/lists_all": {"files_map_rows": 0},
  "02_lists/lists_active": {"files_map_rows": 0}
}
```

### Incremental Snapshots (after mutations)

Mutations applied:
- **Files**: ADD file7.txt, REMOVE file6.txt, CHANGE file1.txt, RENAME file2.txt->file2_renamed.txt, MOVE file3.txt->subfolder/file3.txt
- **Lists**: ADD item7, REMOVE item6, CHANGE item1
- **SitePages**: SKIPPED (app-only auth blocked)

```python
# After incremental crawl scope=all (all mutations)
SNAP_INCR_ALL = {
  "01_files/files_all": {"files_map_rows": 6, "local_files": ["file1.txt", "file2_renamed.txt", "subfolder/file3.txt", "file4.txt", "file5.txt", "file7.txt"]},
  "01_files/files_crawl1": {"files_map_rows": 3, "local_files": ["file1.txt", "file2_renamed.txt", "subfolder/file3.txt"]},
  "02_lists/lists_all": {"files_map_rows": 6},
  "02_lists/lists_active": {"files_map_rows": 3},
  "03_sitepages/pages_all": {"files_map_rows": 3, "local_files": ["_selftest_page1.aspx.html", "_selftest_page2_renamed.aspx.html", "_selftest_page4.aspx.html"]}
}

# After incremental crawl scope=files only (lists/pages unchanged from SNAP_FULL_ALL)
SNAP_INCR_FILES = {
  "01_files/files_all": {"files_map_rows": 6, "local_files": ["file1.txt", "file2_renamed.txt", "subfolder/file3.txt", "file4.txt", "file5.txt", "file7.txt"]},
  "01_files/files_crawl1": {"files_map_rows": 3, "local_files": ["file1.txt", "file2_renamed.txt", "subfolder/file3.txt"]},
  "02_lists/lists_all": {"files_map_rows": 6},  # unchanged
  "02_lists/lists_active": {"files_map_rows": 3},  # unchanged
  "03_sitepages/pages_all": {"files_map_rows": 3, "local_files": ["_selftest_page1.aspx.html", "_selftest_page2.aspx.html", "_selftest_page3.aspx.html"]}  # unchanged
}

# After incremental crawl scope=lists only
SNAP_INCR_LISTS = {
  "01_files/files_all": {"files_map_rows": 6, "local_files": ["file1.txt", "file2.txt", "file3.txt", "file4.txt", "file5.txt", "file6.txt"]},  # unchanged
  "01_files/files_crawl1": {"files_map_rows": 3},  # unchanged
  "02_lists/lists_all": {"files_map_rows": 6},  # updated
  "02_lists/lists_active": {"files_map_rows": 3},  # updated
  "03_sitepages/pages_all": {"files_map_rows": 3}  # unchanged
}

# After incremental crawl scope=sitepages only
SNAP_INCR_PAGES = {
  "01_files/files_all": {"files_map_rows": 6},  # unchanged
  "01_files/files_crawl1": {"files_map_rows": 3},  # unchanged
  "02_lists/lists_all": {"files_map_rows": 6},  # unchanged
  "02_lists/lists_active": {"files_map_rows": 3},  # unchanged
  "03_sitepages/pages_all": {"files_map_rows": 3, "local_files": ["_selftest_page1.aspx.html", "_selftest_page2_renamed.aspx.html", "_selftest_page4.aspx.html"]}  # updated
}
```

## Test Matrix

### A. Full Crawl x Scope (4 tests)

- **A1**: mode=full, scope=all -> SNAP_FULL_ALL
- **A2**: mode=full, scope=files -> SNAP_FULL_FILES
- **A3**: mode=full, scope=lists -> SNAP_FULL_LISTS
- **A4**: mode=full, scope=sitepages -> SNAP_FULL_PAGES

### B. source_id Filter (5 tests)

- **B1**: scope=files, source_id=files_all -> SNAP_FULL_FILES (files_all only)
- **B2**: scope=files, source_id=files_crawl1 -> SNAP_FULL_FILES_CRAWL1
- **B3**: scope=lists, source_id=lists_active -> SNAP_FULL_LISTS_ACTIVE
- **B4**: scope=files, source_id=INVALID -> SNAP_EMPTY
- **B5**: scope=all, source_id=files_all -> filters across all types

### C. Source filter Field (implicit, 0 tests)

Verified implicitly by A1 snapshot - row counts confirm filters work:

- files_all, filter="" -> 6 files
- files_crawl1, filter="Crawl eq 1" -> 3 files
- lists_all, filter="" -> 6 items
- lists_active, filter="Status eq 'Active'" -> 3 items

### D. dry_run (4 tests)

- **D1**: /crawl, dry_run=true, pre=SNAP_EMPTY -> SNAP_EMPTY
- **D2**: /download_data, dry_run=true, pre=SNAP_EMPTY -> SNAP_EMPTY
- **D3**: /process_data, dry_run=true, pre=SNAP_DOWNLOAD_ONLY -> SNAP_DOWNLOAD_ONLY
- **D4**: /embed_data, dry_run=true, pre=SNAP_PROCESS_ONLY -> SNAP_PROCESS_ONLY

### E. Individual Steps (3 tests)

Run sequentially, saving snapshots after each step:

- **E1**: /download_data, pre=SNAP_EMPTY -> SNAP_DOWNLOAD_ONLY (save)
- **E2**: /process_data, continue from E1 -> SNAP_PROCESS_ONLY (save)
- **E3**: /embed_data, continue from E2 -> SNAP_FULL_ALL

### F. Incremental x Scope (4 tests)

Prerequisite: SNAP_FULL_ALL state + SharePoint mutations applied

- **F1**: mode=incremental, scope=all -> SNAP_INCR_ALL
- **F2**: mode=incremental, scope=files -> SNAP_INCR_FILES
- **F3**: mode=incremental, scope=lists -> SNAP_INCR_LISTS
- **F4**: mode=incremental, scope=sitepages -> SNAP_INCR_PAGES

### G. Incremental source_id (2 tests)

- **G1**: scope=files, source_id=files_all -> only files_all updated
- **G2**: scope=files, source_id=files_crawl1 -> only files_crawl1 updated

### H. Job Control (2 tests)

- **H1**: pause during download -> job pauses, resumes on resume
- **H2**: cancel during download -> job stops, partial state

### I. Error Cases (8 tests)

- **I1**: Missing domain_id -> ok=false
- **I2**: Invalid domain_id -> 404
- **I3**: Invalid scope value -> ok=false
- **I4**: Invalid mode value -> ok=false
- **I5**: Non-embeddable file type -> file skipped, no error
- **I6**: Unicode filename -> handled correctly
- **I7**: Same filename in different subfolders -> both downloaded
- **I8**: Empty domain (no sources) -> ok=true, sources_processed=0

### J. Integrity Check (4 tests)

Tests V2CR-FR-03 and V2CR-FR-04 from _V2_SPEC_CRAWLER.md

- **J1**: MISSING_ON_DISK - delete file from disk after download, run incremental -> re-downloaded
- **J2**: ORPHAN_ON_DISK - add orphan file to 02_embedded/, run download -> orphan deleted
- **J3**: WRONG_PATH - move file to wrong path on disk, run download -> moved back to correct path
- **J4**: MAP_FILE_CORRUPTED - corrupt files_map.csv, run crawl -> falls back to mode=full

### K. Advanced Edge Cases (4 tests)

- **K1**: FOLDER_RENAMED - rename subfolder in SharePoint -> all files inside detected as CHANGED
- **K2**: RESTORED - restore file from recycle bin -> detected as ADDED (same sharepoint_unique_file_id)
- **K3**: VS_EMBEDDING_FAILED - embed file that will fail -> moved to 03_failed/, error logged
- **K4**: retry_batches - compare retry_batches=1 vs default behavior on transient failure

### L. Metadata & Reports (3 tests)

- **L1**: files_metadata.json - verify updated after embed with correct fields
- **L2**: Custom property carry-over - add custom property, update file, verify carry-over
- **L3**: Crawl report - verify report.zip created after /crawl (not created for dry_run)

### M. Pre-flight Validation (4 tests)

- **M1**: Config validation - CRAWLER_SELFTEST_SHAREPOINT_SITE must be set
- **M2**: SharePoint connectivity (read) - read /SiteAssets library
- **M2b**: SharePoint connectivity (write) - upload + delete test file to /SiteAssets
- **M3**: OpenAI connectivity - create + delete temp vector store `_selftest_preflight_vs`

### N. Empty State (4 tests)

After deleting all SharePoint content:

- **N1**: Incremental crawl on empty -> all files marked as REMOVED
- **N2**: Verify vector store empty after incremental
- **N3**: Full crawl on empty -> ok=true, 0 files
- **N4**: Verify final vector store state -> exists but empty

### O. Map File Structure (3 tests)

- **O1**: sharepoint_map.csv has 10 columns (per _V2_SPEC_CRAWLER.md)
- **O2**: files_map.csv has 13 columns
- **O3**: vectorstore_map.csv has 19 columns

### Total: ~45 tests (reduced - site pages skipped)

## Test Phases

```
Phase 1: Pre-flight Validation (M1-M3)
├── 1.1 M1: Verify CRAWLER_SELFTEST_SHAREPOINT_SITE configured
├── 1.2 M2: Test SharePoint read access to /SiteAssets
├── 1.3 M2b: Test SharePoint write access (upload + delete test file)
├── 1.4 M3: Test OpenAI connectivity (create + delete temp vector store)

Phase 2: Pre-cleanup (remove leftover artifacts from previous runs)
├── 2.1 Delete _SELFTEST domain via API (ignore errors)
├── 2.2 Delete local snapshots folder (ignore errors)
├── 2.3 Delete crawler/_SELFTEST folder (ignore errors)
├── 2.4 Delete SharePoint list SELFTEST_LIST (ignore errors)
├── 2.5 Delete SharePoint document library /SELFTEST_DOCS (ignore errors)

Phase 3: SharePoint Setup
├── 3.1 Create document library SELFTEST_DOCS
├── 3.2 Add custom field "Crawl" (number)
├── 3.3 Upload 9 files with Crawl field values
├── 3.4 Create list SELFTEST_LIST
├── 3.5 Add 6 list items with Status field
# Site pages creation skipped - app-only auth blocked

Phase 4: Domain Setup
├── 4.1 Create _SELFTEST domain via /v2/domains/create

Phase 5: Error Cases (I1-I4)
├── 5.1 Test missing domain_id
├── 5.2 Test invalid domain_id
├── 5.3 Test invalid scope
├── 5.4 Test invalid mode

Phase 6: Full Crawl Tests (A1-A3)
├── 6.1 Restore SNAP_EMPTY, crawl full/all, verify SNAP_FULL_ALL
├── 6.2 Restore SNAP_EMPTY, crawl full/files, verify SNAP_FULL_FILES
├── 6.3 Restore SNAP_EMPTY, crawl full/lists, verify SNAP_FULL_LISTS
# 6.4 sitepages test skipped - no sitepage_sources

Phase 7: source_id Filter Tests (B1-B5)
├── 7.1 Restore SNAP_EMPTY, crawl files/files_all, verify
├── 7.2 Restore SNAP_EMPTY, crawl files/files_crawl1, verify SNAP_FULL_FILES_CRAWL1
├── 7.3 Restore SNAP_EMPTY, crawl lists/lists_active, verify SNAP_FULL_LISTS_ACTIVE
├── 7.4 Restore SNAP_EMPTY, crawl files/INVALID, verify SNAP_EMPTY
├── 7.5 Test scope=all + source_id behavior

Phase 8: dry_run Tests (D1-D4)
├── 8.1 Restore SNAP_EMPTY, crawl dry_run=true, verify SNAP_EMPTY
├── 8.2 Restore SNAP_EMPTY, download dry_run=true, verify SNAP_EMPTY
├── 8.3 Restore SNAP_DOWNLOAD_ONLY, process dry_run=true, verify SNAP_DOWNLOAD_ONLY
├── 8.4 Restore SNAP_PROCESS_ONLY, embed dry_run=true, verify SNAP_PROCESS_ONLY

Phase 9: Individual Steps Tests (E1-E3)
├── 9.1 Restore SNAP_EMPTY, download_data, verify SNAP_DOWNLOAD_ONLY
├── 9.2 (continue from 9.1) process_data, verify SNAP_PROCESS_ONLY
├── 9.3 (continue from 9.2) embed_data, verify SNAP_FULL_ALL

Phase 10: Apply SharePoint Mutations
├── 10.1 Files: ADD file7.txt (Crawl=1)
├── 10.2 Files: REMOVE file6.txt
├── 10.3 Files: CHANGE file1.txt content
├── 10.4 Files: RENAME file2.txt -> file2_renamed.txt
├── 10.5 Files: MOVE file3.txt -> subfolder/file3.txt
├── 10.6 Lists: ADD item7 (Status=Active)
# Site pages mutations skipped - app-only auth blocked
├── 10.7 Wait for mutations to propagate

Phase 11: Incremental Tests (F1-F3)
├── 11.1 Restore SNAP_FULL_ALL, crawl incremental/all, verify SNAP_INCR_ALL
├── 11.2 Restore SNAP_FULL_ALL, crawl incremental/files, verify SNAP_INCR_FILES
├── 11.3 Restore SNAP_FULL_ALL, crawl incremental/lists, verify SNAP_INCR_LISTS
# 11.4 sitepages test skipped - no sitepage_sources

Phase 12: Incremental source_id Tests (G1-G2)
├── 12.1 Restore SNAP_FULL_ALL, crawl incremental/files/files_all, verify
├── 12.2 Restore SNAP_FULL_ALL, crawl incremental/files/files_crawl1, verify

Phase 13: Job Control Tests (H1-H2)
├── 13.1 Start download, pause, verify paused, resume, verify completes
├── 13.2 Start download, cancel, verify cancelled

Phase 14: Integrity Check Tests (J1-J4)
├── 14.1 Restore SNAP_FULL_ALL, delete file1.txt from disk, run incremental -> file re-downloaded
├── 14.2 Restore SNAP_FULL_ALL, add orphan.txt to 02_embedded/, run download -> orphan deleted
├── 14.3 Restore SNAP_FULL_ALL, move file2.txt to wrong path, run download -> moved back
├── 14.4 Restore SNAP_FULL_ALL, corrupt files_map.csv, run crawl -> mode=full fallback

Phase 15: Advanced Edge Cases (K1-K4)
├── 15.1 Create subfolder in SharePoint, move files, rename subfolder -> files detected as CHANGED
├── 15.2 Delete file from SharePoint, restore from recycle bin -> detected as ADDED
├── 15.3 Upload file that will fail embedding (e.g., empty file) -> moved to 03_failed/
├── 15.4 Test retry_batches=1 behavior on simulated failure

Phase 16: Metadata & Reports Tests (L1-L3)
├── 16.1 After embed, verify files_metadata.json contains embedded files with correct fields
├── 16.2 Add custom property to files_metadata.json, update file, verify carry-over
├── 16.3 Run /crawl, verify report.zip created; run with dry_run=true, verify no report

Phase 17: Map File Structure Tests (O1-O3)
├── 17.1 Verify sharepoint_map.csv has 10 columns
├── 17.2 Verify files_map.csv has 13 columns
├── 17.3 Verify vectorstore_map.csv has 19 columns

Phase 18: Empty State Tests (N1-N4)
├── 18.1 Delete all files from SharePoint library
├── 18.2 Delete all items from SharePoint list
├── 18.3 Run incremental crawl -> all files REMOVED from vector store
├── 18.4 Verify vector store empty
├── 18.5 Run full crawl on empty -> ok=true, 0 files

Phase 19: Cleanup
├── 19.1 Delete vector store files
├── 19.2 Delete vector store
├── 19.3 Delete _SELFTEST domain
├── 19.4 Delete SharePoint list
├── 19.5 Delete SharePoint document library
├── 19.6 Delete crawl reports for _SELFTEST
```

## Helper Functions

### SharePoint Write Operations

```python
async def create_document_library(ctx, library_name: str) -> bool:
  """Create document library with custom 'Crawl' field"""

async def upload_file_to_library(ctx, library_name: str, filename: str, content: bytes, crawl_value: int) -> bool:
  """Upload file and set Crawl field value"""

async def update_file_content(ctx, server_relative_url: str, new_content: bytes) -> bool:
  """Update file content (triggers change detection)"""

async def rename_file(ctx, server_relative_url: str, new_name: str) -> bool:
  """Rename file (keeps same unique_id)"""

async def move_file(ctx, server_relative_url: str, target_folder: str) -> bool:
  """Move file to subfolder"""

async def delete_file(ctx, server_relative_url: str) -> bool:
  """Delete file from library"""

async def create_list(ctx, list_name: str) -> bool:
  """Create list with Status field"""

async def add_list_item(ctx, list_name: str, title: str, status: str) -> bool:
  """Add item to list"""

async def update_list_item(ctx, list_name: str, item_id: int, updates: dict) -> bool:
  """Update list item fields"""

async def delete_list_item(ctx, list_name: str, item_id: int) -> bool:
  """Delete list item"""

async def create_site_page(ctx, page_name: str, content: str) -> bool:
  """Create site page"""

async def update_site_page(ctx, page_name: str, new_content: str) -> bool:
  """Update site page content"""

async def rename_site_page(ctx, old_name: str, new_name: str) -> bool:
  """Rename site page"""

async def delete_site_page(ctx, page_name: str) -> bool:
  """Delete site page"""

async def delete_document_library(ctx, library_name: str) -> bool:
  """Delete entire document library"""

async def delete_list(ctx, list_name: str) -> bool:
  """Delete entire list"""
```

### Snapshot Operations

```python
SNAPSHOT_BASE_PATH = "_selftest_snapshots"  # Under persistent storage

def save_snapshot(storage_path: str, domain_id: str, snapshot_name: str) -> None:
  """
  Copy crawler/{domain_id}/ to _selftest_snapshots/{snapshot_name}/
  Uses shutil.copytree() for full folder copy.
  """
  source = os.path.join(storage_path, "crawler", domain_id)
  target = os.path.join(storage_path, SNAPSHOT_BASE_PATH, snapshot_name)
  if os.path.exists(target): shutil.rmtree(target)
  shutil.copytree(source, target)

def restore_snapshot(storage_path: str, domain_id: str, snapshot_name: str) -> None:
  """
  Restore crawler/{domain_id}/ from _selftest_snapshots/{snapshot_name}/
  Deletes current state first, then copies snapshot.
  """
  source = os.path.join(storage_path, SNAPSHOT_BASE_PATH, snapshot_name)
  target = os.path.join(storage_path, "crawler", domain_id)
  if os.path.exists(target): shutil.rmtree(target)
  if os.path.exists(source): shutil.copytree(source, target)
  else: os.makedirs(target, exist_ok=True)  # Empty restore

def clear_crawler_folder(storage_path: str, domain_id: str) -> None:
  """Delete all content in crawler/{domain_id}/"""
  target = os.path.join(storage_path, "crawler", domain_id)
  if os.path.exists(target): shutil.rmtree(target)
  os.makedirs(target, exist_ok=True)

def compare_snapshots(storage_path: str, domain_id: str, snapshot_name: str) -> list[str]:
  """
  Compare current crawler/{domain_id}/ against _selftest_snapshots/{snapshot_name}/
  Returns list of differences (empty = match).
  Compares: folder structure, map file row counts, local file existence.
  """
  actual = os.path.join(storage_path, "crawler", domain_id)
  expected = os.path.join(storage_path, SNAPSHOT_BASE_PATH, snapshot_name)
  differences = []
  # Walk expected and compare against actual
  for root, dirs, files in os.walk(expected):
    rel_root = os.path.relpath(root, expected)
    for f in files:
      expected_file = os.path.join(root, f)
      actual_file = os.path.join(actual, rel_root, f)
      if not os.path.exists(actual_file):
        differences.append(f"Missing: {rel_root}/{f}")
      elif f.endswith('.csv'):
        # Compare row counts for CSV files
        expected_rows = len(open(expected_file).readlines()) - 1  # Minus header
        actual_rows = len(open(actual_file).readlines()) - 1
        if expected_rows != actual_rows:
          differences.append(f"{rel_root}/{f}: {actual_rows} rows != {expected_rows} expected")
  return differences

def cleanup_snapshots(storage_path: str) -> None:
  """Delete all snapshots in _selftest_snapshots/"""
  snapshots_dir = os.path.join(storage_path, SNAPSHOT_BASE_PATH)
  if os.path.exists(snapshots_dir): shutil.rmtree(snapshots_dir)
```

### Mutation Propagation Wait

```python
MUTATION_POLL_INTERVAL = 5  # seconds
MUTATION_MAX_WAIT = 60  # seconds

async def wait_for_mutation(ctx, check_func, description: str, logger) -> bool:
  """
  Poll SharePoint until mutation is reflected.
  
  Args:
    ctx: SharePoint context
    check_func: Async function returning True when mutation is visible
    description: What we're waiting for (for logging)
    logger: MiddlewareLogger
    
  Returns:
    True if mutation detected, False if timeout
  """
  logger.log_function_output(f"  Waiting for mutation: {description}...")
  waited = 0
  while waited < MUTATION_MAX_WAIT:
    if await check_func():
      logger.log_function_output(f"    Mutation visible after {waited}s.")
      return True
    await asyncio.sleep(MUTATION_POLL_INTERVAL)
    waited += MUTATION_POLL_INTERVAL
  logger.log_function_output(f"    WARNING: Mutation not visible after {MUTATION_MAX_WAIT}s.")
  return False

# Example usage:
async def check_file7_exists():
  try:
    sp_file = ctx.web.get_file_by_server_relative_url(f"{site_path}/_SELFTEST_DOCS/file7.txt")
    sp_file.get().execute_query()
    return True
  except:
    return False

await wait_for_mutation(ctx, check_file7_exists, "file7.txt added", logger)
```

### Test Execution

```python
async def run_crawl_test(
  base_url: str,
  domain_id: str,
  endpoint: str,  # "crawl", "download_data", "process_data", "embed_data"
  mode: str = None,
  scope: str = None,
  source_id: str = None,
  dry_run: bool = False
) -> dict:
  """Execute crawl endpoint via HTTP and wait for completion. Returns JSON result."""
  params = {"domain_id": domain_id, "format": "stream"}
  if mode: params["mode"] = mode
  if scope: params["scope"] = scope
  if source_id: params["source_id"] = source_id
  if dry_run: params["dry_run"] = "true"
  
  url = f"{base_url}/v2/crawler/{endpoint}"
  async with httpx.AsyncClient(timeout=300.0) as client:
    async with client.stream("GET", url, params=params) as response:
      last_event = None
      async for line in response.aiter_lines():
        if line.startswith("data: "):
          try:
            event = json.loads(line[6:])
            if event.get("event") == "end_json":
              return event.get("data", {})
            last_event = event
          except: pass
      return last_event or {"ok": False, "error": "No end event"}

def check_result(result: dict, expected_ok: bool, context: str) -> tuple[bool, str]:
  """Verify result.ok matches expected, return (passed, message)"""
  actual_ok = result.get("ok", False)
  if actual_ok == expected_ok:
    return True, f"OK: {context}"
  return False, f"FAIL: {context} - expected ok={expected_ok}, got ok={actual_ok}"
```

## Implementation Details

### Endpoint Definition

```python
@router.get(f"/{router_name}/selftest")
async def crawler_selftest(request: Request):
  """
  Self-test for crawler operations.
  
  Only supports format=stream.
  
  Creates temporary SharePoint artifacts, runs full test suite,
  verifies results against expected snapshots, cleans up.
  
  Requires CRAWLER_SELFTEST_SHAREPOINT_SITE config.
  
  Example:
  GET {router_prefix}/{router_name}/selftest?format=stream
  """
```

### Test Runner Structure

```python
async def run_selftest():
  # Counters
  test_num = 0
  ok_count = 0
  fail_count = 0
  
  # Helper functions
  def log(msg): ...
  def next_test(desc): ...
  def check(condition, ok_msg, fail_msg): ...
  
  try:
    # Phase 1: SharePoint Setup
    yield log("Phase 1: SharePoint Setup")
    yield log("  Creating document library '_SELFTEST_DOCS'...")
    success = await create_document_library(ctx, "_SELFTEST_DOCS")
    if not success: raise Exception("Failed to create document library")
    # ... continue setup
    
    # Phase 2: Domain Setup
    yield log("Phase 2: Domain Setup")
    # ...
    
    # Phase 3-11: Tests
    # Each test: restore snapshot, run crawl, verify result
    
    # Phase 3: Error Cases
    yield log("Phase 3: Error Cases")
    yield next_test("Missing domain_id")
    result = await run_crawl_test(base_url, "", "crawl")
    yield check(result["ok"] == False, "Correctly rejected", "Should have failed")
    # ...
    
    # Phase 4: Full Crawl Tests
    yield log("Phase 4: Full Crawl Tests")
    
    yield next_test("Full crawl scope=all")
    clear_domain_folder(domain_path)
    result = await run_crawl_test(base_url, "_SELFTEST", "crawl", mode="full", scope="all")
    yield check(result["ok"], "Crawl succeeded", f"Crawl failed: {result.get('message')}")
    failures = verify_against_snapshot(domain_path, SNAP_FULL_ALL)
    yield check(len(failures) == 0, "State matches SNAP_FULL_ALL", f"Mismatches: {failures}")
    # Save this state for incremental tests
    save_domain_snapshot(domain_path)  # -> SNAP_FULL_ALL_SAVED
    # ...
    
  finally:
    # Phase 12: Cleanup (always runs)
    yield log("Phase 12: Cleanup")
    # ... cleanup code
```

## Cleanup

Cleanup runs in `finally` block to ensure execution even on test failure:

```python
finally:
  yield log("Phase 12: Cleanup")
  
  # Delete vector store files and vector store
  if vector_store_id:
    yield log(f"  Deleting vector store '{vector_store_id}'...")
    try:
      await delete_vector_store(openai_client, vector_store_id)
    except: pass
  
  # Delete domain
  yield log("  Deleting _SELFTEST domain...")
  try:
    async with httpx.AsyncClient(timeout=30.0) as client:
      await client.delete(f"{base_url}/v2/domains/delete?domain_id=_SELFTEST")
  except: pass
  
  # Delete local snapshots
  yield log("  Deleting local snapshots...")
  try: cleanup_snapshots(get_persistent_storage_path())
  except: pass
  
  # Delete crawler folder for domain
  yield log("  Deleting crawler/_SELFTEST folder...")
  try: 
    crawler_path = os.path.join(get_persistent_storage_path(), "crawler", "_SELFTEST")
    if os.path.exists(crawler_path): shutil.rmtree(crawler_path)
  except: pass
  
  # Delete SharePoint artifacts (reverse order of creation)
  yield log("  Deleting SharePoint site pages...")
  for page in ["_selftest_page1", "_selftest_page2", "_selftest_page2_renamed", "_selftest_page3", "_selftest_page4"]:
    try: await delete_site_page(ctx, f"{page}.aspx")
    except: pass
  
  yield log("  Deleting SharePoint list '_SELFTEST_LIST'...")
  try: await delete_list(ctx, "_SELFTEST_LIST")
  except: pass
  
  yield log("  Deleting SharePoint document library '_SELFTEST_DOCS'...")
  try: await delete_document_library(ctx, "_SELFTEST_DOCS")
  except: pass
  
  # Finalize job
  stream_logger.log_function_footer()
  writer.finalize()
```

## Implementation Checklist

### SharePoint API Prerequisites (verify before implementing)

- [ ] Verify `ctx.web.lists.add()` for document library creation
- [ ] Verify `list.fields.add_number()` for custom Crawl field
- [ ] Verify `list.fields.add_text()` for Status field on list
- [ ] Verify `file.moveto()` for MOVE operation
- [ ] Verify `file.rename()` or `listitem.update({"FileLeafRef": new_name})` for RENAME
- [ ] Verify site page creation via `ctx.web.lists.get_by_title("Site Pages").items.add()`
- [ ] Verify SharePoint permissions: `Sites.FullControl` or `Sites.Manage` required
- [ ] CRAWLER_SELFTEST_SHAREPOINT_SITE configured in env

### Implementation

- [ ] Add imports: `shutil`, `httpx`
- [ ] Add `SNAPSHOT_BASE_PATH` constant
- [ ] Add selftest to router docs endpoint list: `{"path": "/selftest", "desc": "Self-test", "formats": ["stream"]}`
- [ ] Add "Run Selftest" button to crawler UI toolbar
- [ ] Implement SharePoint write helper functions (17 functions)
- [ ] Implement snapshot save/restore/compare/cleanup functions (5 functions)
- [ ] Implement mutation propagation wait helper (poll every 5s)
- [ ] Implement `wait_for_vector_store_ready()` helper (per CRST-DD-07)
- [ ] Implement test runner with all 17 phases
- [ ] Implement cleanup logic in finally block

### Test Implementation (56 tests)

**Error Cases (8):**
- [ ] I1: Missing domain_id
- [ ] I2: Invalid domain_id
- [ ] I3: Invalid scope
- [ ] I4: Invalid mode
- [ ] I5: Non-embeddable file type
- [ ] I6: Unicode filename
- [ ] I7: Same filename in subfolders
- [ ] I8: Empty domain

**Full Crawl (4):**
- [ ] A1: scope=all
- [ ] A2: scope=files
- [ ] A3: scope=lists
- [ ] A4: scope=sitepages

**source_id Filter (5):**
- [ ] B1-B5

**dry_run (4):**
- [ ] D1-D4

**Individual Steps (3):**
- [ ] E1: download_data
- [ ] E2: process_data
- [ ] E3: embed_data

**Incremental (6):**
- [ ] F1-F4: scope variations
- [ ] G1-G2: source_id variations

**Job Control (2):**
- [ ] H1: pause/resume
- [ ] H2: cancel

**Integrity Check (4):**
- [ ] J1: MISSING_ON_DISK
- [ ] J2: ORPHAN_ON_DISK
- [ ] J3: WRONG_PATH
- [ ] J4: MAP_FILE_CORRUPTED

**Advanced Edge Cases (4):**
- [ ] K1: FOLDER_RENAMED
- [ ] K2: RESTORED from recycle bin
- [ ] K3: VS_EMBEDDING_FAILED
- [ ] K4: retry_batches

**Metadata & Reports (3):**
- [ ] L1: files_metadata.json
- [ ] L2: Custom property carry-over
- [ ] L3: Crawl report creation

**Pre-flight Validation (4):**
- [ ] M1: Config validation
- [ ] M2: SharePoint connectivity (read /SiteAssets)
- [ ] M2b: SharePoint connectivity (write /SiteAssets)
- [ ] M3: OpenAI connectivity (create/delete temp VS)

**Empty State (4):**
- [ ] N1: Incremental on empty
- [ ] N2: Vector store empty after incremental
- [ ] N3: Full crawl on empty
- [ ] N4: Final vector store state

**Map File Structure (3):**
- [ ] O1: sharepoint_map.csv columns
- [ ] O2: files_map.csv columns
- [ ] O3: vectorstore_map.csv columns

### Verification

- [ ] Run selftest, verify all 57 tests pass
- [ ] Verify cleanup removes all SharePoint artifacts (_SELFTEST_DOCS, _SELFTEST_LIST, site pages)
- [ ] Verify cleanup removes _SELFTEST domain folder
- [ ] Verify cleanup removes vector store and files
- [ ] Verify cleanup removes _selftest_snapshots/ folder
- [ ] Run selftest twice consecutively to verify idempotency
- [ ] Verify no orphan files in crawler/ after cleanup

## Spec Changes

**[2025-01-03 12:22]**
- Added: M2b SharePoint write verification (upload + delete to /SiteAssets)
- Changed: M2 now tests read access to /SiteAssets
- Changed: Total tests from 56 to 57

**[2025-01-02 20:05]**
- Added: Test artifacts for I5 (non_embeddable.zip), I6 (file_测试.txt), I7 (subfolder/file1.txt)
- Updated: Snapshot definitions for 9 files total (5 with Crawl=1)
- Fixed: Implementation checklist (17 phases, 56 tests, wait_for_vector_store_ready helper)

**[2025-01-02 20:03]**
- Changed: C section marked as implicit (0 tests) - verified by A1 snapshot
- Changed: Total tests from 60 to 56

**[2025-01-02 19:58]**
- Added: M. Pre-flight Validation tests (3 tests) from Option A
- Added: N. Empty State tests (4 tests) from Option A
- Added: O. Map File Structure tests (3 tests) from Option A
- Added: CRST-DD-07 for wait_for_vector_store_ready()
- Added: Optional parameters skip_cleanup and phase for debugging
- Added: Cleanup step 17.7 for crawl reports deletion
- Changed: Total tests from 47 to 60, phases from 15 to 17

**[2025-01-02 19:55]**
- Added: J. Integrity Check tests (4 tests) for V2CR-FR-03/FR-04
- Added: K. Advanced Edge Cases tests (4 tests) for FOLDER_RENAMED, RESTORED, VS_EMBEDDING_FAILED, retry_batches
- Added: L. Metadata & Reports tests (3 tests) for files_metadata.json, carry-over, crawl report
- Changed: Total tests from 36 to 47
- Added: Test phases 12-14 for new test categories
- Updated: Cleanup phase renumbered to 15

**[2025-01-02 19:50]**
- Added: Design decisions CRST-DD-01 to DD-06 (scope+source_id, folder snapshots, skip embed on failure, 5s poll)
- Fixed: sitepage_sources structure - added sharepoint_url_part, corrected filter syntax
- Changed: Snapshots from dict definitions to actual folder copies with shutil
- Added: Error cases I5-I8 (non-embeddable, unicode, subfolders, empty domain)
- Fixed: dry_run test prerequisites (D3/D4 need E1/E2 states)
- Added: Mutation propagation wait helper (5s poll, 60s max)
- Added: Detailed implementation checklist with SharePoint API verification

**[2025-01-02 19:00]**
- Initial specification created
