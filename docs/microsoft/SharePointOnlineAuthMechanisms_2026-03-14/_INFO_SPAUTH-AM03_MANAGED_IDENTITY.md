<DevSystem MarkdownTablesAllowed=true />

# INFO: Managed Identity Authentication

**Doc ID**: SPAUTH-AM03
**Goal**: Detailed guide for managed identity authentication in FastAPI Azure Web Apps
**Version Scope**: Azure Identity 1.x, Microsoft Entra ID (2026)

**Depends on:**
- `__AUTH_MECHANISMS_SOURCES.md [SPAUTH-SOURCES]` for source references

## 1. Intended Scenario and Recommended Use

### When to Use Managed Identity

Managed Identity is the **most secure** authentication method for Azure-hosted applications:

- **Azure App Service / Functions** - Web apps and serverless functions
- **Azure Virtual Machines** - VMs and VM Scale Sets
- **Azure Kubernetes Service** - Pods with workload identity
- **Azure Container Instances** - Containerized workloads
- **Any Azure compute** - Arc-enabled servers, Service Fabric, etc.

### Why Managed Identity is Preferred

```
┌─────────────────────────────────────────────────────────────────┐
│ Managed Identity Benefits                                       │
├─────────────────────────────────────────────────────────────────┤
│ ✅ No credentials in code or config                             │
│ ✅ No secrets to rotate or manage                               │
│ ✅ Automatic credential rotation by Azure                       │
│ ✅ Network-isolated (IMDS only accessible from within VM)       │
│ ✅ Works with SharePoint, Graph, Key Vault, Storage, etc.       │
└─────────────────────────────────────────────────────────────────┘
```

### When NOT to Use

- **Local development** - IMDS endpoint not available (use DefaultAzureCredential)
- **On-premises servers** - Not Azure-hosted (use certificate credentials)
- **Third-party hosting** - AWS, GCP, other clouds (use certificate)
- **Client applications** - Desktop/mobile apps (use interactive flows)

### System-Assigned vs User-Assigned

| Type            | Description                                      | Use Case                                   |
|-----------------|--------------------------------------------------|--------------------------------------------|
| System-Assigned | Tied to single resource, deleted with resource   | Simple single-application scenarios        |
| User-Assigned   | Independent identity, can be shared              | Multiple applications sharing identity     |

### Recommendation Level

| Scenario                             | Recommendation                      |
|--------------------------------------|-------------------------------------|
| Azure App Service (SharePoint)       | **STRONGLY RECOMMENDED**            |
| Azure Functions                      | **STRONGLY RECOMMENDED**            |
| Azure Virtual Machines               | **RECOMMENDED**                     |
| Local development                    | Not available (use fallback)        |
| On-premises                          | Not available                       |

## 2. How to Use in FastAPI Azure Web App

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ Azure App Service                                               │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ FastAPI Application                                         │ │
│ │                                                             │ │
│ │  ┌───────────────┐    ┌──────────────────────────────────┐  │ │
│ │  │ Endpoint      │───>│ SharePointService                │  │ │
│ │  │ /api/crawl    │    │ - ManagedIdentityCredential      │  │ │
│ │  └───────────────┘    │ - No secrets needed!             │  │ │
│ │                       └──────────────────────────────────┘  │ │
│ │                                    │                        │ │
│ │                                    ▼                        │ │
│ │                       ┌──────────────────────────────────┐  │ │
│ │                       │ IMDS Endpoint                    │  │ │
│ │                       │ 169.254.169.254/metadata/...     │  │ │
│ │                       │ (Azure-managed, internal only)   │  │ │
│ │                       └──────────────────────────────────┘  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Identity: System-Assigned or User-Assigned                      │
│ Permissions: Sites.Selected granted via Graph API               │
└─────────────────────────────────────────────────────────────────┘
```

### Complete FastAPI Implementation

```python
# app/services/sharepoint_mi_auth.py
import os
from azure.identity import ManagedIdentityCredential, DefaultAzureCredential
from office365.sharepoint.client_context import ClientContext
import logging

logger = logging.getLogger(__name__)

class SharePointManagedIdentityService:
    """
    SharePoint service using Managed Identity.
    Falls back to DefaultAzureCredential for local development.
    """
    
    _instance = None
    _credential = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize credential based on environment."""
        self._sharepoint_url = os.environ["SHAREPOINT_URL"]
        
        # Check if running in Azure
        if self._is_azure_environment():
            # User-assigned identity (if configured)
            user_assigned_client_id = os.environ.get("AZURE_CLIENT_ID")
            
            if user_assigned_client_id:
                self._credential = ManagedIdentityCredential(
                    client_id=user_assigned_client_id
                )
                logger.info(f"Using user-assigned managed identity: {user_assigned_client_id}")
            else:
                self._credential = ManagedIdentityCredential()
                logger.info("Using system-assigned managed identity")
        else:
            # Local development fallback
            self._credential = DefaultAzureCredential(
                exclude_managed_identity_credential=True,
                exclude_environment_credential=True
            )
            logger.info("Using DefaultAzureCredential for local development")
    
    def _is_azure_environment(self) -> bool:
        """Detect if running in Azure."""
        azure_indicators = [
            "WEBSITE_INSTANCE_ID",      # App Service
            "FUNCTIONS_WORKER_RUNTIME", # Azure Functions
            "IDENTITY_ENDPOINT",        # Managed Identity available
        ]
        return any(os.environ.get(var) for var in azure_indicators)
    
    def get_token(self) -> str:
        """Get access token for SharePoint."""
        scope = f"{self._sharepoint_url}/.default"
        token = self._credential.get_token(scope)
        return token.token
    
    def get_client_context(self, site_url: str) -> ClientContext:
        """Get SharePoint ClientContext with managed identity."""
        return ClientContext(site_url).with_access_token(self.get_token)


# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager

app = FastAPI()

# Singleton instance
_sp_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    global _sp_service
    try:
        _sp_service = SharePointManagedIdentityService()
        logger.info("SharePoint service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize SharePoint service: {e}")
        raise
    yield

app = FastAPI(lifespan=lifespan)

def get_sharepoint_service() -> SharePointManagedIdentityService:
    if _sp_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return _sp_service

@app.get("/api/sites/{site_name}/lists")
async def get_lists(
    site_name: str,
    sp_service: SharePointManagedIdentityService = Depends(get_sharepoint_service)
):
    try:
        site_url = f"https://contoso.sharepoint.com/sites/{site_name}"
        ctx = sp_service.get_client_context(site_url)
        
        lists = ctx.web.lists.get().execute_query()
        return {"lists": [{"title": l.title} for l in lists]}
    except Exception as e:
        logger.error(f"Error getting lists: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check that verifies managed identity works."""
    try:
        service = get_sharepoint_service()
        token = service.get_token()
        return {"status": "healthy", "auth": "managed_identity"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### Environment Variables

```bash
# Required
SHAREPOINT_URL=https://contoso.sharepoint.com

# Optional: For user-assigned managed identity
AZURE_CLIENT_ID=user-assigned-identity-client-id
```

**Note:** No secrets needed! Managed identity handles authentication automatically.

## 3. Prerequisites

### Enable Managed Identity on App Service

**Azure Portal:**
1. Azure Portal > App Service > Identity
2. System assigned > Status: **On** > Save
3. Note the **Object ID** displayed

**Azure CLI:**
```bash
# Enable system-assigned identity
az webapp identity assign --name myapp --resource-group mygroup

# Output shows principalId (Object ID)
```

**Bicep/ARM:**
```bicep
resource appService 'Microsoft.Web/sites@2022-03-01' = {
  name: 'myapp'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  // ...
}
```

### Grant SharePoint Permissions

Managed Identity requires permissions to be granted to its service principal.

**Step 1: Get the Managed Identity Object ID**
```powershell
# From Azure Portal: App Service > Identity > Object (principal) ID
$miObjectId = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

**Step 2: Grant Sites.Selected Permission via Graph API**

```powershell
# Connect with admin account
Connect-MgGraph -Scopes "Sites.FullControl.All", "Application.Read.All"

# Get the SharePoint site ID
$siteUrl = "contoso.sharepoint.com:/sites/hr"
$site = Get-MgSite -SiteId $siteUrl
$siteId = $site.Id

# Grant permission to managed identity
$params = @{
    roles = @("write")  # or "read" for read-only
    grantedToIdentities = @(
        @{
            application = @{
                id = $miObjectId
                displayName = "My App Service"
            }
        }
    )
}

New-MgSitePermission -SiteId $siteId -BodyParameter $params
```

**Alternative: Using REST API**
```python
import requests

def grant_site_permission(site_id: str, mi_object_id: str, access_token: str):
    """Grant Sites.Selected permission to managed identity."""
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/permissions"
    
    payload = {
        "roles": ["write"],
        "grantedToIdentities": [{
            "application": {
                "id": mi_object_id,
                "displayName": "SharePoint Crawler App"
            }
        }]
    }
    
    response = requests.post(
        url,
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    response.raise_for_status()
    return response.json()
```

### Grant Graph API Permissions (If Needed)

For Graph API access, permissions must be granted via PowerShell:

```powershell
# Get the managed identity service principal
$miObjectId = "your-managed-identity-object-id"
$mi = Get-MgServicePrincipal -Filter "id eq '$miObjectId'"

# Get Microsoft Graph service principal
$graphSp = Get-MgServicePrincipal -Filter "appId eq '00000003-0000-0000-c000-000000000000'"

# Find the permission (e.g., Sites.Read.All)
$permission = $graphSp.AppRoles | Where-Object { $_.Value -eq "Sites.Read.All" }

# Grant the permission
New-MgServicePrincipalAppRoleAssignment `
    -ServicePrincipalId $mi.Id `
    -PrincipalId $mi.Id `
    -ResourceId $graphSp.Id `
    -AppRoleId $permission.Id
```

## 4. Dependencies and Maintenance Problems

### Required Packages

```txt
# requirements.txt
azure-identity>=1.15.0
Office365-REST-Python-Client>=2.5.0
```

### Maintenance Concerns

| Issue                                 | Impact                           | Mitigation                                     |
|---------------------------------------|----------------------------------|------------------------------------------------|
| Cold start delay                      | First request slow (2-5 seconds) | Implement health probe warmup                  |
| Instance Metadata Service timeout     | Token acquisition fails          | Azure SDK handles retries automatically        |
| Permission drift                      | Access lost if site moves        | Monitor with Graph API                         |
| Identity deleted                      | Authentication fails             | Do not delete App Service                      |
| User-assigned identity confusion      | Wrong identity used              | Explicitly specify client_id                   |

### Cold Start Handling

```python
import asyncio
from azure.identity import ManagedIdentityCredential

class WarmupService:
    """Warm up managed identity on startup."""
    
    @staticmethod
    async def warmup():
        """Pre-fetch token during startup."""
        try:
            credential = ManagedIdentityCredential()
            # Trigger token acquisition
            token = credential.get_token("https://graph.microsoft.com/.default")
            logger.info(f"Warmup complete, token expires: {token.expires_on}")
        except Exception as e:
            logger.warning(f"Warmup failed (may be local dev): {e}")

# In FastAPI lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    await WarmupService.warmup()
    yield
```

### Monitoring

```python
@app.get("/health/identity")
async def identity_health():
    """Check managed identity health."""
    import time
    
    start = time.time()
    try:
        credential = ManagedIdentityCredential()
        token = credential.get_token("https://graph.microsoft.com/.default")
        elapsed = time.time() - start
        
        return {
            "status": "healthy",
            "token_acquisition_ms": int(elapsed * 1000),
            "expires_on": token.expires_on
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "elapsed_ms": int((time.time() - start) * 1000)
        }
```

## 5. Code Examples

### Basic Usage

```python
from azure.identity import ManagedIdentityCredential

# System-assigned identity
credential = ManagedIdentityCredential()

# User-assigned identity
credential = ManagedIdentityCredential(
    client_id="user-assigned-identity-client-id"
)

# Get token
token = credential.get_token("https://contoso.sharepoint.com/.default")
print(f"Token acquired, expires: {token.expires_on}")
```

### With SharePoint

```python
from azure.identity import ManagedIdentityCredential
from office365.sharepoint.client_context import ClientContext

credential = ManagedIdentityCredential()

def get_token():
    return credential.get_token("https://contoso.sharepoint.com/.default").token

ctx = ClientContext("https://contoso.sharepoint.com/sites/hr").with_access_token(get_token)

# Get web info
web = ctx.web.get().execute_query()
print(f"Site: {web.title}")

# List all lists
lists = ctx.web.lists.get().execute_query()
for lst in lists:
    print(f"  - {lst.title}")
```

### With Graph API

```python
from azure.identity import ManagedIdentityCredential
import httpx

credential = ManagedIdentityCredential()
token = credential.get_token("https://graph.microsoft.com/.default")

# List SharePoint sites
response = httpx.get(
    "https://graph.microsoft.com/v1.0/sites?search=*",
    headers={"Authorization": f"Bearer {token.token}"}
)
sites = response.json()["value"]
```

### Fallback for Local Development

```python
from azure.identity import (
    ManagedIdentityCredential,
    ChainedTokenCredential,
    AzureCliCredential,
    VisualStudioCodeCredential
)
import os

def create_credential():
    """Create credential with local dev fallback."""
    
    credentials = []
    
    # Try managed identity first (Azure environment)
    if os.environ.get("IDENTITY_ENDPOINT"):
        credentials.append(ManagedIdentityCredential())
    
    # Local development fallbacks
    credentials.extend([
        AzureCliCredential(),
        VisualStudioCodeCredential()
    ])
    
    return ChainedTokenCredential(*credentials)

credential = create_credential()
token = credential.get_token("https://graph.microsoft.com/.default")
```

### Error Handling

```python
from azure.identity import ManagedIdentityCredential, CredentialUnavailableError
from azure.core.exceptions import ClientAuthenticationError

def acquire_token_safely(scope: str):
    try:
        credential = ManagedIdentityCredential()
        return credential.get_token(scope)
    
    except CredentialUnavailableError as e:
        # Not running in Azure environment
        logger.error(f"Managed identity not available: {e}")
        raise RuntimeError("This app must run in Azure with managed identity enabled")
    
    except ClientAuthenticationError as e:
        # Permission issues
        logger.error(f"Authentication failed: {e}")
        if "AADSTS700024" in str(e):
            logger.error("Identity may not have required permissions")
        raise
```

## 6. Gotchas and Quirks

### IMDS Endpoint Cold Start

The IMDS endpoint (169.254.169.254) may take 2-5 seconds to respond on first request after a cold start. Azure Identity SDK handles retries automatically.

```python
# The SDK handles this, but you may see slow first requests
# Consider warming up during startup
```

### Sites.Selected Requires Graph API Grant

Unlike app registrations, managed identities can't have API permissions assigned in the portal. You must use PowerShell or Graph API:

```powershell
# This is the ONLY way to grant Sites.Selected to managed identity
New-MgSitePermission -SiteId $siteId -BodyParameter @{
    roles = @("write")
    grantedToIdentities = @(@{
        application = @{ id = $miObjectId }
    })
}
```

### User-Assigned vs System-Assigned Confusion

If you have both types, explicitly specify which one to use:

```python
# WRONG - may use wrong identity
credential = ManagedIdentityCredential()

# CORRECT - explicit user-assigned
credential = ManagedIdentityCredential(
    client_id="specific-user-assigned-client-id"
)
```

### Local Development: IMDS Not Available

Managed identity only works in Azure. For local development:

```python
# This will FAIL locally
credential = ManagedIdentityCredential()  # CredentialUnavailableError

# Use DefaultAzureCredential instead
credential = DefaultAzureCredential()  # Falls back to CLI/VS Code
```

### Token Resource URL Format

```python
# Wrong
credential.get_token("https://contoso.sharepoint.com")  # Missing /.default

# Correct
credential.get_token("https://contoso.sharepoint.com/.default")
```

### Multiple App Services Sharing Identity

User-assigned identity can be shared across multiple App Services:

```python
# Create user-assigned identity once
# Assign to multiple App Services
# All apps use same permissions

credential = ManagedIdentityCredential(
    client_id="shared-identity-client-id"
)
```

### Debugging: Check Identity is Enabled

```python
import os

@app.get("/debug/identity")
async def debug_identity():
    """Debug endpoint to check identity configuration."""
    return {
        "IDENTITY_ENDPOINT": os.environ.get("IDENTITY_ENDPOINT"),
        "IDENTITY_HEADER": os.environ.get("IDENTITY_HEADER"),
        "WEBSITE_INSTANCE_ID": os.environ.get("WEBSITE_INSTANCE_ID"),
        "identity_available": bool(os.environ.get("IDENTITY_ENDPOINT"))
    }
```

## Sources

**Primary:**
- SPAUTH-SC-MSFT-MIWORK: How managed identities work
- SPAUTH-SC-MSFT-MITOKEN: Using managed identities to acquire tokens
- SPAUTH-SC-MSFT-AZIDREADME: Azure Identity client library

## Document History

**[2026-03-14 17:10]**
- Initial document created
- Sites.Selected permission grant process documented
- Cold start handling and local dev fallback patterns included
