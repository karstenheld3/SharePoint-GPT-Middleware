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
- **What**: Browser UI doesn't receive SSE events in realtime for security scan, but works fine for selftest. Applied `asyncio.sleep(0)` workaround without understanding why it's needed.

**Root cause identified**: Async generators with blocking synchronous I/O between yields don't give the event loop opportunities to flush HTTP response chunks to the browser.

**Learning extracted**: See `SCAN-LN-002` in LEARNINGS.md

## Resolved Issues

### 2026-02-23 - Variable Name Conversion

#### [RESOLVED] `GLOB-FL-002` Truncated snake_case conversion changes meaning

- **Original severity**: [MEDIUM]
- **Resolved**: 2026-02-23 14:21
- **Solution**: Renamed `omit_sharepoint_groups_in_broken_permissions` to `omit_sharepoint_groups_in_broken_permissions_file` in SPEC and IMPL documents

**Prevention rule**: When converting camelCase/PascalCase to snake_case, verify word count matches before and after conversion.

### 2026-02-04 - SSE Streaming Architecture

#### [RESOLVED] `SCAN-FL-004` Sync functions cannot yield SSE events - pattern repeatedly implemented wrong

- **Original severity**: [HIGH]
- **Resolved**: 2026-02-04 00:00
- **Solution**: Refactored scan functions from sync to async generators that yield SSE events directly

**Prevention rule**: Any function that: (1) takes significant time AND (2) needs to show progress to user MUST be an async generator that yields SSE events.

### 2026-02-03 - Broken Inheritance Items Bug

#### [RESOLVED] `SCAN-FL-003` Iterator consumed before iteration in scan_broken_inheritance_items

- **Original severity**: [HIGH]
- **Resolved**: 2026-02-03 18:50
- **Solution**: Convert iterators to lists before using: `ra_list = list(role_assignments)`

**Lesson**: Python iterators can only be consumed once. When you need both the length and to iterate, convert to list first.

### 2026-02-03 - Scanner Bug

#### [RESOLVED] `SCAN-FL-002` Scanner not using return value of execute_query()

- **Original severity**: [HIGH]
- **Resolved**: 2026-02-03 18:37
- **Solution**: Changed `group.users.get().execute_query()` (ignored return) to `users = group.users.get().execute_query()`

**Lesson**: When using Office365-REST-Python-Client, always capture the return value of `execute_query()`.

### 2026-02-03 - PowerShell Commands

#### [RESOLVED] `GLOB-FL-001` Hardcoded client ID instead of reading from .env

- **Original severity**: [MEDIUM]
- **Resolved**: 2026-02-03 18:33
- **Solution**: Used correct pattern with full path to .env file

**Lesson**: Before writing PowerShell commands, check existing scripts for established patterns.

### 2026-02-03 - Security Scan SSE Logging

#### [RESOLVED] `SCAN-FL-001` Detailed logs not appearing in SSE stream

- **Original severity**: [HIGH]
- **Resolved**: 2026-02-03 18:24
- **Solution**: Applied crawler pattern - pass `writer` to scan functions, use `writer.emit_log()` for SSE messages

**Lesson**: When adding SSE logging, always analyze existing working code (crawler) as blueprint.

## Related Sessions

- Sites endpoint failures: `_2026-02-03_V2SitesEndpoint` (SITE-FL-* entries)

## Document History

**[2026-03-02 10:45]**
- Split from `_2026-02-03_V2SitesEndpoint` session - kept SCAN-FL-*, GLOB-FL-* entries

