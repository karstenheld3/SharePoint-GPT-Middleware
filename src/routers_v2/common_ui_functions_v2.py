# Common UI Functions V2 - Reusable UI library for V2 routers
# Implements _V2_SPEC_COMMON_UI_FUNCTIONS.md specification

import html, re
from typing import Any, Dict, List, Optional

from fastapi.responses import HTMLResponse, JSONResponse

from common_utility_functions import convert_to_flat_html_table

# ----------------------------------------- START: Internal Helpers ----------------------------------------------------------

def _escape_html(text: str) -> str:
  """Escape HTML special characters."""
  return html.escape(str(text)) if text else ""

def _sanitize_row_id(item_id: str) -> str:
  """Sanitize row ID to alphanumeric + underscore only (V2UI-DD-13)."""
  return re.sub(r'[^a-zA-Z0-9_]', '_', str(item_id))

def _generate_button(btn: Dict, router_prefix: str, item_id: Optional[str]) -> str:
  """Generate a single button HTML with data-* attributes."""
  text = btn.get("text", "")
  btn_class = btn.get("class", "btn-small")
  
  # Build attributes
  attrs = [f'class="{btn_class}"']
  
  # Data attributes for callEndpoint
  if "data_url" in btn:
    url = btn["data_url"].replace("{router_prefix}", router_prefix)
    attrs.append(f'data-url="{_escape_html(url)}"')
  if "data_method" in btn:
    attrs.append(f'data-method="{btn["data_method"]}"')
  if "data_format" in btn:
    attrs.append(f'data-format="{btn["data_format"]}"')
  if "data_show_result" in btn:
    attrs.append(f'data-show-result="{btn["data_show_result"]}"')
  if "data_reload_on_finish" in btn:
    attrs.append(f'data-reload-on-finish="{btn["data_reload_on_finish"]}"')
  
  # Build onclick
  onclick = btn.get("onclick", "")
  confirm_msg = btn.get("confirm_message", "")
  
  if onclick:
    # Replace {itemId} placeholder
    if item_id:
      onclick = onclick.replace("{itemId}", item_id)
    attrs.append(f'onclick="{_escape_html(onclick)}"')
  elif "data_url" in btn:
    # Auto-generate callEndpoint onclick
    if confirm_msg and item_id:
      confirm_escaped = confirm_msg.replace("{itemId}", item_id).replace("'", "\\'")
      attrs.append(f"onclick=\"if(confirm('{confirm_escaped}')) callEndpoint(this, '{item_id}')\"")
    elif item_id:
      attrs.append(f"onclick=\"callEndpoint(this, '{item_id}')\"")
    else:
      attrs.append('onclick="callEndpoint(this)"')
  
  return f'<button {" ".join(attrs)}>{_escape_html(text)}</button>'

# ----------------------------------------- END: Internal Helpers ------------------------------------------------------------


# ----------------------------------------- START: Response Helpers ----------------------------------------------------------

def json_result(ok: bool, error: str, data: Any) -> JSONResponse:
  """Generate consistent JSON response: {ok, error, data}."""
  status_code = 200 if ok else 400
  return JSONResponse({"ok": ok, "error": error, "data": data}, status_code=status_code)

def html_result(title: str, data: Any, navigation_html: str = "") -> HTMLResponse:
  """
  Generate simple HTML page with data table.
  
  Args:
    title: Page title
    data: Data to display in table
    navigation_html: Raw HTML for navigation links (e.g., '<a href="...">Back</a> | <a href="/">Back to Main Page</a>')
  """
  table_html = convert_to_flat_html_table(data) if data else '<p>No data</p>'
  return HTMLResponse(f"""<!doctype html><html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_escape_html(title)}</title>
  <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
  <h1>{_escape_html(title)}</h1>
  {navigation_html}
  {table_html}
</body>
</html>""")

# ----------------------------------------- END: Response Helpers ------------------------------------------------------------


# ----------------------------------------- START: Component Generators ------------------------------------------------------

def generate_html_head(title: str, include_htmx: bool = True, include_v2_css: bool = True, additional_css: str = "") -> str:
  """Generate <head> section with standard resources."""
  htmx_script = '<script src="/static/js/htmx.js"></script>' if include_htmx else ''
  v2_css = '<link rel="stylesheet" href="/static/css/routers_v2.css">' if include_v2_css else ''
  additional_style = f'<style>{additional_css}</style>' if additional_css else ''
  
  return f"""<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_escape_html(title)}</title>
  <link rel="stylesheet" href="/static/css/styles.css">
  {v2_css}
  {htmx_script}
  {additional_style}
</head>"""

def generate_toast_container() -> str:
  """Generate toast notification container div."""
  return '<div id="toast-container" style="z-index: 10001;"></div>'

def generate_modal_structure() -> str:
  """Generate modal overlay with content shell."""
  return """<div id="modal" class="modal-overlay">
    <div class="modal-content" style="max-width: 900px;">
      <button class="modal-close" onclick="closeModal()">&times;</button>
      <div class="modal-body"></div>
    </div>
  </div>"""

def generate_console_panel(title: str = "Console Output", include_pause_resume_cancel: bool = True) -> str:
  """Generate console panel with resize handle and controls."""
  pause_btn = '<button id="btn-pause-resume" onclick="togglePauseResume()" class="btn-small" disabled>Pause</button>' if include_pause_resume_cancel else ''
  cancel_btn = '<button id="btn-cancel" onclick="cancelCurrentJob()" class="btn-small" disabled>Cancel</button>' if include_pause_resume_cancel else ''
  
  return f"""<div id="console-panel" class="console-panel">
    <div class="console-resize-handle" id="console-resize-handle"></div>
    <div class="console-header">
      <div><span id="console-title">{_escape_html(title)}</span> <span id="console-status" class="console-status">(disconnected)</span> <a id="console-monitor-link" href="#" target="_blank" style="display: none; margin-left: 1rem; font-size: 0.85em;"></a></div>
      <div class="console-controls">
        {pause_btn}
        {cancel_btn}
        <button onclick="clearConsole()" class="btn-small">Clear</button>
        <button onclick="hideConsole()" class="console-close">&times;</button>
      </div>
    </div>
    <pre id="console-output" class="console-output"></pre>
  </div>"""

def generate_toolbar(buttons: List[Dict], router_prefix: str, enable_bulk_delete: bool = True) -> str:
  """Generate toolbar with action buttons."""
  buttons_html = []
  for btn in buttons:
    btn_html = _generate_button(btn, router_prefix, None)
    buttons_html.append(btn_html)
  
  if enable_bulk_delete:
    buttons_html.append('<button id="btn-delete-selected" class="btn-primary btn-delete" onclick="bulkDelete()" disabled>Delete (<span id="selected-count">0</span>)</button>')
  
  return f'<div class="toolbar">{" ".join(buttons_html)}</div>'

def generate_table(columns: List[Dict], rows_html: str, enable_selection: bool = True, empty_message: str = "No items found") -> str:
  """Generate table with headers and tbody."""
  header_cells = []
  if enable_selection:
    header_cells.append('<th><input type="checkbox" id="select-all" onchange="toggleSelectAll()"></th>')
  for col in columns:
    header_cells.append(f'<th>{_escape_html(col.get("header", col.get("field", "")))}</th>')
  
  if not rows_html or rows_html.strip() == "":
    colspan = len(columns) + (1 if enable_selection else 0)
    rows_html = f'<tr><td colspan="{colspan}" class="empty-state">{_escape_html(empty_message)}</td></tr>'
  
  return f"""<table>
      <thead><tr>{"".join(header_cells)}</tr></thead>
      <tbody id="items-tbody">{rows_html}</tbody>
    </table>"""

def generate_table_row(item: Dict, columns: List[Dict], row_id_field: str, row_id_prefix: str, router_prefix: str, enable_selection: bool = True) -> str:
  """Generate single table row."""
  item_id = item.get(row_id_field, "")
  sanitized_id = _sanitize_row_id(str(item_id))
  cells = []
  
  if enable_selection:
    cells.append(f'<td><input type="checkbox" class="item-checkbox" data-item-id="{_escape_html(str(item_id))}" onchange="updateSelectedCount()"></td>')
  
  for col in columns:
    field = col.get("field", "")
    if "buttons" in col:
      btn_html = [_generate_button(btn, router_prefix, str(item_id)) for btn in col["buttons"]]
      cells.append(f'<td class="actions">{" ".join(btn_html)}</td>')
    else:
      value = item.get(field, col.get("default", "-"))
      format_func = col.get("format")
      if format_func and callable(format_func): value = format_func(value)
      cells.append(f'<td>{_escape_html(str(value))}</td>')
  
  return f'<tr id="{row_id_prefix}-{sanitized_id}">{"".join(cells)}</tr>'

def generate_all_table_rows(items: List[Dict], columns: List[Dict], row_id_field: str, row_id_prefix: str, router_prefix: str, enable_selection: bool = True) -> str:
  """Generate all table rows for initial render."""
  if not items: return ""
  return "".join([generate_table_row(item, columns, row_id_field, row_id_prefix, router_prefix, enable_selection) for item in items])

# ----------------------------------------- END: Component Generators --------------------------------------------------------


# ----------------------------------------- START: JavaScript Generators -----------------------------------------------------

def generate_core_js() -> str:
  """Generate toast, modal, escapeHtml functions."""
  return """
// ============================================
// TOAST NOTIFICATIONS
// ============================================
function showToast(title, message, type = 'info', autoDismiss = 5000) {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = 'toast toast-' + type;
  toast.innerHTML = '<div class="toast-content"><div class="toast-title">' + escapeHtml(title) + '</div>' + escapeHtml(message) + '</div><button class="toast-close" onclick="this.parentElement.remove()">&times;</button>';
  container.appendChild(toast);
  if (autoDismiss > 0) setTimeout(() => toast.remove(), autoDismiss);
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ============================================
// MODAL FUNCTIONS
// ============================================
const DEFAULT_MODAL_WIDTH = '600px';

function setModalWidth(width) {
  document.querySelector('#modal .modal-content').style.maxWidth = width || DEFAULT_MODAL_WIDTH;
}

function openModal(width) {
  setModalWidth(width);
  document.getElementById('modal').classList.add('visible');
  document.addEventListener('keydown', handleEscapeKey);
  setTimeout(() => {
    const firstInput = document.querySelector('#modal input:not([type="hidden"]), #modal textarea, #modal select');
    if (firstInput) firstInput.focus();
  }, 50);
}

function closeModal() {
  document.getElementById('modal').classList.remove('visible');
  document.removeEventListener('keydown', handleEscapeKey);
  setModalWidth(DEFAULT_MODAL_WIDTH);
}

function handleEscapeKey(event) {
  if (event.key === 'Escape') closeModal();
}

function showModalError(message) {
  const errorEl = document.querySelector('#modal .modal-error');
  if (errorEl) errorEl.textContent = message;
}

function clearModalError() {
  const errorEl = document.querySelector('#modal .modal-error');
  if (errorEl) errorEl.textContent = '';
}

function showResultModal(data) {
  if (document.getElementById('modal').classList.contains('visible')) {
    const resultType = data?.result?.ok !== false ? 'success' : 'error';
    showToast('Job Finished', data?.job_id || '', resultType);
    return;
  }
  
  const isOk = data?.ok !== false && data?.result?.ok !== false;
  const state = data?.state || '';
  const statusText = isOk ? '(OK' + (state ? ', ' + state : '') + ')' : '(FAIL' + (state ? ', ' + state : '') + ')';
  
  let title = 'Result ' + statusText;
  let endpoint = '';
  if (data?.job_id) {
    title += " - '" + data.job_id + "'";
    endpoint = data.source_url || '';
    try { endpoint = new URL(endpoint).pathname + new URL(endpoint).search; } catch (e) {}
  }
  
  const endpointHtml = endpoint ? '<p style="margin: 0; font-size: 0.85rem;"><strong>Endpoint:</strong> ' + escapeHtml(endpoint) + '</p>' : '';
  const errorMsg = data?.error || data?.result?.error || '';
  const errorHtml = errorMsg ? '<p style="color: #dc3545; margin: 0.5rem 0 0 0; font-weight: 500;">' + escapeHtml(errorMsg) + '</p>' : '';
  
  const modalContent = document.querySelector('#modal .modal-content');
  modalContent.style.maxWidth = '800px';
  const body = document.querySelector('#modal .modal-body');
  const formatted = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
  body.innerHTML = `
    <div class="modal-header"><h3>${title}</h3>${endpointHtml}${errorHtml}</div>
    <div class="modal-scroll"><pre class="result-output">${escapeHtml(formatted)}</pre></div>
    <div class="modal-footer"><button type="button" class="btn-primary" onclick="closeModal()">OK</button></div>
  `;
  openModal();
}

// ============================================
// COMMON FORMATTING FUNCTIONS
// ============================================
function formatTimestamp(ts) {
  if (!ts) return '-';
  try {
    const date = new Date(ts);
    const pad = (n) => String(n).padStart(2, '0');
    return date.getFullYear() + '-' + pad(date.getMonth() + 1) + '-' + pad(date.getDate()) + ' ' + pad(date.getHours()) + ':' + pad(date.getMinutes()) + ':' + pad(date.getSeconds());
  } catch (e) {
    return '-';
  }
}

function formatResultOkFail(ok) {
  if (ok === null || ok === undefined) return '-';
  return ok ? 'OK' : 'FAIL';
}

function sanitizeId(id) {
  return (id || '').replace(/[^a-zA-Z0-9]/g, '_');
}

// ============================================
// COMMON SELECTION FUNCTIONS
// ============================================
function updateSelectedCount() {
  const selected = document.querySelectorAll('.item-checkbox:checked');
  const total = document.querySelectorAll('.item-checkbox');
  const count = selected.length;
  const countEl = document.getElementById('selected-count');
  if (countEl) countEl.textContent = count;
  const btn = document.getElementById('btn-delete-selected');
  if (btn) btn.disabled = count === 0;
  const selectAll = document.getElementById('select-all');
  if (selectAll) selectAll.checked = total.length > 0 && count === total.length;
}

function toggleSelectAll() {
  const selectAll = document.getElementById('select-all');
  if (!selectAll) return;
  document.querySelectorAll('.item-checkbox').forEach(cb => cb.checked = selectAll.checked);
  updateSelectedCount();
}

function getSelectedIds() {
  return Array.from(document.querySelectorAll('.item-checkbox:checked')).map(cb => cb.dataset.itemId);
}
"""

def generate_console_js(router_prefix: str, jobs_control_endpoint: str) -> str:
  """Generate SSE streaming and console management functions."""
  return f"""
// ============================================
// CONSOLE STATE
// ============================================
let currentStreamUrl = null;
let currentJobId = null;
let currentMonitorUrl = null;
let isPaused = false;
const MAX_CONSOLE_CHARS = 1000000;

// ============================================
// CONSOLE STREAMING (SSE)
// ============================================
function connectStream(url, options = {{}}) {{
  const method = options.method || 'GET';
  const bodyData = options.bodyData || null;
  const clearConsoleFirst = options.clearConsole !== false;
  const reloadOnFinish = options.reloadOnFinish !== false;
  const showResultIn = options.showResult || 'toast';
  
  showConsole();
  if (clearConsoleFirst) clearConsole();
  currentStreamUrl = url;
  updateConsoleStatus('connecting', url);
  
  const fetchOptions = {{ method }};
  if (bodyData && (method === 'POST' || method === 'PUT')) {{
    fetchOptions.headers = {{ 'Content-Type': 'application/json' }};
    fetchOptions.body = JSON.stringify(bodyData);
  }}
  
  let lastEndJson = null;
  
  fetch(url, fetchOptions).then(response => {{
    updateConsoleStatus('connected', url);
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let currentEvent = 'log';
    
    function read() {{
      reader.read().then(({{ done, value }}) => {{
        if (done) {{
          const finishedJobId = currentJobId;
          currentJobId = null;
          isPaused = false;
          updatePauseResumeButton();
          updateConsoleStatus('disconnected');
          
          if (showResultIn === 'modal' && lastEndJson) {{
            showResultModal(lastEndJson);
          }} else if (showResultIn === 'toast') {{
            const resultType = lastEndJson?.result?.ok ? 'success' : 'error';
            showToast('Job Finished', finishedJobId || '', resultType);
          }}
          
          if (reloadOnFinish && typeof reloadItems === 'function') reloadItems();
          return;
        }}
        const text = decoder.decode(value);
        const lines = text.split('\\n');
        for (const line of lines) {{
          if (line.startsWith('event: ')) {{
            currentEvent = line.substring(7).trim();
          }} else if (line.startsWith('data: ')) {{
            const data = line.substring(6);
            if (currentEvent === 'end_json') {{
              try {{ lastEndJson = JSON.parse(data); }} catch (e) {{}}
            }}
            handleSSEData(currentEvent, data);
            currentEvent = 'log';
          }}
        }}
        read();
      }});
    }}
    read();
  }}).catch(err => {{
    currentJobId = null;
    isPaused = false;
    updatePauseResumeButton();
    showToast('Job Error', err.message, 'error');
    updateConsoleStatus('disconnected');
  }});
}}

function handleSSEData(eventType, data) {{
  if (eventType === 'log') {{
    appendToConsole(data);
  }} else if (eventType === 'start_json') {{
    try {{
      const json = JSON.parse(data);
      currentJobId = json.job_id || null;
      currentMonitorUrl = json.monitor_url || null;
      isPaused = false;
      updatePauseResumeButton();
      updateMonitorLink();
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
// PAUSE / RESUME / CANCEL
// ============================================
function updatePauseResumeCancelButtons() {{
  const pauseBtn = document.getElementById('btn-pause-resume');
  const cancelBtn = document.getElementById('btn-cancel');
  if (pauseBtn) {{
    if (!currentJobId) {{
      pauseBtn.disabled = true;
      pauseBtn.textContent = 'Pause';
    }} else {{
      pauseBtn.disabled = false;
      pauseBtn.textContent = isPaused ? 'Resume' : 'Pause';
    }}
  }}
  if (cancelBtn) {{
    cancelBtn.disabled = !currentJobId;
  }}
}}

function updatePauseResumeButton() {{ updatePauseResumeCancelButtons(); }}

async function togglePauseResume() {{
  if (!currentJobId) return;
  
  const action = isPaused ? 'resume' : 'pause';
  const btn = document.getElementById('btn-pause-resume');
  btn.disabled = true;
  
  try {{
    const response = await fetch(`{jobs_control_endpoint}?job_id=${{currentJobId}}&action=${{action}}`);
    const result = await response.json();
    if (result.ok) {{
      isPaused = !isPaused;
      showToast(isPaused ? 'Paused' : 'Resumed', currentJobId, 'info');
    }} else {{
      showToast('Control Failed', result.error, 'error');
    }}
  }} catch (e) {{
    showToast('Error', e.message, 'error');
  }}
  
  updatePauseResumeCancelButtons();
}}

async function cancelCurrentJob() {{
  if (!currentJobId) return;
  if (!confirm('Cancel job ' + currentJobId + '?')) return;
  
  const cancelBtn = document.getElementById('btn-cancel');
  if (cancelBtn) cancelBtn.disabled = true;
  
  try {{
    const response = await fetch(`{jobs_control_endpoint}?job_id=${{currentJobId}}&action=cancel`);
    const result = await response.json();
    if (result.ok) {{
      showToast('Cancelled', currentJobId, 'info');
    }} else {{
      showToast('Cancel Failed', result.error, 'error');
    }}
  }} catch (e) {{
    showToast('Error', e.message, 'error');
  }}
  
  updatePauseResumeCancelButtons();
}}

function updateConsoleStatus(state) {{
  const statusEl = document.getElementById('console-status');
  if (state === 'disconnected') {{
    statusEl.textContent = '(disconnected)';
  }} else if (state === 'connecting') {{
    statusEl.textContent = '(connecting...)';
  }} else if (state === 'connected') {{
    statusEl.textContent = '(connected)';
  }}
}}

function updateMonitorLink() {{
  const linkEl = document.getElementById('console-monitor-link');
  if (!linkEl) return;
  if (currentMonitorUrl && currentJobId) {{
    const fullUrl = window.location.origin + currentMonitorUrl;
    linkEl.href = currentMonitorUrl;
    linkEl.textContent = fullUrl;
    linkEl.style.display = 'inline';
  }} else {{
    linkEl.style.display = 'none';
  }}
}}

function appendToConsole(text) {{
  const output = document.getElementById('console-output');
  let content = output.textContent + text + '\\n';
  if (content.length > MAX_CONSOLE_CHARS) {{
    content = '...[truncated]\\n' + content.slice(-MAX_CONSOLE_CHARS + 20);
  }}
  output.textContent = content;
  output.scrollTop = output.scrollHeight;
}}

function clearConsole() {{
  document.getElementById('console-output').textContent = '';
}}

function hideConsole() {{
  document.getElementById('console-panel').classList.add('hidden');
}}

function showConsole() {{
  document.getElementById('console-panel').classList.remove('hidden');
}}

// ============================================
// CONSOLE RESIZE
// ============================================
function initConsoleResize() {{
  const panel = document.getElementById('console-panel');
  const handle = document.getElementById('console-resize-handle');
  if (!panel || !handle) return;
  
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
"""

def generate_table_js(router_prefix: str, list_endpoint: str, columns: List[Dict], row_id_field: str, row_id_prefix: str, enable_selection: bool = True, render_row_js: str = None) -> str:
  """Generate table rendering and reload functions."""
  # Generate JS column config for renderItemRow
  js_columns = []
  for col in columns:
    col_def = {"field": col.get("field", ""), "default": col.get("default", "-")}
    if "buttons" in col:
      col_def["buttons"] = col["buttons"]
    if "js_format" in col:
      col_def["js_format"] = col["js_format"]
    js_columns.append(col_def)
  
  # Custom render function or generate default
  if render_row_js:
    render_func = f"function renderItemRow(item) {{ {render_row_js} }}"
  else:
    render_func = _generate_default_render_row_js(columns, row_id_field, row_id_prefix, router_prefix, enable_selection)
  
  return f"""
// ============================================
// TABLE RENDERING
// ============================================
const LIST_ENDPOINT = '{list_endpoint}';
const ROW_ID_FIELD = '{row_id_field}';
const ROW_ID_PREFIX = '{row_id_prefix}';
const ENABLE_SELECTION = {str(enable_selection).lower()};

async function reloadItems() {{
  try {{
    const response = await fetch(LIST_ENDPOINT);
    const result = await response.json();
    if (result.ok) {{
      renderItemsTable(result.data);
      showToast('Reloaded', result.data.length + ' items', 'info');
    }}
  }} catch (e) {{
    showToast('Reload Failed', e.message, 'error');
  }}
}}

function renderItemsTable(items) {{
  const tbody = document.getElementById('items-tbody');
  if (items.length === 0) {{
    const colspan = {len(columns) + (1 if enable_selection else 0)};
    tbody.innerHTML = '<tr><td colspan="' + colspan + '" class="empty-state">No items found</td></tr>';
  }} else {{
    tbody.innerHTML = items.map(item => renderItemRow(item)).join('');
  }}
  const countEl = document.getElementById('item-count');
  if (countEl) countEl.textContent = items.length;
  if (typeof updateSelectedCount === 'function') updateSelectedCount();
}}

{render_func}

function updateItemCount() {{
  const rows = document.querySelectorAll('#items-tbody tr:not(.empty-state)');
  const count = rows.length;
  const countEl = document.getElementById('item-count');
  if (countEl) countEl.textContent = count;
  if (count === 0) {{
    const colspan = {len(columns) + (1 if enable_selection else 0)};
    document.getElementById('items-tbody').innerHTML = '<tr><td colspan="' + colspan + '" class="empty-state">No items found</td></tr>';
  }}
  if (typeof updateSelectedCount === 'function') updateSelectedCount();
}}
"""

def _generate_default_render_row_js(columns: List[Dict], row_id_field: str, row_id_prefix: str, router_prefix: str, enable_selection: bool) -> str:
  """Generate default renderItemRow function based on column config."""
  
  # Build cell generation statements (one per line)
  cell_statements = []
  
  if enable_selection:
    cell_statements.append(
      "  cells.push('<td><input type=\"checkbox\" class=\"item-checkbox\" ' +\n"
      "    'data-item-id=\"' + escapeHtml(String(itemId)) + '\" ' +\n"
      "    'onchange=\"updateSelectedCount()\"></td>');"
    )
  
  for col in columns:
    field = col.get("field", "")
    if "buttons" in col:
      # Generate buttons into separate array, then join
      btn_pushes = []
      for btn in col["buttons"]:
        btn_js = _generate_button_js(btn, router_prefix)
        btn_pushes.append(f"  btns.push({btn_js});")
      buttons_code = "\n".join(btn_pushes)
      cell_statements.append(
        f"  const btns = [];\n{buttons_code}\n  cells.push('<td class=\"actions\">' + btns.join('') + '</td>');"
      )
    else:
      default = col.get("default", "-")
      js_format = col.get("js_format")
      if js_format:
        cell_statements.append(f"  cells.push('<td>' + escapeHtml(String({js_format})) + '</td>');")
      else:
        cell_statements.append(f"  cells.push('<td>' + escapeHtml(String(item.{field} || '{default}')) + '</td>');")
  
  cells_code = "\n".join(cell_statements)
  
  return f"""function renderItemRow(item) {{
  const itemId = item.{row_id_field} || '';
  const rowId = escapeHtml(String(itemId).replace(/[^a-zA-Z0-9_]/g, '_'));
  const cells = [];
  
{cells_code}
  
  return '<tr id=\"{row_id_prefix}-' + rowId + '\">' + cells.join('') + '</tr>';
}}"""

def _generate_button_js(btn: Dict, router_prefix: str) -> str:
  """
  Generate JS code that produces an HTML button string.
  Uses template with placeholder replacement for maintainability.
  """
  # Escaping constants
  esc_dq = '\\"'  # escaped double quote for HTML attributes
  esc_sq = "\\'"  # escaped single quote for JS strings inside onclick
  
  # Template: each [PLACEHOLDER] is replaced or removed
  template = "<button [CLASS][DATA_URL][DATA_METHOD][DATA_FORMAT][DATA_SHOW_RESULT][ONCLICK]>[TEXT]</button>"
  
  # Step 1: Replace [TEXT]
  text = btn.get("text", "")
  template = template.replace("[TEXT]", text)
  
  # Step 2: Replace [CLASS]
  btn_class = btn.get("class", "")
  if btn_class:
    template = template.replace("[CLASS]", f'class={esc_dq}{btn_class}{esc_dq} ')
  else:
    template = template.replace("[CLASS]", "")
  
  # Step 3: Replace [DATA_URL]
  if "data_url" in btn:
    url = btn["data_url"].replace("{router_prefix}", router_prefix)
    template = template.replace("[DATA_URL]", f'data-url={esc_dq}{url}{esc_dq} ')
  else:
    template = template.replace("[DATA_URL]", "")
  
  # Step 4: Replace [DATA_METHOD]
  if "data_method" in btn:
    template = template.replace("[DATA_METHOD]", f'data-method={esc_dq}{btn["data_method"]}{esc_dq} ')
  else:
    template = template.replace("[DATA_METHOD]", "")
  
  # Step 5: Replace [DATA_FORMAT]
  if "data_format" in btn:
    template = template.replace("[DATA_FORMAT]", f'data-format={esc_dq}{btn["data_format"]}{esc_dq} ')
  else:
    template = template.replace("[DATA_FORMAT]", "")
  
  # Step 6: Replace [DATA_SHOW_RESULT]
  if "data_show_result" in btn:
    template = template.replace("[DATA_SHOW_RESULT]", f'data-show-result={esc_dq}{btn["data_show_result"]}{esc_dq} ')
  else:
    template = template.replace("[DATA_SHOW_RESULT]", "")
  
  # Step 7: Build and replace [ONCLICK]
  onclick = btn.get("onclick", "")
  confirm_msg = btn.get("confirm_message", "")
  
  # Helper: itemId patterns for JS string concatenation
  itemId_quoted = esc_sq + "' + itemId + '" + esc_sq  # for function args: \'' + itemId + \'
  itemId_concat = "' + itemId + '"                     # for string concat
  
  def replace_itemId_for_func(s):
    """Replace '{itemId}' for function arguments (needs quotes in output)."""
    return s.replace("'{itemId}'", itemId_quoted).replace("{itemId}", "' + itemId + '")
  
  def replace_itemId_for_string(s):
    """Replace '{itemId}' for string concatenation (no extra quotes)."""
    return s.replace("'{itemId}'", itemId_concat).replace("{itemId}", "' + itemId + '")
  
  onclick_value = ""
  if onclick:
    onclick_value = replace_itemId_for_func(onclick)
  elif "data_url" in btn:
    call_endpoint = f"callEndpoint(this, {itemId_quoted})"
    if confirm_msg:
      # confirm() uses single quotes, but we're inside a JS string literal
      # So we need escaped quotes: confirm(\'...\')
      confirm_text = replace_itemId_for_string(confirm_msg)
      onclick_value = f"if(confirm({esc_sq}{confirm_text}{esc_sq})) {call_endpoint}"
    else:
      onclick_value = call_endpoint
  
  if onclick_value:
    template = template.replace("[ONCLICK]", f'onclick={esc_dq}{onclick_value}{esc_dq}')
  else:
    template = template.replace("[ONCLICK]", "")
  
  # Clean up any double spaces from empty placeholders
  while "  " in template:
    template = template.replace("  ", " ")
  template = template.replace(" >", ">")
  
  # Return as JS string expression
  return f"'{template}'"

def generate_selection_js(router_prefix: str, delete_endpoint: str) -> str:
  """Generate checkbox selection and bulk delete functions."""
  return f"""
// ============================================
// SELECTION & BULK DELETE
// ============================================
const DELETE_ENDPOINT = '{delete_endpoint}';

function updateSelectedCount() {{
  const selected = document.querySelectorAll('.item-checkbox:checked');
  const total = document.querySelectorAll('.item-checkbox');
  const btn = document.getElementById('btn-delete-selected');
  const countEl = document.getElementById('selected-count');
  if (countEl) countEl.textContent = selected.length;
  if (btn) btn.disabled = selected.length === 0;
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
  
  let deleted = 0;
  let failed = 0;
  
  for (const itemId of itemIds) {{
    try {{
      const url = DELETE_ENDPOINT.replace('{{itemId}}', itemId);
      const response = await fetch(url, {{ method: 'DELETE' }});
      const result = await response.json();
      if (result.ok) {{
        const row = document.getElementById(ROW_ID_PREFIX + '-' + itemId.replace(/[^a-zA-Z0-9_]/g, '_'));
        if (row) row.remove();
        deleted++;
      }} else {{
        failed++;
      }}
    }} catch (e) {{
      failed++;
    }}
  }}
  
  updateItemCount();
  
  if (failed === 0) {{
    showToast('Bulk Delete', deleted + ' items deleted', 'success');
  }} else {{
    showToast('Bulk Delete', deleted + ' deleted, ' + failed + ' failed', 'warning');
  }}
}}
"""

def generate_form_js() -> str:
  """Generate form validation helper functions."""
  return """
// ============================================
// FORM VALIDATION
// ============================================
function showFieldError(input, message) {
  clearFieldError(input);
  const error = document.createElement('div');
  error.className = 'form-error';
  error.textContent = message;
  input.parentElement.appendChild(error);
  input.setCustomValidity(message);
}

function clearFieldError(input) {
  const existing = input.parentElement.querySelector('.form-error');
  if (existing) existing.remove();
  input.setCustomValidity('');
}
"""

def generate_endpoint_caller_js() -> str:
  """Generate unified callEndpoint function."""
  return """
// ============================================
// GENERIC ENDPOINT CALLER
// ============================================
async function callEndpoint(btn, itemId = null, bodyData = null) {
  let url = btn.dataset.url;
  if (itemId && url) url = url.replace('{itemId}', itemId);
  
  const method = (btn.dataset.method || 'GET').toUpperCase();
  const format = btn.dataset.format || 'json';
  const showResult = btn.dataset.showResult || 'toast';
  const reloadOnFinish = btn.dataset.reloadOnFinish !== 'false';
  const closeOnSuccess = btn.dataset.closeOnSuccess === 'true';
  
  if (format === 'stream') {
    connectStream(url, { method, bodyData, reloadOnFinish, showResult });
  } else {
    try {
      const options = { method };
      if (bodyData && (method === 'POST' || method === 'PUT')) {
        options.headers = { 'Content-Type': 'application/json' };
        options.body = JSON.stringify(bodyData);
      }
      const response = await fetch(url, options);
      const result = await response.json();
      if (result.ok) {
        if (closeOnSuccess) closeModal();
        if (method === 'DELETE' && itemId) {
          const row = document.getElementById(ROW_ID_PREFIX + '-' + String(itemId).replace(/[^a-zA-Z0-9_]/g, '_'));
          if (row) row.remove();
          updateItemCount();
        } else if (reloadOnFinish && typeof reloadItems === 'function') {
          reloadItems();
        }
        if (showResult === 'modal') {
          showResultModal(result);
        } else if (showResult === 'toast') {
          const msg = itemId ? (method === 'DELETE' ? 'Deleted' : 'Updated') : 'OK';
          showToast(msg, itemId || '', 'success');
        }
      } else {
        if (closeOnSuccess) {
          showModalError(result.error || 'Request failed');
        } else {
          showToast('Failed', result.error, 'error');
        }
      }
    } catch (e) {
      if (closeOnSuccess) {
        showModalError(e.message);
      } else {
        showToast('Error', e.message, 'error');
      }
    }
  }
}
"""

# ----------------------------------------- END: JavaScript Generators -------------------------------------------------------


# ----------------------------------------- START: High-Level Page Generators ------------------------------------------------

def generate_ui_page(
  title: str,
  router_prefix: str,
  items: List[Dict],
  columns: List[Dict],
  row_id_field: str,
  row_id_prefix: str = "item",
  navigation_html: str = "",
  toolbar_buttons: List[Dict] = None,
  enable_selection: bool = True,
  enable_bulk_delete: bool = True,
  console_initially_hidden: bool = False,
  list_endpoint: str = None,
  delete_endpoint: str = None,
  jobs_control_endpoint: str = None,
  render_row_js: str = None,
  additional_js: str = "",
  additional_css: str = ""
) -> str:
  """
  Generate complete UI page with all V2 features.
  
  Args:
    title: Page title
    router_prefix: API prefix (e.g., "/v2")
    items: List of data dictionaries
    columns: Column configuration
    row_id_field: Field name for row ID
    row_id_prefix: Prefix for row ID attribute
    navigation_html: Raw HTML for navigation links (e.g., '<a href="/">Main</a>')
    toolbar_buttons: List of toolbar button configs
    enable_selection: Show checkboxes for selection
    enable_bulk_delete: Show bulk delete button
    console_initially_hidden: If True, console starts hidden
    list_endpoint: Endpoint for reloading items
    delete_endpoint: Endpoint template for delete
    jobs_control_endpoint: Endpoint for pause/resume/cancel
    render_row_js: Custom JS for renderItemRow
    additional_js: Extra JavaScript
    additional_css: Extra CSS
  """
  # Validate required endpoints (V2UI-IG-11, V2UI-IG-12)
  if enable_bulk_delete and not delete_endpoint:
    raise ValueError("delete_endpoint required when enable_bulk_delete=True (V2UI-IG-11)")
  
  # Check if any button has reloadOnFinish (default true) - requires list_endpoint
  needs_reload = False
  if toolbar_buttons:
    for btn in toolbar_buttons:
      if btn.get("data_reload_on_finish", "true") != "false":
        needs_reload = True
        break
  if needs_reload and not list_endpoint:
    raise ValueError("list_endpoint required when toolbar buttons have reloadOnFinish=true (V2UI-IG-12)")
  
  # Generate components
  head = generate_html_head(title, include_htmx=True, include_v2_css=True, additional_css=additional_css)
  toast = generate_toast_container()
  modal = generate_modal_structure()
  
  toolbar = ""
  if toolbar_buttons:
    toolbar = generate_toolbar(toolbar_buttons, router_prefix, enable_bulk_delete)
  elif enable_bulk_delete:
    toolbar = '<div class="toolbar"><button id="btn-delete-selected" class="btn-primary btn-delete" onclick="bulkDelete()" disabled>Delete (<span id="selected-count">0</span>)</button></div>'
  
  rows_html = generate_all_table_rows(items, columns, row_id_field, row_id_prefix, router_prefix, enable_selection)
  table = generate_table(columns, rows_html, enable_selection)
  
  console_class = "console-panel hidden" if console_initially_hidden else "console-panel"
  console = generate_console_panel()
  if console_initially_hidden:
    console = console.replace('class="console-panel"', f'class="{console_class}"')
  
  # Navigation (raw HTML passed by router)
  nav_html = f'<p>{navigation_html}</p>' if navigation_html else ""
  
  # Generate JavaScript
  js_parts = [
    generate_core_js(),
    generate_console_js(router_prefix, jobs_control_endpoint or f"{router_prefix}/jobs/control"),
    generate_endpoint_caller_js(),
    generate_form_js()
  ]
  
  if list_endpoint:
    js_parts.append(generate_table_js(router_prefix, list_endpoint, columns, row_id_field, row_id_prefix, enable_selection, render_row_js))
  
  if enable_selection:
    js_parts.append(generate_selection_js(router_prefix, delete_endpoint or ""))
  
  if additional_js:
    js_parts.append(additional_js)
  
  # DOMContentLoaded initialization
  js_parts.append("""
// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
  initConsoleResize();
});
""")
  
  all_js = "\n".join(js_parts)
  
  return f"""<!doctype html><html lang="en">
{head}
<body class="has-console">
  {toast}
  {modal}

  <div class="container">
    <div class="page-header"><h1 style="margin: 0;">{_escape_html(title)} (<span id="item-count">{len(items)}</span>)</h1> <button class="btn-small" onclick="reloadItems()">Reload</button></div>
    {nav_html}
    
    {toolbar}
    
    {table}
  </div>

  {console}

<script>
{all_js}
</script>
</body>
</html>"""

def generate_router_docs_page(title: str, description: str, router_prefix: str, endpoints: List[Dict], navigation_html: str = "") -> str:
  """
  Generate router root documentation page (HTML).
  
  Args:
    title: Router title
    description: Router description
    router_prefix: API prefix
    endpoints: List of endpoint configs [{"path": "/get", "desc": "Get item", "formats": ["json", "html"]}]
    navigation_html: Raw HTML for navigation links (e.g., '<a href="/">Back to Main Page</a>')
  """
  endpoints_html = []
  for ep in endpoints:
    path = ep.get("path", "")
    desc = ep.get("desc", "")
    formats = ep.get("formats", [])
    
    full_path = f"{router_prefix}{path}"
    format_links = [f'<a href="{full_path}?format={fmt}">{fmt}</a>' for fmt in formats]
    format_html = f" ({' | '.join(format_links)})" if format_links else ""
    
    endpoints_html.append(f'<li><a href="{_escape_html(full_path)}">{_escape_html(full_path)}</a> - {_escape_html(desc)}{format_html}</li>')
  
  return f"""<!doctype html><html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_escape_html(title)}</title>
  <link rel="stylesheet" href="/static/css/styles.css">
  <script src="/static/js/htmx.js"></script>
</head>
<body>
  <h1>{_escape_html(title)}</h1>
  {navigation_html}
  <p>{_escape_html(description)}</p>

  <h4>Available Endpoints</h4>
  <ul>
    {"".join(endpoints_html)}
  </ul>
</body>
</html>"""

def generate_endpoint_docs(docstring: str, router_prefix: str) -> str:
  """
  Generate action endpoint documentation (plain text UTF-8).
  Simply returns docstring with {router_prefix} placeholder replaced.
  """
  return docstring.replace("{router_prefix}", router_prefix) if docstring else ""

# ----------------------------------------- END: High-Level Page Generators --------------------------------------------------
