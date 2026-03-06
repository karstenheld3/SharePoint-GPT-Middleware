# Session Problems

**Doc ID**: BugFixes-PROBLEMS

## Open

(none)

## Resolved

**V2FX-PR-004: Crawler selftest fails after V2CR-SP01 list export changes**
- **History**: Added 2026-03-06 14:54 | Resolved 2026-03-06 14:55
- **Description**: 9 selftest failures after list export changed from CSV to MD files
- **Root Cause**: Commit 5cc8c73 exports lists as MD (embeddable) creating 1 files_map entry per source, but SNAP_FULL_ALL/SNAP_FULL_LISTS expected 0
- **Solution**: Updated snapshot expectations from 0 to 1 for list sources
- **Verification**: Commit d5ab1c1

**V2FX-PR-003: Selftest dialog and console close automatically after completion**
- **History**: Added 2026-03-06 14:27 | Resolved 2026-03-06 14:27
- **Description**: After running selftest on Domains UI, the results dialog closes and console hides automatically
- **Root Cause**: Selftest button had `data_reload_on_finish: "true"` which triggered `reloadItems()` -> `window.location.reload()`
- **Solution**: Changed to `data_reload_on_finish: "false"` for selftest button
- **Verification**: Tested with Playwright - dialog and console stay open after selftest completes

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

**[2026-03-06 14:55]**
- Added: V2FX-PR-004 (Crawler selftest snapshot expectations) - Resolved

**[2026-03-06 14:30]**
- Updated: V2FX-PR-003 - Added pattern to V2_INFO_IMPLEMENTATION_PATTERNS.md, fixed all routers

**[2026-03-06 14:27]**
- Added: V2FX-PR-003 (Selftest dialog/console auto-close) - Resolved

**[2026-02-05 15:18]**
- Added: V2FX-PR-001 (UI not updated after create)
- Added: V2FX-PR-002 (domainsState cache stale)
