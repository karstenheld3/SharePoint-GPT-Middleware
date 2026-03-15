# SPEC: SharePoint Multi-Authentication

**Doc ID**: SPAUTH-SP01
**Feature**: SHAREPOINT_MULTIAUTH
**Goal**: Replace hardcoded certificate auth with pluggable AuthenticationFactory supporting multiple auth methods across four implementation phases
**Timeline**: Created 2026-03-14

**Target file**: `src/routers_v2/common_sharepoint_functions_v2.py`

**Depends on:**
- `_INFO_SPAUTH_REQUIREMENTS.md [SPAUTH-IN10]` for requirements and architecture decisions
- `_INFO_SPAUTH_TOKEN_SHARING.md [SPAUTH-IN11]` for token sharing strategies
- `_INFO_SPAUTH-IN04_SDK_INTERNALS.md [SPAUTH-IN04]` for SDK integration patterns
- `_INFO_SPAUTH-AM01_CERTIFICATE_CREDENTIALS.md [SPAUTH-AM01]` for certificate auth details
- `_INFO_SPAUTH-AM03_MANAGED_IDENTITY.md [SPAUTH-AM03]` for Managed Identity (MI) auth details
- `_INFO_SPAUTH-AM04_INTERACTIVE_BROWSER.md [SPAUTH-AM04]` for interactive browser details
- `_INFO_SPAUTH-AM05_DEVICE_CODE.md [SPAUTH-AM05]` for device code details
- `_INFO_SPAUTH-AM08_ON_BEHALF_OF.md [SPAUTH-AM08]` for On-Behalf-Of (OBO) details

**Does not depend on:**
- Graph API authentication (separate session, Graph client stays on certificate for now)
- V1 router code (V1 routers are legacy, not in scope)

## MUST-NOT-FORGET

- `ClientContext.with_access_token(token_func)` is the canonical integration pattern for non-certificate auth methods
- Library has built-in token caching - do NOT add external caching for `ClientContext` tokens
- `TokenResponse` requires `accessToken` (str), `tokenType` (str), optionally `expiresIn` (int seconds)
- SharePoint REST API token scope: `https://{tenant}.sharepoint.com/.default` (the `.default` suffix requests all configured permissions)
- Current `get_or_create_pem_from_pfx()` must be preserved (certificate auth stays)
- `get_crawler_config()` in `crawler.py` currently returns cert-only config dict - must be extended
- `common_security_scan_functions_v2.py` also calls `connect_to_site_using_client_id_and_certificate()` - in scope
- `sites.py` also calls `connect_to_site_using_client_id_and_certificate()` - in scope
- No auto-failover between methods - admin explicitly selects method
- Override file written ONLY after successful auth test
- Interactive Browser = standard OAuth redirect in user's browser (NOT server-side browser launch)
- Graph client (`get_graph_client()`) stays on certificate auth - out of scope for this SPEC
- FAILS: SPAUTH-FL-001 (headless browser misconception)

## Table of Contents

1. [Scenario](#1-scenario)
2. [Context](#2-context)
3. [Domain Objects](#3-domain-objects)
4. [Implementation Phases](#4-implementation-phases)
5. [Phase 1: Certificate + Managed Identity](#5-phase-1-certificate--managed-identity)
6. [Phase 2: Interactive Browser](#6-phase-2-interactive-browser)
7. [Phase 3: Device Code](#7-phase-3-device-code)
8. [Phase 4: On-Behalf-Of](#8-phase-4-on-behalf-of)
9. [Cross-Phase Design Decisions](#9-cross-phase-design-decisions)
10. [Cross-Phase Implementation Guarantees](#10-cross-phase-implementation-guarantees)
11. [Key Mechanisms](#11-key-mechanisms)
12. [Action Flow](#12-action-flow)
13. [Data Structures](#13-data-structures)
14. [Implementation Details](#14-implementation-details)
15. [PROPOSAL: Unified Authentication Router](#15-proposal-unified-authentication-router)
16. [Document History](#16-document-history)

## 1. Scenario

**Problem:** One client disabled certificate-based authentication. The crawler cannot connect to their SharePoint sites. Currently, `connect_to_site_using_client_id_and_certificate()` is the only auth path. Adding Managed Identity requires an abstraction layer. Future needs include personal account fallback and Single Page Application (SPA) frontend support.

**Solution:**
- Introduce `AuthenticationFactory` that returns `ClientContext` for any auth method
- Phase implementation: Certificate + Managed Identity first, then Interactive Browser, then Device Code, then On-Behalf-Of (OBO)
- Admin selects auth method explicitly (no auto-failover)
- All callers get `ClientContext` regardless of auth method - no downstream changes needed

**What we don't want:**
- Auto-failover chains (silent fallback masks configuration errors)
- `DefaultAzureCredential` chain (unpredictable in production, tries too many methods)
- Graph API scope in this SPEC (separate session)
- Breaking changes to existing endpoint signatures
- External token caching layer (library handles it)
- Server-side browser launch for Interactive Browser (use OAuth redirect)

## 2. Context

### Current Architecture

```
┌───────────────────────────────────────────────────────────────────────────────┐
│  Callers                                                                      │
│  ├─> crawler.py          → connect_to_site_using_client_id_and_certificate()  │
│  ├─> sites.py            → connect_to_site_using_client_id_and_certificate()  │
│  └─> common_security_scan_functions_v2.py → same function + get_graph_client()│
├───────────────────────────────────────────────────────────────────────────────┤
│  Auth Layer (common_sharepoint_functions_v2.py)                               │
│  └─> connect_to_site_using_client_id_and_certificate()                        │
│      └─> ClientContext(site_url).with_client_certificate(...)                 │
├───────────────────────────────────────────────────────────────────────────────┤
│  Library (office365-rest-python-client 2.6.2)                                 │
│  └─> ClientContext → AuthenticationContext → Microsoft Authentication Library │
│      (MSAL) → Token → HTTP request                                            │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Target Architecture

```
┌───────────────────────────────────────────────────────────────────────────────┐
│  Callers (unchanged signatures)                                               │
│  ├─> crawler.py          → get_sharepoint_context(site_url, request)          │
│  ├─> sites.py            → get_sharepoint_context(site_url, request)          │
│  └─> common_security_scan_functions_v2.py → get_sharepoint_context(...)       │
├───────────────────────────────────────────────────────────────────────────────┤
│  Auth Layer (common_sharepoint_functions_v2.py)                               │
│  ├─> AuthenticationFactory                                                    │
│  │   ├─> CertificateProvider     → ClientContext.with_client_certificate()    │
│  │   ├─> ManagedIdentityProvider → ClientContext.with_access_token()          │
│  │   ├─> InteractiveBrowserProvider → ClientContext.with_access_token()       │
│  │   ├─> DeviceCodeProvider      → ClientContext.with_access_token()          │
│  │   └─> OnBehalfOfProvider      → ClientContext.with_access_token()          │
│  └─> AuthStateManager (override file + default config)                        │
├───────────────────────────────────────────────────────────────────────────────┤
│  Library (office365-rest-python-client 2.6.2)                                 │
│  └─> ClientContext → AuthenticationContext → built-in token cache → HTTP      │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Hosting Environment

- **Production**: Azure App Service (Managed Identity primary; Interactive Browser available as admin fallback)
- **Local dev**: Developer machine (Certificate primary; Interactive Browser available)
- **Single tenant**: One Microsoft Entra ID tenant per deployment

## 3. Domain Objects

### AuthMethod

An **AuthMethod** is an enum representing a supported authentication mechanism.

**System Auth (app-only or admin-delegated)** - configured system-wide via env var or override file:
- `certificate` - certificate credentials (current implementation)
- `managed_identity` - Azure Managed Identity (Phase 1)
- `device_code` - admin authenticates once, all workers use cached token (Phase 3)

**User Auth (delegated)** - per-session overlay, used when user has authenticated:
- `interactive_browser` - OAuth redirect in user's browser (Phase 2)
- `on_behalf_of` - per-request user token exchange (Phase 4)

**Two-Tier Model:** System Auth is always configured (via env var or override file). User Auth is an optional per-session overlay that takes precedence when the request carries a valid user session. This separation ensures non-browser API calls always work via System Auth, while browser-based admin sessions can use delegated permissions. Device Code is System Auth because admin authenticates once and ALL workers/callers use that token (emergency fallback for blocked sites).

### AuthProvider

An **AuthProvider** creates an authenticated `ClientContext` for a specific `AuthMethod`.

**Interface:**
- `get_context(site_url: str, request: Request | None = None) -> ClientContext` - returns authenticated context; `request` required for User Auth methods (Interactive Browser, On-Behalf-Of)
- `validate(site_url: str) -> tuple[bool, str | None]` - tests auth; returns `(True, None)` on success, `(False, error_message)` on failure
- `method` - the `AuthMethod` this provider handles

### AuthenticationFactory

The **AuthenticationFactory** resolves which `AuthProvider` to use for a given request.

**Resolution order (Two-Tier):**
1. [Phase 4] If request has `Authorization` header AND On-Behalf-Of is enabled -> `OnBehalfOfProvider`
2. [Phase 2] If request has valid user session (Interactive Browser token) -> use session's User Auth
3. If override file exists -> provider for overridden System Auth method (certificate, managed_identity, or device_code)
4. Else -> provider for default System Auth method (from env config)

**Note:** Steps 1-2 check for User Auth (per-session). Steps 3-4 resolve System Auth (system-wide). User Auth takes precedence when present, but non-browser API calls without session always use System Auth. Device Code is resolved via override file (step 3) or default (step 4), not per-session.

**Storage:** N/A (stateless, reads config on each call)

### AuthStateManager

The **AuthStateManager** manages the current effective auth method.

**Storage:** `{PERSISTENT_STORAGE_PATH}/sharepoint_online_auth_override.json`

**Key properties:**
- `default_method` - from environment config (`CRAWLER_USE_MANAGED_IDENTITY`)
- `override` - from override file (if exists)
- `effective_method` - override if present, else default

### Override File

An **Override File** persists an admin-selected auth method that differs from the default.

**Storage:** `{PERSISTENT_STORAGE_PATH}/sharepoint_online_auth_override.json`

**Note:** This file stores only the method selection, NOT tokens. Token storage is method-specific:
- Device Code tokens: `{PERSISTENT_STORAGE_PATH}/sharepoint_online_device_code_cache.bin`
- Interactive Browser tokens: encrypted session cookie (travels with each browser request; provider reads from `request.session`, passes to `with_access_token()`)
- Managed Identity/Certificate: no disk persistence needed (in-memory cache per worker; credential auto-refreshes)

**Schema:** (3 valid method values - System Auth only)

```json
{ "method": "certificate", "set_by": "admin@contoso.com", "set_at_utc": "2026-03-14T21:00:00Z" }
```

```json
{ "method": "managed_identity", "set_by": "admin@contoso.com", "set_at_utc": "2026-03-14T21:00:00Z" }
```

```json
{ "method": "device_code", "set_by": "admin@contoso.com", "set_at_utc": "2026-03-14T21:00:00Z" }
```

**Note:** User Auth methods (`interactive_browser`, `on_behalf_of`) are NOT valid override values. They are per-session and managed via user login, not system-wide override.

## 4. Implementation Phases

### Phase Overview

- **Phase 1**: Certificate + Managed Identity (COMPLEXITY-LOW)
  - AuthenticationFactory, AuthProvider interface, CertificateProvider, ManagedIdentityProvider
  - AuthStateManager with default method from env config
  - Replace all `connect_to_site_using_client_id_and_certificate()` calls
  - Auth status endpoint, selftest integration

- **Phase 2**: Interactive Browser (COMPLEXITY-LOW)
  - InteractiveBrowserProvider using OAuth Authorization Code redirect
  - `/auth/login`, `/auth/callback` endpoints
  - Session-based token storage (per user, no cross-worker sharing needed)
  - Override file read/write support (System Auth methods only)

- **Phase 3**: Device Code (COMPLEXITY-MEDIUM)
  - DeviceCodeProvider with shared file-based token cache
  - `/auth/device-code/initiate`, `/auth/device-code/status` endpoints
  - Cross-worker token sharing via `msal-extensions` file locking
  - Admin-initiated flow via middleware UI

- **Phase 4**: On-Behalf-Of (COMPLEXITY-HIGH)
  - OnBehalfOfProvider with per-request token exchange
  - Smart Auth Selection (Authorization header detection)
  - Token validation (issuer, audience, claims)
  - Per-user in-memory token cache
  - Only implement when separate SPA frontend materializes

### Phase Dependencies

```
Phase 1 (Certificate + MI)
    └─> Phase 2 (Interactive Browser) - uses AuthenticationFactory from Phase 1
        └─> Phase 3 (Device Code) - uses override file from Phase 2
            └─> Phase 4 (OBO) - uses Smart Auth Selection
```

## 5. Phase 1: Certificate + Managed Identity

### Functional Requirements

**SPAUTH-FR-01: AuthenticationFactory**
- Single entry point for all callers to get authenticated `ClientContext`
- Signature: `get_sharepoint_context(site_url: str, request: Request) -> ClientContext`
- Resolves effective auth method via `AuthStateManager`
- Returns `ClientContext` ready for SharePoint operations
- Raises descriptive error if auth method not configured or fails

**SPAUTH-FR-02: CertificateProvider**
- Wraps existing `connect_to_site_using_client_id_and_certificate()` logic
- Config from env: `CRAWLER_CLIENT_ID`, `CRAWLER_TENANT_ID`, `CRAWLER_CLIENT_CERTIFICATE_PFX_FILE`, `CRAWLER_CLIENT_CERTIFICATE_PASSWORD`
- PFX-to-PEM conversion preserved (`get_or_create_pem_from_pfx()`)
- Uses `ClientContext.with_client_certificate()` (unchanged from current)

**SPAUTH-FR-03: ManagedIdentityProvider**
- Uses `azure.identity.ManagedIdentityCredential`
- Config from env: `AZURE_CLIENT_ID` (optional, for user-assigned MI)
- Token scope: `https://{tenant}.sharepoint.com/.default`
- Tenant extracted from site URL or `CRAWLER_TENANT_NAME` env var
- Returns `ClientContext.with_access_token(token_func)` where `token_func` returns `TokenResponse`

**SPAUTH-FR-04: AuthStateManager (Phase 1 scope)**
- Reads default method from `CRAWLER_USE_MANAGED_IDENTITY` env var (default: `false` = certificate)
- Valid values: `true` (managed_identity), `false` (certificate)
- Matches OpenAI pattern (`AZURE_OPENAI_USE_MANAGED_IDENTITY`)
- No override file support in Phase 1 (added in Phase 2)

**SPAUTH-FR-05: Auth Status Endpoint**
- `GET /v2/auth/status` returns current auth state
- Response: `{ "effective_method": "managed_identity", "default_method": "managed_identity", "override": null }`
- No authentication required on this endpoint

**SPAUTH-FR-06: Selftest Integration**
- Extend existing selftest in `crawler.py` to use `AuthenticationFactory`
- Test: acquire token + read a known library (e.g., `/SiteAssets`)
- Report which auth method was used and whether it succeeded

**SPAUTH-FR-07: Caller Migration**
- Replace `connect_to_site_using_client_id_and_certificate(site_url, client_id, tenant_id, cert_path, cert_password)` with `get_sharepoint_context(site_url, request)` in:
  - `crawler.py` (2 call sites)
  - `sites.py` (3 call sites)
  - `common_security_scan_functions_v2.py` (4 call sites, SharePoint only - Graph stays unchanged)

### Design Decisions

**SPAUTH-DD-01:** AuthenticationFactory is a module-level function, not a class singleton. Rationale: simpler, no lifecycle management, aligns with existing codebase style (functions, not service classes).

**SPAUTH-DD-02:** Provider resolution happens per-call, not cached. Rationale: override file can change between calls; factory re-reads effective method each time.

**SPAUTH-DD-03:** ManagedIdentityCredential is instantiated once at module level and reused. Rationale: `azure.identity` credentials are designed for reuse; internal token caching is per-credential-instance.

**SPAUTH-DD-04:** Token scope derived from site URL hostname. `https://contoso.sharepoint.com/sites/hr` -> scope `https://contoso.sharepoint.com/.default`. Fallback: if URL doesn't contain `.sharepoint.com` (e.g., vanity domain), use `CRAWLER_TENANT_NAME` env var. Rationale: avoids separate tenant name config in common case; fallback handles edge cases.

**SPAUTH-DD-05:** `get_crawler_config()` in `crawler.py` extended to include `auth_method` field. Rationale: selftest and other callers need to know current method without reading env vars directly.

### Implementation Guarantees

**SPAUTH-IG-01:** Existing certificate auth behavior is identical before and after migration. No changes to PFX handling, PEM caching, or `ClientContext.with_client_certificate()` parameters.

**SPAUTH-IG-02:** If `CRAWLER_USE_MANAGED_IDENTITY=false`, behavior is byte-for-byte identical to current code. No new dependencies loaded, no new network calls.

**SPAUTH-IG-03:** If `CRAWLER_USE_MANAGED_IDENTITY` is not set, default is `false` (certificate). Rationale: zero-config backward compatibility.

**SPAUTH-IG-04:** ManagedIdentityCredential failure produces actionable error: "Managed Identity not available. Ensure app is running in Azure with MI enabled, or set CRAWLER_USE_MANAGED_IDENTITY=false." No automatic fallback to `DefaultAzureCredential` or `AzureCliCredential` - admin must explicitly configure method for local dev (per SPAUTH-DD-42).

**SPAUTH-IG-05:** All callers receive `ClientContext` with identical interface regardless of auth method. No caller needs to know which method was used.

## 6. Phase 2: Interactive Browser

### Functional Requirements

**SPAUTH-FR-10: InteractiveBrowserProvider**
- Uses Microsoft Authentication Library (MSAL) `ConfidentialClientApplication` with Authorization Code + Proof Key for Code Exchange (PKCE) flow
- Config from env: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET` (or certificate), `AUTH_REDIRECT_URI`
- Token scopes: `https://{tenant}.sharepoint.com/Sites.Read.All`, `offline_access` (delegated permissions require explicit scopes, not `.default`)
- Standard OAuth redirect flow: `/auth/login` -> Microsoft login -> `/auth/callback`
- Token stored in user session (FastAPI session middleware)

**SPAUTH-FR-11: Login Endpoint**
- `GET /v2/auth/login` initiates OAuth redirect
- Generates PKCE challenge, stores state in session
- Redirects to `login.microsoftonline.com` authorization endpoint
- After successful callback, creates `ClientContext.with_access_token()` using session token

**SPAUTH-FR-12: Callback Endpoint**
- `GET /v2/auth/callback` receives authorization code
- Validates state parameter against session
- Exchanges code for tokens via MSAL
- Stores tokens in session
- Redirects user back to middleware UI

**SPAUTH-FR-13: Override File Support**
- AuthStateManager extended to read/write override file
- Admin can set override via `POST /v2/auth/override` with `{ "method": "certificate" }` (or `managed_identity`, `device_code`)
- Override written ONLY after successful auth test (SPAUTH-FR-06 selftest)
- `DELETE /v2/auth/override` removes override, reverts to default method
- Note: User Auth methods (`interactive_browser`, `on_behalf_of`) are NOT valid override values - they are per-session

**SPAUTH-FR-14: Auth Status Extended**
- `GET /v2/auth/status` now includes override info and session status
- Response adds: `"override": { "method": "device_code", "set_by": "admin@contoso.com", "set_at_utc": "..." }` or `null`
- Note: `session_authenticated: true` indicates active User Auth (Interactive Browser) session, separate from System Auth override

### Design Decisions

**SPAUTH-DD-10:** Interactive Browser uses Authorization Code flow (not `InteractiveBrowserCredential` from `azure.identity`). Rationale: `InteractiveBrowserCredential` opens a local browser on the server. The middleware UI is already in the user's browser, so standard OAuth redirect is correct.

**SPAUTH-DD-11:** Session middleware added for token storage. Rationale: per-user tokens stored in encrypted session cookie. No cross-worker sharing needed for Interactive Browser. If encrypted token payload exceeds cookie size limits (~4KB), use server-side session storage keyed by session ID instead.

**SPAUTH-DD-12:** `offline_access` scope requested for refresh tokens. Rationale: allows silent token refresh without re-prompting user.

### Token Flow (Session Cookie to SharePoint Header)

```
1. STORAGE: Session cookie in user's browser
   ├─> Encrypted by SESSION_SECRET_KEY
   └─> Contains: { access_token, refresh_token, expires_at }

2. SERVER READS: FastAPI session middleware
   ├─> Request arrives with session cookie
   └─> Session data available via request.session["sharepoint_token"]

3. INTO HEADER: via with_access_token()
   ├─> InteractiveBrowserProvider.get_context(site_url)
   │   └─> token_func = lambda: TokenResponse(request.session["sharepoint_token"])
   ├─> ClientContext(site_url).with_access_token(token_func)
   └─> Library internally sets: Authorization: Bearer <token>
```

### Token Refresh Mechanism

The `token_func` passed to `with_access_token()` must handle token refresh:

```python
def _token_func():
    token_data = request.session["sharepoint_token"]
    expires_at = token_data["expires_at"]
    remaining = expires_at - time.time()
    
    if remaining <= 300:  # 5 minute buffer
        # Refresh using MSAL + refresh_token
        result = msal_app.acquire_token_by_refresh_token(
            token_data["refresh_token"],
            scopes=["https://{tenant}.sharepoint.com/Sites.Read.All"]
        )
        if "access_token" in result:
            # Update session with new tokens
            request.session["sharepoint_token"] = {
                "access_token": result["access_token"],
                "refresh_token": result.get("refresh_token", token_data["refresh_token"]),
                "expires_at": time.time() + result["expires_in"]
            }
            token_data = request.session["sharepoint_token"]
        else:
            raise AuthError("Session expired. Please re-authenticate via /v2/auth/login.")
    
    return TokenResponse(
        access_token=token_data["access_token"],
        token_type="Bearer",
        expiresIn=int(max(0, token_data["expires_at"] - time.time()))
    )
```

**Key points:**
- Check expiry before returning token
- Use 5-minute buffer to refresh proactively
- Update session with refreshed tokens
- If refresh fails, raise clear error per SPAUTH-IG-13

### Implementation Guarantees

**SPAUTH-IG-10:** Interactive Browser auth does not affect requests that don't use it. If default method is `managed_identity`, the `/auth/login` endpoint exists but is not invoked by normal API calls.

**SPAUTH-IG-11:** Override file is atomic: write to temp file, then rename. No partial reads by concurrent workers.

**SPAUTH-IG-12:** When override is active, all workers use the overridden method within one request cycle (file is re-read per factory call, per SPAUTH-DD-02).

**SPAUTH-IG-13:** If session token expires mid-operation, the operation fails with clear error "Session expired. Please re-authenticate via /v2/auth/login." Does NOT silently switch to default method.

## 7. Phase 3: Device Code

### Functional Requirements

**SPAUTH-FR-20: DeviceCodeProvider**
- Uses MSAL `PublicClientApplication` with device code flow
- Config from env: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`
- Token scopes: `https://{tenant}.sharepoint.com/Sites.Read.All`, `offline_access` (delegated flow)
- Shared file-based token cache using `msal-extensions` for cross-worker locking
- Cache location: `{PERSISTENT_STORAGE_PATH}/sharepoint_online_device_code_cache.bin`

**SPAUTH-FR-21: Device Code Initiation Endpoint**
- `POST /v2/auth/device-code/initiate` starts device code flow
- Returns: `{ "user_code": "ABCD-EFGH", "verification_uri": "https://microsoft.com/devicelogin", "expires_in": 900 }`
- Middleware does NOT poll automatically - separate status endpoint used

**SPAUTH-FR-22: Device Code Status Endpoint**
- `GET /v2/auth/device-code/status` checks if user completed auth
- Returns: `{ "status": "pending" | "completed" | "expired", "user": "admin@contoso.com" }`
- On `completed`: token cached, override file written (after auth test)

**SPAUTH-FR-23: Token Cache Sharing**
- All workers access same file-based MSAL token cache
- `msal-extensions` `PersistedTokenCache` with platform-specific persistence: `FilePersistenceWithDataProtection` (Windows), `LibsecretPersistence` (Linux with libsecret), or `PlainTextPersistence` (fallback)
- Automatic token refresh via MSAL when refresh token is available

### Design Decisions

**SPAUTH-DD-20:** Device Code flow is admin-initiated only. No automatic initiation. Rationale: requires human interaction, should be explicit.

**SPAUTH-DD-21:** Single shared token for all workers (not per-user). Rationale: Device Code is an emergency fallback where admin authenticates once for the whole system.

**SPAUTH-DD-22:** New dependency: `msal-extensions` for file-based token cache with cross-platform locking. Note: `msal-extensions` is a separate package, NOT a transitive dependency of `azure-identity`. Must be explicitly added to `pyproject.toml` in Phase 3.

### Implementation Guarantees

**SPAUTH-IG-20:** Device Code token survives worker restarts. Cache is file-based, not in-memory.

**SPAUTH-IG-21:** If token cache file is corrupted or unreadable, DeviceCodeProvider falls back to "not authenticated" state with clear error. Does not crash.

**SPAUTH-IG-22:** Device Code polling does not block the event loop. Uses async polling or background task.

## 8. Phase 4: On-Behalf-Of

### Functional Requirements

**SPAUTH-FR-30: OnBehalfOfProvider**
- Uses MSAL `ConfidentialClientApplication.acquire_token_on_behalf_of()`
- Config from env: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET` (or certificate)
- Input: user's access token from `Authorization` header
- Output: SharePoint token for that user
- In-memory per-worker token cache keyed by hash of user token

**SPAUTH-FR-31: Smart Auth Selection**
- If request has `Authorization: Bearer <token>` header AND On-Behalf-Of is enabled -> use On-Behalf-Of
- If no Authorization header -> use default/override method
- On-Behalf-Of enable/disable controlled by env var `SHAREPOINT_ON_BEHALF_OF_ENABLED` (default: `false`)

**SPAUTH-FR-32: Token Validation**
- Validate incoming user token before OBO exchange:
  - Token issuer matches expected Azure AD tenant
  - Token audience matches middleware's client ID
  - Token is not expired
- Reject with 401 if validation fails

**SPAUTH-FR-33: Long-Running Job Consideration**
- OBO tokens have limited lifetime (~1 hour)
- For long-running crawl jobs, token may expire mid-operation
- Strategy: acquire OBO token at job start, if it expires mid-crawl, fail that operation with clear error
- Do NOT silently switch to app-only auth mid-job

### Design Decisions

**SPAUTH-DD-30:** OBO is opt-in via env var, not enabled by default. Rationale: requires additional Azure AD configuration (API permissions, client secret). Should not activate accidentally.

**SPAUTH-DD-31:** OBO takes priority over override when both conditions are met (Authorization header present AND OBO enabled). Rationale: the caller explicitly sent a user token, indicating they want user-context access.

**SPAUTH-DD-32:** OBO token cache is in-memory per worker, not shared. Rationale: OBO tokens are per-user, per-request. No benefit to sharing across workers. IN11 confirms in-memory is sufficient.

### Implementation Guarantees

**SPAUTH-IG-30:** If On-Behalf-Of is disabled (`SHAREPOINT_ON_BEHALF_OF_ENABLED=false`), Authorization headers are ignored for auth selection. Requests use default/override method.

**SPAUTH-IG-31:** OBO failure does NOT fall back to default/override method. Returns 401/403 to caller. Rationale: caller sent user token expecting user-context access. Silently using app permissions would be a privilege escalation.

## 9. Cross-Phase Design Decisions

**SPAUTH-DD-40:** All auth providers return `ClientContext`. No provider returns raw tokens. Rationale: callers operate on `ClientContext` exclusively. Uniform interface.

**SPAUTH-DD-41:** Auth provider errors include method name in exception message. Example: `"[managed_identity] Failed to acquire token: IMDS endpoint not available"`. Rationale: admin must know WHICH method failed to take corrective action.

**SPAUTH-DD-42:** No auto-failover between methods. If configured method fails, return error. Rationale: silent failover masks misconfiguration, violates principle of least surprise, may cause unexpected privilege changes.

**SPAUTH-DD-43:** `get_graph_client()` in `common_security_scan_functions_v2.py` stays on certificate auth. Out of scope. Rationale: Graph client works, separate session planned. Avoids scope creep per review findings SPAUTH-RV-005.

**SPAUTH-DD-44:** Environment variable `CRAWLER_USE_MANAGED_IDENTITY` controls default auth method (boolean, matches OpenAI pattern):
- `false` (default): Certificate authentication
- `true`: Managed Identity authentication
- Phase 2+: Override file support for System Auth methods (`certificate`, `managed_identity`)
- Phase 3: Override file adds `device_code` option
- Phase 4: OBO is not a selectable default (automatic per-request only)

## 10. Cross-Phase Implementation Guarantees

**SPAUTH-IG-40:** Each phase is independently deployable. Phase 2 code can exist without Phase 3/4. Unused providers are never instantiated.

**SPAUTH-IG-41:** No new pip dependencies in Phase 1 (`azure-identity` already in `pyproject.toml`). Phase 2 adds `itsdangerous` for signed session cookies. Phase 3 adds `msal-extensions` (separate package, NOT transitive via `azure-identity`).

**SPAUTH-IG-42:** `PERSISTENT_STORAGE_PATH` must be set for override file and token cache operations. If not set, factory logs warning and operates without override support.

**SPAUTH-IG-43:** All auth endpoints are under `/v2/auth/` prefix. No changes to existing endpoint paths.

## 11. Key Mechanisms

### Token Acquisition via `with_access_token()`

All non-certificate providers use the same pattern:

```python
def get_context(self, site_url: str) -> ClientContext:
    return ClientContext(site_url).with_access_token(self._token_func)
```

Where `_token_func` is a zero-arg callable returning `TokenResponse`:

```python
from office365.runtime.auth.token_response import TokenResponse

def _token_func():
    token = credential.get_token(f"https://{tenant}.sharepoint.com/.default")
    return TokenResponse(
        access_token=token.token,
        token_type="Bearer",
        expiresIn=int(token.expires_on - time.time())
    )
```

The library caches the `TokenResponse` internally and only calls `_token_func` when the token is `None` or expired.

### Override File Resolution

```
Request arrives
├─> AuthenticationFactory.get_sharepoint_context(site_url, request)
│   ├─> [Phase 4] Check Authorization header + On-Behalf-Of enabled -> OnBehalfOfProvider
│   ├─> AuthStateManager.get_effective_method()
│   │   ├─> Read override file (if exists, valid JSON, known method)
│   │   └─> Else: read CRAWLER_USE_MANAGED_IDENTITY env var
│   │       ├─> true  -> ManagedIdentityProvider (requires Azure, no credentials needed)
│   │       └─> false -> CertificateProvider (works anywhere, requires cert config)
│   └─> Instantiate/reuse provider for effective method
│       └─> provider.get_context(site_url) -> ClientContext
└─> Caller uses ClientContext normally
```

### Tenant Extraction from URL

```python
def _extract_tenant_from_url(site_url: str) -> str:
    # "https://contoso.sharepoint.com/sites/hr" -> "contoso"
    hostname = urlparse(site_url).hostname  # contoso.sharepoint.com
    return hostname.split('.')[0]           # contoso
```

Scope becomes: `https://contoso.sharepoint.com/.default`

## 12. Action Flow

### Phase 1: Normal Request Flow

```
API request (e.g., POST /v2/crawler/sites/{id}/crawl)
├─> crawler endpoint handler
│   ├─> get_sharepoint_context(site_url, request)
│   │   ├─> AuthStateManager.get_effective_method()
│   │   │   └─> Returns "managed_identity" (from env)
│   │   └─> ManagedIdentityProvider.get_context(site_url)
│   │       └─> ClientContext(site_url).with_access_token(_managed_identity_token_func)
│   └─> ctx used for SharePoint operations (unchanged)
└─> Response returned
```

### Phase 2: Interactive Browser Login Flow

```
Admin clicks "Login with Microsoft" in middleware UI
├─> GET /v2/auth/login
│   ├─> Generate PKCE challenge, store state in session
│   └─> Redirect to login.microsoftonline.com/authorize
│
User authenticates in browser
├─> Microsoft redirects to GET /v2/auth/callback?code=...&state=...
│   ├─> Validate state matches session
│   ├─> Exchange code for tokens via MSAL
│   ├─> Store tokens in session (User Auth, per-session)
│   ├─> Test SharePoint access (selftest)
│   └─> Redirect to middleware UI with success message
│
Subsequent API requests (with session cookie)
├─> AuthenticationFactory checks request.session for User Auth token
├─> User Auth active -> InteractiveBrowserProvider.get_context(site_url, request)
│   └─> ClientContext.with_access_token() using session token
└─> SharePoint operations use user's delegated permissions

Note: Interactive Browser does NOT write to override file. It uses per-session tokens.
System Auth (override file) remains available for non-browser API callers.
```

### Phase 3: Device Code Flow

```
Admin clicks "Start Device Code" in middleware UI
├─> POST /v2/auth/device-code/initiate
│   ├─> MSAL PublicClientApplication.initiate_device_flow()
│   └─> Returns { user_code, verification_uri, expires_in }
│
Admin authenticates on separate device
├─> Middleware UI polls GET /v2/auth/device-code/status
│   ├─> Check if MSAL flow completed
│   ├─> On completion: cache token, test SharePoint, write override
│   └─> Returns { status: "completed", user: "admin@contoso.com" }
│
Subsequent API requests (all workers)
├─> AuthStateManager reads override file -> "device_code"
├─> DeviceCodeProvider.get_context(site_url)
│   └─> ClientContext.with_access_token() using cached file token
└─> SharePoint operations use admin's permissions
```

## 13. Data Structures

### Auth Status Response (Phase 1)

```json
{
  "effective_method": "managed_identity",
  "default_method": "managed_identity",
  "override": null,
  "available_methods": ["certificate", "managed_identity"]
}
```

### Auth Status Response (Phase 2+, with override active)

```json
{
  "effective_method": "device_code",
  "default_method": "managed_identity",
  "override": {
    "method": "device_code",
    "set_by": "admin@contoso.com",
    "set_at_utc": "2026-03-14T21:00:00Z"
  },
  "available_methods": ["certificate", "managed_identity", "device_code"],
  "session_authenticated": false
}
```

### Override File

```json
{
  "method": "device_code",
  "set_by": "admin@contoso.com",
  "set_at_utc": "2026-03-14T21:00:00Z"
}
```

### Auth Error Response

```json
{
  "error": "auth_failed",
  "auth_method": "managed_identity",
  "detail": "IMDS endpoint not available. Ensure app is running in Azure with Managed Identity enabled.",
  "suggested_action": "Set CRAWLER_USE_MANAGED_IDENTITY=false or deploy to Azure"
}
```

### Device Code Initiation Response (Phase 3)

```json
{
  "user_code": "ABCD-EFGH",
  "verification_uri": "https://microsoft.com/devicelogin",
  "expires_in": 900,
  "message": "To sign in, visit https://microsoft.com/devicelogin and enter code ABCD-EFGH"
}
```

## 14. Implementation Details

### Module Structure

```
src/routers_v2/
├─> common_sharepoint_functions_v2.py    # Existing + AuthenticationFactory + providers
├─> common_sharepoint_auth_v2.py         # NEW: AuthStateManager, auth endpoints router
├─> crawler.py                           # Modified: use get_sharepoint_context()
├─> sites.py                             # Modified: use get_sharepoint_context()
└─> common_security_scan_functions_v2.py # Modified: SP calls use get_sharepoint_context()
```

### New Environment Variables

Phase 1:
- `CRAWLER_USE_MANAGED_IDENTITY` - `true` for Managed Identity, `false` for Certificate (default: `false`)
- `CRAWLER_MANAGED_IDENTITY_OBJECT_ID` - **Object ID** (Principal ID) of MI, NOT Client ID [VERIFIED]. Used for Sites.Selected permission grants via PnP PowerShell. Optional for system-assigned MI.
- `CRAWLER_SHAREPOINT_TENANT_NAME` - fallback tenant name if not derivable from URL (existing)

Phase 2 adds:
- `AUTH_REDIRECT_URI` - OAuth callback URL (e.g., `https://myapp.azurewebsites.net/v2/auth/callback`)
- `AZURE_CLIENT_SECRET` - for MSAL ConfidentialClientApplication (or use existing certificate)
- `SESSION_SECRET_KEY` - for session encryption

Phase 3 adds:
- No new env vars (uses existing `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `PERSISTENT_STORAGE_PATH`)

Phase 4 adds:
- `SHAREPOINT_ON_BEHALF_OF_ENABLED` - enable On-Behalf-Of flow (`true` | `false`), default: `false`

### Function Signatures

```python
# Phase 1 - core
def get_sharepoint_context(site_url: str, request: Request) -> ClientContext: ...
def get_effective_auth_method(request: Request) -> str: ...
def get_auth_status(request: Request) -> dict: ...

# Phase 1 - providers (internal)
class AuthProvider(Protocol):
    method: str
    def get_context(self, site_url: str, request: Request | None = None) -> ClientContext: ...
    def validate(self, site_url: str) -> tuple[bool, str | None]: ...

class CertificateProvider: ...     # wraps existing logic
class ManagedIdentityProvider: ... # azure.identity + with_access_token

# Phase 2
async def auth_login(request: Request) -> RedirectResponse: ...
async def auth_callback(request: Request) -> RedirectResponse: ...
async def set_auth_override(request: Request, body: dict) -> dict: ...
async def delete_auth_override(request: Request) -> dict: ...
class InteractiveBrowserProvider: ...

# Phase 3
async def initiate_device_code(request: Request) -> dict: ...
async def get_device_code_status(request: Request) -> dict: ...
class DeviceCodeProvider: ...

# Phase 4
class OnBehalfOfProvider: ...
```

## 15. PROPOSAL: Unified Authentication Router

**Status:** PROPOSAL - Not yet approved for implementation

### Rationale

The current endpoint design uses `/v2/auth/` prefix. However, aligning with V2 Routers SPEC (`_V2_SPEC_ROUTERS.md`) patterns suggests a more extensible structure that could support multiple authentication targets (SharePoint, Azure OpenAI, future Graph API).

### Proposed Endpoint Structure

```
/v2/authentication/
├─> sharepoint_online/
│   ├─> status              # GET - current SharePoint Online auth state
│   ├─> login               # GET - initiate OAuth redirect (Phase 2)
│   ├─> callback            # GET - OAuth callback (Phase 2)
│   ├─> override            # POST/DELETE - set/clear method override
│   └─> device_code/
│       ├─> initiate        # POST - start device code flow (Phase 3)
│       └─> status          # GET - poll for completion (Phase 3)
│
└─> azure_openai/           # Future: Azure OpenAI auth management
    └─> status              # GET - current Azure OpenAI auth state
```

### Mapping: Current vs Proposed

- `GET /v2/auth/status` -> `GET /v2/authentication/sharepoint_online/status`
- `GET /v2/auth/login` -> `GET /v2/authentication/sharepoint_online/login`
- `GET /v2/auth/callback` -> `GET /v2/authentication/sharepoint_online/callback`
- `POST /v2/auth/override` -> `POST /v2/authentication/sharepoint_online/override`
- `DELETE /v2/auth/override` -> `DELETE /v2/authentication/sharepoint_online/override`
- `POST /v2/auth/device-code/initiate` -> `POST /v2/authentication/sharepoint_online/device_code/initiate`
- `GET /v2/auth/device-code/status` -> `GET /v2/authentication/sharepoint_online/device_code/status`

### Benefits

- Follows V2 Routers nested resource pattern: `/v2/[RESOURCE]/[RESOURCE]/[ACTION]`
- Single router handles all authentication concerns
- Extensible for future services (Azure OpenAI, Graph API)
- Consistent with existing V2 endpoint naming (full words, not abbreviations)

### Decision Required

Before Phase 2 implementation, decide:
1. **Keep `/v2/auth/`** - shorter, SharePoint-only scope
2. **Use `/v2/authentication/sharepoint_online/`** - extensible, follows V2 patterns

## 16. Document History

**[2026-03-15 19:53]**
- Fixed: MSAL acronym expanded on first use (line 93 diagram, before line 317)
- Fixed: OBO acronym expanded on first use (line 18 header, before line 65)

**[2026-03-15 19:46]**
- Fixed: Override file examples showed `interactive_browser` but User Auth methods are NOT valid override values
- Fixed: SPAUTH-FR-13 example corrected to use System Auth method (`certificate`)
- Fixed: Auth Status Response (Phase 2+) corrected to show `device_code` override, not `interactive_browser`
- Fixed: Phase 2 Action Flow - removed "write override file" step (Interactive Browser uses session, not override)
- Fixed: SPAUTH-DD-22 aligned with SPAUTH-IG-41 - `msal-extensions` is NOT transitive via azure-identity
- Fixed: SPAUTH-DD-44 - removed `interactive_browser` from override options (User Auth, not valid)
- Changed: Phase 2 bullet clarified as "Override file read/write support (System Auth methods only)"
- Added: Clarification notes distinguishing User Auth (per-session) from System Auth (override file)

**[2026-03-15 18:15]**
- Fixed: `CRAWLER_MANAGED_IDENTITY_OBJECT_ID` must contain Object ID, not Client ID [VERIFIED via Microsoft Q&A]
- Rationale: `Grant-PnPAzureADAppSitePermission -AppId` requires Object ID for Managed Identity

**[2026-03-15 17:52]**
- Changed: `SHAREPOINT_AUTH_METHOD` (string enum) replaced with `CRAWLER_USE_MANAGED_IDENTITY` (boolean)
- Changed: Matches OpenAI pattern (`AZURE_OPENAI_USE_MANAGED_IDENTITY`)
- Changed: `AZURE_CLIENT_ID` replaced with `CRAWLER_MANAGED_IDENTITY_OBJECT_ID` for user-assigned MI
- Changed: `CRAWLER_TENANT_NAME` replaced with existing `CRAWLER_SHAREPOINT_TENANT_NAME`
- Updated: SPAUTH-FR-04, SPAUTH-IG-02, SPAUTH-IG-03, SPAUTH-IG-04, SPAUTH-DD-44
- Updated: Override File Resolution diagram, Auth Error Response, New Environment Variables section

**[2026-03-14 23:30]**
- Changed: Device Code moved from User Auth to System Auth (Tier 1)
- Changed: Override file now accepts 3 values: certificate, managed_identity, device_code
- Changed: Resolution order updated - Device Code resolved via override/default, not per-session
- Rationale: Device Code is emergency fallback - admin authenticates once, ALL workers use cached token

**[2026-03-14 23:13]**
- Added: Two-Tier Auth Model (System Auth vs User Auth) - separates app-only from delegated methods
- Changed: AuthProvider.get_context() - added optional `request` parameter for User Auth methods
- Changed: AuthenticationFactory resolution order - User Auth (per-session) takes precedence over System Auth
- Changed: Override File - now only accepts System Auth methods (`certificate`, `managed_identity`)
- Added: Token Refresh Mechanism section in Phase 2 - explicit refresh logic via `token_func`
- Changed: SPAUTH-DD-11 - added note about server-side sessions for large tokens
- Fixed: Function Signatures - AuthProvider interface now matches Domain Objects section
- Fixed: Table of Contents - added PROPOSAL section, renumbered Document History

**[2026-03-14 22:36]**
- Fixed: Line 26 - clarified `with_access_token` is for non-certificate methods only
- Fixed: Line 123 - "Azure AD" updated to "Microsoft Entra ID"
- Fixed: Lines 299, 351 - delegated flows use explicit scopes (`Sites.Read.All`), not `.default`
- Fixed: Line 367 - corrected msal-extensions platform persistence classes

**[2026-03-14 22:32]**
- Fixed: SPAUTH-DD-04 - Added CRAWLER_TENANT_NAME fallback for vanity domains
- Fixed: SPAUTH-IG-04 - Clarified no DefaultAzureCredential fallback for local dev
- Verified: Cross-checked against SPAUTH-IN10, IN11, AM01, AM03

**[2026-03-14 22:06]**
- Fixed: Acronym expansion - MI, MSAL, PKCE expanded on first use (per SPAUTH-FL-002)
- Fixed: AuthProvider.validate() signature consistency (added site_url parameter)
- Added: SPAUTH-IG-13 - Session token expiration handling for Phase 2

**[2026-03-14 22:01]**
- Initial specification created
- Four implementation phases defined with FR, DD, IG per phase
- Cross-phase design decisions and guarantees documented
- Based on research from SPAUTH-IN10, SPAUTH-IN11, SPAUTH-AM01/03/04/05/08
- Incorporates review findings: SPAUTH-RV-001 (token audience), SPAUTH-RV-004 (ClientContext resolved), SPAUTH-RV-006 (OBO deferred to Phase 4)
