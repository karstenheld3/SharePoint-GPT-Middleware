# endpoints for the sharepoint crawler
import datetime, json, os, tempfile
from typing import Any, Dict, List

from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse

from hardcoded_config import CRAWLER_HARDCODED_CONFIG
from utils import convert_to_flat_html_table, convert_to_nested_html_table, log_function_footer, log_function_header, log_function_output, create_logfile, append_to_logfile
from common_crawler_functions import DomainConfig, load_all_domains, domain_config_to_dict, scan_directory_recursive, create_storage_zip_from_scan

router = APIRouter()

# Configuration will be injected from app.py
config = None

def set_config(app_config):
  """Set the configuration for Crawler management."""
  global config
  config = app_config

def _delete_zip_file(file_path: str, log_data: Dict[str, Any] = None) -> None:
  """Delete the zip file after it has been served."""
  try:
    if os.path.exists(file_path):
      os.remove(file_path)
      if log_data:
        log_function_output(log_data, f"Deleted zip file: {file_path}")
  except Exception as e:
    error_msg = f"Failed to delete zip file {file_path}: {str(e)}"
    if log_data:
      log_function_output(log_data, f"ERROR: {error_msg}")

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
  <script src='/static/js/htmx.js'></script>
</head>
<body>
  <h1>{title}</h1>
  {table_html}
</body>
</html>"""


@router.get('/', response_class=HTMLResponse)
async def crawler_root():
  """
  Crawler endpoints documentation and overview.
  """
  return f"""
<!doctype html><html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Crawler Endpoints</title>
  <link rel="stylesheet" href="/static/css/styles.css">
  <script src="/static/js/htmx.js"></script>
</head>
<body>
  <h1>Crawler Endpoints</h1>
  <p>This section provides endpoints for SharePoint crawler functionality, local storage management, and domain operations.</p>

  <h4>Available Endpoints</h4>
  <ul>
    <li><a href="/crawler/localstorage">/crawler/localstorage</a> - Local Storage Inventory (<a href="/crawler/localstorage?format=html">HTML</a> + <a href="/crawler/localstorage?format=json">JSON</a> + <a href="/crawler/localstorage?format=zip">ZIP</a> + <a href="/crawler/localstorage?format=zip&exceptfolder=crawler">ZIP except 'crawler' folder</a>)</li>
    <li><a href="/crawler/loadsharepointfiles">/crawler/loadsharepointfiles</a> - Load SharePoint Files (<a href="/crawler/loadsharepointfiles?domain_id=HOIT&source_id=source01&format=html">Example HTML</a> + <a href="/crawler/loadsharepointfiles?domain_id=HOIT&source_id=source01&format=json">Example JSON</a>)</li>
    <li><a href="/crawler/updatemaps">/crawler/updatemaps</a> - Update Maps for Domain (<a href="/crawler/updatemaps?domain_id=example&logfile=log.txt">Example</a>)</li>
    <li><a href="/crawler/getlogfile">/crawler/getlogfile</a> - Retrieve Logfile (<a href="/crawler/getlogfile?logfile=log.txt">Example</a>)</li>
  </ul>

  <p><a href="/">← Back to Main Page</a></p>
</body>
</html>
"""

@router.get('/getlogfile')
async def getlogfile(request: Request):
  """
  Endpoint to retrieve a logfile from the logs folder.
  
  Parameters:
  - logfile: The name of the logfile to retrieve
    
  Examples:
  /getlogfile?logfile=log.txt
  """
  function_name = 'getlogfile()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')  
  endpoint_documentation = getlogfile.__doc__
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  # Display documentation if no params are provided
  if len(request_params) == 0: await log_function_footer(request_data); return HTMLResponse(documentation_HTML)

  logfile = request_params.get('logfile', None)
  
  # Validate required parameters
  if not logfile:
    error_message = "ERROR: Missing required parameter 'logfile'"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    return HTMLResponse(content=error_message, status_code=400, media_type='text/plain; charset=utf-8')
  
  # Validate PERSISTENT_STORAGE_PATH is configured
  if not hasattr(request.app.state, 'system_info') or not request.app.state.system_info or not request.app.state.system_info.PERSISTENT_STORAGE_PATH:
    error_message = "ERROR: PERSISTENT_STORAGE_PATH not configured or is empty"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    return HTMLResponse(content=error_message, status_code=500, media_type='text/plain; charset=utf-8')
  
  # Build the logfile path
  storage_path = request.app.state.system_info.PERSISTENT_STORAGE_PATH
  logs_folder = os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_LOGS_SUBFOLDER)
  logfile_path = os.path.join(logs_folder, logfile)
  
  # Check if logfile exists
  if not os.path.exists(logfile_path):
    error_message = f"ERROR: Logfile not found: {logfile}"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    return HTMLResponse(content=error_message, status_code=404, media_type='text/plain; charset=utf-8')
  
  # Read and return the logfile content
  try:
    with open(logfile_path, 'r', encoding='utf-8') as f:
      logfile_content = f.read()
    
    log_function_output(request_data, f"Retrieved logfile: {logfile_path}")
    await log_function_footer(request_data)
    return HTMLResponse(content=logfile_content, media_type='text/plain; charset=utf-8')
  except Exception as e:
    error_message = f"ERROR: Failed to read logfile: {str(e)}"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    return HTMLResponse(content=error_message, status_code=500, media_type='text/plain; charset=utf-8')

@router.get('/updatemaps')
async def updatemaps(request: Request):
  """
  Endpoint to update maps for a specific domain.
  
  Parameters:
  - domain_id: The ID of the domain to update maps for
  - logfile: The logfile parameter
    
  Examples:
  /updatemaps?domain_id=example&logfile=log.txt
  """
  function_name = 'updatemaps()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')  
  endpoint_documentation = updatemaps.__doc__
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  # Display documentation if no params are provided
  if len(request_params) == 0: await log_function_footer(request_data); return HTMLResponse(documentation_HTML)

  domain_id = request_params.get('domain_id', None)
  logfile = request_params.get('logfile', None)
  
  # Validate required parameters
  if not logfile:
    error_message = "ERROR: Missing required parameter 'logfile'"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    return HTMLResponse(content=error_message, status_code=400, media_type='text/plain; charset=utf-8')
  
  # Validate PERSISTENT_STORAGE_PATH is configured
  if not hasattr(request.app.state, 'system_info') or not request.app.state.system_info or not request.app.state.system_info.PERSISTENT_STORAGE_PATH:
    error_message = "ERROR: PERSISTENT_STORAGE_PATH not configured or is empty"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    return HTMLResponse(content=error_message, status_code=500, media_type='text/plain; charset=utf-8')
  
  # Build the logs directory path
  storage_path = request.app.state.system_info.PERSISTENT_STORAGE_PATH
  logs_folder = os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_LOGS_SUBFOLDER)
  logfile_path = os.path.join(logs_folder, logfile)
  
  # Create the logfile with initial content
  logfile_content = f"Log file created at {datetime.datetime.now().isoformat()}\n"
  logfile_content += f"Domain ID: {domain_id}\n"
  logfile_content += f"Logfile: {logfile}\n"
  
  # Use utility function to create the logfile
  logfile_content = create_logfile(logfile_path, logfile_content, request_data)
  
  await log_function_footer(request_data)
  return HTMLResponse(content=logfile_content, media_type='text/plain; charset=utf-8')


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
    storage_contents = scan_directory_recursive(storage_path, request_data, except_folder)
    total_items = len(storage_contents)
    
    log_function_output(request_data, f"Found {total_items} items in local storage")
    
    if format == 'zip':
      # Create and return zip file from scan results
      timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
      download_filename = f"{CRAWLER_HARDCODED_CONFIG.LOCALSTORAGE_ZIP_FILENAME_PREFIX}{timestamp}.zip"
      temp_zip_path = os.path.join(storage_path, download_filename)
      zip_file_path = create_storage_zip_from_scan(storage_path, storage_contents, request_data, temp_zip_path, download_filename)
      
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


@router.get('/loadsharepointfiles')
async def load_sharepoint_files(request: Request):
  """
  Endpoint to load files from a SharePoint document library for a specific domain source.
  
  This endpoint connects to SharePoint using the configured crawler credentials,
  retrieves all files from the specified document library (handling pagination for 5000+ items),
  and returns them in the requested format.
  
  Parameters:
  - domain_id: The ID of the domain to load files for (required)
  - source_id: The ID of the file source within the domain (required)
  - format: Response format - 'html' or 'json' (default: 'html')
  
  Examples:
  /loadsharepointfiles?domain_id=ExampleDomain01&source_id=source01&format=json
  /loadsharepointfiles?domain_id=ExampleDomain01&source_id=source01&format=html
  """
  from common_crawler_functions import load_domain
  from common_sharepoint_functions import connect_to_site_using_client_id, try_get_document_library, get_document_library_files
  from dataclasses import asdict
  
  function_name = 'load_sharepoint_files()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')  
  endpoint_documentation = load_sharepoint_files.__doc__
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  
  # Display documentation if no params are provided
  if len(request_params) == 0:
    await log_function_footer(request_data)
    return HTMLResponse(documentation_HTML)
  
  # Get parameters
  domain_id = request_params.get('domain_id')
  source_id = request_params.get('source_id')
  format = request_params.get('format', 'html').lower()
  
  # Validate required parameters
  if not domain_id:
    error_message = "ERROR: Missing required parameter 'domain_id'"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=400)
    return HTMLResponse(content=error_message, status_code=400, media_type='text/plain; charset=utf-8')
  
  if not source_id:
    error_message = "ERROR: Missing required parameter 'source_id'"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=400)
    return HTMLResponse(content=error_message, status_code=400, media_type='text/plain; charset=utf-8')
  
  try:
    # Validate system configuration
    if not hasattr(request.app.state, 'system_info') or not request.app.state.system_info:
      error_message = "ERROR: System configuration not available"
      log_function_output(request_data, error_message)
      await log_function_footer(request_data)
      if format == 'json':
        return JSONResponse({"error": error_message}, status_code=500)
      return HTMLResponse(content=error_message, status_code=500, media_type='text/plain; charset=utf-8')
    
    system_info = request.app.state.system_info
    
    # Validate PERSISTENT_STORAGE_PATH
    if not system_info.PERSISTENT_STORAGE_PATH:
      error_message = "ERROR: PERSISTENT_STORAGE_PATH not configured"
      log_function_output(request_data, error_message)
      await log_function_footer(request_data)
      if format == 'json':
        return JSONResponse({"error": error_message}, status_code=500)
      return HTMLResponse(content=error_message, status_code=500, media_type='text/plain; charset=utf-8')
    
    # Validate crawler credentials from config
    if not config or not config.CRAWLER_CLIENT_ID or not config.CRAWLER_CLIENT_SECRET:
      error_message = "ERROR: Crawler credentials (CRAWLER_CLIENT_ID, CRAWLER_CLIENT_SECRET) not configured"
      log_function_output(request_data, error_message)
      await log_function_footer(request_data)
      if format == 'json':
        return JSONResponse({"error": error_message}, status_code=500)
      return HTMLResponse(content=error_message, status_code=500, media_type='text/plain; charset=utf-8')
    
    storage_path = system_info.PERSISTENT_STORAGE_PATH
    
    # Load domain configuration
    log_function_output(request_data, f"Loading domain: '{domain_id}'")
    try:
      domain_config = load_domain(storage_path, domain_id, request_data)
    except FileNotFoundError as e:
      error_message = f"ERROR: Domain '{domain_id}' not found: {str(e)}"
      log_function_output(request_data, error_message)
      await log_function_footer(request_data)
      if format == 'json':
        return JSONResponse({"error": error_message}, status_code=404)
      return HTMLResponse(content=error_message, status_code=404, media_type='text/plain; charset=utf-8')
    
    # Find the file source with matching source_id
    file_source = next((src for src in domain_config.file_sources if src.source_id == source_id), None)
    
    if not file_source:
      error_message = f"ERROR: File source '{source_id}' not found in domain '{domain_id}'"
      log_function_output(request_data, error_message)
      await log_function_footer(request_data)
      if format == 'json':
        return JSONResponse({"error": error_message}, status_code=404)
      return HTMLResponse(content=error_message, status_code=404, media_type='text/plain; charset=utf-8')
    
    log_function_output(request_data, f"Found file source: '{file_source.site_url}{file_source.sharepoint_url_part}'")
    
    # Connect to SharePoint
    log_function_output(request_data, f"Connecting to SharePoint: '{file_source.site_url}'")
    ctx = connect_to_site_using_client_id(
      file_source.site_url,
      config.CRAWLER_CLIENT_ID,
      config.CRAWLER_CLIENT_SECRET
    )
    
    # Get document library
    log_function_output(request_data, f"Getting document library: '{file_source.sharepoint_url_part}'")
    document_library, library_error = try_get_document_library(ctx, file_source.site_url, file_source.sharepoint_url_part)
    
    if not document_library:
      error_message = f"ERROR: {library_error}"
      log_function_output(request_data, error_message)
      await log_function_footer(request_data)
      if format == 'json':
        return JSONResponse({"error": error_message}, status_code=500)
      return HTMLResponse(content=error_message, status_code=500, media_type='text/plain; charset=utf-8')
    
    # Get all files from the library
    log_function_output(request_data, f"Loading files with filter: '{file_source.filter or '(none)'}'")
    files = get_document_library_files(ctx, document_library, file_source.filter, request_data)
    
    log_function_output(request_data, f"Successfully loaded {len(files)} files")
    
    # Return in requested format
    if format == 'json':
      # Convert SharePointFile dataclasses to dictionaries
      files_dict = [asdict(file) for file in files]
      response_data = {
        "domain_id": domain_id,
        "source_id": source_id,
        "site_url": file_source.site_url,
        "sharepoint_url_part": file_source.sharepoint_url_part,
        "filter": file_source.filter,
        "total_files": len(files),
        "files": files_dict
      }
      await log_function_footer(request_data)
      return JSONResponse(response_data)
    else:
      # HTML format
      title = f"SharePoint Files - {domain_config.name} ({source_id})"
      
      # Convert files to list of dicts for table
      files_data = [asdict(file) for file in files]
      
      table_html = convert_to_flat_html_table(files_data)
      
      html_content = f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
  <title>{title}</title>
  <link rel='stylesheet' href='/static/css/styles.css'>
  <script src='/static/js/htmx.js'></script>
</head>
<body>
  <h1>{title}</h1>
  <p><strong>Domain:</strong> {domain_config.name} ({domain_id})</p>
  <p><strong>Source:</strong> {source_id}</p>
  <p><strong>Site URL:</strong> {file_source.site_url}</p>
  <p><strong>Library:</strong> {file_source.sharepoint_url_part}</p>
  <p><strong>Filter:</strong> {file_source.filter or '(none)'}</p>
  <p><strong>Total Files:</strong> {len(files)}</p>
  <hr>
  {table_html}
  <p><a href="/crawler">← Back to Crawler</a></p>
</body>
</html>"""
      
      await log_function_footer(request_data)
      return HTMLResponse(html_content)
      
  except Exception as e:
    error_message = f"ERROR: Unexpected error: {str(e)}"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=500)
    return HTMLResponse(content=error_message, status_code=500, media_type='text/plain; charset=utf-8')