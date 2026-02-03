# IMPL: Permission Scanner POC

**Doc ID**: PSCP-IP01
**Goal**: Implement POC scripts to validate SharePoint permission scanner API capabilities
**Timeline**: Created 2026-02-03

**Target files**:
- `src/pocs/permission_scanner/00_validate_prerequisites.py` (NEW ~80 lines)
- `src/pocs/permission_scanner/01A_create_library_with_50_files_10_broken_inheritance.py` (NEW ~120 lines)
- `src/pocs/permission_scanner/01A_delete_library_with_50_files_10_broken_inheritance.py` (NEW ~40 lines)
- `src/pocs/permission_scanner/01B_create_library_with_6000_files_30_broken_inheritance.py` (NEW ~150 lines)
- `src/pocs/permission_scanner/01B_delete_library_with_6000_files_30_broken_inheritance.py` (NEW ~40 lines)
- `src/pocs/permission_scanner/02A_test_poc_core_functionality.py` (NEW ~350 lines)
- `src/pocs/permission_scanner/02B_test_poc_performance.py` (NEW ~200 lines)

**Depends on:**
- `_SPEC_PERMISSION_SCANNER_POC.md` [PSCP-SP01] for test cases and requirements

## MUST-NOT-FORGET

- Certificate path: `os.path.join(LOCAL_PERSISTENT_STORAGE_PATH, CRAWLER_CLIENT_CERTIFICATE_PFX_FILE)`
- Use `connect_to_site_using_client_id_and_certificate()` from `common_sharepoint_functions_v2.py`
- Site URL from `CRAWLER_SELFTEST_SHAREPOINT_SITE` env var
- All scripts standalone executable with `python script.py`
- Import path requires `sys.path.insert(0, src_folder)` for relative imports
- **`skip()` is IGNORED** by SharePoint for list items - use `filter(f"ID gt {last_id}")` instead [VERIFIED]
  - External source: `_INFO_SHAREPOINT_LISTITEM.md [SPAPI-IN07]` confirms `$skip` not supported
- **5,000 item view threshold** - queries without indexed columns fail [VERIFIED]
  - ID column is always indexed, so `ID gt {last_id}` is safe
- **`execute_batch()` does NOT work** for file uploads - use sequential `execute_query()` [TESTED]

## Table of Contents

1. [File Structure](#1-file-structure)
2. [Shared Utilities](#2-shared-utilities)
3. [Edge Cases](#3-edge-cases)
4. [Implementation Steps](#4-implementation-steps)
5. [Test Cases](#5-test-cases)
6. [Verification Checklist](#6-verification-checklist)
7. [Document History](#7-document-history)

## 1. File Structure

```
src/pocs/permission_scanner/
├── __init__.py                 # Empty, makes folder a package
├── _poc_utils.py               # Shared utilities for all POC scripts (~60 lines) [NEW]
├── 00_validate_prerequisites.py    # Prerequisite validation (~80 lines) [NEW]
├── 01A_create_library_with_50_files_10_broken_inheritance.py  (~120 lines) [NEW]
├── 01A_delete_library_with_50_files_10_broken_inheritance.py  (~40 lines) [NEW]
├── 01B_create_library_with_6000_files_30_broken_inheritance.py (~150 lines) [NEW]
├── 01B_delete_library_with_6000_files_30_broken_inheritance.py (~40 lines) [NEW]
├── 02A_test_poc_core_functionality.py  (~350 lines) [NEW]
└── 02B_test_poc_performance.py         (~200 lines) [NEW]
```

## 2. Shared Utilities

**File**: `_poc_utils.py`

Common functions used by all POC scripts:

```python
def get_poc_config() -> dict:
    """Load env vars and build config dict with site_url, client_id, tenant_id, cert_path, cert_password."""

def get_sharepoint_context() -> ClientContext:
    """Create authenticated SharePoint context using certificate."""

def print_header(script_name: str) -> None:
    """Print formatted script header with site URL and timestamp."""

def print_result(test_name: str, passed: bool, message: str = "") -> None:
    """Print formatted test result: PASS/FAIL with optional message."""

def print_summary(passed: int, failed: int, skipped: int) -> None:
    """Print final summary line."""
```

## 3. Edge Cases

**PSCP-IP01-EC-01**: Missing env vars -> Print specific missing var name, exit with code 1
**PSCP-IP01-EC-02**: Certificate file not found -> Print path attempted, exit with code 1
**PSCP-IP01-EC-03**: Sites.Selected 403 -> Print clear message about grant requirement
**PSCP-IP01-EC-04**: Library already exists (create) -> Delete first, then create
**PSCP-IP01-EC-05**: Library not found (delete) -> Print warning, exit success
**PSCP-IP01-EC-06**: HasUniqueRoleAssignments not in response -> FAIL TC-04, document as STOP
**PSCP-IP01-EC-07**: Graph API 401 -> Check GroupMember.Read.All permission
**PSCP-IP01-EC-08**: `skip()` pagination returns duplicates -> Use `ID > last_id` filter [TESTED]
**PSCP-IP01-EC-09**: `execute_batch()` with file content -> TypeError, use sequential upload [TESTED]

## 4. Implementation Steps

### PSCP-IP01-IS-01: Create folder structure and __init__.py

**Location**: `src/pocs/permission_scanner/`

**Action**: Create folder and empty `__init__.py`

### PSCP-IP01-IS-02: Implement _poc_utils.py

**Location**: `src/pocs/permission_scanner/_poc_utils.py`

**Action**: Create shared utilities module

**Code outline**:
```python
import os, sys
from datetime import datetime
from dotenv import load_dotenv

# Add src to path for imports
src_path = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, src_path)

from routers_v2.common_sharepoint_functions_v2 import connect_to_site_using_client_id_and_certificate

def get_poc_config() -> dict: ...
def get_sharepoint_context(config: dict) -> ClientContext: ...
def print_header(script_name: str, config: dict) -> None: ...
def print_result(test_name: str, passed: bool, message: str = "") -> None: ...
def print_summary(passed: int, failed: int, skipped: int) -> None: ...
```

### PSCP-IP01-IS-03: Implement 00_validate_prerequisites.py

**Location**: `src/pocs/permission_scanner/00_validate_prerequisites.py`

**Action**: Create prerequisite validation script

**Code outline**:
```python
from _poc_utils import get_poc_config, get_sharepoint_context, print_header, print_result, print_summary

def main():
    config = get_poc_config()  # Validates env vars
    print_header("Prerequisite Validation", config)
    
    # Test 1: SharePoint connection
    ctx = get_sharepoint_context(config)
    web = ctx.web.get().execute_query()
    print_result("SharePoint Connection", True, f"Site: {web.properties['Title']}")
    
    # Test 2: Graph API (optional - skip if no Azure AD groups in site)
    # ...
    
    print_summary(passed, failed, skipped)

if __name__ == "__main__": main()
```

### PSCP-IP01-IS-04: Implement 01A_create_library_with_50_files_10_broken_inheritance.py

**Location**: `src/pocs/permission_scanner/01A_create_library_with_50_files_10_broken_inheritance.py`

**Action**: Create test library setup script

**Code outline**:
```python
LIBRARY_NAME = "POC_PermissionTest_50"
FILE_COUNT = 50
BROKEN_COUNT = 10

def create_library(ctx, name): ...
def upload_files(ctx, library, count): ...
def break_inheritance(ctx, library, item_ids): ...
def add_visitor_permission(ctx, library, item_ids): ...

def main():
    # 1. Get context
    # 2. Delete if exists
    # 3. Create library
    # 4. Upload files
    # 5. Break inheritance on first 10
    # 6. Add Visitors group with Read
    # 7. Print summary
```

### PSCP-IP01-IS-05: Implement 01A_delete_library_with_50_files_10_broken_inheritance.py

**Location**: `src/pocs/permission_scanner/01A_delete_library_with_50_files_10_broken_inheritance.py`

**Action**: Create test library teardown script

**Code outline**:
```python
LIBRARY_NAME = "POC_PermissionTest_50"

def main():
    ctx = get_sharepoint_context(get_poc_config())
    try:
        library = ctx.web.lists.get_by_title(LIBRARY_NAME)
        library.delete_object().execute_query()
        print(f"Deleted library: {LIBRARY_NAME}")
    except Exception as e:
        print(f"Library not found or error: {e}")
```

### PSCP-IP01-IS-06: Implement 01B scripts (6000 files)

**Location**: `src/pocs/permission_scanner/01B_*.py`

**Action**: Same as 01A but with batching for 6000 files

**Key differences**:
- `FILE_COUNT = 6000`, `BROKEN_COUNT = 30`
- Upload sequentially with `execute_query()` per file (batching file content causes TypeError) [TESTED]
- Progress output every 500 files

### PSCP-IP01-IS-07: Implement 02A_test_poc_core_functionality.py

**Location**: `src/pocs/permission_scanner/02A_test_poc_core_functionality.py`

**Action**: Create core functionality test script

**Code outline**:
```python
LIBRARY_NAME = "POC_PermissionTest_50"

def tc_01_basic_auth(ctx): ...
def tc_02_web_properties(ctx): ...
def tc_03_list_enumeration(ctx): ...
def tc_04_has_unique_role_assignments(ctx, library): ...  # CRITICAL
def tc_05_broken_inheritance_count(ctx, library): ...
def tc_06_role_assignments_expansion(ctx): ...  # CRITICAL
def tc_07_item_role_assignments(ctx, library): ...
def tc_08_sharepoint_groups(ctx): ...
def tc_09_graph_transitive_members(ctx): ...  # SKIP if no Azure AD group
def tc_10_batch_execution(ctx): ...
def tc_11_m365_group_detection(ctx): ...  # SKIP if no M365 group

def main():
    results = []
    ctx = get_sharepoint_context(get_poc_config())
    library = ctx.web.lists.get_by_title(LIBRARY_NAME)
    
    for tc in [tc_01, tc_02, ...]:
        try:
            passed, msg = tc(ctx, library)
            results.append((tc.__name__, passed, msg))
        except Exception as e:
            results.append((tc.__name__, False, str(e)))
    
    # Print results and summary
```

### PSCP-IP01-IS-08: Implement 02B_test_poc_performance.py

**Location**: `src/pocs/permission_scanner/02B_test_poc_performance.py`

**Action**: Create performance test script

**Code outline**:
```python
LIBRARY_NAME = "POC_PermissionTest_6000"

def perf_01_full_enumeration(ctx, library): ...  # Uses ID > last_id filter for pagination [TESTED]
def perf_02_bulk_vs_naive(ctx, library): ...      # 52x speedup confirmed [TESTED]
def perf_03_batched_role_assignments(ctx, library): ...  # 3.4x speedup confirmed [TESTED]
def perf_04_pagination(ctx, library): ...         # Uses ID > last_id filter, skip() ignored [TESTED]

def main():
    # Similar structure to 02A but with timing
    import time
    start = time.time()
    # ... run test ...
    elapsed = time.time() - start
    print(f"PERF-01: {elapsed:.2f} sec (estimate: 2-4 sec)")
```

## 5. Test Cases

### Prerequisites (00)

- **PSCP-IP01-TC-01**: Valid env vars -> ok=true, config loaded
- **PSCP-IP01-TC-02**: Missing CRAWLER_SELFTEST_SHAREPOINT_SITE -> ok=false, clear error
- **PSCP-IP01-TC-03**: SharePoint connection -> ok=true, site title returned
- **PSCP-IP01-TC-04**: Sites.Selected 403 -> ok=false, grant message

### Setup/Teardown (01A/01B)

- **PSCP-IP01-TC-05**: Create library -> ok=true, library exists
- **PSCP-IP01-TC-06**: Upload files -> ok=true, count matches
- **PSCP-IP01-TC-07**: Break inheritance -> ok=true, items have unique permissions
- **PSCP-IP01-TC-08**: Delete library -> ok=true, library gone

### Core Functionality (02A)

- **PSCP-IP01-TC-09**: TC-01 to TC-11 per SPEC -> ok=true for each

### Performance (02B)

- **PSCP-IP01-TC-10**: PERF-01 to PERF-04 per SPEC -> ok=true, within 2x estimate

## 6. Verification Checklist

### Prerequisites
- [x] **PSCP-IP01-VC-01**: SPEC [PSCP-SP01] read and understood
- [x] **PSCP-IP01-VC-02**: Existing auth pattern in crawler.py reviewed

### Implementation
- [x] **PSCP-IP01-VC-03**: Folder structure created
- [x] **PSCP-IP01-VC-04**: _poc_utils.py implemented
- [x] **PSCP-IP01-VC-05**: 00_validate_prerequisites.py implemented
- [x] **PSCP-IP01-VC-06**: 01A scripts implemented
- [x] **PSCP-IP01-VC-07**: 01B scripts implemented
- [x] **PSCP-IP01-VC-08**: 02A_test_poc_core_functionality.py implemented
- [x] **PSCP-IP01-VC-09**: 02B_test_poc_performance.py implemented

### Validation
- [x] **PSCP-IP01-VC-10**: All scripts pass `python -m py_compile`
- [x] **PSCP-IP01-VC-11**: 00_validate_prerequisites.py runs successfully
- [x] **PSCP-IP01-VC-12**: 01A_create runs successfully
- [x] **PSCP-IP01-VC-13**: 02A all tests pass (9 PASS, 2 SKIP)
- [x] **PSCP-IP01-VC-14**: 02B all tests pass (4 PASS after pagination fix)
- [x] **PSCP-IP01-VC-15**: 01A_delete runs successfully

## 7. Document History

**[2026-02-03 14:20]**
- Added: External source reference `_INFO_SHAREPOINT_LISTITEM.md [SPAPI-IN07]` confirming $skip limitation
- Added: 5,000 item view threshold with indexed column note
- Changed: `[TESTED]` → `[VERIFIED]` for $skip limitation (external confirmation)

**[2026-02-03 14:15]**
- Synced: Implementation findings from code execution
- Added: EC-08, EC-09 for pagination and batch upload limitations [TESTED]
- Added: MUST-NOT-FORGET items for `skip()` and `execute_batch()` limitations
- Changed: IS-06 to note sequential upload requirement (batch doesn't work)
- Changed: IS-08 performance functions to note tested results
- Changed: Verification checklist marked complete with results

**[2026-02-03 12:25]**
- Initial implementation plan created
