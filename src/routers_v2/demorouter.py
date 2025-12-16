# Demo Router - V2 router for demonstrating CRUD operations with streaming
# Spec: L(jhu)C(jhs)G(jh)U(jhs)D(jhs): /v2/demorouter
# See _V2_SPEC_ROUTERS.md for specification

import json, os
import httpx
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
def get_demo_item_path(item_id: str) -> str:
  folder = get_demorouter_folder()
  return os.path.join(folder, f"{item_id}.json")

# Load a demo item from file
def load_demo_item(item_id: str) -> dict | None:
  path = get_demo_item_path(item_id)
  if not os.path.exists(path): return None
  with open(path, 'r', encoding='utf-8') as f: return json.load(f)

# Save a demo item to file
def save_demo_item(item_id: str, data: dict) -> None:
  ensure_demorouter_folder()
  path = get_demo_item_path(item_id)
  with open(path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2)

# Delete a demo item file
def delete_demo_item(item_id: str) -> bool:
  path = get_demo_item_path(item_id)
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
      item_id = filename[:-5]
      item = load_demo_item(item_id)
      if item: items.append({"item_id": item_id, **item})
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
  - {router_prefix}/demorouter/get?item_id={id} - Get single item (json, html)
  - {router_prefix}/demorouter/create - Create item (json, html, stream)
  - {router_prefix}/demorouter/update?item_id={id} - Update item (json, html, stream)
  - {router_prefix}/demorouter/delete?item_id={id} - Delete item (json, html, stream)
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
    <li><a href="{router_prefix}/demorouter/get">{router_prefix}/demorouter/get</a> - Get single item (<a href="{router_prefix}/demorouter/get?item_id=example&format=json">JSON</a> | <a href="{router_prefix}/demorouter/get?item_id=example&format=html">HTML</a>)</li>
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
      item_id = item.get("item_id", "")
      name = item.get("name", "-")
      version = item.get("version", "-")
      rows_html += f"""<tr id="item-{item_id}">
        <td><input type="checkbox" class="item-checkbox" data-item-id="{item_id}" onchange="updateSelectedCount()"></td>
        <td>{item_id}</td>
        <td>{name}</td>
        <td>{version}</td>
        <td class="actions">
          <button class="btn-small" onclick="showViewModal('{item_id}')">View</button>
          <button class="btn-small" onclick="showUpdateForm('{item_id}')">Update</button>
          <button class="btn-small btn-delete" data-url="{router_prefix}/demorouter/delete?item_id={{itemId}}" data-method="DELETE" data-format="json" onclick="if(confirm('Delete {item_id}?')) callItemEndpoint(this, '{item_id}')">Delete</button>
        </td>
      </tr>"""
    if not items: rows_html = '<tr><td colspan="5" class="empty-state">No demo items found</td></tr>'
    
    return HTMLResponse(f"""<!doctype html><html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Demo Items</title>
  <link rel="stylesheet" href="/static/css/styles.css">
  <script src="/static/js/htmx.js"></script>
  <style>
    /* Toast Container */
    #toast-container {{ position: fixed; top: 1rem; right: 1rem; z-index: 1000; display: flex; flex-direction: column; gap: 0.5rem; max-width: 400px; }}
    .toast {{ background: #f8f9fa; border: 1px solid #dee2e6; border-left: 4px solid #0078d4; padding: 0.75rem 1rem; border-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; animation: slideIn 0.3s ease-out; }}
    .toast.toast-info {{ border-left-color: #0078d4; }}
    .toast.toast-success {{ border-left-color: #28a745; }}
    .toast.toast-error {{ border-left-color: #dc3545; }}
    .toast.toast-warning {{ border-left-color: #ffc107; }}
    .toast-content {{ flex: 1; font-size: 0.875rem; }}
    .toast-title {{ font-weight: 600; margin-bottom: 0.25rem; }}
    .toast-close {{ background: none; border: none; font-size: 1.2rem; cursor: pointer; color: #6c757d; }}
    @keyframes slideIn {{ from {{ transform: translateX(100%); opacity: 0; }} to {{ transform: translateX(0); opacity: 1; }} }}
    
    /* Modal */
    .modal-overlay {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 1100; }}
    .modal-overlay.visible {{ display: flex; justify-content: center; align-items: center; }}
    .modal-content {{ background: #fff; padding: 1.5rem; border-radius: 8px; max-width: 600px; min-width: 400px; max-height: 80vh; overflow: auto; position: relative; }}
    .modal-close {{ position: absolute; top: 0.5rem; right: 0.5rem; background: none; border: none; font-size: 1.5rem; cursor: pointer; }}
    .empty-state {{ text-align: center; color: #6c757d; padding: 2rem; }}
    
    /* Console Panel - fixed bottom per spec */
    .console-panel {{ position: fixed; bottom: 0; left: 0; right: 0; background: #012456; z-index: 900; height: 232px; display: flex; flex-direction: column; }}
    .console-resize-handle {{ height: 4px; background: #aaaaaa; cursor: ns-resize; flex-shrink: 0; transition: background 0.2s; }}
    .console-resize-handle:hover, .console-resize-handle.dragging {{ background: #0090F1; }}
    .console-header {{ display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 1rem; background: #FAFAFA; border-bottom: 1px solid #d0d0d0; font-size: 0.875rem; font-weight: 500; color: #333333; flex-shrink: 0; }}
    .console-controls {{ display: flex; gap: 0.5rem; }}
    .console-output {{ flex: 1; overflow-y: auto; padding: 0.75rem 1rem; margin: 0; font-family: 'Consolas', 'Monaco', monospace; font-size: 0.9rem; line-height: 1.4; background: #012456; color: #ffffff; white-space: pre-wrap; word-wrap: break-word; }}
    
    /* Main content padding to avoid console overlap */
    .container {{ padding-bottom: 250px; }}
  </style>
</head>
<body>
  <!-- Toast Container -->
  <div id="toast-container"></div>
  
  <!-- Modal -->
  <div id="modal" class="modal-overlay" onclick="closeModalOnBackdrop(event)">
    <div class="modal-content">
      <button class="modal-close" onclick="closeModal()">&times;</button>
      <div class="modal-body"></div>
    </div>
  </div>

  <!-- Main Content -->
  <div class="container">
    <h1>Demo Items (<span id="item-count">{len(items)}</span>)</h1>
    <p><a href="{router_prefix}/demorouter">← Back to Demo Router</a> | <a href="/">← Back to Main Page</a></p>
    
    <div class="toolbar">
      <button class="btn-primary" onclick="refreshItems()">Refresh</button>
      <button class="btn-primary" onclick="showCreateForm()">Create</button>
      <button class="btn-primary" onclick="runSelftest()">Run Selftest</button>
      <button id="btn-delete-selected" class="btn-primary btn-delete" onclick="bulkDelete()" disabled>Delete Selected (0)</button>
    </div>
    
    <table>
      <thead><tr><th><input type="checkbox" id="select-all" onchange="toggleSelectAll()"></th><th>ID</th><th>Name</th><th>Version</th><th>Actions</th></tr></thead>
      <tbody id="items-tbody">{rows_html}</tbody>
    </table>
  </div>

  <!-- Console Panel (always visible, fixed bottom) -->
  <div id="console-panel" class="console-panel">
    <div class="console-resize-handle" id="console-resize-handle"></div>
    <div class="console-header">
      <span id="console-title">Console Output (disconnected)</span>
      <div class="console-controls">
        <button onclick="disconnectStream()" class="btn-small" id="btn-disconnect" disabled>Disconnect</button>
        <button onclick="clearConsole()" class="btn-small">Clear</button>
      </div>
    </div>
    <pre id="console-output" class="console-output"></pre>
  </div>

<script>
// ============================================
// CONSOLE STATE
// ============================================
let currentEventSource = null;
let currentStreamUrl = null;
const MAX_CONSOLE_CHARS = 1000000;

// ============================================
// TOAST NOTIFICATIONS
// ============================================
function showToast(title, message, type = 'info', autoDismiss = 5000) {{
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = 'toast toast-' + type;
  toast.innerHTML = '<div class="toast-content"><div class="toast-title">' + escapeHtml(title) + '</div>' + escapeHtml(message) + '</div><button class="toast-close" onclick="this.parentElement.remove()">&times;</button>';
  container.appendChild(toast);
  if (autoDismiss > 0) setTimeout(() => toast.remove(), autoDismiss);
}}

function escapeHtml(text) {{
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}}

// ============================================
// MODAL FUNCTIONS
// ============================================
function openModal() {{
  document.getElementById('modal').classList.add('visible');
  document.addEventListener('keydown', handleEscapeKey);
}}

function closeModal() {{
  document.getElementById('modal').classList.remove('visible');
  document.removeEventListener('keydown', handleEscapeKey);
}}

function closeModalOnBackdrop(event) {{
  if (event.target.classList.contains('modal-overlay')) closeModal();
}}

function handleEscapeKey(event) {{
  if (event.key === 'Escape') closeModal();
}}

// ============================================
// CONSOLE STREAMING (SSE)
// ============================================
function connectStream(url) {{
  disconnectStream();
  currentStreamUrl = url;
  updateConsoleTitle('connecting', url);
  
  currentEventSource = new EventSource(url);
  
  currentEventSource.onopen = function() {{
    updateConsoleTitle('connected', url);
    document.getElementById('btn-disconnect').disabled = false;
  }};
  
  currentEventSource.onerror = function(e) {{
    if (currentEventSource.readyState === EventSource.CLOSED) {{
      updateConsoleTitle('disconnected');
      document.getElementById('btn-disconnect').disabled = true;
      showToast('Stream Ended', '', 'info');
    }} else {{
      showToast('Connection Error', 'Stream connection failed', 'error');
    }}
    currentEventSource = null;
  }};
  
  // Handle start_json event
  currentEventSource.addEventListener('start_json', function(e) {{
    try {{
      const data = JSON.parse(e.data);
      showToast('Stream Started', data.job_id || '', 'info');
    }} catch (err) {{ }}
  }});
  
  // Handle log event
  currentEventSource.addEventListener('log', function(e) {{
    appendToConsole(e.data);
  }});
  
  // Handle end_json event
  currentEventSource.addEventListener('end_json', function(e) {{
    try {{
      const data = JSON.parse(e.data);
      const resultType = data.result?.ok ? 'success' : 'error';
      showToast('Stream Finished', data.job_id || '', resultType);
    }} catch (err) {{ }}
    disconnectStream();
  }});
}}

function disconnectStream() {{
  if (currentEventSource) {{
    currentEventSource.close();
    currentEventSource = null;
  }}
  currentStreamUrl = null;
  updateConsoleTitle('disconnected');
  document.getElementById('btn-disconnect').disabled = true;
}}

function updateConsoleTitle(state, url = '') {{
  const titleEl = document.getElementById('console-title');
  if (state === 'disconnected') {{
    titleEl.textContent = 'Console Output (disconnected)';
  }} else if (state === 'connecting') {{
    titleEl.textContent = 'Console Output (connecting)...';
  }} else if (state === 'connected') {{
    titleEl.textContent = 'Console Output (connected)';
  }}
}}

function appendToConsole(text) {{
  const output = document.getElementById('console-output');
  let content = output.textContent + text + '\\n';
  
  // Truncate if exceeds max chars (per spec: 1M chars)
  if (content.length > MAX_CONSOLE_CHARS) {{
    content = '...[truncated]\\n' + content.slice(-MAX_CONSOLE_CHARS + 20);
  }}
  
  output.textContent = content;
  
  // Auto-scroll to bottom
  output.scrollTop = output.scrollHeight;
}}

function clearConsole() {{
  document.getElementById('console-output').textContent = '';
}}

// ============================================
// CONSOLE RESIZE (per spec: min 45px, max viewport - 30px)
// ============================================
function initConsoleResize() {{
  const panel = document.getElementById('console-panel');
  const handle = document.getElementById('console-resize-handle');
  let startY, startHeight;
  
  handle.addEventListener('mousedown', function(e) {{
    startY = e.clientY;
    startHeight = panel.offsetHeight;
    handle.classList.add('dragging');
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
    e.preventDefault();
  }});
  
  function onMouseMove(e) {{
    const delta = startY - e.clientY;
    const newHeight = Math.min(Math.max(startHeight + delta, 45), window.innerHeight - 30);
    panel.style.height = newHeight + 'px';
  }}
  
  function onMouseUp() {{
    handle.classList.remove('dragging');
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);
  }}
}}

// ============================================
// GENERIC ENDPOINT CALLERS
// ============================================

// Call item-independent endpoint (Create, Selftest) - refreshes full table on success
async function callEndpoint(btn, bodyData = null) {{
  const url = btn.dataset.url;
  const method = (btn.dataset.method || 'GET').toUpperCase();
  const format = btn.dataset.format || 'json';
  
  if (format === 'stream') {{
    streamRequest(method, url, bodyData, null);
  }} else {{
    try {{
      const options = {{ method }};
      if (bodyData && (method === 'POST' || method === 'PUT')) {{
        options.headers = {{ 'Content-Type': 'application/json' }};
        options.body = JSON.stringify(bodyData);
      }}
      const response = await fetch(url, options);
      const result = await response.json();
      if (result.ok) {{
        showToast('OK', '', 'success');
        refreshItems();
      }} else {{
        showToast('Failed', result.error, 'error');
      }}
    }} catch (e) {{
      showToast('Error', e.message, 'error');
    }}
  }}
}}

// Call item-level endpoint (Update, Delete) - updates/removes specific row on success
async function callItemEndpoint(btn, itemId, bodyData = null) {{
  const url = btn.dataset.url.replace('{{itemId}}', itemId);
  const method = (btn.dataset.method || 'GET').toUpperCase();
  const format = btn.dataset.format || 'json';
  
  if (format === 'stream') {{
    streamRequest(method, url, bodyData, itemId);
  }} else {{
    try {{
      const options = {{ method }};
      if (bodyData && (method === 'POST' || method === 'PUT')) {{
        options.headers = {{ 'Content-Type': 'application/json' }};
        options.body = JSON.stringify(bodyData);
      }}
      const response = await fetch(url, options);
      const result = await response.json();
      if (result.ok) {{
        if (method === 'DELETE') {{
          const row = document.getElementById('item-' + itemId);
          if (row) row.remove();
          showToast('Deleted', itemId, 'success');
          updateItemCount();
        }} else {{
          showToast('Updated', itemId, 'success');
          refreshItems();
        }}
      }} else {{
        showToast('Failed', result.error, 'error');
      }}
    }} catch (e) {{
      showToast('Error', e.message, 'error');
    }}
  }}
}}

// Generic stream request - handles both item-independent and item-level
function streamRequest(method, url, bodyData, itemId) {{
  clearConsole();
  updateConsoleTitle('connecting', url);
  document.getElementById('btn-disconnect').disabled = false;
  
  const options = {{ method }};
  if (bodyData && (method === 'POST' || method === 'PUT')) {{
    options.headers = {{ 'Content-Type': 'application/json' }};
    options.body = JSON.stringify(bodyData);
  }}
  
  fetch(url, options).then(response => {{
    updateConsoleTitle('connected', url);
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let currentEvent = 'log';
    
    function read() {{
      reader.read().then(({{ done, value }}) => {{
        if (done) {{
          updateConsoleTitle('disconnected');
          document.getElementById('btn-disconnect').disabled = true;
          showToast('Stream Finished', '', 'success');
          refreshItems();
          return;
        }}
        const text = decoder.decode(value);
        const lines = text.split('\\n');
        for (const line of lines) {{
          if (line.startsWith('event: ')) {{
            currentEvent = line.substring(7).trim();
          }} else if (line.startsWith('data: ')) {{
            const data = line.substring(6);
            handleSSEData(currentEvent, data);
            currentEvent = 'log';
          }}
        }}
        read();
      }});
    }}
    read();
  }}).catch(err => {{
    showToast('Stream Error', err.message, 'error');
    updateConsoleTitle('disconnected');
    document.getElementById('btn-disconnect').disabled = true;
  }});
}}

// Format SSE events for human-readable console output
function handleSSEData(eventType, data) {{
  if (eventType === 'log') {{
    appendToConsole(data);
  }} else if (eventType === 'start_json') {{
    try {{
      const json = JSON.parse(data);
      appendToConsole("===== START: Job ID='" + json.job_id + "'");
    }} catch (e) {{
      appendToConsole(data);
    }}
  }} else if (eventType === 'end_json') {{
    try {{
      const json = JSON.parse(data);
      const status = json.result?.ok ? 'OK' : 'FAIL';
      const error = json.result?.error ? ' - ' + json.result.error : '';
      appendToConsole("===== END: Job ID='" + json.job_id + "' Result='" + status + error + "'");
    }} catch (e) {{
      appendToConsole(data);
    }}
  }} else {{
    appendToConsole(data);
  }}
}}

// ============================================
// TABLE RENDERING
// ============================================
async function refreshItems() {{
  try {{
    const response = await fetch('{router_prefix}/demorouter?format=json');
    const result = await response.json();
    if (result.ok) {{
      renderItemsTable(result.data);
      showToast('Refreshed', result.data.length + ' items', 'info');
    }}
  }} catch (e) {{
    showToast('Refresh Failed', e.message, 'error');
  }}
}}

function renderItemsTable(items) {{
  const tbody = document.getElementById('items-tbody');
  if (items.length === 0) {{
    tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No demo items found</td></tr>';
  }} else {{
    tbody.innerHTML = items.map(item => renderItemRow(item)).join('');
  }}
  document.getElementById('item-count').textContent = items.length;
  updateSelectedCount();
}}

function renderItemRow(item) {{
  const itemId = item.item_id || '';
  const name = item.name || '-';
  const version = item.version || '-';
  return `<tr id="item-${{itemId}}">
    <td><input type="checkbox" class="item-checkbox" data-item-id="${{itemId}}" onchange="updateSelectedCount()"></td>
    <td>${{itemId}}</td>
    <td>${{name}}</td>
    <td>${{version}}</td>
    <td class="actions">
      <button class="btn-small" onclick="showViewModal('${{itemId}}')">View</button>
      <button class="btn-small" onclick="showUpdateForm('${{itemId}}')">Update</button>
      <button class="btn-small btn-delete" data-url="{router_prefix}/demorouter/delete?item_id={{itemId}}" data-method="DELETE" data-format="json" onclick="if(confirm('Delete ${{itemId}}?')) callItemEndpoint(this, '${{itemId}}')">Delete</button>
    </td>
  </tr>`;
}}

function updateItemCount() {{
  const rows = document.querySelectorAll('#items-tbody tr:not(.empty-state)');
  const count = rows.length;
  document.getElementById('item-count').textContent = count;
  if (count === 0) {{
    document.getElementById('items-tbody').innerHTML = '<tr><td colspan="5" class="empty-state">No demo items found</td></tr>';
  }}
  updateSelectedCount();
}}

// ============================================
// SELECTION & BULK DELETE
// ============================================
function updateSelectedCount() {{
  const selected = document.querySelectorAll('.item-checkbox:checked');
  const total = document.querySelectorAll('.item-checkbox');
  const btn = document.getElementById('btn-delete-selected');
  btn.textContent = 'Delete Selected (' + selected.length + ')';
  btn.disabled = selected.length === 0;
  const selectAll = document.getElementById('select-all');
  if (selectAll) selectAll.checked = total.length > 0 && selected.length === total.length;
}}

function toggleSelectAll() {{
  const selectAll = document.getElementById('select-all');
  const checkboxes = document.querySelectorAll('.item-checkbox');
  checkboxes.forEach(cb => cb.checked = selectAll.checked);
  updateSelectedCount();
}}

function getSelectedItemIds() {{
  const selected = document.querySelectorAll('.item-checkbox:checked');
  return Array.from(selected).map(cb => cb.dataset.itemId);
}}

async function bulkDelete() {{
  const itemIds = getSelectedItemIds();
  if (itemIds.length === 0) return;
  if (!confirm('Delete ' + itemIds.length + ' selected items?')) return;
  
  const btnConfig = {{ dataset: {{ url: '{router_prefix}/demorouter/delete?item_id={{itemId}}', method: 'DELETE', format: 'json' }} }};
  for (const itemId of itemIds) {{
    await callItemEndpoint(btnConfig, itemId, null);
  }}
}}

// ============================================
// VIEW MODAL
// ============================================
async function showViewModal(itemId) {{
  const body = document.querySelector('#modal .modal-body');
  body.innerHTML = '<p>Loading...</p>';
  openModal();
  
  try {{
    const response = await fetch('{router_prefix}/demorouter/get?item_id=' + itemId + '&format=html');
    body.innerHTML = await response.text();
  }} catch (e) {{
    body.innerHTML = '<p>Error: ' + e.message + '</p>';
  }}
}}

// ============================================
// CREATE FORM
// ============================================
function showCreateForm() {{
  const body = document.querySelector('#modal .modal-body');
  body.innerHTML = `
    <h3>Create Demo Item</h3>
    <form id="create-form">
      <p><label>Item ID: <input type="text" name="item_id" required style="width: 200px;"></label></p>
      <p><label>Name: <input type="text" name="name" style="width: 200px;"></label></p>
      <p><label>Version: <input type="number" name="version" value="1" style="width: 80px;"></label></p>
      <p>
        <button type="button" class="btn-primary" data-url="{router_prefix}/demorouter/create" data-method="POST" data-format="json" onclick="submitCreateForm(this)">Create</button>
        <button type="button" class="btn-primary" data-url="{router_prefix}/demorouter/create?format=stream" data-method="POST" data-format="stream" onclick="submitCreateForm(this)">Create (Stream)</button>
        <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
      </p>
    </form>
  `;
  openModal();
}}

function submitCreateForm(btn) {{
  const form = document.getElementById('create-form');
  const formData = new FormData(form);
  const data = Object.fromEntries(formData.entries());
  if (data.version) data.version = parseInt(data.version);
  
  if (!data.item_id) {{
    showToast('Validation Error', 'Item ID is required', 'error');
    return;
  }}
  
  closeModal();
  callEndpoint(btn, data);
}}

// ============================================
// UPDATE FORM
// ============================================
async function showUpdateForm(itemId) {{
  const body = document.querySelector('#modal .modal-body');
  body.innerHTML = '<p>Loading...</p>';
  openModal();
  
  try {{
    const response = await fetch('{router_prefix}/demorouter/get?item_id=' + itemId + '&format=json');
    const result = await response.json();
    if (!result.ok) {{
      body.innerHTML = '<p>Error loading item: ' + result.error + '</p>';
      return;
    }}
    const item = result.data;
    body.innerHTML = `
      <h3>Update Item: ${{itemId}}</h3>
      <form id="update-form">
        <input type="hidden" name="item_id" value="${{itemId}}">
        <p><label>Name: <input type="text" name="name" value="${{item.name || ''}}" style="width: 200px;"></label></p>
        <p><label>Version: <input type="number" name="version" value="${{item.version || ''}}" style="width: 80px;"></label></p>
        <p>
          <button type="button" class="btn-primary" data-url="{router_prefix}/demorouter/update?item_id={{itemId}}" data-method="PUT" data-format="json" onclick="submitUpdateForm(this, '${{itemId}}')">Update</button>
          <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
        </p>
      </form>
    `;
  }} catch (e) {{
    body.innerHTML = '<p>Error: ' + e.message + '</p>';
  }}
}}

function submitUpdateForm(btn, itemId) {{
  const form = document.getElementById('update-form');
  const formData = new FormData(form);
  const data = {{}};
  for (const [key, value] of formData.entries()) {{
    if (value && key !== 'item_id') {{
      data[key] = key === 'version' ? parseInt(value) : value;
    }}
  }}
  
  closeModal();
  callItemEndpoint(btn, itemId, data);
}}

// ============================================
// SELFTEST
// ============================================
function runSelftest() {{
  clearConsole();
  const url = '{router_prefix}/demorouter/selftest?format=stream';
  connectStream(url);
}}

// Initialize on load
document.addEventListener('DOMContentLoaded', function() {{
  initConsoleResize();
}});
</script>
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
  - item_id: ID of the demo item (required)
  - format: Response format - json (default), html
  
  Examples:
  {router_prefix}/demorouter/get?item_id=example
  {router_prefix}/demorouter/get?item_id=example&format=html
  """
  logger = MiddlewareLogger.create()
  logger.log_function_header("demorouter_get")
  
  # Return self-documentation if no params
  if len(request.query_params) == 0:
    logger.log_function_footer()
    return PlainTextResponse(demorouter_get.__doc__.replace("{router_prefix}", router_prefix), media_type="text/plain; charset=utf-8")
  
  request_params = dict(request.query_params)
  item_id = request_params.get("item_id", None)
  format_param = request_params.get("format", "json")
  
  # Validate item_id
  if not item_id:
    logger.log_function_footer()
    if format_param == "html": return html_result("Error", {"error": "Missing 'item_id' parameter."}, f"{router_prefix}/demorouter")
    return json_result(False, "Missing 'item_id' parameter.", {})
  
  # Load item
  item = load_demo_item(item_id)
  if item is None:
    logger.log_function_footer()
    if format_param == "html": return html_result("Not Found", {"error": f"Demo item '{item_id}' not found."}, f"{router_prefix}/demorouter")
    return JSONResponse({"ok": False, "error": f"Demo item '{item_id}' not found.", "data": {}}, status_code=404)
  
  item_with_id = {"item_id": item_id, **item}
  
  if format_param == "json":
    logger.log_function_footer()
    return json_result(True, "", item_with_id)
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Demo Item: {item_id}", item_with_id, f"{router_prefix}/demorouter?format=ui")
  
  logger.log_function_footer()
  return json_result(False, f"Format '{format_param}' not supported. Use: json, html", {})

# ----------------------------------------- END: G(jh) - Get single ------------------------------------------------------------


# ----------------------------------------- START: C(jhs) - Create -------------------------------------------------------------

@router.get("/demorouter/create")
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
  POST {router_prefix}/demorouter/create with JSON body {{"item_id": "example", "name": "Test"}}
  POST {router_prefix}/demorouter/create with form data: item_id=example&name=Test
  """
  return PlainTextResponse(demorouter_create_docs.__doc__.replace("{router_prefix}", router_prefix), media_type="text/plain; charset=utf-8")

@router.post("/demorouter/create")
async def demorouter_create(request: Request):
  logger = MiddlewareLogger.create()
  logger.log_function_header("demorouter_create")
  
  # Control params from query string only
  query_params = dict(request.query_params)
  format_param = query_params.get("format", "json")
  dry_run = str(query_params.get("dry_run", "false")).lower() == "true"
  
  # Data from body only (JSON or form) per DD-E005
  body_data = {}
  content_type = request.headers.get("content-type", "")
  try:
    if "application/json" in content_type:
      body_data = await request.json()
    elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
      form = await request.form()
      body_data = dict(form)
    else:
      # Try JSON first, then form
      try:
        body_data = await request.json()
      except:
        form = await request.form()
        body_data = dict(form)
  except: pass
  
  item_id = body_data.get("item_id", None)
  
  # Validate item_id
  if not item_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'item_id' in request body.", {})
  
  # Check if already exists
  if load_demo_item(item_id) is not None:
    logger.log_function_footer()
    return json_result(False, f"Demo item '{item_id}' already exists.", {"item_id": item_id})
  
  # Build item data (exclude control params)
  item_data = {k: v for k, v in body_data.items() if k not in ["item_id", "format", "dry_run"]}
  
  if dry_run:
    logger.log_function_footer()
    return json_result(True, "", {"item_id": item_id, "dry_run": True, "would_create": item_data})
  
  # format=stream - uses StreamingJobWriter for dual output (STREAM-FR-01)
  if format_param == "stream":
    writer = StreamingJobWriter(
      persistent_storage_path=get_persistent_storage_path(),
      router_name="demorouter",
      action="create",
      object_id=item_id,
      source_url=str(request.url),
      router_prefix=router_prefix
    )
    stream_logger = MiddlewareLogger.create(stream_job_writer=writer)
    stream_logger.log_function_header("demorouter_create")
    
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
  
  # Create item
  save_demo_item(item_id, item_data)
  result = {"item_id": item_id, **item_data}
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Created: {item_id}", result, f"{router_prefix}/demorouter?format=ui")
  
  logger.log_function_footer()
  return json_result(True, "", result)

# ----------------------------------------- END: C(jhs) - Create ---------------------------------------------------------------


# ----------------------------------------- START: U(jhs) - Update -------------------------------------------------------------

@router.get("/demorouter/update")
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
  
  Examples:
  PUT {router_prefix}/demorouter/update?item_id=example with JSON body {{"name": "NewName"}}
  PUT {router_prefix}/demorouter/update?item_id=example with form data: name=NewName
  """
  return PlainTextResponse(demorouter_update_docs.__doc__.replace("{router_prefix}", router_prefix), media_type="text/plain; charset=utf-8")

@router.put("/demorouter/update")
async def demorouter_update(request: Request):
  logger = MiddlewareLogger.create()
  logger.log_function_header("demorouter_update")
  
  # Identifier and control params from query string per DD-E011
  query_params = dict(request.query_params)
  item_id = query_params.get("item_id", None)
  format_param = query_params.get("format", "json")
  dry_run = str(query_params.get("dry_run", "false")).lower() == "true"
  
  # Validate item_id
  if not item_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'item_id' query parameter.", {})
  
  # Update data from body (JSON or form) per DD-E005
  body_data = {}
  content_type = request.headers.get("content-type", "")
  try:
    if "application/json" in content_type:
      body_data = await request.json()
    elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
      form = await request.form()
      body_data = dict(form)
    else:
      # Try JSON first, then form
      try:
        body_data = await request.json()
      except:
        form = await request.form()
        body_data = dict(form)
  except: pass
  
  # Check if exists
  existing = load_demo_item(item_id)
  if existing is None:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": f"Demo item '{item_id}' not found.", "data": {}}, status_code=404)
  
  # Build update data (exclude control params)
  update_data = {k: v for k, v in body_data.items() if k not in ["item_id", "format", "dry_run"]}
  merged_data = {**existing, **update_data}
  
  if dry_run:
    logger.log_function_footer()
    return json_result(True, "", {"item_id": item_id, "dry_run": True, "would_update": merged_data})
  
  # format=stream - uses StreamingJobWriter for dual output (STREAM-FR-01)
  if format_param == "stream":
    writer = StreamingJobWriter(
      persistent_storage_path=get_persistent_storage_path(),
      router_name="demorouter",
      action="update",
      object_id=item_id,
      source_url=str(request.url),
      router_prefix=router_prefix
    )
    stream_logger = MiddlewareLogger.create(stream_job_writer=writer)
    stream_logger.log_function_header("demorouter_update")
    
    async def stream_update():
      try:
        yield writer.emit_start()
        sse = stream_logger.log_function_output(f"Updating demo item '{item_id}'...")
        if sse: yield sse
        save_demo_item(item_id, merged_data)
        sse = stream_logger.log_function_output("  OK.")
        if sse: yield sse
        stream_logger.log_function_footer()
        yield writer.emit_end(ok=True, data={"item_id": item_id, **merged_data})
      finally:
        writer.finalize()
    return StreamingResponse(stream_update(), media_type="text/event-stream")
  
  # Update item
  save_demo_item(item_id, merged_data)
  result = {"item_id": item_id, **merged_data}
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Updated: {item_id}", result, f"{router_prefix}/demorouter?format=ui")
  
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
  - item_id: ID of the item to delete (required)
  - format: Response format - json (default), html, stream
  - dry_run: If true, validate only without deleting (optional)
  
  Examples:
  DELETE {router_prefix}/demorouter/delete?item_id=example
  GET {router_prefix}/demorouter/delete?item_id=example
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
  item_id = request_params.get("item_id", None)
  format_param = request_params.get("format", "json")
  dry_run = str(request_params.get("dry_run", "false")).lower() == "true"
  
  # Validate item_id
  if not item_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'item_id' parameter.", {})
  
  # Check if exists
  existing = load_demo_item(item_id)
  if existing is None:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": f"Demo item '{item_id}' not found.", "data": {}}, status_code=404)
  
  if dry_run:
    logger.log_function_footer()
    return json_result(True, "", {"item_id": item_id, "dry_run": True, "would_delete": existing})
  
  # format=stream - uses StreamingJobWriter for dual output (STREAM-FR-01)
  if format_param == "stream":
    writer = StreamingJobWriter(
      persistent_storage_path=get_persistent_storage_path(),
      router_name="demorouter",
      action="delete",
      object_id=item_id,
      source_url=str(request.url),
      router_prefix=router_prefix
    )
    stream_logger = MiddlewareLogger.create(stream_job_writer=writer)
    stream_logger.log_function_header("demorouter_delete")
    
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
  
  # Delete item
  deleted_data = {"item_id": item_id, **existing}
  delete_demo_item(item_id)
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Deleted: {item_id}", deleted_data, f"{router_prefix}/demorouter?format=ui")
  
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
  
  # Get base URL for HTTP calls to self
  base_url = str(request.base_url).rstrip("/")
  
  # Create StreamingJobWriter for job file
  writer = StreamingJobWriter(
    persistent_storage_path=get_persistent_storage_path(),
    router_name="demorouter",
    action="selftest",
    object_id=None,
    source_url=str(request.url),
    router_prefix=router_prefix
  )
  stream_logger = MiddlewareLogger.create(stream_job_writer=writer)
  stream_logger.log_function_header("demorouter_selftest")
  
  # Test item data
  test_id = f"selftest_{uuid.uuid4().hex[:8]}"
  test_data_v1 = {"name": "Test Item", "created": datetime.datetime.now().isoformat(), "version": 1}
  test_data_v2 = {"name": "Updated Item", "version": 2}
  
  async def run_selftest():
    ok_count = 0
    fail_count = 0
    
    def log(msg: str):
      nonlocal ok_count, fail_count
      sse = stream_logger.log_function_output(msg)
      return sse
    
    def check(condition: bool, ok_msg: str, fail_msg: str):
      nonlocal ok_count, fail_count
      if condition:
        ok_count += 1
        return log(f"  OK: {ok_msg}")
      else:
        fail_count += 1
        return log(f"  FAIL: {fail_msg}")
    
    try:
      yield writer.emit_start()
      
      async with httpx.AsyncClient(timeout=30.0) as client:
        create_url = f"{base_url}{router_prefix}/demorouter/create"
        update_url = f"{base_url}{router_prefix}/demorouter/update"
        get_url = f"{base_url}{router_prefix}/demorouter/get?item_id={test_id}&format=json"
        list_url = f"{base_url}{router_prefix}/demorouter?format=json"
        delete_url = f"{base_url}{router_prefix}/demorouter/delete?item_id={test_id}"
        
        # ===== TEST 1: Error cases =====
        sse = log(f"[Test 1] Error cases...")
        if sse: yield sse
        
        # 1a) POST /create without body -> error
        r = await client.post(create_url)
        sse = check(r.json().get("ok") == False, "POST /create without body returns error", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        # 1b) PUT /update without body -> error
        r = await client.put(update_url)
        sse = check(r.json().get("ok") == False, "PUT /update without body returns error", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        # 1c) GET /get without item_id -> error
        r = await client.get(f"{base_url}{router_prefix}/demorouter/get?format=json")
        sse = check(r.json().get("ok") == False, "GET /get without item_id returns error", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        # 1d) DELETE /delete without item_id -> error
        r = await client.delete(f"{base_url}{router_prefix}/demorouter/delete")
        sse = check(r.json().get("ok") == False, "DELETE /delete without item_id returns error", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        # 1e) PUT /update non-existent item -> 404
        r = await client.put(f"{update_url}?item_id=nonexistent_item_xyz", json={})
        sse = check(r.status_code == 404, "PUT /update non-existent returns 404", f"Expected 404, got: {r.status_code}")
        if sse: yield sse
        
        # 1f) DELETE /delete non-existent item -> 404
        r = await client.delete(f"{base_url}{router_prefix}/demorouter/delete?item_id=nonexistent_item_xyz")
        sse = check(r.status_code == 404, "DELETE /delete non-existent returns 404", f"Expected 404, got: {r.status_code}")
        if sse: yield sse
        
        # 1g) PUT /update without item_id query param -> error
        r = await client.put(f"{update_url}?format=json", json={"name": "Test"})
        sse = check(r.json().get("ok") == False, "PUT /update without item_id query param returns error", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        # 1h) POST /create with empty body {} -> missing item_id error
        r = await client.post(create_url, json={})
        sse = check(r.json().get("ok") == False and "item_id" in r.json().get("error", "").lower(), 
                    "POST /create with {} body returns item_id error", f"Expected item_id error, got: {r.json()}")
        if sse: yield sse
        
        # ===== TEST 2: Create with JSON body =====
        sse = log(f"[Test 2] POST /create with JSON body - Creating '{test_id}'...")
        if sse: yield sse
        
        r = await client.post(create_url, json={"item_id": test_id, **test_data_v1})
        result = r.json()
        sse = check(r.status_code == 200, "POST /create returns HTTP 200", f"Expected 200, got: {r.status_code}")
        if sse: yield sse
        sse = check(result.get("ok") == True and result.get("error") == "" and "data" in result,
                    "Response has {ok:true, error:'', data:...} structure", f"Bad structure: {result}")
        if sse: yield sse
        
        # 2b) Create duplicate -> error
        r = await client.post(create_url, json={"item_id": test_id, "name": "Duplicate"})
        sse = check(r.json().get("ok") == False, "POST /create duplicate returns error", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        # ===== TEST 3: Get item =====
        sse = log(f"[Test 3] GET /get - Verifying created item...")
        if sse: yield sse
        
        r = await client.get(get_url)
        result = r.json()
        sse = check(r.status_code == 200, "GET /get returns HTTP 200", f"Expected 200, got: {r.status_code}")
        if sse: yield sse
        sse = check(result.get("ok") == True and "data" in result, "GET /get returned ok=true with data", f"Failed: {result}")
        if sse: yield sse
        
        item_data = result.get("data", {})
        match = (item_data.get("name") == test_data_v1["name"] and item_data.get("version") == test_data_v1["version"])
        sse = check(match, f"Content matches: name='{item_data.get('name')}', version={item_data.get('version')}", f"Mismatch: {item_data}")
        if sse: yield sse
        
        # ===== TEST 4: List all items =====
        sse = log(f"[Test 4] GET / - Listing all items...")
        if sse: yield sse
        
        r = await client.get(list_url)
        list_result = r.json()
        sse = check(r.status_code == 200, "GET / returns HTTP 200", f"Expected 200, got: {r.status_code}")
        if sse: yield sse
        sse = check(isinstance(list_result.get("data"), list), "List data is array", f"Expected array, got: {type(list_result.get('data'))}")
        if sse: yield sse
        items = list_result.get("data", [])
        item_ids = [i.get("item_id") for i in items]
        sse = check(test_id in item_ids, f"Item found in list ({len(items)} total)", f"Item NOT found in list")
        if sse: yield sse
        
        # ===== TEST 5: dry_run for create =====
        sse = log(f"[Test 5] POST /create?dry_run=true...")
        if sse: yield sse
        
        test_id_dry = f"{test_id}_dry"
        r = await client.post(f"{create_url}?dry_run=true", json={"item_id": test_id_dry, "name": "DryRun"})
        result = r.json()
        sse = check(result.get("ok") == True and result.get("data", {}).get("dry_run") == True, 
                    "dry_run=true returns ok with dry_run flag", f"Failed: {result}")
        if sse: yield sse
        
        # Verify item was NOT created
        r = await client.get(f"{base_url}{router_prefix}/demorouter/get?item_id={test_id_dry}&format=json")
        sse = check(r.status_code == 404, "dry_run did NOT create item (404)", f"Item was created! Status: {r.status_code}")
        if sse: yield sse
        
        # ===== TEST 6: Update with JSON body =====
        sse = log(f"[Test 6] PUT /update with JSON body...")
        if sse: yield sse
        
        r = await client.put(f"{update_url}?item_id={test_id}", json=test_data_v2)
        sse = check(r.json().get("ok") == True, "PUT /update ok=true", f"Failed: {r.json().get('error')}")
        if sse: yield sse
        
        # Verify update
        r = await client.get(get_url)
        updated = r.json().get("data", {})
        sse = check(updated.get("name") == test_data_v2["name"] and updated.get("version") == test_data_v2["version"],
                    f"Update verified: name='{updated.get('name')}', version={updated.get('version')}", f"Mismatch: {updated}")
        if sse: yield sse
        
        # Verify original field preserved
        sse = check(updated.get("created") == test_data_v1["created"], "Original 'created' field preserved", "Field lost")
        if sse: yield sse
        
        # ===== TEST 7: dry_run for update =====
        sse = log(f"[Test 7] PUT /update?dry_run=true...")
        if sse: yield sse
        
        r = await client.put(f"{update_url}?item_id={test_id}&dry_run=true", json={"name": "ShouldNotChange"})
        result = r.json()
        sse = check(result.get("ok") == True and result.get("data", {}).get("dry_run") == True,
                    "dry_run=true returns ok with dry_run flag", f"Failed: {result}")
        if sse: yield sse
        
        # Verify item was NOT changed
        r = await client.get(get_url)
        sse = check(r.json().get("data", {}).get("name") == test_data_v2["name"], 
                    "dry_run did NOT change item", f"Item was changed! Name: {r.json().get('data', {}).get('name')}")
        if sse: yield sse
        
        # ===== TEST 8: Create with form data =====
        sse = log(f"[Test 8] POST /create with form data...")
        if sse: yield sse
        
        test_id_form = f"{test_id}_form"
        r = await client.post(create_url, data={"item_id": test_id_form, "name": "FormItem", "source": "form"})
        sse = check(r.json().get("ok") == True, "POST /create with form data ok=true", f"Failed: {r.json().get('error')}")
        if sse: yield sse
        
        # Verify form-created item
        r = await client.get(f"{base_url}{router_prefix}/demorouter/get?item_id={test_id_form}&format=json")
        form_item = r.json().get("data", {})
        sse = check(form_item.get("name") == "FormItem" and form_item.get("source") == "form",
                    f"Form item verified: name='{form_item.get('name')}', source='{form_item.get('source')}'", f"Mismatch: {form_item}")
        if sse: yield sse
        
        # ===== TEST 9: Update with form data =====
        sse = log(f"[Test 9] PUT /update with form data...")
        if sse: yield sse
        
        r = await client.put(f"{update_url}?item_id={test_id_form}", data={"name": "UpdatedFormItem"})
        sse = check(r.json().get("ok") == True, "PUT /update with form data ok=true", f"Failed: {r.json().get('error')}")
        if sse: yield sse
        
        # Verify update
        r = await client.get(f"{base_url}{router_prefix}/demorouter/get?item_id={test_id_form}&format=json")
        sse = check(r.json().get("data", {}).get("name") == "UpdatedFormItem", "Form update verified", f"Mismatch: {r.json()}")
        if sse: yield sse
        
        # Cleanup form item
        await client.delete(f"{base_url}{router_prefix}/demorouter/delete?item_id={test_id_form}")
        
        # ===== TEST 10: Delete with dry_run =====
        sse = log(f"[Test 10] DELETE /delete?dry_run=true...")
        if sse: yield sse
        
        r = await client.delete(f"{delete_url}&dry_run=true")
        result = r.json()
        sse = check(result.get("ok") == True and result.get("data", {}).get("dry_run") == True,
                    "dry_run=true returns ok with dry_run flag", f"Failed: {result}")
        if sse: yield sse
        
        # Verify item still exists
        r = await client.get(get_url)
        sse = check(r.status_code == 200, "Item still exists after dry_run", "Item was deleted!")
        if sse: yield sse
        
        # ===== TEST 11: Actual delete =====
        sse = log(f"[Test 11] DELETE /delete - Actual delete...")
        if sse: yield sse
        
        r = await client.delete(delete_url)
        sse = check(r.json().get("ok") == True, "DELETE ok=true", f"Failed: {r.json().get('error')}")
        if sse: yield sse
        
        # ===== TEST 12: Verify deletion =====
        sse = log(f"[Test 12] Verifying deletion...")
        if sse: yield sse
        
        r = await client.get(get_url)
        sse = check(r.status_code == 404, "GET deleted item returns 404", f"Got: {r.status_code}")
        if sse: yield sse
        
        r = await client.get(list_url)
        items_after = r.json().get("data", [])
        item_ids_after = [i.get("item_id") for i in items_after]
        sse = check(test_id not in item_ids_after, "Item removed from list", "Item still in list!")
        if sse: yield sse
        
        # Verify empty list returns [] (if no other items)
        if len(items_after) == 0:
          sse = check(isinstance(items_after, list), "Empty list returns [] not error", f"Expected [], got: {items_after}")
          if sse: yield sse
      
      # ===== Summary =====
      sse = log(f"")
      if sse: yield sse
      sse = log(f"===== SELFTEST COMPLETE =====")
      if sse: yield sse
      sse = log(f"OK: {ok_count}, FAIL: {fail_count}")
      if sse: yield sse
      
      stream_logger.log_function_footer()
      
      ok = (fail_count == 0)
      yield writer.emit_end(ok=ok, error="" if ok else f"{fail_count} test(s) failed", data={"ok": ok_count, "fail": fail_count})
      
    except Exception as e:
      sse = log(f"ERROR: {type(e).__name__}: {str(e)}")
      if sse: yield sse
      stream_logger.log_function_footer()
      yield writer.emit_end(ok=False, error=str(e), data={"ok": ok_count, "fail": fail_count, "test_id": test_id})
    finally:
      # Cleanup: ensure test item is deleted via HTTP
      try:
        async with httpx.AsyncClient(timeout=10.0) as cleanup_client:
          await cleanup_client.delete(f"{base_url}{router_prefix}/demorouter/delete?item_id={test_id}")
      except:
        pass
      writer.finalize()
  
  return StreamingResponse(run_selftest(), media_type="text/event-stream")

# ----------------------------------------- END: Selftest ----------------------------------------------------------------------
