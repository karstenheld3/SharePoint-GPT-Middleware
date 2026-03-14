# INFO: SharePoint Authentication Requirements

**Doc ID**: SPAUTH-IN10
**Goal**: Capture all authentication requirements for SharePoint crawler multi-auth implementation
**Timeline**: Created 2026-03-14

## Summary

- Certificate auth blocked by ONE client; adding alternative mechanisms (certificate remains supported) [VERIFIED]
- Two-Tier Auth Model: System Auth (app-only, system-wide) + User Auth (delegated, per-session) [VERIFIED]
- Admin-selected System Auth (not auto-failover); User Auth does not break System Auth [VERIFIED]
- Two UI architectures supported: middleware-served UI AND separate SPA frontend [VERIFIED]
- Four admin-selectable methods + On-Behalf-Of (automatic, per-request) [VERIFIED]
- SharePoint REST API blocks client secrets for app-only access [VERIFIED]
- Sites.Selected permission only available for Application permissions, not Delegated [VERIFIED]
- Smart Auth Selection: OBO available alongside override/default based on Authorization header presence [VERIFIED]

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Architecture Decisions](#2-architecture-decisions)
3. [Authentication Methods](#3-authentication-methods)
4. [UI Architecture Scenarios](#4-ui-architecture-scenarios)
5. [Runtime Behavior Scenarios](#5-runtime-behavior-scenarios)
6. [Permission Model](#6-permission-model)
7. [Implementation Constraints](#7-implementation-constraints)
8. [Sources](#sources)
9. [Next Steps](#next-steps)
10. [Document History](#document-history)

## 1. Problem Statement

### 1.1 Current State

- Single authentication method: Client ID + Certificate (App-Only)
- Uses `connect_to_site_using_client_id_and_certificate()` in `common_sharepoint_functions_v2.py`
- Supports Sites.Selected permissions for least-privilege access

### 1.2 Problem

One specific client has disabled certificate-based authentication. Crawler cannot connect to their SharePoint sites.

**Note:** Certificate authentication remains supported and is still used by many other clients. This is NOT a deprecation - we are ADDING new authentication methods alongside the existing certificate method.

### 1.3 Required Solution

1. **Primary**: Implement Managed Identity authentication (Azure-hosted environments)
2. **Fallback**: User login mechanisms for emergency access when automated auth fails
3. **Scope**: Both development AND production use

### 1.4 Fallback Scenario

- Default: Managed Identity (zero-config in Azure)
- If MI access revoked by admins: Admin switches to Device Code in UI
- Device Code: Admin authenticates once → token cached → all workers use it

## 2. Architecture Decisions

### 2.1 API Target

**SharePoint REST API (`/_api/`)** - This session covers SharePoint REST API only. Microsoft Graph API support planned for a separate session.

Implications:
- Certificate REQUIRED for app-only access (client secrets blocked by Microsoft for SharePoint REST)
- Managed Identity works via Graph API permissions which SharePoint accepts
- Delegated flows use user's SharePoint permissions
- Token audience: `https://{tenant}.sharepoint.com`

### 2.2 Hosting Environment

**Azure App Service + Local Development**

- Azure: Managed Identity is primary option
- Local dev: Certificate or Interactive Browser fallback (no IMDS endpoint locally)
- Interactive Browser works in ANY environment where middleware UI is accessed via browser
- Default method configured via environment variables / `.env` file (not hardcoded)

### 2.3 Authentication Selection Model

**Two-Tier Model: System Auth + User Auth**

```
┌─────────────────────────────────────────────────────────────────┐
│ Two-Tier Authentication Model                                   │
│                                                                 │
│  SYSTEM AUTH (app-only or admin-delegated, system-wide):        │
│  ├─> Managed Identity, Certificate, Device Code                 │
│  ├─> Configured via env var or override file                    │
│  └─> Used by ALL workers, ALL requests without user session     │
│                                                                 │
│  USER AUTH (delegated, per-session overlay):                    │
│  ├─> Interactive Browser                                        │
│  ├─> Per-session, does NOT affect other requests                │
│  └─> Admin uses own credentials for inaccessible sites          │
│                                                                 │
│  KEY PRINCIPLE: User Auth must NOT break System Auth            │
│  - Middleware has many independent workers                      │
│  - Other apps may call API without user session                 │
│  - User Auth is an OVERLAY, not a system-wide switch            │
│  - Device Code is System Auth (admin authenticates once,        │
│    ALL workers use cached token - emergency fallback)           │
└─────────────────────────────────────────────────────────────────┘
```

**Why Two-Tier:**
- Middleware workers may be used by other apps we don't control
- Non-browser API callers have no session - must use System Auth
- Goal: Enable admins to scan sites inaccessible via MI, without breaking other callers
- Device Code is System Auth because it's an emergency fallback - all workers need the token

## 3. Authentication Methods

### 3.1 Application Permissions (App-Only)

- **Managed Identity**
  - Environment: Azure only
  - Config: IDENTITY_ENDPOINT auto-set by Azure
  - Notes: Zero credentials in code

- **Certificate**
  - Environment: Any
  - Config: CERT_PATH, passwords
  - Notes: Current implementation

**Client Secret**: Supported in code (used for other services like OpenAI), but blocked by SharePoint Online for REST API app-only access. Will NOT be used for SharePoint authentication.

### 3.2 Delegated Permissions (Admin-Selectable)

- **Interactive Browser**
  - Best for: Any environment where user accesses middleware via browser
  - User experience: Standard OAuth redirect in user's browser (same as any web app login)
  - Works in production AND local dev - middleware UI is already in browser
  - LOW complexity: standard OAuth redirect flow, no token sharing needed

- **Device Code**
  - Best for: CLI tools, scripts, headless automation
  - User experience: Display code, auth on phone/other device
  - MEDIUM complexity: requires token persistence and cross-worker sharing

### 3.3 Automatic Method (Per-Request)

- **On-Behalf-Of (OBO)**
  - Triggered automatically when request has Authorization header
  - NOT admin-selectable; always available alongside selected method
  - Best for: Separate SPA frontend
  - User experience: User already authenticated to frontend

### 3.4 Complete Authentication Options

```
┌─────────────────────────────────────────────────────────────────┐
│ Admin-Selectable Methods (for requests WITHOUT user token)      │
│                                                                 │
│  Application Permissions:                                       │
│  ├─> 1. Managed Identity  (Azure-hosted, zero-config)           │
│  └─> 2. Certificate       (Any environment, current impl)       │
│                                                                 │
│  Delegated Permissions:                                         │
│  ├─> 3. Interactive Browser (Any env, user already in browser)  │
│  └─> 4. Device Code       (CLI/scripts, headless only)          │
│                                                                 │
│  Automatic Method (when request HAS Authorization header)       │
│  └─> On-Behalf-Of         (Per-request, user's permissions)     │
└─────────────────────────────────────────────────────────────────┘
```

## 4. UI Architecture Scenarios

### 4.1 Scenario A: Middleware Serves Own UI

Current architecture with `html_javascript_static_files/`.

**Authentication flow for user fallback:**
- Admin initiates Device Code flow via UI endpoint
- Middleware displays code/URL
- Admin authenticates on phone/browser
- Token cached in middleware
- All workers use cached token

**Applicable methods:** Device Code, Interactive Browser

### 4.2 Scenario B: Separate SPA Frontend

Future architecture with independent SPA application.

**Authentication flow:**
- User authenticates to SPA (via Authorization Code or similar)
- SPA calls middleware API with user's access token
- Middleware exchanges token for SharePoint token (On-Behalf-Of)
- Middleware calls SharePoint with exchanged token

**Applicable methods:** On-Behalf-Of

### 4.3 Both Architectures Supported

System must support BOTH scenarios:
- Scenario A: Device Code, Interactive Browser
- Scenario B: On-Behalf-Of

## 5. Runtime Behavior Scenarios

### 5.1 Scenario 1: Admin Uses Delegated Auth (Per-Session)

Admin uses Middleware UI to authenticate via Interactive Browser or Device Code. Only requests WITH the admin's session use delegated credentials. Other callers continue using System Auth.

```
┌─────────────────────────────────────────────────────────────────┐
│ Scenario 1: Admin Session Active (Two-Tier in Action)           │
│                                                                 │
│  1. Admin opens Middleware UI                                   │
│  2. Admin clicks "Login with Microsoft"                         │
│  3. Admin authenticates (Interactive Browser or Device Code)    │
│  4. Auth TESTED against SharePoint → success                    │
│  5. Token stored in admin's SESSION (not system-wide)           │
│                         │                                       │
│                         v                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ONLY admin's session uses delegated token                   ││
│  │                                                             ││
│  │  - Admin's browser requests → uses admin's token            ││
│  │  - External app calls       → uses System Auth (unchanged)  ││
│  │  - Scheduled jobs           → uses System Auth (unchanged)  ││
│  │  - Other API callers        → uses System Auth (unchanged)  ││
│  │                                                             ││
│  │  Admin can access sites MI cannot reach                     ││
│  │  Other callers are NOT affected                             ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

**Key implications:**
- Admin's session accesses SharePoint with admin's permissions
- Other callers continue using System Auth (MI or Certificate)
- No system-wide disruption when admin logs in
- **Security improvement**: User Auth is isolated to admin's session

### 5.2 Scenario 2: Headless API with OBO and Default Auth

External applications use middleware as headless API. Must support BOTH OBO (when user token provided) AND default auth (when no user token).

#### 5.2.1 Sub-scenario: External App Sends User Token (OBO)

```
┌─────────────────────────────────────────────────────────────────┐
│ Scenario 2A: OBO - External app provides user token             │
│                                                                 │
│  External App (SPA) ──> User logs in ──> Gets user token        │
│                                               │                 │
│                                               v                 │
│  Request to Middleware:                                         │
│  POST /v2/crawler/sites/{id}/crawl                              │
│  Authorization: Bearer <user_access_token>                      │
│                                               │                 │
│                                               v                 │
│  Middleware detects Authorization header                        │
│  ──> OBO exchange ──> Gets SharePoint token for user            │
│                                               │                 │
│                                               v                 │
│  SharePoint access = User's permissions                         │
│  (User must have access to the site being crawled)              │
└─────────────────────────────────────────────────────────────────┘
```

#### 5.2.2 Sub-scenario: External App Without Token (Headless)

```
┌─────────────────────────────────────────────────────────────────┐
│ Scenario 2B: Headless - No user token provided                  │
│                                                                 │
│  External App ──> Request to Middleware                         │
│  POST /v2/crawler/sites/{id}/crawl                              │
│  (No Authorization header)                                      │
│                                               │                 │
│                                               v                 │
│  Middleware checks for override file:                           │
│  ├─> Override exists (device_code) → use cached admin token    │
│  ├─> Override exists (other)       → use specified method      │
│  └─> No override                   → use default (Managed ID)  │
│                                               │                 │
│                                               v                 │
│  SharePoint access = App permissions OR cached user permissions │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Smart Auth Selection (Design Decision)

**Decision**: OBO is always available alongside override/default, based on request header.

```
┌─────────────────────────────────────────────────────────────────┐
│ Smart Auth Selection Algorithm                                  │
│                                                                 │
│  Request arrives at endpoint                                    │
│              │                                                  │
│              v                                                  │
│  ┌─────────────────────────────────────────┐                    │
│  │ Does request have Authorization header? │                    │
│  └─────────────────────────────────────────┘                    │
│         │ YES                    │ NO                           │
│         v                        v                              │
│  ┌─────────────┐        ┌──────────────────────┐                │
│  │ Use OBO     │        │ Use override/default │                │
│  │ Exchange    │        │ Check override file  │                │
│  │ user token  │        │ or use default auth  │                │
│  └─────────────┘        └──────────────────────┘                │
│         │                        │                              │
│         v                        v                              │
│  SP access =              SP access =                           │
│  calling user's           app permissions OR                    │
│  permissions              cached admin permissions              │
└─────────────────────────────────────────────────────────────────┘
```

**Rationale:**
- Simple and predictable: header presence determines auth mode
- No mode switching required for OBO
- External apps can choose: send token (OBO) or don't (use default/override)
- Middleware UI always uses default/override (no user token in requests)

### 5.4 Error Handling for Access Denied

When SharePoint returns 401 (Unauthorized) or 403 (Forbidden):

```
┌─────────────────────────────────────────────────────────────────┐
│ Access Denied Handling                                          │
│                                                                 │
│  SharePoint returns 401/403                                     │
│              │                                                  │
│              v                                                  │
│  ┌─────────────────────────────────────────┐                    │
│  │ Which auth method was used?             │                    │
│  └─────────────────────────────────────────┘                    │
│         │                        │                              │
│    OBO (user token)         Override/Default                    │
│         │                        │                              │
│         v                        v                              │
│  ┌─────────────────┐    ┌─────────────────────────┐             │
│  │ Return 403      │    │ Return 403 with details │             │
│  │ "User lacks     │    │ "Auth method: [method]  │             │
│  │  SharePoint     │    │  failed for site [url]" │             │
│  │  access"        │    │                         │             │
│  └─────────────────┘    │ Include in response:    │             │
│                         │ - current_auth_method   │             │
│                         │ - error_code            │             │
│                         │ - suggested_action      │             │
│                         └─────────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

**No auto-failover** (per requirements):
- If Managed Identity fails, do NOT automatically try Certificate
- Return error to caller with clear indication of which method failed
- Admin must explicitly switch method via UI if needed

**Suggested actions in error response:**
- `token_expired`: "Admin must re-authenticate via Device Code"
- `permission_denied`: "User/app lacks access to this site"
- `auth_not_configured`: "Override method requires configuration"

### 5.5 Comparison: Who Has Access?

**With Application Permissions (Managed Identity, Certificate):**
- Access defined by app registration's Sites.Selected grants
- Same access regardless of who calls the API
- No user context

**With Delegated Override (Device Code, Interactive Browser):**
- Access = Admin's SharePoint permissions
- Anyone calling API gets admin's access level
- Token expires, requires re-auth

**With OBO (per-request user token):**
- Access = Calling user's SharePoint permissions
- Each user has their own access level
- User must have SharePoint access to target sites

## 6. Permission Model

### 6.1 Application Permissions

- **Sites.Selected**: Least-privilege, per-site access (RECOMMENDED)
- **Sites.ReadWrite.All**: All sites access (if many sites needed)
- Requires admin consent in Azure Portal
- No user context - app acts as itself

### 6.2 Delegated Permissions

- **Sites.Read.All / Sites.ReadWrite.All**: Access limited by user's SharePoint permissions
- Sites.Selected NOT available for delegated
- User must consent (or admin pre-consent)
- Effective access = App permissions ∩ User permissions

### 6.3 Permission Matrix by Method

**Application Permissions:**
- **Managed Identity**: Sites.Selected available, user permissions do not apply
- **Certificate**: Sites.Selected available, user permissions do not apply

**Delegated Permissions:**
- **Device Code**: Sites.Selected NOT available, user permissions apply
- **Interactive Browser**: Sites.Selected NOT available, user permissions apply
- **On-Behalf-Of**: Sites.Selected NOT available, user permissions apply

## 7. Implementation Constraints

### 7.1 SharePoint REST API Constraints

- Client secrets blocked for app-only access
- Certificate authentication required for `/_api/` endpoints with Application permissions
- Token audience must be `https://{tenant}.sharepoint.com`

### 7.2 Managed Identity Constraints

- Only works in Azure-hosted environments (App Service, Functions, VMs)
- IMDS endpoint (169.254.169.254) not available locally
- Cold start: 2-5 seconds first token acquisition
- Requires Sites.Selected grant via PowerShell (not Azure Portal)

### 7.3 Device Code Constraints

- Code expires after ~15 minutes
- Requires "Allow public client flows" enabled in app registration
- Polling interval: 5 seconds (SDK handles automatically)
- Token must be cached and shared across workers

### 7.4 On-Behalf-Of Constraints

- Requires middle-tier app to have permission to call downstream API
- User must have consented to downstream API scopes
- Middle-tier needs client secret or certificate

### 7.5 Token Caching Requirements

**System Auth (Certificate, Managed Identity):**
- In-memory cache per worker (credential auto-refreshes)
- No cross-worker sharing needed

**User Auth (Interactive Browser, Device Code):**
- Interactive Browser: Session cookie (per-user, travels with browser request)
- Device Code: Session-scoped token (stored in user's session after auth)
- User Auth does NOT break System Auth - isolated to user's session
- Refresh token handling for session longevity

### 7.6 Environment Requirements

- `PERSISTENT_STORAGE_PATH` must be set (from env var or Azure default)
- If not set: fail with clear error at startup, do not silently default
- Override file and token cache files stored under this path

### 7.7 Override File Safety

- Override file MUST only be written AFTER successful authentication test
- Flow: authenticate → test SharePoint access → on success write override file
- Prevents failure window where workers try an unconfigured method

## Sources

**Primary Sources:**
- `SPAUTH-IN10-SC-SESSION-CONV`: Session conversation 2026-03-14 - Requirements gathering [VERIFIED]
- `SPAUTH-AM01`: Certificate Credentials documentation [VERIFIED]
- `SPAUTH-AM03`: Managed Identity documentation [VERIFIED]
- `SPAUTH-AM04`: Interactive Browser documentation [VERIFIED]
- `SPAUTH-AM05`: Device Code documentation [VERIFIED]
- `SPAUTH-IN07`: Azure Permission Requirements [VERIFIED]

**Code Analysis:**
- `common_sharepoint_functions_v2.py`: Current certificate auth implementation [VERIFIED]
- `app.py`: Application architecture and config loading [VERIFIED]

## Next Steps

1. **Create SPEC**: Write `_SPEC_SPAUTH_MULTIAUTH.md` defining the AuthenticationFactory interface
2. **Analyze Current Code**: Map integration points for new auth methods in `common_sharepoint_functions_v2.py`
3. **Implement Managed Identity**: Priority 1 - most secure, zero-config for Azure
4. **Implement Device Code**: Priority 2 - fallback for when MI fails
5. **Implement On-Behalf-Of**: Priority 3 - for Scenario B (separate SPA)
6. **Design API Endpoints**: Auth status, method switching, Device Code initiation (deferred to SPEC phase)
7. **Design UI/UX**: Admin auth selection interface (deferred to SPEC phase, assumes UI will exist)

## Document History

**[2026-03-14 23:30]**
- Changed: Device Code moved from User Auth to System Auth (Tier 1)
- Changed: Section 2.3 diagram updated - Device Code now in System Auth
- Rationale: Device Code is emergency fallback - admin authenticates once, ALL workers use cached token

**[2026-03-14 23:20]**
- Changed: Authentication model updated to Two-Tier (System Auth + User Auth)
- Changed: Section 2.3 - replaced "Admin-Selected" with "Two-Tier Model" diagram
- Changed: Section 5.1 - User Auth is per-session, does not affect other callers
- Changed: Section 7.5 - Token caching now reflects per-session model for User Auth
- Added: Key principle "User Auth must NOT break System Auth"
- Rationale: Middleware workers may be used by other apps; admin login should not disrupt them

**[2026-03-14 20:40]**
- Fixed: OBO separated from admin-selectable methods (§3.2 → §3.3)
- Fixed: Method count clarified: 4 admin-selectable + OBO automatic
- Fixed: Interactive Browser available in any environment (not local-only)
- Changed: Default method from env vars/.env file, not hardcoded
- Changed: Override file written AFTER successful auth test (§7.7)
- Added: §7.6 Environment Requirements (PERSISTENT_STORAGE_PATH guard)
- Added: §7.7 Override File Safety
- Added: Client Secret clarification (supported in code, blocked for SharePoint)
- Added: Token audience `https://{tenant}.sharepoint.com` to §2.1
- Added: SharePoint REST API only scope note, Graph API deferred
- Changed: Next Steps - endpoints and UI/UX deferred to SPEC phase

**[2026-03-14 21:56]**
- Changed: Interactive Browser now primary delegated method (OAuth redirect, works in production)
- Changed: Device Code demoted to CLI/headless scenarios only
- Fixed: Removed "requires browser on server" misconception - middleware UI IS in browser
- Changed: Reordered delegated methods (Interactive Browser before Device Code)

**[2026-03-14 20:23]**
- Added: Section 5 - Runtime Behavior Scenarios
- Added: Smart Auth Selection design decision (OBO coexists with override/default)
- Added: Error handling for access denied scenarios
- Fixed: Section numbering (7.3, 7.4, 7.5)

**[2026-03-14 19:56]**
- Clarified: Certificate auth remains supported for other clients (not deprecation)

**[2026-03-14 19:55]**
- Initial requirements document created
- Captured all decisions from session conversation
- Five authentication methods identified
- Both UI architectures (A and B) documented
