# Common UI Functions Documentation

This document describes the reusable UI functions in `src/common_ui_functions.py` for generating HTML responses across different routers.

## Function Hierarchy

```
Level 0 - Constants
├── TAB                          - Indentation constant ("  ")
└── TEXT_BACK_TO_MAIN_PAGE       - Default back link text

Level 1 - Atomic Components (no internal dependencies)
├── generate_update_count_script()   - JavaScript for dynamic item count updates
├── generate_error_div()             - Inline error message div with styling
├── generate_success_div()           - Inline success message div
├── generate_modal_dialog_div()      - Modal dialog container div
├── generate_toolbar_button()        - HTMX-enabled toolbar button
├── generate_action_button()         - HTMX action button (edit, delete, etc.)
└── generate_error_html()            - Standalone error page (minimal)

Level 2 - Basic Builders
├── generate_html_head()             - HTML head with CSS/JS resources
└── generate_action_buttons_column() - Table cell with multiple action buttons

Level 3 - Simple Pages
├── generate_simple_page()           - Basic HTML page with title and content
│   └── generate_html_head()
├── generate_table_with_headers()    - HTML table with thead/tbody structure
└── generate_documentation_page()    - Documentation page from endpoint docstring
    └── generate_simple_page()

Level 4 - Intermediate Components
└── generate_table_rows_with_actions() - Table rows with data and action buttons
    └── generate_action_buttons_column()

Level 5 - Container Pages
├── generate_page_with_container()   - Page with container div and optional back link
│   └── generate_html_head()
├── generate_table_page()            - Page with table, toolbar, and dynamic count
│   ├── generate_html_head()
│   └── generate_update_count_script() [conditional]
└── generate_nested_data_page()      - Page with nested table for complex data
    ├── generate_html_head()
    └── convert_to_nested_html_table() [external from utils]

Level 6 - High-Level Pages
└── generate_ui_table_page()         - Complete interactive table page with actions
    ├── generate_table_rows_with_actions()
    ├── generate_table_with_headers()
    └── generate_table_page()

Level 7 - Response Wrappers (FastAPI responses)
├── generate_error_response()        - HTTP error response (JSON or HTML)
│   └── generate_error_div() [for HTML format]
└── generate_success_response()      - HTTP success response (JSON or HTML)
```

---

## Router Usage Summary

| Function | inventory.py | domains.py | crawler.py |
|----------|:------------:|:----------:|:----------:|
| `generate_html_head()` | ✅ | ✅ | - |
| `generate_simple_page()` | ✅ | - | - |
| `generate_table_page()` | ✅ | ✅ | - |
| `generate_table_with_headers()` | ✅ | ✅ | - |
| `generate_update_count_script()` | ✅ | - | - |
| `generate_ui_table_page()` | ✅ | - | ✅ |
| `generate_error_html()` | - | ✅ | ✅ |
| `generate_error_response()` | - | ✅ | - |
| `generate_success_response()` | - | ✅ | - |
| `generate_toolbar_button()` | - | ✅ | ✅ |
| `generate_nested_data_page()` | - | ✅ | ✅ |
| `generate_documentation_page()` | - | ✅ | ✅ |

---

## Function Reference

### Constants

```python
TAB = "  "                                    # Indentation constant
TEXT_BACK_TO_MAIN_PAGE = "← Back to Main Page"  # Default back link text
```

### Level 1 - Atomic Components

#### `generate_error_html(error_message, title="Error")`
Standalone error page HTML. Used for simple error responses.

```python
# Example from crawler.py
return HTMLResponse(generate_error_html("PERSISTENT_STORAGE_PATH not configured"), status_code=500)
```

#### `generate_error_div(error_message)`
Inline error div with styling. Used by `generate_error_response()`.

#### `generate_success_div(message)`
Inline success div. Used for inline success messages.

#### `generate_toolbar_button(text, hx_get, hx_target, hx_swap="innerHTML", button_class="btn-primary")`
HTMX-enabled toolbar button.

```python
# Example from domains.py
generate_toolbar_button('+ Add New Domain', '/domains/create?format=ui', '#form-container')
```

### Level 2 - Basic Builders

#### `generate_html_head(title, additional_scripts="", additional_styles="")`
Standard HTML head section with CSS/JS resources.

```python
# Example from inventory.py
head = generate_html_head(f"{title} ({count})")

# Example from domains.py with scripts
head = generate_html_head("Domains", additional_scripts)
```

#### `generate_action_buttons_column(buttons: List[Dict])`
Table cell with multiple action buttons. Button config options:

```python
{
  'text': 'Delete',              # Button text
  'hx_method': 'delete',         # HTTP method (get, post, delete, put)
  'hx_endpoint': '/files/123',   # Endpoint URL
  'hx_target': '#file-123',      # HTMX target selector
  'hx_swap': 'outerHTML',        # HTMX swap strategy
  'confirm_message': 'Sure?',    # Optional confirmation dialog
  'button_class': 'btn-delete',  # CSS class
  'style': 'color: red;',        # Optional inline CSS
  'onclick': 'handleClick()'     # Optional onclick (disables HTMX)
}
```

### Level 3 - Simple Pages

#### `generate_simple_page(title, html_content, body_attributes="")`
Basic HTML page with title and content.

#### `generate_table_with_headers(headers, rows_html, empty_message="No items found")`
HTML table with thead/tbody structure.

```python
# Example from domains.py
headers = ['Domain ID', 'Name', 'Vector Store Name', 'Vector Store ID', 'Actions']
table_html = generate_table_with_headers(headers, table_rows, "No domains found")
```

#### `generate_documentation_page(endpoint, docstring)`
Documentation page from endpoint docstring.

```python
# Example from domains.py
return HTMLResponse(generate_documentation_page('/domains', list_domains.__doc__))
```

### Level 4 - Intermediate Components

#### `generate_table_rows_with_actions(data, columns, row_id_field, row_id_prefix="row")`
Table rows with data and action buttons. Column config options:

```python
{
  'field': 'filename',           # Field name in data dict
  'header': 'Filename',          # Column header text
  'format': lambda x: f'{x}KB',  # Optional formatting function
  'default': 'N/A',              # Default value if field missing
  'buttons': get_actions_fn      # Function for action buttons (field='actions')
}
```

### Level 5 - Container Pages

#### `generate_page_with_container(title, html_content, back_link=None, back_text=TEXT_BACK_TO_MAIN_PAGE, ...)`
Page with container div and optional back link.

#### `generate_table_page(title, count, table_html, back_link=None, toolbar_html="", dynamic_count=False, additional_content="")`
Page with table and optional toolbar. When `dynamic_count=True`, includes JavaScript for updating count after HTMX swaps.

#### `generate_nested_data_page(title, data, back_link=None, back_text="← Back")`
Page with nested table for complex data structures.

```python
# Example from crawler.py
html_content = generate_nested_data_page(
  title=f"Local Storage Contents - {storage_path}",
  storage_contents,
  back_link="/crawler?format=ui",
  back_text="← Back to Crawler"
)
```

### Level 6 - High-Level Pages

#### `generate_ui_table_page(title, count, data, columns, row_id_field, row_id_prefix="row", back_link=None, back_text=TEXT_BACK_TO_MAIN_PAGE, toolbar_html="")`
Complete interactive table page with HTMX actions.

```python
# Example from inventory.py
def get_vectorstore_actions(vs):
  vs_id = vs.get('id')
  return [
    {'text': 'Files', 'onclick': f"window.location.href='/inventory/vectorstore_files?vector_store_id={vs_id}&format=ui'",
     'button_class': 'btn-small', 'style': 'background-color: #007bff; color: white;'},
    {'text': 'Delete', 'hx_method': 'delete',
     'hx_endpoint': f'/inventory/vectorstores/delete?vector_store_id={vs_id}',
     'hx_target': f'#vectorstore-{vs_id}',
     'confirm_message': f"Delete vector store?",
     'button_class': 'btn-small btn-delete'}
  ]

columns = [
  {'field': 'name', 'header': 'Name'},
  {'field': 'id', 'header': 'ID'},
  {'field': 'created_at', 'header': 'Created At'},
  {'field': 'file_counts', 'header': 'Files', 'format': lambda x: x.get('total', 0)},
  {'field': 'actions', 'header': 'Actions', 'buttons': get_vectorstore_actions}
]

return generate_ui_table_page(title='Vector Stores', count=len(data), data=data,
  columns=columns, row_id_field='id', row_id_prefix='vectorstore', back_link='/')
```

### Level 7 - Response Wrappers

#### `generate_error_response(error_message, response_format, status_code=400)`
HTTP error response in JSON or HTML format.

```python
# Example from domains.py
return generate_error_response("Missing domain_id parameter", format, 400)
return generate_error_response("Domain not found", format, 404)
return generate_error_response("Server error", format, 500)
```

#### `generate_success_response(message, response_format, data=None, refresh=False)`
HTTP success response in JSON or HTML format.

```python
# Example from domains.py
return generate_success_response(
  f"Domain '{name}' created successfully!",
  format,
  data=domain_config_to_dict(domain_config),
  refresh=(format != 'json')
)
```

---

## Implementation Patterns

### Pattern 1: Interactive Table UI (format=ui)

```python
def get_item_actions(item):
  return [
    {'text': 'Edit', 'hx_method': 'get', 'hx_endpoint': f'/items/{item["id"]}/edit',
     'hx_target': '#form-container', 'button_class': 'btn-small btn-edit'},
    {'text': 'Delete', 'hx_method': 'delete', 'hx_endpoint': f'/items/{item["id"]}',
     'hx_target': f'#item-{item["id"]}', 'confirm_message': 'Delete?',
     'button_class': 'btn-small btn-delete'}
  ]

columns = [
  {'field': 'name', 'header': 'Name'},
  {'field': 'size', 'header': 'Size', 'format': lambda x: f'{x/1024:.1f}KB'},
  {'field': 'actions', 'header': 'Actions', 'buttons': get_item_actions}
]

html = generate_ui_table_page(title='Items', count=len(items), data=items,
  columns=columns, row_id_field='id', row_id_prefix='item', back_link='/')
```

### Pattern 2: Documentation Endpoint

```python
@router.get('/myendpoint')
async def my_endpoint(request: Request):
  """
  Endpoint description.
  
  Parameters:
  - param1: Description
  
  Examples:
  /myendpoint?param1=value
  """
  request_params = dict(request.query_params)
  if len(request_params) == 0:
    return HTMLResponse(generate_documentation_page('/myendpoint', my_endpoint.__doc__))
  # ... handle request
```

### Pattern 3: Error/Success Handling

```python
@router.post('/items/create')
async def create_item(request: Request):
  format = request.query_params.get('format', 'json')
  
  if not valid:
    return generate_error_response("Validation failed", format, 400)
  
  try:
    # ... operation
  except Exception as e:
    return generate_error_response(f"Error: {str(e)}", format, 500)
  
  return generate_success_response("Created!", format, data=item_dict, refresh=True)
```

---

## CSS Classes

| Class | Purpose |
|-------|---------|
| `.container` | Main content container |
| `.toolbar` | Toolbar section |
| `.btn-primary` | Primary action button |
| `.btn-small` | Small inline button |
| `.btn-edit` | Edit action button |
| `.btn-delete` | Delete action button |
| `.error` | Error message styling |
| `.success` | Success message styling |
| `.modal` | Modal overlay |
| `.actions` | Table cell for action buttons |

## Related Files

- **Source:** `src/common_ui_functions.py`
- **Styles:** `src/static/css/styles.css`
- **Scripts:** `src/static/js/htmx.js`
- **Routers:** `src/routers/inventory.py`, `src/routers/domains.py`, `src/routers/crawler.py`
