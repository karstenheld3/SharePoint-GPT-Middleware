# Data Sources Documentation

This document describes the data sources used by the SharePoint-GPT-Middleware application, how data flows between them, and how files are tracked across different systems.

## Overview

The application integrates three main data sources:

1. **SharePoint** - Original source of documents, lists, and site pages
2. **Local Files** - Downloaded and processed files stored in persistent storage
3. **Vector Stores** - OpenAI vector stores containing embedded files for AI search

The `files_metadata.json` file serves as the central mapping that connects files across all three sources.

## Data Flow Architecture

```
┌─────────────┐
│  SharePoint │
│   (Source)  │
└──────┬──────┘
       │ 1. Download
       │ (Crawler)
       ▼
┌─────────────────────┐
│   Local Files       │
│ (Persistent Storage)│
│  02_embedded/       │
└──────┬──────────────┘
       │ 2. Upload
       │ (Embedding)
       ▼
┌─────────────────────┐
│  Vector Stores      │
│   (OpenAI API)      │
└─────────────────────┘
       │
       │ 3. Track
       ▼
┌─────────────────────┐
│ files_metadata.json │
│  (Central Mapping)  │
└─────────────────────┘
```

## 1. SharePoint (Original Source)

**Purpose**: Original source of all content

**Content Types**:
- **Document Libraries** - Office documents, PDFs, images, etc.
- **Lists** - Structured data (tasks, contacts, custom lists)
- **Site Pages** - Modern pages and wiki pages

**Access Method**: Microsoft Graph API / SharePoint REST API

**Configuration**: Defined in `domain.json` with three source types:
- `file_sources` - Document library sources
- `list_sources` - SharePoint list sources
- `sitepage_sources` - Site page sources

**Data Provided by SharePoint**:
```json
{
  "sharepoint_listitem_id": 123,
  "sharepoint_unique_file_id": "b!abc123...",
  "filename": "Document.docx",
  "file_type": "docx",
  "file_size": 864368,
  "url": "https://site.sharepoint.com/Shared%20Documents/Document.docx",
  "raw_url": "https://site.sharepoint.com/Shared Documents/Document.docx",
  "server_relative_url": "/sites/Site/Shared Documents/Document.docx",
  "last_modified_utc": "2024-01-15T10:30:00.000000Z",
  "last_modified_timestamp": 1705319400
}
```

**Endpoint**: `/crawler/loadsharepointfiles`
- Connects to SharePoint using client credentials
- Retrieves file metadata and content
- Returns list of files with SharePoint metadata

## 2. Local Files (Persistent Storage)

**Purpose**: Local cache of downloaded files, processed for embedding

**Location**: `PERSISTENT_STORAGE_PATH/crawler/DOMAIN_ID/`

**Folder Structure**:
```
crawler/DOMAIN_ID/
├── 01_files/source_id/
│   ├── 02_embedded/          # Successfully processed files
│   │   ├── Document.docx
│   │   └── SubFolder/
│   │       └── AnotherDoc.pdf
│   └── 03_failed/            # Failed processing
├── 02_lists/source_id/
│   ├── 01_originals/         # Original CSV exports
│   ├── 02_embedded/          # Converted Markdown files
│   └── 03_failed/
└── 03_sitepages/source_id/
    ├── 01_originals/         # Original HTML
    ├── 02_embedded/          # Processed HTML
    └── 03_failed/
```

**Download Process** (Step 1: SharePoint → Local Files):

1. **Crawler connects to SharePoint** using credentials from config
2. **Downloads files** from document libraries defined in `file_sources`
3. **Saves to local storage**:
   - Files go directly to `02_embedded/` (no originals folder for files)
   - Preserves SharePoint folder structure
   - Failed downloads go to `03_failed/`
4. **Exports lists** to CSV in `01_originals/`, converts to Markdown in `02_embedded/`
5. **Downloads site pages** as HTML to `01_originals/`, processes to `02_embedded/`

**Data Provided by Local Files**:
```json
{
  "file_path": "E:/storage/crawler/DOMAIN01/01_files/source01/02_embedded/Document.docx",
  "file_relative_path": "DOMAIN01\\01_files\\source01\\02_embedded\\Document.docx",
  "filename": "Document.docx",
  "file_size": 864368,
  "last_modified_utc": "2024-01-15T10:30:00.000000Z"
}
```

**Endpoint**: `/crawler/loadlocalfiles`
- Scans local `02_embedded/` folders
- Returns list of files with local file system metadata
- Does NOT include SharePoint metadata (only file path, size, modified date)

## 3. Vector Stores (OpenAI)

**Purpose**: AI-searchable embeddings of documents

**Location**: OpenAI cloud service (accessed via API)

**Upload Process** (Step 2: Local Files → Vector Stores):

1. **Files are uploaded** from `02_embedded/` folders to OpenAI
2. **OpenAI processes files**:
   - Creates embeddings for semantic search
   - Assigns unique `openai_file_id` (format: `assistant-...`)
   - Stores in vector store identified by `vector_store_id`
3. **Metadata is tracked** in `files_metadata.json`

**Data Provided by Vector Stores**:
```json
{
  "openai_file_id": "assistant-BuQoNyXQnoedPjTySDTFU1",
  "filename": "Document.docx",
  "bytes": 864368,
  "created_at": 1705319400,
  "status": "completed"
}
```

**Endpoint**: `/crawler/loadvectorstorefiles`
- Queries OpenAI API for files in a vector store
- Returns list of files with OpenAI metadata
- Does NOT include SharePoint or local file path information

## 4. files_metadata.json (Central Mapping)

**Purpose**: Maps files across all three data sources

**Location**: `PERSISTENT_STORAGE_PATH/domains/DOMAIN_ID/files_metadata.json`

**Critical Role**: This file is the **only place** where all three data sources are connected:
- SharePoint metadata (URLs, IDs, timestamps)
- Local file paths (where files are stored)
- OpenAI file IDs (for vector store queries)

### V3 Format (Current)

```json
[
  {
    "sharepoint_listitem_id": 123,
    "sharepoint_unique_file_id": "b!abc123...",
    "openai_file_id": "assistant-BuQoNyXQnoedPjTySDTFU1",
    "file_relative_path": "DOMAIN01\\01_files\\source01\\02_embedded\\Document.docx",
    "url": "https://site.sharepoint.com/Shared%20Documents/Document.docx",
    "raw_url": "https://site.sharepoint.com/Shared Documents/Document.docx",
    "server_relative_url": "/sites/Site/Shared Documents/Document.docx",
    "filename": "Document.docx",
    "file_type": "docx",
    "file_size": 864368,
    "last_modified_utc": "2024-01-15T10:30:00.000000Z",
    "last_modified_timestamp": 1705319400
  }
]
```

### Field Mapping Across Sources

| Field | SharePoint | Local Files | Vector Store | files_metadata.json |
|-------|-----------|-------------|--------------|---------------------|
| `sharepoint_listitem_id` | ✅ Provided | ❌ Not available | ❌ Not available | ✅ Stored |
| `sharepoint_unique_file_id` | ✅ Provided | ❌ Not available | ❌ Not available | ✅ Stored |
| `openai_file_id` | ❌ Not available | ❌ Not available | ✅ Provided | ✅ Stored |
| `file_relative_path` | ❌ Not available | ✅ Provided | ❌ Not available | ✅ Stored |
| `url` | ✅ Provided | ❌ Not available | ❌ Not available | ✅ Stored |
| `raw_url` | ✅ Provided | ❌ Not available | ❌ Not available | ✅ Stored |
| `server_relative_url` | ✅ Provided | ❌ Not available | ❌ Not available | ✅ Stored |
| `filename` | ✅ Provided | ✅ Provided | ✅ Provided | ✅ Stored |
| `file_type` | ✅ Provided | ✅ Derived | ❌ Not available | ✅ Stored |
| `file_size` | ✅ Provided | ✅ Provided | ✅ Provided | ✅ Stored |
| `last_modified_utc` | ✅ Provided | ✅ Provided | ❌ Not available | ✅ Stored |
| `last_modified_timestamp` | ✅ Provided | ❌ Not available | ❌ Not available | ✅ Stored |

### How files_metadata.json is Built

**Step 3: Tracking in files_metadata.json**

1. **During download** (SharePoint → Local):
   - Crawler collects SharePoint metadata
   - Saves file to local storage
   - Records `file_relative_path`

2. **During upload** (Local → Vector Store):
   - File is uploaded to OpenAI
   - OpenAI returns `openai_file_id`
   - Metadata entry is created/updated

3. **Final entry** contains:
   - SharePoint identifiers and URLs
   - Local file path
   - OpenAI file ID
   - All metadata from all sources

## Complete Data Flow Example

### Step 1: Download from SharePoint

**Action**: Crawler downloads `Document.docx` from SharePoint

**Input** (from SharePoint):
```json
{
  "sharepoint_listitem_id": 123,
  "sharepoint_unique_file_id": "b!abc123...",
  "url": "https://site.sharepoint.com/Shared%20Documents/Document.docx",
  "filename": "Document.docx",
  "file_size": 864368,
  "last_modified_utc": "2024-01-15T10:30:00.000000Z"
}
```

**Output** (saved to local storage):
- File location: `E:/storage/crawler/DOMAIN01/01_files/source01/02_embedded/Document.docx`
- Relative path: `DOMAIN01\01_files\source01\02_embedded\Document.docx`

### Step 2: Upload to Vector Store

**Action**: File is uploaded to OpenAI vector store

**Input** (from local storage):
- File path: `E:/storage/crawler/DOMAIN01/01_files/source01/02_embedded/Document.docx`

**Output** (from OpenAI):
```json
{
  "openai_file_id": "assistant-BuQoNyXQnoedPjTySDTFU1",
  "filename": "Document.docx",
  "bytes": 864368,
  "status": "completed"
}
```

### Step 3: Record in files_metadata.json

**Action**: Create metadata entry combining all sources

**Result** (in files_metadata.json):
```json
{
  "sharepoint_listitem_id": 123,
  "sharepoint_unique_file_id": "b!abc123...",
  "openai_file_id": "assistant-BuQoNyXQnoedPjTySDTFU1",
  "file_relative_path": "DOMAIN01\\01_files\\source01\\02_embedded\\Document.docx",
  "url": "https://site.sharepoint.com/Shared%20Documents/Document.docx",
  "raw_url": "https://site.sharepoint.com/Shared Documents/Document.docx",
  "server_relative_url": "/sites/Site/Shared Documents/Document.docx",
  "filename": "Document.docx",
  "file_type": "docx",
  "file_size": 864368,
  "last_modified_utc": "2024-01-15T10:30:00.000000Z",
  "last_modified_timestamp": 1705319400
}
```

## Using the Combined Data

### Search Results Enhancement

When a user searches using the `/query` endpoint:

1. **OpenAI returns results** with `openai_file_id`
2. **Application looks up** `openai_file_id` in `files_metadata.json`
3. **Retrieves complete metadata**:
   - SharePoint URL (for "View in SharePoint" links)
   - Local file path (for local access if needed)
   - All metadata (size, type, modified date)
4. **Returns enriched results** to user

### Example Search Result

```json
{
  "data": "...document content...",
  "source": "https://site.sharepoint.com/Shared%20Documents/Document.docx",
  "metadata": {
    "file_id": "assistant-BuQoNyXQnoedPjTySDTFU1",
    "filename": "Document.docx",
    "file_type": "docx",
    "file_size": 864368,
    "last_modified_utc": "2024-01-15T10:30:00.000000Z",
    "raw_url": "https://site.sharepoint.com/Shared Documents/Document.docx"
  }
}
```

## Endpoint Summary

| Endpoint | Data Source | Returns | Use Case |
|----------|-------------|---------|----------|
| `/crawler/loadsharepointfiles` | SharePoint API | SharePoint metadata + file list | Check what's in SharePoint |
| `/crawler/loadlocalfiles` | Local file system | File paths + basic metadata | Check what's downloaded |
| `/crawler/loadvectorstorefiles` | OpenAI API | OpenAI file IDs + status | Check what's embedded |
| `/query` or `/query2` | All three (via files_metadata.json) | Complete enriched results | Search with full context |

## Data Consistency

### Keeping Data in Sync

**Challenge**: Files can change in SharePoint, be deleted locally, or removed from vector stores.

**Solution**: Use the crawler endpoints to compare:

1. **Compare SharePoint vs Local**:
   ```
   SharePoint files - Local files = Files to download
   Local files - SharePoint files = Files deleted in SharePoint
   ```

2. **Compare Local vs Vector Store**:
   ```
   Local files - Vector store files = Files to upload
   Vector store files - Local files = Files deleted locally
   ```

3. **Update files_metadata.json**:
   - Add entries for newly uploaded files
   - Remove entries for deleted files
   - Update entries for modified files

### Migration from V2 to V3

**Endpoint**: `/crawler/migratefromv2tov3`

**Purpose**: Convert old nested format to new flat format

**Process**:
1. Detects V2 format using `is_files_metadata_v2_format()`
2. Converts each item using `convert_file_metadata_item_from_v2_to_v3()`
3. Creates backup (`files_metadata_v2.json`)
4. Writes new V3 format

**V2 → V3 Field Mapping**:
- `file_id` → `openai_file_id`
- `embedded_file_relative_path` → `file_relative_path`
- `embedded_file_last_modified_utc` → `last_modified_utc`
- `file_metadata.source` → `url`
- All nested fields → Flattened to top level

## Best Practices

1. **Always use files_metadata.json** as the source of truth for file relationships
2. **Keep backups** before running migrations or bulk operations
3. **Verify consistency** regularly using the load endpoints
4. **Monitor failed folders** (`03_failed/`) for processing issues
5. **Use relative paths** in code to support different storage locations
6. **Strip whitespace** from all string fields during processing

## Related Documentation

- **[PERSISTENT_STORAGE_STRUCTURE.md](PERSISTENT_STORAGE_STRUCTURE.md)** - Detailed folder structure
- **[README.md](README.md)** - General application documentation
- **Configuration**: `src/hardcoded_config.py` - Folder name constants
- **Data Classes**: `src/common_crawler_functions.py` - `CrawledFile` dataclass
