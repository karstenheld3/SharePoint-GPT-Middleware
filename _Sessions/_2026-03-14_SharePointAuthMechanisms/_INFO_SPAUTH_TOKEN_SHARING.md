# INFO: Token Sharing Across Workers

**Doc ID**: SPAUTH-IN11
**Goal**: Research how each authentication mechanism can share credentials/tokens across all workers
**Timeline**: Created 2026-03-14

**Depends on:**
- `_INFO_SPAUTH_REQUIREMENTS.md [SPAUTH-IN10]` for authentication method list

## Summary

- **Managed Identity**: No sharing needed - Azure IMDS handles caching at infrastructure level [VERIFIED]
- **Certificate**: Each worker loads cert independently; duplicate Azure AD calls acceptable (fast, no refresh token) [VERIFIED]
- **Device Code**: HIGH complexity - requires shared file cache with locking; all workers must access same tokens [VERIFIED]
- **Interactive Browser**: Per-session token via OAuth redirect; no cross-worker sharing needed [VERIFIED]
- **On-Behalf-Of**: Per-request with user token; in-memory cache per worker is sufficient [VERIFIED]
- **Recommendation**: File-based `SharedTokenCache` with locking for Device Code only; Interactive Browser uses standard session management [VERIFIED]

## Key Questions

**Per-Method Questions:** (Details in [Sections 2-6](#2-managed-identity))

1. **What needs to be shared?**
   → Varies: Nothing (Managed Identity), cert path (Certificate), tokens (Device Code, Interactive Browser, On-Behalf-Of)
2. **How can it be shared?**
   → IMDS (Managed Identity), filesystem (Certificate), file cache with locking (delegated flows)
3. **Thread-safety considerations?**
   → SDK handles (Managed Identity, Certificate), file locking needed (Device Code)
4. **Token expiration/refresh?**
   → Automatic (Managed Identity, Certificate), MSAL handles if cache shared (delegated)

**Architecture Questions:** (Details in [Section 9](#9-mechanism-switching-questions))

5. **Endpoint design changes needed?**
   → **NO** - `AuthenticationFactory` abstracts mechanism
6. **How to switch all workers?**
   → Create override file read on each request, no restart
7. **How to switch back to default?**
   → Delete override file (sharepoint_auth_override.json)

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Managed Identity](#2-managed-identity)
3. [Certificate](#3-certificate)
4. [Device Code](#4-device-code)
5. [Interactive Browser](#5-interactive-browser)
6. [On-Behalf-Of](#6-on-behalf-of)
7. [Comparison Matrix](#7-comparison-matrix)
8. [Recommended Architecture](#8-recommended-architecture)
9. [Mechanism Switching Questions](#9-mechanism-switching-questions)
10. [Sources](#sources)
11. [Next Steps](#next-steps)
12. [Document History](#document-history)

## 1. Problem Statement

### Architecture Context

```
┌─────────────────────────────────────────────────────────────────┐
│ Azure App Service (Multi-Worker)                                │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ Worker 1 │  │ Worker 2 │  │ Worker 3 │  │ Worker N │         │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘         │
│       │             │             │             │               │
│       └─────────────┴──────┬──────┴─────────────┘               │
│                            │                                    │
│                            ▼                                    │
│                  ┌─────────────────────┐                        │
│                  │ Shared Auth State?  │                        │
│                  │ How to share tokens │                        │
│                  │ across all workers? │                        │
│                  └─────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

## 2. Managed Identity

### What Needs to Be Shared

**Nothing explicit** - Azure handles token caching at the IMDS level.

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│ Managed Identity Token Flow                                     │
│                                                                 │
│  Worker 1 ──┐                                                   │
│  Worker 2 ──┼──> IMDS Endpoint ──> Azure AD ──> Token           │
│  Worker N ──┘    (169.254.169.254)                              │
│                                                                 │
│  IMDS handles:                                                  │
│  - Token caching internally                                     │
│  - Automatic refresh before expiry                              │
│  - Thread-safe concurrent requests                              │
└─────────────────────────────────────────────────────────────────┘
```

### Sharing Strategy

- **Credentials**: No credentials to share (IMDS is automatic)
- **Tokens**: Azure Identity SDK caches in-memory per process
- **Cross-worker**: Each worker makes independent IMDS calls; IMDS caches at infrastructure level

### Implementation

```python
from azure.identity import ManagedIdentityCredential

# Each worker creates its own credential instance
# Azure Identity SDK handles caching internally
credential = ManagedIdentityCredential()

# First call: IMDS request
token1 = credential.get_token("https://graph.microsoft.com/.default")

# Second call (same worker, within lifetime): cached
token2 = credential.get_token("https://graph.microsoft.com/.default")
```

### Verdict

- **Sharing complexity**: NONE - Azure handles everything
- **Thread-safe**: Yes (SDK handles)
- **Refresh handling**: Automatic (SDK refreshes 5 min before expiry)

## 3. Certificate

### What Needs to Be Shared

**Certificate file path and password** - each worker loads cert and gets its own token.

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│ Certificate Token Flow                                          │
│                                                                 │
│  Shared: cert.pfx (on disk)                                     │
│                                                                 │
│  Worker 1 ──> Load cert ──> MSAL ──> Token (cached in-process)  │
│  Worker 2 ──> Load cert ──> MSAL ──> Token (cached in-process)  │
│  Worker N ──> Load cert ──> MSAL ──> Token (cached in-process)  │
│                                                                 │
│  Each worker has independent token cache                        │
│  Duplicate Azure AD calls on first request per worker           │
└─────────────────────────────────────────────────────────────────┘
```

### Sharing Strategy

**Option A: Independent Token Caches (Current)**
- Each worker loads cert, gets own token
- Simple but results in N Azure AD calls for N workers
- Acceptable for small worker counts

**Option B: Shared File Token Cache**
- All workers share token cache file
- Risk: File locking issues, race conditions
- MSAL does not guarantee thread-safe file writes

**Option C: Singleton TokenManager**
- Single process holds token, workers request via IPC
- More complex but avoids duplicate calls

### Current Implementation Analysis

```python
# Current: Each worker loads cert independently
def connect_to_site_using_client_id_and_certificate(...):
    pem_file, thumbprint = get_or_create_pem_from_pfx(cert_path, cert_password)
    ctx = ClientContext(site_url).with_client_certificate(...)
    return ctx
```

### Recommendation

**Option A is acceptable** for certificate auth because:
- Client credentials flow has no refresh token
- App can always get new token with credentials
- Azure AD handles concurrent requests well
- Token acquisition is fast (~100-500ms)

### Verdict

- **Sharing complexity**: LOW - share cert file path, each worker gets own token
- **Thread-safe**: Yes (each worker independent)
- **Refresh handling**: Automatic (MSAL handles, no refresh token needed)

## 4. Device Code

### What Needs to Be Shared

**Access token AND refresh token** - user authenticates ONCE, all workers must use that token.

### The Challenge

```
┌─────────────────────────────────────────────────────────────────┐
│ Device Code Flow Challenge                                      │
│                                                                 │
│  Admin User ──> Device Code ──> Browser Auth ──> Token          │
│                                      │                          │
│                                      ▼                          │
│                          ┌─────────────────────┐                │
│                          │ Token acquired by   │                │
│                          │ ONE worker process  │                │
│                          └─────────────────────┘                │
│                                      │                          │
│       ┌──────────────────────────────┼───────────────────┐      │
│       ▼                              ▼                   ▼      │
│  ┌──────────┐                  ┌──────────┐       ┌──────────┐  │
│  │ Worker 1 │ Need the token!  │ Worker 2 │       │ Worker N │  │
│  └──────────┘                  └──────────┘       └──────────┘  │
│                                                                 │
│  HOW DO OTHER WORKERS GET THE TOKEN?                            │
└─────────────────────────────────────────────────────────────────┘
```

### Sharing Strategy

**Required: Persistent Shared Token Cache**

```
┌─────────────────────────────────────────────────────────────────┐
│ Device Code with Shared Cache                                   │
│                                                                 │
│  Admin ──> Device Code ──> Token ──> Shared Cache (File/DB)     │
│                                              │                  │
│       ┌──────────────────────────────────────┼──────────────┐   │
│       ▼                                      ▼              ▼   │
│  Worker 1 ──> Read Cache ──> Token      Worker 2       Worker N │
│                                                                 │
│  All workers read from same cache                               │
│  One worker handles refresh when needed                         │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation Options

**Option A: Shared File Cache**

```python
from msal import PublicClientApplication, SerializableTokenCache
import os
import fcntl  # For file locking (Unix) or msvcrt (Windows)

class SharedDeviceCodeAuth:
    CACHE_FILE = None  # Set at runtime: {PERSISTENT_STORAGE_PATH}/device_code_cache.json
    
    def __init__(self, client_id: str, tenant_id: str):
        self.cache = SerializableTokenCache()
        self.client_id = client_id
        self.tenant_id = tenant_id
        self._load_cache()
    
    def _load_cache(self):
        if os.path.exists(self.CACHE_FILE):
            with open(self.CACHE_FILE, 'r') as f:
                self.cache.deserialize(f.read())
    
    def _save_cache(self):
        # File locking for thread safety
        with open(self.CACHE_FILE, 'w') as f:
            # Platform-specific locking needed
            f.write(self.cache.serialize())
    
    def get_token(self, scopes: list) -> str:
        app = PublicClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            token_cache=self.cache
        )
        
        # Try silent first (from cache)
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(scopes, account=accounts[0])
            if result and "access_token" in result:
                self._save_cache()
                return result["access_token"]
        
        raise Exception("No cached token - admin must authenticate via Device Code")
```

**Option B: In-Memory Singleton with FastAPI Lifespan**

```python
# app_state.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class AuthState:
    device_code_cache: Optional[SerializableTokenCache] = None
    selected_auth_method: str = "managed_identity"

# Global state shared across requests (single worker)
auth_state = AuthState()

# Problem: Only works within single worker process!
# Multiple workers = multiple auth_state instances
```

**Option C: Redis/Database Token Store**

```python
import redis
import json

class RedisTokenCache:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.cache = SerializableTokenCache()
    
    def load(self):
        data = self.redis.get("device_code_cache")
        if data:
            self.cache.deserialize(data.decode())
    
    def save(self):
        if self.cache.has_state_changed:
            self.redis.set("device_code_cache", self.cache.serialize())
    
    def get_cache(self) -> SerializableTokenCache:
        return self.cache
```

### Refresh Token Handling

Device Code flow provides refresh tokens:
- Access token: 60-90 minutes
- Refresh token: 90 days (sliding)

MSAL handles refresh automatically when using `acquire_token_silent()`:
1. Check cache for valid access token
2. If expired but refresh token exists: refresh silently
3. If refresh token expired: raise error (admin must re-authenticate)

### Verdict

- **Sharing complexity**: HIGH - must implement shared cache
- **Thread-safe**: Requires locking mechanism
- **Refresh handling**: MSAL handles if cache is properly shared
- **Recommendation**: File cache with locking, or Redis for multi-instance

## 5. Interactive Browser

### Middleware Architecture Clarification

The middleware serves its own UI (`html_javascript_static_files/`). Users access this UI via browser. This means Interactive Browser auth is a **standard OAuth redirect flow** - NOT "server opens browser on itself."

```
User Browser ──> Middleware UI ──> "Login with Microsoft" button
                                          │
                                          v
                              [Redirect to login.microsoftonline.com]
                                          │
                                          v
                              [User authenticates in SAME browser]
                                          │
                                          v
                              [Redirect back with auth code]
                                          │
                                          v
                              [Middleware exchanges code for token]
```

### What Needs to Be Shared

**Nothing across workers.** Each user session has its own token stored in session/cookie.

### How It Differs from Device Code

| Aspect | Interactive Browser | Device Code |
|--------|---------------------|-------------|
| Flow | OAuth redirect in user's browser | Display code, user authenticates elsewhere |
| Token scope | Per-user session | Shared admin token for all requests |
| Cross-worker sharing | Not needed (session-based) | Required (all workers use same token) |
| Production viable | Yes - standard web app OAuth | Yes - but more complex |
| Use case | Any user accessing middleware UI | CLI tools, scripts, headless automation |

### Sharing Strategy

No cross-worker sharing needed:
- Token stored in user's session (cookie/session store)
- Each request from that user carries session identifier
- Standard web session management

### Verdict

- **Sharing complexity**: LOW (standard session management)
- **Production use**: YES - works like any web app with OAuth login
- **Recommendation**: Preferred delegated method for middleware UI users

## 6. On-Behalf-Of

### What Needs to Be Shared

**User's delegated token** - comes from frontend, must be available to all workers.

### The Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ On-Behalf-Of Flow                                               │
│                                                                 │
│  SPA Frontend ──> User Login ──> User Token                     │
│                                      │                          │
│       ┌──────────────────────────────┼──────────────────────┐   │
│       ▼                              ▼                      ▼   │
│  Request to   ──> Worker receives user token in header          │
│  Middleware       (Authorization: Bearer <user_token>)          │
│                                      │                          │
│                                      ▼                          │
│                          ┌─────────────────────┐                │
│                          │ Exchange for SP     │                │
│                          │ token (OBO)         │                │
│                          └─────────────────────┘                │
│                                      │                          │
│       ┌──────────────────────────────┼──────────────────────┐   │
│       ▼                              ▼                      ▼   │
│  Cache OBO   ──> Key: hash(user_token) ──> Value: SP token      │
│  result          Shared across workers                          │
└─────────────────────────────────────────────────────────────────┘
```

### Key Insight

OBO is **per-request** with user's token in header:
- Each request carries user's access token
- Worker exchanges it for SharePoint token
- Can cache the exchange result (keyed by user token hash)

### Caching Strategy

```python
from msal import ConfidentialClientApplication
import hashlib

class OBOTokenManager:
    """On-Behalf-Of token manager with caching."""
    
    def __init__(self, client_id: str, tenant_id: str, client_secret: str):
        self.app = ConfidentialClientApplication(
            client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            client_credential=client_secret
        )
        # Cache: user_token_hash -> (sp_token, expiry)
        self._cache = {}
    
    def get_sp_token(self, user_token: str, scopes: list) -> str:
        """Exchange user token for SharePoint token."""
        
        # Check cache first
        token_hash = hashlib.sha256(user_token.encode()).hexdigest()[:16]
        if token_hash in self._cache:
            sp_token, expiry = self._cache[token_hash]
            if time.time() < expiry - 300:  # 5 min buffer
                return sp_token
        
        # Exchange via OBO
        result = self.app.acquire_token_on_behalf_of(
            user_assertion=user_token,
            scopes=scopes
        )
        
        if "access_token" in result:
            expiry = time.time() + result.get("expires_in", 3600)
            self._cache[token_hash] = (result["access_token"], expiry)
            return result["access_token"]
        
        raise Exception(f"OBO failed: {result.get('error_description')}")
```

### Cross-Worker Sharing

For OBO, sharing is less critical because:
- User token comes fresh with each request
- OBO exchange is fast (~100-500ms)
- Caching is optimization, not requirement

For high-traffic scenarios:
- Use Redis to cache OBO results
- Key: hash of user token
- Value: SharePoint token + expiry

### Verdict

- **Sharing complexity**: MEDIUM - cache is optional optimization
- **Thread-safe**: Each request has its own user token
- **Refresh handling**: User token refresh is frontend's responsibility
- **Recommendation**: In-memory cache per worker is sufficient for most cases

## 7. Comparison Matrix

**Sharing Requirements by Method:**

- **Managed Identity**
  - Shared state: None
  - Sharing mechanism: N/A (Azure handles)
  - Complexity: None

- **Certificate**
  - Shared state: Cert file path
  - Sharing mechanism: Filesystem
  - Complexity: Low

- **Device Code**
  - Shared state: Access + Refresh tokens
  - Sharing mechanism: File cache with locking OR Redis
  - Complexity: High

- **Interactive Browser**
  - Shared state: Access + Refresh tokens
  - Sharing mechanism: In-memory (local dev) OR same as Device Code
  - Complexity: Low (local) / High (production)

- **On-Behalf-Of**
  - Shared state: OBO exchange results (optional)
  - Sharing mechanism: In-memory cache per worker OR Redis
  - Complexity: Medium

## 8. Recommended Architecture

### For This Application

Based on the requirements (admin-selected, all workers use same method):

```
┌─────────────────────────────────────────────────────────────────┐
│ Recommended Token Sharing Architecture                          │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ AuthenticationFactory (Singleton per worker)                ││
│  │                                                             ││
│  │  selected_method: str  ──> From config/env                  ││
│  │                                                             ││
│  │  Methods:                                                   ││
│  │  ├─> ManagedIdentity: Azure handles sharing                 ││
│  │  ├─> Certificate: Load from shared path                     ││
│  │  ├─> DeviceCode: SharedTokenCache (file-based)              ││
│  │  ├─> InteractiveBrowser: Same as DeviceCode                 ││
│  │  └─> OnBehalfOf: Per-request with optional cache            ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  SharedTokenCache (for delegated flows):                        │
│  ├─> File: {PERSISTENT_STORAGE_PATH}/device_code_cache.json      │
│  ├─> Locking: File locks for concurrent access                  │
│  └─> Format: MSAL SerializableTokenCache JSON                   │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation Priorities

1. **Managed Identity** - No sharing code needed
2. **Certificate** - Current impl works (each worker loads cert)
3. **Device Code** - Implement SharedTokenCache with file locking
4. **Interactive Browser** - Reuse DeviceCode cache infrastructure
5. **On-Behalf-Of** - Per-worker cache is sufficient initially

## 9. Mechanism Switching Questions

### Q1: Do we need to change endpoint design to support multiple auth mechanisms?

**Answer: NO** - Endpoints remain unchanged.

The authentication mechanism is abstracted behind an `AuthenticationFactory` that returns a `ClientContext` or access token. Endpoints call the factory without knowing which mechanism is active.

```
┌─────────────────────────────────────────────────────────────────┐
│ Endpoint Design (No Change Required)                            │
│                                                                 │
│  @app.get("/v2/sites/{site_id}/files")                          │
│  async def get_files(site_id: str):                             │
│      # Endpoint doesn't know which auth method is used          │
│      ctx = auth_factory.get_client_context(site_url)            │
│      files = ctx.web.lists.get().execute_query()                │
│      return files                                               │
│                                                                 │
│  AuthenticationFactory handles:                                 │
│  - Reading selected_method from config/state                    │
│  - Instantiating correct credential                             │
│  - Returning authenticated ClientContext                        │
└─────────────────────────────────────────────────────────────────┘
```

**What changes:**
- Add `AuthenticationFactory` class
- Add `get_client_context()` calls instead of direct `connect_to_site_using_client_id_and_certificate()`
- Add UI endpoint for admin to select/switch mechanism
- Add UI endpoint for Device Code initiation

### Q2: How exactly could all workers be switched from one mechanism to another?

**Answer: Override file read on each request.**

**Semantic:**
- File does NOT exist → use default mechanism (from env var / `.env` file)
- File exists → use method specified in file (override)

```
┌─────────────────────────────────────────────────────────────────┐
│ Mechanism Switching Flow                                        │
│                                                                 │
│  1. Admin clicks "Switch to Device Code" in UI                  │
│                         │                                       │
│                         ▼                                       │
│  2. Admin completes Device Code authentication                  │
│                         │                                       │
│                         ▼                                       │
│  3. Middleware TESTS auth against SharePoint → success           │
│                         │                                       │
│                         ▼                                       │
│  4. Override file written AFTER successful test:                │
│     {PERSISTENT_STORAGE_PATH}/sharepoint_auth_override.json       │
│     { "method": "device_code" }                                 │
│                         │                                       │
│                         ▼                                       │
│  5. All workers read override file on next request              │
│     AuthenticationFactory._get_selected_method()                │
│                         │                                       │
│                         ▼                                       │
│  6. Workers use new mechanism immediately                       │
│     No restart required                                         │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation:**

```python
import json
import os

class AuthenticationFactory:
    # Use system_info.PERSISTENT_STORAGE_PATH from app.py
    # Azure: /home/data, Local: LOCAL_PERSISTENT_STORAGE_PATH env var
    OVERRIDE_FILE = None  # Set at runtime from system_info.PERSISTENT_STORAGE_PATH
    DEFAULT_METHOD = None  # Set at runtime from env var / .env file
    
    def _get_selected_method(self) -> str:
        """Read method from override file, or use default from env config."""
        if not self.OVERRIDE_FILE:
            raise RuntimeError("PERSISTENT_STORAGE_PATH not configured")
        if os.path.exists(self.OVERRIDE_FILE):
            try:
                with open(self.OVERRIDE_FILE, 'r') as f:
                    override = json.load(f)
                    return override.get("method", self.DEFAULT_METHOD)
            except (json.JSONDecodeError, IOError):
                pass
        return self.DEFAULT_METHOD  # File doesn't exist = default
    
    @staticmethod
    def set_override(method: str):
        """Create override file AFTER successful auth test."""
        # Caller must verify auth works before calling this
        with open(AuthenticationFactory.OVERRIDE_FILE, 'w') as f:
            json.dump({"method": method}, f)
    
    @staticmethod
    def clear_override():
        """Delete override file to return to default."""
        if os.path.exists(AuthenticationFactory.OVERRIDE_FILE):
            os.remove(AuthenticationFactory.OVERRIDE_FILE)
```

**Why file-based state works:**
- All workers share same filesystem (Azure App Service)
- File reads are fast (~1ms)
- No external dependencies (Redis, database)
- Atomic writes with proper locking

**Alternative: Environment variable + restart**
- Set `AUTH_METHOD=device_code` in Azure App Settings
- Requires app restart to take effect
- More disruptive but simpler

### Q3: How can the app be switched back to the default mechanism?

**Answer: Delete the override file.**

```
┌─────────────────────────────────────────────────────────────────┐
│ Switching Back to Default                                       │
│                                                                 │
│  Option A: Delete override file (RECOMMENDED)                   │
│  ├─> rm {PERSISTENT_STORAGE_PATH}/sharepoint_auth_override.json   │
│  └─> Factory uses DEFAULT_METHOD (Managed Identity)             │
│                                                                 │
│  Option B: Automatic prompt on error                            │
│  ├─> If Device Code token expires and no re-auth                │
│  ├─> AuthFactory detects error                                  │
│  └─> UI prompts: "Token expired. Reset to default?"             │
└─────────────────────────────────────────────────────────────────┘
```

**UI Flow for Reset:**

```python
@router.post("/v2/auth/reset-to-default")
async def reset_to_default():
    """Reset authentication to default (delete override file)."""
    AuthenticationFactory.clear_override()
    
    # Optionally clear delegated token caches
    if os.path.exists(SharedTokenCache.CACHE_FILE):
        os.remove(SharedTokenCache.CACHE_FILE)
    
    return {"status": "ok", "method": "managed_identity"}
```

**Automatic fallback considerations:**
- Should NOT auto-fallback (per requirements: admin-selected, no surprise changes)
- Instead: Detect failure, notify admin via UI, let admin decide
- Log clear error: "Device Code token expired. Admin action required."

## Sources

**Primary Sources:**
- `SPAUTH-IN06`: Operational Patterns (token caching, MSAL cache behavior) [VERIFIED]
- `SPAUTH-AM03`: Managed Identity documentation (IMDS behavior) [VERIFIED]
- `SPAUTH-AM05`: Device Code documentation (token flow) [VERIFIED]

**Key Findings from Sources:**
- MSAL `SerializableTokenCache` supports file persistence [VERIFIED]
- MSAL checks cache before network request [VERIFIED]
- Client credentials flow has no refresh token (app can always get new token) [VERIFIED]
- Persistent cache on shared filesystems may have race conditions [VERIFIED]

## Next Steps

1. **Implement SharedTokenCache class** using `msal-extensions` package for proper file locking
2. **Add AuthState model** to track selected auth method
3. **Create AuthenticationFactory** that uses appropriate method
4. **Add UI endpoints** for Device Code initiation and auth method selection
5. **Add health check endpoint** to validate current token status and notify admin of expiration
6. **Add method validation** to reject invalid method values in override file

## Document History

**[2026-03-14 21:56]**
- Changed: Interactive Browser section rewritten - standard OAuth redirect, no cross-worker sharing needed
- Added: Middleware architecture clarification diagram
- Added: Comparison table (Interactive Browser vs Device Code)
- Changed: Recommendation updated - SharedTokenCache for Device Code only

**[2026-03-14 20:40]**
- Fixed: Stale `/var/app/` paths replaced with `{PERSISTENT_STORAGE_PATH}`
- Changed: DEFAULT_METHOD from hardcoded to env var / `.env` file
- Changed: Override file written AFTER successful auth test (Q2 flow updated)
- Added: PERSISTENT_STORAGE_PATH guard in AuthenticationFactory code
- Changed: Default mechanism semantic from "Managed Identity" to "from env config"

**[2026-03-14 20:18]**
- Fixed: Path changed to use PERSISTENT_STORAGE_PATH (SPAUTH-RV-002)
- Added: msal-extensions requirement to Next Steps (SPAUTH-RV-001)
- Added: Health check and validation requirements to Next Steps

**[2026-03-14 20:13]**
- Changed: Renamed auth_state.json to sharepoint_auth_override.json
- Changed: Semantic clarified - file exists = override, file absent = default

**[2026-03-14 20:06]**
- Fixed: Acronyms written out in full (SPAUTH-FL-002)

**[2026-03-14 20:02]**
- Added Section 9: Mechanism Switching Questions (Q1-Q3)
- Documented file-based state switching approach
- Confirmed endpoints do not need redesign

**[2026-03-14 19:58]**
- Initial research document created
- Analyzed sharing requirements for all 5 auth methods
- Recommended file-based shared cache for delegated flows
