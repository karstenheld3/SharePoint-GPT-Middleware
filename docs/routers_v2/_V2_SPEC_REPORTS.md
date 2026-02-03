# V2 Reports Specification

**Goal**: Archive and retrieve report files from various operations for auditing and debugging.
**Target file**: `/src/routers_v2/reports.py`
**Helper file**: `/src/routers_v2/common_report_functions_v2.py`

**Depends on:**
- `_V2_SPEC_ROUTERS.md` for endpoint design patterns and JSON result format

**Does not depend on:**
- `_V2_SPEC_COMMON_UI_FUNCTIONS.md` (UI spec is separate)

## Table of Contents

1. Overview
2. Scenario
3. Design Decisions
4. Functional Requirements
5. Implementation Guarantees
6. Domain Objects
7. Archive Structure
8. Python Helper Functions
9. Endpoints
10. Key Mechanisms

## Overview

Generic solution to store operation results as reports. A report is a timestamped zip archive containing:
- `report.json` - Mandatory metadata file with `title`, `type`, `created_utc`, and type-specific data
- Report-specific files (`.csv`, `.json`, etc.)

Report archives stored in `PERSISTENT_STORAGE_PATH/reports/[folder]/` where folder = plural of type.
Reports created by internal endpoint functions only - no create endpoint exposed.

## Scenario

**Real-world problem:**
- Need to audit what was crawled and when
- Need to debug crawl failures by examining map file state at time of crawl
- Need to compare map files between crawls to identify changes
- Need historical record without keeping full file content
- Need to audit SharePoint site scanning reports

**What we don't want:**
- Storing actual crawled file content (too large)
- Complex database schema (use filesystem + JSON)
- Separate operation-dependent archiving solutions
- Elaborate filtering or search
- File uploading via API
- External create endpoint (internal use only)

## Design Decisions

**V2RP-DD-01:** Folder-per-type structure. Reports stored in `reports/[folder]/` where folder is plural form of type (e.g., type=`crawl` -> folder=`crawls`).

**V2RP-DD-02:** report_id format. `[folder]/[filename_without_zip]` (e.g., `crawls/2024-01-15_14-25-00_TEST01_all_full`).

**V2RP-DD-03:** No create endpoint. Reports created by internal Python functions called from other routers.

**V2RP-DD-04:** Minimal metadata. Only `report_id`, `title`, `type`, `created_utc`, `ok`, `error`, `files` are mandatory. Rest is type-specific.

**V2RP-DD-05:** Result pattern for display. UI shows Result column: `-` (pending), `OK` (success), `FAIL` (failure) - same as Jobs UI.

## Functional Requirements

**V2RP-FR-01:** List all reports, sorted by created_utc descending (newest first)
**V2RP-FR-02:** Filter reports by type (optional)
**V2RP-FR-03:** Get single report metadata (report.json content)
**V2RP-FR-04:** Get file from report archive
**V2RP-FR-05:** Download report as ZIP
**V2RP-FR-06:** Delete single report
**V2RP-FR-07:** Internal function to create report archive

## Implementation Guarantees

**V2RP-IG-01:** Archive zip files are valid and readable
**V2RP-IG-02:** report.json contains mandatory fields: report_id, title, type, created_utc, ok, error, files
**V2RP-IG-03:** File paths in archive preserved when keep_folder_structure=true
**V2RP-IG-04:** List endpoint returns reports sorted by created_utc (newest first)
**V2RP-IG-05:** Delete removes report archive completely from disk

## Domain Objects

### Report (minimal mandatory fields)


```
report_id: string       # "[folder]/[filename]" e.g. "crawls/2024-01-15_14-25-00_TEST01_all_full"
title: string           # Human readable title
type: string            # Report type (singular): "crawl", "site_scan", etc.
created_utc: string     # ISO timestamp when archive was created
ok: bool                # true = success, false = failure
error: string           # Error message if ok=false, empty otherwise
files: array            # Flattened inventory of zip archive contents
  └─ filename: string           # File name only (e.g., "sharepoint_map.csv")
  └─ file_path: string          # Path within archive (e.g., "01_files/source01/sharepoint_map.csv")
  └─ file_size: int             # Size in bytes
  └─ last_modified_utc: string  # ISO timestamp of file modification
```

Plus type-specific fields (see Archive Structure).

### Type-to-Folder Mapping

- **crawl** -> `crawls`
- **site_scan** -> `site_scans`

## Archive Structure

### Folder Structure

```
PERSISTENT_STORAGE_PATH/reports/
├── crawls/
│   ├── 2024-01-15_14-25-00_TEST01_all_full.zip
│   │   ├── report.json
│   │   └── ...
│   └── 2024-01-15_14-26-30_TEST01_files_incremental.zip
│       ├── report.json
│       └── ...
└── site_scans/
    └── 2025-03-12_10-12-53_legal-contracts_security.zip
        ├── report.json
        └── ...
```

### report.json Schema (Crawl Type)

```json
{
  "report_id": "crawls/2024-01-15_14-25-00_TEST01_all_full",
  "title": "TEST01 full crawl",
  "type": "crawl",
  "created_utc": "2024-01-15T14:30:00.000000Z",
  "ok": true,
  "error": "",
  "files": [
    {"filename": "report.json", "file_path": "report.json", "file_size": 2048, "last_modified_utc": "2024-01-15T14:30:00.000000Z"},
    {"filename": "sharepoint_map.csv", "file_path": "01_files/source01/sharepoint_map.csv", "file_size": 15360, "last_modified_utc": "2024-01-15T14:28:00.000000Z"},
    {"filename": "files_map.csv", "file_path": "01_files/source01/files_map.csv", "file_size": 12288, "last_modified_utc": "2024-01-15T14:28:00.000000Z"},
    {"filename": "vectorstore_map.csv", "file_path": "01_files/source01/vectorstore_map.csv", "file_size": 8192, "last_modified_utc": "2024-01-15T14:29:00.000000Z"}
  ],
  "domain_id": "TEST01",
  "scope": "all",
  "mode": "full",
  "source_id": null,
  "job_id": "jb_42",
  "started_utc": "2024-01-15T14:25:00.000000Z",
  "finished_utc": "2024-01-15T14:30:00.000000Z",
  "sources": [
    {
      "source_type": "file_sources",
      "source_id": "source01",
      "items_total": 150,
      "items_added": 10,
      "items_changed": 5,
      "items_removed": 2,
      "items_failed": 1,
      "map_files": [
        {"path": "01_files/source01/sharepoint_map.csv", "url": "/v2/reports/file?report_id=crawls/2024-01-15_14-25-00_TEST01_all_full&file_path=01_files/source01/sharepoint_map.csv"},
        {"path": "01_files/source01/files_map.csv", "url": "/v2/reports/file?report_id=crawls/2024-01-15_14-25-00_TEST01_all_full&file_path=01_files/source01/files_map.csv"},
        {"path": "01_files/source01/vectorstore_map.csv", "url": "/v2/reports/file?report_id=crawls/2024-01-15_14-25-00_TEST01_all_full&file_path=01_files/source01/vectorstore_map.csv"}
      ]
    },
    {
      "source_type": "file_sources",
      "source_id": "source02",
      "items_total": 45,
      "items_added": 0,
      "items_changed": 0,
      "items_removed": 0,
      "items_failed": 0,
      "map_files": [
        {"path": "01_files/source02/sharepoint_map.csv", "url": "/v2/reports/file?report_id=...&file_path=01_files/source02/sharepoint_map.csv"},
        {"path": "01_files/source02/files_map.csv", "url": "/v2/reports/file?report_id=...&file_path=01_files/source02/files_map.csv"},
        {"path": "01_files/source02/vectorstore_map.csv", "url": "/v2/reports/file?report_id=...&file_path=01_files/source02/vectorstore_map.csv"}
      ]
    }
  ]
}
```

### Crawl Archive Zip Contents

```
2024-01-15_14-25-00_TEST01_all_full.zip
├── report.json
├── 01_files/
│   ├── source01/
│   │   ├── sharepoint_map.csv
│   │   ├── files_map.csv
│   │   └── vectorstore_map.csv
│   └── source02/
│       ├── sharepoint_map.csv
│       ├── files_map.csv
│       └── vectorstore_map.csv
├── 02_lists/
│   └── list01/
│       ├── sharepoint_map.csv
│       ├── files_map.csv
│       └── vectorstore_map.csv
└── 03_sitepages/
    └── pages01/
        ├── sharepoint_map.csv
        ├── files_map.csv
        └── vectorstore_map.csv
```

### Crawl Archive Filename Format

```
[TIMESTAMP]_[DOMAIN_ID]_[SCOPE]_[MODE].zip
```

**Components:**
- `[TIMESTAMP]` - Archive creation time (YYYY-MM-DD_HH-MM-SS)
- `[DOMAIN_ID]` - Domain identifier
- `[SCOPE]` - One of: `all`, `files`, `lists`, `sitepages`
- `[MODE]` - One of: `full`, `incremental`

**Examples:**
```
2024-01-15_14-25-00_TEST01_all_full.zip
2024-01-15_14-26-30_TEST01_files_incremental.zip
2024-01-15_14-30-00_PROD_sitepages_full.zip
```

### report.json Schema (Site Scan Type)

```json
{
  "report_id": "site_scans/2025-03-12_10-12-53_legal-contracts_security",
  "title": "'/sites/HR-Central' Security Scan",
  "type": "site_scan",
  "created_utc": "2025-03-12T10:15:00.000000Z",
  "ok": true,
  "error": "",
  "files": [
    {"filename": "report.json", "file_path": "report.json", "file_size": 1024, "last_modified_utc": "2025-03-12T10:15:00.000000Z"},
    {"filename": "permissions.csv", "file_path": "permissions.csv", "file_size": 8192, "last_modified_utc": "2025-03-12T10:14:00.000000Z"}
  ],
  "site_url": "https://example.sharepoint.com/sites/HR-Central",
  "scope": "security",
  "job_id": "jb_112",
  "started_utc": "2025-03-12T10:12:53.000000Z",
  "finished_utc": "2025-03-12T10:15:00.000000Z",
  "security": {...}
}
```

### Site Scan Archive Filename Format

```
[TIMESTAMP]_[SITE_ID]_[SCOPE].zip
```

**Components:**
- `[TIMESTAMP]` - Archive creation time (YYYY-MM-DD_HH-MM-SS)
- `[SITE_ID]` - Site identifier
- `[SCOPE]` - One of: `all`, `content`, `security`, `files`

**Examples:**
```
2025-03-12_10-12-53_legal-contracts_security.zip
2025-03-23_09-42-12_hr-central_all.zip
```

## Python Helper Functions

**Target file:** `/src/routers_v2/common_report_functions_v2.py`

### create_report()

```python
def create_report(
  report_type: str,                           # "crawl", "site_scan"
  filename: str,                              # "2024-01-15_14-25-00_TEST01_all_full" (without .zip)
  files: list[tuple[str, bytes]],             # [(archive_path, content), ...]
  metadata: dict,                             # Type-specific metadata (merged with mandatory fields)
  keep_folder_structure: bool = True,         # If True, preserve file paths; if False, flatten to root
  dry_run: bool = False,                      # If True, simulate without writing to disk
  logger: Optional[MiddlewareLogger] = None   # Optional logger for output
) -> str:                                     # Returns report_id
```

Creates zip archive with report.json and provided files.

**Behavior:**
- Derives folder from type: `crawl` -> `crawls`, `site_scan` -> `site_scans`
- Generates report_id: `[folder]/[filename]`
- Adds mandatory fields to metadata: `report_id`, `created_utc`
- If `keep_folder_structure=True`: files added with their archive_path
- If `keep_folder_structure=False`: files added to archive root (basename only)

### list_reports()

```python
def list_reports(type_filter: str = None, logger: Optional[MiddlewareLogger] = None) -> list[dict]:
```

Lists all reports, optionally filtered by type. Returns list of report.json contents, sorted by created_utc descending.

### get_report_metadata()

```python
def get_report_metadata(report_id: str, logger: Optional[MiddlewareLogger] = None) -> dict | None:
```

Reads and returns report.json content from archive. Returns None if not found.

### get_report_file()

```python
def get_report_file(report_id: str, file_path: str, logger: Optional[MiddlewareLogger] = None) -> bytes | None:
```

Reads specific file from archive. Returns None if not found.

### delete_report()

```python
def delete_report(report_id: str, dry_run: bool = False, logger: Optional[MiddlewareLogger] = None) -> dict | None:
```

Deletes archive file. Returns deleted report metadata (per DD-E017), or None if not found.

### get_report_archive_path()

```python
def get_report_archive_path(report_id: str) -> Path | None:
```

Returns full filesystem path to archive. Returns None if not found.

## Endpoints

### GET /v2/reports

List reports. Bare GET (no params) returns self-documentation.

**Parameters:**
- `type` (optional) - Filter by report type
- `format=[json|html|ui]` (default=json)

**Response (format=json):**
```json
{
  "ok": true,
  "error": "",
  "data": [
    {
      "report_id": "crawls/2024-01-15_14-25-00_TEST01_all_full",
      "title": "TEST01 full crawl",
      "type": "crawl",
      "created_utc": "2024-01-15T14:30:00.000000Z",
      "ok": true,
      "error": "",
      ...type-specific fields...
    }
  ]
}
```

### GET /v2/reports/get

Get report metadata (report.json content). Bare GET returns self-documentation.

**Parameters:**
- `report_id` (required) - Report identifier
- `format=[json|html]` (default=json)

**Response (format=json):**
```json
{
  "ok": true,
  "error": "",
  "data": {
    "report_id": "crawls/2024-01-15_14-25-00_TEST01_all_full",
    "title": "TEST01 full crawl",
    ...
  }
}
```

### GET /v2/reports/file

Get specific file from report archive. Bare GET returns self-documentation.

**Parameters:**
- `report_id` (required) - Report identifier
- `file_path` (required) - File path within archive
- `format=[json|html|raw]` (default=raw)

**Response (format=raw):** File content with appropriate Content-Type

### GET /v2/reports/download

Download report archive as ZIP. Bare GET returns self-documentation.

**Parameters:**
- `report_id` (required) - Report identifier

**Response:** ZIP file with Content-Disposition header

**Error Response (404):**
```json
{"ok": false, "error": "Report 'crawls/invalid_id' not found.", "data": {}}
```

### DELETE, GET /v2/reports/delete

Delete report. Bare GET returns self-documentation.

**Parameters:**
- `report_id` (required) - Report identifier

**Response (format=json):**
```json
{
  "ok": true,
  "error": "",
  "data": {
    "report_id": "crawls/2024-01-15_14-25-00_TEST01_all_full",
    "title": "TEST01 full crawl",
    "type": "crawl",
    "created_utc": "2024-01-15T14:30:00.000000Z",
    "ok": true,
    "error": "",
    "files": [...],
    ...type-specific fields...
  }
}
```

## Key Mechanisms

### Type-to-Folder Conversion

```python
def get_folder_for_type(report_type: str) -> str:
  # Simple pluralization: add 's' or handle special cases
  if report_type == "site_scan": return "site_scans"
  return report_type + "s"

def get_type_from_folder(folder: str) -> str:
  if folder == "site_scans": return "site_scan"
  return folder.rstrip("s")
```

### Report ID Generation

```
report_id = f"{folder}/{filename}"
```

Example: `crawls/2024-01-15_14-25-00_TEST01_all_full`

### Archive Path Resolution

```python
def resolve_archive_path(report_id: str) -> Path:
  folder, filename = report_id.split("/", 1)
  return PERSISTENT_STORAGE_PATH / "reports" / folder / f"{filename}.zip"
```

### Result Display Logic (for UI)

```
if report.ok is None or report not finished: display "-"
elif report.ok == true: display "OK"
else: display "FAIL"
```

### Cross-Router Report Links

Other routers can link to report results using the `/v2/reports/get` endpoint:

**View Results (HTML page):**
```
/v2/reports/get?report_id={report_id}&format=html
```

**Download ZIP:**
```
/v2/reports/download?report_id={report_id}
```

**Example: Sites router security scan result links**
- Sites router stores `last_security_scan_report_id` in site.json
- UI renders "View Results" link: `/v2/reports/get?report_id=...&format=html`
- UI renders "Download Zip" link: `/v2/reports/download?report_id=...`
