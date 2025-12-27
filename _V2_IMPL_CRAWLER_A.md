# Implementation Plan: /v2/crawler Router

**Goal**: Implement the V2 crawler router with monitoring UI and streaming job support
**Target files**:
- `/src/routers_v2/crawler.py` (NEW)
- `/src/routers_v2/common_sharepoint_functions_v2.py` (NEW)
- `/src/routers_v2/common_crawler_functions_v2.py` (EXTEND)

**Depends on:**
- `_V2_SPEC_CRAWLER.md` for crawling process and change detection
- `_V2_SPEC_CRAWLER_UI.md` for UI specification
- `_V2_SPEC_ROUTERS.md` for endpoint design and streaming job infrastructure
- `_V2_SPEC_COMMON_UI_FUNCTIONS.md` for UI generation functions

## Table of Contents

1. File Structure
2. common_sharepoint_functions_v2.py
3. common_crawler_functions_v2.py
4. crawler.py
5. Spec Requirements Coverage Matrix
6. Edge Case Handling Matrix
7. Implementation Order
8. Verification Findings
9. Detailed Changes/Additions Plan
10. Implementation Verification Checklist

## 1. File Structure

```
/src/routers_v2/
├── crawler.py                        # Router endpoints + UI (~600 lines)
├── common_sharepoint_functions_v2.py # Generic SharePoint operations (~300 lines) [NEW]
└── common_crawler_functions_v2.py    # Crawler-specific functions (~500 lines) [EXTEND]
```

## 2. common_sharepoint_functions_v2.py (NEW)

**Purpose:** Generic SharePoint API wrapper - reusable by any router needing SharePoint access.

### Dataclasses

```python
@dataclass
class SharePointFile:
  """File metadata from SharePoint API."""
  sharepoint_listitem_id: int
  sharepoint_unique_file_id: str
  filename: str
  file_type: str
  file_size: int
  url: str
  raw_url: str
  server_relative_url: str
  last_modified_utc: str
  last_modified_timestamp: int

@dataclass
class SharePointContext:
  """Active SharePoint connection context."""
  site_url: str
  client_context: Any  # Office365 ClientContext
  connected: bool
  error: str
```

### Functions

| Function | Purpose | Spec Requirement |
|----------|---------|------------------|
| `create_sharepoint_context(site_url, config)` | Create authenticated connection | Crawl step 3 |
| `list_document_library_files(ctx, sharepoint_url_part, filter)` | List files from doc library | Crawl step 4 |
| `list_sitepage_files(ctx, sharepoint_url_part, filter)` | List site pages | Crawl step 4 |
| `list_list_items(ctx, list_name, filter)` | List items from SharePoint list | Crawl step 4 |
| `download_file(ctx, server_relative_url, target_path)` | Download file, preserve timestamp | Crawl step 4 |
| `convert_sp_file_to_dataclass(sp_file)` | Convert API response to SharePointFile | Internal |

### Implementation Notes

- Uses `Office365-REST-Python-Client` library (already in project)
- Certificate-based authentication via `CRAWLER_CLIENT_*` config
- Returns `(success, error)` tuples for error handling
- Applies SharePoint `last_modified_utc` timestamp to downloaded files

## 3. common_crawler_functions_v2.py (EXTEND)

**Purpose:** Crawler-specific logic - map files, change detection, integrity, metadata.

### Existing (keep as-is)

- `FileSource`, `SitePageSource`, `ListSource`, `DomainConfig` dataclasses
- `load_domain()`, `load_all_domains()`, `save_domain_to_file()`, `delete_domain_folder()`, `rename_domain()`

### New Dataclasses

```python
@dataclass
class FilesMapEntry:
  """Row in files_map.csv."""
  sharepoint_unique_file_id: str
  filename: str
  file_type: str  # Added per AMB-02 resolution
  server_relative_url: str
  file_relative_path: str  # Empty if download failed
  file_size: int
  last_modified_utc: str
  last_modified_timestamp: int
  downloaded_utc: str
  downloaded_timestamp: int
  sharepoint_error: str
  processing_error: str

@dataclass
class VectorStoreMapEntry:
  """Row in vectorstore_map.csv."""
  openai_file_id: str
  vector_store_id: str
  file_relative_path: str
  sharepoint_listitem_id: int
  sharepoint_unique_file_id: str
  filename: str
  file_type: str
  file_size: int
  last_modified_utc: str
  last_modified_timestamp: int
  downloaded_utc: str
  downloaded_timestamp: int
  uploaded_utc: str
  uploaded_timestamp: int
  embedded_utc: str
  embedded_timestamp: int
  sharepoint_error: str
  processing_error: str
  embedding_error: str

@dataclass
class ChangeSet:
  """Result of change detection."""
  added: List[SharePointFile]
  removed: List[str]  # sharepoint_unique_file_ids to remove
  changed: List[SharePointFile]

@dataclass
class IntegrityResult:
  """Result of integrity check."""
  missing_in_map: List[str]  # sp_ids in sharepoint_map but not files_map
  missing_on_disk: List[str]  # sp_ids with file_relative_path but file not on disk
  orphan_on_disk: List[str]  # paths on disk not in files_map
  wrong_path: List[tuple]  # (sp_id, actual_path, expected_path)
  all_ok: bool
```

### New Functions - Map File Operations

| Function | Purpose | Spec Requirement |
|----------|---------|------------------|
| `get_source_folder_path(storage_path, domain_id, source_type, source_id)` | Build path to source folder | Local storage structure |
| `get_map_file_path(source_folder, map_type)` | Get path to sharepoint_map/files_map/vectorstore_map | Map files |
| `read_map_csv_gracefully(path, retry=3)` | Read CSV with retry on lock | V2CR-FR-05 |
| `sharepoint_files_to_map_rows(files: list[SharePointFile])` | Convert to sharepoint_map.csv rows | Download step |
| `build_files_map_index(rows)` | Index by sharepoint_unique_file_id | Change detection |

### MapFileWriter Class (Buffered Append)

Replaces `write_map_csv_gracefully()` with a stateful writer that buffers rows and appends to file.

```python
class MapFileWriter:
  """Buffered CSV writer with append mode for efficient map file updates."""
  
  def __init__(self, path: str, fieldnames: list[str], buffer_size: int = None):
    self.path = path
    self.fieldnames = fieldnames
    self.buffer_size = buffer_size or CRAWLER_HARDCODED_CONFIG.APPEND_TO_MAP_FILES_EVERY_X_LINES
    self.buffer: list[dict] = []
    self.total_written = 0
    self.file_exists = os.path.exists(path)
  
  def write_header(self) -> None:
    """Create file with CSV header. Called once at start."""
    # Atomic write: temp file + rename
    
  def append_row(self, row: dict) -> None:
    """Add row to buffer. Flushes when buffer full."""
    self.buffer.append(row)
    if len(self.buffer) >= self.buffer_size:
      self._flush()
  
  def finalize(self) -> None:
    """Flush remaining buffer. Must be called at end."""
    if self.buffer:
      self._flush()
  
  def _flush(self) -> None:
    """Append buffered rows to file."""
    # Open in append mode, write rows, clear buffer
```

**Write triggers:**
1. **Header creation** - `write_header()` creates empty file with CSV header
2. **First item** - `append_row()` flushes after first row (buffer_size check or explicit)
3. **Every X items** - `append_row()` flushes when `len(buffer) >= buffer_size`
4. **Last item** - `finalize()` flushes remaining buffer

**Usage pattern:**
```python
writer = MapFileWriter(path, fieldnames)
writer.write_header()  # Creates file with header

for i, item in enumerate(items):
  row = process_item(item)
  writer.append_row(row)
  if i == 0:
    writer._flush()  # Ensure first item written immediately

writer.finalize()  # Flush remaining buffer
```

### New Functions - Change Detection

| Function | Purpose | Spec Requirement |
|----------|---------|------------------|
| `compute_changes(sp_files, files_map_rows)` | Detect ADDED/REMOVED/CHANGED | V2CR-FR-01, V2CR-FR-02 |
| `is_file_changed(sp_file, local_entry)` | Compare 4 fields | V2CR-FR-02 |

```python
def is_file_changed(sp_file: SharePointFile, local_entry: dict) -> bool:
  return (
    sp_file.filename != local_entry.get('filename') or
    sp_file.server_relative_url != local_entry.get('server_relative_url') or
    sp_file.file_size != int(local_entry.get('file_size', 0)) or
    sp_file.last_modified_utc != local_entry.get('last_modified_utc')
  )
```

### New Functions - Integrity Check

| Function | Purpose | Spec Requirement |
|----------|---------|------------------|
| `run_integrity_check(source_folder, sp_map, files_map)` | Detect anomalies | V2CR-FR-03 |
| `apply_integrity_corrections(result, source_folder, ctx, logger)` | Fix anomalies | V2CR-FR-04 |
| `get_expected_local_path(source_folder, server_relative_url, sharepoint_url_part)` | Derive expected path | Integrity check |

### New Functions - Metadata

| Function | Purpose | Spec Requirement |
|----------|---------|------------------|
| `load_files_metadata(storage_path, domain_id)` | Load files_metadata.json | V2CR-FR-06 |
| `save_files_metadata(storage_path, domain_id, entries)` | Save files_metadata.json gracefully | V2CR-FR-06 |
| `update_files_metadata_after_embed(storage_path, domain_id, embedded_files)` | Add new entries with carry-over | V2CR-FR-06 |
| `carry_over_custom_properties(new_entry, previous_entries)` | Copy non-standard fields | V2CR-FR-06 |

```python
STANDARD_FIELDS = {
  "sharepoint_listitem_id", "sharepoint_unique_file_id", "openai_file_id",
  "file_relative_path", "url", "raw_url", "server_relative_url",
  "filename", "file_type", "file_size", "last_modified_utc", "last_modified_timestamp",
  "embedded_utc", "source_id", "source_type"
}
```

### New Functions - Embed Operations

| Function | Purpose | Spec Requirement |
|----------|---------|------------------|
| `upload_file_to_openai(openai_client, file_path)` | Upload to file storage | Embed step 4 |
| `add_file_to_vector_store(openai_client, vs_id, file_id)` | Add to vector store | Embed step 4 |
| `wait_for_embedding_completion(openai_client, vs_id, file_ids, timeout)` | Poll until done | Embed step 4 WAIT |
| `cleanup_failed_embeddings(openai_client, vs_id, failed_files)` | Remove failed, move to 03_failed | Embed step 4 CLEANUP |

## 4. crawler.py (NEW)

**Purpose:** Router endpoints and UI generation.

### Module Structure

```python
# Imports
from routers_v2.common_sharepoint_functions_v2 import (
  create_sharepoint_context, list_document_library_files, download_file, SharePointFile
)
from routers_v2.common_crawler_functions_v2 import (
  load_domain, DomainConfig, ChangeSet, IntegrityResult,
  read_map_csv_gracefully, write_map_csv_gracefully, compute_changes,
  run_integrity_check, apply_integrity_corrections, update_files_metadata_after_embed
)
from routers_v2.common_job_functions_v2 import StreamingJobWriter
from routers_v2.common_logging_functions_v2 import MiddlewareLogger
from routers_v2.common_ui_functions_v2 import (...)

router = APIRouter()
config = None
router_prefix = None
router_name = "crawler"
```

### Endpoints

| Endpoint | Method | Formats | Purpose |
|----------|--------|---------|---------|
| `/crawler` | GET | json, html, ui | Router root / List crawler jobs |
| `/crawler/crawl` | GET | json, stream | Full crawl (download+process+embed) |
| `/crawler/download_data` | GET | json, stream | Download step only |
| `/crawler/process_data` | GET | json, stream | Process step only |
| `/crawler/embed_data` | GET | json, stream | Embed step only |

### Query Parameters (all streaming endpoints)

| Param | Required | Values | Default |
|-------|----------|--------|---------|
| `domain_id` | Yes | string | - |
| `mode` | No | `full`, `incremental` | `incremental` |
| `scope` | No | `all`, `files`, `lists`, `sitepages` | `all` |
| `source_id` | No | string | - (all sources of scope type) |
| `format` | No | `json`, `stream` | `json` |
| `dry_run` | No | `true`, `false` | `false` |

### Streaming Job Integration

Each streaming endpoint follows this pattern:

```python
@router.get(f"/{router_name}/crawl")
async def crawler_crawl(request: Request):
  # ... param validation ...
  
  async def stream_crawl():
    writer = StreamingJobWriter(
      persistent_storage_path=get_persistent_storage_path(),
      router_name=router_name,
      action="crawl",
      object_id=domain_id,
      source_url=str(request.url),
      router_prefix=router_prefix
    )
    logger = MiddlewareLogger.create(stream_job_writer=writer)
    
    try:
      yield writer.emit_start()
      logger.log_function_header("crawl")
      
      domain = load_domain(storage_path, domain_id, logger)
      sources = get_sources_for_scope(domain, scope, source_id)
      
      for i, source in enumerate(sources):
        yield logger.log_function_output(f"[ {i+1} / {len(sources)} ] Processing source '{source.source_id}'...")
        
        # Download
        yield from download_source(logger, writer, source, mode, dry_run)
        
        # Check for pause/cancel
        async for event in writer.check_control():
          if event == ControlAction.CANCEL:
            yield writer.emit_end(ok=False, error="Cancelled by user", cancelled=True)
            return
          yield event
        
        # Process (for lists/sitepages)
        yield from process_source(logger, writer, source, dry_run)
        
        # Embed
        yield from embed_source(logger, writer, source, mode, domain.vector_store_id, dry_run)
      
      result = build_crawl_result(...)
      yield writer.emit_end(ok=True, data=result)
      
    except Exception as e:
      yield writer.emit_end(ok=False, error=str(e))
    finally:
      writer.finalize()
  
  return StreamingResponse(stream_crawl(), media_type="text/event-stream")
```

### UI Generation (from _V2_SPEC_CRAWLER_UI.md)

```python
def _generate_crawler_ui_page(jobs: list) -> str:
  # Uses common_ui_functions_v2 like jobs.py
  # Filters to crawler jobs only
  # Table columns: ID, Action, Domain ID, Vector Store ID, Mode, Scope, Source ID, Actions
  # Console panel visible by default
```

## 5. Spec Requirements Coverage Matrix

| Requirement | File | Function(s) | Status |
|-------------|------|-------------|--------|
| **V2CR-FR-01** Change detection by sp_unique_file_id | common_crawler | `compute_changes()`, `build_files_map_index()` | Planned |
| **V2CR-FR-02** Four-field comparison | common_crawler | `is_file_changed()` | Planned |
| **V2CR-FR-03** Integrity check after download | common_crawler | `run_integrity_check()` | Planned |
| **V2CR-FR-04** Self-healing corrections | common_crawler | `apply_integrity_corrections()` | Planned |
| **V2CR-FR-05** Graceful map file ops | common_crawler | `read_map_csv_gracefully()`, `write_map_csv_gracefully()` | Planned |
| **V2CR-FR-06** files_metadata.json carry-over | common_crawler | `update_files_metadata_after_embed()`, `carry_over_custom_properties()` | Planned |
| **V2CR-DD-01** sp_unique_file_id as key | common_crawler | `build_files_map_index()` | Planned |
| **V2CR-DD-02** Four-field detection | common_crawler | `is_file_changed()` | Planned |
| **V2CR-DD-03** Integrity always runs | crawler.py | `download_source()` always calls integrity | Planned |
| **V2CR-DD-04** Move over re-download | common_crawler | `apply_integrity_corrections()` | Planned |
| **V2CR-DD-05** Keyed by openai_file_id | common_crawler | `update_files_metadata_after_embed()` | Planned |
| **V2CR-IG-01** Local mirrors SharePoint | common_crawler | Integrity check + corrections | Planned |
| **V2CR-IG-02** No orphan files | common_crawler | `apply_integrity_corrections()` deletes orphans | Planned |
| **V2CR-IG-03** files_map accurate | common_crawler | Integrity check updates files_map | Planned |
| **V2CR-IG-04** Custom props survive | common_crawler | `carry_over_custom_properties()` | Planned |
| **V2CR-IG-05** All edge cases handled | common_crawler | Change detection + integrity | Planned |

## 6. Edge Case Handling Matrix

| Edge Case | Detection | Resolution | Function |
|-----------|-----------|------------|----------|
| **A1-A9** SharePoint changes | `compute_changes()` | ADDED/REMOVED/CHANGED | `download_source()` |
| **A10** Restored | sp_id reappears | Detected as ADDED | `compute_changes()` |
| **A15-A16** Folder rename/move | server_relative_url changed | Detected as CHANGED | `is_file_changed()` |
| **B1** File missing on disk | Integrity check | Re-download | `apply_integrity_corrections()` |
| **B2** Orphan on disk | Integrity check | Delete | `apply_integrity_corrections()` |
| **B3** Wrong path | Integrity check | Move file | `apply_integrity_corrections()` |
| **B6-B7** Map file missing/corrupt | `read_map_csv_gracefully()` | Fallback to mode=full | `download_source()` |
| **C1** VS file missing | `cleanup_vectorstore_map()` | Remove from map | `embed_source()` |
| **C3** Embedding failed | `wait_for_embedding_completion()` | Move to 03_failed | `cleanup_failed_embeddings()` |
| **D2** Concurrent crawls | Graceful read/write | Retry | `read/write_map_csv_gracefully()` |

## 7. Implementation Order

1. **common_sharepoint_functions_v2.py** - Create new file
   - SharePointFile dataclass
   - Connection and listing functions
   - Download function

2. **common_crawler_functions_v2.py** - Extend existing
   - Map file dataclasses
   - Map file read/write functions
   - Change detection functions
   - Integrity check functions
   - Metadata functions

3. **crawler.py** - Create new file
   - Router structure with endpoints
   - Streaming job orchestration
   - UI generation

## 8. Verification Findings

### Issues Found

**ISSUE-01: Missing `cleanup_metadata` endpoint**
- Spec `_V2_SPEC_ROUTERS.md` line 946 defines: `X(jhs): /v2/crawler/cleanup_metadata?domain_id={id}`
- Not listed in implementation plan endpoints table
- **Resolution:** Add endpoint to crawler.py

**ISSUE-02: Missing `sharepoint_listitem_id` in `FilesMapEntry` dataclass**
- Spec defines `sharepoint_map.csv` with `sharepoint_listitem_id` column
- `FilesMapEntry` dataclass in plan lacks this field
- **Resolution:** Add field to dataclass (needed for `vectorstore_map.csv` population)

**ISSUE-03: Incomplete `FilesMapEntry` - missing URL fields**
- Spec defines `files_map.csv` as subset of `sharepoint_map.csv` + local fields
- Plan's `FilesMapEntry` lacks `url`, `raw_url`, `file_type` fields present in spec
- **Resolution:** Add missing fields or document why they are excluded

**ISSUE-04: `apply_integrity_corrections()` needs SharePoint context**
- Function signature shows `ctx` parameter for re-download
- But WRONG_PATH correction only moves files (no download needed per V2CR-DD-04)
- MISSING_ON_DISK requires re-download, needs SharePoint context
- **Resolution:** Clarify when SharePoint context is needed vs local-only operations

**ISSUE-05: Missing `dry_run` handling in helper functions**
- Spec defines `dry_run=true` creates temp map files with job ID suffix
- No helper functions defined for temp file creation/cleanup
- **Resolution:** Add `create_temp_map_files()`, `cleanup_temp_map_files()` functions

**ISSUE-06: Missing Crawl Report archive creation**
- Spec line 89-102 defines report archive creation after `/crawl` completion
- No function defined in plan for creating report archive
- **Resolution:** Add `create_crawl_report_archive()` function or reference `_V2_SPEC_REPORTS.md`

**ISSUE-07: Default mode differs between spec and plan**
- Plan shows `mode` default as `incremental`
- Spec `_V2_SPEC_ROUTERS.md` line 898 shows `mode=full (default)`
- **Resolution:** Use `mode=full` as default per spec

**ISSUE-08: Missing `source_type` handling in helper functions**
- `get_source_folder_path()` takes `source_type` but no mapping defined
- Spec defines: `file_sources` -> `01_files`, `list_sources` -> `02_lists`, `sitepage_sources` -> `03_sitepages`
- **Resolution:** Document mapping constant in plan

**ISSUE-09: Missing OpenAI file deletion on REMOVED**
- Spec line 421-427 for `mode=full`: "removes all files from the vector store but leaves files in global storage"
- For incremental REMOVED, what happens to global files?
- **Resolution:** Clarify behavior - spec says keep in global storage (other VS may use)

**ISSUE-10: Missing `get_sources_for_scope()` function**
- Referenced in crawler.py streaming pattern but not defined
- Needs to filter domain sources by scope and optional source_id
- **Resolution:** Add function definition to plan

### Ambiguities in Spec (RESOLVED)

**AMB-01: downloaded_utc semantics** - RESOLVED
- `files_map.csv`: `downloaded_utc` = when file was downloaded to local disk
- `vectorstore_map.csv`: `downloaded_utc` = copied from files_map (same value)
- `uploaded_utc` = OpenAI `created_at` timestamp from file upload

**AMB-02: file_type in files_map** - RESOLVED
- Added `file_type` column to `files_map.csv` in spec
- Derived from filename extension (e.g., `document.docx` -> `docx`)

**AMB-03: Error handling for SharePoint failures** - RESOLVED
- **Connection fails:** Log error, skip source, continue with next source
- **Download fails:** Log error, set `sharepoint_error` in files_map, skip item, continue with next item

### Corner Cases Not Explicitly Covered

**CORNER-01: Empty domain (no sources configured)**
- What happens when `file_sources`, `list_sources`, `sitepage_sources` are all empty?
- **Decision:** Log warning "No sources configured for domain", return success with 0 items

**CORNER-02: All files fail to download**
- If 100% of files fail download, should integrity check still run?
- **Decision:** Yes, integrity check always runs per V2CR-DD-03

**CORNER-03: Vector store quota exceeded**
- OpenAI vector stores have file limits
- **Decision:** Log error, mark remaining files as failed, continue with partial success

**CORNER-04: File renamed during crawl**
- File changes between SharePoint list and download attempt
- **Decision:** Download will fail or succeed with new name; next crawl picks up change

**CORNER-05: Very large files (>100MB)**
- OpenAI has file size limits for vector stores
- **Decision:** Skip files exceeding limit, log warning, add to 03_failed

**CORNER-06: Network interruption during download batch**
- Partial files may be written
- **Decision:** files_map.csv only updated after successful download; corrupt partials handled by integrity check

### Missing from Plan

1. **Retry logic with backoff** - Spec mentions retry on concurrency errors, no implementation detail
2. **Timeout configuration** - No timeout values defined for SharePoint/OpenAI calls
3. **File type filtering** - `CRAWLER_HARDCODED_CONFIG.VECTOR_STORE_ACCEPTED_FILE_TYPES` usage not documented
4. **Logging format** - Specific log messages for each step not defined
5. **Job metadata** - What metadata to store with streaming job (domain_id, mode, scope, etc.)

## 9. Detailed Changes/Additions Plan

### common_sharepoint_functions_v2.py

| Change | Type | Priority |
|--------|------|----------|
| Create file with header and imports | New | P0 |
| Add `SharePointFile` dataclass (10 fields) | New | P0 |
| Add `SharePointContext` dataclass | New | P0 |
| Add `create_sharepoint_context()` | New | P0 |
| Add `list_document_library_files()` | New | P0 |
| Add `list_sitepage_files()` | New | P1 |
| Add `list_list_items()` | New | P1 |
| Add `download_file()` with timestamp preservation | New | P0 |
| Add `convert_sp_file_to_dataclass()` | New | P0 |
| Add retry logic for API calls | New | P1 |

### common_crawler_functions_v2.py

| Change | Type | Priority |
|--------|------|----------|
| Add `SOURCE_TYPE_FOLDERS` constant mapping | New | P0 |
| Add `FilesMapEntry` dataclass (add missing fields) | New | P0 |
| Add `VectorStoreMapEntry` dataclass | New | P0 |
| Add `ChangeSet` dataclass | New | P0 |
| Add `IntegrityResult` dataclass | New | P0 |
| Add `get_source_folder_path()` | New | P0 |
| Add `get_map_file_path()` | New | P0 |
| Add `read_map_csv_gracefully()` with retry | New | P0 |
| Add `MapFileWriter` class (buffered append) | New | P0 |
| Add `build_files_map_index()` | New | P0 |
| Add `compute_changes()` | New | P0 |
| Add `is_file_changed()` | New | P0 |
| Add `run_integrity_check()` | New | P0 |
| Add `apply_integrity_corrections()` | New | P0 |
| Add `get_expected_local_path()` | New | P0 |
| Add `load_files_metadata()` | New | P1 |
| Add `save_files_metadata()` | New | P1 |
| Add `update_files_metadata_after_embed()` | New | P1 |
| Add `carry_over_custom_properties()` | New | P1 |
| Add `STANDARD_FIELDS` constant | New | P1 |
| Add `upload_file_to_openai()` | New | P0 |
| Add `add_file_to_vector_store()` | New | P0 |
| Add `wait_for_embedding_completion()` | New | P0 |
| Add `cleanup_failed_embeddings()` | New | P0 |
| Add `create_temp_map_files()` for dry_run | New | P1 |
| Add `cleanup_temp_map_files()` for dry_run | New | P1 |
| Add `get_sources_for_scope()` | New | P0 |

### crawler.py

| Change | Type | Priority |
|--------|------|----------|
| Create file with router boilerplate | New | P0 |
| Add `set_config()` function | New | P0 |
| Add `/crawler` root endpoint (L(u)) | New | P0 |
| Add `/crawler/crawl` endpoint (L(jhs)) | New | P0 |
| Add `/crawler/download_data` endpoint (L(jhs)) | New | P0 |
| Add `/crawler/process_data` endpoint (L(jhs)) | New | P1 |
| Add `/crawler/embed_data` endpoint (L(jhs)) | New | P0 |
| Add `/crawler/cleanup_metadata` endpoint (X(jhs)) | New | P2 |
| Add `_generate_crawler_ui_page()` | New | P0 |
| Add `download_source()` generator | New | P0 |
| Add `process_source()` generator | New | P1 |
| Add `embed_source()` generator | New | P0 |
| Add `build_crawl_result()` | New | P0 |
| Add job metadata (domain_id, mode, scope, vector_store_id) | New | P0 |

### app.py

| Change | Type | Priority |
|--------|------|----------|
| Import and mount crawler router | Modify | P0 |

## 10. Implementation Verification Checklist

### Phase 1: SharePoint Functions

- [ ] **SP-01** `SharePointFile` dataclass has all 10 fields from spec
- [ ] **SP-02** `create_sharepoint_context()` uses certificate auth from config
- [ ] **SP-03** `create_sharepoint_context()` returns `(success, error)` tuple
- [ ] **SP-04** `list_document_library_files()` handles pagination (>5000 items)
- [ ] **SP-05** `list_document_library_files()` applies filter parameter
- [ ] **SP-06** `download_file()` preserves SharePoint `last_modified_utc` on local file
- [ ] **SP-07** `download_file()` creates parent directories if missing
- [ ] **SP-08** `download_file()` handles unicode filenames
- [ ] **SP-09** SharePoint errors logged but don't terminate batch

### Phase 2: Map File Operations

- [ ] **MAP-01** `read_map_csv_gracefully()` retries 3x on lock
- [ ] **MAP-02** `read_map_csv_gracefully()` returns empty list on missing file (mode=full fallback)
- [ ] **MAP-03** `read_map_csv_gracefully()` logs warning on corrupt file
- [ ] **MAP-04** `MapFileWriter.write_header()` creates file with atomic write (temp + rename)
- [ ] **MAP-05** `MapFileWriter.append_row()` buffers rows until threshold
- [ ] **MAP-06** `MapFileWriter._flush()` appends buffered rows to file
- [ ] **MAP-07** `MapFileWriter.finalize()` flushes remaining buffer
- [ ] **MAP-08** Force flush on: header creation, first item, last item
- [ ] **MAP-09** CSV files use UTF-8 encoding
- [ ] **MAP-10** `build_files_map_index()` keys by `sharepoint_unique_file_id`

### Phase 3: Change Detection

- [ ] **CHG-01** `compute_changes()` correctly identifies ADDED files
- [ ] **CHG-02** `compute_changes()` correctly identifies REMOVED files
- [ ] **CHG-03** `compute_changes()` correctly identifies CHANGED files
- [ ] **CHG-04** `is_file_changed()` compares all 4 fields (filename, server_relative_url, file_size, last_modified_utc)
- [ ] **CHG-05** Change detection handles A1-A16 edge cases
- [ ] **CHG-06** REMOVED files are deleted from disk
- [ ] **CHG-07** CHANGED files: old deleted, new downloaded

### Phase 4: Integrity Check

- [ ] **INT-01** Integrity check runs after every download_data (V2CR-DD-03)
- [ ] **INT-02** Detects MISSING_IN_MAP anomaly
- [ ] **INT-03** Detects MISSING_ON_DISK anomaly
- [ ] **INT-04** Detects ORPHAN_ON_DISK anomaly
- [ ] **INT-05** Detects WRONG_PATH anomaly
- [ ] **INT-06** Corrects MISSING_ON_DISK by re-download
- [ ] **INT-07** Corrects ORPHAN_ON_DISK by deletion
- [ ] **INT-08** Corrects WRONG_PATH by move (not re-download per V2CR-DD-04)
- [ ] **INT-09** Updates files_map.csv after corrections
- [ ] **INT-10** Logs summary of corrections

### Phase 5: Embed Operations

- [ ] **EMB-01** `upload_file_to_openai()` returns `openai_file_id`
- [ ] **EMB-02** `add_file_to_vector_store()` adds file to specified VS
- [ ] **EMB-03** `wait_for_embedding_completion()` polls until no `in_progress` files
- [ ] **EMB-04** `wait_for_embedding_completion()` has timeout
- [ ] **EMB-05** `cleanup_failed_embeddings()` moves failed to 03_failed
- [ ] **EMB-06** `cleanup_failed_embeddings()` removes from VS and global storage
- [ ] **EMB-07** `cleanup_failed_embeddings()` updates vectorstore_map.csv
- [ ] **EMB-08** Incremental mode skips files already in vectorstore_map
- [ ] **EMB-09** Full mode removes all source files from VS first

### Phase 6: Metadata

- [ ] **META-01** `files_metadata.json` loaded correctly
- [ ] **META-02** `files_metadata.json` saved with atomic write
- [ ] **META-03** Custom properties carried over by `sharepoint_unique_file_id`
- [ ] **META-04** STANDARD_FIELDS constant matches spec
- [ ] **META-05** Multiple entries per `sharepoint_unique_file_id` supported (version history)

### Phase 7: Router Endpoints

- [ ] **RTR-01** `/crawler` returns UI with filtered jobs table
- [ ] **RTR-02** `/crawler/crawl` accepts all query params (domain_id, mode, scope, source_id, dry_run)
- [ ] **RTR-03** `/crawler/crawl` default mode is `full`
- [ ] **RTR-04** `/crawler/crawl` creates streaming job
- [ ] **RTR-05** `/crawler/crawl` runs download -> process -> embed
- [ ] **RTR-06** `/crawler/download_data` runs download only
- [ ] **RTR-07** `/crawler/process_data` runs process only
- [ ] **RTR-08** `/crawler/embed_data` runs embed only
- [ ] **RTR-09** Job supports pause/resume/cancel
- [ ] **RTR-10** Job metadata includes domain_id, mode, scope, vector_store_id
- [ ] **RTR-11** `dry_run=true` creates temp map files
- [ ] **RTR-12** `dry_run=true` cleans up temp files at end
- [ ] **RTR-13** 404 returned for missing domain_id
- [ ] **RTR-14** 404 returned for missing source_id

### Phase 8: UI

- [ ] **UI-01** Jobs table filters to `router == 'crawler'`
- [ ] **UI-02** Table shows: ID, Action, Domain ID, Vector Store ID, Mode, Scope, Source ID, Actions
- [ ] **UI-03** Console panel visible by default
- [ ] **UI-04** Monitor button connects SSE to console
- [ ] **UI-05** Pause/Resume buttons work
- [ ] **UI-06** Cancel button works
- [ ] **UI-07** Navigation links present (Back, Domains, Crawl Results)

### Phase 9: Integration

- [ ] **INTG-01** Router mounted at `/v2/crawler`
- [ ] **INTG-02** `set_config()` called from app.py
- [ ] **INTG-03** Logging uses MiddlewareLogger
- [ ] **INTG-04** Jobs stored in `jobs/crawler/` folder
- [ ] **INTG-05** StreamingJobWriter integration works

## Spec Changes

**[2024-12-27 16:33]**
- Initial implementation plan created

**[2024-12-27 16:40]**
- Added verification findings (10 issues, 3 ambiguities, 6 corner cases)
- Added detailed changes/additions plan with priorities
- Added implementation verification checklist (55 items across 9 phases)

**[2024-12-27 16:55]**
- Updated TOC with sections 8, 9, 10
- Added `file_type` field to `FilesMapEntry` dataclass per AMB-02
- Replaced `write_map_csv_gracefully()` with `MapFileWriter` class in changes table
- Updated Phase 2 verification checklist for `MapFileWriter` (now 10 items)
- Total checklist items: 57 across 9 phases
