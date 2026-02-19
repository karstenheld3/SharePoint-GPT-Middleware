# TASKS: Permission Scanner Optimization

**Doc ID (TDID)**: PSCP-TK01
**Feature**: permission-scanner-performance
**Goal**: Incrementally improve SharePointPermissionScanner.ps1 performance
**Source**: `_INFO_SITE_PERMISSION_SCANNER_ASSESSMENT_POWERSHELL.md [PSCP-IN02]`
**Strategy**: PARTITION-INCREMENTAL (simple refactorings first, testable chunks)

## Task Overview

- Total tasks: 8
- Estimated total: 6 HHW
- Parallelizable: 2 tasks (Phase 1a, 1b)

## MUST-NOT-FORGET

- Script is in `_input/SharePointPermissionScanner/` - reference/POC folder
- Original script must remain functional after each task
- Test on `AiSearchTest01` site (from input CSV)
- PnP.PowerShell 2.4.0+ required for batching features
- GET batching via `Invoke-PnPSPRestMethod -Batch` needs validation

## Task 0 - Baseline (MANDATORY)

Run before starting any implementation:
- [ ] Run existing script on test site, record execution time
- [ ] Count items scanned, note any errors
- [ ] Save baseline output CSVs for comparison
- [ ] Document PnP.PowerShell version installed

```powershell
# Baseline test command
cd E:\Dev\SharePoint-GPT-Middleware\_Sessions\_2026-02-03_V2SitesEndpoint\_input\SharePointPermissionScanner
.\SharePointPermissionScanner.ps1
# Note: Uses SharePointPermissionScanner-In.csv with AiSearchTest01 site
```

## Tasks

### Phase 1: POC Validation (No Script Changes)

These tasks validate the optimization strategies before modifying the main script.

- [x] **PSCP-TK-001** - POC: Bulk HasUniqueRoleAssignments via REST [TESTED 2026-02-19]
  - Files: `_input/SharePointPermissionScanner/POC_BulkHasUniqueRoleAssignments.ps1`
  - Done when: POC script retrieves all items with HasUniqueRoleAssignments flag in single paginated query
  - Verify: Compare item count with baseline, verify HasUniqueRoleAssignments values match
  - Guardrails: Must handle pagination (odata.nextLink), must handle >5000 items
  - Depends: none
  - Parallel: [P]
  - Est: 1 HHW
  - **RESULT**: SUCCESS - 3 items retrieved in 0.77 seconds, REST API works correctly

```powershell
# POC structure
Connect-PnPOnline -Url "https://whizzyapps.sharepoint.com/sites/AiSearchTest01" -Interactive
$response = Invoke-PnPSPRestMethod -Url "/_api/web/lists/getbytitle('Documents')/items?`$select=ID,FileRef,HasUniqueRoleAssignments&`$top=5000"
$response.value | Where-Object { $_.HasUniqueRoleAssignments -eq $true }
```

- [x] **PSCP-TK-002** - POC: Batched RoleAssignments via REST [TESTED 2026-02-19]
  - Files: `_input/SharePointPermissionScanner/POC_BatchedRoleAssignments.ps1`
  - Done when: POC script retrieves RoleAssignments for multiple items in single batch request
  - Verify: Confirm batch returns correct RoleAssignments, compare with per-item approach
  - Guardrails: Test with 10-20 items first, then scale to 100
  - Depends: TK-001 (needs broken items list)
  - Est: 1 HHW
  - **RESULT**: FAILED - Batch returns 0 role assignments, per-item returns 5. GET batching returns INCORRECT data.
  - **DECISION**: Skip Phase 3 (TK-005, TK-006) - batching does not work for RoleAssignments

```powershell
# POC structure - validate GET batching works
$batch = New-PnPBatch -RetainRequests
foreach ($itemId in @(1, 2, 3)) {
    Invoke-PnPSPRestMethod -Method Get -Url "/_api/web/lists/getbytitle('Documents')/items($itemId)/roleassignments?`$expand=Member,RoleDefinitionBindings" -Batch $batch
}
$responses = Invoke-PnPBatch $batch -Details
```

### Phase 2: Core Optimization (Main Script Changes)

Apply validated optimizations to the main script incrementally.

- [ ] **PSCP-TK-003** - Add REST bulk query function
  - Files: `SharePointPermissionScanner.ps1` (add new function ~line 130)
  - Done when: `Get-ItemsWithUniquePermissions` function exists and returns correct results
  - Verify: Call function independently, compare results with POC
  - Guardrails: Do NOT change existing scanning loop yet
  - Depends: TK-001
  - Est: 0.5 HHW

- [ ] **PSCP-TK-004** - Replace per-item HasUniqueRoleAssignments check
  - Files: `SharePointPermissionScanner.ps1` (modify lines 737-760)
  - Done when: Scanning loop uses bulk REST query instead of per-item Get-PnPProperty
  - Verify: Run full scan, compare output CSVs with baseline
  - Guardrails: Output must match baseline (same items detected)
  - Depends: TK-003
  - Est: 1 HHW

**Key change (line 759):**
```powershell
# BEFORE (per-item, slow)
Get-PnPProperty -ClientObject $item -Property HasUniqueRoleAssignments | Out-Null

# AFTER (bulk query, fast)
# Already have HasUniqueRoleAssignments from $itemData returned by Get-ItemsWithUniquePermissions
```

### Phase 3: Batched RoleAssignments [SKIPPED - POC FAILED]

**SKIPPED**: TK-002 POC showed GET batching returns empty results. Keep per-item Load-CSOMProperties approach.

- [~] **PSCP-TK-005** - Add batched RoleAssignments function [SKIPPED]
  - Files: `SharePointPermissionScanner.ps1` (add new function ~line 160)
  - Done when: `Get-BatchedRoleAssignments` function exists and returns correct results
  - Verify: Call function independently, compare results with POC
  - Guardrails: Batch size 100, handle partial failures
  - Depends: TK-002, TK-004
  - Est: 0.5 HHW

- [~] **PSCP-TK-006** - Replace per-item RoleAssignments loading [SKIPPED]
  - Files: `SharePointPermissionScanner.ps1` (modify lines 801-810)
  - Done when: Broken items use batched RoleAssignments instead of per-item Load-CSOMProperties
  - Verify: Run full scan, compare output CSVs with TK-004 results
  - Guardrails: Output must match (same permissions detected)
  - Depends: TK-005
  - Est: 1 HHW
  - **SKIPPED**: GET batching returns incorrect data

**Key change (line 805):**
```powershell
# BEFORE (per-item, slow)
Load-CSOMProperties -parentObject $item -collectionObject $item.RoleAssignments ...

# AFTER (batched, fast)
# Already have RoleAssignments from $roleAssignmentsMap returned by Get-BatchedRoleAssignments
```

### Phase 4: Throttling Protection

- [ ] **PSCP-TK-007** - Add retry wrapper with Retry-After handling
  - Files: `SharePointPermissionScanner.ps1` (add function ~line 200) or `_includes.ps1`
  - Done when: `Invoke-WithRetry` function handles 429/503 with exponential backoff
  - Verify: Simulate throttling (if possible) or code review
  - Guardrails: Max 5 retries, respect Retry-After header
  - Depends: none
  - Parallel: [P]
  - Est: 0.5 HHW

## Task N - Final Verification (MANDATORY)

Run after all tasks complete:
- [ ] Run optimized script on test site, compare execution time with Task 0 baseline
- [ ] Compare output CSVs with baseline (should be identical content)
- [ ] Document performance improvement factor
- [ ] Run /verify workflow
- [ ] Update PROGRESS.md - mark complete

```powershell
# Final verification
cd E:\Dev\SharePoint-GPT-Middleware\_Sessions\_2026-02-03_V2SitesEndpoint\_input\SharePointPermissionScanner
Measure-Command { .\SharePointPermissionScanner.ps1 }
# Compare with baseline time from Task 0
```

## Dependency Graph

```
TK-001 ─────────────────> TK-003 ─> TK-004 ─> TK-005 ─> TK-006
   │                                   │
   └─> TK-002 ─────────────────────────┘
   
TK-007 (parallel, no dependencies)
```

**Critical path:** TK-001 -> TK-003 -> TK-004 (minimum viable optimization)

## Exit Criteria by Phase

**Phase 1 Complete (POC):** [DONE 2026-02-19]
- [x] TK-001: REST bulk query returns same items as per-item approach - SUCCESS
- [x] TK-002: GET batching either works (proceed) or fails (document, skip Phase 3) - FAILED, Phase 3 skipped

**Phase 2 Complete (Core):**
- [ ] TK-004: Script runs faster, output matches baseline

**Phase 3 Complete (Optional):** [SKIPPED]
- [~] TK-006: SKIPPED - GET batching returns incorrect data

**Phase 4 Complete (Hardening):**
- [ ] TK-007: Throttling protection in place

## Rollback Plan

Each task modifies a specific section. If a task causes issues:
1. Revert changes to that section
2. Keep previous task's changes
3. Document why task failed in FAILS.md

## Document History

**[2026-02-19 15:00]**
- Phase 1 POC testing complete
- TK-001: SUCCESS - REST bulk query works (0.77s for 3 items)
- TK-002: FAILED - GET batching returns empty results (0 vs 5 role assignments)
- DECISION: Skip Phase 3, proceed with Phase 2 only
- Revised total: 4 tasks remaining (TK-003, TK-004, TK-007, Task N)

**[2026-02-19 15:05]**
- Initial tasks plan created from INFO assessment
- Focused on simple refactorings, testable chunks
- POC validation before main script changes
- Phase 3 conditional on POC success
