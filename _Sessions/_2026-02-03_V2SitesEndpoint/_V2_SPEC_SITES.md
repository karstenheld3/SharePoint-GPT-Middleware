# V2 Sites Router Specification

**Doc ID**: SITE-SP01
**Goal**: Specify the V2 sites router for managing SharePoint sites registered with the middleware.
**Target file**: `/src/routers_v2/sites.py`

**Depends on:**
- `_V2_SPEC_ROUTERS.md [GLOB-SP01]` for endpoint design patterns and LCGUD conventions
- `_V2_SPEC_COMMON_UI_FUNCTIONS.md` for UI generation patterns

**Does not depend on:**
- V1 router implementations
- Domains router (parallel implementation, not dependent)

## MUST-NOT-FORGET

- Follow LCGUD notation exactly as specified in `_V2_SPEC_ROUTERS.md`
- ID derived from folder name, NOT stored in JSON (DD-E014 rename support)
- Selftest must return `{ok, error, data: {passed, failed, passed_tests, failed_tests}}`
- Bare GET returns self-documentation (DD-E001)
- Delete returns deleted object before deletion (DD-E017)

## Table of Contents

1. Scenario
2. Domain Object Model
3. Storage Structure
4. Endpoint Specification
5. Functional Requirements
6. Implementation Guarantees
7. Design Decisions

## Scenario

**Problem:** Administrators need to manage which SharePoint sites are accessible via the middleware. Currently there is no central registry of sites - they are only referenced within domain configurations.

**Solution:** A dedicated sites router that:
- Provides CRUD operations for SharePoint site registrations
- Stores site data in folder-per-site structure
- Supports future scan operations (file scan, security scan)
- Follows the same patterns as the domains router

**What we don't want:**
- Memory caching of sites (always read from disk)
- Complex relationships to domains (sites are independent)
- Automatic site discovery (manual registration only)

## Domain Object Model

**Site** (as stored in `site.json`)

Note: `site_id` is NOT stored in the JSON file. It is derived from the containing folder name at runtime.

- `name` - Display name for the site (required, string)
- `site_url` - SharePoint site URL (required, string, trailing slash stripped)
- `file_scan_result` - Result of file scan operation (optional, string, read-only in UI)
- `security_scan_result` - Result of security scan operation (optional, string, read-only in UI)

**Site** (as returned in API responses)

- `site_id` - Unique identifier derived from folder name (string)
- `name` - Display name (string)
- `site_url` - SharePoint site URL (string)
- `file_scan_result` - Scan result or empty string (string)
- `security_scan_result` - Scan result or empty string (string)

## Storage Structure

```
PERSISTENT_STORAGE_PATH/
├── sites/                    # Sites root folder
│   ├── site01/               # Site folder (site_id = "site01")
│   │   └── site.json         # Site configuration
│   ├── site02/
│   │   └── site.json
│   └── ...
```

### site.json Schema

```json
{
  "name": "Marketing Site",
  "site_url": "https://contoso.sharepoint.com/sites/Marketing",
  "file_scan_result": "",
  "security_scan_result": ""
}
```

**Validation Rules:**
- `name` - Required, non-empty string
- `site_url` - Required, non-empty string, must start with `https://`
- `site_url` - Trailing slash automatically stripped on create/update
- `file_scan_result` - Optional, defaults to empty string
- `security_scan_result` - Optional, defaults to empty string

## Endpoint Specification

**Router prefix:** `/v2/sites`
**LCGUD notation:** L(jhu)C(jh)G(jh)U(jh)D(jh): `/v2/sites` - SharePoint sites registered with the middleware
- Exception: no `dry_run` flag needed here (same as domains)
- `PUT /v2/sites/update?site_id={id}` supports rename via `site_id` in body (per DD-E014)
- X(s): `/v2/sites/selftest` - Self-test for sites CRUD operations
  - Only supports `format=stream`
  - Tests: create, get, update, rename (ID change), delete, verify deleted
  - Result: `{ok, error, data: {passed, failed, passed_tests, failed_tests}}`

### Endpoints Overview

| Endpoint | Method | Description | Formats |
|----------|--------|-------------|---------|
| `/v2/sites` | GET | List all sites or self-documentation | json, html, ui |
| `/v2/sites/get` | GET | Get single site | json, html |
| `/v2/sites/create` | POST | Create new site | json, html |
| `/v2/sites/update` | PUT | Update existing site | json, html |
| `/v2/sites/delete` | DELETE/GET | Delete site | json, html |
| `/v2/sites/selftest` | GET | Run self-test | stream |

### L - List (GET /v2/sites)

**Bare GET (no params):** Returns self-documentation (HTML)

**With format param:**
- `format=json` - Returns `{"ok": true, "error": "", "data": [...]}`
- `format=html` - Returns HTML table
- `format=ui` - Returns interactive UI page

### G - Get (GET /v2/sites/get)

**Bare GET (no params):** Returns endpoint documentation (plain text)

**Query params:**
- `site_id` (required) - Site identifier
- `format` (optional) - json (default), html

**Responses:**
- 200: `{"ok": true, "error": "", "data": {...}}`
- 404: `{"ok": false, "error": "Site 'xyz' not found.", "data": {}}`

### C - Create (POST /v2/sites/create)

**Query params:**
- `format` (optional) - json (default)

**Body (JSON or form data):**
- `site_id` (required) - Unique identifier, pattern: `[a-zA-Z0-9_-]+`
- `name` (required) - Display name
- `site_url` (required) - SharePoint site URL

**Validation:**
- `site_id` must match pattern `[a-zA-Z0-9_-]+`
- `site_id` must not already exist
- `name` must be non-empty
- `site_url` must be non-empty and start with `https://`

**Processing:**
- Strip trailing slash from `site_url`
- Create folder `PERSISTENT_STORAGE_PATH/sites/{site_id}/`
- Write `site.json` with provided data

**Responses:**
- 200: `{"ok": true, "error": "", "data": {...}}`
- 400: `{"ok": false, "error": "Site 'xyz' already exists.", "data": {}}`

### U - Update (PUT /v2/sites/update)

**Query params:**
- `site_id` (required) - Current site identifier
- `format` (optional) - json (default)

**Body (JSON or form data):**
- `site_id` (optional) - New identifier (triggers rename if different from query param)
- `name` (optional) - New display name
- `site_url` (optional) - New SharePoint URL

**ID Change Flow (per DD-E014):**
1. Query string `site_id` = current identifier
2. Body `site_id` = new identifier (if rename desired)
3. If body `site_id` differs from query `site_id`:
   - Validate current exists (404 if not)
   - Validate new does not exist (400 if collision)
   - Rename folder from current to new
4. Apply remaining body fields

**Processing:**
- Strip trailing slash from `site_url` if provided
- Preserve `file_scan_result` and `security_scan_result` (read-only)

**Responses:**
- 200: `{"ok": true, "error": "", "data": {...}}`
- 404: `{"ok": false, "error": "Site 'xyz' not found.", "data": {}}`

### D - Delete (DELETE/GET /v2/sites/delete)

**Query params:**
- `site_id` (required) - Site identifier
- `format` (optional) - json (default)

**Processing:**
- Delete entire folder `PERSISTENT_STORAGE_PATH/sites/{site_id}/`

**Responses:**
- 200: `{"ok": true, "error": "", "data": {...}}` (returns deleted site data)
- 404: `{"ok": false, "error": "Site 'xyz' not found.", "data": {}}`

### Selftest (GET /v2/sites/selftest)

**Query params:**
- `format` (required) - stream

**Tests performed:**
1. Create test site with unique ID
2. Get created site
3. Update site name
4. Rename site (ID change)
5. Delete site
6. Verify site deleted

**Response:** SSE stream with test progress and results

## Functional Requirements

**SITE-FR-01: Site List Display**
- Display all sites in a table with columns: Site ID, Name, Site URL, Files, Security, Actions
- Show site count in page header
- Empty state message when no sites exist

**SITE-FR-02: New Site**
- [New Site] button opens modal form
- Form fields: Site ID, Name, Site URL (all required)
- Validation on submit
- Success: close modal, reload list, show toast
- Error: show error in modal

**SITE-FR-03: Edit Site**
- [Edit] button opens modal with current values
- Site ID field editable (supports rename)
- Files and Security fields shown as read-only
- Success: close modal, reload list, show toast

**SITE-FR-04: Delete Site**
- [Delete] button with confirmation dialog
- Success: reload list, show toast

**SITE-FR-05: Scan Buttons (Placeholder)**
- [File Scan] button - grey/disabled, no action
- [Security Scan] button - grey/disabled, no action
- Both buttons are placeholders for future functionality

**SITE-FR-06: URL Normalization**
- Trailing slash automatically removed from site_url on create/update
- Example: `https://contoso.sharepoint.com/sites/Marketing/` becomes `https://contoso.sharepoint.com/sites/Marketing`

**SITE-FR-07: Selftest**
- [Run Selftest] button starts streaming test
- Tests all CRUD operations
- Reports passed/failed counts

## Implementation Guarantees

**SITE-IG-01:** Use `common_ui_functions_v2.py` for all UI generation
**SITE-IG-02:** Site data stored in folder-per-site at `PERSISTENT_STORAGE_PATH/sites/{site_id}/site.json`
**SITE-IG-03:** All endpoints follow V2 router patterns with `format` parameter support
**SITE-IG-04:** No memory caching - always read from disk
**SITE-IG-05:** `site_id` derived from folder name, not stored in JSON

## Design Decisions

**SITE-DD-01:** Folder-per-site storage (matches domains pattern)
**SITE-DD-02:** Site ID from folder name (matches domains pattern, enables rename via folder rename)
**SITE-DD-03:** Scan results are read-only in UI (populated by future scan operations)
**SITE-DD-04:** No relationship to domains (sites are independent entities)
**SITE-DD-05:** Trailing slash stripping for URL consistency

## Document History

**[2026-02-03 09:25]**
- Restored C(jh), U(jh), D(jh) per user feedback - all support json+html
- Clarified exception note: same as domains

**[2026-02-03 09:20]**
- Added MUST-NOT-FORGET section per write-documents skill
- Added selftest specification with result schema (X(s))
- Added exception note (no dry_run needed)
- Added DD-E014 rename support reference

**[2026-02-03 09:15]**
- Initial specification created

