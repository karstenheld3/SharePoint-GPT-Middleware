# Sites Router V2 - CRUD operations for SharePoint sites
# Spec: L(jhu)C(jh)G(jh)U(jh)D(jh): /v2/sites
# Uses common_ui_functions_v2.py

import json, os, re, shutil, textwrap, uuid
import httpx
from dataclasses import dataclass, field
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, StreamingResponse

from routers_v2.common_ui_functions_v2 import generate_ui_page, generate_router_docs_page, generate_endpoint_docs, json_result, html_result
from routers_v2.common_logging_functions_v2 import MiddlewareLogger, UNKNOWN
from routers_v2.common_job_functions_v2 import StreamingJobWriter
from hardcoded_config import CRAWLER_HARDCODED_CONFIG

router = APIRouter()
config = None
router_prefix = None
router_name = "sites"
main_page_nav_html = '<a href="/">Back to Main Page</a> | <a href="{router_prefix}/domains?format=ui">Domains</a> | <a href="{router_prefix}/sites?format=ui">Sites</a> | <a href="{router_prefix}/crawler?format=ui">Crawler</a> | <a href="{router_prefix}/jobs?format=ui">Jobs</a> | <a href="{router_prefix}/reports?format=ui">Reports</a>'
example_site_json = """
{
  "name": "Marketing Site",
  "site_url": "https://contoso.sharepoint.com/sites/Marketing",
  "file_scan_result": "",
  "security_scan_result": ""
}
"""

def set_config(app_config, prefix):
  global config, router_prefix
  config = app_config
  router_prefix = prefix

def get_persistent_storage_path(request: Request) -> str:
  """Get persistent storage path from system_info (works in Azure where path is computed)."""
  if hasattr(request.app.state, 'system_info') and request.app.state.system_info:
    return getattr(request.app.state.system_info, 'PERSISTENT_STORAGE_PATH', None) or ''
  return getattr(config, 'LOCAL_PERSISTENT_STORAGE_PATH', None) or ''


# ----------------------------------------- START: Site Data Functions -----------------------------------------------------

@dataclass
class SiteConfig:
  site_id: str
  name: str
  site_url: str
  file_scan_result: str = ""
  security_scan_result: str = ""

def get_sites_folder_path(storage_path: str) -> str:
  return os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_SITES_SUBFOLDER)

def get_site_folder_path(storage_path: str, site_id: str) -> str:
  return os.path.join(get_sites_folder_path(storage_path), site_id)

def get_site_json_path(storage_path: str, site_id: str) -> str:
  return os.path.join(get_site_folder_path(storage_path, site_id), CRAWLER_HARDCODED_CONFIG.SITE_JSON)

def normalize_site_url(url: str) -> str:
  """Strip trailing slash from URL."""
  return url.rstrip('/') if url else url

def validate_site_id(site_id: str) -> tuple[bool, str]:
  """Validate site_id format. Returns (is_valid, error_message)."""
  if not site_id or not site_id.strip():
    return False, "Site ID is required."
  if site_id.startswith('_'):
    return False, "Site ID must not start with '_' (reserved for internal folders)"
  if not re.match(r'^[a-zA-Z0-9_-]+$', site_id):
    return False, "Site ID must match pattern [a-zA-Z0-9_-]+"
  return True, ""

def validate_site_config(data: dict) -> tuple[bool, str]:
  """Validate site data. Returns (is_valid, error_message)."""
  site_id = data.get("site_id", "").strip()
  is_valid, error_msg = validate_site_id(site_id)
  if not is_valid:
    return False, error_msg
  
  name = data.get("name", "").strip()
  if not name:
    return False, "Missing required field: name"
  
  site_url = data.get("site_url", "").strip()
  if not site_url:
    return False, "Missing required field: site_url"
  if not site_url.startswith("https://"):
    return False, "site_url must start with https://"
  
  return True, ""

def site_config_to_dict(site: SiteConfig) -> dict:
  """Convert SiteConfig to dict for JSON serialization."""
  return {
    "site_id": site.site_id,
    "name": site.name,
    "site_url": site.site_url,
    "file_scan_result": site.file_scan_result,
    "security_scan_result": site.security_scan_result
  }

def load_site(storage_path: str, site_id: str, logger=None) -> SiteConfig:
  """Load single site from disk. Raises FileNotFoundError if not found."""
  site_json_path = get_site_json_path(storage_path, site_id)
  if not os.path.exists(site_json_path):
    raise FileNotFoundError(f"Site '{site_id}' not found.")
  
  with open(site_json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
  
  return SiteConfig(
    site_id=site_id,
    name=data.get("name", ""),
    site_url=data.get("site_url", ""),
    file_scan_result=data.get("file_scan_result", ""),
    security_scan_result=data.get("security_scan_result", "")
  )

def load_all_sites(storage_path: str, logger=None) -> list[SiteConfig]:
  """Load all sites from disk. Folders starting with '_' are ignored (internal storage)."""
  sites_folder = get_sites_folder_path(storage_path)
  if not os.path.exists(sites_folder):
    return []
  
  sites = []
  for site_id in os.listdir(sites_folder):
    # Skip folders starting with '_' (reserved for internal storage like caches)
    if site_id.startswith('_'):
      continue
    site_folder = os.path.join(sites_folder, site_id)
    if os.path.isdir(site_folder):
      try:
        site = load_site(storage_path, site_id, logger)
        sites.append(site)
      except Exception as e:
        if logger:
          logger.log_function_output(f"Warning: Could not load site '{site_id}': {str(e)}")
  
  return sorted(sites, key=lambda s: s.site_id)

def save_site_to_file(storage_path: str, site: SiteConfig, logger=None) -> None:
  """Save site to disk. Creates folder if needed."""
  site_folder = get_site_folder_path(storage_path, site.site_id)
  os.makedirs(site_folder, exist_ok=True)
  
  site_json_path = get_site_json_path(storage_path, site.site_id)
  data = {
    "name": site.name,
    "site_url": site.site_url,
    "file_scan_result": site.file_scan_result,
    "security_scan_result": site.security_scan_result
  }
  
  with open(site_json_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

def delete_site_folder(storage_path: str, site_id: str, logger=None) -> bool:
  """Delete site folder. Returns True if deleted, handles FileNotFoundError gracefully."""
  site_folder = get_site_folder_path(storage_path, site_id)
  try:
    if os.path.exists(site_folder):
      shutil.rmtree(site_folder)
    return True
  except FileNotFoundError:
    return True  # Idempotent delete
  except Exception as e:
    if logger:
      logger.log_function_output(f"Error deleting site folder: {str(e)}")
    raise

def rename_site(storage_path: str, old_id: str, new_id: str, logger=None) -> tuple[bool, str]:
  """Rename site folder. Returns (success, error_message)."""
  is_valid, error_msg = validate_site_id(new_id)
  if not is_valid:
    return False, f"Invalid site ID format: {error_msg}"
  
  old_folder = get_site_folder_path(storage_path, old_id)
  new_folder = get_site_folder_path(storage_path, new_id)
  
  if not os.path.exists(old_folder):
    return False, f"Site '{old_id}' not found."
  
  if os.path.exists(new_folder):
    return False, f"Site '{new_id}' already exists."
  
  try:
    os.rename(old_folder, new_folder)
    return True, ""
  except Exception as e:
    return False, f"Error renaming site: {str(e)}"

# ----------------------------------------- END: Site Data Functions -------------------------------------------------------


# ----------------------------------------- START: Router-specific Form JS -------------------------------------------------

def get_router_specific_js() -> str:
  """Router-specific JavaScript for site forms."""
  return f"""
// ============================================
// ROUTER-SPECIFIC FORMS - SITES
// ============================================

const SITE_MODAL_WIDTH = '600px';

function showNotImplemented(feature) {{
  showToast('Not Implemented', `${{feature}} is not yet implemented.`, 'info');
}}

function showNewSiteForm() {{
  const body = document.querySelector('#modal .modal-body');
  body.innerHTML = `
    <div class="modal-header"><h3>New Site</h3></div>
    <div class="modal-scroll">
      <form id="new-site-form" onsubmit="return submitNewSiteForm(event)">
        <div class="form-group">
          <label>Site ID *</label>
          <input type="text" name="site_id" required pattern="[a-zA-Z0-9_\\-]+" title="Only letters, numbers, underscores, and hyphens allowed">
        </div>
        <div class="form-group">
          <label>Name *</label>
          <input type="text" name="name" required>
        </div>
        <div class="form-group">
          <label>Site URL *</label>
          <input type="text" name="site_url" required placeholder="https://contoso.sharepoint.com/sites/MySite">
          <small style="color: #666;">Trailing slash will be removed automatically</small>
        </div>
      </form>
    </div>
    <div class="modal-footer">
      <p class="modal-error"></p>
      <button type="submit" form="new-site-form" class="btn-primary" data-url="{router_prefix}/{router_name}/create" data-method="POST" data-format="json" data-reload-on-finish="true" data-close-on-success="true">OK</button>
      <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
    </div>
  `;
  openModal(SITE_MODAL_WIDTH);
}}

function submitNewSiteForm(event) {{
  event.preventDefault();
  const form = document.getElementById('new-site-form');
  const btn = document.querySelector('.modal-footer button[type="submit"]');
  const formData = new FormData(form);
  const data = {{}};
  
  const siteIdInput = form.querySelector('input[name="site_id"]');
  const siteId = formData.get('site_id');
  if (!siteId || !siteId.trim()) {{
    showFieldError(siteIdInput, 'Site ID is required');
    return;
  }}
  clearFieldError(siteIdInput);
  
  for (const [key, value] of formData.entries()) {{
    if (value && value.trim()) {{
      data[key] = value.trim();
    }}
  }}
  
  clearModalError();
  callEndpoint(btn, null, data);
}}

async function showEditSiteForm(siteId) {{
  const body = document.querySelector('#modal .modal-body');
  body.innerHTML = '<h3>Loading...</h3>';
  openModal(SITE_MODAL_WIDTH);
  
  try {{
    const response = await fetch(`{router_prefix}/{router_name}/get?site_id=${{siteId}}&format=json`);
    const result = await response.json();
    if (!result.ok) {{
      body.innerHTML = '<div class="modal-header"><h3>Error</h3></div><div class="modal-scroll"><p>' + escapeHtml(result.error) + '</p></div><div class="modal-footer"><button class="btn-secondary" onclick="closeModal()">Close</button></div>';
      return;
    }}
    const site = result.data;
    
    body.innerHTML = `
      <div class="modal-header"><h3>Edit Site: ${{escapeHtml(siteId)}}</h3></div>
      <div class="modal-scroll">
        <form id="edit-site-form" onsubmit="return submitEditSiteForm(event)">
          <input type="hidden" name="source_site_id" value="${{escapeHtml(siteId)}}">
          <div class="form-group">
            <label>Site ID</label>
            <input type="text" name="site_id" value="${{escapeHtml(siteId)}}">
            <small style="color: #666;">Change to rename the site</small>
          </div>
          <div class="form-group">
            <label>Name *</label>
            <input type="text" name="name" value="${{escapeHtml(site.name || '')}}" required>
          </div>
          <div class="form-group">
            <label>Site URL *</label>
            <input type="text" name="site_url" value="${{escapeHtml(site.site_url || '')}}" required>
            <small style="color: #666;">Trailing slash will be removed automatically</small>
          </div>
          <div class="form-group">
            <label>File Scan Result (read-only)</label>
            <input type="text" name="file_scan_result" value="${{escapeHtml(site.file_scan_result || '')}}" readonly disabled style="background: #f5f5f5;">
          </div>
          <div class="form-group">
            <label>Security Scan Result (read-only)</label>
            <input type="text" name="security_scan_result" value="${{escapeHtml(site.security_scan_result || '')}}" readonly disabled style="background: #f5f5f5;">
          </div>
        </form>
      </div>
      <div class="modal-footer">
        <p class="modal-error"></p>
        <button type="submit" form="edit-site-form" class="btn-primary" data-url="{router_prefix}/{router_name}/update?site_id=${{siteId}}" data-method="PUT" data-format="json" data-reload-on-finish="true" data-close-on-success="true">OK</button>
        <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
      </div>
    `;
  }} catch (e) {{
    body.innerHTML = '<div class="modal-header"><h3>Error</h3></div><div class="modal-scroll"><p>' + escapeHtml(e.message) + '</p></div><div class="modal-footer"><button class="btn-secondary" onclick="closeModal()">Close</button></div>';
  }}
}}

function submitEditSiteForm(event) {{
  event.preventDefault();
  const form = document.getElementById('edit-site-form');
  const btn = document.querySelector('.modal-footer button[type="submit"]');
  const formData = new FormData(form);
  const data = {{}};
  
  const sourceSiteId = formData.get('source_site_id');
  const targetSiteId = formData.get('site_id');
  
  // Validate Site ID not empty
  const siteIdInput = form.querySelector('input[name="site_id"]');
  if (!targetSiteId || !targetSiteId.trim()) {{
    showFieldError(siteIdInput, 'Site ID cannot be empty');
    return;
  }}
  clearFieldError(siteIdInput);
  
  // Build data object
  for (const [key, value] of formData.entries()) {{
    if (key === 'source_site_id') continue;
    if (key === 'file_scan_result' || key === 'security_scan_result') continue; // Skip read-only fields
    if (key === 'site_id') {{
      // Only include if changed (triggers rename per DD-E014)
      if (value && value.trim() !== sourceSiteId) {{
        data.site_id = value.trim();
      }}
    }} else if (value !== undefined) {{
      data[key] = value.trim();
    }}
  }}
  
  clearModalError();
  callEndpoint(btn, sourceSiteId, data);
}}
"""

# ----------------------------------------- END: Router-specific Form JS ---------------------------------------------------


# ----------------------------------------- START: L(jhu) - Router root / List ---------------------------------------------

@router.get(f"/{router_name}")
async def sites_root(request: Request):
  """Sites Router - CRUD operations for SharePoint sites"""
  logger = MiddlewareLogger.create()
  logger.log_function_header("sites_root")
  request_params = dict(request.query_params)
  
  # Bare GET returns self-documentation
  if len(request_params) == 0:
    logger.log_function_footer()
    endpoints = [
      {"path": "", "desc": "List all sites", "formats": ["json", "html", "ui"]},
      {"path": "/get", "desc": "Get single site", "formats": ["json", "html"]},
      {"path": "/create", "desc": "Create site (POST)", "formats": ["json", "html"]},
      {"path": "/update", "desc": "Update site (PUT)", "formats": ["json", "html"]},
      {"path": "/delete", "desc": "Delete site (DELETE/GET)", "formats": ["json", "html"]},
      {"path": "/selftest", "desc": "Self-test", "formats": ["stream"]}
    ]
    return HTMLResponse(generate_router_docs_page(
      title="Sites",
      description=f"SharePoint sites registered with the middleware. Storage: PERSISTENT_STORAGE_PATH/sites/{{site_id}}/site.json",
      router_prefix=f"{router_prefix}/{router_name}",
      endpoints=endpoints,
      navigation_html=main_page_nav_html.replace("{router_prefix}", router_prefix)
    ))
  
  format_param = request_params.get("format", "json")
  storage_path = get_persistent_storage_path(request)
  
  if not storage_path:
    logger.log_function_footer()
    return json_result(False, "PERSISTENT_STORAGE_PATH not configured", [])
  
  sites = load_all_sites(storage_path, logger)
  sites_list = [site_config_to_dict(s) for s in sites]
  
  if format_param == "json":
    logger.log_function_footer()
    return json_result(True, "", sites_list)
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result("Sites", sites_list, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
  
  if format_param == "ui":
    logger.log_function_footer()
    
    columns = [
      {"field": "site_id", "header": "Site ID"},
      {"field": "name", "header": "Name", "default": "-"},
      {"field": "site_url", "header": "Site URL", "default": "-"},
      {"field": "file_scan_result", "header": "Files", "default": "-"},
      {"field": "security_scan_result", "header": "Security", "default": "-"},
      {
        "field": "actions",
        "header": "Actions",
        "buttons": [
          {"text": "Edit", "onclick": "showEditSiteForm('{itemId}')", "class": "btn-small"},
          {
            "text": "Delete",
            "data_url": f"{router_prefix}/{router_name}/delete?site_id={{itemId}}",
            "data_method": "DELETE",
            "data_format": "json",
            "confirm_message": "Delete site '{itemId}'?",
            "class": "btn-small btn-delete"
          },
          {"text": "File Scan", "onclick": "showNotImplemented(\"File Scan\")", "class": "btn-small btn-disabled"},
          {"text": "Security Scan", "onclick": "showNotImplemented(\"Security Scan\")", "class": "btn-small btn-disabled"}
        ]
      }
    ]
    
    toolbar_buttons = [
      {"text": "New Site", "onclick": "showNewSiteForm()", "class": "btn-primary"},
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
      title="Sites",
      router_prefix=router_prefix,
      items=sites_list,
      columns=columns,
      row_id_field="site_id",
      row_id_prefix="site",
      navigation_html=main_page_nav_html.replace("{router_prefix}", router_prefix),
      toolbar_buttons=toolbar_buttons,
      enable_selection=False,
      enable_bulk_delete=False,
      console_initially_hidden=True,
      list_endpoint=f"{router_prefix}/{router_name}?format=json",
      delete_endpoint=f"{router_prefix}/{router_name}/delete?site_id={{itemId}}",
      additional_js=get_router_specific_js()
    )
    return HTMLResponse(html)
  
  logger.log_function_footer()
  return json_result(False, f"Format '{format_param}' not supported. Use: json, html, ui", {})

# ----------------------------------------- END: L(jhu) - Router root / List -----------------------------------------------


# ----------------------------------------- START: G(jh) - Get single ------------------------------------------------------

@router.get(f"/{router_name}/get")
async def sites_get(request: Request):
  """
  Get a single site by ID.
  
  Parameters:
  - site_id: ID of the site (required)
  - format: Response format - json (default), html
  """
  logger = MiddlewareLogger.create()
  logger.log_function_header("sites_get")
  
  if len(request.query_params) == 0:
    logger.log_function_footer()
    doc = textwrap.dedent(sites_get.__doc__).strip()
    return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")
  
  request_params = dict(request.query_params)
  site_id = request_params.get("site_id", None)
  format_param = request_params.get("format", "json")
  storage_path = get_persistent_storage_path(request)
  
  if not site_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'site_id' parameter.", {})
  
  if not storage_path:
    logger.log_function_footer()
    return json_result(False, "PERSISTENT_STORAGE_PATH not configured", {})
  
  try:
    site = load_site(storage_path, site_id, logger)
    site_dict = site_config_to_dict(site)
  except FileNotFoundError:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": f"Site '{site_id}' not found.", "data": {}}, status_code=404)
  except Exception as e:
    logger.log_function_footer()
    return json_result(False, str(e), {})
  
  if format_param == "json":
    logger.log_function_footer()
    return json_result(True, "", site_dict)
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Site: {site_id}", site_dict, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
  
  logger.log_function_footer()
  return json_result(False, f"Format '{format_param}' not supported. Use: json, html", {})

# ----------------------------------------- END: G(jh) - Get single --------------------------------------------------------


# ----------------------------------------- START: C(jh) - Create ----------------------------------------------------------

@router.get(f"/{router_name}/create")
async def sites_create_docs():
  """
  Create a new site.
  
  Method: POST
  
  Query params:
  - format: Response format - json (default), html
  
  Body (JSON or form data):
  - site_id: Unique ID for the site (required, pattern: [a-zA-Z0-9_-]+)
  - name: Display name (required)
  - site_url: SharePoint site URL (required, must start with https://)
  """
  doc = textwrap.dedent(sites_create_docs.__doc__).strip()
  return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")

@router.post(f"/{router_name}/create")
async def sites_create(request: Request):
  logger = MiddlewareLogger.create()
  logger.log_function_header("sites_create")
  
  query_params = dict(request.query_params)
  format_param = query_params.get("format", "json")
  
  storage_path = get_persistent_storage_path(request)
  if not storage_path:
    logger.log_function_footer()
    return json_result(False, "PERSISTENT_STORAGE_PATH not configured", {})
  
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
  
  # Validate required fields
  is_valid, error_msg = validate_site_config(body_data)
  if not is_valid:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": error_msg, "data": {}}, status_code=400)
  
  site_id = body_data.get("site_id", "").strip()
  
  # Check if site already exists
  try:
    existing = load_site(storage_path, site_id)
    if existing:
      logger.log_function_footer()
      return JSONResponse({"ok": False, "error": f"Site '{site_id}' already exists.", "data": {"site_id": site_id}}, status_code=400)
  except FileNotFoundError:
    pass  # Good, site doesn't exist
  except Exception as e:
    logger.log_function_footer()
    return json_result(False, f"Error checking site: {str(e)}", {})
  
  # Create site config
  site_config = SiteConfig(
    site_id=site_id,
    name=body_data.get("name", "").strip(),
    site_url=normalize_site_url(body_data.get("site_url", "").strip()),
    file_scan_result="",
    security_scan_result=""
  )
  
  # Save to disk
  save_site_to_file(storage_path, site_config, logger)
  
  result = site_config_to_dict(site_config)
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Created: {site_id}", result, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
  
  logger.log_function_footer()
  return json_result(True, "", result)

# ----------------------------------------- END: C(jh) - Create ------------------------------------------------------------


# ----------------------------------------- START: U(jh) - Update ----------------------------------------------------------

@router.get(f"/{router_name}/update")
async def sites_update_docs():
  """
  Update an existing site.
  
  Method: PUT
  
  Query params:
  - site_id: ID of the site to update (required)
  - format: Response format - json (default), html
  
  Body (JSON or form data):
  - site_id: New site ID (optional, triggers rename if different)
  - name: Display name
  - site_url: SharePoint site URL
  
  Note: file_scan_result and security_scan_result are read-only.
  """
  doc = textwrap.dedent(sites_update_docs.__doc__).strip()
  return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")

@router.put(f"/{router_name}/update")
async def sites_update(request: Request):
  logger = MiddlewareLogger.create()
  logger.log_function_header("sites_update")
  
  query_params = dict(request.query_params)
  site_id = query_params.get("site_id", None)
  format_param = query_params.get("format", "json")
  
  if not site_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'site_id' parameter.", {})
  
  storage_path = get_persistent_storage_path(request)
  if not storage_path:
    logger.log_function_footer()
    return json_result(False, "PERSISTENT_STORAGE_PATH not configured", {})
  
  # Load existing site
  try:
    existing = load_site(storage_path, site_id, logger)
  except FileNotFoundError:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": f"Site '{site_id}' not found.", "data": {}}, status_code=404)
  
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
  
  # Rename detection (per DD-E014)
  source_site_id = site_id
  target_site_id = body_data.get("site_id", None)
  rename_requested = target_site_id and target_site_id.strip() != source_site_id
  
  # Handle rename if requested
  if rename_requested:
    target_site_id = target_site_id.strip()
    success, error_msg = rename_site(storage_path, source_site_id, target_site_id)
    if not success:
      logger.log_function_footer()
      return JSONResponse({"ok": False, "error": error_msg, "data": {}}, status_code=400)
    site_id = target_site_id
  
  # Update fields if provided (preserve read-only fields)
  name = body_data.get("name", "").strip() or existing.name
  site_url = body_data.get("site_url", "").strip()
  site_url = normalize_site_url(site_url) if site_url else existing.site_url
  
  # Create updated site config (preserve read-only fields)
  site_config = SiteConfig(
    site_id=site_id,
    name=name,
    site_url=site_url,
    file_scan_result=existing.file_scan_result,
    security_scan_result=existing.security_scan_result
  )
  
  # Save to disk
  save_site_to_file(storage_path, site_config, logger)
  
  result = site_config_to_dict(site_config)
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Updated: {site_id}", result, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
  
  logger.log_function_footer()
  return json_result(True, "", result)

# ----------------------------------------- END: U(jh) - Update ------------------------------------------------------------


# ----------------------------------------- START: D(jh) - Delete ----------------------------------------------------------

@router.get(f"/{router_name}/delete")
async def sites_delete_get(request: Request):
  """Allow DELETE via GET for browser/testing convenience"""
  return await sites_delete(request)

@router.delete(f"/{router_name}/delete")
async def sites_delete(request: Request):
  logger = MiddlewareLogger.create()
  logger.log_function_header("sites_delete")
  
  query_params = dict(request.query_params)
  site_id = query_params.get("site_id", None)
  format_param = query_params.get("format", "json")
  
  if not site_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'site_id' parameter.", {})
  
  storage_path = get_persistent_storage_path(request)
  if not storage_path:
    logger.log_function_footer()
    return json_result(False, "PERSISTENT_STORAGE_PATH not configured", {})
  
  # Load site data BEFORE deletion (DD-E017)
  try:
    site = load_site(storage_path, site_id, logger)
    site_dict = site_config_to_dict(site)
  except FileNotFoundError:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": f"Site '{site_id}' not found.", "data": {}}, status_code=404)
  
  # Delete site
  try:
    delete_site_folder(storage_path, site_id, logger)
  except Exception as e:
    logger.log_function_footer()
    return json_result(False, f"Error deleting site: {str(e)}", {})
  
  # Return deleted site data
  site_dict["deleted"] = True
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Deleted: {site_id}", site_dict, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
  
  logger.log_function_footer()
  return json_result(True, "", site_dict)

# ----------------------------------------- END: D(jh) - Delete ------------------------------------------------------------


# ----------------------------------------- START: Selftest ----------------------------------------------------------------

@router.get(f"/{router_name}/selftest")
async def sites_selftest(request: Request):
  """
  Self-test for sites CRUD operations.
  
  Only supports format=stream.
  
  Tests:
  1. Create site
  2. Get site
  3. Update site
  4. Rename site (ID change)
  5. Delete site
  6. Verify deleted
  
  Example:
  GET {router_prefix}/{router_name}/selftest?format=stream

  Example site:
  {example_site_json}

  Result (end_json event):
  {{
    "ok": true,
    "error": "",
    "data": {{
      "passed": 6,
      "failed": 0,
      "passed_tests": ["Test 1 description", ...],
      "failed_tests": []
    }}
  }}
  """
  request_params = dict(request.query_params)
  
  if len(request_params) == 0:
    doc = textwrap.dedent(sites_selftest.__doc__).replace("{router_prefix}", router_prefix).replace("{router_name}", router_name).replace("{example_site_json}", example_site_json.strip())
    return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")
  
  format_param = request_params.get("format", "")
  
  if format_param != "stream":
    return json_result(False, "Selftest only supports format=stream", {})
  
  base_url = str(request.base_url).rstrip("/")
  
  writer = StreamingJobWriter(
    persistent_storage_path=get_persistent_storage_path(request),
    router_name=router_name,
    action="selftest",
    object_id=None,
    source_url=str(request.url),
    router_prefix=router_prefix
  )
  stream_logger = MiddlewareLogger.create(stream_job_writer=writer)
  stream_logger.log_function_header("sites_selftest")
  
  test_id = f"selftest_{uuid.uuid4().hex[:8]}"
  renamed_test_id = f"{test_id}_renamed"
  underscore_folder_id = f"_internal_{uuid.uuid4().hex[:8]}"
  
  test_site_v1 = {"site_id": test_id, "name": "Test Site", "site_url": "https://test.sharepoint.com/sites/Test"}
  test_site_v2 = {"name": "Updated Site", "site_url": "https://test.sharepoint.com/sites/Updated"}
  
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
      return log(f"[ {test_num} / 9 ] {description}")
    
    def check(condition: bool, ok_msg: str, fail_msg: str):
      nonlocal ok_count, fail_count
      if condition:
        ok_count += 1
        passed_tests.append(ok_msg)
        return log(f"  OK.")
      else:
        fail_count += 1
        failed_tests.append(fail_msg)
        return log(f"  FAIL: {fail_msg}")
    
    try:
      yield writer.emit_start()
      
      async with httpx.AsyncClient(timeout=30.0) as client:
        create_url = f"{base_url}{router_prefix}/{router_name}/create"
        update_url = f"{base_url}{router_prefix}/{router_name}/update"
        get_url = f"{base_url}{router_prefix}/{router_name}/get?site_id={test_id}&format=json"
        delete_url = f"{base_url}{router_prefix}/{router_name}/delete?site_id={test_id}"
        
        # Test 1: Create site
        sse = next_test(f"Creating test site '{test_id}'...")
        if sse: yield sse
        
        r = await client.post(create_url, json=test_site_v1)
        result = r.json()
        sse = check(r.status_code == 200 and result.get("ok") == True, f"Create site '{test_id}'", f"Create failed: {result}")
        if sse: yield sse
        
        # Test 2: Get site
        sse = next_test("Getting test site...")
        if sse: yield sse
        
        r = await client.get(get_url)
        result = r.json()
        site_data = result.get("data", {})
        match = (r.status_code == 200 and site_data.get("name") == test_site_v1["name"])
        sse = check(match, f"Get site '{test_id}'", f"Get failed: {result}")
        if sse: yield sse
        
        # Test 3: Update site
        sse = next_test("Updating test site...")
        if sse: yield sse
        
        r = await client.put(f"{update_url}?site_id={test_id}", json=test_site_v2)
        result = r.json()
        sse = check(r.status_code == 200 and result.get("ok") == True, f"Update site '{test_id}'", f"Update failed: {result}")
        if sse: yield sse
        
        # Test 4: Rename site
        sse = next_test(f"Renaming test site '{test_id}' -> '{renamed_test_id}'...")
        if sse: yield sse
        
        r = await client.put(f"{update_url}?site_id={test_id}", json={"site_id": renamed_test_id})
        result = r.json()
        sse = check(r.status_code == 200 and result.get("ok") == True, f"Rename site to '{renamed_test_id}'", f"Rename failed: {result}")
        if sse: yield sse
        
        # Test 5: Delete site
        sse = next_test(f"Deleting test site '{renamed_test_id}'...")
        if sse: yield sse
        
        r = await client.delete(f"{base_url}{router_prefix}/{router_name}/delete?site_id={renamed_test_id}")
        result = r.json()
        sse = check(r.status_code == 200 and result.get("ok") == True, f"Delete site '{renamed_test_id}'", f"Delete failed: {result}")
        if sse: yield sse
        
        # Test 6: Verify deleted
        sse = next_test("Verifying deletion...")
        if sse: yield sse
        
        r = await client.get(f"{base_url}{router_prefix}/{router_name}/get?site_id={renamed_test_id}&format=json")
        sse = check(r.status_code == 404, "Verify site deleted (404)", f"Expected 404, got: {r.status_code}")
        if sse: yield sse
        
        # Test 7: Create with underscore prefix should fail
        sse = next_test("Creating site with underscore prefix (should fail)...")
        if sse: yield sse
        
        underscore_site = {"site_id": "_invalid_site", "name": "Invalid", "site_url": "https://test.sharepoint.com"}
        r = await client.post(create_url, json=underscore_site)
        result = r.json()
        sse = check(result.get("ok") == False and "must not start with '_'" in result.get("error", ""), "Reject underscore prefix site_id", f"Expected rejection, got: {result}")
        if sse: yield sse
        
        # Test 8: Create underscore folder directly, verify not in list
        sse = next_test("Verifying underscore folders ignored in list...")
        if sse: yield sse
        
        # Create underscore folder directly on disk
        storage_path = get_persistent_storage_path(request)
        underscore_folder = get_site_folder_path(storage_path, underscore_folder_id)
        os.makedirs(underscore_folder, exist_ok=True)
        with open(os.path.join(underscore_folder, CRAWLER_HARDCODED_CONFIG.SITE_JSON), 'w') as f:
          json.dump({"name": "Internal", "site_url": "https://internal.test"}, f)
        
        r = await client.get(f"{base_url}{router_prefix}/{router_name}?format=json")
        sites_list = r.json().get("data", [])
        site_ids = [s.get("site_id") for s in sites_list]
        sse = check(underscore_folder_id not in site_ids, f"Underscore folder '{underscore_folder_id}' not in list", f"Found in list: {site_ids}")
        if sse: yield sse
        
        # Test 9: Cleanup underscore folder
        sse = next_test("Cleaning up underscore folder...")
        if sse: yield sse
        
        shutil.rmtree(underscore_folder, ignore_errors=True)
        sse = check(not os.path.exists(underscore_folder), "Underscore folder cleaned up", "Folder still exists")
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
      sse = log(f"ERROR: Self-test failed -> {type(e).__name__}: {str(e)}")
      if sse: yield sse
      stream_logger.log_function_footer()
      yield writer.emit_end(ok=False, error=str(e), data={"passed": ok_count, "failed": fail_count, "test_id": test_id})
    finally:
      try:
        async with httpx.AsyncClient(timeout=10.0) as cleanup_client:
          await cleanup_client.delete(f"{base_url}{router_prefix}/{router_name}/delete?site_id={test_id}")
          await cleanup_client.delete(f"{base_url}{router_prefix}/{router_name}/delete?site_id={renamed_test_id}")
        # Cleanup underscore folder if it exists
        storage_path = get_persistent_storage_path(request)
        underscore_folder = get_site_folder_path(storage_path, underscore_folder_id)
        shutil.rmtree(underscore_folder, ignore_errors=True)
      except: pass
      writer.finalize()
  
  return StreamingResponse(run_selftest(), media_type="text/event-stream")

# ----------------------------------------- END: Selftest ------------------------------------------------------------------
