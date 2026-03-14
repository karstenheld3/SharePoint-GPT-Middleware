# INFO: SDK Internals

**Doc ID**: SPAUTH-IN04
**Goal**: Document how Azure Identity and MSAL libraries work internally
**Version Scope**: Azure Identity 1.x, MSAL Python 1.x

**Depends on:**
- `__AUTH_MECHANISMS_SOURCES.md [SPAUTH-SOURCES]` for source references

## Summary

The Azure Identity SDK provides a unified interface for acquiring tokens across different authentication scenarios through credential classes. DefaultAzureCredential chains multiple credentials in a specific order, trying each until one succeeds. MSAL (Microsoft Authentication Library) is the underlying library that handles OAuth flows, token caching, and token refresh. MSAL distinguishes between PublicClientApplication (for user-interactive flows) and ConfidentialClientApplication (for server-side with secrets/certificates). The token cache stores access tokens, refresh tokens, and ID tokens with metadata for efficient retrieval. When a token is requested, MSAL first checks the cache and only makes network calls if needed. Office365-REST-Python-Client integrates with both libraries through its with_access_token adapter pattern.

## Key Facts

- **DefaultAzureCredential Order**: Environment -> Workload -> Managed Identity -> Azure CLI -> PowerShell -> Developer CLI -> Interactive [VERIFIED] (SPAUTH-SC-MSFT-CREDCHAINS)
- **MSAL Cache Key**: Composed of client_id + account + scopes [VERIFIED] (SPAUTH-SC-GH-MSALCACHE)
- **Token Refresh**: MSAL refreshes proactively 5 minutes before expiration [VERIFIED] (SPAUTH-SC-MSFT-MSALPYTHON)
- **PublicClientApplication**: Cannot store secrets, uses device code or interactive flows [VERIFIED] (SPAUTH-SC-MSFT-MSALPYTHON)
- **ConfidentialClientApplication**: Server-side apps with secrets/certificates [VERIFIED] (SPAUTH-SC-MSFT-MSALPYTHON)

## Quick Reference

**Credential Chain Order:**
```
DefaultAzureCredential tries:
1. EnvironmentCredential
2. WorkloadIdentityCredential  
3. ManagedIdentityCredential
4. AzureCliCredential
5. AzurePowerShellCredential
6. AzureDeveloperCliCredential
7. InteractiveBrowserCredential (if enabled)
```

## 1. DefaultAzureCredential Chain

### How It Works

DefaultAzureCredential is a meta-credential that wraps multiple credential types and tries them in order:

```python
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
token = credential.get_token("https://graph.microsoft.com/.default")
```

### Chain Order (as of Azure Identity 1.x)

1. **EnvironmentCredential**: Checks environment variables
   - `AZURE_CLIENT_ID` + `AZURE_CLIENT_SECRET` + `AZURE_TENANT_ID` -> ClientSecretCredential
   - `AZURE_CLIENT_ID` + `AZURE_CLIENT_CERTIFICATE_PATH` + `AZURE_TENANT_ID` -> CertificateCredential
   - `AZURE_CLIENT_ID` + `AZURE_USERNAME` + `AZURE_PASSWORD` -> UsernamePasswordCredential

2. **WorkloadIdentityCredential**: For Kubernetes pods with federated identity

3. **ManagedIdentityCredential**: For Azure-hosted resources (VMs, App Service, Functions)

4. **AzureCliCredential**: Uses `az login` session

5. **AzurePowerShellCredential**: Uses `Connect-AzAccount` session

6. **AzureDeveloperCliCredential**: Uses `azd auth login` session

7. **InteractiveBrowserCredential**: Opens browser (only if `exclude_interactive_browser_credential=False`)

### Excluding Credentials

```python
from azure.identity import DefaultAzureCredential

# Skip credentials that don't apply
credential = DefaultAzureCredential(
    exclude_environment_credential=True,
    exclude_managed_identity_credential=False,  # We want this
    exclude_cli_credential=True,
    exclude_powershell_credential=True
)
```

[VERIFIED] (SPAUTH-SC-MSFT-CREDCHAINS | SPAUTH-SC-MSFT-AZIDREADME)

## 2. ChainedTokenCredential

For custom credential ordering:

```python
from azure.identity import (
    ChainedTokenCredential,
    ManagedIdentityCredential,
    AzureCliCredential,
    InteractiveBrowserCredential
)

# Custom order: MI -> CLI -> Interactive
credential = ChainedTokenCredential(
    ManagedIdentityCredential(),
    AzureCliCredential(),
    InteractiveBrowserCredential(client_id="...")
)

token = credential.get_token("https://graph.microsoft.com/.default")
```

### Continuation Policy

As of Azure Identity 1.14.0, the chain continues trying developer credentials even if one fails. Production credentials (Environment, Workload, Managed Identity) still stop the chain on failure.

[VERIFIED] (SPAUTH-SC-MSFT-CREDCHAINS)

## 3. MSAL Application Types

### PublicClientApplication

For applications that cannot securely store secrets (desktop, mobile, CLI):

```python
from msal import PublicClientApplication

app = PublicClientApplication(
    client_id="YOUR_CLIENT_ID",
    authority="https://login.microsoftonline.com/YOUR_TENANT_ID"
)

# Available methods:
# - acquire_token_interactive()
# - acquire_token_by_device_flow()
# - acquire_token_silent()
# - acquire_token_by_username_password() [deprecated]
```

### ConfidentialClientApplication

For server-side applications with secrets or certificates:

```python
from msal import ConfidentialClientApplication

app = ConfidentialClientApplication(
    client_id="YOUR_CLIENT_ID",
    authority="https://login.microsoftonline.com/YOUR_TENANT_ID",
    client_credential="YOUR_SECRET"  # Or certificate dict
)

# Available methods:
# - acquire_token_for_client() [client credentials flow]
# - acquire_token_on_behalf_of() [OBO flow]
# - acquire_token_silent()
# - acquire_token_by_authorization_code()
```

[VERIFIED] (SPAUTH-SC-MSFT-MSALPYTHON)

## 4. MSAL Token Cache Internals

### Cache Data Structure

The token cache stores multiple token types with metadata:

```python
# Internal cache structure (simplified)
{
    "AccessToken": {
        "home_account_id-environment-realm-client_id-target": {
            "credential_type": "AccessToken",
            "secret": "eyJ0eXAiOi...",
            "home_account_id": "oid.tid",
            "environment": "login.microsoftonline.com",
            "realm": "tenant_id",
            "target": "https://graph.microsoft.com/.default",
            "client_id": "client_id",
            "cached_at": "1710425600",
            "expires_on": "1710429200",
            "extended_expires_on": "1710432800"
        }
    },
    "RefreshToken": {
        "home_account_id-environment-client_id": {
            "credential_type": "RefreshToken",
            "secret": "0.AVYA...",
            "home_account_id": "oid.tid",
            "environment": "login.microsoftonline.com",
            "client_id": "client_id"
        }
    },
    "IdToken": { ... },
    "Account": { ... }
}
```

### Cache Lookup Flow

1. **Build cache key** from client_id, account, and scopes
2. **Check AccessToken entries** for matching key
3. **If found and not expired**: Return cached token
4. **If expired but RefreshToken exists**: Use refresh token to get new access token
5. **If no cache hit**: Make network request

### Persistent Cache

```python
from msal import PublicClientApplication, SerializableTokenCache

# Create serializable cache
cache = SerializableTokenCache()

# Load from file if exists
if os.path.exists("token_cache.json"):
    with open("token_cache.json", "r") as f:
        cache.deserialize(f.read())

app = PublicClientApplication(
    client_id="YOUR_CLIENT_ID",
    authority="https://login.microsoftonline.com/YOUR_TENANT_ID",
    token_cache=cache
)

# After token acquisition, save cache
if cache.has_state_changed:
    with open("token_cache.json", "w") as f:
        f.write(cache.serialize())
```

[VERIFIED] (SPAUTH-SC-GH-MSALCACHE | SPAUTH-SC-MSFT-MSALCACHE)

## 5. Token Acquisition Flow in MSAL

### acquire_token_silent Flow

```
acquire_token_silent(scopes, account)
    |
    v
[Check cache for matching access token]
    |
    +---> Found & valid? Return token
    |
    v
[Check cache for refresh token]
    |
    +---> Found? Use to get new access token
    |         |
    |         v
    |     [POST to token endpoint with refresh_token]
    |         |
    |         v
    |     [Update cache with new tokens]
    |         |
    |         v
    |     Return new access token
    |
    +---> Not found? Raise error (caller must use interactive flow)
```

### acquire_token_for_client Flow (Client Credentials)

```
acquire_token_for_client(scopes)
    |
    v
[Check cache for matching access token]
    |
    +---> Found & valid? Return token
    |
    v
[Build token request]
    |
    +---> Client secret: Add client_secret parameter
    |
    +---> Certificate: Create client_assertion JWT
    |
    v
[POST to token endpoint]
    |
    v
[Store in cache]
    |
    v
Return access token
```

[VERIFIED] (SPAUTH-SC-GH-MSALSRC)

## 6. Azure Identity Credential Wrapper Pattern

Azure Identity credentials wrap MSAL internally:

```python
# Simplified view of how CertificateCredential works internally

class CertificateCredential:
    def __init__(self, tenant_id, client_id, certificate_path, ...):
        # Create MSAL ConfidentialClientApplication
        self._app = ConfidentialClientApplication(
            client_id=client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            client_credential={
                "thumbprint": self._get_thumbprint(certificate_path),
                "private_key": self._load_private_key(certificate_path)
            }
        )
    
    def get_token(self, *scopes, **kwargs):
        # Try silent first
        result = self._app.acquire_token_silent(
            list(scopes), 
            account=None
        )
        
        if not result:
            # Acquire new token
            result = self._app.acquire_token_for_client(list(scopes))
        
        return AccessToken(
            token=result["access_token"],
            expires_on=result["expires_in"] + time.time()
        )
```

## 7. Office365-REST-Python-Client Integration

### with_access_token Adapter

This pattern allows using any Azure Identity credential:

```python
from azure.identity import DefaultAzureCredential
from office365.sharepoint.client_context import ClientContext

credential = DefaultAzureCredential()
resource = "https://contoso.sharepoint.com"

def token_provider():
    """Called by library when token is needed."""
    token = credential.get_token(f"{resource}/.default")
    return token.token

ctx = ClientContext(site_url).with_access_token(token_provider)
```

### Internal Flow

```
ClientContext.execute_query()
    |
    v
[Check if token needed]
    |
    v
[Call token_provider function]
    |
    v
[Add Authorization header: "Bearer {token}"]
    |
    v
[Make HTTP request to SharePoint]
```

### with_client_certificate Internal Flow

```python
# What with_client_certificate does internally:

def with_client_certificate(self, tenant, client_id, thumbprint, cert_path):
    # Creates internal MSAL ConfidentialClientApplication
    # Handles token acquisition and caching
    # Similar to CertificateCredential but SharePoint-specific
    pass
```

[VERIFIED] (SPAUTH-SC-PYPI-O365 | SPAUTH-SC-GH-O365)

## SDK Examples (Python)

### Custom Credential Chain

```python
from azure.identity import ChainedTokenCredential, ManagedIdentityCredential
from azure.identity import CertificateCredential, InteractiveBrowserCredential

def create_sharepoint_credential(config):
    """Create credential chain appropriate for environment."""
    
    credentials = []
    
    # In Azure: use managed identity
    credentials.append(ManagedIdentityCredential())
    
    # Fallback: certificate if configured
    if config.get("cert_path"):
        credentials.append(CertificateCredential(
            tenant_id=config["tenant_id"],
            client_id=config["client_id"],
            certificate_path=config["cert_path"]
        ))
    
    # Development: interactive browser
    if config.get("allow_interactive"):
        credentials.append(InteractiveBrowserCredential(
            tenant_id=config["tenant_id"],
            client_id=config["client_id"]
        ))
    
    return ChainedTokenCredential(*credentials)
```

### MSAL with Custom Cache

```python
from msal import ConfidentialClientApplication, SerializableTokenCache
import json
import os

class PersistentTokenCache:
    def __init__(self, cache_file: str):
        self.cache_file = cache_file
        self.cache = SerializableTokenCache()
        self._load()
    
    def _load(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                self.cache.deserialize(f.read())
    
    def save(self):
        if self.cache.has_state_changed:
            with open(self.cache_file, 'w') as f:
                f.write(self.cache.serialize())
    
    def get_cache(self):
        return self.cache

# Usage
token_cache = PersistentTokenCache("tokens.json")

app = ConfidentialClientApplication(
    client_id="YOUR_CLIENT_ID",
    authority="https://login.microsoftonline.com/YOUR_TENANT_ID",
    client_credential="YOUR_SECRET",
    token_cache=token_cache.get_cache()
)

result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

# Save cache after acquisition
token_cache.save()
```

## Error Responses

- **CredentialUnavailableError**: Credential cannot attempt authentication (missing config)
- **ClientAuthenticationError**: Authentication failed (wrong credentials)
- **AuthenticationRequiredError**: User interaction needed but not enabled

## Limitations and Known Issues

- [COMMUNITY] DefaultAzureCredential can be slow if many credentials fail before success (SPAUTH-SC-DEV-MSALCACHE)
- Token cache is not encrypted by default
- MSAL cache format is not documented and may change

## Gotchas and Quirks

- PublicClientApplication requires `accounts` for silent token acquisition
- ConfidentialClientApplication doesn't track accounts (app-only)
- Refresh tokens are not returned for client credentials flow

## Sources

**Primary:**
- SPAUTH-SC-MSFT-AZIDREADME: Azure Identity client library for Python
- SPAUTH-SC-MSFT-CREDCHAINS: Credential chains in Azure Identity
- SPAUTH-SC-MSFT-MSALPYTHON: MSAL for Python overview
- SPAUTH-SC-GH-MSALSRC: MSAL Python source code
- SPAUTH-SC-GH-MSALCACHE: MSAL Python token_cache.py

**Community:**
- SPAUTH-SC-DEV-MSALCACHE: Python MSAL Token Cache for Confidential Clients

## Document History

**[2026-03-14 17:05]**
- Initial document created
- Credential chain order documented
- MSAL internals and cache structure explained
