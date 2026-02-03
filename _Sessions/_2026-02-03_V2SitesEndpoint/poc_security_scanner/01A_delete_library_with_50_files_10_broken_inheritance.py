"""
01A_delete_library_with_50_files_10_broken_inheritance.py
Deletes the test library POC_PermissionTest_50.
"""
import sys
from _poc_utils import get_poc_config, get_sharepoint_context, print_header

LIBRARY_NAME = "POC_PermissionTest_50"


def main():
    try:
        config = get_poc_config()
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    print_header(f"Delete Library: {LIBRARY_NAME}", config)
    
    ctx = get_sharepoint_context(config)
    
    try:
        library = ctx.web.lists.get_by_title(LIBRARY_NAME)
        ctx.load(library)
        ctx.execute_query()
        
        library.delete_object()
        ctx.execute_query()
        
        print(f"SUCCESS: Deleted library: {LIBRARY_NAME}")
    except Exception as e:
        if 'does not exist' in str(e).lower() or '404' in str(e):
            print(f"WARNING: Library not found: {LIBRARY_NAME}")
        else:
            print(f"ERROR: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
