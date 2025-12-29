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
6. **Crawl domain** - Click [Crawl] on row to open crawl options modal, configure and start crawl job

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
| | DOMAIN01    | Sales Docs     | sales-vectorstore    | vs_abc123     | [Crawl] [Edit] [Delete] |
| | DOMAIN02    | HR Documents   | hr-vectorstore       | vs_def456     | [Crawl] [Edit] [Delete] |
| | DOMAIN03    | Engineering    | eng-vectorstore      | vs_ghi789     | [Crawl] [Edit] [Delete] |
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
| Domain ID                                                     |
| [DOMAIN01_____________________________________________]       |
| (Change to rename the domain)                                 |
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

Modal (Crawl Domain):
+---------------------------------------------------------------+
|                                                          [x]  |
| Crawl Domain                                                  |
|                                                               |
| Domain *                                                      |
| [DOMAIN01 - Sales Docs_______________________________] [v]    |
|                                                               |
| Step *                                                        |
| ( ) Full Crawl (download + process + embed)                   |
| ( ) Download Data Only                                        |
| ( ) Process Data Only                                         |
| ( ) Embed Data Only                                           |
|                                                               |
| Mode *                                                        |
| ( ) Full - Clear existing data first                          |
| ( ) Incremental - Only process changes                        |
|                                                               |
| Scope *                                                       |
| ( ) All Sources                                               |
| ( ) Files Only                                                |
| ( ) Lists Only                                                |
| ( ) Site Pages Only                                           |
|                                                               |
| Source Filter (optional, only when scope != all)              |
| [_________________________________________________________]   |
|                                                               |
| [ ] Run test without making changes (dry run)                 |
|                                                               |
| Endpoint Preview:                                             |
| +-----------------------------------------------------------+ |
| | /v2/crawler/crawl?domain_id=DOMAIN01&mode=full&scope=all  | |
| +-----------------------------------------------------------+ |
|                                                               |
|                                           [OK] [Cancel]       |
+---------------------------------------------------------------+
```

## Functional Requirements

**V2DM-FR-01: Domain List Display**
- Display all domains in a table with columns: Domain ID, Name, Vector Store Name, Vector Store ID, Actions
- Show domain count in page header
- Empty state message when no domains exist

**V2DM-FR-02: New Domain**
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

**V2DM-FR-03: Edit Domain**
- [Edit] button on each row opens modal form with current values
- Domain ID field is editable (supports rename per DD-E014 from `_V2_SPEC_ROUTERS.md`)
- Hidden `source_domain_id` field stores original ID for comparison
- Same form fields as Create
- Submit updates domain via PUT to `/v2/domains/update?domain_id={source_id}`
- If Domain ID changed: includes `domain_id` in body to trigger rename
- If Domain ID unchanged: omits `domain_id` from body (no rename)
- ID change flow per DD-E014:
  1. Query string `domain_id` = current identifier (source)
  2. Body `domain_id` = new identifier (target, only if changed)
  3. Backend validates: source exists (404 if not), target not exists (400 if collision)
  4. Backend renames domain folder from source to target
  5. Backend applies remaining body fields
- Success: close modal, reload list, show success toast
- Error: show error in modal footer, keep modal open

**V2DM-FR-05: JSON Example Dialog**
- [Show JSON Example] button opens nested modal
- Shows formatted JSON example with file_sources, sitepage_sources, list_sources
- [Copy to Form] button copies example to Sources JSON textarea
- [Close] button closes the nested modal

**V2DM-FR-04: Delete Domain**
- [Delete] button on each row with confirmation dialog
- Confirm deletes domain via POST to `/v2/domains/delete?format=json&domain_id={id}`
- Success: reload list, show success toast
- Error: show error toast

**V2DM-FR-06: Crawl Domain**
- [Crawl] button on each row opens crawl options modal
- Domain dropdown pre-selected with clicked row's domain
- Form fields:
  - Domain * (dropdown, pre-selected, can change to crawl different domain)
  - Step * (radio buttons):
    - `crawl` - Full Crawl (download + process + embed)
    - `download_data` - Download Data Only
    - `process_data` - Process Data Only
    - `embed_data` - Embed Data Only
  - Mode * (radio buttons):
    - `full` - Full - Clear existing data first
    - `incremental` - Incremental - Only process changes
  - Scope * (radio buttons):
    - `all` - All Sources
    - `files` - Files Only
    - `lists` - Lists Only
    - `sitepages` - Site Pages Only
  - Source Filter (text input, optional, enabled only when scope != all)
  - Dry Run checkbox - "Run test without making changes"
- Endpoint Preview: live-updated preview showing the endpoint URL to be called
- [OK] button:
  1. Shows console panel if hidden
  2. Clears console content
  3. Connects SSE stream to `/v2/crawler/{step}?domain_id={id}&mode={mode}&scope={scope}&source_id={source_id}&dry_run={dry_run}&format=stream`
  4. Closes modal
  5. Shows toast "Crawl started"
- [Cancel] closes modal without action

## Implementation Guarantees

**V2DM-IG-01:** Use `common_ui_functions_v2.py` for all UI generation (html_head, toast, modal, core_js, form_js)
**V2DM-IG-02:** Domain data stored in folder-per-domain at `PERSISTENT_STORAGE_PATH/domains/{domain_id}/domain.json`
**V2DM-IG-03:** All endpoints follow V2 router patterns with `format` parameter support (json, html, ui)
**V2DM-IG-04:** JavaScript rendering follows same pattern as demorouter2.py

## Architecture and Design

**V2DM-DD-01:** Folder-per-domain storage matching V1 structure
**V2DM-DD-02:** Use common UI functions - no inline UI code duplication
**V2DM-DD-03:** Router-specific JavaScript for domain forms and rendering

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
function submitEditDomainForm(event) { ... }

// Delete
function deleteDomain(domainId) { ... }

// Crawl
function showCrawlDomainForm(domainId) { ... }
function updateCrawlEndpointPreview() { ... }
function startCrawl(event) { ... }
```

### Edit Form with ID Change Support

Follows the same pattern as demorouter2.py per DD-E014:

**Edit form structure:**
```html
<form id="edit-domain-form" onsubmit="return submitEditDomainForm(event)">
  <input type="hidden" name="source_domain_id" value="${domainId}">
  <div class="form-group">
    <label>Domain ID</label>
    <input type="text" name="domain_id" value="${domainId}">
    <small style="color: #666;">Change to rename the domain</small>
  </div>
  <!-- ... other fields ... -->
</form>
```

**Submit logic:**
```javascript
function submitEditDomainForm(event) {
  event.preventDefault();
  const form = document.getElementById('edit-domain-form');
  const btn = document.querySelector('.modal-footer button[type="submit"]');
  const formData = new FormData(form);
  const data = {};
  
  const sourceDomainId = formData.get('source_domain_id');
  const targetDomainId = formData.get('domain_id');
  
  // Validate Domain ID not empty
  const domainIdInput = form.querySelector('input[name="domain_id"]');
  if (!targetDomainId || !targetDomainId.trim()) {
    showFieldError(domainIdInput, 'Domain ID cannot be empty');
    return;
  }
  clearFieldError(domainIdInput);
  
  // Build data object
  for (const [key, value] of formData.entries()) {
    if (key === 'source_domain_id') continue;  // Skip source ID
    if (key === 'domain_id') {
      // Only include if changed (triggers rename per DD-E014)
      if (value && value.trim() !== sourceDomainId) {
        data.domain_id = value.trim();
      }
    } else if (value !== undefined) {
      data[key] = value.trim();
    }
  }
  
  clearModalError();
  callEndpoint(btn, sourceDomainId, data);  // Uses source ID in URL
}
```

**Button data attributes:**
```html
<button type="submit" form="edit-domain-form" class="btn-primary"
        data-url="{router_prefix}/{router_name}/update?domain_id=${domainId}"
        data-method="PUT"
        data-format="json"
        data-reload-on-finish="true"
        data-close-on-success="true">OK</button>
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
@router.put("/update")              # U: Update domain
@router.delete("/delete")           # D: Delete domain (GET fallback)
@router.get("/selftest")            # Selftest (stream only)
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

**Delete (DELETE/GET /v2/domains/delete)**
- Query params: `domain_id`, `format` (json)
- Returns: JSON result with success/error

**Selftest (GET /v2/domains/selftest)**
- Query params: `format` (stream only)
- Streaming endpoint that tests all CRUD operations
- Returns: SSE stream with test results, end_json contains passed/failed counts

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

## Crawl Modal Mechanism

### Form Field Values

```
Step (step):
  crawl         -> /v2/crawler/crawl
  download_data -> /v2/crawler/download_data
  process_data  -> /v2/crawler/process_data
  embed_data    -> /v2/crawler/embed_data

Mode (mode):
  full        -> mode=full
  incremental -> mode=incremental

Scope (scope):
  all       -> scope=all (source_id disabled)
  files     -> scope=files
  lists     -> scope=lists
  sitepages -> scope=sitepages

Source Filter (source_id):
  Only enabled when scope != all
  If empty, omitted from URL

Dry Run (dry_run):
  Checked   -> dry_run=true
  Unchecked -> omitted (server default: false)
```

### Endpoint Preview Logic

```javascript
function updateCrawlEndpointPreview() {
  const form = document.getElementById('crawl-domain-form');
  const domainId = form.querySelector('[name="domain_id"]').value;
  const step = form.querySelector('[name="step"]:checked').value;
  const mode = form.querySelector('[name="mode"]:checked').value;
  const scope = form.querySelector('[name="scope"]:checked').value;
  const sourceId = form.querySelector('[name="source_id"]').value.trim();
  const dryRun = form.querySelector('[name="dry_run"]').checked;
  
  let url = `/v2/crawler/${step}?domain_id=${domainId}&mode=${mode}&scope=${scope}`;
  if (scope !== 'all' && sourceId) url += `&source_id=${sourceId}`;
  if (dryRun) url += '&dry_run=true';
  url += '&format=stream';
  
  document.getElementById('crawl-endpoint-preview').textContent = url;
}
```

### Start Crawl Action Flow

```
User clicks [OK]
  -> Build endpoint URL from form values
  -> closeModal()
  -> showConsole()
  -> clearConsole()
  -> startSSE(endpointUrl)
  -> showToast("Crawl started", "info")
  -> SSE events append to console
  -> On 'done' event: showToast(result summary)
```

### Source Filter Interaction

```
Scope radio changes:
  if (scope === 'all'):
    -> Disable source_id input
    -> Clear source_id value
  else:
    -> Enable source_id input
```

## Differences from demorouter2.py

- **Bulk selection**: demorouter2=Yes, domains=No
- **Streaming endpoints**: demorouter2=selftest+create_demo_items, domains=selftest+crawl
- **Console panel**: demorouter2=Yes, domains=Yes (initially hidden)
- **Table columns**: demorouter2=ID/Name/Version, domains=Domain ID/Name/Vector Store Name/Vector Store ID
- **Primary key**: demorouter2=item_id, domains=domain_id
- **Storage**: demorouter2={storage}/demorouter2/items.json, domains={storage}/domains/{domain_id}/domain.json
- **Crawl modal**: domains=Yes (calls /v2/crawler endpoints), demorouter2=No

## Spec Changes

- 2025-12-29: Added [Crawl] button feature (V2DM-FR-06) with modal dialog for crawl options, endpoint preview, and SSE streaming
- 2025-12-27: Updated spec to match implementation: added selftest endpoint, console panel (hidden), corrected DELETE method
- 2025-12-27: Added Domain ID rename support in Edit form (follows demorouter2 pattern per DD-E014)
- 2025-12-18: Initial specification created
- 2025-12-18: Fixed TypeScript interface (added description, file_sources, sitepage_sources, list_sources)
- 2025-12-18: Updated storage to folder-per-domain structure matching V1
- 2025-12-18: Use dataclasses from common_crawler_functions_v2.py
