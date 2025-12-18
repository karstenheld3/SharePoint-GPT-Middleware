# V2 Domains Router UI Specification

This document specifies the interactive UI for the `/v2/domains?format=ui` endpoint.

**Goal**: Provide a UI for managing knowledge domains used for crawling and semantic search.
**Target file**: `/src/routers_v2/domains.py`

**Depends on:**
- `_V2_SPEC_ROUTERS.md` for endpoint design, streaming job infrastructure, and SSE format.
- `_V2_SPEC_COMMON_UI_FUNCTIONS.md` for UI generation functions.

**Does not depend on:**
- `_V1_SPEC_COMMON_UI_FUNCTIONS.md`

## Overview

A reactive web UI for managing knowledge domains with CRUD operations. The UI displays a domain table with inline actions and uses common UI functions from `common_ui_functions_v2.py`.

**Key Technologies:**
- Common UI functions from `common_ui_functions_v2.py`
- HTMX for declarative HTTP interactions (included but minimally used)
- Native JavaScript for SSE streaming via unified `fetch()` with `ReadableStream`
- Modal dialogs for Create/Edit forms

## Scenario

**Problem:** Administrators need to manage knowledge domains that define which SharePoint sites/libraries to crawl and which vector stores to use for semantic search.

**Solution:** A fully functional domains router UI that:
- Lists all domains with Edit, Delete actions
- Provides New Domain creation via modal form
- Shows toast notifications for action feedback

**What we don't want:**
- Complex state management libraries (use simple JavaScript)
- External dependencies beyond HTMX and standard browser APIs
- Polling-based updates (use SSE for streaming when needed)

## Domain Object Model

**Domain** (as displayed in UI table)
- `domain_id` - Unique identifier (user-defined string, e.g., "DOMAIN01")
- `name` - Display name (e.g., "Sales Documents")
- `vector_store_name` - Name of the associated OpenAI vector store
- `vector_store_id` - ID of the associated OpenAI vector store (e.g., "vs_abc123")

**Domain** (full data model - stored in domain folder)
- `domain_id` - Unique identifier (required, pattern: `[a-zA-Z0-9_-]+`)
- `name` - Display name (required)
- `description` - Description text (required)
- `vector_store_name` - Name of the vector store (required)
- `vector_store_id` - ID of the vector store (optional, leave empty if not needed)
- `file_sources` - Array of FileSource objects for SharePoint document libraries
- `sitepage_sources` - Array of SitePageSource objects for SharePoint site pages
- `list_sources` - Array of ListSource objects for SharePoint lists

**FileSource**
- `source_id` - Unique identifier within domain
- `site_url` - SharePoint site URL (e.g., "https://contoso.sharepoint.com/sites/sales")
- `sharepoint_url_part` - Library path (e.g., "/Shared Documents")
- `filter` - OData filter expression (optional)

**SitePageSource**
- `source_id` - Unique identifier within domain
- `site_url` - SharePoint site URL
- `sharepoint_url_part` - Site pages path (e.g., "/SitePages")
- `filter` - OData filter expression (optional)

**ListSource**
- `source_id` - Unique identifier within domain
- `site_url` - SharePoint site URL
- `list_name` - SharePoint list name
- `filter` - OData filter expression (optional)

## User Actions

1. **View domain list** - Page load: server returns HTML with pre-rendered table rows
2. **Reload domains** - Click [Reload] to fetch domains via JSON and re-render table
3. **New domain** - Click [New Domain] to open modal form, submit to create new domain
4. **Edit domain** - Click [Edit] on row to open modal form with current values, submit to update
5. **Delete domain** - Click [Delete] on row with confirmation dialog

## UX Design

```
main page: /v2/domains?format=ui
+-------------------------------------------------------------------------------------------+
| Domains (3)  [Reload]                                                                     |
| Back to Main Page                                                                         |
|                                                                                           |
| [New Domain]                                                                              |
|                                                                                           |
| +-------------+----------------+----------------------+---------------+-------------------+
| | Domain ID   | Name           | Vector Store Name    | Vector Store ID | Actions        |
| +-------------+----------------+----------------------+---------------+-------------------+
| | DOMAIN01    | Sales Docs     | sales-vectorstore    | vs_abc123     | [Edit] [Delete]  |
| | DOMAIN02    | HR Documents   | hr-vectorstore       | vs_def456     | [Edit] [Delete]  |
| | DOMAIN03    | Engineering    | eng-vectorstore      | vs_ghi789     | [Edit] [Delete]  |
| +-------------+----------------+----------------------+---------------+-------------------+
|                                                                                           |
+-------------------------------------------------------------------------------------------+

Toast Container (top-right, fixed position):
+-----------------------------------------------+
| Domain Created | DOMAIN01                [x]  |
+-----------------------------------------------+

Modal (New Domain):
+---------------------------------------------------------------+
|                                                          [x]  |
| New Domain                                                    |
|                                                               |
| Domain ID *                                                   |
| [__________________________________________________________]  |
|                                                               |
| Name *                                                        |
| [__________________________________________________________]  |
|                                                               |
| Description *                                                 |
| [__________________________________________________________]  |
| [__________________________________________________________]  |
| [__________________________________________________________]  |
|                                                               |
| Vector Store Name *                                           |
| [__________________________________________________________]  |
|                                                               |
| Vector Store ID                                               |
| [Optional - leave empty if not needed_____________________ ]  |
|                                                               |
| > Advanced: Sources Configuration (Optional)                  |
|   |                                                           |
|   | Sources JSON (file_sources, sitepage_sources, list_sources)
|   | [Show JSON Example]                                       |
|   | [{"file_sources": [], "sitepage_sources": [], ...}_____ ] |
|   | [______________________________________________________] |
|   | [______________________________________________________] |
|   | Leave empty to create domain without sources.             |
|   | You can add them later.                                   |
|                                                               |
|                                    [OK] [Cancel]          |
+---------------------------------------------------------------+

Modal (JSON Example - nested):
+---------------------------------------------------------------+
|                                                               |
| JSON Example                                                  |
|                                                               |
| Copy this example and modify it for your needs:               |
|                                                               |
| +-----------------------------------------------------------+ |
| | {                                                         | |
| |   "file_sources": [                                       | |
| |     {                                                     | |
| |       "source_id": "source01",                            | |
| |       "site_url": "https://example.sharepoint.com/...",   | |
| |       "sharepoint_url_part": "/Shared Documents",         | |
| |       "filter": ""                                        | |
| |     }                                                     | |
| |   ],                                                      | |
| |   "sitepage_sources": [ ... ],                            | |
| |   "list_sources": [ ... ]                                 | |
| | }                                                         | |
| +-----------------------------------------------------------+ |
|                                                               |
|                              [Copy to Form] [Close]           |
+---------------------------------------------------------------+

Modal (Edit Domain):
+---------------------------------------------------------------+
|                                                          [x]  |
| Edit Domain: DOMAIN01                                         |
|                                                               |
| Domain ID (read-only)                                         |
| [DOMAIN01_____________________________________________] (disabled)
|                                                               |
| Name *                                                        |
| [Sales Docs____________________________________________]      |
|                                                               |
| Description *                                                 |
| [Sales team documentation and resources________________]      |
| [______________________________________________________]      |
|                                                               |
| Vector Store Name *                                           |
| [sales-vectorstore_____________________________________]      |
|                                                               |
| Vector Store ID                                               |
| [vs_abc123_____________________________________________]      |
|                                                               |
| > Advanced: Sources Configuration (Optional)                  |
|   (same as Create form)                                       |
|                                                               |
|                                      [OK] [Cancel]          |
+---------------------------------------------------------------+
```

## Functional Requirements

**DOM-FR-01: Domain List Display**
- Display all domains in a table with columns: Domain ID, Name, Vector Store Name, Vector Store ID, Actions
- Show domain count in page header
- Empty state message when no domains exist

**DOM-FR-02: New Domain**
- [New Domain] button opens modal form
- Form fields:
  - Domain ID * (required, pattern: `[a-zA-Z0-9_-]+`, validated for uniqueness)
  - Name * (required)
  - Description * (required, textarea)
  - Vector Store Name * (required)
  - Vector Store ID (optional, placeholder: "Optional - leave empty if not needed")
  - Advanced: Sources Configuration (collapsible `<details>` section)
    - Sources JSON textarea with placeholder
    - [Show JSON Example] button opens nested modal
    - Help text: "Leave empty to create domain without sources. You can add them later."
- Submit creates domain via POST to `/v2/domains/create?format=json`
- Success: close modal, reload list, show success toast
- Error: show error toast

**DOM-FR-03: Edit Domain**
- [Edit] button on each row opens modal form with current values
- Domain ID field is read-only (disabled)
- Same form fields as Create (except Domain ID is disabled)
- Submit updates domain via POST to `/v2/domains/update?format=json&domain_id={id}`
- Success: close modal, reload list, show success toast
- Error: show error toast

**DOM-FR-05: JSON Example Dialog**
- [Show JSON Example] button opens nested modal
- Shows formatted JSON example with file_sources, sitepage_sources, list_sources
- [Copy to Form] button copies example to Sources JSON textarea
- [Close] button closes the nested modal

**DOM-FR-04: Delete Domain**
- [Delete] button on each row with confirmation dialog
- Confirm deletes domain via POST to `/v2/domains/delete?format=json&domain_id={id}`
- Success: reload list, show success toast
- Error: show error toast

## Implementation Guarantees

**DOM-IG-01:** Use `common_ui_functions_v2.py` for all UI generation (html_head, toast, modal, core_js, form_js)
**DOM-IG-02:** Domain data stored in folder-per-domain at `PERSISTENT_STORAGE_PATH/domains/{domain_id}/domain.json`
**DOM-IG-03:** All endpoints follow V2 router patterns with `format` parameter support (json, html, ui)
**DOM-IG-04:** JavaScript rendering follows same pattern as demorouter2.py

## Architecture and Design

**DD-DOM-01:** Folder-per-domain storage matching V1 structure
**DD-DOM-02:** Use common UI functions - no inline UI code duplication
**DD-DOM-03:** Router-specific JavaScript for domain forms and rendering

### Layer Diagram

```
+---------------------------------------------------------------------------+
|  Router (domains.py)                                                      |
|  +-> GET /v2/domains?format=ui         # Full UI page                     |
|  +-> GET /v2/domains?format=json       # List all domains                 |
|  +-> GET /v2/domains?format=html       # Table rows only                  |
|  +-> POST /v2/domains/create           # Create new domain                |
|  +-> POST /v2/domains/update           # Update existing domain           |
|  +-> POST /v2/domains/delete           # Delete domain                    |
+---------------------------------------------------------------------------+
|  Common UI Functions (common_ui_functions_v2.py)                          |
|  +-> generate_html_head()              # HTML head with CSS/JS            |
|  +-> generate_toast_container()        # Toast notification container     |
|  +-> generate_modal_structure()        # Modal dialog structure           |
|  +-> generate_core_js()                # Core JavaScript functions        |
|  +-> generate_form_js()                # Form handling JavaScript         |
|  +-> json_result()                     # JSON response wrapper            |
|  +-> html_result()                     # HTML response wrapper            |
+---------------------------------------------------------------------------+
|  Domain Functions (common_crawler_functions_v2.py)                        |
|  +-> load_domain()                       # Load single domain             |
|  +-> load_all_domains()                  # Load all domains               |
|  +-> save_domain_to_file()               # Save domain to disk            |
|  +-> delete_domain_folder()              # Delete domain folder           |
|  +-> validate_domain_config()            # Validate domain data           |
|  +-> domain_config_to_dict()             # Convert to dict                |
+---------------------------------------------------------------------------+
|  Storage                                                                  |
|  +-> PERSISTENT_STORAGE_PATH/domains/{domain_id}/domain.json                 |
+---------------------------------------------------------------------------+
```

## Key Mechanisms

### Domain Data File Format

Each domain stored at `PERSISTENT_STORAGE_PATH/domains/{domain_id}/domain.json`.

Note: `domain_id` is not stored in the JSON file - it is derived from the containing folder name at runtime.

```json
{
  "name": "Sales Documents",
  "description": "Sales team documentation and resources",
  "vector_store_name": "sales-vectorstore",
  "vector_store_id": "vs_abc123",
  "file_sources": [
    {
      "source_id": "source01",
      "site_url": "https://contoso.sharepoint.com/sites/sales",
      "sharepoint_url_part": "/Shared Documents",
      "filter": ""
    }
  ],
  "sitepage_sources": [],
  "list_sources": []
}
```

### Router-Specific JavaScript Functions

```javascript
// Domain ID validation (check for duplicates)
const existingDomainIds = [...];  // Populated from server
function validateDomainId(domainIdInput) { ... }

// JSON Example dialog
function showJsonExampleDialog(targetTextareaId) { ... }

// Load and render domains
async function refreshDomains() { ... }
function reloadItems() { refreshDomains(); }

// Render table
function renderAllDomains() { ... }
function renderDomainRow(domain) { ... }

// Forms
function showNewDomainForm() { ... }
function submitNewDomainForm(event) { ... }
function showEditDomainForm(domainId) { ... }
function submitEditDomainForm(event, domainId) { ... }

// Delete
function deleteDomain(domainId) { ... }
```

### JSON Example Content

```json
{
  "file_sources": [
    {
      "source_id": "source01",
      "site_url": "https://example.sharepoint.com/sites/MySite",
      "sharepoint_url_part": "/Shared Documents",
      "filter": ""
    }
  ],
  "sitepage_sources": [
    {
      "source_id": "source01",
      "site_url": "https://example.sharepoint.com/sites/MySite",
      "sharepoint_url_part": "/SitePages",
      "filter": "FSObjType eq 0"
    }
  ],
  "list_sources": [
    {
      "source_id": "source01",
      "site_url": "https://example.sharepoint.com/sites/MySite",
      "list_name": "My List",
      "filter": ""
    }
  ]
}
```

## Implementation Details

### File Structure

```
src/routers_v2/
  +-> domains.py                    # Router implementation
  +-> common_ui_functions_v2.py     # Shared UI functions (existing)
```

### Python Functions (domains.py)

```python
# Configuration
def set_config(app_config, prefix): ...
def get_persistent_storage_path() -> str: ...
def get_domains_file_path() -> str: ...

# Data operations
def load_domains() -> list[dict]: ...
def save_domains(domains: list[dict]) -> None: ...
def find_domain_by_id(domain_id: str) -> Optional[dict]: ...

# Router-specific JavaScript
def get_router_specific_js() -> str: ...

# UI page generation
def _generate_domains_ui_page(domains: list) -> str: ...

# Endpoints
@router.get("/")                    # L: List (ui/json/html)
@router.get("/get")                 # G: Get single domain
@router.post("/create")             # C: Create domain
@router.post("/update")             # U: Update domain
@router.post("/delete")             # D: Delete domain
```

### Endpoint Signatures

**List (GET /v2/domains)**
- Query params: `format` (ui|json|html)
- Returns: UI page, JSON array, or HTML table rows

**Get (GET /v2/domains/get)**
- Query params: `domain_id`, `format` (json|html)
- Returns: Single domain data

**Create (POST /v2/domains/create)**
- Query params: `format` (json)
- Body: `domain_id`, `name`, `description`, `vector_store_name`, `vector_store_id`, `sources_json`
- Validates: domain_id pattern, required fields, domain_id uniqueness, sources_json if provided
- Returns: JSON result with created domain

**Update (POST /v2/domains/update)**
- Query params: `domain_id`, `format` (json)
- Body: `name`, `description`, `vector_store_name`, `vector_store_id`, `sources_json`
- Returns: JSON result with updated domain

**Delete (POST /v2/domains/delete)**
- Query params: `domain_id`, `format` (json)
- Returns: JSON result with success/error

## Data Structures

### JSON Result Format

```json
{
  "ok": true,
  "error": "",
  "data": { ... }
}
```

### Domain Object (TypeScript-style for JS)

```typescript
interface FileSource {
  source_id: string;
  site_url: string;
  sharepoint_url_part: string;
  filter: string;
}

interface SitePageSource {
  source_id: string;
  site_url: string;
  sharepoint_url_part: string;
  filter: string;
}

interface ListSource {
  source_id: string;
  site_url: string;
  list_name: string;
  filter: string;
}

interface Domain {
  domain_id: string;
  name: string;
  description: string;
  vector_store_name: string;
  vector_store_id: string;
  file_sources: FileSource[];
  sitepage_sources: SitePageSource[];
  list_sources: ListSource[];
}
```

## Differences from demorouter2.py

| Feature | demorouter2 | domains |
|---------|-------------|---------|
| Bulk selection | Yes | No (for now) |
| Streaming endpoints | Yes (selftest, create_demo_items) | No (for now) |
| Console panel | Yes | No (for now) |
| Table columns | ID, Name, Version | Domain ID, Name, Vector Store Name, Vector Store ID |
| Primary key | item_id | domain_id |
| Storage | {storage}/demorouter2/items.json | {storage}/domains/{domain_id}/domain.json |

## Spec Changes

- 2025-12-18: Initial specification created
- 2025-12-18: Fixed TypeScript interface (added description, file_sources, sitepage_sources, list_sources)
- 2025-12-18: Updated storage to folder-per-domain structure matching V1
- 2025-12-18: Use dataclasses from common_crawler_functions_v2.py
