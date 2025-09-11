import json, logging, os
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from common_openai_functions import *
from common_openai_functions import CoaiSearchParams
from utils import *

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

# Convert search_results to data object as required by /query endpoint with array of sources { "data": "<text>", "source": "<url>", "metadata": { <attributes> } }
def build_data_object(query, search_results, response, metadata_cache):
  sources = []
  for result in search_results:
    file_id = result.file_id
    metadata = metadata_cache.get(file_id)
    if metadata : metadata = metadata.copy()
    # remove 'source' from metadata because this will be added as the 'source' field separately
    if metadata:
      source_url = metadata.get('source', f'{result.filename}')
      metadata.pop('source', None)
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
  request_number = request_data["request_number"]
  function_name = '_internal_request_to_llm()'
  query = request_params.get('query', '')
  vsid = request_params.get('vsid', None)
  max_num_results = int(request_params.get('results', config.SEARCH_DEFAULT_MAX_NUM_RESULTS))
  temperature = config.SEARCH_DEFAULT_TEMPERATURE
  instructions = request_params.get('instructions', config.SEARCH_DEFAULT_INSTRUCTIONS)

  error_message = ""
  data = {'query': query, 'answer': '', 'source_markers': ['【', '】'], 'sources': []}

  # Do not throw errors on empty messages. Instead return empty 'data' result
  if query:
    log_function_output(request_data, f"Query: {sanitize_queries_and_responses(truncate_string(query,80))}")
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
      log_function_output(request_data, f"ERROR: '{vsid}': {str(e)}")
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
    log_function_output(request_data, f"Response: {sanitize_queries_and_responses(remove_linebreaks(truncate_string(output_text,80)))}")
    search_results_count = len(search_results)
    log_function_output(request_data, f"status='{openai_response.status}', tool_choice='{openai_response.tool_choice}', search_results_count={search_results_count}, input_tokens={openai_response.usage.input_tokens}, output_tokens={openai_response.usage.output_tokens}")
    data = build_data_object(query, search_results, openai_response, request.app.state.metadata_cache)

  response = JSONResponse({'data': data})
  return response, data, error_message

# internal query endpoint function
async def _internal_query(function_name: str, request: Request, request_data: dict) -> JSONResponse:
  request_number = request_data["request_number"]

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
      output = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>[QUERY]</title></head><body>[TABLE_HTML]</body></html>""".replace('[QUERY]', truncate_string(query,50)).replace('[TABLE_HTML]', table_html)
      output = HTMLResponse(output)

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

