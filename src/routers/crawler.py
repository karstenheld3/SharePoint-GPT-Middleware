# endpoints for the sharepoint crawler
import datetime, json, os, tempfile
from typing import Any, Dict, List

from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse

from hardcoded_config import CRAWLER_HARDCODED_CONFIG
from utils import convert_to_flat_html_table, convert_to_nested_html_table, log_function_footer, log_function_header, log_function_output
from common_crawler_functions import (
    DomainConfig, 
    load_all_domains, 
    domain_config_to_dict,
    scan_directory_recursive,
    create_storage_zip_from_scan
)

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
  <script src='/static/js/htmx.min.js'></script>
</head>
<body>
  <h1>{title}</h1>
  {table_html}
</body>
</html>"""


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

@router.get('/domains')
async def domains(request: Request):
  """
  Endpoint to retrieve all domain configurations from the domains folder.
  
  Parameters:
  - format: The response format (json, html, or ui)
    
  Examples:
  /domains
  /domains?format=json
  /domains?format=html
  /domains?format=ui
  """
  function_name = 'domains()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')  
  endpoint_documentation = domains.__doc__
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  # Display documentation if no params are provided
  if len(request_params) == 0: await log_function_footer(request_data); return HTMLResponse(documentation_HTML)

  format = request_params.get('format', 'html')
  
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
    
    # Load all domains using the new function
    domains_list = load_all_domains(storage_path, request_data)
    
    if format == 'json':
      # Convert dataclasses to dictionaries for JSON response
      domains_dict_list = [domain_config_to_dict(domain) for domain in domains_list]
      await log_function_footer(request_data)
      return JSONResponse({"data": domains_dict_list, "count": len(domains_dict_list)})
    elif format == 'ui':
      # Create UI-friendly list with specific columns
      ui_list = []
      for domain in domains_list:
        ui_list.append({
          "ID": domain.domain_id,
          "Name": domain.name,
          "Vector Store ID": domain.vector_store_id,
          "Vector Store Name": domain.vector_store_name
        })
      
      table_html = convert_to_flat_html_table(ui_list)
      html_content = f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
  <title>Domains ({len(ui_list)})</title>
  <link rel='stylesheet' href='/static/css/styles.css'>
  <script src='/static/js/htmx.min.js'></script>
</head>
<body>
  <h1>Domains ({len(ui_list)})</h1>
  {table_html}
</body>
</html>"""
      await log_function_footer(request_data)
      return HTMLResponse(html_content)
    else:
      # HTML format with full domain data (using nested table for complex structures)
      domains_dict_list = [domain_config_to_dict(domain) for domain in domains_list]
      html_content = _generate_html_response_from_nested_data(
        f"Domains ({len(domains_dict_list)})",
        domains_dict_list
      )
      await log_function_footer(request_data)
      return HTMLResponse(html_content)
      
  except FileNotFoundError as e:
    error_message = str(e)
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=404)
    else:
      error_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Error</title></head><body><h1>Error</h1><p>{error_message}</p></body></html>"
      return HTMLResponse(error_html, status_code=404)
  except Exception as e:
    error_message = f"Error retrieving domains: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=500)
    else:
      error_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Error</title></head><body><h1>Error</h1><p>{error_message}</p></body></html>"
      return HTMLResponse(error_html, status_code=500)