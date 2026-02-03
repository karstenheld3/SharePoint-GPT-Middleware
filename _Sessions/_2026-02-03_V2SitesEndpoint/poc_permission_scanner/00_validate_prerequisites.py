"""
00_validate_prerequisites.py
Validates all prerequisites before running POC tests.
"""
import sys
from _poc_utils import get_poc_config, get_sharepoint_context, print_header, print_result, print_skip, print_summary


def main():
    passed = 0
    failed = 0
    skipped = 0
    
    # Test 1: Load configuration
    try:
        config = get_poc_config()
        print_result("TC-00-01: Environment Variables", True, "All required vars present")
        passed += 1
    except ValueError as e:
        print_result("TC-00-01: Environment Variables", False, str(e))
        failed += 1
        print_summary(passed, failed, skipped)
        sys.exit(1)
    
    print_header("Prerequisite Validation", config)
    
    # Test 2: SharePoint connection (Sites.Selected)
    try:
        ctx = get_sharepoint_context(config)
        web = ctx.web.get().execute_query()
        site_title = web.properties.get('Title', 'Unknown')
        print_result("TC-00-02: SharePoint Connection", True, f"Site: {site_title}")
        passed += 1
    except Exception as e:
        error_msg = str(e)
        if '403' in error_msg or 'Forbidden' in error_msg:
            print_result("TC-00-02: SharePoint Connection", False, 
                        "Sites.Selected grant missing for this site. Run: "
                        "Grant-PnPAzureADAppSitePermission -AppId $clientId -Site $siteUrl -Permissions FullControl")
        else:
            print_result("TC-00-02: SharePoint Connection", False, error_msg)
        failed += 1
        print_summary(passed, failed, skipped)
        sys.exit(1)
    
    # Test 3: List enumeration (basic API access)
    try:
        lists = ctx.web.lists.get().execute_query()
        list_count = len(lists)
        print_result("TC-00-03: List Enumeration", True, f"Found {list_count} lists")
        passed += 1
    except Exception as e:
        print_result("TC-00-03: List Enumeration", False, str(e))
        failed += 1
    
    # Test 4: Site groups access
    try:
        groups = ctx.web.site_groups.get().execute_query()
        group_count = len(groups)
        print_result("TC-00-04: Site Groups Access", True, f"Found {group_count} groups")
        passed += 1
    except Exception as e:
        print_result("TC-00-04: Site Groups Access", False, str(e))
        failed += 1
    
    # Test 5: Graph API (skip - requires Azure AD group in site)
    print_skip("TC-00-05: Graph API Access", "Requires Azure AD group in site - tested in TC-09")
    skipped += 1
    
    print_summary(passed, failed, skipped)
    
    if failed == 0:
        print("\nAll prerequisites OK. Ready to run POC tests.")
        sys.exit(0)
    else:
        print("\nSome prerequisites failed. Fix issues before running POC tests.")
        sys.exit(1)


if __name__ == "__main__":
    main()
