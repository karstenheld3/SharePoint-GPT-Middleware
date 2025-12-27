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


# ----------------------------------------- START: Path Helpers -------------------------------------------------------

# Map source_type to folder prefix using config constants
SOURCE_TYPE_FOLDERS = {
  "file_sources": CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOCUMENTS_FOLDER,      # "01_files"
  "list_sources": CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_LISTS_FOLDER,          # "02_lists"
  "sitepage_sources": CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_SITEPAGES_FOLDER   # "03_sitepages"
}

def get_source_folder_path(storage_path: str, domain_id: str, source_type: str, source_id: str) -> str:
  """
  Get the base folder path for a source.
  Example: /data/crawler/DOMAIN01/01_files/source01/
  """
  crawler_folder = CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_CRAWLER_SUBFOLDER
  return os.path.join(storage_path, crawler_folder, domain_id, SOURCE_TYPE_FOLDERS[source_type], source_id)

def get_embedded_folder_path(storage_path: str, domain_id: str, source_type: str, source_id: str) -> str:
  """Get path to 02_embedded subfolder."""
  return os.path.join(get_source_folder_path(storage_path, domain_id, source_type, source_id), CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_EMBEDDED_SUBFOLDER)

def get_failed_folder_path(storage_path: str, domain_id: str, source_type: str, source_id: str) -> str:
  """Get path to 03_failed subfolder."""
  return os.path.join(get_source_folder_path(storage_path, domain_id, source_type, source_id), CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_FAILED_SUBFOLDER)

def get_originals_folder_path(storage_path: str, domain_id: str, source_type: str, source_id: str) -> str:
  """Get path to 01_originals subfolder (lists/sitepages only)."""
  return os.path.join(get_source_folder_path(storage_path, domain_id, source_type, source_id), CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_ORIGINALS_SUBFOLDER)

def server_relative_url_to_local_path(server_relative_url: str, sharepoint_url_part: str) -> str:
  """
  Convert SharePoint server_relative_url to local relative path.
  Example: "/sites/demo/Shared Documents/Reports/Q1.docx" with sharepoint_url_part="/Shared Documents" -> "Reports/Q1.docx"
  """
  from urllib.parse import unquote
  decoded_url = unquote(server_relative_url)
  decoded_part = unquote(sharepoint_url_part)
  idx = decoded_url.lower().find(decoded_part.lower())
  if idx != -1:
    local_path = decoded_url[idx + len(decoded_part):]
    local_path = local_path.lstrip('/')
    return local_path.replace('/', os.sep)
  return os.path.basename(decoded_url)

def get_file_relative_path(domain_id: str, source_type: str, source_id: str, subfolder: str, local_path: str) -> str:
  """
  Build file_relative_path for map files.
  Example: "DOMAIN01\\01_files\\source01\\02_embedded\\Reports\\Q1.docx"
  """
  return os.path.join(domain_id, SOURCE_TYPE_FOLDERS[source_type], source_id, subfolder, local_path)

# ----------------------------------------- END: Path Helpers ---------------------------------------------------------


# ----------------------------------------- START: files_metadata.json Helpers ----------------------------------------

STANDARD_METADATA_FIELDS = {
  "sharepoint_listitem_id", "sharepoint_unique_file_id", "openai_file_id",
  "file_relative_path", "url", "raw_url", "server_relative_url",
  "filename", "file_type", "file_size", "last_modified_utc", "last_modified_timestamp",
  "embedded_utc", "source_id", "source_type"
}

def get_domain_path(storage_path: str, domain_id: str) -> str:
  """Get path to domain folder in domains subfolder."""
  return os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER, domain_id)

def load_files_metadata(domain_path: str) -> list:
  """Load files_metadata.json, return empty list if not exists."""
  metadata_path = os.path.join(domain_path, CRAWLER_HARDCODED_CONFIG.FILES_METADATA_JSON)
  if not os.path.exists(metadata_path): return []
  try:
    with open(metadata_path, 'r', encoding='utf-8') as f:
      return json.load(f)
  except Exception:
    return []

def save_files_metadata(domain_path: str, metadata: list) -> None:
  """Save files_metadata.json with graceful write (temp + rename)."""
  metadata_path = os.path.join(domain_path, CRAWLER_HARDCODED_CONFIG.FILES_METADATA_JSON)
  temp_path = metadata_path + ".tmp"
  os.makedirs(domain_path, exist_ok=True)
  with open(temp_path, 'w', encoding='utf-8') as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)
  os.replace(temp_path, metadata_path)

def carry_over_custom_properties(new_entry: dict, existing_entries: list) -> dict:
  """
  Copy non-standard fields from most recent existing entry with same sharepoint_unique_file_id.
  Implements V2CR-FR-06.
  """
  target_uid = new_entry.get("sharepoint_unique_file_id")
  if not target_uid: return new_entry
  matching = [e for e in existing_entries if e.get("sharepoint_unique_file_id") == target_uid]
  if not matching: return new_entry
  most_recent = max(matching, key=lambda e: e.get("embedded_utc", ""))
  for key, value in most_recent.items():
    if key not in STANDARD_METADATA_FIELDS and key not in new_entry:
      new_entry[key] = value
  return new_entry

def update_files_metadata(domain_path: str, new_entries: list) -> None:
  """
  Add new entries to files_metadata.json with carry-over of custom properties.
  Implements V2CR-FR-06.
  """
  existing = load_files_metadata(domain_path)
  for entry in new_entries:
    entry = carry_over_custom_properties(entry, existing)
    existing.append(entry)
  save_files_metadata(domain_path, existing)

# ----------------------------------------- END: files_metadata.json Helpers ------------------------------------------


# ----------------------------------------- START: Source Filtering ---------------------------------------------------

def get_sources_for_scope(domain: DomainConfig, scope: str, source_id: Optional[str] = None) -> list:
  """
  Filter domain sources by scope and optional source_id.
  
  Args:
    domain: DomainConfig with file_sources, list_sources, sitepage_sources
    scope: "all" | "files" | "lists" | "sitepages"
    source_id: Optional filter to single source
    
  Returns:
    List of (source_type, source) tuples.
  """
  sources = []
  if scope in ("all", "files"):
    for src in domain.file_sources:
      sources.append(("file_sources", src))
  if scope in ("all", "lists"):
    for src in domain.list_sources:
      sources.append(("list_sources", src))
  if scope in ("all", "sitepages"):
    for src in domain.sitepage_sources:
      sources.append(("sitepage_sources", src))
  
  if source_id:
    sources = [(st, src) for st, src in sources if src.source_id == source_id]
  
  return sources

# ----------------------------------------- END: Source Filtering -----------------------------------------------------


# ----------------------------------------- START: dry_run Helpers ----------------------------------------------------

def get_map_filename(base_name: str, job_id: Optional[str] = None) -> str:
  """
  Get map filename, with job_id suffix for dry_run mode.
  
  Examples:
    get_map_filename("sharepoint_map.csv", None) -> "sharepoint_map.csv"
    get_map_filename("sharepoint_map.csv", "jb_123") -> "sharepoint_map_jb_123.csv"
  """
  if not job_id: return base_name
  name, ext = os.path.splitext(base_name)
  return f"{name}_{job_id}{ext}"

def cleanup_temp_map_files(source_folder: str, job_id: str) -> None:
  """Delete temp map files after dry_run completes. Called in finally block."""
  if not job_id: return
  import glob
  pattern = os.path.join(source_folder, f"*_{job_id}.csv")
  for filepath in glob.glob(pattern):
    try:
      os.remove(filepath)
    except Exception:
      pass

# ----------------------------------------- END: dry_run Helpers ------------------------------------------------------


# ----------------------------------------- START: File Type Filtering ------------------------------------------------

def is_file_embeddable(filename: str) -> bool:
  """
  Check if file type is accepted by vector stores.
  Uses CRAWLER_HARDCODED_CONFIG.DEFAULT_FILETYPES_ACCEPTED_BY_VECTOR_STORES.
  """
  if not filename: return False
  ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
  return ext in CRAWLER_HARDCODED_CONFIG.DEFAULT_FILETYPES_ACCEPTED_BY_VECTOR_STORES

def filter_embeddable_files(files: list) -> tuple:
  """
  Split files into embeddable and non-embeddable.
  Returns: (embeddable, skipped)
  Files must have 'filename' attribute.
  """
  embeddable = []
  skipped = []
  for f in files:
    fname = getattr(f, 'filename', None) or f.get('filename', '') if isinstance(f, dict) else None
    if fname and is_file_embeddable(fname):
      embeddable.append(f)
    else:
      skipped.append(f)
  return embeddable, skipped

# ----------------------------------------- END: File Type Filtering --------------------------------------------------
