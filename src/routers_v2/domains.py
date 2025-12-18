# Domains Router V2 - CRUD operations for knowledge domains
# Spec: L(jhu)C(jhs)G(jh)U(jhs)D(jhs): /v2/domains
# Uses common_ui_functions_v2.py and common_crawler_functions_v2.py

import json, os, textwrap
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from routers_v2.common_ui_functions_v2 import generate_ui_page, generate_router_docs_page, generate_endpoint_docs, json_result, html_result
from routers_v2.common_logging_functions_v2 import MiddlewareLogger
from routers_v2.common_crawler_functions_v2 import (
  DomainConfig, FileSource, SitePageSource, ListSource,
  load_domain, load_all_domains, save_domain_to_file, delete_domain_folder,
  validate_domain_config, domain_config_to_dict
)

router = APIRouter()
config = None
router_prefix = None
router_name = "domains"
main_page_nav_html = '<a href="/">Back to Main Page</a>'

def set_config(app_config, prefix):
  global config, router_prefix
  config = app_config
  router_prefix = prefix

def get_persistent_storage_path() -> str:
  return getattr(config, 'LOCAL_PERSISTENT_STORAGE_PATH', None) or ''


# ----------------------------------------- START: Router-specific Form JS ---------------------------------------------------

def get_router_specific_js() -> str:
  """Router-specific JavaScript for domain forms."""
  return f"""
// ============================================
// ROUTER-SPECIFIC FORMS - DOMAINS
// ============================================

const demoSourcesJson = {{
  "file_sources": [
    {{
      "source_id": "source01",
      "site_url": "https://example.sharepoint.com/sites/MySite",
      "sharepoint_url_part": "/Shared Documents",
      "filter": ""
    }}
  ],
  "sitepage_sources": [
    {{
      "source_id": "source01",
      "site_url": "https://example.sharepoint.com/sites/MySite",
      "sharepoint_url_part": "/SitePages",
      "filter": "FSObjType eq 0"
    }}
  ],
  "list_sources": [
    {{
      "source_id": "source01",
      "site_url": "https://example.sharepoint.com/sites/MySite",
      "list_name": "My List",
      "filter": ""
    }}
  ]
}};

function showJsonExampleDialog(targetTextareaId) {{
  const formatted = JSON.stringify(demoSourcesJson, null, 2);
  
  // Create a second modal for JSON example
  const overlay = document.createElement('div');
  overlay.id = 'json-example-modal';
  overlay.className = 'modal-overlay visible';
  overlay.style.zIndex = '10002';
  overlay.innerHTML = `
    <div class="modal-content" style="max-width: 700px;">
      <button class="modal-close" onclick="closeJsonExample()">&times;</button>
      <div class="modal-body">
        <div class="modal-header"><h3>JSON Example</h3></div>
        <div class="modal-scroll">
          <p>Copy this example and modify it for your needs:</p>
          <textarea readonly rows="20" style="width: 100%; font-family: monospace; font-size: 12px;">${{formatted}}</textarea>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn-primary" onclick="copyJsonToForm('${{targetTextareaId}}')">Copy to Form</button>
          <button type="button" class="btn-secondary" onclick="closeJsonExample()">Close</button>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);
}}

function copyJsonToForm(targetTextareaId) {{
  document.getElementById(targetTextareaId).value = JSON.stringify(demoSourcesJson, null, 2);
  closeJsonExample();
}}

function closeJsonExample() {{
  const modal = document.getElementById('json-example-modal');
  if (modal) modal.remove();
}}

function showNewDomainForm() {{
  const body = document.querySelector('#modal .modal-body');
  body.innerHTML = `
    <div class="modal-header"><h3>New Domain</h3></div>
    <div class="modal-scroll">
      <form id="new-domain-form" onsubmit="return submitNewDomainForm(event)">
        <div class="form-group">
          <label>Domain ID *</label>
          <input type="text" name="domain_id" required pattern="[a-zA-Z0-9_\\-]+" title="Only letters, numbers, underscores, and hyphens allowed">
        </div>
        <div class="form-group">
          <label>Name *</label>
          <input type="text" name="name" required>
        </div>
        <div class="form-group">
          <label>Description *</label>
          <textarea name="description" rows="3" required></textarea>
        </div>
        <div class="form-group">
          <label>Vector Store Name *</label>
          <input type="text" name="vector_store_name" required>
        </div>
        <div class="form-group">
          <label>Vector Store ID</label>
          <input type="text" name="vector_store_id" placeholder="Optional - leave empty if not needed">
        </div>
        <details class="form-group">
          <summary style="cursor: pointer; font-weight: bold; margin-bottom: 10px;">Advanced: Sources Configuration (Optional)</summary>
          <div class="form-group">
            <label>Sources JSON (file_sources, sitepage_sources, list_sources)</label>
            <button type="button" class="btn-small" onclick="showJsonExampleDialog('sources_json')" style="margin-bottom: 5px;">Show JSON Example</button>
            <textarea id="sources_json" name="sources_json" rows="10" placeholder='{{"file_sources": [], "sitepage_sources": [], "list_sources": []}}'></textarea>
            <small style="color: #666;">Leave empty to create domain without sources. You can add them later.</small>
          </div>
        </details>
      </form>
    </div>
    <div class="modal-footer">
      <button type="submit" form="new-domain-form" class="btn-primary" data-url="{router_prefix}/{router_name}/create" data-method="POST" data-format="json" data-reload-on-finish="true">OK</button>
      <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
    </div>
  `;
  openModal();
}}

function submitNewDomainForm(event) {{
  event.preventDefault();
  const form = document.getElementById('new-domain-form');
  const btn = document.querySelector('.modal-footer button[type="submit"]');
  const formData = new FormData(form);
  const data = {{}};
  
  const domainIdInput = form.querySelector('input[name="domain_id"]');
  const domainId = formData.get('domain_id');
  if (!domainId || !domainId.trim()) {{
    showFieldError(domainIdInput, 'Domain ID is required');
    return;
  }}
  clearFieldError(domainIdInput);
  
  for (const [key, value] of formData.entries()) {{
    if (value && value.trim()) {{
      data[key] = value.trim();
    }}
  }}
  
  closeModal();
  callEndpoint(btn, null, data);
}}

async function showUpdateDomainForm(domainId) {{
  const body = document.querySelector('#modal .modal-body');
  body.innerHTML = '<h3>Loading...</h3>';
  openModal();
  
  try {{
    const response = await fetch(`{router_prefix}/{router_name}/get?domain_id=${{domainId}}&format=json`);
    const result = await response.json();
    if (!result.ok) {{
      body.innerHTML = '<h3>Error</h3><p>' + escapeHtml(result.error) + '</p><div class="form-actions"><button class="btn-secondary" onclick="closeModal()">Close</button></div>';
      return;
    }}
    const domain = result.data;
    
    const sourcesJson = {{
      file_sources: domain.file_sources || [],
      sitepage_sources: domain.sitepage_sources || [],
      list_sources: domain.list_sources || []
    }};
    const sourcesJsonStr = (sourcesJson.file_sources.length || sourcesJson.sitepage_sources.length || sourcesJson.list_sources.length) 
      ? JSON.stringify(sourcesJson, null, 2) : '';
    
    body.innerHTML = `
      <div class="modal-header"><h3>Edit Domain: ${{escapeHtml(domainId)}}</h3></div>
      <div class="modal-scroll">
        <form id="update-domain-form" onsubmit="return submitUpdateDomainForm(event)">
          <input type="hidden" name="domain_id" value="${{escapeHtml(domainId)}}">
          <div class="form-group">
            <label>Domain ID</label>
            <input type="text" value="${{escapeHtml(domainId)}}" disabled>
          </div>
          <div class="form-group">
            <label>Name *</label>
            <input type="text" name="name" value="${{escapeHtml(domain.name || '')}}" required>
          </div>
          <div class="form-group">
            <label>Description *</label>
            <textarea name="description" rows="3" required>${{escapeHtml(domain.description || '')}}</textarea>
          </div>
          <div class="form-group">
            <label>Vector Store Name *</label>
            <input type="text" name="vector_store_name" value="${{escapeHtml(domain.vector_store_name || '')}}" required>
          </div>
          <div class="form-group">
            <label>Vector Store ID</label>
            <input type="text" name="vector_store_id" value="${{escapeHtml(domain.vector_store_id || '')}}" placeholder="Optional - leave empty if not needed">
          </div>
          <details class="form-group">
            <summary style="cursor: pointer; font-weight: bold; margin-bottom: 10px;">Advanced: Sources Configuration (Optional)</summary>
            <div class="form-group">
              <label>Sources JSON (file_sources, sitepage_sources, list_sources)</label>
              <button type="button" class="btn-small" onclick="showJsonExampleDialog('edit_sources_json')" style="margin-bottom: 5px;">Show JSON Example</button>
              <textarea id="edit_sources_json" name="sources_json" rows="10">${{escapeHtml(sourcesJsonStr)}}</textarea>
              <small style="color: #666;">Leave empty to clear sources.</small>
            </div>
          </details>
        </form>
      </div>
      <div class="modal-footer">
        <button type="submit" form="update-domain-form" class="btn-primary" data-url="{router_prefix}/{router_name}/update?domain_id=${{domainId}}" data-method="PUT" data-format="json" data-reload-on-finish="true">OK</button>
        <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
      </div>
    `;
  }} catch (e) {{
    body.innerHTML = '<h3>Error</h3><p>' + escapeHtml(e.message) + '</p><div class="form-actions"><button class="btn-secondary" onclick="closeModal()">Close</button></div>';
  }}
}}

function submitUpdateDomainForm(event) {{
  event.preventDefault();
  const form = document.getElementById('update-domain-form');
  const btn = document.querySelector('.modal-footer button[type="submit"]');
  const formData = new FormData(form);
  const data = {{}};
  
  for (const [key, value] of formData.entries()) {{
    if (key === 'domain_id') continue; // Skip domain_id, it's in URL
    if (value !== undefined) {{
      data[key] = value.trim();
    }}
  }}
  
  closeModal();
  callEndpoint(btn, null, data);
}}
"""

# ----------------------------------------- END: Router-specific Form JS -----------------------------------------------------


# ----------------------------------------- START: L(jhu) - Router root / List -----------------------------------------------

@router.get(f"/{router_name}")
async def domains_root(request: Request):
  """Domains Router - CRUD operations for knowledge domains"""
  logger = MiddlewareLogger.create()
  logger.log_function_header("domains_root")
  request_params = dict(request.query_params)
  
  # Bare GET returns self-documentation
  if len(request_params) == 0:
    logger.log_function_footer()
    endpoints = [
      {"path": "", "desc": "List all domains", "formats": ["json", "html", "ui"]},
      {"path": "/get", "desc": "Get single domain", "formats": ["json", "html"]},
      {"path": "/create", "desc": "Create domain (POST)", "formats": []},
      {"path": "/update", "desc": "Update domain (PUT)", "formats": []},
      {"path": "/delete", "desc": "Delete domain (DELETE/GET)", "formats": []}
    ]
    return HTMLResponse(generate_router_docs_page(
      title="Domains",
      description=f"Knowledge domains for crawling and semantic search. Storage: PERSISTENT_STORAGE_PATH/domains/{{domain_id}}/domain.json",
      router_prefix=f"{router_prefix}/{router_name}",
      endpoints=endpoints,
      navigation_html=main_page_nav_html
    ))
  
  format_param = request_params.get("format", "json")
  storage_path = get_persistent_storage_path()
  
  if not storage_path:
    logger.log_function_footer()
    return json_result(False, "PERSISTENT_STORAGE_PATH not configured", [])
  
  domains = load_all_domains(storage_path, logger)
  domains_list = [domain_config_to_dict(d) for d in domains]
  
  if format_param == "json":
    logger.log_function_footer()
    return json_result(True, "", domains_list)
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result("Domains", domains_list, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html}')
  
  if format_param == "ui":
    logger.log_function_footer()
    
    columns = [
      {"field": "domain_id", "header": "Domain ID"},
      {"field": "name", "header": "Name", "default": "-"},
      {"field": "vector_store_name", "header": "Vector Store Name", "default": "-"},
      {"field": "vector_store_id", "header": "Vector Store ID", "default": "-"},
      {
        "field": "actions",
        "header": "Actions",
        "buttons": [
          {"text": "Edit", "onclick": "showUpdateDomainForm('{itemId}')", "class": "btn-small"},
          {
            "text": "Delete",
            "data_url": f"{router_prefix}/{router_name}/delete?domain_id={{itemId}}",
            "data_method": "DELETE",
            "data_format": "json",
            "confirm_message": "Delete domain '{itemId}'?",
            "class": "btn-small btn-delete"
          }
        ]
      }
    ]
    
    toolbar_buttons = [
      {"text": "New Domain", "onclick": "showNewDomainForm()", "class": "btn-primary"}
    ]
    
    html = generate_ui_page(
      title="Domains",
      router_prefix=router_prefix,
      items=domains_list,
      columns=columns,
      row_id_field="domain_id",
      row_id_prefix="domain",
      navigation_html=main_page_nav_html,
      toolbar_buttons=toolbar_buttons,
      enable_selection=False,
      enable_bulk_delete=False,
      console_initially_hidden=True,
      list_endpoint=f"{router_prefix}/{router_name}?format=json",
      delete_endpoint=f"{router_prefix}/{router_name}/delete?domain_id={{itemId}}",
      additional_js=get_router_specific_js()
    )
    return HTMLResponse(html)
  
  logger.log_function_footer()
  return json_result(False, f"Format '{format_param}' not supported. Use: json, html, ui", {})

# ----------------------------------------- END: L(jhu) - Router root / List -------------------------------------------------


# ----------------------------------------- START: G(jh) - Get single --------------------------------------------------------

@router.get(f"/{router_name}/get")
async def domains_get(request: Request):
  """
  Get a single domain by ID.
  
  Parameters:
  - domain_id: ID of the domain (required)
  - format: Response format - json (default), html
  """
  logger = MiddlewareLogger.create()
  logger.log_function_header("domains_get")
  
  if len(request.query_params) == 0:
    logger.log_function_footer()
    doc = textwrap.dedent(domains_get.__doc__).strip()
    return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")
  
  request_params = dict(request.query_params)
  domain_id = request_params.get("domain_id", None)
  format_param = request_params.get("format", "json")
  storage_path = get_persistent_storage_path()
  
  if not domain_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'domain_id' parameter.", {})
  
  if not storage_path:
    logger.log_function_footer()
    return json_result(False, "PERSISTENT_STORAGE_PATH not configured", {})
  
  try:
    domain = load_domain(storage_path, domain_id, logger)
    domain_dict = domain_config_to_dict(domain)
  except FileNotFoundError:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": f"Domain '{domain_id}' not found.", "data": {}}, status_code=404)
  except Exception as e:
    logger.log_function_footer()
    return json_result(False, str(e), {})
  
  if format_param == "json":
    logger.log_function_footer()
    return json_result(True, "", domain_dict)
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Domain: {domain_id}", domain_dict, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html}')
  
  logger.log_function_footer()
  return json_result(False, f"Format '{format_param}' not supported. Use: json, html", {})

# ----------------------------------------- END: G(jh) - Get single ----------------------------------------------------------


# ----------------------------------------- START: C(jh) - Create ------------------------------------------------------------

@router.get(f"/{router_name}/create")
async def domains_create_docs():
  """
  Create a new domain.
  
  Method: POST
  
  Query params:
  - format: Response format - json (default), html
  
  Body (JSON or form data):
  - domain_id: Unique ID for the domain (required)
  - name: Display name (required)
  - description: Description text (required)
  - vector_store_name: Name for the vector store (required)
  - vector_store_id: Existing vector store ID (optional)
  - sources_json: JSON string with file_sources, sitepage_sources, list_sources (optional)
  """
  doc = textwrap.dedent(domains_create_docs.__doc__).strip()
  return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")

@router.post(f"/{router_name}/create")
async def domains_create(request: Request):
  logger = MiddlewareLogger.create()
  logger.log_function_header("domains_create")
  
  query_params = dict(request.query_params)
  format_param = query_params.get("format", "json")
  
  storage_path = get_persistent_storage_path()
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
  is_valid, error_msg = validate_domain_config(body_data)
  if not is_valid:
    logger.log_function_footer()
    return json_result(False, error_msg, {})
  
  domain_id = body_data.get("domain_id", "").strip()
  
  # Check if domain already exists
  try:
    existing = load_domain(storage_path, domain_id)
    if existing:
      logger.log_function_footer()
      return json_result(False, f"Domain '{domain_id}' already exists.", {"domain_id": domain_id})
  except FileNotFoundError:
    pass  # Good, domain doesn't exist
  except Exception as e:
    logger.log_function_footer()
    return json_result(False, f"Error checking domain: {str(e)}", {})
  
  # Parse sources JSON if provided
  file_sources = []
  sitepage_sources = []
  list_sources = []
  
  sources_json = body_data.get("sources_json", "").strip()
  if sources_json:
    try:
      sources_data = json.loads(sources_json)
      file_sources = [FileSource(**src) for src in sources_data.get('file_sources', [])]
      sitepage_sources = [SitePageSource(**src) for src in sources_data.get('sitepage_sources', [])]
      list_sources = [ListSource(**src) for src in sources_data.get('list_sources', [])]
    except json.JSONDecodeError as e:
      logger.log_function_footer()
      return json_result(False, f"Invalid JSON in sources_json: {str(e)}", {})
    except Exception as e:
      logger.log_function_footer()
      return json_result(False, f"Error parsing sources: {str(e)}", {})
  
  # Create domain config
  domain_config = DomainConfig(
    domain_id=domain_id,
    name=body_data.get("name", "").strip(),
    description=body_data.get("description", "").strip(),
    vector_store_name=body_data.get("vector_store_name", "").strip(),
    vector_store_id=body_data.get("vector_store_id", "").strip(),
    file_sources=file_sources,
    sitepage_sources=sitepage_sources,
    list_sources=list_sources
  )
  
  # Save to disk
  save_domain_to_file(storage_path, domain_config, logger)
  
  result = domain_config_to_dict(domain_config)
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Created: {domain_id}", result, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html}')
  
  logger.log_function_footer()
  return json_result(True, "", result)

# ----------------------------------------- END: C(jh) - Create --------------------------------------------------------------


# ----------------------------------------- START: U(jh) - Update ------------------------------------------------------------

@router.get(f"/{router_name}/update")
async def domains_update_docs():
  """
  Update an existing domain.
  
  Method: PUT
  
  Query params:
  - domain_id: ID of the domain to update (required)
  - format: Response format - json (default), html
  
  Body (JSON or form data):
  - name: Display name
  - description: Description text
  - vector_store_name: Name for the vector store
  - vector_store_id: Vector store ID
  - sources_json: JSON string with file_sources, sitepage_sources, list_sources
  """
  doc = textwrap.dedent(domains_update_docs.__doc__).strip()
  return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")

@router.put(f"/{router_name}/update")
async def domains_update(request: Request):
  logger = MiddlewareLogger.create()
  logger.log_function_header("domains_update")
  
  query_params = dict(request.query_params)
  domain_id = query_params.get("domain_id", None)
  format_param = query_params.get("format", "json")
  
  if not domain_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'domain_id' parameter.", {})
  
  storage_path = get_persistent_storage_path()
  if not storage_path:
    logger.log_function_footer()
    return json_result(False, "PERSISTENT_STORAGE_PATH not configured", {})
  
  # Load existing domain
  try:
    existing = load_domain(storage_path, domain_id, logger)
  except FileNotFoundError:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": f"Domain '{domain_id}' not found.", "data": {}}, status_code=404)
  
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
  
  # Update fields if provided
  name = body_data.get("name", "").strip() or existing.name
  description = body_data.get("description", "").strip() or existing.description
  vector_store_name = body_data.get("vector_store_name", "").strip() or existing.vector_store_name
  vector_store_id = body_data.get("vector_store_id", "").strip() if "vector_store_id" in body_data else existing.vector_store_id
  
  # Parse sources JSON if provided
  file_sources = existing.file_sources
  sitepage_sources = existing.sitepage_sources
  list_sources = existing.list_sources
  
  sources_json = body_data.get("sources_json", "").strip()
  if sources_json:
    try:
      sources_data = json.loads(sources_json)
      file_sources = [FileSource(**src) for src in sources_data.get('file_sources', [])]
      sitepage_sources = [SitePageSource(**src) for src in sources_data.get('sitepage_sources', [])]
      list_sources = [ListSource(**src) for src in sources_data.get('list_sources', [])]
    except json.JSONDecodeError as e:
      logger.log_function_footer()
      return json_result(False, f"Invalid JSON in sources_json: {str(e)}", {})
    except Exception as e:
      logger.log_function_footer()
      return json_result(False, f"Error parsing sources: {str(e)}", {})
  elif "sources_json" in body_data:
    # Empty sources_json provided - clear sources
    file_sources = []
    sitepage_sources = []
    list_sources = []
  
  # Create updated domain config
  domain_config = DomainConfig(
    domain_id=domain_id,
    name=name,
    description=description,
    vector_store_name=vector_store_name,
    vector_store_id=vector_store_id,
    file_sources=file_sources,
    sitepage_sources=sitepage_sources,
    list_sources=list_sources
  )
  
  # Save to disk
  save_domain_to_file(storage_path, domain_config, logger)
  
  result = domain_config_to_dict(domain_config)
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Updated: {domain_id}", result, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html}')
  
  logger.log_function_footer()
  return json_result(True, "", result)

# ----------------------------------------- END: U(jh) - Update --------------------------------------------------------------


# ----------------------------------------- START: D(jh) - Delete ------------------------------------------------------------

@router.get(f"/{router_name}/delete")
async def domains_delete_get(request: Request):
  """Allow DELETE via GET for browser/testing convenience"""
  return await domains_delete(request)

@router.delete(f"/{router_name}/delete")
async def domains_delete(request: Request):
  logger = MiddlewareLogger.create()
  logger.log_function_header("domains_delete")
  
  query_params = dict(request.query_params)
  domain_id = query_params.get("domain_id", None)
  format_param = query_params.get("format", "json")
  
  if not domain_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'domain_id' parameter.", {})
  
  storage_path = get_persistent_storage_path()
  if not storage_path:
    logger.log_function_footer()
    return json_result(False, "PERSISTENT_STORAGE_PATH not configured", {})
  
  # Verify domain exists
  try:
    load_domain(storage_path, domain_id, logger)
  except FileNotFoundError:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": f"Domain '{domain_id}' not found.", "data": {}}, status_code=404)
  
  # Delete domain
  try:
    delete_domain_folder(storage_path, domain_id, logger)
  except Exception as e:
    logger.log_function_footer()
    return json_result(False, f"Error deleting domain: {str(e)}", {})
  
  result = {"domain_id": domain_id, "deleted": True}
  
  if format_param == "html":
    logger.log_function_footer()
    return html_result(f"Deleted: {domain_id}", result, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html}')
  
  logger.log_function_footer()
  return json_result(True, "", result)

# ----------------------------------------- END: D(jh) - Delete --------------------------------------------------------------
