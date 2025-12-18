# V2 Crawler Crawls Specification

**Goal**: Archive and retrieve crawl state snapshots (map files + metadata) for auditing and debugging.
**Target file**: `/src/routers_v2/crawler.py` (extend existing router)

**Depends on:**
- `_V2_SPEC_ROUTERS.md` for endpoint design patterns and crawler process specification

## Overview

Each crawl action (download_data, process_data, embed_data, crawl) creates a timestamped zip archive containing:
- All `*_map.csv` files from affected sources
- A `crawl.json` metadata file describing the action and its parameters

Archives are stored in `PERSISTENT_STORAGE_PATH/crawls/` and can be listed/queried via the `/v2/crawler/crawls` endpoint.

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

## Functional Requirements

**V2CW-FR-01: Automatic Archive Creation**
- After each successful crawl action, create a zip archive
- Archive contains all `*_map.csv` files from affected sources
- Archive contains `crawl.json` with action metadata
- Failed crawl actions still create archive (captures error state)

**V2CW-FR-02: Archive Storage**
- Path: `PERSISTENT_STORAGE_PATH/crawls/`
- Filename: `[TIMESTAMP]_[[DOMAIN_ID]]_[ACTION]_[SCOPE]_[MODE].zip`
- Timestamp format: `YYYY-MM-DD_HH-MM-SS`

**V2CW-FR-03: List Crawls Endpoint**
- `GET /v2/crawler/crawls?domain_id={id}` - List all crawls for domain
- `GET /v2/crawler/crawls?domain_id={id}&action={action}` - Filter by action
- Returns list of `crawl.json` metadata objects

**V2CW-FR-04: Get Crawl Details Endpoint**
- `GET /v2/crawler/crawls/get?crawl_id={id}` - Get single crawl metadata
- `GET /v2/crawler/crawls/get?crawl_id={id}&file={filename}` - Get specific map file content
- Supports `format=json|csv|html`

**V2CW-FR-05: Delete Crawl Endpoint**
- `GET /v2/crawler/crawls/delete?crawl_id={id}` - Delete single crawl archive
- `GET /v2/crawler/crawls/delete?domain_id={id}&older_than={days}` - Bulk delete old archives

## Archive Structure

### Filename Format

```
[TIMESTAMP]_[[DOMAIN_ID]]_[ACTION]_[SCOPE]_[MODE].zip
```

**Components:**
- `[TIMESTAMP]` - Archive creation time (YYYY-MM-DD_HH-MM-SS)
- `[DOMAIN_ID]` - Domain identifier in brackets
- `[ACTION]` - One of: `download`, `process`, `embed`, `crawl`
- `[SCOPE]` - One of: `all`, `files`, `lists`, `sitepages`
- `[MODE]` - One of: `full`, `incremental`

**Examples:**
```
2025-01-15_14-25-00_[TEST01]_download_sitepages_full.zip
2025-01-15_14-26-30_[TEST01]_crawl_all_incremental.zip
2025-01-15_14-30-00_[PROD]_embed_files_full.zip
```

### Zip Contents

```
2025-01-15_14-25-00_[TEST01]_crawl_all_full.zip
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
  "crawl_id": "2025-01-15_14-25-00_[TEST01]_crawl_all_full",
  "domain_id": "TEST01",
  "action": "crawl",
  "scope": "all",
  "mode": "full",
  "source_id": null,
  "job_id": "jb_42",
  "started_utc": "2025-01-15T14:25:00.000000Z",
  "finished_utc": "2025-01-15T14:30:00.000000Z",
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
        {"path": "01_files/source01/sharepoint_map.csv", "url": "/v2/crawler/crawls/get?crawl_id=2025-01-15_14-25-00_[TEST01]_crawl_all_full&file=01_files/source01/sharepoint_map.csv"},
        {"path": "01_files/source01/files_map.csv", "url": "/v2/crawler/crawls/get?crawl_id=2025-01-15_14-25-00_[TEST01]_crawl_all_full&file=01_files/source01/files_map.csv"},
        {"path": "01_files/source01/vectorstore_map.csv", "url": "/v2/crawler/crawls/get?crawl_id=2025-01-15_14-25-00_[TEST01]_crawl_all_full&file=01_files/source01/vectorstore_map.csv"}
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
        {"path": "01_files/source02/sharepoint_map.csv", "url": "/v2/crawler/crawls/get?crawl_id=...&file=01_files/source02/sharepoint_map.csv"},
        {"path": "01_files/source02/files_map.csv", "url": "/v2/crawler/crawls/get?crawl_id=...&file=01_files/source02/files_map.csv"},
        {"path": "01_files/source02/vectorstore_map.csv", "url": "/v2/crawler/crawls/get?crawl_id=...&file=01_files/source02/vectorstore_map.csv"}
      ]
    }
  ]
}
```

## Endpoints

### GET /v2/crawler/crawls

List crawl archives for a domain.

**Parameters:**
- `domain_id={id}` (required) - Domain to list crawls for
- `action=[download|process|embed|crawl]` (optional) - Filter by action type
- `scope=[all|files|lists|sitepages]` (optional) - Filter by scope
- `limit={n}` (optional, default=50) - Max results
- `format=[json|html]` (default=json)

**Response (format=json):**
```json
{
  "ok": true,
  "error": "",
  "data": {
    "domain_id": "TEST01",
    "crawls": [
      {
        "crawl_id": "2025-01-15_14-25-00_[TEST01]_crawl_all_full",
        "action": "crawl",
        "scope": "all",
        "mode": "full",
        "started_utc": "2025-01-15T14:25:00.000000Z",
        "duration_seconds": 300,
        "ok": true
      },
      {
        "crawl_id": "2025-01-15_12-00-00_[TEST01]_download_files_incremental",
        "action": "download",
        "scope": "files",
        "mode": "incremental",
        "started_utc": "2025-01-15T12:00:00.000000Z",
        "duration_seconds": 45,
        "ok": true
      }
    ],
    "total": 2
  }
}
```

### GET /v2/crawler/crawls/get

Get crawl details or map file content.

**Parameters:**
- `crawl_id={id}` (required) - Crawl archive identifier (filename without .zip)
- `file={path}` (optional) - Specific map file to retrieve (e.g., `01_files/source01/files_map.csv`)
- `format=[json|csv|html]` (default=json)

**Response without file param (returns crawl.json):**
```json
{
  "ok": true,
  "error": "",
  "data": {
    "crawl_id": "2025-01-15_14-25-00_[TEST01]_crawl_all_full",
    "domain_id": "TEST01",
    "action": "crawl",
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
    "crawl_id": "2025-01-15_14-25-00_[TEST01]_crawl_all_full",
    "file": "01_files/source01/files_map.csv",
    "rows": [
      {"file_relative_path": "...", "file_size": 12345, "last_modified_utc": "...", "...": "..."},
      {"file_relative_path": "...", "file_size": 67890, "last_modified_utc": "...", "...": "..."}
    ],
    "total": 2
  }
}
```

**Response with file param (format=csv):**
- Content-Type: `text/csv`
- Returns raw CSV content from archive

**Response with file param (format=html):**
- Content-Type: `text/html`
- Returns HTML table with map file data

### GET /v2/crawler/crawls/delete

Delete crawl archives.

**Parameters:**
- `crawl_id={id}` - Delete single archive
- OR `domain_id={id}&older_than={days}` - Delete archives older than N days

**Response:**
```json
{
  "ok": true,
  "error": "",
  "data": {
    "deleted": ["2025-01-10_14-25-00_[TEST01]_crawl_all_full", "..."],
    "total": 5
  }
}
```

## Implementation Details

### Archive Creation Flow

Called at the end of each crawl action (download_data, process_data, embed_data, crawl):

```python
def create_crawl_archive(
  domain_id: str,
  action: str,           # download | process | embed | crawl
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
  Returns: crawl_id (filename without .zip)
  """
```

### Hardcoded Configuration

Add to `src/hardcoded_config.py`:

```python
PERSISTENT_STORAGE_PATH_CRAWLS_SUBFOLDER: str = "crawls"
```

### Folder Structure

```
PERSISTENT_STORAGE_PATH/
├── domains/
├── crawler/
├── jobs/
└── crawls/                                    # NEW
    ├── 2025-01-15_14-25-00_[TEST01]_crawl_all_full.zip
    ├── 2025-01-15_14-26-30_[TEST01]_download_files_incremental.zip
    └── ...
```

## Key Mechanisms

### Crawl ID Generation

The `crawl_id` is the filename without `.zip` extension:

```python
def generate_crawl_id(domain_id: str, action: str, scope: str, mode: str) -> str:
  timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
  return f"{timestamp}_[{domain_id}]_{action}_{scope}_{mode}"
```

### Map File Collection

Collect map files based on action scope:

| Scope | Folders Included |
|-------|------------------|
| `all` | `01_files/`, `02_lists/`, `03_sitepages/` |
| `files` | `01_files/` only |
| `lists` | `02_lists/` only |
| `sitepages` | `03_sitepages/` only |

If `source_id` is specified, only include that source's folder.

### dry_run Behavior

When `dry_run=true`: No archive is created. Dry runs are for preview only.

## Design Decisions

**V2CW-DD-01:** Flat folder structure for archives. All zips in single `crawls/` folder - filename contains all metadata needed for filtering.

**V2CW-DD-02:** Archive created even on failure. Captures map file state at time of error for debugging.

**V2CW-DD-03:** No separate archive trigger endpoint. Archives created automatically - reduces risk of forgetting to archive.

**V2CW-DD-04:** crawl_id is filename-based. No separate ID generation - filename IS the unique identifier.

**V2CW-DD-05:** Map files stored with folder structure preserved. Allows easy identification of source within archive.
