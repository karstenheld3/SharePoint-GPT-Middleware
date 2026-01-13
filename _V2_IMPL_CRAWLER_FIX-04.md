# Implementation Plan: FIX-04 SSE Streaming During Crawl

**Plan ID**: V2CR-FIX04-IP01
**Goal**: Enable real-time SSE log streaming during crawl operations instead of batched output after completion
**Target files**:
- `/src/routers_v2/crawler.py` (MODIFY)

**Depends on:**
- `_V2_SPEC_CRAWLER.md` for crawl process specification
- `_V2_IMPL_CRAWLER_FIXES.md` for problem description (FIX-04)

**Does not depend on:**
- `_V2_SPEC_ROUTERS.md` (SSE infrastructure already exists)

## Table of Contents

1. Problem Analysis
2. Domain Objects
3. Solution Design
4. Edge Cases
5. Implementation Steps
6. Test Cases
7. Backward Compatibility Test
8. Checklist

## 1. Problem Analysis

**Current Behavior:**
```
User starts crawl
  -> _crawl_stream() calls crawl_domain()
  -> crawl_domain() runs ALL steps (download, integrity, process, embed)
  -> All logger.log_function_output() calls queue SSE events in writer
  -> After crawl_domain() returns, drain_sse_queue() yields ALL events at once
  -> User sees logs only after entire crawl completes
```

**Desired Behavior:**
```
User starts crawl
  -> _crawl_stream() iterates over crawl_domain() generator
  -> After each step, crawl_domain() yields control back
  -> _crawl_stream() drains SSE queue and yields to client
  -> User sees logs in real-time as each step completes
```

**Root Cause:**
- `crawl_domain()` is an `async def` function (returns a single result)
- SSE events are queued in `writer.sse_queue` during execution
- `drain_sse_queue()` is called only once after `crawl_domain()` returns

## 2. Domain Objects

**StreamingJobWriter:**
- Maintains `sse_queue` for buffered SSE events
- `drain_sse_queue()` returns and clears all queued events
- Already supports periodic draining

**crawl_domain():**
- Orchestrates download, integrity, process, embed steps for each source
- Currently returns `dict` with results
- Needs to become async generator that yields SSE drain points

**_crawl_stream():**
- Entry point for SSE streaming
- Calls `crawl_domain()` and yields SSE events
- Needs to iterate over generator instead of awaiting result

## 3. Solution Design

**Approach: Convert crawl_domain to Async Generator**

**Pattern:**
```python
# BEFORE
async def crawl_domain(...) -> dict:
  for source in sources:
    result = await step_download_source(...)
    # ... more steps
  return results

# AFTER
async def crawl_domain(...) -> AsyncGenerator[str, None]:
  for source in sources:
    result = await step_download_source(...)
    for sse in writer.drain_sse_queue(): yield sse  # Drain after each step
    # ... more steps
  # Store results in writer or yield as final value
```

**Caller Pattern:**
```python
# BEFORE
results = await crawl_domain(...)
for sse in writer.drain_sse_queue(): yield sse

# AFTER
async for sse in crawl_domain(...):
  yield sse
results = writer.get_crawl_results()  # New method to retrieve stored results
```

**Results Handling:**
- Store final results in `writer.crawl_results` attribute
- Add `set_crawl_results()` and `get_crawl_results()` methods to StreamingJobWriter
- Alternative: Use a wrapper dataclass passed to crawl_domain

## 4. Edge Cases

- **V2CR-FIX04-IP01-EC-01**: Empty sources list -> Should yield no SSE events, return early
- **V2CR-FIX04-IP01-EC-02**: Exception during step -> Should still yield queued SSE before raising
- **V2CR-FIX04-IP01-EC-03**: Job cancelled mid-crawl -> Should drain queue and exit gracefully
- **V2CR-FIX04-IP01-EC-04**: dry_run mode -> Should work identically with streaming

## 5. Implementation Steps

### V2CR-FIX04-IP01-IS-01: Add results storage to StreamingJobWriter

**Location**: `src/routers_v2/common_job_functions_v2.py` > `StreamingJobWriter` class

**Action**: Add `crawl_results` attribute and accessor methods

**Code**:
```python
class StreamingJobWriter:
  def __init__(self, ...):
    # ... existing init
    self.crawl_results = None  # Add this line
  
  def set_crawl_results(self, results: dict):
    self.crawl_results = results
  
  def get_crawl_results(self) -> dict:
    return self.crawl_results or {}
```

### V2CR-FIX04-IP01-IS-02: Convert crawl_domain to async generator

**Location**: `src/routers_v2/crawler.py` > `crawl_domain()`

**Action**: Change return type and add yield statements after each step

**Code**:
```python
# Add to imports at top of file
from typing import AsyncGenerator

# Change function signature (keep on single line per GLOB-FT-03)
async def crawl_domain(storage_path: str, domain: DomainConfig, mode: str, scope: str, source_id: Optional[str], dry_run: bool, retry_batches: int, writer: StreamingJobWriter, logger: MiddlewareLogger, crawler_config: dict, openai_client) -> AsyncGenerator[str, None]:
  sources = get_sources_for_scope(domain, scope, source_id)
  if not sources:
    logger.log_function_output("WARNING: No sources configured")
    writer.set_crawl_results({"ok": True, "data": {"sources_processed": 0}})
    return
  
  # FIX-01: Auto-create vector store if empty
  skip_embedding = False
  if not domain.vector_store_id:
    # ... existing vector store creation logic
    pass
  
  logger.log_function_output(f"Crawling {len(sources)} source(s)")
  for sse in writer.drain_sse_queue(): yield sse  # Drain after initial log
  
  job_id = writer.job_id if dry_run else None
  download_results, embed_results = [], []
  
  for source_type, source in sources:
    result = await step_download_source(...)
    download_results.append(result)
    for sse in writer.drain_sse_queue(): yield sse  # Drain after download
    
    await step_integrity_check(...)
    for sse in writer.drain_sse_queue(): yield sse  # Drain after integrity
    
    if source_type in ("list_sources", "sitepage_sources"):
      await step_process_source(...)
      for sse in writer.drain_sse_queue(): yield sse  # Drain after process
    
    if not skip_embedding:
      result = await step_embed_source(...)
      embed_results.append(result)
      for sse in writer.drain_sse_queue(): yield sse  # Drain after embed
  
  # Calculate totals and store results
  total_downloaded = sum(r.downloaded for r in download_results)
  total_embedded = sum(r.embedded for r in embed_results)
  total_errors = sum(r.errors for r in download_results) + sum(r.failed for r in embed_results)
  
  writer.set_crawl_results({
    "ok": total_errors == 0,
    "error": f"{total_errors} errors" if total_errors > 0 else "",
    "data": {
      "domain_id": domain.domain_id,
      "mode": mode,
      "scope": scope,
      "dry_run": dry_run,
      "sources_processed": len(sources),
      "total_downloaded": total_downloaded,
      "total_embedded": total_embedded,
      "total_errors": total_errors
    }
  })
```

### V2CR-FIX04-IP01-IS-03: Update _crawl_stream to iterate generator

**Location**: `src/routers_v2/crawler.py` > `_crawl_stream()`

**Action**: Change from await to async for, retrieve results from writer

**Code**:
```python
async def _crawl_stream(domain: DomainConfig, mode: str, scope: str, source_id: Optional[str], dry_run: bool, retry_batches: int, logger: MiddlewareLogger, openai_client):
  writer = StreamingJobWriter(...)
  logger.stream_job_writer = writer
  started_utc, _ = _get_utc_now()
  try:
    yield writer.emit_start()
    yield logger.log_function_output(f"Starting crawl for domain '{domain.domain_id}'")
    
    # Iterate over generator, yielding SSE events in real-time
    async for sse in crawl_domain(get_persistent_storage_path(), domain, mode, scope, source_id, dry_run, retry_batches, writer, logger, get_crawler_config(), openai_client):
      yield sse
    
    # Retrieve results from writer
    results = writer.get_crawl_results()
    
    finished_utc, _ = _get_utc_now()
    if not dry_run and results.get("ok", False):
      report_id = create_crawl_report(...)
      results["data"]["report_id"] = report_id
    
    total_embedded = results.get('data', {}).get('total_embedded', 0)
    yield logger.log_function_output(f"{total_embedded} file{'' if total_embedded == 1 else 's'} embedded.")
    yield writer.emit_end(ok=results.get("ok", False), error=results.get("error", ""), data=results.get("data", {}))
  except Exception as e:
    yield logger.log_function_output(f"ERROR: Crawl failed -> {str(e)}")
    yield writer.emit_end(ok=False, error=str(e), data={})
  finally:
    # ... existing cleanup
    writer.finalize()
```

### V2CR-FIX04-IP01-IS-04: Update download_data, process_data, embed_data streams

**Location**: `src/routers_v2/crawler.py` > `_download_stream()`, `_process_stream()`, `_embed_stream()`

**Action**: These already work correctly as they call individual step functions, but verify they drain SSE properly

**Note**: No changes expected, but verify during testing

## 6. Test Cases

### Manual Testing (3 tests)

- **V2CR-FIX04-IP01-TST-01**: Run `/v2/crawler/crawl?domain_id=_SELFTEST&mode=full&scope=files&format=stream` -> Logs should appear in real-time, not after completion
- **V2CR-FIX04-IP01-TST-02**: Run crawl with 2+ sources -> Logs from first source visible before second source starts
- **V2CR-FIX04-IP01-TST-03**: Cancel job mid-crawl -> Partial logs visible before cancellation

### Selftest Verification (existing tests)

- **V2CR-FIX04-IP01-TST-04**: Run full selftest -> All 55 tests should still pass
- **V2CR-FIX04-IP01-TST-05**: Verify A1 (full crawl) completes successfully
- **V2CR-FIX04-IP01-TST-06**: Verify F1 (incremental crawl) completes successfully

## 7. Backward Compatibility Test

**Purpose**: Verify crawl operations still produce correct results after refactor.

**Test script**: `_V2_IMPL_CRAWLER_FIX-04_backcompat_test.py`

**Run BEFORE implementation**:
```bash
python _V2_IMPL_CRAWLER_FIX-04_backcompat_test.py > backcompat_before.txt
```

**Run AFTER implementation**:
```bash
python _V2_IMPL_CRAWLER_FIX-04_backcompat_test.py > backcompat_after.txt
diff backcompat_before.txt backcompat_after.txt
```

**Test coverage**:
- [ ] Crawl endpoint returns same result structure
- [ ] Crawl report is created with same fields
- [ ] files_metadata.json updated correctly

**Script**:
```python
# _V2_IMPL_CRAWLER_FIX-04_backcompat_test.py
import httpx
import json
import time

BASE_URL = "http://localhost:8000"
DOMAIN_ID = "_SELFTEST"

def run_crawl_and_get_result():
  """Run a full crawl and capture the final result."""
  with httpx.Client(timeout=120) as client:
    r = client.get(f"{BASE_URL}/v2/crawler/crawl?domain_id={DOMAIN_ID}&mode=full&scope=files&format=stream", headers={"Accept": "text/event-stream"})
    last_line = ""
    for line in r.iter_lines():
      if line.startswith("data: "):
        last_line = line[6:]
    return json.loads(last_line) if last_line else {}

def test_crawl_result_structure():
  print("=== Test: Crawl Result Structure ===")
  result = run_crawl_and_get_result()
  print(f"ok: {result.get('ok')}")
  print(f"error: {result.get('error', '')}")
  data = result.get('data', {})
  print(f"domain_id: {data.get('domain_id')}")
  print(f"mode: {data.get('mode')}")
  print(f"scope: {data.get('scope')}")
  print(f"sources_processed: {data.get('sources_processed')}")
  print(f"total_downloaded: {data.get('total_downloaded')}")
  print(f"total_embedded: {data.get('total_embedded')}")
  print(f"has_report_id: {'report_id' in data}")

if __name__ == "__main__":
  test_crawl_result_structure()
```

## 8. Checklist

### Prerequisites
- [ ] **V2CR-FIX04-IP01-VC-01**: Read and understand current crawl_domain implementation
- [ ] **V2CR-FIX04-IP01-VC-02**: Backward compatibility test script created
- [ ] **V2CR-FIX04-IP01-VC-03**: Backward compatibility test run BEFORE changes

### Implementation
- [ ] **V2CR-FIX04-IP01-VC-04**: IS-01 completed (add crawl_results to StreamingJobWriter)
- [ ] **V2CR-FIX04-IP01-VC-05**: IS-02 completed (convert crawl_domain to generator)
- [ ] **V2CR-FIX04-IP01-VC-06**: IS-03 completed (update _crawl_stream)
- [ ] **V2CR-FIX04-IP01-VC-07**: IS-04 verified (download/process/embed streams)

### Verification
- [ ] **V2CR-FIX04-IP01-VC-08**: TST-01 passes (real-time streaming visible)
- [ ] **V2CR-FIX04-IP01-VC-09**: TST-02 passes (multi-source streaming)
- [ ] **V2CR-FIX04-IP01-VC-10**: TST-03 passes (cancel mid-crawl)
- [ ] **V2CR-FIX04-IP01-VC-11**: Full selftest passes (55/55)
- [ ] **V2CR-FIX04-IP01-VC-12**: Backward compatibility test passes (diff empty or expected)

### Documentation
- [ ] **V2CR-FIX04-IP01-VC-13**: Update _V2_IMPL_CRAWLER_FIXES.md to mark FIX-04 complete

## Spec Changes

**[2026-01-13 14:03]**
- Added: Initial implementation plan for FIX-04
