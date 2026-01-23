# Failure Log

**Goal**: Document failures, mistakes, and lessons learned to prevent repetition

## Table of Contents

1. [Active Issues](#active-issues)
2. [Resolved Issues](#resolved-issues)
3. [Document History](#document-history)

## Active Issues

### 2026-01-22 - SharePoint Sites.Selected Permission Management

#### [RESOLVED] `SPGPT-FL-001` Group-Connected Sites Require Direct Connection for Sites.Selected Grants

- **When**: 2026-01-22 12:25
- **Where**: `AddRemoveCrawlerSharePointSites.ps1:326` (Grant-PnPAzureADAppSitePermission call)
- **What**: Granting Sites.Selected permission to group-connected (M365 Group) SharePoint sites fails with "accessDenied" when connected to SharePoint Admin and using `-Site` parameter

**Wrong Assumptions:**

1. `[UNVERIFIED]` **"Admin connection + -Site parameter works for all site types"**
   - Assumed: Connecting to SharePoint Admin URL and specifying target site via `-Site` parameter would work universally
   - Reality: Group-connected sites (Teams sites, modern team sites with M365 Groups) require direct connection to the target site itself
   - Why wrong: Did not verify behavior differences between site types; assumed SharePoint Admin permissions cascade to all operations

2. `[UNVERIFIED]` **"Global Admin + Site Admin = sufficient permissions"**
   - Assumed: Being Global Administrator and Site Administrator grants all necessary permissions for any SharePoint operation
   - Reality: For group-connected sites, the PnP cmdlet requires a different connection context regardless of user permissions
   - Why wrong: Conflated user permissions with API operation requirements

3. `[INCOMPLETE]` **"accessDenied means permission problem"**
   - Assumed: The error indicated missing permissions that needed to be granted in Entra ID
   - Reality: The error indicated wrong connection context, not missing permissions
   - Why wrong: Did not investigate alternative causes for accessDenied; jumped to permission solutions

4. `[UNVERIFIED]` **"Graph API direct call would bypass the issue"**
   - Assumed: Using Invoke-PnPGraphMethod directly would work around PnP cmdlet limitations
   - Reality: Graph API returned BadRequest; the token context from admin connection still lacked required scope for group-connected sites
   - Why wrong: Did not understand that the connection context (not just API choice) determines available operations

- **Evidence**: 
  - AiSearchTest01 (non-group-connected): Permission granted successfully via admin connection
  - MarketIntelligence (group-connected): "accessDenied" via admin connection, SUCCESS via direct site connection
- **Root cause**: Group-connected sites have different permission evaluation paths. The PnP cmdlet internally uses different Graph/SharePoint endpoints based on connection context.
- **Suggested fix**: Implement fallback - if accessDenied, reconnect directly to target site and retry without `-Site` parameter

**Resolution**:
- **Resolved**: 2026-01-22 12:35
- **Solution**: Added fallback mechanism in `AddRemoveCrawlerSharePointSites.ps1`:
  1. Try original method (admin site + `-Site` parameter)
  2. On accessDenied: reconnect directly to target site, retry without `-Site` parameter
- **Verified**: POC script `.tmp-poc-add-site-to-sitesselected.ps1` confirmed fix works

## Resolved Issues

(None yet - see Active Issues for resolved entries)

## Document History

**[2026-01-22 12:36]**
- Initial failure log created
- Added SPGPT-FL-001: Group-connected sites Sites.Selected permission issue

