# Learnings

**Goal**: Extract transferable lessons from resolved problems

## Table of Contents

1. [Learnings](#learnings-1)
2. [Document History](#document-history)

## Learnings

### `SCAN-LN-002` Async Generators with Blocking I/O Require Explicit Event Loop Yields

**Source**: `SCAN-FL-005` (Browser SSE buffering workaround without root cause)

#### Problem Classification

- **Workflow**: BUILD
- **Complexity**: COMPLEXITY-MEDIUM (multiple files, async patterns)
- **Pattern**: Mixing synchronous blocking I/O with async generators for SSE streaming

#### Context at Decision Time

- **Available**: Curl showed events streaming correctly, selftest worked in browser
- **Not available**: Understanding of how uvicorn/Starlette flushes StreamingResponse chunks, difference between curl and browser fetch API
- **Constraints**: SharePoint Office365-REST-Python-Client library is synchronous

#### Assumptions Made

- `[CONTRADICTS]` Async generators yield events immediately to StreamingResponse regardless of blocking code
- `[CONTRADICTS]` Browser fetch API receives chunks same as curl
- `[UNVERIFIED]` Nested async generators behave same as flat ones
- `[VERIFIED]` Selftest works because httpx uses proper async I/O

#### Rationale

- **Decision**: Convert sync scan functions to async generators to enable realtime SSE
- **Trade-off**: Keep using sync SharePoint library vs. rewriting with async client
- **Gap**: Didn't understand that blocking I/O prevents event loop from flushing HTTP response

#### Outcome Gap

- **Expected**: Events stream to browser in realtime after async generator refactoring
- **Actual**: Curl worked, browser buffered everything until scan completed
- **Divergence point**: Tested with curl (worked), assumed browser would work too

#### Evidence

```python
# Selftest - WORKS (has natural await points)
async with httpx.AsyncClient() as client:
    r = await client.post(...)  # yields to event loop
    yield log("result")         # event loop can flush HTTP response

# Security scan - BUFFERED (no await points)
ctx.web.get().execute_query()   # BLOCKING - no yield to event loop
yield writer.emit_log("result") # event loop cannot flush until next await
```

#### Problem Dependency Tree

```
[Root: No await points between yields in security scan]
├─> [Blocking SharePoint API calls (execute_query)]
│   └─> [Event loop cannot flush HTTP response to browser]
│       └─> [Browser fetch API buffers until generator completes]
└─> [Selftest has await points (httpx async)]
    └─> [Event loop can flush after each await]
        └─> [Browser receives events in realtime]
```

#### Root Cause Analysis

1. **Root cause**: Async generators with blocking synchronous I/O between yields don't give the event loop opportunities to flush HTTP response chunks to the browser. Curl works differently because it processes data at TCP level without browser fetch API buffering.

2. **Counterfactual**: If we had used async SharePoint client OR added explicit `await asyncio.sleep(0)` after yields from the start, events would have streamed to browser in realtime.

3. **Prevention**: When using async generators for SSE streaming with blocking I/O:
   - Always add `await asyncio.sleep(0)` after yields to force event loop flush
   - Better: use truly async I/O libraries when available
   - Test with browser UI, not just curl - they have different chunking behavior

#### Transferable Lesson

**Pattern**: Async generators with sync blocking I/O for SSE streaming  
**Rule**: Always add `await asyncio.sleep(0)` after each yield when the generator contains blocking synchronous code.

**Applies to**:
- Any SSE streaming endpoint using sync SharePoint/Graph API calls
- Any async generator that wraps synchronous blocking I/O
- Future scan functions or long-running jobs with sync libraries

**Quick check**: If your async generator uses sync blocking calls (like `execute_query()`), add `await asyncio.sleep(0)` after yields.

**Code pattern**:
```python
async for event in nested_async_generator_with_blocking_io():
    yield event
    await asyncio.sleep(0)  # Force event loop to flush HTTP response
```

### `SITE-LN-001` Quote Escaping in Generated JavaScript

**Source**: `SITE-FL-001` (JavaScript syntax error from unescaped quotes)

#### Problem Classification

- **Workflow**: BUILD
- **Complexity**: COMPLEXITY-MEDIUM (new router, multiple files)
- **Pattern**: Copying existing code without understanding generation pipeline

#### Context at Decision Time

- **Available**: `domains.py` as reference pattern with working onclick handlers
- **Not available**: Understanding of how `common_ui_functions_v2.py` generates button onclick in `renderItemRow()`
- **Constraints**: User requested "copy domains.py patterns exactly"

#### Assumptions Made

- `[VERIFIED]` Standard onclick handlers like `showEditSiteForm('{itemId}')` work correctly
- `[UNVERIFIED]` All onclick string patterns would be handled the same way
- `[CONTRADICTS]` Single quotes in `showNotImplemented('File Scan')` would work like other buttons

#### Rationale

- **Decision**: Copy domains.py pattern, add new placeholder buttons with `showNotImplemented()` function
- **Trade-off**: Speed of implementation over deep understanding of JS generation pipeline
- **Gap**: domains.py has no placeholder buttons with static string arguments

#### Outcome Gap

- **Expected**: All buttons work, JS loads correctly
- **Actual**: Entire router-specific JS failed to parse
- **Divergence point**: The `showNotImplemented('...')` pattern was new - not copied from domains.py

#### Evidence

```
Browser console:
- "missing ) after argument list"
- "ReferenceError: showNewSiteForm is not defined"

Generated JS (wrong):
btns.push('<button ... onclick=\"showNotImplemented('File Scan')\">...');
                                               ^-- quote collision
```

#### Problem Dependency Tree

```
[Root: Quote collision in generated JS]
├─> [Factor: Using single quotes in onclick value]
│   └─> [Symptom: JS syntax error breaks entire script block]
└─> [Factor: common_ui_functions_v2 wraps onclick in single quotes]
    └─> [Symptom: All functions in script block become undefined]
```

#### Root Cause Analysis

1. **Root cause**: When `common_ui_functions_v2.py` generates button onclick handlers in `renderItemRow()`, it wraps the onclick value in single quotes. Using single quotes inside that value causes quote collision.

2. **Counterfactual**: If I had inspected the generated HTML/JS output (via curl or view-source) before browser testing, the syntax error would have been immediately visible.

3. **Prevention**: When adding onclick handlers with string arguments:
   - Use escaped double quotes `\"...\"` for inner strings
   - Or verify generated output before browser testing
   - Or check how the generation function handles the onclick value

#### Transferable Lesson

**Pattern**: Python-to-JS string generation  
**Rule**: Always use escaped double quotes `\"...\"` for string literals inside onclick handlers that will be processed by UI generation functions.

**Applies to**:
- `common_ui_functions_v2.py` button definitions
- Any dict-based UI configuration that generates JS
- Similar patterns in other V2 routers

**Quick check**: If your onclick contains `('...')`, change to `(\"...\")`.

## Document History

**[2026-02-04 00:28]**
- Added SCAN-LN-002: Async generators with blocking I/O require explicit event loop yields

**[2026-02-03 09:33]**
- Added SITE-LN-001: Quote escaping in generated JavaScript
