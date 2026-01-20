# V0 Crawler Toolkit - Standalone SharePoint Crawler

**Goal**: Document the architecture and workflow of the standalone SharePoint-GPT-Crawler-Toolkit.

**Does not depend on:**
- Any V2 specifications (this is the predecessor toolkit)

## Overview

The V0 Crawler Toolkit is a standalone Python/PowerShell toolkit for crawling SharePoint content and uploading it to OpenAI vector stores. It operates as a set of sequential scripts that must be run manually in order.

**Key characteristics:**
- Manual execution of numbered scripts (01_, 02_, 03_, 04_)
- Local OneDrive sync as primary file source (no direct SharePoint API access for files)
- PowerShell scripts for SharePoint List extraction via PnP
- Centralized configuration in `crawler_settings.py`
- Supports both OpenAI and Azure OpenAI backends
- Windows long path support for deeply nested SharePoint folder structures

## Table of Contents

- Overview
- Scenario
- Architecture
  - Folder Structure (Persistent Storage)
  - Content Types per Domain
- Domain Objects
  - CrawlerSettings
  - SharePointDomain
  - SharepointContentSettings
  - FileTypeMapping
  - CrawledFile
  - CrawledFileMetadata
  - CrawledVectorStore
- Key Mechanisms
  - Windows Long Path Handling
  - URL Reconstruction from File Paths
  - File Sync with Delta Detection
- Pipeline Steps
  - Step 0: Extract SharePoint Lists (PowerShell)
  - Step 1: Copy New Files to Crawler Folder
  - Step 2: Convert HTML Files
  - Step 3: Create Vector Stores
  - Step 4: Replicate Vector Store Content
- OpenAI Backend Tools
  - Client Creation
  - File Operations
  - Vector Store Operations
  - Cleanup Utilities
  - Replication
  - Utility Functions
- Design Decisions
- Limitations
- Environment Variables
- Differences from V2 Middleware Crawler
- Spec Changes


## Scenario

**Real-world problem**: Organizations need to make SharePoint content searchable via RAG (Retrieval-Augmented Generation). SharePoint stores documents, lists, and site pages across multiple sites. This content needs to be extracted, cleaned, and uploaded to OpenAI vector stores with proper source URL metadata for citations.

**What we don't want:**
- Direct SharePoint API calls for file retrieval (uses OneDrive sync instead)
- Automatic scheduling (manual execution by design)
- Server deployment (local developer workstation only)
- Incremental vector store updates (full rebuild each run)
- Complex authentication flows (uses interactive login)
- Real-time sync (batch processing is sufficient)


## Architecture

### Folder Structure (Persistent Storage)

```
[LOCAL_PERSISTENT_STORAGE_PATH]/
├─ crawler/
│  └─ [DOMAIN_ID]/                    # e.g. HOIT5, VMS5, SMS5
│     ├─ 01_files/                    # Document library files
│     │  ├─ 01_originals/             # Raw files (unused for files - goes direct to embedded)
│     │  ├─ 02_embedded/              # Files ready for upload
│     │  └─ 03_failed/                # Files that failed processing
│     ├─ 02_lists/                    # SharePoint list exports
│     │  ├─ 01_originals/             # Raw CSV/MD exports
│     │  ├─ 02_embedded/              # Processed exports
│     │  └─ 03_failed/                # Failed exports
│     └─ 03_sitepages/                # SharePoint site pages
│        ├─ 01_originals/             # Raw HTML from browser save
│        ├─ 02_embedded/              # Cleaned/minified HTML
│        └─ 03_failed/                # Failed HTML files
└─ domains/
   └─ [DOMAIN_ID]/
      ├─ domain.json                  # Domain metadata with vector_store_id
      └─ files_metadata.json          # Uploaded file metadata with source URLs
```

### Content Types per Domain

Each SharePoint domain (site) has three content types:
- **files** (`01_files`): Documents from document libraries (synced via OneDrive)
- **lists** (`02_lists`): SharePoint list items exported as CSV/MD via PnP PowerShell
- **sitepages** (`03_sitepages`): SharePoint site pages saved as HTML via browser


## Domain Objects

### CrawlerSettings
```python
@dataclasses.dataclass
class CrawlerSettings:
  domains: List[SharePointDomain]                         # All configured SharePoint sites
  local_persistent_storage_path: str                      # Root path from env var LOCAL_PERSISTENT_STORAGE_PATH
  persistent_storage_path_domains_subfolder: str = "domains"
  persistent_storage_path_crawler_subfolder: str = "crawler"
  crawler_originals_subfolder: str = "01_originals"
  crawler_embedded_subfolder: str = "02_embedded"
  crawler_failed_subfolder: str = "03_failed"
```

### SharePointDomain
```python
@dataclasses.dataclass
class SharePointDomain:
  domain_id: str                                          # Unique identifier (e.g. "HOIT5")
  vector_store_name: str                                  # OpenAI vector store name (usually same as domain_id)
  name: str                                               # Human-readable name (e.g. "House of IT")
  description: str                                        # Domain description for RAG context
  site_url: str                                           # SharePoint site URL (e.g. "https://tenant.sharepoint.com/sites/HouseofIT")
  files_settings: SharepointContentSettings               # Settings for document library files
  lists_settings: SharepointContentSettings               # Settings for list exports
  sitepages_settings: SharepointContentSettings           # Settings for site pages
  vector_store_id: Optional[str] = None                   # Assigned after vector store creation
```

### SharepointContentSettings
```python
@dataclasses.dataclass
class SharepointContentSettings:
  crawler_subfolder: str                                  # Subfolder name (e.g. "01_files", "02_lists", "03_sitepages")
  sharepoint_url_part: str                                # URL path segment (e.g. "/Shared Documents", "/Lists", "/SitePages")
  file_type_mappings: List[FileTypeMapping]               # Extension conversions for URL reconstruction
  local_onedrive_path: Optional[str] = None               # Local OneDrive sync path (only for files_settings)
```

### FileTypeMapping
```python
@dataclasses.dataclass
class FileTypeMapping:
  original_file_type: str                                 # Original SharePoint extension (e.g. "aspx", "")
  embedded_file_type: str                                 # Processed file extension (e.g. "html", "md")
```

**Default mappings:**
- `DEFAULT_SHAREPOINT_FILES_FILE_TYPE_MAPPINGS = []` - no conversion for files
- `DEFAULT_SHAREPOINT_LISTS_FILE_TYPE_MAPPINGS = [FileTypeMapping("", "md")]` - lists become .md, original has no extension
- `DEFAULT_SHAREPOINT_SITEPAGES_FILE_TYPE_MAPPINGS = [FileTypeMapping("aspx", "html")]` - .aspx saved as .html

### CrawledFile
```python
@dataclasses.dataclass
class CrawledFile:
  file_id: str                                            # OpenAI file ID after upload (e.g. "file-abc123")
  embedded_file_path: str                                 # Full local path to processed file
  embedded_filename: str                                  # Filename only
  embedded_file_relative_path: str                        # Path relative to crawler/ folder
  embedded_file_last_modified_utc: str                    # ISO timestamp (e.g. "2025-01-27T12:34:56.789Z")
  file_metadata: CrawledFileMetadata                      # Metadata for vector store attributes
```

### CrawledFileMetadata
```python
@dataclasses.dataclass
class CrawledFileMetadata:
  source: str                                             # URL-encoded SharePoint URL for citations
  raw_url: str                                            # Unencoded SharePoint URL for display
  filename: str                                           # Original filename
  file_type: str                                          # File extension lowercase (e.g. "pdf", "docx")
  file_size: int                                          # Size in bytes
  last_modified: str                                      # Date in YYYY-MM-DD format
```

### CrawledVectorStore
```python
@dataclasses.dataclass
class CrawledVectorStore:
  vector_store: any                                       # OpenAI VectorStore object
  vector_store_id: str                                    # Vector store ID
  files: List[CrawledFile]                                # Successfully uploaded files
  failed_files: List[CrawledFile]                         # Files that failed upload/processing
```


## Key Mechanisms

### Windows Long Path Handling

**V0-DD-01**: Windows has a 260 character path limit (MAX_PATH). SharePoint folder structures with long names can exceed this. The toolkit uses the `\\?\` extended-length path prefix.

**Threshold**: Paths > 240 characters trigger long path handling (conservative margin).

```python
# Used in: 01_copy_new_files_to_crawler_folder.py, 02_convert_html_files.py, 03_create_vector_stores.py
def normalize_long_path(path):
  if os.name == 'nt' and not path.startswith('\\\\?\\'):
    abs_path = os.path.abspath(path)
    if len(abs_path) > 240:
      if abs_path.startswith('\\\\'):                     # UNC path (network share)
        return '\\\\?\\UNC\\' + abs_path[2:]
      else:                                               # Local path
        return '\\\\?\\' + abs_path
  return path

# Reverse operation for display/comparison
def strip_long_path_prefix(path):
  if path.startswith('\\\\?\\UNC\\'):
    return '\\\\' + path[8:]
  elif path.startswith('\\\\?\\'):
    return path[4:]
  return path
```

**Usage pattern**: All file operations use `normalize_long_path()` before calling `os.*` functions:
```python
long_path = normalize_long_path(file_path)
if os.path.exists(long_path):
  file_size = os.path.getsize(long_path)
  with open(long_path, 'r', encoding='utf-8') as f:
    content = f.read()
```

### URL Reconstruction from File Paths

**V0-DD-02**: Original SharePoint URLs are reconstructed from local file paths using domain configuration.

```python
def add_additional_file_metadata_to_crawled_file(crawled_file: CrawledFile, domain: SharePointDomain, settings: SharepointContentSettings):
  # 1. Calculate relative path from crawler folder
  base_path = os.path.join(CRAWLER_SETTINGS.local_persistent_storage_path, CRAWLER_SETTINGS.persistent_storage_path_crawler_subfolder)
  crawled_file.embedded_file_relative_path = os.path.relpath(strip_long_path_prefix(crawled_file.embedded_file_path), strip_long_path_prefix(base_path))
  
  # 2. Get path relative to embedded folder
  embedded_folder_path = os.path.join(base_path, domain.domain_id, settings.crawler_subfolder, CRAWLER_SETTINGS.crawler_embedded_subfolder)
  embedded_filename = os.path.relpath(crawled_file.embedded_file_path, embedded_folder_path)
  
  # 3. Apply file type mapping (reverse the extension change)
  original_filename = embedded_filename
  for mapping in settings.file_type_mappings:
    if mapping.embedded_file_type and crawled_file.file_metadata.file_type == mapping.embedded_file_type:
      if mapping.original_file_type:
        original_filename = os.path.splitext(embedded_filename)[0] + '.' + mapping.original_file_type
      else:
        original_filename = os.path.splitext(embedded_filename)[0]  # Remove extension entirely
  
  # 4. Construct SharePoint URL
  raw_url = f"{domain.site_url}{settings.sharepoint_url_part}/{original_filename}".replace("\\", "/")
  crawled_file.file_metadata.raw_url = raw_url
  crawled_file.file_metadata.source = url_encode_path_component(raw_url)
```

**URL encoding** (path segments only, not scheme/domain):
```python
def url_encode_path_component(url):
  if '://' not in url: return url
  scheme_and_domain, path = url.split('://', 1)
  if '/' not in path: return url
  domain, path_part = path.split('/', 1)
  segments = path_part.split('/')
  encoded_segments = [quote(segment, safe='') for segment in segments]
  return f"{scheme_and_domain}://{domain}/{'/'.join(encoded_segments)}"
```

### File Sync with Delta Detection

**V0-DD-03**: Step 1 compares source and target by relative path and modification time.

```python
def copy_new_files_to_crawler_folder(source_path, target_path, file_types, newer_than_date, delete_files_not_in_source, delete_empty_target_folders, dry_run):
  # Collect files from both locations
  source_files = collect_files(source_path, file_types)   # Dict: relative_path -> {full_path, mtime}
  target_files = collect_files(target_path, file_types)
  
  # Categorize operations
  add_files = [(rel_path, info) for rel_path, info in source_files.items() if rel_path not in target_files]
  update_files = [(rel_path, info) for rel_path, info in source_files.items() 
                  if rel_path in target_files and info['mtime'] > target_files[rel_path]['mtime']]
  delete_files = [(rel_path, info) for rel_path, info in target_files.items() if rel_path not in source_files]
  
  # Filter by newer_than_date if specified
  if newer_than_date is not None:
    newer_than_timestamp = newer_than_date.timestamp()
    files_to_copy = [(p, i) for p, i in add_files + update_files if i['mtime'] > newer_than_timestamp]
  else:
    files_to_copy = add_files + update_files
  
  # Execute copy operations with long path support
  for rel_path, source_info in files_to_copy:
    source_file = source_info['full_path']
    target_file = os.path.join(target_path, rel_path)
    create_directory_recursive(os.path.dirname(target_file))
    shutil.copy2(normalize_long_path(source_file), normalize_long_path(target_file))
```

**Recursive directory creation** (handles long paths and edge cases):
```python
def create_directory_recursive(path):
  long_path = normalize_long_path(path)
  if os.path.exists(long_path): return True
  try:
    os.makedirs(long_path, exist_ok=True)
    return True
  except (FileNotFoundError, OSError):
    parent = os.path.dirname(path)
    if parent == path or not parent: raise
    if not create_directory_recursive(parent): return False
    try:
      os.mkdir(normalize_long_path(path))
      return True
    except (FileNotFoundError, OSError):
      return False
```


## Pipeline Steps

### Step 0: Extract SharePoint Lists (PowerShell)

**Script**: `01_extract_tables_powershell/ExportListItemsAsCSV.ps1`
**Purpose**: Export SharePoint list items to CSV and Markdown files.

**Task configuration** (hardcoded array):
```powershell
$tasks = @(
  @{ siteURL = "https://tenant.sharepoint.com/sites/HouseofIT"; listName = "SPoC BIO List"; outputSubFolder = "HOIT" }
  ,@{ siteURL = "https://tenant.sharepoint.com/sites/HouseofIT"; listName = "List of Acronyms"; outputSubFolder = "HOIT" }
  # ... more tasks
)
```

**Processing per task**:
1. Connect to SharePoint: `Connect-PnPOnline -Url $siteURL -Interactive`
2. Get list metadata: `Get-PnPList -Identity $listName`
3. Get field definitions: `Get-PnPField -List $listName | Where-Object { $_.Hidden -eq $false -and $_.AutoIndexed -eq $false }`
4. Fetch all items: `Get-PnPListItem -List $list -PageSize 4995 -Fields $fieldNames`
5. Export to CSV and MD

**Field filtering**:
```powershell
$fieldsToIgnore = @("Author","Created","Editor","Comment","Modified","_ColorTag","_CommentCount",
  "_ComplianceFlags","_ComplianceTag","_ComplianceTagUserId","_ComplianceTagWrittenTime",
  "_CopySource","_DisplayName","_dlc_DocId","_dlc_DocIdUrl","_IsRecord","_LikeCount",
  "_ModerationStatus","_UIVersionString","AppAuthor","AppEditor","Attachments","CheckoutUser",
  "ComplianceAssetId","ContentType","DocIcon","Edit","FileSizeDisplay","FolderChildCount",
  "ItemChildCount","LinkTitle","LinkFilename","LinkFilenameNoMenu","MediaServiceAutoTags",
  "MediaServiceLocation","MediaServiceOCR","ParentVersionString","SharedWithDetails","SharedWithUsers")
```

**Output format - CSV**:
```
ID,Title,Description,Category
1,"Item One","Description text","Category A"
2,"Item Two","Another description","Category B"
```

**Output format - Markdown**:
```markdown
## List Name

### "List Name" - Item One
**Title**: Item One
**Description**: Description text
**Category**: Category A

### "List Name" - Item Two
...
```


### Step 1: Copy New Files to Crawler Folder

**Script**: `src/01_copy_new_files_to_crawler_folder.py`
**Purpose**: Sync files from OneDrive local sync folder to crawler's embedded folder.

**Main function signature**:
```python
def copy_new_files_to_crawler_folder(
  source_path: str,                     # Local OneDrive sync path
  target_path: str,                     # Crawler embedded folder path
  file_types: List[str],                # Extensions to include (e.g. ["doc", "docx", "pdf"])
  newer_than_date: datetime.datetime,   # Only copy files modified after this date
  delete_files_not_in_source: bool,     # Remove target files not in source
  delete_empty_target_folders: bool,    # Clean up empty directories
  dry_run: bool                         # Preview mode - no actual changes
) -> None
```

**Default file types**: `["doc", "docx", "pptx", "pdf", "html", "md"]`

**Helper functions**:
```python
def normalize_long_path(path) -> str                      # Add \\?\ prefix for long paths
def create_directory_recursive(path) -> bool             # Create nested directories with long path support
def get_relative_path(base_path, full_path) -> str       # Calculate relative path, stripping long path prefix
def get_file_mtime(file_path) -> float                   # Get modification time with long path support
def matches_file_types(file_path, file_types) -> bool    # Check if file extension is in allowed list
def collect_files(base_path, file_types) -> dict         # Recursively collect files with mtime
def remove_empty_dirs(path) -> None                      # Remove empty directories recursively
```


### Step 2: Convert HTML Files

**Script**: `src/02_convert_html_files.py`
**Purpose**: Clean and compress SharePoint HTML files (site pages) for vector store ingestion.

**Main function signature**:
```python
def create_naked_html_files(
  input_path: str,                      # Path containing raw HTML files
  output_subdir: str,                   # Relative output subdirectory (e.g. "../02_embedded")
  preserve_file_timestamp: bool = False,# Copy mtime from input to output
  clean_output_folder: bool = False     # Delete existing output files first
) -> None
```

**SharePoint element removal constants**:
```python
REMOVE_SHAREPOINT_TAGS = ["nav", "button"]
REMOVE_SHAREPOINT_TAGS_EXCEPTION_SPAN_CLASSES_CONTAIN = ["Persona"]  # Keep if contains Persona spans
REMOVE_SHAREPOINT_DIV_IDS = ["O365_HeaderRightRegion", "spLeftNav", "sp-appBar", "spCommandBar", "SuiteNavWrapper", "root", "spSiteHeader"]
REMOVE_SHAREPOINT_DIV_CLASSES = ["ms-HorizontalNavItems-list"]
REMOVE_SHAREPOINT_IMG_SELECTORS = [".ms-Image", "img.fui-Avatar__image", "img.ms-Image-image--portrait"]
REMOVE_SHAREPOINT_UL_NAV_ITEMS = ['sharepoint start page', 'my sites', 'my news', 'my files', 'my lists', 'create']
REMOVE_SHAREPOINT_TEXTS = ["Hide header and navigation"]
REMOVE_UNCESSARY_TAGS = ["span"]
REMOVE_MULTIPLE_CONSECUTIVE_CLOSING_TAGS_LEAVE_JUST_ONE = ["p", "br"]
```

**SharePoint markup transformations**:
```python
REPLACE_SHAREPOINT_TAGS_WITH_TABLE_TAGS = ["cf-data-provider"]        # cf-data-provider -> table
REPLACE_SHAREPOINT_DIVS_WITH_ROLE_WITH_H1_TAGS = ["heading"]          # div[role=heading] -> h1
REPLACE_SHAREPOINT_DIVS_WITH_ROLE_WITH_TR_TAGS = ["row"]              # div[role=row] -> tr
REPLACE_SHAREPOINT_DIVS_WITH_ROLE_WITH_TD_TAGS = ["gridcell"]         # div[role=gridcell] -> td
REMOVE_SHAREPOINT_ULS_AND_H3_AFTER_H3_WITH_TEXT = ['Conversations']   # Remove h3 and following ul
```

**Regex patterns for CSS cleanup**:
```python
REMOVE_BACKGROUND_STYLE_RE = re.compile(r'background(?:-image)?\s*:\s*url\([^;]+\)(?:\s*[^;]+)?\s*;?', re.IGNORECASE)
REMOVE_FONT_FACE_BLOCK_RE = re.compile(r'@font-face\s*{[^}]*}', re.IGNORECASE | re.DOTALL)
REMOVE_ROOT_CSS_BLOCK_RE = re.compile(r':root\s*{[^}]*}', re.IGNORECASE | re.DOTALL)
REMOVE_FAVICON_DATA_URL_RE = re.compile(r'<link[^>]*href="data:image/x-icon;base64,[^"]+"[^>]*>', re.IGNORECASE)
```

**Processing functions**:
```python
def remove_unwanted_elements(soup) -> None                # Remove SharePoint chrome, nav, scripts, etc.
def remove_empty_tags(soup) -> None                       # Remove empty or single-char tags iteratively
def minify_html(html_string: str) -> str                  # Remove whitespace, collapse tags
def convert_embedded_images(soup, quality, max_size)      # Resize/compress base64 images
def remove_css_artifacts(soup) -> None                    # Strip background styles
def has_span_with_exception_classes(tag, classes) -> bool # Check for Persona spans
```

**Large file handling**: Files > 200KB after initial processing get additional `<p>` tag unwrapping.


### Step 3: Create Vector Stores

**Script**: `src/03_create_vector_stores.py`
**Purpose**: Upload processed files to OpenAI vector stores with metadata.

**File collection function**:
```python
def collect_files_from_folder_path(
  folder_path: str,
  include_subfolders: bool = True,
  include_file_types: List[str] = ["*"]
) -> List[CrawledFile]
```

**Vector store upload function**:
```python
def add_collected_files_to_vector_store(
  client,                               # OpenAI client
  vector_store,                         # Target vector store
  files: List[CrawledFile],
  log_headers: bool = True
) -> CrawledVectorStore
```

**Upload process per file**:
1. Upload to Files API: `client.files.create(file=f, purpose="assistants")`
2. Add to vector store with metadata:
   ```python
   client.vector_stores.files.create(
     vector_store_id=vector_store.id,
     file_id=file_id,
     attributes={
       'source': crawled_file.file_metadata.source,
       'raw_url': crawled_file.file_metadata.raw_url,
       'filename': crawled_file.file_metadata.filename,
       'file_type': crawled_file.file_metadata.file_type
     }
   )
   ```
3. Poll for completion status

**Retry logic**: Up to 3 retries for failed uploads with cleanup between attempts.

**Adaptive polling**: Wait times adjusted based on file count and type:
- < 11 files: 10 checks x 3 seconds
- 11-100 files: 15 checks x 10 seconds
- > 100 files: 20 checks x 20 seconds
- HTML files: Additional time based on count and total size

**Chunking strategy** (vector store creation):
```python
def create_vector_store(client, vector_store_name: str, chunk_size=4096, chunk_overlap=2048):
  chunking_strategy = {
    "type": "static",
    "static": {
      "max_chunk_size_tokens": chunk_size,
      "chunk_overlap_tokens": chunk_overlap
    }
  }
  return client.vector_stores.create(name=vector_store_name, chunking_strategy=chunking_strategy)
```

**Output files**:
```python
def write_domain_json(domain: SharePointDomain, output_file_path: str) -> None
# Output: {"domain_id": "HOIT5", "vector_store_name": "HOIT5", "vector_store_id": "vs_xxx", "name": "House of IT", "description": "..."}

def write_files_metadata_json(files: List[CrawledFile], output_file_path: str) -> None
# Output: [{"file_id": "file_xxx", "embedded_file_relative_path": "...", "file_metadata": {...}}, ...]
```


### Step 4: Replicate Vector Store Content

**Script**: `src/04_replicate_vector_store_content.py`
**Purpose**: Combine multiple domain vector stores into global vector stores.

**Main function** (from openai_backendtools.py):
```python
def replicate_vector_store_content(
  client,
  source_vector_store_ids: List[str],
  target_vector_store_ids: List[str],
  remove_target_files_not_in_sources: bool = False
) -> Tuple[List[List[Tuple]], List[List[str]], List[List[Tuple]]]
# Returns: (added_files, removed_files, errors) per target
```

**Replication logic**:
1. Collect all file IDs from source vector stores
2. For each target vector store:
   - Find files in sources not in target -> add references
   - Find files in target not in any source -> optionally remove
3. Files are **not copied**, only linked (same file ID used across stores)

**Cleanup before replication**:
```python
def delete_failed_vector_store_files(client, vector_store_id, dry_run=False, indent=0) -> List
# Removes files with status 'failed' or 'cancelled' from vector store and global storage
```


## OpenAI Backend Tools

**File**: `src/openai_backendtools.py`

### Client Creation

```python
def create_openai_client() -> openai.OpenAI
# Uses OPENAI_API_KEY env var

def create_azure_openai_client(use_key_authentication: bool = False) -> openai.AzureOpenAI
# use_key_authentication=True: Uses AZURE_OPENAI_API_KEY
# use_key_authentication=False: Uses DefaultAzureCredential (managed identity or service principal)
```

### File Operations

```python
def get_all_files(client) -> List[FileObject]             # Paginated listing, adds 'index' attribute
def delete_files(client, files: List) -> None             # Delete by file objects
def delete_file_ids(client, file_ids: List[str]) -> None  # Delete by IDs
def format_files_table(file_list, indent=0) -> str        # Console table output
def get_filelist_metrics(files) -> dict                   # Count by status
```

### Vector Store Operations

```python
def get_all_vector_stores(client) -> List                 # Paginated listing
def get_vector_store_by_name(client, name: str)           # Find by name
def get_vector_store_by_id(client, id: str)               # Find by ID
def get_vector_store_files(client, vector_store) -> List  # All files in store
def get_vector_store_files_with_filenames(client, vs)     # Files with global file attributes
def get_vector_store_file_ids_with_status(client, vs, status: str) -> List[str]
def get_vector_store_file_metrics(client, vs) -> dict     # {total, failed, cancelled, in_progress, completed}
def create_vector_store(client, name, chunk_size, chunk_overlap)
def delete_vector_store_by_name(client, name, delete_files=False)
def delete_vector_store_by_id(client, id, delete_files=False)
def format_vector_stores_table(client, vs_list) -> str    # Console table output
```

### Cleanup Utilities

```python
def delete_failed_vector_store_files(client, vs_id, dry_run=False, indent=0) -> List
def delete_vector_store_files_added_after_date(client, vs_id, date, dry_run=False)
def delete_files_in_all_vector_stores_by_filename(client, filenames, dry_run=False, delete_global=False) -> dict
def delete_files_in_vector_store_by_file_type(client, vs_id, file_types, dry_run=False, delete_global=False)
def delete_duplicate_files_in_vector_stores(client)       # Keep newest, delete older duplicates
def delete_failed_and_unused_files(client, dry_run=False) # Clean orphaned files
def delete_expired_vector_stores(client)                  # Remove expired stores
def delete_empty_vector_stores(client, dry_run=False)     # Remove stores with 0 bytes
def delete_vector_stores_not_used_by_assistants(client, until_date, dry_run=False)
```

### Replication

```python
def replicate_vector_store_content(client, source_ids, target_ids, remove_extra=False)
def print_vector_store_replication_summary(target_ids, added, removed, errors)
def find_files_in_all_vector_stores_by_filename(client, filenames, log_headers=True) -> dict
```

### Utility Functions

```python
def retry_on_openai_errors(fn, indentation=0, retries=5, backoff_seconds=10)  # Rate limit handling
def format_filesize(num_bytes) -> str                     # "1.23 MB"
def format_timestamp(ts) -> str                           # "2025-01-27 12:34:56"
def log_function_header(name) -> datetime                 # "[timestamp] START: name..."
def log_function_footer(name, start_time)                 # "[timestamp] END: name (duration)."
def truncate_string(string, max_length) -> str
def clean_response(string) -> str                         # Remove linebreaks, quotes
def remove_linebreaks(string) -> str
```


## Design Decisions

**V0-DD-01**: Windows long path support via `\\?\` prefix. Threshold 240 chars (conservative). Applied in all file I/O operations.

**V0-DD-02**: OneDrive sync as file source. Files are synced locally via OneDrive rather than fetched via SharePoint API. Simplifies authentication but requires manual sync.

**V0-DD-03**: Sequential manual scripts. No orchestration - each step must be run manually in order. Suitable for periodic batch updates.

**V0-DD-04**: PowerShell for lists only. PnP PowerShell used only for list export. Files come from OneDrive, sitepages from browser save.

**V0-DD-05**: Centralized domain configuration. All domains defined in `crawler_settings.py` with consistent structure.

**V0-DD-06**: URL reconstruction from file paths. Original SharePoint URLs are reconstructed by combining:
- `site_url` + `sharepoint_url_part` + relative file path
- File type mappings reverse extension changes (html -> aspx, md -> no extension)

**V0-DD-07**: Dual URL storage. Both encoded (`source`) and unencoded (`raw_url`) URLs stored in metadata. `source` for API/linking, `raw_url` for display.

**V0-DD-08**: Failed file isolation. Files that fail processing are moved to `03_failed/` subfolder, preserving relative path structure for debugging.

**V0-DD-09**: Static chunking strategy. 4096 token chunks with 2048 overlap. Balances context size with granularity.

**V0-DD-10**: File linking in replication. Global vector stores reference same file IDs as domain stores (no duplication in storage).


## Limitations

1. **No incremental vector store updates**: Cannot replace/update individual files. Must rebuild entire store.
2. **Manual sitepage capture**: HTML sitepages must be saved manually via browser "Save As".
3. **No scheduling**: Scripts must be triggered manually or via external scheduler (Task Scheduler, cron).
4. **Local execution only**: Designed for developer workstation, not server/cloud deployment.
5. **No permission handling**: Assumes user has access to all content. No permission-aware crawling.
6. **No delta detection for vector stores**: Re-uploads all files on each run (compares local files only).
7. **Hardcoded list configuration**: List export tasks hardcoded in PowerShell script, not in central config.


## Environment Variables

```
# OpenAI Configuration
OPENAI_API_KEY                        # API key for standard OpenAI
OPENAI_SERVICE_TYPE                   # "openai" or "azure_openai"

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT                 # Azure OpenAI endpoint URL
AZURE_OPENAI_API_VERSION              # API version (e.g. "2024-02-15-preview")
AZURE_OPENAI_API_KEY                  # API key (if using key auth)
AZURE_OPENAI_USE_KEY_AUTHENTICATION   # "true" or "false"
AZURE_OPENAI_USE_MANAGED_IDENTITY     # "true" or "false"
AZURE_MANAGED_IDENTITY_CLIENT_ID      # Client ID for managed identity

# Storage Configuration
LOCAL_PERSISTENT_STORAGE_PATH         # Root path for crawler data (e.g. "c:\Dev\RAGFiles")
```


## Differences from V2 Middleware Crawler

| Aspect | V0 Toolkit | V2 Middleware |
|--------|-----------|---------------|
| Execution | Manual scripts | HTTP API endpoints |
| File source | OneDrive sync | Direct SharePoint Graph API |
| List extraction | PnP PowerShell | Graph API |
| Sitepage capture | Manual browser save | Graph API with HTML conversion |
| Authentication | Interactive (user login) | Service principal (app-only) |
| Scheduling | External (Task Scheduler) | Built-in streaming jobs |
| Deployment | Local workstation only | Azure App Service |
| Vector store updates | Full rebuild | Incremental add/remove |
| Long path handling | `\\?\` prefix | Same approach |
| Configuration | Python dataclasses | JSON + environment variables |


## Spec Changes

- **2025-12-19**: Initial spec created from analysis of SharePoint-GPT-Crawler-Toolkit source code
