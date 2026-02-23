# TASKS: V2 Security Scan Fixes

**Doc ID (TDID)**: SSCSCN-TK01
**Feature**: V2_SECURITY_SCAN_PARITY
**Goal**: Fix V2 Python security scanner to achieve 100% parity with PowerShell scanner
**Source**: `_V2_IMPL_SITES_SECURITY_SCAN.md [SSCSCN-IP01]`, `_V2_TEST_SITES_SECURITY_SCAN.md [SSCSCN-TP01]`
**Strategy**: PARTITION-PRIORITY

## Comparison Results (2026-02-23)

| CSV File | PowerShell | V2 | Status |
|----------|------------|-----|--------|
| 01_SiteContents | 25 | 12 | -13 rows |
| 03_SiteUsers | 9 | 8 | -1 row |
| 04_IndividualPermissionItems | 87 | 43 | -44 rows (duplicates in PS) |
| 05_IndividualPermissionItemAccess | 131 | 130 | -1 row |

**Root causes identified:**
1. Duplicate rows in PowerShell output (80 vs 40 files, but same unique URLs)
2. Subsite folder detection issue (SCAN-KL-01) - 1 missing item
3. ViaGroup/ViaGroupId incorrect for nested Entra groups (showing SP group instead of Entra group)
4. Missing SiteContents entries for subsites

## Task Overview

- Total tasks: 6
- Estimated total: 4.5 HHW
- Parallelizable: 2 tasks

## Task 0 - Baseline (MANDATORY)

Run before starting any implementation:
- [ ] Run PowerShell scan, save output
- [ ] Run V2 scan, save output
- [ ] Document current differences (above)

## Tasks

### Critical Fixes

- [ ] **SSCSCN-TK-001** - Fix ViaGroup/ViaGroupId for nested Entra groups
  - Files: src/routers_v2/common_security_scan_functions_v2.py
  - Done when: Users from Entra groups show ViaGroup=Entra group name, ViaGroupId=Entra GUID, ViaGroupType=SecurityGroup
  - Verify: Compare 03_SiteUsers.csv - scantest_user3 should have ViaGroup="ScanTest Security Group 01"
  - Guardrails: Do not change site-level SP group resolution
  - Est: 1.5 HHW

- [ ] **SSCSCN-TK-002** - Fix SiteContents subsite entries
  - Files: src/routers_v2/common_security_scan_functions_v2.py
  - Done when: 01_SiteContents.csv includes all subsite lists/libraries
  - Verify: V2 row count matches PowerShell (25 rows)
  - Depends: none
  - Parallel: [P]
  - Est: 0.5 HHW

### Known Limitations (Deferred)

- [ ] **SSCSCN-TK-003** - Implement IS-15: Subsite folder HasUniqueRoleAssignments detection
  - Files: src/routers_v2/common_security_scan_functions_v2.py
  - Done when: Folder "ArilenaDrovik" in Subsite01/Shared Documents detected with broken inheritance
  - Verify: 04_IndividualPermissionItems.csv includes the missing folder
  - Note: SCAN-KL-01 - SDK limitation, may require workaround
  - Est: 2.0 HHW

### Documentation Updates

- [ ] **SSCSCN-TK-004** - Update SPEC/IMPL with ViaGroup resolution rules
  - Files: _V2_SPEC_SITES_SECURITY_SCAN.md, _V2_IMPL_SITES_SECURITY_SCAN.md
  - Done when: ViaGroup field clearly documents which group name appears (immediate parent for Entra groups)
  - Depends: TK-001
  - Est: 0.25 HHW

- [ ] **SSCSCN-TK-005** - Add omit_sharepoint_groups_in_broken_permissions_file implementation
  - Files: src/routers_v2/common_security_scan_functions_v2.py
  - Done when: Setting=true skips SP groups in 05_IndividualPermissionItemAccess.csv
  - Verify: Run with setting=true, verify no ViaGroupType="SharePointGroup" in 05 CSV
  - Depends: none
  - Parallel: [P]
  - Est: 0.5 HHW

## Task N - Final Verification (MANDATORY)

Run after all tasks complete:
- [ ] Run PowerShell scan
- [ ] Run V2 scan
- [ ] Compare all 5 CSV files - differences should only be:
  - Row order (acceptable)
  - IS-15 subsite folder (known limitation until TK-003)
- [ ] Run /verify workflow
- [ ] Update PROGRESS.md - mark complete

## Dependency Graph

```
TK-001 ─> TK-004
TK-002 (parallel)
TK-003 (deferred - SCAN-KL-01)
TK-005 (parallel)
```

## Detailed Analysis

### TK-001: ViaGroup Resolution Issue

**Current V2 behavior:**
```csv
,scantest_user3@...,ScanTest User 3,"",Full Control,,ScanTest Custom Group,12,SharePointGroup,Group,2,ScanTest Custom Group
```

**Expected (PowerShell):**
```csv
,scantest_user3@...,ScanTest User 3,...,Full Control,false,ScanTest Security Group 01,c2bfa136-...,SecurityGroup,Group,2,ScanTest Custom Group
```

**Fix:** When resolving Entra group members, set ViaGroup to the Entra group name, ViaGroupId to the Entra GUID, ViaGroupType to SecurityGroup.

### TK-002: SiteContents Missing Entries

PowerShell includes subsite lists in SiteContents (25 rows), V2 only has 12.
Need to append subsite content entries during subsite scanning.

### TK-003: Subsite Folder Detection (SCAN-KL-01)

Python SDK `HasUniqueRoleAssignments` query doesn't detect folders with broken inheritance in subsites.
Workaround options:
1. Load folder permissions explicitly
2. Use REST API directly instead of SDK
3. Accept limitation and document

## Document History

**[2026-02-23 16:15]**
- Initial tasks plan created from scan comparison
- 6 tasks identified, 2 parallelizable
- TK-003 deferred pending SDK investigation
