# Common functions and dataclasses for SharePoint crawler
import json, os, zipfile
from dataclasses import asdict, dataclass
from typing import Any, Dict, List

from hardcoded_config import CRAWLER_HARDCODED_CONFIG
from utils import log_function_output

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