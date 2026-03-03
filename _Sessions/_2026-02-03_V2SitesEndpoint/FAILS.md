# Failure Log

**Goal**: Document failures, mistakes, and lessons learned to prevent repetition

## Table of Contents

1. [Active Issues](#active-issues)
2. [Resolved Issues](#resolved-issues)
3. [Document History](#document-history)

## Active Issues

### 2026-03-03 - SSE Streaming Not Realtime

#### [RESOLVED] `SITE-FL-002` Security Scan Selftest SSE output not streaming in realtime

- **Severity**: [MEDIUM]
- **When**: 2026-03-03 08:37
- **Where**: `src/routers_v2/sites.py` - `run_selftest()` in `security_scan_selftest` endpoint
- **What**: Browser UI doesn't receive SSE events in realtime - all output appears at once after completion

**Root cause**: Known issue (SCAN-FL-005, SCAN-LN-002). Async generators with blocking sync I/O (SharePoint `execute_query()`) don't give event loop opportunities to flush HTTP response chunks to browser.

**Fix applied**: Added `await asyncio.sleep(0)` after every `yield` statement in the `security_scan_selftest` function (~40 yields).

**Resolution**:
- **Resolved**: 2026-03-03 08:40
- **Verified**: Browser now shows SSE output in realtime
- **Prevention**: Always add `await asyncio.sleep(0)` after yields in async generators with blocking I/O

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

**[2026-03-02 10:45]**
- Split from original session - kept SITE-FL-* entries only

**[2026-02-03 09:31]**
- Added SITE-FL-001: JavaScript quote escaping issue (resolved)
