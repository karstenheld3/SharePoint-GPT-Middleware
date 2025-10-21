# Common functions and dataclasses for SharePoint crawler
import json, os, zipfile, datetime, csv, shutil
from dataclasses import asdict, dataclass
from typing import Any, Dict, List

from hardcoded_config import CRAWLER_HARDCODED_CONFIG
from utils import log_function_output, normalize_long_path
from common_sharepoint_functions import connect_to_site_using_client_id_and_certificate, try_get_document_library, get_document_library_files
from common_openai_functions import get_vector_store_files_with_filenames_as_dict

@dataclass
class FileSource:
    """Represents a SharePoint document library source."""
    source_id: str
    site_url: str
    sharepoint_url_part: str
    filter: str

@dataclass
class SitePageSource:
    """Represents a SharePoint site pages source."""
    source_id: str
    site_url: str
    sharepoint_url_part: str
    filter: str

@dataclass
class ListSource:
    """Represents a SharePoint list source."""
    source_id: str
    site_url: str
    list_name: str
    filter: str

@dataclass
class DomainConfig:
    """Represents a complete domain configuration."""
    domain_id: str
    vector_store_name: str
    vector_store_id: str
    name: str
    description: str
    file_sources: List[FileSource]
    sitepage_sources: List[SitePageSource]
    list_sources: List[ListSource]

@dataclass
class CrawledFile:
  sharepoint_listitem_id: int # SharePoint list item id (e.g. 1, 2, 123456, ...)
  sharepoint_unique_file_id: str # SharePoint unique file id that stays the same even if file is moved (e.g. '12345678-1234-1234-1234-123456789012')
  openai_file_id: str # Open AI file id (e.g. 'assistant-17ak9Sdidc5bGXnq8mRDDf')
  file_relative_path: str # path to file relative to 'crawler' subfolder (e.g. 'ExampleDomain01\01_files\source01\02_embedded\Folder\document.pptx')
  url: str # URL-encoded URL to original file (e.g. 'https://contoso.sharepoint.com/sites/SiteName/Shared%20Documents/Folder/document.pptx')
  raw_url: str # Unencoded URL to original file (e.g. 'https://contoso.sharepoint.com/sites/SiteName/Shared Documents/Folder/document.pptx')
  server_relative_url: str # Unencoded server-relative URL to original file (e.g. '/sites/SiteName/Shared Documents/Folder/document.pptx')
  filename: str # original filename (e.g. 'document.pptx')
  file_type: str # original file type lowercase (e.g. 'pptx')
  file_size: int # file size in bytes
  last_modified_utc: str # last modified date UTC (e.g. '2025-01-27T12:34:56.789Z')
  last_modified_timestamp: int # last modified timestamp (e.g. 1604509082)

@dataclass
class CrawledVectorStore:
  vector_store: any
  vector_store_id: str
  files: List[CrawledFile]
  failed_files: List[CrawledFile]

def load_domain(storage_path: str, domain_id: str, log_data: Dict[str, Any] = None) -> DomainConfig:
  """
  Load a single domain configuration by domain_id.
  
  Args:
    storage_path: Base persistent storage path
    domain_id: The ID of the domain to load
    log_data: Optional logging context
    
  Returns:
    DomainConfig dataclass
    
  Raises:
    FileNotFoundError: If domain folder or domain.json doesn't exist
    ValueError: If domain data is invalid
  """
  domains_path = os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER)
  domain_json_path = os.path.join(domains_path, domain_id, "domain.json")
  
  if log_data:
    log_function_output(log_data, f"Loading domain '{domain_id}' from: {domain_json_path}")
  
  # Check if domain.json exists
  if not os.path.exists(domain_json_path):
    error_message = f"Domain configuration not found: {domain_json_path}"
    if log_data:
      log_function_output(log_data, f"ERROR: {error_message}")
    raise FileNotFoundError(error_message)
  
  try:
    with open(domain_json_path, 'r', encoding='utf-8') as f:
      domain_data = json.load(f)
      
      # Convert nested dictionaries to dataclasses
      file_sources = [FileSource(**src) for src in domain_data.get('file_sources', [])]
      sitepage_sources = [SitePageSource(**src) for src in domain_data.get('sitepage_sources', [])]
      list_sources = [ListSource(**src) for src in domain_data.get('list_sources', [])]
      
      domain_config = DomainConfig(
        domain_id=domain_data['domain_id'],
        vector_store_name=domain_data['vector_store_name'],
        vector_store_id=domain_data['vector_store_id'],
        name=domain_data['name'],
        description=domain_data['description'],
        file_sources=file_sources,
        sitepage_sources=sitepage_sources,
        list_sources=list_sources
      )
      
      if log_data:
        log_function_output(log_data, f"Successfully loaded domain: {domain_config.domain_id}")
      
      return domain_config
      
  except KeyError as e:
    error_message = f"Missing required field in domain.json: {str(e)}"
    if log_data:
      log_function_output(log_data, f"ERROR: {error_message}")
    raise ValueError(error_message)
  except Exception as e:
    error_message = f"Failed to load domain '{domain_id}': {str(e)}"
    if log_data:
      log_function_output(log_data, f"ERROR: {error_message}")
    raise

def load_all_domains(storage_path: str, log_data: Dict[str, Any] = None) -> List[DomainConfig]:
  """
  Load all domain configurations from the domains folder.
  
  Args:
    storage_path: Base persistent storage path
    log_data: Optional logging context
    
  Returns:
    List of DomainConfig dataclasses
    
  Raises:
    FileNotFoundError: If domains folder doesn't exist
  """
  domains_path = os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER)
  
  if log_data:
    log_function_output(log_data, f"Scanning domains path: {domains_path}")
  
  # Check if domains folder exists
  if not os.path.exists(domains_path):
    error_message = f"Domains folder not found: {domains_path}"
    if log_data:
      log_function_output(log_data, f"ERROR: {error_message}")
    raise FileNotFoundError(error_message)
  
  # Get all domain folders
  domain_folders = [d for d in os.listdir(domains_path) if os.path.isdir(os.path.join(domains_path, d))]
  
  if log_data:
    log_function_output(log_data, f"Found {len(domain_folders)} domain folder(s)")
  
  # Load each domain using load_domain function
  domains_list = []
  for domain_folder in domain_folders:
    try:
      domain_config = load_domain(storage_path, domain_folder, log_data)
      domains_list.append(domain_config)
    except (FileNotFoundError, ValueError) as e:
      if log_data:
        log_function_output(log_data, f"WARNING: Skipping domain '{domain_folder}': {str(e)}")
      continue
  
  if log_data:
    log_function_output(log_data, f"Successfully loaded {len(domains_list)} domain(s)")
  
  return domains_list

# Convert a DomainConfig dataclass to a dictionary
def domain_config_to_dict(domain: DomainConfig) -> Dict[str, Any]:
  return asdict(domain)

def scan_directory_recursive(path: str, log_data: Dict[str, Any] = None, except_folder: str = None) -> List[Dict[str, Any]]:
  """
  Recursively scan a directory and return a list of files and folders with their attributes.
  
  Args:
    path: Directory path to scan
    log_data: Optional logging context
    except_folder: Optional folder name to exclude from scanning
    
  Returns:
    List of dictionaries containing file/folder information
  """
  items = []
  try:
    if not os.path.exists(path): return items
    for item_name in os.listdir(path):
      # Skip the except_folder if specified
      if except_folder and item_name == except_folder:
        if log_data:
          log_function_output(log_data, f"Skipping folder: {item_name}")
        continue
        
      item_path = os.path.join(path, item_name)
      try:
        if os.path.isdir(item_path):
          # For directories, recursively get contents
          sub_items = scan_directory_recursive(item_path, log_data, except_folder)
          items.append({"name": item_name, "type": "folder", "size": len(sub_items), "contents": sub_items})
        else:
          # For files, get size in bytes
          file_size = os.path.getsize(item_path)
          items.append({"name": item_name, "type": "file", "size": file_size})
      except (OSError, PermissionError) as e:
        # Handle permission errors or other OS errors gracefully
        items.append({"name": item_name, "type": "error", "size": 0, "error": str(e)})
  except (OSError, PermissionError) as e:
    if log_data:
      log_function_output(log_data, f"Error scanning directory {path}: {str(e)}")
  return items

def create_storage_zip_from_scan(storage_path: str, storage_contents: List[Dict[str, Any]], log_data: Dict[str, Any], temp_zip_path: str, temp_zip_name: str) -> str:
  """
  Create a zip file from the scanned directory structure.
  
  Args:
    storage_path: Base path of the storage directory
    storage_contents: Output from scan_directory_recursive
    log_data: Logging context
    temp_zip_path: Full path where the zip file should be created
    temp_zip_name: Name of the zip file
    
  Returns:
    Path to the created zip file
  """
  
  log_function_output(log_data, f"Creating zip file: {temp_zip_path}")
  
  def _add_items_to_zip(zipf: zipfile.ZipFile, items: List[Dict[str, Any]], current_path: str = ""):
    """Recursively add items from scan results to zip file."""
    for item in items:
      if item["type"] == "error":
        log_function_output(log_data, f"Skipping error item: {item['name']} - {item.get('error', 'Unknown error')}")
        continue
        
      item_path = os.path.join(current_path, item["name"]) if current_path else item["name"]
      full_path = os.path.join(storage_path, item_path)
      
      if item["type"] == "file":
        # Skip temporary zip files with timestamp pattern and the current zip being created
        if ((item["name"].startswith(CRAWLER_HARDCODED_CONFIG.LOCALSTORAGE_ZIP_FILENAME_PREFIX)) and 
            item["name"].endswith(".zip")) or item["name"] == temp_zip_name:
          log_function_output(log_data, f"Skipping zip file: {item['name']}")
          continue
        try:
          zipf.write(full_path, item_path)
          log_function_output(log_data, f"Added to zip: {item_path}")
        except Exception as e:
          log_function_output(log_data, f"WARNING: Failed to add {full_path} to zip: {str(e)}")
      elif item["type"] == "folder" and "contents" in item:
        # Add empty folder to zip if it has no contents
        if len(item["contents"]) == 0:
          # Create empty directory in zip by adding a ZipInfo entry
          zipf.writestr(item_path + "/", "")
          log_function_output(log_data, f"Added empty folder to zip: {item_path}/")
        else:
          # Recursively add folder contents
          _add_items_to_zip(zipf, item["contents"], item_path)
  
  with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    _add_items_to_zip(zipf, storage_contents)
  
  zip_size = os.path.getsize(temp_zip_path)
  log_function_output(log_data, f"Zip file created successfully: {temp_zip_path} ({zip_size} bytes)")
  return temp_zip_path

def validate_domain_config(domain_data: Dict[str, Any]) -> tuple[bool, str]:
  """
  Validate domain configuration data.
  
  Args:
    domain_data: Dictionary containing domain configuration
    
  Returns:
    Tuple of (is_valid, error_message)
  """
  required_fields = ['domain_id', 'name', 'vector_store_name', 'vector_store_id', 'description']
  
  # Check required fields
  for field in required_fields:
    if field not in domain_data or not domain_data[field]:
      return False, f"Missing required field: {field}"
  
  # Validate domain_id format (alphanumeric, underscore, hyphen only)
  domain_id = domain_data['domain_id']
  if not domain_id.replace('_', '').replace('-', '').isalnum():
    return False, "domain_id must contain only alphanumeric characters, underscores, and hyphens"
  
  # Validate source lists exist
  if 'file_sources' not in domain_data:
    domain_data['file_sources'] = []
  if 'sitepage_sources' not in domain_data:
    domain_data['sitepage_sources'] = []
  if 'list_sources' not in domain_data:
    domain_data['list_sources'] = []
  
  return True, ""

def save_domain_to_file(storage_path: str, domain_config: DomainConfig, log_data: Dict[str, Any] = None) -> None:
  """
  Save a domain configuration to disk.
  
  Args:
    storage_path: Base persistent storage path
    domain_config: DomainConfig dataclass to save
    log_data: Optional logging context
    
  Raises:
    OSError: If file operations fail
  """
  domains_path = os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER)
  domain_folder = os.path.join(domains_path, domain_config.domain_id)
  domain_json_path = os.path.join(domain_folder, "domain.json")
  
  # Create domain folder if it doesn't exist
  os.makedirs(domain_folder, exist_ok=True)
  
  if log_data:
    log_function_output(log_data, f"Saving domain to: {domain_json_path}")
  
  # Convert dataclass to dictionary
  domain_dict = domain_config_to_dict(domain_config)
  
  # Write to file with pretty formatting
  with open(domain_json_path, 'w', encoding='utf-8') as f:
    json.dump(domain_dict, f, indent=2, ensure_ascii=False)
  
  if log_data:
    log_function_output(log_data, f"Domain saved successfully: {domain_config.domain_id}")

def delete_domain_folder(storage_path: str, domain_id: str, log_data: Dict[str, Any] = None) -> None:
  """
  Delete a domain folder and all its contents.
  
  Args:
    storage_path: Base persistent storage path
    domain_id: ID of the domain to delete
    log_data: Optional logging context
    
  Raises:
    FileNotFoundError: If domain folder doesn't exist
    OSError: If deletion fails
  """
  import shutil
  
  domains_path = os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER)
  domain_folder = os.path.join(domains_path, domain_id)
  
  if not os.path.exists(domain_folder):
    error_msg = f"Domain folder not found: {domain_id}"
    if log_data:
      log_function_output(log_data, f"ERROR: {error_msg}")
    raise FileNotFoundError(error_msg)
  
  if log_data:
    log_function_output(log_data, f"Deleting domain folder: {domain_folder}")
  
  shutil.rmtree(domain_folder)
  
  if log_data:
    log_function_output(log_data, f"Domain deleted successfully: {domain_id}")

def load_files_from_sharepoint_source( system_info, domain_id: str, source_id: str, request_data: Dict[str, Any], config ) -> List[CrawledFile]:
  """
  Load files from a SharePoint document library for a specific domain source.
  
  This function handles all the validation, connection, and file retrieval logic.
  All logging is performed using the provided request_data dictionary.
  
  Args:
    system_info: System configuration object with PERSISTENT_STORAGE_PATH
    domain_id: The ID of the domain to load files for
    source_id: The ID of the file source within the domain
    request_data: Dictionary for logging output
    config: Configuration object with crawler credentials
    
  Returns:
    List of CrawledFile objects
    
  Raises:
    ValueError: If validation fails or required configuration is missing
    FileNotFoundError: If domain or source is not found
    Exception: For any other errors during file loading
  """
  # Validate PERSISTENT_STORAGE_PATH
  if not system_info.PERSISTENT_STORAGE_PATH:
    raise ValueError("PERSISTENT_STORAGE_PATH not configured")
  
  # Validate crawler credentials from config
  if not config or not config.CRAWLER_CLIENT_ID or not config.CRAWLER_CLIENT_CERTIFICATE_PFX_FILE or not config.CRAWLER_CLIENT_CERTIFICATE_PASSWORD or not config.CRAWLER_TENANT_ID:
    raise ValueError("Crawler credentials (CRAWLER_CLIENT_ID, CRAWLER_CLIENT_CERTIFICATE_PFX_FILE, CRAWLER_CLIENT_CERTIFICATE_PASSWORD, CRAWLER_TENANT_ID) not configured")
  
  storage_path = system_info.PERSISTENT_STORAGE_PATH
  
  # Load domain configuration
  log_function_output(request_data, f"Loading domain: '{domain_id}'")
  domain_config = load_domain(storage_path, domain_id, request_data)
  
  # Find the file source with matching source_id
  file_source = next((src for src in domain_config.file_sources if src.source_id == source_id), None)
  
  if not file_source:
    raise FileNotFoundError(f"File source '{source_id}' not found in domain '{domain_id}'")
  
  log_function_output(request_data, f"Found file source: '{file_source.site_url}{file_source.sharepoint_url_part}'")
  
  # Connect to SharePoint
  log_function_output(request_data, f"Connecting to SharePoint: '{file_source.site_url}'")
  
  # Get certificate path from persistent storage
  cert_path = os.path.join(system_info.PERSISTENT_STORAGE_PATH, config.CRAWLER_CLIENT_CERTIFICATE_PFX_FILE)
  
  ctx = connect_to_site_using_client_id_and_certificate(
    file_source.site_url,
    config.CRAWLER_CLIENT_ID,
    config.CRAWLER_TENANT_ID,
    cert_path,
    config.CRAWLER_CLIENT_CERTIFICATE_PASSWORD
  )
  
  # Get document library
  log_function_output(request_data, f"Getting document library: '{file_source.sharepoint_url_part}'")
  document_library, library_error = try_get_document_library(ctx, file_source.site_url, file_source.sharepoint_url_part)
  
  if not document_library:
    raise Exception(library_error)
  
  # Get all files from the library
  log_function_output(request_data, f"Loading files with filter: '{file_source.filter or '(none)'}'")
  sharepoint_files = get_document_library_files(ctx, document_library, file_source.filter, request_data)
  
  log_function_output(request_data, f"Successfully loaded {len(sharepoint_files)} files from SharePoint")
  
  # Convert SharePointFile objects to CrawledFile objects
  from urllib.parse import quote, urlparse
  crawled_files = []
  
  for sp_file in sharepoint_files:
    # Get file extension
    file_extension = os.path.splitext(sp_file.filename)[1].lstrip('.').lower()
    
    # Extract site path from site_url
    parsed_url = urlparse(file_source.site_url)
    site_path = parsed_url.path
    
    # Construct raw URL from site_url and server_relative_url
    raw_url = f"{file_source.site_url}{sp_file.server_relative_url.replace(site_path, '')}"
    
    # URL-encoded source URL
    source_url = quote(raw_url, safe=':/')
    
    # Construct file_relative_path: domain_id/01_files/source_id/02_embedded/relative_path
    # Extract relative path from server_relative_url by removing the site path and sharepoint_url_part
    relative_from_library = sp_file.server_relative_url.replace(site_path, '').replace(file_source.sharepoint_url_part, '').lstrip('/')
    file_relative_path = os.path.join(
      domain_id,
      CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOCUMENTS_FOLDER,
      source_id,
      CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_EMBEDDED_SUBFOLDER,
      relative_from_library
    )
    
    # Create CrawledFile (without local file system paths)
    crawled_file = CrawledFile(
      sharepoint_listitem_id=int(sp_file.id) if sp_file.id else 0,
      sharepoint_unique_file_id=sp_file.unique_id,
      openai_file_id="",  # Not available from SharePoint API
      file_relative_path=file_relative_path,
      url=source_url,
      raw_url=raw_url,
      server_relative_url=sp_file.server_relative_url,
      filename=sp_file.filename,
      file_type=file_extension,
      file_size=sp_file.file_size,
      last_modified_utc=sp_file.last_modified_utc,
      last_modified_timestamp=sp_file.last_modified_timestamp
    )
    
    crawled_files.append(crawled_file)
  
  log_function_output(request_data, f"Converted {len(crawled_files)} files to CrawledFile objects")
  
  return crawled_files

def load_crawled_files(storage_path: str, domain_id: str, source_id: str, log_data: Dict[str, Any] = None) -> List[CrawledFile]:
  """
  Scan local embedded files directory and return a list of CrawledFile objects.
  
  Args:
    storage_path: Base persistent storage path
    domain_id: The ID of the domain
    source_id: The ID of the file source within the domain
    log_data: Optional logging context
    
  Returns:
    List of CrawledFile objects
    
  Raises:
    FileNotFoundError: If the embedded directory doesn't exist
  """
  from urllib.parse import quote
  
  # Load domain configuration to get source settings
  domain_config = load_domain(storage_path, domain_id, log_data)
  
  # Find the file source with matching source_id
  file_source = next((src for src in domain_config.file_sources if src.source_id == source_id), None)
  
  if not file_source:
    error_message = f"File source '{source_id}' not found in domain '{domain_id}'"
    if log_data:
      log_function_output(log_data, f"ERROR: {error_message}")
    raise FileNotFoundError(error_message)
  
  # Build the path to the embedded files directory
  # Example: C:\Storage\crawler\DOMAIN01\01_files\source01\02_embedded
  embedded_dir = os.path.join(
    storage_path,
    CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_CRAWLER_SUBFOLDER,
    domain_id,
    CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOCUMENTS_FOLDER,
    source_id,
    CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_EMBEDDED_SUBFOLDER
  )
  
  if log_data:
    log_function_output(log_data, f"Scanning embedded files directory: {embedded_dir}")
  
  # Check if directory exists
  if not os.path.exists(embedded_dir):
    error_message = f"Embedded files directory not found: {embedded_dir}"
    if log_data:
      log_function_output(log_data, f"ERROR: {error_message}")
    raise FileNotFoundError(error_message)
  
  # Scan directory recursively
  crawled_files = []
  
  for root, dirs, files in os.walk(embedded_dir):
    for filename in files:
      file_path = os.path.join(root, filename)
      
      # Get file stats
      file_stat = os.stat(file_path)
      file_size = file_stat.st_size
      file_mtime = int(file_stat.st_mtime)  # Convert to int to remove decimals
      
      # Convert timestamp to UTC ISO format with microseconds
      file_mtime_utc = datetime.datetime.fromtimestamp(file_mtime, tz=datetime.timezone.utc)
      file_mtime_utc_str = file_mtime_utc.strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'
      
      # Get last modified date in ISO format (date only)
      file_mtime_date = file_mtime_utc.strftime('%Y-%m-%d')
      
      # Get file extension
      file_extension = os.path.splitext(filename)[1].lstrip('.').lower()
      
      # Build relative path from crawler subfolder
      # Remove the storage_path and crawler subfolder prefix
      crawler_base = os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_CRAWLER_SUBFOLDER)
      relative_path = os.path.relpath(file_path, crawler_base)
      
      # Build relative path from embedded_dir to construct SharePoint URL
      relative_from_embedded = os.path.relpath(file_path, embedded_dir)
      # Convert Windows path separators to forward slashes for URLs
      relative_from_embedded_url = relative_from_embedded.replace('\\', '/')
      
      # Extract site path from site_url (e.g., /sites/SiteName from https://domain.sharepoint.com/sites/SiteName)
      from urllib.parse import urlparse
      parsed_url = urlparse(file_source.site_url)
      site_path = parsed_url.path  # e.g., /sites/AiSearchTest01
      
      # Construct SharePoint URLs based on file source settings
      # Raw URL: site_url + sharepoint_url_part + relative_path
      raw_url = f"{file_source.site_url}{file_source.sharepoint_url_part}/{relative_from_embedded_url}"
      
      # URL-encoded source URL
      source_url = quote(raw_url, safe=':/')
      
      # Server-relative URL: site_path + sharepoint_url_part + relative_path
      server_relative_url = f"{site_path}{file_source.sharepoint_url_part}/{relative_from_embedded_url}"
      
      # Create CrawledFile with empty openai_file_id and SharePoint IDs
      crawled_file = CrawledFile(
        sharepoint_listitem_id=0,  # Not available from local file system
        sharepoint_unique_file_id="",  # Not available from local file system
        openai_file_id="",  # Not available from local file system
        file_relative_path=relative_path,
        url=source_url,
        raw_url=raw_url,
        server_relative_url=server_relative_url,
        filename=filename,
        file_type=file_extension,
        file_size=file_size,
        last_modified_utc=file_mtime_utc_str,
        last_modified_timestamp=file_mtime
      )
      
      crawled_files.append(crawled_file)
  
  if log_data:
    log_function_output(log_data, f"Found {len(crawled_files)} embedded files")
  
  return crawled_files

async def load_vector_store_files_as_crawled_files(openai_client, storage_path: str, domain_id: str, log_data: Dict[str, Any] = None) -> List[CrawledFile]:
  """
  Load files from OpenAI vector store for a specific domain and convert to CrawledFile objects.
  
  Args:
    openai_client: AsyncAzureOpenAI or AsyncOpenAI client
    storage_path: Base persistent storage path
    domain_id: The ID of the domain to load files for
    log_data: Optional logging data dictionary
    
  Returns:
    List of CrawledFile objects with OpenAI and local file metadata
  """
  # Load domain configuration
  domain_config = load_domain(storage_path, domain_id, log_data)
  vector_store_id = domain_config.vector_store_id
  
  if not vector_store_id:
    if log_data:
      log_function_output(log_data, f"ERROR: Domain '{domain_id}' does not have a vector_store_id configured")
    return []
  
  if log_data:
    log_function_output(log_data, f"Loading files from vector store '{vector_store_id}' for domain '{domain_id}'...")
  
  # Get files from vector store with enriched metadata
  vs_files_dict = await get_vector_store_files_with_filenames_as_dict(openai_client, vector_store_id)
  
  if log_data:
    log_function_output(log_data, f"Retrieved {len(vs_files_dict)} files from vector store")
  
  # Load files metadata from domain folder
  domain_folder = os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER, domain_id)
  files_metadata_path = os.path.join(domain_folder, "files_metadata.json")
  
  files_metadata_dict = {}
  if os.path.exists(files_metadata_path):
    with open(files_metadata_path, 'r', encoding='utf-8') as f:
      files_metadata_list = json.load(f)
      # Convert to dictionary with openai_file_id as key (v3) or file_id (v2)
      files_metadata_dict = {item.get('openai_file_id', item.get('file_id', '')): item for item in files_metadata_list}
  
  # Convert to CrawledFile objects
  crawled_files = []
  for file_id, vs_file in vs_files_dict.items():
    # Get metadata from files_metadata.json if available
    # After v3 migration, metadata is flat (not nested under file_metadata)
    file_metadata = files_metadata_dict.get(file_id, {})
    
    # Check if this is v2 format (nested) or v3 format (flat)
    if 'file_metadata' in file_metadata:
      # V2 format - nested structure
      file_meta_info = file_metadata.get('file_metadata', {})
      embedded_file_relative_path = file_metadata.get('embedded_file_relative_path', '')
    else:
      # V3 format - flat structure
      file_meta_info = file_metadata
      embedded_file_relative_path = file_metadata.get('file_relative_path', '')
    
    crawled_file = CrawledFile(
      sharepoint_listitem_id=file_meta_info.get('sharepoint_listitem_id', 0),
      sharepoint_unique_file_id=file_meta_info.get('sharepoint_unique_file_id', ''),
      openai_file_id=file_id,
      file_relative_path=embedded_file_relative_path,
      url=file_meta_info.get('url', file_meta_info.get('source', '')),
      raw_url=file_meta_info.get('raw_url', ''),
      server_relative_url=file_meta_info.get('server_relative_url', ''),
      filename=vs_file.filename,
      file_type=file_meta_info.get('file_type', ''),
      file_size=file_meta_info.get('file_size', 0),
      last_modified_utc=file_meta_info.get('last_modified_utc', file_meta_info.get('last_modified', '')),
      last_modified_timestamp=file_meta_info.get('last_modified_timestamp', 0)
    )
    
    crawled_files.append(crawled_file)
  
  if log_data:
    log_function_output(log_data, f"Converted {len(crawled_files)} vector store files to CrawledFile objects")
  
  return crawled_files

def is_files_metadata_v2_format(first_item: Dict[str, Any]) -> bool:
  """
  Detect if a files_metadata.json item is in V2 format.
  
  V2 format has:
  - embedded_file_relative_path
  - file_metadata (nested object)
  - file_id
  
  Args:
    first_item: First item from the files_metadata.json array
    
  Returns:
    True if V2 format, False otherwise
  """
  return (
    'embedded_file_relative_path' in first_item and
    'file_metadata' in first_item and
    isinstance(first_item.get('file_metadata'), dict)
  )

def is_files_metadata_v3_format(first_item: Dict[str, Any]) -> bool:
  """
  Detect if a files_metadata.json item is in V3 format.
  
  V3 format has:
  - openai_file_id (flat structure)
  - file_relative_path
  - No nested file_metadata object
  
  Args:
    first_item: First item from the files_metadata.json array
    
  Returns:
    True if V3 format, False otherwise
  """
  return (
    'openai_file_id' in first_item and
    'file_relative_path' in first_item and
    'file_metadata' not in first_item
  )

def convert_file_metadata_item_from_v2_to_v3(v2_item: Dict[str, Any]) -> Dict[str, Any]:
  """
  Convert a single files_metadata.json item from V2 to V3 format.
  
  V2 format has nested structure with file_metadata object.
  V3 format has flat structure matching CrawledFile dataclass.
  
  Args:
    v2_item: Single item in V2 format
    
  Returns:
    Item converted to V3 format
  """
  file_metadata = v2_item.get('file_metadata', {})
  
  v3_item = {
    "sharepoint_listitem_id": file_metadata.get('sharepoint_listitem_id', 0),
    "sharepoint_unique_file_id": file_metadata.get('sharepoint_unique_file_id', '').strip() if isinstance(file_metadata.get('sharepoint_unique_file_id'), str) else '',
    "openai_file_id": v2_item.get('file_id', '').strip() if isinstance(v2_item.get('file_id'), str) else '',
    "file_relative_path": v2_item.get('embedded_file_relative_path', '').strip() if isinstance(v2_item.get('embedded_file_relative_path'), str) else '',
    "url": file_metadata.get('source', '').strip() if isinstance(file_metadata.get('source'), str) else '',
    "raw_url": file_metadata.get('raw_url', '').strip() if isinstance(file_metadata.get('raw_url'), str) else '',
    "server_relative_url": file_metadata.get('server_relative_url', '').strip() if isinstance(file_metadata.get('server_relative_url'), str) else '',
    "filename": file_metadata.get('filename', '').strip() if isinstance(file_metadata.get('filename'), str) else '',
    "file_type": file_metadata.get('file_type', '').strip() if isinstance(file_metadata.get('file_type'), str) else '',
    "file_size": file_metadata.get('file_size', 0),
    "last_modified_utc": v2_item.get('embedded_file_last_modified_utc', '').strip() if isinstance(v2_item.get('embedded_file_last_modified_utc'), str) else '',
    "last_modified_timestamp": file_metadata.get('last_modified_timestamp', 0)
  }
  
  return v3_item

def download_files_from_sharepoint(system_info, domain_id: str, source_id: str, request_data: Dict[str, Any], config) -> Dict[str, Any]:
  """
  Download files from SharePoint for a specific domain source, creating CSV maps.
  
  This function:
  1. Loads files from SharePoint using load_files_from_sharepoint_source
  2. Filters files by accepted file types
  3. Creates sharepoint_map.csv with SharePoint metadata
  4. Downloads each file preserving folder structure
  5. Creates files_map.csv with local file metadata
  6. Logs failed downloads to sharepoint_error_map.csv
  
  Args:
    system_info: System configuration object with PERSISTENT_STORAGE_PATH
    domain_id: The ID of the domain to download files for
    source_id: The ID of the file source within the domain (optional, if None all sources are downloaded)
    request_data: Dictionary for logging output
    config: Configuration object with crawler credentials
    
  Returns:
    Dictionary with download statistics and results
    
  Raises:
    ValueError: If validation fails or required configuration is missing
    FileNotFoundError: If domain or source is not found
  """
  
  # Validate PERSISTENT_STORAGE_PATH
  if not system_info.PERSISTENT_STORAGE_PATH:
    raise ValueError("PERSISTENT_STORAGE_PATH not configured")
  
  storage_path = system_info.PERSISTENT_STORAGE_PATH
  
  # Load domain configuration
  log_function_output(request_data, f"Loading domain: '{domain_id}'")
  domain_config = load_domain(storage_path, domain_id, request_data)
  
  # Determine which sources to process
  sources_to_process = []
  if source_id:
    file_source = next((src for src in domain_config.file_sources if src.source_id == source_id), None)
    if not file_source:
      raise FileNotFoundError(f"File source '{source_id}' not found in domain '{domain_id}'")
    sources_to_process.append(file_source)
  else:
    sources_to_process = domain_config.file_sources
  
  if not sources_to_process:
    raise ValueError(f"No file sources found in domain '{domain_id}'")
  
  log_function_output(request_data, f"Processing {len(sources_to_process)} source(s)")
  
  # Prepare paths
  crawler_base_path = os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_CRAWLER_SUBFOLDER, domain_id)
  files_base_path = os.path.join(crawler_base_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOCUMENTS_FOLDER)
  
  # Ensure base path exists
  os.makedirs(files_base_path, exist_ok=True)
  
  # CSV file paths
  sharepoint_map_path = os.path.join(files_base_path, "sharepoint_map.csv")
  files_map_path = os.path.join(files_base_path, "files_map.csv")
  sharepoint_error_map_path = os.path.join(files_base_path, "sharepoint_error_map.csv")
  
  # Define CSV file configurations (path, header)
  map_file_headers = [
    (sharepoint_map_path, ['source_id', 'sharepoint_listitem_id', 'sharepoint_unique_file_id', 'server_relative_url', 'file_relative_path', 'file_size', 'last_modified_utc', 'last_modified_timestamp']),
    (files_map_path, ['source_id', 'file_relative_path', 'file_size', 'last_modified_utc', 'last_modified_timestamp']),
    (sharepoint_error_map_path, ['source_id', 'sharepoint_listitem_id', 'sharepoint_unique_file_id', 'file_relative_path', 'error_message'])
  ]
  
  # Handle existing CSV files based on source_id parameter
  if source_id:
    # If source_id is specified, remove entries for this source_id from existing CSV files
    log_function_output(request_data, f"Cleaning existing entries for source_id='{source_id}' from CSV files...")
    
    for csv_path, header in map_file_headers:
      if os.path.exists(csv_path):
        # Read existing entries
        rows_to_keep = []
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
          reader = csv.reader(csvfile)
          header_row = next(reader, None)
          
          # Keep rows that don't match the source_id
          for row in reader:
            if len(row) > 0 and row[0] != source_id:
              rows_to_keep.append(row)
        
        # Rewrite the file with filtered entries
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
          writer = csv.writer(csvfile)
          writer.writerow(header)
          writer.writerows(rows_to_keep)
        
        log_function_output(request_data, f"Removed entries for source_id='{source_id}' from {os.path.basename(csv_path)}")
      else:
        # Create new file with header
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
          writer = csv.writer(csvfile)
          writer.writerow(header)
        log_function_output(request_data, f"Created: {csv_path}")
  else:
    # If no source_id specified, delete all CSV files
    log_function_output(request_data, "Deleting all existing CSV files...")
    
    for csv_path, header in map_file_headers:
      if os.path.exists(csv_path):
        os.remove(csv_path)
        log_function_output(request_data, f"Deleted: {os.path.basename(csv_path)}")
      
      # Create new file with header
      with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)
      log_function_output(request_data, f"Created: {csv_path}")
  
  # Initialize results
  results = {
    'domain_id': domain_id,
    'sources_processed': [],
    'total_files_in_sharepoint': 0,
    'total_files_in_sharepoint_unsupported': 0,
    'total_files_downloaded': 0,
    'total_files_failed': 0
  }
  
  # Process each source
  for idx, file_source in enumerate(sources_to_process, 1):
    log_function_output(request_data, "")
    log_function_output(request_data, f"{'=' * 80}")
    log_function_output(request_data, f"PROCESSING SOURCE [ {idx} / {len(sources_to_process)} ]: {file_source.source_id}")
    log_function_output(request_data, f"{'=' * 80}")
    
    source_result = {
      'source_id': file_source.source_id,
      'site_url': file_source.site_url,
      'sharepoint_url_part': file_source.sharepoint_url_part,
      'filter': file_source.filter,
      'files_in_sharepoint': 0,
      'files_downloaded': 0,
      'files_failed': 0
    }
    
    # Paths for this source
    local_embedded_path = os.path.join(files_base_path, file_source.source_id, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_EMBEDDED_SUBFOLDER)
    local_failed_path = os.path.join(files_base_path, file_source.source_id, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_FAILED_SUBFOLDER)
    
    # Clean the download folders before downloading
    if os.path.exists(local_embedded_path):
      log_function_output(request_data, f"Cleaning embedded folder: {local_embedded_path}")
      shutil.rmtree(local_embedded_path)
      log_function_output(request_data, f"Cleaned embedded folder")
    
    if os.path.exists(local_failed_path):
      log_function_output(request_data, f"Cleaning failed folder: {local_failed_path}")
      shutil.rmtree(local_failed_path)
      log_function_output(request_data, f"Cleaned failed folder")
    
    # Create fresh download folders
    os.makedirs(local_embedded_path, exist_ok=True)
    log_function_output(request_data, f"Created embedded folder: {local_embedded_path}")
    
    os.makedirs(local_failed_path, exist_ok=True)
    log_function_output(request_data, f"Created failed folder: {local_failed_path}")
    
    # Load files from SharePoint
    log_function_output(request_data, "Loading files from SharePoint...")
    sharepoint_files = load_files_from_sharepoint_source(system_info, domain_id, file_source.source_id, request_data, config)
    log_function_output(request_data, f"Loaded {len(sharepoint_files)} files from SharePoint")
    
    # Filter files by accepted file types
    supported_files = [f for f in sharepoint_files if f.file_type.lower() in CRAWLER_HARDCODED_CONFIG.DEFAULT_FILETYPES_ACCEPTED_BY_VECTOR_STORES]
    unsupported_count = len(sharepoint_files) - len(supported_files)
    
    log_function_output(request_data, f"Total files in SharePoint: {len(sharepoint_files)}")
    
    if unsupported_count > 0:
      log_function_output(request_data, f"Filtered out {unsupported_count} unsupported file type(s)")
    
    log_function_output(request_data, f"Files with supported types: {len(supported_files)}")
    
    source_result['files_in_sharepoint'] = len(sharepoint_files)
    source_result['files_in_sharepoint_unsupported'] = unsupported_count
    results['total_files_in_sharepoint'] += len(sharepoint_files)
    results['total_files_in_sharepoint_unsupported'] += unsupported_count
    
    # Write to sharepoint_map.csv
    log_function_output(request_data, "Writing to sharepoint_map.csv...")
    with open(sharepoint_map_path, 'a', newline='', encoding='utf-8') as csvfile:
      writer = csv.writer(csvfile)
      for sp_file in supported_files:
        writer.writerow([
          file_source.source_id,
          sp_file.sharepoint_listitem_id,
          sp_file.sharepoint_unique_file_id,
          sp_file.server_relative_url,
          sp_file.file_relative_path,
          sp_file.file_size,
          sp_file.last_modified_utc,
          sp_file.last_modified_timestamp
        ])
    
    log_function_output(request_data, f"Wrote {len(supported_files)} entries to sharepoint_map.csv")
    
    # Connect to SharePoint for downloading
    log_function_output(request_data, "Connecting to SharePoint for file downloads...")
    cert_path = os.path.join(storage_path, config.CRAWLER_CLIENT_CERTIFICATE_PFX_FILE)
    ctx = connect_to_site_using_client_id_and_certificate(
      file_source.site_url,
      config.CRAWLER_CLIENT_ID,
      config.CRAWLER_TENANT_ID,
      cert_path,
      config.CRAWLER_CLIENT_CERTIFICATE_PASSWORD
    )
    
    # Download files
    log_function_output(request_data, f"Downloading {len(supported_files)} files...")
    downloaded_count = 0
    failed_count = 0
    
    for file_idx, sp_file in enumerate(supported_files, 1):
      try:
        # Extract relative path from file_relative_path
        # file_relative_path format: domain_id/01_files/source_id/02_embedded/relative_path
        path_parts = sp_file.file_relative_path.split(os.sep)
        # Find the index of EMBEDDED_SUBFOLDER and take everything after it
        try:
          embedded_idx = path_parts.index(CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_EMBEDDED_SUBFOLDER)
          file_rel_path = os.sep.join(path_parts[embedded_idx + 1:])
        except ValueError:
          # Fallback: use filename only
          file_rel_path = sp_file.filename
        
        local_file_path = os.path.join(local_embedded_path, file_rel_path)
        local_file_path_normalized = normalize_long_path(local_file_path)
        
        # Create directory structure
        local_dir = os.path.dirname(local_file_path_normalized)
        os.makedirs(local_dir, exist_ok=True)
        
        # Download file from SharePoint
        with open(local_file_path_normalized, 'wb') as local_file:
          file_obj = ctx.web.get_file_by_server_relative_url(sp_file.server_relative_url)
          file_obj.download(local_file).execute_query()
        
        # Set file modification time to match SharePoint
        timestamp = sp_file.last_modified_timestamp
        os.utime(local_file_path_normalized, (timestamp, timestamp))
        
        # Get actual file size from disk
        actual_file_size = os.path.getsize(local_file_path_normalized)
        
        # Get actual modification time from disk
        file_stat = os.stat(local_file_path_normalized)
        actual_mtime = int(file_stat.st_mtime)
        actual_mtime_utc = datetime.datetime.fromtimestamp(actual_mtime, tz=datetime.timezone.utc)
        actual_mtime_utc_str = actual_mtime_utc.strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'
        
        # Append to files_map.csv immediately after successful download
        with open(files_map_path, 'a', newline='', encoding='utf-8') as csvfile:
          writer = csv.writer(csvfile)
          writer.writerow([
            file_source.source_id,
            file_rel_path,
            actual_file_size,
            actual_mtime_utc_str,
            actual_mtime
          ])
        
        downloaded_count += 1
        
        # Log progress every 10 files
        if downloaded_count % 10 == 0 or downloaded_count == len(supported_files):
          log_function_output(request_data, f"Downloaded [ {downloaded_count} / {len(supported_files)} ] files...")
        
      except Exception as e:
        failed_count += 1
        error_message = str(e)
        
        # Log to sharepoint_error_map.csv
        with open(sharepoint_error_map_path, 'a', newline='', encoding='utf-8') as csvfile:
          writer = csv.writer(csvfile)
          writer.writerow([
            file_source.source_id,
            sp_file.sharepoint_listitem_id,
            sp_file.sharepoint_unique_file_id,
            sp_file.file_relative_path,
            error_message
          ])
        
        log_function_output(request_data, f"ERROR downloading file {file_idx}/{len(supported_files)}: {sp_file.filename} - {error_message}")
    
    log_function_output(request_data, f"Downloaded {downloaded_count} files successfully")
    if failed_count > 0:
      log_function_output(request_data, f"Failed to download {failed_count} files (see sharepoint_error_map.csv)")
    
    source_result['files_downloaded'] = downloaded_count
    source_result['files_failed'] = failed_count
    results['sources_processed'].append(source_result)
    results['total_files_downloaded'] += downloaded_count
    results['total_files_failed'] += failed_count
  
  log_function_output(request_data, "")
  log_function_output(request_data, f"{'=' * 80}")
  log_function_output(request_data, "DOWNLOAD COMPLETE")
  log_function_output(request_data, f"{'=' * 80}")
  log_function_output(request_data, f"Total files in SharePoint: {results['total_files_in_sharepoint']}")
  log_function_output(request_data, f"Total files in SharePoint (unsupported): {results['total_files_in_sharepoint_unsupported']}")
  log_function_output(request_data, f"Total files downloaded: {results['total_files_downloaded']}")
  log_function_output(request_data, f"Total files failed: {results['total_files_failed']}")
  
  return results