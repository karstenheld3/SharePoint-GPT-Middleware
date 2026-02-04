# TASKS: V2 Endpoint Fixes

**Doc ID**: V2FX-TK01
**Goal**: Partitioned tasks for V2 endpoint fixes
**Source**: `_STRUT_V2FX.md [V2FX-ST01]`

## Task 0 - Baseline (MANDATORY)

- [ ] Start dev server, verify it runs
- [ ] Note any pre-existing issues

## Tasks

### Fix 1: Navigation Links (PR-002)

- [ ] **V2FX-TK-001** - Fix reports.py navigation links
  - Files: `src/routers_v2/reports.py`
  - Done when: Navigation links in /v2/reports show proper URLs (not %7B encoded)
  - Verify: Browse /v2/reports?format=ui, check nav links
  - Est: 0.25 HHW

### Fix 2: Stalled Jobs (PR-001)

- [ ] **V2FX-TK-002** - Add isStalled() and Force Cancel to crawler.py
  - Files: `src/routers_v2/crawler.py`
  - Done when: Stalled jobs show "(stalled)" and have Force Cancel button
  - Verify: Check renderJobRow() in crawler UI
  - Depends: TK-001
  - Est: 0.5 HHW

### Fix 3: Query Link (PR-003)

- [ ] **V2FX-TK-003** - Add Query link to domains actions
  - Files: `src/routers_v2/domains.py`
  - Done when: Each domain row has Query button linking to /query2
  - Verify: Browse /v2/domains?format=ui, click Query
  - Depends: TK-002
  - Est: 0.25 HHW

### Fix 4: Vector Store ID Link (PR-004)

- [ ] **V2FX-TK-004** - Make vector_store_id clickable
  - Files: `src/routers_v2/domains.py`, possibly `common_ui_functions_v2.py`
  - Done when: vector_store_id column links to inventory
  - Verify: Browse /v2/domains?format=ui, click VS ID
  - Depends: TK-003
  - Est: 0.5 HHW

### Fix 5: Selftest Cleanup (PR-005)

- [ ] **V2FX-TK-005** - Delete sub-jobs after selftest completion
  - Files: `src/routers_v2/crawler.py`
  - Done when: After selftest, only main job remains
  - Verify: Run selftest, check /v2/jobs for leftover jobs
  - Depends: TK-004
  - Est: 0.5 HHW

## Task N - Final Verification (MANDATORY)

- [ ] Run all V2 endpoints, verify no regressions
- [ ] Commit working fixes
- [ ] Update PROGRESS.md

## Dependency Graph

```
TK-001 ─> TK-002 ─> TK-003 ─> TK-004 ─> TK-005
```

## Document History

**[2026-02-04 12:57]**
- Initial tasks plan created
