# Crawler Technical Specification Version 2

**Goal**: Specify the crawling process, change detection, edge case handling, and local storage synchronization for SharePoint-GPT-Middleware.

**Target file**: `/src/routers_v2/crawler.py`

**Depends on:**
- `_V2_SPEC_ROUTERS.md` for endpoint definitions and streaming job infrastructure
- `hardcoded_config.py` for path constants

**Does not depend on:**
- V1 crawler implementations

## Table of Contents

1. Scenario
2. Domain Objects
3. Functional Requirements
4. Design Decisions
5. Implementation Guarantees
6. Local Storage Structure
7. Map Files
8. Source-Specific Processing
9. Crawling Process Steps
10. Complete List of Edge Cases
11. Edge Case Handling Mechanism
12. Integrity Check
13. files_metadata.json Update
14. Spec Changes

## Scenario

**Problem:** SharePoint content changes frequently - files are added, removed, renamed, moved, updated, restored from recycle bin, or replaced. The crawler must detect all these changes reliably and keep local storage synchronized with SharePoint while maintaining vector store consistency.

**Solution:** A robust crawling process that:
- Uses `sharepoint_unique_file_id` as immutable identifier for change detection
- Compares all relevant fields (`filename`, `server_relative_url`, `file_size`, `last_modified_utc`)
- Includes sync-check after download to verify local storage matches SharePoint
- Falls back to brute-force re-download when inconsistencies are detected

**What we don't want:**
- Silent data loss (files removed from vector store without logging)
- Orphaned local files (files on disk not tracked in map files)
- Stale embeddings (vector store contains outdated content)
- Complex recovery procedures (self-healing preferred)

## Domain Objects

### Domain

A **Domain** represents a knowledge base configuration for crawling SharePoint content and embedding it into OpenAI vector stores.

**Storage:** `PERSISTENT_STORAGE_PATH/domains/[DOMAIN_ID]/`
**Definition:** `domain.json` - contains SharePoint connection, source definitions, vector store configuration
**Metadata:** `files_metadata.json` - joins embedded file data with extracted metadata

**Key properties:**
- `domain_id` - unique identifier (derived from folder name)
- `file_sources` - list of SharePoint document library sources
- `list_sources` - list of SharePoint list sources
- `sitepage_sources` - list of SharePoint site page sources
- `vector_store_id` - target OpenAI vector store for embeddings

**domain.json schema:**

```json
{
  "name": "My Domain",
  "description": "Domain description",
  "vector_store_name": "my-vector-store",
  "vector_store_id": "vs_abc123",
  "file_sources": [
    {
      "source_id": "docs_main",
      "site_url": "https://contoso.sharepoint.com/sites/MyProject",
      "sharepoint_url_part": "/Shared Documents",
      "filter": ""
    }
  ],
  "list_sources": [
    {
      "source_id": "tasks",
      "site_url": "https://contoso.sharepoint.com/sites/MyProject",
      "list_name": "Project Tasks",
      "filter": "Status eq 'Active'"
    }
  ],
  "sitepage_sources": [
    {
      "source_id": "pages_all",
      "site_url": "https://contoso.sharepoint.com/sites/MyProject",
      "sharepoint_url_part": "/SitePages",
      "filter": ""
    }
  ]
}
```

**Source field definitions:**

- `source_id` (All) - Unique identifier for this source within the domain
- `site_url` (All) - SharePoint site URL (e.g., `https://contoso.sharepoint.com/sites/MyProject`)
- `sharepoint_url_part` (FileSource, SitePageSource) - **URL path** to the library (e.g., `/Shared Documents`, `/SiteAssets`, `/SitePages`). Not the display title.
- `list_name` (ListSource) - Display title of the SharePoint list (e.g., `Project Tasks`)
- `filter` (All) - OData filter expression (empty string for no filter)

### Crawl

A **Crawl** is a single execution of the crawling process for a domain. It performs download, processing, and embedding steps.

**Trigger:** `/v2/crawler/crawl?domain_id={id}&mode=[full|incremental]&scope=[all|files|lists|sitepages]`
**Job:** Creates a streaming job (`jb_*`) that can be monitored, paused, resumed, or cancelled

**Crawl steps:**
1. **Download** - fetch files from SharePoint to local storage, update `sharepoint_map.csv` and `files_map.csv`
2. **Process** - convert/clean files for embedding (lists → markdown, sitepages → cleaned HTML)
3. **Embed** - upload files to OpenAI, add to vector store, update `vectorstore_map.csv`
4. **Archive** - create crawl result archive (only for `/crawl` endpoint)

**Modes:**
- `full` - re-crawl everything, delete existing local files first
- `incremental` - only process changes since last crawl (uses map file comparison)

**Scopes:**
- `all` - crawl all source types
- `files` - crawl only `file_sources`
- `lists` - crawl only `list_sources`
- `sitepages` - crawl only `sitepage_sources`

### Crawl Report

A **Crawl Report** is a timestamped archive created after a `/crawl` endpoint completes. It captures the state of all map files at the time of crawl for auditing and debugging.

**Storage:** `PERSISTENT_STORAGE_PATH/reports/crawls/[filename].zip`
**Report ID format:** `crawls/[TIMESTAMP]_[DOMAIN_ID]_[SCOPE]_[MODE]` (e.g., `crawls/2025-01-15_14-25-00_TEST01_all_full`)
**Specification:** See `_V2_SPEC_REPORTS.md` (type=crawl)

**Contents:**
- `report.json` - crawl metadata (parameters, timing, per-source statistics)
- `*_map.csv` files - snapshot of map files at crawl completion

**Not created when:**
- Individual actions (`download_data`, `process_data`, `embed_data`) - no archive
- `dry_run=true` - no archive
- Job cancelled - no archive

### files_metadata.json

The **files_metadata.json** file stores metadata for all embedded files in a domain. It joins data from map files with extracted metadata (custom properties).

**Storage:** `PERSISTENT_STORAGE_PATH/domains/[DOMAIN_ID]/files_metadata.json`
**Format:** Flat array of objects, one per embedded file version

**Relationship to crawl:**
- **Updated by:** `embed_data` step (after successful upload to vector store)
- **Keyed by:** `openai_file_id` (allows multiple versions of same SharePoint file)
- **Linked by:** `sharepoint_unique_file_id` (enables carry-over of custom properties on file update)

**V3 fields:**
- `sharepoint_listitem_id`, `sharepoint_unique_file_id`, `openai_file_id`
- `file_relative_path`, `url`, `raw_url`, `server_relative_url`
- `filename`, `file_type`, `file_size`, `last_modified_utc`, `last_modified_timestamp`

**V2 extensions:**
- `embedded_utc` - when file was embedded
- `source_id` - source within domain
- `source_type` - `file_sources`, `list_sources`, or `sitepage_sources`

**Custom properties:**
- Any field not in standard set is preserved on file update (carry-over by `sharepoint_unique_file_id`)

### Relationships

```
SharePoint ──► download_data ──► sharepoint_map.csv ─┐
                              └─► files_map.csv      │
                                                     │
               process_data ────► files_map.csv      │
                                                     ├──► Domain
               embed_data ──────► vectorstore_map.csv│   (files_metadata.json)
                              └─► files_metadata.json┘

               archive ─────────────────────────────────► Crawl Result
                                                          (crawl.json + *_map.csv)
```

## Functional Requirements

**V2CR-FR-01: Change Detection by Immutable ID**
- Use `sharepoint_unique_file_id` as primary key for comparing SharePoint and local state
- Detect ADDED, REMOVED, CHANGED states for each file

**V2CR-FR-02: Complete Field Comparison**
- Compare `filename`, `server_relative_url`, `file_size`, `last_modified_utc` to detect changes
- Any field difference triggers CHANGED state (re-download required)

**V2CR-FR-03: Integrity Check After Download**
- Verify local storage matches `sharepoint_map.csv` after every download step
- Detect and correct: MISSING_IN_MAP, MISSING_ON_DISK, ORPHAN_ON_DISK, WRONG_PATH

**V2CR-FR-04: Self-Healing Corrections**
- Re-download missing files automatically
- Delete orphan files automatically
- Move misplaced files to correct paths automatically

**V2CR-FR-05: Graceful Map File Operations**
- Buffered append writes using `MapFileWriter` class
- Write header once at start (atomic: temp file + rename)
- Append rows in batches (every `APPEND_TO_MAP_FILES_EVERY_X_LINES` items)
- Force flush on: header creation, first item, last item
- Retry on concurrency errors
- Fallback to `mode=full` on corrupted/missing map files

**V2CR-FR-06: files_metadata.json Carry-Over**
- Preserve custom properties when file is updated (same `sharepoint_unique_file_id`)
- Support multiple `openai_file_id` entries per `sharepoint_unique_file_id` (version history)

**V2CR-FR-07: Auto-Create Vector Store on First Crawl**
- If `vector_store_id` is empty on first embed, create new vector store using `vector_store_name` from domain.json
- If `vector_store_name` is also empty, use `domain_id` as the vector store name
- Write the new `vector_store_id` back to `domain.json`
- If vector store creation fails, log error and skip embedding (do not fail entire crawl)
- Log: "Created vector store '{name}' (ID={id})"

## Design Decisions

**V2CR-DD-01:** `sharepoint_unique_file_id` as immutable key. SharePoint assigns this GUID on file creation; it never changes on rename/move/update. This enables reliable tracking across all edge cases.

**V2CR-DD-02:** Four-field change detection. Comparing `filename` + `server_relative_url` + `file_size` + `last_modified_utc` catches all meaningful changes including renames and moves that don't modify content.

**V2CR-DD-03:** Integrity check always runs. No optional parameter - guarantees local storage consistency after every download regardless of mode.

**V2CR-DD-04:** Move over re-download for WRONG_PATH. Moving files is faster and preserves download timestamps; content is already correct.

**V2CR-DD-05:** files_metadata.json keyed by `openai_file_id`. Allows multiple entries for same SharePoint file (version history) while enabling carry-over of extracted metadata.

**V2CR-DD-06: URL-based library access.** Document libraries are accessed by their URL path (`sharepoint_url_part`), not by display title. This avoids issues where the library URL differs from its title (e.g., URL `/SiteAssets` vs title `Site Assets`). The implementation uses `ctx.web.get_list(server_relative_url)` instead of `ctx.web.lists.get_by_title(title)`.

## Implementation Guarantees

**V2CR-IG-01:** Local storage mirrors SharePoint folder structure after successful download + integrity check
**V2CR-IG-02:** No orphan files remain on disk after integrity check
**V2CR-IG-03:** `files_map.csv` accurately reflects disk state after integrity check
**V2CR-IG-04:** Custom properties in `files_metadata.json` survive file updates (carry-over by `sharepoint_unique_file_id`)
**V2CR-IG-05:** All edge cases are handled without data loss
**V2CR-IG-06:** All paths and filenames use `CRAWLER_HARDCODED_CONFIG` constants from `hardcoded_config.py` (no hardcoded strings)

## Local Storage Structure

Data is stored in two top-level folders:

**`PERSISTENT_STORAGE_PATH/crawler/`:**
- Local cache of downloaded files, processed for embedding

**`PERSISTENT_STORAGE_PATH/domains/`:**
- Local storage of domain definitions and embedded file metadata

**Note:** All folder and file names below are defined in `CRAWLER_HARDCODED_CONFIG` (`hardcoded_config.py`):
- `domains` = `PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER`
- `crawler` = `PERSISTENT_STORAGE_PATH_CRAWLER_SUBFOLDER`
- `01_files` = `PERSISTENT_STORAGE_PATH_DOCUMENTS_FOLDER`
- `02_lists` = `PERSISTENT_STORAGE_PATH_LISTS_FOLDER`
- `03_sitepages` = `PERSISTENT_STORAGE_PATH_SITEPAGES_FOLDER`
- `01_originals` = `PERSISTENT_STORAGE_PATH_ORIGINALS_SUBFOLDER`
- `02_embedded` = `PERSISTENT_STORAGE_PATH_EMBEDDED_SUBFOLDER`
- `03_failed` = `PERSISTENT_STORAGE_PATH_FAILED_SUBFOLDER`
- `domain.json` = `DOMAIN_JSON`
- `files_metadata.json` = `FILES_METADATA_JSON`
- `sharepoint_map.csv` = `SHAREPOINT_MAP_CSV`
- `files_map.csv` = `FILE_MAP_CSV`
- `vectorstore_map.csv` = `VECTOR_STORE_MAP_CSV`

**Folder Structure**:
```
/domains/
├── DOMAIN01/                 # Domain folder
│   ├── domain.json           # Domain definition file
│   └── files_metadata.json   # Embedded file metadata (joins data from map files and metadata extraction)
├── DOMAIN02/
│   ├── domain.json
│   └── files_metadata.json
└── ...

/crawler/
├── DOMAIN01/                 # Domain folder containing cached crawler files
├── DOMAIN02/                 # Domain folder containing cached crawler files
└── ...

/crawler/[DOMAIN_ID]/
├── 01_files/[SOURCE_ID]/
│   ├── sharepoint_map.csv    # Cached data for data in SharePoint
│   ├── files_map.csv         # Cached data for downloaded and processed files
│   ├── vectorstore_map.csv   # Cached data for embedded files in vector stores + mapping to local storage and SharePoint
│   ├── 02_embedded/          # Successfully embedded files
│   │   ├── Document1.docx
│   │   └── SubFolder/
│   │       └── AnotherDoc1.pdf
│   └── 03_failed/            # Files where embedding failed
│       ├── Document2.docx
│       └── SubFolder/
│           └── AnotherDoc2.pdf
├── 02_lists/[SOURCE_ID]/
│   ├── sharepoint_map.csv
│   ├── files_map.csv
│   ├── vectorstore_map.csv
│   ├── 01_originals/         # Original CSV exports
│   ├── 02_embedded/          # Converted Markdown files
│   └── 03_failed/
└── 03_sitepages/[SOURCE_ID]/
    ├── sharepoint_map.csv
    ├── files_map.csv
    ├── vectorstore_map.csv
    ├── 01_originals/         # Original HTML
    ├── 02_embedded/          # Processed HTML
    └── 03_failed/
```

## Map Files

Map files allow the crawler to quickly identify changes and analyze errors.

Map file types:
- `sharepoint_map.csv` - caches file metadata from SharePoint
- `files_map.csv` - caches local storage, contains file download and processing status
- `vectorstore_map.csv`- caches vector store data, contains everything in other map files + upload and embedding status

**`sharepoint_map.csv` columns:**
- `sharepoint_listitem_id` - number - SharePoint list item ID (e.g., 123)
- `sharepoint_unique_file_id` - string - GUID unique to this file (e.g., "b!abc123...")
- `filename` - string - file name with extension (e.g., "Document.docx")
- `file_type` - string - file extension without dot (e.g., "docx")
- `file_size` - number - size in bytes (e.g., 864368)
- `url` - string - URL-encoded SharePoint URL (e.g., "https://company.sharepoint.com/sites/demo/Shared%20Documents/Document.docx")
- `raw_url` - string - unencoded SharePoint URL (e.g., "https://company.sharepoint.com/sites/demo/Shared Documents/Document.docx")
- `server_relative_url` - string - path from site root (e.g., "/sites/demo/Shared Documents/Document.docx")
- `last_modified_utc` - string (ISO 8601 / RFC3339) - SharePoint UTC timestamp (e.g., "2024-01-15T10:30:00.000000Z")
- `last_modified_timestamp` - number - SharePoint Unix timestamp in seconds (e.g., 1705319400)

**`files_map.csv` columns:**
- `sharepoint_listitem_id` - number - SharePoint list item ID (e.g., 123)
- `sharepoint_unique_file_id` - string - GUID unique to this file, used as key for change detection (e.g., "b!abc123...")
- `filename` - string - file name with extension, used for rename detection (e.g., "Document.docx")
- `file_type` - string - file extension without dot (e.g., "docx")
- `server_relative_url` - string - path from site root, used for move detection (e.g., "/sites/demo/Shared Documents/Document.docx")
- `file_relative_path` - string - path relative to storage root with backslashes
  - Empty if download failed.
  - Processing failed example: "DOMAIN01\01_files\source01\03_failed\Reports\Q1.docx"
  - Succeeded example: "DOMAIN01\01_files\source01\02_embedded\Reports\Q1.docx"
- `file_size` - number - size in bytes (e.g., 864368)
- `last_modified_utc` - string (ISO 8601 / RFC3339) - SharePoint UTC timestamp (e.g., "2024-01-15T10:30:00.000000Z")
- `last_modified_timestamp` - number - SharePoint Unix timestamp in seconds (e.g., 1705319400)
- `downloaded_utc` - string (ISO 8601 / RFC3339) - When file was downloaded to local disk (e.g., "2024-01-15T10:30:00.000000Z")
- `downloaded_timestamp` - number - When file was downloaded to local disk, Unix timestamp in seconds (e.g., 1705319400)
- `sharepoint_error` - string - Any error that might have occurred during the download
- `processing_error` - string - Any error that might have occurred during the processing of the file

**`vectorstore_map.csv` columns:**
- `openai_file_id` - string - OpenAI file ID assigned after upload (e.g., "assistant-BuQoNyXQnoedPjTySDTFU1")
  - empty if file could not be uploaded or embedded
- `vector_store_id` - string - OpenAI vector store ID where the file was embedded last (Domain vector store ID)
  - empty if file could not be uploaded or embedded
- `file_relative_path` - string - path relative to storage root with backslashes
  - Example if succeeded: "DOMAIN01\01_files\source01\02_embedded\Reports\Q1.docx"
  - Example if failed: "DOMAIN01\01_files\source01\03_failed\Reports\Q1.docx"
- `sharepoint_listitem_id` - number - SharePoint list item ID (e.g., 123)
- `sharepoint_unique_file_id` - string - GUID unique to this file (e.g., "b!abc123...")
- `filename` - string - file name with extension (e.g., "Document.docx")
- `file_type` - string - file extension without dot (e.g., "docx")
- `file_size` - number - size in bytes (e.g., 864368)
- `last_modified_utc` - string (ISO 8601 / RFC3339) - UTC timestamp (e.g., "2024-01-15T10:30:00.000000Z")
- `last_modified_timestamp` - number - Unix timestamp in seconds (e.g., 1705319400)
- `downloaded_utc` - string (ISO 8601 / RFC3339) - When file was downloaded to local disk, copied from files_map.csv (e.g., "2024-01-15T10:30:00.000000Z")
- `downloaded_timestamp` - number - When file was downloaded to local disk, copied from files_map.csv, Unix timestamp in seconds (e.g., 1705319400)
- `uploaded_utc` - string (ISO 8601 / RFC3339) - `created_at` Open AI UTC timestamp returned by file upload (e.g., "2024-01-15T10:30:00.000000Z")
  - empty if file could not be uploaded or embedded
- `uploaded_timestamp` - number - `created_at` Open AI UTC timestamp returned by file upload (e.g., 1705319400)
  - empty if file could not be uploaded or embedded
- `embedded_utc` - string (ISO 8601 / RFC3339) - `created_at` Open AI UTC timestamp returned by file embedding (e.g., "2024-01-15T10:30:00.000000Z")
  - empty if file could not be uploaded or embedded
- `embedded_timestamp` - number - `created_at` Open AI UTC timestamp returned by file upload (e.g., 1705319400)
  - empty if file could not be uploaded or embedded
- `sharepoint_error` - string - Any error that might have occurred during the download
- `processing_error` - string - Any error that might have occurred during the processing of the file
- `embedding_error` - string - Any error that might have occurred during the upload to the Open AI backend or the embedding

## Source-Specific Processing

**file_sources:**
- Download target: `02_embedded/` folder
- Process step: Skipped (files embedded directly)
- `file_relative_path` set by: Download step

**list_sources:**
- Download target: `01_originals/` folder (exports SharePoint list to CSV)
- Process step: Converts each CSV row to individual Markdown file in `02_embedded/`
- `file_relative_path` set by: Process step (points to `02_embedded/`)

**sitepage_sources:**
- Download target: `01_originals/` folder (fetches page HTML)
- Process step: Extracts content, cleans HTML, writes to `02_embedded/`
- `file_relative_path` set by: Process step (points to `02_embedded/`)

## Crawling Process Steps

Applies to: `file_sources`, `list_sources`, `sitepage_sources`

**Parameters:**
- `domain_id={id}` - The domain id
- `mode=[full|incremental]` - Full or incremental crawl
- `source_type=[file_sources|list_sources|sitepage_sources]` - Type of sources to crawl
- Optional: `source_id={id}` - Process only a single source
- `dry_run=false` (default) - performs action as specified
- `retry_batches=2` (default) - number of processing batches for failed items:
  - Batch 1: Process all items, collect failures into retry list
  - Batch 2: Retry failed items from batch 1
  - Set to `1` to disable retries
  - Applies to: download, process, embed steps (SharePoint timeouts, OpenAI rate limits, etc.)
- `dry_run=true` - simulates action, producing previewable stream output but not modifying persistent data:
  - Creates temporary `sharepoint_map_[ID].csv` and `files_map_[ID].csv` files (ID = JOB_ID for streaming, random ID for json/html)
  - All map comparisons and change detection run against temporary files
  - No files are downloaded, uploaded, or deleted
  - No vector store modifications
  - Temporary files are deleted at end of job

**Parallel-safe design:**
- All crawl actions can run in parallel (different sources, different actions, or same source + different action)
- No locking mechanism - parallelism achieved via lock-free eventual consistency:
  - **Graceful write**: Write to temp file, then atomic rename. Retry on concurrency error.
  - **Graceful read**: Retry on locked file.
  - **Precondition check**: Each action verifies item state before processing.
- Preconditions by action:
  - Download: (none)
  - Process: `file_relative_path` exists in `01_originals/` on disk
  - Embed: `file_relative_path` exists in `02_embedded/` on disk
- Items not meeting preconditions are skipped (logged as warning). Re-running the action picks them up.
- Result includes count of skipped items so caller knows if re-run is needed.
- For guaranteed sequential processing, run actions one at a time or use the combined `/crawl` endpoint.

**Download data:**
1. Crawler loads domain config for `domain_id` and loads all sources of specified `source_type` (404 for missing domain)
2. If optional `source_id` is given, filters out all other sources (404 for missing source)
3. [For each source]
    - Crawler connects to SharePoint site using credentials from config
    - **If connection fails:** Log error, skip source, continue with next source
    - Loads item list from SharePoint as defined in source (with filter if configured)
4. [For each connected source]
    - Writes `sharepoint_map.csv` file gracefully (retries on concurrency problems)
    - If `mode=incremental`:
      - Loads `files_map.csv` to internal `file_map` (fallback to `mode=full` if file not exists)
      - Verifies each `file_relative_path` in `file_map` exists on disk (if missing: treat as ADDED for re-download)
      - Identifies 1) added files, 2) removed files, 3) changed files by comparing `sharepoint_unique_file_id`:
        - ADDED: `sharepoint_unique_file_id` in SharePoint but not in `file_map`
        - REMOVED: `sharepoint_unique_file_id` in `file_map` but not in SharePoint
        - CHANGED: any of `filename`, `server_relative_url`, `file_size`, or `last_modified_utc` differs
      - REMOVED: Deletes all removed files from target folders and from `file_map`. Writes `files_map.csv` gracefully.
      - ADDED/CHANGED: Filter to embeddable files only (using `DEFAULT_FILETYPES_ACCEPTED_BY_VECTOR_STORES`). Non-embeddable files are logged and skipped (tracked in `sharepoint_map.csv` only).
      - ADDED: Downloads added embeddable items to target folder, applying SharePoint last modified timestamp. **If download fails:** Log error, set `sharepoint_error` in files_map, skip item. Writes updated `files_map.csv` gracefully.
      - CHANGED: Deletes all changed items from target folders.
      - CHANGED: Downloads changed embeddable items to target folder, applying SharePoint last modified timestamp. **If download fails:** Log error, set `sharepoint_error` in files_map, skip item. Writes updated `files_map.csv` gracefully.
    - If `mode=full`:
      - Deletes all subfolders in `01_originals/`, `02_embedded/`, and `03_failed/` folders (fresh start)
      - Deletes `files_map.csv` and creates new internal `file_map`
      - ALL: Filter to embeddable files only (using `DEFAULT_FILETYPES_ACCEPTED_BY_VECTOR_STORES`). Non-embeddable files are logged and skipped (tracked in `sharepoint_map.csv` only).
      - ALL: Downloads all embeddable items to target folder, applying SharePoint last modified timestamp. **If download fails:** Log error, set `sharepoint_error` in files_map, skip item. Writes updated `files_map.csv` gracefully.

5. Runs Integrity Check for this source (see "Integrity Check" section)

Expected outcome:
- `sharepoint_map.csv` contains all items (rows) that could be identified in SharePoint
- `sharepoint_map.csv` does not contain items not existing in SharePoint
- `files_map.csv` contains only embeddable files (non-embeddable tracked in `sharepoint_map.csv` only)
- `files_map.csv` > `file_relative_path` column is empty if download failed
- Target folders do not contain items not existing in SharePoint
- Target folders might be missing items that could not be downloaded from SharePoint
- Local storage mirrors SharePoint folder structure (guaranteed by Integrity Check)

**Process data:**
- Source-type specific processing (see "Source-specific processing" above)
- For list/sitepage sources:
  - Verifies each `file_relative_path` in `files_map.csv` exists in `01_originals/` (if missing: log warning, mark for re-download by clearing `file_relative_path`)
  - Converts original files to `02_embedded/`
  - Updates `file_relative_path` in `files_map.csv` to point to processed file in `02_embedded/`
- Writes updated `files_map.csv` gracefully

**Embed data:**
1. Crawler loads domain config for `domain_id` and loads all sources of specified `source_type` (404 for missing domain)
2. If optional `source_id` is given, filters out all other sources (404 for missing source)
3. Get target vector store
    - If `vector_store_id` in domain.json is empty:
      - Create new vector store using `vector_store_name` (or `domain_id` if name is empty)
      - Write new `vector_store_id` back to domain.json
      - Log: "Created vector store '{name}' (ID={id})"
      - If creation fails: log error, skip embedding for all sources (continue crawl without embed)
    - Validate vector store exists (404 if missing)
    - Load all vector store files 
4. [For each source]
    - Loads `files_map.csv` (skip source if not found)
    - Loads `vectorstore_map.csv` (create empty internal map if not found)
    - Cleanup `vectorstore_map.csv`: Removes all files with `openai_file_id` not found in the vector store. Writes `vectorstore_map.csv` gracefully.
    - If `mode=incremental`:
        - Verifies each `file_relative_path` in `files_map.csv` exists on disk (if missing: skip file, log warning)
        - Compares the content of `files_map.csv` and `vectorstore_map.csv` while ignoring all files in `03_failed/` folders
        - Identifies 1) added files, 2) removed files, 3) changed files (based on `file_size` and `last_modified_utc`)
        - All changes must be reflected in internal `vectorstore_map`
        - REMOVED: Removes all files from the vector store. Writes updated `vectorstore_map.csv` gracefully.
        - ADDED: For each file, uploads the file to the global file storage and adds it to the vector store. Writes updated `vectorstore_map.csv` gracefully.
        - CHANGED: For each file, removes the file from the vector store (if still exists), uploads the file to the global file storage and adds it to the vector store. Writes updated `vectorstore_map.csv` gracefully.
    - If `mode=full`:
        - Clears internal `vectorstore_map`
        - REMOVED: Removes all files from this source in the vector store but leaves files in global storage (other vector stores might still use it). Writes updated `vectorstore_map.csv` gracefully.
        - ALL: For each file in `files_map.csv`, uploads the file to the global file storage and adds it to the vector store. Writes updated `vectorstore_map.csv` gracefully.
    - After modifying the target vector store:
        - WAIT: Waits until the vector store has no files with status = 'in_progress'
        - CLEANUP: Removes files where embedding has failed
          - Loads all vector store files
          - Filters to only files that were added or changed in this run
          - Identify files with status != 'completed'
          - For each file
            - Removes file from vector store and deletes file in the global storage
            - Moves file from `02_embedded/` to `03_failed/` folder
            - Updates file properties like `embedding_error` and `file_relative_path` in `vectorstore_map`
          - Writes updated `vectorstore_map.csv` gracefully
5. Updates `files_metadata.json` (see "files_metadata.json Update" section)

## Complete List of Edge Cases

**A. SharePoint state changes (between crawls):**
- **A1. ADDED** - New file created in SharePoint (new `sharepoint_unique_file_id`)
- **A2. REMOVED** - File deleted from SharePoint (`sharepoint_unique_file_id` gone)
- **A3. CONTENT_UPDATED** - Content changed, same name/location (`file_size` and/or `last_modified_utc` changed)
- **A4. RENAMED** - Filename changed, same folder (`filename` and `server_relative_url` changed, size/date same or changed)
- **A5. MOVED** - File moved to different folder (`server_relative_url` changed, `filename` same)
- **A6. RENAMED+MOVED** - Both filename and location changed
- **A7. RENAMED+UPDATED** - Filename and content changed
- **A8. MOVED+UPDATED** - Location and content changed
- **A9. RENAMED+MOVED+UPDATED** - All three changed
- **A10. RESTORED** - Restored from Recycle Bin (same `sharepoint_unique_file_id` reappears)
- **A11. VERSION_ROLLBACK** - Reverted to older version (`last_modified_utc` older than before)
- **A12. COPIED** - File copied (new `sharepoint_unique_file_id`, treated as new file)
- **A13. REPLACED** - Deleted + new file with same name (old ID gone + new ID appears)
- **A14. CHECK-IN/CHECK-OUT** - Metadata change without content change
- **A15. FOLDER_RENAMED** - Parent folder renamed (all files inside have new `server_relative_url`)
- **A16. FOLDER_MOVED** - Parent folder moved (all files inside have new `server_relative_url`)

**B. Local storage anomalies:**
- **B1. LOCAL_FILE_MISSING** - File in `files_map.csv` but not on disk
- **B2. LOCAL_FILE_EXTRA** - File on disk but not in `files_map.csv` (orphan)
- **B3. LOCAL_FILE_WRONG_PATH** - File exists but path differs from `file_relative_path`
- **B4. LOCAL_FILE_CORRUPTED** - File exists but can't be read (0 bytes, locked, encoding error)
- **B5. LOCAL_FOLDER_MISSING** - Parent folder deleted from disk
- **B6. MAP_FILE_MISSING** - `files_map.csv` doesn't exist (first run or deleted)
- **B7. MAP_FILE_CORRUPTED** - `files_map.csv` can't be parsed (encoding, format error)

**C. Vector store anomalies:**
- **C1. VS_FILE_MISSING** - `openai_file_id` in `vectorstore_map.csv` but not in vector store
- **C2. VS_FILE_EXTRA** - File in vector store but not in `vectorstore_map.csv`
- **C3. VS_EMBEDDING_FAILED** - File uploaded but status != 'completed'
- **C4. VS_DELETED** - Target vector store no longer exists
- **C5. OPENAI_FILE_DELETED** - File in global storage deleted externally
- **C6. VS_CREATION_FAILED** - Auto-create vector store failed (API error, quota, permissions)

**D. Timing/concurrency:**
- **D1. RAPID_CHANGES** - Multiple changes between crawls (only final state visible)
- **D2. CONCURRENT_CRAWLS** - Two crawls running on same source simultaneously
- **D3. PARTIAL_FAILURE** - Crawl fails mid-way, partial state written
- **D4. SHAREPOINT_TIMEOUT** - SharePoint API call times out mid-crawl
- **D5. OPENAI_RATE_LIMIT** - Upload blocked by rate limiting
- **D6. OPENAI_TIMEOUT** - OpenAI API call times out

**E. Data quality:**
- **E1. UNICODE_FILENAME** - Special characters, emojis, RTL characters in filename
- **E2. VERY_LONG_PATH** - Path exceeds OS limits (260 chars Windows, 4096 Linux)
- **E3. ZERO_BYTE_FILE** - Empty file from SharePoint
- **E4. UNSUPPORTED_TYPE** - File type not accepted by vector store
- **E5. DUPLICATE_FILENAME** - Same filename in different SharePoint folders
- **E6. SPECIAL_CHARS_IN_PATH** - Spaces, quotes, ampersands in folder names

## Edge Case Handling Mechanism

**Key principle:** Use `sharepoint_unique_file_id` as immutable identifier. This ID never changes regardless of rename/move/update.

**Change detection algorithm:**

Compare `sharepoint_map.csv` (current SharePoint state) with `files_map.csv` (last known local state) by `sharepoint_unique_file_id`:
- For each file in SharePoint map:
  - If `sharepoint_unique_file_id` NOT in local map → **ADDED**
  - Else compare: `filename`, `server_relative_url`, `file_size`, `last_modified_utc`
  - Any field differs → **CHANGED**
- For each file in local map:
  - If `sharepoint_unique_file_id` NOT in SharePoint map → **REMOVED**

**Handling by detected state:**
- **ADDED** - Download to correct path, add to `files_map.csv`
- **REMOVED** - Delete local file, remove from `files_map.csv`
- **CHANGED** - Delete old local file, download to new correct path, update `files_map.csv`

**Edge case resolution:**
- **A1-A9** - Handled by change detection (ADDED/REMOVED/CHANGED)
- **A10. RESTORED** - ID reappears → detected as ADDED
- **A11. VERSION_ROLLBACK** - `last_modified_utc` differs → detected as CHANGED
- **A12. COPIED** - New ID → detected as ADDED
- **A13. REPLACED** - Old ID gone + new ID → REMOVED + ADDED
- **A14. CHECK-IN/CHECK-OUT** - If `last_modified_utc` changed → CHANGED, else no action
- **A15-A16. FOLDER_RENAMED/MOVED** - All files inside have new `server_relative_url` → detected as CHANGED
- **B1. LOCAL_FILE_MISSING** - Detected by sync-check → re-download
- **B2. LOCAL_FILE_EXTRA** - Detected by sync-check → delete orphan
- **B3. LOCAL_FILE_WRONG_PATH** - Detected by sync-check → move or re-download
- **B4. LOCAL_FILE_CORRUPTED** - Detected during embed (read fails) → re-download
- **B5. LOCAL_FOLDER_MISSING** - Parent created automatically on download
- **B6. MAP_FILE_MISSING** - Fallback to `mode=full`
- **B7. MAP_FILE_CORRUPTED** - Fallback to `mode=full`, log warning
- **C1. VS_FILE_MISSING** - Cleanup removes from `vectorstore_map.csv`, re-embed
- **C2. VS_FILE_EXTRA** - Ignored (may belong to other source/domain)
- **C3. VS_EMBEDDING_FAILED** - Move to `03_failed/`, log error
- **C4. VS_DELETED** - Return 404 error, abort embed
- **C5. OPENAI_FILE_DELETED** - Re-upload during embed
- **C6. VS_CREATION_FAILED** - Log error, skip embedding, continue crawl (download/process still succeed)
- **D1. RAPID_CHANGES** - Only final state matters, handled normally
- **D2. CONCURRENT_CRAWLS** - Graceful read/write with retry handles conflicts
- **D3. PARTIAL_FAILURE** - Next run picks up from `files_map.csv` state
- **D4-D6. TIMEOUTS/RATE_LIMITS** - Retry with backoff, fail gracefully
- **E1. UNICODE_FILENAME** - Handled by UTF-8 encoding throughout
- **E2. VERY_LONG_PATH** - Log warning, skip file, add to `03_failed/`
- **E3. ZERO_BYTE_FILE** - Download succeeds, embed may fail → `03_failed/`
- **E4. UNSUPPORTED_TYPE** - Skip during embed, log warning
- **E5. DUPLICATE_FILENAME** - Different `server_relative_url` → different local paths
- **E6. SPECIAL_CHARS_IN_PATH** - URL-decoded for local path

**Change detection function:**

```python
def is_changed(sp_file, local_file) -> bool:
  return (
    sp_file.filename != local_file.filename or
    sp_file.server_relative_url != local_file.server_relative_url or
    sp_file.file_size != local_file.file_size or
    sp_file.last_modified_utc != local_file.last_modified_utc
  )
```

## Integrity Check

Runs at the end of every `download_data` step (both full and incremental modes) to verify local storage matches SharePoint and correct any anomalies.

**Integrity check algorithm:**

1. Build expected state from `sharepoint_map.csv`:
   - `expected_files` = { `sharepoint_unique_file_id` -> (`filename`, `server_relative_url`, `expected_local_path`) }

2. Build actual state from `files_map.csv` + disk scan:
   - `actual_files` = { `sharepoint_unique_file_id` -> (`filename`, `server_relative_url`, `actual_local_path`, `file_exists_on_disk`) }

3. Scan disk for orphan files:
   - For `file_sources`: scan `02_embedded/` folder (files downloaded directly there)
   - For `list_sources`/`sitepage_sources`: scan both `01_originals/` and `02_embedded/` folders
   - `orphan_files` = files on disk not referenced by any `file_relative_path` in `files_map.csv`

4. Compare and identify anomalies:
   - **MISSING_IN_MAP** - file in `sharepoint_map.csv` but not in `files_map.csv` (download failed silently)
   - **MISSING_ON_DISK** - file in `files_map.csv` with non-empty `file_relative_path` but file not on disk
   - **ORPHAN_ON_DISK** - file on disk but not referenced in `files_map.csv`
   - **WRONG_PATH** - file exists on disk but at different path than `file_relative_path` in `files_map.csv`

5. Correct anomalies (always attempt all corrections):
   - **MISSING_IN_MAP** - Re-download file from SharePoint, add to `files_map.csv`
   - **MISSING_ON_DISK** - Re-download file from SharePoint, update `files_map.csv`
   - **ORPHAN_ON_DISK** - Delete orphan file from disk
   - **WRONG_PATH** - Move file to correct path, update `file_relative_path` in `files_map.csv`

6. Write corrected `files_map.csv` gracefully

7. Log summary:
   - If anomalies found: `"Integrity check corrected: X missing, Y orphans deleted, Z moved"`
   - If no anomalies: `"Integrity check passed: N files verified"`

**Expected local path derivation:**

```python
from hardcoded_config import CRAWLER_HARDCODED_CONFIG as CFG

# Map source_type to folder prefix using config constants
SOURCE_TYPE_FOLDERS = {
  "file_sources": CFG.PERSISTENT_STORAGE_PATH_DOCUMENTS_FOLDER,
  "list_sources": CFG.PERSISTENT_STORAGE_PATH_LISTS_FOLDER,
  "sitepage_sources": CFG.PERSISTENT_STORAGE_PATH_SITEPAGES_FOLDER
}

def get_expected_local_path(domain_id: str, source_type: str, source_id: str, server_relative_url: str) -> str:
  # Extract relative path from SharePoint URL
  # e.g., "/sites/demo/Shared Documents/Reports/Q1.docx" -> "Reports/Q1.docx"
  relative_path = extract_relative_path(server_relative_url)
  
  # Build local path using config constants
  # e.g., "DOMAIN01/01_files/source01/02_embedded/Reports/Q1.docx"
  return f"{domain_id}/{SOURCE_TYPE_FOLDERS[source_type]}/{source_id}/{CFG.PERSISTENT_STORAGE_PATH_EMBEDDED_SUBFOLDER}/{relative_path}"
```

**Anomaly detection handles edge cases:**
- **B1. LOCAL_FILE_MISSING** - Detected as MISSING_ON_DISK → re-download
- **B2. LOCAL_FILE_EXTRA** - Detected as ORPHAN_ON_DISK → delete
- **B3. LOCAL_FILE_WRONG_PATH** - Detected as WRONG_PATH → move
- **B5. LOCAL_FOLDER_MISSING** - Parent folder created automatically during correction

## files_metadata.json Update

Updated after each `embed_data` step to maintain a domain-level index of all embedded files with their metadata.

**Location:** `PERSISTENT_STORAGE_PATH/domains/[DOMAIN_ID]/files_metadata.json`

**Structure:** V3 format - flat array of objects matching `CrawledFile` dataclass:

```json
[
  {
    "sharepoint_listitem_id": 123,
    "sharepoint_unique_file_id": "b!abc123...",
    "openai_file_id": "assistant-BuQoNyXQnoedPjTySDTFU1",
    "file_relative_path": "DOMAIN01\\01_files\\source01\\02_embedded\\Reports\\Document.docx",
    "url": "https://contoso.sharepoint.com/sites/Example/Shared%20Documents/Reports/Document.docx",
    "raw_url": "https://contoso.sharepoint.com/sites/Example/Shared Documents/Reports/Document.docx",
    "server_relative_url": "/sites/Example/Shared Documents/Reports/Document.docx",
    "filename": "Document.docx",
    "file_type": "docx",
    "file_size": 864368,
    "last_modified_utc": "2024-01-15T10:30:00.000000Z",
    "embedded_utc": "2024-01-16T14:20:00.000000Z",
    "source_id": "source01",
    "source_type": "file_sources",
    "custom_property_1": "extracted value",
    "custom_property_2": "another value"
  }
]
```

**V3 Key Fields** (from `PERSISTENT_STORAGE_STRUCTURE.md`):
- `sharepoint_listitem_id` - SharePoint list item ID
- `sharepoint_unique_file_id` - SharePoint unique file identifier (immutable)
- `openai_file_id` - OpenAI file ID (format: `assistant-...`)
- `file_relative_path` - Relative path to embedded file (backslashes)
- `url` - URL-encoded SharePoint source URL
- `raw_url` - Raw SharePoint URL (not encoded)
- `server_relative_url` - Server-relative URL path
- `filename` - Original filename
- `file_type` - File extension (docx, pdf, xlsx, etc.)
- `file_size` - File size in bytes
- `last_modified_utc` - UTC timestamp ISO 8601 with microseconds
- `last_modified_timestamp` - Unix timestamp of last modification

**V2 Extensions** (added by this spec):
- `embedded_utc` - UTC timestamp when file was embedded (ISO 8601)
- `source_id` - Source identifier within domain
- `source_type` - Source type: `file_sources`, `list_sources`, or `sitepage_sources`

**Update algorithm (after embed_data completes):**

1. Load existing `files_metadata.json` (create empty array if not exists)
2. Build lookup: `existing_by_sp_id` = { `sharepoint_unique_file_id` -> [entries] }
3. For each successfully embedded file in this run:
   - If `openai_file_id` already in array → skip (already recorded)
   - Else create new entry with all fields from `vectorstore_map.csv`
   - **Carry-over:** Find previous entries with same `sharepoint_unique_file_id`
     - Copy custom properties (fields not in standard schema) to new entry
     - Keep old entries in array (version history)
4. Write updated `files_metadata.json` gracefully

**Carry-over logic:**

```python
STANDARD_FIELDS = {
  # V3 fields
  "sharepoint_listitem_id", "sharepoint_unique_file_id", "openai_file_id",
  "file_relative_path", "url", "raw_url", "server_relative_url",
  "filename", "file_type", "file_size", "last_modified_utc", "last_modified_timestamp",
  # V2 extensions
  "embedded_utc", "source_id", "source_type"
}

def carry_over_custom_properties(new_entry: dict, previous_entries: list) -> dict:
  if not previous_entries: return new_entry
  # Use most recent previous entry (by embedded_utc)
  latest = max(previous_entries, key=lambda e: e.get("embedded_utc", ""))
  for key, value in latest.items():
    if key not in STANDARD_FIELDS and key not in new_entry:
      new_entry[key] = value
  return new_entry
```

**Cleanup mechanism:**

Endpoint: `GET /v2/crawler/cleanup_metadata?domain_id={id}`

**Purpose:** Remove stale entries from `files_metadata.json` to keep it clean and reduce file size.

**Removes entries where:**
- `openai_file_id` no longer exists in the domain's vector store
- `sharepoint_unique_file_id` no longer exists in any source's `vectorstore_map.csv`

**Returns:** JSON with count of removed entries and remaining entries

**Edge case handling:**
- **File updated (A3-A9):** New `openai_file_id` entry created, custom properties carried over from previous entry with same `sharepoint_unique_file_id`
- **File removed (A2):** Entry remains in `files_metadata.json` (historical record), cleanup removes if needed
- **File restored (A10):** New entry created, carry-over from historical entry if exists

## Spec Changes

**[2026-01-13 11:04]**
- Added **V2CR-FR-07**: Auto-Create Vector Store on First Crawl
- Updated Embed Data step: auto-create vector store when `vector_store_id` is empty
- Added fallback: use `domain_id` as name when `vector_store_name` is also empty
- Added error handling: skip embedding if vector store creation fails (crawl continues)
- Added **C6. VS_CREATION_FAILED** edge case and resolution

**[2026-01-03 13:10]**
- Added `domain.json` schema with complete example
- Added source field definitions table
- Added **V2CR-DD-06**: URL-based library access - document libraries accessed by `sharepoint_url_part` (URL path), not by display title
- Clarified: `FileSource` and `SitePageSource` use `sharepoint_url_part`, `ListSource` uses `list_name`

**[2024-12-27 17:38]**
- Added `retry_batches=2` parameter for retry logic (download, process, embed steps)
- Expanded `/v2/crawler/cleanup_metadata` endpoint documentation with purpose and return format
- Clarified integrity check runs per-source after download step completes

**[2024-12-27 17:21]**
- Added `sharepoint_listitem_id` column to `files_map.csv` for consistency with other map files
- Updated `get_expected_local_path()` code example to use `CRAWLER_HARDCODED_CONFIG` constants
- Clarified integrity check folder scanning: `file_sources` scans `02_embedded/`, `list_sources`/`sitepage_sources` scan both `01_originals/` and `02_embedded/`

**[2024-12-27 17:12]**
- Implementation must use `CRAWLER_HARDCODED_CONFIG` constants from `hardcoded_config.py`:
  - Folder paths: `PERSISTENT_STORAGE_PATH_CRAWLER_SUBFOLDER`, `PERSISTENT_STORAGE_PATH_DOCUMENTS_FOLDER`, `PERSISTENT_STORAGE_PATH_LISTS_FOLDER`, `PERSISTENT_STORAGE_PATH_SITEPAGES_FOLDER`, `PERSISTENT_STORAGE_PATH_ORIGINALS_SUBFOLDER`, `PERSISTENT_STORAGE_PATH_EMBEDDED_SUBFOLDER`, `PERSISTENT_STORAGE_PATH_FAILED_SUBFOLDER`
  - File names: `DOMAIN_JSON`, `FILES_METADATA_JSON`, `SHAREPOINT_MAP_CSV`, `FILE_MAP_CSV`, `VECTOR_STORE_MAP_CSV`
  - Settings: `APPEND_TO_MAP_FILES_EVERY_X_LINES`, `DEFAULT_FILETYPES_ACCEPTED_BY_VECTOR_STORES`

**[2024-12-27 16:53]**
- Updated V2CR-FR-05: Replaced full-file rewrite with buffered append writes
- Added `MapFileWriter` class with `APPEND_TO_MAP_FILES_EVERY_X_LINES` config
- Force flush triggers: header creation, first item, last item

**[2024-12-27 16:48]**
- Added `file_type` column to `files_map.csv`
- Clarified `downloaded_utc` semantics: files_map = when downloaded to disk, vectorstore_map = copied from files_map
- Added error handling for SharePoint connection failures: skip source, continue with next
- Added error handling for file download failures: log error, set `sharepoint_error`, skip item, continue

**[2024-12-19 17:26]**
- Initial version extracted from `_V2_SPEC_ROUTERS.md`
- Added complete edge case list (A1-A16, B1-B7, C1-C5, D1-D6, E1-E6)
- Added edge case resolution mapping
- Added Functional Requirements (V2CR-FR-01 to V2CR-FR-06)
- Added Design Decisions (V2CR-DD-01 to V2CR-DD-05)
- Added Implementation Guarantees (V2CR-IG-01 to V2CR-IG-05)
- Added Integrity Check section
- Added files_metadata.json Update section with carry-over logic
