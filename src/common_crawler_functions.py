# Common functions and dataclasses for SharePoint crawler
import json, logging, os, zipfile
from dataclasses import dataclass
from typing import Any, Dict, List

from hardcoded_config import CRAWLER_HARDCODED_CONFIG
from utils import log_function_output

logger = logging.getLogger(__name__)

@dataclass
class DocumentSource:
    """Represents a SharePoint document library source."""
    site_url: str
    sharepoint_url_part: str
    filter: str

@dataclass
class PageSource:
    """Represents a SharePoint site pages source."""
    site_url: str
    sharepoint_url_part: str
    filter: str

@dataclass
class ListSource:
    """Represents a SharePoint list source."""
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
    document_sources: List[DocumentSource]
    page_sources: List[PageSource]
    list_sources: List[ListSource]

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
    ValueError: If domain data is invalid
  """
  domains_path = os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER)
  
  if log_data:
    log_function_output(log_data, f"Scanning domains path: {domains_path}")
  else:
    logger.info(f"Scanning domains path: {domains_path}")
  
  # Check if domains folder exists
  if not os.path.exists(domains_path):
    error_message = f"Domains folder not found: {domains_path}"
    if log_data:
      log_function_output(log_data, f"ERROR: {error_message}")
    else:
      logger.error(error_message)
    raise FileNotFoundError(error_message)
  
  # Collect all domain.json files
  domains_list = []
  domain_folders = [d for d in os.listdir(domains_path) if os.path.isdir(os.path.join(domains_path, d))]
  
  if log_data:
    log_function_output(log_data, f"Found {len(domain_folders)} domain folder(s)")
  else:
    logger.info(f"Found {len(domain_folders)} domain folder(s)")
  
  for domain_folder in domain_folders:
    domain_json_path = os.path.join(domains_path, domain_folder, "domain.json")
    
    if os.path.exists(domain_json_path):
      try:
        with open(domain_json_path, 'r', encoding='utf-8') as f:
          domain_data = json.load(f)
          
          # Convert nested dictionaries to dataclasses
          document_sources = [DocumentSource(**src) for src in domain_data.get('document_sources', [])]
          page_sources = [PageSource(**src) for src in domain_data.get('page_sources', [])]
          list_sources = [ListSource(**src) for src in domain_data.get('list_sources', [])]
          
          domain_config = DomainConfig(
            domain_id=domain_data['domain_id'],
            vector_store_name=domain_data['vector_store_name'],
            vector_store_id=domain_data['vector_store_id'],
            name=domain_data['name'],
            description=domain_data['description'],
            document_sources=document_sources,
            page_sources=page_sources,
            list_sources=list_sources
          )
          
          domains_list.append(domain_config)
          
          if log_data:
            log_function_output(log_data, f"Loaded domain: {domain_config.domain_id}")
          else:
            logger.info(f"Loaded domain: {domain_config.domain_id}")
      except Exception as e:
        if log_data:
          log_function_output(log_data, f"WARNING: Failed to load {domain_json_path}: {str(e)}")
        else:
          logger.warning(f"Failed to load {domain_json_path}: {str(e)}")
    else:
      if log_data:
        log_function_output(log_data, f"WARNING: domain.json not found in {domain_folder}")
      else:
        logger.warning(f"domain.json not found in {domain_folder}")
  
  if log_data:
    log_function_output(log_data, f"Successfully loaded {len(domains_list)} domain(s)")
  else:
    logger.info(f"Successfully loaded {len(domains_list)} domain(s)")
  
  return domains_list

def domain_config_to_dict(domain: DomainConfig) -> Dict[str, Any]:
  """
  Convert a DomainConfig dataclass to a dictionary.
  
  Args:
    domain: DomainConfig dataclass instance
    
  Returns:
    Dictionary representation of the domain configuration
  """
  return {
    "domain_id": domain.domain_id,
    "vector_store_name": domain.vector_store_name,
    "vector_store_id": domain.vector_store_id,
    "name": domain.name,
    "description": domain.description,
    "document_sources": [
      {"site_url": src.site_url, "sharepoint_url_part": src.sharepoint_url_part, "filter": src.filter}
      for src in domain.document_sources
    ],
    "page_sources": [
      {"site_url": src.site_url, "sharepoint_url_part": src.sharepoint_url_part, "filter": src.filter}
      for src in domain.page_sources
    ],
    "list_sources": [
      {"site_url": src.site_url, "list_name": src.list_name, "filter": src.filter}
      for src in domain.list_sources
    ]
  }

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
    else:
      logger.error(f"Error scanning directory {path}: {str(e)}")
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