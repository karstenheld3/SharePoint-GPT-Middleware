# CRUD endpoints for domain management
import json
from typing import Any, Dict

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse

from hardcoded_config import CRAWLER_HARDCODED_CONFIG
from utils import log_function_footer, log_function_header, log_function_output
from common_crawler_functions import (
    DomainConfig, DocumentSource, PageSource, ListSource,
    load_all_domains, domain_config_to_dict, 
    save_domain_to_file, delete_domain_folder, validate_domain_config
)

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
        <div class="modal-content">
            <h2>Create New Domain</h2>
            <form hx-post="/domains/create?format=json" 
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
                <div class="form-actions">
                    <button type="submit" class="btn-primary">Create Domain</button>
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
    vector_store_id: str = Form(...)
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
            document_sources=[],
            page_sources=[],
            list_sources=[]
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
            return HTMLResponse(f"""
                <div class='success'>
                    {success_msg}
                    <button onclick="location.reload()" class="btn-primary">Refresh Page</button>
                </div>
            """)
        
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
        
        # Generate pre-filled form
        form_html = f"""
        <div class="modal" id="update-modal">
            <div class="modal-content">
                <h2>Update Domain: {domain.name}</h2>
                <form hx-put="/domains/update?format=json" 
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
                    <div class="form-actions">
                        <button type="submit" class="btn-primary">Update Domain</button>
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
    vector_store_id: str = Form(...)
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
        
        # Load existing domain to preserve sources
        domains_list = load_all_domains(storage_path, request_data)
        existing_domain = next((d for d in domains_list if d.domain_id == domain_id), None)
        
        if not existing_domain:
            error_msg = f"Domain '{domain_id}' not found"
            log_function_output(request_data, f"ERROR: {error_msg}")
            await log_function_footer(request_data)
            return _generate_error_response(error_msg, format, 404)
        
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
        
        # Create updated DomainConfig object (preserve existing sources)
        updated_domain = DomainConfig(
            domain_id=domain_id,
            name=domain_data['name'],
            description=domain_data['description'],
            vector_store_name=domain_data['vector_store_name'],
            vector_store_id=domain_data['vector_store_id'],
            document_sources=existing_domain.document_sources,
            page_sources=existing_domain.page_sources,
            list_sources=existing_domain.list_sources
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
            return HTMLResponse(f"""
                <div class='success'>
                    {success_msg}
                    <button onclick="location.reload()" class="btn-primary">Refresh Page</button>
                </div>
            """)
        
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
            # Return empty response to remove the row from table
            return HTMLResponse("")
        
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
