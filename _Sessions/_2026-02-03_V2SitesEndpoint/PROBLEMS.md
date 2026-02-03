# Session Problems

**Doc ID**: 2026-02-03_V2SitesEndpoint-PROBLEMS

## Open

### SCAN-PR-005: Browser SSE buffering with async generators - root cause not fully understood

- **Status**: Open (workaround applied)
- **Severity**: Medium
- **Workaround**: `await asyncio.sleep(0)` after each yield forces event loop flush
- **Issue**: Browser UI doesn't receive SSE events in realtime for security scan, but works for selftest. Curl works for both.
- **Hypothesis**: Blocking sync I/O (SharePoint `execute_query()`) prevents event loop from flushing HTTP response chunks
- **Unknown**: Why exactly does curl work but browser doesn't? What triggers Starlette/uvicorn to flush?
- **Related**: `SCAN-FL-005`, `SCAN-LN-002`
- **TODO**: Deep investigation into uvicorn/Starlette StreamingResponse flushing behavior

## Resolved

### SITE-PR-001: Define site.json schema

- **Status**: Resolved (2026-02-03)
- **Resolution**: `SiteConfig` dataclass in `sites.py:44-50` defines schema
- **Fields**: `site_id`, `name`, `site_url`, `file_scan_result`, `security_scan_result`

### SITE-PR-002: Integrate sites router into app.py

- **Status**: Resolved (2026-02-03)
- **Resolution**: Router included at `app.py:515-516` with `set_config()`

### SITE-PR-003: Add sites folder to hardcoded_config.py

- **Status**: Resolved (2026-02-03)
- **Resolution**: `PERSISTENT_STORAGE_PATH_SITES_SUBFOLDER="sites"` at line 36

### SITE-PR-004: Implement placeholder scan buttons

- **Status**: Resolved (2026-02-03)
- **Resolution**: Sites router implemented with full UI including scan button placeholders

## Deferred

(None yet)

