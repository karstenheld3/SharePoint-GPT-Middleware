## Code formatting

- Indent with 2 spaces (no tabs).
- If a statement is ≤ 220 characters (including spaces), keep it on a single line.
- Function definitions: put the full signature on a single line; function body starts on the next line.
- One empty line as delimiter between imports, functions and class definitions

## Imports

- All imports at the top of the file.
- One import statement per line.
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

### Example: Imports, formatting, naming, loops

**BAD**:

```
def process(items, vs_id, logger):
    import time
    from utils import conv, nested_tbl
    # process the items and log stuff
    uploaded_files = []
    dyn_cnt = True
    for i in range(len(items)):
        f = items[i]
        logger.info(f"Uploading {i+1}/{len(items)} {f.path} to {vs_id}")
        res = client.vector_stores.files.content(
            vector_store_id = vs_id,
            file_id = f.id
        )
        uploaded_files.append(res)
    return uploaded_files
```

**GOOD**:

```
import time
from utils import convert_to_flat_html_table, convert_to_nested_html_table

def process_vector_store_files(files, vector_store_id, logger):
  """
  Upload files to a vector store and return the uploaded file objects.

  Example result item:
    {"id": "file_123", "vector_store_id": "vs_123", "status": "completed"}
  """
  uploaded_files = []
  use_dynamic_count_for_updating = True

  for index, file in enumerate(files, start=1):
    logger.info(f"[ {index} / {len(files)} ] Uploading file '{file.path}' to vector store ID='{vector_store_id}'...")
    content_page = client.vector_stores.files.content(vector_store_id=vector_store_id, file_id=file.id)
    uploaded_files.append(content_page)

  return uploaded_files
```

**Improvements:**

- Imports moved to the top and on separate lines; no local imports in the function.
- Names made explicit and consistent: `files`, `vector_store_id`, `use_dynamic_count_for_updating`, `content_page`.
- Function renamed to reflect purpose; arguments self-explanatory.
- Single-line call kept within limit: `content_page = client.vector_stores.files.content(...)`.
- Loop uses `enumerate` instead of indexing; no lambda/iterator helpers.
- Log format is structured and includes quoted paths and IDs.
- Added a docstring with an example only because the function is non-trivial and returns structured data.

### Example: Single-line statements, conditionals, error handling, logging

**BAD**:

```
def generate_error_response(msg: str, fmt: str, status_code: int = 400):
    """
    Generate error response in requested format.
    """
    if fmt == 'json':
        return JSONResponse({"error": msg}, status_code=status_code)
    elif fmt == 'html':
        return HTMLResponse(generate_error_div(msg), status_code=status_code)
    else:
        logger.error(f"Unknown format {fmt}")
        raise ValueError("Unknown format")

def upload_file(file_path, vs_id, logger):
    logger.info(f"Uploading {file_path}")
    if not vs_id:
        raise ValueError(f"Expected a non-empty value for 'vector_store_id' but received {vs_id!r}")
    # ...
```

**GOOD**:

```
# Generate HTTP error response in requested format ('json' | 'html'). log_data: Optional Dict from log_function_header() for logging context
def generate_error_response(error_message: str, response_format: str, status_code: int = 400, log_data: Dict[str, Any] = None):
  if response_format == "json": return JSONResponse({"error": error_message}, status_code=status_code)
  if response_format == "html": return HTMLResponse(generate_error_div(error_message), status_code=status_code)
  if log_data: log_function_output(log_data, f"ERROR: Unsupported response_format='{response_format}'")
  raise ValueError(f"Unsupported response_format='{response_format}'")

# Upload file to OpenAI vector store. log_data: Dict from log_function_header() contains logging context
def upload_file_to_vector_store(file_path: str, vector_store_id: str, log_data: Dict[str, Any]):
  if not vector_store_id: raise ValueError(f"Expected a non-empty value for 'vector_store_id' but received {vector_store_id!r}")
  log_function_output(log_data, f"Uploading file '{file_path}' to vector store ID='{vector_store_id}'...")
  # ... rest of implementation
```

**Improvements:**

- Comment instead of trivial docstring for the small function.
- Variable names clarified: `msg` → `error_message`, `fmt` → `response_format`.
- Single-intention lines are kept on one line (`if ...: return ...`) because they are within the 220-character limit.
- Error log message uses a clear `ERROR` keyword and consistent quoting of arguments.
- The second function’s name now clearly states its purpose; parameters typed and named explicitly.
- The validation `if not vector_store_id` follows the "single intention on one line" rule for guard clauses.

### Example: Logging, retries, and structured output

**BAD**:

```
Uploading item 1/2 C:\Example.docx to vs_62573645276345
SUCCESS: Verified uploaded file.
Uploading item 2/2 C:\Test.docx to vs_62573645276345
ERROR: BlockingIOError: [Errno 11] Resource temporarily unavailable
Retrying...
Uploading again...
Verified.
```

**GOOD**:

```
[ 1 / 2 ] Uploading file 'C:\Example.docx' to vector store ID='vs_62573645276345'...
  Verifying uploaded file ID='file_923748237'...
  OK.
[ 2 / 2 ] Uploading file 'C:\Test.docx' to vector store ID='vs_62573645276345'...
  WARNING: File could not be opened. Maybe it is locked. -> BlockingIOError: [Errno 11] Resource temporarily unavailable
  Waiting 5 seconds ( 1 / 2 ) for retry...
  Uploading file...
  Verifying uploaded file ID='file_238756235'...
  OK.
```

**Improvements:**

- Uses `[ x / n ]` prefix for iterations.
- Sub-actions are indented by 2 spaces.
- Status keywords `OK` and `WARNING` are on separate, indented lines.
- File paths and IDs are always in single quotes.
- Retry count is clearly shown as `( 1 / 2 )`.
- Messages describe what is happening before the action occurs.


