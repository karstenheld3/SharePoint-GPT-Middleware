from dataclasses import asdict
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from routers_v1.common_openai_functions_v1 import get_all_vector_stores, get_all_files, get_all_assistants, convert_openai_timestamps_to_utc, delete_vector_store_by_id, get_vector_store_files_with_filenames_as_dict, try_get_vector_store_by_id, remove_file_from_vector_store, delete_file_from_vector_store_and_storage, delete_file_by_id, delete_assistant_by_id
from routers_v1.common_ui_functions_v1 import generate_html_head, generate_simple_page, generate_table_page, generate_table_with_headers, generate_update_count_script, generate_ui_table_page
from common_utility_functions import convert_to_flat_html_table, include_exclude_attributes
from routers_v1.common_logging_functions_v1 import log_function_footer, log_function_header, log_function_output

router = APIRouter()

# Configuration will be injected from app.py
config = None
router_prefix = ""

def set_config(app_config, prefix: str = ""):
  """Set the configuration for Inventory management."""
  global config, router_prefix
  config = app_config
  router_prefix = prefix

@router.get('/inventory', response_class=HTMLResponse)
async def inventory_root():
  """
  Inventory endpoints documentation and overview.
  """
  return f"""
<!doctype html><html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Inventory Endpoints</title>
  <link rel="stylesheet" href="/static/css/styles.css">
  <script src="/static/js/htmx.js"></script>
</head>
<body>
  <h1>Inventory Endpoints</h1>
  <p>This section provides endpoints for managing and viewing Azure OpenAI resources including vector stores, files, and assistants.</p>

  <h4>Available Endpoints</h4>
  <ul>
    <li><a href="{router_prefix}/inventory/vectorstores">{router_prefix}/inventory/vectorstores</a> - List All Vector Stores (<a href="{router_prefix}/inventory/vectorstores?format=html">HTML</a> + <a href="{router_prefix}/inventory/vectorstores?format=json">JSON</a> + <a href="{router_prefix}/inventory/vectorstores?format=ui">UI</a>)</li>
    <li><a href="{router_prefix}/inventory/vectorstores/delete">{router_prefix}/inventory/vectorstores/delete</a> - Delete Vector Store (<a href="{router_prefix}/inventory/vectorstores/delete">Docs</a>)</li>
    <li><a href="{router_prefix}/inventory/vectorstore_files">{router_prefix}/inventory/vectorstore_files</a> - List Files in Vector Store (<a href="{router_prefix}/inventory/vectorstore_files?vector_store_id=vs_abc123&format=html">Example HTML</a> + <a href="{router_prefix}/inventory/vectorstore_files?vector_store_id=vs_abc123&format=json">Example JSON</a>)</li>
    <li><a href="{router_prefix}/inventory/vectorstore_files/remove">{router_prefix}/inventory/vectorstore_files/remove</a> - Remove File from Vector Store (<a href="{router_prefix}/inventory/vectorstore_files/remove">Docs</a>)</li>
    <li><a href="{router_prefix}/inventory/vectorstore_files/delete">{router_prefix}/inventory/vectorstore_files/delete</a> - Delete File from Vector Store and Storage (<a href="{router_prefix}/inventory/vectorstore_files/delete">Docs</a>)</li>
    <li><a href="{router_prefix}/inventory/files">{router_prefix}/inventory/files</a> - List All Files (<a href="{router_prefix}/inventory/files?format=html">HTML</a> + <a href="{router_prefix}/inventory/files?format=json">JSON</a> + <a href="{router_prefix}/inventory/files?format=ui">UI</a>)</li>
    <li><a href="{router_prefix}/inventory/files/delete">{router_prefix}/inventory/files/delete</a> - Delete File from Storage (<a href="{router_prefix}/inventory/files/delete">Docs</a>)</li>
    <li><a href="{router_prefix}/inventory/assistants">{router_prefix}/inventory/assistants</a> - List All Assistants (<a href="{router_prefix}/inventory/assistants?format=html">HTML</a> + <a href="{router_prefix}/inventory/assistants?format=json">JSON</a> + <a href="{router_prefix}/inventory/assistants?format=ui">UI</a>)</li>
    <li><a href="{router_prefix}/inventory/assistants/delete">{router_prefix}/inventory/assistants/delete</a> - Delete Assistant (<a href="{router_prefix}/inventory/assistants/delete">Docs</a>)</li>
  </ul>

  <p><a href="/">← Back to Main Page</a></p>
</body>
</html>
"""

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
  head = generate_html_head(f"{title} ({count})")
  return f"""{head}
<body>
  <h1>{title} ({count})</h1>
  {table_html}
</body>
</html>"""

def _generate_ui_response_for_vector_store_files(title: str, count: int, vector_store_id: str, files: List[Dict]) -> str:
  """
  Generate UI HTML response with action buttons for vector store files.
  
  Args:
    title: Page title
    count: Number of files
    vector_store_id: ID of the vector store
    files: List of file dictionaries
    
  Returns:
    Complete HTMX page with interactive UI
  """
  def get_file_actions(file):
    file_id = file.get('id', 'N/A')
    filename = file.get('filename', 'N/A')
    return [
      {'text': 'Remove', 'hx_method': 'delete', 'hx_endpoint': f'{router_prefix}/inventory/vectorstore_files/remove?vector_store_id={vector_store_id}&file_id={file_id}', 'hx_target': f'#file-{file_id}', 'confirm_message': f"Remove file '{filename}' from vector store? (File will remain in global storage)", 'button_class': 'btn-small btn-delete'},
      {'text': 'Delete', 'hx_method': 'delete', 'hx_endpoint': f'{router_prefix}/inventory/vectorstore_files/delete?vector_store_id={vector_store_id}&file_id={file_id}', 'hx_target': f'#file-{file_id}', 'confirm_message': f"Delete file '{filename}' from vector store AND global storage? This cannot be undone!", 'button_class': 'btn-small', 'style': 'background-color: #dc3545; color: white;'}
    ]
  
  columns = [
    {'field': 'filename', 'header': 'Filename'},
    {'field': 'id', 'header': 'ID'},
    {'field': 'created_at', 'header': 'Created At'},
    {'field': 'bytes', 'header': 'Size (bytes)', 'default': 0},
    {'field': 'status', 'header': 'Status'},
    {'field': 'actions', 'header': 'Actions', 'buttons': get_file_actions}
  ]
  
  return generate_ui_table_page(title=title, count=count, data=files, columns=columns, row_id_field='id', row_id_prefix='file', back_link=f'{router_prefix}/inventory/vectorstores?format=ui', back_text='← Back to Vector Stores')

def _generate_ui_response_for_files(title: str, count: int, files: List[Dict]) -> str:
  """
  Generate UI HTML response with delete buttons for files.
  
  Args:
    title: Page title
    count: Number of files
    files: List of file dictionaries
    
  Returns:
    Complete HTMX page with interactive UI
  """
  def get_file_actions(file):
    file_id = file.get('id', 'N/A')
    filename = file.get('filename', 'N/A')
    return [{'text': 'Delete', 'hx_method': 'delete', 'hx_endpoint': f'{router_prefix}/inventory/files/delete?file_id={file_id}', 'hx_target': f'#file-{file_id}', 'confirm_message': f"Delete file '{filename}' from global storage? This cannot be undone!", 'button_class': 'btn-small btn-delete', 'style': 'background-color: #dc3545; color: white;'}]
  
  columns = [
    {'field': 'filename', 'header': 'Filename'},
    {'field': 'id', 'header': 'ID'},
    {'field': 'created_at', 'header': 'Created At'},
    {'field': 'bytes', 'header': 'Size (bytes)', 'default': 0},
    {'field': 'purpose', 'header': 'Purpose'},
    {'field': 'actions', 'header': 'Actions', 'buttons': get_file_actions}
  ]
  
  return generate_ui_table_page(title=title, count=count, data=files, columns=columns, row_id_field='id', row_id_prefix='file', back_link='/')

def _generate_ui_response_for_assistants(title: str, count: int, assistants: List[Dict]) -> str:
  """
  Generate UI HTML response with delete buttons for assistants.
  
  Args:
    title: Page title
    count: Number of assistants
    assistants: List of assistant dictionaries
    
  Returns:
    Complete HTMX page with interactive UI
  """
  def format_description(desc):
    description_text = desc if desc else ''
    return description_text[:50] + '...' if len(description_text) > 50 else description_text
  
  def get_assistant_actions(assistant):
    assistant_id = assistant.get('id', 'N/A')
    name = assistant.get('name', 'N/A')
    return [{'text': 'Delete', 'hx_method': 'delete', 'hx_endpoint': f'{router_prefix}/inventory/assistants/delete?assistant_id={assistant_id}', 'hx_target': f'#assistant-{assistant_id}', 'confirm_message': f"Delete assistant '{name}'? This cannot be undone!", 'button_class': 'btn-small btn-delete', 'style': 'background-color: #dc3545; color: white;'}]
  
  columns = [
    {'field': 'name', 'header': 'Name'},
    {'field': 'id', 'header': 'ID'},
    {'field': 'created_at', 'header': 'Created At'},
    {'field': 'model', 'header': 'Model'},
    {'field': 'description', 'header': 'Description', 'format': format_description, 'default': ''},
    {'field': 'actions', 'header': 'Actions', 'buttons': get_assistant_actions}
  ]
  
  return generate_ui_table_page(title=title, count=count, data=assistants, columns=columns, row_id_field='id', row_id_prefix='assistant', back_link='/')

def _generate_ui_response_for_vector_stores(title: str, count: int, vector_stores: List[Dict]) -> str:
  """
  Generate UI HTML response with delete buttons for vector stores.
  
  Args:
    title: Page title
    count: Number of vector stores
    vector_stores: List of vector store dictionaries
    
  Returns:
    Complete HTMX page with interactive UI
  """
  def format_file_count(file_counts):
    return file_counts.get('total', 0) if isinstance(file_counts, dict) else 0
  
  def get_vectorstore_actions(vs):
    vs_id = vs.get('id', 'N/A')
    vs_name = vs.get('name', 'N/A')
    file_counts = vs.get('file_counts', {})
    total_files = file_counts.get('total', 0) if isinstance(file_counts, dict) else 0
    return [
      {'text': 'Files', 'onclick': f"window.location.href='{router_prefix}/inventory/vectorstore_files?vector_store_id={vs_id}&format=ui'", 'button_class': 'btn-small', 'style': 'background-color: #007bff; color: white;'},
      {'text': 'Delete', 'hx_method': 'delete', 'hx_endpoint': f'{router_prefix}/inventory/vectorstores/delete?vector_store_id={vs_id}&delete_files=false', 'hx_target': f'#vectorstore-{vs_id}', 'confirm_message': f"Delete vector store '{vs_name}'? (Files will remain in storage)", 'button_class': 'btn-small btn-delete'},
      {'text': 'Delete with Files', 'hx_method': 'delete', 'hx_endpoint': f'{router_prefix}/inventory/vectorstores/delete?vector_store_id={vs_id}&delete_files=true', 'hx_target': f'#vectorstore-{vs_id}', 'confirm_message': f"Delete vector store '{vs_name}' AND all {total_files} files? This cannot be undone!", 'button_class': 'btn-small', 'style': 'background-color: #dc3545; color: white;'}
    ]
  
  columns = [
    {'field': 'name', 'header': 'Name'},
    {'field': 'id', 'header': 'ID'},
    {'field': 'created_at', 'header': 'Created At'},
    {'field': 'file_counts', 'header': 'Files', 'format': format_file_count},
    {'field': 'actions', 'header': 'Actions', 'buttons': get_vectorstore_actions}
  ]
  
  return generate_ui_table_page(title=title, count=count, data=vector_stores, columns=columns, row_id_field='id', row_id_prefix='vectorstore', back_link='/')


@router.get('/inventory/vectorstores')
async def vectorstores(request: Request):
  """
  Endpoint to retrieve all vector stores from Azure OpenAI.
  
  Parameters:
  - format: The response format (json, html, or ui)
  - includeattributes: Comma-separated list of attributes to include in response (takes precedence over excludeattributes)
  - excludeattributes: Comma-separated list of attributes to exclude from response (ignored if includeattributes is set)
    
  Examples:
  {router_prefix}/inventory/vectorstores
  {router_prefix}/inventory/vectorstores?format=json
  {router_prefix}/inventory/vectorstores?format=ui (interactive UI with delete buttons)
  {router_prefix}/inventory/vectorstores?format=json&includeattributes=id,name,created_at
  {router_prefix}/inventory/vectorstores?format=html&excludeattributes=file_counts,metadata
  """
  function_name = 'vectorstores()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params) 
  endpoint = '/' + function_name.replace('()','')  
  endpoint_documentation = vectorstores.__doc__.replace('{router_prefix}', router_prefix)
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
    elif format == 'ui':
      # UI format with delete buttons
      html_content = _generate_ui_response_for_vector_stores('Vector Stores', len(vector_stores), vector_stores_list)
      await log_function_footer(request_data)
      return HTMLResponse(html_content)
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

@router.api_route('/inventory/vectorstores/delete', methods=['GET', 'DELETE'])
async def delete_vectorstore(request: Request):
  """
  Delete a vector store configuration.
  
  Parameters:
  - vector_store_id: ID of vector store to delete
  - delete_files: Whether to delete files from global storage (true/false, default: false)
  - format: Response format (json or html, default: html)
  
  Examples:
  DELETE {router_prefix}/inventory/vectorstores/delete?vector_store_id=vs_123
  DELETE {router_prefix}/inventory/vectorstores/delete?vector_store_id=vs_123&delete_files=true
  DELETE {router_prefix}/inventory/vectorstores/delete?vector_store_id=vs_123&format=json
  """
  function_name = 'delete_vectorstore()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')
  endpoint_documentation = delete_vectorstore.__doc__.replace('{router_prefix}', router_prefix)
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  # Display documentation if no params are provided
  if len(request_params) == 0: await log_function_footer(request_data); return HTMLResponse(documentation_HTML)
  
  format = request_params.get('format', 'html')
  vector_store_id = request_params.get('vector_store_id')
  delete_files = request_params.get('delete_files', 'false').lower() == 'true'
  
  if not vector_store_id:
    await log_function_footer(request_data)
    error_msg = "Missing vector_store_id parameter"
    if format == 'json':
      return JSONResponse({"error": error_msg}, status_code=400)
    else:
      return HTMLResponse(f"<tr><td colspan='5' class='error'>{error_msg}</td></tr>", status_code=400)
  
  try:
    if not hasattr(request.app.state, 'openai_client') or not request.app.state.openai_client:
      error_message = "OpenAI client not configured"
      log_function_output(request_data, f"ERROR: {error_message}")
      await log_function_footer(request_data)
      if format == 'json':
        return JSONResponse({"error": error_message}, status_code=500)
      else:
        return HTMLResponse(f"<tr><td colspan='5' class='error'>{error_message}</td></tr>", status_code=500)
    
    client = request.app.state.openai_client
    
    # Delete vector store
    success, message = await delete_vector_store_by_id(client, vector_store_id, delete_files, request_data)
    
    if not success:
      log_function_output(request_data, f"ERROR: {message}")
      await log_function_footer(request_data)
      if format == 'json':
        return JSONResponse({"error": message}, status_code=404 if "not found" in message.lower() else 500)
      else:
        return HTMLResponse(f"<tr><td colspan='5' class='error'>{message}</td></tr>", status_code=404 if "not found" in message.lower() else 500)
    
    log_function_output(request_data, message)
    await log_function_footer(request_data)
    
    if format == 'json':
      return JSONResponse({"message": message})
    else:
      # Return empty response to remove the row from UI
      return HTMLResponse("")
    
  except Exception as e:
    error_message = f"Error deleting vector store: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=500)
    else:
      return HTMLResponse(f"<tr><td colspan='5' class='error'>{error_message}</td></tr>", status_code=500)

@router.get('/inventory/vectorstore_files')
async def vectorstore_files(request: Request):
  """
  Endpoint to retrieve all files from a specific vector store.
  
  Parameters:
  - vector_store_id: ID of the vector store to retrieve files from (required)
  - format: The response format (json, html, or ui)
  - includeattributes: Comma-separated list of attributes to include in response (takes precedence over excludeattributes)
  - excludeattributes: Comma-separated list of attributes to exclude from response (ignored if includeattributes is set)
    
  Examples:
  {router_prefix}/inventory/vectorstore_files
  {router_prefix}/inventory/vectorstore_files?vector_store_id=vs_123&format=json
  {router_prefix}/inventory/vectorstore_files?vector_store_id=vs_123&format=html
  {router_prefix}/inventory/vectorstore_files?vector_store_id=vs_123&format=json&includeattributes=id,filename,created_at
  {router_prefix}/inventory/vectorstore_files?vector_store_id=vs_123&format=html&excludeattributes=status_details,last_error
  """
  function_name = 'vectorstore_files()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params) 
  
  endpoint = '/' + function_name.replace('()','')  
  endpoint_documentation = vectorstore_files.__doc__.replace('{router_prefix}', router_prefix)
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  # Display documentation if no params are provided
  if len(request_params) == 0: await log_function_footer(request_data); return HTMLResponse(documentation_HTML)

  format = request_params.get('format', None)
  vector_store_id = request_params.get('vector_store_id')
  include_attributes = request_params.get('includeattributes', None)
  exclude_attributes = request_params.get('excludeattributes', None)
  
  # Validate required parameter
  if not vector_store_id:
    error_message = "Missing required parameter: vector_store_id"
    log_function_output(request_data, f"ERROR: {error_message}")
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=400)
    else:
      error_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Error</title></head><body><h1>Error</h1><p>{error_message}</p></body></html>"
      return HTMLResponse(error_html, status_code=400)
  
  try:
    client = request.app.state.openai_client
    
    # Verify vector store exists
    vector_store = await try_get_vector_store_by_id(client, vector_store_id)
    if not vector_store:
      error_message = f"Vector store not found: {vector_store_id}"
      log_function_output(request_data, f"ERROR: {error_message}")
      await log_function_footer(request_data)
      if format == 'json':
        return JSONResponse({"error": error_message}, status_code=404)
      else:
        error_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Error</title></head><body><h1>Error</h1><p>{error_message}</p></body></html>"
        return HTMLResponse(error_html, status_code=404)
    
    # Get files dictionary and convert to list
    files_dict = await get_vector_store_files_with_filenames_as_dict(client, vector_store_id)
    files_list = [asdict(file) for file in files_dict.values()]
    
    # Apply datetime conversion
    convert_openai_timestamps_to_utc({"data": files_list}, request_data)
    
    # Apply attribute filtering
    files_list = include_exclude_attributes(files_list, include_attributes, exclude_attributes)
    
    if format == 'json':
      await log_function_footer(request_data)
      return JSONResponse({"data": files_list})
    elif format == 'ui':
      # UI format with action buttons
      html_content = _generate_ui_response_for_vector_store_files(
        f'Vector Store Files: {vector_store.name}',
        len(files_list),
        vector_store_id,
        files_list
      )
      await log_function_footer(request_data)
      return HTMLResponse(html_content)
    else:
      # HTML format with minimal HTMX (no buttons)
      html_content = _generate_html_response_from_object_list(
        f'Vector Store Files (vs: {vector_store_id})', 
        len(files_list), 
        files_list
      )
      await log_function_footer(request_data)
      return HTMLResponse(html_content)
      
  except Exception as e:
    error_message = f"Error retrieving vector store files: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=500)
    else:
      error_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Error</title></head><body><h1>Error</h1><p>{error_message}</p></body></html>"
      return HTMLResponse(error_html, status_code=500)

@router.api_route('/inventory/vectorstore_files/remove', methods=['GET', 'DELETE'])
async def remove_file_from_vectorstore(request: Request):
  """
  Remove a file from a vector store (file remains in global storage).
  
  Parameters:
  - vector_store_id: ID of the vector store
  - file_id: ID of the file to remove
  - format: Response format (json or html, default: html)
  
  Examples:
  DELETE {router_prefix}/inventory/vectorstore_files/remove?vector_store_id=vs_123&file_id=file_456
  DELETE {router_prefix}/inventory/vectorstore_files/remove?vector_store_id=vs_123&file_id=file_456&format=json
  """
  function_name = 'remove_file_from_vectorstore()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')
  endpoint_documentation = remove_file_from_vectorstore.__doc__.replace('{router_prefix}', router_prefix)
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  # Display documentation if no params are provided
  if len(request_params) == 0: await log_function_footer(request_data); return HTMLResponse(documentation_HTML)
  
  format = request_params.get('format', 'html')
  vector_store_id = request_params.get('vector_store_id')
  file_id = request_params.get('file_id')
  
  if not vector_store_id or not file_id:
    await log_function_footer(request_data)
    error_msg = "Missing required parameters: vector_store_id and file_id"
    if format == 'json':
      return JSONResponse({"error": error_msg}, status_code=400)
    else:
      return HTMLResponse(f"<tr><td colspan='6' class='error'>{error_msg}</td></tr>", status_code=400)
  
  try:
    client = request.app.state.openai_client
    
    # Remove file from vector store using common function
    success, message = await remove_file_from_vector_store(client, vector_store_id, file_id, request_data)
    
    await log_function_footer(request_data)
    
    if not success:
      if format == 'json':
        return JSONResponse({"error": message}, status_code=500)
      else:
        return HTMLResponse(f"<tr><td colspan='6' class='error'>{message}</td></tr>", status_code=500)
    
    if format == 'json':
      return JSONResponse({"message": message})
    else:
      # Return empty response to remove the row from UI
      return HTMLResponse("")
    
  except Exception as e:
    error_message = f"Error removing file from vector store: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=500)
    else:
      return HTMLResponse(f"<tr><td colspan='6' class='error'>{error_message}</td></tr>", status_code=500)

@router.api_route('/inventory/vectorstore_files/delete', methods=['GET', 'DELETE'])
async def delete_file_from_vectorstore(request: Request):
  """
  Delete a file from a vector store AND from global storage.
  
  Parameters:
  - vector_store_id: ID of the vector store
  - file_id: ID of the file to delete
  - format: Response format (json or html, default: html)
  
  Examples:
  DELETE {router_prefix}/inventory/vectorstore_files/delete?vector_store_id=vs_123&file_id=file_456
  DELETE {router_prefix}/inventory/vectorstore_files/delete?vector_store_id=vs_123&file_id=file_456&format=json
  """
  function_name = 'delete_file_from_vectorstore()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')
  endpoint_documentation = delete_file_from_vectorstore.__doc__.replace('{router_prefix}', router_prefix)
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  # Display documentation if no params are provided
  if len(request_params) == 0: await log_function_footer(request_data); return HTMLResponse(documentation_HTML)
  
  format = request_params.get('format', 'html')
  vector_store_id = request_params.get('vector_store_id')
  file_id = request_params.get('file_id')
  
  if not vector_store_id or not file_id:
    await log_function_footer(request_data)
    error_msg = "Missing required parameters: vector_store_id and file_id"
    if format == 'json':
      return JSONResponse({"error": error_msg}, status_code=400)
    else:
      return HTMLResponse(f"<tr><td colspan='6' class='error'>{error_msg}</td></tr>", status_code=400)
  
  try:
    client = request.app.state.openai_client
    
    # Delete file from vector store and global storage using common function
    success, message = await delete_file_from_vector_store_and_storage(client, vector_store_id, file_id, request_data)
    
    await log_function_footer(request_data)
    
    if not success:
      if format == 'json':
        return JSONResponse({"error": message}, status_code=500)
      else:
        return HTMLResponse(f"<tr><td colspan='6' class='error'>{message}</td></tr>", status_code=500)
    
    if format == 'json':
      return JSONResponse({"message": message})
    else:
      # Return empty response to remove the row from UI
      return HTMLResponse("")
    
  except Exception as e:
    error_message = f"Error deleting file: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=500)
    else:
      return HTMLResponse(f"<tr><td colspan='6' class='error'>{error_message}</td></tr>", status_code=500)

@router.get('/inventory/files')
async def files(request: Request):
  """
  Endpoint to retrieve all files from Azure OpenAI.
  
  Parameters:
  - format: The response format (json or html)
  - includeattributes: Comma-separated list of attributes to include in response (takes precedence over excludeattributes)
  - excludeattributes: Comma-separated list of attributes to exclude from response (ignored if includeattributes is set)
    
  Examples:
  {router_prefix}/inventory/files
  {router_prefix}/inventory/files?format=json
  {router_prefix}/inventory/files?format=json&includeattributes=id,filename,created_at
  {router_prefix}/inventory/files?format=html&excludeattributes=status,status_details
  """
  function_name = 'files()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')  
  endpoint_documentation = files.__doc__.replace('{router_prefix}', router_prefix)
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
    elif format == 'ui':
      # UI format with delete buttons
      html_content = _generate_ui_response_for_files('Files', len(files_list), files_dict_list)
      await log_function_footer(request_data)
      return HTMLResponse(html_content)
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

@router.api_route('/inventory/files/delete', methods=['GET', 'DELETE'])
async def delete_file(request: Request):
  """
  Delete a file from global storage.
  
  Parameters:
  - file_id: ID of the file to delete
  - format: Response format (json or html, default: html)
  
  Examples:
  DELETE {router_prefix}/inventory/files/delete?file_id=file_456
  DELETE {router_prefix}/inventory/files/delete?file_id=file_456&format=json
  """
  function_name = 'delete_file()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')
  endpoint_documentation = delete_file.__doc__.replace('{router_prefix}', router_prefix)
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  # Display documentation if no params are provided
  if len(request_params) == 0: await log_function_footer(request_data); return HTMLResponse(documentation_HTML)
  
  format = request_params.get('format', 'html')
  file_id = request_params.get('file_id')
  
  if not file_id:
    await log_function_footer(request_data)
    error_msg = "Missing required parameter: file_id"
    if format == 'json':
      return JSONResponse({"error": error_msg}, status_code=400)
    else:
      return HTMLResponse(f"<tr><td colspan='6' class='error'>{error_msg}</td></tr>", status_code=400)
  
  try:
    client = request.app.state.openai_client
    
    # Delete file using common function
    success, message = await delete_file_by_id(client, file_id, request_data)
    
    await log_function_footer(request_data)
    
    if not success:
      if format == 'json':
        return JSONResponse({"error": message}, status_code=500)
      else:
        return HTMLResponse(f"<tr><td colspan='6' class='error'>{message}</td></tr>", status_code=500)
    
    if format == 'json':
      return JSONResponse({"message": message})
    else:
      # Return empty response to remove the row from UI
      return HTMLResponse("")
    
  except Exception as e:
    error_message = f"Error deleting file: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=500)
    else:
      return HTMLResponse(f"<tr><td colspan='6' class='error'>{error_message}</td></tr>", status_code=500)

@router.get('/inventory/assistants')
async def assistants(request: Request):
  """
  Endpoint to retrieve all assistants from Azure OpenAI.
  
  Parameters:
  - format: The response format (json or html)
  - includeattributes: Comma-separated list of attributes to include in response (takes precedence over excludeattributes)
  - excludeattributes: Comma-separated list of attributes to exclude from response (ignored if includeattributes is set)
    
  Examples:
  {router_prefix}/inventory/assistants
  {router_prefix}/inventory/assistants?format=json
  {router_prefix}/inventory/assistants?format=json&includeattributes=id,name,model,created_at
  {router_prefix}/inventory/assistants?format=html&excludeattributes=metadata,tools,description
  """
  function_name = 'assistants()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')  
  endpoint_documentation = assistants.__doc__.replace('{router_prefix}', router_prefix)
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
    elif format == 'ui':
      # UI format with delete buttons
      html_content = _generate_ui_response_for_assistants('Assistants', len(assistants_list), assistants_dict_list)
      await log_function_footer(request_data)
      return HTMLResponse(html_content)
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

@router.api_route('/inventory/assistants/delete', methods=['GET', 'DELETE'])
async def delete_assistant(request: Request):
  """
  Delete an assistant.
  
  Parameters:
  - assistant_id: ID of the assistant to delete
  - format: Response format (json or html, default: html)
  
  Examples:
  DELETE {router_prefix}/inventory/assistants/delete?assistant_id=asst_456
  DELETE {router_prefix}/inventory/assistants/delete?assistant_id=asst_456&format=json
  """
  function_name = 'delete_assistant()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')
  endpoint_documentation = delete_assistant.__doc__.replace('{router_prefix}', router_prefix)
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  # Display documentation if no params are provided
  if len(request_params) == 0: await log_function_footer(request_data); return HTMLResponse(documentation_HTML)
  
  format = request_params.get('format', 'html')
  assistant_id = request_params.get('assistant_id')
  
  if not assistant_id:
    await log_function_footer(request_data)
    error_msg = "Missing required parameter: assistant_id"
    if format == 'json':
      return JSONResponse({"error": error_msg}, status_code=400)
    else:
      return HTMLResponse(f"<tr><td colspan='6' class='error'>{error_msg}</td></tr>", status_code=400)
  
  try:
    client = request.app.state.openai_client
    
    # Delete assistant using common function
    success, message = await delete_assistant_by_id(client, assistant_id, request_data)
    
    await log_function_footer(request_data)
    
    if not success:
      if format == 'json':
        return JSONResponse({"error": message}, status_code=500)
      else:
        return HTMLResponse(f"<tr><td colspan='6' class='error'>{message}</td></tr>", status_code=500)
    
    if format == 'json':
      return JSONResponse({"message": message})
    else:
      # Return empty response to remove the row from UI
      return HTMLResponse("")
    
  except Exception as e:
    error_message = f"Error deleting assistant: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=500)
    else:
      return HTMLResponse(f"<tr><td colspan='6' class='error'>{error_message}</td></tr>", status_code=500)
