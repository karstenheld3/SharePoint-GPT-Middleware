# Session Problems

**Doc ID**: 2026-02-03_V2SitesEndpoint-PROBLEMS

## Open

### SCAN-PR-007: V2 vs PowerShell 03_SiteUsers.csv mismatch - SDK limitation

- **Status**: Open (partially fixed)
- **Severity**: Low (4/5 files PASS, only 03_SiteUsers.csv differs)
- **Issue**: V2 missing 3 users that PowerShell includes (user3, user6, empty row)
- **Root cause**: Python SDK `group.users.get()` does not return Entra ID groups (M365/Security) as members of SharePoint groups. PnP PowerShell does.
- **Fixes applied** [TESTED]:
  - Added `skip_users_csv` parameter to exclude subsite users
  - Added `do_not_resolve_these_groups` check at SharePoint group level
  - Added Entra group resolution for direct role assignments (principal_type 4)
  - Added `ScanTest Custom Group` to `do_not_resolve_these_groups`
  - Deleted cached settings file at correct path (`.localstorage/AzureOpenAiProject/sites/`)
- **Remaining**: SDK doesn't return M365/Security groups as SP group members
- **Workaround options**:
  - Use REST API `/_api/web/sitegroups(ID)/users` with $expand
  - Query Entra ID groups separately and match by permission level
  - Accept 4/5 parity as sufficient for current use case

### SCAN-PR-006: Subsite folder HasUniqueRoleAssignments detection - SDK limitation

- **Status**: Open
- **Severity**: Low (98% parity achieved)
- **Issue**: SDK `select(["HasUniqueRoleAssignments"])` does not detect folders with broken inheritance in subsite document libraries
- **Example**: Folder `ArilenaDrovik` in `Subsite01/Shared Documents` not detected by V2 scanner, but detected by PowerShell PnP cmdlet
- **Impact**: V2 achieves 42/43 items (98% parity), outputs 63x more access entries than PowerShell (126 vs 2)
- **Root cause**: SDK may not correctly load HasUniqueRoleAssignments for subsite items when using subsite-scoped ClientContext
- **Related**: SCAN-KL-01 in SPEC, IS-15 in IMPL (pending fix)
- **Workaround options**: REST API for subsites, ensure_property() per item, two-pass scan

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

