# V2 Sites Router UI Specification

**Doc ID**: SITE-SP02
**Goal**: Specify the interactive UI for the `/v2/sites?format=ui` endpoint.
**Target file**: `/src/routers_v2/sites.py`

**Depends on:**
- `_V2_SPEC_SITES.md [SITE-SP01]` for site data model and endpoint definitions
- `_V2_SPEC_ROUTERS.md [GLOB-SP01]` for endpoint design and SSE format
- `_V2_SPEC_COMMON_UI_FUNCTIONS.md` for UI generation functions

**Does not depend on:**
- Domains router UI (parallel implementation)

## Table of Contents

1. Scenario
2. Site Object Model
3. User Actions
4. UX Design
5. Functional Requirements
6. Implementation Guarantees
7. Architecture and Design
8. Key Mechanisms
9. Router-Specific JavaScript Functions
10. Differences from Domains Router

## Scenario

**Problem:** Administrators need a simple way to manage which SharePoint sites are registered with the middleware without programming skills.

**Solution:** A fully functional sites router UI that:
- Lists all sites with Edit, Delete, and scan actions
- Provides New Site creation via modal form
- Shows toast notifications for action feedback
- Follows the same look and feel as the domains router

**What we don't want:**
- Complex state management (use simple JavaScript)
- Memory caching of site data
- Active scan functionality (placeholders only for now)

## Site Object Model

**Site** (as displayed in UI table)
- `site_id` - Unique identifier (derived from folder name)
- `name` - Display name
- `site_url` - SharePoint site URL
- `file_scan_result` - Result of file scan (may be empty)
- `security_scan_result` - Result of security scan (may be empty)

**Site** (full data model - stored in site folder)
- `name` - Display name (required)
- `site_url` - SharePoint site URL (required, trailing slash stripped)
- `file_scan_result` - Scan result (optional, read-only in UI)
- `security_scan_result` - Scan result (optional, read-only in UI)

## User Actions

1. **View site list** - Page load: server returns HTML with pre-rendered table rows
2. **Reload sites** - Click [Reload] to fetch sites via JSON and re-render table
3. **New site** - Click [New Site] to open modal form, submit to create new site
4. **Edit site** - Click [Edit] on row to open modal form with current values, submit to update
5. **Delete site** - Click [Delete] on row with confirmation dialog
6. **Run selftest** - Click [Run Selftest] to test all CRUD operations

## UX Design

```
main page: /v2/sites?format=ui
+---------------------------------------------------------------------------------------------------------------------------------------+
| Sites (3)  [Reload]                                                                                                                   |
| Back to Main Page | Domains | Crawler | Jobs | Reports                                                                                |
|                                                                                                                                       |
| [New Site] [Run Selftest]                                                                                                             |
|                                                                                                                                       |
| +----------+----------------+----------------------------------------+----------+-------+---------------------------------------------+
| | Site ID  | Name           | Site URL                               | Security | Files | Actions                                     |
| +----------+----------------+----------------------------------------+----------+-------+---------------------------------------------+
| | site01   | Marketing Site | https://contoso.sharepoint.com/...     | -        | -     | [Edit] [Delete] [Security Scan] [File Scan] |
| | site02   | HR Portal      | https://contoso.sharepoint.com/...     | -        | -     | [Edit] [Delete] [Security Scan] [File Scan] |
| | site03   | Engineering    | https://contoso.sharepoint.com/...     | -        | -     | [Edit] [Delete] [Security Scan] [File Scan] |
| +----------+----------------+----------------------------------------+----------+-------+---------------------------------------------+
|                                                                                                                                       |
+---------------------------------------------------------------------------------------------------------------------------------------+

Toast Container (top-right, fixed position):
+-----------------------------------------------+
| Site Created | site01                    [x]  |
+-----------------------------------------------+

Modal (New Site):
+---------------------------------------------------------------+
|                                                          [x]  |
| New Site                                                      |
|                                                               |
| Site ID *                                                     |
| [__________________________________________________________]  |
|                                                               |
| Name *                                                        |
| [__________________________________________________________]  |
|                                                               |
| Site URL *                                                    |
| [https://contoso.sharepoint.com/sites/MySite_______________]  |
| (Trailing slash will be removed automatically)                |
|                                                               |
|                                         [OK] [Cancel]         |
+---------------------------------------------------------------+

Modal (Edit Site):
+---------------------------------------------------------------+
|                                                          [x]  |
| Edit Site: site01                                             |
|                                                               |
| Site ID                                                       |
| [site01__________________________________________________]    |
| (Change to rename the site)                                   |
|                                                               |
| Name *                                                        |
| [Marketing Site__________________________________________]    |
|                                                               |
| Site URL *                                                    |
| [https://contoso.sharepoint.com/sites/Marketing__________]    |
| (Trailing slash will be removed automatically)                |
|                                                               |
| File Scan Result (read-only)                                  |
| [____________________________________________________________]|
|                                                               |
| Security Scan Result (read-only)                              |
| [____________________________________________________________]|
|                                                               |
|                                         [OK] [Cancel]         |
+---------------------------------------------------------------+
```

## Functional Requirements

**SITE-UI-FR-01: Site List Display**
- Display all sites in a table with columns: Site ID, Name, Site URL, Security, Files, Actions
- Show site count in page header (e.g., "Sites (3)")
- Empty state: "No sites found." message when list is empty

**SITE-UI-FR-02: New Site Form**
- [New Site] button opens modal form
- Form fields:
  - Site ID * (required, pattern: `[a-zA-Z0-9_-]+`, validated for uniqueness)
  - Name * (required)
  - Site URL * (required, placeholder shows example URL)
- Help text: "Trailing slash will be removed automatically"
- Submit creates site via POST to `/v2/sites/create?format=json`
- Success: close modal, reload list, show success toast
- Error: show error in modal footer

**SITE-UI-FR-03: Edit Site Form**
- [Edit] button on each row opens modal form with current values
- Site ID field is editable (supports rename per DD-E014)
- Hidden `source_site_id` field stores original ID for comparison
- File Scan Result and Security Scan Result shown as read-only fields
- Submit updates site via PUT to `/v2/sites/update?site_id={source_id}`
- If Site ID changed: includes `site_id` in body to trigger rename
- Success: close modal, reload list, show success toast
- Error: show error in modal footer, keep modal open

**SITE-UI-FR-04: Delete Site**
- [Delete] button on each row with confirmation dialog
- Confirm deletes site via DELETE to `/v2/sites/delete?site_id={id}&format=json`
- Success: reload list, show success toast
- Error: show error toast

**SITE-UI-FR-05: Scan Buttons**
- [File Scan] button - grey/disabled appearance, shows toast "File Scan not yet implemented"
- [Security Scan] button - opens security scan dialog with scope and options

**SITE-UI-FR-07: Security Column Display**
- If no security scan performed: shows "-"
- If security scan performed, Security column displays:
  - Line 1: Summary stats (e.g., "7 groups, 10 users, 2 subsites, 13 individual permissions")
  - Line 2: `YYYY-MM-DD HH:MM - View Results | Download Zip`
- "View Results" link opens modal with full report.json content (via `/v2/reports/get?format=json`)
- "Download Zip" link downloads the report archive (via `/v2/reports/download`)
- Date format: UTC timestamp in "YYYY-MM-DD HH:MM" format

**SITE-UI-FR-08: View Results Modal**
- Modal header displays: `Result (OK|FAIL) - '[title]'`
- Below title: clickable endpoint URL link (e.g., `/v2/reports/get?report_id=...&format=json`)
- Link opens in new tab for direct API access
- Modal body: formatted JSON of full report.json content
- Modal footer: OK button to close

**SITE-UI-FR-06: Selftest**
- [Run Selftest] button in toolbar
- Connects to `/v2/sites/selftest?format=stream`
- Shows console panel with streaming output
- On completion: shows result in modal or toast

## Implementation Guarantees

**SITE-UI-IG-01:** Use `common_ui_functions_v2.py` for all UI generation (generate_ui_page, etc.)
**SITE-UI-IG-02:** Site data stored in folder-per-site at `PERSISTENT_STORAGE_PATH/sites/{site_id}/site.json`
**SITE-UI-IG-03:** All endpoints follow V2 router patterns with `format` parameter support
**SITE-UI-IG-04:** JavaScript rendering follows same pattern as domains.py
**SITE-UI-IG-05:** No memory caching - reload from disk on each request

## Architecture and Design

**SITE-UI-DD-01:** Folder-per-site storage matching domains structure
**SITE-UI-DD-02:** Use common UI functions - no inline UI code duplication
**SITE-UI-DD-03:** Router-specific JavaScript for site forms

### Layer Diagram

```
+---------------------------------------------------------------------------+
|  Router (sites.py)                                                        |
|  +-> GET /v2/sites?format=ui         # Full UI page                       |
|  +-> GET /v2/sites?format=json       # List all sites                     |
|  +-> GET /v2/sites?format=html       # Table rows only                    |
|  +-> GET /v2/sites/get               # Get single site                    |
|  +-> POST /v2/sites/create           # Create new site                    |
|  +-> PUT /v2/sites/update            # Update existing site               |
|  +-> DELETE /v2/sites/delete         # Delete site                        |
|  +-> GET /v2/sites/selftest          # Selftest (stream)                  |
+---------------------------------------------------------------------------+
|  Common UI Functions (common_ui_functions_v2.py)                          |
|  +-> generate_ui_page()              # Full UI page with table            |
|  +-> generate_router_docs_page()     # Router documentation               |
|  +-> generate_endpoint_docs()        # Endpoint documentation             |
|  +-> json_result()                   # JSON response wrapper              |
|  +-> html_result()                   # HTML response wrapper              |
+---------------------------------------------------------------------------+
|  Site Functions (sites.py - inline or common_site_functions_v2.py)        |
|  +-> load_site()                     # Load single site                   |
|  +-> load_all_sites()                # Load all sites                     |
|  +-> save_site_to_file()             # Save site to disk                  |
|  +-> delete_site_folder()            # Delete site folder                 |
|  +-> rename_site()                   # Rename site folder                 |
|  +-> validate_site_config()          # Validate site data                 |
|  +-> site_config_to_dict()           # Convert to dict                    |
+---------------------------------------------------------------------------+
|  Storage                                                                  |
|  +-> PERSISTENT_STORAGE_PATH/sites/{site_id}/site.json                    |
+---------------------------------------------------------------------------+
```

## Key Mechanisms

### Site Data File Format

Each site stored at `PERSISTENT_STORAGE_PATH/sites/{site_id}/site.json`.

Note: `site_id` is not stored in the JSON file - it is derived from the containing folder name at runtime.

```json
{
  "name": "Marketing Site",
  "site_url": "https://contoso.sharepoint.com/sites/Marketing",
  "file_scan_result": "",
  "security_scan_result": ""
}
```

### Table Columns Configuration

```python
columns = [
  {"field": "site_id", "header": "Site ID"},
  {"field": "name", "header": "Name", "default": "-"},
  {"field": "site_url", "header": "Site URL", "default": "-"},
  {"field": "file_scan_result", "header": "Files", "default": "-"},
  {"field": "security_scan_result", "header": "Security", "default": "-"},
  {
    "field": "actions",
    "header": "Actions",
    "buttons": [
      {"text": "Edit", "onclick": "showEditSiteForm('{itemId}')", "class": "btn-small"},
      {
        "text": "Delete",
        "data_url": "/v2/sites/delete?site_id={itemId}",
        "data_method": "DELETE",
        "data_format": "json",
        "confirm_message": "Delete site '{itemId}'?",
        "class": "btn-small btn-delete"
      },
      {"text": "File Scan", "onclick": "showNotImplemented('File Scan')", "class": "btn-small btn-disabled"},
      {"text": "Security Scan", "onclick": "showNotImplemented('Security Scan')", "class": "btn-small btn-disabled"}
    ]
  }
]
```

### Toolbar Buttons Configuration

```python
toolbar_buttons = [
  {"text": "New Site", "onclick": "showNewSiteForm()", "class": "btn-primary"},
  {
    "text": "Run Selftest",
    "data_url": "/v2/sites/selftest?format=stream",
    "data_format": "stream",
    "data_show_result": "modal",
    "data_reload_on_finish": "true",
    "class": "btn-primary"
  }
]
```

## Router-Specific JavaScript Functions

```javascript
// ============================================
// ROUTER-SPECIFIC FORMS - SITES
// ============================================

const SITE_MODAL_WIDTH = '600px';

function showNotImplemented(feature) {
  showToast('Not Implemented', `${feature} is not yet implemented.`, 'info');
}

function showNewSiteForm() {
  // Opens modal with Site ID, Name, Site URL fields
  // Submit calls POST /v2/sites/create
}

function submitNewSiteForm(event) {
  // Validates required fields
  // Calls callEndpoint() with form data
}

async function showEditSiteForm(siteId) {
  // Fetches site data via GET /v2/sites/get?site_id={siteId}
  // Opens modal with editable fields
  // Shows read-only scan result fields
}

function submitEditSiteForm(event) {
  // Handles ID change detection for rename
  // Calls PUT /v2/sites/update?site_id={sourceSiteId}
}
```

### Edit Form with ID Change Support

Follows the same pattern as domains.py per DD-E014:

```html
<form id="edit-site-form" onsubmit="return submitEditSiteForm(event)">
  <input type="hidden" name="source_site_id" value="${siteId}">
  <div class="form-group">
    <label>Site ID</label>
    <input type="text" name="site_id" value="${siteId}">
    <small style="color: #666;">Change to rename the site</small>
  </div>
  <!-- ... other fields ... -->
  <div class="form-group">
    <label>File Scan Result (read-only)</label>
    <input type="text" name="file_scan_result" value="${site.file_scan_result}" readonly disabled>
  </div>
  <div class="form-group">
    <label>Security Scan Result (read-only)</label>
    <input type="text" name="security_scan_result" value="${site.security_scan_result}" readonly disabled>
  </div>
</form>
```

## Differences from Domains Router

| Aspect | Domains | Sites |
|--------|---------|-------|
| Table columns | Domain ID, Name, VS Name, VS ID | Site ID, Name, Site URL, Files, Security |
| Primary key | domain_id | site_id |
| Storage | domains/{domain_id}/domain.json | sites/{site_id}/site.json |
| Action buttons | Crawl, Edit, Delete | Edit, Delete, File Scan*, Security Scan* |
| Toolbar buttons | New Domain, Run Selftest | New Site, Run Selftest |
| Form complexity | Complex (sources JSON) | Simple (3 editable fields) |
| Read-only fields | None | file_scan_result, security_scan_result |
| Modal width | 900px | 600px |

*Placeholder buttons - not yet implemented

## Document History

**[2026-02-03 09:20]**
- Initial UI specification created

