# Implementation Plan: Domains Selftest Endpoint

**Plan ID**: V2DM-IP02
**Goal**: Add exhaustive selftest endpoint for domains router
**Target file**: `src/routers_v2/domains.py`

**Depends on:**
- `_V2_SPEC_DOMAINS_UI.md` for domain object model and endpoint patterns
- `_V2_IMPL_DOMAINS_RENAME.md` for rename functionality

## Table of Contents

1. Overview
2. Test Data
3. Test Cases by Category
4. Implementation Structure
5. Checklist

## Overview

The selftest endpoint validates all CRUD operations for the domains router via HTTP calls to itself. Pattern follows `demorouter2.py` selftest but adapted for domain-specific functionality.

**Endpoint**: `GET /v2/domains/selftest?format=stream`
**Response**: SSE stream with test progress and final summary

## Test Data

### Global Constant (add after `main_page_nav_html`)

```python
example_domain_json = """
{
  "domain_id": "example_domain",
  "name": "Example Domain",
  "description": "Example description",
  "vector_store_name": "example_vs",
  "vector_store_id": "",
  "file_sources": [],
  "sitepage_sources": [],
  "list_sources": []
}
"""
```

### Test Variables (inside run_selftest)

```python
test_id = f"selftest_{uuid.uuid4().hex[:8]}"

test_domain_v1 = {
  "domain_id": test_id,
  "name": "Test Domain",
  "description": "Selftest domain",
  "vector_store_name": "test_vs"
}

test_domain_v2 = {
  "name": "Updated Domain",
  "description": "Updated description",
  "vector_store_name": "updated_vs"
}

test_sources_json = json.dumps({
  "file_sources": [{"source_id": "src1", "site_url": "https://test.sharepoint.com", "sharepoint_url_part": "/Docs", "filter": ""}],
  "sitepage_sources": [],
  "list_sources": []
})

renamed_test_id = f"{test_id}_renamed"
```

## Test Cases by Category

### Category 1: Error Cases (8 tests)

| # | Test | Expected | HTTP |
|---|------|----------|------|
| 1 | POST /create without body | ok=false | 200 |
| 2 | POST /create with empty required fields | ok=false, validation error | 200 |
| 3 | PUT /update without domain_id param | ok=false | 200 |
| 4 | PUT /update with non-existent domain_id | ok=false | 404 |
| 5 | GET /get without domain_id | ok=false | 200 |
| 6 | GET /get with non-existent domain_id | ok=false | 404 |
| 7 | DELETE /delete without domain_id | ok=false | 200 |
| 8 | DELETE /delete with non-existent domain_id | ok=false | 404 |

### Category 2: Create Tests (4 tests)

| # | Test | Expected |
|---|------|----------|
| 9 | POST /create with valid data | ok=true |
| 10 | GET /get → verify created data | name, description match |
| 11 | POST /create with same domain_id | ok=false, "already exists" |
| 12 | GET / → domain in list | test_id in list |

### Category 3: Create with Sources (3 tests)

| # | Test | Expected |
|---|------|----------|
| 13 | POST /create second domain with sources_json | ok=true |
| 14 | GET /get → verify sources parsed | file_sources.length == 1 |
| 15 | POST /create with invalid sources_json | ok=false, JSON error |

### Category 4: Update Tests (4 tests)

| # | Test | Expected |
|---|------|----------|
| 16 | PUT /update with new name | ok=true |
| 17 | GET /get → verify name changed | name == "Updated Domain" |
| 18 | PUT /update with sources_json | ok=true |
| 19 | GET /get → verify sources updated | file_sources present |

### Category 5: Rename Tests (6 tests)

| # | Test | Expected |
|---|------|----------|
| 20 | PUT /update with domain_id in body (rename) | ok=true |
| 21 | GET /get with old domain_id | 404 |
| 22 | GET /get with new domain_id | 200, correct data |
| 23 | PUT /update rename to existing domain_id | ok=false, 400 |
| 24 | PUT /update rename to invalid format | ok=false, 400 |
| 25 | GET / → renamed domain in list | new_id in list, old_id not |

### Category 6: Delete Tests (4 tests)

| # | Test | Expected |
|---|------|----------|
| 26 | DELETE /delete | ok=true |
| 27 | GET /get → 404 | 404 |
| 28 | GET / → domain not in list | test_id not in list |
| 29 | DELETE /delete same domain again | 404 |

## Implementation Structure

### Endpoint Docs List (in `domains_root`, add to endpoints array)

```python
{"path": "/selftest", "desc": "Self-test", "formats": ["stream"]}
```

### Toolbar Button (in `domains_root` format=ui, add to toolbar_buttons)

```python
{
  "text": "Run Selftest",
  "data_url": f"{router_prefix}/{router_name}/selftest?format=stream",
  "data_format": "stream",
  "data_show_result": "modal",
  "data_reload_on_finish": "true",
  "class": "btn-primary"
}
```

### Selftest Endpoint

```python
@router.get(f"/{router_name}/selftest")
async def domains_selftest(request: Request):
  """
  Self-test for domains CRUD operations.
  
  Only supports format=stream.
  
  Tests:
  1. Error cases (missing params, non-existent domains)
  2. Create domain
  3. Create with sources
  4. Update domain
  5. Rename domain (ID change)
  6. Delete domain
  
  Example:
  GET {router_prefix}/{router_name}/selftest?format=stream

  Example domain:
  {example_domain_json}
  """
  request_params = dict(request.query_params)
  
  # Bare GET returns documentation
  if len(request_params) == 0:
    doc = textwrap.dedent(domains_selftest.__doc__).replace("{router_prefix}", router_prefix).replace("{router_name}", router_name).replace("{example_domain_json}", example_domain_json.strip())
    return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), media_type="text/plain; charset=utf-8")
  
  format_param = request_params.get("format", "")
  
  if format_param != "stream":
    return json_result(False, "Selftest only supports format=stream", {})
  
  base_url = str(request.base_url).rstrip("/")
  
  writer = StreamingJobWriter(
    persistent_storage_path=get_persistent_storage_path(),
    router_name=router_name,
    action="selftest",
    object_id=None,
    source_url=str(request.url),
    router_prefix=router_prefix
  )
  stream_logger = MiddlewareLogger.create(stream_job_writer=writer)
  stream_logger.log_function_header("domains_selftest")
  
  # Test variables, run_selftest() generator, return StreamingResponse
```

### Helper Functions (inside run_selftest)

```python
def log(msg: str):
  return stream_logger.log_function_output(msg)

def next_test(description: str):
  nonlocal test_num
  test_num += 1
  return log(f"[Test {test_num}] {description}")

def check(condition: bool, ok_msg: str, fail_msg: str):
  nonlocal ok_count, fail_count
  if condition:
    ok_count += 1
    passed_tests.append(ok_msg)
    return log(f"  OK: {ok_msg}")
  else:
    fail_count += 1
    failed_tests.append(fail_msg)
    return log(f"  FAIL: {fail_msg}")
```

### Cleanup

```python
finally:
  try:
    async with httpx.AsyncClient(timeout=10.0) as cleanup_client:
      # Delete test domain
      await cleanup_client.delete(f"{base_url}{router_prefix}/{router_name}/delete?domain_id={test_id}")
      # Delete renamed domain
      await cleanup_client.delete(f"{base_url}{router_prefix}/{router_name}/delete?domain_id={renamed_test_id}")
      # Delete sources test domain
      await cleanup_client.delete(f"{base_url}{router_prefix}/{router_name}/delete?domain_id={sources_test_id}")
  except: pass
  writer.finalize()
```

## Checklist

### Prerequisites

- [x] Rename functionality implemented (per _V2_IMPL_DOMAINS_RENAME.md)

### Implementation

- [x] Add imports: `uuid`, `httpx`, `StreamingResponse`
- [x] Add imports: `StreamingJobWriter` from common_job_functions_v2
- [x] Add `example_domain_json` global constant
- [x] Add selftest to router docs endpoint list: `{"path": "/selftest", "desc": "Self-test", "formats": ["stream"]}`
- [x] Add "Run Selftest" button to UI toolbar with `data_show_result="modal"`
- [x] Implement `domains_selftest` endpoint:
  - [x] Bare GET returns docstring documentation
  - [x] format != stream returns error
  - [x] base_url extraction: `str(request.base_url).rstrip("/")`
  - [x] StreamingJobWriter setup
  - [x] run_selftest() async generator
  - [x] StreamingResponse return

### Test Cases (29 total)

**Error Cases (8):**
- [x] Test 1: POST /create without body
- [x] Test 2: POST /create empty required fields
- [x] Test 3: PUT /update without domain_id param
- [x] Test 4: PUT /update non-existent domain
- [x] Test 5: GET /get without domain_id
- [x] Test 6: GET /get non-existent domain
- [x] Test 7: DELETE without domain_id
- [x] Test 8: DELETE non-existent domain

**Create (4):**
- [x] Test 9: POST /create valid
- [x] Test 10: GET /get verify data
- [x] Test 11: POST /create duplicate
- [x] Test 12: GET / in list

**Create with Sources (3):**
- [x] Test 13: POST /create with sources
- [x] Test 14: GET /get verify sources
- [x] Test 15: POST /create invalid sources

**Update (4):**
- [x] Test 16: PUT /update name
- [x] Test 17: GET /get verify update
- [x] Test 18: PUT /update sources
- [x] Test 19: GET /get verify sources

**Rename (6):**
- [x] Test 20: PUT /update with domain_id (rename)
- [x] Test 21: GET old ID → 404
- [x] Test 22: GET new ID → 200
- [x] Test 23: Rename to existing → 400
- [x] Test 24: Rename invalid format → 400
- [x] Test 25: GET / verify list

**Delete (4):**
- [x] Test 26: DELETE /delete
- [x] Test 27: GET → 404
- [x] Test 28: GET / not in list
- [x] Test 29: DELETE again → 404

### Verification

- [ ] Run selftest via UI
- [ ] Verify all 29 tests pass
- [ ] Verify cleanup removes test domains
