# _V2_SPEC_SITES_SECURITY_SCAN_REVIEW.md

**Doc ID**: SSCSCN-SP01-RV01
**Goal**: Document potential issues, risks, and suggestions for improvement
**Reviewed**: 2026-02-03 15:19
**Context**: Devil's Advocate review of security scan specification before IMPL plan

## MUST-NOT-FORGET (Review Constraints)

- Scope param changed from 4 booleans to single `scope` string
- Report archive integration per `_V2_SPEC_REPORTS.md`
- FAILS.md has `$skip` pagination issue documented
- PowerShell CSV format is authoritative reference

## MUST-RESEARCH

1. SharePoint API throttling - How to handle limits during large scans
2. Azure AD transitive members - Performance and limits for nested groups
3. CSV streaming - Memory-safe incremental writing patterns
4. SharePoint batch requests - Can role assignments be batched?
5. Permission scanner at scale - What breaks on sites with 100K+ items?

## Table of Contents

1. [Critical Issues](#critical-issues)
2. [High Priority](#high-priority)
3. [Medium Priority](#medium-priority)
4. [Low Priority](#low-priority)
5. [Industry Research Findings](#industry-research-findings)
6. [Recommendations](#recommendations)
7. [Document History](#document-history)

## Critical Issues

(None found)

## High Priority

### `SCAN-RV-001` Inconsistent Scope Parameters in Action Flow

- **Location**: Section 10, lines 455-476 (Action Flow)
- **What**: Action flow still uses old boolean params (`scan_site_level`, `scan_lists`, `scan_items`) instead of new single `scope` param
- **Risk**: IMPL will be confused about correct parameter design; code may implement wrong API
- **Suggested action**: Update action flow to reference `scope` values (`all`, `site`, `lists`, `items`)

### `SCAN-RV-002` Request Example Uses Old Parameters

- **Location**: Section 11, line 487
- **What**: Request example shows `?scan_site_level=true&scan_lists=true&scan_items=true` instead of `?scope=all`
- **Risk**: Copy-paste implementation will use wrong params
- **Suggested action**: Update to `GET /v2/sites/security_scan?site_id=site01&scope=all&include_subsites=false`

### `SCAN-RV-003` Design Decision Contradicts Report Storage

- **Location**: Section 7, SCAN-DD-03
- **What**: States "Store results in site folder" but spec was updated to use report archive in `reports/site_scans/`
- **Risk**: Conflicting storage locations during implementation
- **Suggested action**: Update SCAN-DD-03 to "Store results as report archive per `_V2_SPEC_REPORTS.md`"

### `SCAN-RV-004` No Throttling Strategy Defined

- **Location**: Missing from spec
- **What**: No strategy for handling SharePoint API throttling (429 responses, Retry-After headers)
- **Risk**: Large site scans will hit throttling limits; scan may fail or take extremely long
- **Evidence**: Microsoft docs confirm apps have resource unit limits; CSOM/REST consume more than Graph
- **Suggested action**: Add SCAN-FR or SCAN-IG for throttling: "Honor Retry-After header, implement exponential backoff, decorate traffic with User-Agent"

## Medium Priority

### `SCAN-RV-005` Batching for Role Assignments Not Explored

- **Location**: Section 9, Key Mechanisms
- **What**: Each item with broken inheritance triggers separate role assignment query
- **Risk**: N+1 query pattern; scanning 1000 broken items = 1000 separate API calls
- **Evidence**: SharePoint supports batch requests up to 1000 operations
- **Suggested action**: Add mechanism for batching `RoleAssignments` queries; or add SCAN-DD explaining why not batching

### `SCAN-RV-006` Graph API Transitive Members Has Limits

- **Location**: Section 9, Group Resolution mechanism
- **What**: Azure AD transitive member resolution has undocumented pagination limits
- **Risk**: Groups with 1000+ members may require multiple pages; current pseudo-code doesn't handle pagination
- **Evidence**: Graph API `/transitivemembers` returns paged results (default 100 per page)
- **Suggested action**: Add note about Graph pagination handling in group resolution; update SCAN-IG-05

### `SCAN-RV-007` CSV Escaping Regex May Not Match PowerShell Exactly

- **Location**: Section 9, CSV Escaping mechanism
- **What**: Python regex pattern for CSV escaping is inferred, not verified against actual PowerShell behavior
- **Risk**: Subtle escaping differences could cause "byte-for-byte compatible" guarantee (SCAN-IG-01) to fail
- **Suggested action**: Add test case comparing Python-generated CSV with actual PowerShell output file

### `SCAN-RV-008` User Actions Section References Old Modal

- **Location**: Section 12, line 515
- **What**: "Check/uncheck scope options in dialog" but modal now uses dropdown, not checkboxes
- **Risk**: Minor inconsistency; may confuse UI implementation
- **Suggested action**: Update to "Select scope from dropdown in dialog"

## Low Priority

### `SCAN-RV-009` No Cancel Cleanup Defined

- **Location**: SCAN-FR-02, SCAN-IG-04
- **What**: Spec says "Report archive created on successful completion (not on cancel)" but doesn't specify what happens to partial CSV files on cancel
- **Suggested action**: Clarify: partial files deleted on cancel, or kept in temp location?

### `SCAN-RV-010` 5-Level Nesting May Be Insufficient

- **Location**: SCAN-IG-05
- **What**: Max 5 nesting levels for Azure AD groups is arbitrary
- **Suggested action**: Consider making configurable via query param; or document why 5 is chosen

### `SCAN-RV-011` Error Count in Stats But No Error Log

- **Location**: report.json schema, `stats.errors`
- **What**: Stats include error count but no list of actual errors encountered
- **Suggested action**: Consider adding `errors: [{item_id, error_message}]` array for debugging

## Industry Research Findings

### SharePoint API Throttling (Microsoft Learn)

- **Pattern found**: Apps have resource unit limits per tenant; CSOM/REST cost more than Graph
- **How it applies**: Security scan makes many REST calls; should consider Graph alternatives where possible
- **Source**: https://learn.microsoft.com/en-us/sharepoint/dev/general-development/how-to-avoid-getting-throttled-or-blocked-in-sharepoint-online

**Key points:**
- Honor `Retry-After` header when throttled
- Use `RateLimit` headers (preview) for proactive throttling
- Decorate traffic with app identifier (User-Agent)
- Delta with token costs 1 resource unit (cheaper)
- Batching is evaluated per-request within batch

### Graph API Transitive Members

- **Pattern found**: `/transitivemembers` returns flat list of all nested members in one call
- **How it applies**: Can replace recursive resolution with single Graph call per group
- **Source**: https://learn.microsoft.com/en-us/graph/api/group-list-transitivemembers

**Key points:**
- Returns paged results (handle `@odata.nextLink`)
- More efficient than recursive expansion
- Spec currently describes manual recursion; could simplify with Graph

### Alternatives Considered

- **Graph API instead of REST**: Lower resource cost, better throttling handling. Con: may require different auth setup.
- **Batching role assignments**: Fewer API calls. Con: more complex error handling if one fails.
- **Streaming CSV via generator**: Memory-efficient. Already specified in SCAN-FR-07.

## Recommendations

### Must Do (Before IMPL)

- [ ] Fix SCAN-RV-001: Update action flow to use `scope` param
- [ ] Fix SCAN-RV-002: Update request example in Section 11
- [ ] Fix SCAN-RV-003: Update SCAN-DD-03 for report storage
- [ ] Fix SCAN-RV-008: Update User Actions section

### Should Do

- [ ] Add SCAN-FR-10 or SCAN-IG-06 for throttling handling
- [ ] Add note about Graph pagination in group resolution
- [ ] Add test comparing CSV output with PowerShell reference

### Could Do

- [ ] Consider Graph API transitive members instead of manual recursion
- [ ] Consider batching role assignment queries
- [ ] Add error details array to report.json

## Document History

**[2026-02-03 15:19]**
- Initial review created
- Identified 4 high priority, 4 medium priority, 3 low priority issues
- Researched SharePoint throttling and Graph transitive members
