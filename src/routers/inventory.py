import datetime, json, logging, os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse

from common_openai_functions import get_all_vector_stores
from utils import log_function_header, log_function_footer, log_function_output, convert_to_html_table

router = APIRouter()

# Configuration will be injected from app.py
config = None

logger = logging.getLogger(__name__)

def set_config(app_config):
  """Set the configuration for Inventory management."""
  global config
  config = app_config


def convert_vector_stores_to_dict(vector_stores):
  """Convert vector stores list to dictionary format."""
  if not vector_stores: return []
  
  retVal = []
  for vs in vector_stores:
    # Handle file_counts serialization
    file_counts = getattr(vs, 'file_counts', {})
    if hasattr(file_counts, '__dict__'):
      file_counts = file_counts.__dict__
    elif not isinstance(file_counts, dict):
      file_counts = str(file_counts)
    
    # Handle created_at serialization
    created_at = getattr(vs, 'created_at', None)
    if created_at:
      try: created_at2 = datetime.datetime.fromtimestamp(float(created_at)).isoformat()
      except Exception as e:
        logger.warning(f"Failed to convert timestamp {created_at}: {e}")
        created_at2 = str(created_at)
    else:
      created_at2 = None
    
    vs_dict = {
      'id': vs.id,
      'name': getattr(vs, 'name', None),
      'status': getattr(vs, 'status', None),
      'file_counts': file_counts,
      'usage_bytes': getattr(vs, 'usage_bytes', 0),
      'created_at': created_at2
    }
    retVal.append(vs_dict)
  
  return retVal


@router.get('/vectorstores')
async def vectorstores(request: Request):
  """
  Endpoint to retrieve all vector stores from Azure OpenAI.
  
  Parameters:
  - format: The response format (json or html)
    
  Examples:
  /vectorstores
  /vectorstores?format=json
  """
  function_name = 'vectorstores()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')  
  endpoint_documentation = vectorstores.__doc__
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"

  format = request_params.get('format', None)
  
  # Display documentation if no params are provided
  if len(request_params) == 0:
    await log_function_footer(request_data)
    return HTMLResponse(documentation_HTML)
  
  try:
    client = request.app.state.openai_client
    vector_stores = await get_all_vector_stores(client)
    
    if format == 'json':
      # Convert vector stores to serializable format
      retVal = convert_vector_stores_to_dict(vector_stores)
      await log_function_footer(request_data)
      return JSONResponse({"data": retVal})
    else:
      # HTML format - now uses array of dicts directly
      vector_stores_list = convert_vector_stores_to_dict(vector_stores)
      table_html = convert_to_html_table(vector_stores_list)
      html_content = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Vector Stores</title></head><body><h1>Vector Stores ({len(vector_stores)} found)</h1>{table_html}</body></html>"
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

