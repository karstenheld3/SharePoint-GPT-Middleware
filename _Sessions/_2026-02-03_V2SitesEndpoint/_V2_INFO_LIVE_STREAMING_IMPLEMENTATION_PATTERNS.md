<DevSystem MarkdownTablesAllowed=true />

# INFO: Live SSE Streaming Implementation Patterns

**Doc ID**: STRM-IN01
**Goal**: Document SSE streaming patterns across V2 routers to prevent recurring buffering issues
**Timeline**: Created 2026-03-03

## Summary

- **Pattern A (Async HTTP)**: Direct `StreamingResponse(run_selftest())` works for async I/O (httpx) [VERIFIED]
- **Pattern B (Blocking I/O)**: Requires endpoint-level wrapper with `async for` + `asyncio.sleep(0)` [VERIFIED]
- **Pattern C (Delegated)**: Iterate over external async generator with sleep after each yield [VERIFIED]
- Inline `asyncio.sleep(0)` after yields does NOT fix blocking I/O buffering [TESTED]
- Root cause: Sync `execute_query()` blocks event loop, preventing HTTP chunk flush [VERIFIED]

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Endpoint Inventory](#2-endpoint-inventory)
3. [Pattern Analysis](#3-pattern-analysis)
4. [Implementation Guidelines](#4-implementation-guidelines)
5. [Sources](#5-sources)
6. [Next Steps](#6-next-steps)
7. [Document History](#7-document-history)

## 1. Problem Statement

SSE (Server-Sent Events) streaming requires the HTTP response to flush chunks to the browser as they are generated. When async generators contain synchronous blocking I/O (e.g., SharePoint SDK `execute_query()`), the event loop is blocked and cannot flush response chunks until the blocking call completes.

**Symptoms:**
- Console shows all output at once after endpoint completes
- curl works (processes at TCP level)
- Browser fetch API buffers until flush

**Related Issues:**
- `SCAN-FL-005` - Browser SSE buffering
- `SCAN-LN-002` - Async generators with blocking I/O
- `SITE-FL-002` - Security Scan Selftest buffering

## 2. Endpoint Inventory

### 2.1 sites.py

| Endpoint | I/O Type | Pattern | Works? |
|----------|----------|---------|--------|
| `/sites/selftest` | Async (httpx) | A - Direct | Yes |
| `/sites/security_scan` | Blocking (Office365 SDK) | C - Delegated | Yes |
| `/sites/security_scan/selftest` | Blocking (Office365 SDK) | B - Wrapper | Yes (after fix) |

### 2.2 domains.py

| Endpoint | I/O Type | Pattern | Works? |
|----------|----------|---------|--------|
| `/domains/selftest` | Async (httpx) | A - Direct | Yes |

### 2.3 jobs.py

| Endpoint | I/O Type | Pattern | Works? |
|----------|----------|---------|--------|
| `/jobs/monitor` | File polling + sleep | Special (polling loop) | Yes |
| `/jobs/selftest` | Async (httpx) | A - Direct | Yes |

### 2.4 crawler.py

| Endpoint | I/O Type | Pattern | Works? |
|----------|----------|---------|--------|
| `/crawler/crawl` | Mixed (async OpenAI + blocking SharePoint) | A/C hybrid - no sleep | **UNVERIFIED** |
| `/crawler/download_data` | Blocking (SharePoint SDK) | A - Direct (no sleep) | **UNVERIFIED** |
| `/crawler/process_data` | Local file I/O | A - Direct | Yes |
| `/crawler/embed_data` | Async (OpenAI SDK) | A - Direct | Yes |
| `/crawler/selftest` | Blocking (SharePoint SDK) | A - Direct (no sleep) | **UNVERIFIED** |

### 2.5 reports.py

| Endpoint | I/O Type | Pattern | Works? |
|----------|----------|---------|--------|
| `/reports/create_demo_reports` | Local file I/O | A - Direct | Yes |

### 2.6 demorouter1.py, demorouter2.py

| Endpoint | I/O Type | Pattern | Works? |
|----------|----------|---------|--------|
| `/demo*/create` (stream) | Local file I/O | A - Direct | Yes |
| `/demo*/update` (stream) | Local file I/O | A - Direct | Yes |
| `/demo*/delete` (stream) | Local file I/O | A - Direct | Yes |
| `/demo*/selftest` | Async (httpx) | A - Direct | Yes |
| `/demo*/create_demo_items` | Local file I/O | A - Direct | Yes |

## 3. Pattern Analysis

### 3.1 Pattern A: Direct StreamingResponse (Async I/O)

**When to use:** Endpoint uses TRUE async operations (httpx, aiohttp, asyncio primitives)

**Implementation:**
```python
async def run_selftest():
  async with httpx.AsyncClient() as client:
    r = await client.post(url, json=data)  # TRUE async - event loop stays responsive
    yield writer.emit_log("Result received")
    # No sleep needed - event loop naturally flushes between awaits

return StreamingResponse(run_selftest(), media_type="text/event-stream")
```

**Why it works:** `await client.post()` returns control to event loop, allowing HTTP chunks to flush.

**Examples:**
- `sites.py:sites_selftest`
- `domains.py:domains_selftest`
- `jobs.py:jobs_selftest`

### 3.2 Pattern B: Endpoint-Level Wrapper (Blocking I/O)

**When to use:** Endpoint directly contains synchronous blocking calls (Office365 SDK, synchronous DB, etc.)

**Implementation:**
```python
async def run_selftest():
  ctx.web.get().execute_query()  # BLOCKING - holds event loop
  yield writer.emit_log("Connected")
  # Inline sleep here does NOT help - blocking already happened

async def stream_with_flush():
  """Wrapper that forces event loop flush after each SSE event."""
  async for event in run_selftest():
    yield event
    await asyncio.sleep(0)  # Force flush AFTER yield at endpoint level

return StreamingResponse(stream_with_flush(), media_type="text/event-stream")
```

**Why it works:** The `async for` loop with `asyncio.sleep(0)` at the endpoint level gives the event loop a chance to flush HTTP chunks between yielded events.

**Why inline sleep doesn't work:**
1. Blocking `execute_query()` runs and holds event loop
2. Returns result
3. Yield SSE event
4. `await asyncio.sleep(0)` - event loop was blocked BEFORE yield, flush opportunity missed

**Examples:**
- `sites.py:sites_security_scan_selftest` (after fix)

### 3.3 Pattern C: Delegated Async Generator

**When to use:** Endpoint delegates to an external async generator that handles blocking I/O internally

**Implementation:**
```python
async def _crawl_stream(...):
  yield writer.emit_start()
  async for sse in crawl_domain(...):  # External async generator
    yield sse
  yield writer.emit_end(...)

return StreamingResponse(_crawl_stream(...), media_type="text/event-stream")
```

**Variant with explicit flush (for blocking I/O in external generator):**
```python
async for event in run_security_scan(...):
  yield event
  await asyncio.sleep(0)  # Force flush each event
```

**Examples:**
- `sites.py:sites_security_scan` (uses `run_security_scan` async generator)
- `crawler.py:_crawl_stream` (uses `crawl_domain` async generator)

## 4. Implementation Guidelines

### 4.1 Decision Tree

```
Is your generator using blocking sync I/O?
├── NO (httpx, aiohttp, asyncio)
│   └── Use Pattern A: Direct StreamingResponse
└── YES (Office365 SDK, sync DB, sync file I/O)
    ├── Is blocking I/O in external async generator?
    │   └── Use Pattern C: Iterate with async for + sleep(0)
    └── Is blocking I/O directly in endpoint function?
        └── Use Pattern B: Wrapper with async for + sleep(0)
```

### 4.2 Checklist for New SSE Endpoints

1. [ ] Identify I/O type (async vs blocking sync)
2. [ ] Choose correct pattern (A, B, or C)
3. [ ] Import asyncio if using Pattern B or C
4. [ ] Test in browser (not just curl) to verify realtime streaming
5. [ ] Document pattern used in code comment

### 4.3 Common Mistakes

- **Mistake 1**: Adding `asyncio.sleep(0)` after yields INSIDE generator with blocking I/O
  - **Fix**: Move sleep to endpoint-level wrapper (Pattern B)

- **Mistake 2**: Forgetting `import asyncio` when using sleep
  - **Fix**: Add to module imports

- **Mistake 3**: Testing only with curl (which works even without flush)
  - **Fix**: Always test in browser UI

## 5. Sources

**Primary Sources:**
- `STRM-IN01-SC-SITES-PY`: `sites.py` - All three patterns implemented [VERIFIED]
- `STRM-IN01-SC-CRAWL-PY`: `crawler.py` - Pattern C delegated streaming [VERIFIED]
- `STRM-IN01-SC-FAILS-MD`: `FAILS.md` - SITE-FL-002 root cause analysis [VERIFIED]
- `STRM-IN01-SC-SCAN-LN`: `LEARNINGS.md` - SCAN-LN-002 pattern documentation [VERIFIED]

## 6. Next Steps

1. **[PRIORITY]** Test crawler endpoints in browser to verify if buffering occurs
2. If buffering found, add `asyncio.sleep(0)` wrapper pattern to crawler streaming
3. Add code comments referencing this document where Pattern B/C is used
4. Consider creating a `stream_with_flush()` utility function in `common_job_functions_v2.py`

## 7. Document History

**[2026-03-03 09:45]**
- Fixed: Crawler endpoints marked UNVERIFIED - uses blocking I/O without sleep wrapper
- Added priority action to test crawler streaming

**[2026-03-03 09:35]**
- Initial research document created
- Documented all SSE streaming endpoints across V2 routers
- Classified three implementation patterns (A, B, C)
- Added decision tree and implementation guidelines
