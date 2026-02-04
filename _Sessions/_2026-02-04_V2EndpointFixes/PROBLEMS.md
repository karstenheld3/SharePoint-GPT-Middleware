# Session Problems

**Doc ID**: 2026-02-04_V2EndpointFixes-PROBLEMS

## Open

**V2FX-PR-001: Job appearance inconsistency between /v2/crawler and /v2/jobs**
- **History**: Added 2026-02-04 12:52
- **Description**: Stalled and running jobs in /v2/crawler UI should have the same bold appearance and force delete options as in /v2/jobs
- **Impact**: Inconsistent UX across related endpoints
- **Next Steps**: Compare job rendering in both routers, align /v2/crawler with /v2/jobs styling

**V2FX-PR-002: Broken navigation links with URL-encoded placeholder**
- **History**: Added 2026-02-04 12:52
- **Description**: Navigation links show `/v2/%7Brouter_prefix%7D/reports?format=ui` instead of proper URLs. The `{router_prefix}` placeholder is being URL-encoded instead of substituted.
- **Impact**: Navigation between V2 endpoints is broken in some cases
- **Next Steps**: Audit all V2 routers for `{router_prefix}` usage in navigation HTML, fix f-string interpolation

**V2FX-PR-003: Missing "Query" link in /v2/domains rows**
- **History**: Added 2026-02-04 12:52
- **Description**: Domain rows in /v2/domains should provide a "Query" link to the query2 endpoint, as implemented in /v1/domains
- **Impact**: Users must manually navigate to query endpoint for each domain
- **Next Steps**: Add query2 link to domain row actions in domains_v2.py

**V2FX-PR-004: Vector Store ID not clickable in /v2/domains**
- **History**: Added 2026-02-04 12:52
- **Description**: "Vector Store ID" column cells should link to `/v1/inventory/vectorstore_files?vector_store_id=[VSID]&format=ui`
- **Impact**: Users cannot quickly view vector store contents from domain list
- **Next Steps**: Make vector_store_id a hyperlink in domain row rendering

**V2FX-PR-005: Crawler Selftest creates excessive job files**
- **History**: Added 2026-02-04 12:52
- **Description**: Crawler Selftest leaves too many jobs. All sub-jobs except the first main job should be deleted immediately after finishing.
- **Impact**: Job list clutter, disk space usage
- **Next Steps**: Modify selftest to delete child jobs after completion

## Resolved

(none yet)

## Deferred

(none yet)

## Problems Changes

**[2026-02-04 12:52]**
- Added: V2FX-PR-001 (job appearance inconsistency)
- Added: V2FX-PR-002 (broken navigation links)
- Added: V2FX-PR-003 (missing Query link)
- Added: V2FX-PR-004 (Vector Store ID not clickable)
- Added: V2FX-PR-005 (excessive selftest jobs)
