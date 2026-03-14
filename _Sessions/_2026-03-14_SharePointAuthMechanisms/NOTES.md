# Session Notes

**Doc ID**: 2026-03-14_SharePointAuthMechanisms-NOTES

## Initial Request

````text
Currently we have just 1 authentication method for the crawler to connect to SharePoint sites: Via Client ID and Certificate.

Problem: The client has disabled this

Solution:

1) We need a second authentication mechanism via managed identity
2) If the cawler fails to connect to SharePoint I want to explore possibilities to log in manually via personal account

Create a new session and these 2 problems.

First we have to implement 1)
Then we explore and implement 2)
````

## Session Info

- **Started**: 2026-03-14
- **Goal**: Add managed identity authentication for SharePoint crawler; explore personal account login as fallback
- **Operation Mode**: IMPL-CODEBASE
- **Output Location**: src/

## Current Phase

**Phase**: EXPLORE
**Workflow**: (pending assessment)
**Assessment**: (pending)

## Agent Instructions

- Research Azure Managed Identity authentication for SharePoint
- Maintain backward compatibility with existing certificate authentication
- Document findings in INFO document before implementation

## Key Decisions

**[2026-03-14] Architecture Decisions:**

1. **API Target**: SharePoint REST API (`/_api/`)
   - Implication: Certificate required for app-only (client secrets blocked by Microsoft)
   - Managed Identity works via Graph API permissions

2. **Hosting**: Azure App Service + Local Development
   - Azure: Managed Identity primary
   - Local dev: Certificate or Device Code fallback

3. **User Fallback Scope**: Developer AND Production
   - Device Code for both development and production emergency fallback
   - Scenario: Admins revoke Managed Identity access → Device Code allows temporary crawling

**[2026-03-14] Authentication Selection Model:**

```
┌─────────────────────────────────────────────────────────────────┐
│ Admin-Selected Authentication (NOT auto-failover)               │
│                                                                 │
│  UI Admin selects ONE mechanism → Used by ALL workers           │
│                                                                 │
│  Admin-Selectable Methods (for requests WITHOUT user token):    │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Application Permissions:                                    ││
│  │ 1. Managed Identity  (Azure-hosted, zero-config)            ││
│  │ 2. Certificate       (Any environment, current impl)        ││
│  │                                                             ││
│  │ Delegated Permissions:                                      ││
│  │ 3. Device Code       (Headless/server, production+dev)      ││
│  │ 4. Interactive Browser (Any env, requires browser)          ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  Automatic Method (when request HAS Authorization header):      │
│  └─> On-Behalf-Of (per-request, user's permissions)             │
│                                                                 │
│  Workers do NOT independently try/failover                      │
│  UI endpoints use the globally selected mechanism               │
└─────────────────────────────────────────────────────────────────┘
```

**[2026-03-14] Why Admin-Selected (not auto-failover):**
- UI always calls endpoints, does not track individual workers
- Consistent behavior: all workers use same auth method
- Admin control: explicit choice when MI access revoked
- No surprise fallbacks: admin knows which mechanism is active

**[2026-03-14] Fallback Scenario:**
- Default: Managed Identity (zero-config in Azure)
- If MI access revoked: Admin switches to Device Code in UI
- Device Code: Admin authenticates once → token cached → all workers use it

## Important Findings

(none yet)

## Topic Registry

- `SPAUTH` - SharePoint authentication mechanisms
- `CRWL` - Crawler operations

## Mandatory Reading

**Authentication Mechanisms (AM):**
- `docs/microsoft/SharePointOnlineAuthMechanisms_2026-03-14/_INFO_SPAUTH-AM01_CERTIFICATE_CREDENTIALS.md`
- `docs/microsoft/SharePointOnlineAuthMechanisms_2026-03-14/_INFO_SPAUTH-AM03_MANAGED_IDENTITY.md`
- `docs/microsoft/SharePointOnlineAuthMechanisms_2026-03-14/_INFO_SPAUTH-AM04_INTERACTIVE_BROWSER.md`
- `docs/microsoft/SharePointOnlineAuthMechanisms_2026-03-14/_INFO_SPAUTH-AM05_DEVICE_CODE.md`
- `docs/microsoft/SharePointOnlineAuthMechanisms_2026-03-14/_INFO_SPAUTH-AM06_AUTHORIZATION_CODE.md`

**Background Information (IN):**
- `docs/microsoft/SharePointOnlineAuthMechanisms_2026-03-14/_INFO_SPAUTH-IN01_OAUTH_FLOWS.md`
- `docs/microsoft/SharePointOnlineAuthMechanisms_2026-03-14/_INFO_SPAUTH-IN05_SECURITY.md`
- `docs/microsoft/SharePointOnlineAuthMechanisms_2026-03-14/_INFO_SPAUTH-IN06_OPERATIONAL.md`
- `docs/microsoft/SharePointOnlineAuthMechanisms_2026-03-14/_INFO_SPAUTH-IN07_AZURE_PERMISSION_REQUIREMENTS.md`

## Files to Read on Session Load

- `docs/V2_INFO_IMPLEMENTATION_PATTERNS.md`
- `docs/routers_v2/_V2_SPEC_ROUTERS.md`
- `docs/routers_v2/_V2_SPEC_CRAWLER.md`
- `docs/routers_v2/_V2_IMPL_CRAWLER.md`
- `docs/routers_v2/_V2_IMPL_CRAWLER_SELFTEST.md`

## Significant Prompts Log

(none yet)
