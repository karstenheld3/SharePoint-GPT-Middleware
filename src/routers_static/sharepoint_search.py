import json, logging, os, re
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from routers_v1.common_openai_functions_v1 import CoaiSearchParams, get_search_results_using_responses_api, get_search_results_using_search_api, try_get_vector_store_by_id
from routers_v1.router_crawler_functions import is_files_metadata_v2_format, convert_file_metadata_item_from_v2_to_v3
from hardcoded_config import CRAWLER_HARDCODED_CONFIG
from common_utils import convert_to_nested_html_table, remove_linebreaks
from routers_v1.common_logging_functions_v1 import log_function_footer, log_function_header, log_function_output, log_function_footer_sync, sanitize_queries_and_responses, truncate_string

router = APIRouter()

# Configuration will be injected from app.py
config = None

def set_config(app_config):
  """Set the configuration for SharePoint Search."""
  global config
  config = app_config

logger = logging.getLogger(__name__)

# Cache for vector store IDs
found_vector_store_ids = {}

def build_domains_and_metadata_cache(config, system_info, initialization_errors):
  log_data = log_function_header("build_domains_and_metadata_cache")
  metadata_cache = {}; domains = []
  
  try:
    domains_folder_path = os.path.join(system_info.PERSISTENT_STORAGE_PATH, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER)
    log_function_output(log_data, f"Domains folder path: {domains_folder_path}")
    
    if not os.path.exists(domains_folder_path):
      error_msg = f"Domains folder not found: {domains_folder_path}"
      log_function_output(log_data, f"ERROR: {error_msg}")
      initialization_errors.append({"component": "SharePoint Data Loading", "error": error_msg})
      log_function_footer_sync(log_data)
      return domains, metadata_cache
    
    # Iterate through each domain folder (VMS, HOIT, etc.)
    try:
      domain_folder_names = os.listdir(domains_folder_path)
      log_function_output(log_data, f"Found {len(domain_folder_names)} items in domains folder")
    except Exception as e:
      error_msg = f"Failed to list domains folder: {str(e)}"
      log_function_output(log_data, f"ERROR: {error_msg}")
      initialization_errors.append({"component": "SharePoint Data Loading", "error": error_msg})
      log_function_footer_sync(log_data)
      return domains, metadata_cache
    
    for domain_folder_name in domain_folder_names:
      domain_folder_path = os.path.join(domains_folder_path, domain_folder_name)
      
      # Skip folders that start with an underscore (_)
      if not os.path.isdir(domain_folder_path) or domain_folder_name.startswith('_'):
        log_function_output(log_data, f"Skipping: {domain_folder_name}")
        continue
      
      log_function_output(log_data, f"Processing domain folder: {domain_folder_name}")
      
      # Load domain.json
      domain_json_path = os.path.join(domain_folder_path, CRAWLER_HARDCODED_CONFIG.DOMAIN_JSON)
      if os.path.exists(domain_json_path):
        file_content = None
        try:
          for encoding in ['utf-8', 'utf-16', 'utf-16-le', 'utf-16-be']:
            try:
              with open(domain_json_path, 'r', encoding=encoding) as f:
                file_content = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
              continue
          
          if file_content is None:
            error_msg = f"domain.json for {domain_folder_name} has unsupported encoding"
            log_function_output(log_data, f"ERROR: {error_msg}")
            initialization_errors.append({"component": "SharePoint Data Loading", "error": error_msg})
            continue
          
          if not file_content.strip():
            error_msg = f"domain.json for {domain_folder_name} is empty (file size: {os.path.getsize(domain_json_path)} bytes)"
            log_function_output(log_data, f"ERROR: {error_msg}")
            initialization_errors.append({"component": "SharePoint Data Loading", "error": error_msg})
            continue
          
          domain_data = json.loads(file_content)
          if domain_data.get('vector_store_id') != config.SEARCH_DEFAULT_GLOBAL_VECTOR_STORE_ID:
            domain_name = domain_data.get('name', domain_folder_name)
            domain_description = domain_data.get('description', '')
            domains[:] = [d for d in domains if d['name'] != domain_name]
            domains.append({"name": domain_name, "description": domain_description})
            log_function_output(log_data, f"Added domain: {domain_name}")
          else:
            log_function_output(log_data, f"Skipping global vector store domain: {domain_folder_name}")
        except json.JSONDecodeError as e:
          error_msg = f"Invalid JSON in domain.json for {domain_folder_name}: {str(e)} (file size: {os.path.getsize(domain_json_path)} bytes, first 100 chars: {file_content[:100]!r})"
          log_function_output(log_data, f"ERROR: {error_msg}")
          initialization_errors.append({"component": "SharePoint Data Loading", "error": error_msg})
        except Exception as e:
          error_msg = f"Failed to load domain.json for {domain_folder_name}: {str(e)}"
          log_function_output(log_data, f"ERROR: {error_msg}")
          initialization_errors.append({"component": "SharePoint Data Loading", "error": error_msg})
      
      # Load files_metadata.json
      files_metadata_json_path = os.path.join(domain_folder_path, CRAWLER_HARDCODED_CONFIG.FILES_METADATA_JSON)
      if os.path.exists(files_metadata_json_path):
        file_content = None
        try:
          for encoding in ['utf-8', 'utf-16', 'utf-16-le', 'utf-16-be']:
            try:
              with open(files_metadata_json_path, 'r', encoding=encoding) as f:
                file_content = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
              continue
          
          if file_content is None:
            error_msg = f"files_metadata.json for {domain_folder_name} has unsupported encoding"
            log_function_output(log_data, f"ERROR: {error_msg}")
            initialization_errors.append({"component": "SharePoint Data Loading", "error": error_msg})
            continue
          
          if not file_content.strip():
            error_msg = f"files_metadata.json for {domain_folder_name} is empty (file size: {os.path.getsize(files_metadata_json_path)} bytes)"
            log_function_output(log_data, f"ERROR: {error_msg}")
            initialization_errors.append({"component": "SharePoint Data Loading", "error": error_msg})
            continue
          
          # Clean invalid control characters (tabs, etc.) from JSON string values
          # This handles cases where openai_file_id or other fields have embedded tabs
          file_content = re.sub(r':\s*"([^"]*)\t([^"]*)"', r': "\1\2"', file_content)
          
          files_metadata = json.loads(file_content)
          
          # Detect format using first item and convert if needed
          if files_metadata and len(files_metadata) > 0:
            first_item = files_metadata[0]
            is_v2 = is_files_metadata_v2_format(first_item)
            
            if is_v2:
              log_function_output(log_data, f"Detected V2 format for {domain_folder_name}, converting to V3...")
              files_metadata = [convert_file_metadata_item_from_v2_to_v3(item) for item in files_metadata]
            
            # Add all items to cache (now all in V3 format)
            files_added = 0
            for file_data in files_metadata:
              file_id = file_data.get('openai_file_id', '').strip()
              if file_id:
                metadata_cache[file_id] = file_data
                files_added += 1
            
            log_function_output(log_data, f"Added {files_added} file metadata entries from {domain_folder_name}")
          else:
            log_function_output(log_data, f"No file metadata entries found in {domain_folder_name}")
        except json.JSONDecodeError as e:
          error_msg = f"Invalid JSON in files_metadata.json for {domain_folder_name}: {str(e)} (file size: {os.path.getsize(files_metadata_json_path)} bytes, first 100 chars: {file_content[:100]!r})"
          log_function_output(log_data, f"ERROR: {error_msg}")
          initialization_errors.append({"component": "SharePoint Data Loading", "error": error_msg})
        except Exception as e:
          error_msg = f"Failed to load files_metadata.json for {domain_folder_name}: {str(e)}"
          log_function_output(log_data, f"ERROR: {error_msg}")
          initialization_errors.append({"component": "SharePoint Data Loading", "error": error_msg})
    
    log_function_output(log_data, f"Total domains loaded: {len(domains)}, Total metadata entries: {len(metadata_cache)}")
              
  except Exception as e:
    error_msg = f"Unexpected error in build_domains_and_metadata_cache: {str(e)}"
    log_function_output(log_data, f"ERROR: {error_msg}")
    initialization_errors.append({"component": "SharePoint Data Loading", "error": error_msg})
  
  log_function_footer_sync(log_data)
  return domains, metadata_cache


# Convert search_results to data object as required by /query endpoint with array of sources { "data": "<text>", "source": "<url>", "metadata": { <attributes> } }
def build_data_object(query, search_results, response, metadata_cache):
  sources = []
  for result in search_results:
    file_id = result.file_id
    metadata = metadata_cache.get(file_id)
    if metadata : metadata = metadata.copy()
    # Get URL from V3 format metadata and remove it before adding to metadata dict
    # V3 format uses 'url' field, which maps to the output 'source' field
    if metadata:
      source_url = metadata.get('url', f'{result.filename}')
      metadata.pop('url', None)
    else:
      source_url = f'[NO_METADATA_FOR_THIS_VECTOR_STORE]'
    source = {
      "data": result.content[0].text if result.content else ""
      ,"source": source_url
      ,"metadata": {"file_id": file_id, "score": result.score, **(result.attributes or {}), **(metadata or {})}
    }
    sources.append(source)
  data = {
    "query": query
    ,"answer": response.output_text if response else ""
    ,"source_markers": ["【", "】"]
    ,"sources": sources
  }
  return data

# Internal query function (used by /query and /query2) that returns a JSON response, the original data object and an error message (if any)
async def _internal_request_to_llm(request: Request, request_params: dict, request_data: dict) -> tuple[JSONResponse, Any, str]:
  query = request_params.get('query', '')
  vsid = request_params.get('vsid', None)
  max_num_results = int(request_params.get('results', config.SEARCH_DEFAULT_MAX_NUM_RESULTS))
  temperature = config.SEARCH_DEFAULT_TEMPERATURE

  error_message = ""
  data = {'query': query, 'answer': '', 'source_markers': ['【', '】'], 'sources': []}

  # Do not throw errors on empty messages. Instead return empty 'data' result
  if query:
    truncate_length = 200 if config.LOG_QUERIES_AND_RESPONSES else 5
    log_function_output(request_data, f"Query: {sanitize_queries_and_responses(truncate_string(query, truncate_length))}")
    if not vsid: vsid = config.SEARCH_DEFAULT_GLOBAL_VECTOR_STORE_ID

    # try to get the vector store (with caching)
    vs = None
    if vsid in found_vector_store_ids:
      vs = found_vector_store_ids[vsid]
    else:
      vs = await try_get_vector_store_by_id(request.app.state.openai_client, vsid)
      if vs is not None:
        found_vector_store_ids[vsid] = vs
        log_function_output(request_data, f"VectorStoreCache - Added '{vs.name}' (id='{vsid}')")
    
    if vs is None:
      error_message = f"ERROR: Vector store '{vsid}' not found!"
      log_function_output(request_data, error_message)
      fake_search_results = []
      data = build_data_object(query, fake_search_results, None, request.app.state.metadata_cache)
      return JSONResponse({'error': error_message}), data, error_message

    # Select the appropriate model based on service type
    model_name = config.AZURE_OPENAI_DEFAULT_MODEL_DEPLOYMENT_NAME if config.OPENAI_SERVICE_TYPE.lower() == "azure_openai" else config.OPENAI_DEFAULT_MODEL_NAME
    
    log_function_output(request_data, f"service_type='{config.OPENAI_SERVICE_TYPE}', model='{model_name}', vs '{vs.name}' (id='{vsid}'), max_num_results={max_num_results}, temperature={temperature}")
    
    try:
      # The OpenAI client automatically retries on 429 Rate Limit errors with 2 retries
      search_params = CoaiSearchParams(query=query, max_num_results=max_num_results)
      if config.OPENAI_SERVICE_TYPE.lower() == "azure_openai":
        search_results, openai_response = await get_search_results_using_responses_api(request.app.state.openai_client, search_params, vsid, model_name, config.SEARCH_DEFAULT_INSTRUCTIONS)
      else:
        search_results, openai_response = await get_search_results_using_search_api(request.app.state.openai_client, search_params, vsid)
    except Exception as e:
      # If the search fails, try to refresh the vector store cache
      log_function_output(request_data, f"{str(e)}")
      vs_refreshed = await try_get_vector_store_by_id(request.app.state.openai_client, vsid)
      if vs_refreshed:
        # Vector store exists, update cache
        found_vector_store_ids[vsid] = vs_refreshed
      else:
        # Vector store no longer exists, remove from cache
        if vsid in found_vector_store_ids:
          del found_vector_store_ids[vsid]
          log_function_output(request_data, f"VectorStoreCache - Removed '{vsid}' from cache. Vector store no longer exists!")
          error_message = f"ERROR: Vector store '{vsid}' no longer exists!"
        else: 
          error_message = f"ERROR: {str(e)}"
        log_function_output(request_data, error_message)
      fake_search_results = []
      data = build_data_object(query, fake_search_results, None, request.app.state.metadata_cache)
      return JSONResponse({'error': error_message}), data, error_message
    
    output_text = openai_response.output_text
    log_function_output(request_data, f"Response: {sanitize_queries_and_responses(remove_linebreaks(truncate_string(output_text, truncate_length)))}")
    search_results_count = len(search_results)
    log_function_output(request_data, f"status='{openai_response.status}', tool_choice='{openai_response.tool_choice}', search_results_count={search_results_count}, input_tokens={openai_response.usage.input_tokens}, output_tokens={openai_response.usage.output_tokens}")
    data = build_data_object(query, search_results, openai_response, request.app.state.metadata_cache)

  response = JSONResponse({'data': data})
  return response, data, error_message

# internal query endpoint function
async def _internal_query(function_name: str, request: Request, request_data: dict) -> JSONResponse:

  # Get request data and validate
  message = ""
  try: 
    request_object = await request.json()
    if not request_object.get('data'): 
      message = "Missing 'data' attribute in request JSON." 
    if message != "":
      log_function_output(request_data, f"Error: {message}")
      return JSONResponse(content={'error': f'{message}'}, status_code=400, headers={'Content-Type': 'application/json'})

    request_params = request_object['data']

    response, data, error_message = await _internal_request_to_llm(request, request_params, request_data)

    if error_message:
      log_function_output(request_data, f"Error: {error_message}")
      return JSONResponse(content={'error': error_message}, status_code=400, headers={'Content-Type': 'application/json'})
    else:
      return response
  except Exception as e:
    logging.exception("error in SP search tool", exc_info=e)
    return JSONResponse(content={'error': "error in SP search tool"})

# Internal function that also returns HTML for testing
async def _internal_query2(request: Request, request_params, function_name: str, request_data: dict) -> Response:
  """
  Endpoint parameters:
  - query: The search query
  - vsid: The vector store id. Default: [SEARCH_DEFAULT_GLOBAL_VECTOR_STORE_ID]
  - results: The maximum number of results. Default: [SEARCH_DEFAULT_MAX_NUM_RESULTS]
  - instructions: The instructions for the model. Default: [SEARCH_DEFAULT_INSTRUCTIONS]
  - format: The response format (json or html). Default: html
    
  Examples:
  /query2?query=What is HMS&vsid=vs_4hoDNrRzXuPPiPPojHDJNvqa
  /query2?query=Who is Arilena Drovik&vsid=vs_MQlkBy0gAOQtZLJfIsaz8or5&format=json
  """
  endpoint = '/' + function_name.replace('()','')  
  endpoint_documentation = _internal_query2.__doc__.replace('[SEARCH_DEFAULT_GLOBAL_VECTOR_STORE_ID]', str(config.SEARCH_DEFAULT_GLOBAL_VECTOR_STORE_ID)).replace('[SEARCH_DEFAULT_MAX_NUM_RESULTS]', str(config.SEARCH_DEFAULT_MAX_NUM_RESULTS)).replace('[SEARCH_DEFAULT_INSTRUCTIONS]', str(config.SEARCH_DEFAULT_INSTRUCTIONS))
  documentation_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>[ENDPOINT] - Documentation</title></head><body><pre>[DOCUMENTATION]</pre></body></html>""".replace('[ENDPOINT]', endpoint).replace('[DOCUMENTATION]', endpoint_documentation)

  format = request_params.get('format', 'html') 
  query = request_params.get('query', '')
  output = ""

  # display documentation if no params are provided
  if len(request_params) == 0:
    output = HTMLResponse(documentation_HTML)
    error_message = ""
  else:
    response, data, error_message = await _internal_request_to_llm(request, request_params, request_data)
    if format == 'json':
      if error_message:
        output = JSONResponse({"error": error_message})
      else:
        output = JSONResponse({"data": data})
    else:
      if error_message:
        table_html = error_message
      else:
        # For HTML response, convert the data dict to HTML table and wrap in proper HTML document
        table_html = convert_to_nested_html_table(data)
      html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
      <title>SharePoint Search Query Results</title>
      <link rel='stylesheet' href='/static/css/styles.css'>
      <script src='/static/js/htmx.js'></script>
      </head><body>
      <h1>{truncate_string(query,50)}</h1>
      {table_html}
      </body></html>
      """
      output = HTMLResponse(html)

  return output

# ----------------------------------------------------- /describe ----------------------------------------------------
@router.post('/describe')
async def describe(request: Request):
  """Describe Endpoint: Returns metadata describing your SharePoint content search tool, including available domains and content root"""
  function_name = 'describe()'
  request_data = log_function_header(function_name)
  
  # Prepare response
  response = {
    'data': {
      'description': 'This tool can search the content of SharePoint documents.',
      'domains': request.app.state.domains,
      'content_root': config.SEARCH_DEFAULT_SHAREPOINT_ROOT_URL
      # 'favicon': 'AAABAAAIACoJQAANgA...APgfAAA='  # base64, optional
    }
  }

  await log_function_footer(request_data)
  return JSONResponse(content=response, status_code=200)

@router.get('/describe2')
async def describe2(request: Request):
  """
  Describe Endpoint: Returns metadata describing your SharePoint content search tool, including available domains and content root
  
  Parameters:
  - format: The response format (json or html). Default: html
    
  Examples:
  /describe2
  /describe2?format=json
  /describe2?format=html
  """
  function_name = 'describe2()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')  
  endpoint_documentation = describe2.__doc__
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  
  format = request_params.get('format', 'html')
  
  # Display documentation if no params are provided
  if len(request_params) == 0:
    await log_function_footer(request_data)
    return HTMLResponse(documentation_HTML)
  
  # Prepare response data
  response_data = {
    'data': {
      'description': 'This tool can search the content of SharePoint documents.',
      'domains': request.app.state.domains,
      'content_root': config.SEARCH_DEFAULT_SHAREPOINT_ROOT_URL
    }
  }
  
  await log_function_footer(request_data)
  
  if format == 'json':
    return JSONResponse(content=response_data, status_code=200)
  else:
    # HTML format using nested table utility
    title = "SharePoint Search Tool Description"
    table_html = convert_to_nested_html_table(response_data['data'])
    html_content = f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'><title>{title}</title>
  <link rel='stylesheet' href='/static/css/styles.css'>
  <script src='/static/js/htmx.js'></script>
</head><body>{table_html}</body></html>"""
    
    return HTMLResponse(html_content)


# ----------------------------------------------------- /query -------------------------------------------------------
@router.post('/query')
async def query(request: Request):
  function_name = 'query()'
  request_data = log_function_header(function_name)
  response = await _internal_query(function_name, request, request_data)
  await log_function_footer(request_data)
  return response

# ----------------------------------------------------- /query2 ------------------------------------------------------
@router.get('/query2')
async def query2(request: Request):
  function_name = 'query2()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  retVal = await _internal_query2(request, request_params, function_name, request_data)
  await log_function_footer(request_data)
  return retVal

