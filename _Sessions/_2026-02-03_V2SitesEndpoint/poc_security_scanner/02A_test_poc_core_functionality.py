"""
02A_test_poc_core_functionality.py
Tests core API functionality against POC_PermissionTest_50 library.
"""
import sys
from typing import Tuple
from _poc_utils import get_poc_config, get_sharepoint_context, print_header, print_result, print_skip, print_summary

LIBRARY_NAME = "POC_PermissionTest_50"
EXPECTED_FILE_COUNT = 50
EXPECTED_BROKEN_COUNT = 10


# TC-01: Basic Authentication - connect with certificate auth
def tc_01_basic_auth(ctx) -> Tuple[bool, str]:
    print("  Connecting with certificate auth...")
    web = ctx.web.get().execute_query()
    title = web.properties.get('Title', '[UNKNOWN]')
    return True, f"Connected to site_title='{title}'"

# TC-02: Web Properties - $select works
def tc_02_web_properties(ctx) -> Tuple[bool, str]:
    print("  Querying web with $select=['Title', 'Url']...")
    web = ctx.web.get().select(["Title", "Url"]).execute_query()
    title = web.properties.get('Title')
    url = web.properties.get('Url')
    if title and url:
        return True, f"title='{title}', url='{url[:50]}...'"
    return False, "Missing Title or Url in response"

# TC-03: List Enumeration - filter by BaseTemplate
def tc_03_list_enumeration(ctx) -> Tuple[bool, str]:
    print("  Enumerating lists with BaseTemplate=101...")
    lists = ctx.web.lists.get().execute_query()
    doc_libs = [lst for lst in lists if lst.properties.get('BaseTemplate') == 101]
    found = any(lst.properties.get('Title') == LIBRARY_NAME for lst in doc_libs)
    if found:
        return True, f"{len(doc_libs)} document libraries found, including '{LIBRARY_NAME}'"
    return False, f"Library '{LIBRARY_NAME}' not found. Run 01A_create first."


# TC-04: List Items with HasUniqueRoleAssignments (CRITICAL)
def tc_04_has_unique_role_assignments(ctx, library) -> Tuple[bool, str]:
    print("  Querying items with $select=['ID', 'FileRef', 'HasUniqueRoleAssignments']...")
    items = library.items.get().select(["ID", "FileRef", "HasUniqueRoleAssignments"]).top(100).execute_query()
    print(f"    {len(items)} items retrieved.")
    if len(items) == 0:
        return False, "No items found in library"
    first_item = items[0]
    props = first_item.properties
    if 'HasUniqueRoleAssignments' not in props:
        return False, "STOP: HasUniqueRoleAssignments NOT in response. API does not support this field."
    return True, f"{len(items)} items have HasUniqueRoleAssignments field"

# TC-05: Verify Broken Inheritance Count
def tc_05_broken_inheritance_count(ctx, library) -> Tuple[bool, str]:
    print("  Counting items with HasUniqueRoleAssignments=True...")
    items = library.items.get().select(["ID", "HasUniqueRoleAssignments"]).top(100).execute_query()
    broken_count = sum(1 for item in items if item.properties.get('HasUniqueRoleAssignments') == True)
    print(f"    {broken_count} items with broken inheritance found.")
    if broken_count == EXPECTED_BROKEN_COUNT:
        return True, f"expected={EXPECTED_BROKEN_COUNT}, actual={broken_count}"
    return False, f"expected={EXPECTED_BROKEN_COUNT}, actual={broken_count}"


# TC-06: Role Assignments with Expansion (CRITICAL)
def tc_06_role_assignments_expansion(ctx) -> Tuple[bool, str]:
    print("  Querying role_assignments with $expand=['Member', 'RoleDefinitionBindings']...")
    role_assignments = ctx.web.role_assignments.get().expand(["Member", "RoleDefinitionBindings"]).execute_query()
    print(f"    {len(role_assignments)} role assignments retrieved.")
    if len(role_assignments) == 0:
        return False, "No role assignments found"
    first_ra = role_assignments[0]
    member = first_ra.member
    if not member:
        return False, "Member not expanded in response"
    bindings = first_ra.role_definition_bindings
    if len(bindings) == 0:
        return False, "RoleDefinitionBindings not expanded"
    first_binding = bindings[0]
    role_name = first_binding.properties.get('Name', '')
    if not role_name:
        return False, "Permission level NAME not accessible"
    return True, f"Member + RoleDefinitionBindings expanded, sample_role='{role_name}'"


# TC-07: Item Role Assignments
def tc_07_item_role_assignments(ctx, library) -> Tuple[bool, str]:
    print("  Finding first item with broken inheritance...")
    items = library.items.get().select(["ID", "HasUniqueRoleAssignments"]).top(20).execute_query()
    broken_item = None
    for item in items:
        if item.properties.get('HasUniqueRoleAssignments') == True:
            broken_item = item
            break
    if not broken_item:
        return False, "No item with broken inheritance found"
    item_id = broken_item.properties.get('ID')
    print(f"    Found item ID={item_id}, querying role_assignments...")
    item_ra = broken_item.role_assignments.get().expand(["Member", "RoleDefinitionBindings"]).execute_query()
    if len(item_ra) == 0:
        return False, "No role assignments on broken item"
    return True, f"item ID={item_id} has {len(item_ra)} role assignments"


# TC-08: SharePoint Groups - enumeration and members
def tc_08_sharepoint_groups(ctx) -> Tuple[bool, str]:
    print("  Querying site_groups...")
    groups = ctx.web.site_groups.get().execute_query()
    print(f"    {len(groups)} groups found.")
    if len(groups) == 0:
        return False, "No site groups found"
    first_group = groups[0]
    group_id = first_group.properties.get('Id')
    print(f"    Querying users for group ID={group_id}...")
    users = first_group.users.get().execute_query()
    if not group_id:
        return False, "Group ID not accessible for ViaGroup tracking"
    return True, f"{len(groups)} groups found, first group ID={group_id} has {len(users)} members"


# TC-09: Graph API - Transitive Members (Security Groups only)
def tc_09_graph_transitive_members(ctx) -> Tuple[bool, str, bool]:
    # This requires an Azure AD Security Group in the site - skip if none exists
    return None, "Requires Azure AD Security Group in site", True

# TC-10: Batch Execution - execute_batch() works
def tc_10_batch_execution(ctx) -> Tuple[bool, str]:
    print("  Queueing 4 operations (web title, web url, lists, groups)...")
    web1 = ctx.web.get().select(["Title"])
    web2 = ctx.web.get().select(["Url"])
    lists_query = ctx.web.lists.get()
    groups_query = ctx.web.site_groups.get()
    print("  Executing batch...")
    ctx.execute_batch()
    title = web1.properties.get('Title')
    url = web2.properties.get('Url')
    list_count = len(lists_query)
    group_count = len(groups_query)
    if title and url and list_count > 0 and group_count > 0:
        return True, f"4 queries batched: title='{title}', {list_count} lists, {group_count} groups"
    return False, "Some batch results missing"

# TC-11: M365 Group Detection - distinguish via _o suffix
def tc_11_m365_group_detection(ctx) -> Tuple[bool, str, bool]:
    # This requires an M365 Group in the site permissions - skip if none exists
    return None, "Requires M365 Group in site", True


def main():
    passed = 0
    failed = 0
    skipped = 0
    
    try:
        config = get_poc_config()
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    print_header("Core Functionality Tests", config)
    print(f"Library: {LIBRARY_NAME}")
    print()
    
    ctx = get_sharepoint_context(config)
    
    # Get library reference
    try:
        library = ctx.web.lists.get_by_title(LIBRARY_NAME)
        ctx.load(library)
        ctx.execute_query()
    except Exception as e:
        print(f"ERROR: Library {LIBRARY_NAME} not found. Run 01A_create first.")
        print(f"  Details: {e}")
        sys.exit(1)
    
    # Run test cases
    test_cases = [
        ("TC-01: Basic Authentication", lambda: tc_01_basic_auth(ctx)),
        ("TC-02: Web Properties", lambda: tc_02_web_properties(ctx)),
        ("TC-03: List Enumeration", lambda: tc_03_list_enumeration(ctx)),
        ("TC-04: HasUniqueRoleAssignments", lambda: tc_04_has_unique_role_assignments(ctx, library)),
        ("TC-05: Broken Inheritance Count", lambda: tc_05_broken_inheritance_count(ctx, library)),
        ("TC-06: Role Assignments Expansion", lambda: tc_06_role_assignments_expansion(ctx)),
        ("TC-07: Item Role Assignments", lambda: tc_07_item_role_assignments(ctx, library)),
        ("TC-08: SharePoint Groups", lambda: tc_08_sharepoint_groups(ctx)),
        ("TC-09: Graph Transitive Members", lambda: tc_09_graph_transitive_members(ctx)),
        ("TC-10: Batch Execution", lambda: tc_10_batch_execution(ctx)),
        ("TC-11: M365 Group Detection", lambda: tc_11_m365_group_detection(ctx)),
    ]
    
    total = len(test_cases)
    for i, (name, test_func) in enumerate(test_cases, 1):
        print(f"[ {i} / {total} ] {name}")
        try:
            result = test_func()
            # Handle skip case (3-tuple with skip flag)
            if isinstance(result, tuple) and len(result) == 3 and result[2] == True:
                print_skip(name, result[1])
                skipped += 1
            elif result[0]:
                print_result(name, True, result[1])
                passed += 1
            else:
                print_result(name, False, result[1])
                failed += 1
        except Exception as e:
            print_result(name, False, f"Exception -> {e}")
            failed += 1
    
    print_summary(passed, failed, skipped)
    
    # STOP/GO decision
    print()
    critical_tests = ["TC-04", "TC-06"]
    critical_failed = any(name.startswith(tc) for tc in critical_tests 
                         for name, _ in test_cases 
                         if name.startswith(tc))
    
    if failed == 0:
        print("DECISION: GO - All core functionality tests passed.")
    elif any("TC-04" in name or "TC-06" in name for name, test_func in test_cases):
        # Check if critical tests failed
        print("DECISION: Review results - check if critical tests (TC-04, TC-06) passed.")
    
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
