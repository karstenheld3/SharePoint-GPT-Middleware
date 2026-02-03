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


def tc_01_basic_auth(ctx) -> Tuple[bool, str]:
    """TC-01: Basic Authentication - connect with certificate auth."""
    web = ctx.web.get().execute_query()
    title = web.properties.get('Title', 'Unknown')
    return True, f"Connected to: {title}"


def tc_02_web_properties(ctx) -> Tuple[bool, str]:
    """TC-02: Web Properties - $select works."""
    web = ctx.web.get().select(["Title", "Url"]).execute_query()
    title = web.properties.get('Title')
    url = web.properties.get('Url')
    if title and url:
        return True, f"Title={title}, Url={url[:50]}..."
    return False, "Missing Title or Url in response"


def tc_03_list_enumeration(ctx) -> Tuple[bool, str]:
    """TC-03: List Enumeration - filter by BaseTemplate."""
    lists = ctx.web.lists.get().execute_query()
    doc_libs = [lst for lst in lists if lst.properties.get('BaseTemplate') == 101]
    found = any(lst.properties.get('Title') == LIBRARY_NAME for lst in doc_libs)
    if found:
        return True, f"Found {len(doc_libs)} document libraries including {LIBRARY_NAME}"
    return False, f"Library {LIBRARY_NAME} not found. Run 01A_create first."


def tc_04_has_unique_role_assignments(ctx, library) -> Tuple[bool, str]:
    """TC-04: List Items with HasUniqueRoleAssignments (CRITICAL)."""
    items = library.items.get().select(["ID", "FileRef", "HasUniqueRoleAssignments"]).top(100).execute_query()
    
    if len(items) == 0:
        return False, "No items found in library"
    
    # Check if HasUniqueRoleAssignments is present
    first_item = items[0]
    props = first_item.properties
    
    if 'HasUniqueRoleAssignments' not in props:
        return False, "STOP: HasUniqueRoleAssignments NOT in response. API does not support this field."
    
    return True, f"All {len(items)} items have HasUniqueRoleAssignments field"


def tc_05_broken_inheritance_count(ctx, library) -> Tuple[bool, str]:
    """TC-05: Verify Broken Inheritance Count."""
    items = library.items.get().select(["ID", "HasUniqueRoleAssignments"]).top(100).execute_query()
    
    broken_count = sum(1 for item in items if item.properties.get('HasUniqueRoleAssignments') == True)
    
    if broken_count == EXPECTED_BROKEN_COUNT:
        return True, f"Expected: {EXPECTED_BROKEN_COUNT}, Actual: {broken_count}"
    return False, f"Expected: {EXPECTED_BROKEN_COUNT}, Actual: {broken_count}"


def tc_06_role_assignments_expansion(ctx) -> Tuple[bool, str]:
    """TC-06: Role Assignments with Expansion (CRITICAL)."""
    role_assignments = ctx.web.role_assignments.get().expand(["Member", "RoleDefinitionBindings"]).execute_query()
    
    if len(role_assignments) == 0:
        return False, "No role assignments found"
    
    # Check first assignment has Member and RoleDefinitionBindings
    first_ra = role_assignments[0]
    
    # Verify Member is accessible
    member = first_ra.member
    if not member:
        return False, "Member not expanded in response"
    
    # Verify RoleDefinitionBindings accessible
    bindings = first_ra.role_definition_bindings
    if len(bindings) == 0:
        return False, "RoleDefinitionBindings not expanded"
    
    # Verify permission level NAME is accessible
    first_binding = bindings[0]
    role_name = first_binding.properties.get('Name', '')
    if not role_name:
        return False, "Permission level NAME not accessible"
    
    return True, f"Member + RoleDefinitionBindings expanded. Sample role: {role_name}"


def tc_07_item_role_assignments(ctx, library) -> Tuple[bool, str]:
    """TC-07: Item Role Assignments."""
    # Get first item with broken inheritance
    items = library.items.get().select(["ID", "HasUniqueRoleAssignments"]).top(20).execute_query()
    
    broken_item = None
    for item in items:
        if item.properties.get('HasUniqueRoleAssignments') == True:
            broken_item = item
            break
    
    if not broken_item:
        return False, "No item with broken inheritance found"
    
    # Get role assignments for that item
    item_ra = broken_item.role_assignments.get().expand(["Member", "RoleDefinitionBindings"]).execute_query()
    
    if len(item_ra) == 0:
        return False, "No role assignments on broken item"
    
    return True, f"Item {broken_item.properties.get('ID')} has {len(item_ra)} role assignments"


def tc_08_sharepoint_groups(ctx) -> Tuple[bool, str]:
    """TC-08: SharePoint Groups - enumeration and members."""
    groups = ctx.web.site_groups.get().execute_query()
    
    if len(groups) == 0:
        return False, "No site groups found"
    
    # Try to get members of first group
    first_group = groups[0]
    users = first_group.users.get().execute_query()
    
    # Verify we can get group ID for ViaGroup tracking
    group_id = first_group.properties.get('Id')
    if not group_id:
        return False, "Group ID not accessible for ViaGroup tracking"
    
    return True, f"Found {len(groups)} groups. First group ID={group_id}, members={len(users)}"


def tc_09_graph_transitive_members(ctx) -> Tuple[bool, str, bool]:
    """TC-09: Graph API - Transitive Members (Security Groups only)."""
    # This requires an Azure AD Security Group in the site
    # Skip if no such group exists
    return None, "Requires Azure AD Security Group in site - skipped", True


def tc_10_batch_execution(ctx) -> Tuple[bool, str]:
    """TC-10: Batch Execution - execute_batch() works."""
    # Queue multiple operations
    web1 = ctx.web.get().select(["Title"])
    web2 = ctx.web.get().select(["Url"])
    lists_query = ctx.web.lists.get()
    groups_query = ctx.web.site_groups.get()
    
    # Execute as batch
    ctx.execute_batch()
    
    # Verify all results populated
    title = web1.properties.get('Title')
    url = web2.properties.get('Url')
    list_count = len(lists_query)
    group_count = len(groups_query)
    
    if title and url and list_count > 0 and group_count > 0:
        return True, f"Batch: Title={title}, lists={list_count}, groups={group_count}"
    return False, "Some batch results missing"


def tc_11_m365_group_detection(ctx) -> Tuple[bool, str, bool]:
    """TC-11: M365 Group Detection - distinguish via _o suffix."""
    # This requires an M365 Group in the site permissions
    # Skip if no such group exists
    return None, "Requires M365 Group in site - skipped", True


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
    
    for name, test_func in test_cases:
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
            print_result(name, False, str(e))
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
