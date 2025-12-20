# V2 Common Report Functions Implementation Plan

**Goal**: Implement helper functions for report archive management
**Target file**: `/src/routers_v2/common_report_functions_v2.py`
**Test file**: `/src/routers_v2/common_report_functions_v2_test.py`

**Depends on:**
- `_V2_SPEC_REPORTS.md` for specification
- `hardcoded_config.py` for `LOCAL_PERSISTENT_STORAGE_PATH`

## Table of Contents

1. Function Signatures
2. Implementation Details
3. Review Checklist (Corner Cases)
4. Test Coverage

## Function Signatures

```python
# Dependencies
import zipfile, json, datetime, os, sys
from pathlib import Path
from typing import Optional
from routers_v2.common_logging_functions_v2 import MiddlewareLogger

# Module-level config
config = None

def set_config(app_config): ...
def get_reports_path() -> Path: ...
def _long_path(path: Path) -> Path: ...  # Windows extended path support

# Type/Folder Conversion
def get_folder_for_type(report_type: str) -> str: ...
def get_type_from_folder(folder: str) -> str: ...

# Report CRUD (all support optional MiddlewareLogger)
def create_report(report_type: str, filename: str, files: list[tuple[str, bytes]], metadata: dict, keep_folder_structure: bool = True, dry_run: bool = False, logger: Optional[MiddlewareLogger] = None) -> str: ...
def list_reports(type_filter: str = None, logger: Optional[MiddlewareLogger] = None) -> list[dict]: ...
def get_report_metadata(report_id: str, logger: Optional[MiddlewareLogger] = None) -> dict | None: ...
def get_report_file(report_id: str, file_path: str, logger: Optional[MiddlewareLogger] = None) -> bytes | None: ...
def delete_report(report_id: str, dry_run: bool = False, logger: Optional[MiddlewareLogger] = None) -> dict | None: ...
def get_report_archive_path(report_id: str) -> Path | None: ...
```

## Implementation Details

### set_config(app_config)

Sets module-level config for accessing `LOCAL_PERSISTENT_STORAGE_PATH`.

### get_reports_path() -> Path

Returns `PERSISTENT_STORAGE_PATH / "reports"`.

### _long_path(path: Path) -> Path

Windows extended path support. Adds `\\?\` prefix for paths >240 chars.

### get_folder_for_type(report_type: str) -> str

- `crawl` -> `crawls`
- `site_scan` -> `site_scans`
- Default: append `s`

### get_type_from_folder(folder: str) -> str

- `site_scans` -> `site_scan`
- Default: strip trailing `s`

### create_report()

**Input:**
- `report_type`: "crawl", "site_scan", etc.
- `filename`: Archive name without .zip
- `files`: List of (archive_path, content_bytes)
- `metadata`: Dict with title, type, ok, error and type-specific fields
- `keep_folder_structure`: Preserve paths or flatten

**Behavior:**
1. Derive folder from type
2. Generate report_id: `[folder]/[filename]`
3. Create folder if not exists
4. Add mandatory fields: `report_id`, `created_utc`, `type`
5. Build files inventory array
6. Serialize report.json
7. Create zip with report.json + files
8. Return report_id

### list_reports(type_filter: str = None) -> list[dict]

**Behavior:**
1. Return [] if reports folder doesn't exist
2. Iterate type folders (apply filter if given)
3. For each .zip file:
   - Skip corrupt zips (log warning)
   - Skip zips without report.json (log warning)
   - Skip invalid JSON (log warning)
   - Add valid report.json to results
4. Sort by created_utc descending
5. Return results

### get_report_metadata(report_id: str) -> dict | None

**Behavior:**
1. Get archive path (return None if not found)
2. Open zip, read report.json
3. Return parsed dict or None on error

### get_report_file(report_id: str, file_path: str) -> bytes | None

**Behavior:**
1. Get archive path (return None if not found)
2. Open zip, check if file_path exists
3. Return bytes or None

### delete_report(report_id: str, dry_run: bool = False, logger: Optional[MiddlewareLogger] = None) -> dict | None

**Behavior:**
1. Get archive path (return None if not found)
2. Log "Deleting report..." if logger
3. Read metadata before delete
4. If dry_run: log DRY_RUN message, return metadata without deleting
5. Delete archive file
6. Log "OK." if logger
7. Return metadata (per DD-E017)

### get_report_archive_path(report_id: str) -> Path | None

**Behavior:**
1. Validate format (must contain `/`)
2. Split into folder/filename
3. Build path: `reports_path / folder / filename.zip`
4. Return path if exists, else None

## Review Checklist (Corner Cases)

### create_report()

- **C1**: Valid inputs -> Creates zip, returns report_id
- **C2**: Empty files list -> Creates zip with only report.json
- **C3**: Files with nested paths, keep_folder_structure=True -> Paths preserved
- **C4**: Files with nested paths, keep_folder_structure=False -> Flattened to root
- **C5**: Duplicate filenames when flattened -> Last file wins
- **C6**: Unknown report_type -> Creates folder anyway (no validation)
- **C7**: Filename with special chars -> Works if filesystem allows
- **C8**: Folder doesn't exist -> Auto-creates folder
- **C9**: metadata missing mandatory fields -> Adds report_id, created_utc
- **C10**: metadata has title, type, ok, error -> Preserved in report.json
- **C11**: Binary file content -> Stored as-is
- **C12**: Empty file content (0 bytes) -> Works
- **C13**: Long path (>260 chars on Windows) -> Works with extended path prefix
- **C14**: dry_run=True -> Returns report_id but does NOT create file

### list_reports()

- **L1**: No reports exist -> Returns []
- **L2**: Reports exist, no filter -> Returns all, sorted by created_utc desc
- **L3**: Filter by existing type -> Returns only matching type
- **L4**: Filter by non-existent type -> Returns []
- **L5**: Corrupt zip file -> Skip with warning
- **L6**: Zip without report.json -> Skip with warning
- **L7**: Invalid JSON in report.json -> Skip with warning

### get_report_metadata()

- **M1**: Valid report_id -> Returns dict
- **M2**: Non-existent report_id -> Returns None
- **M3**: Invalid report_id format (no slash) -> Returns None
- **M4**: Corrupt zip -> Returns None
- **M5**: Missing report.json in zip -> Returns None

### get_report_file()

- **F1**: Valid report_id and file_path -> Returns bytes
- **F2**: Valid report_id, non-existent file_path -> Returns None
- **F3**: Non-existent report_id -> Returns None
- **F4**: report.json readable -> Returns bytes
- **F5**: Binary file -> Returns bytes correctly

### delete_report()

- **D1**: Valid report_id -> Deletes file, returns metadata
- **D2**: Non-existent report_id -> Returns None
- **D3**: File locked/permission error -> Raises exception
- **D4**: dry_run=True -> Returns metadata but does NOT delete file

### get_report_archive_path()

- **P1**: Valid existing report_id -> Returns Path
- **P2**: Valid format but non-existent -> Returns None
- **P3**: Invalid format (no slash) -> Returns None
- **P4**: Long path (>260 chars) -> Works with extended path prefix

## Test Coverage

**Test file**: `/src/routers_v2/common_report_functions_v2_test.py`

**Run command**: `python src/routers_v2/common_report_functions_v2_test.py`

**Test groups:**
1. Type/Folder Conversion (6 tests)
2. create_report() (18 tests)
3. list_reports() (10 tests)
4. get_report_metadata() (6 tests)
5. get_report_file() (6 tests)
6. delete_report() (5 tests)
7. dry_run tests (7 tests)
8. get_report_archive_path() (4 tests)
9. Long path support (6 tests)

**Total: 68 tests**

All tests use a temporary directory and clean up after completion.

## Implementation Status

- [x] Implementation complete: `common_report_functions_v2.py`
- [x] Test suite complete: `common_report_functions_v2_test.py`
- [x] All tests passing
- [x] MiddlewareLogger and dry_run support added
- [x] Long path support (Windows extended paths)
