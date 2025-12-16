# Demo Router - V2 router for demonstrating streaming endpoints
# See _V2_SPEC_ROUTERS.md for specification

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()
config = None
router_prefix = None

def set_config(app_config, prefix):
  global config, router_prefix
  config = app_config
  router_prefix = prefix

@router.get("/demorouter")
async def root(request: Request):
  """
  Demo Router - demonstrates streaming endpoints with job management.
  
  Endpoints:
  - /demorouter - This documentation (bare GET)
  - /demorouter?format=ui - Interactive UI (coming soon)
  
  See _V2_SPEC_ROUTERS.md for full specification.
  """
  request_params = dict(request.query_params)
  
  # Bare GET returns self-documentation as HTML
  if len(request_params) == 0:
    return HTMLResponse(f"""<!doctype html><html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Demo Router</title>
  <link rel="stylesheet" href="/static/css/styles.css">
  <script src="/static/js/htmx.js"></script>
</head>
<body>
  <h1>Demo Router</h1>
  <p>Demonstrates streaming endpoints with job management.</p>

  <h4>Available Endpoints</h4>
  <ul>
    <li><a href="{router_prefix}/demorouter">{router_prefix}/demorouter</a> - This documentation</li>
    <li><a href="{router_prefix}/demorouter?format=ui">{router_prefix}/demorouter?format=ui</a> - Interactive UI (coming soon)</li>
  </ul>

  <p><a href="/">← Back to Main Page</a></p>
</body>
</html>""")
  
  format_param = request_params.get("format", None)
  
  # format=ui returns interactive UI
  if format_param == "ui":
    return HTMLResponse(f"""<!doctype html><html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Demo Router UI</title>
  <link rel="stylesheet" href="/static/css/styles.css">
  <script src="/static/js/htmx.js"></script>
</head>
<body>
  <h1>Demo Router UI</h1>
  <p>Interactive UI coming soon.</p>

  <p><a href="{router_prefix}/demorouter">← Back to Demo Router</a> | <a href="/">← Back to Main Page</a></p>
</body>
</html>""")
  
  # Unknown format
  return HTMLResponse(f"""<!doctype html><html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Demo Router</title>
  <link rel="stylesheet" href="/static/css/styles.css">
  <script src="/static/js/htmx.js"></script>
</head>
<body>
  <h1>Demo Router</h1>
  <p>Unknown format: {format_param}</p>

  <p><a href="{router_prefix}/demorouter">← Back to Demo Router</a></p>
</body>
</html>""")
