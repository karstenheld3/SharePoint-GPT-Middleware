# IMPL: Add/Remove Crawler Permissions Script - Dual Target Support

**Doc ID**: ARCP-IP01
**Feature**: CRAWLER_PERMISSIONS_DUAL_TARGET
**Goal**: Extend AddRemoveCrawlerPermissions.ps1 to manage API permissions for both SP and MI
**Timeline**: Created 2026-03-15

**Target files**:
- `AddRemoveCrawlerPermissions.ps1` (EXTEND ~200 lines)

**Depends on:**
- `_SPEC_ADD_REMOVE_CRAWLER_PERMISSIONS_SCRIPT.md [ARCP-SP01]` for requirements

## MUST-NOT-FORGET

- MI uses `New-MgServicePrincipalAppRoleAssignment` (not Update-AzADApplication)
- MI needs Graph SP lookup before granting Graph permissions
- Menu loop until Exit
- Target selection: 1=Both, 2=SP, 3=MI

## Table of Contents

1. [Implementation Steps](#1-implementation-steps)
2. [Verification Checklist](#2-verification-checklist)
3. [Document History](#3-document-history)

## 1. Implementation Steps

### ARCP-IP01-IS-01: Add MI Detection and Microsoft.Graph Module

**Location**: After `Import-Module Az.Resources`, before `Clear-Host`

**Action**: Add MI config detection and Microsoft.Graph import

### ARCP-IP01-IS-02: Add MI Permission Functions

**Location**: After `Get-AppPermissions` function

**Action**: Add functions:
- `Get-ManagedIdentityPermissions` - check MI app role assignments
- `Add-ManagedIdentityPermission` - grant permission to MI
- `Remove-ManagedIdentityPermission` - revoke permission from MI
- `Get-TargetSelection` - target selection menu (matches Sites script)

### ARCP-IP01-IS-03: Update Configuration Display

**Location**: After config validation, before Azure login

**Action**: Display both targets, detect `$hasManagedIdentity`

### ARCP-IP01-IS-04: Update Permission Status Check

**Location**: Replace current permission check section

**Action**: Check permissions for both SP and MI, display side-by-side

### ARCP-IP01-IS-05: Refactor to Menu Loop

**Location**: Replace current menu/action section

**Action**: Add while loop with:
- Permission status display
- Action menu (Add/Remove/Exit)
- Target selection
- Per-target operations

### ARCP-IP01-IS-06: Update Add Permissions Logic

**Location**: Inside menu loop, choice "1"

**Action**: Add permissions for selected targets using appropriate APIs

### ARCP-IP01-IS-07: Update Remove Permissions Logic

**Location**: Inside menu loop, choice "2"

**Action**: Remove permissions for selected targets with confirmation

### ARCP-IP01-IS-08: Update Admin Consent URLs

**Location**: After add operation

**Action**: Show consent URLs for both targets when applicable

## 2. Verification Checklist

- [ ] **ARCP-IP01-VC-01**: ARCP-SP01 requirements met
- [ ] **ARCP-IP01-VC-02**: Script runs without syntax errors
- [ ] **ARCP-IP01-VC-03**: SP-only mode unchanged (backward compatible)
- [ ] **ARCP-IP01-VC-04**: MI detection works
- [ ] **ARCP-IP01-VC-05**: Target selection menu works
- [ ] **ARCP-IP01-VC-06**: Menu loop works

## 3. Document History

**[2026-03-15 19:44]**
- Initial implementation plan created
