# SPEC: Permission Scanner POC (Proof of Concept)

**Doc ID**: PSCP-SP01
**Goal**: Validate Office365-REST-Python-Client and Graph API capabilities for SharePoint permission scanning
**Timeline**: Created 2026-02-03

**Target files:**
- `src/pocs/permission_scanner/00_validate_prerequisites.py`
- `src/pocs/permission_scanner/01A_create_library_with_50_files_10_broken_inheritance.py`
- `src/pocs/permission_scanner/01A_delete_library_with_50_files_10_broken_inheritance.py`
- `src/pocs/permission_scanner/01B_create_library_with_6000_files_30_broken_inheritance.py`
- `src/pocs/permission_scanner/01B_delete_library_with_6000_files_30_broken_inheritance.py`
- `src/pocs/permission_scanner/02A_test_poc_core_functionality.py`
- `src/pocs/permission_scanner/02B_test_poc_performance.py`

**Depends on:**
- `_INFO_SITE_PERMISSION_SCANNER_ASSESSMENT.md` for API mapping and performance estimates

## MUST-NOT-FORGET

- Use `CRAWLER_SELFTEST_SHAREPOINT_SITE` env var for SharePoint URL (same as crawler selftest)
- Certificate path: `os.path.join(LOCAL_PERSISTENT_STORAGE_PATH, CRAWLER_CLIENT_CERTIFICATE_PFX_FILE)`
- Use `connect_to_site_using_client_id_and_certificate()` from `common_sharepoint_functions_v2.py`
- Test with `Sites.Selected` first; document if upgrade to `Sites.FullControl.All` needed
- All scripts must be standalone executable with `python script.py`
- **`$skip` is NOT supported** for SharePoint list items - use `$skiptoken` for pagination [TESTED]
- **Throttling**: Production implementation must handle Retry-After header [ASSUMED]

## Table of Contents

1. [Scenario](#1-scenario)
2. [Context](#2-context)
3. [Test Environment](#3-test-environment)
4. [Functional Requirements](#4-functional-requirements)
5. [Design Decisions](#5-design-decisions)
6. [Script Specifications](#6-script-specifications)
7. [Test Cases](#7-test-cases)
8. [Expected Output](#8-expected-output)
9. [Document History](#9-document-history)

## 1. Scenario

**Problem:** Before implementing a full SharePoint permission scanner, we must validate that:
- Office365-REST-Python-Client supports required operations (`$select` with `HasUniqueRoleAssignments`, `$expand`, batching)
- Current app permissions (`Sites.Selected`) are sufficient
- Performance estimates from INFO document are accurate

**Solution:**
- Create test libraries with known permission inheritance states
- Run systematic tests against each required API capability
- Measure actual performance vs estimates
- Document working code patterns for implementation

**What we don't want:**
- Starting full implementation before validating library capabilities
- Hard-coded SharePoint URLs (use env var)
- Manual test setup (automate with scripts)

## 2. Context

This POC (Proof of Concept) validates findings from `_INFO_SITE_PERMISSION_SCANNER_ASSESSMENT.md` before implementation begins. The middleware already has SharePoint authentication via certificate; POC scripts reuse this pattern.

**Current App Permissions:**
- Microsoft Graph: `Group.Read.All`, `User.Read.All`, `GroupMember.Read.All` - SUFFICIENT [VERIFIED]
- SharePoint: `Sites.Selected` - [ASSUMED] may need `Sites.FullControl.All`

## 3. Test Environment

### 3.1 Test Library A (Core Functionality)

- **Name**: `POC_PermissionTest_50`
- **Items**: 50 files (simple .txt files)
- **Broken inheritance**: 10 items (20%) - realistic ratio for testing filter efficiency
- **Purpose**: Validate API functionality without performance concerns

### 3.2 Test Library B (Performance)

- **Name**: `POC_PermissionTest_6000`
- **Items**: 6000 files (simple .txt files)
- **Broken inheritance**: 30 items (0.5%)
- **Purpose**: Validate pagination, batching, and measure real performance

### 3.3 SharePoint URL Configuration

Use environment variable: `CRAWLER_SELFTEST_SHAREPOINT_SITE`

Load from `.env` file using same pattern as crawler:
```python
from dotenv import load_dotenv
import os

load_dotenv()
site_url = os.getenv("CRAWLER_SELFTEST_SHAREPOINT_SITE")
```

## 4. Functional Requirements

**PSCP-FR-01: Test Environment Setup**
- Create document library with specified name
- Upload specified number of .txt files with unique content
- Break permission inheritance on specified number of items
- Assign test permission to broken items (use existing SharePoint group)

**PSCP-FR-02: Test Environment Teardown**
- Delete document library and all contents
- No orphaned permissions or items

**PSCP-FR-03: Core Functionality Tests**
- Test each API capability from INFO document Section 10
- Report pass/fail with error details
- Output working code snippets for implementation

**PSCP-FR-04: Performance Tests**
- Measure time for each operation type
- Compare against INFO document estimates
- Test pagination with 6000 items
- Test batching effectiveness

## 5. Design Decisions

**PSCP-DD-01:** Use `Office365-REST-Python-Client` as primary library. Rationale: Already assessed in INFO document; provides `execute_batch()` and OData query support. [ASSUMED]

**PSCP-DD-02:** Create simple .txt files with sequential names (`file_001.txt` to `file_NNN.txt`). Rationale: Minimal overhead, easy to verify counts.

**PSCP-DD-03:** Break inheritance on first N items (not random). Rationale: Deterministic, easy to verify in tests.

**PSCP-DD-04:** Use existing SharePoint Visitors group for test permissions. Rationale: No group creation needed; always exists on sites. [ASSUMED]

**PSCP-DD-05:** Scripts are standalone (not FastAPI endpoints). Rationale: POC validation, not production code.

## 6. Script Specifications

### 6.1 Prerequisite Script (00)

**00_validate_prerequisites.py**
```
├─> Load env vars
├─> Verify CRAWLER_SELFTEST_SHAREPOINT_SITE is set
├─> Authenticate with certificate
├─> Test Sites.Selected access (try ctx.web.get())
│   └─> If 403: Print "Sites.Selected grant missing for this site"
├─> Test Graph API access (try get user info)
└─> Print summary: "All prerequisites OK" or list failures
```

### 6.2 Setup Scripts (01A/01B)

**01A_create_library_with_50_files_10_broken_inheritance.py**
```
├─> Load env vars (CRAWLER_SELFTEST_SHAREPOINT_SITE, CRAWLER_CLIENT_ID, etc.)
├─> Authenticate with certificate
├─> Create library "POC_PermissionTest_50"
├─> Upload 50 files (file_001.txt to file_050.txt)
├─> Break inheritance on items 1-10
├─> Add Visitors group with Read permission to broken items
└─> Print summary (created, broken count)
```

**01A_delete_library_with_50_files_10_broken_inheritance.py**
```
├─> Load env vars
├─> Authenticate
├─> Delete library "POC_PermissionTest_50"
└─> Print confirmation
```

**01B_create_library_with_6000_files_30_broken_inheritance.py**
- Same as 01A but: 6000 files, 30 broken, library name `POC_PermissionTest_6000`
- Use batching for file upload (100 files per batch)
- Show progress every 500 files

**01B_delete_library_with_6000_files_30_broken_inheritance.py**
- Delete library `POC_PermissionTest_6000`

### 6.3 Test Scripts (02A/02B)

**02A_test_poc_core_functionality.py**

Test cases executed against `POC_PermissionTest_50`:

```
TC-01: Basic Authentication
├─> Connect with certificate auth
└─> Expected: No 401 errors

TC-02: Web Properties
├─> ctx.web.get().select(["Title", "Url"])
└─> Expected: Returns site title and URL

TC-03: List Enumeration
├─> ctx.web.lists.get()
├─> Filter by BaseTemplate == 101
└─> Expected: Document libraries including POC_PermissionTest_50

TC-04: List Items with HasUniqueRoleAssignments (CRITICAL)
├─> list.items.get().select(["ID", "FileRef", "HasUniqueRoleAssignments"]).top(100)
└─> Expected: All 50 items with HasUniqueRoleAssignments field present

TC-05: Verify Broken Inheritance Count
├─> Filter items where HasUniqueRoleAssignments == True
└─> Expected: Exactly 10 items

TC-06: Role Assignments with Expansion (CRITICAL)
├─> ctx.web.role_assignments.get().expand(["Member", "RoleDefinitionBindings"])
├─> Expected: Principal info + permission level names
└─> Verify: Permission level NAME accessible (e.g., "Full Control", "Read")

TC-07: Item Role Assignments
├─> item.role_assignments.get().expand(["Member", "RoleDefinitionBindings"])
└─> Expected: Visitors group with Read permission

TC-08: SharePoint Groups
├─> ctx.web.site_groups.get()
├─> group.users.get()
├─> Expected: Group list with members
└─> Verify: Member's source group ID accessible for ViaGroup tracking

TC-09: Graph API - Transitive Members (Security Groups)
├─> client.groups.by_group_id(id).transitive_members.get()
└─> Expected: Flat list of all nested members (Security Groups only)

TC-10: Batch Execution
├─> Queue 5 operations, call execute_batch()
└─> Expected: All results populated, fewer HTTP calls

TC-11: M365 Group Detection
├─> Find Azure AD group with login name containing "_o" suffix
├─> Verify: Can detect M365 Group vs Security Group
└─> Note: M365 Groups use /members (no transitiveMembers)
```

**02B_test_poc_performance.py**

Performance tests against `POC_PermissionTest_6000`:

```
PERF-01: Full Item Enumeration
├─> Enumerate all 6000 items with HasUniqueRoleAssignments
├─> Measure time, count pagination calls
└─> Compare: INFO estimate ~2-4 sec (2 pagination calls)

PERF-02: Bulk Select vs Naive
├─> Method A: Single query with $select (bulk)
├─> Method B: Per-item HasUniqueRoleAssignments check (naive, sample 100 items)
├─> Compare times
└─> Expected: Bulk is 10-100x faster

PERF-03: Batched RoleAssignments
├─> Load RoleAssignments for 30 broken items
├─> Method A: execute_batch() with 100 items per batch
├─> Method B: Sequential calls (for comparison)
└─> Measure time difference

PERF-04: Pagination Verification
├─> Verify pagination works correctly
├─> NOTE: `$skip` is IGNORED by SharePoint for list items [TESTED]
├─> Use `$skiptoken=Paged=TRUE&p_ID=<last_id>` or follow `odata.nextLink`
├─> Ensure no items missed across pages
└─> Count: Should be exactly 6000
```

## 7. Test Cases

### 7.1 Core Functionality (02A)

- **TC-01**: Basic Authentication - connect, no 401
- **TC-02**: Web Properties - `$select` works
- **TC-03**: List Enumeration - filter by BaseTemplate
- **TC-04**: List Items with HasUniqueRoleAssignments - field present in response
- **TC-05**: Verify Broken Inheritance Count - 10 items with broken inheritance
- **TC-06**: Role Assignments with Expansion - `$expand` returns nested data + permission level NAME
- **TC-07**: Item Role Assignments - per-item permissions accessible
- **TC-08**: SharePoint Groups - enumeration, members, source group ID for ViaGroup
- **TC-09**: Graph API Transitive Members - Security Group nested resolution
- **TC-10**: Batch Execution - `execute_batch()` works
- **TC-11**: M365 Group Detection - distinguish from Security Groups via `_o` suffix

### 7.2 Performance (02B)

- **PERF-01**: Full enumeration timing (6000 items)
- **PERF-02**: Bulk vs naive comparison
- **PERF-03**: Batched vs sequential RoleAssignments
- **PERF-04**: Pagination correctness

## 8. Expected Output

### 8.1 Test Report Format

```
===============================================
Permission Scanner POC - Core Functionality
===============================================
Site: https://contoso.sharepoint.com/sites/TestSite
Library: POC_PermissionTest_50
Date: 2026-02-03 12:00:00
===============================================

TC-01: Basic Authentication .............. PASS
TC-02: Web Properties .................... PASS
TC-03: List Enumeration .................. PASS
TC-04: HasUniqueRoleAssignments Select ... PASS
  - All 50 items returned with field
TC-05: Broken Inheritance Count .......... PASS
  - Expected: 10, Actual: 10
TC-06: Role Assignments Expansion ........ PASS
  - Permission level names accessible
TC-07: Item Role Assignments ............. PASS
TC-08: SharePoint Groups ................. PASS
  - Source group ID accessible for ViaGroup
TC-09: Graph Transitive Members .......... SKIP (no Azure AD group in test)
TC-10: Batch Execution ................... PASS
TC-11: M365 Group Detection .............. SKIP (no M365 group in test)

===============================================
SUMMARY: 9 PASS, 0 FAIL, 2 SKIP
===============================================
```

### 8.2 Performance Report Format

```
===============================================
Permission Scanner POC - Performance
===============================================
Site: https://contoso.sharepoint.com/sites/TestSite
Library: POC_PermissionTest_6000
Date: 2026-02-03 12:05:00
===============================================

PERF-01: Full Item Enumeration
  - Items: 6000
  - Time: 1.8 sec
  - API calls: 2 (pagination)
  - INFO estimate: ~1.2 sec
  - Status: WITHIN RANGE

PERF-02: Bulk vs Naive
  - Bulk (6000 items): 1.8 sec
  - Naive (100 items sample): 12.3 sec
  - Extrapolated naive (6000): ~12 min
  - Speedup: 400x
  - Status: PASS

PERF-03: Batched RoleAssignments (30 items)
  - Batched (items_per_batch=100): 0.4 sec
  - Sequential: 4.2 sec
  - Speedup: 10x
  - Status: PASS

PERF-04: Pagination
  - Total counted: 6000
  - Expected: 6000
  - Status: PASS

===============================================
SUMMARY: All performance tests passed
===============================================
```

### 8.3 Results Document

Create `_POC_PERMISSION_SCANNER_RESULTS.md` after running tests with:
- Pass/fail status for each test
- Actual vs expected performance numbers
- Working code snippets
- Permission upgrade requirements (if any)
- Recommendations for implementation

## 9. Document History

**[2026-02-03 14:05]**
- Added: `$skip` limitation to MUST-NOT-FORGET (SharePoint ignores for list items) [TESTED]
- Added: Throttling note for production implementation
- Changed: PERF-04 to note correct pagination method (`$skiptoken`)

**[2026-02-03 12:16]**
- Changed: Target folder from `src/routers_v2/permission_scanner_poc/` to `src/pocs/permission_scanner/`

**[2026-02-03 12:12]**
- Clarified: Certificate path pattern `os.path.join(LOCAL_PERSISTENT_STORAGE_PATH, CRAWLER_CLIENT_CERTIFICATE_PFX_FILE)`
- Clarified: Must use `connect_to_site_using_client_id_and_certificate()` from existing middleware

**[2026-02-03 12:10]**
- Added: 00_validate_prerequisites.py script (checks Sites.Selected grant)
- Added: TC-11 for M365 Group detection via `_o` suffix
- Changed: Library A broken inheritance from 30 (60%) to 10 (20%) for realistic ratio
- Changed: Filenames updated to reflect 10 broken items
- Clarified: TC-06 must verify permission level NAME is accessible
- Clarified: TC-08 must verify source group ID for ViaGroup tracking
- Clarified: TC-09 applies to Security Groups only (not M365)
- Fixed: PERF-01 estimate to ~2-4 sec (2 pagination calls)

**[2026-02-03 12:06]**
- Fixed: Expanded POC acronym on first use
- Fixed: Removed invalid Doc ID reference from INFO dependency
- Added: Verification labels [ASSUMED], [VERIFIED] per workflow rules

**[2026-02-03 12:04]**
- Initial specification created
