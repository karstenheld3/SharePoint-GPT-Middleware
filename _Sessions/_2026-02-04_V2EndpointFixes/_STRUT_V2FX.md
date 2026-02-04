# STRUT: V2 Endpoint Fixes

**Doc ID**: V2FX-ST01
**Goal**: Fix 5 V2 endpoint issues with individual testing and verification

## MUST-NOT-FORGET

- Each fix is independent - commit only working fixes
- Test after each fix to ensure no regressions
- Delete temp test scripts after use
- Use Playwright for UI verification where applicable
- Check navigation links work correctly (no URL-encoded placeholders)

## Analysis Summary

| Issue | Location | Root Cause | Fix |
|-------|----------|------------|-----|
| PR-001 | `crawler.py:2271-2315` | Missing `isStalled()` and Force Cancel | Copy from `jobs.py:70-76, 168-199` |
| PR-002 | `reports.py:706,718` | `main_page_nav_html` not `.replace()` | Add `.replace("{router_prefix}", router_prefix)` |
| PR-003 | `domains.py:534-555` | No Query link in columns | Add button to actions column |
| PR-004 | `domains.py:538` | `vector_store_id` is plain text | Make it a hyperlink |
| PR-005 | `crawler.py:1138+` | Selftest creates jobs but doesn't delete them | Delete sub-jobs after completion |

## Plan

[ ] P1 [IMPLEMENT]: Fix issues one by one with testing
├─ Objectives:
│   ├─ [ ] All 5 issues fixed ← P1-D1, P1-D2, P1-D3, P1-D4, P1-D5
│   └─ [ ] No regressions introduced ← P1-D6
├─ Strategy: Fix each issue sequentially, test immediately, commit if working
│   - Run baseline test first to establish known state
│   - Use Playwright MCP to verify UI changes
│   - Each fix gets its own verification before moving on
├─ [ ] P1-S0 [TEST](baseline - start server, verify current state)
├─ [ ] P1-S1 [IMPLEMENT](PR-002 - navigation links in reports.py)
├─ [ ] P1-S1a [TEST](verify /v2/reports navigation links)
├─ [ ] P1-S2 [IMPLEMENT](PR-001 - stalled jobs in crawler.py)
├─ [ ] P1-S2a [TEST](verify /v2/crawler job rendering)
├─ [ ] P1-S3 [IMPLEMENT](PR-003 - Query link in domains.py)
├─ [ ] P1-S3a [TEST](verify /v2/domains Query link works)
├─ [ ] P1-S4 [IMPLEMENT](PR-004 - vector_store_id link in domains.py)
├─ [ ] P1-S4a [TEST](verify vector_store_id is clickable)
├─ [ ] P1-S5 [IMPLEMENT](PR-005 - selftest job cleanup in crawler.py)
├─ [ ] P1-S5a [TEST](run selftest, verify sub-jobs deleted)
├─ [ ] P1-S6 [TEST](full regression - all V2 endpoints)
├─ [ ] P1-S7 [COMMIT](working fixes only)
├─ Deliverables:
│   ├─ [ ] P1-D1: PR-002 fixed (navigation links)
│   ├─ [ ] P1-D2: PR-001 fixed (stalled jobs)
│   ├─ [ ] P1-D3: PR-003 fixed (Query link)
│   ├─ [ ] P1-D4: PR-004 fixed (vector_store_id link)
│   ├─ [ ] P1-D5: PR-005 fixed (selftest cleanup)
│   └─ [ ] P1-D6: Regression test passed
└─> Transitions:
    - All deliverables checked → [END]
    - Any fix breaks other functionality → revert that fix, mark as failed

## Implementation Details

### PR-002: Navigation Links Fix

**File**: `src/routers_v2/reports.py`
**Lines**: 706, 718

**Current (broken)**:
```python
navigation_html=main_page_nav_html
```

**Fix**:
```python
navigation_html=main_page_nav_html.replace("{router_prefix}", router_prefix)
```

### PR-001: Stalled Jobs in Crawler

**File**: `src/routers_v2/crawler.py`
**Location**: `renderJobRow()` function around line 2271

**Changes needed**:
1. Add `isStalled()` function (copy from jobs.py:70-76)
2. Modify `renderJobRow()` to show "(stalled)" state
3. Add "Force Cancel" button for stalled jobs (copy pattern from jobs.py:180-188)

### PR-003: Query Link in Domains

**File**: `src/routers_v2/domains.py`
**Location**: columns definition around line 542

**Add button**:
```python
{"text": "Query", "href": "/query2?vsid={vector_store_id}&query=List+all+files&results=50", "class": "btn-small"}
```

### PR-004: Vector Store ID Link

**File**: `src/routers_v2/domains.py`
**Location**: columns definition line 538

**Change from**:
```python
{"field": "vector_store_id", "header": "Vector Store ID", "default": "-"},
```

**To**:
```python
{"field": "vector_store_id", "header": "Vector Store ID", "default": "-", "link_template": "/v1/inventory/vectorstore_files?vector_store_id={value}&format=ui"},
```

### PR-005: Selftest Job Cleanup

**File**: `src/routers_v2/crawler.py`
**Location**: `_selftest_stream()` function

**Approach**: Track child job IDs created during selftest, delete them after each test completes.

## Document History

**[2026-02-04 12:57]**
- Initial STRUT plan created from analysis
