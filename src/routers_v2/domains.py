# Domains Router V2 - CRUD operations for knowledge domains
# Spec: L(jhu)C(jhs)G(jh)U(jhs)D(jhs): /v2/domains
# Uses common_ui_functions_v2.py and common_crawler_functions_v2.py

import json, os, textwrap, uuid
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, StreamingResponse

from routers_v2.common_ui_functions_v2 import generate_ui_page, generate_router_docs_page, generate_endpoint_docs, json_result, html_result
from routers_v2.common_logging_functions_v2 import MiddlewareLogger, UNKNOWN
from routers_v2.common_job_functions_v2 import StreamingJobWriter
from routers_v2.common_crawler_functions_v2 import (
  DomainConfig, FileSource, SitePageSource, ListSource,
  load_domain, load_all_domains, save_domain_to_file, delete_domain_folder, rename_domain,
  validate_domain_config, domain_config_to_dict
)

router = APIRouter()
config = None
router_prefix = None
router_name = "domains"
main_page_nav_html = '<a href="/">Back to Main Page</a> | <a href="{router_prefix}/domains?format=ui">Domains</a> | <a href="{router_prefix}/crawler?format=ui">Crawler</a> | <a href="{router_prefix}/jobs?format=ui">Jobs</a> | <a href="{router_prefix}/reports?format=ui">Reports</a>'
example_domain_json = """
{
  "domain_id": "example_domain",
  "name": "Example Domain",
  "description": "Example description",
  "vector_store_name": "example_vs",
  "vector_store_id": "",
  "file_sources": [],
  "sitepage_sources": [],
  "list_sources": []
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


# ----------------------------------------- START: Router-specific Form JS ---------------------------------------------------

def get_router_specific_js() -> str:
  """Router-specific JavaScript for domain forms."""
  return f"""
// ============================================
// ROUTER-SPECIFIC FORMS - DOMAINS
// ============================================

const DOMAIN_MODAL_WIDTH = '900px';

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
      <p class="modal-error"></p>
      <button type="submit" form="new-domain-form" class="btn-primary" data-url="{router_prefix}/{router_name}/create" data-method="POST" data-format="json" data-reload-on-finish="true" data-close-on-success="true">OK</button>
      <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
    </div>
  `;
  openModal(DOMAIN_MODAL_WIDTH);
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
  
  clearModalError();
  callEndpoint(btn, null, data);
}}

async function showEditDomainForm(domainId) {{
  const body = document.querySelector('#modal .modal-body');
  body.innerHTML = '<h3>Loading...</h3>';
  openModal(DOMAIN_MODAL_WIDTH);
  
  try {{
    const response = await fetch(`{router_prefix}/{router_name}/get?domain_id=${{domainId}}&format=json`);
    const result = await response.json();
    if (!result.ok) {{
      body.innerHTML = '<div class="modal-header"><h3>Error</h3></div><div class="modal-scroll"><p>' + escapeHtml(result.error) + '</p></div><div class="modal-footer"><button class="btn-secondary" onclick="closeModal()">Close</button></div>';
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
        <form id="edit-domain-form" onsubmit="return submitEditDomainForm(event)">
          <input type="hidden" name="source_domain_id" value="${{escapeHtml(domainId)}}">
          <div class="form-group">
            <label>Domain ID</label>
            <input type="text" name="domain_id" value="${{escapeHtml(domainId)}}">
            <small style="color: #666;">Change to rename the domain</small>
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
        <p class="modal-error"></p>
        <button type="submit" form="edit-domain-form" class="btn-primary" data-url="{router_prefix}/{router_name}/update?domain_id=${{domainId}}" data-method="PUT" data-format="json" data-reload-on-finish="true" data-close-on-success="true">OK</button>
        <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
      </div>
    `;
  }} catch (e) {{
    body.innerHTML = '<div class="modal-header"><h3>Error</h3></div><div class="modal-scroll"><p>' + escapeHtml(e.message) + '</p></div><div class="modal-footer"><button class="btn-secondary" onclick="closeModal()">Close</button></div>';
  }}
}}

function submitEditDomainForm(event) {{
  event.preventDefault();
  const form = document.getElementById('edit-domain-form');
  const btn = document.querySelector('.modal-footer button[type="submit"]');
  const formData = new FormData(form);
  const data = {{}};
  
  const sourceDomainId = formData.get('source_domain_id');
  const targetDomainId = formData.get('domain_id');
  
  // Validate Domain ID not empty
  const domainIdInput = form.querySelector('input[name="domain_id"]');
  if (!targetDomainId || !targetDomainId.trim()) {{
    showFieldError(domainIdInput, 'Domain ID cannot be empty');
    return;
  }}
  clearFieldError(domainIdInput);
  
  // Build data object
  for (const [key, value] of formData.entries()) {{
    if (key === 'source_domain_id') continue;
    if (key === 'domain_id') {{
      // Only include if changed (triggers rename per DD-E014)
      if (value && value.trim() !== sourceDomainId) {{
        data.domain_id = value.trim();
      }}
    }} else if (value !== undefined) {{
      data[key] = value.trim();
    }}
  }}
  
  clearModalError();
  callEndpoint(btn, sourceDomainId, data);
}}

// ============================================
// CRAWL DOMAIN FORM
// ============================================

const domainsState = new Map();

document.addEventListener('DOMContentLoaded', async () => {{
  await cacheDomains();
}});

async function cacheDomains() {{
  try {{
    const response = await fetch('{router_prefix}/{router_name}?format=json');
    const result = await response.json();
    if (result.ok) {{
      domainsState.clear();
      result.data.forEach(d => domainsState.set(d.domain_id, d));
    }}
  }} catch (e) {{
    console.error('Failed to cache domains:', e);
  }}
}}

function showCrawlDomainForm(domainId) {{
  const domain = domainsState.get(domainId);
  if (!domain) {{
    showToast('Error', 'Domain not found in cache. Please reload the page.', 'error');
    return;
  }}
  
  const domainOptions = Array.from(domainsState.values())
    .map(d => `<option value="${{escapeHtml(d.domain_id)}}" ${{d.domain_id === domainId ? 'selected' : ''}}>${{escapeHtml(d.domain_id)}} - ${{escapeHtml(d.name || '')}}</option>`)
    .join('');
  
  const body = document.querySelector('#modal .modal-body');
  body.innerHTML = `
    <div class="modal-header"><h3>Crawl Domain</h3></div>
    <div class="modal-scroll">
      <form id="crawl-domain-form" onsubmit="return startCrawl(event)">
        <div class="form-group">
          <label>Domain *</label>
          <select name="domain_id" onchange="onCrawlDomainChange()" required>
            ${{domainOptions}}
          </select>
        </div>
        
        <div class="form-group">
          <label>Step *</label>
          <div style="display: flex; flex-direction: column; gap: 4px;">
            <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;"><input type="radio" name="step" value="crawl" checked onchange="updateCrawlEndpointPreview()" style="width: auto; margin-right: 0.5rem;"> Full Crawl (download + process + embed)</label>
            <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;"><input type="radio" name="step" value="download_data" onchange="updateCrawlEndpointPreview()" style="width: auto; margin-right: 0.5rem;"> Download Data Only</label>
            <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;"><input type="radio" name="step" value="process_data" onchange="updateCrawlEndpointPreview()" style="width: auto; margin-right: 0.5rem;"> Process Data Only</label>
            <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;"><input type="radio" name="step" value="embed_data" onchange="updateCrawlEndpointPreview()" style="width: auto; margin-right: 0.5rem;"> Embed Data Only</label>
          </div>
        </div>
        
        <div class="form-group">
          <label>Mode *</label>
          <div style="display: flex; flex-direction: column; gap: 4px;">
            <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;"><input type="radio" name="mode" value="full" onchange="updateCrawlEndpointPreview()" style="width: auto; margin-right: 0.5rem;"> Full - Clear existing data first</label>
            <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;"><input type="radio" name="mode" value="incremental" checked onchange="updateCrawlEndpointPreview()" style="width: auto; margin-right: 0.5rem;"> Incremental - Only process changes</label>
          </div>
        </div>
        
        <div class="form-group">
          <label>Scope *</label>
          <div style="display: flex; flex-direction: column; gap: 4px;">
            <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;"><input type="radio" name="scope" value="all" checked onchange="onScopeChange()" style="width: auto; margin-right: 0.5rem;"> All Sources</label>
            <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;"><input type="radio" name="scope" value="files" onchange="onScopeChange()" style="width: auto; margin-right: 0.5rem;"> Files Only</label>
            <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;"><input type="radio" name="scope" value="lists" onchange="onScopeChange()" style="width: auto; margin-right: 0.5rem;"> Lists Only</label>
            <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;"><input type="radio" name="scope" value="sitepages" onchange="onScopeChange()" style="width: auto; margin-right: 0.5rem;"> Site Pages Only</label>
          </div>
        </div>
        
        <div class="form-group">
          <label>Source ID (optional)</label>
          <select name="source_id" id="crawl-source-id" disabled onchange="updateCrawlEndpointPreview()">
            <option value="">(empty - no filter)</option>
          </select>
          <small style="color: #666;">Enabled when scope is not "All Sources"</small>
        </div>
        
        <div class="form-group">
          <label><input type="checkbox" name="dry_run" onchange="updateCrawlEndpointPreview()"> Run test without making changes (dry run)</label>
        </div>
        
        <div class="form-group">
          <label>Endpoint Preview:</label>
          <pre id="crawl-endpoint-preview" style="background: #f5f5f5; padding: 8px; border-radius: 4px; overflow-x: auto; font-size: 12px;">/v2/crawler/crawl?domain_id=${{escapeHtml(domainId)}}&mode=incremental&scope=all&format=stream</pre>
        </div>
      </form>
    </div>
    <div class="modal-footer">
      <p class="modal-error"></p>
      <button type="submit" form="crawl-domain-form" class="btn-primary">OK</button>
      <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
    </div>
  `;
  openModal('700px');
  updateCrawlEndpointPreview();
}}

function onCrawlDomainChange() {{
  updateSourceIdDropdown();
  updateCrawlEndpointPreview();
}}

function onScopeChange() {{
  const form = document.getElementById('crawl-domain-form');
  const scope = form.querySelector('[name="scope"]:checked').value;
  const sourceIdSelect = document.getElementById('crawl-source-id');
  
  if (scope === 'all') {{
    sourceIdSelect.disabled = true;
    sourceIdSelect.value = '';
  }} else {{
    sourceIdSelect.disabled = false;
    updateSourceIdDropdown();
  }}
  updateCrawlEndpointPreview();
}}

function updateSourceIdDropdown() {{
  const form = document.getElementById('crawl-domain-form');
  const domainId = form.querySelector('[name="domain_id"]').value;
  const scope = form.querySelector('[name="scope"]:checked').value;
  const sourceIdSelect = document.getElementById('crawl-source-id');
  
  const domain = domainsState.get(domainId);
  if (!domain) return;
  
  let sources = [];
  if (scope === 'files') sources = domain.file_sources || [];
  else if (scope === 'lists') sources = domain.list_sources || [];
  else if (scope === 'sitepages') sources = domain.sitepage_sources || [];
  
  sourceIdSelect.innerHTML = '<option value="">(empty - no filter)</option>' +
    sources.map(s => `<option value="${{escapeHtml(s.source_id)}}">${{escapeHtml(s.source_id)}}</option>`).join('');
}}

function updateCrawlEndpointPreview() {{
  const form = document.getElementById('crawl-domain-form');
  if (!form) return;
  
  const domainId = form.querySelector('[name="domain_id"]').value;
  const step = form.querySelector('[name="step"]:checked').value;
  const mode = form.querySelector('[name="mode"]:checked').value;
  const scope = form.querySelector('[name="scope"]:checked').value;
  const sourceId = form.querySelector('[name="source_id"]').value.trim();
  const dryRun = form.querySelector('[name="dry_run"]').checked;
  
  let url = `/v2/crawler/${{step}}?domain_id=${{domainId}}&mode=${{mode}}&scope=${{scope}}`;
  if (scope !== 'all' && sourceId) url += `&source_id=${{sourceId}}`;
  if (dryRun) url += '&dry_run=true';
  url += '&format=stream';
  
  document.getElementById('crawl-endpoint-preview').textContent = url;
}}

function startCrawl(event) {{
  event.preventDefault();
  const form = document.getElementById('crawl-domain-form');
  const domainId = form.querySelector('[name="domain_id"]').value;
  const step = form.querySelector('[name="step"]:checked').value;
  const mode = form.querySelector('[name="mode"]:checked').value;
  const scope = form.querySelector('[name="scope"]:checked').value;
  const sourceId = form.querySelector('[name="source_id"]').value.trim();
  const dryRun = form.querySelector('[name="dry_run"]').checked;
  
  let url = `/v2/crawler/${{step}}?domain_id=${{domainId}}&mode=${{mode}}&scope=${{scope}}`;
  if (scope !== 'all' && sourceId) url += `&source_id=${{sourceId}}`;
  if (dryRun) url += '&dry_run=true';
  url += '&format=stream';
  
  closeModal();
  showConsole();
  clearConsole();
  connectStream(url, {{ reloadOnFinish: false, showResult: 'toast', clearConsole: false }});
  showToast('Crawl Started', domainId, 'info');
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
      {"path": "/delete", "desc": "Delete domain (DELETE/GET)", "formats": []},
      {"path": "/selftest", "desc": "Self-test", "formats": ["stream"]}
    ]
    return HTMLResponse(generate_router_docs_page(
      title="Domains",
      description=f"Knowledge domains for crawling and semantic search. Storage: PERSISTENT_STORAGE_PATH/domains/{{domain_id}}/domain.json",
      router_prefix=f"{router_prefix}/{router_name}",
      endpoints=endpoints,
      navigation_html=main_page_nav_html.replace("{router_prefix}", router_prefix)
    ))
  
  format_param = request_params.get("format", "json")
  storage_path = get_persistent_storage_path(request)
  
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
    return html_result("Domains", domains_list, f'<a href="{router_prefix}/{router_name}">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
  
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
          {"text": "Crawl", "onclick": "showCrawlDomainForm('{itemId}')", "class": "btn-small"},
          {"text": "Edit", "onclick": "showEditDomainForm('{itemId}')", "class": "btn-small"},
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
      {"text": "New Domain", "onclick": "showNewDomainForm()", "class": "btn-primary"},
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
      title="Domains",
      router_prefix=router_prefix,
      items=domains_list,
      columns=columns,
      row_id_field="domain_id",
      row_id_prefix="domain",
      navigation_html=main_page_nav_html.replace("{router_prefix}", router_prefix),
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
  storage_path = get_persistent_storage_path(request)
  
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
    return html_result(f"Domain: {domain_id}", domain_dict, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
  
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
    return html_result(f"Created: {domain_id}", result, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
  
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
  
  storage_path = get_persistent_storage_path(request)
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
  
  # Rename detection (per DD-E014)
  source_domain_id = domain_id
  target_domain_id = body_data.get("domain_id", None)
  rename_requested = target_domain_id and target_domain_id != source_domain_id
  
  # Handle rename if requested
  if rename_requested:
    success, error_msg = rename_domain(storage_path, source_domain_id, target_domain_id)
    if not success:
      logger.log_function_footer()
      return JSONResponse({"ok": False, "error": error_msg, "data": {}}, status_code=400)
    domain_id = target_domain_id
  
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
    return html_result(f"Updated: {domain_id}", result, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
  
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
  
  storage_path = get_persistent_storage_path(request)
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
    return html_result(f"Deleted: {domain_id}", result, f'<a href="{router_prefix}/{router_name}?format=ui">Back</a> | {main_page_nav_html.replace("{router_prefix}", router_prefix)}')
  
  logger.log_function_footer()
  return json_result(True, "", result)

# ----------------------------------------- END: D(jh) - Delete --------------------------------------------------------------


# ----------------------------------------- START: Selftest ------------------------------------------------------------------

@router.get(f"/{router_name}/selftest")
async def domains_selftest(request: Request):
  """
  Self-test for domains CRUD operations.
  
  Only supports format=stream.
  
  Tests:
  1. Error cases (missing params, non-existent domains)
  2. Create domain
  3. Create with sources
  4. Update domain
  5. Rename domain (ID change)
  6. Delete domain
  
  Example:
  GET {router_prefix}/{router_name}/selftest?format=stream

  Example domain:
  {example_domain_json}

  Result (end_json event):
  {
    "ok": true,
    "error": "",
    "data": {
      "passed": 29,
      "failed": 0,
      "passed_tests": ["Test 1 description", ...],
      "failed_tests": []
    }
  }
  """
  request_params = dict(request.query_params)
  
  if len(request_params) == 0:
    doc = textwrap.dedent(domains_selftest.__doc__).replace("{router_prefix}", router_prefix).replace("{router_name}", router_name).replace("{example_domain_json}", example_domain_json.strip())
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
  stream_logger.log_function_header("domains_selftest")
  
  test_id = f"selftest_{uuid.uuid4().hex[:8]}"
  sources_test_id = f"selftest_src_{uuid.uuid4().hex[:8]}"
  renamed_test_id = f"{test_id}_renamed"
  
  test_domain_v1 = {"domain_id": test_id, "name": "Test Domain", "description": "Selftest domain", "vector_store_name": "test_vs"}
  test_domain_v2 = {"name": "Updated Domain", "description": "Updated description", "vector_store_name": "updated_vs"}
  test_sources_json = json.dumps({"file_sources": [{"source_id": "src1", "site_url": "https://test.sharepoint.com", "sharepoint_url_part": "/Docs", "filter": ""}], "sitepage_sources": [], "list_sources": []})
  
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
        get_url = f"{base_url}{router_prefix}/{router_name}/get?domain_id={test_id}&format=json"
        list_url = f"{base_url}{router_prefix}/{router_name}?format=json"
        delete_url = f"{base_url}{router_prefix}/{router_name}/delete?domain_id={test_id}"
        
        # ===== ERROR CASES =====
        sse = next_test("Error cases...")
        if sse: yield sse
        
        # Test 1: POST /create without body
        r = await client.post(create_url)
        sse = check(r.json().get("ok") == False, "POST /create without body - returns error (ok=false)", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        # Test 2: POST /create with empty required fields
        r = await client.post(create_url, json={"domain_id": "", "name": "", "description": "", "vector_store_name": ""})
        sse = check(r.json().get("ok") == False, "POST /create empty fields - returns validation error (ok=false)", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        # Test 3: PUT /update without domain_id param
        r = await client.put(f"{base_url}{router_prefix}/{router_name}/update")
        sse = check(r.json().get("ok") == False, "PUT /update without domain_id - returns error (ok=false)", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        # Test 4: PUT /update with non-existent domain_id
        r = await client.put(f"{base_url}{router_prefix}/{router_name}/update?domain_id=nonexistent_domain_xyz")
        sse = check(r.status_code == 404, "PUT /update non-existent - returns 404", f"Expected 404, got: {r.status_code}")
        if sse: yield sse
        
        # Test 5: GET /get without domain_id
        r = await client.get(f"{base_url}{router_prefix}/{router_name}/get?format=json")
        sse = check(r.json().get("ok") == False, "GET /get without domain_id - returns error (ok=false)", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        # Test 6: GET /get with non-existent domain_id
        r = await client.get(f"{base_url}{router_prefix}/{router_name}/get?domain_id=nonexistent_domain_xyz&format=json")
        sse = check(r.status_code == 404, "GET /get non-existent - returns 404", f"Expected 404, got: {r.status_code}")
        if sse: yield sse
        
        # Test 7: DELETE without domain_id
        r = await client.delete(f"{base_url}{router_prefix}/{router_name}/delete")
        sse = check(r.json().get("ok") == False, "DELETE without domain_id - returns error (ok=false)", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        # Test 8: DELETE non-existent domain
        r = await client.delete(f"{base_url}{router_prefix}/{router_name}/delete?domain_id=nonexistent_domain_xyz")
        sse = check(r.status_code == 404, "DELETE non-existent - returns 404", f"Expected 404, got: {r.status_code}")
        if sse: yield sse
        
        # ===== CREATE TESTS =====
        sse = next_test(f"POST /create - Creating '{test_id}'...")
        if sse: yield sse
        
        # Test 9: POST /create with valid data
        r = await client.post(create_url, json=test_domain_v1)
        result = r.json()
        sse = check(r.status_code == 200 and result.get("ok") == True, "POST /create - call succeeded (HTTP 200, ok=true)", f"status={r.status_code}, response={result}")
        if sse: yield sse
        
        # Test 10: GET /get - verify created data
        sse = next_test("GET /get - Verifying created domain...")
        if sse: yield sse
        
        r = await client.get(get_url)
        result = r.json()
        domain_data = result.get("data", {})
        match = (r.status_code == 200 and domain_data.get("name") == test_domain_v1["name"] and domain_data.get("description") == test_domain_v1["description"])
        sse = check(match, f"GET /get - domain retrieved with correct data (name='{domain_data.get('name')}')", f"status={r.status_code}, data={domain_data}")
        if sse: yield sse
        
        # Test 11: POST /create with same domain_id
        sse = next_test("POST /create duplicate...")
        if sse: yield sse
        
        r = await client.post(create_url, json=test_domain_v1)
        sse = check(r.json().get("ok") == False and "already exists" in r.json().get("error", ""), "POST /create duplicate - returns 'already exists' error", f"Expected 'already exists' error, got: {r.json()}")
        if sse: yield sse
        
        # Test 12: GET / - domain in list
        sse = next_test("GET / - Listing all domains...")
        if sse: yield sse
        
        r = await client.get(list_url)
        list_result = r.json()
        domains = list_result.get("data", [])
        domain_ids = [d.get("domain_id") for d in domains]
        sse = check(test_id in domain_ids, f"GET / - domain found in list ({len(domains)} total)", "Domain NOT found in list")
        if sse: yield sse
        
        # ===== CREATE WITH SOURCES =====
        sse = next_test(f"POST /create with sources - Creating '{sources_test_id}'...")
        if sse: yield sse
        
        # Test 13: POST /create with sources_json
        sources_domain = {"domain_id": sources_test_id, "name": "Sources Test", "description": "Test with sources", "vector_store_name": "sources_vs", "sources_json": test_sources_json}
        r = await client.post(create_url, json=sources_domain)
        sse = check(r.json().get("ok") == True, "POST /create with sources - call succeeded (ok=true)", f"Failed: {r.json()}")
        if sse: yield sse
        
        # Test 14: GET /get - verify sources parsed
        sse = next_test("GET /get - Verifying sources...")
        if sse: yield sse
        
        r = await client.get(f"{base_url}{router_prefix}/{router_name}/get?domain_id={sources_test_id}&format=json")
        sources_data = r.json().get("data", {})
        file_sources = sources_data.get("file_sources", [])
        sse = check(len(file_sources) == 1, f"GET /get - sources parsed correctly (file_sources.length={len(file_sources)})", f"Expected 1 file_source, got: {file_sources}")
        if sse: yield sse
        
        # Test 15: POST /create with invalid sources_json
        sse = next_test("POST /create with invalid sources_json...")
        if sse: yield sse
        
        invalid_sources_domain = {"domain_id": f"invalid_{uuid.uuid4().hex[:8]}", "name": "Invalid", "description": "Invalid sources", "vector_store_name": "invalid_vs", "sources_json": "not valid json"}
        r = await client.post(create_url, json=invalid_sources_domain)
        sse = check(r.json().get("ok") == False, "POST /create invalid sources - returns error (ok=false)", f"Expected error, got: {r.json()}")
        if sse: yield sse
        
        # ===== UPDATE TESTS =====
        sse = next_test("PUT /update - Updating domain...")
        if sse: yield sse
        
        # Test 16: PUT /update with new name
        r = await client.put(f"{update_url}?domain_id={test_id}", json=test_domain_v2)
        sse = check(r.json().get("ok") == True, "PUT /update - call succeeded (ok=true)", f"Failed: {r.json().get('error')}")
        if sse: yield sse
        
        # Test 17: GET /get - verify name changed
        sse = next_test("GET /get - Verifying update...")
        if sse: yield sse
        
        r = await client.get(get_url)
        updated = r.json().get("data", {})
        sse = check(updated.get("name") == test_domain_v2["name"], f"PUT /update - domain modified (name='{updated.get('name')}')", f"Mismatch: {updated}")
        if sse: yield sse
        
        # Test 18: PUT /update with sources_json
        sse = next_test("PUT /update with sources...")
        if sse: yield sse
        
        r = await client.put(f"{update_url}?domain_id={test_id}", json={"sources_json": test_sources_json})
        sse = check(r.json().get("ok") == True, "PUT /update with sources - call succeeded (ok=true)", f"Failed: {r.json()}")
        if sse: yield sse
        
        # Test 19: GET /get - verify sources updated
        r = await client.get(get_url)
        updated_sources = r.json().get("data", {}).get("file_sources", [])
        sse = check(len(updated_sources) == 1, f"PUT /update - sources updated (file_sources.length={len(updated_sources)})", f"Expected 1, got: {updated_sources}")
        if sse: yield sse
        
        # ===== RENAME TESTS =====
        sse = next_test(f"PUT /update with domain_id (rename) '{test_id}' -> '{renamed_test_id}'...")
        if sse: yield sse
        
        # Test 20: PUT /update with domain_id in body (rename)
        r = await client.put(f"{update_url}?domain_id={test_id}", json={"domain_id": renamed_test_id})
        sse = check(r.json().get("ok") == True, "PUT /update rename - call succeeded (ok=true)", f"Failed: {r.json()}")
        if sse: yield sse
        
        # Test 21: GET /get with old domain_id - should be 404
        sse = next_test("GET /get old ID - Verifying rename...")
        if sse: yield sse
        
        r = await client.get(get_url)
        sse = check(r.status_code == 404, "GET /get old ID - returns 404 (renamed away)", f"Expected 404, got: {r.status_code}")
        if sse: yield sse
        
        # Test 22: GET /get with new domain_id - should work
        r = await client.get(f"{base_url}{router_prefix}/{router_name}/get?domain_id={renamed_test_id}&format=json")
        sse = check(r.status_code == 200 and r.json().get("ok") == True, "GET /get new ID - returns 200 (domain found)", f"Expected 200, got: {r.status_code}, {r.json()}")
        if sse: yield sse
        
        # Test 23: PUT /update rename to existing domain_id
        sse = next_test("PUT /update rename to existing ID...")
        if sse: yield sse
        
        r = await client.put(f"{update_url}?domain_id={renamed_test_id}", json={"domain_id": sources_test_id})
        sse = check(r.status_code == 400 and "already exists" in r.json().get("error", ""), "PUT /update rename to existing - returns 400 'already exists'", f"Expected 400 with 'already exists', got: {r.status_code}, {r.json()}")
        if sse: yield sse
        
        # Test 24: PUT /update rename to invalid format
        sse = next_test("PUT /update rename to invalid format...")
        if sse: yield sse
        
        r = await client.put(f"{update_url}?domain_id={renamed_test_id}", json={"domain_id": "invalid id with spaces!"})
        sse = check(r.status_code == 400 and "Invalid domain ID format" in r.json().get("error", ""), "PUT /update rename invalid format - returns 400 'Invalid domain ID format'", f"Expected 400 with format error, got: {r.status_code}, {r.json()}")
        if sse: yield sse
        
        # Test 25: GET / - verify renamed domain in list
        sse = next_test("GET / - Verifying list after rename...")
        if sse: yield sse
        
        r = await client.get(list_url)
        domains_after_rename = r.json().get("data", [])
        domain_ids_after = [d.get("domain_id") for d in domains_after_rename]
        renamed_in_list = renamed_test_id in domain_ids_after
        old_not_in_list = test_id not in domain_ids_after
        sse = check(renamed_in_list and old_not_in_list, f"GET / - renamed domain in list, old ID removed", f"renamed_in_list={renamed_in_list}, old_not_in_list={old_not_in_list}")
        if sse: yield sse
        
        # ===== DELETE TESTS =====
        sse = next_test(f"DELETE /delete '{renamed_test_id}'...")
        if sse: yield sse
        
        # Test 26: DELETE /delete
        r = await client.delete(f"{base_url}{router_prefix}/{router_name}/delete?domain_id={renamed_test_id}")
        sse = check(r.json().get("ok") == True, "DELETE /delete - call succeeded (ok=true)", f"Failed: {r.json().get('error')}")
        if sse: yield sse
        
        # Test 27: GET /get - should be 404
        sse = next_test("Verifying deletion...")
        if sse: yield sse
        
        r = await client.get(f"{base_url}{router_prefix}/{router_name}/get?domain_id={renamed_test_id}&format=json")
        sse = check(r.status_code == 404, "DELETE /delete - domain deleted (GET returns 404)", f"Got: {r.status_code}")
        if sse: yield sse
        
        # Test 28: GET / - domain not in list
        r = await client.get(list_url)
        domains_after_delete = r.json().get("data", [])
        domain_ids_final = [d.get("domain_id") for d in domains_after_delete]
        sse = check(renamed_test_id not in domain_ids_final, "DELETE /delete - domain removed from list", "Domain still in list!")
        if sse: yield sse
        
        # Test 29: DELETE same domain again - should be 404
        sse = next_test("DELETE same domain again...")
        if sse: yield sse
        
        r = await client.delete(f"{base_url}{router_prefix}/{router_name}/delete?domain_id={renamed_test_id}")
        sse = check(r.status_code == 404, "DELETE again - returns 404 (already deleted)", f"Expected 404, got: {r.status_code}")
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
          await cleanup_client.delete(f"{base_url}{router_prefix}/{router_name}/delete?domain_id={test_id}")
          await cleanup_client.delete(f"{base_url}{router_prefix}/{router_name}/delete?domain_id={renamed_test_id}")
          await cleanup_client.delete(f"{base_url}{router_prefix}/{router_name}/delete?domain_id={sources_test_id}")
      except: pass
      writer.finalize()
  
  return StreamingResponse(run_selftest(), media_type="text/event-stream")

# ----------------------------------------- END: Selftest --------------------------------------------------------------------
