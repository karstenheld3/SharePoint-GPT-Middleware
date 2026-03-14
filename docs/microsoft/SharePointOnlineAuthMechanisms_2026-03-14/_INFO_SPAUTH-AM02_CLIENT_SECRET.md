<DevSystem MarkdownTablesAllowed=true />

# INFO: Client Secret Authentication

**Doc ID**: SPAUTH-AM02
**Goal**: Detailed guide for client secret authentication in FastAPI Azure Web Apps
**Version Scope**: Azure Identity 1.x, MSAL Python 1.x, Microsoft Entra ID (2026)

**Depends on:**
- `__AUTH_MECHANISMS_SOURCES.md [SPAUTH-SOURCES]` for source references

## 1. Intended Scenario and Recommended Use

### When to Use Client Secret

Client secrets provide simple app-only authentication but with significant limitations:

- **Microsoft Graph API only** - Works for Graph endpoints (`graph.microsoft.com`)
- **Quick prototypes** - Fastest setup for non-SharePoint scenarios
- **Non-sensitive environments** - Development, testing where security is less critical
- **Microservices calling Graph** - When managed identity isn't available

### When NOT to Use

- **SharePoint REST API** - **BLOCKED** - Client secrets do NOT work for `/_api/` endpoints
- **Production high-security** - Secrets can be leaked, intercepted, or compromised
- **Long-running services** - Secrets expire and require rotation
- **Azure-hosted apps** - Use Managed Identity instead (more secure, no secrets)

### Critical Limitation: SharePoint Blocks Client Secrets

```
┌────────────────────────────────────────────────────────────────┐
│ WARNING: SharePoint Online blocks client secret authentication │
│ for app-only access. You MUST use certificates for SharePoint. │
└────────────────────────────────────────────────────────────────┘
```

| API | Client Secret Support |
|-----|----------------------|
| Microsoft Graph (`graph.microsoft.com`) | Yes |
| SharePoint REST (`/_api/`) | **NO - Blocked** |
| SharePoint via Graph (`/sites/...`) | Yes (but limited) |

### Recommendation Level

| Scenario | Recommendation |
|----------|----------------|
| SharePoint REST API | **NOT SUPPORTED** |
| Microsoft Graph API | Acceptable (certificate preferred) |
| Development/Testing | OK for quick iteration |
| Production | **NOT RECOMMENDED** - use certificate or MI |

## 2. How to Use in FastAPI Azure Web App

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Azure App Service                                           │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ FastAPI Application                                     │ │
│ │                                                         │ │
│ │  ┌─────────────┐    ┌──────────────────────────────┐    │ │
│ │  │ Endpoint    │───>│ GraphService                 │    │ │
│ │  │ /api/users  │    │ - ClientSecretCredential     │    │ │
│ │  └─────────────┘    │ - Graph API calls            │    │ │
│ │                     └──────────────────────────────┘    │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Secret stored in:                                           │
│ - Azure Key Vault (recommended)                             │
│ - App Service Configuration                                 │
│ - Environment variables (not for production)                │
└─────────────────────────────────────────────────────────────┘
         │
         │ Works for Graph API
         v
┌─────────────────────┐
│ Microsoft Graph API │  ✅ Supported
└─────────────────────┘

         │
         │ BLOCKED for SharePoint REST
         v
┌─────────────────────┐
│ SharePoint REST API │  ❌ Access Denied
└─────────────────────┘
```

### FastAPI Implementation (Graph API Only)

```python
# app/services/graph_auth.py
import os
from functools import lru_cache
from azure.identity import ClientSecretCredential
import httpx
import logging

logger = logging.getLogger(__name__)

class GraphService:
    """
    Service for Microsoft Graph API using client secret.
    NOTE: This does NOT work for SharePoint REST API.
    """
    
    _instance = None
    _credential = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize credential once at startup."""
        self._tenant_id = os.environ["AZURE_TENANT_ID"]
        self._client_id = os.environ["AZURE_CLIENT_ID"]
        self._client_secret = os.environ["AZURE_CLIENT_SECRET"]
        
        self._credential = ClientSecretCredential(
            tenant_id=self._tenant_id,
            client_id=self._client_id,
            client_secret=self._client_secret
        )
        
        self._graph_url = "https://graph.microsoft.com/v1.0"
        logger.info("Initialized Graph service with client secret")
    
    def get_token(self) -> str:
        """Get access token for Graph API."""
        token = self._credential.get_token("https://graph.microsoft.com/.default")
        return token.token
    
    async def get_user(self, user_id: str) -> dict:
        """Get user from Graph API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._graph_url}/users/{user_id}",
                headers={"Authorization": f"Bearer {self.get_token()}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def list_sites(self) -> list:
        """List SharePoint sites via Graph API (limited functionality)."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._graph_url}/sites?search=*",
                headers={"Authorization": f"Bearer {self.get_token()}"}
            )
            response.raise_for_status()
            return response.json().get("value", [])


# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from app.services.graph_auth import GraphService

app = FastAPI()

def get_graph_service() -> GraphService:
    return GraphService()

@app.get("/api/users/{user_id}")
async def get_user(
    user_id: str,
    graph: GraphService = Depends(get_graph_service)
):
    try:
        user = await graph.get_user(user_id)
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sites")
async def list_sites(graph: GraphService = Depends(get_graph_service)):
    """List sites via Graph API (works with client secret)."""
    try:
        sites = await graph.list_sites()
        return {"sites": sites}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Demonstrating SharePoint Failure

```python
# This code demonstrates WHY client secrets fail for SharePoint REST API

from azure.identity import ClientSecretCredential
import httpx

credential = ClientSecretCredential(
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-secret"
)

# This token IS acquired successfully
token = credential.get_token("https://contoso.sharepoint.com/.default")
print(f"Token acquired: {token.token[:50]}...")  # Works!

# But SharePoint REST API rejects it
response = httpx.get(
    "https://contoso.sharepoint.com/_api/web",
    headers={"Authorization": f"Bearer {token.token}"}
)
print(f"Status: {response.status_code}")  # 401 or 403!
print(f"Error: {response.text}")  # Access denied
```

### Environment Variables

```bash
# Required
AZURE_TENANT_ID=12345678-1234-1234-1234-123456789012
AZURE_CLIENT_ID=abcdefab-1234-5678-abcd-abcdefabcdef
AZURE_CLIENT_SECRET=your-client-secret-value
```

## 3. Prerequisites

### Azure AD App Registration

1. **Create App Registration**
   - Azure Portal > Microsoft Entra ID > App registrations > New registration
   - Name: "Graph API App"
   - Supported account types: Single tenant

2. **Create Client Secret**
   - App registration > Certificates & secrets > Client secrets > New client secret
   - Description: "Production secret"
   - Expiration: 6 months, 12 months, or 24 months (max)
   - **Copy the secret value immediately** - it's only shown once!

3. **Configure API Permissions**
   
   This method uses **Application permissions** (app-only). **Graph API only** - SharePoint REST blocked.
   
   - **Recommended:** `Sites.Selected` - Least-privilege, per-site access
   - **Alternative:** `Sites.ReadWrite.All` - If accessing many sites
   - **Important:** Client secrets do NOT work with SharePoint REST API
   
   See [`_INFO_SPAUTH-IN07_AZURE_PERMISSION_REQUIREMENTS.md`](_INFO_SPAUTH-IN07_AZURE_PERMISSION_REQUIREMENTS.md) for full details.

### Storing Secrets Securely

**Option 1: Azure Key Vault (Recommended)**
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

def get_client_secret():
    credential = DefaultAzureCredential()  # Uses managed identity
    client = SecretClient(
        vault_url="https://mykeyvault.vault.azure.net",
        credential=credential
    )
    secret = client.get_secret("graph-client-secret")
    return secret.value
```

**Option 2: App Service Configuration**
- Azure Portal > App Service > Configuration > Application settings
- Add: `AZURE_CLIENT_SECRET` = `your-secret`
- Secrets are encrypted at rest

**Option 3: Environment Variables (Dev Only)**
```bash
export AZURE_CLIENT_SECRET="your-secret-here"
```

## 4. Dependencies and Maintenance Problems

### Required Packages

```txt
# requirements.txt
azure-identity>=1.15.0
msal>=1.26.0
httpx>=0.25.0  # For async HTTP calls
```

### Maintenance Concerns

| Issue                      | Impact                                      | Mitigation                                                 |
|----------------------------|---------------------------------------------|------------------------------------------------------------|
| Secret expiration          | **Authentication fails** - max 24 months    | Set rotation reminders; use Key Vault rotation             |
| Secret in logs             | Security breach                             | Never log secrets; use structured logging                  |
| Secret in source control   | Compromised credential                      | Use .gitignore; scan for secrets in continuous integration |
| Secret theft               | Full application access                     | Monitor sign-in logs; use Conditional Access               |
| No rotation mechanism      | Manual rotation needed                      | Implement dual-secret strategy                             |

### Secret Rotation Strategy

```python
# Support two secrets during rotation
class DualSecretCredential:
    """
    Tries primary secret, falls back to secondary.
    Enables zero-downtime secret rotation.
    """
    
    def __init__(self, tenant_id: str, client_id: str):
        self.credentials = []
        
        # Primary secret
        primary = os.environ.get("AZURE_CLIENT_SECRET")
        if primary:
            self.credentials.append(
                ClientSecretCredential(tenant_id, client_id, primary)
            )
        
        # Secondary secret (during rotation)
        secondary = os.environ.get("AZURE_CLIENT_SECRET_SECONDARY")
        if secondary:
            self.credentials.append(
                ClientSecretCredential(tenant_id, client_id, secondary)
            )
    
    def get_token(self, scope: str):
        for cred in self.credentials:
            try:
                return cred.get_token(scope)
            except Exception:
                continue
        raise Exception("All secrets failed")
```

### Rotation Procedure

1. Generate new secret in Azure Portal (don't delete old one)
2. Update Key Vault / App Configuration with new secret
3. Verify app works with new secret
4. Delete old secret from Azure Portal

## 5. Code Examples

### Basic Token Acquisition

```python
from azure.identity import ClientSecretCredential

credential = ClientSecretCredential(
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-secret"
)

# For Graph API (works)
token = credential.get_token("https://graph.microsoft.com/.default")
print(f"Token: {token.token[:50]}...")
```

### With MSAL

```python
from msal import ConfidentialClientApplication

app = ConfidentialClientApplication(
    client_id="your-client-id",
    authority="https://login.microsoftonline.com/your-tenant-id",
    client_credential="your-secret"
)

result = app.acquire_token_for_client(
    scopes=["https://graph.microsoft.com/.default"]
)

if "access_token" in result:
    print(f"Token: {result['access_token'][:50]}...")
else:
    print(f"Error: {result.get('error_description')}")
```

### Calling Graph API

```python
import httpx
from azure.identity import ClientSecretCredential

credential = ClientSecretCredential(
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-secret"
)

token = credential.get_token("https://graph.microsoft.com/.default")

# List all users
response = httpx.get(
    "https://graph.microsoft.com/v1.0/users",
    headers={"Authorization": f"Bearer {token.token}"}
)
users = response.json()

# List SharePoint sites via Graph (limited, but works)
response = httpx.get(
    "https://graph.microsoft.com/v1.0/sites?search=*",
    headers={"Authorization": f"Bearer {token.token}"}
)
sites = response.json()
```

### Error Handling

```python
from azure.identity import ClientSecretCredential
from azure.core.exceptions import ClientAuthenticationError

def get_graph_token():
    try:
        credential = ClientSecretCredential(
            tenant_id=os.environ["AZURE_TENANT_ID"],
            client_id=os.environ["AZURE_CLIENT_ID"],
            client_secret=os.environ["AZURE_CLIENT_SECRET"]
        )
        return credential.get_token("https://graph.microsoft.com/.default")
    
    except ClientAuthenticationError as e:
        if "AADSTS7000215" in str(e):
            logger.error("Invalid client secret")
        elif "AADSTS700016" in str(e):
            logger.error("Application not found")
        elif "AADSTS70011" in str(e):
            logger.error("Invalid scope")
        raise
```

## 6. Gotchas and Quirks

### Critical: SharePoint Does Not Support Client Secrets

This is the #1 gotcha. The token acquisition succeeds, but SharePoint rejects it:

```python
# Token acquired successfully
token = credential.get_token("https://contoso.sharepoint.com/.default")
# ✅ No error here

# But SharePoint REST API rejects it
response = requests.get(
    "https://contoso.sharepoint.com/_api/web",
    headers={"Authorization": f"Bearer {token.token}"}
)
# ❌ 401 Unauthorized or 403 Forbidden
```

**Solution:** Use certificate credentials for SharePoint REST API.

### Secret Value Only Shown Once

When you create a client secret in Azure Portal, the value is displayed only once. If you navigate away without copying it, you must create a new secret.

```
┌──────────────────────────────────────────────────┐
│ ⚠️ Copy the secret value NOW - you can't see it  │
│    again after leaving this page!                │
└──────────────────────────────────────────────────┘
```

### Secret Expiration

- Maximum lifetime: 24 months
- No auto-rotation (unlike certificates in Key Vault)
- Set calendar reminders for rotation

```python
# Check secret expiration in Azure Portal
# App registration > Certificates & secrets > Client secrets
# Shows "Expires" column
```

### Scope Format

```python
# Wrong - specific scopes don't work for client credentials
credential.get_token("User.Read.All")  # FAILS

# Correct - must use .default
credential.get_token("https://graph.microsoft.com/.default")
```

### Common Error Codes

| Error Code    | Meaning                  | Solution                                 |
|---------------|--------------------------|------------------------------------------|
| AADSTS7000215 | Invalid client secret    | Check secret value; may be expired       |
| AADSTS700016  | Application not found    | Check client_id and tenant_id            |
| AADSTS70011   | Invalid scope            | Use `.default` suffix                    |
| AADSTS65001   | No permission granted    | Grant administrator consent              |

### Performance: Reuse Credential Instance

```python
# BAD - new credential per request
@app.get("/api/data")
async def get_data():
    cred = ClientSecretCredential(...)  # Creates new each time
    token = cred.get_token(...)
    ...

# GOOD - singleton pattern
_credential = ClientSecretCredential(
    tenant_id=os.environ["AZURE_TENANT_ID"],
    client_id=os.environ["AZURE_CLIENT_ID"],
    client_secret=os.environ["AZURE_CLIENT_SECRET"]
)

@app.get("/api/data")
async def get_data():
    token = _credential.get_token(...)  # Reuses credential and cache
    ...
```

## Sources

**Primary:**
- SPAUTH-SC-MSFT-CLIENTCREDS: Client credentials flow documentation
- SPAUTH-SC-MSFT-AZIDREADME: Azure Identity client library

## Document History

**[2026-03-14 17:05]**
- Initial document created
- SharePoint limitation prominently documented
- FastAPI patterns for Graph API included
