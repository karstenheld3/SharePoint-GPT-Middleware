import logging
from dataclasses import asdict
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from common_openai_functions import get_all_vector_stores, get_all_files, get_all_assistants, convert_openai_timestamps_to_utc
from utils import convert_to_flat_html_table, log_function_footer, log_function_header, log_function_output

router = APIRouter()

# Configuration will be injected from app.py
config = None

logger = logging.getLogger(__name__)

def set_config(app_config):
  """Set the configuration for Inventory management."""
  global config
  config = app_config

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
  table_html = convert_to_flat_html_table(objects)
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


