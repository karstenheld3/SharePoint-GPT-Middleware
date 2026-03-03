<DevSystem MarkdownTablesAllowed=true />

# Failure Log

**Goal**: Document failures, mistakes, and lessons learned to prevent repetition

## Table of Contents

1. [Active Issues](#active-issues)
2. [Resolved Issues](#resolved-issues)
3. [Document History](#document-history)

## Active Issues

### 2026-03-03 - Agent Attention Failures

#### `GLOB-FL-001` Agent ignored user's multi-line selection

- **Severity**: [MEDIUM]
- **When**: 2026-03-03 22:29
- **Where**: Conversation context - user selected lines 113-116
- **What**: User selected 3 lines in DROP section but agent only addressed 1 of them

**Evidence**:
User selected:
```
- **`/v2/sites/security_scan/selftest`** - Reason: Requires SharePoint credentials
- **`/v2/crawler/selftest`** - Reason: Requires SharePoint credentials, long runtime
- **`/v2/crawler/crawl`** - Reason: Requires configured domain and SharePoint access
```

User said: "dont drop must test"

Agent interpreted: Only move `security_scan/selftest` to MUST TEST
User intended: Move ALL 3 endpoints from DROP

**Root cause**: Agent did not carefully read the full selection context. Assumed user was referring to only the first item.

**Fix**: When user references a multi-line selection, address ALL lines in the selection, not just the first one.

**Status**: Open - need user clarification on whether crawler endpoints should also move to MUST TEST

### 2026-03-03 - SSE Streaming Not Realtime

#### [RESOLVED] `SITE-FL-002` Security Scan Selftest SSE output not streaming in realtime

- **Severity**: [MEDIUM]
- **When**: 2026-03-03 08:37
- **Where**: `src/routers_v2/sites.py` - `security_scan_selftest` endpoint
- **What**: Browser UI doesn't receive SSE events in realtime - all output appears at once after completion

**Root cause analysis**:

| Sites SELFTEST (works) | Security Scan SELFTEST (broken) |
|------------------------|--------------------------------|
| `await client.post()` | `ctx.web.get().execute_query()` |
| TRUE async (httpx) | SYNCHRONOUS blocking (Office365 SDK) |
| Event loop stays responsive | Event loop blocked during `execute_query()` |

Adding `asyncio.sleep(0)` INSIDE the generator after yields does NOT help because:
1. Blocking `execute_query()` runs and holds event loop
2. Returns result
3. Yield SSE event
4. `await asyncio.sleep(0)` - but event loop was already blocked BEFORE the yield

**Wrong fix (first attempt)**: Added `await asyncio.sleep(0)` after each yield inside `run_selftest()` - did not work.

**Correct fix**: Wrap generator in endpoint-level async iterator that adds sleep AFTER each yielded event:
```python
async def stream_with_flush():
  async for event in run_selftest():
    yield event
    await asyncio.sleep(0)  # Force flush to browser
return StreamingResponse(stream_with_flush(), ...)
```

This matches the working `security_scan` endpoint pattern.

**Additional fix required**: Added `import asyncio` to module imports.

**Resolution**:
- **Resolved**: 2026-03-03 09:29
- **Verified**: Browser now shows SSE output in realtime
- **Prevention**: For endpoints with blocking sync I/O, use endpoint-level wrapper pattern, not inline sleeps

**Related**: `SCAN-FL-005`, `SCAN-LN-002`, `SCAN-PR-005`

## Resolved Issues

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

**Lesson**: When defining onclick handlers in Python dicts that get converted to JS, use escaped double quotes `\"...\"` for string arguments to avoid quote collision with the outer string delimiters.

**Learning**: See `SITE-LN-001` in LEARNINGS.md for full analysis.

## Related Sessions

- Security scanner failures moved to: `_2026-02-03_V2SiteSecurityScanner`

## Document History

**[2026-03-03 22:32]**
- Added GLOB-FL-001: Agent ignored multi-line selection (open)

**[2026-03-03 09:29]**
- Added SITE-FL-002: SSE streaming fix with root cause analysis (resolved)

**[2026-03-02 10:45]**
- Split from original session - kept SITE-FL-* entries only

**[2026-02-03 09:31]**
- Added SITE-FL-001: JavaScript quote escaping issue (resolved)
