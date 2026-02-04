# Session Notes

**Doc ID**: 2026-02-04_V2EndpointFixes-NOTES

## Initial Request

````text
I want to do a number of small improvements and fixes:
- Stalled and running jobs in /v2/crawler should have the same appearance (bold) and options (force delete) as in /v2/jobs
- Navigation links in /v2/[endpoint] must be checked for all v2 endpoints. Sometimes we get broken links like this: /v2/%7Brouter_prefix%7D/reports?format=ui
- Domain rows in /v2/domains should also provide a "Query" link to the query2 endpoint as it is implemented in /v1/domains
- Domain row cells in column "Vector Store ID" should be a link to /v1/inventory/vectorstore_files?vector_store_id=[VSID]&format=ui
- Crawler Selftest leaves too many jobs that it subsequently creates. All except the first main job should be deleted immediately after being finished.
````

## Session Info

- **Started**: 2026-02-04
- **Goal**: Fix V2 endpoint UI consistency and navigation issues
- **Operation Mode**: IMPL-CODEBASE
- **Output Location**: src/routers_v2/

## Current Phase

**Phase**: EXPLORE
**Workflow**: (pending assessment)
**Assessment**: (pending)

## Agent Instructions

- Follow SOPS.md for V2 router modifications
- Maintain V2 navigation consistency across all routers (Back to Main Page | Domains | Sites | Crawler | Jobs | Reports)
- Use `{router_prefix}` placeholder correctly in URLs

## Key Decisions

(none yet)

## Important Findings

(none yet)

## Topic Registry

- `V2FX` - V2 Endpoint Fixes (this session)

## Significant Prompts Log

(none yet)
