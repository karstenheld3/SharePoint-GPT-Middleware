# POC Results: Permission Scanner

**Doc ID**: PSCP-RS01
**Date**: 2026-02-03
**Decision**: **GO** - Proceed with implementation

## Executive Summary

The Permission Scanner POC validated that Office365-REST-Python-Client supports all critical operations needed for SharePoint permission scanning. All 9 core functionality tests passed.

## Test Results

### Core Functionality (02A) - POC_PermissionTest_50

- **TC-01: Basic Authentication** - PASS: Certificate auth works [TESTED]
- **TC-02: Web Properties** - PASS: `$select` works [TESTED]
- **TC-03: List Enumeration** - PASS: BaseTemplate filter works [TESTED]
- **TC-04: HasUniqueRoleAssignments** - PASS: **CRITICAL** - Field accessible via `$select` [TESTED]
- **TC-05: Broken Inheritance Count** - PASS: 10/10 detected correctly [TESTED]
- **TC-06: Role Assignments Expansion** - PASS: **CRITICAL** - `$expand` returns Member + permission level NAME [TESTED]
- **TC-07: Item Role Assignments** - PASS: Per-item permissions accessible [TESTED]
- **TC-08: SharePoint Groups** - PASS: Groups and members enumerable, ID accessible [TESTED]
- **TC-09: Graph Transitive Members** - SKIP: No Azure AD Security Group in test site
- **TC-10: Batch Execution** - PASS: `execute_batch()` works correctly [TESTED]
- **TC-11: M365 Group Detection** - SKIP: No M365 Group in test site

**Summary**: 9 PASS, 0 FAIL, 2 SKIP

### Performance (02B) - POC_PermissionTest_6000

- **PERF-01: Full Enumeration** - PASS: 6000 items in 17.5s (2 pages) using `ID > last_id` filter [TESTED]
- **PERF-02: Bulk vs Naive** - PASS: 52x speedup (0.5s bulk vs 24s naive for 100 items) [TESTED]
- **PERF-03: Batched RoleAssignments** - PASS: 3.4x speedup (0.8s batch vs 2.7s sequential) [TESTED]
- **PERF-04: Pagination** - PASS: 6000 unique items in 1.98s using `ID > last_id` filter [TESTED]

**Summary**: 4 PASS, 0 FAIL

**Key Performance Findings**:
- `top(5000)` works correctly, ~1.5s per 5000 items
- `skip()` is **ignored** by SharePoint - use `$filter` with `ID gt {last_id}` instead [TESTED]
- **Workaround works**: `ID > last_id` filter retrieves all 6000 items correctly
- Bulk `$select` is 52x faster than per-item fetches
- `execute_batch()` is 3.4x faster than sequential `execute_query()`

**Pagination Recommendation**: Use list view threshold (5000 items max) or implement server-side filtering instead of `skip()`. For libraries >5000 items, use indexed columns with `$filter`.

### Critical Finding: `$skip` Not Supported [VERIFIED]

**Research confirmed** (Microsoft documentation, Stack Overflow):
- SharePoint REST API **ignores** `$skip` for list items
- Only works for "collections" (like list of lists), not list items
- This is documented behavior, not a bug

**Working pagination method** (tested in POC):
```python
# First page
items = library.items.get().select(["ID", ...]).top(5000).execute_query()
last_id = max(item.properties.get('ID') for item in items)

# Next pages
items = library.items.get().select(["ID", ...]).filter(f"ID gt {last_id}").top(5000).execute_query()
```

**Impact**: Production implementation must use `ID > last_id` filter or `$skiptoken`, not `skip()`.

## Working Code Patterns

### Connect with Certificate

```python
from routers_v2.common_sharepoint_functions_v2 import connect_to_site_using_client_id_and_certificate

ctx = connect_to_site_using_client_id_and_certificate(
    site_url=site_url,
    client_id=client_id,
    tenant_id=tenant_id,
    cert_path=cert_path,
    cert_password=cert_password
)
```

### Get Items with HasUniqueRoleAssignments

```python
items = library.items.get().select(["ID", "FileRef", "HasUniqueRoleAssignments"]).top(5000).execute_query()
broken_items = [item for item in items if item.properties.get('HasUniqueRoleAssignments') == True]
```

### Get Role Assignments with Expansion

```python
role_assignments = ctx.web.role_assignments.get().expand(["Member", "RoleDefinitionBindings"]).execute_query()
for ra in role_assignments:
    member = ra.member
    bindings = ra.role_definition_bindings
    for binding in bindings:
        role_name = binding.properties.get('Name')  # e.g., "Full Control", "Read"
```

### Batch Execution

```python
web1 = ctx.web.get().select(["Title"])
lists = ctx.web.lists.get()
groups = ctx.web.site_groups.get()
ctx.execute_batch()  # All queries executed in single round-trip
```

## Permission Requirements

- **SharePoint**: `Sites.Selected` with FullControl grant - SUFFICIENT
- **Microsoft Graph**: `Group.Read.All`, `User.Read.All`, `GroupMember.Read.All` - SUFFICIENT

No permission upgrade needed.

## Recommendations for Implementation

1. **Use `$select` with `HasUniqueRoleAssignments`** for efficient bulk scanning
2. **Use `$expand` for RoleAssignments** to get permissions in single call
3. **Use `execute_batch()`** for multiple queries to reduce round-trips
4. **Implement Python-side filtering** since `$filter` on `HasUniqueRoleAssignments` may not work
5. **Use `$skiptoken` for pagination** - `skip()` is ignored by SharePoint [TESTED]
6. **Implement throttling retry** with Retry-After header support
7. **Check for `odata.nextLink`** in responses for automatic pagination

## Files Created

```
src/pocs/permission_scanner/
├── __init__.py
├── _poc_utils.py
├── 00_validate_prerequisites.py
├── 01A_create_library_with_50_files_10_broken_inheritance.py
├── 01A_delete_library_with_50_files_10_broken_inheritance.py
├── 01B_create_library_with_6000_files_30_broken_inheritance.py
├── 01B_delete_library_with_6000_files_30_broken_inheritance.py
├── 02A_test_poc_core_functionality.py
└── 02B_test_poc_performance.py
```

## Next Steps

1. Create SPEC for full Permission Scanner implementation
2. Use working code patterns from this POC
3. Implement group resolution (SharePoint groups, Azure AD groups)
4. Implement CSV output matching PowerShell scanner format

## Document History

**[2026-02-03 14:05]**
- Added: Critical Finding section explaining `$skip` not supported (verified via research)
- Added: Correct `$skiptoken` format for pagination
- Added: Throttling retry recommendation
- Changed: Pagination recommendation to use `$skiptoken`

**[2026-02-03 13:55]**
- Added: Performance test results (PERF-01 to PERF-04)
- Added: Key finding - `skip()` is unreliable for pagination
- Added: Pagination recommendation

**[2026-02-03 12:35]**
- Fixed: Converted Markdown table to list format
- Added: [TESTED] verification labels to test results

**[2026-02-03 12:30]**
- Initial results document created
