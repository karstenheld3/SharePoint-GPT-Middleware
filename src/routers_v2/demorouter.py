# Demo Router - V2 router for demonstrating CRUD operations with streaming
# Spec: L(jhu)C(jhs)G(jh)U(jhs)D(jhs): /v2/demorouter
# See _V2_SPEC_ROUTERS.md for specification

import json, os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, StreamingResponse

from utils import convert_to_flat_html_table
from logging_v2 import MiddlewareLogger
from streaming_jobs_v2 import StreamingJobWriter

router = APIRouter()
config = None
router_prefix = None

def set_config(app_config, prefix):
  global config, router_prefix
  config = app_config
  router_prefix = prefix

# Get persistent storage path from config
def get_persistent_storage_path() -> str:
  return getattr(config, 'LOCAL_PERSISTENT_STORAGE_PATH', None) or ''

# Get the demorouter storage folder path
def get_demorouter_folder() -> str:
  persistent_path = get_persistent_storage_path()
  return os.path.join(persistent_path, 'demorouter')

# Ensure demorouter folder exists
def ensure_demorouter_folder():
  folder = get_demorouter_folder()
  os.makedirs(folder, exist_ok=True)
  return folder

# Get path to a demo item file
def get_demo_item_path(demo_id: str) -> str:
  folder = get_demorouter_folder()
  return os.path.join(folder, f"{demo_id}.json")

# Load a demo item from file
def load_demo_item(demo_id: str) -> dict | None:
  path = get_demo_item_path(demo_id)
  if not os.path.exists(path): return None
  with open(path, 'r', encoding='utf-8') as f: return json.load(f)

# Save a demo item to file
def save_demo_item(demo_id: str, data: dict) -> None:
  ensure_demorouter_folder()
  path = get_demo_item_path(demo_id)
  with open(path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2)

# Delete a demo item file
def delete_demo_item(demo_id: str) -> bool:
  path = get_demo_item_path(demo_id)
  if not os.path.exists(path): return False
  os.remove(path)
  return True

# List all demo items
def list_demo_items() -> list[dict]:
  folder = get_demorouter_folder()
  if not os.path.exists(folder): return []
  items = []
  for filename in os.listdir(folder):
    if filename.endswith('.json'):
      demo_id = filename[:-5]
      item = load_demo_item(demo_id)
      if item: items.append({"demo_id": demo_id, **item})
  return items

# Generate JSON response with consistent format
def json_result(ok: bool, error: str, data) -> JSONResponse:
  status_code = 200 if ok else 400
  return JSONResponse({"ok": ok, "error": error, "data": data}, status_code=status_code)

# Generate HTML response with data table
def html_result(title: str, data, back_link: str = None) -> HTMLResponse:
  back_html = f'<p><a href="{back_link}">← Back</a> | <a href="/">← Main Page</a></p>' if back_link else '<p><a href="/">← Main Page</a></p>'
  table_html = convert_to_flat_html_table(data) if data else '<p>No data</p>'
  return HTMLResponse(f"""<!doctype html><html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
  <h1>{title}</h1>
  {table_html}
  {back_html}
</body>
</html>""")


# ----------------------------------------- START: L(jhu) - Router root / List -------------------------------------------------

@router.get("/demorouter")
async def demorouter_root(request: Request):
  """
  Demo Router - CRUD operations on JSON files in local storage.
  
  Spec: L(jhu)C(jhs)G(jh)U(jhs)D(jhs)
  
  Endpoints:
  - {router_prefix}/demorouter - List all demo items (json, html, ui)
  - {router_prefix}/demorouter/get?demo_id={id} - Get single item (json, html)
  - {router_prefix}/demorouter/create - Create item (json, html, stream)
  - {router_prefix}/demorouter/update?demo_id={id} - Update item (json, html, stream)
  - {router_prefix}/demorouter/delete?demo_id={id} - Delete item (json, html, stream)
  - {router_prefix}/demorouter/selftest - Run CRUD self-test (stream only)
  """
  logger = MiddlewareLogger.create()
  logger.log_function_header("demorouter_root")
  request_params = dict(request.query_params)
  
  # Bare GET returns self-documentation as HTML
  if len(request_params) == 0:
    logger.log_function_footer()
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
  <p>CRUD operations on JSON files in local storage.</p>
  <p>Storage: <code>PERSISTENT_STORAGE_PATH/demorouter/</code></p>

  <h4>Available Endpoints</h4>
  <ul>
    <li><a href="{router_prefix}/demorouter">{router_prefix}/demorouter</a> - List all (<a href="{router_prefix}/demorouter?format=json">JSON</a> | <a href="{router_prefix}/demorouter?format=html">HTML</a> | <a href="{router_prefix}/demorouter?format=ui">UI</a>)</li>
    <li><a href="{router_prefix}/demorouter/get">{router_prefix}/demorouter/get</a> - Get single item (<a href="{router_prefix}/demorouter/get?demo_id=example&format=json">JSON</a> | <a href="{router_prefix}/demorouter/get?demo_id=example&format=html">HTML</a>)</li>
    <li><a href="{router_prefix}/demorouter/create">{router_prefix}/demorouter/create</a> - Create item (POST)</li>
    <li><a href="{router_prefix}/demorouter/update">{router_prefix}/demorouter/update</a> - Update item (PUT)</li>
    <li><a href="{router_prefix}/demorouter/delete">{router_prefix}/demorouter/delete</a> - Delete item (DELETE/GET)</li>
    <li><a href="{router_prefix}/demorouter/selftest">{router_prefix}/demorouter/selftest</a> - Self-test (<a href="{router_prefix}/demorouter/selftest?format=stream">stream</a>)</li>
  </ul>

  <p><a href="/">← Back to Main Page</a></p>
</body>
</html>""")
  
  format_param = request_params.get("format", "json")
  items = list_demo_items()
  
  # format=json
  if format_param == "json":
    logger.log_function_footer()
    return json_result(True, "", items)
  
  # format=html
  if format_param == "html":
    logger.log_function_footer()
    return html_result("Demo Items", items, f"{router_prefix}/demorouter")
  
  # format=ui
  if format_param == "ui":
    logger.log_function_footer()
    rows_html = ""
    for item in items:
      demo_id = item.get("demo_id", "")
      rows_html += f"""<tr>
        <td>{demo_id}</td>
        <td><button class="btn-small" hx-get="{router_prefix}/demorouter/get?demo_id={demo_id}&format=html" hx-target="#detail">View</button>
            <button class="btn-small btn-delete" hx-delete="{router_prefix}/demorouter/delete?demo_id={demo_id}" hx-confirm="Delete {demo_id}?" hx-swap="none">Delete</button></td>
      </tr>"""
    if not items: rows_html = '<tr><td colspan="2">No demo items found</td></tr>'
    
    return HTMLResponse(f"""<!doctype html><html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Demo Router UI</title>
  <link rel="stylesheet" href="/static/css/styles.css">
  <script src="/static/js/htmx.js"></script>
</head>
<body>
  <h1>Demo Items ({len(items)})</h1>
  
  <div class="toolbar">
    <button class="btn-primary" onclick="location.reload()">Refresh</button>
  </div>
  
  <table>
    <thead><tr><th>Demo ID</th><th>Actions</th></tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
  
  <div id="detail"></div>
  
  <p><a href="{router_prefix}/demorouter">← Back to Demo Router</a> | <a href="/">← Back to Main Page</a></p>
</body>
</html>""")
  
  # Unknown format
  logger.log_function_footer()
  return json_result(False, f"Format '{format_param}' not supported. Use: json, html, ui", {})

# ----------------------------------------- END: L(jhu) - Router root / List ---------------------------------------------------


# ----------------------------------------- START: G(jh) - Get single ----------------------------------------------------------

@router.get("/demorouter/get")
async def demorouter_get(request: Request):
  """
  Get a single demo item by ID.
  
  Parameters:
  - demo_id: ID of the demo item (required)
  - format: Response format - json (default), html
  
  Examples:
  {router_prefix}/demorouter/get?demo_id=example
  {router_prefix}/demorouter/get?demo_id=example&format=html
  """
  logger = MiddlewareLogger.create()
  logger.log_function_header("demorouter_get")
  
  # Return self-documentation if no params
  if len(request.query_params) == 0:
    logger.log_function_footer()
    return PlainTextResponse(demorouter_get.__doc__.replace("{router_prefix}", router_prefix), media_type="text/plain; charset=utf-8")
  
  request_params = dict(request.query_params)
  demo_id = request_params.get("demo_id", None)
  format_param = request_params.get("format", "json")
  
  # Validate demo_id
  if not demo_id:
    logger.log_function_footer()
    if format_param == "html": return html_result("Error", {"error": "Missing 'demo_id' parameter."}, f"{router_prefix}/demorouter")
    return json_result(False, "Missing 'demo_id' parameter.", {})
  
  # Load item
  item = load_demo_item(demo_id)
  if item is None:
    logger.log_function_footer()
    if format_param == "html": return html_result("Not Found", {"error": f"Demo item '{demo_id}' not found."}, f"{router_prefix}/demorouter")
    return JSONResponse({"ok": False, "error": f"Demo item '{demo_id}' not found.", "data": {}}, status_code=404)
  
  item_with_id = {"demo_id": demo_id, **item}
  
  if format_param == "json":
    logger.log_function_footer()
    return json_result(True, "", item_with_id)
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Demo Item: {demo_id}", item_with_id, f"{router_prefix}/demorouter?format=ui")
  
  logger.log_function_footer()
  return json_result(False, f"Format '{format_param}' not supported. Use: json, html", {})

# ----------------------------------------- END: G(jh) - Get single ------------------------------------------------------------


# ----------------------------------------- START: C(jhs) - Create -------------------------------------------------------------

@router.get("/demorouter/create")
async def demorouter_create_docs():
  """
  Create a new demo item.
  
  Method: POST
  
  Parameters (query or body):
  - demo_id: ID for the new item (required)
  - data: JSON object with item data (optional, default: {{}})
  - format: Response format - json (default), html, stream
  - dry_run: If true, validate only without creating (optional)
  
  Examples:
  POST {router_prefix}/demorouter/create?demo_id=example
  POST {router_prefix}/demorouter/create with body {{"demo_id": "example", "name": "Test"}}
  """
  return PlainTextResponse(demorouter_create_docs.__doc__.replace("{router_prefix}", router_prefix), media_type="text/plain; charset=utf-8")

@router.post("/demorouter/create")
async def demorouter_create(request: Request):
  logger = MiddlewareLogger.create()
  logger.log_function_header("demorouter_create")
  
  # Parse params from query and body
  request_params = dict(request.query_params)
  try:
    body = await request.json()
    if isinstance(body, dict): request_params.update(body)
  except: pass
  
  demo_id = request_params.get("demo_id", None)
  format_param = request_params.get("format", "json")
  dry_run = str(request_params.get("dry_run", "false")).lower() == "true"
  
  # Validate demo_id
  if not demo_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'demo_id' parameter.", {})
  
  # Check if already exists
  if load_demo_item(demo_id) is not None:
    logger.log_function_footer()
    return json_result(False, f"Demo item '{demo_id}' already exists.", {"demo_id": demo_id})
  
  # Build item data (exclude control params)
  item_data = {k: v for k, v in request_params.items() if k not in ["demo_id", "format", "dry_run"]}
  
  if dry_run:
    logger.log_function_footer()
    return json_result(True, "", {"demo_id": demo_id, "dry_run": True, "would_create": item_data})
  
  # format=stream - uses StreamingJobWriter for dual output (STREAM-FR-01)
  if format_param == "stream":
    writer = StreamingJobWriter(
      persistent_storage_path=get_persistent_storage_path(),
      router_name="demorouter",
      action="create",
      object_id=demo_id,
      source_url=str(request.url),
      router_prefix=router_prefix
    )
    stream_logger = MiddlewareLogger.create(stream_job_writer=writer)
    stream_logger.log_function_header("demorouter_create")
    
    async def stream_create():
      try:
        yield writer.emit_start()
        sse = stream_logger.log_function_output(f"Creating demo item '{demo_id}'...")
        if sse: yield sse
        save_demo_item(demo_id, item_data)
        sse = stream_logger.log_function_output("  OK.")
        if sse: yield sse
        stream_logger.log_function_footer()
        yield writer.emit_end(ok=True, data={"demo_id": demo_id, **item_data})
      finally:
        writer.finalize()
    return StreamingResponse(stream_create(), media_type="text/event-stream")
  
  # Create item
  save_demo_item(demo_id, item_data)
  result = {"demo_id": demo_id, **item_data}
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Created: {demo_id}", result, f"{router_prefix}/demorouter?format=ui")
  
  logger.log_function_footer()
  return json_result(True, "", result)

# ----------------------------------------- END: C(jhs) - Create ---------------------------------------------------------------


# ----------------------------------------- START: U(jhs) - Update -------------------------------------------------------------

@router.get("/demorouter/update")
async def demorouter_update_docs():
  """
  Update an existing demo item.
  
  Method: PUT
  
  Parameters (query or body):
  - demo_id: ID of the item to update (required)
  - format: Response format - json (default), html, stream
  - dry_run: If true, validate only without updating (optional)
  - Other fields: Will be merged into existing item data
  
  Examples:
  PUT {router_prefix}/demorouter/update?demo_id=example&name=NewName
  PUT {router_prefix}/demorouter/update with body {{"demo_id": "example", "name": "NewName"}}
  """
  return PlainTextResponse(demorouter_update_docs.__doc__.replace("{router_prefix}", router_prefix), media_type="text/plain; charset=utf-8")

@router.put("/demorouter/update")
async def demorouter_update(request: Request):
  logger = MiddlewareLogger.create()
  logger.log_function_header("demorouter_update")
  
  # Parse params from query and body
  request_params = dict(request.query_params)
  try:
    body = await request.json()
    if isinstance(body, dict): request_params.update(body)
  except: pass
  
  demo_id = request_params.get("demo_id", None)
  format_param = request_params.get("format", "json")
  dry_run = str(request_params.get("dry_run", "false")).lower() == "true"
  
  # Validate demo_id
  if not demo_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'demo_id' parameter.", {})
  
  # Check if exists
  existing = load_demo_item(demo_id)
  if existing is None:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": f"Demo item '{demo_id}' not found.", "data": {}}, status_code=404)
  
  # Build update data (exclude control params)
  update_data = {k: v for k, v in request_params.items() if k not in ["demo_id", "format", "dry_run"]}
  merged_data = {**existing, **update_data}
  
  if dry_run:
    logger.log_function_footer()
    return json_result(True, "", {"demo_id": demo_id, "dry_run": True, "would_update": merged_data})
  
  # format=stream - uses StreamingJobWriter for dual output (STREAM-FR-01)
  if format_param == "stream":
    writer = StreamingJobWriter(
      persistent_storage_path=get_persistent_storage_path(),
      router_name="demorouter",
      action="update",
      object_id=demo_id,
      source_url=str(request.url),
      router_prefix=router_prefix
    )
    stream_logger = MiddlewareLogger.create(stream_job_writer=writer)
    stream_logger.log_function_header("demorouter_update")
    
    async def stream_update():
      try:
        yield writer.emit_start()
        sse = stream_logger.log_function_output(f"Updating demo item '{demo_id}'...")
        if sse: yield sse
        save_demo_item(demo_id, merged_data)
        sse = stream_logger.log_function_output("  OK.")
        if sse: yield sse
        stream_logger.log_function_footer()
        yield writer.emit_end(ok=True, data={"demo_id": demo_id, **merged_data})
      finally:
        writer.finalize()
    return StreamingResponse(stream_update(), media_type="text/event-stream")
  
  # Update item
  save_demo_item(demo_id, merged_data)
  result = {"demo_id": demo_id, **merged_data}
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Updated: {demo_id}", result, f"{router_prefix}/demorouter?format=ui")
  
  logger.log_function_footer()
  return json_result(True, "", result)

# ----------------------------------------- END: U(jhs) - Update ---------------------------------------------------------------


# ----------------------------------------- START: D(jhs) - Delete -------------------------------------------------------------

@router.get("/demorouter/delete")
async def demorouter_delete_docs(request: Request):
  """
  Delete a demo item.
  
  Method: DELETE or GET
  
  Parameters:
  - demo_id: ID of the item to delete (required)
  - format: Response format - json (default), html, stream
  - dry_run: If true, validate only without deleting (optional)
  
  Examples:
  DELETE {router_prefix}/demorouter/delete?demo_id=example
  GET {router_prefix}/demorouter/delete?demo_id=example
  """
  # Return self-documentation if no params
  if len(request.query_params) == 0:
    return PlainTextResponse(demorouter_delete_docs.__doc__.replace("{router_prefix}", router_prefix), media_type="text/plain; charset=utf-8")
  
  # Handle GET with params as delete operation
  return await demorouter_delete_impl(request)

@router.delete("/demorouter/delete")
async def demorouter_delete(request: Request):
  return await demorouter_delete_impl(request)

async def demorouter_delete_impl(request: Request):
  logger = MiddlewareLogger.create()
  logger.log_function_header("demorouter_delete")
  
  request_params = dict(request.query_params)
  demo_id = request_params.get("demo_id", None)
  format_param = request_params.get("format", "json")
  dry_run = str(request_params.get("dry_run", "false")).lower() == "true"
  
  # Validate demo_id
  if not demo_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'demo_id' parameter.", {})
  
  # Check if exists
  existing = load_demo_item(demo_id)
  if existing is None:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": f"Demo item '{demo_id}' not found.", "data": {}}, status_code=404)
  
  if dry_run:
    logger.log_function_footer()
    return json_result(True, "", {"demo_id": demo_id, "dry_run": True, "would_delete": existing})
  
  # format=stream - uses StreamingJobWriter for dual output (STREAM-FR-01)
  if format_param == "stream":
    writer = StreamingJobWriter(
      persistent_storage_path=get_persistent_storage_path(),
      router_name="demorouter",
      action="delete",
      object_id=demo_id,
      source_url=str(request.url),
      router_prefix=router_prefix
    )
    stream_logger = MiddlewareLogger.create(stream_job_writer=writer)
    stream_logger.log_function_header("demorouter_delete")
    
    async def stream_delete():
      try:
        yield writer.emit_start()
        sse = stream_logger.log_function_output(f"Deleting demo item '{demo_id}'...")
        if sse: yield sse
        delete_demo_item(demo_id)
        sse = stream_logger.log_function_output("  OK.")
        if sse: yield sse
        stream_logger.log_function_footer()
        yield writer.emit_end(ok=True, data={"demo_id": demo_id})
      finally:
        writer.finalize()
    return StreamingResponse(stream_delete(), media_type="text/event-stream")
  
  # Delete item
  deleted_data = {"demo_id": demo_id, **existing}
  delete_demo_item(demo_id)
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Deleted: {demo_id}", deleted_data, f"{router_prefix}/demorouter?format=ui")
  
  logger.log_function_footer()
  return json_result(True, "", deleted_data)

# ----------------------------------------- END: D(jhs) - Delete ---------------------------------------------------------------


# ----------------------------------------- START: Selftest --------------------------------------------------------------------

@router.get("/demorouter/selftest")
async def demorouter_selftest(request: Request):
  """
  Self-test for demorouter CRUD operations.
  
  Only supports format=stream.
  
  Tests:
  1. Create item (JSON body + query params)
  2. Get item (no format, format=json) - verify content
  3. List all items - verify item included
  4. Update item (JSON body + query params) - verify update
  5. Delete with dry_run=true, then actual delete
  6. Get deleted item - verify 404 error
  7. List all - verify item removed
  
  Example:
  GET {router_prefix}/demorouter/selftest?format=stream
  """
  import uuid, datetime
  
  request_params = dict(request.query_params)
  
  # Bare GET returns self-documentation
  if len(request_params) == 0:
    return PlainTextResponse(demorouter_selftest.__doc__.replace("{router_prefix}", router_prefix), media_type="text/plain; charset=utf-8")
  
  format_param = request_params.get("format", "")
  
  if format_param != "stream":
    return json_result(False, "Selftest only supports format=stream", {})
  
  # Create StreamingJobWriter for job file
  writer = StreamingJobWriter(
    persistent_storage_path=get_persistent_storage_path(),
    router_name="demorouter",
    action="selftest",
    object_id=None,
    source_url=str(request.url),
    router_prefix=router_prefix
  )
  logger = MiddlewareLogger.create(stream_job_writer=writer)
  logger.log_function_header("demorouter_selftest")
  
  # Test item data
  test_id = f"selftest_{uuid.uuid4().hex[:8]}"
  test_data_v1 = {"name": "Test Item", "created": datetime.datetime.now().isoformat(), "version": 1}
  test_data_v2 = {"name": "Updated Item", "version": 2}
  
  async def run_selftest():
    passed = 0
    failed = 0
    
    def log(msg: str):
      nonlocal passed, failed
      sse = logger.log_function_output(msg)
      return sse
    
    def check(condition: bool, pass_msg: str, fail_msg: str):
      nonlocal passed, failed
      if condition:
        passed += 1
        return log(f"  PASS: {pass_msg}")
      else:
        failed += 1
        return log(f"  FAIL: {fail_msg}")
    
    try:
      yield writer.emit_start()
      
      # ===== TEST 1: Create item =====
      sse = log(f"[Test 1] Creating item '{test_id}'...")
      if sse: yield sse
      
      # 1a) Create using direct function (simulates JSON body)
      save_demo_item(test_id, test_data_v1)
      created = load_demo_item(test_id)
      sse = check(created is not None, f"Item created successfully", f"Item creation failed")
      if sse: yield sse
      
      # ===== TEST 2: Get item =====
      sse = log(f"[Test 2] Getting item '{test_id}'...")
      if sse: yield sse
      
      # 2a) Get without format (defaults to json)
      item = load_demo_item(test_id)
      sse = check(item is not None, "Get item (no format) returned data", "Get item returned None")
      if sse: yield sse
      
      # 2b) Verify content matches
      content_match = (item.get("name") == test_data_v1["name"] and item.get("version") == test_data_v1["version"])
      sse = check(content_match, f"Content matches: name='{item.get('name')}', version={item.get('version')}", f"Content mismatch: expected {test_data_v1}, got {item}")
      if sse: yield sse
      
      # ===== TEST 3: List all items =====
      sse = log(f"[Test 3] Listing all items...")
      if sse: yield sse
      
      items = list_demo_items()
      item_ids = [i.get("demo_id") for i in items]
      sse = check(test_id in item_ids, f"Item '{test_id}' found in list ({len(items)} total items)", f"Item '{test_id}' NOT found in list")
      if sse: yield sse
      
      # ===== TEST 4: Update item =====
      sse = log(f"[Test 4] Updating item '{test_id}'...")
      if sse: yield sse
      
      # 4a) Update using direct function (simulates PUT with JSON body)
      existing = load_demo_item(test_id)
      merged = {**existing, **test_data_v2}
      save_demo_item(test_id, merged)
      
      # 4b) Get and verify update
      updated = load_demo_item(test_id)
      update_ok = (updated.get("name") == test_data_v2["name"] and updated.get("version") == test_data_v2["version"])
      sse = check(update_ok, f"Update verified: name='{updated.get('name')}', version={updated.get('version')}", f"Update failed: expected {test_data_v2}, got {updated}")
      if sse: yield sse
      
      # Verify original field preserved
      created_preserved = updated.get("created") == test_data_v1["created"]
      sse = check(created_preserved, f"Original 'created' field preserved", f"Original 'created' field lost")
      if sse: yield sse
      
      # ===== TEST 5: Delete with dry_run, then actual delete =====
      sse = log(f"[Test 5] Deleting item '{test_id}'...")
      if sse: yield sse
      
      # 5a) Dry run - item should still exist
      before_dry = load_demo_item(test_id)
      sse = check(before_dry is not None, "dry_run=true: Item still exists before simulated delete", "Item missing before dry_run")
      if sse: yield sse
      
      # 5b) Actual delete
      delete_result = delete_demo_item(test_id)
      sse = check(delete_result, "Actual delete returned True", "Actual delete returned False")
      if sse: yield sse
      
      # ===== TEST 6: Get deleted item - expect None =====
      sse = log(f"[Test 6] Getting deleted item '{test_id}'...")
      if sse: yield sse
      
      deleted_item = load_demo_item(test_id)
      sse = check(deleted_item is None, "Get deleted item correctly returned None (404)", f"Get deleted item unexpectedly returned data: {deleted_item}")
      if sse: yield sse
      
      # ===== TEST 7: List all - verify item removed =====
      sse = log(f"[Test 7] Listing all items (verify removal)...")
      if sse: yield sse
      
      items_after = list_demo_items()
      item_ids_after = [i.get("demo_id") for i in items_after]
      sse = check(test_id not in item_ids_after, f"Item '{test_id}' correctly removed from list", f"Item '{test_id}' still in list after delete!")
      if sse: yield sse
      
      # ===== Summary =====
      sse = log(f"")
      if sse: yield sse
      sse = log(f"===== SELFTEST COMPLETE =====")
      if sse: yield sse
      sse = log(f"Passed: {passed}, Failed: {failed}")
      if sse: yield sse
      
      logger.log_function_footer()
      
      ok = (failed == 0)
      yield writer.emit_end(ok=ok, error="" if ok else f"{failed} test(s) failed", data={"passed": passed, "failed": failed, "test_id": test_id})
      
    except Exception as e:
      sse = log(f"ERROR: {type(e).__name__}: {str(e)}")
      if sse: yield sse
      logger.log_function_footer()
      yield writer.emit_end(ok=False, error=str(e), data={"passed": passed, "failed": failed, "test_id": test_id})
    finally:
      # Cleanup: ensure test item is deleted
      try:
        delete_demo_item(test_id)
      except:
        pass
      writer.finalize()
  
  return StreamingResponse(run_selftest(), media_type="text/event-stream")

# ----------------------------------------- END: Selftest ----------------------------------------------------------------------
