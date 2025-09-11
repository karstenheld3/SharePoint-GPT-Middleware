import ctypes, inspect, logging, os, platform
from dataclasses import dataclass
from typing import Optional

from azure.identity.aio import ClientSecretCredential, DefaultAzureCredential
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, Response

from common_openai_functions import *
from hardcoded_config import *
from routers.sharepoint_search import build_domains_and_metadata_cache
from routers import sharepoint_search, openai_proxy, inventory
from utils import *

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
  """Test if a directory is writable by creating and deleting a temporary file."""
  if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
    return False
  
  import tempfile
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

def create_system_info() -> SystemInfo:
  """Create system information."""
  retVal = SystemInfo(
    TOTAL_MEMORY_BYTES=-1,
    FREE_MEMORY_BYTES=-1,
    NUMBER_OF_CORES=-1,
    ENVIRONMENT="N/A",
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

  # Set persistent storage path
  try: retVal.PERSISTENT_STORAGE_PATH = os.getenv("HOME", "/home") if is_azure_environment else os.getenv('LOCAL_PERSISTENT_STORAGE_PATH') or ""
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
  # Configure logging first to ensure all initialization logs are properly formatted
  configure_logging()
  # Load configuration
  config = load_config()
  # Create FastAPI app instance
  app = FastAPI(title="SharePoint-GPT-Middleware")
  # Store config in app state
  app.state.config = config
  # Create system info
  system_info = create_system_info()
  app.state.system_info = system_info

  # Validate paths before zip extraction
  if not system_info.APP_SRC_PATH or system_info.APP_SRC_PATH == "N/A":
    initialization_errors.append({"component": "Zip Extraction", "error": "Source path not configured"})
  elif not os.path.exists(system_info.APP_SRC_PATH):
    initialization_errors.append({"component": "Zip Extraction", "error": f"Source path not found: {system_info.APP_SRC_PATH}"})
  elif not system_info.PERSISTENT_STORAGE_PATH:
    initialization_errors.append({"component": "Zip Extraction", "error": "Destination path not configured. Set LOCAL_PERSISTENT_STORAGE_PATH environment variable."})
  elif not os.path.exists(system_info.PERSISTENT_STORAGE_PATH):
    initialization_errors.append({"component": "Zip Extraction", "error": f"Destination path not found: {system_info.PERSISTENT_STORAGE_PATH}"})
  else:
    # Process overwrite folder
    overwrite_source_folder = os.path.join(system_info.APP_SRC_PATH, CRAWLER_HARDCODED_CONFIG.UNZIP_TO_PERSISTENT_STORAGE_OVERWRITE)
    extract_zip_files(overwrite_source_folder, system_info.PERSISTENT_STORAGE_PATH, ZipExtractionMode.OVERWRITE, initialization_errors)

    # Process if-newer folder
    if_newer_source_folder = os.path.join(system_info.APP_SRC_PATH, CRAWLER_HARDCODED_CONFIG.UNZIP_TO_PERSISTENT_STORAGE_IF_NEWER)
    extract_zip_files(if_newer_source_folder, system_info.PERSISTENT_STORAGE_PATH, ZipExtractionMode.OVERWRITE_IF_NEWER, initialization_errors)

  # Build domains and metadata cache
  domains, metadata_cache = build_domains_and_metadata_cache(config, system_info, initialization_errors)
  app.state.domains = domains
  app.state.metadata_cache = metadata_cache
  
  # Add CORS middleware to handle preflight OPTIONS requests
  app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
  
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

  # Include OpenAI proxy router under /openai
  try:
    app.include_router(openai_proxy.router, tags=["OpenAI Proxy"], prefix="/openai")
    openai_proxy.set_config(config)
  except Exception as e:
    initialization_errors.append({"component": "OpenAI Proxy Router", "error": str(e)})
  
  # Include SharePoint Search router at root /
  try:
    app.include_router(sharepoint_search.router, tags=["SharePoint Search"])
    sharepoint_search.set_config(config)
  except Exception as e:
    initialization_errors.append({"component": "SharePoint Search Router", "error": str(e)})
  
  # Include Inventory router under /inventory
  try:
    app.include_router(inventory.router, tags=["Inventory Management"], prefix="/inventory")
    inventory.set_config(config)
  except Exception as e:
    initialization_errors.append({"component": "Inventory Router", "error": str(e)})
    
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
  errors_html = f"<h4>Errors</h4>{convert_to_html_table(initialization_errors)}" if initialization_errors else ""
  system_info = app.state.system_info
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
      if exists and writable:
        verification = "✅ Exists, ✅ Writable"
      elif exists:
        verification = "✅ Exists, ❌ Not writable"
      else:
        verification = "❌ Not found"
    
    system_info_list.append({"Field": key, "Value": value, "Verification": verification})
  
  system_info_html = f"<h4>System Information</h4>{convert_to_html_table(system_info_list)}"
  
  return f"""
<!doctype html><html lang="en"><head><meta charset="utf-8"><title>SharePoint-GPT-Middleware</title></head><body>
<font face="Open Sans, Arial, Helvetica, sans-serif">
<h3>SharePoint-GPT-Middleware is running</h3>
<p>This middleware provides OpenAI proxy endpoints, SharePoint search functionality, and inventory management for vector stores.</p>

<h4>Available Links</h4>
<ul>
  <li><a href="/docs">/docs</a> - API Documentation</li>
  <li><a href="/openapi.json">/openapi.json</a> - OpenAPI JSON</li>
  <li><a href="/openaiproxyselftest">/openaiproxyselftest</a> - Self Test (will take a while)</li>
  <li><a href="/describe">/describe</a> - SharePoint Search Description</li>
  <li><a href="/query">/query</a> - SharePoint Search Query (JSON)</li>
  <li><a href="/query2">/query2</a> - SharePoint Search Query (<a href="/query2?query=List+all+documents">HTML</a> +  JSON)</li>
  <li><a href="/inventory/vectorstores">/inventory/vectorstores</a> - Vector Stores Inventory (<a href="/inventory/vectorstores?format=html">HTML</a> + <a href="/inventory/vectorstores?format=json">JSON</a>)</li>
</ul>
<h4>Configuration</h4>
{convert_to_html_table(format_config_for_displaying(app.state.config))}
{system_info_html}
{errors_html}
</font></body></html>
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