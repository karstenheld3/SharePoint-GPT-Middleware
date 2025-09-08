import os
import inspect
import logging
from typing import Optional
from dataclasses import dataclass
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers import openai_proxy
from utils import *

# Load environment variables from a local .env file if present
load_dotenv()

@dataclass
class Config:
  OPENAI_SERVICE_TYPE: str
  AZURE_OPENAI_USE_KEY_AUTHENTICATION: Optional[bool]
  AZURE_OPENAI_ENDPOINT: Optional[str]
  AZURE_OPENAI_API_KEY: Optional[str]
  AZURE_OPENAI_API_VERSION: str
  AZURE_OPENAI_DEFAULT_MODEL_DEPLOYMENT_NAME: Optional[str]
  OPENAI_API_KEY: Optional[str]
  OPENAI_ORGANIZATION: Optional[str]
  OPENAI_DEFAULT_MODEL_NAME: str

def load_config() -> Config:
  """Load configuration from environment variables."""
  return Config(
    OPENAI_SERVICE_TYPE=os.getenv("OPENAI_SERVICE_TYPE", "openai"),
    AZURE_OPENAI_USE_KEY_AUTHENTICATION=os.getenv("AZURE_OPENAI_USE_KEY_AUTHENTICATION").lower() == "true" if os.getenv("AZURE_OPENAI_USE_KEY_AUTHENTICATION") else None,
    AZURE_OPENAI_ENDPOINT=os.getenv("AZURE_OPENAI_ENDPOINT"),
    AZURE_OPENAI_API_KEY=os.getenv("AZURE_OPENAI_API_KEY"),
    AZURE_OPENAI_API_VERSION=os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview"),
    AZURE_OPENAI_DEFAULT_MODEL_DEPLOYMENT_NAME=os.getenv("AZURE_OPENAI_DEFAULT_MODEL_DEPLOYMENT_NAME"),
    OPENAI_API_KEY=os.getenv("OPENAI_API_KEY"),
    OPENAI_ORGANIZATION=os.getenv("OPENAI_ORGANIZATION"),
    OPENAI_DEFAULT_MODEL_NAME=os.getenv("OPENAI_DEFAULT_MODEL_NAME")
  )

def configure_logging():
  """Configure logging to suppress verbose Azure SDK and HTTP logs."""
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

def create_app() -> FastAPI:
  """Initialize and configure the FastAPI application."""
  # Load configuration
  config = load_config()
  
  # Create FastAPI app instance
  app = FastAPI(title="SharePoint-GPT-Middleware")
  
  # Add CORS middleware to handle preflight OPTIONS requests
  app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
  )
  
  # Include OpenAI proxy router under /openai
  app.include_router(openai_proxy.router, tags=["OpenAI Proxy"], prefix="/openai")
  openai_proxy.set_config(config)
  
  # Configure logging
  configure_logging()
  
  # Store config in app state for access in endpoints
  app.state.config = config
  
  return app

# Initialize the FastAPI application
app = create_app()

def get_config() -> Config:
  """Get the current application configuration."""
  return app.state.config


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
  return f"""
<!doctype html><html lang="en"><head><meta charset="utf-8"><title>SharePoint-GPT-Middleware</title></head><body>
<font face="Open Sans, Arial, Helvetica, sans-serif">
<h3>SharePoint-GPT-Middleware is running</h3>
<p>This middleware provides 1:1 proxy endpoints for OpenAI and Azure OpenAI Service.</p>

<h4>Available Links</h4>
<ul>
  <li><a href="/docs">/docs</a> - API Documentation</li>
  <li><a href="/openapi.json">/openapi.json</a> - OpenAPI JSON</li>
  <li><a href="/openaiproxyselftest">/openaiproxyselftest</a> - Self Test (will take a while)</li>
</ul>

<h4>Configuration</h4>
{convert_to_nested_html_table(format_config_for_displaying(app.state.config))}
</font></body></html>
"""


# Self-test endpoint (not under /openai)
@app.get("/openaiproxyselftest", response_class=HTMLResponse)
async def openai_proxy_self_test(request: Request, timeoutSecs: Optional[float] = None):
  log_data = log_function_header("openai_proxy_self_test")
  try:
    retVal = await openai_proxy.self_test(request)
    return retVal
  finally:
    await log_function_footer(log_data)