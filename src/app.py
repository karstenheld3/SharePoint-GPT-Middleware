import os
import inspect
import logging
from typing import Any
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, Response, HTMLResponse
from dotenv import load_dotenv
from utils import *

# Load environment variables from a local .env file if present
load_dotenv()

app = FastAPI(title="SharePoint-GPT-Middleware")

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

@app.get("/", response_class=HTMLResponse)
def root() -> str:
  return """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>SharePoint-GPT-Middleware</title></head><body>
<font face="Open Sans, Arial, Helvetica, sans-serif">
<h3>SharePoint-GPT-Middleware is running</h3>
<ul>
  <li><a href="/docs">/docs</a> API Documentation</li>
  <li><a href="/openapi.json">/openapi.json</a> OpenAPI JSON</li>
</ul></font></body></html>
"""

# Ensure the default document is not served
@app.get('/hostingstart.html', response_class=PlainTextResponse)
async def ignore_default_doc():
  log_data = log_function_header(inspect.currentframe().f_code.co_name)
  retVal = root()
  await log_function_footer(log_data)
  return retVal
