<DevSystem MarkdownTablesAllowed=true />

# INFO: Development Tool Credentials

**Doc ID**: SPAUTH-AM09
**Goal**: Detailed guide for development tool credentials in FastAPI Azure Web Apps
**Version Scope**: Azure Identity 1.x, Microsoft Entra ID (2026)

**Depends on:**
- `__AUTH_MECHANISMS_SOURCES.md [SPAUTH-SOURCES]` for source references

## 1. Intended Scenario and Recommended Use

### When to Use Development Tool Credentials

Development tool credentials leverage existing CLI/IDE authentication for local development:

- **Local development** - No need to set up separate credentials
- **Quick prototyping** - Get started immediately
- **Testing scripts** - Run scripts with your identity
- **DefaultAzureCredential fallback** - Part of the credential chain

### Available Development Credentials

| Credential                    | Source                            | Command to Authenticate  |
|-------------------------------|-----------------------------------|--------------------------|  
| AzureCliCredential            | Azure Command Line Interface      | `az login`               |
| AzurePowerShellCredential     | Azure PowerShell                  | `Connect-AzAccount`      |
| VisualStudioCodeCredential    | Visual Studio Code Azure extension| Sign in via extension    |
| AzureDeveloperCliCredential   | Azure Developer CLI               | `azd auth login`         |

### When NOT to Use

- **Production deployments** - Use Managed Identity or certificate
- **CI/CD pipelines** - Use service principal
- **Automated scripts** - Credentials may expire during execution
- **Shared environments** - Developer identity shouldn't access prod data

### Recommendation Level

| Scenario                               | Recommendation     |
|----------------------------------------|--------------------|
| Local development                      | **RECOMMENDED**    |
| Quick testing                          | **RECOMMENDED**    |
| Production                             | **DO NOT USE**     |
| Continuous Integration/Deployment      | **DO NOT USE**     |

## 2. How to Use in FastAPI Azure Web App (Local Development)

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ Local Development Machine                                       │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ FastAPI Application (localhost:8000)                        │ │
│ │                                                             │ │
│ │  ┌───────────────┐    ┌──────────────────────────────────┐  │ │
│ │  │ Endpoint      │───>│ SharePointService                │  │ │
│ │  │ /api/lists    │    │ - Uses AzureCliCredential        │  │ │
│ │  └───────────────┘    │ - Gets token from az CLI cache   │  │ │
│ │                       └──────────────────────────────────┘  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Prerequisites:                                                  │
│ $ az login                                                      │
│ (or Connect-AzAccount, or VS Code Azure sign-in)                │
└─────────────────────────────────────────────────────────────────┘
```

### Complete Implementation

```python
# app/services/dev_auth.py
import os
from azure.identity import (
    DefaultAzureCredential,
    AzureCliCredential,
    AzurePowerShellCredential,
    VisualStudioCodeCredential,
    ChainedTokenCredential,
    ManagedIdentityCredential
)
from office365.sharepoint.client_context import ClientContext
import logging

logger = logging.getLogger(__name__)

class DevelopmentAuthService:
    """
    Authentication service that automatically uses the best available
    credential based on the environment.
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
        self._sharepoint_url = os.environ.get(
            "SHAREPOINT_URL", 
            "https://contoso.sharepoint.com"
        )
        
        if self._is_production():
            # Production: Use managed identity only
            self._credential = ManagedIdentityCredential()
            logger.info("Using ManagedIdentityCredential (production)")
        else:
            # Development: Chain of development credentials
            self._credential = self._create_dev_credential_chain()
            logger.info("Using development credential chain")
    
    def _is_production(self) -> bool:
        """Detect if running in Azure."""
        return bool(os.environ.get("WEBSITE_INSTANCE_ID"))
    
    def _create_dev_credential_chain(self):
        """Create credential chain for local development."""
        credentials = []
        
        # Try Azure CLI first (most common for developers)
        try:
            cli_cred = AzureCliCredential()
            credentials.append(cli_cred)
            logger.debug("Added AzureCliCredential to chain")
        except Exception as e:
            logger.debug(f"AzureCliCredential not available: {e}")
        
        # Try Azure PowerShell
        try:
            ps_cred = AzurePowerShellCredential()
            credentials.append(ps_cred)
            logger.debug("Added AzurePowerShellCredential to chain")
        except Exception as e:
            logger.debug(f"AzurePowerShellCredential not available: {e}")
        
        # Try VS Code
        try:
            vsc_cred = VisualStudioCodeCredential()
            credentials.append(vsc_cred)
            logger.debug("Added VisualStudioCodeCredential to chain")
        except Exception as e:
            logger.debug(f"VisualStudioCodeCredential not available: {e}")
        
        if not credentials:
            raise RuntimeError(
                "No development credentials available. "
                "Please run 'az login' or 'Connect-AzAccount'"
            )
        
        return ChainedTokenCredential(*credentials)
    
    def get_token(self) -> str:
        """Get access token for SharePoint."""
        scope = f"{self._sharepoint_url}/.default"
        token = self._credential.get_token(scope)
        return token.token
    
    def get_client_context(self, site_url: str) -> ClientContext:
        """Get SharePoint ClientContext."""
        return ClientContext(site_url).with_access_token(self.get_token)


# app/main.py
from fastapi import FastAPI, Depends, HTTPException
import os

app = FastAPI()

def get_auth_service() -> DevelopmentAuthService:
    return DevelopmentAuthService()

@app.get("/api/lists")
async def get_lists(
    auth: DevelopmentAuthService = Depends(get_auth_service)
):
    """Get SharePoint lists using development credentials."""
    try:
        site_url = f"{os.environ['SHAREPOINT_URL']}/sites/dev"
        ctx = auth.get_client_context(site_url)
        
        lists = ctx.web.lists.get().execute_query()
        return {"lists": [{"title": l.title} for l in lists]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health/auth")
async def auth_health():
    """Check which credential is being used."""
    try:
        auth = DevelopmentAuthService()
        token = auth.get_token()
        return {
            "status": "authenticated",
            "credential_type": type(auth._credential).__name__,
            "token_preview": token[:20] + "..."
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

### Environment Variables

```bash
# Optional - defaults work for most scenarios
SHAREPOINT_URL=https://contoso.sharepoint.com
```

## 3. Prerequisites

### Azure CLI

```bash
# Install Azure CLI
# Windows: winget install Microsoft.AzureCLI
# macOS: brew install azure-cli
# Linux: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login
az login

# Verify
az account show
```

### Azure PowerShell

```powershell
# Install Azure PowerShell
Install-Module -Name Az -Scope CurrentUser -Repository PSGallery

# Login
Connect-AzAccount

# Verify
Get-AzContext
```

### VS Code Azure Extension

1. Install "Azure Account" extension in VS Code
2. Press `Ctrl+Shift+P` > "Azure: Sign In"
3. Complete browser authentication

### Required Permissions

This method uses **Delegated permissions** (your developer identity). Your SharePoint permissions apply.

- **Read-only access:** `Sites.Read.All`
- **Read-write access:** `Sites.ReadWrite.All`
- **Note:** `Sites.Selected` is NOT available for delegated permissions

See [`_INFO_SPAUTH-IN07_AZURE_PERMISSION_REQUIREMENTS.md`](_INFO_SPAUTH-IN07_AZURE_PERMISSION_REQUIREMENTS.md) for full details.

## 4. Dependencies and Maintenance Problems

### Required Packages

```txt
# requirements.txt
azure-identity>=1.15.0
Office365-REST-Python-Client>=2.5.0
```

### Maintenance Concerns

| Issue                                   | Impact                          | Mitigation                               |
|-----------------------------------------|---------------------------------|------------------------------------------|
| Token expiration                        | Authentication fails after ~1 hour | Re-run `az login`                     |
| Wrong account signed in                 | Access to wrong tenant          | Verify with `az account show`            |
| Multiple subscriptions                  | May use wrong subscription      | Set default with `az account set`        |
| Visual Studio Code extension issues     | Credential not found            | Re-sign in via extension                 |
| CLI/PowerShell not installed            | Credential unavailable          | Install required tool                    |

### Refresh Tokens

Development credentials use refresh tokens that last longer:

```bash
# Azure CLI tokens refresh automatically for ~90 days
# But will eventually require re-authentication

# Force new login
az login --force
```

## 5. Code Examples

### AzureCliCredential

```python
from azure.identity import AzureCliCredential

# Requires: az login
credential = AzureCliCredential()

# Get token for SharePoint
token = credential.get_token("https://contoso.sharepoint.com/.default")
print(f"Token acquired via Azure CLI")
```

### AzurePowerShellCredential

```python
from azure.identity import AzurePowerShellCredential

# Requires: Connect-AzAccount
credential = AzurePowerShellCredential()

token = credential.get_token("https://graph.microsoft.com/.default")
```

### VisualStudioCodeCredential

```python
from azure.identity import VisualStudioCodeCredential

# Requires: VS Code Azure extension sign-in
credential = VisualStudioCodeCredential()

token = credential.get_token("https://graph.microsoft.com/.default")
```

### DefaultAzureCredential (Recommended)

```python
from azure.identity import DefaultAzureCredential

# Automatically tries credentials in order:
# 1. EnvironmentCredential
# 2. WorkloadIdentityCredential
# 3. ManagedIdentityCredential
# 4. AzureCliCredential
# 5. AzurePowerShellCredential
# 6. AzureDeveloperCliCredential

credential = DefaultAzureCredential()

# Works in Azure (managed identity) and locally (CLI/PowerShell)
token = credential.get_token("https://graph.microsoft.com/.default")
```

### Excluding Credentials

```python
from azure.identity import DefaultAzureCredential

# Exclude credentials you don't want
credential = DefaultAzureCredential(
    exclude_environment_credential=True,
    exclude_managed_identity_credential=True,  # Local dev only
    exclude_powershell_credential=True,
    exclude_visual_studio_code_credential=True,
    # Only use Azure CLI
)
```

### With SharePoint

```python
from azure.identity import AzureCliCredential
from office365.sharepoint.client_context import ClientContext

credential = AzureCliCredential()

def get_token():
    return credential.get_token("https://contoso.sharepoint.com/.default").token

ctx = ClientContext("https://contoso.sharepoint.com/sites/dev").with_access_token(get_token)

web = ctx.web.get().execute_query()
print(f"Site: {web.title}")
```

### Detecting Credential Type

```python
from azure.identity import (
    ChainedTokenCredential,
    AzureCliCredential,
    AzurePowerShellCredential,
    CredentialUnavailableError
)

def get_available_credential():
    """Get first available credential with logging."""
    
    # Try Azure CLI
    try:
        cred = AzureCliCredential()
        cred.get_token("https://management.azure.com/.default")
        print("Using Azure CLI credential")
        return cred
    except CredentialUnavailableError:
        pass
    
    # Try PowerShell
    try:
        cred = AzurePowerShellCredential()
        cred.get_token("https://management.azure.com/.default")
        print("Using Azure PowerShell credential")
        return cred
    except CredentialUnavailableError:
        pass
    
    raise RuntimeError("No credential available")
```

## 6. Gotchas and Quirks

### "az login" Required Before Use

```python
# Error: CredentialUnavailableError
# "Azure CLI not found or not logged in"

# Solution:
# $ az login
```

### Token Scope Format

```python
# Wrong - specific Graph scope
credential.get_token("User.Read")  # FAILS

# Correct - full URL with .default
credential.get_token("https://graph.microsoft.com/.default")
```

### Multiple Azure Accounts

If you have multiple Azure accounts, the CLI uses the default:

```bash
# Check current account
az account show

# List all accounts
az account list

# Switch account
az account set --subscription "Subscription Name"
```

### VS Code Credential Quirks

```python
# VS Code credential may fail if:
# 1. Azure Account extension not installed
# 2. Not signed in via the extension
# 3. VS Code not running when script runs

# Workaround: Use AzureCliCredential instead
```

### Tenant Selection

```bash
# Login to specific tenant
az login --tenant your-tenant-id

# Or for PowerShell
Connect-AzAccount -TenantId your-tenant-id
```

### DefaultAzureCredential in Docker

```python
# DefaultAzureCredential may be slow in Docker
# because it tries credentials that don't exist

# Solution: Explicitly exclude unavailable credentials
credential = DefaultAzureCredential(
    exclude_visual_studio_code_credential=True,
    exclude_shared_token_cache_credential=True
)
```

### Performance: Credential Caching

```python
# BAD - Creates credential per request
@app.get("/api/data")
async def get_data():
    cred = AzureCliCredential()  # Slow!
    token = cred.get_token(...)

# GOOD - Reuse credential
_credential = AzureCliCredential()

@app.get("/api/data")
async def get_data():
    token = _credential.get_token(...)  # Uses cached credential
```

### Environment-Specific Configuration

```python
import os

def create_credential():
    """Create appropriate credential for environment."""
    env = os.environ.get("ENVIRONMENT", "development")
    
    if env == "production":
        from azure.identity import ManagedIdentityCredential
        return ManagedIdentityCredential()
    elif env == "staging":
        from azure.identity import CertificateCredential
        return CertificateCredential(
            tenant_id=os.environ["AZURE_TENANT_ID"],
            client_id=os.environ["AZURE_CLIENT_ID"],
            certificate_path=os.environ["CERT_PATH"]
        )
    else:  # development
        from azure.identity import DefaultAzureCredential
        return DefaultAzureCredential(
            exclude_managed_identity_credential=True
        )
```

## Sources

**Primary:**
- SPAUTH-SC-MSFT-AZIDREADME: Azure Identity client library
- SPAUTH-SC-MSFT-CREDCHAINS: Credential chains

## Document History

**[2026-03-14 17:40]**
- Initial document created
- All development credential types documented
- Local development patterns included
