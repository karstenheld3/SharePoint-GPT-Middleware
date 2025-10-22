# endpoints for the sharepoint crawler
import csv, datetime, json, os, tempfile
from typing import Any, Dict, List
from dataclasses import asdict
from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse

from hardcoded_config import CRAWLER_HARDCODED_CONFIG
from utils import convert_to_flat_html_table, convert_to_nested_html_table, log_function_footer, log_function_header, log_function_output, include_exclude_attributes
from common_crawler_functions import DomainConfig, load_all_domains, domain_config_to_dict, scan_directory_recursive, create_storage_zip_from_scan, load_domain, load_files_from_sharepoint_source, load_crawled_files, load_vector_store_files_as_crawled_files, is_files_metadata_v2_format, is_files_metadata_v3_format, convert_file_metadata_item_from_v2_to_v3, download_files_from_sharepoint, update_vector_store as update_vector_store_impl
from common_openai_functions import OPENAI_DATETIME_ATTRIBUTES


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
    <li><a href="/crawler/download_files">/crawler/download_files</a> - Download SharePoint Files (<a href="/crawler/download_files?domain_id=ExampleDomain01&source_id=source01&format=html">Example HTML</a> + <a href="/crawler/download_files?domain_id=ExampleDomain01&format=json">Example JSON</a>)</li>
    <li><a href="/crawler/update_vector_store">/crawler/update_vector_store</a> - Update Vector Store (<a href="/crawler/update_vector_store?domain_id=ExampleDomain01&format=html">Example HTML</a> + <a href="/crawler/update_vector_store?domain_id=ExampleDomain01&temp_vs_only=true&format=json">Example JSON</a>)</li>
    <li><a href="/crawler/localstorage">/crawler/localstorage</a> - Local Storage Inventory (<a href="/crawler/localstorage?format=html">HTML</a> + <a href="/crawler/localstorage?format=json">JSON</a> + <a href="/crawler/localstorage?format=zip">ZIP</a> + <a href="/crawler/localstorage?format=zip&exceptfolder=crawler">ZIP except 'crawler' folder</a>)</li>
    <li><a href="/crawler/list_sharepoint_files">/crawler/list_sharepoint_files</a> - List SharePoint Files (<a href="/crawler/list_sharepoint_files?domain_id=ExampleDomain01&source_id=source01&format=html&includeattributes=sharepoint_listitem_id,sharepoint_unique_file_id,raw_url,filename,file_size,last_modified_utc">Example HTML</a> + <a href="/crawler/list_sharepoint_files?domain_id=ExampleDomain01&source_id=source01&format=json">Example JSON</a>)</li>
    <li><a href="/crawler/list_local_files">/crawler/list_local_files</a> - List Local Embedded Files (<a href="/crawler/list_local_files?domain_id=ExampleDomain01&format=html&includeattributes=file_path,raw_url,file_size,last_modified_utc">Example HTML</a> + <a href="/crawler/list_local_files?domain_id=ExampleDomain01&source_id=source01&format=json">Example JSON</a>)</li>
    <li><a href="/crawler/list_vectorstore_files">/crawler/list_vectorstore_files</a> - List Vector Store Files (<a href="/crawler/list_vectorstore_files?domain_id=ExampleDomain01&format=html">Example HTML</a> + <a href="/crawler/list_vectorstore_files?domain_id=ExampleDomain01&format=json">Example JSON</a>)</li>
    <li><a href="/crawler/migrate_from_v2_to_v3">/crawler/migrate_from_v2_to_v3</a> - Migrate files_metadata.json from v2 to v3 format (<a href="/crawler/migrate_from_v2_to_v3?format=html">HTML</a> + <a href="/crawler/migrate_from_v2_to_v3?format=json">JSON</a>)</li>
  </ul>

  <p><a href="/">← Back to Main Page</a></p>
</body>
</html>
"""

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


@router.get('/list_sharepoint_files')
async def list_sharepoint_files(request: Request):
  """
  Endpoint to list files from a SharePoint document library for a specific domain source.
  
  This endpoint connects to SharePoint using the configured crawler credentials,
  retrieves all files from the specified document library (handling pagination for 5000+ items),
  and returns them in the requested format.
  
  Parameters:
  - domain_id: The ID of the domain to list files for (required)
  - source_id: The ID of the file source within the domain (required)
  - format: Response format - 'html' or 'json' (default: 'html')
  - includeattributes: Comma-separated list of attributes to include in response (takes precedence over excludeattributes)
  - excludeattributes: Comma-separated list of attributes to exclude from response (ignored if includeattributes is set)
  
  Examples:
  /list_sharepoint_files?domain_id=ExampleDomain01&source_id=source01&format=json
  /list_sharepoint_files?domain_id=ExampleDomain01&source_id=source01&format=html
  /list_sharepoint_files?domain_id=ExampleDomain01&source_id=source01&format=json&includeattributes=filename,file_size,last_modified_utc
  /list_sharepoint_files?domain_id=ExampleDomain01&source_id=source01&format=json&excludeattributes=file_id,file_path
  """
  
  function_name = 'list_sharepoint_files()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')  
  endpoint_documentation = list_sharepoint_files.__doc__
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  
  # Display documentation if no params are provided
  if len(request_params) == 0:
    await log_function_footer(request_data)
    return HTMLResponse(documentation_HTML)
  
  # Get parameters
  domain_id = request_params.get('domain_id')
  source_id = request_params.get('source_id')
  format = request_params.get('format', 'html').lower()
  include_attributes = request_params.get('includeattributes')
  exclude_attributes = request_params.get('excludeattributes')
  
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
    
    # Load files using the refactored function
    try:
      files = load_files_from_sharepoint_source(system_info, domain_id, source_id, request_data, config)
    except ValueError as e:
      error_message = f"ERROR: {str(e)}"
      log_function_output(request_data, error_message)
      await log_function_footer(request_data)
      if format == 'json':
        return JSONResponse({"error": error_message}, status_code=500)
      return HTMLResponse(content=error_message, status_code=500, media_type='text/plain; charset=utf-8')
    except FileNotFoundError as e:
      error_message = f"ERROR: {str(e)}"
      log_function_output(request_data, error_message)
      await log_function_footer(request_data)
      if format == 'json':
        return JSONResponse({"error": error_message}, status_code=404)
      return HTMLResponse(content=error_message, status_code=404, media_type='text/plain; charset=utf-8')
    
    # Reload domain config for response metadata
    domain_config = load_domain(system_info.PERSISTENT_STORAGE_PATH, domain_id, request_data)
    file_source = next((src for src in domain_config.file_sources if src.source_id == source_id), None)
    
    # Apply include/exclude filters
    filtered_files = include_exclude_attributes(files, include_attributes, exclude_attributes)
    
    # Return in requested format
    if format == 'json':
      response_data = {
        "domain_id": domain_id,
        "source_id": source_id,
        "site_url": file_source.site_url,
        "sharepoint_url_part": file_source.sharepoint_url_part,
        "filter": file_source.filter,
        "total_files": len(filtered_files),
        "files": filtered_files
      }
      await log_function_footer(request_data)
      return JSONResponse(response_data)
    else:
      # HTML format
      title = f"SharePoint Files - {domain_config.name} ({source_id})"
      
      table_html = convert_to_flat_html_table(filtered_files)
      
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

@router.get('/list_local_files')
async def list_local_files(request: Request):
  """
  Endpoint to list local embedded files from the crawler storage for a specific domain source.
  
  This endpoint scans the local embedded files directory and returns a list of files
  with their metadata (filename, relative path, last modified date, file size).
  
  Parameters:
  - domain_id: The ID of the domain to list files for (required)
  - source_id: The ID of the file source within the domain (required)
  - format: Response format - 'html' or 'json' (default: 'html')
  - includeattributes: Comma-separated list of attributes to include in response (takes precedence over excludeattributes)
  - excludeattributes: Comma-separated list of attributes to exclude from response (ignored if includeattributes is set)
  
  Examples:
  /list_local_files?domain_id=ExampleDomain01&source_id=source01&format=json
  /list_local_files?domain_id=ExampleDomain01&source_id=source01&format=html
  /list_local_files?domain_id=ExampleDomain01&source_id=source01&format=json&includeattributes=filename,file_size,last_modified_utc
  /list_local_files?domain_id=ExampleDomain01&source_id=source01&format=json&excludeattributes=file_id,file_path
  """
  
  function_name = 'list_local_files()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')  
  endpoint_documentation = list_local_files.__doc__
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  
  # Display documentation if no params are provided
  if len(request_params) == 0:
    await log_function_footer(request_data)
    return HTMLResponse(documentation_HTML)
  
  # Get parameters
  domain_id = request_params.get('domain_id')
  source_id = request_params.get('source_id')
  format = request_params.get('format', 'html').lower()
  include_attributes = request_params.get('includeattributes')
  exclude_attributes = request_params.get('excludeattributes')
  
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
    
    # Load local embedded files
    try:
      files = load_crawled_files(system_info.PERSISTENT_STORAGE_PATH, domain_id, source_id, request_data)
    except FileNotFoundError as e:
      error_message = f"ERROR: {str(e)}"
      log_function_output(request_data, error_message)
      await log_function_footer(request_data)
      if format == 'json':
        return JSONResponse({"error": error_message}, status_code=404)
      return HTMLResponse(content=error_message, status_code=404, media_type='text/plain; charset=utf-8')
    
    # Load domain config for response metadata
    try:
      domain_config = load_domain(system_info.PERSISTENT_STORAGE_PATH, domain_id, request_data)
      file_source = next((src for src in domain_config.file_sources if src.source_id == source_id), None)
    except FileNotFoundError:
      # Domain config not found, use minimal metadata
      domain_config = None
      file_source = None
    
    # Apply include/exclude filters
    filtered_files = include_exclude_attributes(files, include_attributes, exclude_attributes)
    
    # Return in requested format
    if format == 'json':
      response_data = {
        "domain_id": domain_id,
        "source_id": source_id,
        "total_files": len(filtered_files),
        "files": filtered_files
      }
      await log_function_footer(request_data)
      return JSONResponse(response_data)
    else:
      # HTML format
      title = f"Local Embedded Files - {domain_config.name if domain_config else domain_id} ({source_id})"
      
      table_html = convert_to_flat_html_table(filtered_files)
      
      html_content = f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
  <title>{title}</title>
  <link rel='stylesheet' href='/static/css/styles.css'>
  <script src='/static/js/htmx.js'></script>
</head>
<body>
  <h1>{title}</h1>
  <p><strong>Domain:</strong> {domain_config.name if domain_config else domain_id} ({domain_id})</p>
  <p><strong>Source:</strong> {source_id}</p>"""
      
      if file_source:
        html_content += f"""
  <p><strong>Site URL:</strong> {file_source.site_url}</p>
  <p><strong>Library:</strong> {file_source.sharepoint_url_part}</p>
  <p><strong>Filter:</strong> {file_source.filter or '(none)'}</p>"""
      
      html_content += f"""
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

@router.get('/list_vectorstore_files')
async def list_vectorstore_files(request: Request):
  """
  Endpoint to list files from the OpenAI vector store for a specific domain.
  
  This endpoint retrieves all files from the vector store associated with the domain,
  including enriched metadata (filename, file size, status, etc.) from the global files list.
  
  Parameters:
  - domain_id: The ID of the domain to list files for (required)
  - format: Response format - 'html' or 'json' (default: 'html')
  - includeattributes: Comma-separated list of attributes to include in response (takes precedence over excludeattributes)
  - excludeattributes: Comma-separated list of attributes to exclude from response (ignored if includeattributes is set)
  
  Examples:
  /list_vectorstore_files?domain_id=ExampleDomain01&format=json
  /list_vectorstore_files?domain_id=ExampleDomain01&format=html
  /list_vectorstore_files?domain_id=ExampleDomain01&format=json&includeattributes=filename,bytes,status
  /list_vectorstore_files?domain_id=ExampleDomain01&format=json&excludeattributes=expires_at,status_details
  """
  
  function_name = 'list_vectorstore_files()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')  
  endpoint_documentation = list_vectorstore_files.__doc__
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  
  # Display documentation if no params are provided
  if len(request_params) == 0:
    await log_function_footer(request_data)
    return HTMLResponse(documentation_HTML)
  
  # Get parameters
  domain_id = request_params.get('domain_id')
  format = request_params.get('format', 'html').lower()
  include_attributes = request_params.get('includeattributes')
  exclude_attributes = request_params.get('excludeattributes')
  
  # Validate required parameters
  if not domain_id:
    error_message = "ERROR: Missing required parameter 'domain_id'"
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
    
    # Validate OpenAI client
    if not hasattr(request.app.state, 'openai_client') or not request.app.state.openai_client:
      error_message = "ERROR: OpenAI client not available"
      log_function_output(request_data, error_message)
      await log_function_footer(request_data)
      if format == 'json':
        return JSONResponse({"error": error_message}, status_code=500)
      return HTMLResponse(content=error_message, status_code=500, media_type='text/plain; charset=utf-8')
    
    system_info = request.app.state.system_info
    openai_client = request.app.state.openai_client
    
    # Load files from vector store using wrapper function
    try:
      files = await load_vector_store_files_as_crawled_files(openai_client, system_info.PERSISTENT_STORAGE_PATH, domain_id, request_data)
    except FileNotFoundError as e:
      error_message = f"ERROR: {str(e)}"
      log_function_output(request_data, error_message)
      await log_function_footer(request_data)
      if format == 'json':
        return JSONResponse({"error": error_message}, status_code=404)
      return HTMLResponse(content=error_message, status_code=404, media_type='text/plain; charset=utf-8')
    except Exception as e:
      error_message = f"ERROR: Failed to retrieve files from vector store: {str(e)}"
      log_function_output(request_data, error_message)
      await log_function_footer(request_data)
      if format == 'json':
        return JSONResponse({"error": error_message}, status_code=500)
      return HTMLResponse(content=error_message, status_code=500, media_type='text/plain; charset=utf-8')
    
    # Reload domain config for response metadata
    domain_config = load_domain(system_info.PERSISTENT_STORAGE_PATH, domain_id, request_data)
    
    # Convert to list of dicts
    files_list = [asdict(f) for f in files]
    
    # Apply include/exclude filters
    filtered_files = include_exclude_attributes(files_list, include_attributes, exclude_attributes)
    
    # Return in requested format
    if format == 'json':
      response_data = {
        "domain_id": domain_id,
        "vector_store_id": domain_config.vector_store_id,
        "vector_store_name": domain_config.vector_store_name,
        "total_files": len(filtered_files),
        "files": filtered_files
      }
      await log_function_footer(request_data)
      return JSONResponse(response_data)
    else:
      # HTML format
      title = f"Vector Store Files - {domain_config.name}"
      
      table_html = convert_to_flat_html_table(filtered_files)
      
      html_content = f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
  <title>{title}</title>
  <link rel='stylesheet' href='/static/css/styles.css'>
  <script src='/static/js/htmx.js'></script>
</head>
<body>
  <h1>{title}</h1>
  <p><strong>Domain:</strong> {domain_config.name} ({domain_id})</p>
  <p><strong>Vector Store:</strong> {domain_config.vector_store_name}</p>
  <p><strong>Vector Store ID:</strong> {domain_config.vector_store_id}</p>
  <p><strong>Total Files:</strong> {len(files_list)}</p>
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


@router.get('/migrate_from_v2_to_v3')
async def migrate_from_v2_to_v3(request: Request):
  """
  Migrate files_metadata.json from v2 to v3 format across all domains.
  
  V2 format has:
  - embedded_file_relative_path
  - embedded_file_last_modified_utc
  - file_metadata object with nested fields
  
  V3 format is a flat array matching the CrawledFile dataclass with fields:
  - openai_file_id (from file_id)
  - sharepoint_listitem_id
  - sharepoint_unique_file_id
  - file_relative_path (from embedded_file_relative_path)
  - url (from file_metadata.source)
  - raw_url (from file_metadata.raw_url)
  - server_relative_url
  - filename (from file_metadata.filename)
  - file_type (from file_metadata.file_type)
  - file_size (from file_metadata.file_size)
  - last_modified_utc (from embedded_file_last_modified_utc)
  - last_modified_timestamp
  - openai_file_id (from file_id)
  
  Query Parameters:
  - format: Response format ('html' or 'json', default: 'html')
  
  Returns:
  - HTML or JSON response with migration results
  """
  function_name = 'migrate_from_v2_to_v3()'
  request_data = log_function_header(function_name)
  
  system_info = request.app.state.system_info
  
  # Get query parameters
  format = request.query_params.get('format', 'html').lower()
  
  try:
    # Load all domains
    log_function_output(request_data, "Loading all domains...")
    domains = load_all_domains(system_info.PERSISTENT_STORAGE_PATH, request_data)
    log_function_output(request_data, f"Found {len(domains)} domain(s)")
    
    migration_results = []
    
    # Process each domain
    for domain in domains:
      domain_id = domain.domain_id
      log_function_output(request_data, f"\n--- Processing domain: {domain_id} ---")
      
      # Path to files_metadata.json
      metadata_file_path = os.path.join(
        system_info.PERSISTENT_STORAGE_PATH,
        CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER,
        domain_id,
        CRAWLER_HARDCODED_CONFIG.FILES_METADATA_JSON
      )
      
      # Check if files_metadata.json exists
      if not os.path.exists(metadata_file_path):
        log_function_output(request_data, f"  No files_metadata.json found, skipping")
        migration_results.append({
          "domain_id": domain_id,
          "status": "skipped",
          "reason": "files_metadata.json not found"
        })
        continue
      
      # Read the file
      log_function_output(request_data, f"  Reading: {metadata_file_path}")
      with open(metadata_file_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
      
      # Check if it's empty
      if not metadata or len(metadata) == 0:
        log_function_output(request_data, f"  Empty metadata file, skipping")
        migration_results.append({
          "domain_id": domain_id,
          "status": "skipped",
          "reason": "empty metadata file"
        })
        continue
      
      # Detect v2 format
      first_item = metadata[0]
      is_v2 = is_files_metadata_v2_format(first_item)
      
      if not is_v2:
        log_function_output(request_data, f"  Already in v3 format or unknown format, skipping")
        migration_results.append({
          "domain_id": domain_id,
          "status": "skipped",
          "reason": "already v3 format or unknown format"
        })
        continue
      
      log_function_output(request_data, f"  Detected v2 format with {len(metadata)} file(s)")
      
      # Create backup
      backup_file_path = metadata_file_path.replace('.json', '_v2.json')
      log_function_output(request_data, f"  Creating backup: '{backup_file_path}'")
      with open(backup_file_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
      
      # Convert to v3 format
      log_function_output(request_data, f"  Converting to v3 format...")
      v3_metadata = [convert_file_metadata_item_from_v2_to_v3(item) for item in metadata]
      
      # Write v3 format
      log_function_output(request_data, f"  Writing v3 format to: {metadata_file_path}")
      with open(metadata_file_path, 'w', encoding='utf-8') as f:
        json.dump(v3_metadata, f, indent=2, ensure_ascii=False)
      
      log_function_output(request_data, f"  ✓ Successfully migrated {len(v3_metadata)} file(s)")
      migration_results.append({
        "domain_id": domain_id,
        "status": "migrated",
        "files_count": len(v3_metadata),
        "backup_file": backup_file_path
      })
    
    # Summary
    log_function_output(request_data, f"\n=== Migration Summary ===")
    migrated_count = sum(1 for r in migration_results if r['status'] == 'migrated')
    skipped_count = sum(1 for r in migration_results if r['status'] == 'skipped')
    log_function_output(request_data, f"Total domains: {len(domains)}")
    log_function_output(request_data, f"Migrated: {migrated_count}")
    log_function_output(request_data, f"Skipped: {skipped_count}")
    
    log_function_footer(request_data)
    
    # Return response
    if format == 'json':
      return JSONResponse({
        "total_domains": len(domains),
        "migrated": migrated_count,
        "skipped": skipped_count,
        "results": migration_results
      })
    else:
      # HTML format
      results_html = "<ul>"
      for result in migration_results:
        if result['status'] == 'migrated':
          results_html += f"<li><strong>{result['domain_id']}</strong>: ✓ Migrated {result['files_count']} files (backup: {os.path.basename(result['backup_file'])})</li>"
        else:
          results_html += f"<li><strong>{result['domain_id']}</strong>: Skipped ({result['reason']})</li>"
      results_html += "</ul>"
      
      html_content = f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
  <title>Migration v2 to v3 Results</title>
  <link rel='stylesheet' href='/static/css/styles.css'>
  <script src='/static/js/htmx.js'></script>
</head>
<body>
  <h1>Migration v2 to v3 Results</h1>
  <p><strong>Total Domains:</strong> {len(domains)}</p>
  <p><strong>Migrated:</strong> {migrated_count}</p>
  <p><strong>Skipped:</strong> {skipped_count}</p>
  <hr>
  <h2>Details</h2>
  {results_html}
  <hr>
  <p><a href="/crawler">← Back to Crawler</a></p>
</body>
</html>"""
      
      return HTMLResponse(html_content)
  
  except Exception as e:
    error_message = f"ERROR: Migration failed: {str(e)}"
    log_function_output(request_data, error_message)
    log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=500)
    return HTMLResponse(content=error_message, status_code=500, media_type='text/plain; charset=utf-8')

@router.get('/download_files')
async def download_files(request: Request):
  """
  Endpoint to download files from SharePoint for a specific domain.
  
  Parameters:
  - domain_id: The ID of the domain to download files for (required)
  - source_id: The ID of the file source within the domain (optional, if not given all sources are downloaded)
  - format: Response format - 'html' or 'json' (default: 'html')
    
  Examples:
  /download_files?domain_id=ExampleDomain01&source_id=source01&format=html
  /download_files?domain_id=ExampleDomain01&format=json
  """
  function_name = 'download_files()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')  
  endpoint_documentation = download_files.__doc__
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  # Display documentation if no params are provided
  if len(request_params) == 0: await log_function_footer(request_data); return HTMLResponse(documentation_HTML)

  domain_id = request_params.get('domain_id', None)
  source_id = request_params.get('source_id', None)
  format = request_params.get('format', 'html').lower()
  
  # Validate required parameters
  if not domain_id:
    error_message = "ERROR: Missing required parameter 'domain_id'"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    return HTMLResponse(content=error_message, status_code=400, media_type='text/plain; charset=utf-8')
  
  # Validate format parameter
  if format not in ['html', 'json']:
    error_message = f"ERROR: Invalid format '{format}'. Must be 'html' or 'json'"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    return HTMLResponse(content=error_message, status_code=400, media_type='text/plain; charset=utf-8')
  
  # Validate system configuration
  if not hasattr(request.app.state, 'system_info') or not request.app.state.system_info or not request.app.state.system_info.PERSISTENT_STORAGE_PATH:
    error_message = "ERROR: PERSISTENT_STORAGE_PATH not configured or is empty"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    return HTMLResponse(content=error_message, status_code=500, media_type='text/plain; charset=utf-8')
  
  # Validate crawler configuration
  if not config or not config.CRAWLER_CLIENT_ID or not config.CRAWLER_CLIENT_CERTIFICATE_PFX_FILE or not config.CRAWLER_CLIENT_CERTIFICATE_PASSWORD or not config.CRAWLER_TENANT_ID:
    error_message = "ERROR: Crawler credentials not configured"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    return HTMLResponse(content=error_message, status_code=500, media_type='text/plain; charset=utf-8')
  
  try:
    # Call the download function
    log_function_output(request_data, f"Starting download for domain_id='{domain_id}', source_id='{source_id or '(all sources)'}'")
    
    results = download_files_from_sharepoint(
      system_info=request.app.state.system_info,
      domain_id=domain_id,
      source_id=source_id,
      request_data=request_data,
      config=config
    )
    
    log_function_output(request_data, "Download completed successfully")
    await log_function_footer(request_data)
    
    # Return response based on format
    if format == 'json':
      return JSONResponse(content=results)
    else:
      # Generate HTML response
      html_response = _generate_html_response_from_nested_data(
        title=f"Download Files - {domain_id}",
        data=results
      )
      return HTMLResponse(content=html_response)
      
  except FileNotFoundError as e:
    error_message = f"ERROR: {str(e)}"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    return HTMLResponse(content=error_message, status_code=404, media_type='text/plain; charset=utf-8')
  except ValueError as e:
    error_message = f"ERROR: {str(e)}"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    return HTMLResponse(content=error_message, status_code=400, media_type='text/plain; charset=utf-8')
  except Exception as e:
    error_message = f"ERROR: Failed to download files: {str(e)}"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    return HTMLResponse(content=error_message, status_code=500, media_type='text/plain; charset=utf-8')

@router.get('/update_vector_store')
async def update_vector_store(request: Request):
  """
  Endpoint to update vector store with files from local storage.
  
  Parameters:
  - domain_id: The ID of the domain to process (required)
  - temp_vs_only: If false (default), temp vs is replicated into domain vs (optional, default: false)
  - format: Response format - 'html' or 'json' (default: 'html')
    
  Examples:
  /update_vector_store?domain_id=ExampleDomain01&format=html
  /update_vector_store?domain_id=ExampleDomain01&temp_vs_only=true&format=json
  """
  function_name = 'update_vector_store()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')  
  endpoint_documentation = update_vector_store.__doc__
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  if len(request_params) == 0: await log_function_footer(request_data); return HTMLResponse(documentation_HTML)

  domain_id = request_params.get('domain_id', None)
  temp_vs_only = request_params.get('temp_vs_only', 'false').lower() in ['true', '1', 'yes']
  format = request_params.get('format', 'html').lower()
  
  # Validate required parameters
  if not domain_id:
    error_message = "ERROR: Missing required parameter 'domain_id'"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    return HTMLResponse(content=error_message, status_code=400, media_type='text/plain; charset=utf-8')
  
  # Validate format parameter
  if format not in ['html', 'json']:
    error_message = f"ERROR: Invalid format '{format}'. Must be 'html' or 'json'"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    return HTMLResponse(content=error_message, status_code=400, media_type='text/plain; charset=utf-8')
  
  # Validate system configuration
  if not hasattr(request.app.state, 'system_info') or not request.app.state.system_info or not request.app.state.system_info.PERSISTENT_STORAGE_PATH:
    error_message = "ERROR: PERSISTENT_STORAGE_PATH not configured or is empty"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    return HTMLResponse(content=error_message, status_code=500, media_type='text/plain; charset=utf-8')
  
  # Validate OpenAI client
  if not hasattr(request.app.state, 'openai_client') or not request.app.state.openai_client:
    error_message = "ERROR: OpenAI client not configured"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    return HTMLResponse(content=error_message, status_code=500, media_type='text/plain; charset=utf-8')
  
  try:
    # Call the update function
    log_function_output(request_data, f"Starting vector store update for domain_id='{domain_id}', temp_vs_only={temp_vs_only}")
    
    results = await update_vector_store_impl(
      system_info=request.app.state.system_info,
      openai_client=request.app.state.openai_client,
      domain_id=domain_id,
      temp_vs_only=temp_vs_only,
      request_data=request_data
    )
    
    log_function_output(request_data, "Vector store update completed successfully")
    await log_function_footer(request_data)
    
    # Return response based on format
    if format == 'json':
      return JSONResponse(content=results)
    else:
      html_response = _generate_html_response_from_nested_data(title=f"Update Vector Store - {domain_id}", data=results)
      return HTMLResponse(content=html_response)
      
  except FileNotFoundError as e:
    error_message = f"ERROR: {str(e)}"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    return HTMLResponse(content=error_message, status_code=404, media_type='text/plain; charset=utf-8')
  except ValueError as e:
    error_message = f"ERROR: {str(e)}"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    return HTMLResponse(content=error_message, status_code=400, media_type='text/plain; charset=utf-8')
  except Exception as e:
    error_message = f"ERROR: Failed to update vector store: {str(e)}"
    log_function_output(request_data, error_message)
    await log_function_footer(request_data)
    return HTMLResponse(content=error_message, status_code=500, media_type='text/plain; charset=utf-8')
