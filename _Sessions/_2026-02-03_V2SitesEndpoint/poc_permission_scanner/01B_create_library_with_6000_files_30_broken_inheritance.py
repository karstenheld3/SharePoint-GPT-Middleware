"""
01B_create_library_with_6000_files_30_broken_inheritance.py
Creates test library with 6000 files, 30 with broken inheritance.
Uses batching for efficient upload.
"""
import sys
from _poc_utils import get_poc_config, get_sharepoint_context, print_header

LIBRARY_NAME = "POC_PermissionTest_6000"
FILE_COUNT = 6000
BROKEN_COUNT = 30
BATCH_SIZE = 100
PROGRESS_INTERVAL = 500


def delete_library_if_exists(ctx, library_name: str) -> bool:
    """Delete library if it exists."""
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
    list_info.BaseTemplate = 101
    
    new_list = ctx.web.lists.add(list_info)
    ctx.execute_query()
    print(f"  Created library: {library_name}")
    return new_list


def upload_files_sequential(ctx, library, count: int, progress_interval: int):
    """Upload files sequentially (batching doesn't work with file content)."""
    root_folder = library.root_folder
    ctx.load(root_folder)
    ctx.execute_query()
    
    for i in range(1, count + 1):
        filename = f"file_{i:05d}.txt"
        content = f"Test file {i} for Permission Scanner POC performance testing."
        root_folder.upload_file(filename, content.encode('utf-8')).execute_query()
        
        # Progress output
        if i % progress_interval == 0:
            print(f"  Uploaded {i}/{count} files...")
    
    print(f"  Uploaded {count} files total.")


def break_inheritance(ctx, library, item_count: int):
    """Break inheritance on first N items (copies existing permissions)."""
    items = library.items.get().top(item_count).execute_query()
    
    for i, item in enumerate(items):
        item.break_role_inheritance(True, False)  # copy_role_assignments, clear_subscopes
        ctx.execute_query()
        
        if (i + 1) % 10 == 0:
            print(f"  Broke inheritance on {i + 1}/{item_count} items...")
    
    print(f"  Broke inheritance on {item_count} items total.")


def main():
    try:
        config = get_poc_config()
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    print_header(f"Create Library: {LIBRARY_NAME}", config)
    print(f"NOTE: This will create {FILE_COUNT} files. This may take several minutes.")
    print()
    
    ctx = get_sharepoint_context(config)
    
    print("Step 1: Checking for existing library...")
    delete_library_if_exists(ctx, LIBRARY_NAME)
    
    print("Step 2: Creating library...")
    library = create_library(ctx, LIBRARY_NAME)
    
    print(f"Step 3: Uploading {FILE_COUNT} files (this will take several minutes)...")
    upload_files_sequential(ctx, library, FILE_COUNT, PROGRESS_INTERVAL)
    
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
