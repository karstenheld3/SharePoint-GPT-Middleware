# REVIEW: Permission Scanner POC Implementation

**Doc ID**: PSCP-IP01-RV01
**Reviewed**: 2026-02-03 14:00
**Source**: `_IMPL_PERMISSION_SCANNER_POC.md` [PSCP-IP01] and `_POC_PERMISSION_SCANNER_RESULTS.md` [PSCP-RS01]
**Focus**: Performance optimization strategies - did we overlook anything?

## Industry Research Findings

### 1. `$skip` is NOT Supported for SharePoint List Items [VERIFIED]

**Source**: Microsoft documentation, Stack Overflow, multiple blog posts

**Finding**: SharePoint REST API **ignores** the `$skip` query option for list items. It only works for "collections" like lists, not list items.

**Quote from research**:
> "$skip is not supported for list data. Ugh! That's clearly pointed out in the SharePoint REST API documentation. $skip is only supported for what they call 'collections'..."

**Impact on POC**: This explains why PERF-01 and PERF-04 failed - our `skip()` calls were being ignored, returning the same items.

### 2. `$skiptoken` is the Correct Pagination Method [VERIFIED]

**Source**: SharePoint REST API documentation, Stack Overflow

**Correct format**:
```
$skiptoken=Paged=TRUE&p_ID=<last_item_id>&$top=<count>
```

**Key insight**: The `p_ID` value is the **last item ID returned**, not a skip count. SharePoint returns a `odata.nextLink` with the next `$skiptoken` value automatically.

**Missing from POC**: We did not implement `$skiptoken`-based pagination. The library's `skip()` method doesn't use `$skiptoken`.

### 3. Indexed Columns Enable Filtering on Large Lists [VERIFIED]

**Source**: SharePoint documentation, Stack Exchange answers

**Finding**: Creating an index on columns used for filtering (e.g., `Modified`, `HasUniqueRoleAssignments`) allows efficient retrieval even when list exceeds 5000 items.

**Missing from POC**: No consideration of indexed columns for performance optimization.

### 4. Alternative: SharePoint 2010 REST Interface [VERIFIED]

**Source**: Stack Overflow

**Finding**: The older `_vti_bin/ListData.svc` endpoint DOES support `$skip`. Could be used as fallback.

**Example**: `https://site/_vti_bin/ListData.svc/ListName?$skip=5000&$top=5000`

**Not tested in POC**: Could be a viable workaround for pagination.

### 5. `get_all()` Method in Office365-REST-Python-Client

**Potential solution**: The library may have a `get_all()` method that handles pagination internally using `odata.nextLink`.

**Not tested in POC**: Should investigate library capabilities further.

## Critical Issues

### PSCP-RV-001: Wrong Pagination Strategy [CRITICAL]

- **Category**: Flawed Assumption
- **Severity**: Critical
- **Location**: `02B_test_poc_performance.py`, PERF-01, PERF-04

**Wrong assumption**: "`skip()` works for SharePoint list items"

**Reality**: SharePoint REST API ignores `$skip` for list items. Only `$skiptoken` works.

**Evidence**: PERF-04 returned 5000 unique items when fetching 10000 - second page returned same items as first.

**Fix required**: Implement `$skiptoken`-based pagination or use library's built-in paging (if available).

### PSCP-RV-002: No `odata.nextLink` Handling [HIGH]

- **Category**: Missing Implementation
- **Severity**: High
- **Location**: All pagination code

**Issue**: SharePoint returns `odata.nextLink` in response when more items exist. We're not checking for or using this.

**Impact**: Cannot reliably paginate through large lists.

**Fix required**: Check response for `odata.nextLink` and follow it for next page.

### PSCP-RV-003: Indexed Column Strategy Not Considered [MEDIUM]

- **Category**: Missing Optimization
- **Severity**: Medium
- **Location**: IMPL plan, performance tests

**Issue**: For libraries >5000 items, indexed columns on `ID` or `Modified` can dramatically improve filter performance.

**Impact**: Large list scans may hit list view threshold errors without indexed columns.

**Recommendation**: Document indexed column requirements for production implementation.

## High Priority Issues

### PSCP-RV-004: No Retry Logic for Throttling [HIGH]

- **Category**: Missing Error Handling
- **Severity**: High
- **Location**: All API calls

**Issue**: SharePoint Online throttles requests. No retry-after handling implemented.

**Impact**: Scanning large sites could trigger throttling with no recovery.

**Recommendation**: Implement exponential backoff with Retry-After header support.

### PSCP-RV-005: Connection Reuse Not Verified [MEDIUM]

- **Category**: Unverified Assumption
- **Severity**: Medium
- **Location**: Performance tests

**Issue**: Unclear if the library reuses HTTP connections or creates new ones per request.

**Impact**: Connection overhead could significantly impact bulk operations.

**Recommendation**: Verify connection pooling behavior, consider session reuse.

## Medium Priority Issues

### PSCP-RV-006: Parallel Request Potential Not Explored [MEDIUM]

- **Category**: Missing Optimization
- **Severity**: Medium
- **Location**: Performance strategy

**Issue**: All tests use sequential requests. SharePoint supports concurrent requests (with throttling limits).

**Impact**: Could potentially achieve 2-4x speedup with parallel requests for independent operations.

**Recommendation**: Test concurrent `execute_query()` calls with asyncio or threading.

### PSCP-RV-007: CAML Query Alternative Not Tested [LOW]

- **Category**: Alternative Not Explored
- **Severity**: Low
- **Location**: Enumeration strategy

**Issue**: CAML queries can be more efficient than REST for complex filtering scenarios.

**Impact**: May be leaving performance on the table for certain query patterns.

**Recommendation**: Consider CAML for production if REST performance insufficient.

## Questions That Need Answers

1. Does Office365-REST-Python-Client have a `get_all()` or `paging` method that handles `$skiptoken` automatically?
2. What is the throttling threshold for SharePoint Online REST API calls?
3. Can we use `$filter` on `HasUniqueRoleAssignments` if the column is indexed?
4. Does `execute_batch()` count as one request or multiple for throttling purposes?

## Recommendations

### Immediate (Before Production Implementation)

1. **Research library pagination** - Check if `get_all()` or `paging=True` parameter exists
2. **Implement `$skiptoken` fallback** - Manual pagination using `odata.nextLink`
3. **Add throttling retry logic** - Exponential backoff with Retry-After

### Future Optimization

1. **Test parallel requests** - asyncio for concurrent independent queries
2. **Document indexed column requirements** - For sites with large libraries
3. **Benchmark CAML vs REST** - For permission enumeration specifically

## Summary

The POC validated core API capabilities (51x bulk speedup, 3.8x batch speedup) but **used the wrong pagination strategy**. The `skip()` method is ignored by SharePoint for list items. Production implementation must use `$skiptoken`-based pagination or library-provided paging methods.

**Decision**: GO with implementation, but pagination strategy must be fixed first.

## Document History

**[2026-02-03 14:00]**
- Initial review created
- Research findings on SharePoint pagination
- 7 issues identified (2 critical, 2 high, 3 medium)
