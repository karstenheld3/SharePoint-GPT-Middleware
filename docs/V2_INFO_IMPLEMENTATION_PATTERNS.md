# V2 Implementation Patterns

**Doc ID**: V2-IMPL-PATTERNS
**Goal**: Mandatory patterns for V2 router implementation

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

## Document History

**[2026-03-03]**
- Initial version from STRM-IN01, STRM-IP01 analysis
