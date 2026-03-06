# Session Notes

**Doc ID**: 2026-03-06_V2CrawlerEndpoint-NOTES

## Session Info

- **Started**: 2026-03-06
- **Goal**: V2 Crawler Endpoint development and documentation

## Current Phase

**Phase**: DELIVER
**Workflow**: Doc sync complete
**Assessment**: [TESTED] Implementation complete, tested with live SharePoint data (6 items, 15 fields exported)

## Document Sync Pattern

This session uses a **doc-sync workflow**:

**Source**: `docs/routers_v2/_V2_*.md`
**Session Copy**: All V2 SPEC/IMPL docs copied to session folder

**On Session Load** (`/session-load`):
1. Load session tracking files (NOTES, PROGRESS, PROBLEMS)
2. Load reference docs:
   - `docs/V2_INFO_IMPLEMENTATION_PATTERNS.md`
   - `SOPS.md`
3. V2 docs are already in session folder (copied on init)

**On Session Save/Close** (`/session-save`, `/session-finalize`):
1. Copy modified `_V2_*.md` files back to `docs/routers_v2/`
2. Commit changes

## Workflows to Run on Resume

```
/session-load
```

**Files to load on resume:**
- `docs/V2_INFO_IMPLEMENTATION_PATTERNS.md`
- `SOPS.md`
- All `_V2_*.md` in session folder

## IMPORTANT: Cascade Agent Instructions

1. **Doc sync on save/close**: Before closing session, copy all modified `_V2_*.md` files back to `docs/routers_v2/`
2. **Reference patterns**: Check `V2_INFO_IMPLEMENTATION_PATTERNS.md` for established V2 patterns
3. **SOPs**: Follow `SOPS.md` for V2 router/endpoint procedures
4. **Dependency management**: Run `InstallAndCompileDependencies.bat` after adding new imports
5. **Report type naming**: Use singular form (`"crawl"`, not `"crawls"`)
6. **Async generator pattern**: Use `AsyncGenerator[str, None]` for SSE streaming

## Key Decisions

- [TESTED] Use `.md` (Markdown) as default embedded format for list items (more readable for LLM)
- [TESTED] Use pipe `|` as multi-value separator, semicolon `;` for multi-user fields
- [TESTED] DateTime format: `YYYY-MM-DD HH:mm:ss` (RFC3339-like, Excel compatible)
- [TESTED] Skip Modified/Created fields in Markdown (system timestamps not useful for embedding)
- [TESTED] Title always first in Markdown body (aids search)
- [TESTED] CSV column order: ID, Title, alphabetical user fields, Created, Modified
- [TESTED] Plain markdown output - no code fences

## Important Findings

- Current implementation loses all list item content - only ID, Title, Modified captured
- `get_list_items()` returns full properties but `get_list_items_as_sharepoint_files()` discards them
- PowerShell reference implementation in `_input/` shows proper column type conversions
- See `_INFO_SHAREPOINT_LIST_COLUMN_TYPES.md [V2CR-IN01]` for complete conversion reference

## V2 Documents in Session

### Specifications (SPEC)
- `_V2_SPEC_ROUTERS.md` - Main V2 router specification (required for all router sessions)
- `_V2_SPEC_CRAWLER_UI.md` - Crawler UI specification
- `_V2_SPEC_COMMON_UI_FUNCTIONS.md` - Common UI functions

### Implementation Plans (IMPL)
- `_V2_IMPL_CRAWLER.md` - Crawler implementation
- `_V2_IMPL_CRAWLER_SELFTEST.md` - Crawler self-test

### Session Documents
- `_INFO_SHAREPOINT_LIST_COLUMN_TYPES.md [V2CR-IN01]` - SharePoint field type conversion research
- `_SPEC_CRAWLER_LISTS.md [V2CR-SP01]` - List item export specification
