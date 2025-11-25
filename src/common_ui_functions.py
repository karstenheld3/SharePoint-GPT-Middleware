"""
Common UI functions for generating HTML responses across different routers.
Provides reusable components for building consistent HTMX-enabled pages.

See COMMON_UI_FUNCTIONS.md for comprehensive documentation with examples.
"""
from typing import Any, Dict, List, Optional

from fastapi.responses import HTMLResponse, JSONResponse
from utils import convert_to_nested_html_table

TAB = "  "
TEXT_BACK_TO_MAIN_PAGE = "← Back to Main Page"

def generate_html_head(title: str, additional_scripts: str = "", additional_styles: str = "") -> str:
  """
  Generate standard HTML head section with common resources.
  
  Args:
    title: Page title (e.g., 'Files')
    additional_scripts: Optional JavaScript code to include
    additional_styles: Optional CSS code to include
    
  Returns:
    HTML head section. Example output:
      <!DOCTYPE html><html><head><meta charset='utf-8'>
        <title>[title]</title>
        [... scripts and styles added by generate_html_head ...]
      </head>
  """
  scripts_section = f"\n{TAB}<script>\n{additional_scripts}\n{TAB}</script>" if additional_scripts else ""
  styles_section = f"\n{TAB}<style>\n{additional_styles}\n{TAB}</style>" if additional_styles else ""
  
  return f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
{TAB}<title>{title}</title>
{TAB}<link rel='stylesheet' href='/static/css/styles.css'>
{TAB}<script src='/static/js/htmx.js'></script>{scripts_section}{styles_section}
</head>"""

# Generate JavaScript for updating dynamic item counts (items have to be counted before removal so that item count is correct afterwards)
def generate_update_count_script() -> str:
  return """    function updateCount() {
    const rows = document.querySelectorAll('tbody tr:not(.empty-row)');
    const countElement = document.getElementById('item-count');
    if (countElement) {
      countElement.textContent = rows.length;
    }
  }"""

def generate_simple_page(title: str, html_content: str, body_attributes: str = "") -> str:
  """
  Generate simple HTML page with title and content.
  
  Args:
    title: Page title (e.g., 'Error')
    html_content: HTML content to display (e.g., '<p>Page not found</p>')
    body_attributes: Optional HTML attributes for body tag (e.g., 'class="error-page"')
    
  Returns:
    Complete HTML page string. Example output:
      <!DOCTYPE html><html><head><meta charset='utf-8'>
        <title>[title]</title>
        [... scripts and styles added by generate_html_head ...]
      </head>
      <body>
        [html_content]
      </body>
      </html>
  """
  head = generate_html_head(title)
  body_tag = f"<body {body_attributes}>" if body_attributes else "<body>"
  
  return f"""{head}
{body_tag}
{TAB}{html_content}
</body>
</html>"""

# Generate documentation page from endpoint docstring
def generate_documentation_page(endpoint: str, docstring: str) -> str:
  return generate_simple_page(title=f"{endpoint} - Documentation", html_content=f"<pre>{docstring}</pre>")

def generate_page_with_container(title: str, html_content: str, back_link: Optional[str] = None, back_text: str = TEXT_BACK_TO_MAIN_PAGE, body_attributes: str = "", additional_scripts: str = "", additional_styles: str = "") -> str:
  """
  Generate HTML page with container div and optional back link.
  
  Args:
    title: Page title (e.g., 'Settings')
    html_content: HTML content to display (e.g., '<form>...</form>')
    back_link: Optional URL for back link (e.g., '/')
    back_text: Text for back link (default: TEXT_BACK_TO_MAIN_PAGE)
    body_attributes: HTML attributes for body tag (e.g., 'hx-boost="true"')
    additional_scripts: JavaScript code to include
    additional_styles: CSS code to include
    
  Returns:
    Complete HTML page string. Example output:
      <!DOCTYPE html><html><head>
        <title>[title]</title>
        [... scripts and styles added by generate_html_head ...]
      </head>
      <body>
        <div class="container">
          <h1>[title]</h1>
          <p><a href='[back_link]'>[back_text]</a></p>
          [html_content]
        </div>
      </body>
      </html>
  """
  head = generate_html_head(title, additional_scripts, additional_styles)
  body_tag = f"<body {body_attributes}>" if body_attributes else "<body>"
  back_link_html = f"<p><a href='{back_link}'>{back_text}</a></p>\n{TAB}" if back_link else ""
  
  return f"""{head}
{body_tag}
{TAB}<div class="container">
{TAB}<h1>{title}</h1>
{TAB}{back_link_html}{html_content}
{TAB}</div>
</body>
</html>"""

def generate_table_page(title: str, count: int, table_html: str, back_link: Optional[str] = None, toolbar_html: str = "", dynamic_count: bool = False, additional_content: str = "") -> str:
  """
  Generate HTML page with table and optional toolbar.
  
  Args:
    title: Page title (e.g., 'Files')
    count: Number of items in table (e.g., 42)
    table_html: HTML table content (e.g., '<table>...</table>')
    back_link: Optional URL for back link (e.g., '/')
    toolbar_html: HTML for toolbar section (e.g., '<button>Add</button>')
    dynamic_count: Enable dynamic count updates via HTMX (e.g., True)
    additional_content: Additional HTML content after table (e.g., '<p>Footer text</p>')
    
  Returns:
    Complete HTML page string with table. Example output:
      <!DOCTYPE html><html><head>
        <title>[title] ([count])</title>
        [... scripts and styles added by generate_html_head ...]
      </head>
      <body hx-on::after-swap="updateCount()">
        <div class="container">
          <h1>[title] (<span id='item-count'>[count]</span>)</h1>
          <p><a href='[back_link]'>[back_text or TEXT_BACK_TO_MAIN_PAGE]</a></p>
          [toolbar_html]
          [table_html]
          [additional_content]
        </div>
      </body>
      </html>
  """
  count_display = f"<span id='item-count'>{count}</span>" if dynamic_count else str(count)
  back_link_html = f"<p><a href='{back_link}'>{TEXT_BACK_TO_MAIN_PAGE}</a></p>\n{TAB}" if back_link else ""
  toolbar_section = f"{toolbar_html}\n{TAB}" if toolbar_html else ""
  additional_section = f"\n{TAB}{additional_content}" if additional_content else ""
  
  scripts = generate_update_count_script() if dynamic_count else ""
  body_attributes = 'hx-on::after-swap="updateCount()"' if dynamic_count else ""
  
  head = generate_html_head(f"{title} ({count_display})", scripts)
  body_tag = f"<body {body_attributes}>" if body_attributes else "<body>"
  
  return f"""{head}
{body_tag}
{TAB}<div class="container">
{TAB}<h1>{title} ({count_display})</h1>
{TAB}{back_link_html}{toolbar_section}{table_html}{additional_section}
{TAB}</div>
</body>
</html>"""

def generate_table_with_headers(headers: List[str], rows_html: str, empty_message: str = "No items found") -> str:
  """
  Generate HTML table with headers and rows.
  
  Args:
    headers: List of column header texts (e.g., ['Name', 'Size', 'Actions'])
    rows_html: HTML string containing table rows (e.g., '<tr><td>file.txt</td><td>1024</td></tr>')
    empty_message: Message to display when no rows provided (e.g., 'No files found')
    
  Returns:
    HTML table element. Example output:
      <table>
        <thead>
        <tr>
          <th>Name</th>
          <th>Size</th>
          <th>Actions</th>
        </tr>
        </thead>
        <tbody>
        [rows_html or empty row with colspan]
        </tbody>
      </table>
  """
  header_cells = f"\n{TAB*3}".join([f"<th>{header}</th>" for header in headers])
  colspan = len(headers)
  rows_content = rows_html if rows_html else f'<tr class="empty-row"><td colspan="{colspan}">{empty_message}</td></tr>'
  
  return f"""<table>
{TAB*2}<thead>
{TAB*2}<tr>
{TAB*3}{header_cells}
{TAB*2}</tr>
{TAB*2}</thead>
{TAB*2}<tbody>
{TAB*2}{rows_content}
{TAB*2}</tbody>
{TAB}</table>"""

# Generate error page HTML
def generate_error_html(error_message: str, title: str = "Error") -> str:
  return f"""<!DOCTYPE html><html><head><meta charset='utf-8'><title>{title}</title></head><body><h1>{title}</h1><p>{error_message}</p></body></html>"""

# Generate error div for inline display
def generate_error_div(error_message: str) -> str:
  return f"<div class='error' style='padding: 15px; margin: 10px 0; background-color: #fee; border: 1px solid #fcc; border-radius: 4px; color: #c00;'><strong>Error:</strong> {error_message}</div>"

# Generate success div for inline display
def generate_success_div(message: str) -> str:
  return f"<div class='success'>{message}</div>"

def generate_modal_dialog_div(title: str, html_content: str, modal_id: str = "modal", max_width: str = "600px") -> str:
  """
  Generate modal dialog HTML container.
  
  Args:
    title: Modal title (e.g., 'Confirm Action')
    html_content: HTML content to display in modal body (e.g., '<p>Are you sure?</p>')
    modal_id: HTML id attribute for the modal (e.g., 'confirm-modal')
    max_width: Maximum width of modal content (e.g., '600px')
    
  Returns:
    HTML div element for modal. Example output:
      <div class="modal" id="modal">
        <div class="modal-content" style="max-width: 600px;">
          <h2>[title]</h2>
          [html_content]
        </div>
      </div>
  """
  return f"""<div class="modal" id="{modal_id}">
{TAB*2}<div class="modal-content" style="max-width: {max_width};">
{TAB*3}<h2>{title}</h2>
{TAB*3}{html_content}
{TAB*2}</div>
{TAB}</div>"""

# Generate HTMX toolbar button
def generate_toolbar_button(text: str, hx_get: str, hx_target: str, hx_swap: str = "innerHTML", button_class: str = "btn-primary") -> str:
  return f"""<button class="{button_class}" 
{TAB*4}hx-get="{hx_get}"
{TAB*4}hx-target="{hx_target}"
{TAB*4}hx-swap="{hx_swap}">
{TAB*2}{text}
{TAB*2}</button>"""

def generate_action_button(text: str, hx_method: str, hx_endpoint: str, hx_target: str, hx_swap: str = "outerHTML", confirm_message: Optional[str] = None, button_class: str = "btn-small", additional_attrs: str = "") -> str:
  """
  Generate HTMX action button (edit, delete, etc.).
  
  Args:
    text: Button text
    hx_method: HTTP method (get, post, delete, etc.)
    hx_endpoint: Endpoint URL
    hx_target: HTMX target selector
    hx_swap: HTMX swap strategy
    confirm_message: Optional confirmation message
    button_class: CSS class for button
    additional_attrs: Additional HTML attributes
    
  Returns:
    HTML button element
  """
  confirm_attr = f'\n{TAB*4}hx-confirm="{confirm_message}"' if confirm_message else ""
  attrs = f" {additional_attrs}" if additional_attrs else ""
  return f"""<button class="{button_class}" 
{TAB*4}hx-{hx_method}="{hx_endpoint}"{confirm_attr}
{TAB*4}hx-target="{hx_target}"
{TAB*4}hx-swap="{hx_swap}"{attrs}>
{TAB*3}{text}
{TAB*2}</button>"""


# Generate HTML page with nested table for complex data structures
def generate_nested_data_page(title: str, data: Any, back_link: Optional[str] = None, back_text: str = "← Back") -> str:
  table_html = convert_to_nested_html_table(data)
  back_link_html = f"<p><a href='{back_link}'>{back_text}</a></p>\n{TAB}" if back_link else ""
  head = generate_html_head(title)
  return f"""{head}
<body>
{TAB}<div class="container">
{TAB}<h1>{title}</h1>
{TAB}{back_link_html}{table_html}
{TAB}</div>
</body>
</html>"""

# Generate HTTP error response in requested format ('json' | 'html')
def generate_error_response(error_message: str, response_format: str, status_code: int = 400):
  if response_format == 'json': return JSONResponse({"error": error_message}, status_code=status_code)
  else: return HTMLResponse(generate_error_div(error_message), status_code=status_code)

# Generate HTTP success response in requested format ('json' | 'html')
def generate_success_response(message: str, response_format: str, data: Optional[Dict[str, Any]] = None, refresh: bool = False):
  if response_format == 'json':
    response = {"message": message}
    if data: response["data"] = data
    return JSONResponse(response)
  headers = {"HX-Refresh": "true"} if refresh else {}
  html_content = f"<div class='success'>{message}{' Reloading...' if refresh else ''}</div>"
  return HTMLResponse(html_content, headers=headers)

def generate_action_buttons_column(buttons: List[Dict[str, Any]]) -> str:
  """
  Generate HTML for action buttons column in a table.
  
  Args:
    buttons: List of button configurations. Example:
      [
        {
          'text': 'Delete',
          'hx_method': 'delete',
          'hx_endpoint': '/files/file-123',
          'hx_target': '#file-123',
          'hx_swap': 'outerHTML',
          'confirm_message': 'Are you sure you want to delete this file?',
          'button_class': 'btn-small btn-delete',
          'style': 'background-color: red;'
        },
        {
          'text': 'Edit',
          'hx_method': 'get',
          'hx_endpoint': '/files/file-123/edit',
          'hx_target': '#file-123',
          'button_class': 'btn-small btn-edit'
        }
      ]
      Each button config can have:
        - text: Button text (default: 'Action')
        - hx_method: HTTP method - 'get', 'post', 'delete', etc. (default: 'get')
        - hx_endpoint: Endpoint URL (default: '')
        - hx_target: HTMX target selector (default: '')
        - hx_swap: HTMX swap strategy (default: 'outerHTML')
        - confirm_message: Optional confirmation dialog message
        - button_class: CSS class (default: 'btn-small')
        - style: Optional inline CSS style
        - onclick: Optional onclick handler (if set, HTMX attributes are ignored)
      
  Returns:
    HTML string for table cell with action buttons. Example output:
      <td class="actions">
        <button class="btn-small btn-delete" hx-delete="/files/file-123" hx-confirm="Are you sure?" hx-target="#file-123" hx-swap="outerHTML">Delete</button>
        <button class="btn-small btn-edit" hx-get="/files/file-123/edit" hx-target="#file-123" hx-swap="outerHTML">Edit</button>
      </td>
  """
  buttons_html = ""
  for btn in buttons:
    hx_method = btn.get('hx_method', 'get')
    hx_endpoint = btn.get('hx_endpoint', '')
    hx_target = btn.get('hx_target', '')
    hx_swap = btn.get('hx_swap', 'outerHTML')
    confirm_msg = btn.get('confirm_message')
    btn_class = btn.get('button_class', 'btn-small')
    btn_style = btn.get('style', '')
    btn_text = btn.get('text', 'Action')
    onclick = btn.get('onclick')
    
    confirm_attr = f' hx-confirm="{confirm_msg}"' if confirm_msg else ''
    style_attr = f' style="{btn_style}"' if btn_style else ''
    
    if onclick:
      buttons_html += f'<button class="{btn_class}" onclick="{onclick}"{style_attr}>{btn_text}</button>\n{TAB*3}'
    else:
      buttons_html += f'<button class="{btn_class}" hx-{hx_method}="{hx_endpoint}"{confirm_attr} hx-target="{hx_target}" hx-swap="{hx_swap}"{style_attr}>{btn_text}</button>\n{TAB*3}'
  
  return f'<td class="actions">\n{TAB*3}{buttons_html}</td>'

def generate_table_rows_with_actions(data: List[Dict[str, Any]], columns: List[Dict[str, Any]], row_id_field: str, row_id_prefix: str = "row") -> str:
  """
  Generate table rows from data with action buttons.
  
  Args:
    data: List of data dictionaries. Example:
      [
        {'id': 'file-123', 'filename': 'document.pdf', 'size': 1024},
        {'id': 'file-456', 'filename': 'report.docx', 'size': 2048}
      ]
    columns: List of column configurations. Example:
      [
        {'field': 'filename', 'header': 'Filename'},
        {'field': 'size', 'header': 'Size', 'format': lambda x: f'{x} bytes', 'default': 0},
        {'field': 'actions', 'header': 'Actions', 'buttons': lambda item: [
          {'text': 'Delete', 'hx_method': 'delete', 'hx_endpoint': f'/files/{item["id"]}', 
           'hx_target': f'#file-{item["id"]}', 'confirm_message': 'Are you sure?'}
        ]}
      ]
      Each column config can have:
        - field: Field name in data dict (or 'actions' for action column)
        - header: Column header text (only used by generate_ui_table_page)
        - format: Optional formatting function
        - default: Default value if field is missing
        - buttons: Function or list that returns button configurations (for 'actions' field)
    row_id_field: Field name to use for row ID (e.g., 'id')
    row_id_prefix: Prefix for row ID attribute (e.g., 'file' produces 'file-123')
    
  Returns:
    HTML string with table rows. Example output:
      <tr id="[row_id_prefix]-[row_id]">
        <td>[value]</td>
        <td>[value]</td>
        <td class="actions">
          <button class="btn-small" hx-delete="/endpoint?id=[row_id]" hx-target="#[row_id_prefix]-[row_id]" hx-swap="outerHTML">Delete</button>
        </td>
      </tr>
  """
  rows_html = ""
  for item in data:
    row_id = item.get(row_id_field, 'unknown')
    rows_html += f'<tr id="{row_id_prefix}-{row_id}">\n{TAB*2}'
    
    for col in columns:
      field = col.get('field')
      if field == 'actions':
        buttons = col.get('buttons', [])
        if callable(buttons): buttons = buttons(item)
        rows_html += generate_action_buttons_column(buttons)
      else:
        value = item.get(field, col.get('default', 'N/A'))
        format_fn = col.get('format')
        if format_fn and callable(format_fn): value = format_fn(value)
        rows_html += f'<td>{value}</td>\n{TAB*2}'
    
    rows_html += f'</tr>\n{TAB*2}'
  
  return rows_html

def generate_ui_table_page(title: str, count: int, data: List[Dict[str, Any]], columns: List[Dict[str, Any]], row_id_field: str, row_id_prefix: str = "row", back_link: Optional[str] = None, back_text: str = TEXT_BACK_TO_MAIN_PAGE, toolbar_html: str = "") -> str:
  """
  Generate complete HTML page with table and action buttons.
  
  Args:
    title: Page title (e.g., 'Files')
    count: Number of items (e.g., 42)
    data: List of data dictionaries. Example: [{'id': 'file-123', 'filename': 'document.pdf', 'size': 1024}]
    columns: List of column configurations. Example: [{'field': 'filename', 'header': 'Filename'}, {'field': 'size', 'header': 'Size'}, {'field': 'actions', 'header': 'Actions', 'buttons': lambda item: [{'text': 'Delete', 'hx_method': 'delete', 'hx_endpoint': f'/files/{item["id"]}', 'hx_target': f'#file-{item["id"]}'}]}]
    row_id_field: Field name to use for row ID (e.g., 'id')
    row_id_prefix: Prefix for row ID attribute (e.g., 'file' produces 'file-123')
    back_link: Optional URL for back link (e.g., '/')
    back_text: Text for back link (default: TEXT_BACK_TO_MAIN_PAGE)
    toolbar_html: HTML for toolbar section (e.g., '<button>Refresh</button>')
    
  Returns:
    Complete HTML page string. Example output:
      <!DOCTYPE html><html><head>
        <title>[title] ([count])</title>
        [... scripts and styles added by generate_html_head ...]
      </head>
      <body hx-on::after-swap="updateCount()">
        <div class="container">
          <h1>[title] (<span id='item-count'>[count]</span>)</h1>
          <p><a href='[back_link]'>[back_text]</a></p>
          [toolbar_html]
          <table>
            <thead>
              <tr>
                <th>[header]</th>
                <th>[header]</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr id="[row_id_prefix]-[row_id]">
                <td>[value]</td>
                <td>[value]</td>
                <td class="actions">
                  <button class="btn-small" hx-delete="/endpoint?id=[row_id]" hx-target="#[row_id_prefix]-[row_id]" hx-swap="outerHTML">Delete</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </body>
      </html>
  """
  headers = [col.get('header', col.get('field', '')) for col in columns]
  rows_html = generate_table_rows_with_actions(data, columns, row_id_field, row_id_prefix)
  table_html = generate_table_with_headers(headers, rows_html, "No items found")
  
  page_html = generate_table_page(title=title, count=count, table_html=table_html, back_link=back_link, toolbar_html=toolbar_html, dynamic_count=True)
  if back_text != TEXT_BACK_TO_MAIN_PAGE: page_html = page_html.replace(TEXT_BACK_TO_MAIN_PAGE, back_text)
  return page_html
