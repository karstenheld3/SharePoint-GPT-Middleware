# TEST: V2 Reports View

**Doc ID**: RPTV-TP01
**Goal**: Verify `/v2/reports/view` endpoint and UI functionality via Playwright
**Target file**: Playwright browser tests (manual via MCP)

**Depends on:**
- `_V2_SPEC_REPORTS_VIEW.md [RPTV-SP01]` for requirements
- `_V2_IMPL_REPORTS_VIEW.md [RPTV-IP01]` for implementation details

## MUST-NOT-FORGET

- Test via Playwright MCP, not Python test files
- Each test case maps to a verification step
- Tests require running dev server on localhost:8000

## Test Strategy

**Approach**: Integration testing via Playwright browser automation

**Execution:**
1. Start dev server if not running
2. Navigate to reports UI
3. Click View button on a report
4. Verify viewer page loads and functions

## Test Cases

### Endpoint Tests (4 tests)

- **RPTV-TC-01**: Bare GET returns self-documentation -> ok=true, plain text with "report_id"
- **RPTV-TC-02**: Missing report_id returns error -> ok=false, "Missing 'report_id' parameter"
- **RPTV-TC-03**: Invalid report_id returns 404 -> ok=false, "not found"
- **RPTV-TC-04**: format != ui returns error -> ok=false, "only supports format=ui"

### Tree Component Tests (4 tests)

- **RPTV-TC-05**: Tree displays files from report -> tree contains file nodes
- **RPTV-TC-06**: Folders are collapsible -> clicking folder toggles children visibility
- **RPTV-TC-07**: CSV files are clickable -> clicking CSV loads content
- **RPTV-TC-08**: Non-CSV files are disabled -> report.json has disabled class, not clickable

### Table Component Tests (3 tests)

- **RPTV-TC-09**: CSV content displays in table -> table has thead and tbody
- **RPTV-TC-10**: First CSV auto-selected on load -> selected class on first CSV node
- **RPTV-TC-11**: Error handling on file load failure -> shows error message

### Resize Tests (2 tests)

- **RPTV-TC-12**: Resize handle visible -> element with col-resize cursor exists
- **RPTV-TC-13**: Drag adjusts panel width -> tree-panel width changes after drag

### Navigation Tests (2 tests)

- **RPTV-TC-14**: View button exists in reports list -> button with "View" text visible
- **RPTV-TC-15**: View button navigates to viewer -> clicking opens /reports/view page

## Test Phases

1. **Phase 1: Server Setup** - Ensure dev server running
2. **Phase 2: Endpoint Tests** - TC-01 to TC-04 via direct fetch
3. **Phase 3: UI Tests** - TC-05 to TC-15 via Playwright navigation

## Verification Checklist

- [ ] TC-01: Bare GET self-documentation
- [ ] TC-02: Missing report_id error
- [ ] TC-03: Invalid report_id 404
- [ ] TC-04: format != ui error
- [ ] TC-05: Tree displays files
- [ ] TC-06: Folders collapsible
- [ ] TC-07: CSV files clickable
- [ ] TC-08: Non-CSV disabled
- [ ] TC-09: CSV content in table
- [ ] TC-10: First CSV auto-selected
- [ ] TC-11: Error handling
- [ ] TC-12: Resize handle visible
- [ ] TC-13: Drag adjusts width
- [ ] TC-14: View button exists
- [ ] TC-15: View button navigates

## Document History

**[2026-02-04 08:45]**
- Initial test plan created
