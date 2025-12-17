# CRUD endpoints for domain management
import json
from dataclasses import asdict
from typing import Any, Dict

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse

from hardcoded_config import CRAWLER_HARDCODED_CONFIG
from routers_v1.common_ui_functions_v1 import generate_html_head, generate_table_page, generate_table_with_headers, generate_error_html, generate_error_response, generate_success_response, generate_toolbar_button, generate_nested_data_page, generate_documentation_page
from common_utils import convert_to_flat_html_table, convert_to_nested_html_table
from routers_v1.common_logging_functions_v1 import log_function_footer, log_function_header, log_function_output
from routers_v1.router_crawler_functions import ( DomainConfig, FileSource, SitePageSource, ListSource, load_all_domains, domain_config_to_dict, save_domain_to_file, delete_domain_folder, validate_domain_config )

router = APIRouter()

# Configuration will be injected from app.py
config = None
router_prefix = ""

def set_config(app_config, prefix: str = ""):
  """Set the configuration for Domain management."""
  global config, router_prefix
  config = app_config
  router_prefix = prefix


@router.get('/domains')
async def list_domains(request: Request):
  """
  Endpoint to retrieve all domain configurations from the domains folder.
  
  Parameters:
  - format: The response format (json, html, or ui)
    
  Examples:
  /v1/domains
  /v1/domains?format=json
  /v1/domains?format=html
  /v1/domains?format=ui
  """
  function_name = 'list_domains()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  # Display documentation if no params are provided
  if len(request_params) == 0:
    await log_function_footer(request_data)
    return HTMLResponse(generate_documentation_page(f'{router_prefix}/domains', list_domains.__doc__))

  format = request_params.get('format', 'html')
  
  try:
    if not hasattr(request.app.state, 'system_info') or not request.app.state.system_info or not request.app.state.system_info.PERSISTENT_STORAGE_PATH:
      error_message = "PERSISTENT_STORAGE_PATH not configured or is empty"
      log_function_output(request_data, f"ERROR: {error_message}")
      await log_function_footer(request_data)
      if format == 'json':
        return JSONResponse({"error": error_message}, status_code=500)
      else:
        return HTMLResponse(generate_error_html(error_message), status_code=500)
    
    storage_path = request.app.state.system_info.PERSISTENT_STORAGE_PATH
    
    # Load all domains using the new function
    domains_list = load_all_domains(storage_path, request_data)
    
    if format == 'json':
      # Convert dataclasses to dictionaries for JSON response
      domains_dict_list = [domain_config_to_dict(domain) for domain in domains_list]
      await log_function_footer(request_data)
      return JSONResponse({"data": domains_dict_list, "count": len(domains_dict_list)})
    elif format == 'ui':
      # Create UI-friendly list with action buttons
      table_rows = ""
      for domain in domains_list:
        table_rows += f"""
    <tr id="domain-{domain.domain_id}">
      <td>{domain.domain_id}</td>
      <td>{domain.name}</td>
      <td>{domain.vector_store_name}</td>
      <td>{domain.vector_store_id}</td>
      <td class="actions">
      <button class="btn-small btn-edit" 
          hx-get="{router_prefix}/domains/update?domain_id={domain.domain_id}&format=ui"
          hx-target="#form-container"
          hx-swap="innerHTML">
        Edit
      </button>
      <button class="btn-small btn-delete" 
          hx-delete="{router_prefix}/domains/delete?domain_id={domain.domain_id}&format=html"
          hx-confirm="Are you sure you want to delete domain '{domain.name}'?"
          hx-target="#domain-{domain.domain_id}"
          hx-swap="outerHTML">
        Delete
      </button>
      <a href="/query2?vsid={domain.vector_store_id}&query=List all files&results=50">
        Query
      </a>
      </td>
    </tr>
    """
      
      # JavaScript for domain validation and JSON example dialog
      additional_scripts = f"""  // Store existing domain IDs for client-side validation
  const existingDomainIds = {json.dumps([d.domain_id for d in domains_list])};
  
  function validateDomainId(domainIdInput) {{
    const domainId = domainIdInput.value.trim();
    const errorDiv = document.getElementById('domain-id-error');
    
    if (existingDomainIds.includes(domainId)) {{
      if (!errorDiv) {{
        const error = document.createElement('div');
        error.id = 'domain-id-error';
        error.style.cssText = 'color: #c00; font-size: 0.9em; margin-top: 5px;';
        error.textContent = `Domain ID '${{domainId}}' already exists. Please choose a different ID.`;
        domainIdInput.parentElement.appendChild(error);
      }}
      domainIdInput.setCustomValidity('Domain ID already exists');
      return false;
    }} else {{
      if (errorDiv) {{
        errorDiv.remove();
      }}
      domainIdInput.setCustomValidity('');
      return true;
    }}
  }}
  
  function showJsonExampleDialog(targetTextareaId) {{
    const demoJson = {{
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
    
    const formatted = JSON.stringify(demoJson, null, 2);
    
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
      <div class="modal-content" style="max-width: 700px;">
        <h3>JSON Example</h3>
        <p>Copy this example and modify it for your needs:</p>
        <textarea readonly rows="20" style="width: 100%; font-family: monospace; font-size: 12px;">${{formatted}}</textarea>
        <div class="form-actions">
          <button class="btn-primary" onclick="document.getElementById('${{targetTextareaId}}').value = this.parentElement.parentElement.querySelector('textarea').value; this.closest('.modal').remove();">Copy to Form</button>
          <button class="btn-secondary" onclick="this.closest('.modal').remove()">Close</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  }}"""
      
      toolbar_html = f"""<div class="toolbar">
    {generate_toolbar_button('+ Add New Domain', f'{router_prefix}/domains/create?format=ui', '#form-container')}
  </div>"""
      
      headers = ['Domain ID', 'Name', 'Vector Store Name', 'Vector Store ID', 'Actions']
      table_html = generate_table_with_headers(headers, table_rows, "No domains found")
      additional_content = '<div id="form-container"></div>'
      
      # Generate page using common UI function
      head = generate_html_head("Domains", additional_scripts)
      html_content = f"""{head}
<body>
  <div class="container">
  <h1>Domains ({len(domains_list)})</h1>
  <p><a href="/">← Back to Main Page</a></p>
  {toolbar_html}
  {table_html}
  {additional_content}
  </div>
</body>
</html>"""
      await log_function_footer(request_data)
      return HTMLResponse(html_content)
    else:
      # HTML format with full domain data (using nested table for complex structures)
      domains_dict_list = [domain_config_to_dict(domain) for domain in domains_list]
      html_content = generate_nested_data_page(f"Domains ({len(domains_dict_list)})", domains_dict_list)
      await log_function_footer(request_data)
      return HTMLResponse(html_content)
      
  except FileNotFoundError as e:
    error_message = str(e)
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=404)
    else:
      return HTMLResponse(generate_error_html(error_message), status_code=404)
  except Exception as e:
    error_message = f"Error retrieving domains: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=500)
    else:
      return HTMLResponse(generate_error_html(error_message), status_code=500)


@router.get('/domains/create')
async def get_create_form(request: Request):
  """
  Display form to create a new domain.
  
  Parameters:
  - format: Response format (html or ui)
  
  Examples:
  /v1/domains/create?format=ui
  """
  function_name = 'get_create_form()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  format = request_params.get('format', 'ui')
  
  # Generate form HTML
  form_html = """
  <div class="modal" id="create-modal">
    <div class="modal-content" style="max-width: 900px;">
      <h2>Create New Domain</h2>
      <form hx-post="{router_prefix}/domains/create?format=html" 
          hx-target="#form-container"
          hx-swap="innerHTML">
        <div class="form-group">
          <label for="domain_id">Domain ID *</label>
          <input type="text" id="domain_id" name="domain_id" required 
               pattern="[a-zA-Z0-9_\-]+" 
               title="Only letters, numbers, underscores, and hyphens allowed"
               onblur="validateDomainId(this)"
               oninput="validateDomainId(this)">
        </div>
        <div class="form-group">
          <label for="name">Name *</label>
          <input type="text" id="name" name="name" required>
        </div>
        <div class="form-group">
          <label for="description">Description *</label>
          <textarea id="description" name="description" rows="3" required></textarea>
        </div>
        <div class="form-group">
          <label for="vector_store_name">Vector Store Name *</label>
          <input type="text" id="vector_store_name" name="vector_store_name" required>
        </div>
        <div class="form-group">
          <label for="vector_store_id">Vector Store ID</label>
          <input type="text" id="vector_store_id" name="vector_store_id" value="" placeholder="Optional - leave empty if not needed">
        </div>
        
        <details class="form-group">
          <summary style="cursor: pointer; font-weight: bold; margin-bottom: 10px;">Advanced: Sources Configuration (Optional)</summary>
          
          <div class="form-group">
            <label for="sources_json">Sources JSON (file_sources, sitepage_sources, list_sources)</label>
            <button type="button" class="btn-small" onclick="showJsonExampleDialog('sources_json')" style="margin-bottom: 5px;">Show JSON Example</button>
            <textarea id="sources_json" name="sources_json" rows="10" placeholder='{"file_sources": [], "sitepage_sources": [], "list_sources": []}'></textarea>
            <small style="color: #666;">Leave empty to create domain without sources. You can add them later.</small>
          </div>
        </details>
        
        <div class="form-actions">
          <button type="submit" class="btn-primary">Create</button>
          <button type="button" class="btn-secondary" onclick="document.getElementById('create-modal').remove()">Cancel</button>
        </div>
      </form>
    </div>
  </div>
  """
  
  await log_function_footer(request_data)
  return HTMLResponse(form_html)

@router.post('/domains/create')
async def create_domain(
  request: Request,
  domain_id: str = Form(...),
  name: str = Form(...),
  description: str = Form(...),
  vector_store_name: str = Form(...),
  vector_store_id: str = Form(default=""),
  sources_json: str = Form(default="")
):
  """
  Create a new domain configuration.
  
  Parameters:
  - format: Response format (json or html)
  - Form data: domain_id, name, description, vector_store_name, vector_store_id
  
  Examples:
  POST /v1/domains/create?format=json
  """
  function_name = 'create_domain()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  format = request_params.get('format', 'json')
  
  # Log received form data for debugging
  log_function_output(request_data, f"Received form data - domain_id: {domain_id}, name: {name}, vector_store_id: '{vector_store_id}'")
  
  try:
    if not hasattr(request.app.state, 'system_info') or not request.app.state.system_info.PERSISTENT_STORAGE_PATH:
      error_message = "PERSISTENT_STORAGE_PATH not configured"
      log_function_output(request_data, f"ERROR: {error_message}")
      await log_function_footer(request_data)
      return generate_error_response(error_message, format, 500)
    
    storage_path = request.app.state.system_info.PERSISTENT_STORAGE_PATH
    
    # Parse sources JSON if provided
    file_sources_list = []
    sitepage_sources_list = []
    list_sources_list = []
    
    if sources_json and sources_json.strip():
      try:
        sources_data = json.loads(sources_json)
        file_sources_list = [FileSource(**src) for src in sources_data.get('file_sources', [])]
        sitepage_sources_list = [SitePageSource(**src) for src in sources_data.get('sitepage_sources', [])]
        list_sources_list = [ListSource(**src) for src in sources_data.get('list_sources', [])]
        log_function_output(request_data, f"Parsed sources: {len(file_sources_list)} file, {len(sitepage_sources_list)} sitepage, {len(list_sources_list)} list")
      except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in sources_json: {str(e)}"
        log_function_output(request_data, f"ERROR: {error_msg}")
        await log_function_footer(request_data)
        return generate_error_response(error_msg, format, 400)
      except Exception as e:
        error_msg = f"Error parsing sources: {str(e)}"
        log_function_output(request_data, f"ERROR: {error_msg}")
        await log_function_footer(request_data)
        return generate_error_response(error_msg, format, 400)
    
    # Prepare domain data
    domain_data = {
      'domain_id': domain_id.strip(),
      'name': name.strip(),
      'description': description.strip(),
      'vector_store_name': vector_store_name.strip(),
      'vector_store_id': vector_store_id.strip(),
      'file_sources': [],
      'sitepage_sources': [],
      'list_sources': []
    }
    
    # Validate domain data
    is_valid, error_msg = validate_domain_config(domain_data)
    if not is_valid:
      log_function_output(request_data, f"Validation error: {error_msg}")
      await log_function_footer(request_data)
      return generate_error_response(error_msg, format, 400)
    
    # Check if domain already exists
    try:
      existing_domains = load_all_domains(storage_path, request_data)
      if any(d.domain_id == domain_id for d in existing_domains):
        error_msg = f"Domain with ID '{domain_id}' already exists"
        log_function_output(request_data, f"ERROR: {error_msg}")
        await log_function_footer(request_data)
        return generate_error_response(error_msg, format, 409)
    except FileNotFoundError:
      # Domains folder doesn't exist yet, that's fine
      pass
    
    # Create DomainConfig object
    domain_config = DomainConfig(
      domain_id=domain_data['domain_id'],
      name=domain_data['name'],
      description=domain_data['description'],
      vector_store_name=domain_data['vector_store_name'],
      vector_store_id=domain_data['vector_store_id'],
      file_sources=file_sources_list,
      sitepage_sources=sitepage_sources_list,
      list_sources=list_sources_list
    )
    
    # Save to file
    save_domain_to_file(storage_path, domain_config, request_data)
    
    log_function_output(request_data, f"Domain created successfully: {domain_id}")
    await log_function_footer(request_data)
    
    success_msg = f"Domain '{name}' created successfully!"
    return generate_success_response(success_msg, format, data=domain_config_to_dict(domain_config), refresh=(format != 'json'))
    
  except Exception as e:
    import traceback
    error_message = f"Error creating domain: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    log_function_output(request_data, f"TRACEBACK: {traceback.format_exc()}")
    await log_function_footer(request_data)
    return generate_error_response(error_message, format, 500)

@router.get('/domains/update')
async def get_update_form(request: Request):
  """
  Display form to update an existing domain.
  
  Parameters:
  - domain_id: ID of domain to update
  - format: Response format (html or ui)
  
  Examples:
  /v1/domains/update?domain_id=my_domain&format=ui
  """
  function_name = 'get_update_form()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  format = request_params.get('format', 'ui')
  domain_id = request_params.get('domain_id')
  
  if not domain_id:
    await log_function_footer(request_data)
    return generate_error_response("Missing domain_id parameter", format, 400)
  
  try:
    if not hasattr(request.app.state, 'system_info') or not request.app.state.system_info.PERSISTENT_STORAGE_PATH:
      error_message = "PERSISTENT_STORAGE_PATH not configured"
      await log_function_footer(request_data)
      return generate_error_response(error_message, format, 500)
    
    storage_path = request.app.state.system_info.PERSISTENT_STORAGE_PATH
    
    # Load existing domain
    domains_list = load_all_domains(storage_path, request_data)
    domain = next((d for d in domains_list if d.domain_id == domain_id), None)
    
    if not domain:
      await log_function_footer(request_data)
      return generate_error_response(f"Domain '{domain_id}' not found", format, 404)
    
    # Pre-serialize sources to JSON for the textarea
    sources_dict = {
      'file_sources': [asdict(src) for src in domain.file_sources],
      'sitepage_sources': [asdict(src) for src in domain.sitepage_sources],
      'list_sources': [asdict(src) for src in domain.list_sources]
    }
    sources_json_str = json.dumps(sources_dict, indent=2)
    
    # Generate pre-filled form
    form_html = f"""
    <div class="modal" id="update-modal">
      <div class="modal-content" style="max-width: 900px;">
        <h2>Update Domain: {domain.name}</h2>
        <form hx-put="{router_prefix}/domains/update?format=html" 
            hx-target="#form-container"
            hx-swap="innerHTML">
          <input type="hidden" name="domain_id" value="{domain.domain_id}">
          <div class="form-group">
            <label for="domain_id_display">Domain ID</label>
            <input type="text" id="domain_id_display" value="{domain.domain_id}" disabled>
          </div>
          <div class="form-group">
            <label for="name">Name *</label>
            <input type="text" id="name" name="name" value="{domain.name}" required>
          </div>
          <div class="form-group">
            <label for="description">Description *</label>
            <textarea id="description" name="description" rows="3" required>{domain.description}</textarea>
          </div>
          <div class="form-group">
            <label for="vector_store_name">Vector Store Name *</label>
            <input type="text" id="vector_store_name" name="vector_store_name" value="{domain.vector_store_name}" required>
          </div>
          <div class="form-group">
            <label for="vector_store_id">Vector Store ID</label>
            <input type="text" id="vector_store_id" name="vector_store_id" value="{domain.vector_store_id}" placeholder="Optional - leave empty if not needed">
          </div>
          
          <details class="form-group" open>
            <summary style="cursor: pointer; font-weight: bold; margin-bottom: 10px;">Advanced: Sources Configuration</summary>
            
            <div class="form-group">
              <label for="sources_json_update">Sources JSON (file_sources, sitepage_sources, list_sources)</label>
              <button type="button" class="btn-small" onclick="showJsonExampleDialog('sources_json_update')" style="margin-bottom: 5px;">Show JSON Example</button>
              <textarea id="sources_json_update" name="sources_json" rows="10">{sources_json_str}</textarea>
              <small style="color: #666;">Modify the JSON to update sources.</small>
            </div>
          </details>
          
          <div class="form-actions">
            <button type="submit" class="btn-primary">Update</button>
            <button type="button" class="btn-secondary" onclick="document.getElementById('update-modal').remove()">Cancel</button>
          </div>
        </form>
      </div>
    </div>
    """
    
    await log_function_footer(request_data)
    return HTMLResponse(form_html)
    
  except Exception as e:
    error_message = f"Error loading domain: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    await log_function_footer(request_data)
    return generate_error_response(error_message, format, 500)

@router.put('/domains/update')
async def update_domain(
  request: Request,
  domain_id: str = Form(...),
  name: str = Form(...),
  description: str = Form(...),
  vector_store_name: str = Form(...),
  vector_store_id: str = Form(default=""),
  sources_json: str = Form(default="")
):
  """
  Update an existing domain configuration.
  
  Parameters:
  - format: Response format (json or html)
  - Form data: domain_id, name, description, vector_store_name, vector_store_id
  
  Examples:
  PUT /v1/domains/update?format=json
  """
  function_name = 'update_domain()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  format = request_params.get('format', 'json')
  
  try:
    if not hasattr(request.app.state, 'system_info') or not request.app.state.system_info.PERSISTENT_STORAGE_PATH:
      error_message = "PERSISTENT_STORAGE_PATH not configured"
      log_function_output(request_data, f"ERROR: {error_message}")
      await log_function_footer(request_data)
      return generate_error_response(error_message, format, 500)
    
    storage_path = request.app.state.system_info.PERSISTENT_STORAGE_PATH
    
    # Load existing domain
    domains_list = load_all_domains(storage_path, request_data)
    existing_domain = next((d for d in domains_list if d.domain_id == domain_id), None)
    
    if not existing_domain:
      error_msg = f"Domain '{domain_id}' not found"
      log_function_output(request_data, f"ERROR: {error_msg}")
      await log_function_footer(request_data)
      return generate_error_response(error_msg, format, 404)
    
    # Parse sources JSON if provided, otherwise keep existing sources
    file_sources_list = existing_domain.file_sources
    sitepage_sources_list = existing_domain.sitepage_sources
    list_sources_list = existing_domain.list_sources
    
    if sources_json and sources_json.strip():
      try:
        sources_data = json.loads(sources_json)
        file_sources_list = [FileSource(**src) for src in sources_data.get('file_sources', [])]
        sitepage_sources_list = [SitePageSource(**src) for src in sources_data.get('sitepage_sources', [])]
        list_sources_list = [ListSource(**src) for src in sources_data.get('list_sources', [])]
        log_function_output(request_data, f"Updated sources: {len(file_sources_list)} file, {len(sitepage_sources_list)} sitepage, {len(list_sources_list)} list")
      except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in sources_json: {str(e)}"
        log_function_output(request_data, f"ERROR: {error_msg}")
        await log_function_footer(request_data)
        return generate_error_response(error_msg, format, 400)
      except Exception as e:
        error_msg = f"Error parsing sources: {str(e)}"
        log_function_output(request_data, f"ERROR: {error_msg}")
        await log_function_footer(request_data)
        return generate_error_response(error_msg, format, 400)
    
    # Prepare updated domain data
    domain_data = {
      'domain_id': domain_id.strip(),
      'name': name.strip(),
      'description': description.strip(),
      'vector_store_name': vector_store_name.strip(),
      'vector_store_id': vector_store_id.strip(),
      'file_sources': [],
      'sitepage_sources': [],
      'list_sources': []
    }
    
    # Validate domain data
    is_valid, error_msg = validate_domain_config(domain_data)
    if not is_valid:
      log_function_output(request_data, f"Validation error: {error_msg}")
      await log_function_footer(request_data)
      return generate_error_response(error_msg, format, 400)
    
    # Create updated DomainConfig object
    updated_domain = DomainConfig(
      domain_id=domain_id,
      name=domain_data['name'],
      description=domain_data['description'],
      vector_store_name=domain_data['vector_store_name'],
      vector_store_id=domain_data['vector_store_id'],
      file_sources=file_sources_list,
      sitepage_sources=sitepage_sources_list,
      list_sources=list_sources_list
    )
    
    # Save to file
    save_domain_to_file(storage_path, updated_domain, request_data)
    
    log_function_output(request_data, f"Domain updated successfully: {domain_id}")
    await log_function_footer(request_data)
    
    success_msg = f"Domain '{name}' updated successfully!"
    return generate_success_response(success_msg, format, data=domain_config_to_dict(updated_domain), refresh=(format != 'json'))
    
  except Exception as e:
    error_message = f"Error updating domain: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    await log_function_footer(request_data)
    return generate_error_response(error_message, format, 500)

@router.delete('/domains/delete')
async def delete_domain(request: Request):
  """
  Delete a domain configuration.
  
  Parameters:
  - domain_id: ID of domain to delete
  - format: Response format (json or html)
  
  Examples:
  DELETE /v1/domains/delete?domain_id=my_domain&format=json
  """
  function_name = 'delete_domain()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  format = request_params.get('format', 'json')
  domain_id = request_params.get('domain_id')
  
  if not domain_id:
    await log_function_footer(request_data)
    return generate_error_response("Missing domain_id parameter", format, 400)
  
  try:
    if not hasattr(request.app.state, 'system_info') or not request.app.state.system_info.PERSISTENT_STORAGE_PATH:
      error_message = "PERSISTENT_STORAGE_PATH not configured"
      log_function_output(request_data, f"ERROR: {error_message}")
      await log_function_footer(request_data)
      return generate_error_response(error_message, format, 500)
    
    storage_path = request.app.state.system_info.PERSISTENT_STORAGE_PATH
    
    # Delete domain folder
    delete_domain_folder(storage_path, domain_id, request_data)
    
    log_function_output(request_data, f"Domain deleted successfully: {domain_id}")
    await log_function_footer(request_data)
    
    success_msg = f"Domain '{domain_id}' deleted successfully!"
    return generate_success_response(success_msg, format, refresh=True)
    
  except FileNotFoundError as e:
    error_message = str(e)
    log_function_output(request_data, f"ERROR: {error_message}")
    await log_function_footer(request_data)
    return generate_error_response(error_message, format, 404)
  except Exception as e:
    error_message = f"Error deleting domain: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    await log_function_footer(request_data)
    return generate_error_response(error_message, format, 500)
