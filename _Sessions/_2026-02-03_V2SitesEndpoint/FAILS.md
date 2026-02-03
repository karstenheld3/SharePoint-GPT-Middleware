# Failure Log

**Goal**: Document failures, mistakes, and lessons learned to prevent repetition

## Table of Contents

1. [Active Issues](#active-issues)
2. [Resolved Issues](#resolved-issues)
3. [Document History](#document-history)

## Active Issues

(none)

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
