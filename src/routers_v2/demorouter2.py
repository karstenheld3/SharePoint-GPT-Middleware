# Demo Router 2 - V2 router using common_ui_functions_v2.py
# Spec: L(jhu)C(jhs)G(jh)U(jhs)D(jhs): /v2/demorouter2
# This router demonstrates the use of common_ui_functions_v2.py
# Same functionality as demorouter1 but UI generated via shared library

import json, os, textwrap
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, StreamingResponse

from routers_v2.common_ui_functions_v2 import generate_ui_page, generate_router_docs_page, generate_endpoint_docs, json_result, html_result
from routers_v2.common_logging_functions_v2 import MiddlewareLogger
from routers_v2.common_job_functions_v2 import StreamingJobWriter, ControlAction

router = APIRouter()
config = None
router_prefix = None
router_name = "demorouter2"
main_page_nav_html = '<a href="/">Back to Main Page</a>'
example_item_json = """
{
  "item_id": "demo_7b50d184",
  "name": "Demo Item 3",
  "version": 3
}
"""

def set_config(app_config, prefix):
  global config, router_prefix
  config = app_config
  router_prefix = prefix

def get_persistent_storage_path() -> str:
  return getattr(config, 'LOCAL_PERSISTENT_STORAGE_PATH', None) or ''

def get_demorouter_folder() -> str:
  return os.path.join(get_persistent_storage_path(), router_name)

def ensure_demorouter_folder():
  folder = get_demorouter_folder()
  os.makedirs(folder, exist_ok=True)
  return folder

def get_demo_item_path(item_id: str) -> str:
  return os.path.join(get_demorouter_folder(), f"{item_id}.json")

def load_demo_item(item_id: str) -> dict | None:
  path = get_demo_item_path(item_id)
  if not os.path.exists(path): return None
  with open(path, 'r', encoding='utf-8') as f: return json.load(f)

def save_demo_item(item_id: str, data: dict, dry_run: bool = False) -> None:
  ensure_demorouter_folder()
  path = get_demo_item_path(item_id)
  if not dry_run:
    with open(path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2)

def delete_demo_item(item_id: str, dry_run: bool = False) -> bool:
  path = get_demo_item_path(item_id)
  if not os.path.exists(path): return False
  if not dry_run: os.remove(path)
  return True

def rename_demo_item(source_item_id: str, target_item_id: str, dry_run: bool = False) -> tuple[bool, str]:
  source_path = get_demo_item_path(source_item_id)
  target_path = get_demo_item_path(target_item_id)
  if not os.path.exists(source_path): return (False, f"Source item '{source_item_id}' not found.")
  if os.path.exists(target_path): return (False, f"Target item ID '{target_item_id}' already exists.")
  if not dry_run: os.rename(source_path, target_path)
  return (True, "")

def list_demo_items() -> list[dict]:
  folder = get_demorouter_folder()
  if not os.path.exists(folder): return []
  items = []
  for filename in os.listdir(folder):
    if filename.endswith('.json'):
      item_id = filename[:-5]
      item = load_demo_item(item_id)
      if item: items.append({"item_id": item_id, **item})
  return items


# ----------------------------------------- START: Router-specific Form JS ---------------------------------------------------

def get_router_specific_js() -> str:
  """Router-specific JavaScript for create/update/demo item forms."""
  return f"""
// ============================================
// ROUTER-SPECIFIC FORMS
// ============================================

function showNewItemForm() {{
  const body = document.querySelector('#modal .modal-body');
  body.innerHTML = `
    <h3>New Item</h3>
    <form id="new-item-form" onsubmit="return submitNewItemForm(event)">
      <div class="form-group">
        <label>Item ID (required)</label>
        <input type="text" name="item_id" required>
      </div>
      <div class="form-group">
        <label>Name</label>
        <input type="text" name="name">
      </div>
      <div class="form-group">
        <label>Version</label>
        <input type="number" name="version" value="1">
      </div>
      <div class="form-actions">
        <button type="submit" class="btn-primary" data-url="{router_prefix}/{router_name}/create" data-method="POST" data-format="json" data-reload-on-finish="true">OK</button>
        <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
      </div>
    </form>
  `;
  openModal();
}}

function submitNewItemForm(event) {{
  event.preventDefault();
  const form = document.getElementById('new-item-form');
  const btn = form.querySelector('button[type="submit"]');
  const formData = new FormData(form);
  const data = {{}};
  
  const itemIdInput = form.querySelector('input[name="item_id"]');
  const itemId = formData.get('item_id');
  if (!itemId || !itemId.trim()) {{
    showFieldError(itemIdInput, 'Item ID is required');
    return;
  }}
  clearFieldError(itemIdInput);
  
  for (const [key, value] of formData.entries()) {{
    if (value) {{
      data[key] = key === 'version' ? parseInt(value) : value;
    }}
  }}
  
  closeModal();
  callEndpoint(btn, null, data);
}}

async function showUpdateForm(itemId) {{
  const body = document.querySelector('#modal .modal-body');
  body.innerHTML = '<h3>Loading...</h3>';
  openModal();
  
  try {{
    const response = await fetch(`{router_prefix}/{router_name}/get?item_id=${{itemId}}&format=json`);
    const result = await response.json();
    if (!result.ok) {{
      body.innerHTML = '<h3>Error</h3><p>' + escapeHtml(result.error) + '</p><div class="form-actions"><button class="btn-secondary" onclick="closeModal()">Close</button></div>';
      return;
    }}
    const item = result.data;
    
    body.innerHTML = `
      <h3>Update Item</h3>
      <form id="update-item-form" onsubmit="return submitUpdateForm(event)">
        <input type="hidden" name="source_item_id" value="${{itemId}}">
        <div class="form-group">
          <label>Item ID</label>
          <input type="text" name="item_id" value="${{escapeHtml(itemId)}}">
          <small style="color: #666;">Change to rename the item</small>
        </div>
        <div class="form-group">
          <label>Name</label>
          <input type="text" name="name" value="${{escapeHtml(item.name || '')}}">
        </div>
        <div class="form-group">
          <label>Version</label>
          <input type="number" name="version" value="${{item.version || 1}}">
        </div>
        <div class="form-actions">
          <button type="submit" class="btn-primary" data-url="{router_prefix}/{router_name}/update?item_id=${{itemId}}" data-method="PUT" data-format="json" data-reload-on-finish="true">OK</button>
          <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
        </div>
      </form>
    `;
  }} catch (e) {{
    body.innerHTML = '<h3>Error</h3><p>' + escapeHtml(e.message) + '</p><div class="form-actions"><button class="btn-secondary" onclick="closeModal()">Close</button></div>';
  }}
}}

function submitUpdateForm(event) {{
  event.preventDefault();
  const form = document.getElementById('update-item-form');
  const btn = form.querySelector('button[type="submit"]');
  const formData = new FormData(form);
  const data = {{}};
  
  const sourceItemId = formData.get('source_item_id');
  const targetItemId = formData.get('item_id');
  
  const itemIdInput = form.querySelector('input[name="item_id"]');
  if (!targetItemId || !targetItemId.trim()) {{
    showFieldError(itemIdInput, 'Item ID cannot be empty');
    return;
  }}
  clearFieldError(itemIdInput);
  
  for (const [key, value] of formData.entries()) {{
    if (key === 'source_item_id') continue;
    if (key === 'item_id') {{
      if (value && value !== sourceItemId) {{
        data.item_id = value.trim();
      }}
    }} else if (value) {{
      data[key] = key === 'version' ? parseInt(value) : value;
    }}
  }}
  
  closeModal();
  callEndpoint(btn, sourceItemId, data);
}}

function showCreateDemoItemsForm() {{
  const body = document.querySelector('#modal .modal-body');
  body.innerHTML = `
    <h3>Create Demo Items</h3>
    <p>This will create a number of demo items as a background job.</p>
    <form id="create-demo-items-form" onsubmit="return submitCreateDemoItemsForm(event)">
      <div class="form-group">
        <label>Count (1-100)</label>
        <input type="number" name="count" value="10" min="1" max="100">
      </div>
      <div class="form-group">
        <label>Delay per item (ms)</label>
        <input type="number" name="delay_ms" value="300" min="0" max="10000">
      </div>
      <div class="form-actions">
        <button type="submit" class="btn-primary" data-url="{router_prefix}/{router_name}/create_demo_items?format=stream&count={{count}}&delay_ms={{delay_ms}}" data-format="stream" data-reload-on-finish="true" data-show-result="modal">OK</button>
        <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
      </div>
    </form>
  `;
  openModal();
}}

function submitCreateDemoItemsForm(event) {{
  event.preventDefault();
  const form = document.getElementById('create-demo-items-form');
  const btn = form.querySelector('button[type="submit"]');
  const formData = new FormData(form);
  const count = parseInt(formData.get('count')) || 10;
  const delayMs = parseInt(formData.get('delay_ms')) || 300;
  
  if (count < 1 || count > 100) {{
    showToast('Invalid', 'Count must be between 1 and 100', 'error');
    return;
  }}
  if (delayMs < 0 || delayMs > 10000) {{
    showToast('Invalid', 'Delay must be between 0 and 10000 ms', 'error');
    return;
  }}
  
  const urlTemplate = btn.dataset.url;
  const url = urlTemplate.replace('{{count}}', count).replace('{{delay_ms}}', delayMs);
  const reloadOnFinish = btn.dataset.reloadOnFinish === 'true';
  const showResult = btn.dataset.showResult || 'toast';
  
  closeModal();
  connectStream(url, {{ reloadOnFinish, showResult }});
}}
"""


# ----------------------------------------- END: Router-specific Form JS -----------------------------------------------------


# ----------------------------------------- START: L(jhu) - Router root / List -----------------------------------------------

@router.get(f"/{router_name}")
async def demorouter_root(request: Request):
  """Demo Router 2 - CRUD operations using common_ui_functions_v2.py"""
  logger = MiddlewareLogger.create()
  logger.log_function_header("demorouter2_root")
  request_params = dict(request.query_params)
  
  # Bare GET returns self-documentation as HTML
  if len(request_params) == 0:
    logger.log_function_footer()
    endpoints = [
      {"path": "", "desc": "List all", "formats": ["json", "html", "ui"]},
      {"path": "/get", "desc": "Get single item", "formats": ["json", "html"]},
      {"path": "/create", "desc": "Create item (POST)", "formats": []},
      {"path": "/update", "desc": "Update item (PUT)", "formats": []},
      {"path": "/delete", "desc": "Delete item (DELETE/GET)", "formats": []},
      {"path": "/selftest", "desc": "Self-test", "formats": ["stream"]},
      {"path": "/create_demo_items", "desc": "Create demo items", "formats": ["stream"]}
    ]
    return HTMLResponse(generate_router_docs_page(
      title="Demo Router 2",
      description=f"CRUD operations on JSON files using common_ui_functions_v2.py. Storage: PERSISTENT_STORAGE_PATH/{router_name}/",
      router_prefix=f"{router_prefix}/{router_name}",
      endpoints=endpoints,
      navigation_html=main_page_nav_html
    ))
  
  format_param = request_params.get("format", "json")
  items = list_demo_items()
  
  if format_param == "json":
    logger.log_function_footer()
    return json_result(True, "", items)
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result("Demo Items", items, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html}')
  
  if format_param == "ui":
    logger.log_function_footer()
    
    columns = [
      {"field": "item_id", "header": "ID"},
      {"field": "name", "header": "Name", "default": "-"},
      {"field": "version", "header": "Version", "default": "-"},
      {
        "field": "actions",
        "header": "Actions",
        "buttons": [
          {"text": "Edit", "onclick": "showUpdateForm('{itemId}')", "class": "btn-small"},
          {
            "text": "Delete",
            "data_url": f"{router_prefix}/{router_name}/delete?item_id={{itemId}}",
            "data_method": "DELETE",
            "data_format": "json",
            "confirm_message": "Delete item '{itemId}'?",
            "class": "btn-small btn-delete"
          }
        ]
      }
    ]
    
    toolbar_buttons = [
      {"text": "New Item", "onclick": "showNewItemForm()", "class": "btn-primary"},
      {"text": "Create Demo Items", "onclick": "showCreateDemoItemsForm()", "class": "btn-primary"},
      {
        "text": "Run Selftest",
        "data_url": f"{router_prefix}/{router_name}/selftest?format=stream",
        "data_format": "stream",
        "data_show_result": "modal",
        "data_reload_on_finish": "true",
        "class": "btn-primary"
      }
    ]
    
    html = generate_ui_page(
      title="Demo Items",
      router_prefix=router_prefix,
      items=items,
      columns=columns,
      row_id_field="item_id",
      row_id_prefix="item",
      navigation_html=main_page_nav_html,
      toolbar_buttons=toolbar_buttons,
      enable_selection=True,
      enable_bulk_delete=True,
      list_endpoint=f"{router_prefix}/{router_name}?format=json",
      delete_endpoint=f"{router_prefix}/{router_name}/delete?item_id={{itemId}}",
      jobs_control_endpoint=f"{router_prefix}/jobs/control",
      additional_js=get_router_specific_js()
    )
    return HTMLResponse(html)
  
  logger.log_function_footer()
  return json_result(False, f"Format '{format_param}' not supported. Use: json, html, ui", {})

# ----------------------------------------- END: L(jhu) - Router root / List -------------------------------------------------


# ----------------------------------------- START: G(jh) - Get single --------------------------------------------------------

@router.get(f"/{router_name}/get")
async def demorouter_get(request: Request):
  """
  Get a single demo item by ID.
  
  Parameters:
  - item_id: ID of the demo item (required)
  - format: Response format - json (default), html
  
  Examples:
  {router_prefix}/{router_name}/get?item_id=example
  {router_prefix}/{router_name}/get?item_id=example&format=html

  Example item:
  {example_item_json}
  """
  logger = MiddlewareLogger.create()
  logger.log_function_header("demorouter2_get")
  
  if len(request.query_params) == 0:
    logger.log_function_footer()
    doc = textwrap.dedent(demorouter_get.__doc__).replace("{router_prefix}", router_prefix).replace("{router_name}", router_name).replace("{example_item_json}", example_item_json.strip())
    return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")
  
  request_params = dict(request.query_params)
  item_id = request_params.get("item_id", None)
  format_param = request_params.get("format", "json")
  
  if not item_id:
    logger.log_function_footer()
    if format_param == "html": return html_result("Error", {"error": "Missing 'item_id' parameter."}, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html}')
    return json_result(False, "Missing 'item_id' parameter.", {})
  
  item = load_demo_item(item_id)
  if item is None:
    logger.log_function_footer()
    if format_param == "html": return html_result("Not Found", {"error": f"Demo item '{item_id}' not found."}, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html}')
    return JSONResponse({"ok": False, "error": f"Demo item '{item_id}' not found.", "data": {}}, status_code=404)
  
  item_with_id = {"item_id": item_id, **item}
  
  if format_param == "json":
    logger.log_function_footer()
    return json_result(True, "", item_with_id)
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Demo Item: {item_id}", item_with_id, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html}')
  
  logger.log_function_footer()
  return json_result(False, f"Format '{format_param}' not supported. Use: json, html", {})

# ----------------------------------------- END: G(jh) - Get single ----------------------------------------------------------


# ----------------------------------------- START: C(jhs) - Create -----------------------------------------------------------

@router.get(f"/{router_name}/create")
async def demorouter_create_docs():
  """
  Create a new demo item.
  
  Method: POST
  
  Body (JSON or form data):
  - item_id: ID for the new item (required)
  - [other fields]: Additional item data
  
  Query params:
  - format: Response format - json (default), html, stream
  - dry_run: If true, validate only without creating (optional)
  
  Examples:
  POST {router_prefix}/{router_name}/create with JSON body {"item_id": "example", "name": "Test"}
  POST {router_prefix}/{router_name}/create with form data: item_id=example&name=Test

  Example item:
  {example_item_json}
  """
  doc = textwrap.dedent(demorouter_create_docs.__doc__).replace("{router_prefix}", router_prefix).replace("{router_name}", router_name).replace("{example_item_json}", example_item_json.strip())
  return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")

@router.post(f"/{router_name}/create")
async def demorouter_create(request: Request):
  logger = MiddlewareLogger.create()
  logger.log_function_header("demorouter2_create")
  
  query_params = dict(request.query_params)
  format_param = query_params.get("format", "json")
  dry_run = str(query_params.get("dry_run", "false")).lower() == "true"
  
  body_data = {}
  content_type = request.headers.get("content-type", "")
  try:
    if "application/json" in content_type:
      body_data = await request.json()
    elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
      form = await request.form()
      body_data = dict(form)
    else:
      try:
        body_data = await request.json()
      except:
        form = await request.form()
        body_data = dict(form)
  except: pass
  
  item_id = body_data.get("item_id", None)
  
  if not item_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'item_id' in request body.", {})
  
  if load_demo_item(item_id) is not None:
    logger.log_function_footer()
    return json_result(False, f"Demo item '{item_id}' already exists.", {"item_id": item_id})
  
  item_data = {k: v for k, v in body_data.items() if k not in ["item_id", "format", "dry_run"]}
  
  if format_param == "stream" and not dry_run:
    writer = StreamingJobWriter(
      persistent_storage_path=get_persistent_storage_path(),
      router_name=router_name,
      action="create",
      object_id=item_id,
      source_url=str(request.url),
      router_prefix=router_prefix
    )
    stream_logger = MiddlewareLogger.create(stream_job_writer=writer)
    stream_logger.log_function_header("demorouter2_create")
    
    async def stream_create():
      try:
        yield writer.emit_start()
        sse = stream_logger.log_function_output(f"Creating demo item '{item_id}'...")
        if sse: yield sse
        save_demo_item(item_id, item_data)
        sse = stream_logger.log_function_output("  OK.")
        if sse: yield sse
        stream_logger.log_function_footer()
        yield writer.emit_end(ok=True, data={"item_id": item_id, **item_data})
      finally:
        writer.finalize()
    return StreamingResponse(stream_create(), media_type="text/event-stream")
  
  save_demo_item(item_id, item_data, dry_run=dry_run)
  
  result = {"item_id": item_id, **item_data}
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Created: {item_id}", result, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html}')
  
  logger.log_function_footer()
  return json_result(True, "", result)

# ----------------------------------------- END: C(jhs) - Create -------------------------------------------------------------


# ----------------------------------------- START: U(jhs) - Update -----------------------------------------------------------

@router.get(f"/{router_name}/update")
async def demorouter_update_docs():
  """
  Update an existing demo item.
  
  Method: PUT
  
  Query params:
  - item_id: ID of the item to update (required)
  - format: Response format - json (default), html, stream
  - dry_run: If true, validate only without updating (optional)
  
  Body (JSON or form data):
  - [fields]: Fields to merge into existing item data
  - item_id: Optional new ID (triggers ID change if different from query string)
  
  ID change: If body contains item_id different from query string:
  1. Validate current item exists (404 if not)
  2. Validate new ID does not exist (400 if collision)
  3. Change item identifier from current to new
  4. Apply remaining body fields
  
  Examples:
  PUT {router_prefix}/{router_name}/update?item_id=example with JSON body {"name": "NewName"}
  PUT {router_prefix}/{router_name}/update?item_id=old_id with JSON body {"item_id": "new_id"} (ID change)

  Example item:
  {example_item_json}
  """
  doc = textwrap.dedent(demorouter_update_docs.__doc__).replace("{router_prefix}", router_prefix).replace("{router_name}", router_name).replace("{example_item_json}", example_item_json.strip())
  return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")

@router.put(f"/{router_name}/update")
async def demorouter_update(request: Request):
  logger = MiddlewareLogger.create()
  logger.log_function_header("demorouter2_update")
  
  query_params = dict(request.query_params)
  item_id = query_params.get("item_id", None)
  format_param = query_params.get("format", "json")
  dry_run = str(query_params.get("dry_run", "false")).lower() == "true"
  
  if not item_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'item_id' query parameter.", {})
  
  body_data = {}
  content_type = request.headers.get("content-type", "")
  try:
    if "application/json" in content_type:
      body_data = await request.json()
    elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
      form = await request.form()
      body_data = dict(form)
    else:
      try:
        body_data = await request.json()
      except:
        form = await request.form()
        body_data = dict(form)
  except: pass
  
  source_item_id = item_id
  target_item_id = body_data.get("item_id", None)
  rename_requested = target_item_id and target_item_id != source_item_id
  
  existing = load_demo_item(source_item_id)
  if existing is None:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": f"Source item '{source_item_id}' not found.", "data": {}}, status_code=404)
  
  if rename_requested and format_param != "stream":
    success, error_msg = rename_demo_item(source_item_id, target_item_id, dry_run=dry_run)
    if not success:
      logger.log_function_footer()
      return JSONResponse({"ok": False, "error": error_msg, "data": {}}, status_code=400)
    item_id = target_item_id
  
  update_data = {k: v for k, v in body_data.items() if k not in ["item_id", "format", "dry_run"]}
  merged_data = {**existing, **update_data}
  
  if format_param == "stream" and not dry_run:
    final_item_id = target_item_id if rename_requested else source_item_id
    writer = StreamingJobWriter(
      persistent_storage_path=get_persistent_storage_path(),
      router_name=router_name,
      action="update",
      object_id=final_item_id,
      source_url=str(request.url),
      router_prefix=router_prefix
    )
    stream_logger = MiddlewareLogger.create(stream_job_writer=writer)
    stream_logger.log_function_header("demorouter2_update")
    
    async def stream_update():
      nonlocal item_id
      try:
        yield writer.emit_start()
        
        if rename_requested:
          sse = stream_logger.log_function_output(f"Renaming item '{source_item_id}' to '{target_item_id}'...")
          if sse: yield sse
          success, error_msg = rename_demo_item(source_item_id, target_item_id)
          if not success:
            sse = stream_logger.log_function_output(f"  FAIL: {error_msg}")
            if sse: yield sse
            stream_logger.log_function_footer()
            yield writer.emit_end(ok=False, error=error_msg, data={})
            return
          sse = stream_logger.log_function_output("  OK.")
          if sse: yield sse
          item_id = target_item_id
        
        sse = stream_logger.log_function_output(f"Updating item '{item_id}'...")
        if sse: yield sse
        save_demo_item(item_id, merged_data)
        sse = stream_logger.log_function_output("  OK.")
        if sse: yield sse
        stream_logger.log_function_footer()
        yield writer.emit_end(ok=True, data={"item_id": item_id, **merged_data})
      finally:
        writer.finalize()
    return StreamingResponse(stream_update(), media_type="text/event-stream")
  
  save_demo_item(item_id, merged_data, dry_run=dry_run)
  
  result = {"item_id": item_id, **merged_data}
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Updated: {item_id}", result, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html}')
  
  logger.log_function_footer()
  return json_result(True, "", result)

# ----------------------------------------- END: U(jhs) - Update -------------------------------------------------------------


# ----------------------------------------- START: D(jhs) - Delete -----------------------------------------------------------

@router.get(f"/{router_name}/delete")
async def demorouter_delete_docs(request: Request):
  """
  Delete a demo item.
  
  Method: DELETE or GET
  
  Parameters:
  - item_id: ID of the item to delete (required)
  - format: Response format - json (default), html, stream
  - dry_run: If true, validate only without deleting (optional)
  
  Examples:
  DELETE {router_prefix}/{router_name}/delete?item_id=example
  GET {router_prefix}/{router_name}/delete?item_id=example

  Example item:
  {example_item_json}
  """
  if len(request.query_params) == 0:
    doc = textwrap.dedent(demorouter_delete_docs.__doc__).replace("{router_prefix}", router_prefix).replace("{router_name}", router_name).replace("{example_item_json}", example_item_json.strip())
    return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")
  return await demorouter_delete_impl(request)

@router.delete(f"/{router_name}/delete")
async def demorouter_delete(request: Request):
  return await demorouter_delete_impl(request)

async def demorouter_delete_impl(request: Request):
  logger = MiddlewareLogger.create()
  logger.log_function_header("demorouter2_delete")
  
  request_params = dict(request.query_params)
  item_id = request_params.get("item_id", None)
  format_param = request_params.get("format", "json")
  dry_run = str(request_params.get("dry_run", "false")).lower() == "true"
  
  if not item_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'item_id' parameter.", {})
  
  existing = load_demo_item(item_id)
  if existing is None:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": f"Demo item '{item_id}' not found.", "data": {}}, status_code=404)
  
  if format_param == "stream" and not dry_run:
    writer = StreamingJobWriter(
      persistent_storage_path=get_persistent_storage_path(),
      router_name=router_name,
      action="delete",
      object_id=item_id,
      source_url=str(request.url),
      router_prefix=router_prefix
    )
    stream_logger = MiddlewareLogger.create(stream_job_writer=writer)
    stream_logger.log_function_header("demorouter2_delete")
    
    async def stream_delete():
      try:
        yield writer.emit_start()
        sse = stream_logger.log_function_output(f"Deleting demo item '{item_id}'...")
        if sse: yield sse
        delete_demo_item(item_id)
        sse = stream_logger.log_function_output("  OK.")
        if sse: yield sse
        stream_logger.log_function_footer()
        yield writer.emit_end(ok=True, data={"item_id": item_id})
      finally:
        writer.finalize()
    return StreamingResponse(stream_delete(), media_type="text/event-stream")
  
  delete_demo_item(item_id, dry_run=dry_run)
  
  deleted_data = {"item_id": item_id, **existing}
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Deleted: {item_id}", deleted_data, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html}')
  
  logger.log_function_footer()
  return json_result(True, "", deleted_data)

# ----------------------------------------- END: D(jhs) - Delete -------------------------------------------------------------


# ----------------------------------------- START: Selftest ------------------------------------------------------------------

@router.get(f"/{router_name}/selftest")
async def demorouter_selftest(request: Request):
  """
  Self-test for demorouter2 CRUD operations.
  
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
  GET {router_prefix}/{router_name}/selftest?format=stream

  Example item:
  {example_item_json}
  """
  import uuid, datetime
  
  request_params = dict(request.query_params)
  
  if len(request_params) == 0:
    doc = textwrap.dedent(demorouter_selftest.__doc__).replace("{router_prefix}", router_prefix).replace("{router_name}", router_name).replace("{example_item_json}", example_item_json.strip())
    return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")
  
  format_param = request_params.get("format", "")
  
  if format_param != "stream":
    return json_result(False, "Selftest only supports format=stream", {})
  
  base_url = str(request.base_url).rstrip("/")
  
  writer = StreamingJobWriter(
    persistent_storage_path=get_persistent_storage_path(),
    router_name=router_name,
    action="selftest",
    object_id=None,
    source_url=str(request.url),
    router_prefix=router_prefix
  )
  stream_logger = MiddlewareLogger.create(stream_job_writer=writer)
  stream_logger.log_function_header("demorouter2_selftest")
  
  test_id = f"selftest_{uuid.uuid4().hex[:8]}"
  test_data_v1 = {"name": "Test Item", "version": 1}
  test_data_v2 = {"name": "Updated Item", "version": 2}
  
  async def run_selftest():
    ok_count = 0
    fail_count = 0
    test_num = 0
    passed_tests = []
    failed_tests = []
    
    def log(msg: str):
      return stream_logger.log_function_output(msg)
    
    def next_test(description: str):
      nonlocal test_num
      test_num += 1
      return log(f"[Test {test_num}] {description}")
    
    def check(condition: bool, ok_msg: str, fail_msg: str):
      nonlocal ok_count, fail_count
      if condition:
        ok_count += 1
        passed_tests.append(ok_msg)
        return log(f"  OK: {ok_msg}")
      else:
        fail_count += 1
        failed_tests.append(fail_msg)
        return log(f"  FAIL: {fail_msg}")
    
    try:
      yield writer.emit_start()
      
      async with httpx.AsyncClient(timeout=30.0) as client:
        create_url = f"{base_url}{router_prefix}/{router_name}/create"
        update_url = f"{base_url}{router_prefix}/{router_name}/update"
        get_url = f"{base_url}{router_prefix}/{router_name}/get?item_id={test_id}&format=json"
        list_url = f"{base_url}{router_prefix}/{router_name}?format=json"
        delete_url = f"{base_url}{router_prefix}/{router_name}/delete?item_id={test_id}"
        
        # Error cases
        sse = next_test("Error cases...")
        if sse: yield sse
        
        r = await client.post(create_url)
        sse = check(r.json().get("ok") == False, "POST /create without body - returns error (ok=false)", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        r = await client.put(update_url)
        sse = check(r.json().get("ok") == False, "PUT /update without body - returns error (ok=false)", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        r = await client.get(f"{base_url}{router_prefix}/{router_name}/get?format=json")
        sse = check(r.json().get("ok") == False, "GET /get without item_id - returns error (ok=false)", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        r = await client.delete(f"{base_url}{router_prefix}/{router_name}/delete")
        sse = check(r.json().get("ok") == False, "DELETE /delete without item_id - returns error (ok=false)", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        # Create dry_run
        sse = next_test(f"POST /create?dry_run=true...")
        if sse: yield sse
        
        r = await client.post(f"{create_url}?dry_run=true", json={"item_id": test_id, **test_data_v1})
        sse = check(r.json().get("ok") == True, "POST /create?dry_run=true - call succeeded (ok=true)", f"Failed: {r.json()}")
        if sse: yield sse
        
        r = await client.get(get_url)
        sse = check(r.status_code == 404, "POST /create?dry_run=true - item not created (GET returns 404)", "Item was created!")
        if sse: yield sse
        
        # Create
        sse = next_test(f"POST /create - Creating '{test_id}'...")
        if sse: yield sse
        
        r = await client.post(create_url, json={"item_id": test_id, **test_data_v1})
        result = r.json()
        sse = check(r.status_code == 200 and result.get("ok") == True, "POST /create - call succeeded (HTTP 200, ok=true)", f"status={r.status_code}, response={result}")
        if sse: yield sse
        
        # Get
        sse = next_test("GET /get - Verifying created item...")
        if sse: yield sse
        
        r = await client.get(get_url)
        result = r.json()
        item_data = result.get("data", {})
        match = (r.status_code == 200 and item_data.get("name") == test_data_v1["name"])
        sse = check(match, f"GET /get - item retrieved with correct data (name='{item_data.get('name')}')", f"status={r.status_code}, data={item_data}")
        if sse: yield sse
        
        # List
        sse = next_test("GET / - Listing all items...")
        if sse: yield sse
        
        r = await client.get(list_url)
        list_result = r.json()
        items = list_result.get("data", [])
        item_ids = [i.get("item_id") for i in items]
        sse = check(test_id in item_ids, f"GET / - item found in list ({len(items)} total)", "Item NOT found in list")
        if sse: yield sse
        
        # Update dry_run
        sse = next_test("PUT /update?dry_run=true...")
        if sse: yield sse
        
        r = await client.put(f"{update_url}?item_id={test_id}&dry_run=true", json=test_data_v2)
        sse = check(r.json().get("ok") == True, "PUT /update?dry_run=true - call succeeded (ok=true)", f"Failed: {r.json()}")
        if sse: yield sse
        
        r = await client.get(get_url)
        unchanged = r.json().get("data", {})
        sse = check(unchanged.get("name") == test_data_v1["name"], "PUT /update?dry_run=true - item not modified (name unchanged)", f"Item was modified: {unchanged}")
        if sse: yield sse
        
        # Update
        sse = next_test("PUT /update...")
        if sse: yield sse
        
        r = await client.put(f"{update_url}?item_id={test_id}", json=test_data_v2)
        sse = check(r.json().get("ok") == True, "PUT /update - call succeeded (ok=true)", f"Failed: {r.json().get('error')}")
        if sse: yield sse
        
        r = await client.get(get_url)
        updated = r.json().get("data", {})
        sse = check(updated.get("name") == test_data_v2["name"], f"PUT /update - item modified (name='{updated.get('name')}')", f"Mismatch: {updated}")
        if sse: yield sse
        
        # Delete dry_run
        sse = next_test("DELETE /delete?dry_run=true...")
        if sse: yield sse
        
        r = await client.delete(f"{delete_url}&dry_run=true")
        result = r.json()
        sse = check(result.get("ok") == True, "DELETE /delete?dry_run=true - call succeeded (ok=true)", f"Failed: {result}")
        if sse: yield sse
        
        r = await client.get(get_url)
        sse = check(r.status_code == 200, "DELETE /delete?dry_run=true - item not deleted (GET returns 200)", "Item was deleted!")
        if sse: yield sse
        
        # Actual delete
        sse = next_test("DELETE /delete - Actual delete...")
        if sse: yield sse
        
        r = await client.delete(delete_url)
        sse = check(r.json().get("ok") == True, "DELETE /delete - call succeeded (ok=true)", f"Failed: {r.json().get('error')}")
        if sse: yield sse
        
        # Verify deletion
        sse = next_test("Verifying deletion...")
        if sse: yield sse
        
        r = await client.get(get_url)
        sse = check(r.status_code == 404, "DELETE /delete - item deleted (GET returns 404)", f"Got: {r.status_code}")
        if sse: yield sse
        
        r = await client.get(list_url)
        items_after = r.json().get("data", [])
        item_ids_after = [i.get("item_id") for i in items_after]
        sse = check(test_id not in item_ids_after, "DELETE /delete - item removed from list", "Item still in list!")
        if sse: yield sse
      
      # Summary
      sse = log(f"")
      if sse: yield sse
      sse = log(f"===== SELFTEST COMPLETE =====")
      if sse: yield sse
      sse = log(f"OK: {ok_count}, FAIL: {fail_count}")
      if sse: yield sse
      
      stream_logger.log_function_footer()
      
      ok = (fail_count == 0)
      yield writer.emit_end(ok=ok, error="" if ok else f"{fail_count} test(s) failed.", data={"passed": ok_count, "failed": fail_count, "passed_tests": passed_tests, "failed_tests": failed_tests})
      
    except Exception as e:
      sse = log(f"ERROR: {type(e).__name__}: {str(e)}")
      if sse: yield sse
      stream_logger.log_function_footer()
      yield writer.emit_end(ok=False, error=str(e), data={"passed": ok_count, "failed": fail_count, "test_id": test_id})
    finally:
      try:
        async with httpx.AsyncClient(timeout=10.0) as cleanup_client:
          await cleanup_client.delete(f"{base_url}{router_prefix}/{router_name}/delete?item_id={test_id}")
      except: pass
      writer.finalize()
  
  return StreamingResponse(run_selftest(), media_type="text/event-stream")

# ----------------------------------------- END: Selftest --------------------------------------------------------------------


# ----------------------------------------- START: Create Demo Items ---------------------------------------------------------

@router.get(f"/{router_name}/create_demo_items")
async def demorouter_create_demo_items(request: Request):
  """
  Create multiple demo items as a long-running operation demo.
  
  Only supports format=stream.
  
  Parameters:
  - count: Number of items to create (default: 10)
  - delay_ms: Delay per item in milliseconds (default: 300)
  
  Examples:
  GET {router_prefix}/{router_name}/create_demo_items?format=stream
  GET {router_prefix}/{router_name}/create_demo_items?format=stream&count=5&delay_ms=500

  Example item:
  {example_item_json}
  """
  import asyncio, uuid, datetime
  
  request_params = dict(request.query_params)
  
  if len(request_params) == 0:
    doc = textwrap.dedent(demorouter_create_demo_items.__doc__).replace("{router_prefix}", router_prefix).replace("{router_name}", router_name).replace("{example_item_json}", example_item_json.strip())
    return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")
  
  format_param = request_params.get("format", "")
  
  if format_param != "stream":
    return json_result(False, "This endpoint only supports format=stream", {})
  
  try:
    count = int(request_params.get("count", "10"))
  except ValueError:
    return json_result(False, "Invalid 'count' parameter. Must be integer.", {})
  
  try:
    delay_ms = int(request_params.get("delay_ms", "300"))
  except ValueError:
    return json_result(False, "Invalid 'delay_ms' parameter. Must be integer.", {})
  
  if count < 1 or count > 100:
    return json_result(False, "'count' must be between 1 and 100.", {})
  
  if delay_ms < 0 or delay_ms > 10000:
    return json_result(False, "'delay_ms' must be between 0 and 10000.", {})
  
  writer = StreamingJobWriter(
    persistent_storage_path=get_persistent_storage_path(),
    router_name=router_name,
    action="create_demo_items",
    object_id=None,
    source_url=str(request.url),
    router_prefix=router_prefix
  )
  stream_logger = MiddlewareLogger.create(stream_job_writer=writer)
  stream_logger.log_function_header("demorouter2_create_demo_items")
  
  async def stream_create_demo_items():
    created_items = []
    failed_items = []
    batch_id = uuid.uuid4().hex[:8]
    
    try:
      yield writer.emit_start()
      
      sse = stream_logger.log_function_output(f"Creating {count} demo items (batch ID='{batch_id}', delay={delay_ms}ms each)...")
      if sse: yield sse
      
      for i in range(count):
        item_id = f"demo_{batch_id}_{i+1:03d}"
        item_data = {
          "name": f"Demo Item {i+1}",
          "version": 1
        }
        
        sse = stream_logger.log_function_output(f"[ {i+1} / {count} ] Creating item '{item_id}'...")
        if sse: yield sse
        
        await asyncio.sleep(delay_ms / 1000.0)
        
        log_events, control_action = await writer.check_control()
        for sse in log_events:
          yield sse
        
        if control_action == ControlAction.CANCEL:
          sse = stream_logger.log_function_output(f"Cancelled after creating {len(created_items)} items.")
          if sse: yield sse
          stream_logger.log_function_footer()
          yield writer.emit_end(ok=False, error="Cancelled by user.", data={"created": len(created_items), "items": created_items}, cancelled=True)
          return
        
        try:
          save_demo_item(item_id, item_data)
          created_items.append(item_id)
          sse = stream_logger.log_function_output("  OK.")
          if sse: yield sse
        except Exception as e:
          failed_items.append({"item_id": item_id, "error": str(e)})
          sse = stream_logger.log_function_output(f"  FAIL: {str(e)}")
          if sse: yield sse
      
      sse = stream_logger.log_function_output(f"")
      if sse: yield sse
      sse = stream_logger.log_function_output(f"Completed: {len(created_items)} created, {len(failed_items)} failed.")
      if sse: yield sse
      
      stream_logger.log_function_footer()
      
      ok = len(failed_items) == 0
      yield writer.emit_end(
        ok=ok,
        error="" if ok else f"{len(failed_items)} item(s) failed.",
        data={"batch_id": batch_id, "created": len(created_items), "failed": len(failed_items), "items": created_items}
      )
      
    except Exception as e:
      sse = stream_logger.log_function_output(f"ERROR: {type(e).__name__}: {str(e)}")
      if sse: yield sse
      stream_logger.log_function_footer()
      yield writer.emit_end(ok=False, error=str(e), data={"created": len(created_items), "items": created_items})
    finally:
      writer.finalize()
  
  return StreamingResponse(stream_create_demo_items(), media_type="text/event-stream")

# ----------------------------------------- END: Create Demo Items -----------------------------------------------------------
