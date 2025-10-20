# CRUD endpoints for domain management
import json
from dataclasses import asdict
from typing import Any, Dict

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse

from hardcoded_config import CRAWLER_HARDCODED_CONFIG
from utils import convert_to_flat_html_table, convert_to_nested_html_table, log_function_footer, log_function_header, log_function_output
from common_crawler_functions import ( DomainConfig, DocumentSource, PageSource, ListSource, load_all_domains, domain_config_to_dict, save_domain_to_file, delete_domain_folder, validate_domain_config )

router = APIRouter()

# Configuration will be injected from app.py
config = None

def set_config(app_config):
  """Set the configuration for Domain management."""
  global config
  config = app_config

def _generate_error_response(error_message: str, format: str, status_code: int = 400):
  """Generate error response in requested format."""
  if format == 'json':
    return JSONResponse({"error": error_message}, status_code=status_code)
  else:
    return HTMLResponse(
      f"<div class='error'>{error_message}</div>",
      status_code=status_code
    )

def _generate_success_response(message: str, format: str, data: Dict[str, Any] = None):
  """Generate success response in requested format."""
  if format == 'json':
    response = {"message": message}
    if data:
      response["data"] = data
    return JSONResponse(response)
  else:
    return HTMLResponse(f"<div class='success'>{message}</div>")

@router.get('/domains')
async def list_domains(request: Request):
  """
  Endpoint to retrieve all domain configurations from the domains folder.
  
  Parameters:
  - format: The response format (json, html, or ui)
    
  Examples:
  /domains
  /domains?format=json
  /domains?format=html
  /domains?format=ui
  """
  function_name = 'list_domains()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/domains'
  endpoint_documentation = list_domains.__doc__
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  # Display documentation if no params are provided
  if len(request_params) == 0:
    await log_function_footer(request_data)
    return HTMLResponse(documentation_HTML)

  format = request_params.get('format', 'html')
  
  try:
    if not hasattr(request.app.state, 'system_info') or not request.app.state.system_info or not request.app.state.system_info.PERSISTENT_STORAGE_PATH:
      error_message = "PERSISTENT_STORAGE_PATH not configured or is empty"
      log_function_output(request_data, f"ERROR: {error_message}")
      await log_function_footer(request_data)
      if format == 'json':
        return JSONResponse({"error": error_message}, status_code=500)
      else:
        error_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Error</title></head><body><h1>Error</h1><p>{error_message}</p></body></html>"
        return HTMLResponse(error_html, status_code=500)
    
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
          hx-get="/domains/update?domain_id={domain.domain_id}&format=ui"
          hx-target="#form-container"
          hx-swap="innerHTML">
        Edit
      </button>
      <button class="btn-small btn-delete" 
          hx-delete="/domains/delete?domain_id={domain.domain_id}&format=html"
          hx-confirm="Are you sure you want to delete domain '{domain.name}'?"
          hx-target="#domain-{domain.domain_id}"
          hx-swap="outerHTML">
        Delete
      </button>
      </td>
    </tr>
    """
      
      html_content = f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
  <title>Domains Management ({len(domains_list)})</title>
  <link rel='stylesheet' href='/static/css/styles.css'>
  <script src='/static/js/htmx.js'></script>
</head>
<body>
  <div class="container">
  <h1>Domains Management ({len(domains_list)})</h1>
  
  <div class="toolbar">
    <button class="btn-primary" 
        hx-get="/domains/create?format=ui"
        hx-target="#form-container"
        hx-swap="innerHTML">
    + Add New Domain
    </button>
  </div>
  
  <table>
    <thead>
    <tr>
      <th>Domain ID</th>
      <th>Name</th>
      <th>Vector Store Name</th>
      <th>Vector Store ID</th>
      <th>Actions</th>
    </tr>
    </thead>
    <tbody>
    {table_rows if table_rows else '<tr><td colspan="5">No domains found</td></tr>'}
    </tbody>
  </table>
  
  <div id="form-container"></div>
  </div>
</body>
</html>"""
      await log_function_footer(request_data)
      return HTMLResponse(html_content)
    else:
      # HTML format with full domain data (using nested table for complex structures)
      domains_dict_list = [domain_config_to_dict(domain) for domain in domains_list]
      html_content = _generate_html_response_from_nested_data(
        f"Domains ({len(domains_dict_list)})",
        domains_dict_list
      )
      await log_function_footer(request_data)
      return HTMLResponse(html_content)
      
  except FileNotFoundError as e:
    error_message = str(e)
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=404)
    else:
      error_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Error</title></head><body><h1>Error</h1><p>{error_message}</p></body></html>"
      return HTMLResponse(error_html, status_code=404)
  except Exception as e:
    error_message = f"Error retrieving domains: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=500)
    else:
      error_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Error</title></head><body><h1>Error</h1><p>{error_message}</p></body></html>"
      return HTMLResponse(error_html, status_code=500)

def _generate_html_response_from_nested_data(title: str, data: Any) -> str:
  """
  Generate HTML response with nested table for complex data structures.
  
  Args:
    title: Page title
    data: Complex data structure to convert to nested HTML table
    
  Returns:
    Complete HTML page with nested table
  """
  table_html = convert_to_nested_html_table(data)
  return f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
  <title>{title}</title>
  <link rel='stylesheet' href='/static/css/styles.css'>
  <script src='/static/js/htmx.js'></script>
</head>
<body>
  <h1>{title}</h1>
  {table_html}
</body>
</html>"""

@router.get('/domains/create')
async def get_create_form(request: Request):
  """
  Display form to create a new domain.
  
  Parameters:
  - format: Response format (html or ui)
  
  Examples:
  /domains/create?format=ui
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
      <form hx-post="/domains/create?format=html" 
          hx-target="#form-container"
          hx-swap="innerHTML">
        <div class="form-group">
          <label for="domain_id">Domain ID *</label>
          <input type="text" id="domain_id" name="domain_id" required 
               pattern="[a-zA-Z0-9_-]+" 
               title="Only letters, numbers, underscores, and hyphens allowed">
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
          <label for="vector_store_id">Vector Store ID *</label>
          <input type="text" id="vector_store_id" name="vector_store_id" required>
        </div>
        
        <details class="form-group">
          <summary style="cursor: pointer; font-weight: bold; margin-bottom: 10px;">Advanced: Sources Configuration (Optional)</summary>
          
          <div class="form-group">
            <label for="sources_json">Sources JSON (document_sources, page_sources, list_sources)</label>
            <button type="button" class="btn-small" onclick="showJsonExampleDialog('sources_json')" style="margin-bottom: 5px;">Show JSON Example</button>
            <textarea id="sources_json" name="sources_json" rows="10" placeholder='{"document_sources": [], "page_sources": [], "list_sources": []}'></textarea>
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
  
  <script>
  function showJsonExampleDialog(targetTextareaId) {
    const demoJson = {
      "document_sources": [
        {
          "site_url": "https://example.sharepoint.com/sites/MySite",
          "sharepoint_url_part": "/Documents",
          "filter": ""
        }
      ],
      "page_sources": [
        {
          "site_url": "https://example.sharepoint.com/sites/MySite",
          "sharepoint_url_part": "/SitePages",
          "filter": "FSObjType eq 0"
        }
      ],
      "list_sources": [
        {
          "site_url": "https://example.sharepoint.com/sites/MySite",
          "list_name": "My List",
          "filter": ""
        }
      ]
    };
    
    const formatted = JSON.stringify(demoJson, null, 2);
    
    // Show in a simple alert-style modal
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
      <div class="modal-content" style="max-width: 700px;">
        <h3>JSON Example</h3>
        <p>Copy this example and modify it for your needs:</p>
        <textarea readonly rows="20" style="width: 100%; font-family: monospace; font-size: 12px;">${formatted}</textarea>
        <div class="form-actions">
          <button class="btn-primary" onclick="document.getElementById('${targetTextareaId}').value = this.parentElement.parentElement.querySelector('textarea').value; this.closest('.modal').remove();">Copy to Form</button>
          <button class="btn-secondary" onclick="this.closest('.modal').remove()">Close</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  }
  </script>
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
  vector_store_id: str = Form(...),
  sources_json: str = Form(default="")
):
  """
  Create a new domain configuration.
  
  Parameters:
  - format: Response format (json or html)
  - Form data: domain_id, name, description, vector_store_name, vector_store_id
  
  Examples:
  POST /domains/create?format=json
  """
  function_name = 'create_domain()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  format = request_params.get('format', 'json')
  
  try:
    if not hasattr(request.app.state, 'system_info') or not request.app.state.system_info.PERSISTENT_STORAGE_PATH:
      error_message = "PERSISTENT_STORAGE_PATH not configured"
      log_function_output(request_data, f"ERROR: {error_message}")
      await log_function_footer(request_data)
      return _generate_error_response(error_message, format, 500)
    
    storage_path = request.app.state.system_info.PERSISTENT_STORAGE_PATH
    
    # Parse sources JSON if provided
    document_sources_list = []
    page_sources_list = []
    list_sources_list = []
    
    if sources_json and sources_json.strip():
      try:
        sources_data = json.loads(sources_json)
        document_sources_list = [DocumentSource(**src) for src in sources_data.get('document_sources', [])]
        page_sources_list = [PageSource(**src) for src in sources_data.get('page_sources', [])]
        list_sources_list = [ListSource(**src) for src in sources_data.get('list_sources', [])]
        log_function_output(request_data, f"Parsed sources: {len(document_sources_list)} document, {len(page_sources_list)} page, {len(list_sources_list)} list")
      except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in sources_json: {str(e)}"
        log_function_output(request_data, f"ERROR: {error_msg}")
        await log_function_footer(request_data)
        return _generate_error_response(error_msg, format, 400)
      except Exception as e:
        error_msg = f"Error parsing sources: {str(e)}"
        log_function_output(request_data, f"ERROR: {error_msg}")
        await log_function_footer(request_data)
        return _generate_error_response(error_msg, format, 400)
    
    # Prepare domain data
    domain_data = {
      'domain_id': domain_id.strip(),
      'name': name.strip(),
      'description': description.strip(),
      'vector_store_name': vector_store_name.strip(),
      'vector_store_id': vector_store_id.strip(),
      'document_sources': [],
      'page_sources': [],
      'list_sources': []
    }
    
    # Validate domain data
    is_valid, error_msg = validate_domain_config(domain_data)
    if not is_valid:
      log_function_output(request_data, f"Validation error: {error_msg}")
      await log_function_footer(request_data)
      return _generate_error_response(error_msg, format, 400)
    
    # Check if domain already exists
    try:
      existing_domains = load_all_domains(storage_path, request_data)
      if any(d.domain_id == domain_id for d in existing_domains):
        error_msg = f"Domain with ID '{domain_id}' already exists"
        log_function_output(request_data, f"ERROR: {error_msg}")
        await log_function_footer(request_data)
        return _generate_error_response(error_msg, format, 409)
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
      document_sources=document_sources_list,
      page_sources=page_sources_list,
      list_sources=list_sources_list
    )
    
    # Save to file
    save_domain_to_file(storage_path, domain_config, request_data)
    
    log_function_output(request_data, f"Domain created successfully: {domain_id}")
    await log_function_footer(request_data)
    
    success_msg = f"Domain '{name}' created successfully!"
    if format == 'json':
      return JSONResponse({
        "message": success_msg,
        "data": domain_config_to_dict(domain_config)
      })
    else:
      # Use HX-Refresh header to trigger page reload
      return HTMLResponse(
        f"<div class='success'>{success_msg} Reloading...</div>",
        headers={"HX-Refresh": "true"}
      )
    
  except Exception as e:
    error_message = f"Error creating domain: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    await log_function_footer(request_data)
    return _generate_error_response(error_message, format, 500)

@router.get('/domains/update')
async def get_update_form(request: Request):
  """
  Display form to update an existing domain.
  
  Parameters:
  - domain_id: ID of domain to update
  - format: Response format (html or ui)
  
  Examples:
  /domains/update?domain_id=my_domain&format=ui
  """
  function_name = 'get_update_form()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  format = request_params.get('format', 'ui')
  domain_id = request_params.get('domain_id')
  
  if not domain_id:
    await log_function_footer(request_data)
    return _generate_error_response("Missing domain_id parameter", format, 400)
  
  try:
    if not hasattr(request.app.state, 'system_info') or not request.app.state.system_info.PERSISTENT_STORAGE_PATH:
      error_message = "PERSISTENT_STORAGE_PATH not configured"
      await log_function_footer(request_data)
      return _generate_error_response(error_message, format, 500)
    
    storage_path = request.app.state.system_info.PERSISTENT_STORAGE_PATH
    
    # Load existing domain
    domains_list = load_all_domains(storage_path, request_data)
    domain = next((d for d in domains_list if d.domain_id == domain_id), None)
    
    if not domain:
      await log_function_footer(request_data)
      return _generate_error_response(f"Domain '{domain_id}' not found", format, 404)
    
    # Pre-serialize sources to JSON for the textarea
    sources_dict = {
      'document_sources': [asdict(src) for src in domain.document_sources],
      'page_sources': [asdict(src) for src in domain.page_sources],
      'list_sources': [asdict(src) for src in domain.list_sources]
    }
    sources_json_str = json.dumps(sources_dict, indent=2)
    
    # Generate pre-filled form
    form_html = f"""
    <div class="modal" id="update-modal">
      <div class="modal-content" style="max-width: 900px;">
        <h2>Update Domain: {domain.name}</h2>
        <form hx-put="/domains/update?format=html" 
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
            <label for="vector_store_id">Vector Store ID *</label>
            <input type="text" id="vector_store_id" name="vector_store_id" value="{domain.vector_store_id}" required>
          </div>
          
          <details class="form-group" open>
            <summary style="cursor: pointer; font-weight: bold; margin-bottom: 10px;">Advanced: Sources Configuration</summary>
            
            <div class="form-group">
              <label for="sources_json_update">Sources JSON (document_sources, page_sources, list_sources)</label>
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
    return _generate_error_response(error_message, format, 500)

@router.put('/domains/update')
async def update_domain(
  request: Request,
  domain_id: str = Form(...),
  name: str = Form(...),
  description: str = Form(...),
  vector_store_name: str = Form(...),
  vector_store_id: str = Form(...),
  sources_json: str = Form(default="")
):
  """
  Update an existing domain configuration.
  
  Parameters:
  - format: Response format (json or html)
  - Form data: domain_id, name, description, vector_store_name, vector_store_id
  
  Examples:
  PUT /domains/update?format=json
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
      return _generate_error_response(error_message, format, 500)
    
    storage_path = request.app.state.system_info.PERSISTENT_STORAGE_PATH
    
    # Load existing domain
    domains_list = load_all_domains(storage_path, request_data)
    existing_domain = next((d for d in domains_list if d.domain_id == domain_id), None)
    
    if not existing_domain:
      error_msg = f"Domain '{domain_id}' not found"
      log_function_output(request_data, f"ERROR: {error_msg}")
      await log_function_footer(request_data)
      return _generate_error_response(error_msg, format, 404)
    
    # Parse sources JSON if provided, otherwise keep existing sources
    document_sources_list = existing_domain.document_sources
    page_sources_list = existing_domain.page_sources
    list_sources_list = existing_domain.list_sources
    
    if sources_json and sources_json.strip():
      try:
        sources_data = json.loads(sources_json)
        document_sources_list = [DocumentSource(**src) for src in sources_data.get('document_sources', [])]
        page_sources_list = [PageSource(**src) for src in sources_data.get('page_sources', [])]
        list_sources_list = [ListSource(**src) for src in sources_data.get('list_sources', [])]
        log_function_output(request_data, f"Updated sources: {len(document_sources_list)} document, {len(page_sources_list)} page, {len(list_sources_list)} list")
      except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in sources_json: {str(e)}"
        log_function_output(request_data, f"ERROR: {error_msg}")
        await log_function_footer(request_data)
        return _generate_error_response(error_msg, format, 400)
      except Exception as e:
        error_msg = f"Error parsing sources: {str(e)}"
        log_function_output(request_data, f"ERROR: {error_msg}")
        await log_function_footer(request_data)
        return _generate_error_response(error_msg, format, 400)
    
    # Prepare updated domain data
    domain_data = {
      'domain_id': domain_id.strip(),
      'name': name.strip(),
      'description': description.strip(),
      'vector_store_name': vector_store_name.strip(),
      'vector_store_id': vector_store_id.strip(),
      'document_sources': [],
      'page_sources': [],
      'list_sources': []
    }
    
    # Validate domain data
    is_valid, error_msg = validate_domain_config(domain_data)
    if not is_valid:
      log_function_output(request_data, f"Validation error: {error_msg}")
      await log_function_footer(request_data)
      return _generate_error_response(error_msg, format, 400)
    
    # Create updated DomainConfig object
    updated_domain = DomainConfig(
      domain_id=domain_id,
      name=domain_data['name'],
      description=domain_data['description'],
      vector_store_name=domain_data['vector_store_name'],
      vector_store_id=domain_data['vector_store_id'],
      document_sources=document_sources_list,
      page_sources=page_sources_list,
      list_sources=list_sources_list
    )
    
    # Save to file
    save_domain_to_file(storage_path, updated_domain, request_data)
    
    log_function_output(request_data, f"Domain updated successfully: {domain_id}")
    await log_function_footer(request_data)
    
    success_msg = f"Domain '{name}' updated successfully!"
    if format == 'json':
      return JSONResponse({
        "message": success_msg,
        "data": domain_config_to_dict(updated_domain)
      })
    else:
      # Use HX-Refresh header to trigger page reload
      return HTMLResponse(
        f"<div class='success'>{success_msg} Reloading...</div>",
        headers={"HX-Refresh": "true"}
      )
    
  except Exception as e:
    error_message = f"Error updating domain: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    await log_function_footer(request_data)
    return _generate_error_response(error_message, format, 500)

@router.delete('/domains/delete')
async def delete_domain(request: Request):
  """
  Delete a domain configuration.
  
  Parameters:
  - domain_id: ID of domain to delete
  - format: Response format (json or html)
  
  Examples:
  DELETE /domains/delete?domain_id=my_domain&format=json
  """
  function_name = 'delete_domain()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  format = request_params.get('format', 'json')
  domain_id = request_params.get('domain_id')
  
  if not domain_id:
    await log_function_footer(request_data)
    return _generate_error_response("Missing domain_id parameter", format, 400)
  
  try:
    if not hasattr(request.app.state, 'system_info') or not request.app.state.system_info.PERSISTENT_STORAGE_PATH:
      error_message = "PERSISTENT_STORAGE_PATH not configured"
      log_function_output(request_data, f"ERROR: {error_message}")
      await log_function_footer(request_data)
      return _generate_error_response(error_message, format, 500)
    
    storage_path = request.app.state.system_info.PERSISTENT_STORAGE_PATH
    
    # Delete domain folder
    delete_domain_folder(storage_path, domain_id, request_data)
    
    log_function_output(request_data, f"Domain deleted successfully: {domain_id}")
    await log_function_footer(request_data)
    
    success_msg = f"Domain '{domain_id}' deleted successfully!"
    if format == 'json':
      return JSONResponse({"message": success_msg})
    else:
      # Use HX-Refresh header to trigger page reload and update count
      return HTMLResponse("", headers={"HX-Refresh": "true"})
    
  except FileNotFoundError as e:
    error_message = str(e)
    log_function_output(request_data, f"ERROR: {error_message}")
    await log_function_footer(request_data)
    return _generate_error_response(error_message, format, 404)
  except Exception as e:
    error_message = f"Error deleting domain: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    await log_function_footer(request_data)
    return _generate_error_response(error_message, format, 500)
