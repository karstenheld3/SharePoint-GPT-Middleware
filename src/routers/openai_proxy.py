import os
import json
import uuid
import httpx
import logging
import datetime
import asyncio
from typing import Any, Dict, Optional
from fastapi import APIRouter, Request, HTTPException, Header, File, UploadFile, Form
from fastapi.responses import StreamingResponse, Response, HTMLResponse
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from utils import *

router = APIRouter()

# Configuration will be injected from app.py
config = None
token_provider = None

logger = logging.getLogger(__name__)

def set_config(app_config):
  """Set the configuration and initialize Azure AD credentials if needed."""
  global config, token_provider
  config = app_config
  
  # Initialize Azure AD credentials if needed
  if config.OPENAI_SERVICE_TYPE == "azure_openai" and not config.AZURE_OPENAI_USE_KEY_AUTHENTICATION:
    try:
      cred = DefaultAzureCredential()
      token_provider = get_bearer_token_provider(cred, "https://cognitiveservices.azure.com/.default")
    except Exception as e:
      logger.error(f"Failed to initialize Azure AD credentials: {e}")
      token_provider = None

async def proxy_request(request: Request, target_path: str, method: str = "POST", files: Optional[Dict[str, Any]] = None, timeout_seconds: Optional[float] = None) -> Any:
  """Proxy requests to OpenAI/Azure OpenAI Service while maintaining 1:1 API compatibility."""
  log_data = log_function_header("proxy_request")
  # Per-call HTTP timeout (defaults to httpx's default if None)
  http_timeout = httpx.Timeout(timeout_seconds) if timeout_seconds else httpx.Timeout(300.0)
  # Validate configuration
  if config.OPENAI_SERVICE_TYPE == "azure_openai":
    if not config.AZURE_OPENAI_ENDPOINT:
      raise HTTPException(status_code=500, detail="Azure OpenAI endpoint not configured")
    if config.AZURE_OPENAI_USE_KEY_AUTHENTICATION and not config.AZURE_OPENAI_API_KEY:
      raise HTTPException(status_code=500, detail="Azure OpenAI API key not configured")
    if not config.AZURE_OPENAI_USE_KEY_AUTHENTICATION and not token_provider:
      raise HTTPException(status_code=500, detail="Azure AD authentication failed")
  else:
    if not config.OPENAI_API_KEY:
      raise HTTPException(status_code=500, detail="OpenAI API key not configured")
  
  # Construct target URL
  if config.OPENAI_SERVICE_TYPE == "azure_openai":
    base = config.AZURE_OPENAI_ENDPOINT.rstrip('/')
    if "/openai" not in base:
      base = f"{base}/openai"
    target_url = f"{base}/{target_path.lstrip('/')}"
    if "api-version" not in target_url:
      separator = "&" if "?" in target_url else "?"
      target_url += f"{separator}api-version={config.AZURE_OPENAI_API_VERSION}"
  else:
    target_url = f"https://api.openai.com/v1/{target_path.lstrip('/')}"
  
  # Prepare headers
  headers: Dict[str, str] = {}
  if config.OPENAI_SERVICE_TYPE == "azure_openai":
    if config.AZURE_OPENAI_USE_KEY_AUTHENTICATION:
      headers["api-key"] = config.AZURE_OPENAI_API_KEY
    else:
      token = token_provider()
      headers["Authorization"] = f"Bearer {token}"
  else:
    headers["Authorization"] = f"Bearer {config.OPENAI_API_KEY}"
    if config.OPENAI_ORGANIZATION:
      headers["OpenAI-Organization"] = config.OPENAI_ORGANIZATION
  
  # Add OpenAI-Beta header for assistants API endpoints
  if "assistants" in target_path:
    headers["OpenAI-Beta"] = "assistants=v2"
  
  # Copy incoming headers except hop-by-hop and auth; let our auth override
  hop_by_hop = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade", "host", "content-length", "authorization"}
  for header_name, header_value in request.headers.items():
    lname = header_name.lower()
    if lname not in hop_by_hop and lname not in ["api-key"]:
      # do not overwrite our auth headers
      if lname not in {"authorization", "openai-organization"}:
        headers[header_name] = header_value
  
  try:
    # Pre-request diagnostic logging
    logger.info(f"Proxying {method} -> {target_url}")
    async with httpx.AsyncClient(timeout=http_timeout) as client:
      _start = log_data.get("start_time", datetime.datetime.now())
      if files:
        # Handle multipart/form-data for file uploads
        response = await client.request(method=method, url=target_url, files=files, headers=headers)
      else:
        # Pass through body and content-type as-is
        body = await request.body()
        response = await client.request(method=method, url=target_url, content=body, headers=headers)
      _elapsed_milliseconds = int((datetime.datetime.now() - _start).total_seconds() * 1000)
      service_type = "Azure OpenAI" if config.OPENAI_SERVICE_TYPE == "azure_openai" else "OpenAI"
      auth_type = "Key" if config.AZURE_OPENAI_USE_KEY_AUTHENTICATION else "Token"
      msg = f"Proxied {method} {target_path} -> {response.status_code} [{service_type} {auth_type}]"
      log_function_output(log_data, msg)
      
      # Handle streaming responses
      if response.headers.get("content-type", "").startswith("text/event-stream"):
        retVal = StreamingResponse(content=response.aiter_bytes(), status_code=response.status_code, headers=dict(response.headers), media_type="text/event-stream")
        return (retVal, _elapsed_milliseconds)
      
      # Pass through raw bytes for non-streaming
      media_type = response.headers.get("content-type")
      retVal = Response(content=response.content, status_code=response.status_code, headers=dict(response.headers), media_type=media_type)
      return (retVal, _elapsed_milliseconds)
      
  except httpx.RequestError as e:
    logger.error(f"Request error when proxying to OpenAI: {e}")
    raise HTTPException(status_code=502, detail=f"Error connecting to {config.OPENAI_SERVICE_TYPE}")
  except Exception as e:
    logger.error(f"Unexpected error when proxying to OpenAI: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
  finally:
    await log_function_footer(log_data)

# ============================================================================
# RESPONSES API
# ============================================================================

@router.post("/responses")
async def create_response(request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Responses API - Create Response. Mirrors: POST /responses"""
  log_data = log_function_header("create_response")
  try:
    target_path = f"responses?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "POST")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.get("/responses")
async def list_responses(request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Responses API - List Responses. Mirrors: GET /responses"""
  log_data = log_function_header("list_responses")
  try:
    target_path = f"responses?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "GET")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.get("/responses/{response_id}")
async def get_response(response_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Responses API - Get Response. Mirrors: GET /responses/{response_id}"""
  log_data = log_function_header("get_response")
  try:
    target_path = f"responses/{response_id}?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "GET")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.delete("/responses/{response_id}")
async def delete_response(response_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Responses API - Delete Response. Mirrors: DELETE /responses/{response_id}"""
  log_data = log_function_header("delete_response")
  try:
    target_path = f"responses/{response_id}?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "DELETE")
    return retVal
  finally:
    await log_function_footer(log_data)

# ============================================================================
# FILES API
# ============================================================================

@router.post("/files")
async def upload_file(file: UploadFile = File(...), purpose: str = Form(...), api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Files API - Upload File. Mirrors: POST /files"""
  log_data = log_function_header("upload_file")
  try:
    files = {"file": (file.filename, await file.read(), file.content_type), "purpose": (None, purpose)}
    
    # Create a dummy request for the proxy function
    class DummyRequest:
      async def body(self): return b""
      @property
      def headers(self): return {}
    
    dummy_request = DummyRequest()
    target_path = f"files?api-version={api_version}" if config.OPENAI_SERVICE_TYPE == "azure_openai" else "files"
    retVal, _milliseconds = await proxy_request(dummy_request, target_path, "POST", files=files)
    return retVal
  finally:
    await log_function_footer(log_data)

@router.get("/files")
async def list_files(request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Files API - List Files. Mirrors: GET /files"""
  log_data = log_function_header("list_files")
  try:
    target_path = f"files?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "GET")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.get("/files/{file_id}")
async def get_file(file_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Files API - Get File. Mirrors: GET /files/{file_id}"""
  log_data = log_function_header("get_file")
  try:
    target_path = f"files/{file_id}?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "GET")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.delete("/files/{file_id}")
async def delete_file(file_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Files API - Delete File. Mirrors: DELETE /files/{file_id}"""
  log_data = log_function_header("delete_file")
  try:
    target_path = f"files/{file_id}?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "DELETE")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.get("/files/{file_id}/content")
async def get_file_content(file_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Files API - Get File Content. Mirrors: GET /files/{file_id}/content"""
  log_data = log_function_header("get_file_content")
  try:
    target_path = f"files/{file_id}/content?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "GET")
    return retVal
  finally:
    await log_function_footer(log_data)

# ============================================================================
# VECTOR STORES API
# ============================================================================

@router.post("/vector_stores")
async def create_vector_store(request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Vector Stores API - Create Vector Store. Mirrors: POST /vector_stores"""
  log_data = log_function_header("create_vector_store")
  try:
    target_path = f"vector_stores?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "POST")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.get("/vector_stores")
async def list_vector_stores(request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Vector Stores API - List Vector Stores. Mirrors: GET /vector_stores"""
  log_data = log_function_header("list_vector_stores")
  try:
    target_path = f"vector_stores?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "GET")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.get("/vector_stores/{vector_store_id}")
async def get_vector_store(vector_store_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Vector Stores API - Get Vector Store. Mirrors: GET /vector_stores/{vector_store_id}"""
  log_data = log_function_header("get_vector_store")
  try:
    target_path = f"vector_stores/{vector_store_id}?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "GET")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.post("/vector_stores/{vector_store_id}")
async def update_vector_store(vector_store_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Vector Stores API - Update Vector Store. Mirrors: POST /vector_stores/{vector_store_id}"""
  log_data = log_function_header("update_vector_store")
  try:
    target_path = f"vector_stores/{vector_store_id}?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "POST")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.delete("/vector_stores/{vector_store_id}")
async def delete_vector_store(vector_store_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Vector Stores API - Delete Vector Store. Mirrors: DELETE /vector_stores/{vector_store_id}"""
  log_data = log_function_header("delete_vector_store")
  try:
    target_path = f"vector_stores/{vector_store_id}?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "DELETE")
    return retVal
  finally:
    await log_function_footer(log_data)

# Vector Store Files endpoints
@router.post("/vector_stores/{vector_store_id}/files")
async def create_vector_store_file(vector_store_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Vector Stores API - Create Vector Store File. Mirrors: POST /vector_stores/{vector_store_id}/files"""
  log_data = log_function_header("create_vector_store_file")
  try:
    target_path = f"vector_stores/{vector_store_id}/files?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "POST")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.get("/vector_stores/{vector_store_id}/files")
async def list_vector_store_files(vector_store_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Vector Stores API - List Vector Store Files. Mirrors: GET /vector_stores/{vector_store_id}/files"""
  log_data = log_function_header("list_vector_store_files")
  try:
    target_path = f"vector_stores/{vector_store_id}/files?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "GET")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.get("/vector_stores/{vector_store_id}/files/{file_id}")
async def get_vector_store_file(vector_store_id: str, file_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Vector Stores API - Get Vector Store File. Mirrors: GET /vector_stores/{vector_store_id}/files/{file_id}"""
  log_data = log_function_header("get_vector_store_file")
  try:
    target_path = f"vector_stores/{vector_store_id}/files/{file_id}?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "GET")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.delete("/vector_stores/{vector_store_id}/files/{file_id}")
async def delete_vector_store_file(vector_store_id: str, file_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Vector Stores API - Delete Vector Store File. Mirrors: DELETE /vector_stores/{vector_store_id}/files/{file_id}"""
  log_data = log_function_header("delete_vector_store_file")
  try:
    target_path = f"vector_stores/{vector_store_id}/files/{file_id}?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "DELETE")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.post("/vector_stores/{vector_store_id}/search")
async def search_vector_store(vector_store_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Vector Stores API - Search Vector Store. Mirrors: POST /vector_stores/{vector_store_id}/search"""
  log_data = log_function_header("search_vector_store")
  try:
    target_path = f"vector_stores/{vector_store_id}/search?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "POST")
    return retVal
  finally:
    await log_function_footer(log_data)

# ============================================================================
# ASSISTANTS API
# ============================================================================

@router.post("/assistants")
async def create_assistant(request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Assistants API - Create Assistant. Mirrors: POST /assistants"""
  log_data = log_function_header("create_assistant")
  try:
    target_path = f"assistants?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "POST")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.get("/assistants")
async def list_assistants(request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Assistants API - List Assistants. Mirrors: GET /assistants"""
  log_data = log_function_header("list_assistants")
  try:
    target_path = f"assistants?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "GET")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.get("/assistants/{assistant_id}")
async def get_assistant(assistant_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Assistants API - Get Assistant. Mirrors: GET /assistants/{assistant_id}"""
  log_data = log_function_header("get_assistant")
  try:
    target_path = f"assistants/{assistant_id}?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "GET")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.post("/assistants/{assistant_id}")
async def update_assistant(assistant_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Assistants API - Update Assistant. Mirrors: POST /assistants/{assistant_id}"""
  log_data = log_function_header("update_assistant")
  try:
    target_path = f"assistants/{assistant_id}?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "POST")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.delete("/assistants/{assistant_id}")
async def delete_assistant(assistant_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Assistants API - Delete Assistant. Mirrors: DELETE /assistants/{assistant_id}"""
  log_data = log_function_header("delete_assistant")
  try:
    target_path = f"assistants/{assistant_id}?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "DELETE")
    return retVal
  finally:
    await log_function_footer(log_data)

# ============================================================================
# THREADS API
# ============================================================================

@router.post("/threads")
async def create_thread(request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Threads API - Create Thread. Mirrors: POST /threads"""
  log_data = log_function_header("create_thread")
  try:
    target_path = f"threads?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "POST")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.get("/threads")
async def list_threads(request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Threads API - List Threads. Mirrors: GET /threads"""
  log_data = log_function_header("list_threads")
  try:
    target_path = f"threads?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "GET")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.get("/threads/{thread_id}")
async def get_thread(thread_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Threads API - Get Thread. Mirrors: GET /threads/{thread_id}"""
  log_data = log_function_header("get_thread")
  try:
    target_path = f"threads/{thread_id}?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "GET")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.post("/threads/{thread_id}")
async def update_thread(thread_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Threads API - Update Thread. Mirrors: POST /threads/{thread_id}"""
  log_data = log_function_header("update_thread")
  try:
    target_path = f"threads/{thread_id}?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "POST")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Threads API - Delete Thread. Mirrors: DELETE /threads/{thread_id}"""
  log_data = log_function_header("delete_thread")
  try:
    target_path = f"threads/{thread_id}?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "DELETE")
    return retVal
  finally:
    await log_function_footer(log_data)

# Thread Messages endpoints
@router.post("/threads/{thread_id}/messages")
async def create_thread_message(thread_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Threads API - Create Thread Message. Mirrors: POST /threads/{thread_id}/messages"""
  log_data = log_function_header("create_thread_message")
  try:
    target_path = f"threads/{thread_id}/messages?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "POST")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.get("/threads/{thread_id}/messages")
async def list_thread_messages(thread_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Threads API - List Thread Messages. Mirrors: GET /threads/{thread_id}/messages"""
  log_data = log_function_header("list_thread_messages")
  try:
    target_path = f"threads/{thread_id}/messages?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "GET")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.get("/threads/{thread_id}/messages/{message_id}")
async def get_thread_message(thread_id: str, message_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Threads API - Get Thread Message. Mirrors: GET /threads/{thread_id}/messages/{message_id}"""
  log_data = log_function_header("get_thread_message")
  try:
    target_path = f"threads/{thread_id}/messages/{message_id}?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "GET")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.post("/threads/{thread_id}/messages/{message_id}")
async def update_thread_message(thread_id: str, message_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Threads API - Update Thread Message. Mirrors: POST /threads/{thread_id}/messages/{message_id}"""
  log_data = log_function_header("update_thread_message")
  try:
    target_path = f"threads/{thread_id}/messages/{message_id}?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "POST")
    return retVal
  finally:
    await log_function_footer(log_data)

# Thread Runs endpoints
@router.post("/threads/{thread_id}/runs")
async def create_thread_run(thread_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Threads API - Create Thread Run. Mirrors: POST /threads/{thread_id}/runs"""
  log_data = log_function_header("create_thread_run")
  try:
    target_path = f"threads/{thread_id}/runs?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "POST")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.get("/threads/{thread_id}/runs")
async def list_thread_runs(thread_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Threads API - List Thread Runs. Mirrors: GET /threads/{thread_id}/runs"""
  log_data = log_function_header("list_thread_runs")
  try:
    target_path = f"threads/{thread_id}/runs?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "GET")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.get("/threads/{thread_id}/runs/{run_id}")
async def get_thread_run(thread_id: str, run_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Threads API - Get Thread Run. Mirrors: GET /threads/{thread_id}/runs/{run_id}"""
  log_data = log_function_header("get_thread_run")
  try:
    target_path = f"threads/{thread_id}/runs/{run_id}?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "GET")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.post("/threads/{thread_id}/runs/{run_id}")
async def update_thread_run(thread_id: str, run_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Threads API - Update Thread Run. Mirrors: POST /threads/{thread_id}/runs/{run_id}"""
  log_data = log_function_header("update_thread_run")
  try:
    target_path = f"threads/{thread_id}/runs/{run_id}?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "POST")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.post("/threads/{thread_id}/runs/{run_id}/cancel")
async def cancel_thread_run(thread_id: str, run_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Threads API - Cancel Thread Run. Mirrors: POST /threads/{thread_id}/runs/{run_id}/cancel"""
  log_data = log_function_header("cancel_thread_run")
  try:
    target_path = f"threads/{thread_id}/runs/{run_id}/cancel?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "POST")
    return retVal
  finally:
    await log_function_footer(log_data)

# ============================================================================
# SELF TEST (callable utility; exposed at app-level, not under /openai)
# ============================================================================

async def self_test(request: Request):
  """Test all endpoints and return results as simple HTML."""
  log_data = log_function_header("self_test")
  results = {}
  try: timeout_seconds = float(request.query_params.get("timeoutSecs")) if "timeoutSecs" in request.query_params else None
  except Exception: timeout_seconds = None
  if timeout_seconds is None: timeout_seconds = 120
  
  # Build path helper: append api-version only for Azure
  def build_azure_openai_endpoint_path(base_path: str) -> str:
    return f"{base_path}?api-version={config.AZURE_OPENAI_API_VERSION}" if config.OPENAI_SERVICE_TYPE == "azure_openai" else base_path
  
  # Helpers for dummy requests (defined before first use)
  class DummyRequest:
    async def body(self): return b""
    @property
    def headers(self): return {}
  
  class DummyRequestJson:
    def __init__(self, obj: Dict[str, Any]): self._b = json.dumps(obj).encode("utf-8")
    async def body(self): return self._b
    @property
    def headers(self): return {"Content-Type": "application/json"}
  
  # Helpers for result suffixes
  def format_for_display(input_string: Any, max_length: int = 120) -> str:
    try: return truncate_string(clean_response(str(input_string)), max_length)
    except Exception: return input_string
  
  def get_error_details(response, data: Dict[str, Any] = None) -> str:
    """Extract error message from API response for display in Details column."""
    if response.status_code < 400: return ""
    error_msg = ""
    if data: error_msg = data.get("error", {}).get("message", "") if isinstance(data.get("error"), dict) else str(data.get("error", ""))
    if not error_msg and response.body:
      try: error_msg = format_for_display(response.body.decode("utf-8"), 100)
      except: error_msg = f"HTTP {response.status_code}"
    return f"Error: {error_msg}" if error_msg else f"HTTP {response.status_code}"
  
  def _extract_answer(obj: Dict[str, Any]) -> Optional[str]:
    if not isinstance(obj, dict): return None
    if "output_text" in obj and obj.get("output_text"): return str(obj.get("output_text"))
    out = obj.get("output")
    if isinstance(out, list) and len(out) > 0:
      # Try common shapes: [{"content":[{"type":"output_text","text":"..."}]}]
      try:
        content = out[0].get("content")
        if isinstance(content, list):
          for item in content:
            if isinstance(item, dict) and (item.get("text") or item.get("content")):
              return item.get("text") or item.get("content")
      except Exception:
        pass
    # Fallbacks used by some responses
    if "content" in obj and isinstance(obj["content"], str): return obj["content"]
    if "message" in obj and isinstance(obj["message"], str): return obj["message"]
    return None
  
  # Responses API test: create a response
  try:
    resp_post_path = build_azure_openai_endpoint_path("responses")
    # Build minimal request body
    model_name = config.AZURE_OPENAI_DEFAULT_MODEL_DEPLOYMENT_NAME if config.OPENAI_SERVICE_TYPE == "azure_openai" else config.OPENAI_DEFAULT_MODEL_NAME
    if not model_name:
      results["/responses (POST create)"] = {"Result": "Skipped (missing model name)", "Details": ""}
    else:
      question = "3rd Roman emperor?"
      create_req = DummyRequestJson({"model": model_name, "input": question})
      create_resp, _milliseconds = await proxy_request(create_req, resp_post_path, "POST", timeout_seconds=timeout_seconds)
      create_data = json.loads(create_resp.body.decode("utf-8")) if create_resp.body else {}
      resp_id = create_data.get("id")
      answer = _extract_answer(create_data) or "?"
      status_ok = create_resp.status_code < 400 and resp_id
      emoji = "✅" if status_ok else "❌"
      main = ("OK" if status_ok else f"HTTP {create_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if status_ok:
        details = f"Q: '{format_for_display(question)}' A: '{format_for_display(answer, 40)}'"
      else:
        error_msg = create_data.get("error", {}).get("message", "") if create_data else ""
        if not error_msg and create_resp.body:
          error_msg = format_for_display(create_resp.body.decode("utf-8"), 100)
        details = f"Error: {error_msg}" if error_msg else f"HTTP {create_resp.status_code}"
      results["/responses (POST create)"] = {"Result": f"{emoji} {main}", "Details": details}
      # If created, immediately try GET by id
      try:
        if resp_id:
          get_resp, _milliseconds = await proxy_request(request, build_azure_openai_endpoint_path(f"responses/{resp_id}"), "GET", timeout_seconds=timeout_seconds)
          ok = get_resp.status_code < 400
          emoji = "✅" if ok else "❌"
          main = ("OK" if ok else f"HTTP {get_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
          details = f"id: '{format_for_display(resp_id)}'"
          results["/responses/{id} (GET)"] = {"Result": f"{emoji} {main}", "Details": details}
        else:
          results["/responses/{id} (GET)"] = {"Result": "Skipped (missing id)", "Details": ""}
      except Exception as e:
        results["/responses/{id} (GET)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  except Exception as e:
    results["/responses (POST create)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  uploaded_file_id = None
  vector_store_id = None
  
  # Upload file
  try:
    files = {"file": ("selftest.txt", b"hello from selftest", "text/plain"), "purpose": (None, "assistants")}
    upload_resp, _milliseconds = await proxy_request(DummyRequest(), build_azure_openai_endpoint_path("files"), "POST", files=files, timeout_seconds=timeout_seconds)
    data = json.loads(upload_resp.body.decode("utf-8")) if upload_resp.body else {}
    uploaded_file_id = data.get("id")
    ok = bool(uploaded_file_id)
    emoji = "✅" if ok else "❌"
    main = ("OK" if ok else "No file id returned") + f" ({format_milliseconds(_milliseconds)})"
    if ok:
      details = f"filename: 'selftest.txt' id: '{format_for_display(uploaded_file_id)}'"
    else:
      details = get_error_details(upload_resp, data)
    results["/files (POST upload)"] = {"Result": f"{emoji} {main}", "Details": details}
  except Exception as e:
    results["/files (POST upload)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # Get file
  try:
    if uploaded_file_id:
      get_file_resp, _milliseconds = await proxy_request(request, build_azure_openai_endpoint_path(f"files/{uploaded_file_id}"), "GET", timeout_seconds=timeout_seconds)
      get_file_data = json.loads(get_file_resp.body.decode("utf-8")) if get_file_resp.body else {}
      ok = get_file_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {get_file_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        filename = get_file_data.get("filename", "unknown")
        purpose = get_file_data.get("purpose", "unknown")
        details = f"filename: '{format_for_display(filename)}' purpose: '{format_for_display(purpose)}'"
      else:
        details = get_error_details(get_file_resp, get_file_data)
      results["/files/{id} (GET)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/files/{id} (GET)"] = {"Result": "Skipped (missing file id)", "Details": ""}
  except Exception as e:
    results["/files/{id} (GET)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # Create vector store
  try:
    vs_name = f"selftest-vs-{uuid.uuid4().hex[:8]}"
    vs_req = DummyRequestJson({"name": vs_name})
    vs_resp, _milliseconds = await proxy_request(vs_req, build_azure_openai_endpoint_path("vector_stores"), "POST", timeout_seconds=timeout_seconds)
    vs_data = json.loads(vs_resp.body.decode("utf-8")) if vs_resp.body else {}
    vector_store_id = vs_data.get("id")
    ok = bool(vector_store_id)
    emoji = "✅" if ok else "❌"
    main = ("OK" if ok else "No vector_store id returned") + f" ({format_milliseconds(_milliseconds)})"
    if ok:
      details = f"name: '{format_for_display(vs_name)}' id: '{format_for_display(vector_store_id)}'"
    else:
      details = get_error_details(vs_resp, vs_data)
    results["/vector_stores (POST create)"] = {"Result": f"{emoji} {main}", "Details": details}
  except Exception as e:
    results["/vector_stores (POST create)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # List vector stores
  try:
    list_vs_resp, _milliseconds = await proxy_request(request, build_azure_openai_endpoint_path("vector_stores"), "GET", timeout_seconds=timeout_seconds)
    try:
      list_vs_data = json.loads(list_vs_resp.body.decode("utf-8")) if list_vs_resp.body else {}
      vs_count = len(list_vs_data.get("data", [])) if isinstance(list_vs_data, dict) else 0
    except (UnicodeDecodeError, json.JSONDecodeError):
      list_vs_data = {}
      vs_count = 0
    ok = list_vs_resp.status_code < 400
    emoji = "✅" if ok else "❌"
    main = ("OK" if ok else f"HTTP {list_vs_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
    if ok:
      details = f"items: {vs_count}"
    else:
      details = get_error_details(list_vs_resp, list_vs_data)
    results["/vector_stores (GET)"] = {"Result": f"{emoji} {main}", "Details": details}
  except Exception as e:
    results["/vector_stores (GET)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # Add file to vector store
  try:
    if vector_store_id and uploaded_file_id:
      add_req = DummyRequestJson({"file_id": uploaded_file_id})
      add_resp, _milliseconds = await proxy_request(add_req, build_azure_openai_endpoint_path(f"vector_stores/{vector_store_id}/files"), "POST", timeout_seconds=timeout_seconds)
      ok = add_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {add_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"vector_store_id: '{format_for_display(vector_store_id)}' file_id: '{format_for_display(uploaded_file_id)}'"
      else:
        add_data = json.loads(add_resp.body.decode("utf-8")) if add_resp.body else {}
        details = get_error_details(add_resp, add_data)
      results["/vector_stores/{id}/files (POST add)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/vector_stores/{id}/files (POST add)"] = {"Result": "Skipped (missing ids)", "Details": ""}
  except Exception as e:
    results["/vector_stores/{id}/files (POST add)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # Search vector store (wait for file processing)
  try:
    if vector_store_id and uploaded_file_id:
      # Wait for file to be processed (check status)
      max_wait_seconds = 10; wait_interval = 2; max_retries = 3; file_ready = False
      
      for attempt in range(max_wait_seconds // wait_interval):
        try:
          status_resp, _ms = await proxy_request(DummyRequest(), build_azure_openai_endpoint_path(f"vector_stores/{vector_store_id}/files/{uploaded_file_id}"), "GET", timeout_seconds=5)
          if status_resp.status_code < 400:
            status_data = json.loads(status_resp.body.decode("utf-8")) if status_resp.body else {}
            file_status = status_data.get("status", "unknown")
            if file_status == "completed":
              file_ready = True
              break
            elif file_status in ["failed", "cancelled"]:
              break
        except Exception:
          pass
        await asyncio.sleep(wait_interval)
      
      # Perform search
      search_query = "hello"
      search_req = DummyRequestJson({"query": search_query})
      search_resp, _milliseconds = await proxy_request(search_req, build_azure_openai_endpoint_path(f"vector_stores/{vector_store_id}/search"), "POST", timeout_seconds=timeout_seconds)
      search_data = json.loads(search_resp.body.decode("utf-8")) if search_resp.body else {}
      results_count = len(search_data.get("data", [])) if isinstance(search_data, dict) else 0
      ok = search_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {search_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        status_note = f" (file {'ready' if file_ready else 'not ready'})"
        details = f"query: '{format_for_display(search_query)}' results: {results_count}{status_note}"
      else:
        details = get_error_details(search_resp, search_data)
      results["/vector_stores/{id}/search (POST)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/vector_stores/{id}/search (POST)"] = {"Result": "Skipped (missing ids)", "Details": ""}
  except Exception as e:
    results["/vector_stores/{id}/search (POST)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # Remove file from vector store
  try:
    if vector_store_id and uploaded_file_id:
      delvf_resp, _milliseconds = await proxy_request(DummyRequest(), build_azure_openai_endpoint_path(f"vector_stores/{vector_store_id}/files/{uploaded_file_id}"), "DELETE", timeout_seconds=timeout_seconds)
      ok = delvf_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {delvf_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"vector_store_id: '{format_for_display(vector_store_id)}' file_id: '{format_for_display(uploaded_file_id)}'"
      else:
        delvf_data = json.loads(delvf_resp.body.decode("utf-8")) if delvf_resp.body else {}
        details = get_error_details(delvf_resp, delvf_data)
      results["/vector_stores/{id}/files/{file_id} (DELETE)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/vector_stores/{id}/files/{file_id} (DELETE)"] = {"Result": "Skipped (missing ids)", "Details": ""}
  except Exception as e:
    results["/vector_stores/{id}/files/{file_id} (DELETE)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # Delete vector store
  try:
    if vector_store_id:
      delvs_resp, _milliseconds = await proxy_request(DummyRequest(), build_azure_openai_endpoint_path(f"vector_stores/{vector_store_id}"), "DELETE", timeout_seconds=timeout_seconds)
      ok = delvs_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {delvs_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"id: '{format_for_display(vector_store_id)}'"
      else:
        delvs_data = json.loads(delvs_resp.body.decode("utf-8")) if delvs_resp.body else {}
        details = get_error_details(delvs_resp, delvs_data)
      results["/vector_stores/{id} (DELETE)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/vector_stores/{id} (DELETE)"] = {"Result": "Skipped (missing id)", "Details": ""}
  except Exception as e:
    results["/vector_stores/{id} (DELETE)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # Delete file
  try:
    if uploaded_file_id:
      delf_resp, _milliseconds = await proxy_request(DummyRequest(), build_azure_openai_endpoint_path(f"files/{uploaded_file_id}"), "DELETE", timeout_seconds=timeout_seconds)
      ok = delf_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {delf_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"id: '{format_for_display(uploaded_file_id)}'"
      else:
        delf_data = json.loads(delf_resp.body.decode("utf-8")) if delf_resp.body else {}
        details = get_error_details(delf_resp, delf_data)
      results["/files/{id} (DELETE)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/files/{id} (DELETE)"] = {"Result": "Skipped (missing id)", "Details": ""}
  except Exception as e:
    results["/files/{id} (DELETE)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  assistant_id = None
  
  # Create assistant
  try:
    model_name = config.AZURE_OPENAI_DEFAULT_MODEL_DEPLOYMENT_NAME if config.OPENAI_SERVICE_TYPE == "azure_openai" else config.OPENAI_DEFAULT_MODEL_NAME
    if not model_name:
      results["/assistants (POST create)"] = {"Result": "Skipped (missing model name)", "Details": ""}
    else:
      assistant_name = f"selftest-assistant-{uuid.uuid4().hex[:8]}"
      create_assistant_req = DummyRequestJson({"model": model_name, "name": assistant_name, "instructions": "You are a helpful assistant for testing purposes."})
      create_assistant_resp, _milliseconds = await proxy_request(create_assistant_req, build_azure_openai_endpoint_path("assistants"), "POST", timeout_seconds=timeout_seconds)
      create_assistant_data = json.loads(create_assistant_resp.body.decode("utf-8")) if create_assistant_resp.body else {}
      assistant_id = create_assistant_data.get("id")
      ok = bool(assistant_id)
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else "No assistant id returned") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"name: '{format_for_display(assistant_name)}' id: '{format_for_display(assistant_id)}'"
      else:
        details = get_error_details(create_assistant_resp, create_assistant_data)
      results["/assistants (POST create)"] = {"Result": f"{emoji} {main}", "Details": details}
  except Exception as e:
    results["/assistants (POST create)"] = {"Result": f"Error: {str(e)}", "Details": ""}

  # List assistants
  try:
    list_resp, _milliseconds = await proxy_request(request, build_azure_openai_endpoint_path("assistants"), "GET", timeout_seconds=timeout_seconds)
    try:
      list_data = json.loads(list_resp.body.decode("utf-8")) if list_resp.body else {}
      assistants_count = len(list_data.get("data", [])) if isinstance(list_data, dict) else 0
    except (UnicodeDecodeError, json.JSONDecodeError):
      list_data = {}
      assistants_count = 0
    ok = list_resp.status_code < 400
    emoji = "✅" if ok else "❌"
    main = ("OK" if ok else f"HTTP {list_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
    if ok:
      details = f"assistants: {assistants_count}"
    else:
      details = get_error_details(list_resp, list_data)
    results["/assistants (GET)"] = {"Result": f"{emoji} {main}", "Details": details}
  except Exception as e:
    results["/assistants (GET)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # Delete assistant
  try:
    if assistant_id:
      delete_assistant_resp, _milliseconds = await proxy_request(DummyRequest(), build_azure_openai_endpoint_path(f"assistants/{assistant_id}"), "DELETE", timeout_seconds=timeout_seconds)
      ok = delete_assistant_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {delete_assistant_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"id: '{format_for_display(assistant_id)}'"
      else:
        delete_assistant_data = json.loads(delete_assistant_resp.body.decode("utf-8")) if delete_assistant_resp.body else {}
        details = get_error_details(delete_assistant_resp, delete_assistant_data)
      results["/assistants/{id} (DELETE)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/assistants/{id} (DELETE)"] = {"Result": "Skipped (missing id)", "Details": ""}
  except Exception as e:
    results["/assistants/{id} (DELETE)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  thread_id = None
  message_id = None
  
  # Create thread
  try:
    create_thread_req = DummyRequestJson({})
    create_thread_resp, _milliseconds = await proxy_request(create_thread_req, build_azure_openai_endpoint_path("threads"), "POST", timeout_seconds=timeout_seconds)
    create_thread_data = json.loads(create_thread_resp.body.decode("utf-8")) if create_thread_resp.body else {}
    thread_id = create_thread_data.get("id")
    ok = bool(thread_id)
    emoji = "✅" if ok else "❌"
    main = ("OK" if ok else "No thread id returned") + f" ({format_milliseconds(_milliseconds)})"
    if ok:
      details = f"id: '{format_for_display(thread_id)}'"
    else:
      details = get_error_details(create_thread_resp, create_thread_data)
    results["/threads (POST create)"] = {"Result": f"{emoji} {main}", "Details": details}
  except Exception as e:
    results["/threads (POST create)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # List threads
  try:
    list_threads_resp, _milliseconds = await proxy_request(request, build_azure_openai_endpoint_path("threads"), "GET", timeout_seconds=timeout_seconds)
    try:
      list_threads_data = json.loads(list_threads_resp.body.decode("utf-8")) if list_threads_resp.body else {}
      threads_count = len(list_threads_data.get("data", [])) if isinstance(list_threads_data, dict) else 0
    except (UnicodeDecodeError, json.JSONDecodeError):
      list_threads_data = {}
      threads_count = 0
    ok = list_threads_resp.status_code < 400
    emoji = "✅" if ok else "❌"
    main = ("OK" if ok else f"HTTP {list_threads_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
    if ok:
      details = f"threads: {threads_count}"
    else:
      details = get_error_details(list_threads_resp, list_threads_data)
    results["/threads (GET)"] = {"Result": f"{emoji} {main}", "Details": details}
  except Exception as e:
    results["/threads (GET)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # Get thread
  try:
    if thread_id:
      get_thread_resp, _milliseconds = await proxy_request(request, build_azure_openai_endpoint_path(f"threads/{thread_id}"), "GET", timeout_seconds=timeout_seconds)
      get_thread_data = json.loads(get_thread_resp.body.decode("utf-8")) if get_thread_resp.body else {}
      ok = get_thread_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {get_thread_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"id: '{format_for_display(thread_id)}'"
      else:
        details = get_error_details(get_thread_resp, get_thread_data)
      results["/threads/{id} (GET)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/threads/{id} (GET)"] = {"Result": "Skipped (missing thread id)", "Details": ""}
  except Exception as e:
    results["/threads/{id} (GET)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # Create thread message
  try:
    if thread_id:
      message_content = "Hello, this is a test message from the self test."
      create_message_req = DummyRequestJson({"role": "user", "content": message_content})
      create_message_resp, _milliseconds = await proxy_request(create_message_req, build_azure_openai_endpoint_path(f"threads/{thread_id}/messages"), "POST", timeout_seconds=timeout_seconds)
      create_message_data = json.loads(create_message_resp.body.decode("utf-8")) if create_message_resp.body else {}
      message_id = create_message_data.get("id")
      ok = bool(message_id)
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else "No message id returned") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"content: '{format_for_display(message_content, 30)}' id: '{format_for_display(message_id)}'"
      else:
        details = get_error_details(create_message_resp, create_message_data)
      results["/threads/{id}/messages (POST create)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/threads/{id}/messages (POST create)"] = {"Result": "Skipped (missing thread id)", "Details": ""}
  except Exception as e:
    results["/threads/{id}/messages (POST create)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # List thread messages
  try:
    if thread_id:
      list_messages_resp, _milliseconds = await proxy_request(request, build_azure_openai_endpoint_path(f"threads/{thread_id}/messages"), "GET", timeout_seconds=timeout_seconds)
      try:
        list_messages_data = json.loads(list_messages_resp.body.decode("utf-8")) if list_messages_resp.body else {}
        messages_count = len(list_messages_data.get("data", [])) if isinstance(list_messages_data, dict) else 0
      except (UnicodeDecodeError, json.JSONDecodeError):
        list_messages_data = {}
        messages_count = 0
      ok = list_messages_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {list_messages_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"messages: {messages_count}"
      else:
        details = get_error_details(list_messages_resp, list_messages_data)
      results["/threads/{id}/messages (GET)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/threads/{id}/messages (GET)"] = {"Result": "Skipped (missing thread id)", "Details": ""}
  except Exception as e:
    results["/threads/{id}/messages (GET)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # Get thread message
  try:
    if thread_id and message_id:
      get_message_resp, _milliseconds = await proxy_request(request, build_azure_openai_endpoint_path(f"threads/{thread_id}/messages/{message_id}"), "GET", timeout_seconds=timeout_seconds)
      get_message_data = json.loads(get_message_resp.body.decode("utf-8")) if get_message_resp.body else {}
      ok = get_message_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {get_message_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"thread_id: '{format_for_display(thread_id)}' message_id: '{format_for_display(message_id)}'"
      else:
        details = get_error_details(get_message_resp, get_message_data)
      results["/threads/{id}/messages/{message_id} (GET)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/threads/{id}/messages/{message_id} (GET)"] = {"Result": "Skipped (missing ids)", "Details": ""}
  except Exception as e:
    results["/threads/{id}/messages/{message_id} (GET)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # Delete thread
  try:
    if thread_id:
      delete_thread_resp, _milliseconds = await proxy_request(DummyRequest(), build_azure_openai_endpoint_path(f"threads/{thread_id}"), "DELETE", timeout_seconds=timeout_seconds)
      ok = delete_thread_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {delete_thread_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"id: '{format_for_display(thread_id)}'"
      else:
        delete_thread_data = json.loads(delete_thread_resp.body.decode("utf-8")) if delete_thread_resp.body else {}
        details = get_error_details(delete_thread_resp, delete_thread_data)
      results["/threads/{id} (DELETE)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/threads/{id} (DELETE)"] = {"Result": "Skipped (missing id)", "Details": ""}
  except Exception as e:
    results["/threads/{id} (DELETE)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # Generate HTML
  html = "<html><body style='font-family: Arial, sans-serif;'>"
  html += "<h2>OpenAI Proxy Self Test Results</h2>"
  html += convert_to_nested_html_table(results)
  html += "<p><b>Configuration:</b></p>"
  html += convert_to_nested_html_table(format_config_for_displaying(config))
  html += "</body></html>"
  try:
    return HTMLResponse(content=html)
  finally:
    await log_function_footer(log_data)
