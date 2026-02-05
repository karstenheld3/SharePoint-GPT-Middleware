# Session Problems

**Doc ID**: BugFixes-PROBLEMS

## Open

(none)

## Resolved

**V2FX-PR-001: Domains UI not updated after creating new domain**
- **History**: Added 2026-02-05 15:18 | Resolved 2026-02-05 15:52
- **Description**: After creating a new domain via UI, the table does not show the new domain.
- **Root Cause**: JavaScript function hoisting - using `async function reloadItems()` declaration caused `_originalReloadItems` to capture the override itself, creating infinite recursion.
- **Solution**: Changed to function expression assignment: `reloadItems = async function() {...}`
- **Verification**: Tested with Playwright - created domain appears immediately, Crawl button works

**V2FX-PR-002: domainsState cache not updated after CRUD operations**
- **History**: Added 2026-02-05 15:18 | Resolved 2026-02-05 15:52
- **Description**: The `domainsState` Map used by `showCrawlDomainForm()` was only populated on page load
- **Solution**: Override `reloadItems()` to also call `cacheDomains()` after table refresh
- **Verification**: "Crawl" button opens form correctly for newly created domains

## Deferred

(none yet)

## Problems Changes

**[2026-02-05 15:18]**
- Added: V2FX-PR-001 (UI not updated after create)
- Added: V2FX-PR-002 (domainsState cache stale)
