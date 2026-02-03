# Failure Log

**Goal**: Document failures, mistakes, and lessons learned to prevent repetition

## Table of Contents

1. [Active Issues](#active-issues)
2. [Resolved Issues](#resolved-issues)
3. [Document History](#document-history)

## Active Issues

### 2026-02-04 - Browser SSE Buffering

#### [ACTIVE] `SCAN-FL-005` Browser SSE buffering - workaround applied without root cause

- **Severity**: [MEDIUM]
- **When**: 2026-02-04 00:23
- **Where**: `sites.py` - `run_scan()` async generator
- **What**: Browser UI doesn't receive SSE events in realtime for security scan, but works fine for selftest. Curl shows events streaming correctly. Applied `asyncio.sleep(0)` workaround without understanding why it's needed.

**Evidence:**
- Selftest: Works in browser UI realtime (no asyncio.sleep(0) needed)
- Security scan: Browser UI buffers all events until scan completes
- Curl: Both work correctly in realtime
- Workaround: `await asyncio.sleep(0)` after each yield fixes browser issue

**What we know:**
- Both use identical `connectStream()` JavaScript function
- Both use identical `StreamingResponse(generator, media_type="text/event-stream")`
- Curl receives events properly for both
- Browser only buffers security scan, not selftest

**Key difference between selftest and security scan:**
- Selftest: Uses `await client.post()` (httpx async) - proper async I/O with natural await points
- Security scan: Uses nested async generators with sync SharePoint API calls (`execute_query()`) - blocking I/O

**Hypotheses (unverified):**
1. **Event loop starvation**: Without await points, uvicorn may not get chances to flush HTTP response to browser
2. **Browser fetch buffering**: Browser's `response.body.getReader()` may have different chunking behavior than curl
3. **Nested async generator issue**: Python's async generator iteration may buffer differently than direct yields
4. **Starlette response flushing**: StreamingResponse may require explicit event loop yields to flush with blocking code

**Why the workaround works:**
`asyncio.sleep(0)` forces an await point that yields control to the event loop, allowing uvicorn to flush the HTTP response chunk to the browser.

**What we should investigate:**
1. Why does curl work but browser doesn't?
2. What exactly triggers Starlette/uvicorn to flush response chunks?
3. Is there a proper configuration for StreamingResponse flushing?
4. Why does httpx async work but sync SharePoint API doesn't?

**Current workaround (not a fix):**
```python
async for event in run_security_scan(...):
    yield event
    await asyncio.sleep(0)  # Force flush - WHY IS THIS NEEDED?
```

**Learning extracted**: See `SCAN-LN-002` in LEARNINGS.md

**Root cause identified**: Async generators with blocking synchronous I/O between yields don't give the event loop opportunities to flush HTTP response chunks to the browser. The selftest works because httpx uses proper async I/O with natural await points.

## Resolved Issues

### 2026-02-04 - SSE Streaming Architecture

#### [RESOLVED] `SCAN-FL-004` Sync functions cannot yield SSE events - pattern repeatedly implemented wrong

- **Original severity**: [HIGH]
- **Resolved**: 2026-02-04 00:00
- **Solution**: Refactored `scan_site_contents()`, `scan_site_groups()`, `scan_broken_inheritance_items()` from sync functions to async generators that yield SSE events directly

- **Severity**: [HIGH]
- **When**: 2026-02-03 23:50
- **Where**: `common_security_scan_functions_v2.py` - `scan_site_contents()`, `scan_site_groups()`, `scan_broken_inheritance_items()`
- **What**: Scan functions are sync and call `writer.emit_log()` which queues events, but cannot yield them. Events only appear after entire function completes, not in realtime.

**Why it keeps happening (Root Cause Analysis):**

1. **Incorrect mental model**: Thinking "emit" means "send" when it actually means "queue"
2. **Copy-paste without understanding**: Copying `writer.emit_log()` pattern without understanding that sync functions CANNOT yield
3. **Ignoring working examples**: Crawler selftest uses `yield log()` pattern - every log is yielded immediately
4. **Wrong abstraction**: Created sync functions that do their own logging instead of generators that yield events

**The correct pattern IS documented and implemented:**

```python
# WRONG - sync function queues events, caller must drain after function returns
def scan_something(writer):
    writer.emit_log("Step 1...")  # Queued, not sent
    # ... long operation ...
    writer.emit_log("Step 2...")  # Queued, not sent
    return result
# Caller: for sse in writer.drain_sse_queue(): yield sse  # All logs appear at once

# CORRECT - async generator yields events immediately
async def scan_something(writer):
    yield writer.emit_log("Step 1...")  # Sent immediately
    # ... operation ...
    yield writer.emit_log("Step 2...")  # Sent immediately
    return result  # Use writer._step_result for return value
# Caller: async for event in scan_something(writer): yield event
```

**Evidence**: Crawler selftest shows realtime logs. Security scan shows logs only after each major step completes.

**Why the pattern is not obvious despite being implemented:**

1. The `emit_log()` function name suggests it emits/sends, but it only queues
2. The drain pattern (`for sse in writer.drain_sse_queue(): yield sse`) works but batches logs
3. No clear documentation that "time-consuming operations with logging MUST be async generators"
4. Agent focuses on making code work (logs appear eventually) not on UX (logs appear realtime)

**Fix**: Refactor all scan functions to async generators that yield SSE events directly.

**Prevention rule to add to DevSystem:**
> Any function that: (1) takes significant time AND (2) needs to show progress to user MUST be an async generator that yields SSE events. Sync functions with `emit_log()` will batch all logs until function returns.

## Resolved Issues

### 2026-02-03 - Broken Inheritance Items Bug

#### [RESOLVED] `SCAN-FL-003` Iterator consumed before iteration in scan_broken_inheritance_items

- **Original severity**: [HIGH]
- **Resolved**: 2026-02-03 18:50
- **Solution**: Convert iterators to lists before using: `ra_list = list(role_assignments)` then iterate over `ra_list`

**Details:**
- **When**: 2026-02-03 18:42
- **Where**: `common_security_scan_functions_v2.py:416-423`
- **What**: 04_IndividualPermissionItems.csv had 11 items but 05_IndividualPermissionItemAccess.csv was empty
- **Why it went wrong**: Called `len(list(role_assignments))` which consumes the iterator, then tried to iterate over the now-empty `role_assignments`. Same issue with `ra.role_definition_bindings`.
- **Evidence**: Server logs showed "Item 1: 5 role assignments" with bindings logged, but no entries added to access_rows

**Lesson**: Python iterators can only be consumed once. When you need both the length and to iterate, convert to list first: `items = list(iterator)` then use `len(items)` and `for item in items`.

### 2026-02-03 - Scanner Bug

#### [RESOLVED] `SCAN-FL-002` Scanner not using return value of execute_query()

- **Original severity**: [HIGH]
- **Resolved**: 2026-02-03 18:37
- **Solution**: Changed `group.users.get().execute_query()` (ignored return) to `users = group.users.get().execute_query()` then iterate over `users`

**Details:**
- **When**: 2026-02-03 18:35
- **Where**: `common_security_scan_functions_v2.py:191`
- **What**: Scanner reported 0 members for all groups even though PowerShell showed 2 members
- **Why it went wrong**: Called `group.users.get().execute_query()` but ignored the return value, then iterated over `group.users` which remained empty
- **Evidence**: POC code shows correct pattern: `users = first_group.users.get().execute_query()`

**Lesson**: When using Office365-REST-Python-Client, always capture the return value of `execute_query()` - the original object property may not be updated in place.

### 2026-02-03 - PowerShell Commands

#### [RESOLVED] `GLOB-FL-001` Hardcoded client ID instead of reading from .env

- **Original severity**: [MEDIUM]
- **Resolved**: 2026-02-03 18:33
- **Solution**: Used correct pattern with full path to .env file

**Details:**
- **When**: 2026-02-03 18:31
- **Where**: Agent-generated PowerShell commands
- **What**: Used hardcoded client ID instead of reading from .env file
- **Why it went wrong**: Did not follow established codebase patterns

**Lesson**: Before writing PowerShell commands, check existing scripts for established patterns. The workspace uses `.env` files for all configuration.

### 2026-02-03 - Security Scan SSE Logging

#### [RESOLVED] `SCAN-FL-001` Detailed logs not appearing in SSE stream

- **Original severity**: [HIGH]
- **Resolved**: 2026-02-03 18:24
- **Solution**: Applied crawler pattern - pass `writer` to scan functions, use `writer.emit_log()` for SSE messages, call `writer.drain_sse_queue()` in main generator to yield queued events
- **Link**: `common_security_scan_functions_v2.py` - `scan_site_groups()`, `resolve_sharepoint_group_members()`

**Details:**
- **When**: 2026-02-03 18:20
- **Where**: `src/routers_v2/common_security_scan_functions_v2.py`
- **What**: Added detailed logging to debug Entra ID group resolution, but logs only appear in server console, not in browser SSE console panel
- **Why it went wrong**: Used `logger.log_function_output()` which writes to server logs, but did NOT emit to SSE stream via `writer.emit_log()`. Failed to analyze existing crawler pattern.
- **Evidence**: Screenshot shows console panel with only high-level messages

**Lesson**: When adding SSE logging, always analyze existing working code (crawler) as blueprint. The pattern is:
1. Pass `writer` to functions that need to emit SSE events
2. Use `writer.emit_log(msg)` to queue SSE events
3. Call `for sse in writer.drain_sse_queue(): yield sse` in the async generator after sync operations

### 2026-02-03 - V2 Sites Endpoint

#### [RESOLVED] `SITE-FL-001` JavaScript syntax error from unescaped quotes in onclick handlers

- **Original severity**: [MEDIUM]
- **Resolved**: 2026-02-03
- **Solution**: Changed single quotes to escaped double quotes in onclick handlers
- **Link**: Commit `a04dfb9`

**Details:**
- **When**: 2026-02-03 09:29
- **Where**: `src/routers_v2/sites.py:424-425` (button definitions in UI columns)
- **What**: JavaScript "missing ) after argument list" error prevented all router-specific JS functions from loading
- **Why it went wrong**: Used single quotes inside onclick attribute that was already delimited by single quotes in the generated JS string. Quote collision caused syntax error.
- **Evidence**: Browser console showed "missing ) after argument list" and "ReferenceError: showNewSiteForm is not defined"

**Code example:**
```python
# Before (wrong) - single quotes collide
{"text": "File Scan", "onclick": "showNotImplemented('File Scan')", "class": "btn-small btn-disabled"}

# After (correct) - escaped double quotes
{"text": "File Scan", "onclick": "showNotImplemented(\"File Scan\")", "class": "btn-small btn-disabled"}
```

**Lesson**: When defining onclick handlers in Python dicts that get converted to JS, use escaped double quotes `\"...\"` for string arguments to avoid quote collision with the outer string delimiters.

**Learning**: See `SITE-LN-001` in LEARNINGS.md for full analysis.

## Document History

**[2026-02-03 09:31]**
- Added SITE-FL-001: JavaScript quote escaping issue (resolved)
