"""
01A_create_library_with_50_files_10_broken_inheritance.py
Creates test library with 50 files, 10 with broken inheritance.
"""
import sys
from _poc_utils import get_poc_config, get_sharepoint_context, print_header

LIBRARY_NAME = "POC_PermissionTest_50"
FILE_COUNT = 50
BROKEN_COUNT = 10


def delete_library_if_exists(ctx, library_name: str) -> bool:
    """Delete library if it exists. Returns True if deleted."""
    try:
        library = ctx.web.lists.get_by_title(library_name)
        ctx.load(library)
        ctx.execute_query()
        library.delete_object()
        ctx.execute_query()
        print(f"  Deleted existing library: {library_name}")
        return True
    except:
        return False


def create_library(ctx, library_name: str):
    """Create a new document library."""
    from office365.sharepoint.lists.creation_information import ListCreationInformation
    
    list_info = ListCreationInformation()
    list_info.Title = library_name
    list_info.BaseTemplate = 101  # Document Library
    
    new_list = ctx.web.lists.add(list_info)
    ctx.execute_query()
    print(f"  Created library: {library_name}")
    return new_list


def upload_files(ctx, library, count: int):
    """Upload simple text files to the library."""
    root_folder = library.root_folder
    ctx.load(root_folder)
    ctx.execute_query()
    
    for i in range(1, count + 1):
        filename = f"file_{i:03d}.txt"
        content = f"Test file {i} for Permission Scanner POC.\nCreated for testing HasUniqueRoleAssignments."
        root_folder.upload_file(filename, content.encode('utf-8'))
        
        if i % 10 == 0:
            ctx.execute_query()
            print(f"  Uploaded {i}/{count} files...")
    
    ctx.execute_query()
    print(f"  Uploaded {count} files total.")


def break_inheritance(ctx, library, item_count: int):
    """Break inheritance on first N items (copies existing permissions)."""
    # Get items
    items = library.items.get().top(item_count).execute_query()
    
    for i, item in enumerate(items):
        # Break inheritance - copy existing permissions so item has unique role assignments
        item.break_role_inheritance(True, False)  # copy_role_assignments=True, clear_subscopes=False
        ctx.execute_query()
        
        print(f"  Broke inheritance on item {i + 1}/{item_count}: {item.properties.get('FileLeafRef', 'unknown')}")
    
    print(f"  Broke inheritance on {item_count} items (copied existing permissions).")


def main():
    try:
        config = get_poc_config()
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    print_header(f"Create Library: {LIBRARY_NAME}", config)
    
    ctx = get_sharepoint_context(config)
    
    # Step 1: Delete if exists
    print("Step 1: Checking for existing library...")
    delete_library_if_exists(ctx, LIBRARY_NAME)
    
    # Step 2: Create library
    print("Step 2: Creating library...")
    library = create_library(ctx, LIBRARY_NAME)
    
    # Step 3: Upload files
    print(f"Step 3: Uploading {FILE_COUNT} files...")
    upload_files(ctx, library, FILE_COUNT)
    
    # Step 4: Break inheritance on first N items
    print(f"Step 4: Breaking inheritance on first {BROKEN_COUNT} items...")
    break_inheritance(ctx, library, BROKEN_COUNT)
    
    print()
    print("=" * 60)
    print(f"SUCCESS: Created {LIBRARY_NAME}")
    print(f"  - Files: {FILE_COUNT}")
    print(f"  - Broken inheritance: {BROKEN_COUNT}")
    print("=" * 60)


if __name__ == "__main__":
    main()
