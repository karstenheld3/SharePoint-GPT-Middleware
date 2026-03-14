# Session Problems

**Doc ID**: 2026-03-14_SharePointAuthMechanisms-PROBLEMS

## Open

**SPAUTH-PR-001: Implement Managed Identity authentication for SharePoint crawler**
- **History**: Added 2026-03-14
- **Description**: Client has disabled certificate-based authentication (Client ID + Certificate). Need to implement Azure Managed Identity as an alternative authentication mechanism.
- **Impact**: Crawler cannot connect to SharePoint sites in client's environment
- **Priority**: HIGH - blocking issue
- **Next Steps**: Research Azure Managed Identity integration with Microsoft Graph API and SharePoint

**SPAUTH-PR-002: Explore personal account login as fallback authentication**
- **History**: Added 2026-03-14
- **Description**: When crawler fails to connect via automated methods (certificate or managed identity), explore possibilities to allow manual login via personal account.
- **Impact**: Provides fallback option for environments where automated auth is not available
- **Priority**: MEDIUM - secondary to SPAUTH-PR-001
- **Next Steps**: Research interactive login flows, device code flow, and implications for headless operation

## Resolved

(none yet)

## Deferred

(none yet)

## Problems Changes

**[2026-03-14]**
- Added: SPAUTH-PR-001 (Managed Identity authentication)
- Added: SPAUTH-PR-002 (Personal account login fallback)
