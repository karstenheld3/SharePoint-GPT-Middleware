"""
02B_test_poc_performance.py
Tests performance against POC_PermissionTest_6000 library.
"""
import sys
import time
from typing import Tuple
from _poc_utils import get_poc_config, get_sharepoint_context, print_header, print_result, print_summary

LIBRARY_NAME = "POC_PermissionTest_6000"
EXPECTED_FILE_COUNT = 6000
EXPECTED_BROKEN_COUNT = 30


def perf_01_full_enumeration(ctx, library) -> Tuple[bool, str, float]:
    """PERF-01: Full Item Enumeration - enumerate all items with HasUniqueRoleAssignments using $skiptoken."""
    print("  Fetching all items using $skiptoken pagination...")
    start = time.time()
    
    all_items = []
    page_count = 0
    last_id = 0
    
    while True:
        page_count += 1
        page_start = time.time()
        
        # Use $filter with ID > last_id to simulate $skiptoken pagination
        # This works because ID is indexed and ordered
        if last_id == 0:
            print(f"  [ {page_count} ] Fetching first page (top 5000)...")
            items = library.items.get().select(["ID", "FileRef", "HasUniqueRoleAssignments"]).top(5000).execute_query()
        else:
            print(f"  [ {page_count} ] Fetching next page (ID > {last_id})...")
            items = library.items.get().select(["ID", "FileRef", "HasUniqueRoleAssignments"]).filter(f"ID gt {last_id}").top(5000).execute_query()
        
        items_list = list(items)
        print(f"    {len(items_list)} items in {time.time() - page_start:.2f}s")
        
        if len(items_list) == 0:
            break
        
        all_items.extend(items_list)
        
        # Get the last ID for next page
        last_id = max(item.properties.get('ID') for item in items_list)
        
        # If we got less than 5000, we're done
        if len(items_list) < 5000:
            break
    
    elapsed = time.time() - start
    
    estimate_min = 2.0
    estimate_max = 6.0  # Allow more time for 6000 items
    
    if len(all_items) >= EXPECTED_FILE_COUNT * 0.9:  # Allow 10% tolerance
        within_estimate = elapsed <= estimate_max * 2  # Allow 2x estimate
        msg = f"{len(all_items)} items in {elapsed:.2f}s ({page_count} pages). Estimate: {estimate_min}-{estimate_max}s"
        return within_estimate, msg, elapsed
    return False, f"Only {len(all_items)} items found, expected ~{EXPECTED_FILE_COUNT}", elapsed


def perf_02_bulk_vs_naive(ctx, library) -> Tuple[bool, str, float, float]:
    """PERF-02: Bulk Select vs Naive - compare $select bulk query vs per-item checks."""
    # Method A: Bulk query with $select
    print("  Method A: Bulk query with $select (100 items)...")
    start_bulk = time.time()
    items_bulk = library.items.get().select(["ID", "HasUniqueRoleAssignments"]).top(100).execute_query()
    bulk_time = time.time() - start_bulk
    print(f"    {len(list(items_bulk))} items in {bulk_time:.3f}s")
    
    # Method B: Naive per-item check (sample 10 items only - too slow for 100)
    print("  Method B: Naive per-item fetch (10 items, extrapolate to 100)...")
    start_naive = time.time()
    items_list = list(items_bulk)
    for i, item in enumerate(items_list[:10]):
        print(f"    [ {i+1} / 10 ] Fetching item ID={item.properties.get('ID')}...")
        single_item = library.items.get_by_id(item.properties.get('ID'))
        ctx.load(single_item)
        ctx.execute_query()
    naive_time = time.time() - start_naive
    print(f"    10 items in {naive_time:.3f}s")
    
    # Extrapolate naive time to 100 items
    naive_time_extrapolated = naive_time * 10
    
    speedup = naive_time_extrapolated / bulk_time if bulk_time > 0 else 0
    
    msg = f"Bulk: {bulk_time:.3f}s (100 items), Naive: {naive_time:.3f}s (10 items, ~{naive_time_extrapolated:.2f}s for 100). Speedup: ~{speedup:.0f}x"
    
    # Pass if bulk is at least 5x faster
    return speedup >= 5, msg, bulk_time, naive_time_extrapolated


def perf_03_batched_role_assignments(ctx, library) -> Tuple[bool, str, float, float]:
    """PERF-03: Batched vs Sequential RoleAssignments."""
    # Get items with broken inheritance
    print("  Finding items with broken inheritance...")
    items = library.items.get().select(["ID", "HasUniqueRoleAssignments"]).top(50).execute_query()
    broken_items = [item for item in items if item.properties.get('HasUniqueRoleAssignments') == True][:10]
    print(f"    {len(broken_items)} items with broken inheritance found")
    
    if len(broken_items) < 5:
        return False, f"Only {len(broken_items)} broken items found, need at least 5", 0, 0
    
    # Method A: Batch
    print(f"  Method A: Batch execute_batch() for {len(broken_items)} items...")
    start_batch = time.time()
    for item in broken_items:
        ra = item.role_assignments.get().expand(["Member"])
    ctx.execute_batch()
    batch_time = time.time() - start_batch
    print(f"    Completed in {batch_time:.3f}s")
    
    # Method B: Sequential
    print(f"  Method B: Sequential execute_query() for {len(broken_items)} items...")
    start_seq = time.time()
    for i, item in enumerate(broken_items):
        print(f"    [ {i+1} / {len(broken_items)} ] Getting role assignments...")
        ra = item.role_assignments.get().expand(["Member"]).execute_query()
    seq_time = time.time() - start_seq
    print(f"    Completed in {seq_time:.3f}s")
    
    speedup = seq_time / batch_time if batch_time > 0 else 0
    
    msg = f"Batch: {batch_time:.3f}s, Sequential: {seq_time:.3f}s ({len(broken_items)} items). Speedup: {speedup:.1f}x"
    
    # Pass if batch is faster (any improvement counts)
    return batch_time < seq_time, msg, batch_time, seq_time


def perf_04_pagination(ctx, library) -> Tuple[bool, str]:
    """PERF-04: Pagination Verification - verify ID > filter pagination retrieves all items."""
    print("  Verifying pagination with ID > filter (replaces broken $skip)...")
    start = time.time()
    
    all_ids = set()
    page_count = 0
    last_id = 0
    
    while True:
        page_count += 1
        page_start = time.time()
        
        if last_id == 0:
            print(f"  [ {page_count} ] Fetching first page...")
            items = library.items.get().select(["ID"]).top(5000).execute_query()
        else:
            print(f"  [ {page_count} ] Fetching page (ID > {last_id})...")
            items = library.items.get().select(["ID"]).filter(f"ID gt {last_id}").top(5000).execute_query()
        
        items_list = list(items)
        print(f"    {len(items_list)} items in {time.time() - page_start:.2f}s")
        
        if len(items_list) == 0:
            break
        
        for item in items_list:
            all_ids.add(item.properties.get('ID'))
        
        last_id = max(item.properties.get('ID') for item in items_list)
        
        if len(items_list) < 5000:
            break
    
    elapsed = time.time() - start
    total = len(all_ids)
    
    if total >= EXPECTED_FILE_COUNT * 0.9:  # Allow 10% tolerance
        msg = f"Pagination OK: {total} unique items in {elapsed:.2f}s ({page_count} pages)"
        return True, msg
    return False, f"Only {total} unique items found, expected ~{EXPECTED_FILE_COUNT}"


def main():
    passed = 0
    failed = 0
    skipped = 0
    
    try:
        config = get_poc_config()
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    print_header("Performance Tests", config)
    print(f"Library: {LIBRARY_NAME}")
    print()
    
    ctx = get_sharepoint_context(config)
    
    # Get library reference
    try:
        library = ctx.web.lists.get_by_title(LIBRARY_NAME)
        ctx.load(library)
        ctx.execute_query()
    except Exception as e:
        print(f"ERROR: Library {LIBRARY_NAME} not found. Run 01B_create first.")
        print(f"  Details: {e}")
        sys.exit(1)
    
    # PERF-01: Full Enumeration
    try:
        result, msg, elapsed = perf_01_full_enumeration(ctx, library)
        print_result("PERF-01: Full Enumeration", result, msg)
        if result:
            passed += 1
        else:
            failed += 1
    except Exception as e:
        print_result("PERF-01: Full Enumeration", False, str(e))
        failed += 1
    
    # PERF-02: Bulk vs Naive
    try:
        result, msg, bulk_t, naive_t = perf_02_bulk_vs_naive(ctx, library)
        print_result("PERF-02: Bulk vs Naive", result, msg)
        if result:
            passed += 1
        else:
            failed += 1
    except Exception as e:
        print_result("PERF-02: Bulk vs Naive", False, str(e))
        failed += 1
    
    # PERF-03: Batched RoleAssignments
    try:
        result, msg, batch_t, seq_t = perf_03_batched_role_assignments(ctx, library)
        print_result("PERF-03: Batched RoleAssignments", result, msg)
        if result:
            passed += 1
        else:
            failed += 1
    except Exception as e:
        print_result("PERF-03: Batched RoleAssignments", False, str(e))
        failed += 1
    
    # PERF-04: Pagination
    try:
        result, msg = perf_04_pagination(ctx, library)
        print_result("PERF-04: Pagination", result, msg)
        if result:
            passed += 1
        else:
            failed += 1
    except Exception as e:
        print_result("PERF-04: Pagination", False, str(e))
        failed += 1
    
    print_summary(passed, failed, skipped)
    
    if failed == 0:
        print("\nAll performance tests passed. Performance estimates validated.")
    
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
