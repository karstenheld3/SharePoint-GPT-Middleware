# Implementation Plan: Domain ID Rename Feature

**Goal**: Add ability to rename Domain ID via the Edit dialog in `/v2/domains?format=ui`
**Design pattern**: Same as demorouter2.py (per DD-E014 from `_V2_SPEC_ROUTERS.md`)
**Spec reference**: `_V2_SPEC_DOMAINS_UI.md` (V2DM-FR-03)

## Table of Contents

1. Overview
2. Files to Modify
3. Implementation Steps
4. Final Checklist

## Overview

The Domain ID rename feature allows administrators to change a domain's identifier through the Edit modal. The implementation follows DD-E014:
- Query string `domain_id` = current/source identifier
- Body `domain_id` = new/target identifier (only included if changed)
- Backend validates, renames folder, applies remaining fields

## Files to Modify

```
src/routers_v2/
├── common_crawler_functions_v2.py   # Add rename_domain() helper
└── domains.py                       # Update endpoint + UI JavaScript
```

## Implementation Steps

### Step 1: Add Helper Function in common_crawler_functions_v2.py

**Function**: `rename_domain(storage_path, source_domain_id, target_domain_id) -> tuple[bool, str]`

**Location**: Add after `delete_domain_folder()` function

**Logic**:
```python
def rename_domain(storage_path: str, source_domain_id: str, target_domain_id: str) -> tuple[bool, str]:
  """
  Rename a domain by renaming its folder.
  Returns (success, error_message).
  """
  domains_path = os.path.join(storage_path, "domains")
  source_path = os.path.join(domains_path, source_domain_id)
  target_path = os.path.join(domains_path, target_domain_id)
  
  # Validate source exists
  if not os.path.exists(source_path):
    return False, f"Source domain '{source_domain_id}' not found."
  
  # Validate target not exists
  if os.path.exists(target_path):
    return False, f"Target domain '{target_domain_id}' already exists."
  
  # Validate target ID format
  if not re.match(r'^[a-zA-Z0-9_-]+$', target_domain_id):
    return False, f"Invalid domain ID format: '{target_domain_id}'. Use only letters, numbers, underscores, hyphens."
  
  # Rename folder
  try:
    os.rename(source_path, target_path)
    return True, ""
  except Exception as e:
    return False, f"Failed to rename domain: {str(e)}"
```

**Dependencies**: `os`, `re` (both already imported in the file)

**Note**: No `dry_run` parameter - domains router doesn't support dry_run per spec.

### Step 2: Update domains.py - Import Helper

Modify existing import to add `rename_domain`:
```python
# Current:
from routers_v2.common_crawler_functions_v2 import (
  load_domain, load_all_domains, save_domain_to_file, delete_domain_folder,
  ...
)

# Add rename_domain to the import list:
from routers_v2.common_crawler_functions_v2 import (
  load_domain, load_all_domains, save_domain_to_file, delete_domain_folder,
  rename_domain,  # <-- ADD THIS
  ...
)
```

### Step 3: Update domains.py - Update Endpoint

**Location**: `@router.put(f"/{router_name}/update")` function

**Current logic**: Accepts body fields, updates domain.json. Body parsing already exists (lines 589-603).

**New logic** (insert AFTER body parsing, BEFORE "Load existing domain" comment):
```python
# Rename detection (per DD-E014)
source_domain_id = domain_id  # From query string
target_domain_id = body_data.get("domain_id", None)
rename_requested = target_domain_id and target_domain_id != source_domain_id
```

**Modify existing domain load** (after the try/except that loads existing domain):
```python
# Handle rename if requested (after loading existing, before field updates)
if rename_requested:
  success, error_msg = rename_domain(storage_path, source_domain_id, target_domain_id)
  if not success:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": error_msg, "data": {}}, status_code=400)
  domain_id = target_domain_id  # Use new ID for remaining operations
```

**CRITICAL: Update DomainConfig creation** (modify existing code around line 636):
```python
# Create updated domain config - use domain_id which is now target if renamed
domain_config = DomainConfig(
  domain_id=domain_id,  # This is target_domain_id after rename!
  name=name,
  ...
)
```

**Note**: The sources_json parsing (lines 616-633) remains unchanged.

### Step 4: Update domains.py - Edit Form HTML

**Location**: `showEditDomainForm()` function in `get_router_specific_js()`

**Changes**:

1. Change hidden field name from `domain_id` to `source_domain_id`:
```javascript
// OLD
<input type="hidden" name="domain_id" value="${{escapeHtml(domainId)}}">

// NEW
<input type="hidden" name="source_domain_id" value="${{escapeHtml(domainId)}}">
```

2. Make Domain ID field editable (remove `disabled`):
```javascript
// OLD
<div class="form-group">
  <label>Domain ID</label>
  <input type="text" value="${{escapeHtml(domainId)}}" disabled>
</div>

// NEW
<div class="form-group">
  <label>Domain ID</label>
  <input type="text" name="domain_id" value="${{escapeHtml(domainId)}}">
  <small style="color: #666;">Change to rename the domain</small>
</div>
```

### Step 5: Update domains.py - Submit Function

**Location**: `submitEditDomainForm()` function in `get_router_specific_js()`

**Replace entire function with**:
```javascript
function submitEditDomainForm(event) {{
  event.preventDefault();
  const form = document.getElementById('edit-domain-form');
  const btn = document.querySelector('.modal-footer button[type="submit"]');
  const formData = new FormData(form);
  const data = {{}};
  
  const sourceDomainId = formData.get('source_domain_id');
  const targetDomainId = formData.get('domain_id');
  
  // Validate Domain ID not empty
  const domainIdInput = form.querySelector('input[name="domain_id"]');
  if (!targetDomainId || !targetDomainId.trim()) {{
    showFieldError(domainIdInput, 'Domain ID cannot be empty');
    return;
  }}
  clearFieldError(domainIdInput);
  
  // Build data object
  for (const [key, value] of formData.entries()) {{
    if (key === 'source_domain_id') continue;  // Skip source ID
    if (key === 'domain_id') {{
      // Only include if changed (triggers rename per DD-E014)
      if (value && value.trim() !== sourceDomainId) {{
        data.domain_id = value.trim();
      }}
    }} else if (value !== undefined) {{
      data[key] = value.trim();
    }}
  }}
  
  clearModalError();
  callEndpoint(btn, sourceDomainId, data);  // Uses source ID in URL
}}
```

### Step 6: Update domains.py - Button Data Attributes

**Location**: OK button in `showEditDomainForm()`

**Verify these attributes are present**:
```javascript
data-url="{router_prefix}/{router_name}/update?domain_id=${{domainId}}"
data-method="PUT"
data-format="json"
data-reload-on-finish="true"
data-close-on-success="true"
```

Note: `domainId` in the URL is the source ID (from when form was opened).

## Final Checklist

### Helper Functions (common_crawler_functions_v2.py)

- [ ] Add `rename_domain(storage_path, source_domain_id, target_domain_id)` function
- [ ] Validate source exists (return error tuple if not)
- [ ] Validate target not exists (return error tuple if collision)
- [ ] Validate target ID format matches `[a-zA-Z0-9_-]+`
- [ ] Rename folder using `os.rename()`
- [ ] Return tuple `(success: bool, error_msg: str)`

### Router Endpoint (domains.py - update endpoint)

- [ ] Import `rename_domain` from common_crawler_functions_v2
- [ ] Extract `source_domain_id` from query string (after body parsing)
- [ ] Extract `target_domain_id` from body (if present)
- [ ] Detect rename: `rename_requested = target_domain_id and target_domain_id != source_domain_id`
- [ ] Validate source domain exists (404 if not) - already exists
- [ ] If rename requested: call `rename_domain(storage_path, source, target)`, handle errors (400)
- [ ] Update `domain_id` variable to target ID after successful rename
- [ ] **CRITICAL**: Use updated `domain_id` in `DomainConfig(domain_id=domain_id, ...)`
- [ ] Save domain to new location (save_domain_to_file uses domain_id from config)

### UI JavaScript (domains.py - get_router_specific_js)

**showEditDomainForm()**:
- [ ] Add hidden field: `<input type="hidden" name="source_domain_id" value="${{escapeHtml(domainId)}}">`
- [ ] Change Domain ID input: remove `disabled`, add `name="domain_id"`
- [ ] Add hint text: `<small style="color: #666;">Change to rename the domain</small>`

**submitEditDomainForm()**:
- [ ] Get `sourceDomainId` from `formData.get('source_domain_id')`
- [ ] Get `targetDomainId` from `formData.get('domain_id')`
- [ ] Validate Domain ID not empty, show field error if empty
- [ ] Skip `source_domain_id` when building data object
- [ ] Include `domain_id` in data only if `targetDomainId !== sourceDomainId`
- [ ] Call `callEndpoint(btn, sourceDomainId, data)` with source ID

**Button attributes**:
- [ ] `data-url` uses source ID: `?domain_id=${{domainId}}`
- [ ] `data-method="PUT"`
- [ ] `data-close-on-success="true"`
- [ ] `data-reload-on-finish="true"`

### Testing

- [ ] Edit domain without changing ID → domain updated, ID unchanged
- [ ] Edit domain with new ID → folder renamed, domain updated at new location
- [ ] Rename to existing ID → error "already exists" shown in modal
- [ ] Rename to invalid ID format → error shown in modal
- [ ] Empty Domain ID → client-side validation error
- [ ] Cancel edit → no changes made

## Implementation Order

1. **Step 1**: Add `rename_domain()` helper in common_crawler_functions_v2.py
2. **Step 2**: Import helper in domains.py
3. **Step 3**: Update `/update` endpoint with rename logic
4. **Step 4-6**: Update UI JavaScript (form HTML + submit logic)
5. **Test**: Manual testing via browser

## Notes

- The `callEndpoint()` function from common_ui_functions_v2.py handles the actual HTTP call
- Error responses are displayed in the modal footer (`.modal-error` element) via `showModalError()`
- On success with `data-close-on-success="true"`, modal closes automatically
- Table reloads via `reloadItems()` when `data-reload-on-finish="true"`
