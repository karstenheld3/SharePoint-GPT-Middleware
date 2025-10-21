# Persistent Storage Structure Documentation

This document describes the folder structure and file organization used by the SharePoint-GPT-Middleware application for persistent storage.

## Overview

The application uses a persistent storage path (configured via `PERSISTENT_STORAGE_PATH` environment variable) to store domains, crawler data, and logs.

## Root Structure

```
PERSISTENT_STORAGE_PATH/
├── domains/          # Domain configuration files
├── crawler/          # Crawler data organized by domain
└── logs/            # Application log files
```

## 1. Domains Subfolder

**Path**: `PERSISTENT_STORAGE_PATH/domains/`

Contains domain-specific folders with JSON configuration and metadata files.

### Structure

```
domains/
├── DOMAIN01/
│   ├── domain.json
│   └── files_metadata.json
├── DOMAIN02/
│   ├── domain.json
│   └── files_metadata.json
└── ...
```

### Domain JSON File Format (`domain.json`)

Each domain has a `domain.json` file with the following structure:

```json
{
  "domain_id": "DOMAIN01",
  "vector_store_name": "SharePoint-DOMAIN01",
  "vector_store_id": "vs_xxxxxxxxxxxxxxxxxxxxx",
  "name": "Example Domain 01",
  "description": "Description of the SharePoint site and its purpose",
  "file_sources": [
    {
      "source_id": "source01",
      "site_url": "https://contoso.sharepoint.com/sites/ExampleSite",
      "sharepoint_url_part": "/Shared Documents",
      "filter": ""
    }
  ],
  "sitepage_sources": [
    {
      "source_id": "source01",
      "site_url": "https://contoso.sharepoint.com/sites/ExampleSite",
      "sharepoint_url_part": "/SitePages",
      "filter": "FSObjType eq 0 and not startswith(ContentTypeId, '0x0101009D1CB255DA76424F860D91F20E6C4118AA'"
    }
  ],
  "list_sources": [
    {
      "source_id": "source01",
      "site_url": "https://contoso.sharepoint.com/sites/ExampleSite",
      "list_name": "Tasks",
      "filter": ""
    },
    {
      "source_id": "source02",
      "site_url": "https://contoso.sharepoint.com/sites/ExampleSite",
      "list_name": "Contacts",
      "filter": ""
    }
  ]
}
```

**Key Fields**:
- `domain_id`: Unique identifier for the domain (matches folder name)
- `vector_store_name`: Display name for the OpenAI vector store
- `vector_store_id`: OpenAI vector store ID (format: `vs_...`)
- `name`: Human-readable name for the domain
- `description`: Detailed description of the domain/site
- `file_sources`: Array of SharePoint document library sources
  - `source_id`: Unique identifier for this source (used in folder structure)
  - `site_url`: Full SharePoint site URL
  - `sharepoint_url_part`: Path to the document library
  - `filter`: Optional OData filter for documents
- `sitepage_sources`: Array of SharePoint site page sources
  - `source_id`: Unique identifier for this source (used in folder structure)
  - `site_url`: Full SharePoint site URL
  - `sharepoint_url_part`: Path to site pages (usually `/SitePages`)
  - `filter`: OData filter to exclude certain content types
- `list_sources`: Array of SharePoint list sources
  - `source_id`: Unique identifier for this source (used in folder structure)
  - `site_url`: Full SharePoint site URL
  - `list_name`: Name of the SharePoint list
  - `filter`: Optional OData filter for list items

### Files Metadata JSON File Format (`files_metadata.json`)

Contains metadata for all files that have been uploaded to the OpenAI vector store.

**Migration**: Use the `/crawler/migratefromv2tov3` endpoint to automatically migrate from v2 to v3 format. This endpoint creates a backup of the v2 file before conversion.

#### V3 Format (Current)

The v3 format uses a flat structure matching the `CrawledFile` dataclass:

```json
[
  {
    "sharepoint_listitem_id": 123,
    "sharepoint_unique_file_id": "b!abc123...",
    "openai_file_id": "assistant-BuQoNyXQnoedPjTySDTFU1",
    "file_relative_path": "DOMAIN01\\01_files\\source01\\02_embedded\\Document.docx",
    "url": "https://contoso.sharepoint.com/sites/Example/Shared%20Documents/Document.docx",
    "raw_url": "https://contoso.sharepoint.com/sites/Example/Shared Documents/Document.docx",
    "server_relative_url": "/sites/Example/Shared Documents/Document.docx",
    "filename": "Document.docx",
    "file_type": "docx",
    "file_size": 864368,
    "last_modified_utc": "2024-01-15T10:30:00.000000Z",
    "last_modified_timestamp": 1705319400
  },
  {
    "sharepoint_listitem_id": 124,
    "sharepoint_unique_file_id": "b!def456...",
    "openai_file_id": "assistant-1TZS6Y9z4V6oYuStT8qLUr",
    "file_relative_path": "DOMAIN01\\01_files\\source01\\02_embedded\\SubFolder\\AnotherDocument.pdf",
    "url": "https://contoso.sharepoint.com/sites/Example/Shared%20Documents/SubFolder/AnotherDocument.pdf",
    "raw_url": "https://contoso.sharepoint.com/sites/Example/Shared Documents/SubFolder/AnotherDocument.pdf",
    "server_relative_url": "/sites/Example/Shared Documents/SubFolder/AnotherDocument.pdf",
    "filename": "AnotherDocument.pdf",
    "file_type": "pdf",
    "file_size": 1234567,
    "last_modified_utc": "2024-01-10T14:22:15.000000Z",
    "last_modified_timestamp": 1704896535
  }
]
```

**V3 Key Fields**:
- `sharepoint_listitem_id`: SharePoint list item ID
- `sharepoint_unique_file_id`: SharePoint unique file identifier
- `openai_file_id`: OpenAI file ID (format: `assistant-...`)
- `file_relative_path`: Relative path to the embedded file in the crawler storage structure (format: `DOMAIN\\01_files\\source_id\\02_embedded\\filename.ext`)
- `url`: URL-encoded SharePoint source URL
- `raw_url`: Raw SharePoint URL (not encoded)
- `server_relative_url`: Server-relative URL path
- `filename`: Original filename
- `file_type`: File extension (docx, pdf, xlsx, etc.)
- `file_size`: File size in bytes
- `last_modified_utc`: UTC timestamp of when the file was last modified in ISO 8601 format with microseconds (format: `YYYY-MM-DDTHH:MM:SS.ffffffZ`)
- `last_modified_timestamp`: Unix timestamp of last modification

#### V2 Format (Legacy)

The v2 format uses a nested structure with a `file_metadata` object:

```json
[
  {
    "file_id": "assistant-BuQoNyXQnoedPjTySDTFU1",
    "embedded_file_relative_path": "DOMAIN01\\01_files\\source01\\02_embedded\\Document.docx",
    "embedded_file_last_modified_utc": "2024-01-15T10:30:00.000000Z",
    "file_metadata": {
      "source": "https://contoso.sharepoint.com/sites/Example/Shared%20Documents/Document.docx",
      "filename": "Document.docx",
      "file_type": "docx",
      "file_size": 864368,
      "last_modified": "2024-01-15",
      "raw_url": "https://contoso.sharepoint.com/sites/Example/Shared Documents/Document.docx"
    }
  }
]
```

**V2 Key Fields** (deprecated):
- `file_id`: OpenAI file ID (format: `assistant-...`)
- `embedded_file_relative_path`: Relative path to the embedded file
- `embedded_file_last_modified_utc`: UTC timestamp of last modification
- `file_metadata`: Nested object containing file metadata
  - `source`: URL-encoded SharePoint source URL
  - `filename`: Original filename
  - `file_type`: File extension
  - `file_size`: File size in bytes
  - `last_modified`: Last modification date (YYYY-MM-DD)
  - `raw_url`: Raw SharePoint URL

## 2. Crawler Subfolder

**Path**: `PERSISTENT_STORAGE_PATH/crawler/`

Contains crawled and processed data from SharePoint sites, organized by domain.

### Structure

```
crawler/
├── DOMAIN01/
│   ├── 01_files/
│   │   ├── source01/
│   │   │   ├── 02_embedded/
│   │   │   │   ├── document1.pdf
│   │   │   │   ├── document2.docx
│   │   │   │   ├── SubFolder1/
│   │   │   │   │   ├── document3.pdf
│   │   │   │   │   └── ...
│   │   │   │   └── ...
│   │   │   └── 03_failed/
│   │   │       ├── failed_file1.pdf
│   │   │       └── ...
│   │   ├── source02/
│   │   │   └── (same structure as source01)
│   │   └── ...
│   ├── 02_lists/
│   │   ├── source01/
│   │   │   ├── 01_originals/
│   │   │   │   ├── Tasks.csv
│   │   │   │   └── ...
│   │   │   ├── 02_embedded/
│   │   │   │   ├── Tasks.md
│   │   │   │   └── ...
│   │   │   └── 03_failed/
│   │   │       ├── FailedList1.csv
│   │   │       └── ...
│   │   ├── source02/
│   │   │   └── (same structure as source01)
│   │   └── ...
│   └── 03_sitepages/
│       ├── source01/
│       │   ├── 01_originals/
│       │   │   ├── Home.html
│       │   │   ├── About.html
│       │   │   └── ...
│       │   ├── 02_embedded/
│       │   │   ├── Home.html
│       │   │   ├── About.html
│       │   │   └── ...
│       │   └── 03_failed/
│       │       ├── FailedPage1.html
│       │       └── ...
│       ├── source02/
│       │   └── (same structure as source01)
│       └── ...
├── DOMAIN02/
│   └── (same structure as DOMAIN01)
└── ...
```

### Folder Descriptions

#### `01_files/` - Document Libraries
Contains files from SharePoint document libraries, organized by source_id.

- **`source_id/`**: Each document source has its own folder (e.g., `source01/`, `source02/`)
  - **`02_embedded/`**: Successfully processed files ready for vector store embedding
    - Contains actual files (PDF, DOCX, XLSX, PPTX, etc.) preserving SharePoint folder structure
    - These files are uploaded to OpenAI vector stores
    - File metadata is tracked in `files_metadata.json`
  - **`03_failed/`**: Files that failed processing
    - Contains files that couldn't be processed (corrupted, unsupported format, too large, etc.)

**Note**: The `01_files/` folder does NOT have an `01_originals/` subfolder. Files go directly to either `02_embedded/` or `03_failed/` after download from SharePoint.

#### `02_lists/` - SharePoint Lists
Contains data from SharePoint lists, organized by source_id.

- **`source_id/`**: Each list source has its own folder (e.g., `source01/`, `source02/`)
  - **`01_originals/`**: Original list data in CSV format
    - One CSV file per list
    - Contains raw list item data exported from SharePoint
    - CSV format with headers matching SharePoint column names
  - **`02_embedded/`**: Processed list data in Markdown format
    - Converted to Markdown for better readability and embedding
    - One MD file per list
    - Formatted with headers and structured data
  - **`03_failed/`**: Lists that failed processing
    - Contains CSV files for lists that couldn't be processed or converted
    - May include lists with errors, access issues, or conversion failures

**List CSV Format** (`01_originals/ListName.csv`):
```csv
ID,Title,Status,AssignedTo,DueDate
1,Task 1,In Progress,user@contoso.com,2024-01-15
2,Task 2,Completed,user2@contoso.com,2024-01-10
3,Task 3,Not Started,user3@contoso.com,2024-01-20
```

**List Markdown Format** (`02_embedded/ListName.md`):
```markdown
## List Name

### "List Name" - Item 1
**Title**: Task 1
**Status**: In Progress
**AssignedTo**: user@contoso.com
**DueDate**: 2024-01-15

### "List Name" - Item 2
**Title**: Task 2
**Status**: Completed
**AssignedTo**: user2@contoso.com
**DueDate**: 2024-01-10
```

#### `03_sitepages/` - SharePoint Site Pages
Contains SharePoint site pages (modern pages, wiki pages), organized by source_id.

- **`source_id/`**: Each page source has its own folder (e.g., `source01/`, `source02/`)
  - **`01_originals/`**: Original page content in HTML format
    - One HTML file per page
    - Contains full page HTML including styles and scripts
    - Saved using SingleFile format (complete standalone HTML)
  - **`02_embedded/`**: Processed page content in HTML format
    - Cleaned/processed HTML for embedding
    - One HTML file per page
    - May have simplified HTML structure
  - **`03_failed/`**: Site pages that failed processing
    - Contains HTML files for pages that couldn't be processed or converted
    - May include pages with errors, access issues, or conversion failures

**Site Page HTML Format** (`01_originals/PageName.html`):
```html
<!DOCTYPE html>
<html lang="en-US" dir="ltr">
<meta charset="utf-8">
<style>...</style>
<body>
  <div class="page-content">
    <h1>Page Title</h1>
    <p>Page content...</p>
  </div>
</body>
</html>
```

## 3. Logs Subfolder

**Path**: `PERSISTENT_STORAGE_PATH/logs/`

Contains application log files created by various endpoints.

### Structure

```
logs/
├── crawler_DOMAIN01_20240115_120000.log
├── update_maps_DOMAIN01.log
├── update_maps_DOMAIN02.log
├── error_log.txt
└── ...
```

### Log File Format

Log files are plain text (UTF-8 encoded) with timestamped entries:

```
Log file created at 2024-01-15T12:00:00.123456
Domain ID: DOMAIN01
Logfile: update_maps_DOMAIN01.log

[2024-01-15 12:00:01] Starting crawler for domain: DOMAIN01
[2024-01-15 12:00:05] Scanning document libraries...
[2024-01-15 12:00:10] Found 150 files in library: Documents
[2024-01-15 12:00:12] Found 45 files in library: Shared Documents
[2024-01-15 12:00:15] Processing lists...
[2024-01-15 12:00:18] Found 3 lists to process
[2024-01-15 12:00:20] Processing site pages...
[2024-01-15 12:00:25] Found 20 site pages
[2024-01-15 12:00:30] Processing complete
```

## Hardcoded Configuration

All folder names and structure are defined in `src/hardcoded_config.py`:

```python
@dataclass
class CrawlerHardcodedConfig:
  # Root subfolders
  PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER: str = "domains"
  PERSISTENT_STORAGE_PATH_CRAWLER_SUBFOLDER: str = "crawler"
  PERSISTENT_STORAGE_PATH_LOGS_SUBFOLDER: str = "logs"
  
  # Crawler structure - main folders
  PERSISTENT_STORAGE_PATH_DOCUMENTS_FOLDER: str = "01_files"
  PERSISTENT_STORAGE_PATH_LISTS_FOLDER: str = "02_lists"
  PERSISTENT_STORAGE_PATH_SITEPAGES_FOLDER: str = "03_sitepages"
  
  # Crawler structure - subfolders
  PERSISTENT_STORAGE_PATH_ORIGINALS_SUBFOLDER: str = "01_originals"
  PERSISTENT_STORAGE_PATH_EMBEDDED_SUBFOLDER: str = "02_embedded"
  PERSISTENT_STORAGE_PATH_FAILED_SUBFOLDER: str = "03_failed"
```

### Configuration Reference

| Configuration Key | Value | Description |
|------------------|-------|-------------|
| `PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER` | `"domains"` | Root folder for domain configurations |
| `PERSISTENT_STORAGE_PATH_CRAWLER_SUBFOLDER` | `"crawler"` | Root folder for crawler data |
| `PERSISTENT_STORAGE_PATH_LOGS_SUBFOLDER` | `"logs"` | Root folder for log files |
| `PERSISTENT_STORAGE_PATH_DOCUMENTS_FOLDER` | `"01_files"` | Folder for SharePoint document libraries |
| `PERSISTENT_STORAGE_PATH_LISTS_FOLDER` | `"02_lists"` | Folder for SharePoint lists |
| `PERSISTENT_STORAGE_PATH_SITEPAGES_FOLDER` | `"03_sitepages"` | Folder for SharePoint site pages |
| `PERSISTENT_STORAGE_PATH_ORIGINALS_SUBFOLDER` | `"01_originals"` | Subfolder for original/raw data |
| `PERSISTENT_STORAGE_PATH_EMBEDDED_SUBFOLDER` | `"02_embedded"` | Subfolder for processed/embedded data |
| `PERSISTENT_STORAGE_PATH_FAILED_SUBFOLDER` | `"03_failed"` | Subfolder for failed processing |

## Path Construction Examples

### Domain Configuration File
```python
domain_folder = os.path.join(
    PERSISTENT_STORAGE_PATH,
    CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER,
    domain_id
)
domain_file = os.path.join(domain_folder, "domain.json")
# Result: PERSISTENT_STORAGE_PATH/domains/DOMAIN01/domain.json
```

### Files Metadata File
```python
metadata_file = os.path.join(
    PERSISTENT_STORAGE_PATH,
    CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER,
    domain_id,
    "files_metadata.json"
)
# Result: PERSISTENT_STORAGE_PATH/domains/DOMAIN01/files_metadata.json
```

### Embedded Documents for a Domain and Source
```python
embedded_docs = os.path.join(
    PERSISTENT_STORAGE_PATH,
    CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_CRAWLER_SUBFOLDER,
    domain_id,
    CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOCUMENTS_FOLDER,
    source_id,
    CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_EMBEDDED_SUBFOLDER
)
# Result: PERSISTENT_STORAGE_PATH/crawler/DOMAIN01/01_files/source01/02_embedded/
```

### Original Lists for a Domain and Source
```python
original_lists = os.path.join(
    PERSISTENT_STORAGE_PATH,
    CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_CRAWLER_SUBFOLDER,
    domain_id,
    CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_LISTS_FOLDER,
    source_id,
    CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_ORIGINALS_SUBFOLDER
)
# Result: PERSISTENT_STORAGE_PATH/crawler/DOMAIN01/02_lists/source01/01_originals/
```

### Embedded Site Pages for a Domain and Source
```python
embedded_pages = os.path.join(
    PERSISTENT_STORAGE_PATH,
    CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_CRAWLER_SUBFOLDER,
    domain_id,
    CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_SITEPAGES_FOLDER,
    source_id,
    CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_EMBEDDED_SUBFOLDER
)
# Result: PERSISTENT_STORAGE_PATH/crawler/DOMAIN01/03_sitepages/source01/02_embedded/
```

### Log File
```python
log_file = os.path.join(
    PERSISTENT_STORAGE_PATH,
    CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_LOGS_SUBFOLDER,
    f"crawler_{domain_id}.log"
)
# Result: PERSISTENT_STORAGE_PATH/logs/crawler_DOMAIN01.log
```

## Notes

1. **Numeric Prefixes**: Folders use numeric prefixes (`01_`, `02_`, `03_`) to enforce ordering in file explorers
2. **Domain Isolation**: Each domain has its own isolated folder structure under both `domains/` and `crawler/`
3. **Source Isolation**: Each source (document library, list, or site page collection) has its own `source_id` folder within the content type folder
4. **Processing Pipeline**: 
   - **Lists**: CSV (`source_id/01_originals/`) → Markdown (`source_id/02_embedded/`) or `source_id/03_failed/`
   - **SitePages**: HTML (`source_id/01_originals/`) → HTML (`source_id/02_embedded/`) or `source_id/03_failed/`
   - **Files**: Direct download → `source_id/02_embedded/` or `source_id/03_failed/` (no originals folder)
5. **File Types**: Only files matching `DEFAULT_FILETYPES_ACCEPTED_BY_VECTOR_STORES` are processed for embedding
6. **JSON Encoding**: All JSON files use UTF-8 encoding
7. **Log Files**: Created on-demand by various endpoints, plain text UTF-8 format
8. **Metadata Tracking**: `files_metadata.json` tracks all files uploaded to OpenAI vector stores with their IDs and metadata

## Related Files

- **Configuration**: `src/hardcoded_config.py`
- **Domain Management**: `src/routers/domains.py`
- **Crawler Endpoints**: `src/routers/crawler.py`
- **Utility Functions**: `src/utils.py` (logfile functions)
- **Common Functions**: `src/common_crawler_functions.py`
