# V2 Implementation Patterns

**Doc ID**: V2-IMPL-PATTERNS
**Goal**: Mandatory patterns for V2 router implementation

## Table of Contents

1. [SSE Streaming Pattern](#sse-streaming-pattern)
2. [Logger Pattern](#logger-pattern)
3. [Response Pattern](#response-pattern)
4. [Import Pattern](#import-pattern)
5. [Endpoint Structure Pattern](#endpoint-structure-pattern)
6. [Selftest Button Pattern](#selftest-button-pattern)

## SSE Streaming Pattern

**Intent**: Prevent browser buffering of SSE events when generators contain blocking I/O.

### The Problem

Async generators with blocking sync I/O (Office365 SDK `execute_query()`) hold the event loop and prevent HTTP chunk flush. Browser buffers all output until endpoint completes. Curl works (TCP level), but browser fetch API does not.

### The Solution

**Always wrap SSE generators with `stream_with_flush()`:**

```python
from routers_v2.common_job_functions_v2 import StreamingJobWriter, stream_with_flush

return StreamingResponse(stream_with_flush(run_selftest()), media_type="text/event-stream")
```

The wrapper forces event loop flush after each yielded event:

```python
async def stream_with_flush(generator):
  async for event in generator:
    yield event
    await asyncio.sleep(0)
```

### Rules

1. **ALWAYS** use `stream_with_flush()` for all `StreamingResponse` calls
2. **NEVER** add inline `asyncio.sleep(0)` after yields inside generators
3. **TEST** in browser UI, not curl (curl works even without flush)

### Why Always Wrap?

- No performance overhead (`asyncio.sleep(0)` is near-zero cost)
- Safe for both async and blocking I/O endpoints
- Prevents future bugs when I/O type changes
- Single consistent pattern across all routers

### Common Mistake

```python
# WRONG - sleep inside generator does NOT fix buffering
async def run_selftest():
  ctx.execute_query()  # BLOCKING - holds event loop
  yield writer.emit_log("Done")
  await asyncio.sleep(0)  # Too late - blocking already happened

# CORRECT - wrap at endpoint level
return StreamingResponse(stream_with_flush(run_selftest()), ...)
```

## Logger Pattern

**Intent**: Consistent logging across all endpoints with optional SSE streaming support.

### Standard Logger

```python
from routers_v2.common_logging_functions_v2 import MiddlewareLogger, UNKNOWN

@router.get("/endpoint")
async def my_endpoint(request: Request):
  logger = MiddlewareLogger.create()
  logger.log_function_header("my_endpoint")
  # ... endpoint logic ...
  logger.log_function_footer()
  return json_result(True, "", data)
```

### Streaming Logger

For SSE endpoints, create logger with `stream_job_writer`:

```python
writer = StreamingJobWriter(job_id=job_id, ...)
stream_logger = MiddlewareLogger.create(stream_job_writer=writer)
```

### Rules

1. Call `MiddlewareLogger.create()` at start of every endpoint
2. Use `UNKNOWN` constant for missing values (never hardcode placeholders)
3. For streaming endpoints, pass `stream_job_writer` to logger

## Response Pattern

**Intent**: Consistent response format across all endpoints.

### JSON Responses

```python
from routers_v2.common_ui_functions_v2 import json_result, html_result

# Success
return json_result(True, "", {"item_id": "123"})

# Error
return json_result(False, "Item not found.", {})
```

### HTML/UI Responses

```python
# Simple HTML
return html_result("<div>Content</div>")

# Full UI page
return HTMLResponse(generate_ui_page(title, content, ...))
```

### SSE Streaming Responses

```python
return StreamingResponse(stream_with_flush(generator()), media_type="text/event-stream")
```

### Rules

1. **Never** use `HTTPException` - use `json_result(False, error, {})` instead
2. All JSON responses use `json_result()` helper
3. All SSE responses use `stream_with_flush()` wrapper

## Import Pattern

**Intent**: Consistent import structure across all routers.

### Standard Imports

```python
import asyncio, json, uuid
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, StreamingResponse

from routers_v2.common_ui_functions_v2 import generate_ui_page, json_result, html_result
from routers_v2.common_logging_functions_v2 import MiddlewareLogger, UNKNOWN
from routers_v2.common_job_functions_v2 import StreamingJobWriter, stream_with_flush
```

### Rules

1. Group imports: stdlib, fastapi, then `routers_v2.common_*`
2. Import `stream_with_flush` from `common_job_functions_v2`
3. Import `UNKNOWN` constant from `common_logging_functions_v2`

## Endpoint Structure Pattern

**Intent**: Consistent endpoint structure for maintainability.

### Standard Endpoint

```python
@router.get(f"/{router_name}/action")
async def router_action(request: Request):
  logger = MiddlewareLogger.create()
  logger.log_function_header("router_action")
  
  request_params = dict(request.query_params)
  format_param = request_params.get("format", "json")
  
  # ... validation ...
  # ... business logic ...
  
  if format_param == "ui":
    return HTMLResponse(generate_ui_page(...))
  
  logger.log_function_footer()
  return json_result(True, "", data)
```

### Streaming Endpoint

```python
@router.get(f"/{router_name}/stream_action")
async def router_stream_action(request: Request):
  writer = StreamingJobWriter(job_id=..., source_url=str(request.url), ...)
  stream_logger = MiddlewareLogger.create(stream_job_writer=writer)
  
  async def run_stream():
    try:
      yield writer.emit_start()
      # ... streaming logic with yield writer.emit_log() ...
      yield writer.emit_end(ok=True, data={...})
    except Exception as e:
      yield writer.emit_end(ok=False, error=str(e), data={})
    finally:
      writer.finalize()
  
  return StreamingResponse(stream_with_flush(run_stream()), media_type="text/event-stream")
```

### Rules

1. Logger creation first, then param extraction
2. Format check (`ui`/`json`/`stream`) determines response type
3. Streaming generators must call `writer.finalize()` in `finally` block

## Selftest Button Pattern

**Intent**: Selftest buttons should display results in a modal dialog and keep the console visible after completion.

### The Problem

Selftest operations run via SSE streaming and output logs to the console. When `data_reload_on_finish` is set to `"true"`, the page reloads after selftest completes, which:
1. Closes the results dialog before user can review
2. Hides the console log output
3. Prevents examination of test failures

### The Solution

**Selftest toolbar buttons must use these exact settings:**

```python
toolbar_buttons = [
  {
    "text": "Run Selftest",
    "data_url": f"{router_prefix}/{router_name}/selftest?format=stream",
    "data_format": "stream",
    "data_show_result": "modal",
    "data_reload_on_finish": "false",
    "class": "btn-primary"
  }
]
```

**For HTML-based buttons (custom UI):**

```html
<button class="btn-primary" 
        data-url="/v2/router/selftest?format=stream" 
        data-format="stream" 
        data-show-result="modal" 
        data-reload-on-finish="false" 
        onclick="callEndpoint(this)">Run Selftest</button>
```

**For custom selftest dialogs with `connectStream()`:**

```javascript
connectStream(url, { showResult: 'modal', reloadOnFinish: false });
```

### Rules

1. **ALWAYS** set `data_show_result` to `"modal"` for selftest buttons
2. **ALWAYS** set `data_reload_on_finish` to `"false"` for selftest buttons
3. Selftest results should remain visible until user explicitly closes them
4. Console output should remain visible for debugging failed tests

### Why No Reload?

- Selftests create and delete test data - no persistent changes to display
- User needs to review results and console output for failures
- Modal dialog provides clear pass/fail summary with details
- User can manually reload if needed after reviewing results

### Common Mistake

```python
# WRONG - reload closes dialog and console
{
  "text": "Run Selftest",
  "data_url": f"{router_prefix}/{router_name}/selftest?format=stream",
  "data_format": "stream",
  "data_show_result": "modal",
  "data_reload_on_finish": "true",  # BAD - closes everything!
  "class": "btn-primary"
}

# CORRECT - dialog and console stay open
{
  "text": "Run Selftest",
  "data_url": f"{router_prefix}/{router_name}/selftest?format=stream",
  "data_format": "stream",
  "data_show_result": "modal",
  "data_reload_on_finish": "false",  # GOOD - user can review results
  "class": "btn-primary"
}
```

## Document History

**[2026-03-06]**
- Added Selftest Button Pattern (V2FX-PR-003)

**[2026-03-03]**
- Added Logger, Response, Import, and Endpoint Structure patterns
- Initial version from STRM-IN01, STRM-IP01 analysis
