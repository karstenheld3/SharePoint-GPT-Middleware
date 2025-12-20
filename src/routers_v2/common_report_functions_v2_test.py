# Test script for common_report_functions_v2.py
# Run: python -m routers_v2.common_report_functions_v2_test
# Or:  python src/routers_v2/common_report_functions_v2_test.py

import sys, os, tempfile, shutil, json, zipfile
from pathlib import Path
from dataclasses import dataclass

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from routers_v2 import common_report_functions_v2 as rf

# ----------------------------------------- START: Test Infrastructure ------------------------------------------------

@dataclass
class MockConfig:
  LOCAL_PERSISTENT_STORAGE_PATH: str

test_count = 0
pass_count = 0
fail_count = 0

def test(name: str, condition: bool, details: str = ""):
  global test_count, pass_count, fail_count
  test_count += 1
  if condition:
    pass_count += 1
    print(f"  OK: {name}")
  else:
    fail_count += 1
    print(f"  FAIL: {name}" + (f" -> {details}" if details else ""))

def section(name: str):
  print(f"\n{'=' * 60}\n{name}\n{'=' * 60}")

# ----------------------------------------- END: Test Infrastructure --------------------------------------------------


# ----------------------------------------- START: Test Cases ---------------------------------------------------------

def test_type_folder_conversion():
  section("Type/Folder Conversion")
  
  # get_folder_for_type
  test("crawl -> crawls", rf.get_folder_for_type("crawl") == "crawls")
  test("site_scan -> site_scans", rf.get_folder_for_type("site_scan") == "site_scans")
  test("custom -> customs", rf.get_folder_for_type("custom") == "customs")
  
  # get_type_from_folder
  test("crawls -> crawl", rf.get_type_from_folder("crawls") == "crawl")
  test("site_scans -> site_scan", rf.get_type_from_folder("site_scans") == "site_scan")
  test("customs -> custom", rf.get_type_from_folder("customs") == "custom")

def test_create_report(temp_dir: str):
  section("create_report()")
  
  # C1: Valid inputs
  report_id = rf.create_report(
    report_type="crawl",
    filename="2024-01-15_14-25-00_TEST01_all_full",
    files=[("data/file1.csv", b"col1,col2\na,b")],
    metadata={"title": "TEST01 full crawl", "ok": True, "error": ""}
  )
  test("C1: Valid inputs returns report_id", report_id == "crawls/2024-01-15_14-25-00_TEST01_all_full")
  
  # Verify archive exists
  archive_path = Path(temp_dir) / "reports" / "crawls" / "2024-01-15_14-25-00_TEST01_all_full.zip"
  test("C1: Archive file created", archive_path.exists())
  
  # Verify report.json content
  with zipfile.ZipFile(archive_path, 'r') as zf:
    report_json = json.loads(zf.read("report.json").decode("utf-8"))
    test("C1: report_id in metadata", report_json.get("report_id") == report_id)
    test("C1: created_utc in metadata", "created_utc" in report_json)
    test("C1: title preserved", report_json.get("title") == "TEST01 full crawl")
    test("C1: files inventory exists", "files" in report_json)
    test("C1: files inventory has 2 items", len(report_json.get("files", [])) == 2)
  
  # C2: Empty files list
  report_id_empty = rf.create_report(
    report_type="crawl",
    filename="empty_files_test",
    files=[],
    metadata={"title": "Empty test", "ok": True, "error": ""}
  )
  archive_empty = Path(temp_dir) / "reports" / "crawls" / "empty_files_test.zip"
  with zipfile.ZipFile(archive_empty, 'r') as zf:
    test("C2: Empty files - only report.json", zf.namelist() == ["report.json"])
  
  # C3: Files with nested paths, keep structure
  rf.create_report(
    report_type="crawl",
    filename="nested_test",
    files=[
      ("01_files/source01/map.csv", b"data1"),
      ("02_lists/list01/map.csv", b"data2")
    ],
    metadata={"title": "Nested test", "ok": True, "error": ""},
    keep_folder_structure=True
  )
  archive_nested = Path(temp_dir) / "reports" / "crawls" / "nested_test.zip"
  with zipfile.ZipFile(archive_nested, 'r') as zf:
    names = zf.namelist()
    test("C3: Nested paths preserved", "01_files/source01/map.csv" in names and "02_lists/list01/map.csv" in names)
  
  # C4: Files with nested paths, flatten
  rf.create_report(
    report_type="crawl",
    filename="flatten_test",
    files=[
      ("01_files/source01/file1.csv", b"data1"),
      ("02_lists/list01/file2.csv", b"data2")
    ],
    metadata={"title": "Flatten test", "ok": True, "error": ""},
    keep_folder_structure=False
  )
  archive_flatten = Path(temp_dir) / "reports" / "crawls" / "flatten_test.zip"
  with zipfile.ZipFile(archive_flatten, 'r') as zf:
    names = zf.namelist()
    test("C4: Flattened - file1.csv at root", "file1.csv" in names)
    test("C4: Flattened - file2.csv at root", "file2.csv" in names)
    test("C4: Flattened - no nested paths", "01_files/source01/file1.csv" not in names)
  
  # C6: Unknown report_type creates folder anyway
  rf.create_report(
    report_type="custom_type",
    filename="custom_test",
    files=[],
    metadata={"title": "Custom type", "ok": True, "error": ""}
  )
  custom_folder = Path(temp_dir) / "reports" / "custom_types"
  test("C6: Unknown type - folder created", custom_folder.exists())
  
  # C8: Folder auto-created
  site_scan_folder = Path(temp_dir) / "reports" / "site_scans"
  test("C8: Folder doesn't exist before", not site_scan_folder.exists())
  rf.create_report(
    report_type="site_scan",
    filename="site_test",
    files=[],
    metadata={"title": "Site scan", "ok": True, "error": ""}
  )
  test("C8: Folder auto-created", site_scan_folder.exists())
  
  # C11: Binary file content
  binary_content = bytes(range(256))
  rf.create_report(
    report_type="crawl",
    filename="binary_test",
    files=[("binary.bin", binary_content)],
    metadata={"title": "Binary test", "ok": True, "error": ""}
  )
  archive_binary = Path(temp_dir) / "reports" / "crawls" / "binary_test.zip"
  with zipfile.ZipFile(archive_binary, 'r') as zf:
    read_content = zf.read("binary.bin")
    test("C11: Binary content preserved", read_content == binary_content)
  
  # C12: Empty file content
  rf.create_report(
    report_type="crawl",
    filename="empty_content_test",
    files=[("empty.txt", b"")],
    metadata={"title": "Empty content", "ok": True, "error": ""}
  )
  archive_empty_content = Path(temp_dir) / "reports" / "crawls" / "empty_content_test.zip"
  with zipfile.ZipFile(archive_empty_content, 'r') as zf:
    test("C12: Empty file exists", "empty.txt" in zf.namelist())
    test("C12: Empty file is 0 bytes", len(zf.read("empty.txt")) == 0)

def test_list_reports(temp_dir: str):
  section("list_reports()")
  
  # L1: No reports exist (clean state)
  # Clear existing reports
  reports_path = Path(temp_dir) / "reports"
  if reports_path.exists(): shutil.rmtree(reports_path)
  
  result = rf.list_reports()
  test("L1: No reports - returns []", result == [])
  
  # Create some test reports with slight delay to ensure different timestamps
  import time
  rf.create_report("crawl", "report_a", [], {"title": "Report A", "ok": True, "error": ""})
  time.sleep(0.01)
  rf.create_report("crawl", "report_b", [], {"title": "Report B", "ok": False, "error": "Failed"})
  time.sleep(0.01)
  rf.create_report("site_scan", "report_c", [], {"title": "Report C", "ok": True, "error": ""})
  
  # L2: Returns all, sorted by created_utc desc (newest first)
  all_reports = rf.list_reports()
  test("L2: All reports returned", len(all_reports) == 3)
  # Last created should be first (report_c)
  test("L2: Sorted newest first", all_reports[0]["title"] == "Report C")
  
  # L3: Filter by existing type
  crawl_reports = rf.list_reports(type_filter="crawl")
  test("L3: Filter crawl - 2 results", len(crawl_reports) == 2)
  
  site_scan_reports = rf.list_reports(type_filter="site_scan")
  test("L3: Filter site_scan - 1 result", len(site_scan_reports) == 1)
  
  # L4: Filter by non-existent type
  no_reports = rf.list_reports(type_filter="nonexistent")
  test("L4: Non-existent type - returns []", no_reports == [])
  
  # L5: Corrupt zip file (create one manually)
  corrupt_path = reports_path / "crawls" / "corrupt.zip"
  corrupt_path.write_bytes(b"not a zip file")
  result_with_corrupt = rf.list_reports(type_filter="crawl")
  test("L5: Corrupt zip skipped", len(result_with_corrupt) == 2)  # Still 2 valid crawls
  corrupt_path.unlink()  # Clean up
  
  # L6: Zip without report.json
  no_report_json_path = reports_path / "crawls" / "no_report_json.zip"
  with zipfile.ZipFile(no_report_json_path, 'w') as zf:
    zf.writestr("other.txt", "some content")
  result_no_json = rf.list_reports(type_filter="crawl")
  test("L6: Zip without report.json skipped", len(result_no_json) == 2)
  no_report_json_path.unlink()
  
  # L7: Invalid JSON in report.json
  bad_json_path = reports_path / "crawls" / "bad_json.zip"
  with zipfile.ZipFile(bad_json_path, 'w') as zf:
    zf.writestr("report.json", "not valid json {{{")
  result_bad_json = rf.list_reports(type_filter="crawl")
  test("L7: Invalid JSON skipped", len(result_bad_json) == 2)
  bad_json_path.unlink()

def test_get_report_metadata(temp_dir: str):
  section("get_report_metadata()")
  
  # Create a test report
  rf.create_report("crawl", "meta_test", [("file.csv", b"data")], {"title": "Meta Test", "ok": True, "error": ""})
  
  # M1: Valid report_id
  metadata = rf.get_report_metadata("crawls/meta_test")
  test("M1: Valid report_id returns dict", metadata is not None)
  test("M1: Title correct", metadata.get("title") == "Meta Test")
  
  # M2: Non-existent report_id
  result = rf.get_report_metadata("crawls/nonexistent")
  test("M2: Non-existent returns None", result is None)
  
  # M3: Invalid report_id format (no slash)
  result = rf.get_report_metadata("invalid_format")
  test("M3: Invalid format returns None", result is None)
  
  # M4: Corrupt zip
  reports_path = Path(temp_dir) / "reports" / "crawls"
  corrupt_meta_path = reports_path / "corrupt_meta.zip"
  corrupt_meta_path.write_bytes(b"not a zip")
  result = rf.get_report_metadata("crawls/corrupt_meta")
  test("M4: Corrupt zip returns None", result is None)
  corrupt_meta_path.unlink()
  
  # M5: Missing report.json in zip
  no_json_path = reports_path / "no_json_meta.zip"
  with zipfile.ZipFile(no_json_path, 'w') as zf:
    zf.writestr("other.txt", "content")
  result = rf.get_report_metadata("crawls/no_json_meta")
  test("M5: Missing report.json returns None", result is None)
  no_json_path.unlink()

def test_get_report_file(temp_dir: str):
  section("get_report_file()")
  
  # Create test report with files
  rf.create_report("crawl", "file_test", [
    ("data/file1.csv", b"content1"),
    ("data/file2.csv", b"content2"),
    ("binary.bin", bytes([0, 1, 2, 255]))
  ], {"title": "File Test", "ok": True, "error": ""})
  
  # F1: Valid report_id and file_path
  content = rf.get_report_file("crawls/file_test", "data/file1.csv")
  test("F1: Valid file returns bytes", content == b"content1")
  
  # F2: Valid report_id, non-existent file_path
  result = rf.get_report_file("crawls/file_test", "nonexistent.csv")
  test("F2: Non-existent file returns None", result is None)
  
  # F3: Non-existent report_id
  result = rf.get_report_file("crawls/nonexistent", "data/file1.csv")
  test("F3: Non-existent report returns None", result is None)
  
  # F4: report.json can be read
  report_json = rf.get_report_file("crawls/file_test", "report.json")
  test("F4: report.json readable", report_json is not None)
  parsed = json.loads(report_json.decode("utf-8"))
  test("F4: report.json valid JSON", parsed.get("title") == "File Test")
  
  # F5: Binary file
  binary = rf.get_report_file("crawls/file_test", "binary.bin")
  test("F5: Binary file content correct", binary == bytes([0, 1, 2, 255]))

def test_delete_report(temp_dir: str):
  section("delete_report()")
  
  # Create test report
  rf.create_report("crawl", "delete_test", [], {"title": "Delete Test", "ok": True, "error": ""})
  
  # Verify it exists
  archive_path = Path(temp_dir) / "reports" / "crawls" / "delete_test.zip"
  test("D1: Report exists before delete", archive_path.exists())
  
  # D1: Valid report_id - delete and return metadata
  deleted = rf.delete_report("crawls/delete_test")
  test("D1: Delete returns metadata", deleted is not None)
  test("D1: Returned title correct", deleted.get("title") == "Delete Test")
  test("D1: Archive file removed", not archive_path.exists())
  
  # D2: Non-existent report_id
  result = rf.delete_report("crawls/nonexistent")
  test("D2: Non-existent returns None", result is None)

def test_dry_run(temp_dir: str):
  section("dry_run tests")
  
  # Clear reports folder for clean test
  reports_path = Path(temp_dir) / "reports"
  if reports_path.exists(): shutil.rmtree(reports_path)
  
  # DR1: create_report with dry_run=True does NOT create file
  report_id = rf.create_report(
    report_type="crawl",
    filename="dry_run_create_test",
    files=[("data.csv", b"content")],
    metadata={"title": "Dry Run Create", "ok": True, "error": ""},
    dry_run=True
  )
  test("DR1: create_report dry_run returns report_id", report_id == "crawls/dry_run_create_test")
  archive_path = Path(temp_dir) / "reports" / "crawls" / "dry_run_create_test.zip"
  test("DR1: create_report dry_run does NOT create file", not archive_path.exists())
  
  # DR2: Create a real report, then test delete with dry_run
  rf.create_report("crawl", "dry_run_delete_test", [], {"title": "Dry Run Delete", "ok": True, "error": ""})
  archive_delete = Path(temp_dir) / "reports" / "crawls" / "dry_run_delete_test.zip"
  test("DR2: Report created for delete test", archive_delete.exists())
  
  deleted = rf.delete_report("crawls/dry_run_delete_test", dry_run=True)
  test("DR2: delete_report dry_run returns metadata", deleted is not None)
  test("DR2: delete_report dry_run title correct", deleted.get("title") == "Dry Run Delete")
  test("DR2: delete_report dry_run does NOT delete file", archive_delete.exists())
  
  # Clean up - actually delete it
  rf.delete_report("crawls/dry_run_delete_test")
  test("DR2: Cleanup - file now deleted", not archive_delete.exists())

def test_get_report_archive_path(temp_dir: str):
  section("get_report_archive_path()")
  
  # Create test report
  rf.create_report("crawl", "path_test", [], {"title": "Path Test", "ok": True, "error": ""})
  
  # P1: Valid existing report_id
  path = rf.get_report_archive_path("crawls/path_test")
  test("P1: Returns Path object", isinstance(path, Path))
  test("P1: Path is correct", path.name == "path_test.zip")
  
  # P2: Valid format but non-existent
  result = rf.get_report_archive_path("crawls/nonexistent")
  test("P2: Non-existent returns None", result is None)
  
  # P3: Invalid format (no slash)
  result = rf.get_report_archive_path("invalid_format")
  test("P3: Invalid format returns None", result is None)

def test_long_paths(temp_dir: str):
  section("Long path support (Windows)")
  
  # Create a very long filename (>200 chars to trigger long path when combined with temp_dir)
  long_filename = "a" * 200 + "_long_path_test"
  
  # LP1: Create report with long filename
  try:
    report_id = rf.create_report(
      report_type="crawl",
      filename=long_filename,
      files=[("data.csv", b"content")],
      metadata={"title": "Long Path Test", "ok": True, "error": ""}
    )
    test("LP1: create_report with long path succeeds", report_id == f"crawls/{long_filename}")
    
    # LP2: Get metadata works
    metadata = rf.get_report_metadata(report_id)
    test("LP2: get_report_metadata with long path works", metadata is not None)
    test("LP2: Title correct", metadata.get("title") == "Long Path Test")
    
    # LP3: Get file works
    content = rf.get_report_file(report_id, "data.csv")
    test("LP3: get_report_file with long path works", content == b"content")
    
    # LP4: List reports includes long path report
    all_reports = rf.list_reports(type_filter="crawl")
    long_report = next((r for r in all_reports if r.get("title") == "Long Path Test"), None)
    test("LP4: list_reports finds long path report", long_report is not None)
    
    # LP5: Delete works
    deleted = rf.delete_report(report_id)
    test("LP5: delete_report with long path works", deleted is not None)
    
    # LP6: Verify deleted
    result = rf.get_report_archive_path(report_id)
    test("LP6: Report actually deleted", result is None)
    
  except Exception as e:
    test(f"LP: Long path test failed with exception", False, str(e))

# ----------------------------------------- END: Test Cases -----------------------------------------------------------


# ----------------------------------------- START: Main ---------------------------------------------------------------

def main():
  global test_count, pass_count, fail_count
  
  print("\n" + "=" * 60)
  print("common_report_functions_v2.py - Test Suite")
  print("=" * 60)
  
  # Create temp directory for tests
  temp_dir = tempfile.mkdtemp(prefix="report_test_")
  print(f"\nTest directory: {temp_dir}")
  
  try:
    # Configure module with temp directory
    config = MockConfig(LOCAL_PERSISTENT_STORAGE_PATH=temp_dir)
    rf.set_config(config)
    
    # Run all test groups
    test_type_folder_conversion()
    test_create_report(temp_dir)
    test_list_reports(temp_dir)
    test_get_report_metadata(temp_dir)
    test_get_report_file(temp_dir)
    test_delete_report(temp_dir)
    test_dry_run(temp_dir)
    test_get_report_archive_path(temp_dir)
    test_long_paths(temp_dir)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"SUMMARY: {pass_count}/{test_count} tests passed")
    if fail_count > 0:
      print(f"         {fail_count} tests FAILED")
    print("=" * 60 + "\n")
    
    return 0 if fail_count == 0 else 1
    
  finally:
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
    print(f"Cleaned up: {temp_dir}")

if __name__ == "__main__":
  sys.exit(main())

# ----------------------------------------- END: Main -----------------------------------------------------------------
