# Endpoint CRUD Implementation Pattern Specification

## Overview

This document describes the generic implementation pattern for CRUD (Create, Read, Update, Delete) operations across all router endpoints in the SharePoint-GPT-Middleware application.

## HTTP Method and URL Pattern Summary

- **CREATE**: `POST /router/endpoint/create?format=[json|html]` with form data
- **READ (Single)**: `GET /router/endpoint?id=[ID]&format=[json|html|ui]`
- **READ (List)**: `GET /router/endpoint?format=[json|html|ui]&includeattributes=[...]&excludeattributes=[...]`
- **UPDATE**: `PUT /router/endpoint/update?format=[json|html]` with form data
- **DELETE**: `DELETE /router/endpoint/delete?id=[ID]&format=[json|html]`

**Note:** The exact parameter name for identifying resources varies by endpoint:
- Domains: `domain_id`
- Vector Stores: `vector_store_id`
- Files: `file_id`
- Assistants: `assistant_id`

## Format Parameter

All endpoints support a `format` query parameter that controls the response format:

### Format Types

- **`json`**: Returns structured JSON data for API consumption
- **`html`**: Returns formatted HTML page (read-only view with tables)
- **`ui`**: Returns interactive HTML page with HTMX-powered buttons and forms
- **`(no format)`**: Returns endpoint documentation (docstring)

### Format Response Examples

#### JSON Format
```json
{
  "data": [
    {"id": "vs_123", "name": "Example Vector Store", "created_at": "2025-11-27 14:30:00"},
    {"id": "vs_456", "name": "Another Store", "created_at": "2025-11-27 15:45:00"}
  ],
  "count": 2
}
```

**Success Response (Create/Update/Delete):**
```json
{
  "message": "Domain 'ExampleDomain' created successfully!",
  "data": {
    "domain_id": "example01",
    "name": "ExampleDomain",
    "vector_store_id": "vs_123"
  }
}
```

**Error Response:**
```json
{
  "error": "Domain with ID 'example01' already exists"
}
```

#### HTML Format
Returns a complete HTML page with:
- Page title and header
- Data displayed in HTML tables (flat or nested)
- Back navigation link
- No interactive elements (read-only)

**Example:**
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset='utf-8'>
  <title>Vector Stores (2)</title>
  <link rel='stylesheet' href='/static/css/styles.css'>
</head>
<body>
  <h1>Vector Stores (2)</h1>
  <table>
    <thead>
      <tr><th>ID</th><th>Name</th><th>Created At</th></tr>
    </thead>
    <tbody>
      <tr><td>vs_123</td><td>Example Vector Store</td><td>2025-11-27 14:30:00</td></tr>
      <tr><td>vs_456</td><td>Another Store</td><td>2025-11-27 15:45:00</td></tr>
    </tbody>
  </table>
  <p><a href="/">← Back to Main Page</a></p>
</body>
</html>
```

#### UI Format
Returns an interactive HTML page with:
- HTMX-powered action buttons (Edit, Delete, etc.)
- Modal forms for Create/Update operations
- Real-time updates without page refresh
- Confirmation dialogs for destructive actions
- Toolbar with action buttons

**Example:**
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset='utf-8'>
  <title>Domains (3)</title>
  <link rel='stylesheet' href='/static/css/styles.css'>
  <script src='/static/js/htmx.js'></script>
</head>
<body>
  <div class="container">
    <h1>Domains (3)</h1>
    <p><a href="/">← Back to Main Page</a></p>
    
    <div class="toolbar">
      <button class="btn-primary" 
              hx-get="/domains/create?format=ui" 
              hx-target="#form-container">
        + Add New Domain
      </button>
    </div>
    
    <table>
      <thead>
        <tr><th>Domain ID</th><th>Name</th><th>Actions</th></tr>
      </thead>
      <tbody>
        <tr id="domain-example01">
          <td>example01</td>
          <td>Example Domain</td>
          <td class="actions">
            <button class="btn-small btn-edit" 
                    hx-get="/domains/update?domain_id=example01&format=ui"
                    hx-target="#form-container">
              Edit
            </button>
            <button class="btn-small btn-delete" 
                    hx-delete="/domains/delete?domain_id=example01&format=html"
                    hx-confirm="Are you sure you want to delete domain 'Example Domain'?"
                    hx-target="#domain-example01"
                    hx-swap="outerHTML">
              Delete
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    
    <div id="form-container"></div>
  </div>
</body>
</html>
```

#### No Format (Documentation)
When no query parameters are provided, endpoints return their documentation:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset='utf-8'>
  <title>/vectorstores - Documentation</title>
</head>
<body>
  <pre>
  Endpoint to retrieve all vector stores from Azure OpenAI.
  
  Parameters:
  - format: The response format (json, html, or ui)
  - includeattributes: Comma-separated list of attributes to include
  - excludeattributes: Comma-separated list of attributes to exclude
  
  Examples:
  /vectorstores?format=json
  /vectorstores?format=ui
  </pre>
</body>
</html>
```

## CRUD Operation Patterns

### CREATE Operation

**Endpoint Pattern:**
```
POST /router/endpoint?format=[json|html]
```

**Request:**
- Method: `POST`
- Content-Type: `application/x-www-form-urlencoded` (HTML form data)
- Body: Form fields as key-value pairs

**Form Data Example:**
```
domain_id=example01
name=Example Domain
description=This is an example
vector_store_name=Example VS
vector_store_id=vs_123
sources_json={"file_sources": []}
```

**Response:**
- **JSON format**: Returns success message with created object data
- **HTML format**: Returns success message with page refresh trigger (HTMX)

**Implementation Pattern:**
```python
@router.post('/endpoint/create')
async def create_item(
  request: Request,
  field1: str = Form(...),
  field2: str = Form(...),
  optional_field: str = Form(default="")
):
  function_name = 'create_item()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  format = request_params.get('format', 'json')
  
  try:
    # Validate system configuration
    if not hasattr(request.app.state, 'system_info'):
      return generate_error_response("System not configured", format, 500)
    
    # Validate input data
    is_valid, error_msg = validate_data(field1, field2)
    if not is_valid:
      return generate_error_response(error_msg, format, 400)
    
    # Check for duplicates
    existing_items = load_all_items(storage_path, request_data)
    if any(item.id == field1 for item in existing_items):
      return generate_error_response(f"Item '{field1}' already exists", format, 409)
    
    # Create and save item
    new_item = ItemConfig(field1=field1, field2=field2, optional_field=optional_field)
    save_item_to_file(storage_path, new_item, request_data)
    
    log_function_output(request_data, f"Item created successfully: {field1}")
    await log_function_footer(request_data)
    
    success_msg = f"Item '{field1}' created successfully!"
    return generate_success_response(success_msg, format, data=item_to_dict(new_item), refresh=(format != 'json'))
    
  except Exception as e:
    error_message = f"Error creating item: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    await log_function_footer(request_data)
    return generate_error_response(error_message, format, 500)
```

**Success Response Examples:**

JSON:
```json
{
  "message": "Item 'example01' created successfully!",
  "data": {
    "id": "example01",
    "name": "Example Item",
    "created_at": "2025-11-27 14:30:00"
  }
}
```

HTML (triggers page refresh):
```html
<div class="success-message">
  Item 'example01' created successfully!
  <script>
    setTimeout(() => { window.location.reload(); }, 1000);
  </script>
</div>
```

### READ Operation (List)

**Endpoint Pattern:**
```
GET /router/endpoint?format=[json|html|ui]&includeattributes=[attr1,attr2]&excludeattributes=[attr3,attr4]
```

**Query Parameters:**
- `format`: Response format (json, html, ui)
- `includeattributes`: Comma-separated list of attributes to include (takes precedence)
- `excludeattributes`: Comma-separated list of attributes to exclude

**Implementation Pattern:**
```python
@router.get('/endpoint')
async def list_items(request: Request):
  """
  Endpoint to retrieve all items.
  
  Parameters:
  - format: The response format (json, html, or ui)
  - includeattributes: Comma-separated list of attributes to include
  - excludeattributes: Comma-separated list of attributes to exclude
  
  Examples:
  /endpoint?format=json
  /endpoint?format=ui
  /endpoint?format=json&includeattributes=id,name,created_at
  """
  function_name = 'list_items()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')
  endpoint_documentation = list_items.__doc__
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  
  # Display documentation if no params are provided
  if len(request_params) == 0:
    await log_function_footer(request_data)
    return HTMLResponse(documentation_HTML)
  
  format = request_params.get('format', 'html')
  include_attributes = request_params.get('includeattributes', None)
  exclude_attributes = request_params.get('excludeattributes', None)
  
  try:
    # Load all items
    items_list = load_all_items(storage_path, request_data)
    
    # Convert to dict
    items_dict_list = [item_to_dict(item) for item in items_list]
    
    # Apply attribute filtering
    items_dict_list = include_exclude_attributes(items_dict_list, include_attributes, exclude_attributes)
    
    if format == 'json':
      await log_function_footer(request_data)
      return JSONResponse({"data": items_dict_list, "count": len(items_dict_list)})
    elif format == 'ui':
      # UI format with action buttons
      html_content = generate_ui_table_page(title='Items', count=len(items_list), data=items_dict_list, columns=columns, row_id_field='id', row_id_prefix='item', back_link='/')
      await log_function_footer(request_data)
      return HTMLResponse(html_content)
    else:
      # HTML format (read-only)
      html_content = generate_nested_data_page(f"Items ({len(items_dict_list)})", items_dict_list)
      await log_function_footer(request_data)
      return HTMLResponse(html_content)
      
  except Exception as e:
    error_message = f"Error retrieving items: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=500)
    else:
      return HTMLResponse(generate_error_html(error_message), status_code=500)
```

### READ Operation (Single Item)

**Endpoint Pattern:**
```
GET /router/endpoint?id=[ID]&format=[json|html|ui]
```

**Implementation Pattern:**
```python
@router.get('/endpoint/get')
async def get_item(request: Request):
  """
  Endpoint to retrieve a single item by ID.
  
  Parameters:
  - id: The ID of the item to retrieve (required)
  - format: The response format (json, html, or ui)
  
  Examples:
  /endpoint/get?id=example01&format=json
  /endpoint/get?id=example01&format=html
  """
  function_name = 'get_item()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  # Display documentation if no params
  if len(request_params) == 0:
    await log_function_footer(request_data)
    return HTMLResponse(generate_documentation_page('/endpoint/get', get_item.__doc__))
  
  item_id = request_params.get('id')
  format = request_params.get('format', 'json')
  
  if not item_id:
    error_message = "Missing required parameter: id"
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=400)
    return HTMLResponse(generate_error_html(error_message), status_code=400)
  
  try:
    # Load item
    item = load_item_by_id(storage_path, item_id, request_data)
    
    if not item:
      error_message = f"Item '{item_id}' not found"
      await log_function_footer(request_data)
      if format == 'json':
        return JSONResponse({"error": error_message}, status_code=404)
      return HTMLResponse(generate_error_html(error_message), status_code=404)
    
    item_dict = item_to_dict(item)
    
    if format == 'json':
      await log_function_footer(request_data)
      return JSONResponse({"data": item_dict})
    else:
      # HTML format
      html_content = generate_nested_data_page(f"Item: {item_id}", item_dict)
      await log_function_footer(request_data)
      return HTMLResponse(html_content)
      
  except Exception as e:
    error_message = f"Error retrieving item: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=500)
    return HTMLResponse(generate_error_html(error_message), status_code=500)
```

### UPDATE Operation

**Endpoint Pattern:**
```
PUT /router/endpoint?format=[json|html]
```

**Two-Step Process:**

1. **GET form** (displays pre-filled form):
```
GET /router/endpoint/update?id=[ID]&format=ui
```

2. **PUT data** (submits updated data):
```
PUT /router/endpoint/update?format=[json|html]
```

**Implementation Pattern:**

**Step 1: Display Update Form**
```python
@router.get('/endpoint/update')
async def get_update_form(request: Request):
  """
  Display form to update an existing item.
  
  Parameters:
  - id: ID of item to update (required)
  - format: Response format (html or ui)
  
  Examples:
  /endpoint/update?id=example01&format=ui
  """
  function_name = 'get_update_form()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  format = request_params.get('format', 'ui')
  item_id = request_params.get('id')
  
  if not item_id:
    await log_function_footer(request_data)
    return generate_error_response("Missing id parameter", format, 400)
  
  try:
    # Load existing item
    item = load_item_by_id(storage_path, item_id, request_data)
    
    if not item:
      await log_function_footer(request_data)
      return generate_error_response(f"Item '{item_id}' not found", format, 404)
    
    # Generate pre-filled form
    form_html = f"""
    <div class="modal" id="update-modal">
      <div class="modal-content">
        <h2>Update Item: {item.name}</h2>
        <form hx-put="/endpoint/update?format=html" 
              hx-target="#form-container"
              hx-swap="innerHTML">
          <input type="hidden" name="id" value="{item.id}">
          <div class="form-group">
            <label for="name">Name *</label>
            <input type="text" id="name" name="name" value="{item.name}" required>
          </div>
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
    error_message = f"Error loading item: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    await log_function_footer(request_data)
    return generate_error_response(error_message, format, 500)
```

**Step 2: Process Update**
```python
@router.put('/endpoint/update')
async def update_item(
  request: Request,
  id: str = Form(...),
  name: str = Form(...),
  optional_field: str = Form(default="")
):
  """
  Update an existing item.
  
  Parameters:
  - format: Response format (json or html)
  - Form data: id, name, optional_field
  
  Examples:
  PUT /endpoint/update?format=json
  """
  function_name = 'update_item()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  format = request_params.get('format', 'json')
  
  try:
    # Load existing item
    existing_item = load_item_by_id(storage_path, id, request_data)
    
    if not existing_item:
      error_msg = f"Item '{id}' not found"
      log_function_output(request_data, f"ERROR: {error_msg}")
      await log_function_footer(request_data)
      return generate_error_response(error_msg, format, 404)
    
    # Validate updated data
    is_valid, error_msg = validate_data(name, optional_field)
    if not is_valid:
      log_function_output(request_data, f"Validation error: {error_msg}")
      await log_function_footer(request_data)
      return generate_error_response(error_msg, format, 400)
    
    # Create updated item
    updated_item = ItemConfig(id=id, name=name.strip(), optional_field=optional_field.strip())
    
    # Save to file
    save_item_to_file(storage_path, updated_item, request_data)
    
    log_function_output(request_data, f"Item updated successfully: {id}")
    await log_function_footer(request_data)
    
    success_msg = f"Item '{name}' updated successfully!"
    return generate_success_response(success_msg, format, data=item_to_dict(updated_item), refresh=(format != 'json'))
    
  except Exception as e:
    error_message = f"Error updating item: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    await log_function_footer(request_data)
    return generate_error_response(error_message, format, 500)
```

### DELETE Operation

**Endpoint Pattern:**
```
DELETE /router/endpoint/delete?id=[ID]&format=[json|html]
```

**Query Parameters:**
- `id`: ID of the item to delete (required)
- `format`: Response format (json or html, default: html)
- Additional parameters for delete options (e.g., `delete_files=true`)

**Implementation Pattern:**
```python
@router.api_route('/endpoint/delete', methods=['GET', 'DELETE'])
async def delete_item(request: Request):
  """
  Delete an item.
  
  Parameters:
  - id: ID of item to delete (required)
  - format: Response format (json or html, default: html)
  
  Examples:
  DELETE /endpoint/delete?id=example01
  DELETE /endpoint/delete?id=example01&format=json
  """
  function_name = 'delete_item()'
  request_data = log_function_header(function_name)
  request_params = dict(request.query_params)
  
  endpoint = '/' + function_name.replace('()','')
  endpoint_documentation = delete_item.__doc__
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  
  # Display documentation if no params
  if len(request_params) == 0:
    await log_function_footer(request_data)
    return HTMLResponse(documentation_HTML)
  
  format = request_params.get('format', 'html')
  item_id = request_params.get('id')
  
  if not item_id:
    await log_function_footer(request_data)
    error_msg = "Missing required parameter: id"
    if format == 'json':
      return JSONResponse({"error": error_msg}, status_code=400)
    else:
      return HTMLResponse(f"<tr><td colspan='5' class='error'>{error_msg}</td></tr>", status_code=400)
  
  try:
    # Delete item
    delete_item_by_id(storage_path, item_id, request_data)
    
    log_function_output(request_data, f"Item deleted successfully: {item_id}")
    await log_function_footer(request_data)
    
    success_msg = f"Item '{item_id}' deleted successfully!"
    
    if format == 'json':
      return JSONResponse({"message": success_msg})
    else:
      # Return empty response to remove the row from UI (HTMX)
      return HTMLResponse("")
    
  except FileNotFoundError as e:
    error_message = str(e)
    log_function_output(request_data, f"ERROR: {error_message}")
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=404)
    else:
      return HTMLResponse(f"<tr><td colspan='5' class='error'>{error_message}</td></tr>", status_code=404)
  except Exception as e:
    error_message = f"Error deleting item: {str(e)}"
    log_function_output(request_data, f"ERROR: {error_message}")
    await log_function_footer(request_data)
    if format == 'json':
      return JSONResponse({"error": error_message}, status_code=500)
    else:
      return HTMLResponse(f"<tr><td colspan='5' class='error'>{error_message}</td></tr>", status_code=500)
```

**Delete Response Examples:**

JSON Success:
```json
{
  "message": "Item 'example01' deleted successfully!"
}
```

HTML Success (HTMX removes row):
```html

```

JSON Error:
```json
{
  "error": "Item 'example01' not found"
}
```

HTML Error (HTMX displays error in row):
```html
<tr><td colspan='5' class='error'>Item 'example01' not found</td></tr>
```

## Common Patterns and Conventions

### Logging

All endpoints follow this logging pattern:

```python
function_name = 'endpoint_name()'
request_data = log_function_header(function_name)
# ... endpoint logic ...
log_function_output(request_data, "Action description")
await log_function_footer(request_data)
```

### Error Handling

Standard error handling pattern:

```python
try:
  # Endpoint logic
except FileNotFoundError as e:
  # Handle 404 errors
  return generate_error_response(str(e), format, 404)
except ValueError as e:
  # Handle 400 validation errors
  return generate_error_response(str(e), format, 400)
except Exception as e:
  # Handle 500 server errors
  error_message = f"Error performing action: {str(e)}"
  log_function_output(request_data, f"ERROR: {error_message}")
  return generate_error_response(error_message, format, 500)
```

### Validation

Common validation checks:

1. **System Configuration:**
```python
if not hasattr(request.app.state, 'system_info') or not request.app.state.system_info:
  return generate_error_response("System configuration not available", format, 500)
```

2. **Required Parameters:**
```python
if not item_id:
  return generate_error_response("Missing required parameter: id", format, 400)
```

3. **Data Validation:**
```python
is_valid, error_msg = validate_item_data(data)
if not is_valid:
  return generate_error_response(error_msg, format, 400)
```

4. **Duplicate Check:**
```python
existing_items = load_all_items(storage_path, request_data)
if any(item.id == new_id for item in existing_items):
  return generate_error_response(f"Item '{new_id}' already exists", format, 409)
```

### Attribute Filtering

Endpoints support attribute filtering for READ operations:

```python
# Apply include/exclude filters
filtered_data = include_exclude_attributes(data_list, include_attributes, exclude_attributes)
```

**Usage:**
- `includeattributes=id,name,created_at` - Only include specified attributes
- `excludeattributes=metadata,internal_data` - Exclude specified attributes
- `includeattributes` takes precedence over `excludeattributes`

### HTMX Integration

UI format uses HTMX for dynamic interactions:

**Action Buttons:**
```html
<button class="btn-small btn-edit" 
        hx-get="/endpoint/update?id=example01&format=ui"
        hx-target="#form-container"
        hx-swap="innerHTML">
  Edit
</button>

<button class="btn-small btn-delete" 
        hx-delete="/endpoint/delete?id=example01&format=html"
        hx-confirm="Are you sure you want to delete this item?"
        hx-target="#item-example01"
        hx-swap="outerHTML">
  Delete
</button>
```

**Form Submission:**
```html
<form hx-post="/endpoint/create?format=html" 
      hx-target="#form-container"
      hx-swap="innerHTML">
  <!-- form fields -->
</form>
```

### HTTP Status Codes

Standard status codes used:

- **200 OK**: Successful GET, PUT, DELETE
- **201 Created**: Successful POST (not consistently used)
- **400 Bad Request**: Missing required parameters, validation errors
- **404 Not Found**: Resource not found
- **409 Conflict**: Duplicate resource (e.g., ID already exists)
- **500 Internal Server Error**: Unexpected errors, system configuration issues

### Response Helper Functions

Common helper functions for generating responses:

```python
# Error responses
generate_error_response(error_message: str, format: str, status_code: int)
generate_error_html(error_message: str)

# Success responses
generate_success_response(success_msg: str, format: str, data: dict = None, refresh: bool = False)

# UI generation
generate_ui_table_page(title: str, count: int, data: List[Dict], columns: List[Dict], row_id_field: str, row_id_prefix: str, back_link: str)
generate_nested_data_page(title: str, data: Union[List, Dict], back_link: str = None, back_text: str = None)
generate_documentation_page(endpoint: str, documentation: str)
```

## UI Components

### Column Definition for Tables

Tables in UI format use column definitions:

```python
columns = [
  {'field': 'id', 'header': 'ID'},
  {'field': 'name', 'header': 'Name'},
  {'field': 'created_at', 'header': 'Created At'},
  {'field': 'file_count', 'header': 'Files', 'format': format_file_count, 'default': 0},
  {'field': 'actions', 'header': 'Actions', 'buttons': get_action_buttons}
]
```

**Column Properties:**
- `field`: Data field name
- `header`: Column header text
- `format`: Optional formatter function
- `default`: Default value if field is missing
- `buttons`: Function that returns list of button definitions

### Button Definitions

Buttons are defined as dictionaries:

```python
def get_action_buttons(item):
  item_id = item.get('id', 'N/A')
  item_name = item.get('name', 'N/A')
  return [
    {
      'text': 'Edit',
      'onclick': f"window.location.href='/endpoint/update?id={item_id}&format=ui'",
      'button_class': 'btn-small btn-edit'
    },
    {
      'text': 'Delete',
      'hx_method': 'delete',
      'hx_endpoint': f'/endpoint/delete?id={item_id}',
      'hx_target': f'#item-{item_id}',
      'confirm_message': f"Delete item '{item_name}'?",
      'button_class': 'btn-small btn-delete',
      'style': 'background-color: #dc3545; color: white;'
    }
  ]
```

**Button Properties:**
- `text`: Button label
- `onclick`: JavaScript onclick handler (for navigation)
- `hx_method`: HTMX HTTP method (get, post, put, delete)
- `hx_endpoint`: HTMX target endpoint
- `hx_target`: HTMX target element selector
- `confirm_message`: Confirmation dialog message
- `button_class`: CSS class(es)
- `style`: Inline CSS styles

## Example: Complete CRUD Implementation

### Domain Management Endpoints

**List Domains:**
```
GET /domains?format=ui
```

**Create Domain:**
```
GET /domains/create?format=ui  (displays form)
POST /domains/create?format=html  (submits data)
```

**Update Domain:**
```
GET /domains/update?domain_id=example01&format=ui  (displays form)
PUT /domains/update?format=html  (submits data)
```

**Delete Domain:**
```
DELETE /domains/delete?domain_id=example01&format=html
```

### Vector Store Management Endpoints

**List Vector Stores:**
```
GET /inventory/vectorstores?format=ui
```

**Delete Vector Store:**
```
DELETE /inventory/vectorstores/delete?vector_store_id=vs_123&delete_files=false&format=html
```

**List Files in Vector Store:**
```
GET /inventory/vectorstore_files?vector_store_id=vs_123&format=ui
```

**Remove File from Vector Store:**
```
DELETE /inventory/vectorstore_files/remove?vector_store_id=vs_123&file_id=file_456&format=html
```

**Delete File from Vector Store and Storage:**
```
DELETE /inventory/vectorstore_files/delete?vector_store_id=vs_123&file_id=file_456&format=html
```

## Best Practices

1. **Always log function entry and exit** using `log_function_header()` and `log_function_footer()`

2. **Display documentation when no parameters provided** to help users understand endpoint usage

3. **Validate all required parameters** before processing

4. **Use appropriate HTTP status codes** for different error conditions

5. **Support multiple response formats** (json, html, ui) for flexibility

6. **Apply attribute filtering** for READ operations to reduce payload size

7. **Use HTMX for interactive UI** to avoid full page reloads

8. **Provide confirmation dialogs** for destructive operations (delete)

9. **Return empty HTML response for successful deletes** to trigger HTMX row removal

10. **Include back navigation links** in all HTML/UI responses

11. **Use consistent naming conventions** for endpoints and parameters

12. **Handle both GET and DELETE methods** for delete endpoints (GET for documentation)

13. **Separate form display (GET) from form submission (POST/PUT)** for create/update operations

14. **Use Form(...) for required fields** and Form(default="") for optional fields in FastAPI

15. **Convert dataclasses to dicts** before applying attribute filtering or returning JSON responses
