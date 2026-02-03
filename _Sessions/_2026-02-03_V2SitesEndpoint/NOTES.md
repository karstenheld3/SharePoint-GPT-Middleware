# Session Notes

**Doc ID**: 2026-02-03_V2SitesEndpoint-NOTES

## Session Info

- **Started**: 2026-02-03
- **Goal**: Add V2 sites endpoint for managing SharePoint sites registered with the middleware

## Current Phase

**Phase**: EXPLORE
**Workflow**: BUILD
**Assessment**: COMPLEXITY-MEDIUM (multiple files, new router, follows existing patterns)

## IMPORTANT: Cascade Agent Instructions

1. Follow patterns from `/v2/domains` router for consistency
2. Use `common_ui_functions_v2.py` for UI generation
3. Sites stored at `PERSISTENT_STORAGE_PATH/sites/{site_id}/site.json`
4. No memory caching - read from disk on each access
5. Use LCGUD endpoint pattern: L(jhu)C(jh)G(jh)U(jh)D(jh)

## User Prompts

### Initial Request (2026-02-03)

````
I want to add a version 2 sites endpoint.

The endpoint can create, update and delete SharePoint sites that are registered with the middleware. 
New endpoint definition (read _V2_SPEC_ROUTERS.md)

L(jhu)C(jh)G(jh)U(jh)D(jh): `/v2/sites` - SharePoint sites that are accessible via the middleware

We want to first create specs (functional and ui), then see how we can integrate the endpoint in the existing application, then create IMPL, TEST and TASKS plans. And then create and test the endpoint.

The look and feel should be copied from the domains endpoint.
All sites are stored in the PERSISTENT_STORAGE_PATH/sites folder.
Each site has its own subfolder PERSISTENT_STORAGE_PATH/sites/site_id
The site data for each site is stored in a site.json file (analog to domain.json)
Sites are not cached in memory. Each read access (list, get) reads the sites from PERSISTENT_STORAGE_PATH.

We want the following buttons in the action row above the table:
[New Site] - Registers new SharePoint with site_id, site_name and site_url via dialog
[Run Selftest] - Test all endpoint functionality to ensure that we can read, write, update sites

We want the following table fields:
Site ID - internal site_id (unique) -> this is a subfolder in the PERSISTENT_STORAGE_PATH/sites/
Name - Internal "name", the site display name -> stored in site.json
Site URL - The site_url (trailing slash will be removed upon create or update) -> stored in site.json
Files - Internal file_scan_result, result of site file scan operation (read-only in edit dialog) -> stored in site.json
Security - Internal security_scan_result, result of site security scan operation (read-only in edit dialog) -> stored in site.json
Actions - [Edit] [Delete] [File Scan] [Security Scan]

[File Scan] and [Security Scan] are grey buttons without links for now
````

## Key Decisions

- Follow domains router pattern exactly for consistency
- Site ID derived from folder name (not stored in site.json)
- Trailing slash removal on site_url during create/update
- Scan result fields are read-only in UI

## Important Findings

- Domains router uses `common_ui_functions_v2.py` generate_ui_page() for table rendering
- Storage pattern: `PERSISTENT_STORAGE_PATH/sites/{site_id}/site.json`
- LCGUD format explained in `_V2_SPEC_ROUTERS.md`

## Topic Registry Addition

- `SITE` - SharePoint Sites management

## Workflows to Run on Resume

1. `/recap` - Review current state
2. `/continue` - Execute next pending items

