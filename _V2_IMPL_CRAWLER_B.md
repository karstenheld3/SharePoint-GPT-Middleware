# Implementation Plan: /v2/crawler Router (Option B: Step-based Functions)

**Plan ID**: V2CR-IP01B
**Goal**: Implement the V2 crawler router using composable step functions with shared helpers
**Target files**:
- `/src/routers_v2/crawler.py` (NEW)
- `/src/routers_v2/common_map_file_functions_v2.py` (NEW)
- `/src/routers_v2/common_embed_functions_v2.py` (NEW)
- `/src/routers_v2/common_sharepoint_functions_v2.py` (EXTEND)
- `/src/routers_v2/common_crawler_functions_v2.py` (EXTEND)

**Depends on:**
- `_V2_SPEC_CRAWLER.md` for crawling process and change detection
- `_V2_SPEC_CRAWLER_UI.md` for UI specification
- `_V2_SPEC_ROUTERS.md` for endpoint design and streaming job infrastructure
- `_V2_SPEC_COMMON_UI_FUNCTIONS.md` for UI generation functions

**Does not depend on:**
- `_V1_SPEC_COMMON_UI_FUNCTIONS.md` (V1 UI functions superseded by V2)

## Table of Contents

1. File Structure
2. common_map_file_functions_v2.py (NEW)
3. common_embed_functions_v2.py (NEW)
4. common_sharepoint_functions_v2.py (EXTEND)
5. common_crawler_functions_v2.py (EXTEND)
6. crawler.py (NEW)
7. Spec Requirements Coverage
8. Edge Case Handling
9. Implementation Order
10. Verification Findings
11. Detailed Changes/Additions Plan
12. Implementation Verification Checklist

## 1. File Structure

```
/src/routers_v2/
├── crawler.py                        # Router endpoints, orchestrator, UI (~500 lines)
├── common_map_file_functions_v2.py   # MapFileWriter, reader, change detection (~250 lines) [NEW]
├── common_embed_functions_v2.py      # OpenAI upload, vector store ops (~200 lines) [NEW]
├── common_sharepoint_functions_v2.py # SharePoint ops (~350 lines) [EXTEND +100 lines]
└── common_crawler_functions_v2.py    # Domain/source dataclasses (~350 lines) [EXTEND +90 lines]
```

**Design philosophy:**
- Each module has a single responsibility
- Step functions are pure: explicit inputs, explicit outputs
- Shared helpers prevent duplication across steps
- Source-type differences handled via inline conditionals (minimal branching)

## 2. common_map_file_functions_v2.py (NEW)

**Purpose:** Map file I/O with buffered writes, change detection algorithm.

### Dataclasses

```python
@dataclass
class SharePointMapRow:
  """Row in sharepoint_map.csv - current SharePoint state."""
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
class FilesMapRow:
  """Row in files_map.csv - local file state."""
  sharepoint_listitem_id: int
  sharepoint_unique_file_id: str
  filename: str
  file_type: str
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
class VectorStoreMapRow:
  """Row in vectorstore_map.csv - embedded file state."""
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
class ChangeDetectionResult:
  """Result of comparing SharePoint state vs local state."""
  added: list[SharePointMapRow]    # New files in SharePoint
  removed: list[FilesMapRow]       # Files no longer in SharePoint
  changed: list[SharePointMapRow]  # Files with field differences
  unchanged: list[FilesMapRow]     # Files matching exactly
```

### Classes

```python
class MapFileWriter:
  """
  Buffered writer for CSV map files with graceful error handling.
  Implements V2CR-FR-05: Buffered append writes.
  
  Usage:
    writer = MapFileWriter(filepath, SharePointMapRow)
    writer.write_header()
    for item in items:
      writer.append_row(item)
    writer.finalize()
  """
  def __init__(self, filepath: str, row_class: type, buffer_size: int = None)
  def write_header(self) -> None  # Atomic: temp file + rename
  def append_row(self, row: dataclass) -> None  # Buffered
  def flush(self) -> None  # Force write buffer to disk
  def finalize(self) -> None  # Flush + close
```

### Functions

```python
# Read map files
def read_sharepoint_map(filepath: str) -> list[SharePointMapRow]
def read_files_map(filepath: str) -> list[FilesMapRow]
def read_vectorstore_map(filepath: str) -> list[VectorStoreMapRow]

# Change detection (V2CR-FR-01, V2CR-FR-02)
def detect_changes(sharepoint_items: list[SharePointMapRow], local_items: list[FilesMapRow]) -> ChangeDetectionResult

# Helpers
def is_file_changed(sp: SharePointMapRow, local: FilesMapRow) -> bool
  # For download step: compares filename, server_relative_url, file_size, last_modified_utc

def is_file_changed_for_embed(files_row: FilesMapRow, vs_row: VectorStoreMapRow) -> bool
  # For embed step: compares file_size, last_modified_utc only

```

## 3. common_embed_functions_v2.py (NEW)

**Purpose:** OpenAI file upload and vector store operations.

### Functions

```python
# File operations
async def upload_file_to_openai(client, filepath: str, purpose: str = "assistants") -> tuple[str, str]
  # Returns: (openai_file_id, error_message)

async def delete_file_from_openai(client, file_id: str) -> tuple[bool, str]
  # Returns: (success, error_message)

# Vector store operations
async def add_file_to_vector_store(client, vector_store_id: str, file_id: str) -> tuple[bool, str]
  # Returns: (success, error_message)

async def remove_file_from_vector_store(client, vector_store_id: str, file_id: str) -> tuple[bool, str]
  # Returns: (success, error_message)

async def list_vector_store_files(client, vector_store_id: str) -> list[dict]
  # Returns list of file objects with id, status, etc.

async def wait_for_vector_store_ready(client, vector_store_id: str, file_ids: list[str], timeout_seconds: int = 300) -> list[dict]
  # Polls until all files have status != 'in_progress'
  # Returns list of file statuses

async def get_failed_embeddings(client, vector_store_id: str, file_ids: list[str]) -> list[dict]
  # Returns files where status != 'completed'
```

## 4. common_sharepoint_functions_v2.py (EXTEND)

**Purpose:** SharePoint API operations. Already exists with basic structure.

### Existing (modify SharePointFile)

```python
@dataclass
class SharePointFile:
  """File metadata from SharePoint API - aligned with sharepoint_map.csv columns."""
  sharepoint_listitem_id: int       # Was: id (str)
  sharepoint_unique_file_id: str    # Was: unique_id
  filename: str
  file_type: str                    # NEW: extension without dot
  file_size: int
  url: str                          # NEW: URL-encoded full URL
  raw_url: str                      # NEW: unencoded full URL  
  server_relative_url: str
  last_modified_utc: str
  last_modified_timestamp: int
```

### Existing functions (keep as-is)
- `get_or_create_pem_from_pfx()`
- `connect_to_site_using_client_id_and_certificate()`
- `try_get_document_library()`
- `get_document_library_files()` - update to populate new SharePointFile fields

### Add: File download function

```python
def download_file_from_sharepoint(
  ctx: ClientContext,
  server_relative_url: str,
  target_path: str,
  preserve_timestamp: bool = True,
  last_modified_timestamp: int = None
) -> tuple[bool, str]:
  """
  Download a single file from SharePoint to local disk.
  
  Args:
    ctx: Authenticated SharePoint context
    server_relative_url: SharePoint file path (e.g., "/sites/demo/Shared Documents/file.docx")
    target_path: Local filesystem path to save file
    preserve_timestamp: If True, set file mtime to SharePoint last_modified
    last_modified_timestamp: Unix timestamp to apply if preserve_timestamp=True
    
  Returns:
    (success, error_message)
  """
```

### Add: List operations (for list_sources)

```python
def get_list_items(ctx: ClientContext, list_name: str, filter: str, logger: MiddlewareLogger) -> list[dict]:
  """Get all items from a SharePoint list as dictionaries."""

def export_list_to_csv(ctx: ClientContext, list_name: str, filter: str, target_path: str, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Export SharePoint list to CSV file. Returns (success, error_message)."""
```

### Add: Site pages operations (for sitepage_sources)

```python
def get_site_pages(ctx: ClientContext, pages_url_part: str, filter: str, logger: MiddlewareLogger) -> list[SharePointFile]:
  """Get site pages metadata. Similar to get_document_library_files but for SitePages library."""

def download_site_page_html(ctx: ClientContext, server_relative_url: str, target_path: str, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Download site page content as HTML file. Returns (success, error_message)."""
```

## 5. common_crawler_functions_v2.py (EXTEND)

**Purpose:** Domain/source dataclasses and helpers. Already exists.

### Existing (keep as-is)
- `FileSource`, `SitePageSource`, `ListSource` dataclasses
- `DomainConfig` dataclass
- `load_domain()`, `load_all_domains()`
- `domain_config_to_dict()`, `validate_domain_config()`
- `save_domain_to_file()`, `delete_domain_folder()`, `rename_domain()`

### Add: Path helpers

```python
# Map source_type to folder prefix using config constants
SOURCE_TYPE_FOLDERS = {
  "file_sources": CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOCUMENTS_FOLDER,      # "01_files"
  "list_sources": CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_LISTS_FOLDER,          # "02_lists"
  "sitepage_sources": CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_SITEPAGES_FOLDER   # "03_sitepages"
}

def get_source_folder_path(storage_path: str, domain_id: str, source_type: str, source_id: str) -> str:
  """
  Get the base folder path for a source.
  Example: /data/crawler/DOMAIN01/01_files/source01/
  """
  crawler_folder = CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_CRAWLER_SUBFOLDER
  return os.path.join(storage_path, crawler_folder, domain_id, SOURCE_TYPE_FOLDERS[source_type], source_id)

def get_embedded_folder_path(storage_path: str, domain_id: str, source_type: str, source_id: str) -> str:
  """Get path to 02_embedded subfolder."""
  return os.path.join(get_source_folder_path(storage_path, domain_id, source_type, source_id), CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_EMBEDDED_SUBFOLDER)

def get_failed_folder_path(storage_path: str, domain_id: str, source_type: str, source_id: str) -> str:
  """Get path to 03_failed subfolder."""
  return os.path.join(get_source_folder_path(storage_path, domain_id, source_type, source_id), CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_FAILED_SUBFOLDER)

def get_originals_folder_path(storage_path: str, domain_id: str, source_type: str, source_id: str) -> str:
  """Get path to 01_originals subfolder (lists/sitepages only)."""
  return os.path.join(get_source_folder_path(storage_path, domain_id, source_type, source_id), CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_ORIGINALS_SUBFOLDER)

def server_relative_url_to_local_path(server_relative_url: str, sharepoint_url_part: str) -> str:
  """
  Convert SharePoint server_relative_url to local relative path.
  Example: "/sites/demo/Shared Documents/Reports/Q1.docx" -> "Reports/Q1.docx"
  """

def get_file_relative_path(domain_id: str, source_type: str, source_id: str, subfolder: str, local_path: str) -> str:
  """
  Build file_relative_path for map files.
  Example: "DOMAIN01\\01_files\\source01\\02_embedded\\Reports\\Q1.docx"
  """
```

### Add: files_metadata.json helpers

```python
STANDARD_METADATA_FIELDS = {
  "sharepoint_listitem_id", "sharepoint_unique_file_id", "openai_file_id",
  "file_relative_path", "url", "raw_url", "server_relative_url",
  "filename", "file_type", "file_size", "last_modified_utc", "last_modified_timestamp",
  "embedded_utc", "source_id", "source_type"
}

def load_files_metadata(domain_path: str) -> list[dict]:
  """Load files_metadata.json, return empty list if not exists."""

def save_files_metadata(domain_path: str, metadata: list[dict]) -> None:
  """Save files_metadata.json with graceful write (temp + rename)."""

def update_files_metadata(domain_path: str, new_entries: list[dict]) -> None:
  """
  Add new entries to files_metadata.json with carry-over of custom properties.
  Implements V2CR-FR-06.
  """

def carry_over_custom_properties(new_entry: dict, existing_entries: list[dict]) -> dict:
  """Copy non-standard fields from most recent existing entry with same sharepoint_unique_file_id."""
```

### Add: Source filtering helper

```python
def get_sources_for_scope(
  domain: DomainConfig,
  scope: str,  # "all" | "files" | "lists" | "sitepages"
  source_id: str | None = None
) -> list[tuple[str, FileSource | ListSource | SitePageSource]]:
  """
  Filter domain sources by scope and optional source_id.
  
  Returns: List of (source_type, source) tuples.
  
  Example:
    get_sources_for_scope(domain, "files", None)
    -> [("file_sources", FileSource(...)), ("file_sources", FileSource(...))]
    
    get_sources_for_scope(domain, "all", "source01")
    -> [("file_sources", FileSource(source_id="source01"))]  # if found
  """
```

### dry_run Implementation Pattern

**Design principle:**
1. Map files use temp filenames: `sharepoint_map_[JOB_ID].csv` (same folder, different name)
2. Skip ONLY the mutation line (downloads, uploads, deletes, moves)
3. Temp map files are used throughout the complete chain
4. Temp map files are deleted at end of job

**Temp file naming:**

```python
def get_map_filename(base_name: str, job_id: str = None) -> str:
  """
  Get map filename, with job_id suffix for dry_run mode.
  
  Examples:
    get_map_filename("sharepoint_map.csv", None) -> "sharepoint_map.csv"
    get_map_filename("sharepoint_map.csv", "[jb_123]") -> "sharepoint_map_[jb_123].csv"
    get_map_filename("files_map.csv", "[jb_123]") -> "files_map_[jb_123].csv"
    get_map_filename("vectorstore_map.csv", "[jb_123]") -> "vectorstore_map_[jb_123].csv"
  """
  if not job_id: return base_name
  name, ext = os.path.splitext(base_name)
  return f"{name}_{job_id}{ext}"  # job_id already includes brackets

def cleanup_temp_map_files(source_folder: str, job_id: str) -> None:
  """Delete temp map files after dry_run completes. Called in finally block."""
```

**Chain usage in /crawl with dry_run=true:**

```
1. step_download_source:
   └─ Reads real sharepoint_map.csv (previous state)
   └─ Writes sharepoint_map_[jb_123].csv (new state)
   └─ Writes files_map_[jb_123].csv (what would be downloaded)
   └─ Skips actual download

2. step_integrity_check:
   └─ Reads sharepoint_map_[jb_123].csv
   └─ Reads files_map_[jb_123].csv
   └─ Logs anomalies but skips corrections

3. step_process_source:
   └─ Reads files_map_[jb_123].csv
   └─ Updates files_map_[jb_123].csv with expected file_relative_path
   └─ Skips actual file processing

4. step_embed_source:
   └─ Reads files_map_[jb_123].csv
   └─ Writes vectorstore_map_[jb_123].csv (what would be embedded)
   └─ Skips OpenAI upload and vector store operations

5. Cleanup (finally block):
   └─ Deletes sharepoint_map_[jb_123].csv
   └─ Deletes files_map_[jb_123].csv
   └─ Deletes vectorstore_map_[jb_123].csv
```

**Mutation points (skipped when dry_run=true):**

- **Download - Write file to disk**: `if not dry_run: download_file(...)`
- **Download - Set file timestamp**: `if not dry_run: os.utime(path, ...)`
- **Integrity - Re-download missing**: `if not dry_run: download_file(...)`
- **Integrity - Delete orphan**: `if not dry_run: os.remove(path)`
- **Integrity - Move wrong path**: `if not dry_run: shutil.move(...)`
- **Process - Write processed file**: `if not dry_run: write_file(...)`
- **Embed - Upload to OpenAI**: `if not dry_run: client.files.create(...)`
- **Embed - Add to vector store**: `if not dry_run: client.vector_stores.files.create(...)`
- **Embed - Delete from VS**: `if not dry_run: client.vector_stores.files.delete(...)`
- **Embed - Move to 03_failed**: `if not dry_run: shutil.move(...)`
- **Metadata - Write files_metadata.json**: `if not dry_run: save_files_metadata(...)`
- **Report - Create archive**: `if not dry_run: create_crawl_report(...)`

**Temp map files ARE written** - preview of what WOULD happen.
**Real map files NOT modified** - original state preserved.
**files_metadata.json NOT written** - only contains successfully embedded files.

### Add: File type filtering

```python
def is_file_embeddable(filename: str) -> bool:
  """
  Check if file type is accepted by vector stores.
  Uses CRAWLER_HARDCODED_CONFIG.DEFAULT_FILETYPES_ACCEPTED_BY_VECTOR_STORES.
  
  Returns: True if file extension is in accepted list.
  """

def filter_embeddable_files(files: list[FilesMapRow]) -> tuple[list[FilesMapRow], list[FilesMapRow]]:
  """
  Split files into embeddable and non-embeddable.
  Returns: (embeddable, skipped)
  Skipped files are logged with warning.
  """
```

## 6. crawler.py (NEW)

**Purpose:** Router endpoints, step functions, orchestrator, UI generation.

### Module constants

```python
router = APIRouter()
config = None
router_prefix = None
router_name = "crawler"
main_page_nav_html = '<a href="/">Back to Main Page</a> | <a href="/v2/domains?format=ui">Domains</a>'
```

### Step function signatures

```python
@dataclass
class DownloadResult:
  """Result of download_data step for one source."""
  source_id: str
  source_type: str
  total_files: int
  downloaded: int
  skipped: int
  errors: int
  removed: int  # For incremental mode

@dataclass
class ProcessResult:
  """Result of process_data step for one source."""
  source_id: str
  source_type: str
  total_files: int
  processed: int
  skipped: int
  errors: int

@dataclass
class EmbedResult:
  """Result of embed_data step for one source."""
  source_id: str
  source_type: str
  total_files: int
  uploaded: int
  embedded: int
  failed: int
  removed: int  # Files removed from vector store

@dataclass
class IntegrityResult:
  """Result of integrity check for one source."""
  source_id: str
  files_verified: int
  missing_redownloaded: int
  orphans_deleted: int
  wrong_path_moved: int

# Step functions (async generators yielding SSE strings)
async def step_download_source(
  storage_path: str,
  domain: DomainConfig,
  source: FileSource | ListSource | SitePageSource,
  source_type: str,
  mode: str,  # "full" | "incremental"
  dry_run: bool,
  retry_batches: int,  # default=2, set to 1 to disable retries
  writer: StreamingJobWriter,
  logger: MiddlewareLogger,
  crawler_config: dict  # Client ID, cert path, etc.
) -> AsyncGenerator[str, None]:
  """
  Download files from SharePoint for one source.
  Yields SSE log events.
  Updates sharepoint_map.csv and files_map.csv.
  
  Download target varies by source_type:
    - file_sources: downloads to 02_embedded/ directly
    - list_sources: exports to 01_originals/ as CSV
    - sitepage_sources: downloads to 01_originals/ as HTML
  
  Retry logic:
    - Batch 1: Process all items, collect failures into retry_list
    - Batch 2 (if retry_batches >= 2): Retry items from retry_list
    - Failures after all batches: logged with sharepoint_error
  
  After download completes: runs integrity check for this source.
  """

async def step_integrity_check(
  storage_path: str,
  domain_id: str,
  source: FileSource | ListSource | SitePageSource,
  source_type: str,
  dry_run: bool,
  writer: StreamingJobWriter,
  logger: MiddlewareLogger,
  crawler_config: dict
) -> AsyncGenerator[str, None]:
  """
  Verify local storage matches sharepoint_map.csv.
  Yields SSE log events.
  Corrects anomalies: MISSING_ON_DISK, ORPHAN_ON_DISK, WRONG_PATH.
  
  dry_run behavior: Detection runs normally, corrections skipped:
  - MISSING_ON_DISK: logged, not re-downloaded
  - ORPHAN_ON_DISK: logged, not deleted
  - WRONG_PATH: logged, not moved
  
  Log output format (per spec line 612-614):
  - If anomalies found: "Integrity check corrected: X missing, Y orphans deleted, Z moved"
  - If dry_run + anomalies: "[DRY RUN] Would correct: X missing, Y orphans, Z wrong path"
  - If no anomalies: "Integrity check passed: N files verified"
  
  Returns: IntegrityResult dataclass with counts.
  """

async def step_process_source(
  storage_path: str,
  domain_id: str,
  source: ListSource | SitePageSource,
  source_type: str,
  dry_run: bool,
  writer: StreamingJobWriter,
  logger: MiddlewareLogger
) -> AsyncGenerator[str, None]:
  """
  Process downloaded files (lists -> markdown, sitepages -> cleaned HTML).
  Yields SSE log events.
  Updates files_map.csv with new file_relative_path.
  Only for list_sources and sitepage_sources.
  
  dry_run behavior: Processing logic runs, file write skipped:
  - Logs what would be written to 02_embedded/
  - files_map.csv updated with expected file_relative_path
  """

async def step_embed_source(
  storage_path: str,
  domain: DomainConfig,
  source: FileSource | ListSource | SitePageSource,
  source_type: str,
  mode: str,
  dry_run: bool,
  retry_batches: int,  # default=2
  writer: StreamingJobWriter,
  logger: MiddlewareLogger,
  openai_client
) -> AsyncGenerator[str, None]:
  """
  Upload files to OpenAI and add to vector store.
  Yields SSE log events.
  Updates vectorstore_map.csv and files_metadata.json.
  """
```

### Job metadata specification

StreamingJobWriter stores job metadata in the job file header. Crawler jobs include:

```python
job_metadata = {
  "domain_id": str,           # Domain being crawled
  "vector_store_id": str,     # Target vector store ID
  "mode": str,                # "full" | "incremental"
  "scope": str,               # "all" | "files" | "lists" | "sitepages"
  "source_id": str | None,    # If filtering to single source
  "dry_run": bool,            # True if simulation mode
  "retry_batches": int        # Number of retry batches
}
```

This metadata is used by:
- UI to display job parameters in table
- `/v2/jobs/get` to return job details
- Crawl report archive to record parameters

### Orchestrator functions

```python
async def crawl_domain(
  storage_path: str,
  domain: DomainConfig,
  mode: str,
  scope: str,  # "all" | "files" | "lists" | "sitepages"
  source_id: str | None,
  dry_run: bool,
  writer: StreamingJobWriter,
  logger: MiddlewareLogger,
  crawler_config: dict,
  openai_client
) -> dict:
  """
  Full crawl: download -> integrity_check -> process -> embed -> archive for all sources in scope.
  Steps:
    1. For each source in scope: step_download_source()
    2. For each source in scope: step_integrity_check()
    3. For list/sitepage sources: step_process_source()
    4. For each source in scope: step_embed_source()
    5. If not dry_run and not cancelled: create crawl report archive
  Returns result summary dict.
  """

async def download_domain_data(
  storage_path: str,
  domain: DomainConfig,
  mode: str,
  scope: str,
  source_id: str | None,
  dry_run: bool,
  writer: StreamingJobWriter,
  logger: MiddlewareLogger,
  crawler_config: dict
) -> dict:
  """Download step only. Returns result summary."""

async def process_domain_data(
  storage_path: str,
  domain: DomainConfig,
  scope: str,
  source_id: str | None,
  writer: StreamingJobWriter,
  logger: MiddlewareLogger
) -> dict:
  """Process step only. Returns result summary."""

async def embed_domain_data(
  storage_path: str,
  domain: DomainConfig,
  mode: str,
  scope: str,
  source_id: str | None,
  dry_run: bool,
  writer: StreamingJobWriter,
  logger: MiddlewareLogger,
  openai_client
) -> dict:
  """Embed step only. Returns result summary."""

def create_crawl_report(
  storage_path: str,
  domain_id: str,
  mode: str,
  scope: str,
  results: list,  # list[DownloadResult | ProcessResult | EmbedResult]
  started_utc: str,
  finished_utc: str
) -> str:
  """
  Create timestamped zip archive after /crawl completes (per spec line 89-102).
  
  Returns: report_id (e.g., 'crawls/2025-01-15_14-25-00_TEST01_all_full')
  
  Archive contents:
  - report.json: {report_id, title, type, created_utc, ok, error, files, parameters, timing, per_source_stats}
  - *_map.csv snapshots from each source
  
  Storage: PERSISTENT_STORAGE_PATH/reports/crawls/[filename].zip
  
  Not created when:
  - dry_run=true
  - Job cancelled
  - Individual actions (/download_data, /process_data, /embed_data)
  """
```

### Endpoints

```
GET /v2/crawler                    -> Router docs (HTML) or jobs list (json/html/ui)
GET /v2/crawler/crawl              -> Full crawl (stream)
GET /v2/crawler/download_data      -> Download step only (stream)
GET /v2/crawler/process_data       -> Process step only (stream)
GET /v2/crawler/embed_data         -> Embed step only (stream)
GET /v2/crawler/cleanup_metadata   -> Clean stale entries from files_metadata.json (json)
```

### Query Parameters (streaming endpoints)

- **domain_id** (required): Domain to crawl
- **mode**: `full` | `incremental`, default `full` (per spec line 898)
- **scope**: `all` | `files` | `lists` | `sitepages`, default `all`
- **source_id**: Filter to single source
- **format**: `json` | `stream`, default `json`
- **dry_run**: `true` | `false`, default `false`
- **retry_batches**: integer, default `2` (1 = no retry)

### UI generation

```python
def _generate_crawler_ui_page(jobs: list) -> str:
  """Generate the Crawler UI page HTML using common_ui_functions_v2."""
  # Reuses: generate_html_head, generate_toast_container, generate_modal_structure,
  #         generate_console_panel, generate_core_js, generate_console_js, etc.
  # Router-specific JS: refreshJobsTable, monitorJob, controlJob
```

## 7. Spec Requirements Coverage

**Functional Requirements:**
- **V2CR-FR-01**: Change detection by immutable ID -> `detect_changes()` in common_map_file_functions_v2.py
- **V2CR-FR-02**: Four-field comparison -> `is_file_changed()` compares filename, server_relative_url, file_size, last_modified_utc
- **V2CR-FR-03**: Integrity check after download -> `step_integrity_check()` runs after every `step_download_source()`
- **V2CR-FR-04**: Self-healing corrections -> Integrity check re-downloads missing, deletes orphans, moves wrong-path
- **V2CR-FR-05**: Graceful map file operations -> `MapFileWriter` class with buffered appends, atomic header write
- **V2CR-FR-06**: files_metadata.json carry-over -> `update_files_metadata()` with `carry_over_custom_properties()`

**Design Decisions:**
- **V2CR-DD-01**: sharepoint_unique_file_id as key -> All change detection uses this field as primary key
- **V2CR-DD-02**: Four-field change detection -> `is_file_changed()` function
- **V2CR-DD-03**: Integrity check always runs -> Called unconditionally after download step
- **V2CR-DD-04**: Move over re-download for WRONG_PATH -> Integrity check moves files instead of re-downloading
- **V2CR-DD-05**: files_metadata.json keyed by openai_file_id -> Multiple entries per sharepoint_unique_file_id allowed

**Implementation Guarantees:**
- **V2CR-IG-01**: Local storage mirrors SharePoint -> Integrity check verifies and corrects
- **V2CR-IG-02**: No orphan files after integrity check -> Orphan detection and deletion in integrity check
- **V2CR-IG-03**: files_map.csv reflects disk state -> Integrity check updates map after corrections
- **V2CR-IG-04**: Custom properties survive updates -> carry_over_custom_properties() in files_metadata update
- **V2CR-IG-05**: All edge cases handled without data loss -> See Edge Case Handling below

## 8. Edge Case Handling

### A. SharePoint state changes (V2CR-IP01B-EC-01 to EC-16)

- **V2CR-IP01B-EC-01** (ADDED): `detect_changes()` -> added list -> download
- **V2CR-IP01B-EC-02** (REMOVED): `detect_changes()` -> removed list -> delete local file
- **V2CR-IP01B-EC-03** (CONTENT_UPDATED): `is_file_changed()` -> changed list -> re-download
- **V2CR-IP01B-EC-04** (RENAMED): `is_file_changed()` (filename differs) -> re-download
- **V2CR-IP01B-EC-05** (MOVED): `is_file_changed()` (server_relative_url differs) -> re-download
- **V2CR-IP01B-EC-06** (COMBINED_CHANGES): `is_file_changed()` catches any field difference
- **V2CR-IP01B-EC-07** (RESTORED): ID reappears -> detected as ADDED
- **V2CR-IP01B-EC-08** (VERSION_ROLLBACK): last_modified_utc differs -> CHANGED
- **V2CR-IP01B-EC-09** (COPIED): New ID -> detected as ADDED
- **V2CR-IP01B-EC-10** (REPLACED): Old ID REMOVED + new ID ADDED
- **V2CR-IP01B-EC-11** (CHECK-IN/CHECK-OUT): If last_modified_utc changed -> CHANGED
- **V2CR-IP01B-EC-12** (FOLDER_RENAMED): All files have new server_relative_url -> CHANGED
- **V2CR-IP01B-EC-13** (FOLDER_MOVED): All files have new server_relative_url -> CHANGED

### B. Local storage anomalies (V2CR-IP01B-EC-14 to EC-20)

- **V2CR-IP01B-EC-14** (LOCAL_FILE_MISSING): `step_integrity_check()` -> re-download
- **V2CR-IP01B-EC-15** (LOCAL_FILE_EXTRA): `step_integrity_check()` -> delete orphan
- **V2CR-IP01B-EC-16** (LOCAL_FILE_WRONG_PATH): `step_integrity_check()` -> move file
- **V2CR-IP01B-EC-17** (LOCAL_FILE_CORRUPTED): Detected during embed (read fails) -> set error, move to 03_failed
- **V2CR-IP01B-EC-18** (LOCAL_FOLDER_MISSING): `os.makedirs()` creates parent on download
- **V2CR-IP01B-EC-19** (MAP_FILE_MISSING): Fallback to mode=full
- **V2CR-IP01B-EC-20** (MAP_FILE_CORRUPTED): Fallback to mode=full, log warning

### C. Vector store anomalies (V2CR-IP01B-EC-21 to EC-25)

- **V2CR-IP01B-EC-21** (VS_FILE_MISSING): `step_embed_source()` cleanup removes from vectorstore_map, re-embeds
- **V2CR-IP01B-EC-22** (VS_FILE_EXTRA): Ignored (may belong to other source/domain)
- **V2CR-IP01B-EC-23** (VS_EMBEDDING_FAILED): Move to 03_failed, set embedding_error in map
- **V2CR-IP01B-EC-24** (VS_DELETED): Return 404 error, abort embed
- **V2CR-IP01B-EC-25** (OPENAI_FILE_DELETED): Re-upload during embed

### D. Timing/concurrency (V2CR-IP01B-EC-26 to EC-31)

- **V2CR-IP01B-EC-26** (RAPID_CHANGES): Only final state visible, handled normally
- **V2CR-IP01B-EC-27** (CONCURRENT_CRAWLS): `MapFileWriter` with atomic writes, retry on error
- **V2CR-IP01B-EC-28** (PARTIAL_FAILURE): Next run picks up from map file state
- **V2CR-IP01B-EC-29** (SHAREPOINT_TIMEOUT): Retry with backoff in `download_file_from_sharepoint`
- **V2CR-IP01B-EC-30** (OPENAI_RATE_LIMIT): Retry with backoff in `upload_file_to_openai`
- **V2CR-IP01B-EC-31** (OPENAI_TIMEOUT): Retry with backoff, fail gracefully

### E. Data quality (V2CR-IP01B-EC-32 to EC-37)

- **V2CR-IP01B-EC-32** (UNICODE_FILENAME): UTF-8 encoding throughout
- **V2CR-IP01B-EC-33** (VERY_LONG_PATH): `normalize_long_path()` from common_utility_functions
- **V2CR-IP01B-EC-34** (ZERO_BYTE_FILE): Download succeeds, embed may fail -> 03_failed
- **V2CR-IP01B-EC-35** (UNSUPPORTED_TYPE): Skip during embed, log warning
- **V2CR-IP01B-EC-36** (DUPLICATE_FILENAME): Different server_relative_url -> different local paths
- **V2CR-IP01B-EC-37** (SPECIAL_CHARS_IN_PATH): URL-decode for local path

## 9. Implementation Order

**Phase 1: Foundation (~2 hours)**
- **V2CR-IP01B-IS-01**: `common_map_file_functions_v2.py` - dataclasses, MapFileWriter, read functions, change detection
- **V2CR-IP01B-IS-02**: Extend `common_crawler_functions_v2.py` - path helpers, files_metadata helpers

**Phase 2: SharePoint operations (~1.5 hours)**
- **V2CR-IP01B-IS-03**: Extend `common_sharepoint_functions_v2.py` - download_file_from_sharepoint, list operations, site page operations

**Phase 3: OpenAI operations (~1 hour)**
- **V2CR-IP01B-IS-04**: `common_embed_functions_v2.py` - upload, vector store operations

**Phase 4: Step functions (~3 hours)**
- **V2CR-IP01B-IS-05**: `crawler.py` - step_download_source (including integrity check)
- **V2CR-IP01B-IS-06**: `crawler.py` - step_process_source
- **V2CR-IP01B-IS-07**: `crawler.py` - step_embed_source

**Phase 5: Router endpoints (~1.5 hours)**
- **V2CR-IP01B-IS-08**: `crawler.py` - orchestrator functions
- **V2CR-IP01B-IS-09**: `crawler.py` - endpoints (/crawl, /download_data, /process_data, /embed_data)
- **V2CR-IP01B-IS-10**: `crawler.py` - UI generation

**Phase 6: Integration (~1 hour)**
- **V2CR-IP01B-IS-11**: Register router in app.py
- **V2CR-IP01B-IS-12**: Integration testing

## 10. Verification Findings

### Field Name Inconsistencies

**F1: `SharePointFile.id` vs `sharepoint_listitem_id`**
- Existing: `SharePointFile.id: str`
- Spec: expects `sharepoint_listitem_id: int`
- **Fix**: Rename and change type to `int`

**F2: `SharePointFile.unique_id` vs `sharepoint_unique_file_id`**
- Existing: `unique_id: str`
- Spec: expects `sharepoint_unique_file_id`
- **Fix**: Rename for consistency

**F3: Missing `file_type` in `SharePointFile`**
- Spec requires `file_type` column in sharepoint_map.csv
- **Fix**: Add `file_type: str` field, derive from filename extension

**F4: Missing `url` and `raw_url` in `SharePointFile`**
- Spec requires both URL-encoded and raw URLs
- **Fix**: Add fields, build from site_url + server_relative_url

### Config Usage Issues

**C1: Path helpers must use config constants**
- Plan uses hardcoded `"01_files"` etc.
- **Fix**: Use `CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOCUMENTS_FOLDER` etc.

### Missing Plan Elements

**M1: Crawl Report archive not covered**
- Spec: `/crawl` creates archive after completion
- **Fix**: Add archive step to `crawl_domain()` orchestrator

**M2: `dry_run` implementation**
- Uses temp map filenames: `sharepoint_map_[JOB_ID].csv` (same folder)
- Temp files used throughout chain, deleted at end
- Mutations (downloads, uploads, deletes, moves) skipped
- See Section 5 "dry_run Implementation Pattern" for full chain flow

**M3: Missing precondition checks**
- Process: requires file in `01_originals/` on disk
- Embed: requires file in `02_embedded/` on disk
- **Fix**: Add precondition validation to step functions

### Corner Case Decisions

**CORNER-01: Empty domain (no sources configured)**
- When `file_sources`, `list_sources`, `sitepage_sources` are all empty
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

### Error Handling Protocol

**SharePoint connection failure:**
- Log error with site URL
- Skip entire source
- Continue with next source
- Set `sharepoint_error` on all items from that source

**File download failure:**
- Log error with filename and error message
- Set `sharepoint_error` in files_map row
- Skip item, continue with next item
- Integrity check will detect and retry on next crawl

**OpenAI upload failure:**
- Log error with filename
- Set `embedding_error` in vectorstore_map row
- Move file to `03_failed/`
- Continue with next file

**OpenAI rate limit (429):**
- Handled by `retry_batches` parameter (not exponential backoff in async streaming)
- Batch 1: Process all items, collect failures
- Batch 2+: Retry failed items from previous batch
- After all batches: set `embedding_error` on remaining failures

### Clarifications Needed

**A1: Download target varies by source type**
- `file_sources` -> `02_embedded/` directly
- `list_sources`, `sitepage_sources` -> `01_originals/`
- **Implementation**: Branch in `step_download_source()` based on source_type

**A2: Embed uses 2-field comparison, not 4-field**
- Download change detection: `filename`, `server_relative_url`, `file_size`, `last_modified_utc`
- Embed change detection: `file_size`, `last_modified_utc` only
- **Fix**: Add `is_file_changed_for_embed()` function

**A3: Async/sync mixing**
- SharePoint library is sync-only
- OpenAI SDK has async API
- **Fix**: Run SharePoint calls in `asyncio.to_thread()` if needed

### Existing Code Analysis

**common_sharepoint_functions_v2.py (254 lines):**
- `SharePointFile` dataclass: needs field renames (see F1-F4 above)
- Certificate handling: complete
- Document library listing: complete with pagination
- Missing: file download, list operations, site page operations

**common_crawler_functions_v2.py (262 lines):**
- Source dataclasses: complete (FileSource, SitePageSource, ListSource)
- DomainConfig: complete
- Domain CRUD: complete
- Missing: path helpers, files_metadata helpers

**common_job_functions_v2.py (532 lines):**
- StreamingJobWriter: complete, can be reused as-is
- Job control/monitoring: complete

**common_logging_functions_v2.py (176 lines):**
- MiddlewareLogger: complete, integrates with StreamingJobWriter

**hardcoded_config.py (58 lines):**
- All path constants present
- Legacy constants exist (SHAREPOINT_ERROR_MAP_CSV, FILE_FAILED_MAP_CSV) - ignore for V2

### Config Constants Usage

All implementations MUST use `CRAWLER_HARDCODED_CONFIG` constants instead of hardcoded strings:

**Folder paths:**
- `PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER` = `"domains"` - domain config location
- `PERSISTENT_STORAGE_PATH_CRAWLER_SUBFOLDER` = `"crawler"` - crawler cache location
- `PERSISTENT_STORAGE_PATH_JOBS_SUBFOLDER` = `"jobs"` - job files location
- `PERSISTENT_STORAGE_PATH_DOCUMENTS_FOLDER` = `"01_files"` - file_sources subfolder
- `PERSISTENT_STORAGE_PATH_LISTS_FOLDER` = `"02_lists"` - list_sources subfolder
- `PERSISTENT_STORAGE_PATH_SITEPAGES_FOLDER` = `"03_sitepages"` - sitepage_sources subfolder
- `PERSISTENT_STORAGE_PATH_ORIGINALS_SUBFOLDER` = `"01_originals"` - original downloads
- `PERSISTENT_STORAGE_PATH_EMBEDDED_SUBFOLDER` = `"02_embedded"` - processed/embeddable files
- `PERSISTENT_STORAGE_PATH_FAILED_SUBFOLDER` = `"03_failed"` - failed files

**File names:**
- `DOMAIN_JSON` = `"domain.json"` - domain configuration file
- `FILES_METADATA_JSON` = `"files_metadata.json"` - embedded file metadata
- `SHAREPOINT_MAP_CSV` = `"sharepoint_map.csv"` - SharePoint state cache
- `FILE_MAP_CSV` = `"files_map.csv"` - local file state cache
- `VECTOR_STORE_MAP_CSV` = `"vectorstore_map.csv"` - vector store state cache

**Settings:**
- `APPEND_TO_MAP_FILES_EVERY_X_LINES` = `10` - MapFileWriter buffer size
- `DEFAULT_FILETYPES_ACCEPTED_BY_VECTOR_STORES` - file type filter for embed step

**Usage examples:**
```python
# Path building
source_folder = os.path.join(storage_path, 
  CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_CRAWLER_SUBFOLDER,
  domain_id,
  CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOCUMENTS_FOLDER,
  source_id)

# Map file paths
sp_map_path = os.path.join(source_folder, CRAWLER_HARDCODED_CONFIG.SHAREPOINT_MAP_CSV)
files_map_path = os.path.join(source_folder, CRAWLER_HARDCODED_CONFIG.FILE_MAP_CSV)
vs_map_path = os.path.join(source_folder, CRAWLER_HARDCODED_CONFIG.VECTOR_STORE_MAP_CSV)

# MapFileWriter buffer size
writer = MapFileWriter(filepath, row_class, 
  buffer_size=CRAWLER_HARDCODED_CONFIG.APPEND_TO_MAP_FILES_EVERY_X_LINES)

# File type filtering
if file_type not in CRAWLER_HARDCODED_CONFIG.DEFAULT_FILETYPES_ACCEPTED_BY_VECTOR_STORES:
  logger.log_function_output(f"Skipping unsupported file type: {file_type}")
```

### Dependencies

- Office365-REST-Python-Client: already in requirements.txt
- OpenAI SDK: already configured in app.py

## 11. Detailed Changes/Additions Plan

### common_map_file_functions_v2.py (NEW - ~250 lines)

```
Lines 1-10: Imports
Lines 11-50: SharePointMapRow, FilesMapRow, VectorStoreMapRow dataclasses
Lines 51-60: ChangeDetectionResult dataclass
Lines 61-130: MapFileWriter class
Lines 131-160: read_sharepoint_map, read_files_map, read_vectorstore_map
Lines 161-200: detect_changes function
Lines 201-220: is_file_changed function
Lines 221-250: Helper functions (CSV parsing, row conversion)
```

### common_embed_functions_v2.py (NEW - ~200 lines)

```
Lines 1-10: Imports
Lines 11-50: upload_file_to_openai (with retry logic)
Lines 51-80: delete_file_from_openai
Lines 81-110: add_file_to_vector_store, remove_file_from_vector_store
Lines 111-140: list_vector_store_files
Lines 141-180: wait_for_vector_store_ready
Lines 181-200: get_failed_embeddings
```

### common_sharepoint_functions_v2.py (EXTEND - +100 lines)

```
Lines 255-290: download_file_from_sharepoint
Lines 291-320: get_list_items
Lines 321-340: export_list_to_csv
Lines 341-360: get_site_pages (reuses get_document_library_files pattern)
Lines 361-380: download_site_page_html
```

### common_crawler_functions_v2.py (EXTEND - +90 lines)

```
Lines 263-290: Path helper functions (get_source_folder_path, etc.)
Lines 291-310: server_relative_url_to_local_path, get_file_relative_path
Lines 311-330: STANDARD_METADATA_FIELDS, load_files_metadata, save_files_metadata
Lines 331-350: update_files_metadata, carry_over_custom_properties
```

### crawler.py (NEW - ~500 lines)

```
Lines 1-30: Imports, module constants
Lines 31-70: Result dataclasses (DownloadResult, ProcessResult, EmbedResult, IntegrityResult)
Lines 71-150: step_download_source (async generator)
Lines 151-200: step_integrity_check (async generator)
Lines 201-250: step_process_source (async generator)
Lines 251-320: step_embed_source (async generator)
Lines 321-370: crawl_domain orchestrator
Lines 371-400: download_domain_data, process_domain_data, embed_domain_data orchestrators
Lines 401-450: Router endpoints (/crawler root, /crawl, /download_data, /process_data, /embed_data)
Lines 451-500: UI generation (_generate_crawler_ui_page, get_router_specific_js)
```

### app.py (MODIFY - +10 lines)

```
Add import: from routers_v2 import crawler
Add router registration in create_app():
  app.include_router(crawler.router, tags=["Crawler V2"], prefix=v2_router_prefix)
  crawler.set_config(config, v2_router_prefix)
Add link in root() available links section
```

## 12. Code Generator Verification Checklist

Systematic verification that all plan items are implemented. Check each item exists in code with correct signature.

### A. common_map_file_functions_v2.py (NEW)

**Dataclasses:**
- [ ] **V2CR-IP01B-VC-01**: `SharePointMapRow` with 10 fields: sharepoint_listitem_id, sharepoint_unique_file_id, filename, file_type, file_size, url, raw_url, server_relative_url, last_modified_utc, last_modified_timestamp
- [ ] **V2CR-IP01B-VC-02**: `FilesMapRow` with 13 fields: sharepoint_listitem_id, sharepoint_unique_file_id, filename, file_type, server_relative_url, file_relative_path, file_size, last_modified_utc, last_modified_timestamp, downloaded_utc, downloaded_timestamp, sharepoint_error, processing_error
- [ ] **V2CR-IP01B-VC-03**: `VectorStoreMapRow` with 19 fields: openai_file_id, vector_store_id, file_relative_path, sharepoint_listitem_id, sharepoint_unique_file_id, filename, file_type, file_size, last_modified_utc, last_modified_timestamp, downloaded_utc, downloaded_timestamp, uploaded_utc, uploaded_timestamp, embedded_utc, embedded_timestamp, sharepoint_error, processing_error, embedding_error
- [ ] **V2CR-IP01B-VC-04**: `ChangeDetectionResult` with 4 fields: added, removed, changed, unchanged

**Classes:**
- [ ] **V2CR-IP01B-VC-05**: `MapFileWriter.__init__(filepath, row_class, buffer_size)`
- [ ] **V2CR-IP01B-VC-06**: `MapFileWriter.write_header()` with atomic temp+rename
- [ ] **V2CR-IP01B-VC-07**: `MapFileWriter.append_row(row)` with buffering
- [ ] **V2CR-IP01B-VC-08**: `MapFileWriter.flush()`
- [ ] **V2CR-IP01B-VC-09**: `MapFileWriter.finalize()`

**Functions:**
- [ ] **V2CR-IP01B-VC-10**: `read_sharepoint_map(filepath) -> list[SharePointMapRow]`
- [ ] **V2CR-IP01B-VC-11**: `read_files_map(filepath) -> list[FilesMapRow]`
- [ ] **V2CR-IP01B-VC-12**: `read_vectorstore_map(filepath) -> list[VectorStoreMapRow]`
- [ ] **V2CR-IP01B-VC-13**: `detect_changes(sharepoint_items, local_items) -> ChangeDetectionResult`
- [ ] **V2CR-IP01B-VC-14**: `is_file_changed(sp, local) -> bool` compares 4 fields
- [ ] **V2CR-IP01B-VC-15**: `is_file_changed_for_embed(files_row, vs_row) -> bool` compares 2 fields

### B. common_embed_functions_v2.py (NEW)

**Functions:**
- [ ] **V2CR-IP01B-VC-16**: `async upload_file_to_openai(client, filepath, purpose) -> tuple[str, str]`
- [ ] **V2CR-IP01B-VC-17**: `async delete_file_from_openai(client, file_id) -> tuple[bool, str]`
- [ ] **V2CR-IP01B-VC-18**: `async add_file_to_vector_store(client, vector_store_id, file_id) -> tuple[bool, str]`
- [ ] **V2CR-IP01B-VC-19**: `async remove_file_from_vector_store(client, vector_store_id, file_id) -> tuple[bool, str]`
- [ ] **V2CR-IP01B-VC-20**: `async list_vector_store_files(client, vector_store_id) -> list[dict]`
- [ ] **V2CR-IP01B-VC-21**: `async wait_for_vector_store_ready(client, vector_store_id, file_ids, timeout_seconds) -> list[dict]`
- [ ] **V2CR-IP01B-VC-22**: `async get_failed_embeddings(client, vector_store_id, file_ids) -> list[dict]`

### C. common_sharepoint_functions_v2.py (EXTEND)

**Modify existing:**
- [ ] **V2CR-IP01B-VC-23**: `SharePointFile` renamed fields: id->sharepoint_listitem_id (int), unique_id->sharepoint_unique_file_id
- [ ] **V2CR-IP01B-VC-24**: `SharePointFile` new fields: file_type, url, raw_url
- [ ] **V2CR-IP01B-VC-25**: `get_document_library_files()` populates new SharePointFile fields

**Add functions:**
- [ ] **V2CR-IP01B-VC-26**: `download_file_from_sharepoint(ctx, server_relative_url, target_path, preserve_timestamp, last_modified_timestamp) -> tuple[bool, str]`
- [ ] **V2CR-IP01B-VC-27**: `get_list_items(ctx, list_name, filter, logger) -> list[dict]`
- [ ] **V2CR-IP01B-VC-28**: `export_list_to_csv(ctx, list_name, filter, target_path, logger) -> tuple[bool, str]`
- [ ] **V2CR-IP01B-VC-29**: `get_site_pages(ctx, pages_url_part, filter, logger) -> list[SharePointFile]`
- [ ] **V2CR-IP01B-VC-30**: `download_site_page_html(ctx, server_relative_url, target_path, logger) -> tuple[bool, str]`

### D. common_crawler_functions_v2.py (EXTEND)

**Add constants:**
- [ ] **V2CR-IP01B-VC-31**: `SOURCE_TYPE_FOLDERS` dict mapping source_type to folder constants

**Add path helpers:**
- [ ] **V2CR-IP01B-VC-32**: `get_source_folder_path(storage_path, domain_id, source_type, source_id) -> str`
- [ ] **V2CR-IP01B-VC-33**: `get_embedded_folder_path(storage_path, domain_id, source_type, source_id) -> str`
- [ ] **V2CR-IP01B-VC-34**: `get_failed_folder_path(storage_path, domain_id, source_type, source_id) -> str`
- [ ] **V2CR-IP01B-VC-35**: `get_originals_folder_path(storage_path, domain_id, source_type, source_id) -> str`
- [ ] **V2CR-IP01B-VC-36**: `server_relative_url_to_local_path(server_relative_url, sharepoint_url_part) -> str`
- [ ] **V2CR-IP01B-VC-37**: `get_file_relative_path(domain_id, source_type, source_id, subfolder, local_path) -> str`

**Add files_metadata helpers:**
- [ ] **V2CR-IP01B-VC-38**: `STANDARD_METADATA_FIELDS` set with 14 field names
- [ ] **V2CR-IP01B-VC-39**: `load_files_metadata(domain_path) -> list[dict]`
- [ ] **V2CR-IP01B-VC-40**: `save_files_metadata(domain_path, metadata)` with temp+rename
- [ ] **V2CR-IP01B-VC-41**: `update_files_metadata(domain_path, new_entries)`
- [ ] **V2CR-IP01B-VC-42**: `carry_over_custom_properties(new_entry, existing_entries) -> dict`

**Add source filtering:**
- [ ] **V2CR-IP01B-VC-43**: `get_sources_for_scope(domain, scope, source_id) -> list[tuple[str, Source]]`

**Add dry_run helpers:**
- [ ] **V2CR-IP01B-VC-44**: `get_map_filename(base_name, job_id) -> str`
- [ ] **V2CR-IP01B-VC-45**: `cleanup_temp_map_files(source_folder, job_id)`

**Add file type filtering:**
- [ ] **V2CR-IP01B-VC-46**: `is_file_embeddable(filename) -> bool`
- [ ] **V2CR-IP01B-VC-47**: `filter_embeddable_files(files) -> tuple[list, list]`

### E. crawler.py (NEW)

**Module constants:**
- [ ] **V2CR-IP01B-VC-48**: `router = APIRouter()`
- [ ] **V2CR-IP01B-VC-49**: `config = None`
- [ ] **V2CR-IP01B-VC-50**: `router_prefix = None`
- [ ] **V2CR-IP01B-VC-51**: `router_name = "crawler"`
- [ ] **V2CR-IP01B-VC-52**: `main_page_nav_html` string

**Result dataclasses:**
- [ ] **V2CR-IP01B-VC-53**: `DownloadResult` with 7 fields: source_id, source_type, total_files, downloaded, skipped, errors, removed
- [ ] **V2CR-IP01B-VC-54**: `ProcessResult` with 6 fields: source_id, source_type, total_files, processed, skipped, errors
- [ ] **V2CR-IP01B-VC-55**: `EmbedResult` with 7 fields: source_id, source_type, total_files, uploaded, embedded, failed, removed
- [ ] **V2CR-IP01B-VC-56**: `IntegrityResult` with 5 fields: source_id, files_verified, missing_redownloaded, orphans_deleted, wrong_path_moved

**Step functions (async generators):**
- [ ] **V2CR-IP01B-VC-57**: `step_download_source(storage_path, domain, source, source_type, mode, dry_run, retry_batches, writer, logger, crawler_config)`
- [ ] **V2CR-IP01B-VC-58**: `step_integrity_check(storage_path, domain_id, source, source_type, dry_run, writer, logger, crawler_config)`
- [ ] **V2CR-IP01B-VC-59**: `step_process_source(storage_path, domain_id, source, source_type, dry_run, writer, logger)`
- [ ] **V2CR-IP01B-VC-60**: `step_embed_source(storage_path, domain, source, source_type, mode, dry_run, retry_batches, writer, logger, openai_client)`

**Orchestrator functions:**
- [ ] **V2CR-IP01B-VC-61**: `async crawl_domain(storage_path, domain, mode, scope, source_id, dry_run, writer, logger, crawler_config, openai_client) -> dict`
- [ ] **V2CR-IP01B-VC-62**: `async download_domain_data(storage_path, domain, mode, scope, source_id, dry_run, writer, logger, crawler_config) -> dict`
- [ ] **V2CR-IP01B-VC-63**: `async process_domain_data(storage_path, domain, scope, source_id, writer, logger) -> dict`
- [ ] **V2CR-IP01B-VC-64**: `async embed_domain_data(storage_path, domain, mode, scope, source_id, dry_run, writer, logger, openai_client) -> dict`
- [ ] **V2CR-IP01B-VC-65**: `create_crawl_report(storage_path, domain_id, mode, scope, results, started_utc, finished_utc) -> str`

**Endpoints:**
- [ ] **V2CR-IP01B-VC-66**: `GET /v2/crawler` returns router docs or jobs list
- [ ] **V2CR-IP01B-VC-67**: `GET /v2/crawler/crawl` with params: domain_id, mode, scope, source_id, format, dry_run, retry_batches
- [ ] **V2CR-IP01B-VC-68**: `GET /v2/crawler/download_data` with same params
- [ ] **V2CR-IP01B-VC-69**: `GET /v2/crawler/process_data` with params: domain_id, scope, source_id, format
- [ ] **V2CR-IP01B-VC-70**: `GET /v2/crawler/embed_data` with same params as /crawl
- [ ] **V2CR-IP01B-VC-71**: `GET /v2/crawler/cleanup_metadata` with params: domain_id, format

**UI generation:**
- [ ] **V2CR-IP01B-VC-72**: `_generate_crawler_ui_page(jobs) -> str`
- [ ] **V2CR-IP01B-VC-73**: `set_config(app_config, prefix)` function

### F. app.py (MODIFY)

- [ ] **V2CR-IP01B-VC-74**: Import: `from routers_v2 import crawler`
- [ ] **V2CR-IP01B-VC-75**: Router registration: `app.include_router(crawler.router, ...)`
- [ ] **V2CR-IP01B-VC-76**: Config setup: `crawler.set_config(config, v2_router_prefix)`
- [ ] **V2CR-IP01B-VC-77**: Root page link to /v2/crawler

### G. dry_run Implementation

- [ ] **V2CR-IP01B-VC-78**: All step functions accept `dry_run: bool` parameter
- [ ] **V2CR-IP01B-VC-79**: Temp map filenames use `_[job_id]` suffix when dry_run=true
- [ ] **V2CR-IP01B-VC-80**: 12 mutation points guarded with `if not dry_run:`
- [ ] **V2CR-IP01B-VC-81**: `cleanup_temp_map_files()` called in finally block

### H. Job Metadata

- [ ] **V2CR-IP01B-VC-82**: Job files include metadata: domain_id, vector_store_id, mode, scope, source_id, dry_run, retry_batches

### I. Spec Requirements Traceability (_V2_SPEC_CRAWLER.md)

**Functional Requirements:**
- [ ] **V2CR-IP01B-VC-83**: V2CR-FR-01 - Change detection uses `sharepoint_unique_file_id` as primary key
- [ ] **V2CR-IP01B-VC-84**: V2CR-FR-02 - `is_file_changed()` compares 4 fields: filename, server_relative_url, file_size, last_modified_utc
- [ ] **V2CR-IP01B-VC-85**: V2CR-FR-03 - `step_integrity_check()` runs after every `step_download_source()`
- [ ] **V2CR-IP01B-VC-86**: V2CR-FR-04 - Integrity check re-downloads missing, deletes orphans, moves wrong-path
- [ ] **V2CR-IP01B-VC-87**: V2CR-FR-05 - `MapFileWriter` uses buffered appends, atomic header write, retry on concurrency
- [ ] **V2CR-IP01B-VC-88**: V2CR-FR-06 - `carry_over_custom_properties()` preserves non-standard fields on file update

**Implementation Guarantees:**
- [ ] **V2CR-IP01B-VC-89**: V2CR-IG-01 - Local storage mirrors SharePoint folder structure after download + integrity check
- [ ] **V2CR-IP01B-VC-90**: V2CR-IG-02 - No orphan files remain after integrity check
- [ ] **V2CR-IP01B-VC-91**: V2CR-IG-03 - `files_map.csv` accurately reflects disk state after integrity check
- [ ] **V2CR-IP01B-VC-92**: V2CR-IG-04 - Custom properties in `files_metadata.json` survive file updates
- [ ] **V2CR-IP01B-VC-93**: V2CR-IG-05 - All 37 edge cases handled (EC-01 to EC-37)
- [ ] **V2CR-IP01B-VC-94**: V2CR-IG-06 - All paths use `CRAWLER_HARDCODED_CONFIG` constants (no hardcoded strings)

**Design Decisions:**
- [ ] **V2CR-IP01B-VC-95**: V2CR-DD-01 - `sharepoint_unique_file_id` used as immutable key throughout
- [ ] **V2CR-IP01B-VC-96**: V2CR-DD-02 - Four-field change detection implemented
- [ ] **V2CR-IP01B-VC-97**: V2CR-DD-03 - Integrity check always runs (no optional skip)
- [ ] **V2CR-IP01B-VC-98**: V2CR-DD-04 - WRONG_PATH files moved (not re-downloaded)
- [ ] **V2CR-IP01B-VC-99**: V2CR-DD-05 - `files_metadata.json` keyed by `openai_file_id`

### J. Map File Columns (_V2_SPEC_CRAWLER.md lines 275-333)

**sharepoint_map.csv (10 columns):**
- [ ] **V2CR-IP01B-VC-100**: sharepoint_listitem_id, sharepoint_unique_file_id, filename, file_type, file_size
- [ ] **V2CR-IP01B-VC-101**: url, raw_url, server_relative_url, last_modified_utc, last_modified_timestamp

**files_map.csv (13 columns):**
- [ ] **V2CR-IP01B-VC-102**: sharepoint_listitem_id, sharepoint_unique_file_id, filename, file_type, server_relative_url
- [ ] **V2CR-IP01B-VC-103**: file_relative_path, file_size, last_modified_utc, last_modified_timestamp
- [ ] **V2CR-IP01B-VC-104**: downloaded_utc, downloaded_timestamp, sharepoint_error, processing_error

**vectorstore_map.csv (19 columns):**
- [ ] **V2CR-IP01B-VC-105**: openai_file_id, vector_store_id, file_relative_path
- [ ] **V2CR-IP01B-VC-106**: sharepoint_listitem_id, sharepoint_unique_file_id, filename, file_type, file_size
- [ ] **V2CR-IP01B-VC-107**: last_modified_utc, last_modified_timestamp, downloaded_utc, downloaded_timestamp
- [ ] **V2CR-IP01B-VC-108**: uploaded_utc, uploaded_timestamp, embedded_utc, embedded_timestamp
- [ ] **V2CR-IP01B-VC-109**: sharepoint_error, processing_error, embedding_error

### K. UI Specification (_V2_SPEC_CRAWLER_UI.md)

**Table Columns (8 columns):**
- [ ] **V2CR-IP01B-VC-110**: ID, Action, Domain ID, Vector Store ID, Mode, Scope, Source ID, Actions

**Action Buttons by State:**
- [ ] **V2CR-IP01B-VC-111**: running: [Monitor] [Pause] [Cancel]
- [ ] **V2CR-IP01B-VC-112**: paused: [Monitor] [Resume] [Cancel]
- [ ] **V2CR-IP01B-VC-113**: done/cancelled/error: [Monitor] only

**Navigation Links:**
- [ ] **V2CR-IP01B-VC-114**: Back to Main Page -> `/`
- [ ] **V2CR-IP01B-VC-115**: Domains -> `/v2/domains?format=ui`
- [ ] **V2CR-IP01B-VC-116**: Crawl Results -> `/v2/crawl-results?format=ui`

**Console Panel:**
- [ ] **V2CR-IP01B-VC-117**: Visible by default
- [ ] **V2CR-IP01B-VC-118**: Resizable via drag handle
- [ ] **V2CR-IP01B-VC-119**: [Clear] button clears content
- [ ] **V2CR-IP01B-VC-120**: SSE streaming for live output
- [ ] **V2CR-IP01B-VC-121**: Auto-scroll to bottom

**Job Filtering:**
- [ ] **V2CR-IP01B-VC-122**: Only jobs where `router == 'crawler'` displayed

**Router-Specific JavaScript:**
- [ ] **V2CR-IP01B-VC-123**: `refreshJobsTable()` fetches and re-renders jobs
- [ ] **V2CR-IP01B-VC-124**: `monitorJob(jobId)` connects SSE to console
- [ ] **V2CR-IP01B-VC-125**: `controlJob(jobId, action)` calls pause/resume/cancel endpoint

## Spec Changes

**[2024-12-30 10:45]**
- Added: Plan ID V2CR-IP01B to header block
- Changed: Edge Cases now use IDs V2CR-IP01B-EC-01 to EC-37 (37 items)
- Changed: Implementation Order now uses IDs V2CR-IP01B-IS-01 to IS-12 (12 items)
- Changed: Verification Checklist now uses IDs V2CR-IP01B-VC-01 to VC-125 (125 items)
- Changed: Section I references now link VC IDs to spec requirement IDs (e.g., VC-83 traces to V2CR-FR-01)

**[2024-12-27 18:25]**
- Added: Section I - Spec Requirements Traceability (17 items: V2CR-FR-01 to FR-06, V2CR-IG-01 to IG-06, V2CR-DD-01 to DD-05)
- Added: Section J - Map File Columns verification (3 CSV files, 42 total columns)
- Added: Section K - UI Specification verification (15 items from _V2_SPEC_CRAWLER_UI.md)

**[2024-12-27 18:22]**
- Changed: Replaced manual test checklist with Code Generator Verification Checklist
- Added: 71 verification items organized by target file (A-H sections)
- Added: Field counts for all dataclasses for exact verification

**[2024-12-27 18:17]**
- Changed: Converted tables to lists per implementation-specification-rules.md (Query Params, Requirements Coverage, Edge Cases A-E, Mutation Points)
- Changed: Fixed hierarchy indenting to use └─ in dry_run chain flow
- Added: "Does not depend on" section
- Changed: Section titles "Matrix" -> removed (7. Spec Requirements Coverage, 8. Edge Case Handling)

**[2024-12-27 18:13]**
- Restored temp file naming for dry_run: `sharepoint_map_[JOB_ID].csv`
- Added complete chain flow documentation for dry_run mode
- Temp files used by all steps, deleted in finally block

**[2024-12-27 18:08]**
- Added dry_run Implementation Pattern section with mutation points table
- Added `dry_run` parameter to `step_integrity_check()` and `step_process_source()`

**[2024-12-27 18:03]**
- Added Corner Case Decisions (CORNER-01 to CORNER-06)
- Added Error Handling Protocol (SharePoint connection, download, OpenAI failures)
- Added `get_sources_for_scope()` function to common_crawler_functions_v2.py
- Added file type filtering functions: `is_file_embeddable()`, `filter_embeddable_files()`
- Added Job metadata specification with all crawler-specific fields

**[2024-12-27 18:00]**
- Added `create_crawl_report()` function to orchestrator section (per spec line 89-102)
- Added explicit log summary format to `step_integrity_check()` docstring (per spec line 612-614)
- Added Query Parameters table with explicit `mode=full` default (per spec line 898)
- Added `retry_batches` parameter to query parameters table
