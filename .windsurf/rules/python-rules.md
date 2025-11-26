---
trigger: manual
---

## Definitions
- MAX_LINE_CHARS = 220
- TAB = "  " (2 spaces)

## Code formatting

- Indent code with TAB.
- If a statement is ≤ MAX_LINE_CHARS characters (including spaces), keep it on a single line.
- Function definitions: put the full signature on a single line; function body starts on the next line.
- One empty line as delimiter between imports, functions and class definitions

## Imports

- All imports at the top of the file.
- One import statement per line (even if longer than MAX_LINE_CHARS).
- No local imports inside functions.
- Group imports: standard library first, then third-party libraries, then internal modules.
- Prefer importing all needed names from a module in a single line.

## Code generation principles

- Do not rename existing symbols unless explicitly asked.
- Analyze the existing codebase before creating new code. Re-use existing implementation patterns, naming patterns, code formatting, design philosphy, logging style and functions.
- Before implementiong new helper functions, make sure no alternatives exist in the code base.
- Principle of Least Surprise: prefer simple, idiomatic Python over clever or magical code.
- Use clear, fully written names; follow existing naming patterns; avoid ambiguous abbreviations.
- Optimize for readability and maintainability, not micro-optimizations.
- Concise is good, but not at the expense of clarity: multiple simple statements can share a line if they are one clear intention.
- Avoid `lambda`, `map`, `filter`, `reduce` and similar helpers for control flow; use explicit `for` loops. Exception: string / list joins.
- Prefer standard library over third-party packages; add dependencies only if a helper function would be unreasonably complex.
- No emojis in the code or logging. UI may occasionally use ✅=OK, ❌=FAIL, ⚠️=WARNING

## Code documentation principles

- Avoid comments that restate obvious code; comment intent, edge cases, and non-obvious behavior.
- Docstrings:
  - No docstrings for small, single-purpose functions with self-explanatory names and arguments.
  - Use a single comment above such functions if intent or types need clarification.
  - Use docstrings for FastAPI endpoints and complex functions (more than 5 arguments, multiple responsibilities, or complex/structured return types), and include example outputs.
- For documentation or UI output, avoid "typographic quotes" and use typewriter / ASCII "double quotes" or 'single quotes'
- When creating hierarchies and maps, use "└─" for indenting

## Logging

- Indent sub-actions with 2 spaces.
- Log the action description before executing it.
- Do not use emojis in logs. Exception: 
- Put status keywords on a separate, indented line: `OK`, `ERROR`, `FAIL`, `WARNING`.
- Surround file paths, names and IDs with single quotes `'...'`.
- For iterations, prefix lines with `[ x / n ]`.
- For retries, use `( x / n )` inline where `x` is current retry and `n` is max retries.

## Examples

### Write single intentions on single line even if the line gets very long
- apply only to single-statement conditionals
*BAD*:
```
content_page = client.vector_stores.files.content(
  vector_store_id=vector_store_id,
  file_id=file_id
)
```
*GOOD*:
```
content_page = client.vector_stores.files.content(vector_store_id=vector_store_id, file_id=file_id)
```
*BAD*:
```
if not vector_store_id:
  raise ValueError(f"Expected a non-empty value for 'vector_store_id' but received {vector_store_id!r}")
```
*GOOD*:
```
if not vector_store_id: raise ValueError(f"Expected a non-empty value for 'vector_store_id' but received {vector_store_id!r}")
```

### Console and internal log formatting
- Indent subactions with 2 spaces
- Put OK / ERROR / FAIL / WARNING on indented separate lines
- `OK` = action succeeded. `ERROR` = intermediate or final error occurred. `FAIL` = action failed even after error mitigation. `WARNING` = intermediate error that will be mitigated
- Put file paths, names and IDs in single quotes
- Log action / subaction description before executing action
- For iterations, ùse `[ x / n ]` format at the beginning of a line where x = current item number, n = total items.
- For retries use `( x / n )` inline where x = current retry, n = max retries.

*BAD*:
```
Uploading item 1/2 Example.docx to vs_62573645276345
SUCCESS: Verified uploaded file.
Uploading item 1/2 Test.docx to vs_62573645276345
ERROR: BlockingIOError: [Errno 11] Resource temporarily unavailable
```
*GOOD*:
```
[ 1 / 2 ] Uploading file 'C:\Example.docx' to vector store ID='vs_62573645276345'...
  Verifying uploaded file ID='file_923748237'...
  OK.
[ 2 / 2 ] Uploading file 'C:\Test.docx' to vector store ID='vs_62573645276345'...
  WARNING: File could not be opened. Maybe it's locked. -> BlockingIOError: [Errno 11] Resource temporarily unavailable
  Waiting 5 seconds ( 1 / 2 ) for retry...
  Uploading file...
  Verifying uploaded file ID='file_238756235'...
  OK.
```

### No local imports; all imports at the top of the file
*BAD*:
```
def function_abc():
 from utils import convert_to_nested_html_table
 # ...
```
*GOOD*:
```
from utils import convert_to_flat_html_table, convert_to_nested_html_table
def function_abc():
 # ...
```

### No docstrings for smaller functions
*BAD*:
```
def generate_error_response(error_message: str, format: str, status_code: int = 400):
  """
  Generate error response in requested format.
  Args: ...
  Returns: ...
  """
  if format == 'json':
    return JSONResponse({"error": error_message}, status_code=status_code)
  else:
    return HTMLResponse(generate_error_div(error_message), status_code=status_code)
```
*GOOD*:
```
# Generate HTTP error response in requested format ('json' | 'html')
def generate_error_response(error_message: str, format: str, status_code: int = 400):
  if format == 'json': return JSONResponse({"error": error_message}, status_code=status_code)
  else: return HTMLResponse(generate_error_div(error_message), status_code=status_code)
```

### Variable naming
*BAD* -> *GOOD*:
```
body_attrs -> body_attributes
content -> html_content
dynamic_count -> use_dynamic_count_for_updating
```

### Function comments
*BAD*:
```
def set_config(app_config):
  """Set the configuration for Crawler management."""
  global config
  config = app_config
```
*GOOD*:
```
# Set the configuration for Crawler management. app_config: Config dataclass with openai_client, persistent_storage_path, etc.
def set_config(app_config):
  global config
  config = app_config  
```
*BAD*:
```
# Generate simple HTML page with title and html content
def generate_simple_page(title: str, html_content: str, body_attributes: str = "") -> str:
  head = generate_html_head(title)
  body_tag = f"<body {body_attributes}>" if body_attributes else "<body>"
  
  return f"""{head}
{body_tag}
{TAB}{html_content}
</body>
</html>"""
```
*GOOD*:
```
def generate_simple_page(title: str, html_content: str, body_attributes: str = "") -> str:
  """
  Generate simple HTML page with title and html content.
  
  Example output:
    <!DOCTYPE html><html><head>[GENERATE_HTML_HEAD_OUTPUT]</head>
    <body [BODY_ATTRIBUTES_IF_ANY]>
	  [HTML_CONTENT]
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
```

### Function grouping and space after function
- Group functions under common topic
- Use start and end markers with centered topic (127 chars long)
- Single line space after each function

*BAD*:
```
def function01():
  ...


def function02():
  ...
def function03():
  ...
def function04():
  ...
```
*GOOD*:
```
# ----------------------------------------------------- START: Topic A --------------------------------------------------------

def function01():
  ...

def function02():
  ...

# ----------------------------------------------------- END: Topic A ----------------------------------------------------------


# ----------------------------------------------------- START: Topic B --------------------------------------------------------
def function03():
  ...

def function04():
  ...  

# ----------------------------------------------------- END: Topic B ----------------------------------------------------------
```
