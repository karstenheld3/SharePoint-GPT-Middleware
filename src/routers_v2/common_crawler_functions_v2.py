# Common functions and dataclasses for domains management V2
# V2 version using MiddlewareLogger
import json, os, re, shutil
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from hardcoded_config import CRAWLER_HARDCODED_CONFIG
from routers_v2.common_logging_functions_v2 import MiddlewareLogger

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

def load_domain(storage_path: str, domain_id: str, logger: Optional[MiddlewareLogger] = None) -> DomainConfig:
  """
  Load a single domain configuration by domain_id.
  
  Args:
    storage_path: Base persistent storage path
    domain_id: The ID of the domain to load
    logger: Optional MiddlewareLogger instance for logging output
    
  Returns:
    DomainConfig dataclass
    
  Raises:
    FileNotFoundError: If domain folder or domain.json doesn't exist
    ValueError: If domain data is invalid
  """
  domains_path = os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER)
  domain_json_path = os.path.join(domains_path, domain_id, CRAWLER_HARDCODED_CONFIG.DOMAIN_JSON)
  
  if logger:
    logger.log_function_output(f"Loading domain '{domain_id}' from: {domain_json_path}")
  
  if not os.path.exists(domain_json_path):
    error_message = f"Domain configuration not found: {domain_json_path}"
    if logger:
      logger.log_function_output(f"ERROR: {error_message}")
    raise FileNotFoundError(error_message)
  
  try:
    with open(domain_json_path, 'r', encoding='utf-8') as f:
      domain_data = json.load(f)
      
      file_sources = [FileSource(**src) for src in domain_data.get('file_sources', [])]
      sitepage_sources = [SitePageSource(**src) for src in domain_data.get('sitepage_sources', [])]
      list_sources = [ListSource(**src) for src in domain_data.get('list_sources', [])]
      
      domain_config = DomainConfig(
        domain_id=domain_id,  # Derived from folder name, not stored in JSON
        vector_store_name=domain_data['vector_store_name'],
        vector_store_id=domain_data['vector_store_id'],
        name=domain_data['name'],
        description=domain_data['description'],
        file_sources=file_sources,
        sitepage_sources=sitepage_sources,
        list_sources=list_sources
      )
      
      if logger:
        logger.log_function_output(f"Successfully loaded domain: {domain_config.domain_id}")
      
      return domain_config
      
  except KeyError as e:
    error_message = f"Missing required field in domain.json: {str(e)}"
    if logger:
      logger.log_function_output(f"ERROR: {error_message}")
    raise ValueError(error_message)
  except Exception as e:
    error_message = f"Failed to load domain '{domain_id}': {str(e)}"
    if logger:
      logger.log_function_output(f"ERROR: {error_message}")
    raise

def load_all_domains(storage_path: str, logger: Optional[MiddlewareLogger] = None) -> List[DomainConfig]:
  """
  Load all domain configurations from the domains folder.
  Creates the domains folder if it doesn't exist.
  
  Args:
    storage_path: Base persistent storage path
    logger: Optional MiddlewareLogger instance for logging output
    
  Returns:
    List of DomainConfig dataclasses
  """
  domains_path = os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER)
  
  if logger:
    logger.log_function_output(f"Scanning domains path: {domains_path}")
  
  if not os.path.exists(domains_path):
    os.makedirs(domains_path, exist_ok=True)
    if logger:
      logger.log_function_output(f"Created domains folder: {domains_path}")
  
  domain_folders = [d for d in os.listdir(domains_path) if os.path.isdir(os.path.join(domains_path, d))]
  
  if logger:
    logger.log_function_output(f"Found {len(domain_folders)} domain folder(s)")
  
  domains_list = []
  for domain_folder in domain_folders:
    try:
      domain_config = load_domain(storage_path, domain_folder, logger)
      domains_list.append(domain_config)
    except (FileNotFoundError, ValueError) as e:
      if logger:
        logger.log_function_output(f"WARNING: Skipping domain '{domain_folder}': {str(e)}")
      continue
  
  if logger:
    logger.log_function_output(f"Successfully loaded {len(domains_list)} domain(s)")
  
  return domains_list

def domain_config_to_dict(domain: DomainConfig) -> Dict[str, Any]:
  """Convert a DomainConfig dataclass to a dictionary."""
  return asdict(domain)

def validate_domain_config(domain_data: Dict[str, Any]) -> tuple[bool, str]:
  """
  Validate domain configuration data.
  
  Args:
    domain_data: Dictionary containing domain configuration
    
  Returns:
    Tuple of (is_valid, error_message)
  """
  required_fields = ['name', 'vector_store_name', 'description']  # domain_id derived from folder name
  
  for field in required_fields:
    if field not in domain_data or not domain_data[field]:
      return False, f"Missing required field: {field}"
  
  domain_id = domain_data['domain_id']
  if not domain_id.replace('_', '').replace('-', '').isalnum():
    return False, "domain_id must contain only alphanumeric characters, underscores, and hyphens"
  
  if 'file_sources' not in domain_data:
    domain_data['file_sources'] = []
  if 'sitepage_sources' not in domain_data:
    domain_data['sitepage_sources'] = []
  if 'list_sources' not in domain_data:
    domain_data['list_sources'] = []
  
  return True, ""

def save_domain_to_file(storage_path: str, domain_config: DomainConfig, logger: Optional[MiddlewareLogger] = None) -> None:
  """
  Save a domain configuration to disk.
  
  Args:
    storage_path: Base persistent storage path
    domain_config: DomainConfig dataclass to save
    logger: Optional MiddlewareLogger instance for logging output
    
  Raises:
    OSError: If file operations fail
  """
  domains_path = os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER)
  domain_folder = os.path.join(domains_path, domain_config.domain_id)
  domain_json_path = os.path.join(domain_folder, CRAWLER_HARDCODED_CONFIG.DOMAIN_JSON)
  
  os.makedirs(domain_folder, exist_ok=True)
  
  if logger:
    logger.log_function_output(f"Saving domain to: {domain_json_path}")
  
  domain_dict = domain_config_to_dict(domain_config)
  domain_dict.pop('domain_id', None)  # Don't store domain_id in JSON - derived from folder name
  
  with open(domain_json_path, 'w', encoding='utf-8') as f:
    json.dump(domain_dict, f, indent=2, ensure_ascii=False)
  
  if logger:
    logger.log_function_output(f"Domain saved successfully: {domain_config.domain_id}")

def delete_domain_folder(storage_path: str, domain_id: str, logger: Optional[MiddlewareLogger] = None) -> None:
  """
  Delete a domain folder and all its contents.
  
  Args:
    storage_path: Base persistent storage path
    domain_id: ID of the domain to delete
    logger: Optional MiddlewareLogger instance for logging output
    
  Raises:
    FileNotFoundError: If domain folder doesn't exist
    OSError: If deletion fails
  """
  domains_path = os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER)
  domain_folder = os.path.join(domains_path, domain_id)
  
  if not os.path.exists(domain_folder):
    error_msg = f"Domain folder not found: {domain_id}"
    if logger:
      logger.log_function_output(f"ERROR: {error_msg}")
    raise FileNotFoundError(error_msg)
  
  if logger:
    logger.log_function_output(f"Deleting domain folder: {domain_folder}")
  
  shutil.rmtree(domain_folder)
  
  if logger:
    logger.log_function_output(f"Domain deleted successfully: {domain_id}")

def rename_domain(storage_path: str, source_domain_id: str, target_domain_id: str) -> tuple[bool, str]:
  """
  Rename a domain by renaming its folder.
  Returns (success, error_message).
  """
  domains_path = os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER)
  source_path = os.path.join(domains_path, source_domain_id)
  target_path = os.path.join(domains_path, target_domain_id)
  
  if not os.path.exists(source_path): return False, f"Source domain '{source_domain_id}' not found."
  if os.path.exists(target_path): return False, f"Target domain '{target_domain_id}' already exists."
  if not re.match(r'^[a-zA-Z0-9_-]+$', target_domain_id): return False, f"Invalid domain ID format: '{target_domain_id}'. Use only letters, numbers, underscores, hyphens."
  
  try:
    os.rename(source_path, target_path)
    return True, ""
  except Exception as e:
    return False, f"Failed to rename domain: {str(e)}"
