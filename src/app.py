import ctypes, glob, inspect, logging, os, platform, shutil, tempfile
from dataclasses import dataclass
from typing import Optional

from azure.identity.aio import ClientSecretCredential, DefaultAzureCredential
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

from common_openai_functions import create_async_azure_openai_client_with_api_key, create_async_azure_openai_client_with_credential, create_async_openai_client
from hardcoded_config import CRAWLER_HARDCODED_CONFIG
from routers_v1 import crawler, inventory, domains, testrouter, testrouter2, testrouter3
from routers_static import openai_proxy, sharepoint_search
from routers_static.sharepoint_search import build_domains_and_metadata_cache
from utils import ZipExtractionMode, acquire_startup_lock, convert_to_flat_html_table, extract_zip_files, format_config_for_displaying, format_filesize, clear_folder
from logging_v1 import log_function_footer, log_function_header, log_function_output, log_function_footer_sync

# Load environment variables from a local .env file if present
load_dotenv()

# Global initialization errors array
initialization_errors = []

@dataclass
class SystemInfo:
  TOTAL_MEMORY_BYTES: int
  FREE_MEMORY_BYTES: int
  NUMBER_OF_CORES: int
  ENVIRONMENT: str
  OS_PLATFORM: str
  PERSISTENT_STORAGE_PATH: str
  PERSISTENT_STORAGE_FREE_SPACE_BYTES: int | str
  PERSISTENT_STORAGE_TOTAL_SPACE_BYTES: int | str
  APP_SRC_PATH: str

@dataclass
class Config:
  OPENAI_SERVICE_TYPE: str
  AZURE_OPENAI_USE_KEY_AUTHENTICATION: Optional[bool]
  AZURE_OPENAI_USE_MANAGED_IDENTITY: Optional[bool]
  AZURE_OPENAI_ENDPOINT: Optional[str]
  AZURE_OPENAI_API_KEY: Optional[str]
  AZURE_OPENAI_API_VERSION: str
  AZURE_OPENAI_DEFAULT_MODEL_DEPLOYMENT_NAME: Optional[str]
  AZURE_TENANT_ID: Optional[str]
  AZURE_CLIENT_ID: Optional[str]
  AZURE_CLIENT_SECRET: Optional[str]
  AZURE_CLIENT_NAME: Optional[str]
  AZURE_MANAGED_IDENTITY_CLIENT_ID: Optional[str]
  OPENAI_API_KEY: Optional[str]
  OPENAI_ORGANIZATION: Optional[str]
  OPENAI_DEFAULT_MODEL_NAME: Optional[str]
  LOCAL_PERSISTENT_STORAGE_PATH: Optional[str]
  # SharePoint Search Configuration
  SEARCH_DEFAULT_GLOBAL_VECTOR_STORE_ID: Optional[str]
  SEARCH_DEFAULT_MAX_NUM_RESULTS: int
  SEARCH_DEFAULT_TEMPERATURE: float
  SEARCH_DEFAULT_INSTRUCTIONS: str
  SEARCH_DEFAULT_SHAREPOINT_ROOT_URL: str
  LOG_QUERIES_AND_RESPONSES: bool
  # Crawler Configuration
  CRAWLER_CLIENT_ID: Optional[str]
  CRAWLER_CLIENT_CERTIFICATE_PFX_FILE: Optional[str]
  CRAWLER_CLIENT_CERTIFICATE_PASSWORD: Optional[str]
  CRAWLER_CLIENT_NAME: Optional[str]
  CRAWLER_TENANT_ID: Optional[str]


def load_config() -> Config:
  """Load configuration from environment variables."""
  
  return Config(
    OPENAI_SERVICE_TYPE=os.getenv("OPENAI_SERVICE_TYPE", "azure_openai")
    ,AZURE_OPENAI_USE_KEY_AUTHENTICATION=os.getenv("AZURE_OPENAI_USE_KEY_AUTHENTICATION", "true").lower() == "true"
    ,AZURE_OPENAI_USE_MANAGED_IDENTITY=os.getenv("AZURE_OPENAI_USE_MANAGED_IDENTITY", "false").lower() == "true"
    ,AZURE_OPENAI_ENDPOINT=os.getenv("AZURE_OPENAI_ENDPOINT")
    ,AZURE_OPENAI_API_KEY=os.getenv("AZURE_OPENAI_API_KEY")
    ,AZURE_OPENAI_API_VERSION=os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
    ,AZURE_OPENAI_DEFAULT_MODEL_DEPLOYMENT_NAME=os.getenv("AZURE_OPENAI_DEFAULT_MODEL_DEPLOYMENT_NAME")
    ,AZURE_TENANT_ID=os.getenv("AZURE_TENANT_ID")
    ,AZURE_CLIENT_ID=os.getenv("AZURE_CLIENT_ID")
    ,AZURE_CLIENT_SECRET=os.getenv("AZURE_CLIENT_SECRET")
    ,AZURE_CLIENT_NAME=os.getenv("AZURE_CLIENT_NAME")
    ,AZURE_MANAGED_IDENTITY_CLIENT_ID=os.getenv("AZURE_MANAGED_IDENTITY_CLIENT_ID")
    ,OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
    ,OPENAI_ORGANIZATION=os.getenv("OPENAI_ORGANIZATION")
    ,OPENAI_DEFAULT_MODEL_NAME=os.getenv("OPENAI_DEFAULT_MODEL_NAME", "gpt-4o-mini")
    ,LOCAL_PERSISTENT_STORAGE_PATH=os.getenv('LOCAL_PERSISTENT_STORAGE_PATH')
    # SharePoint Search Configuration
    ,SEARCH_DEFAULT_GLOBAL_VECTOR_STORE_ID=os.getenv('SEARCH_DEFAULT_GLOBAL_VECTOR_STORE_ID')
    ,SEARCH_DEFAULT_MAX_NUM_RESULTS=int(os.getenv('SEARCH_DEFAULT_MAX_NUM_RESULTS', '20'))
    ,SEARCH_DEFAULT_TEMPERATURE=float(os.getenv('SEARCH_DEFAULT_TEMPERATURE', '0.0'))
    ,SEARCH_DEFAULT_INSTRUCTIONS=os.getenv('SEARCH_DEFAULT_INSTRUCTIONS', 'If the query can\'t be answered based on the available information, return N/A.')
    ,SEARCH_DEFAULT_SHAREPOINT_ROOT_URL=os.getenv('SEARCH_DEFAULT_SHAREPOINT_ROOT_URL', '')
    ,LOG_QUERIES_AND_RESPONSES=os.getenv("LOG_QUERIES_AND_RESPONSES", "false").lower() == "true"
    # Crawler Configuration
    ,CRAWLER_CLIENT_ID=os.getenv('CRAWLER_CLIENT_ID')
    ,CRAWLER_CLIENT_CERTIFICATE_PFX_FILE=os.getenv('CRAWLER_CLIENT_CERTIFICATE_PFX_FILE')
    ,CRAWLER_CLIENT_CERTIFICATE_PASSWORD=os.getenv('CRAWLER_CLIENT_CERTIFICATE_PASSWORD')
    ,CRAWLER_CLIENT_NAME=os.getenv('CRAWLER_CLIENT_NAME')
    ,CRAWLER_TENANT_ID=os.getenv('CRAWLER_TENANT_ID')
  )

def configure_logging():
  """Configure logging to suppress verbose Azure SDK and HTTP logs."""
  logging.getLogger('azure').setLevel(logging.WARNING)
  logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
  logging.getLogger('azure.identity').setLevel(logging.WARNING)
  logging.getLogger('azure.identity._credentials').setLevel(logging.WARNING)
  logging.getLogger('azure.identity._internal').setLevel(logging.WARNING)
  logging.getLogger('msal').setLevel(logging.WARNING)
  logging.getLogger('urllib3').setLevel(logging.WARNING)
  logging.getLogger('requests').setLevel(logging.WARNING)
  logging.getLogger('httpx').setLevel(logging.WARNING)
  # Suppress OpenAI SDK retry and HTTP logs
  logging.getLogger('openai').setLevel(logging.WARNING)
  logging.getLogger('openai._base_client').setLevel(logging.WARNING)
  logging.getLogger('httpcore').setLevel(logging.WARNING)


def is_running_on_azure_app_service() -> bool:
  """Detect if the application is running on Azure App Service."""
  return os.path.exists("/home/site/wwwroot") or os.path.exists("/opt/startup") or os.path.exists("/home/site")

def test_directory_writable(directory_path: str) -> bool:
  """Test if a directory is writable by creating a temporary file."""
  if not os.path.exists(directory_path):
    return False
  
  try:
    # Create a temporary file in the directory
    with tempfile.NamedTemporaryFile(dir=directory_path, delete=False) as temp_file:
      temp_file.write(b"test")
      temp_file_path = temp_file.name
    
    # Clean up the temporary file
    os.unlink(temp_file_path)
    return True
  except (OSError, PermissionError, IOError):
    return False

def verify_system_info(system_info: SystemInfo) -> list[dict]:
  """
  Verify system information and create a list with verification results.
  
  Args:
    system_info: SystemInfo dataclass instance
    
  Returns:
    List of dicts with Field, Value, and Display Value / Verification
  """
  system_info_list = []
  for field in system_info.__dataclass_fields__:
    value = getattr(system_info, field)
    key = field
    # Create verification column
    verification = ""
    if (key.endswith('MEMORY_BYTES') or key.endswith('SPACE_BYTES')) and isinstance(value, int):
      verification = format_filesize(value)
    elif key.endswith('PATH') and isinstance(value, str) and value != "N/A":
      exists = os.path.exists(value)
      writable = test_directory_writable(value) if exists else False
      if exists and writable: verification = "✅ Exists, ✅ Writable"
      elif exists: verification = "✅ Exists, ❌ Not writable"
      else: verification = "❌ Not found"
    
    system_info_list.append({"Field": key, "Value": value, "Display Value / Verification": verification})
  
  return system_info_list

def verify_config(config: Config, system_info: SystemInfo) -> list[dict]:
  """
  Verify configuration and create a list with verification results.
  
  Args:
    config: Config dataclass instance
    system_info: SystemInfo dataclass instance (for PERSISTENT_STORAGE_PATH)
    
  Returns:
    List of dicts with Field, Value, and Display Value / Verification
  """
  config_list = []
  formatted_config = format_config_for_displaying(config)
  
  for field, value in formatted_config.items():
    verification = ""
    
    # Verify CRAWLER_CLIENT_CERTIFICATE_PFX_FILE exists in PERSISTENT_STORAGE_PATH
    if field == "CRAWLER_CLIENT_CERTIFICATE_PFX_FILE" and value and not value.startswith("⚠️"):
      # Extract the actual filename from the formatted value (remove "✅ " prefix)
      filename = value.replace("✅ ", "").strip()
      cert_path = os.path.join(system_info.PERSISTENT_STORAGE_PATH, filename)
      if os.path.exists(cert_path): verification = f"✅ Found"
      else: verification = f"❌ Not found"
    
    # Verify AZURE_OPENAI_ENDPOINT - check if OpenAI client was created successfully
    elif field == "AZURE_OPENAI_ENDPOINT" and value and not value.startswith("⚠️"):
      try:
        openai_client = app.state.openai_client
        if openai_client is not None: verification = "✅ Client created successfully"
        else: verification = "❌ Client creation failed"
      except AttributeError:
        verification = "⚠️ App state not available"
    
    config_list.append({"Field": field, "Value": value, "Display Value / Verification": verification})
  
  return config_list

def create_system_info() -> SystemInfo:
  """Create system information."""
  retVal = SystemInfo(
    TOTAL_MEMORY_BYTES=-1,
    FREE_MEMORY_BYTES=-1,
    NUMBER_OF_CORES=-1,
    ENVIRONMENT="N/A",
    OS_PLATFORM="N/A",
    PERSISTENT_STORAGE_PATH="",
    PERSISTENT_STORAGE_FREE_SPACE_BYTES="N/A",
    PERSISTENT_STORAGE_TOTAL_SPACE_BYTES="N/A",
    APP_SRC_PATH=os.path.dirname(os.path.abspath(__file__))
  )

  # Get number of CPU cores
  try: retVal.NUMBER_OF_CORES = os.cpu_count() or -1 if platform.system() == "Windows" else os.sysconf('SC_NPROCESSORS_ONLN')
  except: pass
  
  # Get memory information
  try:
    if platform.system() == "Windows":
      class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
          ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
          ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)
        ]
      stat = MEMORYSTATUSEX(); stat.dwLength = ctypes.sizeof(stat); ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
      retVal.TOTAL_MEMORY_BYTES = stat.ullTotalPhys; retVal.FREE_MEMORY_BYTES = stat.ullAvailPhys
    else:
      pagesize = os.sysconf("SC_PAGE_SIZE"); total_pages = os.sysconf("SC_PHYS_PAGES"); avail_pages = os.sysconf("SC_AVPHYS_PAGES")
      retVal.TOTAL_MEMORY_BYTES = pagesize * total_pages; retVal.FREE_MEMORY_BYTES = pagesize * avail_pages
  except: pass

  # Determine environment
  try: is_azure_environment = is_running_on_azure_app_service(); retVal.ENVIRONMENT = "Azure" if is_azure_environment else "Local"
  except: pass

  # Determine OS platform
  try: retVal.OS_PLATFORM = "Windows" if platform.system() == "Windows" else "Linux"
  except: pass

  # Set persistent storage path
  try: 
    if is_azure_environment:
      retVal.PERSISTENT_STORAGE_PATH = os.path.join(os.getenv("HOME", r"d:\home"), "data") if platform.system() == "Windows" else "/home/data"
    else:
      retVal.PERSISTENT_STORAGE_PATH = os.getenv('LOCAL_PERSISTENT_STORAGE_PATH') or ""
  except: pass

  # Create persistent storage directory if it doesn't exist
  try: os.makedirs(retVal.PERSISTENT_STORAGE_PATH, exist_ok=True)
  except: pass

  # Get disk space for persistent storage path
  try:
    if retVal.PERSISTENT_STORAGE_PATH and os.path.exists(retVal.PERSISTENT_STORAGE_PATH):
      disk_usage = shutil.disk_usage(retVal.PERSISTENT_STORAGE_PATH); retVal.PERSISTENT_STORAGE_FREE_SPACE_BYTES = disk_usage.free; retVal.PERSISTENT_STORAGE_TOTAL_SPACE_BYTES = disk_usage.total
    else:
      check_path = os.getcwd() if os.path.exists(os.getcwd()) else os.path.expanduser("~"); disk_usage = shutil.disk_usage(check_path)
      retVal.PERSISTENT_STORAGE_FREE_SPACE_BYTES = disk_usage.free; retVal.PERSISTENT_STORAGE_TOTAL_SPACE_BYTES = disk_usage.total
  except: retVal.PERSISTENT_STORAGE_FREE_SPACE_BYTES = "N/A"; retVal.PERSISTENT_STORAGE_TOTAL_SPACE_BYTES = "N/A"

  return retVal

def create_app() -> FastAPI:
  """Create and configure the FastAPI application."""
  log_data = log_function_header("create_app")
  # Configure logging first to ensure all initialization logs are properly formatted
  configure_logging()
  log_function_output(log_data, "Logging configured")
  # Load configuration
  config = load_config()
  log_function_output(log_data, "Configuration loaded")
  # Create FastAPI app instance
  app = FastAPI(title="SharePoint-GPT-Middleware")
  # Store config in app state
  app.state.config = config
  # Create system info
  system_info = create_system_info()
  app.state.system_info = system_info
  # Summarize key system info
  try:
    free_str = format_filesize(system_info.PERSISTENT_STORAGE_FREE_SPACE_BYTES) if isinstance(system_info.PERSISTENT_STORAGE_FREE_SPACE_BYTES, int) else str(system_info.PERSISTENT_STORAGE_FREE_SPACE_BYTES)
    total_str = format_filesize(system_info.PERSISTENT_STORAGE_TOTAL_SPACE_BYTES) if isinstance(system_info.PERSISTENT_STORAGE_TOTAL_SPACE_BYTES, int) else str(system_info.PERSISTENT_STORAGE_TOTAL_SPACE_BYTES)
    log_function_output(
      log_data,
      f"System info: ENVIRONMENT={system_info.ENVIRONMENT}, PERSISTENT_STORAGE_PATH='{system_info.PERSISTENT_STORAGE_PATH or 'N/A'}', DISK_FREE={free_str}, DISK_TOTAL={total_str}"
    )
  except Exception:
    pass

  # Validate paths before zip extraction
  if not system_info.APP_SRC_PATH or system_info.APP_SRC_PATH == "N/A":
    initialization_errors.append({"component": "Zip Extraction", "error": "APP_SRC_PATH not configured"})
  elif not os.path.exists(system_info.APP_SRC_PATH):
    initialization_errors.append({"component": "Zip Extraction", "error": f"APP_SRC_PATH not found: {system_info.APP_SRC_PATH}"})
  elif not system_info.PERSISTENT_STORAGE_PATH:
    initialization_errors.append({"component": "Zip Extraction", "error": "PERSISTENT_STORAGE_PATH not configured. Set LOCAL_PERSISTENT_STORAGE_PATH environment variable."})
  elif not os.path.exists(system_info.PERSISTENT_STORAGE_PATH):
    initialization_errors.append({"component": "Zip Extraction", "error": f"PERSISTENT_STORAGE_PATH not found: {system_info.PERSISTENT_STORAGE_PATH}"})
  else:
    # Use lock to ensure only first worker extracts zip files
    with acquire_startup_lock("zip_extraction", log_data, timeout_seconds=60) as should_proceed:
      if should_proceed:
        log_function_output(log_data, "This worker will extract zip files")
        
        # Get all zip files from all folders first
        clear_before_source_folder = os.path.join(system_info.APP_SRC_PATH, CRAWLER_HARDCODED_CONFIG.UNZIP_TO_PERSISTENT_STORAGE_CLEAR_BEFORE)
        clear_before_zips = glob.glob(os.path.join(clear_before_source_folder, "*.zip"))
        
        overwrite_source_folder = os.path.join(system_info.APP_SRC_PATH, CRAWLER_HARDCODED_CONFIG.UNZIP_TO_PERSISTENT_STORAGE_OVERWRITE)
        overwrite_zips = glob.glob(os.path.join(overwrite_source_folder, "*.zip"))
        
        if_newer_source_folder = os.path.join(system_info.APP_SRC_PATH, CRAWLER_HARDCODED_CONFIG.UNZIP_TO_PERSISTENT_STORAGE_IF_NEWER)
        if_newer_zips = glob.glob(os.path.join(if_newer_source_folder, "*.zip"))
        
        # If no zip files were found in any folder, delete the .done and .lock files so we check again on next startup
        total_zips = len(clear_before_zips) + len(overwrite_zips) + len(if_newer_zips)
        if total_zips == 0:
          done_file_path = os.path.join(tempfile.gettempdir(), "zip_extraction.done")
          lock_file_path = os.path.join(tempfile.gettempdir(), "zip_extraction.lock")
          
          if os.path.exists(done_file_path):
            try:
              os.unlink(done_file_path)
              log_function_output(log_data, f"No zip files found, deleted done file '{done_file_path}' to allow checking again on next startup")
            except Exception as e:
              log_function_output(log_data, f"WARNING: Failed to delete done file '{done_file_path}': {e}")
          
          if os.path.exists(lock_file_path):
            try:
              os.unlink(lock_file_path)
              log_function_output(log_data, f"No zip files found, deleted lock file '{lock_file_path}' to allow checking again on next startup")
            except Exception as e:
              log_function_output(log_data, f"WARNING: Failed to delete lock file '{lock_file_path}': {e}")
        
        # Process clear before folder
        log_function_output(log_data, f"Found {len(clear_before_zips)} zip file(s) in clear-before folder '{clear_before_source_folder}'")
        if len(clear_before_zips) > 0:
          # Safety check: Do not clear if LOCAL_PERSISTENT_STORAGE_PATH equals PERSISTENT_STORAGE_PATH
          if (config.LOCAL_PERSISTENT_STORAGE_PATH and os.path.normpath(config.LOCAL_PERSISTENT_STORAGE_PATH) == os.path.normpath(system_info.PERSISTENT_STORAGE_PATH)):
            log_function_output(log_data, f"SAFETY CHECK: Skipping folder clearing because LOCAL_PERSISTENT_STORAGE_PATH equals PERSISTENT_STORAGE_PATH")
            log_function_output(log_data, f"SAFETY CHECK: Would have cleared contents of folder: {system_info.PERSISTENT_STORAGE_PATH}")
            log_function_output(log_data, f"SAFETY CHECK: Would have extracted {len(clear_before_zips)} file(s) from clear-before folder.")
          else:
            clear_folder(system_info.PERSISTENT_STORAGE_PATH, True, log_data)
            extracted_files = extract_zip_files(clear_before_source_folder, system_info.PERSISTENT_STORAGE_PATH, ZipExtractionMode.OVERWRITE, initialization_errors)
            if extracted_files:
              log_function_output(log_data, f"Extracted {len(extracted_files)} file(s) from clear-before folder:")
              for file_path in extracted_files:
                log_function_output(log_data, f"  '{file_path}'")

        # Process overwrite folder
        log_function_output(log_data, f"Found {len(overwrite_zips)} zip file(s) in overwrite folder '{overwrite_source_folder}'")
        if len(overwrite_zips) > 0:
          extracted_files = extract_zip_files(overwrite_source_folder, system_info.PERSISTENT_STORAGE_PATH, ZipExtractionMode.OVERWRITE, initialization_errors)
          if extracted_files:
            log_function_output(log_data, f"Extracted {len(extracted_files)} file(s) from overwrite folder:")
            for file_path in extracted_files:
              log_function_output(log_data, f"  '{file_path}'")

        # Process if-newer folder
        log_function_output(log_data, f"Found {len(if_newer_zips)} zip file(s) in if-newer folder '{if_newer_source_folder}'")
        if len(if_newer_zips) > 0:
          extracted_files = extract_zip_files(if_newer_source_folder, system_info.PERSISTENT_STORAGE_PATH, ZipExtractionMode.OVERWRITE_IF_NEWER, initialization_errors)
          if extracted_files:
            log_function_output(log_data, f"Extracted {len(extracted_files)} file(s) from if-newer folder:")
            for file_path in extracted_files:
              log_function_output(log_data, f"  '{file_path}'")
      else:
        log_function_output(log_data, "Zip extraction already completed by another worker, skipping")
    
  # Build domains and metadata cache
  domains_cache, metadata_cache = build_domains_and_metadata_cache(config, system_info, initialization_errors)
  app.state.domains = domains_cache
  app.state.metadata_cache = metadata_cache
  try:
    domains_count = len(domains_cache) if hasattr(domains_cache, "__len__") else "unknown"
    metadata_count = len(metadata_cache) if hasattr(metadata_cache, "__len__") else "unknown"
    log_function_output(log_data, f"Domains and metadata cache built. Domains={domains_count}, MetadataEntries={metadata_count}")
  except Exception:
    pass
  
  # Add CORS middleware to handle preflight OPTIONS requests
  app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
  log_function_output(log_data, "CORS middleware added")
  
  # Create the appropriate OpenAI client based on configuration
  openai_client = None
  try:
    if config.OPENAI_SERVICE_TYPE.lower() == "azure_openai":
      if config.AZURE_OPENAI_USE_KEY_AUTHENTICATION:
        # 1) Use Azure key authentication
        openai_client = create_async_azure_openai_client_with_api_key(config.AZURE_OPENAI_ENDPOINT, config.AZURE_OPENAI_API_VERSION, config.AZURE_OPENAI_API_KEY)
      elif config.AZURE_OPENAI_USE_MANAGED_IDENTITY and config.AZURE_MANAGED_IDENTITY_CLIENT_ID:
        # 2) Use managed identity if configured
        credential = DefaultAzureCredential(managed_identity_client_id=config.AZURE_MANAGED_IDENTITY_CLIENT_ID)
        openai_client = create_async_azure_openai_client_with_credential(config.AZURE_OPENAI_ENDPOINT, config.AZURE_OPENAI_API_VERSION, credential)
      elif config.AZURE_TENANT_ID and config.AZURE_CLIENT_ID and config.AZURE_CLIENT_SECRET:
        # 3) Use service principal if configured
        credential = ClientSecretCredential(tenant_id=config.AZURE_TENANT_ID, client_id=config.AZURE_CLIENT_ID, client_secret=config.AZURE_CLIENT_SECRET)
        openai_client = create_async_azure_openai_client_with_credential(config.AZURE_OPENAI_ENDPOINT, config.AZURE_OPENAI_API_VERSION, credential)
      else:
        # 4) Use default credential as fallback
        credential = DefaultAzureCredential()
        openai_client = create_async_azure_openai_client_with_credential(config.AZURE_OPENAI_ENDPOINT, config.AZURE_OPENAI_API_VERSION, credential)
    else:
      openai_client = create_async_openai_client(config.OPENAI_API_KEY)
  except Exception as e:
    initialization_errors.append({"component": "OpenAI Client Creation", "error": str(e)})
  app.state.openai_client = openai_client
  try:
    svc = (config.OPENAI_SERVICE_TYPE or "").lower()
    log_function_output(log_data, f"OpenAI client created (service='{svc}', available={bool(openai_client)})")
  except Exception:
    pass

  # Include OpenAI proxy router under /openai
  try:
    app.include_router(openai_proxy.router, tags=["OpenAI Proxy"], prefix="/openai")
    openai_proxy.set_config(config)
    log_function_output(log_data, "OpenAI proxy router included at /openai")
  except Exception as e:
    initialization_errors.append({"component": "OpenAI Proxy Router", "error": str(e)})
  
  # Include SharePoint Search router at root /
  try:
    app.include_router(sharepoint_search.router, tags=["SharePoint Search"])
    sharepoint_search.set_config(config)
    log_function_output(log_data, "SharePoint Search router included at /")
  except Exception as e:
    initialization_errors.append({"component": "SharePoint Search Router", "error": str(e)})
  
  # Include V1 routers
  v1_router_prefix = "/v1"
  
  # Include Inventory router
  try:
    app.include_router(inventory.router, tags=["Inventory"], prefix=v1_router_prefix)
    inventory.set_config(config, v1_router_prefix)
    log_function_output(log_data, f"Inventory router included at {v1_router_prefix}")
  except Exception as e:
    initialization_errors.append({"component": "Inventory Router", "error": str(e)})
  
  # Include Crawler router under /v1
  try:
    app.include_router(crawler.router, tags=["Crawler"], prefix=v1_router_prefix)
    crawler.set_config(config, v1_router_prefix)
    log_function_output(log_data, f"Crawler router included at {v1_router_prefix}")
  except Exception as e:
    initialization_errors.append({"component": "Crawler Router", "error": str(e)})
  
  # Include Domains router under /v1
  try:
    app.include_router(domains.router, tags=["Domains"], prefix=v1_router_prefix)
    domains.set_config(config, v1_router_prefix)
    log_function_output(log_data, f"Domains router included at {v1_router_prefix}")
  except Exception as e:
    initialization_errors.append({"component": "Domains Router", "error": str(e)})
  
  # Include Test router under /testrouter
  try:
    app.include_router(testrouter.router, tags=["Test"], prefix=v1_router_prefix)
    testrouter.set_config(config, v1_router_prefix)
    log_function_output(log_data, f"Test router included at {v1_router_prefix}")
  except Exception as e:
    initialization_errors.append({"component": "Test Router", "error": str(e)})
  
  # Include Test router V1B under /testrouter2
  try:
    app.include_router(testrouter2.router, tags=["Test V1B"], prefix=v1_router_prefix)
    testrouter2.set_config(config, v1_router_prefix)
    log_function_output(log_data, f"Test router V2 included at {v1_router_prefix}")
  except Exception as e:
    initialization_errors.append({"component": "Test Router 2", "error": str(e)})
  
  # Include Test router V1C under /testrouter3
  try:
    app.include_router(testrouter3.router, tags=["Test V1C"], prefix=v1_router_prefix)
    testrouter3.set_config(config, v1_router_prefix)
    log_function_output(log_data, f"Test router V3 included at {v1_router_prefix}")
  except Exception as e:
    initialization_errors.append({"component": "Test Router 3", "error": str(e)})

  # Mount static files directory
  static_path = os.path.join(os.path.dirname(__file__), "static")
  if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")
    log_function_output(log_data, f"Static files mounted from '{static_path}' at /static")
  else:
    initialization_errors.append({"component": "Static Files", "error": f"Static directory not found: {static_path}"})
    log_function_output(log_data, f"Static directory not found: {static_path}")
    
  # Final summary - log any initialization errors
  try:
    if initialization_errors:
      log_function_output(log_data, f"App initialization completed with {len(initialization_errors)} initialization error(s):")
      for error in initialization_errors:
        log_function_output(log_data, f"  - {error['component']}: {error['error']}")
    else:
      log_function_output(log_data, "App initialization completed successfully with no errors")
  except Exception: pass
  log_function_footer_sync(log_data)
  return app

# Initialize the FastAPI application
app = create_app()

@app.get("/alive", response_class=PlainTextResponse)
async def health():
  """Health check endpoint for monitoring."""
  return PlainTextResponse(content="alive", status_code=200)

@app.get("/favicon.ico")
async def favicon(): return Response(status_code=204)

# Ensure the default document is not served
@app.get('/hostingstart.html', response_class=PlainTextResponse)
async def ignore_default_doc():
  log_data = log_function_header(inspect.currentframe().f_code.co_name)
  retVal = root()
  await log_function_footer(log_data)
  return retVal


@app.get("/", response_class=HTMLResponse)
def root() -> str:
  errors_html = f'<div class="section"><h4>Errors</h4>{convert_to_flat_html_table(initialization_errors)}</div>' if initialization_errors else ""
  system_info = app.state.system_info
  
  # Use verification functions
  system_info_list = verify_system_info(system_info)
  config_list = verify_config(app.state.config, system_info)
  
  return f"""
<!doctype html><html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SharePoint-GPT-Middleware</title>
  <link rel="stylesheet" href="/static/css/styles.css">
  <script src="/static/js/htmx.js"></script>
</head>
<body>
  <h1>SharePoint-GPT-Middleware</h1>
  <p>This middleware provides OpenAI proxy endpoints, SharePoint search functionality, and inventory management for vector stores.</p>
  
  <div class="toolbar">
    <a href="/v1/domains?format=ui" class="btn-primary"> Domains </a>
    <a href="/v1/crawler/?format=ui" class="btn-primary">  Crawler </a>
    <a href="/v1/inventory/vectorstores?format=ui" class="btn-primary"> Vector Stores </a>
    <a href="/v1/inventory/files?format=ui" class="btn-primary"> Files </a>
    <a href="/v1/inventory/assistants?format=ui" class="btn-primary"> Assistants </a>
  </div>

  <h4>Available Links</h4>
  <ul>
    <li><a href="/docs">/docs</a> - API Documentation</li>
    <li><a href="/openapi.json">/openapi.json</a> - OpenAPI JSON</li>
    <li><a href="/openaiproxyselftest">/openaiproxyselftest</a> - Self Test (will take a while)</li>
    <li><a href="/describe">/describe</a> - SharePoint Search Description</li>
    <li><a href="/describe2">/describe2</a> - SharePoint Search Description (<a href="/describe2?format=html">HTML</a> + <a href="/describe2?format=json">JSON</a>)</li>
    <li><a href="/query">/query</a> - SharePoint Search Query (JSON)</li>
    <li><a href="/query2">/query2</a> - SharePoint Search Query (<a href="/query2?query=List+all+documents&results=50">HTML</a> +  JSON)</li>
    <p>Version 1 Routers</p>
    <li><a href="/v1/inventory">/v1/inventory</a> - Inventory Endpoints (Vector Stores, Files, Assistants)</li>
    <li><a href="/v1/inventory/vectorstores">/v1/inventory/vectorstores</a> - Vector Stores Inventory (<a href="/v1/inventory/vectorstores?format=html&excludeattributes=metadata">HTML</a> + <a href="/v1/inventory/vectorstores?format=json">JSON</a> + <a href="/v1/inventory/vectorstores?format=ui">UI</a>)</li>
    <li><a href="/v1/inventory/files">/v1/inventory/files</a> - Files Inventory (<a href="/v1/inventory/files?format=html&excludeattributes=purpose,status_details">HTML</a> + <a href="/v1/inventory/files?format=json">JSON</a>)</li>
    <li><a href="/v1/inventory/assistants">/v1/inventory/assistants</a> - Assistants Inventory (<a href="/v1/inventory/assistants?format=html&excludeattributes=description,instructions,tools,tool_resources">HTML</a> + <a href="/v1/inventory/assistants?format=json">JSON</a>)</li>
    <li><a href="/v1/domains">/v1/domains</a> - Domains Management (<a href="/v1/domains?format=html">HTML</a> + <a href="/v1/domains?format=json">JSON</a> + <a href="/v1/domains?format=ui">UI</a> + <a href="/v1/domains/create">Create</a> + <a href="/v1/domains/update">Update</a> + <a href="/v1/domains/delete">Delete</a>)</li>
    <li><a href="/v1/crawler">/v1/crawler</a> - Crawler Endpoints (<a href="/v1/crawler/localstorage">Local Storage</a> + <a href="/v1/crawler/updatemaps">Update Maps</a> + <a href="/v1/crawler/getlogfile">Get Logfile</a>)</li>
    <li><a href="/v1/testrouter/streaming01">/v1/testrouter/streaming01</a> - V1 Streaming Test (<a href="/v1/testrouter/streaming01?format=stream">Stream</a>)</li>
    <li><a href="/v1/testrouter2/streaming01">/v1/testrouter2/streaming01</a> - V2 Streaming Test (<a href="/v1/testrouter2/streaming01?format=stream">Stream</a> + <a href="/v1/testrouter2/jobs?format=html">Jobs</a>)</li>
    <li><a href="/v1/testrouter3/jobs">/v1/testrouter3/jobs</a> - V3 Streaming Test with UI (<a href="/v1/testrouter3/streaming01?format=stream">Stream</a> + <a href="/v1/testrouter3/jobs?format=ui">Jobs UI</a>)</li>
  </ul>

  <div class="section">
    <h4>Configuration</h4>
    {convert_to_flat_html_table(config_list)}
  </div>

  <div class="section">
    <h4>System Information</h4>
    {convert_to_flat_html_table(system_info_list)}
  </div>

  {errors_html}
</body>
</html>
"""

# Self-test endpoint (not under /openai)
@app.get("/openaiproxyselftest", response_class=HTMLResponse)
async def openai_proxy_self_test(request: Request):
  log_data = log_function_header("openai_proxy_self_test")
  try:
    retVal = await openai_proxy.self_test(request)
    return retVal
  finally:
    await log_function_footer(log_data)