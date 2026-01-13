# Test script for common_sharepoint_functions_v2.py
# Run: python -m routers_v2.common_sharepoint_functions_v2_test
# Or:  python src/routers_v2/common_sharepoint_functions_v2_test.py
#
# Prerequisites:
# - Domain "AiSearchTest01" must exist with valid SharePoint credentials
# - Environment variables or config must provide SharePoint credentials

import sys, os, tempfile, shutil, json
from pathlib import Path
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from routers_v2 import common_sharepoint_functions_v2 as cspf
from routers_v2.common_logging_functions_v2 import MiddlewareLogger
from routers_v2.common_crawler_functions_v2 import load_domain, DomainConfig

# ----------------------------------------- START: Configuration -----------------------------------------------------

# Test options
delete_downloaded_files_after_test = False

# Domain to test with
test_domain_id = "AiSearchTest01"

# Path to persistent storage - read from environment like app.py does
persistent_storage_path = os.environ.get('LOCAL_PERSISTENT_STORAGE_PATH', r'E:\Dev\RAGFiles2\AzureOpenAiProject')

# SharePoint credentials from environment (same env vars as app.py)
sharepoint_client_id = os.environ.get('CRAWLER_CLIENT_ID', '')
sharepoint_tenant_id = os.environ.get('CRAWLER_TENANT_ID', '')
sharepoint_cert_file = os.environ.get('CRAWLER_CLIENT_CERTIFICATE_PFX_FILE', '')  # Relative to persistent_storage_path
sharepoint_cert_password = os.environ.get('CRAWLER_CLIENT_CERTIFICATE_PASSWORD', '')

# Build full cert path
sharepoint_cert_path = os.path.join(persistent_storage_path, sharepoint_cert_file) if sharepoint_cert_file else ''

# ----------------------------------------- END: Configuration -------------------------------------------------------


# ----------------------------------------- START: Test Infrastructure -----------------------------------------------

test_count = 0
pass_count = 0
fail_count = 0
skip_count = 0
failed_tests = []
skipped_tests = []
section_num = 0
total_sections = 12

def test(name: str, condition: bool, details: str = ""):
  global test_count, pass_count, fail_count
  test_count += 1
  if condition:
    pass_count += 1
    print(f"  OK: {name}")
  else:
    fail_count += 1
    fail_msg = f"{name}" + (f" -> {details}" if details else "")
    failed_tests.append(fail_msg)
    print(f"  FAIL: {fail_msg}")

def skip(name: str, reason: str = ""):
  global skip_count
  skip_count += 1
  skip_msg = f"{name}" + (f" -> {reason}" if reason else "")
  skipped_tests.append(skip_msg)
  print(f"  SKIP: {skip_msg}")

def section(name: str):
  global section_num
  section_num += 1
  print(f"[ {section_num} / {total_sections} ] {name}")
# ----------------------------------------- END: Test Infrastructure -------------------------------------------------


# ----------------------------------------- START: Test Cases --------------------------------------------------------

def test_sharepoint_file_dataclass():
  """Test SharePointFile dataclass creation and serialization. No external dependencies."""
  section("SharePointFile Dataclass")
  
  # Create instance with all fields
  sp_file = cspf.SharePointFile(
    sharepoint_listitem_id=42,
    sharepoint_unique_file_id="abc-123-def",
    filename="test.docx",
    file_type="docx",
    file_size=12345,
    url="https://example.sharepoint.com/sites/test/Shared%20Documents/test.docx",
    raw_url="https://example.sharepoint.com/sites/test/Shared Documents/test.docx",
    server_relative_url="/sites/test/Shared Documents/test.docx",
    last_modified_utc="2024-01-15T14:30:00.000000Z",
    last_modified_timestamp=1705329000
  )
  
  test("Instance created", sp_file is not None)
  test("sharepoint_listitem_id correct", sp_file.sharepoint_listitem_id == 42)
  test("filename correct", sp_file.filename == "test.docx")
  test("file_type correct", sp_file.file_type == "docx")
  test("file_size correct", sp_file.file_size == 12345)
  
  # Test asdict conversion
  sp_dict = asdict(sp_file)
  test("asdict works", isinstance(sp_dict, dict))
  test("asdict has 10 keys", len(sp_dict) == 10)

def test_pem_conversion(cert_path: str, cert_password: str):
  """
  Test PFX to PEM certificate conversion.
  - Verifies PEM file is created from PFX
  - Verifies thumbprint is extracted
  - Verifies idempotency (second call returns cached result)
  """
  section("get_or_create_pem_from_pfx()")
  
  if not cert_path or not os.path.exists(cert_path):
    skip("PEM conversion", f"Certificate not found at '{cert_path}'")
    return None, None
  
  pem_file, thumbprint = cspf.get_or_create_pem_from_pfx(cert_path, cert_password)
  
  test("Returns pem_file path", pem_file is not None and pem_file.endswith('.pem'))
  test("Returns thumbprint", thumbprint is not None and len(thumbprint) > 0)
  test("PEM file created", os.path.exists(pem_file))
  
  # Test idempotency - second call should use cached PEM
  pem_file2, thumbprint2 = cspf.get_or_create_pem_from_pfx(cert_path, cert_password)
  test("Idempotent - same pem_file", pem_file == pem_file2)
  test("Idempotent - same thumbprint", thumbprint == thumbprint2)
  
  return pem_file, thumbprint

def test_connect_to_site(site_url: str, client_id: str, tenant_id: str, cert_path: str, cert_password: str):
  """
  Test SharePoint site connection using certificate authentication.
  - Verifies ClientContext is created
  - Verifies connection works by retrieving web title
  Returns: ClientContext or None if connection fails
  """
  section("connect_to_site_using_client_id_and_certificate()")
  
  if not all([site_url, client_id, tenant_id, cert_path, cert_password]):
    skip("Connection test", "Missing credentials")
    return None
  
  if not os.path.exists(cert_path):
    skip("Connection test", f"Certificate not found at '{cert_path}'")
    return None
  
  try:
    ctx = cspf.connect_to_site_using_client_id_and_certificate(site_url, client_id, tenant_id, cert_path, cert_password)
    test("Context created", ctx is not None)
    
    # Verify connection works by getting web title
    web = ctx.web.get().execute_query()
    web_title = web.properties.get('Title', '')
    test("Connection works - web title retrieved", len(web_title) > 0, f"Title: '{web_title}'")
    print(f"    Connected to: '{web_title}'")
    
    return ctx
  except Exception as e:
    test("Connection succeeds", False, str(e))
    return None

def test_try_get_document_library(ctx, site_url: str, library_url_part: str):
  """
  Test document library retrieval.
  - Verifies valid library path returns library object
  - Verifies invalid library path returns None + error message
  Returns: Library object or None
  """
  section("try_get_document_library()")
  
  if ctx is None:
    skip("Document library test", "No context available")
    return None
  
  # Test with valid library
  library, error = cspf.try_get_document_library(ctx, site_url, library_url_part)
  test("Valid library - returns library", library is not None, error or "")
  test("Valid library - no error", error is None)
  
  if library:
    lib_title = library.properties.get('Title') or cspf.UNKNOWN
    lib_id = library.properties.get('Id') or cspf.UNKNOWN
    print(f"    Using library '{lib_title}' ID={lib_id}")
  
  # Test with invalid library
  bad_library, bad_error = cspf.try_get_document_library(ctx, site_url, "/NonExistent Library 12345")
  test("Invalid library - returns None", bad_library is None)
  test("Invalid library - returns error", bad_error is not None)
  
  return library

def test_get_document_library_files(ctx, document_library, logger: MiddlewareLogger):
  """
  Test file listing from document library.
  - Verifies returns list of SharePointFile instances
  - Verifies file metadata (filename, server_relative_url, file_type)
  - Verifies OData filter query works
  Returns: List of SharePointFile objects
  """
  section("get_document_library_files()")
  
  if ctx is None or document_library is None:
    skip("Get files test", "No context or library available")
    return []
  
  # Get all files (no filter)
  files = cspf.get_document_library_files(ctx, document_library, "", logger)
  test("Returns list", isinstance(files, list))
  test("Returns SharePointFile instances", len(files) == 0 or isinstance(files[0], cspf.SharePointFile))
  print(f"    {len(files)} file{'' if len(files) == 1 else 's'} retrieved.")
  
  if len(files) > 0:
    first_file = files[0]
    test("File has filename", len(first_file.filename) > 0)
    test("File has server_relative_url", len(first_file.server_relative_url) > 0)
    test("File has file_type", first_file.file_type is not None)
    print(f"    First file: '{first_file.filename}' ({first_file.file_type}, {first_file.file_size} bytes)")
  
  # Test with filter (if we have files)
  if len(files) > 0:
    test_filename = files[0].filename
    filter_query = f"FileLeafRef eq '{test_filename}'"
    filtered_files = cspf.get_document_library_files(ctx, document_library, filter_query, logger)
    test("Filter returns results", len(filtered_files) >= 1)
    if len(filtered_files) > 0:
      test("Filter matches filename", filtered_files[0].filename == test_filename)
  
  # Test dry_run - should return empty list but verify access
  dry_files = cspf.get_document_library_files(ctx, document_library, "", logger, dry_run=True)
  test("dry_run returns empty list", dry_files == [])
  
  return files

def test_download_file(ctx, files: list, temp_dir: str):
  """
  Test file download from SharePoint.
  - Verifies file downloads successfully
  - Verifies local file size matches SharePoint
  - Verifies timestamp preservation (last_modified)
  - Verifies invalid path returns error
  """
  section("download_file_from_sharepoint()")
  
  if ctx is None or len(files) == 0:
    skip("Download test", "No context or files available")
    return
  
  # Pick first file to download
  test_file = files[0]
  target_path = os.path.join(temp_dir, "01_files", test_file.filename)
  
  success, error = cspf.download_file_from_sharepoint(
    ctx,
    test_file.server_relative_url,
    target_path,
    preserve_timestamp=True,
    last_modified_timestamp=test_file.last_modified_timestamp
  )
  
  test("Download succeeds", success, error)
  test("File exists locally", os.path.exists(target_path))
  
  if os.path.exists(target_path):
    local_size = os.path.getsize(target_path)
    test("File size matches", local_size == test_file.file_size, f"Local: {local_size}, SharePoint: {test_file.file_size}")
    
    # Check timestamp preservation
    if test_file.last_modified_timestamp > 0:
      local_mtime = int(os.path.getmtime(target_path))
      test("Timestamp preserved", local_mtime == test_file.last_modified_timestamp, f"Local: {local_mtime}, SharePoint: {test_file.last_modified_timestamp}")
  
  # Test download with invalid path
  bad_target_path = os.path.join(temp_dir, "bad.docx")
  bad_success, bad_error = cspf.download_file_from_sharepoint(ctx, "/nonexistent/path/file.docx", bad_target_path)
  test("Invalid path - returns False", bad_success == False)
  test("Invalid path - returns error", len(bad_error) > 0)
  test("Invalid path - no file left behind", not os.path.exists(bad_target_path), f"File exists: {bad_target_path}")
  
  # Test dry_run - should verify file exists but not download
  dry_target = os.path.join(temp_dir, "dry_run_file.docx")
  dry_success, dry_error = cspf.download_file_from_sharepoint(ctx, test_file.server_relative_url, dry_target, dry_run=True)
  test("dry_run succeeds", dry_success, dry_error)
  test("dry_run does not create file", not os.path.exists(dry_target))
  
  # Test dry_run with invalid path - should fail validation
  dry_bad_success, dry_bad_error = cspf.download_file_from_sharepoint(ctx, "/nonexistent/path/file.docx", dry_target, dry_run=True)
  test("dry_run invalid path - returns False", dry_bad_success == False)
  test("dry_run invalid path - returns error", len(dry_bad_error) > 0)

def test_get_list_items(ctx, list_name: str, logger: MiddlewareLogger):
  """
  Test SharePoint list item retrieval.
  - Verifies returns list of dictionaries
  - Skips if no list_name configured in domain
  Returns: List of item dictionaries
  """
  section("get_list_items()")
  
  if ctx is None:
    skip("Get list items test", "No context available")
    return []
  
  if not list_name:
    skip("Get list items test", "No list_name configured in domain")
    return []
  
  # Get all items
  items = cspf.get_list_items(ctx, list_name, "", logger)
  test("Returns list", isinstance(items, list))
  print(f"    {len(items)} list item{'' if len(items) == 1 else 's'} retrieved.")
  
  if len(items) > 0:
    first_item = items[0]
    test("Items are dictionaries", isinstance(first_item, dict))
    print(f"    First item keys: {list(first_item.keys())[:5]}...")
  
  return items

def test_export_list_to_csv(ctx, list_name: str, temp_dir: str, logger: MiddlewareLogger):
  """
  Test SharePoint list export to CSV.
  - Verifies CSV file is created
  - Verifies CSV has header row
  - Skips if no list_name configured in domain
  """
  section("export_list_to_csv()")
  
  if ctx is None:
    skip("Export list test", "No context available")
    return
  
  if not list_name:
    skip("Export list test", "No list_name configured in domain")
    return
  
  target_path = os.path.join(temp_dir, "02_lists", f"{list_name}.csv")
  
  success, error = cspf.export_list_to_csv(ctx, list_name, "", target_path, logger)
  test("Export succeeds", success, error)
  test("CSV file created", os.path.exists(target_path))
  
  if os.path.exists(target_path):
    with open(target_path, 'r', encoding='utf-8') as f:
      lines = f.readlines()
    test("CSV has header", len(lines) >= 1)
    print(f"    {len(lines)} CSV line{'' if len(lines) == 1 else 's'}.")
  
  # Test dry_run - should verify list access but not create file
  dry_target = os.path.join(temp_dir, "02_lists", "dry_run.csv")
  dry_success, dry_error = cspf.export_list_to_csv(ctx, list_name, "", dry_target, logger, dry_run=True)
  test("dry_run succeeds", dry_success, dry_error)
  test("dry_run does not create file", not os.path.exists(dry_target))

def test_get_site_pages(ctx, site_url: str, pages_url_part: str, logger: MiddlewareLogger):
  """
  Test site pages retrieval.
  - Verifies returns list of SharePointFile instances
  - Defaults to /SitePages if no pages_url_part provided
  Returns: List of SharePointFile objects
  """
  section("get_site_pages()")
  
  if ctx is None:
    skip("Site pages test", "No context available")
    return []
  
  if not pages_url_part:
    # Default to SitePages
    pages_url_part = "/SitePages"
  
  pages = cspf.get_site_pages(ctx, site_url, pages_url_part, "", logger)
  test("Returns list", isinstance(pages, list))
  print(f"    {len(pages)} site page{'' if len(pages) == 1 else 's'} retrieved.")
  
  if len(pages) > 0:
    test("Pages are SharePointFile", isinstance(pages[0], cspf.SharePointFile))
    print(f"    First page: '{pages[0].filename}'")
  
  # Test dry_run - should verify library exists but return empty list
  dry_pages = cspf.get_site_pages(ctx, site_url, pages_url_part, "", logger, dry_run=True)
  test("dry_run returns empty list", dry_pages == [])
  
  return pages

def test_download_site_page_html(ctx, pages: list, temp_dir: str, logger: MiddlewareLogger):
  """
  Test site page HTML download.
  - Downloads first .aspx page found
  - Verifies HTML file is created with content
  - Skips if no .aspx pages found
  """
  section("download_site_page_html()")
  
  if ctx is None or len(pages) == 0:
    skip("Download site page test", "No context or pages available")
    return
  
  # Pick first .aspx page
  aspx_pages = [p for p in pages if p.filename.endswith('.aspx')]
  if len(aspx_pages) == 0:
    skip("Download site page test", "No .aspx pages found")
    return
  
  test_page = aspx_pages[0]
  target_path = os.path.join(temp_dir, "03_sitepages", test_page.filename)
  
  success, error = cspf.download_site_page_html(ctx, test_page.server_relative_url, target_path, logger)
  test("Download succeeds", success, error)
  test("File exists", os.path.exists(target_path))
  
  if os.path.exists(target_path):
    size = os.path.getsize(target_path)
    test("File has content", size > 0, f"Size: {size} bytes")
  
  # Test dry_run - should verify page exists but not download
  dry_target = os.path.join(temp_dir, "03_sitepages", "dry_run.aspx")
  dry_success, dry_error = cspf.download_site_page_html(ctx, test_page.server_relative_url, dry_target, logger, dry_run=True)
  test("dry_run succeeds", dry_success, dry_error)
  test("dry_run does not create file", not os.path.exists(dry_target))

# ----------------------------------------- END: Test Cases ----------------------------------------------------------


# ----------------------------------------- START: Main --------------------------------------------------------------

# Print status of loaded credentials from environment variables
def print_credentials_status():
  print(f"\nCredentials from environment variables:")
  print(f"  CRAWLER_CLIENT_ID: {sharepoint_client_id[:8]}..." if sharepoint_client_id else "  CRAWLER_CLIENT_ID: (not set)")
  print(f"  CRAWLER_TENANT_ID: {sharepoint_tenant_id[:8]}..." if sharepoint_tenant_id else "  CRAWLER_TENANT_ID: (not set)")
  print(f"  CRAWLER_CLIENT_CERTIFICATE_PFX_FILE: {sharepoint_cert_file}" if sharepoint_cert_file else "  CRAWLER_CLIENT_CERTIFICATE_PFX_FILE: (not set)")
  print(f"  Cert full path: {sharepoint_cert_path}")
  if sharepoint_cert_path and os.path.exists(sharepoint_cert_path):
    print(f"    OK: Certificate file exists.")
  elif sharepoint_cert_path:
    print(f"    ERROR: Certificate file not found.")

def main():
  global test_count, pass_count, fail_count, skip_count
  
  print("=" * 70)
  print("common_sharepoint_functions_v2.py Test Suite")
  print("=" * 70)
  print(f"\nTest domain: {test_domain_id}")
  print(f"Persistent storage: {persistent_storage_path}")
  
  # Print credentials status
  print_credentials_status()
  
  # Verify required credentials are available
  missing_creds = []
  if not sharepoint_client_id: missing_creds.append("CRAWLER_CLIENT_ID")
  if not sharepoint_tenant_id: missing_creds.append("CRAWLER_TENANT_ID")
  if not sharepoint_cert_file: missing_creds.append("CRAWLER_CLIENT_CERTIFICATE_PFX_FILE")
  if not sharepoint_cert_password: missing_creds.append("CRAWLER_CLIENT_CERTIFICATE_PASSWORD")
  if sharepoint_cert_path and not os.path.exists(sharepoint_cert_path): missing_creds.append(f"Certificate file not found: '{sharepoint_cert_path}'")
  
  if missing_creds:
    print(f"\nERROR: Missing required credentials:")
    for mc in missing_creds: print(f"  - {mc}")
    print("\nRESULT: FAIL (missing credentials)")
    sys.exit(1)
  
  # Create test output directory (clear existing data first)
  test_output_dir = os.path.join(persistent_storage_path, "crawler", "_common_sharepoint_functions_v2_test")
  if os.path.exists(test_output_dir):
    shutil.rmtree(test_output_dir)
    print(f"Cleared existing test output directory: {test_output_dir}")
  os.makedirs(test_output_dir, exist_ok=True)
  print(f"Test output directory: {test_output_dir}")

  print("=" * 70)
  
  # Create logger without line headers for cleaner test output
  logger = MiddlewareLogger.create(include_line_header=False)
  
  try:
    # Test 1: SharePointFile dataclass (no external dependencies)
    test_sharepoint_file_dataclass()
    
    # Test 2: PEM conversion
    test_pem_conversion(sharepoint_cert_path, sharepoint_cert_password)
    
    # Load domain configuration
    section("Load Domain Configuration")
    try:
      domain = load_domain(persistent_storage_path, test_domain_id, logger)
      test("Domain loaded", domain is not None)
      print(f"    Domain: '{domain.name}'")
      print(f"    {len(domain.file_sources)} file source{'' if len(domain.file_sources) == 1 else 's'}.")
      print(f"    {len(domain.list_sources)} list source{'' if len(domain.list_sources) == 1 else 's'}.")
      print(f"    {len(domain.sitepage_sources)} site page source{'' if len(domain.sitepage_sources) == 1 else 's'}.")
    except FileNotFoundError as e:
      test("Domain loaded", False, str(e))
      domain = None
    
    if domain is None or len(domain.file_sources) == 0:
      print("\nWARNING: Cannot continue without a valid domain with file_sources")
      return
    
    # Get first file source for testing
    file_source = domain.file_sources[0]
    site_url = file_source.site_url
    library_url_part = file_source.sharepoint_url_part
    
    print(f"  Using file source: source_id='{file_source.source_id}'")
    print(f"    Site: site_url='{site_url}'")
    print(f"    Library: sharepoint_url_part='{library_url_part}'")
    
    # Test 3: Connection
    ctx = test_connect_to_site(site_url, sharepoint_client_id, sharepoint_tenant_id, sharepoint_cert_path, sharepoint_cert_password)
    
    # Test 4: Get document library
    library = test_try_get_document_library(ctx, site_url, library_url_part)
    
    # Test 5: Get files
    files = test_get_document_library_files(ctx, library, logger)
    
    # Test 6: Download file
    test_download_file(ctx, files, test_output_dir)
    
    # Test 7: List operations (if list_sources configured)
    list_name = domain.list_sources[0].list_name if len(domain.list_sources) > 0 else ""
    test_get_list_items(ctx, list_name, logger)
    test_export_list_to_csv(ctx, list_name, test_output_dir, logger)
    
    # Test 8: Site pages (if sitepage_sources configured)
    pages_site_url = domain.sitepage_sources[0].site_url if len(domain.sitepage_sources) > 0 else site_url
    pages_url_part = domain.sitepage_sources[0].sharepoint_url_part if len(domain.sitepage_sources) > 0 else "/SitePages"
    pages = test_get_site_pages(ctx, pages_site_url, pages_url_part, logger)
    test_download_site_page_html(ctx, pages, test_output_dir, logger)
    
  finally:
    # Cleanup
    print("\nCleanup")
    print("=" * 70)
    if delete_downloaded_files_after_test:
      try:
        shutil.rmtree(test_output_dir)
        print(f"  Removed test output directory: {test_output_dir}")
      except Exception as e:
        print(f"  Failed to remove test output directory: {e}")
    else:
      print(f"  Keeping test output directory: {test_output_dir}")
  
  # Summary
  print("\nTEST SUMMARY")
  print("=" * 70)
  print(f"  Sections: {section_num} / {total_sections}")
  print(f"  Tests:    {test_count} total, {pass_count} passed, {fail_count} failed, {skip_count} skipped")
  
  if len(failed_tests) > 0:
    print(f"\nFailed tests ({len(failed_tests)}):")
    for ft in failed_tests:
      print(f"  - {ft}")
  
  if len(skipped_tests) > 0:
    print(f"\nSkipped tests ({len(skipped_tests)}):")
    for st in skipped_tests:
      print(f"  - {st}")
  
  print("=" * 70)
  
  if fail_count > 0:
    print(f"\nRESULT: FAIL ({fail_count} test(s) failed)")
    sys.exit(1)
  else:
    print(f"\nRESULT: OK (all {pass_count} tests passed)")
    sys.exit(0)

if __name__ == "__main__":
  main()

# ----------------------------------------- END: Main ----------------------------------------------------------------
