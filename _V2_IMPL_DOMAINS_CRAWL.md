# Implementation Plan: Crawl Domain Dialog

**Plan ID**: V2DM-IP03
**Goal**: Add [Crawl] button to domain rows that opens a modal dialog for configuring and starting crawl jobs
**Target files**:
- `/src/routers_v2/domains.py` (MODIFY)

**Depends on:**
- `_V2_SPEC_DOMAINS_UI.md` for V2DM-FR-06 specification
- `_V2_SPEC_ROUTERS.md` for SSE streaming patterns
- `_V2_SPEC_COMMON_UI_FUNCTIONS.md` for UI generation functions

**Does not depend on:**
- `_V2_SPEC_CRAWLER.md` (crawler endpoints already exist)

## Table of Contents

1. Domain Objects
2. Actions
3. Edge Cases
4. Known Limitations
5. Verification Issues (from /verify-spec)
6. Implementation Steps
7. Test Cases
8. Backward Compatibility Test
9. Checklist
10. Spec Update Required

## Domain Objects

- **Domain**: Knowledge domain with `domain_id`, `name`, `file_sources[]`, `sitepage_sources[]`, `list_sources[]`
- **Source**: Individual source within a domain with `source_id`, `site_url`, etc.
- **Crawl Job**: Streaming job created by `/v2/crawler/{step}` endpoints

## Actions

- **showCrawlDomainForm(domainId)**: Opens modal with crawl options, pre-selects domain
- **updateCrawlEndpointPreview()**: Live-updates endpoint URL preview based on form values
- **updateSourceIdDropdown()**: Populates source_id dropdown based on selected scope
- **startCrawl(event)**: Validates form, builds URL, connects SSE stream, closes modal

## Edge Cases

- **V2DM-IP03-EC-01**: Domain has no sources -> Show warning in modal, allow crawl (will complete with "No sources configured")
- **V2DM-IP03-EC-02**: Source ID dropdown with empty sources for selected scope -> Show only "(empty - no filter)" option
- **V2DM-IP03-EC-03**: Domain dropdown changes mid-form -> Reset source_id dropdown, update endpoint preview
- **V2DM-IP03-EC-04**: Scope changes to "all" -> Disable source_id dropdown, reset to empty
- **V2DM-IP03-EC-05**: Network error during crawl -> Show error toast, keep console open with partial output
- **V2DM-IP03-EC-06**: Domain deleted while crawl dialog is open -> Crawl will fail with 404, toast shows error
- **V2DM-IP03-EC-07**: Stale domain data in dropdown (domain created by another user) -> User must close/reopen modal or reload page
- **V2DM-IP03-EC-08**: Multiple concurrent crawls on same domain -> Allowed (jobs system handles, each gets unique job_id)
- **V2DM-IP03-EC-09**: SharePoint credentials not configured -> Download step fails, error shows in console
- **V2DM-IP03-EC-10**: Domain has empty vector_store_id -> Embed step fails, error shows in console

## Known Limitations

- **KL-01**: Domain cache populated on page load only. Newly created domains won't appear in crawl modal dropdown until page refresh.
- **KL-02**: Stale cache after CRUD operations - user must reload page to see new domains in crawl dropdown.

## Verification Issues (from /verify-spec)

Issues found during verification against existing code:

### V2DM-IP03-VI-01: Duplicate reloadItems() function (CRITICAL)

**Problem**: The plan's IS-02 adds a `reloadItems()` function, but `generate_ui_page()` already generates one in common_ui_functions_v2.py (line 672). This causes JS redefinition.

**Fix**: Do NOT add custom `reloadItems()`. Instead:
1. Add `domainsState` Map at top of router-specific JS
2. Add a `cacheDomains()` function that fetches and caches domain data
3. Modify approach: call `cacheDomains()` on DOMContentLoaded, don't override `reloadItems()`

### V2DM-IP03-VI-02: renderAllDomains() not defined (CRITICAL)

**Problem**: IS-02 calls `renderAllDomains()` which doesn't exist.

**Fix**: Remove call to `renderAllDomains()`. The table is already rendered server-side and `reloadItems()` handles refresh via `renderItemsTable()`.

### V2DM-IP03-VI-03: domainsState needs initialization (MEDIUM)

**Problem**: The `domainsState` Map needs to be populated on page load for source_id dropdown to work.

**Fix**: Add DOMContentLoaded handler that calls `cacheDomains()` which fetches `/v2/domains?format=json` and populates the Map. The existing `reloadItems()` handles table rendering.

### V2DM-IP03-VI-04: Common UI functions exist (VERIFIED OK)

**Verified**: `connectStream()`, `showConsole()`, `clearConsole()` all exist in common_ui_functions_v2.py. No issues.

### V2DM-IP03-VI-05: Spec inconsistency - Router-Specific JS functions (DOCUMENTATION)

**Problem**: Spec (lines 407-427) lists `refreshDomains()`, `reloadItems()`, `renderAllDomains()`, `renderDomainRow()` as router-specific, but these are actually provided by `generate_ui_page()` in common_ui_functions_v2.py.

**Fix**: The SPEC should be updated to remove these from the "Router-Specific JavaScript Functions" section. The plan is correct; the spec is outdated.

**Action**: After implementation, update `_V2_SPEC_DOMAINS_UI.md` lines 407-413 to remove the auto-generated functions.

### V2DM-IP03-VI-06: Missing edge case - empty vector_store_id (MEDIUM)

**Problem**: If domain has empty `vector_store_id`, the embed step will fail.

**Fix**: This is acceptable behavior - the crawler endpoint will return an error. The UI doesn't need special handling; the error will show in console and toast.

### V2DM-IP03-VI-07: Missing edge case - SharePoint credentials not configured (LOW)

**Problem**: If SharePoint credentials are not configured, download step will fail.

**Fix**: Same as VI-06 - acceptable. Error will show in console.

## Implementation Steps (REVISED)

### V2DM-IP03-IS-01: Add [Crawl] button to Actions column

**Location**: `domains.py` > `domains_root()` > `columns` definition

**Action**: Add Crawl button as first button in actions column

**Code**:
```python
{
  "field": "actions",
  "header": "Actions",
  "buttons": [
    {"text": "Crawl", "onclick": "showCrawlDomainForm('{itemId}')", "class": "btn-small"},
    {"text": "Edit", "onclick": "showEditDomainForm('{itemId}')", "class": "btn-small"},
    # ... existing delete button
  ]
}
```

### V2DM-IP03-IS-02: Add domainsState Map and cacheDomains() (REVISED)

**Location**: `domains.py` > `get_router_specific_js()` > top of function, after constants

**Action**: Add state management for caching full domain objects (needed for source_id dropdown population)

**Code**:
```javascript
// Domain cache for crawl form source dropdown
const domainsState = new Map();

// Cache domains on page load (table is already server-rendered)
document.addEventListener('DOMContentLoaded', async () => {
  await cacheDomains();
});

async function cacheDomains() {
  try {
    const response = await fetch('{router_prefix}/{router_name}?format=json');
    const result = await response.json();
    if (result.ok) {
      domainsState.clear();
      result.data.forEach(d => domainsState.set(d.domain_id, d));
    }
  } catch (e) {
    console.error('Failed to cache domains:', e);
  }
}
```

**Note**: This does NOT override `reloadItems()` - that function is generated by `generate_ui_page()` and handles table refresh. The `cacheDomains()` function only populates the Map for the crawl form's source dropdown.

### V2DM-IP03-IS-03: Add showCrawlDomainForm() function

**Location**: `domains.py` > `get_router_specific_js()` > after Edit form functions

**Action**: Add function to display crawl options modal

**Code**:
```javascript
function showCrawlDomainForm(domainId) {
  const domain = domainsState.get(domainId);
  if (!domain) {
    showToast('Error', 'Domain not found in cache', 'error');
    return;
  }
  
  // Build domain dropdown options
  const domainOptions = Array.from(domainsState.values())
    .map(d => `<option value="${escapeHtml(d.domain_id)}" ${d.domain_id === domainId ? 'selected' : ''}>${escapeHtml(d.domain_id)} - ${escapeHtml(d.name || '')}</option>`)
    .join('');
  
  const body = document.querySelector('#modal .modal-body');
  body.innerHTML = `
    <div class="modal-header"><h3>Crawl Domain</h3></div>
    <div class="modal-scroll">
      <form id="crawl-domain-form" onsubmit="return startCrawl(event)">
        <div class="form-group">
          <label>Domain *</label>
          <select name="domain_id" onchange="onCrawlDomainChange()" required>
            ${domainOptions}
          </select>
        </div>
        
        <div class="form-group">
          <label>Step *</label>
          <div style="display: flex; flex-direction: column; gap: 4px;">
            <label><input type="radio" name="step" value="crawl" checked onchange="updateCrawlEndpointPreview()"> Full Crawl (download + process + embed)</label>
            <label><input type="radio" name="step" value="download_data" onchange="updateCrawlEndpointPreview()"> Download Data Only</label>
            <label><input type="radio" name="step" value="process_data" onchange="updateCrawlEndpointPreview()"> Process Data Only</label>
            <label><input type="radio" name="step" value="embed_data" onchange="updateCrawlEndpointPreview()"> Embed Data Only</label>
          </div>
        </div>
        
        <div class="form-group">
          <label>Mode *</label>
          <div style="display: flex; flex-direction: column; gap: 4px;">
            <label><input type="radio" name="mode" value="full" onchange="updateCrawlEndpointPreview()"> Full - Clear existing data first</label>
            <label><input type="radio" name="mode" value="incremental" checked onchange="updateCrawlEndpointPreview()"> Incremental - Only process changes</label>
          </div>
        </div>
        
        <div class="form-group">
          <label>Scope *</label>
          <div style="display: flex; flex-direction: column; gap: 4px;">
            <label><input type="radio" name="scope" value="all" checked onchange="onScopeChange()"> All Sources</label>
            <label><input type="radio" name="scope" value="files" onchange="onScopeChange()"> Files Only</label>
            <label><input type="radio" name="scope" value="lists" onchange="onScopeChange()"> Lists Only</label>
            <label><input type="radio" name="scope" value="sitepages" onchange="onScopeChange()"> Site Pages Only</label>
          </div>
        </div>
        
        <div class="form-group">
          <label>Source ID (optional)</label>
          <select name="source_id" id="crawl-source-id" disabled onchange="updateCrawlEndpointPreview()">
            <option value="">(empty - no filter)</option>
          </select>
          <small style="color: #666;">Enabled when scope is not "All Sources"</small>
        </div>
        
        <div class="form-group">
          <label><input type="checkbox" name="dry_run" onchange="updateCrawlEndpointPreview()"> Run test without making changes (dry run)</label>
        </div>
        
        <div class="form-group">
          <label>Endpoint Preview:</label>
          <pre id="crawl-endpoint-preview" style="background: #f5f5f5; padding: 8px; border-radius: 4px; overflow-x: auto; font-size: 12px;">/v2/crawler/crawl?domain_id=${escapeHtml(domainId)}&mode=incremental&scope=all&format=stream</pre>
        </div>
      </form>
    </div>
    <div class="modal-footer">
      <p class="modal-error"></p>
      <button type="submit" form="crawl-domain-form" class="btn-primary">OK</button>
      <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
    </div>
  `;
  openModal('700px');
  updateCrawlEndpointPreview();
}
```

### V2DM-IP03-IS-04: Add helper functions for crawl form

**Location**: `domains.py` > `get_router_specific_js()` > after showCrawlDomainForm()

**Action**: Add functions for form interactions

**Code**:
```javascript
function onCrawlDomainChange() {
  updateSourceIdDropdown();
  updateCrawlEndpointPreview();
}

function onScopeChange() {
  const form = document.getElementById('crawl-domain-form');
  const scope = form.querySelector('[name="scope"]:checked').value;
  const sourceIdSelect = document.getElementById('crawl-source-id');
  
  if (scope === 'all') {
    sourceIdSelect.disabled = true;
    sourceIdSelect.value = '';
  } else {
    sourceIdSelect.disabled = false;
    updateSourceIdDropdown();
  }
  updateCrawlEndpointPreview();
}

function updateSourceIdDropdown() {
  const form = document.getElementById('crawl-domain-form');
  const domainId = form.querySelector('[name="domain_id"]').value;
  const scope = form.querySelector('[name="scope"]:checked').value;
  const sourceIdSelect = document.getElementById('crawl-source-id');
  
  const domain = domainsState.get(domainId);
  if (!domain) return;
  
  let sources = [];
  if (scope === 'files') sources = domain.file_sources || [];
  else if (scope === 'lists') sources = domain.list_sources || [];
  else if (scope === 'sitepages') sources = domain.sitepage_sources || [];
  
  sourceIdSelect.innerHTML = '<option value="">(empty - no filter)</option>' +
    sources.map(s => `<option value="${escapeHtml(s.source_id)}">${escapeHtml(s.source_id)}</option>`).join('');
}

function updateCrawlEndpointPreview() {
  const form = document.getElementById('crawl-domain-form');
  if (!form) return;
  
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

### V2DM-IP03-IS-05: Add startCrawl() function

**Location**: `domains.py` > `get_router_specific_js()` > after helper functions

**Action**: Add function to start the crawl job

**Code**:
```javascript
function startCrawl(event) {
  event.preventDefault();
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
  
  closeModal();
  showConsole();
  clearConsole();
  connectStream(url, { reloadOnFinish: false, showResult: 'toast', clearConsole: false });
  showToast('Crawl Started', domainId, 'info');
}
```

### V2DM-IP03-IS-06: Refresh cache on reloadItems (REVISED)

**Location**: `domains.py` > `get_router_specific_js()` > after cacheDomains()

**Action**: Hook into reload to refresh cache

**Code**:
```javascript
// Extend reloadItems to also refresh cache
const originalReloadItems = typeof reloadItems === 'function' ? reloadItems : null;
window.reloadItemsWithCache = async function() {
  await cacheDomains();
  if (originalReloadItems) originalReloadItems();
};
```

**Note**: This is optional. If the user reloads the page, the cache will be refreshed anyway via DOMContentLoaded. For simplicity, we can skip this step and accept that the cache may be stale until page reload. The crawl form will still work - it just won't show newly created domains until page refresh.

**Decision**: SKIP this step for initial implementation. Document as known limitation.

## Test Cases

### Manual UI Tests (4 tests)

- **V2DM-IP03-TST-01**: Click [Crawl] on domain row -> Modal opens with domain pre-selected, endpoint preview shows correct URL
- **V2DM-IP03-TST-02**: Change scope from "All" to "Files" -> source_id dropdown enables, populates with file_sources
- **V2DM-IP03-TST-03**: Check dry_run checkbox -> Endpoint preview updates to include `&dry_run=true`
- **V2DM-IP03-TST-04**: Click [OK] -> Modal closes, console shows, SSE stream connects, toast shows "Crawl Started"

### Edge Case Tests (3 tests)

- **V2DM-IP03-TST-05**: Domain with no sources, click [Crawl], select scope=files -> source_id dropdown shows only "(empty - no filter)"
- **V2DM-IP03-TST-06**: Change domain dropdown -> source_id dropdown repopulates for new domain
- **V2DM-IP03-TST-07**: Select scope=all -> source_id dropdown disables and resets to empty

## Backward Compatibility Test

**Purpose**: Verify existing domains UI behavior is preserved.

**Test script**: `_V2_IMPL_DOMAINS_CRAWL_backcompat_test.py`

**Run BEFORE implementation**:
```bash
python _V2_IMPL_DOMAINS_CRAWL_backcompat_test.py > backcompat_before.txt
```

**Run AFTER implementation**:
```bash
python _V2_IMPL_DOMAINS_CRAWL_backcompat_test.py > backcompat_after.txt
diff backcompat_before.txt backcompat_after.txt
```

**Test coverage**:
- [ ] GET /v2/domains?format=json returns same structure
- [ ] GET /v2/domains?format=ui returns HTML with table
- [ ] GET /v2/domains/get?domain_id=X returns domain data
- [ ] Existing Edit/Delete buttons still work

**Script**:
```python
# _V2_IMPL_DOMAINS_CRAWL_backcompat_test.py
import httpx, json

BASE_URL = "http://localhost:8000"

def test_list_domains():
  r = httpx.get(f"{BASE_URL}/v2/domains?format=json")
  print(f"GET /v2/domains?format=json: {r.status_code}")
  result = r.json()
  print(f"  ok={result.get('ok')}, domains={len(result.get('data', []))}")
  if result.get('data'):
    print(f"  first domain keys: {list(result['data'][0].keys())}")

def test_ui_page():
  r = httpx.get(f"{BASE_URL}/v2/domains?format=ui")
  print(f"GET /v2/domains?format=ui: {r.status_code}")
  print(f"  contains 'Domains': {'Domains' in r.text}")
  print(f"  contains 'New Domain': {'New Domain' in r.text}")
  print(f"  contains 'Edit': {'showEditDomainForm' in r.text}")
  print(f"  contains 'Delete': {'Delete' in r.text}")

if __name__ == "__main__":
  test_list_domains()
  test_ui_page()
```

## Checklist

### Prerequisites
- [ ] **V2DM-IP03-VC-01**: Related specs read (_V2_SPEC_DOMAINS_UI.md, _V2_SPEC_COMMON_UI_FUNCTIONS.md)
- [ ] **V2DM-IP03-VC-02**: Backward compatibility test script created
- [ ] **V2DM-IP03-VC-03**: Backward compatibility test run BEFORE changes

### Implementation
- [ ] **V2DM-IP03-VC-04**: IS-01 completed (Add [Crawl] button to Actions column)
- [ ] **V2DM-IP03-VC-05**: IS-02 completed (Add domainsState Map)
- [ ] **V2DM-IP03-VC-06**: IS-03 completed (Add showCrawlDomainForm function)
- [ ] **V2DM-IP03-VC-07**: IS-04 completed (Add helper functions)
- [ ] **V2DM-IP03-VC-08**: IS-05 completed (Add startCrawl function)

### Verification
- [ ] **V2DM-IP03-VC-09**: All manual UI tests pass (TST-01 through TST-07)
- [ ] **V2DM-IP03-VC-10**: Backward compatibility test run AFTER (diff empty or expected)
- [ ] **V2DM-IP03-VC-11**: [Crawl] button visible in domains UI
- [ ] **V2DM-IP03-VC-12**: Modal opens with correct form fields
- [ ] **V2DM-IP03-VC-13**: Endpoint preview updates dynamically
- [ ] **V2DM-IP03-VC-14**: Crawl job starts and streams to console
- [ ] **V2DM-IP03-VC-15**: No JS console errors on page load
- [ ] **V2DM-IP03-VC-16**: No duplicate function definitions (check for reloadItems redefinition)
- [ ] **V2DM-IP03-VC-17**: Edit and Delete buttons still work after changes
- [ ] **V2DM-IP03-VC-18**: New Domain button still works after changes
- [ ] **V2DM-IP03-VC-19**: Crawl with dry_run=true completes without making changes
- [ ] **V2DM-IP03-VC-20**: Step dropdown correctly maps to crawler endpoints
- [ ] **V2DM-IP03-VC-21**: Scope=files populates source_id from file_sources
- [ ] **V2DM-IP03-VC-22**: Scope=lists populates source_id from list_sources
- [ ] **V2DM-IP03-VC-23**: Scope=sitepages populates source_id from sitepage_sources

## Spec Update Required

After implementation, update `_V2_SPEC_DOMAINS_UI.md`:
- Lines 407-413: Remove `refreshDomains()`, `reloadItems()`, `renderAllDomains()`, `renderDomainRow()` from Router-Specific JavaScript Functions (these are auto-generated by `generate_ui_page()`)

## Bug Fixes During Verification

The following bugs were discovered and fixed during verification testing:

### BF-01: CSS radio button display (2025-12-30)

**Files**: `src/static/css/routers_v2.css`, `src/routers_v2/domains.py`
**Problem**: `.form-group input { width: 100% }` caused radio buttons to stretch across full width
**Fix**: Added specific CSS for radio/checkbox inputs + inline styles in crawl form HTML

### BF-02: StreamingJobWriter metadata parameter (2025-12-30)

**Files**: `src/routers_v2/crawler.py`
**Problem**: `metadata=` parameter passed to StreamingJobWriter but class doesn't accept it
**Fix**: Removed invalid `metadata=` parameter from all 4 StreamingJobWriter calls

### BF-03: SSE log events not appearing in console (2025-12-30)

**Files**: `src/routers_v2/common_job_functions_v2.py`, `src/routers_v2/crawler.py`
**Problem**: Logs from nested async functions (crawl_domain, step_* functions) were written to job file but not yielded to HTTP response
**Fix**: 
1. Added `_sse_queue` list to StreamingJobWriter
2. Added `drain_sse_queue()` method
3. Modified `emit_log()` to queue SSE events
4. Updated all stream functions to drain queue after each await
