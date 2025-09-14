import asyncio, datetime, json, logging, uuid
from typing import Any, Dict, Optional

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from fastapi import APIRouter, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, Response, StreamingResponse

import httpx

from utils import clean_response, convert_to_html_table, format_config_for_displaying, format_milliseconds, log_function_footer, log_function_header, log_function_output, truncate_string
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
  
  # Azure deployment endpoints that require model-based URL transformation
  _deployments_endpoints = {"completions", "chat/completions", "embeddings", "audio/transcriptions", "audio/translations", "audio/speech", "images/generations", "images/edits"}
  
  # For Azure OpenAI deployment endpoints, check if we need to transform the URL
  transformed_target_path = target_path
  request_body = None
  if config.OPENAI_SERVICE_TYPE == "azure_openai":
    # Extract the base path without query parameters for comparison
    base_path = target_path.split('?')[0]
    if base_path in _deployments_endpoints and not files:
      # Read request body to extract model name for deployment URL transformation
      try:
        request_body = await request.body()
        if request_body:
          request_data = json.loads(request_body.decode('utf-8'))
          model = request_data.get('model')
          if model and "/deployments" not in target_path:
            # Transform URL to deployment format: /deployments/{model}/chat/completions
            if '?' in target_path:
              query_part = target_path.split('?', 1)[1]
              transformed_target_path = f"deployments/{model}/{base_path}?{query_part}"
            else:
              transformed_target_path = f"deployments/{model}/{base_path}"
      except (json.JSONDecodeError, UnicodeDecodeError):
        # If we can't parse the body, continue with original path
        pass
  
  # Construct target URL
  if config.OPENAI_SERVICE_TYPE == "azure_openai":
    base = config.AZURE_OPENAI_ENDPOINT.rstrip('/')
    if not base.endswith("/openai"):
      base = f"{base}/openai"
    target_url = f"{base}/{transformed_target_path.lstrip('/')}"
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
  
  # Add OpenAI-Beta header for assistants API endpoints (includes threads, runs, messages, etc.)
  if any(keyword in target_path for keyword in ["assistants", "threads", "runs", "messages", "vector_stores"]):
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
        body = request_body if request_body is not None else await request.body()
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
# CHAT COMPLETIONS API
# ============================================================================

@router.post("/chat/completions")
async def create_chat_completion(request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Chat Completions API - Create Chat Completion. Mirrors: POST /chat/completions"""
  log_data = log_function_header("create_chat_completion")
  try:
    target_path = f"chat/completions?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "POST")
    return retVal
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

@router.post("/threads/{thread_id}/runs/{run_id}/submit_tool_outputs")
async def submit_tool_outputs(thread_id: str, run_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Threads API - Submit Tool Outputs. Mirrors: POST /threads/{thread_id}/runs/{run_id}/submit_tool_outputs"""
  log_data = log_function_header("submit_tool_outputs")
  try:
    target_path = f"threads/{thread_id}/runs/{run_id}/submit_tool_outputs?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "POST")
    return retVal
  finally:
    await log_function_footer(log_data)

# Thread Run Steps endpoints
@router.get("/threads/{thread_id}/runs/{run_id}/steps")
async def list_run_steps(thread_id: str, run_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Threads API - List Run Steps. Mirrors: GET /threads/{thread_id}/runs/{run_id}/steps"""
  log_data = log_function_header("list_run_steps")
  try:
    target_path = f"threads/{thread_id}/runs/{run_id}/steps?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "GET")
    return retVal
  finally:
    await log_function_footer(log_data)

@router.get("/threads/{thread_id}/runs/{run_id}/steps/{step_id}")
async def get_run_step(thread_id: str, run_id: str, step_id: str, request: Request, api_version: str = "2025-04-01-preview"):
  """Proxy for OpenAI Threads API - Get Run Step. Mirrors: GET /threads/{thread_id}/runs/{run_id}/steps/{step_id}"""
  log_data = log_function_header("get_run_step")
  try:
    target_path = f"threads/{thread_id}/runs/{run_id}/steps/{step_id}?api-version={api_version}"
    retVal, _milliseconds = await proxy_request(request, target_path, "GET")
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
  
  # Build path helper: use standard OpenAI format, let proxy handle Azure transformation
  def build_openai_endpoint_path(base_path: str) -> str:
    # Always use standard OpenAI format - the proxy will transform for Azure if needed
    return base_path
  
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
  
  def get_error_details(response, data):
    """Extract error details from response for display."""
    if not response: return "No response"
    error_msg = ""
    if data: error_msg = data.get("error", {}).get("message", "") if isinstance(data.get("error"), dict) else str(data.get("error", ""))
    if not error_msg and response.body:
      try: error_msg = format_for_display(response.body.decode("utf-8", errors="replace"), 100)
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
  
  # Chat Completions API test: create a chat completion
  try:
    chat_post_path = build_openai_endpoint_path("chat/completions")
    model_name = config.AZURE_OPENAI_DEFAULT_MODEL_DEPLOYMENT_NAME if config.OPENAI_SERVICE_TYPE == "azure_openai" else config.OPENAI_DEFAULT_MODEL_NAME
    if not model_name:
      results["/chat/completions (POST create)"] = {"Result": "Skipped (missing model name)", "Details": ""}
    else:
      question = "What is 2+2?"
      chat_req = DummyRequestJson({"model": model_name, "messages": [{"role": "user", "content": question}], "max_tokens": 50})
      chat_resp, _milliseconds = await proxy_request(chat_req, chat_post_path, "POST", timeout_seconds=timeout_seconds)
      try:
        chat_data = json.loads(chat_resp.body.decode("utf-8", errors="replace")) if chat_resp.body else {}
        has_decode_error = False
      except (UnicodeDecodeError, json.JSONDecodeError):
        chat_data = {}
        has_decode_error = True
      
      # Extract answer from chat completion response
      answer = "?"
      if chat_data.get("choices") and len(chat_data["choices"]) > 0:
        choice = chat_data["choices"][0]
        if choice.get("message") and choice["message"].get("content"):
          answer = choice["message"]["content"].strip()
      
      status_ok = chat_resp.status_code < 400 and chat_data.get("choices")
      emoji = "✅" if status_ok and not has_decode_error else ("⚠️" if has_decode_error else "❌")
      main = ("OK" if status_ok else f"HTTP {chat_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if status_ok:
        details = f"Q: '{format_for_display(question)}' A: '{format_for_display(answer, 40)}'"
      else:
        error_msg = chat_data.get("error", {}).get("message", "") if chat_data else ""
        if not error_msg and chat_resp.body:
          error_msg = format_for_display(chat_resp.body.decode("utf-8", errors="replace"), 100)
        details = f"Error: {error_msg}" if error_msg else f"HTTP {chat_resp.status_code}"
      results["/chat/completions (POST create)"] = {"Result": f"{emoji} {main}", "Details": details}
  except Exception as e:
    results["/chat/completions (POST create)"] = {"Result": f"Error: {str(e)}", "Details": ""}

  # Responses API test: create a response
  try:
    resp_post_path = build_openai_endpoint_path("responses")
    # Build minimal request body
    model_name = config.AZURE_OPENAI_DEFAULT_MODEL_DEPLOYMENT_NAME if config.OPENAI_SERVICE_TYPE == "azure_openai" else config.OPENAI_DEFAULT_MODEL_NAME
    if not model_name:
      results["/responses (POST create)"] = {"Result": "Skipped (missing model name)", "Details": ""}
    else:
      question = "3rd Roman emperor?"
      create_req = DummyRequestJson({"model": model_name, "input": question})
      create_resp, _milliseconds = await proxy_request(create_req, resp_post_path, "POST", timeout_seconds=timeout_seconds)
      try:
        create_data = json.loads(create_resp.body.decode("utf-8", errors="replace")) if create_resp.body else {}
        has_decode_error = False
      except (UnicodeDecodeError, json.JSONDecodeError):
        create_data = {}
        has_decode_error = True
      resp_id = create_data.get("id")
      answer = _extract_answer(create_data) or "?"
      status_ok = create_resp.status_code < 400 and resp_id
      emoji = "✅" if status_ok and not has_decode_error else ("⚠️" if has_decode_error else "❌")
      main = ("OK" if status_ok else f"HTTP {create_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if status_ok:
        details = f"Q: '{format_for_display(question)}' A: '{format_for_display(answer, 40)}'"
      else:
        error_msg = create_data.get("error", {}).get("message", "") if create_data else ""
        if not error_msg and create_resp.body:
          error_msg = format_for_display(create_resp.body.decode("utf-8", errors="replace"), 100)
        details = f"Error: {error_msg}" if error_msg else f"HTTP {create_resp.status_code}"
      results["/responses (POST create)"] = {"Result": f"{emoji} {main}", "Details": details}
      # If created, immediately try GET by id
      try:
        if resp_id:
          get_resp, _milliseconds = await proxy_request(request, build_openai_endpoint_path(f"responses/{resp_id}"), "GET", timeout_seconds=timeout_seconds)
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
    files = {"file": ("selftest.txt", b"Arilena Drovik was born 1987-05-03", "text/plain"), "purpose": (None, "assistants")}
    upload_resp, _milliseconds = await proxy_request(DummyRequest(), build_openai_endpoint_path("files"), "POST", files=files, timeout_seconds=timeout_seconds)
    try:
      data = json.loads(upload_resp.body.decode("utf-8", errors="replace")) if upload_resp.body else {}
      has_decode_error = False
    except (UnicodeDecodeError, json.JSONDecodeError):
      data = {}
      has_decode_error = True
    uploaded_file_id = data.get("id")
    ok = bool(uploaded_file_id)
    emoji = "✅" if ok else ("⚠️" if has_decode_error else "❌")
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
      get_file_resp, _milliseconds = await proxy_request(request, build_openai_endpoint_path(f"files/{uploaded_file_id}"), "GET", timeout_seconds=timeout_seconds)
      try:
        get_file_data = json.loads(get_file_resp.body.decode("utf-8", errors="replace")) if get_file_resp.body else {}
        has_decode_error = False
      except (UnicodeDecodeError, json.JSONDecodeError):
        get_file_data = {}
        has_decode_error = True
      ok = get_file_resp.status_code < 400
      emoji = "✅" if ok else ("⚠️" if has_decode_error else "❌")
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
    vs_resp, _milliseconds = await proxy_request(vs_req, build_openai_endpoint_path("vector_stores"), "POST", timeout_seconds=timeout_seconds)
    try:
      vs_data = json.loads(vs_resp.body.decode("utf-8", errors="replace")) if vs_resp.body else {}
      has_decode_error = False
    except (UnicodeDecodeError, json.JSONDecodeError):
      vs_data = {}
      has_decode_error = True
    vector_store_id = vs_data.get("id")
    ok = bool(vector_store_id)
    emoji = "✅" if ok else ("⚠️" if has_decode_error else "❌")
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
    list_vs_resp, _milliseconds = await proxy_request(request, build_openai_endpoint_path("vector_stores"), "GET", timeout_seconds=timeout_seconds)
    try:
      list_vs_data = json.loads(list_vs_resp.body.decode("utf-8", errors="replace")) if list_vs_resp.body else {}
      vs_count = len(list_vs_data.get("data", [])) if isinstance(list_vs_data, dict) else 0
      has_decode_error = False
    except (UnicodeDecodeError, json.JSONDecodeError):
      list_vs_data = {}
      vs_count = 0
      has_decode_error = True
    ok = list_vs_resp.status_code < 400
    emoji = "✅" if ok else ("⚠️" if has_decode_error else "❌")
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
      add_resp, _milliseconds = await proxy_request(add_req, build_openai_endpoint_path(f"vector_stores/{vector_store_id}/files"), "POST", timeout_seconds=timeout_seconds)
      ok = add_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {add_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"vector_store_id: '{format_for_display(vector_store_id)}' file_id: '{format_for_display(uploaded_file_id)}'"
      else:
        try:
          add_data = json.loads(add_resp.body.decode("utf-8", errors="replace")) if add_resp.body else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
          add_data = {}
        details = get_error_details(add_resp, add_data)
      results["/vector_stores/{id}/files (POST add)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/vector_stores/{id}/files (POST with attributes)"] = {"Result": "Skipped (missing ids)", "Details": ""}
  except Exception as e:
    results["/vector_stores/{id}/files (POST with attributes)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # Search vector store (wait for file processing)
  try:
    if vector_store_id and uploaded_file_id:
      # Wait for file to be processed (check status)
      max_wait_seconds = 10; wait_interval = 2; max_retries = 3; file_ready = False
      
      for attempt in range(max_wait_seconds // wait_interval):
        try:
          status_resp, _ms = await proxy_request(DummyRequest(), build_openai_endpoint_path(f"vector_stores/{vector_store_id}/files/{uploaded_file_id}"), "GET", timeout_seconds=5)
          if status_resp.status_code < 400:
            try:
              status_data = json.loads(status_resp.body.decode("utf-8", errors="replace")) if status_resp.body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
              status_data = {}
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
      search_resp, _milliseconds = await proxy_request(search_req, build_openai_endpoint_path(f"vector_stores/{vector_store_id}/search"), "POST", timeout_seconds=timeout_seconds)
      try:
        search_data = json.loads(search_resp.body.decode("utf-8", errors="replace")) if search_resp.body else {}
        has_decode_error = False
      except (UnicodeDecodeError, json.JSONDecodeError):
        search_data = {}
        has_decode_error = True
      results_count = len(search_data.get("data", [])) if isinstance(search_data, dict) else 0
      ok = search_resp.status_code < 400
      emoji = "✅" if ok else ("⚠️" if has_decode_error else "❌")
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
  
  assistant_id = None
  
  # Create assistant with file_search tool and vector store
  try:
    model_name = config.AZURE_OPENAI_DEFAULT_MODEL_DEPLOYMENT_NAME if config.OPENAI_SERVICE_TYPE == "azure_openai" else config.OPENAI_DEFAULT_MODEL_NAME
    if not model_name or not vector_store_id:
      results["/assistants (POST create)"] = {"Result": "Skipped (missing model name or vector store)", "Details": ""}
    else:
      assistant_name = f"selftest-assistant-{uuid.uuid4().hex[:8]}"
      assistant_payload = {
        "model": model_name,
        "name": assistant_name,
        "instructions": "You are a helpful assistant that can search through files to answer questions about their content.",
        "tools": [{"type": "file_search"}],
        "tool_resources": {"file_search": {"vector_store_ids": [vector_store_id]}}
      }
      create_assistant_req = DummyRequestJson(assistant_payload)
      create_assistant_resp, _milliseconds = await proxy_request(create_assistant_req, build_openai_endpoint_path("assistants"), "POST", timeout_seconds=timeout_seconds)
      try:
        create_assistant_data = json.loads(create_assistant_resp.body.decode("utf-8", errors="replace")) if create_assistant_resp.body else {}
        has_decode_error = False
      except (UnicodeDecodeError, json.JSONDecodeError):
        create_assistant_data = {}
        has_decode_error = True
      assistant_id = create_assistant_data.get("id")
      ok = bool(assistant_id)
      emoji = "✅" if ok else ("⚠️" if has_decode_error else "❌")
      main = ("OK" if ok else "No assistant id returned") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"name: '{format_for_display(assistant_name)}' id: '{format_for_display(assistant_id)}' with file_search"
      else:
        details = get_error_details(create_assistant_resp, create_assistant_data)
      results["/assistants (POST create)"] = {"Result": f"{emoji} {main}", "Details": details}
  except Exception as e:
    results["/assistants (POST create)"] = {"Result": f"Error: {str(e)}", "Details": ""}

  # List assistants
  try:
    list_resp, _milliseconds = await proxy_request(request, build_openai_endpoint_path("assistants"), "GET", timeout_seconds=timeout_seconds)
    try:
      list_data = json.loads(list_resp.body.decode("utf-8", errors="replace")) if list_resp.body else {}
      assistants_count = len(list_data.get("data", [])) if isinstance(list_data, dict) else 0
      has_decode_error = False
    except (UnicodeDecodeError, json.JSONDecodeError):
      list_data = {}
      assistants_count = 0
      has_decode_error = True
    ok = list_resp.status_code < 400
    emoji = "✅" if ok else ("⚠️" if has_decode_error else "❌")
    main = ("OK" if ok else f"HTTP {list_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
    if ok:
      details = f"assistants: {assistants_count}"
    else:
      details = get_error_details(list_resp, list_data)
    results["/assistants (GET)"] = {"Result": f"{emoji} {main}", "Details": details}
  except Exception as e:
    results["/assistants (GET)"] = {"Result": f"Error: {str(e)}", "Details": ""}
    
  thread_id = None
  message_id = None
  
  # Create thread
  try:
    create_thread_req = DummyRequestJson({})
    create_thread_resp, _milliseconds = await proxy_request(create_thread_req, build_openai_endpoint_path("threads"), "POST", timeout_seconds=timeout_seconds)
    try:
      create_thread_data = json.loads(create_thread_resp.body.decode("utf-8", errors="replace")) if create_thread_resp.body else {}
      has_decode_error = False
    except (UnicodeDecodeError, json.JSONDecodeError):
      create_thread_data = {}
      has_decode_error = True
    thread_id = create_thread_data.get("id")
    ok = bool(thread_id)
    emoji = "✅" if ok else ("⚠️" if has_decode_error else "❌")
    main = ("OK" if ok else "No thread id returned") + f" ({format_milliseconds(_milliseconds)})"
    if ok:
      details = f"id: '{format_for_display(thread_id)}'"
    else:
      details = get_error_details(create_thread_resp, create_thread_data)
    results["/threads (POST create)"] = {"Result": f"{emoji} {main}", "Details": details}
  except Exception as e:
    results["/threads (POST create)"] = {"Result": f"Error: {str(e)}", "Details": ""}
    
  # Get thread
  try:
    if thread_id:
      get_thread_resp, _milliseconds = await proxy_request(request, build_openai_endpoint_path(f"threads/{thread_id}"), "GET", timeout_seconds=timeout_seconds)
      try:
        get_thread_data = json.loads(get_thread_resp.body.decode("utf-8", errors="replace")) if get_thread_resp.body else {}
        has_decode_error = False
      except (UnicodeDecodeError, json.JSONDecodeError):
        get_thread_data = {}
        has_decode_error = True
      ok = get_thread_resp.status_code < 400
      emoji = "✅" if ok else ("⚠️" if has_decode_error else "❌")
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
  
  # Create thread message asking about file content
  try:
    if thread_id:
      message_content = "What is Arilena Drovik's birthday?"
      create_message_req = DummyRequestJson({"role": "user", "content": message_content})
      create_message_resp, _milliseconds = await proxy_request(create_message_req, build_openai_endpoint_path(f"threads/{thread_id}/messages"), "POST", timeout_seconds=timeout_seconds)
      try:
        create_message_data = json.loads(create_message_resp.body.decode("utf-8", errors="replace")) if create_message_resp.body else {}
        has_decode_error = False
      except (UnicodeDecodeError, json.JSONDecodeError):
        create_message_data = {}
        has_decode_error = True
      message_id = create_message_data.get("id")
      ok = bool(message_id)
      emoji = "✅" if ok else ("⚠️" if has_decode_error else "❌")
      main = ("OK" if ok else "No message id returned") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"content: '{format_for_display(message_content, 50)}' id: '{format_for_display(message_id)}'"
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
      list_messages_resp, _milliseconds = await proxy_request(request, build_openai_endpoint_path(f"threads/{thread_id}/messages"), "GET", timeout_seconds=timeout_seconds)
      try:
        list_messages_data = json.loads(list_messages_resp.body.decode("utf-8", errors="replace")) if list_messages_resp.body else {}
        messages_count = len(list_messages_data.get("data", [])) if isinstance(list_messages_data, dict) else 0
        has_decode_error = False
      except (UnicodeDecodeError, json.JSONDecodeError):
        list_messages_data = {}
        messages_count = 0
        has_decode_error = True
      ok = list_messages_resp.status_code < 400
      emoji = "✅" if ok else ("⚠️" if has_decode_error else "❌")
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
      get_message_resp, _milliseconds = await proxy_request(request, build_openai_endpoint_path(f"threads/{thread_id}/messages/{message_id}"), "GET", timeout_seconds=timeout_seconds)
      try:
        get_message_data = json.loads(get_message_resp.body.decode("utf-8", errors="replace")) if get_message_resp.body else {}
        has_decode_error = False
      except (UnicodeDecodeError, json.JSONDecodeError):
        get_message_data = {}
        has_decode_error = True
      ok = get_message_resp.status_code < 400
      emoji = "✅" if ok else ("⚠️" if has_decode_error else "❌")
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
  
  run_id = None
  
  # Create thread run (requires assistant)
  try:
    if thread_id and assistant_id:
      create_run_req = DummyRequestJson({"assistant_id": assistant_id})
      create_run_resp, _milliseconds = await proxy_request(create_run_req, build_openai_endpoint_path(f"threads/{thread_id}/runs"), "POST", timeout_seconds=timeout_seconds)
      try:
        create_run_data = json.loads(create_run_resp.body.decode("utf-8", errors="replace")) if create_run_resp.body else {}
        has_decode_error = False
      except (UnicodeDecodeError, json.JSONDecodeError):
        create_run_data = {}
        has_decode_error = True
      run_id = create_run_data.get("id")
      ok = bool(run_id)
      emoji = "✅" if ok else ("⚠️" if has_decode_error else "❌")
      main = ("OK" if ok else "No run id returned") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"thread_id: '{format_for_display(thread_id)}' assistant_id: '{format_for_display(assistant_id)}' run_id: '{format_for_display(run_id)}'"
      else:
        details = get_error_details(create_run_resp, create_run_data)
      results["/threads/{id}/runs (POST create)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/threads/{id}/runs (POST create)"] = {"Result": "Skipped (missing thread or assistant id)", "Details": ""}
  except Exception as e:
    results["/threads/{id}/runs (POST create)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # List thread runs
  try:
    if thread_id:
      list_runs_resp, _milliseconds = await proxy_request(request, build_openai_endpoint_path(f"threads/{thread_id}/runs"), "GET", timeout_seconds=timeout_seconds)
      try:
        list_runs_data = json.loads(list_runs_resp.body.decode("utf-8", errors="replace")) if list_runs_resp.body else {}
        runs_count = len(list_runs_data.get("data", [])) if isinstance(list_runs_data, dict) else 0
        has_decode_error = False
      except (UnicodeDecodeError, json.JSONDecodeError):
        list_runs_data = {}
        runs_count = 0
        has_decode_error = True
      ok = list_runs_resp.status_code < 400
      emoji = "✅" if ok else ("⚠️" if has_decode_error else "❌")
      main = ("OK" if ok else f"HTTP {list_runs_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"runs: {runs_count}"
      else:
        details = get_error_details(list_runs_resp, list_runs_data)
      results["/threads/{id}/runs (GET)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/threads/{id}/runs (GET)"] = {"Result": "Skipped (missing thread id)", "Details": ""}
  except Exception as e:
    results["/threads/{id}/runs (GET)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # Get thread run and wait for completion
  try:
    if thread_id and run_id:
      # Wait for run to complete with proper polling and timeout
      run_completed = False; final_status = "unknown"
      max_wait_seconds = 15; elapsed_seconds = 0
      
      # Poll run status until completion or timeout
      while elapsed_seconds < max_wait_seconds:
        try:
          get_run_resp, _ms = await proxy_request(request, build_openai_endpoint_path(f"threads/{thread_id}/runs/{run_id}"), "GET", timeout_seconds=5)
          if get_run_resp.status_code < 400:
            try:
              get_run_data = json.loads(get_run_resp.body.decode("utf-8", errors="replace")) if get_run_resp.body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
              get_run_data = {}
            final_status = get_run_data.get("status", "unknown")
            if final_status == 'completed':
              run_completed = True
              break
            elif final_status in ['requires_action', 'failed', 'cancelled', 'expired', 'incomplete']:
              break
          await asyncio.sleep(1)
          elapsed_seconds += 1
        except Exception:
          break
      
      # Final status check
      get_run_resp, _milliseconds = await proxy_request(request, build_openai_endpoint_path(f"threads/{thread_id}/runs/{run_id}"), "GET", timeout_seconds=timeout_seconds)
      try:
        get_run_data = json.loads(get_run_resp.body.decode("utf-8", errors="replace")) if get_run_resp.body else {}
        has_decode_error = False
      except (UnicodeDecodeError, json.JSONDecodeError):
        get_run_data = {}
        has_decode_error = True
      ok = get_run_resp.status_code < 400
      run_status = get_run_data.get("status", "unknown")
      is_timeout = not run_completed and run_status == "unknown"
      emoji = "⚠️" if is_timeout else ("✅" if ok else ("⚠️" if has_decode_error else "❌"))
      main = ("OK" if ok else f"HTTP {get_run_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        completion_note = f" ({'completed' if run_completed else 'timeout'})"
        details = f"thread_id: '{format_for_display(thread_id)}' run_id: '{format_for_display(run_id)}' status: '{run_status}'{completion_note}"
      else:
        details = get_error_details(get_run_resp, get_run_data)
      results["/threads/{id}/runs/{run_id} (GET)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/threads/{id}/runs/{run_id} (GET)"] = {"Result": "Skipped (missing ids)", "Details": ""}
  except Exception as e:
    results["/threads/{id}/runs/{run_id} (GET)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # Get assistant response (if run completed successfully)
  try:
    if thread_id and run_completed and final_status == "completed":
      # Get updated messages to see assistant's response
      list_messages_after_resp, _milliseconds = await proxy_request(request, build_openai_endpoint_path(f"threads/{thread_id}/messages"), "GET", timeout_seconds=timeout_seconds)
      try:
        list_messages_after_data = json.loads(list_messages_after_resp.body.decode("utf-8", errors="replace")) if list_messages_after_resp.body else {}
        messages = list_messages_after_data.get("data", []) if isinstance(list_messages_after_data, dict) else []
        # Find the latest assistant message
        assistant_response = None
        for msg in messages:
          if isinstance(msg, dict) and msg.get("role") == "assistant":
            content = msg.get("content", [])
            if isinstance(content, list) and len(content) > 0:
              text_content = content[0].get("text", {}).get("value", "") if isinstance(content[0], dict) else ""
              if text_content:
                assistant_response = text_content
                break
      except (UnicodeDecodeError, json.JSONDecodeError):
        list_messages_after_data = {}
        assistant_response = None
      ok = list_messages_after_resp.status_code < 400 and assistant_response is not None
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {list_messages_after_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"response: '{format_for_display(assistant_response, 60)}'"
      else:
        details = get_error_details(list_messages_after_resp, list_messages_after_data) if not assistant_response else "No assistant response found"
      results["/threads/{id}/messages (GET assistant response)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/threads/{id}/messages (GET assistant response)"] = {"Result": "Skipped (run not completed)", "Details": ""}
  except Exception as e:
    results["/threads/{id}/messages (GET assistant response)"] = {"Result": f"Error: {str(e)}", "Details": ""}

  # List run steps
  try:
    if thread_id and run_id:
      list_steps_resp, _milliseconds = await proxy_request(request, build_openai_endpoint_path(f"threads/{thread_id}/runs/{run_id}/steps"), "GET", timeout_seconds=timeout_seconds)
      try:
        list_steps_data = json.loads(list_steps_resp.body.decode("utf-8", errors="replace")) if list_steps_resp.body else {}
        steps_count = len(list_steps_data.get("data", [])) if isinstance(list_steps_data, dict) else 0
      except (UnicodeDecodeError, json.JSONDecodeError):
        list_steps_data = {}
        steps_count = 0
      ok = list_steps_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {list_steps_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"steps: {steps_count}"
      else:
        details = get_error_details(list_steps_resp, list_steps_data)
      results["/threads/{id}/runs/{run_id}/steps (GET)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/threads/{id}/runs/{run_id}/steps (GET)"] = {"Result": "Skipped (missing ids)", "Details": ""}
  except Exception as e:
    results["/threads/{id}/runs/{run_id}/steps (GET)"] = {"Result": f"Error: {str(e)}", "Details": ""}
    
  # Delete thread
  try:
    if thread_id:
      delete_thread_resp, _milliseconds = await proxy_request(DummyRequest(), build_openai_endpoint_path(f"threads/{thread_id}"), "DELETE", timeout_seconds=timeout_seconds)
      ok = delete_thread_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {delete_thread_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"id: '{format_for_display(thread_id)}'"
      else:
        try:
          delete_thread_data = json.loads(delete_thread_resp.body.decode("utf-8", errors="replace")) if delete_thread_resp.body else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
          delete_thread_data = {}
        details = get_error_details(delete_thread_resp, delete_thread_data)
      results["/threads/{id} (DELETE)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/threads/{id} (DELETE)"] = {"Result": "Skipped (missing id)", "Details": ""}
  except Exception as e:
    results["/threads/{id} (DELETE)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # Delete assistant
  try:
    if assistant_id:
      delete_assistant_resp, _milliseconds = await proxy_request(DummyRequest(), build_openai_endpoint_path(f"assistants/{assistant_id}"), "DELETE", timeout_seconds=timeout_seconds)
      ok = delete_assistant_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {delete_assistant_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"id: '{format_for_display(assistant_id)}'"
      else:
        try:
          delete_assistant_data = json.loads(delete_assistant_resp.body.decode("utf-8", errors="replace")) if delete_assistant_resp.body else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
          delete_assistant_data = {}
        details = get_error_details(delete_assistant_resp, delete_assistant_data)
      results["/assistants/{id} (DELETE)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/assistants/{id} (DELETE)"] = {"Result": "Skipped (missing id)", "Details": ""}
  except Exception as e:
    results["/assistants/{id} (DELETE)"] = {"Result": f"Error: {str(e)}", "Details": ""}
    

  # Vector Store Attributes Tests
  vector_store_with_attrs_id = None
  file_with_attrs_id = None
  
  # Create vector store with attributes
  try:
    long_text_512 = "A" * 512  # 512 character text
    test_metadata = {
      "short_text": "test_value",
      "long_text_512": long_text_512,
    }
    vs_attrs_req = DummyRequestJson({"name": "test-vector-store-attrs", "metadata": test_metadata})
    create_vs_attrs_resp, _milliseconds = await proxy_request(vs_attrs_req, build_openai_endpoint_path("vector_stores"), "POST", timeout_seconds=timeout_seconds)
    try:
      create_vs_attrs_data = json.loads(create_vs_attrs_resp.body.decode("utf-8", errors="replace")) if create_vs_attrs_resp.body else {}
      has_decode_error = False
    except (UnicodeDecodeError, json.JSONDecodeError):
      create_vs_attrs_data = {}
      has_decode_error = True
    ok = create_vs_attrs_resp.status_code < 400
    emoji = "✅" if ok else ("⚠️" if has_decode_error else "❌")
    main = ("OK" if ok else f"HTTP {create_vs_attrs_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
    if ok:
      vector_store_with_attrs_id = create_vs_attrs_data.get("id")
      metadata = create_vs_attrs_data.get("metadata", {})
      details = f"id: '{format_for_display(vector_store_with_attrs_id)}' metadata_count: {len(metadata)}"
    else:
      details = get_error_details(create_vs_attrs_resp, create_vs_attrs_data)
    results["/vector_stores (POST with attributes)"] = {"Result": f"{emoji} {main}", "Details": details}
  except Exception as e:
    results["/vector_stores (POST with attributes)"] = {"Result": f"Error: {str(e)}", "Details": ""}

  # Get vector store with attributes
  try:
    if vector_store_with_attrs_id:
      get_vs_attrs_resp, _milliseconds = await proxy_request(DummyRequest(), build_openai_endpoint_path(f"vector_stores/{vector_store_with_attrs_id}"), "GET", timeout_seconds=timeout_seconds)
      try:
        get_vs_attrs_data = json.loads(get_vs_attrs_resp.body.decode("utf-8", errors="replace")) if get_vs_attrs_resp.body else {}
        has_decode_error = False
      except (UnicodeDecodeError, json.JSONDecodeError):
        get_vs_attrs_data = {}
        has_decode_error = True
      ok = get_vs_attrs_resp.status_code < 400
      emoji = "✅" if ok else ("⚠️" if has_decode_error else "❌")
      main = ("OK" if ok else f"HTTP {get_vs_attrs_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        metadata = get_vs_attrs_data.get("metadata", {})
        # Validate all attribute types
        short_text_match = metadata.get("short_text") == test_metadata["short_text"]
        long_text_match = metadata.get("long_text_512") == test_metadata["long_text_512"]
        all_attrs_match = all([short_text_match, long_text_match])
        details = f"id: '{format_for_display(vector_store_with_attrs_id)}' attrs_count: {len(metadata)}; all_match: {all_attrs_match}"
      else:
        details = get_error_details(get_vs_attrs_resp, get_vs_attrs_data)
      results["/vector_stores/{id} (GET with attributes)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/vector_stores/{id} (GET with attributes)"] = {"Result": "Skipped (missing id)", "Details": ""}
  except Exception as e:
    results["/vector_stores/{id} (GET with attributes)"] = {"Result": f"Error: {str(e)}", "Details": ""}

  # Add file to vector store with attributes
  try:
    if vector_store_with_attrs_id and uploaded_file_id:
      file_long_text_512 = "B" * 512  # Different 512 character text for files
      file_test_attributes = {
        "file_short_text": "file_test_value",
        "file_long_text_512": file_long_text_512,
        "file_integer_number": 99,
        "file_float_number": 2.71828,
        "file_date_iso": "2024-02-20T14:45:30Z",
        "is_test": True
      }
      file_attrs_req = DummyRequestJson({"file_id": uploaded_file_id, "attributes": file_test_attributes})
      add_file_attrs_resp, _milliseconds = await proxy_request(file_attrs_req, build_openai_endpoint_path(f"vector_stores/{vector_store_with_attrs_id}/files"), "POST", timeout_seconds=timeout_seconds)
      try:
        add_file_attrs_data = json.loads(add_file_attrs_resp.body.decode("utf-8", errors="replace")) if add_file_attrs_resp.body else {}
        has_decode_error = False
      except (UnicodeDecodeError, json.JSONDecodeError):
        add_file_attrs_data = {}
        has_decode_error = True
      ok = add_file_attrs_resp.status_code < 400
      emoji = "✅" if ok else ("⚠️" if has_decode_error else "❌")
      main = ("OK" if ok else f"HTTP {add_file_attrs_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        file_with_attrs_id = add_file_attrs_data.get("id")
        attributes = add_file_attrs_data.get("attributes", {})
        details = f"vector_store_id: '{format_for_display(vector_store_with_attrs_id)}' file_id: '{format_for_display(file_with_attrs_id)}' attrs_count: {len(attributes)}"
      else:
        details = get_error_details(add_file_attrs_resp, add_file_attrs_data)
      results["/vector_stores/{id}/files (POST with attributes)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/vector_stores/{id}/files (POST with attributes)"] = {"Result": "Skipped (missing ids)", "Details": ""}
  except Exception as e:
    results["/vector_stores/{id}/files (POST with attributes)"] = {"Result": f"Error: {str(e)}", "Details": ""}

  # Get file from vector store with attributes
  try:
    if vector_store_with_attrs_id and file_with_attrs_id:
      get_file_attrs_resp, _milliseconds = await proxy_request(DummyRequest(), build_openai_endpoint_path(f"vector_stores/{vector_store_with_attrs_id}/files/{file_with_attrs_id}"), "GET", timeout_seconds=timeout_seconds)
      try:
        get_file_attrs_data = json.loads(get_file_attrs_resp.body.decode("utf-8", errors="replace")) if get_file_attrs_resp.body else {}
        has_decode_error = False
      except (UnicodeDecodeError, json.JSONDecodeError):
        get_file_attrs_data = {}
        has_decode_error = True
      ok = get_file_attrs_resp.status_code < 400
      if ok:
        attributes = get_file_attrs_data.get("attributes", {})
        # Validate all file attribute types
        file_short_text_match = attributes.get("file_short_text") == file_test_attributes["file_short_text"]
        file_long_text_match = attributes.get("file_long_text_512") == file_test_attributes["file_long_text_512"]
        file_integer_match = attributes.get("file_integer_number") == file_test_attributes["file_integer_number"]
        file_float_match = attributes.get("file_float_number") == file_test_attributes["file_float_number"]
        file_date_match = attributes.get("file_date_iso") == file_test_attributes["file_date_iso"]
        file_boolean_match = attributes.get("is_test") == file_test_attributes["is_test"]
        all_file_attrs_match = all([file_short_text_match, file_long_text_match, file_integer_match, file_float_match, file_date_match, file_boolean_match])
        # Test passes only if HTTP OK AND attributes are correctly preserved
        test_success = ok and len(attributes) > 0 and all_file_attrs_match
        emoji = "✅" if test_success else "❌"
        main = ("OK" if ok else f"HTTP {get_file_attrs_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
        details = f"vector_store_id: '{format_for_display(vector_store_with_attrs_id)}' file_id: '{format_for_display(file_with_attrs_id)}' attrs_count: {len(attributes)}; all_match: {all_file_attrs_match}"
      else:
        emoji = "⚠️" if has_decode_error else "❌"
        main = f"HTTP {get_file_attrs_resp.status_code}" + f" ({format_milliseconds(_milliseconds)})"
        details = get_error_details(get_file_attrs_resp, get_file_attrs_data)
      results["/vector_stores/{id}/files/{file_id} (GET with attributes)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/vector_stores/{id}/files/{file_id} (GET with attributes)"] = {"Result": "Skipped (missing ids)", "Details": ""}
  except Exception as e:
    results["/vector_stores/{id}/files/{file_id} (GET with attributes)"] = {"Result": f"Error: {str(e)}", "Details": ""}

  # Remove file from vector store
  try:
    if vector_store_id and uploaded_file_id:
      delvf_resp, _milliseconds = await proxy_request(DummyRequest(), build_openai_endpoint_path(f"vector_stores/{vector_store_id}/files/{uploaded_file_id}"), "DELETE", timeout_seconds=timeout_seconds)
      ok = delvf_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {delvf_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"vector_store_id: '{format_for_display(vector_store_id)}' file_id: '{format_for_display(uploaded_file_id)}'"
      else:
        try:
          delvf_data = json.loads(delvf_resp.body.decode("utf-8", errors="replace")) if delvf_resp.body else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
          delvf_data = {}
        details = get_error_details(delvf_resp, delvf_data)
      results["/vector_stores/{id}/files/{file_id} (DELETE)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/vector_stores/{id}/files/{file_id} (DELETE)"] = {"Result": "Skipped (missing ids)", "Details": ""}
  except Exception as e:
    results["/vector_stores/{id}/files/{file_id} (DELETE)"] = {"Result": f"Error: {str(e)}", "Details": ""}

  # Remove file with attributes from vector store
  try:
    if vector_store_with_attrs_id and file_with_attrs_id:
      delvf_attrs_resp, _milliseconds = await proxy_request(DummyRequest(), build_openai_endpoint_path(f"vector_stores/{vector_store_with_attrs_id}/files/{file_with_attrs_id}"), "DELETE", timeout_seconds=timeout_seconds)
      ok = delvf_attrs_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {delvf_attrs_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"vector_store_id: '{format_for_display(vector_store_with_attrs_id)}' file_id: '{format_for_display(file_with_attrs_id)}'"
      else:
        try:
          delvf_attrs_data = json.loads(delvf_attrs_resp.body.decode("utf-8", errors="replace")) if delvf_attrs_resp.body else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
          delvf_attrs_data = {}
        details = get_error_details(delvf_attrs_resp, delvf_attrs_data)
      results["/vector_stores/{id}/files/{file_id} (DELETE with attributes)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/vector_stores/{id}/files/{file_id} (DELETE with attributes)"] = {"Result": "Skipped (missing ids)", "Details": ""}
  except Exception as e:
    results["/vector_stores/{id}/files/{file_id} (DELETE with attributes)"] = {"Result": f"Error: {str(e)}", "Details": ""}

  # Delete vector store with attributes
  try:
    if vector_store_with_attrs_id:
      delvs_attrs_resp, _milliseconds = await proxy_request(DummyRequest(), build_openai_endpoint_path(f"vector_stores/{vector_store_with_attrs_id}"), "DELETE", timeout_seconds=timeout_seconds)
      ok = delvs_attrs_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {delvs_attrs_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"id: '{format_for_display(vector_store_with_attrs_id)}'"
      else:
        try:
          delvs_attrs_data = json.loads(delvs_attrs_resp.body.decode("utf-8", errors="replace")) if delvs_attrs_resp.body else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
          delvs_attrs_data = {}
        details = get_error_details(delvs_attrs_resp, delvs_attrs_data)
      results["/vector_stores/{id} (DELETE with attributes)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/vector_stores/{id} (DELETE with attributes)"] = {"Result": "Skipped (missing id)", "Details": ""}
  except Exception as e:
    results["/vector_stores/{id} (DELETE with attributes)"] = {"Result": f"Error: {str(e)}", "Details": ""}

  # Delete main vector store
  try:
    if vector_store_id:
      delvs_resp, _milliseconds = await proxy_request(DummyRequest(), build_openai_endpoint_path(f"vector_stores/{vector_store_id}"), "DELETE", timeout_seconds=timeout_seconds)
      ok = delvs_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {delvs_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"id: '{format_for_display(vector_store_id)}'"
      else:
        try:
          delvs_data = json.loads(delvs_resp.body.decode("utf-8", errors="replace")) if delvs_resp.body else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
          delvs_data = {}
        details = get_error_details(delvs_resp, delvs_data)
      results["/vector_stores/{id} (DELETE)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/vector_stores/{id} (DELETE)"] = {"Result": "Skipped (missing id)", "Details": ""}
  except Exception as e:
    results["/vector_stores/{id} (DELETE)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # Delete file
  try:
    if uploaded_file_id:
      delf_resp, _milliseconds = await proxy_request(DummyRequest(), build_openai_endpoint_path(f"files/{uploaded_file_id}"), "DELETE", timeout_seconds=timeout_seconds)
      ok = delf_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {delf_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      if ok:
        details = f"id: '{format_for_display(uploaded_file_id)}'"
      else:
        try:
          delf_data = json.loads(delf_resp.body.decode("utf-8", errors="replace")) if delf_resp.body else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
          delf_data = {}
        details = get_error_details(delf_resp, delf_data)
      results["/files/{id} (DELETE)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/files/{id} (DELETE)"] = {"Result": "Skipped (missing id)", "Details": ""}
  except Exception as e:
    results["/files/{id} (DELETE)"] = {"Result": f"Error: {str(e)}", "Details": ""}

  # Generate HTML
  html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
  <title>OpenAI Proxy Self Test Results</title>
  <link rel='stylesheet' href='/static/css/styles.css'>
  <script src='/static/js/htmx.min.js'></script>
</head><body>
"""
  html += f"<h1>OpenAI Proxy Self Test Results ({config.OPENAI_SERVICE_TYPE})</h1>"
  html += convert_to_html_table(results)
  html += "<p><b>Configuration:</b></p>"
  html += convert_to_html_table(format_config_for_displaying(config))
  html += "</body></html>"
  try:
    return HTMLResponse(content=html)
  finally:
    await log_function_footer(log_data)
