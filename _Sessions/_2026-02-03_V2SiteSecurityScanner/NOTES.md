# Session Notes

**Doc ID**: 2026-02-03_V2SiteSecurityScanner-NOTES

## Session Info

- **Started**: 2026-02-03
- **Split from**: `_2026-02-03_V2SitesEndpoint` on 2026-03-02
- **Goal**: Security scanner implementation for SharePoint sites

## Current Phase

**Phase**: REFINE
**Workflow**: BUILD
**Assessment**: COMPLEXITY-MEDIUM
**Last Activity**: 2026-02-21 18:45 - V2 vs PowerShell output alignment (4/5 files PASS)

## IMPORTANT: Cascade Agent Instructions

1. Security scan functions in `common_security_scan_functions_v2.py`
2. SSE streaming requires `await asyncio.sleep(0)` after yields with blocking I/O
3. Scanner settings cached at `.localstorage/AzureOpenAiProject/sites/security_scan_settings.json`
4. PowerShell scanner requires PowerShell 7+ (pwsh)

## User Prompts

### Permission Scanner Assessment (2026-02-03 09:51)

````
Read:
- MasteringSharePointPermissions.md
- _SPEC_SHAREPOINT_PERMISSION_INSIGHTS_SCANNER.md
- PermissionInsightsScanner/_includes.ps1
- PermissionInsightsScanner/PermissionInsightsScanner.ps1

We want to assess how we can implement a similar exhaustive permission scanning 
functionality in our middleware using Python.

The goal is to produce similar output files as the result of the permission scanning:
- 0002 spst - BrokenPermissionInheritanceSubsite01
- 0003 spst - Shared Documents
- 0004 spst - Shared Documents - SharedByRequest

It should contain all cases of SharePoint permissions (via inheritance or via broken 
permission inheritance) that we must cover. We must include all cases so that as a 
result we see 100% of people who have access to a site or site element (libraries, 
lists, folders, files).

Then as a next step we have to create an inventory of all used API calls in the 
PowerShell script and how to map them to Python libraries and API calls. This 
assessment must be very detailed.

/write-strut first write a strut for this assessment to keep track of all activities.
Analyze the existing PowerShell script and output files in detail.
Then go /research all API mapping options.
/write-info _INFO_SITE_PERMISSION_SCANNER_ASSESSMENT.md
Record this prompt as outlined in NOTES_TEMPLATE.md in session management skill.
````

**Output**: `_INFO_SITE_PERMISSION_SCANNER_ASSESSMENT.md [PERM-IN01]`

### PowerShell Scanner Optimization (2026-02-19)

````
Research: How can we optimize performance of SharePointPermissionScanner.ps1?
Currently it takes way too long - list elements are scanned individually.
Write _INFO_SITE_PERMISSION_SCANNER_ASSESSMENT_POWERSHELL.md for PnP PowerShell only.
Then /critique and /reconcile to validate findings.
Then /write-tasks-plan for incremental improvements.
````

**Output**: `_INFO_SITE_PERMISSION_SCANNER_ASSESSMENT_POWERSHELL.md [PSCP-IN02]`
**Review**: `_INFO_SITE_PERMISSION_SCANNER_ASSESSMENT_POWERSHELL_REVIEW.md [PSCP-IN02-RV01]`
**Tasks**: `TASKS_PERMISSION_SCANNER_POWERSHELL_OPTIMIZATION.md [PSCP-TK01]`

## Key Decisions

- Use Office365-REST-Python-Client for SharePoint API
- Use msgraph-sdk for Entra ID group resolution
- CSV output format matches PowerShell scanner
- SSE streaming for realtime progress

## Important Findings

### PnP PowerShell GET Batching [TESTED 2026-02-19]

**Finding**: `Invoke-PnPSPRestMethod -Batch` does NOT work correctly for GET requests on RoleAssignments.
- Batch method returns 0 role assignments per item
- Per-item method returns 5 role assignments (correct)
- **Conclusion**: GET batching returns empty/incorrect data - cannot use for optimization

**Impact**: Phase 3 of Permission Scanner optimization skipped. Use per-item Load-CSOMProperties.

### Scanner Settings File Location [TESTED 2026-02-21]

**Finding**: Scanner settings file is stored at `.localstorage/AzureOpenAiProject/sites/security_scan_settings.json`, NOT `local_storage/sites/`.

**Impact**: When updating `DEFAULT_SECURITY_SCAN_SETTINGS` in hardcoded_config.py, must delete the correct cached settings file.

### PowerShell Version Requirement [TESTED 2026-02-21]

**Finding**: PowerShell scanner requires **PowerShell 7+** (pwsh), not Windows PowerShell 5.1.
- PnP.PowerShell module installed in PS7 path: `C:\Users\<user>\Documents\PowerShell\Modules\`
- Windows PS5.1 path: `C:\Users\<user>\Documents\WindowsPowerShell\Modules\`

**Symptom**: `The term 'Connect-PnPOnline' is not recognized...`

**Fix**: Use `pwsh -ExecutionPolicy Bypass -File ...` instead of `powershell.exe`

### SSE Streaming Pattern [TESTED]

**For async generators with blocking sync I/O (like SharePoint `execute_query()`):**
```python
async for event in nested_generator_with_blocking_io():
    yield event
    await asyncio.sleep(0)  # Force event loop to flush HTTP response
```

**Why needed**: Blocking sync I/O prevents event loop from flushing HTTP response chunks to browser. Curl works without this because it processes data at TCP level. Browser fetch API requires explicit event loop yields.

**See**: `SCAN-LN-002` in LEARNINGS.md, `SCAN-PR-005` in PROBLEMS.md

## Topic Registry

- `SCAN` - Security Scanner
- `PSCP` - Permission Scanner POC

## Related Sessions

- Sites endpoint work: `_2026-02-03_V2SitesEndpoint` (completed)

## Workflows to Run on Resume

1. `/recap` - Review current state
2. `/continue` - Execute next pending items

