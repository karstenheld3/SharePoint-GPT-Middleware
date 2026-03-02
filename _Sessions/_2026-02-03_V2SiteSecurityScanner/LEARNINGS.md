# Learnings

**Goal**: Extract transferable lessons from resolved problems

## Table of Contents

1. [Learnings](#learnings-1)
2. [Document History](#document-history)

## Learnings

### `SCAN-LN-002` Async Generators with Blocking I/O Require Explicit Event Loop Yields

**Source**: `SCAN-FL-005` (Browser SSE buffering workaround without root cause)

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

**Root cause**: Async generators with blocking synchronous I/O between yields don't give the event loop opportunities to flush HTTP response chunks to the browser. Curl works differently because it processes data at TCP level.

## Related Sessions

- Sites endpoint learnings: `_2026-02-03_V2SitesEndpoint` (SITE-LN-* entries)

## Document History

**[2026-03-02 10:45]**
- Split from `_2026-02-03_V2SitesEndpoint` session - kept SCAN-LN-* entries

**[2026-02-04 00:28]**
- Added SCAN-LN-002: Async generators with blocking I/O require explicit event loop yields

