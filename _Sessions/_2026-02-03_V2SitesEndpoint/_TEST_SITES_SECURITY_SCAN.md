# TEST: Sites Security Scan

**Doc ID**: SCAN-TP01
**Feature**: SECURITY_SCAN
**Goal**: Verify security scan endpoint correctly captures all permission assignment paths and outputs CSV matching PowerShell scanner format.
**Timeline**: Created 2026-02-03, Updated 0 times
**Target file**: `src/routers_v2/common_security_scan_functions_v2.py`

**Depends on:**
- `_V2_SPEC_SITES_SECURITY_SCAN.md` [SITE-SP03] for requirements
- `_V2_IMPL_SITES_SECURITY_SCAN.md` [SCAN-IP01] for implementation details

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

- **SCAN-TC-01**: CSV column order matches SPEC Section 14 -> ok=true, columns in exact order
- **SCAN-TC-02**: CSV escaping for quotes -> ok=true, value `"test"` becomes `"""test"""`
- **SCAN-TC-03**: CSV escaping for commas -> ok=true, value `a,b` becomes `"a,b"`
- **SCAN-TC-04**: CSV escaping for newlines -> ok=true, value with `\n` quoted
- **SCAN-TC-05**: UTF-8 encoding without BOM -> ok=true, no BOM bytes at file start

### Category 2: SharePoint Group Resolution (6 tests)

- **SCAN-TC-06**: Site Owners group captured -> ok=true, Role=SiteOwners, PermissionLevel=Full Control
- **SCAN-TC-07**: Site Members group captured -> ok=true, Role=SiteMembers, PermissionLevel=Edit
- **SCAN-TC-08**: Site Visitors group captured -> ok=true, Role=SiteVisitors, PermissionLevel=Read
- **SCAN-TC-09**: Custom SP group captured -> ok=true, Role=Custom
- **SCAN-TC-10**: Limited Access filtered out -> ok=true, no entries with PermissionLevel="Limited Access"
- **SCAN-TC-11**: SP group members have NestingLevel=1 -> ok=true, ViaGroupType=SharePointGroup

### Category 3: Entra ID Group Resolution (7 tests)

- **SCAN-TC-12**: Security group in SP group resolved -> ok=true, members appear with NestingLevel=2
- **SCAN-TC-13**: Nested security group (level 2) resolved -> ok=true, NestingLevel=3
- **SCAN-TC-14**: Deeply nested group (level 3) resolved -> ok=true, NestingLevel=4
- **SCAN-TC-15**: M365 group resolved -> ok=true, ViaGroupType=SecurityGroup
- **SCAN-TC-16**: Entra members have empty Id field -> ok=true, Id="" for nested members
- **SCAN-TC-17**: ParentGroup populated correctly -> ok=true, shows immediate parent group name
- **SCAN-TC-18**: Max nesting level (5) enforced -> ok=true, stops at level 5

### Category 4: Direct Assignments (3 tests)

- **SCAN-TC-19**: Direct user at site level -> ok=true, NestingLevel=0, AssignmentType=User
- **SCAN-TC-20**: Direct user on item -> ok=true, appears in 05_IndividualPermissionItemAccess.csv
- **SCAN-TC-21**: Direct group on item -> ok=true, group members resolved

### Category 5: Broken Inheritance (5 tests)

- **SCAN-TC-22**: Item with unique permissions in 04 CSV -> ok=true, HasUniqueRoleAssignments=true items listed
- **SCAN-TC-23**: Folder with unique permissions -> ok=true, Type=FOLDER
- **SCAN-TC-24**: List item with unique permissions -> ok=true, Type=ITEM
- **SCAN-TC-25**: All accessors in 05 CSV -> ok=true, every user with access listed
- **SCAN-TC-26**: Sharing link info captured -> ok=true, SharedDateTime, SharedByDisplayName populated

### Category 6: Sharing Links (4 tests)

- **SCAN-TC-27**: Organization-wide link -> ok=true, AssignmentType=SharingLink
- **SCAN-TC-28**: People-specific link -> ok=true, specific users listed
- **SCAN-TC-29**: Anonymous link -> ok=true, captured if present
- **SCAN-TC-30**: Sharing link ViaGroup format -> ok=true, ViaGroup contains "SharingLinks.*"

### Category 7: Scope Options (4 tests)

- **SCAN-TC-31**: scope=all scans everything -> ok=true, all 5 CSVs populated
- **SCAN-TC-32**: scope=site skips items -> ok=true, only 02/03 CSVs
- **SCAN-TC-33**: scope=lists includes structure -> ok=true, 01/02/03 CSVs
- **SCAN-TC-34**: include_subsites=true -> ok=true, subsite in 01 CSV with Type=SUBSITE

### Category 8: Caching (4 tests)

- **SCAN-TC-35**: Entra group cached after first resolve -> ok=true, cache file created
- **SCAN-TC-36**: Cache hit on second scan -> ok=true, no Graph API call
- **SCAN-TC-37**: delete_caches=true clears cache -> ok=true, cache folder empty
- **SCAN-TC-38**: Corrupt cache file handled -> ok=true, re-fetches from API

### Category 9: Error Handling (7 tests)

- **SCAN-TC-39**: Invalid site_id -> ok=false, error="Site not found"
- **SCAN-TC-40**: Access denied on item -> ok=true, item skipped, scan continues
- **SCAN-TC-41**: Empty site (no groups) -> ok=true, CSVs with headers only
- **SCAN-TC-42**: Cancellation mid-scan -> ok=false, no report created
- **SCAN-TC-46**: Invalid scope parameter -> ok=false, error="Invalid scope"
- **SCAN-TC-47**: 429 throttling response -> ok=true, scan retries with backoff
- **SCAN-TC-48**: Auth token refresh mid-scan -> ok=true, scan continues after reconnect

### Category 10: Report Output (3 tests)

- **SCAN-TC-43**: Report archive created -> ok=true, ZIP in reports/site_scans/
- **SCAN-TC-44**: report.json contains stats -> ok=true, groups_found, users_found populated
- **SCAN-TC-45**: Report accessible via /v2/reports -> ok=true, listed and downloadable

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

3. **Phase 3: Unit Tests** - SCAN-TC-01 to SCAN-TC-05
   - CSV format verification (no SharePoint needed)

4. **Phase 4: Integration Tests** - SCAN-TC-06 to SCAN-TC-45
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
- [ ] **SCAN-TP01-VC-01**: Entra ID users created (6)
- [ ] **SCAN-TP01-VC-02**: Security groups created with nesting (3)
- [ ] **SCAN-TP01-VC-03**: M365 group created (1)
- [ ] **SCAN-TP01-VC-04**: SharePoint custom group created
- [ ] **SCAN-TP01-VC-05**: Broken inheritance items created (4)
- [ ] **SCAN-TP01-VC-06**: Sharing links created
- [ ] **SCAN-TP01-VC-07**: Subsite created

### Test Execution
- [ ] **SCAN-TP01-VC-08**: CSV format tests pass (TC-01 to TC-05)
- [ ] **SCAN-TP01-VC-09**: SP group tests pass (TC-06 to TC-11)
- [ ] **SCAN-TP01-VC-10**: Entra ID group tests pass (TC-12 to TC-18)
- [ ] **SCAN-TP01-VC-11**: Direct assignment tests pass (TC-19 to TC-21)
- [ ] **SCAN-TP01-VC-12**: Broken inheritance tests pass (TC-22 to TC-26)
- [ ] **SCAN-TP01-VC-13**: Sharing link tests pass (TC-27 to TC-30)
- [ ] **SCAN-TP01-VC-14**: Scope option tests pass (TC-31 to TC-34)
- [ ] **SCAN-TP01-VC-15**: Caching tests pass (TC-35 to TC-38)
- [ ] **SCAN-TP01-VC-16**: Error handling tests pass (TC-39 to TC-42, TC-46 to TC-48)
- [ ] **SCAN-TP01-VC-17**: Report output tests pass (TC-43 to TC-45)

### Cleanup Verification
- [ ] **SCAN-TP01-VC-18**: SharePoint test objects removed
- [ ] **SCAN-TP01-VC-19**: Entra ID test objects removed
- [ ] **SCAN-TP01-VC-20**: No orphaned test data

## 11. Document History

**[2026-02-03 16:30]**
- Added: TC-46 (invalid scope), TC-47 (throttling), TC-48 (auth refresh)
- Fixed: Coverage gaps for SCAN-IG-06, EC-03, EC-05, EC-06
- Changed: Test count from 45 to 48

**[2026-02-03 16:20]**
- Initial test plan created
- 45 test cases across 10 categories
- PowerShell setup/teardown scripts specified
