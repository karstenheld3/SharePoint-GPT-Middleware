import os
import json
import uuid
import httpx
import logging
import datetime
from typing import Any, Dict, Optional
from fastapi import APIRouter, Request, HTTPException, Header, File, UploadFile, Form
from fastapi.responses import StreamingResponse, Response, HTMLResponse
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from utils import *

router = APIRouter()

# OpenAI / Azure OpenAI configuration
OPENAI_SERVICE_TYPE = os.getenv("OPENAI_SERVICE_TYPE", "openai")
AZURE_OPENAI_USE_KEY_AUTHENTICATION = os.getenv("AZURE_OPENAI_USE_KEY_AUTHENTICATION", "true").lower() == "true"
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORGANIZATION = os.getenv("OPENAI_ORGANIZATION")

logger = logging.getLogger(__name__)

# Initialize Azure AD credentials if needed
if OPENAI_SERVICE_TYPE == "azure_openai" and not AZURE_OPENAI_USE_KEY_AUTHENTICATION:
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
  if OPENAI_SERVICE_TYPE == "azure_openai":
    if not AZURE_OPENAI_ENDPOINT:
      raise HTTPException(status_code=500, detail="Azure OpenAI endpoint not configured")
    if AZURE_OPENAI_USE_KEY_AUTHENTICATION and not AZURE_OPENAI_API_KEY:
      raise HTTPException(status_code=500, detail="Azure OpenAI API key not configured")
    if not AZURE_OPENAI_USE_KEY_AUTHENTICATION and not token_provider:
      raise HTTPException(status_code=500, detail="Azure AD authentication failed")
  else:
    if not OPENAI_API_KEY:
      raise HTTPException(status_code=500, detail="OpenAI API key not configured")
  
  # Construct target URL
  if OPENAI_SERVICE_TYPE == "azure_openai":
    base = AZURE_OPENAI_ENDPOINT.rstrip('/')
    if "/openai" not in base:
      base = f"{base}/openai"
    target_url = f"{base}/{target_path.lstrip('/')}"
    if "api-version" not in target_url:
      separator = "&" if "?" in target_url else "?"
      target_url += f"{separator}api-version={AZURE_OPENAI_API_VERSION}"
  else:
    target_url = f"https://api.openai.com/v1/{target_path.lstrip('/')}"
  
  # Prepare headers
  headers: Dict[str, str] = {}
  if OPENAI_SERVICE_TYPE == "azure_openai":
    if AZURE_OPENAI_USE_KEY_AUTHENTICATION:
      headers["api-key"] = AZURE_OPENAI_API_KEY
    else:
      token = token_provider()
      headers["Authorization"] = f"Bearer {token}"
  else:
    headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    if OPENAI_ORGANIZATION:
      headers["OpenAI-Organization"] = OPENAI_ORGANIZATION
  
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
      service_type = "Azure OpenAI" if OPENAI_SERVICE_TYPE == "azure_openai" else "OpenAI"
      auth_type = "Key" if AZURE_OPENAI_USE_KEY_AUTHENTICATION else "Token"
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
    raise HTTPException(status_code=502, detail=f"Error connecting to {OPENAI_SERVICE_TYPE}")
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
async def upload_file(file: UploadFile = File(...), purpose: str = Form(...), api_version: str = AZURE_OPENAI_API_VERSION):
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
    target_path = f"files?api-version={api_version}" if OPENAI_SERVICE_TYPE == "azure_openai" else "files"
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

# ============================================================================
# SELF TEST (callable utility; exposed at app-level, not under /openai)
# ============================================================================

async def self_test(request: Request):
  """Test all endpoints and return results as simple HTML."""
  log_data = log_function_header("self_test")
  results = {}
  try:
    timeout_seconds = float(request.query_params.get("timeoutSecs")) if "timeoutSecs" in request.query_params else None
  except Exception:
    timeout_seconds = None
  if timeout_seconds is None: timeout_seconds = 120
  
  # Generic, runtime capability probe (no hard-coding). Uses short timeouts to avoid long hangs.
  async def probe_supported(method: str, target_path: str, probe_timeout: float = 5.0) -> str:
    """Return 'supported', 'unsupported', or 'indeterminate' for the given method/path."""
    # Try the actual method directly with a short timeout and minimal request body
    try:
      if method == "POST":
        # For POST, send minimal valid request to avoid 400 errors
        model_name = os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT_NAME") if OPENAI_SERVICE_TYPE == "azure_openai" else os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
        if model_name and "responses" in target_path:
          probe_req = DummyRequestJson({"model": model_name, "input": "test"})
          resp, _milliseconds = await proxy_request(probe_req, target_path, method, timeout_seconds=probe_timeout)
        else:
          resp, _milliseconds = await proxy_request(DummyRequest(), target_path, method, timeout_seconds=probe_timeout)
      else:
        resp, _milliseconds = await proxy_request(request, target_path, method, timeout_seconds=probe_timeout)
      
      sc = resp.status_code
      # If we get anything other than 404/405/408, assume endpoint is reachable/supported
      if sc not in (404, 405, 408): return "supported"
      # 404/405 likely indicate unsupported, 408 is timeout
      if sc in (404, 405): return "unsupported"
    except Exception:
      # Network or other error
      pass
    return "indeterminate"

  # Build path helper: append api-version only for Azure
  def build_azure_openai_endpoint_path(base_path: str) -> str:
    return f"{base_path}?api-version={AZURE_OPENAI_API_VERSION}" if OPENAI_SERVICE_TYPE == "azure_openai" else base_path
  
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
  
  # Responses API test: probe POST, then create a response
  try:
    resp_post_path = build_azure_openai_endpoint_path("responses")
    post_support = await probe_supported("POST", resp_post_path)
    emoji = "✅" if post_support == "supported" else "❌"
    results["/responses (POST) probe"] = {"Result": f"{emoji} {post_support}", "Details": "method: POST path: responses"}
    # Build minimal request body
    model_name = os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT_NAME") if OPENAI_SERVICE_TYPE == "azure_openai" else os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
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
      details = f"Q: '{format_for_display(question)}' A: '{format_for_display(answer, 40)}'"
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
  
  try:
    resp, _milliseconds = await proxy_request(request, build_azure_openai_endpoint_path("vector_stores"), "GET", timeout_seconds=timeout_seconds)
    try:
      _data = json.loads(resp.body.decode("utf-8")) if resp.body else {}
      _count = len(_data.get("data", [])) if isinstance(_data, dict) else 0
    except (UnicodeDecodeError, json.JSONDecodeError):
      _data = {}
      _count = 0
    ok = resp.status_code < 400
    emoji = "✅" if ok else "❌"
    main = ("OK" if ok else f"HTTP {resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
    results["/vector_stores (GET)"] = {"Result": f"{emoji} {main}", "Details": f"items: {_count}"}
  except Exception as e:
    results["/vector_stores (GET)"] = {"Result": f"Error: {str(e)}", "Details": ""}
    
  
  api_version = AZURE_OPENAI_API_VERSION
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
    details = f"filename: 'selftest.txt' id: '{format_for_display(uploaded_file_id)}'"
    results["/files (POST upload)"] = {"Result": f"{emoji} {main}", "Details": details}
  except Exception as e:
    results["/files (POST upload)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
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
    details = f"name: '{format_for_display(vs_name)}' id: '{format_for_display(vector_store_id)}'"
    results["/vector_stores (POST create)"] = {"Result": f"{emoji} {main}", "Details": details}
  except Exception as e:
    results["/vector_stores (POST create)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # Add file to vector store
  try:
    if vector_store_id and uploaded_file_id:
      add_req = DummyRequestJson({"file_id": uploaded_file_id})
      add_resp, _milliseconds = await proxy_request(add_req, build_azure_openai_endpoint_path(f"vector_stores/{vector_store_id}/files"), "POST", timeout_seconds=timeout_seconds)
      ok = add_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {add_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      details = f"vector_store_id: '{format_for_display(vector_store_id)}' file_id: '{format_for_display(uploaded_file_id)}'"
      results["/vector_stores/{id}/files (POST add)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/vector_stores/{id}/files (POST add)"] = {"Result": "Skipped (missing ids)", "Details": ""}
  except Exception as e:
    results["/vector_stores/{id}/files (POST add)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # Remove file from vector store
  try:
    if vector_store_id and uploaded_file_id:
      delvf_resp, _milliseconds = await proxy_request(DummyRequest(), build_azure_openai_endpoint_path(f"vector_stores/{vector_store_id}/files/{uploaded_file_id}"), "DELETE", timeout_seconds=timeout_seconds)
      ok = delvf_resp.status_code < 400
      emoji = "✅" if ok else "❌"
      main = ("OK" if ok else f"HTTP {delvf_resp.status_code}") + f" ({format_milliseconds(_milliseconds)})"
      details = f"vector_store_id: '{format_for_display(vector_store_id)}' file_id: '{format_for_display(uploaded_file_id)}'"
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
      details = f"id: '{format_for_display(vector_store_id)}'"
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
      details = f"id: '{format_for_display(uploaded_file_id)}'"
      results["/files/{id} (DELETE)"] = {"Result": f"{emoji} {main}", "Details": details}
    else:
      results["/files/{id} (DELETE)"] = {"Result": "Skipped (missing id)", "Details": ""}
  except Exception as e:
    results["/files/{id} (DELETE)"] = {"Result": f"Error: {str(e)}", "Details": ""}
  
  # Generate HTML
  html = "<html><body style='font-family: Arial, sans-serif;'>"
  html += "<h2>OpenAI Proxy Self Test Results</h2>"
  html += f"<p><b>Service Type:</b> {OPENAI_SERVICE_TYPE}</p>"
  if OPENAI_SERVICE_TYPE == 'azure_openai':
    html += f"<p><b>Authentication:</b> {'Key' if AZURE_OPENAI_USE_KEY_AUTHENTICATION else 'Azure AD Token'}</p>"
    html += f"<p><b>Endpoint:</b> {AZURE_OPENAI_ENDPOINT}</p>"
  html += convert_to_nested_html_table(results)
  html += "</body></html>"
  try:
    return HTMLResponse(content=html)
  finally:
    await log_function_footer(log_data)
