# Session Problems

**Doc ID**: SSE-PROBLEMS

## Open

(none)

## Resolved

### SSE-PR-001: Crawler logs not streaming in realtime

**Status**: Resolved
**Severity**: Medium
**Description**: Logs from `get_document_library_files()` (pagination progress, file counts) only appear in browser after entire step completes, not during execution.

**Root Cause**: 
- `step_download_source` is `async def` returning `DownloadResult`
- Logs queue in `writer._sse_queue` 
- Queue drained only after function returns

**Solution**: Convert step functions to async generators that yield SSE events during execution.

**Affected Functions**:

**Step functions (must become async generators):**
- `step_download_source()` - primary target
- `step_embed_source()` - same pattern
- `step_integrity_check()` - same pattern  
- `step_process_source()` - same pattern

**SharePoint functions that log during execution (no change needed - logs queue correctly):**
- `get_document_library_files()` - pagination callback logs progress
- `get_list_items()` - pagination callback logs progress
- `get_list_items_as_sharepoint_files()` - wraps get_list_items
- `get_site_pages()` - wraps get_document_library_files

**Callers that need updating (to iterate yields):**
- `crawl_domain()` lines 355-366
- `download_source_job()` line 695
- `process_source_job()` line 791
- `embed_source_job()` line 883

## Deferred
