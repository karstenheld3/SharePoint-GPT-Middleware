# TEST: Sites Security Scan

**Doc ID**: SSCSCN-TP01
**Feature**: SECURITY_SCAN
**Goal**: Verify security scan endpoint correctly captures all permission assignment paths and outputs CSV matching PowerShell scanner format.
**Timeline**: Created 2026-02-03, Updated 0 times
**Target file**: `src/routers_v2/common_security_scan_functions_v2.py`

**Depends on:**
- `_V2_SPEC_SITES_SECURITY_SCAN.md` [SSCSCN-SP01] for requirements
- `_V2_IMPL_SITES_SECURITY_SCAN.md` [SSCSCN-IP01] for implementation details

## MUST-NOT-FORGET

- CSV output must match PowerShell scanner format exactly (column order, escaping)
- All permission paths must be tested: direct, SP group, Entra ID group, nested, sharing link
- NestingLevel values: 0=direct, 1=via group, 2+=nested
- Filter out "Limited Access" permission level
- Empty Id field for nested Entra ID group members

## Table of Contents

1. [Overview](#1-overview)
2. [Scenario](#2-scenario)
3. [Test Strategy](#3-test-strategy)
4. [Test Priority Matrix](#4-test-priority-matrix)
5. [Test Data](#5-test-data)
6. [Test Cases](#6-test-cases)
7. [Test Phases](#7-test-phases)
8. [Helper Functions](#8-helper-functions)
9. [Cleanup](#9-cleanup)
10. [Verification Checklist](#10-verification-checklist)
11. [Document History](#11-document-history)

## 1. Overview

This test plan covers end-to-end verification of the security scan feature. Tests are executed against a real SharePoint site with pre-configured permission scenarios created by PowerShell setup scripts.

## 2. Scenario

**Problem:** Security scan must correctly identify and report ALL users with access to a SharePoint site, regardless of how they obtained access (direct assignment, SP group membership, Entra ID group membership, nested groups, sharing links).

**Solution:**
- Create comprehensive test data covering all permission assignment paths
- Run security scan and verify CSV output matches expected results
- Compare output with PowerShell scanner for format compatibility

**What we don't want:**
- Missing any permission assignment path
- Incorrect NestingLevel or ViaGroup values
- CSV format differences from PowerShell scanner

## 3. Test Strategy

**Approach**: Integration test with real SharePoint/Entra ID environment

**Test Flow:**
1. Setup: Create Entra ID users and groups via PowerShell
2. Setup: Create SharePoint permission scenarios via PowerShell
3. Execute: Run security scan endpoint
4. Verify: Compare CSV output against expected results
5. Cleanup: Remove SharePoint permissions
6. Cleanup: Remove Entra ID objects

**Environment Requirements:**
- SharePoint Online site (from `CRAWLER_SELFTEST_SHAREPOINT_SITE`)
- Entra ID tenant with test user/group creation permissions
- App registration with `User.ReadWrite.All`, `Group.ReadWrite.All`, `Sites.FullControl.All`

## 4. Test Priority Matrix

### MUST TEST (Critical Business Logic)

- **`resolve_sharepoint_group_members()`** - common_security_scan_functions_v2
  - Testability: **EASY** via API, Effort: Medium
  - Verify SP group members captured with correct ViaGroup, NestingLevel

- **`resolve_entra_group_members()`** - common_security_scan_functions_v2
  - Testability: **EASY** via API, Effort: Medium
  - Verify Entra ID group members resolved with correct nesting

- **`csv_escape()`** - common_security_scan_functions_v2
  - Testability: **EASY** unit test, Effort: Low
  - Verify escaping matches PowerShell scanner

- **`scan_site_groups()`** - common_security_scan_functions_v2
  - Testability: **MEDIUM** requires SharePoint, Effort: Medium
  - Verify 02_SiteGroups.csv and 03_SiteUsers.csv output

- **`scan_items_with_broken_inheritance()`** - common_security_scan_functions_v2
  - Testability: **MEDIUM** requires SharePoint, Effort: High
  - Verify 04/05 CSV output for items with unique permissions

### SHOULD TEST (Important Workflows)

- **`run_security_scan()`** - common_security_scan_functions_v2
  - Testability: Medium, Effort: High
  - End-to-end scan with all scope options

- **Group member caching** - Entra ID cache
  - Testability: Medium, Effort: Medium
  - Verify cache hit/miss behavior

### DROP (Not Worth Testing)

- **UI modal dialog** - Reason: UI-only, tested manually
- **SSE streaming format** - Reason: Covered by existing job infrastructure tests
- **Report archive creation** - Reason: Covered by common_report_functions_v2 tests

## 5. Test Data

### Required Entra ID Objects

**Users (6):**
- `scantest_user1@{tenant}` - Direct assignment user
- `scantest_user2@{tenant}` - SP group member
- `scantest_user3@{tenant}` - Security group member
- `scantest_user4@{tenant}` - Nested group member (level 2)
- `scantest_user5@{tenant}` - Deeply nested member (level 3)
- `scantest_user6@{tenant}` - M365 group member

**Security Groups (3):**
- `ScanTest_SecurityGroup01` - Contains user3, nested in SP group
- `ScanTest_SecurityGroup02` - Contains user4, nested in SecurityGroup01
- `ScanTest_SecurityGroup03` - Contains user5, nested in SecurityGroup02

**M365 Group (1):**
- `ScanTest_M365Group01` - Contains user6

### Required SharePoint Objects

**Custom SP Group:**
- `ScanTest Custom Group` - Contains SecurityGroup01

**Broken Inheritance Items:**
- Folder `TestFolder_DirectShare` - User1 added directly
- Folder `TestFolder_GroupShare` - Custom group added
- Folder `TestFolder_SharingLink` - Shared via org-wide link
- List item `TestItem_BrokenInherit` - Unique permissions

**Subsite:**
- `ScanTestSubsite` - With unique permissions

### Setup Scripts Location

`[SESSION_FOLDER]/permission_test_cases/`

### Teardown

Scripts remove all test objects in reverse order to avoid dependency errors.

## 5.1. Actual Created Test Data

### Entra ID Objects (from `created_entra_objects.json`)

**Users:**
- `scantest_user1` (d5812dab-d4ad-4dc6-b12b-fecb1d7560b7) - Direct assignment test user
- `scantest_user2` (8b4eaf49-60f9-400c-b26d-a930d397d248) - SP group member test user
- `scantest_user3` (0b750ac8-702d-48b6-b01d-426d93bab481) - Security group member
- `scantest_user4` (cc71b7e0-e775-4dfc-818d-4d985a701c9a) - Nested group member (level 2)
- `scantest_user5` (a57168e3-3f7b-4ef9-bd02-693a45a3f855) - Deeply nested member (level 3)
- `scantest_user6` (9ea69885-e956-4daf-8d4e-1a1626752a27) - M365 group member

**Security Groups (nested structure):**
```
ScanTest_SecurityGroup01 (c2bfa136-9719-4a20-b386-8591802896ad)
├─> scantest_user3
└─> ScanTest_SecurityGroup02 (3e5ccbf1-cf65-456b-87b9-d6d5a002a824)
    ├─> scantest_user4
    └─> ScanTest_SecurityGroup03 (06c58c3d-a8a4-4805-8603-2a9215276465)
        └─> scantest_user5
```

**M365 Group:**
- `ScanTest_M365Group01` (60ac7968-89f9-490e-9500-aeecc62200d7)
  - Contains: `scantest_user6`

### SharePoint Objects (from `created_sharepoint_objects.json`)

**Site:** `https://whizzyapps.sharepoint.com/sites/AiSearchTest01`

**Default Site Groups:**
- `AiSearchTest01 Owners` - Full Control (contains site owner)
- `AiSearchTest01 Members` - Edit (contains `scantest_user2`)
- `AiSearchTest01 Visitors` - Read (empty)

**Custom SP Group:**
- `ScanTest Custom Group` - Full Control
  - Contains: `ScanTest_SecurityGroup01` (Entra security group)
  - Contains: `ScanTest_M365Group01` (Entra M365 group)

**Direct Assignments:**
- `scantest_user1` - Read permission at site level

**Test Folders (Shared Documents library):**
- `TestFolder_DirectShare`
- `TestFolder_GroupShare`
- `TestFolder_SharingLink`

**Test List:** `ScanTestList`

### Permission Hierarchy Diagram

```
Site: AiSearchTest01
├─> AiSearchTest01 Owners (Full Control)
│   └─> Existing site owner (site owner)
├─> AiSearchTest01 Members (Edit)
│   ├─> Existing site member
│   └─> scantest_user2 [NestingLevel=1, ViaGroup=AiSearchTest01 Members]
├─> AiSearchTest01 Visitors (Read)
│   └─> (empty)
├─> ScanTest Custom Group (Full Control)
│   ├─> ScanTest_SecurityGroup01 [Entra ID]
│   │   ├─> scantest_user3 [NestingLevel=2, ViaGroup=ScanTest Custom Group]
│   │   └─> ScanTest_SecurityGroup02 [nested Entra]
│   │       ├─> scantest_user4 [NestingLevel=3]
│   │       └─> ScanTest_SecurityGroup03 [nested Entra]
│   │           └─> scantest_user5 [NestingLevel=4]
│   └─> ScanTest_M365Group01 [Entra ID]
│       └─> scantest_user6 [NestingLevel=2, ViaGroup=ScanTest Custom Group]
└─> scantest_user1 (Read) [NestingLevel=0, Direct Assignment]
```

## 5.2. Expected CSV Report Content

### 02_SiteGroups.csv (Expected 4 rows + header)

```csv
Id,Role,Title,PermissionLevel,Owner
3,SiteOwners,AiSearchTest01 Owners,Full Control,Existing site owner
4,SiteMembers,AiSearchTest01 Members,Edit,AiSearchTest01 Owners
5,SiteVisitors,AiSearchTest01 Visitors,Read,AiSearchTest01 Owners
{id},Custom,ScanTest Custom Group,Full Control,{owner}
```

**Notes:**
- Limited Access groups filtered out (not included)
- Role determined by group name pattern (owner/member/visitor)

### 03_SiteUsers.csv (Expected 7+ rows + header)

```csv
Id,LoginName,DisplayName,Email,PermissionLevel,ViaGroup,ViaGroupId,ViaGroupType,AssignmentType,NestingLevel,ParentGroup
{id},i:0#.f|membership|existing_owner@...,Existing site owner,existing_owner@...,Full Control,AiSearchTest01 Owners,3,SharePointGroup,Group,1,
{id},i:0#.f|membership|existing_member@...,Existing site member,existing_member@...,Edit,AiSearchTest01 Members,4,SharePointGroup,Group,1,
{id},i:0#.f|membership|scantest_user2@...,ScanTest User 2,scantest_user2@...,Edit,AiSearchTest01 Members,4,SharePointGroup,Group,1,
,scantest_user6@...,ScanTest User 6,scantest_user6@...,Full Control,ScanTest Custom Group,{gid},SharePointGroup,Group,2,ScanTest M365 Group 01
,scantest_user3@...,ScanTest User 3,scantest_user3@...,Full Control,ScanTest Custom Group,{gid},SharePointGroup,Group,2,ScanTest Security Group 01
,scantest_user4@...,ScanTest User 4,scantest_user4@...,Full Control,ScanTest Custom Group,{gid},SharePointGroup,Group,3,ScanTest Security Group 02
,scantest_user5@...,ScanTest User 5,scantest_user5@...,Full Control,ScanTest Custom Group,{gid},SharePointGroup,Group,4,ScanTest Security Group 03
```

**Key observations:**
- `Id` is empty for users resolved from Entra ID groups (they don't have SP user ID)
- `NestingLevel` increments: 1=SP group member, 2=Entra group in SP group, 3+=nested Entra
- `ParentGroup` shows the immediate parent Entra group name
- `ViaGroup` always points to the top-level SharePoint group

### Verification Query (PowerShell)

```powershell
# Verify members in ScanTest Custom Group
$envPath = "E:\Dev\SharePoint-GPT-Middleware\.env"
$config = @{}; Get-Content $envPath | ForEach-Object { 
  if ($_ -match '^(?!#)([^=]+)=([^#]*)') { $config[$matches[1].Trim()] = $matches[2].Trim() } 
}
Connect-PnPOnline -Url "https://whizzyapps.sharepoint.com/sites/AiSearchTest01" -Interactive -ClientId $config.PNP_CLIENT_ID
Get-PnPGroupMember -Group "ScanTest Custom Group" | Select Title, LoginName
Disconnect-PnPOnline
```

## 6. Test Cases

### Category 1: CSV Format Verification (5 tests)

- **SSCSCN-TC-01**: CSV column order matches SPEC Section 14 -> ok=true, columns in exact order
- **SSCSCN-TC-02**: CSV escaping for quotes -> ok=true, value `"test"` becomes `"""test"""`
- **SSCSCN-TC-03**: CSV escaping for commas -> ok=true, value `a,b` becomes `"a,b"`
- **SSCSCN-TC-04**: CSV escaping for newlines -> ok=true, value with `\n` quoted
- **SSCSCN-TC-05**: UTF-8 encoding without BOM -> ok=true, no BOM bytes at file start

### Category 2: SharePoint Group Resolution (6 tests)

- **SSCSCN-TC-06**: Site Owners group captured -> ok=true, Role=SiteOwners, PermissionLevel=Full Control
- **SSCSCN-TC-07**: Site Members group captured -> ok=true, Role=SiteMembers, PermissionLevel=Edit
- **SSCSCN-TC-08**: Site Visitors group captured -> ok=true, Role=SiteVisitors, PermissionLevel=Read
- **SSCSCN-TC-09**: Custom SP group captured -> ok=true, Role=Custom
- **SSCSCN-TC-10**: Limited Access filtered out -> ok=true, no entries with PermissionLevel="Limited Access"
- **SSCSCN-TC-11**: SP group members have NestingLevel=1 -> ok=true, ViaGroupType=SharePointGroup

### Category 3: Entra ID Group Resolution (7 tests)

- **SSCSCN-TC-12**: Security group in SP group resolved -> ok=true, members appear with NestingLevel=2
- **SSCSCN-TC-13**: Nested security group (level 2) resolved -> ok=true, NestingLevel=3
- **SSCSCN-TC-14**: Deeply nested group (level 3) resolved -> ok=true, NestingLevel=4
- **SSCSCN-TC-15**: M365 group resolved -> ok=true, ViaGroupType=SecurityGroup
- **SSCSCN-TC-16**: Entra members have empty Id field -> ok=true, Id="" for nested members
- **SSCSCN-TC-17**: ParentGroup populated correctly -> ok=true, shows immediate parent group name
- **SSCSCN-TC-18**: Max nesting level (5) enforced -> ok=true, stops at level 5

### Category 4: Direct Assignments (3 tests)

- **SSCSCN-TC-19**: Direct user at site level -> ok=true, NestingLevel=0, AssignmentType=User
- **SSCSCN-TC-20**: Direct user on item -> ok=true, appears in 05_IndividualPermissionItemAccess.csv
- **SSCSCN-TC-21**: Direct group on item -> ok=true, group members resolved

### Category 5: Broken Inheritance (5 tests)

- **SSCSCN-TC-22**: Item with unique permissions in 04 CSV -> ok=true, HasUniqueRoleAssignments=true items listed
- **SSCSCN-TC-23**: Folder with unique permissions -> ok=true, Type=FOLDER
- **SSCSCN-TC-24**: List item with unique permissions -> ok=true, Type=ITEM
- **SSCSCN-TC-25**: All accessors in 05 CSV -> ok=true, every user with access listed
- **SSCSCN-TC-26**: Sharing link info captured -> ok=true, SharedDateTime, SharedByDisplayName populated

### Category 6: Sharing Links (4 tests)

- **SSCSCN-TC-27**: Organization-wide link -> ok=true, AssignmentType=SharingLink
- **SSCSCN-TC-28**: People-specific link -> ok=true, specific users listed
- **SSCSCN-TC-29**: Anonymous link -> ok=true, captured if present
- **SSCSCN-TC-30**: Sharing link ViaGroup format -> ok=true, ViaGroup contains "SharingLinks.*"

### Category 7: Scope Options (4 tests)

- **SSCSCN-TC-31**: scope=all scans everything -> ok=true, all 5 CSVs populated
- **SSCSCN-TC-32**: scope=site skips items -> ok=true, only 02/03 CSVs
- **SSCSCN-TC-33**: scope=lists includes structure -> ok=true, 01/02/03 CSVs
- **SSCSCN-TC-34**: include_subsites=true -> ok=true, subsite in 01 CSV with Type=SUBSITE

### Category 7B: Subsite Scanning (6 tests)

- **SSCSCN-TC-49**: Subsite lists in 01_SiteContents.csv -> ok=true, subsite Documents/Site Pages listed
- **SSCSCN-TC-50**: Subsite groups in 02_SiteGroups.csv -> ok=true, "Subsite01 Owners/Members/Visitors" listed
- **SSCSCN-TC-51**: Subsite users in 03_SiteUsers.csv -> ok=true, subsite group members resolved
- **SSCSCN-TC-52**: Subsite broken inheritance in 04/05 CSVs -> ok=true, subsite items with broken permissions captured
- **SSCSCN-TC-53**: Subsite with broken inheritance itself -> ok=true, subsite appears in 04 CSV if HasUniqueRoleAssignments=true
- **SSCSCN-TC-54**: Recursive subsite scanning -> ok=true, sub-subsites scanned when include_subsites=true

### Category 7C: Group Resolution Edge Cases (4 tests)

- **SSCSCN-TC-55**: M365 group with _o suffix -> ok=true, group ID correctly extracted, Graph API call succeeds
- **SSCSCN-TC-56**: do_not_resolve_these_groups adds entry -> ok=true, "Everyone except external users" appears in 03_SiteUsers.csv
- **SSCSCN-TC-57**: do_not_resolve_these_groups skips resolution -> ok=true, no nested members for skipped groups
- **SSCSCN-TC-58**: Special claim c:0-.f format detected -> ok=true, "Everyone except external users" identified as group

### Category 8: Caching (4 tests)

- **SSCSCN-TC-35**: Entra group cached after first resolve -> ok=true, cache file created
- **SSCSCN-TC-36**: Cache hit on second scan -> ok=true, no Graph API call
- **SSCSCN-TC-37**: delete_caches=true clears cache -> ok=true, cache folder empty
- **SSCSCN-TC-38**: Corrupt cache file handled -> ok=true, re-fetches from API

### Category 9: Error Handling (7 tests)

- **SSCSCN-TC-39**: Invalid site_id -> ok=false, error="Site not found"
- **SSCSCN-TC-40**: Access denied on item -> ok=true, item skipped, scan continues
- **SSCSCN-TC-41**: Empty site (no groups) -> ok=true, CSVs with headers only
- **SSCSCN-TC-42**: Cancellation mid-scan -> ok=false, no report created
- **SSCSCN-TC-46**: Invalid scope parameter -> ok=false, error="Invalid scope"
- **SSCSCN-TC-47**: 429 throttling response -> ok=true, scan retries with backoff
- **SSCSCN-TC-48**: Auth token refresh mid-scan -> ok=true, scan continues after reconnect

### Category 10: Report Output (3 tests)

- **SSCSCN-TC-43**: Report archive created -> ok=true, ZIP in reports/site_scans/
- **SSCSCN-TC-44**: report.json contains stats -> ok=true, groups_found, users_found populated
- **SSCSCN-TC-45**: Report accessible via /v2/reports -> ok=true, listed and downloadable

## 7. Test Phases

Ordered execution sequence:

1. **Phase 1: Entra ID Setup** - Run `01_Create_EntraID_UsersAnd_Groups.ps1`
   - Creates 6 test users
   - Creates 3 security groups with nesting
   - Creates 1 M365 group

2. **Phase 2: SharePoint Setup** - Run `02_Create_SharePoint_Permission_Cases.ps1`
   - Creates custom SP group
   - Adds Entra groups to SP groups
   - Creates folders/items with broken inheritance
   - Creates sharing links
   - Creates subsite

3. **Phase 3: Unit Tests** - SSCSCN-TC-01 to SSCSCN-TC-05
   - CSV format verification (no SharePoint needed)

4. **Phase 4: Integration Tests** - SSCSCN-TC-06 to SSCSCN-TC-45
   - Run security scan
   - Verify CSV output

5. **Phase 5: SharePoint Cleanup** - Run `03_Remove_SharePoint_Permission_Cases.ps1`
   - Remove sharing links
   - Remove broken inheritance items
   - Remove custom SP group
   - Remove subsite

6. **Phase 6: Entra ID Cleanup** - Run `04_Remove_EntraID_UsersAnd_Groups.ps1`
   - Remove M365 group
   - Remove security groups
   - Remove test users

## 8. Helper Functions

```python
def compare_csv_columns(actual_path: str, expected_columns: list) -> bool:
    """Verify CSV has exact column order."""
    with open(actual_path, 'r', encoding='utf-8') as f:
        header = f.readline().strip()
    actual_cols = header.split(',')
    return actual_cols == expected_columns

def find_user_in_csv(csv_path: str, login_name: str) -> dict | None:
    """Find user row by LoginName."""
    import csv
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('LoginName') == login_name:
                return row
    return None

def verify_nesting_level(csv_path: str, login_name: str, expected_level: int) -> bool:
    """Verify user has expected NestingLevel."""
    row = find_user_in_csv(csv_path, login_name)
    return row and int(row.get('NestingLevel', -1)) == expected_level
```

## 9. Cleanup

Artifacts to remove after testing:

- Entra ID test users (`scantest_user*`)
- Entra ID test groups (`ScanTest_*`)
- SharePoint custom group (`ScanTest Custom Group`)
- SharePoint folders with broken inheritance
- SharePoint subsite (`ScanTestSubsite`)
- Sharing links created during test
- Entra group cache files (`_entra_group_cache/*.json`)
- Report archives from test runs

## 10. Verification Checklist

### Setup Verification
- [ ] **SSCSCN-TP01-VC-01**: Entra ID users created (6)
- [ ] **SSCSCN-TP01-VC-02**: Security groups created with nesting (3)
- [ ] **SSCSCN-TP01-VC-03**: M365 group created (1)
- [ ] **SSCSCN-TP01-VC-04**: SharePoint custom group created
- [ ] **SSCSCN-TP01-VC-05**: Broken inheritance items created (4)
- [ ] **SSCSCN-TP01-VC-06**: Sharing links created
- [ ] **SSCSCN-TP01-VC-07**: Subsite created

### Test Execution
- [ ] **SSCSCN-TP01-VC-08**: CSV format tests pass (TC-01 to TC-05)
- [ ] **SSCSCN-TP01-VC-09**: SP group tests pass (TC-06 to TC-11)
- [ ] **SSCSCN-TP01-VC-10**: Entra ID group tests pass (TC-12 to TC-18)
- [ ] **SSCSCN-TP01-VC-11**: Direct assignment tests pass (TC-19 to TC-21)
- [ ] **SSCSCN-TP01-VC-12**: Broken inheritance tests pass (TC-22 to TC-26)
- [ ] **SSCSCN-TP01-VC-13**: Sharing link tests pass (TC-27 to TC-30)
- [ ] **SSCSCN-TP01-VC-14**: Scope option tests pass (TC-31 to TC-34)
- [ ] **SSCSCN-TP01-VC-15**: Caching tests pass (TC-35 to TC-38)
- [ ] **SSCSCN-TP01-VC-16**: Error handling tests pass (TC-39 to TC-42, TC-46 to TC-48)
- [ ] **SSCSCN-TP01-VC-17**: Report output tests pass (TC-43 to TC-45)
- [ ] **SSCSCN-TP01-VC-21**: Subsite scanning tests pass (TC-49 to TC-54)
- [ ] **SSCSCN-TP01-VC-22**: Group resolution edge case tests pass (TC-55 to TC-58)

### Cleanup Verification
- [ ] **SSCSCN-TP01-VC-18**: SharePoint test objects removed
- [ ] **SSCSCN-TP01-VC-19**: Entra ID test objects removed
- [ ] **SSCSCN-TP01-VC-20**: No orphaned test data

## 11. Document History

**[2026-02-03 22:40]**
- Added: TC-49 to TC-54 (subsite scanning - 6 tests)
- Added: TC-55 to TC-58 (group resolution edge cases - 4 tests)
- Added: VC-21, VC-22 verification checklist items
- Changed: Test count from 48 to 58

**[2026-02-03 16:30]**
- Added: TC-46 (invalid scope), TC-47 (throttling), TC-48 (auth refresh)
- Fixed: Coverage gaps for SCAN-IG-06, EC-03, EC-05, EC-06
- Changed: Test count from 45 to 48

**[2026-02-03 16:20]**
- Initial test plan created
- 45 test cases across 10 categories
- PowerShell setup/teardown scripts specified
