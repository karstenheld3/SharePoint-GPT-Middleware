import datetime, json, logging, os, tempfile, zipfile
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, HTTPException, Query, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse

from common_openai_functions import get_all_vector_stores, get_all_files, get_all_assistants, convert_openai_timestamps_to_utc
from hardcoded_config import CRAWLER_HARDCODED_CONFIG
from utils import convert_to_html_table, convert_to_nested_html_table, log_function_footer, log_function_header, log_function_output

router = APIRouter()

# Configuration will be injected from app.py
config = None

logger = logging.getLogger(__name__)

def set_config(app_config):
  """Set the configuration for Inventory management."""
  global config
  config = app_config

def _delete_zip_file(file_path: str, log_data: Dict[str, Any] = None) -> None:
  """Delete the zip file after it has been served."""
  try:
    if os.path.exists(file_path):
      os.remove(file_path)
      if log_data:
        log_function_output(log_data, f"Deleted zip file: {file_path}")
      else:
        logger.info(f"Deleted zip file: {file_path}")
  except Exception as e:
    error_msg = f"Failed to delete zip file {file_path}: {str(e)}"
    if log_data:
      log_function_output(log_data, f"ERROR: {error_msg}")
    else:
      logger.error(error_msg)

def include_exclude_attributes(data: Union[List[Dict], Dict], include_attributes: Optional[str] = None, exclude_attributes: Optional[str] = None) -> Union[List[Dict], Dict]:
  """
  Filter attributes in data objects based on include/exclude parameters.
  
  Args:
    data: Single dict or list of dicts to filter
    include_attributes: Comma-separated list of attributes to include (takes precedence)
    exclude_attributes: Comma-separated list of attributes to exclude (ignored if include_attributes is set)
    
  Returns:
    Filtered data with only specified attributes
  """
  if not include_attributes and not exclude_attributes: return data    
  # Handle single dict
  if isinstance(data, dict): return _filter_single_object(data, include_attributes, exclude_attributes)    
  # Handle list of dicts
  if isinstance(data, list): return [_filter_single_object(item, include_attributes, exclude_attributes) for item in data]
  return data

def _filter_single_object(obj: Dict, include_attributes: Optional[str], exclude_attributes: Optional[str]) -> Dict:
  """
  Filter a single object based on include/exclude attributes. If includes are given, excludes ar ignored.
  """
  if not isinstance(obj, dict): return obj    
  # If include_attributes is specified, only include those attributes
  if include_attributes:
    include_list = [attr.strip() for attr in include_attributes.split(',') if attr.strip()]
    return {key: value for key, value in obj.items() if key in include_list}
  # If exclude_attributes is specified, exclude those attributes
  if exclude_attributes:
    exclude_list = [attr.strip() for attr in exclude_attributes.split(',') if attr.strip()]
    return {key: value for key, value in obj.items() if key not in exclude_list}
  return obj

def _generate_html_response_from_object_list(title: str, count: int, objects: List[Dict]) -> str:
  """
  Generate HTML response with minimal HTMX integration for inventory endpoints.
  
  Args:
    title: Page title (e.g., "Vector Stores", "Files", "Assistants")
    count: Number of items found
    objects: List of dictionary objects to convert to HTML table
    
  Returns:
    Complete HTMX page with table
  """
  table_html = convert_to_html_table(objects)
  return f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
  <title>{title}</title>
  <link rel='stylesheet' href='/static/css/styles.css'>
  <script src='/static/js/htmx.min.js'></script>
</head>
<body>
  <h1>{title} ({count})</h1>
  {table_html}
</body>
</html>"""

def _generate_html_response_from_nested_data(title: str, data: Any) -> str:
  """
  Generate HTML response with nested table for complex data structures.
  
  Args:
    title: Page title
    data: Complex data structure to convert to nested HTML table
    
  Returns:
    Complete HTMX page with nested table
  """
  table_html = convert_to_nested_html_table(data)
  return f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
  <title>{title}</title>
  <link rel='stylesheet' href='/static/css/styles.css'>
  <script src='/static/js/htmx.min.js'></script>
</head>
<body>
  <h1>{title}</h1>
  {table_html}
</body>
</html>"""

def _create_storage_zip_from_scan(storage_path: str, storage_contents: List[Dict[str, Any]], log_data: Dict[str, Any], temp_zip_path: str, temp_zip_name: str) -> str:
  """
  Create a zip file from the scanned directory structure.
  
  Args:
    storage_path: Base path of the storage directory
    storage_contents: Output from _scan_directory_recursive
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
        # Recursively add folder contents
        _add_items_to_zip(zipf, item["contents"], item_path)
  
  with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    _add_items_to_zip(zipf, storage_contents)
  
  zip_size = os.path.getsize(temp_zip_path)
  log_function_output(log_data, f"Zip file created successfully: {temp_zip_path} ({zip_size} bytes)")
  return temp_zip_path

# Recursively scan a directory and return a list of files and folders with their attributes.
def _scan_directory_recursive(path: str, log_data: Dict[str, Any] = None, except_folder: str = None) -> List[Dict[str, Any]]:
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
          sub_items = _scan_directory_recursive(item_path, log_data, except_folder)
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


@router.get('/vectorstores')
async def vectorstores(request: Request):
  """
  Endpoint to retrieve all vector stores from Azure OpenAI.
  
  Parameters:
  - format: The response format (json or html)
  - includeattributes: Comma-separated list of attributes to include in response (takes precedence over excludeattributes)
  - excludeattributes: Comma-separated list of attributes to exclude from response (ignored if includeattributes is set)
    
  Examples:
  /vectorstores
  /vectorstores?format=json
  /vectorstores?format=json&includeattributes=id,name,created_at
  /vectorstores?format=html&excludeattributes=file_counts,metadata
  """
  function_name = 'vectorstores()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params) 
  endpoint = '/' + function_name.replace('()','')  
  endpoint_documentation = vectorstores.__doc__
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  # Display documentation if no params are provided
  if len(request_params) == 0: await log_function_footer(request_data); return HTMLResponse(documentation_HTML)

  format = request_params.get('format', None)
  include_attributes = request_params.get('includeattributes', None)
  exclude_attributes = request_params.get('excludeattributes', None)
  
  try:
    client = request.app.state.openai_client
    vector_stores = await get_all_vector_stores(client)
    # Convert to dict and apply datetime conversion once for both formats
    vector_stores_list = [asdict(vs) for vs in vector_stores]
    convert_openai_timestamps_to_utc({"data": vector_stores_list}, request_data)
    
    # Apply attribute filtering
    vector_stores_list = include_exclude_attributes(vector_stores_list, include_attributes, exclude_attributes)
    
    if format == 'json':
      await log_function_footer(request_data)
      return JSONResponse({"data": vector_stores_list})
    else:
      # HTML format with minimal HTMX
      html_content = _generate_html_response_from_object_list('Vector Stores', len(vector_stores), vector_stores_list)
      await log_function_footer(request_data)
      return HTMLResponse(html_content)
      
  except Exception as e:
    error_message = f"Error retrieving vector stores: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=500)
    else:
      error_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Error</title></head><body><h1>Error</h1><p>{error_message}</p></body></html>"
      return HTMLResponse(error_html, status_code=500)

@router.get('/files')
async def files(request: Request):
  """
  Endpoint to retrieve all files from Azure OpenAI.
  
  Parameters:
  - format: The response format (json or html)
  - includeattributes: Comma-separated list of attributes to include in response (takes precedence over excludeattributes)
  - excludeattributes: Comma-separated list of attributes to exclude from response (ignored if includeattributes is set)
    
  Examples:
  /files
  /files?format=json
  /files?format=json&includeattributes=id,filename,created_at
  /files?format=json&excludeattributes=purpose,status_details
  """
  function_name = 'files()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')  
  endpoint_documentation = files.__doc__
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  # Display documentation if no params are provided
  if len(request_params) == 0: await log_function_footer(request_data); return HTMLResponse(documentation_HTML)

  format = request_params.get('format', None)
  include_attributes = request_params.get('includeattributes', None)
  exclude_attributes = request_params.get('excludeattributes', None)
  
  try:
    client = request.app.state.openai_client
    files_list = await get_all_files(client)
    
    # Convert to dict and apply datetime conversion once for both formats
    files_dict_list = [asdict(file) for file in files_list]
    convert_openai_timestamps_to_utc({"data": files_dict_list}, request_data)
    
    # Apply attribute filtering
    files_dict_list = include_exclude_attributes(files_dict_list, include_attributes, exclude_attributes)
    
    if format == 'json':
      await log_function_footer(request_data)
      return JSONResponse({"data": files_dict_list})
    else:
      # HTML format with minimal HTMX
      html_content = _generate_html_response_from_object_list('Files', len(files_list), files_dict_list)
      await log_function_footer(request_data)
      return HTMLResponse(html_content)
      
  except Exception as e:
    error_message = f"Error retrieving files: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=500)
    else:
      error_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Error</title></head><body><h1>Error</h1><p>{error_message}</p></body></html>"
      return HTMLResponse(error_html, status_code=500)

@router.get('/assistants')
async def assistants(request: Request):
  """
  Endpoint to retrieve all assistants from Azure OpenAI.
  
  Parameters:
  - format: The response format (json or html)
  - includeattributes: Comma-separated list of attributes to include in response (takes precedence over excludeattributes)
  - excludeattributes: Comma-separated list of attributes to exclude from response (ignored if includeattributes is set)
    
  Examples:
  /assistants
  /assistants?format=json
  /assistants?format=json&includeattributes=id,name,model,created_at
  /assistants?format=json&excludeattributes=instructions,description
  """
  function_name = 'assistants()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')  
  endpoint_documentation = assistants.__doc__
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  # Display documentation if no params are provided
  if len(request_params) == 0: await log_function_footer(request_data); return HTMLResponse(documentation_HTML)

  format = request_params.get('format', None)
  include_attributes = request_params.get('includeattributes', None)
  exclude_attributes = request_params.get('excludeattributes', None)
  
  try:
    client = request.app.state.openai_client
    assistants_list = await get_all_assistants(client)
    
    # Convert to dict and apply datetime conversion once for both formats
    assistants_dict_list = [asdict(assistant) for assistant in assistants_list]
    convert_openai_timestamps_to_utc({"data": assistants_dict_list}, request_data)
    
    # Apply attribute filtering
    assistants_dict_list = include_exclude_attributes(assistants_dict_list, include_attributes, exclude_attributes)
    
    if format == 'json':
      await log_function_footer(request_data)
      return JSONResponse({"data": assistants_dict_list})
    else:
      # HTML format with minimal HTMX
      html_content = _generate_html_response_from_object_list('Assistants', len(assistants_list), assistants_dict_list)
      await log_function_footer(request_data)
      return HTMLResponse(html_content)
      
  except Exception as e:
    error_message = f"Error retrieving assistants: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=500)
    else:
      error_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Error</title></head><body><h1>Error</h1><p>{error_message}</p></body></html>"
      return HTMLResponse(error_html, status_code=500)

@router.get('/localstorage')
async def localstorage(request: Request, background_tasks: BackgroundTasks):
  """
  Endpoint to retrieve all files and folders from local persistent storage recursively.
  
  Parameters:
  - format: The response format (json, html, or zip)
  - exceptfolder: Folder name to exclude from processing (optional)
    
  Examples:
  /localstorage
  /localstorage?format=json
  /localstorage?format=html
  /localstorage?format=zip
  /localstorage?format=zip&exceptfolder=crawler
  """
  function_name = 'localstorage()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')  
  endpoint_documentation = localstorage.__doc__
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  # Display documentation if no params are provided
  if len(request_params) == 0: await log_function_footer(request_data); return HTMLResponse(documentation_HTML)

  format = request_params.get('format', 'html')
  except_folder = request_params.get('exceptfolder', None)
  
  try:
    if not hasattr(request.app.state, 'system_info') or not request.app.state.system_info or not request.app.state.system_info.PERSISTENT_STORAGE_PATH:
      error_message = "PERSISTENT_STORAGE_PATH not configured or is empty"
      log_function_output(request_data, f"ERROR: {error_message}")
      await log_function_footer(request_data)
      if format == 'json':
        return JSONResponse({"error": error_message}, status_code=500)
      else:
        error_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Error</title></head><body><h1>Error</h1><p>{error_message}</p></body></html>"
        return HTMLResponse(error_html, status_code=500)
    
    storage_path = request.app.state.system_info.PERSISTENT_STORAGE_PATH
    if except_folder:
      log_function_output(request_data, f"Scanning local storage path (excluding {except_folder}): {storage_path}")
    else:
      log_function_output(request_data, f"Scanning local storage path: {storage_path}")
    
    # Always scan directory structure first (used by all formats)
    storage_contents = _scan_directory_recursive(storage_path, request_data, except_folder)
    total_items = len(storage_contents)
    
    log_function_output(request_data, f"Found {total_items} items in local storage")
    
    if format == 'zip':
      # Create and return zip file from scan results
      timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
      download_filename = f"{CRAWLER_HARDCODED_CONFIG.LOCALSTORAGE_ZIP_FILENAME_PREFIX}{timestamp}.zip"
      temp_zip_path = os.path.join(storage_path, download_filename)
      zip_file_path = _create_storage_zip_from_scan(storage_path, storage_contents, request_data, temp_zip_path, download_filename)
      
      # Schedule cleanup of the zip file after it's served
      background_tasks.add_task(_delete_zip_file, zip_file_path, request_data)
      
      await log_function_footer(request_data)
      return FileResponse( path=zip_file_path, filename=download_filename, media_type='application/zip' )
    elif format == 'json':
      await log_function_footer(request_data)
      return JSONResponse({"data": storage_contents, "path": storage_path, "total_items": total_items})
    else:
      # HTML format with nested table
      title = f"Local Storage Contents - {storage_path}"
      html_content = _generate_html_response_from_nested_data(title, storage_contents)
      await log_function_footer(request_data)
      return HTMLResponse(html_content)
      
  except Exception as e:
    error_message = f"Error retrieving local storage contents: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=500)
    else:
      error_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Error</title></head><body><h1>Error</h1><p>{error_message}</p></body></html>"
      return HTMLResponse(error_html, status_code=500)

