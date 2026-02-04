# TEST: V2 Endpoint Fixes

**Doc ID**: V2FX-TP01
**Goal**: Test plan for V2 endpoint fixes
**Source**: `_STRUT_V2FX.md [V2FX-ST01]`, `_TASKS_V2FX.md [V2FX-TK01]`

## Test Strategy

- Use Playwright MCP to verify UI changes
- Manual browser verification as backup
- Each fix tested immediately after implementation
- Regression test at end

## Test Cases

### TC-001: Navigation Links (PR-002)

**Precondition**: Server running at localhost:8000

1. Navigate to /v2/reports?format=ui
2. Inspect navigation links in page HTML
3. **Pass**: Links show `/v2/domains?format=ui`, NOT `%7Brouter_prefix%7D`
4. **Fail**: Links contain URL-encoded placeholders

### TC-002: Stalled Jobs Display (PR-001)

**Precondition**: Server running, at least one job exists

1. Navigate to /v2/crawler?format=ui
2. If a job is stalled (>5min old, still "running"), verify:
   - State shows "(stalled)"
   - "Force Cancel" button appears
3. **Pass**: Stalled jobs properly indicated with force option
4. **Fail**: Stalled jobs look same as running jobs

### TC-003: Query Link (PR-003)

**Precondition**: Server running, at least one domain exists

1. Navigate to /v2/domains?format=ui
2. Find domain with vector_store_id configured
3. Click "Query" button
4. **Pass**: Navigates to /query2 with correct vsid parameter
5. **Fail**: No Query button OR wrong URL

### TC-004: Vector Store ID Link (PR-004)

**Precondition**: Server running, domain with vector_store_id exists

1. Navigate to /v2/domains?format=ui
2. Click on vector_store_id value
3. **Pass**: Navigates to /v1/inventory/vectorstore_files?vector_store_id=...
4. **Fail**: VS ID not clickable OR wrong URL

### TC-005: Selftest Job Cleanup (PR-005)

**Precondition**: Server running, CRAWLER_SELFTEST_SHAREPOINT_SITE configured

1. Run crawler selftest: /v2/crawler/selftest?format=stream&phase=1
2. Wait for completion
3. Check /v2/jobs?format=json
4. **Pass**: Only main selftest job remains, sub-jobs deleted
5. **Fail**: Multiple selftest-related jobs remain

### TC-006: Regression - All V2 Endpoints

1. /v2/domains?format=ui - loads without error
2. /v2/sites?format=ui - loads without error
3. /v2/crawler?format=ui - loads without error
4. /v2/jobs?format=ui - loads without error
5. /v2/reports?format=ui - loads without error
6. All navigation links work
7. **Pass**: All endpoints functional
8. **Fail**: Any endpoint errors or navigation broken

## Document History

**[2026-02-04 12:57]**
- Initial test plan created
