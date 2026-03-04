# INFO: Logging Harmonization - File Inventory

**Doc ID**: LOG-IN03
**Goal**: Exhaustive list of all files, scripts, and features using logging for harmonization
**Timeline**: Created 2026-03-04

## Summary

- **Python**: 31 files with logging (1469 matches total)
- **Python SSE**: 29 files with SSE streaming (1050 matches) - overlaps with logging
- **PowerShell**: 21 scripts with logging (691 matches total, excluding .venv)
- **Batch files**: 12 wrapper scripts (minimal logging, call .ps1 scripts)
- **Test files**: 4 Python test files, 7 PowerShell test scripts
- **Logging infrastructure**: 2 Python modules (V1 and V2)
- **Logging rules**: 4 documentation files in `.windsurf/skills/coding-conventions/`

## Table of Contents

1. [Logging Infrastructure](#1-logging-infrastructure)
2. [Python Files with Logging](#2-python-files-with-logging)
3. [PowerShell Scripts with Logging](#3-powershell-scripts-with-logging)
4. [Test Files](#4-test-files)
5. [Logging Rules Documentation](#5-logging-rules-documentation)

## 1. Logging Infrastructure

### Python Logging Modules

- `src/routers_v1/common_logging_functions_v1.py` (10 matches)
  - Standalone logging functions
  - Console format: `[timestamp,process PID,request N,function_name] message`

- `src/routers_v2/common_logging_functions_v2.py` (11 matches)
  - `MiddlewareLogger` dataclass with request-scoped state
  - Methods: `log_function_header()`, `log_function_output()`, `log_function_footer()`
  - Auto-indentation based on nesting depth (2 spaces per level)
  - Optional SSE streaming via `stream_job_writer` parameter

### PowerShell Logging Infrastructure

- `tests/SiteSecurityScan/SharePointPermissionScanner/_includes.ps1` (10 matches)
  - `Write-ScriptHeader`, `Write-ScriptFooter` functions
  - `Get-DisplayFileSize` utility
  - Shared across all Permission Scanner scripts

## 2. Python Files with Logging

### High Usage (>50 matches)

- `src/routers_v1/crawler.py` - 141 matches (Router)
- `src/routers_v2/common_sharepoint_functions_v2.py` - 141 matches (Shared functions)
- `src/routers_v1/router_crawler_functions_v1.py` - 115 matches (Router functions)
- `src/routers_static/openai_proxy.py` - 104 matches (Static router)
- `src/routers_v2/crawler.py` - 95 matches (Router)
- `src/routers_v2/demorouter1.py` - 74 matches (Demo router)
- `src/routers_v2/demorouter2.py` - 71 matches (Demo router)
- `src/routers_v2/sites.py` - 70 matches (Router)
- `src/routers_v1/inventory.py` - 68 matches (Router)
- `src/routers_v1/domains.py` - 64 matches (Router)
- `src/routers_v2/jobs.py` - 61 matches (Router)
- `src/test_sharepoint_access_with_app_registration.py` - 61 matches (Selftest)
- `src/routers_v2/common_sharepoint_functions_v2_test.py` - 56 matches (Test)
- `src/routers_v2/domains.py` - 51 matches (Router)
- `src/routers_v2/reports.py` - 51 matches (Router)

### Medium Usage (10-50 matches)

- `src/app.py` - 48 matches (Main app)
- `src/routers_static/sharepoint_search.py` - 46 matches (Static router)
- `src/common_utility_functions.py` - 21 matches (Utilities)
- `src/routers_v2/common_crawler_functions_v2.py` - 20 matches (Shared functions)
- `src/routers_v1/common_openai_functions_v1.py` - 19 matches (OpenAI functions)
- `src/routers_v2/common_openai_functions_v2.py` - 18 matches (OpenAI functions)
- `src/routers_v2/common_report_functions_v2.py` - 15 matches (Report functions)
- `src/routers_v2/common_report_functions_v2_test.py` - 12 matches (Test)

### Low Usage (<10 matches)

- `src/routers_v1/common_sharepoint_functions_v1.py` - 10 matches (Shared functions)
- `src/routers_v2/common_embed_functions_v2.py` - 4 matches (Embed functions)
- `src/routers_v2/common_security_scan_functions_v2.py` - 4 matches (Security scan)
- `src/test_azure_openai_access_with_service_principal.py` - 4 matches (Selftest)
- `src/test_azure_openai_access_with_api_key.py` - 3 matches (Selftest)
- `src/routers_v2/common_job_functions_v2.py` - 1 match (Job functions)
- `src/routers_v2/common_ui_functions_v2.py` - 5 SSE matches (UI functions)
- `src/routers_v2/common_map_file_functions_v2.py` - 3 SSE matches (Map file functions)
- `src/routers_v1/common_ui_functions_v1.py` - (UI functions V1)
- `src/routers_v1/common_job_functions_v1.py` - 1 match (Job functions V1)
- `src/hardcoded_config.py` - 3 SSE matches (Config)

## 3. PowerShell Scripts with Logging

### Workspace Root Scripts (Production)

- `AddRemoveCrawlerPermissions.ps1` - 73 matches (Manage Entra ID app permissions)
- `AddRemoveCrawlerSharePointSites.ps1` - 73 matches (Manage Sites.Selected permissions)
- `CreateAzureAppService.ps1` - 28 matches (Create Azure App Service)
- `DeployAzureAppService.ps1` - 23 matches (Deploy to Azure)
- `DeleteAzureAppService.ps1` - 11 matches (Delete Azure App Service)
- `CreateSelfSignedCertificate.ps1` - 1 match (Generate certificate)

### Batch File Wrappers (minimal logging)

- `AddRemoveCrawlerPermissions.bat` - Calls .ps1
- `AddRemoveCrawlerSharePointSites.bat` - Calls .ps1
- `CreateAzureAppService.bat` - Calls .ps1
- `CreateSelfSignedCertificateRunAsAdmin.bat` - Calls .ps1
- `DeleteAzureAppService.bat` - Calls .ps1
- `DeployAzureAppService.bat` - Calls .ps1
- `InstallAndCompileDependencies.bat` - Python/pip commands
- `Set-AzureOpenAiProject-Env.bat` - Environment setup
- `Set-AzureOpenAiService-Env.bat` - Environment setup
- `Set-OpenAi-Env.bat` - Environment setup
- `Set-OpenAiOld-Env.bat` - Environment setup
- `Windsurf.bat` - IDE launch

### Test Scripts (tests/SiteSecurityScan/)

- `SharePointPermissionScanner/SharePointPermissionScanner.ps1` - 43 matches (Main scanner script)
- `01_RunAll.ps1` - 35 matches (Test orchestrator)
- `04_RunV2SecurityScan.ps1` - 24 matches (V2 API test)
- `03_RunPowerShellScanner.ps1` - 11 matches (PowerShell scanner test)
- `05_CompareOutputs.ps1` - 11 matches (Output comparison)
- `SharePointPermissionScanner/_includes.ps1` - 10 matches (Shared functions)
- `02_SetupSharePointPermissionScanner.ps1` - 6 matches (Setup script)

### Session Scripts (archived/POC)

- `_Sessions/.../01_Create_EntraID_UsersAnd_Groups.ps1` - 46 matches (Test data setup)
- `_Sessions/.../POC_BatchedRoleAssignments.ps1` - 44 matches (POC)
- `_Sessions/.../SharePointPermissionScanner.ps1` - 43 matches (Original scanner)
- `_Sessions/.../02_Create_SharePoint_Permission_Cases.ps1` - 34 matches (Test data setup)
- `_Sessions/.../04_Remove_EntraID_UsersAnd_Groups.ps1` - 30 matches (Test data cleanup)
- `_Sessions/.../03_Remove_SharePoint_Permission_Cases.ps1` - 21 matches (Test data cleanup)
- `_Sessions/.../POC_BulkHasUniqueRoleAssignments.ps1` - 14 matches (POC)
- `_Sessions/.../_includes.ps1` - 10 matches (Shared functions)

## 4. Test Files

### Python Test Files

- `src/routers_v2/common_sharepoint_functions_v2_test.py` (56 matches)
- `src/routers_v2/common_report_functions_v2_test.py` (12 matches)
- `_Sessions/.../poc_security_scanner/02A_test_poc_core_functionality.py`
- `_Sessions/.../poc_security_scanner/02B_test_poc_performance.py`

### Python Selftest Files

- `src/test_sharepoint_access_with_app_registration.py` (61 matches)
- `src/test_azure_openai_access_with_service_principal.py` (4 matches)
- `src/test_azure_openai_access_with_api_key.py` (3 matches)

### PowerShell Test Scripts

- `tests/SiteSecurityScan/01_RunAll.ps1` - Test orchestrator
- `tests/SiteSecurityScan/02_SetupSharePointPermissionScanner.ps1` - Setup
- `tests/SiteSecurityScan/03_RunPowerShellScanner.ps1` - PowerShell scanner
- `tests/SiteSecurityScan/04_RunV2SecurityScan.ps1` - V2 API test
- `tests/SiteSecurityScan/05_CompareOutputs.ps1` - Output comparison

## 5. Logging Rules Documentation

### Current Documentation

- `.windsurf/skills/coding-conventions/LOGGING-RULES.md` - General rules (LOG-GN-01 to LOG-GN-11)
- `.windsurf/skills/coding-conventions/LOGGING-RULES-USER-FACING.md` - User-facing rules (LOG-UF-01 to LOG-UF-06)
- `.windsurf/skills/coding-conventions/LOGGING-RULES-APP-LEVEL.md` - App-level rules (LOG-AP-01 to LOG-AP-05)
- `.windsurf/skills/coding-conventions/LOGGING-RULES-TEST-LEVEL.md` - Script-level rules (LOG-SC-01 to LOG-SC-07)

### Session INFO Documents

- `_Sessions/_2026-03-04_LoggingHarmonization/_INFO_V2_LOGGING_PRACTICES.md` [LOG-IN01]
- `_Sessions/_2026-03-04_LoggingHarmonization/_INFO_POWERSHELL_LOGGING_PRACTICES.md` [LOG-IN02]

## Harmonization Scope

### Files Requiring Updates (if rules change)

**Priority 1 - High Impact:**
- `src/routers_v2/common_logging_functions_v2.py` - Logging infrastructure
- `src/routers_v1/common_logging_functions_v1.py` - Logging infrastructure
- `tests/SiteSecurityScan/SharePointPermissionScanner/_includes.ps1` - PS infrastructure

**Priority 2 - High Usage:**
- `src/routers_v1/crawler.py` (141 matches)
- `src/routers_v2/common_sharepoint_functions_v2.py` (141 matches)
- `src/routers_v1/router_crawler_functions_v1.py` (115 matches)
- `AddRemoveCrawlerPermissions.ps1` (73 matches)
- `AddRemoveCrawlerSharePointSites.ps1` (73 matches)

**Priority 3 - Test Files:**
- All files in `tests/SiteSecurityScan/`
- All `*_test.py` files

## 6. Pattern Analysis and Rule Checklists

### Observed Patterns in Codebase

**Python App-Level (MiddlewareLogger):**
- `START: function_name()...` / `END: function_name() (duration).`
- Console format: `[timestamp,process PID,request N,function_name] message`
- SSE format: `[YYYY-MM-DD HH:MM:SS] message`
- 2-space indentation per nesting level
- Status keywords: `OK.`, `ERROR:`, `WARNING:`, `FAIL:`, `SKIP:`
- Progress: `[ x / n ] Action...`
- Properties: `key='value'` format
- Error chains: `ERROR: context -> error_message`
- Summaries: Numbers first (`3 created, 1 failed.`)

**PowerShell Scripts:**
- Header: `===... START: TITLE ...===` (100 chars)
- Footer: `===... END: TITLE ...===` + timestamp + duration
- Progress: `[ x / n ]` format (matches Python)
- Colors: Green=OK, Yellow=Warning, Red=Error
- 2-space indentation (matches Python)

**Python Tests:**
- Section: `===` (60 chars) separators
- Status: `OK:`, `FAIL:`, `SKIP:` with test name
- Summary: `OK: x, FAIL: y, SKIP: z`
- No timestamps (deterministic)

### User-Facing Checklist (LOG-UF)

For each file producing user-visible output:

- [ ] **LOG-UF-01** Timestamp format `[YYYY-MM-DD HH:MM:SS]`
- [ ] **LOG-UF-02** Progress uses `[ x / n ]` at line start
- [ ] **LOG-UF-02** Nested progress uses `( x / n )`
- [ ] **LOG-UF-03** Status keywords: `OK.`, `ERROR:`, `WARNING:`, `FAIL:`
- [ ] **LOG-UF-03** Summaries use numbers first (`3 added, 1 failed.`)
- [ ] **LOG-UF-04** Feedback every ~10 seconds for long operations
- [ ] **LOG-UF-05** 2-space indentation per hierarchy level
- [ ] **LOG-UF-06** Scripts use 100-char START/END headers/footers
- [ ] **Full Disclosure** Each section self-contained (filenames, URLs included)

**Python Files to Check:**
- `common_logging_functions_v2.py` - SSE timestamp format
- All routers with `stream_job_writer` - progress indicators
- `common_sharepoint_functions_v2.py` - iteration logging

**PowerShell Files to Check:**
- `_includes.ps1` - `Write-ScriptHeader`/`Write-ScriptFooter` (100 chars)
- All production scripts - progress format

### App-Level Checklist (LOG-AP)

For each file producing server/debug logs:

- [ ] **LOG-AP-01** Extended timestamp with PID and request number
- [ ] **LOG-AP-02** Log levels used appropriately (INFO, WARNING, ERROR)
- [ ] **LOG-AP-03** Properties use `key='value'` format
- [ ] **LOG-AP-04** Functions use `START:` / `END:` markers
- [ ] **LOG-AP-04** Duration shown in footer `(X.X secs)`
- [ ] **LOG-AP-05** Error chains preserve context `-> error_message`
- [ ] **LOG-GN-01** 2-space indentation per nesting level
- [ ] **LOG-GN-03** Numbers and counters first in results

**Python Files to Check:**
- `common_logging_functions_v2.py` - console format implementation
- `common_logging_functions_v1.py` - V1 format consistency
- All files using `logger.log_function_*` methods

### Script-Level Checklist (LOG-SC)

For each test/selftest file:

- [ ] **LOG-SC-01** No timestamps (deterministic output)
- [ ] **LOG-SC-02** 100-char START/END headers/footers
- [ ] **LOG-SC-02** Phase headers use `===== Phase N: Name =====`
- [ ] **LOG-SC-03** Test cases have IDs (`TC-01:`, `M1:`)
- [ ] **LOG-SC-04** Status markers: `OK:`, `FAIL:`, `SKIP:`, `EXPECTED FAIL:`
- [ ] **LOG-SC-05** Failures show expected vs actual values
- [ ] **LOG-SC-06** Errors include full context for debugging
- [ ] **LOG-SC-07** Summary with counts and RESULT line

**Python Test Files to Check:**
- `common_sharepoint_functions_v2_test.py` - section separators, status format
- `common_report_functions_v2_test.py` - summary format
- `test_sharepoint_access_with_app_registration.py` - selftest format

**PowerShell Test Files to Check:**
- `tests/SiteSecurityScan/01_RunAll.ps1` - orchestrator logging
- `tests/SiteSecurityScan/05_CompareOutputs.ps1` - comparison output

### General Rules Checklist (LOG-GN)

For ALL files with logging:

- [ ] **LOG-GN-01** 2-space indentation (not tabs, not 4 spaces)
- [ ] **LOG-GN-02** Properties: `key='value'` with single quotes
- [ ] **LOG-GN-03** Numbers first in results (`5 files processed.`)
- [ ] **LOG-GN-03** Counters first in progress (`[ 1 / 5 ] Processing...`)
- [ ] **LOG-GN-04** Arrow convention for nested details (`->`)
- [ ] **LOG-GN-05** Singular/plural handling (`1 file` vs `2 files`)
- [ ] **LOG-GN-06** Additional properties in parentheses `(key='value')`
- [ ] **LOG-GN-07** Duration format consistent (`X.X secs`, `X mins Y secs`)
- [ ] **LOG-GN-08** `UNKNOWN = '[UNKNOWN]'` for missing values
- [ ] **LOG-GN-09** Announce-Track-Report pattern followed
- [ ] **LOG-GN-10** Two-level errors (summary + details)
- [ ] **LOG-GN-11** Error chains preserve full context

### Compliance Summary

**Currently Compliant:**
- 2-space indentation (Python and PowerShell)
- `[ x / n ]` progress format
- `START:` / `END:` markers
- `OK.`, `ERROR:`, `WARNING:` keywords
- Numbers first in summaries
- `key='value'` property format
- Duration formatting

**Needs Review:**
- PowerShell header/footer width uses dynamic calculation `(52 - (title.Length / 2))` - NOT fixed 100 chars [VERIFIED]
- Python test section separators use 60 chars (`'=' * 60`) - NOT 100 chars [VERIFIED]
- Test summary format varies: `OK: x, FAIL: y` vs `x passed, y failed` [VERIFIED]
- Full Disclosure in comparison outputs
- No `( x / n )` nested progress format found in codebase [VERIFIED] - rule may be aspirational

## Next Steps

1. Rename `LOGGING-RULES-TEST-LEVEL.md` to `LOGGING-RULES-SCRIPT-LEVEL.md`
2. Update all LOG-TS-* references to LOG-SC-*
3. Update session PROBLEMS.md with resolved items
4. Review PowerShell `Write-ScriptHeader` for 100-char compliance
5. Standardize test section separators to 100 chars

## Document History

**[2026-03-04 20:21]**
- Verified: PowerShell header uses dynamic width, not fixed 100 chars
- Verified: Python tests use 60-char separators, not 100 chars
- Verified: No `( x / n )` nested progress format in codebase
- Verified: Test summary format inconsistent across files

**[2026-03-04 20:20]**
- Added: Section 6 - Pattern Analysis and Rule Checklists
- Added: Observed patterns from codebase analysis
- Added: Checklists for LOG-UF, LOG-AP, LOG-SC, LOG-GN
- Added: Compliance summary with review items

**[2026-03-04 20:19]**
- Added: 12 batch file wrappers
- Added: 6 overlooked Python files (UI, Map, Job, Config)
- Added: SSE streaming file count (29 files, 1050 matches)

**[2026-03-04 20:18]**
- Initial inventory created
- Documented 31 Python files (1469 matches)
- Documented 21 PowerShell scripts (691 matches)
- Categorized by usage level and purpose
