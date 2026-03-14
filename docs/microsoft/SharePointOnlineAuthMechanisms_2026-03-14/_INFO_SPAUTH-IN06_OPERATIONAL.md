<DevSystem MarkdownTablesAllowed=true />

# INFO: Operational Patterns

**Doc ID**: SPAUTH-IN06
**Goal**: Document token caching, lifetime, refresh, and debugging patterns
**Version Scope**: Microsoft Entra ID (2026), MSAL Python 1.x, Azure Identity 1.x

**Depends on:**
- `__AUTH_MECHANISMS_SOURCES.md [SPAUTH-SOURCES]` for source references

## Summary

Operational aspects of authentication include token caching for performance, understanding token lifetimes, implementing proper refresh logic, and debugging authentication issues. MSAL provides built-in token caching that checks the cache before making network requests and handles refresh automatically. Access tokens typically have 60-90 minute lifetimes while refresh tokens can last up to 90 days with sliding expiration. MSAL refreshes tokens proactively 5 minutes before expiration. For production applications, persistent token caching reduces authentication latency and network calls. Error handling should implement exponential backoff for transient failures and handle specific error codes appropriately. Debugging tools include token inspection, logging, and the Azure portal's sign-in logs.

## Key Facts

- **Access Token Lifetime**: 60-90 minutes default for Microsoft Graph [VERIFIED] (SPAUTH-SC-MSFT-TOKENLIFE)
- **Refresh Token Lifetime**: Up to 90 days with sliding expiration [VERIFIED] (SPAUTH-SC-MSFT-REFRESH)
- **Proactive Refresh**: MSAL refreshes 5 minutes before expiration [VERIFIED] (SPAUTH-SC-MSFT-MSALPYTHON)
- **Cache-First**: MSAL checks cache before network request [VERIFIED] (SPAUTH-SC-GH-MSALCACHE)
- **No Refresh Token for Client Credentials**: App can always get new token with credentials [VERIFIED] (SPAUTH-SC-MSFT-CLIENTCREDS)

## Quick Reference

**Token Lifetimes (Defaults):**
```
Access Token:  60-90 minutes
ID Token:      60 minutes
Refresh Token: 90 days (sliding, 24hr inactivity max)
```

**MSAL Cache Behavior:**
```
acquire_token_*()
  -> Check cache for valid token
    -> Found: Return cached token
    -> Expired but refresh token exists: Refresh silently
    -> No cache: Make network request
```

## 1. Token Caching Strategies

### In-Memory Cache (Default)

MSAL uses in-memory cache by default. Tokens are lost when the process exits.

```python
from msal import ConfidentialClientApplication

# Default in-memory cache
app = ConfidentialClientApplication(
    client_id="YOUR_CLIENT_ID",
    authority="https://login.microsoftonline.com/YOUR_TENANT_ID",
    client_credential="YOUR_SECRET"
)

# First call: network request
result1 = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

# Second call (within lifetime): returns cached token
result2 = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
```

### Persistent Cache

For long-running services or multi-instance deployments.

**Security warning:** File-based caches store tokens in plain text. For production, use OS-level secure storage (DPAPI on Windows, Keychain on macOS) or the `keyring` library.

```python
from msal import ConfidentialClientApplication, SerializableTokenCache
import os
import json

class FileTokenCache:
    """Persistent token cache backed by file."""
    
    def __init__(self, cache_file: str):
        self.cache_file = cache_file
        self.cache = SerializableTokenCache()
        self._load()
    
    def _load(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    self.cache.deserialize(f.read())
            except (json.JSONDecodeError, IOError):
                pass  # Start fresh if corrupted
    
    def save(self):
        if self.cache.has_state_changed:
            with open(self.cache_file, 'w') as f:
                f.write(self.cache.serialize())
    
    def get_cache(self) -> SerializableTokenCache:
        return self.cache

# Usage
token_cache = FileTokenCache("/var/app/tokens.json")

app = ConfidentialClientApplication(
    client_id="YOUR_CLIENT_ID",
    authority="https://login.microsoftonline.com/YOUR_TENANT_ID",
    client_credential="YOUR_SECRET",
    token_cache=token_cache.get_cache()
)

result = app.acquire_token_for_client(scopes=["..."])
token_cache.save()  # Persist after acquisition
```

### Azure Identity Cache

Azure Identity handles caching internally:

```python
from azure.identity import CertificateCredential, TokenCachePersistenceOptions

# Enable persistent cache
credential = CertificateCredential(
    tenant_id="YOUR_TENANT_ID",
    client_id="YOUR_CLIENT_ID",
    certificate_path="cert.pem",
    cache_persistence_options=TokenCachePersistenceOptions(
        name="my_app_cache",
        enable_persistence=True
    )
)
```

[VERIFIED] (SPAUTH-SC-MSFT-MSALCACHE | SPAUTH-SC-DEV-MSALCACHE)

## 2. Token Lifetime Configuration

### Default Lifetimes

| Token Type    | Default Lifetime | Configurable         |
|---------------|------------------|----------------------|
| Access Token  | 60-90 minutes    | Yes (10 min - 1 day) |
| ID Token      | 60 minutes       | No                   |
| Refresh Token | 90 days          | No (as of Jan 2021)  |
| Session Token | Varies           | No                   |

### Configuring Access Token Lifetime

```powershell
# PowerShell: Create token lifetime policy
$policy = @{
    displayName = "CustomAccessTokenPolicy"
    definition = @(
        @{
            TokenLifetimePolicy = @{
                AccessTokenLifetime = "02:00:00"  # 2 hours
            }
        } | ConvertTo-Json
    )
    isOrganizationDefault = $false
}

New-MgPolicyTokenLifetimePolicy -BodyParameter $policy
```

### Refresh Token Behavior

- **Sliding expiration**: 90 days from last use
- **Inactivity timeout**: 24 hours of inactivity = revoked
- **Single-use rotation**: Some scenarios rotate refresh token on each use
- **No refresh token for client credentials**: App credentials are sufficient

[VERIFIED] (SPAUTH-SC-MSFT-TOKENLIFE | SPAUTH-SC-MSFT-REFRESH)

## 3. Proactive Token Refresh

### MSAL Refresh Behavior

MSAL refreshes tokens before they expire to avoid disruption:

```python
# MSAL internal logic (simplified)
def should_refresh(token_entry):
    expires_on = token_entry["expires_on"]
    refresh_on = token_entry.get("refresh_on", expires_on - 300)  # 5 min buffer
    return time.time() >= refresh_on
```

### Manual Refresh Check

```python
from datetime import datetime, timedelta

def is_token_expiring_soon(token_result: dict, buffer_minutes: int = 5) -> bool:
    """Check if token expires within buffer period."""
    expires_in = token_result.get("expires_in", 0)
    # Token was issued now, so expires_in seconds from now
    expires_at = datetime.now() + timedelta(seconds=expires_in)
    buffer = timedelta(minutes=buffer_minutes)
    return datetime.now() + buffer >= expires_at
```

### Force Refresh

```python
from msal import ConfidentialClientApplication

app = ConfidentialClientApplication(...)

# Force new token acquisition (bypass cache)
result = app.acquire_token_for_client(
    scopes=["https://graph.microsoft.com/.default"],
    force_refresh=True  # Skip cache, get fresh token
)
```

## 4. Error Handling and Retry

### Transient vs Permanent Errors

**Transient (retry):**
- Network timeouts
- 5xx server errors
- `AADSTS50196`: Loop detected (service overloaded)

**Permanent (don't retry):**
- `AADSTS700016`: App not found
- `AADSTS7000215`: Invalid credentials
- `AADSTS50076`: MFA required

### Exponential Backoff

```python
import time
import random
from msal import ConfidentialClientApplication

def acquire_token_with_retry(app, scopes, max_retries=3):
    """Acquire token with exponential backoff."""
    
    for attempt in range(max_retries):
        result = app.acquire_token_for_client(scopes=scopes)
        
        if "access_token" in result:
            return result
        
        error = result.get("error", "")
        
        # Permanent errors - don't retry
        if error in ["invalid_client", "unauthorized_client"]:
            raise AuthenticationError(result.get("error_description"))
        
        # Transient errors - retry with backoff
        if attempt < max_retries - 1:
            wait = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait)
    
    raise AuthenticationError(f"Failed after {max_retries} attempts")
```

### MSAL Built-in Retry

MSAL includes retry logic for transient errors:

```python
from msal import ConfidentialClientApplication
import msal

# Configure HTTP client with custom retry
app = ConfidentialClientApplication(
    client_id="YOUR_CLIENT_ID",
    authority="https://login.microsoftonline.com/YOUR_TENANT_ID",
    client_credential="YOUR_SECRET",
    http_client=msal.HttpClient(
        timeout=30,
        verify=True
    )
)
```

## 5. Multi-Tenant Configuration

### Single-Tenant App

```python
# Specific tenant only
app = ConfidentialClientApplication(
    client_id="YOUR_CLIENT_ID",
    authority="https://login.microsoftonline.com/YOUR_TENANT_ID",
    client_credential="YOUR_SECRET"
)
```

### Multi-Tenant App

```python
# Any Azure AD tenant
app = ConfidentialClientApplication(
    client_id="YOUR_CLIENT_ID",
    authority="https://login.microsoftonline.com/common",
    client_credential="YOUR_SECRET"
)

# Or organizations only (no personal accounts)
app = ConfidentialClientApplication(
    client_id="YOUR_CLIENT_ID",
    authority="https://login.microsoftonline.com/organizations",
    client_credential="YOUR_SECRET"
)
```

### Dynamic Tenant

```python
def get_token_for_tenant(tenant_id: str, scopes: list):
    """Get token for specific tenant."""
    app = ConfidentialClientApplication(
        client_id="YOUR_CLIENT_ID",
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        client_credential="YOUR_SECRET"
    )
    return app.acquire_token_for_client(scopes=scopes)
```

## 6. Debugging Authentication Issues

### Enable MSAL Logging

```python
import logging
import msal

# Enable verbose logging
logging.basicConfig(level=logging.DEBUG)

# MSAL-specific logger
msal_logger = logging.getLogger("msal")
msal_logger.setLevel(logging.DEBUG)

# Enable PII logging (only for debugging!)
app = msal.ConfidentialClientApplication(
    client_id="YOUR_CLIENT_ID",
    authority="https://login.microsoftonline.com/YOUR_TENANT_ID",
    client_credential="YOUR_SECRET",
    enable_pii_log=True  # WARNING: Logs sensitive data
)
```

### Azure Identity Logging

```python
import logging
from azure.identity import DefaultAzureCredential

# Enable Azure SDK logging
logging.basicConfig(level=logging.DEBUG)
azure_logger = logging.getLogger("azure")
azure_logger.setLevel(logging.DEBUG)

credential = DefaultAzureCredential(logging_enable=True)
```

### Token Inspection

```python
import jwt
from datetime import datetime

def debug_token(token: str):
    """Inspect token for debugging."""
    
    # Decode without verification
    decoded = jwt.decode(token, options={"verify_signature": False})
    
    print("=== Token Debug ===")
    print(f"Issuer: {decoded.get('iss')}")
    print(f"Audience: {decoded.get('aud')}")
    print(f"Subject: {decoded.get('sub')}")
    
    # Check times
    iat = decoded.get('iat')
    exp = decoded.get('exp')
    if iat:
        print(f"Issued: {datetime.fromtimestamp(iat)}")
    if exp:
        exp_time = datetime.fromtimestamp(exp)
        print(f"Expires: {exp_time}")
        print(f"Expired: {datetime.now() > exp_time}")
    
    # Check permissions
    if 'scp' in decoded:
        print(f"Delegated scopes: {decoded['scp']}")
    if 'roles' in decoded:
        print(f"App roles: {decoded['roles']}")
    
    return decoded
```

### Azure Portal Sign-in Logs

1. Navigate to Azure Portal -> Microsoft Entra ID
2. Select "Sign-in logs" under Monitoring
3. Filter by application, user, or time range
4. Check "Status" column for errors
5. Click entry for detailed error information

## SDK Examples (Python)

### Complete Token Manager Class

```python
from msal import ConfidentialClientApplication, SerializableTokenCache
import os
import time
import logging

class TokenManager:
    """Production-ready token manager with caching and retry."""
    
    def __init__(self, client_id: str, tenant_id: str, client_secret: str, 
                 cache_file: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Set up cache
        self.cache = SerializableTokenCache()
        self.cache_file = cache_file
        if cache_file and os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                self.cache.deserialize(f.read())
        
        # Create MSAL app
        self.app = ConfidentialClientApplication(
            client_id=client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            client_credential=client_secret,
            token_cache=self.cache
        )
    
    def get_token(self, scopes: list, force_refresh: bool = False) -> str:
        """Get access token with automatic caching and retry."""
        
        # Try to get from cache first
        if not force_refresh:
            result = self.app.acquire_token_silent(scopes, account=None)
            if result and "access_token" in result:
                self.logger.debug("Token retrieved from cache")
                return result["access_token"]
        
        # Acquire new token with retry
        for attempt in range(3):
            result = self.app.acquire_token_for_client(scopes=scopes)
            
            if "access_token" in result:
                self._save_cache()
                return result["access_token"]
            
            error = result.get("error", "")
            self.logger.warning(f"Token acquisition failed: {error}")
            
            if error in ["invalid_client", "unauthorized_client"]:
                raise Exception(f"Authentication failed: {result.get('error_description')}")
            
            if attempt < 2:
                time.sleep(2 ** attempt)
        
        raise Exception("Failed to acquire token after retries")
    
    def _save_cache(self):
        if self.cache_file and self.cache.has_state_changed:
            with open(self.cache_file, 'w') as f:
                f.write(self.cache.serialize())

# Usage
token_manager = TokenManager(
    client_id="YOUR_CLIENT_ID",
    tenant_id="YOUR_TENANT_ID",
    client_secret="YOUR_SECRET",
    cache_file="/var/app/tokens.json"
)

token = token_manager.get_token(["https://graph.microsoft.com/.default"])
```

## Error Responses

- **AADSTS50196**: Loop detected (retry with backoff)
- **AADSTS700016**: Application not found in tenant
- **AADSTS7000215**: Invalid client secret or certificate
- **AADSTS50076**: MFA required (delegated flows only)
- **AADSTS700024**: Client assertion expired

## Limitations and Known Issues

- [COMMUNITY] Persistent cache on shared filesystems may have race conditions (SPAUTH-SC-DEV-MSALCACHE)
- Token cache serialization format is not documented
- No built-in distributed cache in MSAL (must implement)

## Gotchas and Quirks

- `acquire_token_silent` returns None (not error) when no cached token
- `force_refresh=True` doesn't clear cache, just bypasses it
- Multi-tenant apps need separate cache entries per tenant

## Sources

**Primary:**
- SPAUTH-SC-MSFT-TOKENLIFE: Configurable token lifetimes
- SPAUTH-SC-MSFT-REFRESH: Refresh tokens
- SPAUTH-SC-MSFT-MSALCACHE: MSAL Python token cache serialization
- SPAUTH-SC-GH-MSALCACHE: MSAL Python token_cache.py

**Community:**
- SPAUTH-SC-DEV-MSALCACHE: Python MSAL Token Cache for Confidential Clients

## Document History

**[2026-03-14 17:15]**
- Initial document created
- Caching strategies and token lifetime documented
- Error handling and debugging patterns added
