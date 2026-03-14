<DevSystem MarkdownTablesAllowed=true />

# INFO: SharePoint Authentication Mechanisms for Python

**Doc ID**: SPAUTH-IN01
**Goal**: Comprehensive reference for all SharePoint/Graph authentication mechanisms in Python
**Research Type**: MCPI (exhaustive)
**Timeline**: Created 2026-03-14

## Quick Reference Summary

### Authentication Methods at a Glance

**App-Only (No User Context):**
- **Certificate Credentials** - Azure AD app with X.509 certificate (RECOMMENDED for SharePoint)
- **Client Secret** - Azure AD app with secret string (NOT supported for SharePoint REST API)
- **Managed Identity** - Azure-hosted apps with system/user-assigned identity
- **Workload Identity** - Kubernetes pods with federated identity

**User Context (Delegated):**
- **Interactive Browser** - Opens browser, user logs in, redirect callback
- **Device Code** - User visits URL and enters code on any device
- **Authorization Code** - Web app redirect flow with PKCE
- **Username/Password** - Direct credentials (ROPC, legacy/deprecated)
- **On-Behalf-Of** - Token exchange for downstream APIs

**Development Tools:**
- **Azure CLI Credential** - Uses `az login` session
- **Azure PowerShell Credential** - Uses `Connect-AzAccount` session
- **VS Code Credential** - Uses Azure Account extension

### Python Libraries

- **azure-identity** - Azure Identity SDK (recommended for new development)
- **msal** - Microsoft Authentication Library (lower-level control)
- **Office365-REST-Python-Client** - SharePoint/Graph client with built-in auth

### Token Resources/Scopes

- **SharePoint REST API**: `https://{tenant}.sharepoint.com/.default`
- **Microsoft Graph API**: `https://graph.microsoft.com/.default`

## Table of Contents

1. Certificate Credentials (App-Only)
2. Client Secret (App-Only) 
3. Managed Identity
4. Interactive Browser (Delegated)
5. Device Code Flow (Delegated)
6. Authorization Code (Delegated)
7. Username/Password (Legacy)
8. On-Behalf-Of Flow
9. Development Tool Credentials
10. Office365-REST-Python-Client Methods
11. Permission Scopes Reference
12. Decision Guide
13. Sources

## 1. Certificate Credentials (App-Only)

**Use case:** Background services, daemons, automated processes without user interaction.

**SharePoint requirement:** Certificate-based authentication is MANDATORY for SharePoint app-only access. Client secrets are NOT supported for SharePoint REST API.

### Azure Identity SDK

```python
from azure.identity import CertificateCredential

credential = CertificateCredential(
    tenant_id="YOUR_TENANT_ID",
    client_id="YOUR_CLIENT_ID",
    certificate_path="/path/to/cert.pem",        # PEM file with private key
    # OR
    certificate_data=cert_bytes,                  # Certificate bytes
    password="cert_password"                      # If encrypted
)

# Get token for SharePoint
token = credential.get_token("https://contoso.sharepoint.com/.default")
```

### MSAL Python

```python
from msal import ConfidentialClientApplication

app = ConfidentialClientApplication(
    client_id="YOUR_CLIENT_ID",
    authority="https://login.microsoftonline.com/YOUR_TENANT_ID",
    client_credential={
        "thumbprint": "CERT_THUMBPRINT",
        "private_key": open("private_key.pem").read()
    }
)

result = app.acquire_token_for_client(
    scopes=["https://contoso.sharepoint.com/.default"]
)
token = result["access_token"]
```

### Office365-REST-Python-Client

```python
from office365.sharepoint.client_context import ClientContext

ctx = ClientContext(site_url).with_client_certificate(
    tenant=tenant_id,
    client_id=client_id,
    thumbprint=thumbprint,
    cert_path="/path/to/cert.pem"
)
```

### PFX to PEM Conversion

```python
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption

with open("cert.pfx", "rb") as f:
    pfx_data = f.read()

private_key, certificate, _ = pkcs12.load_key_and_certificates(
    pfx_data, 
    password.encode() if password else None
)

# Write PEM file
with open("cert.pem", "wb") as f:
    f.write(private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))
    f.write(certificate.public_bytes(Encoding.PEM))

# Get thumbprint
thumbprint = certificate.fingerprint(certificate.signature_hash_algorithm).hex().upper()
```

## 2. Client Secret (App-Only)

**Use case:** Microsoft Graph API only. Simple setup for non-SharePoint services.

**WARNING:** Client secrets do NOT work for SharePoint REST API (`/_api/`). SharePoint requires certificate authentication for app-only access.

### Azure Identity SDK

```python
from azure.identity import ClientSecretCredential

credential = ClientSecretCredential(
    tenant_id="YOUR_TENANT_ID",
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET"
)

# Works for Graph API
token = credential.get_token("https://graph.microsoft.com/.default")

# Does NOT work for SharePoint REST API - will get Access Denied
# token = credential.get_token("https://contoso.sharepoint.com/.default")  # FAILS
```

### MSAL Python

```python
from msal import ConfidentialClientApplication

app = ConfidentialClientApplication(
    client_id="YOUR_CLIENT_ID",
    authority="https://login.microsoftonline.com/YOUR_TENANT_ID",
    client_credential="YOUR_CLIENT_SECRET"
)

result = app.acquire_token_for_client(
    scopes=["https://graph.microsoft.com/.default"]
)
```

### Office365-REST-Python-Client

```python
from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext

# For SharePoint App-Only (legacy ACS model, NOT Azure AD)
credentials = ClientCredential(client_id, client_secret)
ctx = ClientContext(site_url).with_credentials(credentials)

# Note: This uses legacy SharePoint ACS, not Azure AD
# Requires: set-spotenant -DisableCustomAppAuthentication $false
```

## 3. Managed Identity

**Use case:** Azure-hosted applications (App Service, Functions, VMs, AKS) without storing credentials.

**Sites.Selected compatibility:** To use Managed Identity with `Sites.Selected` permission, you must grant the permission to the MI's service principal (not the app registration). Use Graph API or PowerShell: `New-MgSitePermission -SiteId {site-id} -Roles "write" -GrantedToIdentities @{application=@{id="{MI-object-id}"}}`.

**Supported Azure services:**
- Azure App Service and Azure Functions
- Azure Virtual Machines
- Azure Kubernetes Service (AKS)
- Azure Container Instances
- Azure Service Fabric
- Azure Arc
- Azure Cloud Shell

### System-Assigned Managed Identity

```python
from azure.identity import ManagedIdentityCredential

credential = ManagedIdentityCredential()

# Get token for SharePoint
token = credential.get_token("https://contoso.sharepoint.com/.default")
```

### User-Assigned Managed Identity

```python
from azure.identity import ManagedIdentityCredential

credential = ManagedIdentityCredential(
    client_id="USER_ASSIGNED_IDENTITY_CLIENT_ID"
)

token = credential.get_token("https://contoso.sharepoint.com/.default")
```

### DefaultAzureCredential (Development/Fallback)

Automatically tries multiple credential types in order. Best for local development; for production, use specific credentials per Decision Guide below.

```python
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()

# Tries in order:
# 1. EnvironmentCredential
# 2. WorkloadIdentityCredential
# 3. ManagedIdentityCredential
# 4. AzureCliCredential
# 5. AzurePowerShellCredential
# 6. AzureDeveloperCliCredential
# 7. InteractiveBrowserCredential (if enabled)

token = credential.get_token("https://contoso.sharepoint.com/.default")
```

### Integration with Office365-REST-Python-Client

```python
from azure.identity import ManagedIdentityCredential
from office365.sharepoint.client_context import ClientContext

credential = ManagedIdentityCredential()

def get_token():
    token = credential.get_token("https://contoso.sharepoint.com/.default")
    return token.token

ctx = ClientContext(site_url).with_access_token(get_token)
web = ctx.web.get().execute_query()
```

## 4. Interactive Browser (Delegated)

**Use case:** Desktop apps, web apps where user is present and has a browser.

**Production note:** For deployed apps, set `redirect_uri` to your actual app URL (e.g., `https://myapp.azurewebsites.net/auth/callback`), not localhost.

### Azure Identity SDK

```python
from azure.identity import InteractiveBrowserCredential

credential = InteractiveBrowserCredential(
    client_id="YOUR_CLIENT_ID",
    tenant_id="YOUR_TENANT_ID",
    redirect_uri="http://localhost:8400"  # Must match app registration
)

# Opens browser, user logs in, redirects back
token = credential.get_token("https://contoso.sharepoint.com/.default")
```

### With Login Hint

```python
credential = InteractiveBrowserCredential(
    client_id="YOUR_CLIENT_ID",
    tenant_id="YOUR_TENANT_ID",
    login_hint="user@contoso.com"  # Pre-fill username
)
```

### Office365-REST-Python-Client

```python
from office365.sharepoint.client_context import ClientContext

ctx = ClientContext(site_url).with_interactive(
    tenant_name_or_id="YOUR_TENANT_ID",
    client_id="YOUR_CLIENT_ID"
)

# Requires redirect URI configured as http://localhost in Azure Portal
web = ctx.web.get().execute_query()
```

### Token Caching

```python
from azure.identity import InteractiveBrowserCredential, TokenCachePersistenceOptions

credential = InteractiveBrowserCredential(
    client_id="YOUR_CLIENT_ID",
    tenant_id="YOUR_TENANT_ID",
    cache_persistence_options=TokenCachePersistenceOptions(
        name="my_app_cache",
        enable_persistence=True
    )
)
```

## 5. Device Code Flow (Delegated)

**Use case:** Headless servers, SSH sessions, CLI tools, IoT devices without local browser.

### Azure Identity SDK

```python
from azure.identity import DeviceCodeCredential

def prompt_callback(verification_uri, user_code, expires_on):
    print(f"Go to: {verification_uri}")
    print(f"Enter code: {user_code}")
    print(f"Expires: {expires_on}")

credential = DeviceCodeCredential(
    client_id="YOUR_CLIENT_ID",
    tenant_id="YOUR_TENANT_ID",
    prompt_callback=prompt_callback,
    timeout=300  # seconds to wait for user
)

token = credential.get_token("https://contoso.sharepoint.com/.default")
```

### MSAL Python

```python
from msal import PublicClientApplication

app = PublicClientApplication(
    client_id="YOUR_CLIENT_ID",
    authority="https://login.microsoftonline.com/YOUR_TENANT_ID"
)

flow = app.initiate_device_flow(
    scopes=["https://contoso.sharepoint.com/.default"]
)
print(flow["message"])  # Display to user

result = app.acquire_token_by_device_flow(flow)
token = result["access_token"]
```

### Integration with Office365-REST-Python-Client

```python
from azure.identity import DeviceCodeCredential
from office365.sharepoint.client_context import ClientContext

credential = DeviceCodeCredential(
    client_id="YOUR_CLIENT_ID",
    tenant_id="YOUR_TENANT_ID"
)

def get_token():
    return credential.get_token("https://contoso.sharepoint.com/.default").token

ctx = ClientContext(site_url).with_access_token(get_token)
```

## 6. Authorization Code Flow (Delegated)

**Use case:** Web applications with server-side code.

### MSAL Python (Web App)

```python
from msal import ConfidentialClientApplication

app = ConfidentialClientApplication(
    client_id="YOUR_CLIENT_ID",
    authority="https://login.microsoftonline.com/YOUR_TENANT_ID",
    client_credential="YOUR_CLIENT_SECRET"  # Or certificate
)

# Step 1: Get authorization URL
auth_url = app.get_authorization_request_url(
    scopes=["https://contoso.sharepoint.com/.default"],
    redirect_uri="https://yourapp.com/callback"
)
# Redirect user to auth_url

# Step 2: Exchange code for token (in callback handler)
result = app.acquire_token_by_authorization_code(
    code=request.args["code"],
    scopes=["https://contoso.sharepoint.com/.default"],
    redirect_uri="https://yourapp.com/callback"
)
token = result["access_token"]
```

### Azure Identity SDK

```python
from azure.identity import AuthorizationCodeCredential

credential = AuthorizationCodeCredential(
    tenant_id="YOUR_TENANT_ID",
    client_id="YOUR_CLIENT_ID",
    authorization_code="CODE_FROM_CALLBACK",
    redirect_uri="https://yourapp.com/callback",
    client_secret="YOUR_CLIENT_SECRET"  # Optional
)

token = credential.get_token("https://contoso.sharepoint.com/.default")
```

## 7. Username/Password (Legacy)

**WARNING:** This flow (ROPC - Resource Owner Password Credentials) is deprecated and NOT recommended. It does not support:
- Multi-factor authentication (MFA)
- Conditional access policies
- Federated authentication

### MSAL Python

```python
from msal import PublicClientApplication

app = PublicClientApplication(
    client_id="YOUR_CLIENT_ID",
    authority="https://login.microsoftonline.com/YOUR_TENANT_ID"
)

result = app.acquire_token_by_username_password(
    username="user@contoso.com",
    password="password",
    scopes=["https://contoso.sharepoint.com/.default"]
)
token = result["access_token"]
```

### Office365-REST-Python-Client

```python
from office365.runtime.auth.user_credential import UserCredential
from office365.sharepoint.client_context import ClientContext

credentials = UserCredential("user@contoso.com", "password")
ctx = ClientContext(site_url).with_credentials(credentials)

# Will fail if MFA is enabled
```

## 8. On-Behalf-Of Flow

**Use case:** Middle-tier API that needs to call downstream APIs on behalf of the user.

### MSAL Python

```python
from msal import ConfidentialClientApplication

app = ConfidentialClientApplication(
    client_id="MIDDLE_TIER_CLIENT_ID",
    authority="https://login.microsoftonline.com/YOUR_TENANT_ID",
    client_credential="YOUR_CLIENT_SECRET"
)

# user_token is the token received from the calling application
result = app.acquire_token_on_behalf_of(
    user_assertion=user_token,
    scopes=["https://contoso.sharepoint.com/.default"]
)
downstream_token = result["access_token"]
```

### Azure Identity SDK

```python
from azure.identity import OnBehalfOfCredential

credential = OnBehalfOfCredential(
    tenant_id="YOUR_TENANT_ID",
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    user_assertion=user_token
)

token = credential.get_token("https://contoso.sharepoint.com/.default")
```

## 9. Development Tool Credentials

### Azure CLI Credential

```python
from azure.identity import AzureCliCredential

# Requires: az login
credential = AzureCliCredential()
token = credential.get_token("https://contoso.sharepoint.com/.default")
```

### Azure PowerShell Credential

```python
from azure.identity import AzurePowerShellCredential

# Requires: Connect-AzAccount
credential = AzurePowerShellCredential()
token = credential.get_token("https://contoso.sharepoint.com/.default")
```

### Azure Developer CLI Credential

```python
from azure.identity import AzureDeveloperCliCredential

# Requires: azd auth login
credential = AzureDeveloperCliCredential()
token = credential.get_token("https://contoso.sharepoint.com/.default")
```

### Chained Credential (Custom Order)

```python
from azure.identity import ChainedTokenCredential, ManagedIdentityCredential, AzureCliCredential

credential = ChainedTokenCredential(
    ManagedIdentityCredential(),  # Try managed identity first
    AzureCliCredential()          # Fall back to Azure CLI
)

token = credential.get_token("https://contoso.sharepoint.com/.default")
```

## 10. Office365-REST-Python-Client Methods

### Summary of Auth Methods

| Method                             | Auth Type | Use Case              |
|------------------------------------|-----------|----------------------|
| `with_client_certificate()`        | App-Only  | Azure AD + Certificate |
| `with_credentials(ClientCredential)` | App-Only  | Legacy ACS model       |
| `with_credentials(UserCredential)` | Delegated | Username/password      |
| `with_interactive()`               | Delegated | Browser popup          |
| `with_access_token()`              | Any       | Custom token provider  |

### with_access_token (Universal Adapter)

Use any Azure Identity credential with Office365-REST-Python-Client:

```python
from azure.identity import DefaultAzureCredential
from office365.sharepoint.client_context import ClientContext

credential = DefaultAzureCredential()
resource = "https://contoso.sharepoint.com"

def token_provider():
    return credential.get_token(f"{resource}/.default").token

ctx = ClientContext(site_url).with_access_token(token_provider)
web = ctx.web.get().execute_query()
```

### Azure Environment Support

```python
from office365.azure_env import AzureEnvironment
from office365.sharepoint.client_context import ClientContext

ctx = ClientContext(
    site_url, 
    environment=AzureEnvironment.USGovernmentHigh
).with_credentials(credentials)
```

**Supported environments:**
- `AzureEnvironment.Default` - Azure Public Cloud
- `AzureEnvironment.USGovernment` - Azure US Government
- `AzureEnvironment.USGovernmentHigh` - Azure US Government High
- `AzureEnvironment.USGovernmentDoD` - Azure US Government DoD
- `AzureEnvironment.Germany` - Azure Germany
- `AzureEnvironment.China` - Azure China

## 11. Permission Scopes Reference

### SharePoint Permissions (Azure AD)

| Permission               | Type          | Description                     |
|--------------------------|---------------|----------------------------------|
| `Sites.Read.All`         | Delegated/App | Read all site collections        |
| `Sites.ReadWrite.All`    | Delegated/App | Read/write all site collections  |
| `Sites.Manage.All`       | Delegated/App | Create, edit, delete lists       |
| `Sites.FullControl.All`  | App only      | Full control all sites           |
| `Sites.Selected`         | App only      | Access to specific sites only    |

### Sites.Selected Permission Model

For granular per-site access (instead of tenant-wide):

1. Grant `Sites.Selected` application permission in Azure AD
2. Use Graph API or PowerShell to grant specific site access:

```http
POST https://graph.microsoft.com/v1.0/sites/{site-id}/permissions
Content-Type: application/json

{
  "roles": ["write"],
  "grantedToIdentities": [{
    "application": {
      "id": "{app-client-id}",
      "displayName": "My App"
    }
  }]
}
```

### Token Resource URLs

| API                        | Resource/Scope                             |
|----------------------------|--------------------------------------------|
| SharePoint REST (`/_api/`) | `https://{tenant}.sharepoint.com/.default` |
| Microsoft Graph            | `https://graph.microsoft.com/.default`     |
| SharePoint via Graph       | `https://graph.microsoft.com/.default`     |

**Note:** A token for `graph.microsoft.com` can access SharePoint via Graph endpoints (`/sites/...`), but NOT SharePoint REST API (`/_api/`). For REST API, you need a token scoped to the SharePoint resource.

## 12. Decision Guide

### Which Auth Method to Use?

```
Is a user present and signing in?
├─> YES: Delegated flow
│   ├─> Browser available on device?
│   │   ├─> YES: InteractiveBrowserCredential
│   │   └─> NO: DeviceCodeCredential
│   └─> Web app with redirect?
│       └─> YES: AuthorizationCodeCredential
│
└─> NO: App-only flow
    ├─> Running in Azure?
    │   ├─> YES: ManagedIdentityCredential (preferred)
    │   └─> NO: CertificateCredential
    └─> Which API?
        ├─> SharePoint REST: Certificate required
        └─> Graph API: Certificate or Secret
```

### Quick Recommendations

| Scenario                    | Recommended Credential                       |
|-----------------------------|----------------------------------------------|
| Azure App Service/Functions | `ManagedIdentityCredential`                  |
| Local development           | `DefaultAzureCredential` or `AzureCliCredential` |
| Web app with user login     | `InteractiveBrowserCredential`               |
| CLI tool                    | `DeviceCodeCredential`                       |
| Daemon/background service   | `CertificateCredential`                      |
| Middle-tier API             | `OnBehalfOfCredential`                       |

### Common Mistakes

**1. Using client secret for SharePoint REST API**
- Client secrets only work for Graph API
- SharePoint REST requires certificate authentication

**2. Wrong token resource**
- Graph endpoints need `graph.microsoft.com` token
- SharePoint REST needs `{tenant}.sharepoint.com` token

**3. Missing permissions**
- App permissions require admin consent
- Delegated permissions require user consent

**4. Not handling token refresh**
- Azure Identity SDK handles refresh automatically
- MSAL requires checking `result.get("access_token")` and re-acquiring

## Sources

### Microsoft Learn Documentation

- **SPAUTH-IN01-SC-MSLEARN-AZID**: Azure Identity client library for Python
  - https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme

- **SPAUTH-IN01-SC-MSLEARN-MSAL**: MSAL for Python overview
  - https://learn.microsoft.com/en-us/entra/msal/python/

- **SPAUTH-IN01-SC-MSLEARN-APPONLY**: Granting access via Entra ID App-Only
  - https://learn.microsoft.com/en-us/sharepoint/dev/solution-guidance/security-apponly-azuread

- **SPAUTH-IN01-SC-MSLEARN-DEVCRED**: DeviceCodeCredential class
  - https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.devicecodecredential

- **SPAUTH-IN01-SC-MSLEARN-MGDID**: ManagedIdentityCredential class
  - https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.managedidentitycredential

- **SPAUTH-IN01-SC-MSLEARN-DEFCRED**: DefaultAzureCredential class
  - https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential

- **SPAUTH-IN01-SC-MSLEARN-SELECTED**: Sites.Selected permissions overview
  - https://learn.microsoft.com/en-us/graph/permissions-selected-overview

### PyPI Packages

- **SPAUTH-IN01-SC-PYPI-AZID**: azure-identity
  - https://pypi.org/project/azure-identity/

- **SPAUTH-IN01-SC-PYPI-MSAL**: msal
  - https://pypi.org/project/msal/

- **SPAUTH-IN01-SC-PYPI-O365**: Office365-REST-Python-Client
  - https://pypi.org/project/Office365-REST-Python-Client/

### GitHub

- **SPAUTH-IN01-SC-GH-O365**: vgrem/Office365-REST-Python-Client
  - https://github.com/vgrem/Office365-REST-Python-Client

## Document History

**[2026-03-14 16:30]**
- Initial document created
- Added: 9 authentication mechanisms with Python examples
- Added: Office365-REST-Python-Client integration patterns
- Added: Permission scopes reference
- Added: Decision guide for auth method selection
- Added: Common mistakes section
