# Crawler Fixes: Graceful Error Handling

**Plan ID**: V2CR-FIX01
**Goal**: Fix crawler to handle errors gracefully so everything that CAN be crawled IS embedded after crawling
**Target files**:
- `src/routers_v2/crawler.py`
- `src/routers_v2/common_crawler_functions_v2.py`

**Depends on:**
- `_V2_SPEC_CRAWLER.md` lines 487-491 for vector store auto-creation spec
- `_V2_IMPL_CRAWLER.md` for implementation context

## Problems Found

### FIX-01: Vector Store Not Auto-Created When Empty (CRITICAL)

**Symptom:**
```
ERROR: Add to vector store failed: Expected a non-empty value for `vector_store_id` but received ''
```

**Root Cause:**
The spec at `_V2_SPEC_CRAWLER.md:487-491` states:
> If `vector_store_id` in domain.json is empty:
>   - Create new vector store using `vector_store_name` (or `domain_id` if name is empty)
>   - Write new `vector_store_id` back to domain.json
>   - Log: "Created vector store '{name}' (ID={id})"
>   - If creation fails: log error, skip embedding for all sources (continue crawl without embed)

This logic is NOT implemented. `crawl_domain()` at `crawler.py:317` passes `domain.vector_store_id` directly to `step_embed_source()` without checking if it's empty.

**Impact:** ALL embedding operations fail when vector_store_id is not pre-configured.

**Fix Location:** `crawler.py` - `crawl_domain()` function, before the source loop

**Fix Steps:**
1. Before source loop, check if `domain.vector_store_id` is empty
2. If empty, create vector store using `create_vector_store()` from `common_openai_functions_v2.py`
3. Update domain config with new `vector_store_id`
4. Save updated domain to disk using `save_domain_to_file()`
5. If creation fails, set flag to skip embedding for all sources

### FIX-02: Unreachable SharePoint Site (Already Handled)

**Symptom:**
```
ERROR: List 'Security training catalog' - failed to get items -> HTTPSConnectionPool(host='example.sharepoint.com', port=443): Max retries exceeded with url: ... (Caused by NameResolutionError(...))
```

**Root Cause:** Domain has misconfigured source with fake URL `https://example.sharepoint.com/sites/MySite`

**Current Behavior:** Error is logged, source returns 0 items, crawl continues to next source.

**Status:** ALREADY HANDLED GRACEFULLY - No fix needed.

### FIX-03: Site Pages 'bytes-like object' Error

**Symptom:**
```
ERROR: a bytes-like object is required, not 'str'
```

**Root Cause:** In `get_site_pages()` at line 421, calls `try_get_document_library(ctx, ctx.web.url, pages_url_part)`. The `ctx.web.url` property may not be loaded/executed, returning a string representation instead of the actual URL.

**Fix Location:** `common_sharepoint_functions_v2.py` - `get_site_pages()` function

**Fix Steps:**
1. Load `ctx.web` before accessing `.url` property
2. Or pass site_url from source config instead of relying on `ctx.web.url`

### FIX-04: SSE Logs Not Streaming During Crawl

**Symptom:**
When running `/v2/crawler/crawl`, download and embed logs only appear after the entire crawl completes, not in real-time.

**Root Cause:**
In `_crawl_stream()` at `crawler.py:569-570`:
```python
results = await crawl_domain(...)  # All logs queue up during this call
for sse in writer.drain_sse_queue(): yield sse  # Only drained ONCE after completion
```

`crawl_domain()` is a regular async function, not a generator. All `logger.log_function_output()` calls inside it queue SSE events in `writer`, but they're only yielded to the client after the entire crawl completes.

**Fix Location:** `crawler.py` - `crawl_domain()` function

**Fix Options:**
1. **Convert `crawl_domain` to async generator** - Bigger refactor, yields SSE events during execution
2. **Periodic drain inside loop** - Add `for sse in writer.drain_sse_queue(): yield sse` after each step in the source loop

Option 2 is simpler but requires `crawl_domain()` to become an async generator.

**Fix Steps:**
1. Change `crawl_domain()` return type to `AsyncGenerator`
2. Add `yield` statements after each step (download, integrity, process, embed)
3. Update `_crawl_stream()` to iterate over the generator: `async for sse in crawl_domain(...): yield sse`
4. Return final results via a different mechanism (e.g., store in writer or return as last yielded value)

## Implementation Checklist

- [x] **FIX-01**: Auto-create vector store when empty
  - [x] Add vector store creation logic to `crawl_domain()`
  - [x] Update domain.json with new vector_store_id
  - [x] Handle creation failure gracefully (skip embed, continue download)
  - [ ] Add tests
- [ ] **FIX-02**: No action needed (already graceful)
- [x] **FIX-03**: Fix site pages URL resolution
  - [x] Add site_url parameter to get_site_pages()
  - [x] Update crawler.py to pass source.site_url
  - [x] Update test file to pass site_url
- [x] **FIX-04**: SSE logs not streaming during crawl
  - [x] Add set_crawl_results/get_crawl_results to StreamingJobWriter
  - [x] Convert `crawl_domain()` to async generator
  - [x] Add drain points after each step
  - [x] Update `_crawl_stream()` to iterate generator
- [x] **FIX-05**: Skip downloading non-embeddable files
  - [x] Filter to_download list by is_file_embeddable()
  - [x] Non-embeddable files tracked in sharepoint_map.csv only (not in files_map.csv)
  - [x] Log skipped count
  - [x] Update spec

## Spec Changes

**[2026-01-13 14:13]**
- Fixed: FIX-04 - converted crawl_domain to async generator for real-time SSE streaming

**[2026-01-13 13:05]**
- Added: FIX-05 for skipping download of non-embeddable files

**[2026-01-13 12:56]**
- Fixed: FIX-03 - added site_url parameter to get_site_pages() instead of using ctx.web.url

**[2026-01-13 12:55]**
- Added: FIX-04 for SSE logs not streaming during crawl

**[2026-01-13 12:40]**
- Fixed: FIX-01 implemented in `crawler.py:323-339` - auto-create vector store when empty
- Added: Import `create_vector_store` from `common_openai_functions_v2.py`
- Added: `skip_embedding` flag to skip embed step when vector store creation fails

**[2026-01-13 12:35]**
- Added: Initial fixes document with 3 issues identified from crawl job log
