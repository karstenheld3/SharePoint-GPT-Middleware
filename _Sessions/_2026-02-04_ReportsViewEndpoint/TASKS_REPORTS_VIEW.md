# TASKS: Reports View Tasks Plan

**Doc ID**: RPTV-TK01
**Goal**: Partitioned tasks for Reports View endpoint implementation
**Source**: `_V2_IMPL_REPORTS_VIEW.md [RPTV-IP01]`, `_V2_TEST_REPORTS_VIEW.md [RPTV-TP01]`
**Strategy**: PARTITION-TESTABILITY (tasks partitioned for Playwright verification)

## Task Overview

- Total tasks: 6
- Estimated total: 1.5 HHW
- Parallelizable: 0 (sequential dependency chain)

## Task 0 - Baseline (MANDATORY)

- [ ] Verify dev server can start
- [ ] Verify existing reports endpoint works

## STRUT Plan

[ ] P1 [IMPLEMENT]: Build reports view endpoint and UI
├─ Objectives:
│   ├─ [ ] View endpoint works ← P1-D1, P1-D2
│   └─ [ ] UI fully functional ← P1-D3, P1-D4, P1-D5
├─ Strategy: Implement in order, test each with Playwright after completion
├─ [ ] P1-S1 [IMPLEMENT](endpoint + page generation skeleton)
├─ [ ] P1-S2 [TEST](TC-01 to TC-04 via Playwright)
├─ [ ] P1-S3 [IMPLEMENT](tree component JS)
├─ [ ] P1-S4 [TEST](TC-05 to TC-08 via Playwright)
├─ [ ] P1-S5 [IMPLEMENT](CSV table + resize)
├─ [ ] P1-S6 [TEST](TC-09 to TC-13 via Playwright)
├─ [ ] P1-S7 [IMPLEMENT](View button in reports list)
├─ [ ] P1-S8 [TEST](TC-14, TC-15 via Playwright)
├─ [ ] P1-S9 [COMMIT]
├─ Deliverables:
│   ├─ [ ] P1-D1: Endpoint returns HTML for valid request
│   ├─ [ ] P1-D2: Endpoint errors handled correctly
│   ├─ [ ] P1-D3: Tree displays and is interactive
│   ├─ [ ] P1-D4: CSV loads and displays in table
│   ├─ [ ] P1-D5: View button works in reports list
│   └─ [ ] P1-D6: All changes committed
└─> Transitions:
    - P1-D1 - P1-D6 checked → [END]
    - Test failures → [FIX] and retry

## Tasks

### Backend Layer

- [ ] **RPTV-TK-001** - Add /reports/view endpoint
  - Files: src/routers_v2/reports.py
  - Done when: Endpoint handles bare GET, missing params, invalid ID, valid request
  - Verify: Playwright TC-01 to TC-04
  - Est: 0.25 HHW

### UI Layer - Tree

- [ ] **RPTV-TK-002** - Add page generation and tree component
  - Files: src/routers_v2/reports.py
  - Done when: Page renders with file tree from report metadata
  - Verify: Playwright TC-05 to TC-08
  - Depends: TK-001
  - Est: 0.5 HHW

### UI Layer - Table and Resize

- [ ] **RPTV-TK-003** - Add CSV loading, table rendering, resize
  - Files: src/routers_v2/reports.py
  - Done when: Clicking CSV loads content, resize handle works
  - Verify: Playwright TC-09 to TC-13
  - Depends: TK-002
  - Est: 0.25 HHW

### Integration

- [ ] **RPTV-TK-004** - Add View button to reports list
  - Files: src/routers_v2/reports.py
  - Done when: View button appears and navigates to viewer
  - Verify: Playwright TC-14, TC-15
  - Depends: TK-003
  - Est: 0.25 HHW

## Task N - Final Verification (MANDATORY)

- [ ] Run all test cases TC-01 to TC-15
- [ ] Compare to baseline (no regressions)
- [ ] Run /verify workflow
- [ ] Commit all changes

## Dependency Graph

TK-001 ─> TK-002 ─> TK-003 ─> TK-004

## Document History

**[2026-02-04 08:45]**
- Initial tasks plan created from IMPL/TEST
