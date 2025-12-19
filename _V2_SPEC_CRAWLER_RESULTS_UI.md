# V2 Crawler Results UI Specification

**Goal**: Provide UI for viewing, downloading, and managing crawl result archives
**Target file**: `/src/routers_v2/crawl_results.py`

**Depends on:**
- `_V2_SPEC_ROUTERS.md` for endpoint design and JSON result format
- `_V2_SPEC_COMMON_UI_FUNCTIONS.md` for UI generation functions
- `_V2_SPEC_CRAWL_RESULTS.md` for crawl result domain objects and archive structure

**Does not depend on:**
- `_V2_SPEC_CRAWLER_UI.md` (separate router)

## Table of Contents

1. Overview
2. Scenario
3. User Actions
4. UX Design
5. Domain Objects
6. Key Mechanisms
7. Action Flow

## Overview

The `/v2/crawl-results` router provides management interface for crawl result archives. Each archive contains a snapshot of map files and metadata from a completed crawl.

**Key characteristics:**
- Single-page UI with results table and hidden console panel
- Console hidden by default (no streaming needed for this UI)
- Bulk delete support via checkboxes
- View action opens results dialog (same pattern as jobs UI)

## Scenario

**Real-world problem:**
Users need to review historical crawl results for auditing and debugging. They may need to download archives or clean up old results.

**What we don't want:**
- Complex filtering or search
- Inline editing of results
- Automatic cleanup (user controls deletion)

## User Actions

| Action | Trigger | Effect |
|--------|---------|--------|
| View | Click [View] button | Open modal dialog with crawl result details |
| Download | Click [Download] button | Download crawl result archive as ZIP |
| Delete | Click [Delete] button | Delete single crawl result after confirmation |
| Bulk Delete | Select rows + click [Delete (n)] | Delete multiple crawl results after confirmation |
| Refresh | Click [Refresh] link | Reload results table |

## UX Design

### Main Layout

```
+---------------------------------------------------------------------------------------------------------------------------------------------------+
| Crawl Results [Refresh]                                                                                                                           |
|                                                                                                                                                   |
| Back to Main Page | Domains | Crawler                                                                                                            |
|                                                                                                                                                   |
| [Delete (0)]                                                                                                                                      |
|                                                                                                                                                   |
| +---+------------------------------+-----------+-----------------+-------------+-------+------------------+----------------+----------------------+
| |   | Crawl Result ID              | Domain ID | Vector Store ID | Mode        | Scope | Started          | Duration       | Actions              |
| +---+------------------------------+-----------+-----------------+-------------+-------+------------------+----------------+----------------------+
| |[ ]| 20241219_143022_domain01     | domain_01 | vs_abc123       | full        | all   | 2024-12-19 14:30 | 1 hour 23 mins | [View] [DL] [Delete] |
| |[ ]| 20241218_091500_domain02     | domain_02 | vs_def456       | incremental | all   | 2024-12-18 09:15 | 12 mins        | [View] [DL] [Delete] |
| +---+------------------------------+-----------+-----------------+-------------+-------+------------------+----------------+----------------------+
|                                                                                                                                                   |
| +-------------------------------------------------------------------------------------------------------------------------------------------------+
| | [Resize Handle - Draggable]                                                                                                          (hidden)   |
| | Console Output                                                                                                                         [Clear] |
| +-------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                                                                                                   |
+---------------------------------------------------------------------------------------------------------------------------------------------------+
```

### Table Columns

| Column | Source | Notes |
|--------|--------|-------|
| Checkbox | - | For bulk selection |
| Crawl Result ID | `result.id` | Archive identifier |
| Domain ID | `result.domain_id` | Domain that was crawled |
| Vector Store ID | `result.vector_store_id` | Target vector store |
| Mode | `result.mode` | `full` or `incremental` |
| Scope | `result.scope` | `all` or `source` |
| Started | `result.started` | Format: `YYYY-MM-DD HH:MM` |
| Duration | computed | Human readable: `1 hour 23 mins`, `12 mins`, `45 secs` |
| Actions | - | [View] [Download] [Delete] |

### Toolbar

| Button | State | Action |
|--------|-------|--------|
| Delete (0) | No selection | Disabled |
| Delete (n) | n items selected | Enabled, triggers bulk delete confirmation |

### Navigation Links

- **Back to Main Page** - `/` root endpoint
- **Domains** - `/v2/domains?format=ui`
- **Crawler** - `/v2/crawler?format=ui`

### View Dialog (Modal)

Same pattern as jobs UI "Results" dialog:

```
+-----------------------------------------------+
| Crawl Result: 20241219_143022_domain01    [x] |
+-----------------------------------------------+
| Domain ID:        domain_01                   |
| Vector Store ID:  vs_abc123                   |
| Mode:             full                        |
| Scope:            all                         |
| Started:          2024-12-19 14:30:22         |
| Finished:         2024-12-19 15:53:45         |
| Duration:         1 hour 23 mins              |
|                                               |
| Files:                                        |
|   sharepoint_map.csv    (1,234 rows)          |
|   files_map.csv         (1,234 rows)          |
|   vectorstore_map.csv   (1,189 rows)          |
|                                               |
| Summary:                                      |
|   Downloaded: 1,234                           |
|   Processed:  1,234                           |
|   Embedded:   1,189                           |
|   Skipped:    45                              |
|   Errors:     0                               |
+-----------------------------------------------+
```

### Delete Confirmation Dialog

```
+-----------------------------------------------+
| Delete Crawl Result                       [x] |
+-----------------------------------------------+
| Are you sure you want to delete this crawl    |
| result?                                       |
|                                               |
| ID: 20241219_143022_domain01                  |
|                                               |
|                    [Cancel] [Delete]          |
+-----------------------------------------------+
```

### Bulk Delete Confirmation Dialog

```
+-----------------------------------------------+
| Delete Crawl Results                      [x] |
+-----------------------------------------------+
| Are you sure you want to delete 3 crawl       |
| results?                                      |
|                                               |
| - 20241219_143022_domain01                    |
| - 20241218_091500_domain02                    |
| - 20241217_080000_domain01                    |
|                                               |
|                    [Cancel] [Delete]          |
+-----------------------------------------------+
```

## Domain Objects

### Crawl Result

```
CrawlResult:
  id: string                    # Archive ID (e.g., "20241219_143022_domain01")
  domain_id: string             # Domain that was crawled
  vector_store_id: string       # Target vector store
  mode: string                  # "full" or "incremental"
  scope: string                 # "all" or "source"
  source_id: string | null      # Source ID if scope="source"
  started: string               # ISO timestamp
  finished: string              # ISO timestamp
  duration_seconds: int         # Duration in seconds
  files:
    sharepoint_map_rows: int    # Row count
    files_map_rows: int         # Row count
    vectorstore_map_rows: int   # Row count
  summary:
    downloaded: int             # Files downloaded
    processed: int              # Files processed
    embedded: int               # Files embedded to vector store
    skipped: int                # Files skipped
    errors: int                 # Files with errors
```

## Key Mechanisms

### Console Panel (Hidden)

- Hidden by default (no streaming operations in this UI)
- Can be shown manually if needed for future features
- Same resize/clear behavior as other UIs

### Duration Formatting

Convert `duration_seconds` to human-readable format:
- `< 60` -> `45 secs`
- `60-3599` -> `12 mins` or `12 mins 30 secs`
- `>= 3600` -> `1 hour 23 mins`

### Bulk Selection

- Header checkbox toggles all rows
- Individual checkboxes toggle single rows
- Toolbar button updates count: `Delete (n)`
- Count of 0 disables button

### Download Action

1. User clicks [Download]
2. Browser initiates file download
3. Server streams ZIP archive with:
   - `crawl.json` (metadata)
   - `sharepoint_map.csv`
   - `files_map.csv`
   - `vectorstore_map.csv`

## Action Flow

### View Result

```
User clicks [View]
  -> fetchResultDetails(resultId)
  -> showModal(resultDetailsHtml)
```

### Download Result

```
User clicks [Download]
  -> window.location = `/v2/crawl-results/${resultId}/download`
  -> Browser downloads ZIP file
```

### Delete Single Result

```
User clicks [Delete]
  -> showConfirmDialog("Delete crawl result?", resultId)
  -> User clicks [Delete] in dialog
  -> POST /v2/crawl-results/${resultId}/delete
  -> showToast("Crawl result deleted", "success")
  -> refreshResultsTable()
```

### Bulk Delete Results

```
User selects multiple rows
  -> Toolbar shows "Delete (n)"
User clicks [Delete (n)]
  -> showConfirmDialog("Delete n crawl results?", selectedIds)
  -> User clicks [Delete] in dialog
  -> POST /v2/crawl-results/delete-bulk with body { ids: [...] }
  -> showToast("n crawl results deleted", "success")
  -> refreshResultsTable()
```

## Implementation Notes

### Endpoints

```
GET  /v2/crawl-results?format=ui              -> HTML page with results table
GET  /v2/crawl-results?format=json            -> JSON list of crawl results
GET  /v2/crawl-results/${id}?format=json      -> JSON details of single result
GET  /v2/crawl-results/${id}/download         -> ZIP file download
POST /v2/crawl-results/${id}/delete           -> Delete single result
POST /v2/crawl-results/delete-bulk            -> Delete multiple results
```

### Dependencies

- `common_ui_functions_v2.py` for page generation, table, modal, console
- Archive storage path from `hardcoded_config.py`

### Router-Specific JavaScript

- `refreshResultsTable()` - fetch and re-render results
- `viewResult(resultId)` - fetch details and show modal
- `downloadResult(resultId)` - trigger file download
- `deleteResult(resultId)` - single delete with confirmation
- `deleteSelectedResults()` - bulk delete with confirmation
- `toggleSelectAll()` / `updateSelection()` - checkbox handling
- `formatDuration(seconds)` - human-readable duration
