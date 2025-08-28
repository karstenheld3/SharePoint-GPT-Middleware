import os
import inspect
import logging
from typing import Any, Optional
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, Response, HTMLResponse
from dotenv import load_dotenv
from utils import *
from routers import openai_proxy

# Load environment variables from a local .env file if present
load_dotenv()
app = FastAPI(title="SharePoint-GPT-Middleware")
# Include OpenAI proxy router under /openai
app.include_router(openai_proxy.router, tags=["OpenAI Proxy"], prefix="/openai")

# Configure logging to suppress verbose Azure SDK and HTTP logs
# ------------------------------------------------------------------------------
logging.getLogger('azure').setLevel(logging.WARNING)
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('azure.identity').setLevel(logging.WARNING)
logging.getLogger('azure.identity._credentials').setLevel(logging.WARNING)
logging.getLogger('azure.identity._internal').setLevel(logging.WARNING)
logging.getLogger('msal').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
# Suppress OpenAI SDK retry and HTTP logs
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('openai._base_client').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)


@app.get("/alive", response_class=PlainTextResponse)
async def health():
  """Health check endpoint for monitoring."""
  return PlainTextResponse(content="alive", status_code=200)

@app.get("/favicon.ico")
async def favicon(): return Response(status_code=204)

# Ensure the default document is not served
@app.get('/hostingstart.html', response_class=PlainTextResponse)
async def ignore_default_doc():
  log_data = log_function_header(inspect.currentframe().f_code.co_name)
  retVal = root()
  await log_function_footer(log_data)
  return retVal


@app.get("/", response_class=HTMLResponse)
def root() -> str:
  return """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>SharePoint-GPT-Middleware</title></head><body>
<font face="Open Sans, Arial, Helvetica, sans-serif">
<h3>SharePoint-GPT-Middleware is running</h3>
<p>This middleware provides 1:1 proxy endpoints for OpenAI and Azure OpenAI Service.</p>
<ul>
  <li><a href="/docs">/docs</a> API Documentation</li>
  <li><a href="/openapi.json">/openapi.json</a> OpenAPI JSON</li>
</ul>
<h4>Available OpenAI Endpoints (under /openai):</h4>
<ul>
  <li><strong>Responses API:</strong></li>
  <ul>
    <li>POST /openai/responses - Create response</li>
    <li>GET /openai/responses - List responses</li>
    <li>GET /openai/responses/{response_id} - Get response</li>
    <li>DELETE /openai/responses/{response_id} - Delete response</li>
  </ul>
  <li><strong>Files API:</strong></li>
  <ul>
    <li>POST /openai/files - Upload file</li>
    <li>GET /openai/files - List files</li>
    <li>GET /openai/files/{file_id} - Get file</li>
    <li>DELETE /openai/files/{file_id} - Delete file</li>
    <li>GET /openai/files/{file_id}/content - Get file content</li>
  </ul>
  <li><strong>Vector Stores API:</strong></li>
  <ul>
    <li>POST /openai/vector_stores - Create vector store</li>
    <li>GET /openai/vector_stores - List vector stores</li>
    <li>GET /openai/vector_stores/{vector_store_id} - Get vector store</li>
    <li>POST /openai/vector_stores/{vector_store_id} - Update vector store</li>
    <li>DELETE /openai/vector_stores/{vector_store_id} - Delete vector store</li>
    <li>POST /openai/vector_stores/{vector_store_id}/files - Create vector store file</li>
    <li>GET /openai/vector_stores/{vector_store_id}/files - List vector store files</li>
    <li>GET /openai/vector_stores/{vector_store_id}/files/{file_id} - Get vector store file</li>
    <li>DELETE /openai/vector_stores/{vector_store_id}/files/{file_id} - Delete vector store file</li>
  </ul>
</ul>
    </font></body></html>
"""


# Self-test endpoint (not under /openai)
@app.get("/openaiproxyselftest", response_class=HTMLResponse)
async def openai_proxy_self_test(request: Request, timeoutSecs: Optional[float] = None):
  log_data = log_function_header("openai_proxy_self_test")
  try:
    _ = timeoutSecs  # documented query param; parsing happens inside self_test via request.query_params
    retVal = await openai_proxy.self_test(request)
    return retVal
  finally:
    await log_function_footer(log_data)