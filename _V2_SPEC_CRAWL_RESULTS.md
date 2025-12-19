# V2 Crawl Results Specification

**Goal**: Archive and retrieve crawl state snapshots (map files + metadata) for auditing and debugging.
**Target file**: `/src/routers_v2/crawler.py` (extend existing router)

**Depends on:**
- `_V2_SPEC_ROUTERS.md` for endpoint design patterns and crawler process specification

## Table of Contents

1. Overview
2. Scenario
3. Design Decisions
4. Functional Requirements
5. Implementation Guarantees
6. Archive Structure
7. Endpoints
8. Implementation Details
9. Key Mechanisms
10. Endpoint Result Schemas

## Overview

The `/v2/crawler/crawl` endpoint creates a timestamped zip archive after completion containing:
- All `*_map.csv` files from affected sources
- A `crawl.json` metadata file describing the crawl parameters and results

Archives are stored in `PERSISTENT_STORAGE_PATH/crawl_results/` and can be listed/queried via the `/v2/crawler/crawl_results` endpoint.

**Note:** Individual actions (`download_data`, `process_data`, `embed_data`) do NOT create archives. Only the combined `/crawl` endpoint archives state.

## Scenario

**Real-world problem:**
- Need to audit what was crawled and when
- Need to debug crawl failures by examining map file state at time of crawl
- Need to compare map files between crawls to identify changes
- Need historical record without keeping full file content

**What we don't want:**
- Storing actual crawled file content (too large)
- Complex database schema (use filesystem + JSON)
- Separate archive creation endpoint (automatic after each crawl action)

## Design Decisions

**V2CW-DD-01:** Flat folder structure for archives. All zips in single `crawl_results/` folder - filename contains all metadata needed for filtering.

**V2CW-DD-02:** Archive created even on failure. Captures map file state at time of error for debugging.

**V2CW-DD-03:** No separate archive trigger endpoint. Archives created automatically - reduces risk of forgetting to archive.

**V2CW-DD-04:** crawl_result_id is filename-based. No separate ID generation - filename IS the unique identifier.

**V2CW-DD-05:** Map files stored with folder structure preserved. Allows easy identification of source within archive.

**V2CW-DD-06:** Archive created as step 4 in `/crawl` flow (after embed, before end_json). The `crawl_result_id` and `crawl_result_url` are included in the end_json result.

**V2CW-DD-07:** No archive on cancellation. Cancelled jobs are user-interrupted - partial state not useful for auditing.


## Functional Requirements

**V2CW-FR-01: Automatic Archive Creation**
- After `/v2/crawler/crawl` endpoint completes, create a zip archive
- Archive contains all `*_map.csv` files from affected sources
- Archive contains `crawl.json` with crawl metadata
- Failed crawls still create archive (captures error state)
- Individual actions (`download_data`, `process_data`, `embed_data`) do NOT create archives

**V2CW-FR-02: Archive Storage**
- Path: `PERSISTENT_STORAGE_PATH/crawl_results/`
- Filename: `[TIMESTAMP]_[DOMAIN_ID]_[SCOPE]_[MODE].zip`
- Timestamp format: `YYYY-MM-DD_HH-MM-SS`

**V2CW-FR-03: List Crawl Results**
- List all crawl result archives for a given domain
- Optionally filter by scope

**V2CW-FR-04: Get Crawl Result**
- Retrieve crawl metadata (crawl.json) by crawl_result_id
- Retrieve specific map file content from archive
- Support JSON, CSV, and HTML output formats for map files

**V2CW-FR-05: Delete Crawl Result**
- Delete a crawl result archive by crawl_result_id

## Implementation Guarantees

**V2CW-IG-01:** Archive zip file is valid and readable after creation
**V2CW-IG-02:** crawl.json contains accurate statistics matching actual map file contents
**V2CW-IG-03:** Map file paths in archive match source folder structure
**V2CW-IG-04:** List endpoint returns results sorted by timestamp (newest first)
**V2CW-IG-05:** Delete removes archive file completely from disk

## Archive Structure

### Filename Format

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

### Zip Contents

```
2024-01-15_14-25-00_TEST01_all_full.zip
├── crawl.json                              # Crawl metadata
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

### crawl.json Schema

```json
{
  "crawl_result_id": "2024-01-15_14-25-00_TEST01_all_full",
  "domain_id": "TEST01",
  "scope": "all",
  "mode": "full",
  "source_id": null,
  "job_id": "jb_42",
  "started_utc": "2024-01-15T14:25:00.000000Z",
  "finished_utc": "2024-01-15T14:30:00.000000Z",
  "ok": true,
  "error": "",
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
        {"path": "01_files/source01/sharepoint_map.csv", "url": "/v2/crawler/crawl_results/get?crawl_result_id=2024-01-15_14-25-00_TEST01_all_full&file=01_files/source01/sharepoint_map.csv"},
        {"path": "01_files/source01/files_map.csv", "url": "/v2/crawler/crawl_results/get?crawl_result_id=2024-01-15_14-25-00_TEST01_all_full&file=01_files/source01/files_map.csv"},
        {"path": "01_files/source01/vectorstore_map.csv", "url": "/v2/crawler/crawl_results/get?crawl_result_id=2024-01-15_14-25-00_TEST01_all_full&file=01_files/source01/vectorstore_map.csv"}
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
        {"path": "01_files/source02/sharepoint_map.csv", "url": "/v2/crawler/crawl_results/get?crawl_result_id=...&file=01_files/source02/sharepoint_map.csv"},
        {"path": "01_files/source02/files_map.csv", "url": "/v2/crawler/crawl_results/get?crawl_result_id=...&file=01_files/source02/files_map.csv"},
        {"path": "01_files/source02/vectorstore_map.csv", "url": "/v2/crawler/crawl_results/get?crawl_result_id=...&file=01_files/source02/vectorstore_map.csv"}
      ]
    }
  ]
}
```

## Endpoints

### GET /v2/crawler/crawl_results

List crawl archives for a domain.

**Parameters:**
- `domain_id={id}` (required) - Domain to list crawl results for
- `scope=[all|files|lists|sitepages]` (optional) - Filter by scope
- `format=[json|html]` (default=json)

**Response (format=json):**
```json
{
  "ok": true,
  "error": "",
  "data": {
    "domain_id": "TEST01",
    "crawl_results": [
      {
        "crawl_result_id": "2024-01-15_10-30-00_TEST01_all_full",
        "scope": "all",
        "mode": "full",
        "started_utc": "2024-01-15T10:30:00.000000Z",
        "finished_utc": "2024-01-15T12:23:34.000000Z",
        "ok": true
      },
      {
        "crawl_result_id": "2024-01-14_09-00-00_TEST01_files_incremental",
        "scope": "files",
        "mode": "incremental",
        "started_utc": "2024-01-14T09:00:00.000000Z",
        "finished_utc": "2024-01-14T09:00:45.000000Z",
        "ok": true
      }
    ]
  }
}
```

### GET /v2/crawler/crawl_results/get

Get crawl details or map file content.

**Parameters:**
- `crawl_result_id={id}` (required) - Crawl archive identifier (filename without .zip)
- `file={path}` (optional) - Specific map file to retrieve (e.g., `01_files/source01/files_map.csv`)
- `format=[json|csv|html]` (default=json)

**Response without file param (returns crawl.json):**
```json
{
  "ok": true,
  "error": "",
  "data": {
    "crawl_result_id": "2024-01-15_14-25-00_TEST01_all_full",
    "domain_id": "TEST01",
    "scope": "all",
    "...": "full crawl.json content"
  }
}
```

**Response with file param (format=json):**
```json
{
  "ok": true,
  "error": "",
  "data": {
    "crawl_result_id": "2024-01-15_14-25-00_TEST01_all_full",
    "file": "01_files/source01/files_map.csv",
    "rows": [
      {"file_relative_path": "...", "file_size": 12345, "last_modified_utc": "...", "...": "..."},
      {"file_relative_path": "...", "file_size": 67890, "last_modified_utc": "...", "...": "..."}
    ]
  }
}
```

**Response with file param (format=csv):**
- Content-Type: `text/csv`
- Returns raw CSV content from archive

**Response with file param (format=html):**
- Content-Type: `text/html`
- Returns HTML table with map file data

### GET /v2/crawler/crawl_results/delete

Delete a crawl result archive.

**Parameters:**
- `crawl_result_id={id}` (required) - Crawl archive to delete

**Response:**
```json
{
  "ok": true,
  "error": "",
  "data": {
    "crawl_result_id": "2025-01-10_14-25-00_TEST01_all_full"
  }
}
```

## Implementation Details

### Archive Creation Flow

Called at the end of `/v2/crawler/crawl` endpoint only:

```python
def create_crawl_result_archive(
  domain_id: str,
  scope: str,            # all | files | lists | sitepages
  mode: str,             # full | incremental
  source_id: str | None,
  job_id: str | None,
  started_utc: str,
  finished_utc: str,
  ok: bool,
  error: str,
  sources: list[dict]
) -> str:
  """
  Create crawl archive zip file.
  Returns: crawl_result_id (filename without .zip)
  """
```

### Hardcoded Configuration

Add to `src/hardcoded_config.py`:

```python
PERSISTENT_STORAGE_PATH_CRAWL_RESULTS_SUBFOLDER: str = "crawl_results"
```

### Folder Structure

```
PERSISTENT_STORAGE_PATH/
├── domains/
├── crawler/
├── jobs/
└── crawl_results/                                    # NEW
    ├── 2024-01-15_14-25-00_TEST01_all_full.zip
    ├── 2024-01-15_14-26-30_TEST01_files_incremental.zip
    └── ...
```

## Key Mechanisms

### Crawl Result ID Generation

The `crawl_result_id` is the filename without `.zip` extension:

```python
def generate_crawl_result_id(domain_id: str, scope: str, mode: str) -> str:
  timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
  return f"{timestamp}_{domain_id}_{scope}_{mode}"
```

### Map File Collection

Collect map files based on crawl scope:

- `all` - includes `01_files/`, `02_lists/`, `03_sitepages/`
- `files` - includes `01_files/` only
- `lists` - includes `02_lists/` only
- `sitepages` - includes `03_sitepages/` only

If `source_id` is specified, only include that source's folder.

### dry_run Behavior

When `dry_run=true`: Archive creation function is called but skips actual archive creation. Dry runs are for preview only.

### Cancellation Behavior

When job is cancelled: No archive is created. Cancelled jobs do not produce archives.

### Failure Behavior

When crawl fails (error during download/process/embed): Archive is still created, capturing partial state at time of failure. This aids debugging.


## Endpoint Result Schemas

Unified schema for all crawler endpoints: `/download_data`, `/process_data`, `/embed_data`, `/crawl`

```json
{
  "ok": true,
  "error": "",
  "data": {
    "domain_id": "TEST01",
    "mode": "incremental",
    "scope": "all",
    "source_id": null,
    "vector_store_id": "vs_abc123",
    "crawl_result_id": "2024-01-15_14-25-00_TEST01_all_incremental",
    "crawl_result_url": "/v2/crawler/crawl_results/get?crawl_result_id=2024-01-15_14-25-00_TEST01_all_incremental",
    "archive": {"ok": true, "error": "", "duration_seconds": 2},
    "sources": [
      {
        "source_type": "file_sources",
        "source_id": "source01",
        "download": {"ok": true, "error": "", "duration_seconds": 30, "items_total": 150, "items_added": 10, "items_changed": 5, "items_removed": 2, "items_skipped": 0, "items_failed": 1},
        "process": {"ok": true, "error": "", "duration_seconds": 15, "items_total": 150, "items_processed": 148, "items_skipped": 0, "items_failed": 2},
        "embed": {"ok": true, "error": "", "duration_seconds": 45, "items_total": 148, "items_added": 10, "items_changed": 5, "items_removed": 2, "items_skipped": 0, "items_failed": 1}
      }
    ]
  }
}
```

**Field presence by endpoint:**
- `vector_store_id` - only `/embed_data` and `/crawl`
- `crawl_result_id`, `crawl_result_url` - only `/crawl` (null when dry_run=true)
- `archive` - only `/crawl` (top-level, single operation for entire crawl)
- `sources[].download` - only `/download_data` and `/crawl`
- `sources[].process` - only `/process_data` and `/crawl`
- `sources[].embed` - only `/embed_data` and `/crawl`

**Action fields:**
- `ok` - action succeeded for this source
- `error` - error message if failed
- `duration_seconds` - time taken for this source
- `items_total` - total items in scope
- `items_added` - new items (download/embed)
- `items_changed` - modified items (download/embed)
- `items_removed` - deleted items (download/embed)
- `items_processed` - items processed (process only)
- `items_skipped` - items skipped (precondition not met)
- `items_failed` - items that failed

**Notes:**
- On failure, top-level `ok=false` and `error` contains error; partial results in `data`
- Per-source `ok=false` indicates that specific source failed while others may succeed
