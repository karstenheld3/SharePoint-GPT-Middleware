# Common functions for SharePoint operations using Office365-REST-Python-Client
# https://pypi.org/project/Office365-REST-Python-Client/#Working-with-SharePoint-API
# V2 version using MiddlewareLogger
import csv, os, re, time
from cryptography import x509
from datetime import datetime, timezone
from typing import Optional, Any
from urllib.parse import urlparse, quote, unquote
from dataclasses import asdict, dataclass, field
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.lists.list import List as DocumentLibrary
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.backends import default_backend
from routers_v2.common_logging_functions_v2 import MiddlewareLogger, UNKNOWN

@dataclass
class SharePointFile:
    """File metadata from SharePoint API - aligned with sharepoint_map.csv columns (10 fields)."""
    sharepoint_listitem_id: int
    sharepoint_unique_file_id: str
    filename: str
    file_type: str
    file_size: int
    url: str
    raw_url: str
    server_relative_url: str
    last_modified_utc: str
    last_modified_timestamp: int

# ----------------------------------------- START: Retry Logic for Transient Errors --------------------------------

def _is_transient_error(e: Exception) -> bool:
  """Check if exception is a transient connection error that should be retried."""
  error_str = str(e).lower()
  # ConnectionResetError (10054) - connection forcibly closed by remote host
  # ConnectionAbortedError - connection aborted
  # TimeoutError - connection timed out
  # NameResolutionError - DNS resolution failed (transient network issue)
  # Max retries exceeded - urllib3 exhausted retries
  transient_patterns = ['connectionreset', 'connection aborted', 'forcibly closed', '10054', 'timed out', 'timeout', 'nameresolutionerror', 'getaddrinfo failed', 'max retries exceeded']
  return any(pattern in error_str for pattern in transient_patterns)

def _execute_with_retry(query_action, max_retries: int = 5, delay_seconds: float = 3.0):
  """
  Execute a SharePoint query with retry logic for transient connection errors.
  
  Args:
    query_action: A callable that performs the query (e.g., lambda: ctx.web.get_list(url).get().execute_query())
    max_retries: Maximum number of retry attempts (default: 5)
    delay_seconds: Delay between retries in seconds (default: 3.0)
    
  Returns:
    The result of the query_action
    
  Raises:
    The original exception if all retries fail or if error is not transient
  """
  last_exception = None
  for attempt in range(max_retries + 1):
    try:
      return query_action()
    except Exception as e:
      last_exception = e
      if not _is_transient_error(e) or attempt >= max_retries:
        raise
      time.sleep(delay_seconds * (attempt + 1))  # Progressive delay: 3s, 6s, 9s, 12s, 15s
  raise last_exception

# ----------------------------------------- END: Retry Logic for Transient Errors ----------------------------------

def get_or_create_pem_from_pfx(cert_path: str, cert_password: str) -> tuple[str, str]:
  """
  Convert a PFX certificate to PEM format.
  Only recreates the PEM file if it doesn't exist or has a different timestamp than the PFX file.
  
  Args:
    cert_path: Path to the PFX certificate file
    cert_password: Password for the PFX certificate
    
  Returns:
    tuple: (pem_file_path, certificate_thumbprint)
  """
  
  pem_file = cert_path.replace('.pfx', '.pem')
  
  # Get PFX file modification time
  pfx_mtime = os.path.getmtime(cert_path)
  
  # Check if PEM file exists and has the same timestamp as PFX
  needs_conversion = True
  if os.path.exists(pem_file):
    pem_mtime = os.path.getmtime(pem_file)
    if pem_mtime == pfx_mtime: needs_conversion = False
  
  # Load and convert PFX to PEM format (required by with_client_certificate)
  with open(cert_path, 'rb') as f: pfx_data = f.read()
  
  # Extract private key and certificate from PFX
  private_key, certificate, _ = pkcs12.load_key_and_certificates( pfx_data, cert_password.encode() if cert_password else None, backend=default_backend() )
  
  # Create or update PEM file if needed
  if needs_conversion:
    with open(pem_file, 'wb') as f:
      # Write private key
      f.write( private_key.private_bytes(encoding=Encoding.PEM, format=PrivateFormat.PKCS8,encryption_algorithm=NoEncryption()) )
      # Write certificate
      f.write(certificate.public_bytes(Encoding.PEM))
    
    # Set PEM file timestamp to match PFX file
    os.utime(pem_file, (pfx_mtime, pfx_mtime))
  
  # Get certificate thumbprint
  thumbprint = certificate.fingerprint(certificate.signature_hash_algorithm).hex().upper()
  
  return pem_file, thumbprint

def connect_to_site_using_client_id_and_certificate(site_url: str, client_id: str, tenant_id: str, cert_path: str, cert_password: str) -> ClientContext:
  """
  Connect to a SharePoint site using certificate-based authentication (App-Only authentication).
  This method uses MSAL with certificate credentials to authenticate with SharePoint Online, which supports Sites.Selected permissions.
  
  Args:
    site_url: The SharePoint site URL (e.g., 'https://contoso.sharepoint.com/sites/mysite')
    client_id: The OAuth client ID of the registered application
    tenant_id: The Azure AD tenant ID
    cert_path: Path to the PFX certificate file
    cert_password: Password for the PFX certificate
    
  Returns:
    ClientContext: An authenticated SharePoint client context object
  """
  
  # Get or create PEM file from PFX certificate
  pem_file, thumbprint = get_or_create_pem_from_pfx(cert_path, cert_password)
  
  # Connect using certificate-based authentication; the library handles MSAL token acquisition internally
  ctx = ClientContext(site_url).with_client_certificate( tenant=tenant_id, client_id=client_id, thumbprint=thumbprint, cert_path=pem_file )
  return ctx

def test_connection(ctx: ClientContext) -> tuple[bool, str, str]:
  """
  Test SharePoint connection by retrieving web title (with retry for transient errors).
  
  Args:
    ctx: An authenticated SharePoint client context
    
  Returns:
    tuple: (success, web_title, error_message)
      - If successful: (True, web_title, "")
      - If failed: (False, "", error_message)
  """
  try:
    web = _execute_with_retry(lambda: ctx.web.get().execute_query())
    web_title = web.properties.get('Title', '')
    return True, web_title, ""
  except Exception as e:
    return False, "", str(e)

def try_get_document_library(ctx: ClientContext, site_url: str, library_url_part: str) -> tuple[Optional[DocumentLibrary], Optional[str]]:
  """
  Get a SharePoint document library by its server-relative URL.
  
  Args:
    ctx: An authenticated SharePoint client context
    site_url: The SharePoint site URL (e.g., 'https://contoso.sharepoint.com/sites/demosite')
    library_url_part: The URL part of the document library (e.g., '/Shared Documents')
    
  Returns:
    tuple: (DocumentLibrary or None, error_message or None)
      - If successful: (DocumentLibrary, None)
      - If failed: (None, error_message)
    
  Example:
    site_url = "https://contoso.sharepoint.com/sites/demosite"
    library_url_part = "/Shared Documents"
    # This will construct: "/sites/demosite/Shared Documents"
    
    library, error = try_get_document_library(ctx, site_url, library_url_part)
    if library:
      # Success
    else:
      # Failed, error contains the message
  """
  
  # Extract the site path from the site URL; e.g., 'https://contoso.sharepoint.com/sites/demosite' -> '/sites/demosite'
  parsed_url = urlparse(site_url)
  site_path = parsed_url.path.rstrip('/')
  
  # Ensure the library URL part starts with a forward slash
  if not library_url_part.startswith('/'): library_url_part = '/' + library_url_part
  
  # Construct the full server-relative URL; e.g., '/sites/demosite' + '/Shared Documents' = '/sites/demosite/Shared Documents'
  site_relative_url = site_path + library_url_part
  
  # Get the list (document library) by its server-relative URL (with retry for transient errors)
  try:
    document_library = _execute_with_retry(lambda: ctx.web.get_list(site_relative_url).get().execute_query())
    return document_library, None
  except Exception as e:
    error_message = f"Failed to get document library at '{site_relative_url}': {str(e)}"
    return None, error_message


def get_document_library_files(ctx: ClientContext, document_library: DocumentLibrary, filter: str, logger: MiddlewareLogger, dry_run: bool = False) -> list[SharePointFile]:
  """
  Get all files from a SharePoint document library, handling pagination automatically.
  dry_run=True verifies library is accessible without fetching all files.
  
  Args:
    ctx: An authenticated SharePoint client context
    document_library: The SharePoint document library object
    filter: Optional OData filter string (e.g., "FileLeafRef eq 'document.pdf'"). If None or empty, no filter is applied.
    logger: MiddlewareLogger instance for logging output
    dry_run: If True, verify access only without fetching all files
    
  Returns:
    list[SharePointFile]: List of SharePointFile dataclass instances
  """
  
  logger.log_function_header("get_document_library_files()")
  try:
    lib_title = document_library.properties.get('Title') or UNKNOWN
    lib_id = document_library.properties.get('Id') or UNKNOWN
    logger.log_function_output(f"Library: '{lib_title}' (ID={lib_id})")
    
    # Callback to track pagination progress
    def print_progress(items):
      logger.log_function_output(f"{len(items)} item{'' if len(items) == 1 else 's'} retrieved so far...")
    
    # Build the query with optional filter
    # Use FSObjType to filter: 0 = file, 1 = folder
    items_query = document_library.items.select([
      "Id",
      "UniqueId", 
      "FileLeafRef",
      "FileRef",
      "File/Length",
      "Modified",
      "FSObjType"
    ]).expand(["File"]).filter("FSObjType eq 0")  # Only files, not folders
    
    # Apply additional filter if provided
    if filter and filter.strip():
      items_query = items_query.filter(filter)
      logger.log_function_output(f"Applying filter: {filter}")
    
    # Use get_all() to retrieve all items with pagination (page size: 1000)
    # This method automatically handles the 5000 item limit by paginating (with retry for transient errors)
    page_size = 5000
    all_items = _execute_with_retry(lambda: items_query.get_all(page_size, print_progress).execute_query())
    
    logger.log_function_output(f"{len(all_items)} file{'' if len(all_items) == 1 else 's'} retrieved.")
    
    # Convert to SharePointFile dataclass instances
    sharepoint_files = []
    # Get site base URL for building full URLs
    parsed = urlparse(ctx.service_root_url())
    site_base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    for item in all_items:
      try:
        # Extract properties
        item_id = int(item.properties.get('Id', 0))
        unique_id = str(item.properties.get('UniqueId', ''))
        file_leaf_ref = item.properties.get('FileLeafRef', '')
        file_ref = item.properties.get('FileRef', '')
        # Derive file_type from filename
        file_type = file_leaf_ref.rsplit('.', 1)[-1].lower() if '.' in file_leaf_ref else ''
        # Build URLs
        raw_url = site_base_url + file_ref
        url = site_base_url + quote(file_ref, safe='/:@')
        # Get file size from expanded File property
        file_size = 0
        if 'File' in item.properties and item.properties['File']:
          file_obj = item.properties['File']
          if hasattr(file_obj, 'properties') and 'Length' in file_obj.properties:
            file_size = int(file_obj.properties['Length'])
          elif hasattr(file_obj, 'Length'):
            file_size = int(file_obj.Length)
        if file_size == 0 and 'Length' in item.properties:
          file_size = int(item.properties.get('Length', 0))
        modified = item.properties.get('Modified', '')
        
        # Parse and format the modified date
        last_modified_utc = ''
        last_modified_timestamp = 0
        if modified:
          try:
            dt = datetime.fromisoformat(modified.replace('Z', '+00:00'))
            last_modified_utc = dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            last_modified_timestamp = int(dt.timestamp())
          except Exception as date_error:
            logger.log_function_output(f"  WARNING: File '{file_ref}' (ID={item_id}) - failed to parse date '{modified}' -> {date_error}")
            last_modified_utc = modified
            last_modified_timestamp = 0
        
        # Create SharePointFile instance with new fields
        sp_file = SharePointFile(
          sharepoint_listitem_id=item_id,
          sharepoint_unique_file_id=unique_id,
          filename=file_leaf_ref,
          file_type=file_type,
          file_size=file_size,
          url=url,
          raw_url=raw_url,
          server_relative_url=file_ref,
          last_modified_utc=last_modified_utc,
          last_modified_timestamp=last_modified_timestamp
        )
        sharepoint_files.append(sp_file)
        
      except Exception as item_error:
        item_id_str = item.properties.get('Id') or UNKNOWN
        file_ref_str = item.properties.get('FileRef') or UNKNOWN
        logger.log_function_output(f"  WARNING: File '{file_ref_str}' (ID={item_id_str}) - failed to process -> {item_error}")
        continue
    
    logger.log_function_output(f"{len(sharepoint_files)} file{'' if len(sharepoint_files) == 1 else 's'} converted to SharePointFile objects.")
    logger.log_function_footer()
    return sharepoint_files
    
  except Exception as e:
    lib_title = (document_library.properties.get('Title') or UNKNOWN) if document_library else UNKNOWN
    logger.log_function_output(f"  ERROR: Failed to retrieve files from library '{lib_title}' -> {str(e)}")
    logger.log_function_footer()
    return []


# ----------------------------------------- START: File Download ------------------------------------------------------

def download_file_from_sharepoint(ctx: ClientContext, server_relative_url: str, target_path: str, preserve_timestamp: bool = True, last_modified_timestamp: int = None, dry_run: bool = False) -> tuple[bool, str]:
  """
  Download a single file from SharePoint to local disk.
  
  Args:
    ctx: Authenticated SharePoint context
    server_relative_url: SharePoint file path (e.g., "/sites/demo/Shared Documents/file.docx")
    target_path: Local filesystem path to save file
    preserve_timestamp: If True, set file mtime to SharePoint last_modified
    last_modified_timestamp: Unix timestamp to apply if preserve_timestamp=True
    dry_run: If True, verify file exists but don't download
    
  Returns:
    (success, error_message)
  """
  try:
    sp_file = ctx.web.get_file_by_server_relative_url(server_relative_url)
    if dry_run:
      _execute_with_retry(lambda: sp_file.get().execute_query())
      return True, ""
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    # Download with retry - each attempt opens fresh file handle
    def download_with_fresh_handle():
      with open(target_path, 'wb') as f:
        sp_file.download(f).execute_query()
    _execute_with_retry(download_with_fresh_handle)
    if preserve_timestamp and last_modified_timestamp:
      os.utime(target_path, (last_modified_timestamp, last_modified_timestamp))
    return True, ""
  except Exception as e:
    if not dry_run and os.path.exists(target_path): os.remove(target_path)
    return False, str(e)

# ----------------------------------------- END: File Download --------------------------------------------------------


# ----------------------------------------- START: List Operations ----------------------------------------------------

def get_list_items(ctx: ClientContext, list_name: str, filter_query: str, logger: MiddlewareLogger) -> list:
  """Get all items from a SharePoint list as dictionaries."""
  logger.log_function_header("get_list_items()")
  try:
    sp_list = ctx.web.lists.get_by_title(list_name)
    items_query = sp_list.items
    if filter_query and filter_query.strip():
      items_query = items_query.filter(filter_query)
    
    def print_progress(items):
      logger.log_function_output(f"{len(items)} list item{'' if len(items) == 1 else 's'} retrieved so far...")
    
    all_items = _execute_with_retry(lambda: items_query.get_all(5000, print_progress).execute_query())
    logger.log_function_output(f"{len(all_items)} list item{'' if len(all_items) == 1 else 's'} retrieved.")
    
    result = []
    for item in all_items:
      result.append(dict(item.properties))
    logger.log_function_footer()
    return result
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to get items from list '{list_name}' -> {str(e)}")
    logger.log_function_footer()
    return []

def export_list_to_csv(ctx: ClientContext, list_name: str, filter_query: str, target_path: str, logger: MiddlewareLogger, dry_run: bool = False) -> tuple[bool, str]:
  """Export SharePoint list to CSV file. Returns (success, error_message). dry_run=True verifies list access only."""
  logger.log_function_header("export_list_to_csv()")
  try:
    items = get_list_items(ctx, list_name, filter_query, logger)
    if dry_run or not items:
      logger.log_function_footer()
      return True, ""
    
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    # Get all unique keys from all items
    all_keys = set()
    for item in items:
      all_keys.update(item.keys())
    fieldnames = sorted(all_keys)
    
    with open(target_path, 'w', newline='', encoding='utf-8') as f:
      writer = csv.DictWriter(f, fieldnames=fieldnames)
      writer.writeheader()
      for item in items:
        writer.writerow(item)
    
    logger.log_function_output(f"{len(items)} item{'' if len(items) == 1 else 's'} exported to '{target_path}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    logger.log_function_footer()
    return False, str(e)

def get_list_items_as_sharepoint_files(ctx: ClientContext, list_name: str, filter_query: str, logger: MiddlewareLogger, dry_run: bool = False) -> list:
  """Get list items and convert them to SharePointFile objects for crawler compatibility."""
  logger.log_function_header("get_list_items_as_sharepoint_files()")
  try:
    items = get_list_items(ctx, list_name, filter_query, logger)
    
    result = []
    for item in items:
      item_id = item.get('ID', item.get('Id', 0))
      title = item.get('Title', f'Item_{item_id}')
      modified = item.get('Modified', '')
      modified_ts = 0
      if modified:
        try:
          from datetime import datetime
          dt = datetime.fromisoformat(modified.replace('Z', '+00:00'))
          modified_ts = int(dt.timestamp())
        except: pass
      
      # Create a virtual filename based on list item ID
      filename = f"{list_name}_{item_id}.csv"
      server_relative_url = f"/Lists/{list_name}/{item_id}"
      
      sp_file = SharePointFile(
        sharepoint_listitem_id=item_id,
        sharepoint_unique_file_id=str(item_id),
        filename=filename,
        file_type="csv",
        file_size=0,
        url=f"{ctx.web.url}/_layouts/15/listform.aspx?PageType=4&ListId={list_name}&ID={item_id}",
        raw_url="",
        server_relative_url=server_relative_url,
        last_modified_utc=modified,
        last_modified_timestamp=modified_ts
      )
      result.append(sp_file)
    
    logger.log_function_output(f"{len(result)} list item{'' if len(result) == 1 else 's'} converted to SharePointFile objects.")
    logger.log_function_footer()
    return result
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to process list '{list_name}' -> {str(e)}")
    logger.log_function_footer()
    return []

# ----------------------------------------- END: List Operations ------------------------------------------------------


# ----------------------------------------- START: Site Pages Operations ----------------------------------------------

def get_site_pages(ctx: ClientContext, site_url: str, pages_url_part: str, filter_query: str, logger: MiddlewareLogger, dry_run: bool = False) -> list:
  """Get site pages metadata. Similar to get_document_library_files but for SitePages library. dry_run=True only verifies library exists."""
  logger.log_function_header("get_site_pages()")
  library, error = try_get_document_library(ctx, site_url, pages_url_part)
  if error:
    logger.log_function_output(f"ERROR: Site pages '{pages_url_part}' - {error}")
    logger.log_function_footer()
    return []
  result = get_document_library_files(ctx, library, filter_query, logger, dry_run)
  logger.log_function_footer()
  return result

def download_site_page_html(ctx: ClientContext, server_relative_url: str, target_path: str, logger: MiddlewareLogger, dry_run: bool = False) -> tuple[bool, str]:
  """Download site page content as HTML file. Returns (success, error_message). dry_run=True verifies page exists only."""
  logger.log_function_header("download_site_page_html()")
  try:
    sp_file = ctx.web.get_file_by_server_relative_url(server_relative_url)
    if dry_run:
      _execute_with_retry(lambda: sp_file.get().execute_query())
      logger.log_function_footer()
      return True, ""
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    # Download with retry - each attempt opens fresh file handle
    def download_with_fresh_handle():
      with open(target_path, 'wb') as f:
        sp_file.download(f).execute_query()
    _execute_with_retry(download_with_fresh_handle)
    logger.log_function_output(f"Site page downloaded to '{target_path}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    if not dry_run and os.path.exists(target_path): os.remove(target_path)
    logger.log_function_footer()
    return False, str(e)

# ----------------------------------------- END: Site Pages Operations ------------------------------------------------


# ----------------------------------------- START: SharePoint Write Operations (Selftest) -----------------------------

def create_document_library(ctx: ClientContext, library_url_part: str, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Create a document library. Accepts URL part (e.g., '/_SELFTEST_DOCS' or '_SELFTEST_DOCS'). Returns (success, error_message)."""
  logger.log_function_header("create_document_library()")
  try:
    # Strip leading slash - Title doesn't have it
    library_title = library_url_part.lstrip('/')
    from office365.sharepoint.lists.creation_information import ListCreationInformation
    list_info = ListCreationInformation()
    list_info.Title = library_title
    list_info.BaseTemplate = 101  # Document Library template
    ctx.web.lists.add(list_info).execute_query()
    logger.log_function_output(f"Created document library '{library_title}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to create document library '{library_url_part}' -> {str(e)}")
    logger.log_function_footer()
    return False, str(e)

def add_number_field_to_list(ctx: ClientContext, list_url_part: str, field_name: str, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Add a number field to a list/library. Uses URL-based access. Returns (success, error_message)."""
  logger.log_function_header("add_number_field_to_list()")
  try:
    # Get site path and construct server-relative URL
    web = ctx.web.get().execute_query()
    site_path = urlparse(web.url).path.rstrip('/')
    if not list_url_part.startswith('/'): list_url_part = '/' + list_url_part
    list_relative_url = site_path + list_url_part
    sp_list = ctx.web.get_list(list_relative_url)
    from office365.sharepoint.fields.creation_information import FieldCreationInformation
    field_info = FieldCreationInformation(field_name, 9)  # 9 = Number field type
    sp_list.fields.add(field_info).execute_query()
    logger.log_function_output(f"Added number field '{field_name}' to '{list_url_part}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to add field '{field_name}' -> {str(e)}")
    logger.log_function_footer()
    return False, str(e)

def add_text_field_to_list(ctx: ClientContext, list_name: str, field_name: str, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Add a text field to a list. Returns (success, error_message)."""
  logger.log_function_header("add_text_field_to_list()")
  try:
    sp_list = ctx.web.lists.get_by_title(list_name)
    from office365.sharepoint.fields.creation_information import FieldCreationInformation
    field_info = FieldCreationInformation(field_name, 2)  # 2 = Text field type
    sp_list.fields.add(field_info).execute_query()
    logger.log_function_output(f"Added text field '{field_name}' to '{list_name}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to add field '{field_name}' -> {str(e)}")
    logger.log_function_footer()
    return False, str(e)

def upload_file_to_library(ctx: ClientContext, library_url_part: str, filename: str, content: bytes, metadata: dict, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Upload file to document library root folder. Uses URL-based access (not title). Returns (success, error_message)."""
  logger.log_function_header("upload_file_to_library()")
  try:
    # Get site path from context and construct server-relative URL
    web = ctx.web.get().execute_query()
    site_path = urlparse(web.url).path.rstrip('/')
    if not library_url_part.startswith('/'): library_url_part = '/' + library_url_part
    library_relative_url = site_path + library_url_part
    # Get library by URL (not by title) and upload to root folder
    sp_list = ctx.web.get_list(library_relative_url)
    root_folder = sp_list.root_folder
    uploaded_file = root_folder.upload_file(filename, content).execute_query()
    if metadata:
      list_item = uploaded_file.listItemAllFields.get().execute_query()
      for key, value in metadata.items(): list_item.set_property(key, value)
      list_item.update().execute_query()
    logger.log_function_output(f"Uploaded '{filename}' to '{library_url_part}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to upload '{filename}' -> {str(e)}")
    logger.log_function_footer()
    return False, str(e)

def upload_file_to_folder(ctx: ClientContext, library_url_part: str, folder_path: str, filename: str, content: bytes, metadata: dict, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Upload file to a subfolder in document library. Uses URL-based access. Creates folder if needed. Returns (success, error_message)."""
  logger.log_function_header("upload_file_to_folder()")
  try:
    # Get site path from context and construct server-relative URL
    web = ctx.web.get().execute_query()
    site_path = urlparse(web.url).path.rstrip('/')
    if not library_url_part.startswith('/'): library_url_part = '/' + library_url_part
    library_relative_url = site_path + library_url_part
    # Get library by URL (not by title) and upload to subfolder
    sp_list = ctx.web.get_list(library_relative_url)
    root_folder = sp_list.root_folder.get().execute_query()
    target_folder = root_folder.folders.add(folder_path).execute_query()
    uploaded_file = target_folder.upload_file(filename, content).execute_query()
    if metadata:
      list_item = uploaded_file.listItemAllFields.get().execute_query()
      for key, value in metadata.items(): list_item.set_property(key, value)
      list_item.update().execute_query()
    logger.log_function_output(f"Uploaded '{folder_path}/{filename}' to '{library_url_part}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to upload '{folder_path}/{filename}' -> {str(e)}")
    logger.log_function_footer()
    return False, str(e)

def update_file_content(ctx: ClientContext, server_relative_url: str, new_content: bytes, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Update file content. Returns (success, error_message)."""
  logger.log_function_header("update_file_content()")
  try:
    sp_file = ctx.web.get_file_by_server_relative_url(server_relative_url)
    sp_file.save_binary_stream(new_content).execute_query()
    logger.log_function_output(f"Updated content of '{server_relative_url}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to update '{server_relative_url}' -> {str(e)}")
    logger.log_function_footer()
    return False, str(e)

def rename_file(ctx: ClientContext, server_relative_url: str, new_name: str, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Rename file (keeps same unique_id). Returns (success, error_message)."""
  logger.log_function_header("rename_file()")
  try:
    sp_file = ctx.web.get_file_by_server_relative_url(server_relative_url)
    list_item = sp_file.listItemAllFields.get().execute_query()
    list_item.set_property("FileLeafRef", new_name)
    list_item.update().execute_query()
    logger.log_function_output(f"Renamed '{server_relative_url}' to '{new_name}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to rename '{server_relative_url}' -> {str(e)}")
    logger.log_function_footer()
    return False, str(e)

def move_file(ctx: ClientContext, server_relative_url: str, target_folder_url: str, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Move file to another folder. Returns (success, error_message)."""
  logger.log_function_header("move_file()")
  try:
    sp_file = ctx.web.get_file_by_server_relative_url(server_relative_url)
    filename = server_relative_url.split('/')[-1]
    new_url = target_folder_url.rstrip('/') + '/' + filename
    sp_file.moveto(new_url, 1).execute_query()  # 1 = Overwrite
    logger.log_function_output(f"Moved '{server_relative_url}' to '{new_url}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to move '{server_relative_url}' -> {str(e)}")
    logger.log_function_footer()
    return False, str(e)

def delete_file(ctx: ClientContext, server_relative_url: str, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Delete file from library. Returns (success, error_message)."""
  logger.log_function_header("delete_file()")
  try:
    sp_file = ctx.web.get_file_by_server_relative_url(server_relative_url)
    sp_file.delete_object().execute_query()
    logger.log_function_output(f"Deleted '{server_relative_url}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to delete '{server_relative_url}' -> {str(e)}")
    logger.log_function_footer()
    return False, str(e)

def create_folder_in_library(ctx: ClientContext, library_name: str, folder_path: str, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Create folder in document library. Returns (success, error_message)."""
  logger.log_function_header("create_folder_in_library()")
  try:
    sp_list = ctx.web.lists.get_by_title(library_name)
    root_folder = sp_list.root_folder.get().execute_query()
    root_folder.folders.add(folder_path).execute_query()
    logger.log_function_output(f"Created folder '{folder_path}' in '{library_name}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to create folder '{folder_path}' -> {str(e)}")
    logger.log_function_footer()
    return False, str(e)

def delete_document_library(ctx: ClientContext, library_url_part: str, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Delete entire document library. Uses URL-based access. Returns (success, error_message)."""
  logger.log_function_header("delete_document_library()")
  try:
    # Get site path and construct server-relative URL
    web = ctx.web.get().execute_query()
    site_path = urlparse(web.url).path.rstrip('/')
    if not library_url_part.startswith('/'): library_url_part = '/' + library_url_part
    library_relative_url = site_path + library_url_part
    sp_list = ctx.web.get_list(library_relative_url)
    sp_list.delete_object().execute_query()
    logger.log_function_output(f"Deleted document library '{library_url_part}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to delete library '{library_url_part}' -> {str(e)}")
    logger.log_function_footer()
    return False, str(e)

def create_list(ctx: ClientContext, list_name: str, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Create a SharePoint list. Returns (success, error_message)."""
  logger.log_function_header("create_list()")
  try:
    from office365.sharepoint.lists.creation_information import ListCreationInformation
    list_info = ListCreationInformation()
    list_info.Title = list_name
    list_info.BaseTemplate = 100  # Generic List template
    ctx.web.lists.add(list_info).execute_query()
    logger.log_function_output(f"Created list '{list_name}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to create list '{list_name}' -> {str(e)}")
    logger.log_function_footer()
    return False, str(e)

def add_list_item(ctx: ClientContext, list_name: str, item_data: dict, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Add item to list. Returns (success, error_message)."""
  logger.log_function_header("add_list_item()")
  try:
    sp_list = ctx.web.lists.get_by_title(list_name)
    sp_list.add_item(item_data).execute_query()
    logger.log_function_output(f"Added item to '{list_name}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to add item -> {str(e)}")
    logger.log_function_footer()
    return False, str(e)

def update_list_item(ctx: ClientContext, list_name: str, item_id: int, updates: dict, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Update list item fields. Returns (success, error_message)."""
  logger.log_function_header("update_list_item()")
  try:
    sp_list = ctx.web.lists.get_by_title(list_name)
    item = sp_list.get_item_by_id(item_id)
    for key, value in updates.items(): item.set_property(key, value)
    item.update().execute_query()
    logger.log_function_output(f"Updated item {item_id} in '{list_name}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to update item {item_id} -> {str(e)}")
    logger.log_function_footer()
    return False, str(e)

def delete_list_item(ctx: ClientContext, list_name: str, item_id: int, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Delete list item. Returns (success, error_message)."""
  logger.log_function_header("delete_list_item()")
  try:
    sp_list = ctx.web.lists.get_by_title(list_name)
    item = sp_list.get_item_by_id(item_id)
    item.delete_object().execute_query()
    logger.log_function_output(f"Deleted item {item_id} from '{list_name}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to delete item {item_id} -> {str(e)}")
    logger.log_function_footer()
    return False, str(e)

def delete_list(ctx: ClientContext, list_name: str, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Delete entire list. Returns (success, error_message)."""
  logger.log_function_header("delete_list()")
  try:
    sp_list = ctx.web.lists.get_by_title(list_name)
    sp_list.delete_object().execute_query()
    logger.log_function_output(f"Deleted list '{list_name}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to delete list '{list_name}' -> {str(e)}")
    logger.log_function_footer()
    return False, str(e)

def create_site_page(ctx: ClientContext, page_name: str, content: str, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Create a site page by uploading an .aspx file to Site Pages library. Returns (success, error_message)."""
  logger.log_function_header("create_site_page()")
  try:
    # Site Pages is a document library, not a list - must upload file, not add item
    site_pages_folder = ctx.web.get_folder_by_server_relative_url("SitePages")
    html_content = f"<html><head><title>{page_name.replace('.aspx', '')}</title></head><body><div>{content}</div></body></html>"
    site_pages_folder.upload_file(page_name, html_content.encode('utf-8')).execute_query()
    logger.log_function_output(f"Created site page '{page_name}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to create site page '{page_name}' -> {str(e)}")
    logger.log_function_footer()
    return False, str(e)

def update_site_page(ctx: ClientContext, page_name: str, new_content: str, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Update site page content. Returns (success, error_message)."""
  logger.log_function_header("update_site_page()")
  try:
    site_pages = ctx.web.lists.get_by_title("Site Pages")
    items = site_pages.items.filter(f"FileLeafRef eq '{page_name}'").get().execute_query()
    if len(items) == 0:
      logger.log_function_footer()
      return False, f"Page '{page_name}' not found"
    item = items[0]
    item.set_property("CanvasContent1", f"<div>{new_content}</div>")
    item.update().execute_query()
    logger.log_function_output(f"Updated site page '{page_name}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to update site page '{page_name}' -> {str(e)}")
    logger.log_function_footer()
    return False, str(e)

def rename_site_page(ctx: ClientContext, old_name: str, new_name: str, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Rename site page. Returns (success, error_message)."""
  logger.log_function_header("rename_site_page()")
  try:
    site_pages = ctx.web.lists.get_by_title("Site Pages")
    items = site_pages.items.filter(f"FileLeafRef eq '{old_name}'").get().execute_query()
    if len(items) == 0:
      logger.log_function_footer()
      return False, f"Page '{old_name}' not found"
    item = items[0]
    item.set_property("FileLeafRef", new_name)
    item.set_property("Title", new_name.replace('.aspx', ''))
    item.update().execute_query()
    logger.log_function_output(f"Renamed site page '{old_name}' to '{new_name}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to rename site page '{old_name}' -> {str(e)}")
    logger.log_function_footer()
    return False, str(e)

def delete_site_page(ctx: ClientContext, page_name: str, logger: MiddlewareLogger) -> tuple[bool, str]:
  """Delete site page. Returns (success, error_message)."""
  logger.log_function_header("delete_site_page()")
  try:
    site_pages = ctx.web.lists.get_by_title("Site Pages")
    items = site_pages.items.filter(f"FileLeafRef eq '{page_name}'").get().execute_query()
    if len(items) == 0:
      logger.log_function_output(f"Site page '{page_name}' not found, skipping.")
      logger.log_function_footer()
      return True, ""  # Already deleted, not an error
    items[0].delete_object().execute_query()
    logger.log_function_output(f"Deleted site page '{page_name}'.")
    logger.log_function_footer()
    return True, ""
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to delete site page '{page_name}' -> {str(e)}")
    logger.log_function_footer()
    return False, str(e)

def file_exists_in_library(ctx: ClientContext, server_relative_url: str, logger: MiddlewareLogger) -> bool:
  """Check if file exists in library. Returns True if exists."""
  try:
    sp_file = ctx.web.get_file_by_server_relative_url(server_relative_url)
    sp_file.get().execute_query()
    return True
  except:
    return False

# ----------------------------------------- END: SharePoint Write Operations (Selftest) -------------------------------


# ----------------------------------------- START: List Export Operations ------------------------------------------

# System fields to skip during export (per V2CR-FR-09)
LIST_EXPORT_IGNORE_FIELDS = {
  'Author', 'Editor', 'AppAuthor', 'AppEditor', 'Attachments', 'CheckoutUser',
  'ComplianceAssetId', 'ContentType', 'ContentTypeId', 'DocIcon', 'Edit',
  'FileSizeDisplay', 'FolderChildCount', 'ItemChildCount', 'LinkTitle',
  'LinkFilename', 'LinkFilenameNoMenu', 'MediaServiceAutoTags', 'MediaServiceLocation',
  'MediaServiceOCR', 'ParentVersionString', 'SharedWithDetails', 'SharedWithUsers',
  'GUID', 'FileRef', 'FileDirRef', 'FileLeafRef', 'FSObjType', 'PermMask',
  'UniqueId', 'SyncClientId', 'ProgId', 'ScopeId', 'MetaInfo', 'ItemType',
  'owshiddenversion', 'WorkflowVersion', 'WorkflowInstanceID', 'Order',
  'InstanceID', 'ServerRedirectedEmbedUrl', 'ServerRedirectedEmbedUri'
}

@dataclass
class ListFieldInfo:
  """SharePoint list field metadata."""
  internal_name: str
  display_name: str
  field_type_kind: int
  is_hidden: bool = False

@dataclass
class ListExportResult:
  """Result of list export operation."""
  csv_content: str
  md_content: str
  item_count: int
  field_count: int

def convert_field_to_text(value: Any, field_type_kind: int = None) -> str | int | float | bool | None:
  """
  Convert SharePoint field value to human-readable text or native type.
  Handles: User, Lookup, URL, Taxonomy, DateTime, Choice, MultiChoice, primitives.
  """
  if value is None:
    return None
  
  # FieldUserValue - check for Email attribute (single user)
  if hasattr(value, 'LookupValue') and hasattr(value, 'LookupId'):
    # Check if it's a user (has Email) or just a lookup
    email = getattr(value, 'Email', None) or ''
    display = getattr(value, 'LookupValue', '') or ''
    if email:
      return f"{display} <{email}>"
    # Check for Label (TaxonomyFieldValue)
    label = getattr(value, 'Label', None)
    if label:
      return label
    return display
  
  # List of FieldUserValue or FieldLookupValue
  if isinstance(value, (list, tuple)) and len(value) > 0:
    first = value[0]
    # User array
    if hasattr(first, 'Email'):
      parts = []
      for v in value:
        email = getattr(v, 'Email', None) or ''
        display = getattr(v, 'LookupValue', '') or ''
        parts.append(f"{display} <{email}>" if email else display)
      return '; '.join(parts)
    # Taxonomy array
    if hasattr(first, 'Label'):
      return '|'.join(getattr(v, 'Label', '') for v in value if getattr(v, 'Label', None))
    # Lookup array
    if hasattr(first, 'LookupValue'):
      return '|'.join(getattr(v, 'LookupValue', '') for v in value if getattr(v, 'LookupValue', None))
    # String array (MultiChoice)
    if all(isinstance(v, str) for v in value):
      return '|'.join(value)
  
  # FieldUrlValue - can be object or dict from API
  if hasattr(value, 'Url') and hasattr(value, 'Description'):
    return getattr(value, 'Url', '') or ''
  if isinstance(value, dict) and 'Url' in value:
    return value.get('Url', '') or ''
  
  # TaxonomyFieldValue (single)
  if hasattr(value, 'Label') and hasattr(value, 'TermGuid'):
    return getattr(value, 'Label', '') or ''
  
  # DateTime - convert to local timezone with standard format
  if isinstance(value, datetime):
    try:
      if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
      local_dt = value.astimezone()
      return local_dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
      return str(value)
  
  # Handle ISO date strings from SharePoint API
  if isinstance(value, str) and len(value) >= 19 and 'T' in value:
    try:
      dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
      local_dt = dt.astimezone()
      return local_dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
      pass
  
  # Primitives - return as-is
  if isinstance(value, bool):
    return value
  if isinstance(value, (int, float)):
    return value
  if isinstance(value, str):
    return value
  
  # Fallback - convert to string
  return str(value) if value else None

def csv_escape(value: Any) -> str:
  """Escape value for RFC 4180 CSV output. Numbers/bools unquoted, strings quoted if needed."""
  if value is None:
    return ''
  if isinstance(value, bool):
    return str(value)
  if isinstance(value, (int, float)):
    return str(value)
  
  s = str(value)
  # Quote if: contains comma, quote, newline, or starts with special chars (=, +, -, @, tab, CR)
  needs_quote = bool(re.search(r'[,"\n\r]', s)) or (s and s[0] in '=+-@\t\r')
  if needs_quote:
    return '"' + s.replace('"', '""') + '"'
  return s

def get_list_fields(ctx: ClientContext, list_name: str, logger: MiddlewareLogger) -> list[ListFieldInfo]:
  """Get field definitions for a SharePoint list (display names, types)."""
  logger.log_function_header("get_list_fields()")
  try:
    sp_list = ctx.web.lists.get_by_title(list_name)
    fields = _execute_with_retry(lambda: sp_list.fields.filter("Hidden eq false").get().execute_query())
    
    result = []
    for f in fields:
      internal_name = f.properties.get('InternalName', '')
      # Skip system fields
      if internal_name.startswith('_') or internal_name in LIST_EXPORT_IGNORE_FIELDS:
        continue
      result.append(ListFieldInfo(
        internal_name=internal_name,
        display_name=f.properties.get('Title', internal_name),
        field_type_kind=f.properties.get('FieldTypeKind', 0),
        is_hidden=f.properties.get('Hidden', False)
      ))
    
    logger.log_function_output(f"{len(result)} visible field{'' if len(result) == 1 else 's'} retrieved.")
    logger.log_function_footer()
    return result
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to get fields for '{list_name}' -> {str(e)}")
    logger.log_function_footer()
    return []

def get_list_items_with_fields(ctx: ClientContext, list_name: str, filter_query: str, logger: MiddlewareLogger) -> tuple[list[dict], list[ListFieldInfo]]:
  """Get all items from a SharePoint list with field definitions. Returns (items, fields)."""
  logger.log_function_header("get_list_items_with_fields()")
  try:
    # Get field definitions first
    fields = get_list_fields(ctx, list_name, logger)
    field_names = [f.internal_name for f in fields]
    
    # Get items with select to include all visible fields
    sp_list = ctx.web.lists.get_by_title(list_name)
    items_query = sp_list.items
    if field_names:
      items_query = items_query.select(field_names)
    if filter_query and filter_query.strip():
      items_query = items_query.filter(filter_query)
    
    def print_progress(items):
      logger.log_function_output(f"{len(items)} list item{'' if len(items) == 1 else 's'} retrieved so far...")
    
    all_items = _execute_with_retry(lambda: items_query.get_all(5000, print_progress).execute_query())
    logger.log_function_output(f"{len(all_items)} list item{'' if len(all_items) == 1 else 's'} retrieved with {len(fields)} field{'' if len(fields) == 1 else 's'}.")
    
    result = []
    for item in all_items:
      result.append(dict(item.properties))
    logger.log_function_footer()
    return result, fields
  except Exception as e:
    logger.log_function_output(f"  ERROR: Failed to get items with fields from list '{list_name}' -> {str(e)}")
    logger.log_function_footer()
    return [], []

def export_list_items_to_csv_string(items: list[dict], fields: list[ListFieldInfo]) -> str:
  """Export list items to CSV string with field display names as headers.
  Column order: ID, Title, alphabetical user fields, Created, Modified."""
  if not items or not fields:
    return ''
  
  # Build ordered field list: ID, Title, alphabetical, Created, Modified
  system_fields = {'ID', 'Title', 'Created', 'Modified'}
  id_field = next((f for f in fields if f.internal_name == 'ID'), None)
  title_field = next((f for f in fields if f.internal_name == 'Title'), None)
  created_field = next((f for f in fields if f.internal_name == 'Created'), None)
  modified_field = next((f for f in fields if f.internal_name == 'Modified'), None)
  
  # User fields sorted alphabetically by display name
  user_fields = sorted([f for f in fields if f.internal_name not in system_fields], key=lambda f: f.display_name.lower())
  
  # Final order: ID, Title, user fields, Created, Modified
  ordered_fields = []
  if id_field: ordered_fields.append(id_field)
  if title_field: ordered_fields.append(title_field)
  ordered_fields.extend(user_fields)
  if created_field: ordered_fields.append(created_field)
  if modified_field: ordered_fields.append(modified_field)
  
  lines = []
  # Header row with display names
  header = ','.join(csv_escape(f.display_name) for f in ordered_fields)
  lines.append(header)
  
  # Data rows
  for item in items:
    values = []
    for f in ordered_fields:
      raw_value = item.get(f.internal_name)
      converted = convert_field_to_text(raw_value, f.field_type_kind)
      values.append(csv_escape(converted))
    lines.append(','.join(values))
  
  return '\n'.join(lines)

def export_list_items_to_markdown_string(items: list[dict], list_name: str, fields: list[ListFieldInfo], currency_fields: set[str] = None) -> str:
  """Export list items to Markdown string. Currency fields get $ prefix."""
  if not items:
    return ''
  
  currency_fields = currency_fields or set()
  # Auto-detect currency fields from field_type_kind (10 = Currency)
  for f in fields:
    if f.field_type_kind == 10:
      currency_fields.add(f.internal_name)
  
  lines = [f"## {list_name}", ""]
  # Fields to skip in body: ID in heading, Modified/Created are system timestamps
  skip_fields = {'ID', 'Modified', 'Created'}
  
  # Find Title field for outputting first
  title_field = next((f for f in fields if f.internal_name == 'Title'), None)
  
  for item in items:
    item_id = item.get('ID', item.get('Id', '?'))
    title = item.get('Title') or f"Item {item_id}"
    lines.append(f'### "{list_name}" - {title}')
    
    # Output Title first if present
    if title_field and title:
      lines.append(f"- {title_field.display_name}: {title}")
    
    for f in fields:
      if f.internal_name in skip_fields or f.internal_name == 'Title':
        continue
      raw_value = item.get(f.internal_name)
      converted = convert_field_to_text(raw_value, f.field_type_kind)
      if converted is None or converted == '':
        continue
      # Add $ prefix for currency fields
      if f.internal_name in currency_fields and isinstance(converted, (int, float)):
        lines.append(f"- {f.display_name}: $ {converted}")
      else:
        lines.append(f"- {f.display_name}: {converted}")
    lines.append("")
  
  return '\n'.join(lines)

def export_list_to_files(ctx: ClientContext, list_name: str, filter_query: str, csv_path: str, md_path: str, logger: MiddlewareLogger, dry_run: bool = False) -> tuple[bool, str, ListExportResult]:
  """
  Export SharePoint list to both CSV and Markdown files.
  Returns (success, error_message, result).
  """
  logger.log_function_header("export_list_to_files()")
  try:
    items, fields = get_list_items_with_fields(ctx, list_name, filter_query, logger)
    
    if dry_run or not items:
      result = ListExportResult(csv_content='', md_content='', item_count=len(items), field_count=len(fields))
      logger.log_function_footer()
      return True, "", result
    
    # Generate content
    csv_content = export_list_items_to_csv_string(items, fields)
    md_content = export_list_items_to_markdown_string(items, list_name, fields)
    
    # Write files
    if csv_path:
      os.makedirs(os.path.dirname(csv_path), exist_ok=True)
      with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        f.write(csv_content)
      logger.log_function_output(f"CSV exported to '{csv_path}'.")
    
    if md_path:
      os.makedirs(os.path.dirname(md_path), exist_ok=True)
      with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
      logger.log_function_output(f"Markdown exported to '{md_path}'.")
    
    result = ListExportResult(csv_content=csv_content, md_content=md_content, item_count=len(items), field_count=len(fields))
    logger.log_function_output(f"{len(items)} item{'' if len(items) == 1 else 's'} exported with {len(fields)} field{'' if len(fields) == 1 else 's'}.")
    logger.log_function_footer()
    return True, "", result
  except Exception as e:
    logger.log_function_footer()
    return False, str(e), ListExportResult(csv_content='', md_content='', item_count=0, field_count=0)

# ----------------------------------------- END: List Export Operations --------------------------------------------
