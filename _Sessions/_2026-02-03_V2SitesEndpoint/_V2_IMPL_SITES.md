# V2 Sites Router Implementation Plan

**Doc ID**: SITE-IP01
**Goal**: Implementation plan for the V2 sites router.
**Target file**: `/src/routers_v2/sites.py`

**Depends on:**
- `_V2_SPEC_SITES.md [SITE-SP01]` for functional requirements
- `_V2_SPEC_SITES_UI.md [SITE-SP02]` for UI requirements

## MUST-NOT-FORGET

- All CUD endpoints support both json AND html formats (per LCGUD notation)
- Selftest must return `{ok, error, data: {passed, failed, passed_tests, failed_tests}}`
- ID derived from folder name, NOT stored in JSON
- Delete returns deleted object BEFORE deletion (DD-E017)
- Preserve read-only fields (file_scan_result, security_scan_result) on update

## Table of Contents

1. Implementation Steps
2. File Changes Summary
3. Code Patterns
4. Verification Checklist

## Implementation Steps

### SITE-IP01-IS-01: Add hardcoded config constants

**File**: `src/hardcoded_config.py`

Add to `CrawlerHardcodedConfig` dataclass:
```python
PERSISTENT_STORAGE_PATH_SITES_SUBFOLDER: str
SITE_JSON: str
```

Add to `CRAWLER_HARDCODED_CONFIG` instance:
```python
,PERSISTENT_STORAGE_PATH_SITES_SUBFOLDER="sites"
,SITE_JSON="site.json"
```

### SITE-IP01-IS-02: Create sites.py router file

**File**: `src/routers_v2/sites.py`

Structure (following domains.py pattern):
1. Imports
2. Router configuration
3. Helper functions (load_site, load_all_sites, save_site_to_file, etc.)
4. Router-specific JavaScript
5. Endpoints:
   - `GET /sites` - List/UI/docs
   - `GET /sites/get` - Get single site
   - `POST /sites/create` - Create site
   - `PUT /sites/update` - Update site
   - `DELETE /sites/delete` - Delete site
   - `GET /sites/selftest` - Run selftest

### SITE-IP01-IS-03: Implement Site dataclass and helper functions

```python
@dataclass
class SiteConfig:
  site_id: str
  name: str
  site_url: str
  file_scan_result: str = ""
  security_scan_result: str = ""

def load_site(storage_path: str, site_id: str, logger=None) -> SiteConfig:
  """Load single site from disk."""

def load_all_sites(storage_path: str, logger=None) -> list[SiteConfig]:
  """Load all sites from disk."""

def save_site_to_file(storage_path: str, site: SiteConfig, logger=None) -> None:
  """Save site to disk."""

def delete_site_folder(storage_path: str, site_id: str, logger=None) -> bool:
  """Delete site folder."""

def rename_site(storage_path: str, old_id: str, new_id: str, logger=None) -> bool:
  """Rename site folder."""

def validate_site_config(data: dict) -> tuple[bool, str]:
  """Validate site data. Returns (is_valid, error_message)."""

def site_config_to_dict(site: SiteConfig) -> dict:
  """Convert SiteConfig to dict for JSON serialization."""

def normalize_site_url(url: str) -> str:
  """Strip trailing slash from URL."""
```

### SITE-IP01-IS-04: Implement router-specific JavaScript

```javascript
const SITE_MODAL_WIDTH = '600px';

function showNotImplemented(feature) {
  showToast('Not Implemented', `${feature} is not yet implemented.`, 'info');
}

function showNewSiteForm() { ... }
function submitNewSiteForm(event) { ... }
async function showEditSiteForm(siteId) { ... }
function submitEditSiteForm(event) { ... }
```

### SITE-IP01-IS-05: Implement List endpoint (GET /sites)

- Bare GET: Return router documentation HTML
- `format=json`: Return sites list as JSON
- `format=html`: Return HTML table
- `format=ui`: Return interactive UI page using generate_ui_page()

Table columns:
- site_id, name, site_url, file_scan_result, security_scan_result, actions

Toolbar buttons:
- [New Site] - onclick: showNewSiteForm()
- [Run Selftest] - streaming endpoint

### SITE-IP01-IS-06: Implement Get endpoint (GET /sites/get)

- Bare GET: Return endpoint documentation
- With `site_id`: Return site data
- Formats: json, html

### SITE-IP01-IS-07: Implement Create endpoint (POST /sites/create)

- Validate required fields: site_id, name, site_url
- Check site_id doesn't exist
- Normalize site_url (strip trailing slash)
- Create folder and save site.json
- Formats: json (default), html

### SITE-IP01-IS-08: Implement Update endpoint (PUT /sites/update)

- Get site_id from query param
- Check site exists
- Handle ID change (rename) per DD-E014
- Normalize site_url if provided
- Preserve read-only fields (file_scan_result, security_scan_result)
- Formats: json (default), html

### SITE-IP01-IS-09: Implement Delete endpoint (DELETE/GET /sites/delete)

- Get site_id from query param
- Load site data BEFORE deletion (for return value per DD-E017)
- Delete folder
- Formats: json (default), html

### SITE-IP01-IS-10: Implement Selftest endpoint (GET /sites/selftest)

- Create StreamingJobWriter
- Test create, get, update, rename, delete, verify deleted
- Return SSE stream with results
- Result schema: `{ok, error, data: {passed, failed, passed_tests, failed_tests}}`

### SITE-IP01-IS-11: Register router in app.py

**File**: `src/app.py`

1. Add import at line 15:
```python
from routers_v2 import ... sites as sites_v2
```

2. Add router registration after domains_v2 (around line 512):
```python
# Include Sites V2 router under /v2
try:
  app.include_router(sites_v2.router, tags=["Sites"], prefix=v2_router_prefix)
  sites_v2.set_config(config, v2_router_prefix)
  log_function_output(log_data, f"Sites V2 router included at {v2_router_prefix}")
except Exception as e:
  initialization_errors.append({"component": "Sites V2 Router", "error": str(e)})
```

3. Add Sites link to toolbar (around line 593):
```python
<a href="/v2/sites?format=ui" class="btn-primary"> Sites </a>
```

4. Add Sites link to V2 routers list (around line 621):
```python
<li><a href="/v2/sites">/v2/sites</a> - Sites Management ...</li>
```

### SITE-IP01-IS-12: Update navigation in other V2 routers

Add Sites link to `main_page_nav_html` in:
- `src/routers_v2/domains.py`
- Other V2 routers as needed

## File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `src/hardcoded_config.py` | Modify | Add SITES_SUBFOLDER and SITE_JSON constants |
| `src/routers_v2/sites.py` | Create | New router file with all endpoints |
| `src/app.py` | Modify | Import and register sites router, add UI links |
| `src/routers_v2/domains.py` | Modify | Add Sites to navigation |

## Code Patterns

### Storage Path Construction

```python
def get_sites_folder_path(storage_path: str) -> str:
  return os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_SITES_SUBFOLDER)

def get_site_folder_path(storage_path: str, site_id: str) -> str:
  return os.path.join(get_sites_folder_path(storage_path), site_id)

def get_site_json_path(storage_path: str, site_id: str) -> str:
  return os.path.join(get_site_folder_path(storage_path, site_id), CRAWLER_HARDCODED_CONFIG.SITE_JSON)
```

### URL Normalization

```python
def normalize_site_url(url: str) -> str:
  """Strip trailing slash from URL."""
  return url.rstrip('/') if url else url
```

### Selftest Pattern

```python
async def sites_selftest(request: Request):
  # Create unique test site ID
  test_site_id = f"_test_{uuid.uuid4().hex[:8]}"
  
  # Test sequence
  # 1. Create site
  # 2. Get site
  # 3. Update site
  # 4. Rename site
  # 5. Delete site
  # 6. Verify deleted
```

## Verification Checklist

- [ ] SITE-IP01-VC-01: All endpoints return correct format based on `format` param
- [ ] SITE-IP01-VC-02: Create validates required fields and uniqueness
- [ ] SITE-IP01-VC-03: Update handles ID change (rename) correctly
- [ ] SITE-IP01-VC-04: Delete returns deleted site data
- [ ] SITE-IP01-VC-05: Selftest completes without errors
- [ ] SITE-IP01-VC-06: UI displays all columns correctly
- [ ] SITE-IP01-VC-07: Scan buttons show "not implemented" toast
- [ ] SITE-IP01-VC-08: Trailing slash stripped from site_url
- [ ] SITE-IP01-VC-09: Create/Update/Delete support format=html
- [ ] SITE-IP01-VC-10: Selftest returns correct result schema

## Edge Cases

### SITE-IP01-EC-01: Empty sites folder
- List returns empty array `[]`
- UI shows "No sites found."

### SITE-IP01-EC-02: Site URL with trailing slash
- Create/Update strips trailing slash
- Example: `https://site.com/` becomes `https://site.com`

### SITE-IP01-EC-03: Rename to existing ID
- Returns 400 error: "Site '{new_id}' already exists."

### SITE-IP01-EC-04: Invalid site_id pattern
- Returns 400 error: "Site ID must match pattern [a-zA-Z0-9_-]+"

### SITE-IP01-EC-05: Race condition on delete
- If folder deleted between load and delete, handle FileNotFoundError gracefully
- Return success (idempotent delete)

## Critique Findings (Reconciled)

### Confirmed - Implement

- **Keep functions inline in sites.py** - Do NOT create separate common_site_functions_v2.py
- **Copy domains.py patterns exactly** - User explicitly requested same look and feel
- **Handle FileNotFoundError on delete** - Graceful handling for race conditions

### Dismissed - Not Implementing

- **File locking** - Same as domains.py, acceptable for single-admin MVP
- **Reserved site_id names** - Theoretical risk, not worth complexity
- **Size limits on fields** - Admin-only access, theoretical risk
- **Backup before delete** - Out of scope for MVP
- **Atomic folder rename** - Same behavior as domains.py, acceptable

## Document History

**[2026-02-03 09:45]**
- Added EC-05: Race condition on delete
- Added "Critique Findings (Reconciled)" section with confirmed/dismissed items

**[2026-02-03 09:35]**
- Added MUST-NOT-FORGET section
- Fixed CUD endpoints to specify html format support
- Added selftest result schema
- Added VC-09 and VC-10 to verification checklist
- Fixed Delete to note DD-E017 (load before delete)

**[2026-02-03 09:30]**
- Initial implementation plan created

