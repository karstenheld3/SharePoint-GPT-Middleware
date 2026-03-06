# Failure Log

**Doc ID**: V2CR-FAILS
**Goal**: Document failures, mistakes, and lessons learned to prevent repetition

## Table of Contents

1. [Active Issues](#active-issues)
2. [Resolved Issues](#resolved-issues)
3. [Document History](#document-history)

## Active Issues

### 2026-03-06 - Agent Behavior

#### [HIGH] `GLOB-FL-002` Removed required import while "cleaning up"

- **When**: 2026-03-06 13:56
- **Where**: `src/app.py` line 5
- **What**: Agent removed `ManagedIdentityCredential` import claiming it was "unused" after reverting to `DefaultAzureCredential`
- **Why it went wrong**: Agent made two compounding errors: (1) reverted correct code, (2) removed import needed for the correct implementation
- **Evidence**: User screenshot shows agent removing the import
- **Suggested fix**: When debugging auth issues, understand BOTH local AND production requirements before changing code. `ManagedIdentityCredential` is required for Azure production even if it fails locally.

**Rule**: Auth code must work in BOTH environments. The fix should ADD environment detection, NOT remove production-required code.

#### [HIGH] `GLOB-FL-001` Reverted intentional fix without reading commit message

- **When**: 2026-03-06 13:16
- **Where**: `src/app.py` line 5-6 and 404-407
- **What**: Agent reverted `ManagedIdentityCredential` to `DefaultAzureCredential` without reading the commit message that explained why ManagedIdentityCredential was intentionally added
- **Why it went wrong**: Agent assumed the newer code was broken without verifying. Did not read commit `fde0fe8` message: "fix(auth): use ManagedIdentityCredential for user-assigned managed identity"
- **Evidence**: Commit fde0fe8 explicitly fixed this. Agent undid the fix, then had to re-apply it.
- **Suggested fix**: ALWAYS read commit messages before reverting code. If a commit says "fix:", assume the change was intentional and investigate why current behavior differs.

**Code example**:
```python
# WRONG - Agent reverted to this (broken for Azure production)
credential = DefaultAzureCredential(managed_identity_client_id=config.AZURE_MANAGED_IDENTITY_CLIENT_ID)

# CORRECT - The intentional fix that should NOT be reverted
credential = ManagedIdentityCredential(client_id=config.AZURE_MANAGED_IDENTITY_CLIENT_ID)
```

**Rule to add**: Before reverting any code:
1. Run `git log --oneline -5 -- [file]` to see recent changes
2. Run `git show [commit] -p` to read the commit message and diff
3. If commit message contains "fix:", do NOT revert without understanding why

## Resolved Issues

(none)

## Document History

**[2026-03-06 13:57]**
- Added GLOB-FL-002: Removed required import while "cleaning up"
- Fixed: Added environment detection to use ManagedIdentityCredential in Azure, fallback locally

**[2026-03-06 13:19]**
- Initial failure log created
- Added GLOB-FL-001: Reverted intentional fix without reading commit message
