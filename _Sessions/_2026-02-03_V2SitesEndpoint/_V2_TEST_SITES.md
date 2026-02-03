# V2 Sites Router Test Plan

**Doc ID**: SITE-TP01
**Goal**: Test plan for the V2 sites router.
**Target file**: `/src/routers_v2/sites.py`

**Depends on:**
- `_V2_SPEC_SITES.md [SITE-SP01]` for functional requirements
- `_V2_IMPL_SITES.md [SITE-IP01]` for implementation details

## MUST-NOT-FORGET

- All LCGUD formats must be tested (L: jhu, C: jh, G: jh, U: jh, D: jh)
- Selftest result schema: `{ok, error, data: {passed, failed, passed_tests, failed_tests}}`
- Test both success and error cases for each endpoint
- Verify read-only fields cannot be modified via Update

## Test Categories

1. Unit Tests (Python)
2. API Tests (HTTP)
3. UI Tests (Browser/Playwright)
4. Selftest Verification

## Test Cases

### SITE-TP01-TC-01: List Endpoint - Bare GET

**Endpoint**: `GET /v2/sites`
**Expected**: Router documentation HTML
**Verify**: Response contains endpoint list

### SITE-TP01-TC-02: List Endpoint - JSON Format

**Endpoint**: `GET /v2/sites?format=json`
**Expected**: `{"ok": true, "error": "", "data": [...]}`
**Verify**: Response is valid JSON with site objects

### SITE-TP01-TC-03: List Endpoint - UI Format

**Endpoint**: `GET /v2/sites?format=ui`
**Expected**: Interactive HTML page
**Verify**: Contains table, toolbar buttons, JavaScript

### SITE-TP01-TC-03b: List Endpoint - HTML Format

**Endpoint**: `GET /v2/sites?format=html`
**Expected**: HTML table rows only
**Verify**: Returns table without page wrapper

### SITE-TP01-TC-04: Get Endpoint - Valid Site

**Endpoint**: `GET /v2/sites/get?site_id={valid_id}&format=json`
**Expected**: `{"ok": true, "error": "", "data": {...}}`
**Verify**: Returns site with all fields

### SITE-TP01-TC-05: Get Endpoint - Invalid Site

**Endpoint**: `GET /v2/sites/get?site_id=nonexistent&format=json`
**Expected**: `{"ok": false, "error": "Site 'nonexistent' not found.", "data": {}}`
**Status**: 404

### SITE-TP01-TC-06: Create Endpoint - Valid Data

**Endpoint**: `POST /v2/sites/create?format=json`
**Body**: `{"site_id": "test01", "name": "Test Site", "site_url": "https://test.sharepoint.com/sites/Test"}`
**Expected**: `{"ok": true, "error": "", "data": {...}}`
**Verify**: Site folder and site.json created

### SITE-TP01-TC-07: Create Endpoint - Duplicate ID

**Endpoint**: `POST /v2/sites/create?format=json`
**Body**: `{"site_id": "existing", ...}`
**Expected**: `{"ok": false, "error": "Site 'existing' already exists.", "data": {}}`
**Status**: 400

### SITE-TP01-TC-08: Create Endpoint - Missing Fields

**Endpoint**: `POST /v2/sites/create?format=json`
**Body**: `{"site_id": "test"}`
**Expected**: `{"ok": false, "error": "Missing required field: name", "data": {}}`
**Status**: 400

### SITE-TP01-TC-09: Create Endpoint - URL Normalization

**Endpoint**: `POST /v2/sites/create?format=json`
**Body**: `{"site_id": "test", "name": "Test", "site_url": "https://test.com/"}`
**Expected**: Site created with `site_url: "https://test.com"` (no trailing slash)

### SITE-TP01-TC-09b: Create Endpoint - HTML Format

**Endpoint**: `POST /v2/sites/create?format=html`
**Body**: `{"site_id": "test", "name": "Test", "site_url": "https://test.com"}`
**Expected**: HTML response with created site

### SITE-TP01-TC-09c: Create Endpoint - Invalid Site ID Pattern

**Endpoint**: `POST /v2/sites/create?format=json`
**Body**: `{"site_id": "invalid id!", "name": "Test", "site_url": "https://test.com"}`
**Expected**: `{"ok": false, "error": "Site ID must match pattern [a-zA-Z0-9_-]+", "data": {}}`
**Status**: 400

### SITE-TP01-TC-10: Update Endpoint - Valid Update

**Endpoint**: `PUT /v2/sites/update?site_id=test01&format=json`
**Body**: `{"name": "Updated Name"}`
**Expected**: `{"ok": true, "error": "", "data": {...}}`
**Verify**: Name updated, other fields preserved

### SITE-TP01-TC-11: Update Endpoint - ID Rename

**Endpoint**: `PUT /v2/sites/update?site_id=old_id&format=json`
**Body**: `{"site_id": "new_id", "name": "Same Name"}`
**Expected**: Site renamed, folder changed
**Verify**: old_id folder gone, new_id folder exists

### SITE-TP01-TC-12: Update Endpoint - Rename Collision

**Endpoint**: `PUT /v2/sites/update?site_id=site_a&format=json`
**Body**: `{"site_id": "site_b"}` (site_b already exists)
**Expected**: `{"ok": false, "error": "Site 'site_b' already exists.", "data": {}}`
**Status**: 400

### SITE-TP01-TC-13: Update Endpoint - Preserve Read-Only Fields

**Endpoint**: `PUT /v2/sites/update?site_id=test&format=json`
**Body**: `{"file_scan_result": "hacked"}`
**Expected**: `file_scan_result` NOT changed (read-only)

### SITE-TP01-TC-13b: Update Endpoint - HTML Format

**Endpoint**: `PUT /v2/sites/update?site_id=test&format=html`
**Body**: `{"name": "Updated"}`
**Expected**: HTML response with updated site

### SITE-TP01-TC-14: Delete Endpoint - Valid Site

**Endpoint**: `DELETE /v2/sites/delete?site_id=test01&format=json`
**Expected**: `{"ok": true, "error": "", "data": {...}}`
**Verify**: Returns deleted site data, folder removed

### SITE-TP01-TC-15: Delete Endpoint - Invalid Site

**Endpoint**: `DELETE /v2/sites/delete?site_id=nonexistent&format=json`
**Expected**: `{"ok": false, "error": "Site 'nonexistent' not found.", "data": {}}`
**Status**: 404

### SITE-TP01-TC-15b: Delete Endpoint - HTML Format

**Endpoint**: `DELETE /v2/sites/delete?site_id=test01&format=html`
**Expected**: HTML response with deleted site data

### SITE-TP01-TC-16: Selftest Endpoint

**Endpoint**: `GET /v2/sites/selftest?format=stream`
**Expected**: SSE stream with test results
**Verify**: All tests pass, end_json contains success summary

### SITE-TP01-TC-17: UI - New Site Form

**Action**: Click [New Site] button
**Expected**: Modal opens with form fields
**Verify**: Site ID, Name, Site URL fields visible

### SITE-TP01-TC-18: UI - Edit Site Form

**Action**: Click [Edit] on site row
**Expected**: Modal opens with current values
**Verify**: Read-only scan fields visible but disabled

### SITE-TP01-TC-19: UI - Delete Confirmation

**Action**: Click [Delete] on site row
**Expected**: Confirmation dialog appears
**Verify**: Cancel returns to list, Confirm deletes

### SITE-TP01-TC-20: UI - Scan Buttons Placeholder

**Action**: Click [File Scan] or [Security Scan]
**Expected**: Toast "... not yet implemented"
**Verify**: No action performed, toast shown

## Selftest Verification Script

Run via API or browser:
```
GET /v2/sites/selftest?format=stream
```

Expected output (SSE):
```
event: start_json
data: {"job_id": "jb_X", "state": "running", ...}

event: log
data: [ 1 / 6 ] Creating test site '_test_abc123'...

event: log
data:   OK.

event: log
data: [ 2 / 6 ] Getting test site...

event: log
data:   OK.

event: log
data: [ 3 / 6 ] Updating test site...

event: log
data:   OK.

event: log
data: [ 4 / 6 ] Renaming test site...

event: log
data:   OK.

event: log
data: [ 5 / 6 ] Deleting test site...

event: log
data:   OK.

event: log
data: [ 6 / 6 ] Verifying deletion...

event: log
data:   OK.

event: end_json
data: {"job_id": "jb_X", "state": "completed", "result": {"ok": true, "error": "", "data": {"passed": 6, "failed": 0, "passed_tests": [...], "failed_tests": []}}}
```

## Document History

**[2026-02-03 09:40]**
- Added MUST-NOT-FORGET section
- Added TC-03b, TC-09b, TC-09c, TC-13b, TC-15b for html format coverage
- Added TC-09c for invalid site_id pattern test
- Fixed selftest result schema to include passed_tests, failed_tests arrays

**[2026-02-03 09:35]**
- Initial test plan created

