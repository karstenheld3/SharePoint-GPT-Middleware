# IMPL: SSE Streaming Harmonization

**Doc ID**: STRM-IP01
**Feature**: SSE_FLUSH_WRAPPER
**Goal**: Harmonize SSE streaming pattern across all V2 endpoints to prevent browser buffering issues
**Timeline**: Created 2026-03-03

**Target files**:
- `src/routers_v2/common_job_functions_v2.py` (EXTEND +15 lines)
- `src/routers_v2/sites.py` (MODIFY)
- `src/routers_v2/crawler.py` (MODIFY)
- `src/routers_v2/domains.py` (MODIFY)
- `src/routers_v2/jobs.py` (MODIFY)
- `src/routers_v2/reports.py` (MODIFY)
- `src/routers_v2/demorouter1.py` (MODIFY)
- `src/routers_v2/demorouter2.py` (MODIFY)

**Depends on:**
- `_V2_INFO_LIVE_STREAMING_IMPLEMENTATION_PATTERNS.md` [STRM-IN01] for pattern analysis and rationale

## MUST-NOT-FORGET

- Import `stream_with_flush` from common_job_functions_v2 in each router
- Test in BROWSER (not curl) - curl works even without flush
- Endpoints using true async I/O (httpx) still benefit from wrapper (no overhead)
- Do NOT add inline `asyncio.sleep(0)` after yields - use wrapper instead

## Table of Contents

1. [Rationale](#1-rationale)
2. [File Structure](#2-file-structure)
3. [Edge Cases](#3-edge-cases)
4. [Implementation Steps](#4-implementation-steps)
5. [Endpoint Implementation Matrix](#5-endpoint-implementation-matrix)
6. [Test Cases](#6-test-cases)
7. [Verification Checklist](#7-verification-checklist)
8. [Document History](#8-document-history)

## 1. Rationale

### 1.1 Problem Evidence

**Failure `SITE-FL-002`** (2026-03-03): Security Scan Selftest SSE output not streaming in realtime. Browser UI showed all output at once after completion.

**Failure `SCAN-FL-005`** (2026-02-04): Browser SSE buffering for security scan. Applied `asyncio.sleep(0)` workaround without understanding root cause.

**Failure `SCAN-FL-004`** (2026-02-04): Sync functions cannot yield SSE events - pattern repeatedly implemented wrong.

### 1.2 Root Cause (from `SCAN-LN-002`)

Async generators with blocking synchronous I/O (Office365 SDK `execute_query()`) don't give event loop opportunities to flush HTTP response chunks to browser. Curl works because it processes at TCP level, but browser fetch API buffers until flush.

### 1.3 Wrong Fix Pattern

Adding `asyncio.sleep(0)` INSIDE generator after yields does NOT work because:
1. Blocking `execute_query()` runs and holds event loop
2. Returns result
3. Yield SSE event
4. `await asyncio.sleep(0)` - event loop was blocked BEFORE yield, flush opportunity missed

### 1.4 Correct Fix Pattern

Wrap generator at endpoint level with `async for` + `asyncio.sleep(0)`:
```python
async def stream_with_flush(generator):
  async for event in generator:
    yield event
    await asyncio.sleep(0)

return StreamingResponse(stream_with_flush(run_selftest()), ...)
```

### 1.5 Why Harmonize All Endpoints

- Consistent pattern prevents future bugs
- No performance overhead (`asyncio.sleep(0)` is near-zero cost)
- Safe for both async and blocking I/O endpoints
- Single utility function, DRY principle

## 2. File Structure

```
src/routers_v2/
├── common_job_functions_v2.py  # Add stream_with_flush() [EXTEND +15 lines]
├── sites.py                    # Apply to 3 endpoints [MODIFY]
├── crawler.py                  # Apply to 5 endpoints [MODIFY]
├── domains.py                  # Apply to 1 endpoint [MODIFY]
├── jobs.py                     # Apply to 2 endpoints [MODIFY]
├── reports.py                  # Apply to 1 endpoint [MODIFY]
├── demorouter1.py              # Apply to 5 endpoints [MODIFY]
└── demorouter2.py              # Apply to 5 endpoints [MODIFY]
```

## 3. Edge Cases

- **STRM-IP01-EC-01**: Generator raises exception -> Exception propagates through wrapper unchanged
- **STRM-IP01-EC-02**: Generator yields None -> Wrapper yields None (transparent)
- **STRM-IP01-EC-03**: Empty generator -> Wrapper completes immediately (no events)
- **STRM-IP01-EC-04**: Generator yields very large event -> No chunking, single yield (transparent)

## 4. Implementation Steps

### STRM-IP01-IS-01: Create `stream_with_flush()` utility function

**Location**: `common_job_functions_v2.py` > after `StreamingJobWriter` class

**Action**: Add new async generator function

**Code**:
```python
async def stream_with_flush(generator):
  """
  Wrapper that forces event loop flush after each SSE event.
  
  Required for endpoints with blocking sync I/O (Office365 SDK, etc.)
  to ensure browser receives events in realtime.
  
  Reference: STRM-IN01, SCAN-LN-002, SITE-FL-002
  """
  async for event in generator:
    yield event
    await asyncio.sleep(0)
```

**Note**: Requires `import asyncio` at top of file (verify present).

### STRM-IP01-IS-02: Update sites.py imports

**Location**: `sites.py` > imports section

**Action**: Add import for `stream_with_flush`

**Code**:
```python
from routers_v2.common_job_functions_v2 import StreamingJobWriter, stream_with_flush
```

### STRM-IP01-IS-03: Apply to sites.py endpoints

**Location**: `sites.py` > `sites_selftest`, `sites_security_scan`, `sites_security_scan_selftest`

**Action**: Wrap StreamingResponse content with `stream_with_flush()`

**Pattern**:
```python
# BEFORE
return StreamingResponse(run_selftest(), media_type="text/event-stream")

# AFTER
return StreamingResponse(stream_with_flush(run_selftest()), media_type="text/event-stream")
```

**Note**: For `security_scan_selftest`, remove the inline `stream_with_flush()` wrapper and use centralized version.

### STRM-IP01-IS-04: Update crawler.py imports and endpoints

**Location**: `crawler.py` > imports section and 5 streaming endpoints

**Action**: Add import, apply wrapper to all StreamingResponse calls

**Endpoints**:
- `_crawl_stream()` at line ~641
- `_download_stream()` at line ~751
- `_process_stream()` at line ~846
- `_embed_stream()` at line ~939
- `_selftest_stream()` at line ~1192

### STRM-IP01-IS-05: Update domains.py

**Location**: `domains.py` > imports and `domains_selftest` endpoint

**Action**: Add import, apply wrapper

**Endpoint**: Line ~1327

### STRM-IP01-IS-06: Update jobs.py

**Location**: `jobs.py` > imports and streaming endpoints

**Action**: Add import, apply wrapper

**Endpoints**:
- `jobs_monitor` stream_log() at line ~616
- `jobs_selftest` run_selftest() at line ~1412

### STRM-IP01-IS-07: Update reports.py

**Location**: `reports.py` > imports and streaming endpoint

**Action**: Add import, apply wrapper

**Endpoint**: `reports_create_demo_reports` at line ~1182

### STRM-IP01-IS-08: Update demorouter1.py

**Location**: `demorouter1.py` > imports and 5 streaming endpoints

**Action**: Add import, apply wrapper

**Endpoints**:
- `demo1_create` stream_create() at line ~1085
- `demo1_update` stream_update() at line ~1239
- `demo1_delete` stream_delete() at line ~1337
- `demo1_selftest` run_selftest() at line ~1772
- `demo1_create_demo_items` stream_create_demo_items() at line ~1912

### STRM-IP01-IS-09: Update demorouter2.py

**Location**: `demorouter2.py` > imports and 5 streaming endpoints

**Action**: Add import, apply wrapper (same pattern as demorouter1)

**Endpoints**:
- `demo2_create` stream_create() at line ~526
- `demo2_update` stream_update() at line ~666
- `demo2_delete` stream_delete() at line ~754
- `demo2_selftest` run_selftest() at line ~1019
- `demo2_create_demo_items` stream_create_demo_items() at line ~1151

## 5. Endpoint Implementation Matrix

### sites.py (3 endpoints)

- **`/sites/selftest`**
  - I/O Type: Async (httpx)
  - Current: Direct StreamingResponse
  - Change: Wrap with `stream_with_flush()`
  - Rationale: Consistency, no overhead

- **`/sites/security_scan`**
  - I/O Type: Blocking (Office365 SDK)
  - Current: `async for` + inline sleep
  - Change: Use centralized `stream_with_flush()`
  - Rationale: DRY, centralized fix

- **`/sites/security_scan/selftest`**
  - I/O Type: Blocking (Office365 SDK)
  - Current: Local `stream_with_flush()` wrapper
  - Change: Use centralized `stream_with_flush()`
  - Rationale: DRY, remove duplicate code

### crawler.py (5 endpoints)

- **`/crawler/crawl`**
  - I/O Type: Mixed (async OpenAI + blocking SharePoint)
  - Current: Direct StreamingResponse (NO sleep)
  - Change: Wrap with `stream_with_flush()`
  - Rationale: **CRITICAL** - has blocking I/O, currently may buffer

- **`/crawler/download_data`**
  - I/O Type: Blocking (SharePoint SDK)
  - Current: Direct StreamingResponse (NO sleep)
  - Change: Wrap with `stream_with_flush()`
  - Rationale: **CRITICAL** - has blocking I/O, currently may buffer

- **`/crawler/process_data`**
  - I/O Type: Local file I/O
  - Current: Direct StreamingResponse
  - Change: Wrap with `stream_with_flush()`
  - Rationale: Consistency

- **`/crawler/embed_data`**
  - I/O Type: Async (OpenAI SDK)
  - Current: Direct StreamingResponse
  - Change: Wrap with `stream_with_flush()`
  - Rationale: Consistency

- **`/crawler/selftest`**
  - I/O Type: Blocking (SharePoint SDK)
  - Current: Direct StreamingResponse (NO sleep)
  - Change: Wrap with `stream_with_flush()`
  - Rationale: **CRITICAL** - has blocking I/O, currently may buffer

### domains.py (1 endpoint)

- **`/domains/selftest`**
  - I/O Type: Async (httpx)
  - Current: Direct StreamingResponse
  - Change: Wrap with `stream_with_flush()`
  - Rationale: Consistency

### jobs.py (2 endpoints)

- **`/jobs/monitor`**
  - I/O Type: File polling + sleep
  - Current: Direct StreamingResponse
  - Change: Wrap with `stream_with_flush()`
  - Rationale: Consistency

- **`/jobs/selftest`**
  - I/O Type: Async (httpx)
  - Current: Direct StreamingResponse
  - Change: Wrap with `stream_with_flush()`
  - Rationale: Consistency

### reports.py (1 endpoint)

- **`/reports/create_demo_reports`**
  - I/O Type: Local file I/O
  - Current: Direct StreamingResponse
  - Change: Wrap with `stream_with_flush()`
  - Rationale: Consistency

### demorouter1.py (5 endpoints)

- All use local file I/O or async httpx
- Change: Wrap all with `stream_with_flush()`
- Rationale: Consistency

### demorouter2.py (5 endpoints)

- All use local file I/O or async httpx
- Change: Wrap all with `stream_with_flush()`
- Rationale: Consistency

## 6. Test Cases

### Category 1: Browser Realtime Streaming (5 tests)

- **STRM-IP01-TC-01**: `/sites/security_scan/selftest` -> Browser console shows events in realtime
- **STRM-IP01-TC-02**: `/crawler/selftest` -> Browser console shows events in realtime
- **STRM-IP01-TC-03**: `/crawler/crawl` -> Browser console shows events in realtime
- **STRM-IP01-TC-04**: `/sites/selftest` -> Browser console shows events in realtime
- **STRM-IP01-TC-05**: `/domains/selftest` -> Browser console shows events in realtime

### Category 2: Functional Correctness (3 tests)

- **STRM-IP01-TC-06**: All selftest endpoints -> ok=true, all tests pass
- **STRM-IP01-TC-07**: Exception in generator -> Propagates correctly, job shows error
- **STRM-IP01-TC-08**: Cancel stream mid-execution -> Graceful handling

## 7. Verification Checklist

### Prerequisites
- [ ] **STRM-IP01-VC-01**: Read `_V2_INFO_LIVE_STREAMING_IMPLEMENTATION_PATTERNS.md` [STRM-IN01]
- [ ] **STRM-IP01-VC-02**: Read FAILS.md for SITE-FL-002, SCAN-FL-005 context

### Implementation
- [ ] **STRM-IP01-VC-03**: IS-01 completed - `stream_with_flush()` added to common_job_functions_v2.py
- [ ] **STRM-IP01-VC-04**: IS-02/03 completed - sites.py updated
- [ ] **STRM-IP01-VC-05**: IS-04 completed - crawler.py updated
- [ ] **STRM-IP01-VC-06**: IS-05 completed - domains.py updated
- [ ] **STRM-IP01-VC-07**: IS-06 completed - jobs.py updated
- [ ] **STRM-IP01-VC-08**: IS-07 completed - reports.py updated
- [ ] **STRM-IP01-VC-09**: IS-08 completed - demorouter1.py updated
- [ ] **STRM-IP01-VC-10**: IS-09 completed - demorouter2.py updated

### Validation
- [ ] **STRM-IP01-VC-11**: TC-01 through TC-05 pass (browser realtime test)
- [ ] **STRM-IP01-VC-12**: TC-06 through TC-08 pass (functional correctness)
- [ ] **STRM-IP01-VC-13**: All existing selftests still pass
- [ ] **STRM-IP01-VC-14**: No duplicate `asyncio.sleep(0)` patterns remain in code

## 8. Document History

**[2026-03-03 09:50]**
- Initial implementation plan created
- Added rationale backed by SITE-FL-002, SCAN-FL-005, SCAN-LN-002
- Detailed endpoint matrix with I/O type and change rationale
