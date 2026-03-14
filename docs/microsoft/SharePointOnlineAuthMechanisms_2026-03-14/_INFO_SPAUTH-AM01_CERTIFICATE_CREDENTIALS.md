<DevSystem MarkdownTablesAllowed=true />

# INFO: Certificate Credentials Authentication

**Doc ID**: SPAUTH-AM01
**Goal**: Detailed guide for certificate-based authentication in FastAPI Azure Web Apps
**Version Scope**: Azure Identity 1.x, MSAL Python 1.x, Microsoft Entra ID (2026)

**Depends on:**
- `__AUTH_MECHANISMS_SOURCES.md [SPAUTH-SOURCES]` for source references

## 1. Intended Scenario and Recommended Use

### When to Use Certificate Credentials

Certificate credentials are the **mandatory** authentication method for SharePoint Online app-only access. Use this when:

- **Background services/daemons** - Automated processes running without user interaction
- **Scheduled jobs** - Crawlers, sync tasks, data processing pipelines
- **API-to-API communication** - Your FastAPI app calling SharePoint on behalf of the application itself
- **SharePoint REST API access** - Any `/_api/` endpoint requires certificate auth for app-only
- **High-security environments** - Certificate private keys never leave the server

### When NOT to Use

- **User-delegated scenarios** - When you need to act on behalf of a specific user (use Interactive/Auth Code instead)
- **Quick prototyping** - Setup overhead is higher than other methods
- **Environments without secure key storage** - Don't use if you can't protect the private key

### Recommendation Level

| Scenario | Recommendation |
|----------|----------------|
| SharePoint REST API (app-only) | **REQUIRED** - Only supported method |
| Microsoft Graph API (app-only) | **RECOMMENDED** - More secure than secrets |
| Azure-hosted apps | Consider Managed Identity first, then certificate |
| On-premises apps | **RECOMMENDED** - Best option for non-Azure |

## 2. How to Use in FastAPI Azure Web App

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│ Azure App Service                                       │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ FastAPI Application                                 │ │
│ │                                                     │ │
│ │  ┌─────────────┐    ┌──────────────────────────┐   │ │
│ │  │ Endpoint    │───>│ SharePointService        │   │ │
│ │  │ /api/crawl  │    │ - CertificateCredential  │   │ │
│ │  └─────────────┘    │ - Token acquisition      │   │ │
│ │                     │ - SharePoint API calls   │   │ │
│ │                     └──────────────────────────┘   │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Certificate stored in:                                  │
│ - Azure Key Vault (recommended)                         │
│ - App Service Certificate Store                         │
│ - File system (not recommended)                         │
└─────────────────────────────────────────────────────────┘
```

### Complete FastAPI Implementation

```python
# app/services/sharepoint_auth.py
import os
from functools import lru_cache
from azure.identity import CertificateCredential
from azure.keyvault.secrets import SecretClient
from office365.sharepoint.client_context import ClientContext
import logging

logger = logging.getLogger(__name__)

class SharePointAuthService:
    """
    Singleton service for SharePoint certificate authentication.
    Reuses credential instance to leverage token caching.
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
        self._sharepoint_url = os.environ["SHAREPOINT_URL"]
        
        # Option 1: Certificate from file (local dev)
        cert_path = os.environ.get("CERT_PATH")
        if cert_path and os.path.exists(cert_path):
            self._credential = CertificateCredential(
                tenant_id=self._tenant_id,
                client_id=self._client_id,
                certificate_path=cert_path,
                password=os.environ.get("CERT_PASSWORD")
            )
            logger.info("Initialized certificate credential from file")
            return
        
        # Option 2: Certificate from Key Vault (production)
        keyvault_url = os.environ.get("AZURE_KEYVAULT_URL")
        cert_name = os.environ.get("KEYVAULT_CERT_NAME")
        if keyvault_url and cert_name:
            self._credential = self._load_from_keyvault(keyvault_url, cert_name)
            logger.info("Initialized certificate credential from Key Vault")
            return
        
        raise ValueError("No certificate configuration found")
    
    def _load_from_keyvault(self, keyvault_url: str, cert_name: str):
        """Load certificate from Azure Key Vault."""
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.certificates import CertificateClient
        
        # Use managed identity to access Key Vault
        kv_credential = DefaultAzureCredential()
        cert_client = CertificateClient(keyvault_url, kv_credential)
        
        # Get certificate with private key
        cert = cert_client.get_certificate(cert_name)
        secret_client = SecretClient(keyvault_url, kv_credential)
        secret = secret_client.get_secret(cert_name)
        
        # Parse PFX from base64
        import base64
        pfx_bytes = base64.b64decode(secret.value)
        
        return CertificateCredential(
            tenant_id=self._tenant_id,
            client_id=self._client_id,
            certificate_data=pfx_bytes
        )
    
    def get_token(self) -> str:
        """Get access token for SharePoint."""
        scope = f"{self._sharepoint_url}/.default"
        token = self._credential.get_token(scope)
        return token.token
    
    def get_client_context(self, site_url: str) -> ClientContext:
        """Get SharePoint ClientContext with certificate auth."""
        return ClientContext(site_url).with_access_token(self.get_token)


# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from app.services.sharepoint_auth import SharePointAuthService

app = FastAPI()

def get_sharepoint_service() -> SharePointAuthService:
    """Dependency injection for SharePoint service."""
    return SharePointAuthService()

@app.get("/api/sites/{site_name}/lists")
async def get_lists(
    site_name: str,
    sp_service: SharePointAuthService = Depends(get_sharepoint_service)
):
    try:
        site_url = f"https://contoso.sharepoint.com/sites/{site_name}"
        ctx = sp_service.get_client_context(site_url)
        
        lists = ctx.web.lists.get().execute_query()
        return {"lists": [{"title": l.title} for l in lists]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup():
    """Initialize SharePoint service at startup."""
    try:
        SharePointAuthService()
    except Exception as e:
        logger.error(f"Failed to initialize SharePoint auth: {e}")
        raise
```

### Environment Variables

```bash
# Required
AZURE_TENANT_ID=12345678-1234-1234-1234-123456789012
AZURE_CLIENT_ID=abcdefab-1234-5678-abcd-abcdefabcdef
SHAREPOINT_URL=https://contoso.sharepoint.com

# Option 1: File-based certificate (local dev)
CERT_PATH=/app/certs/app_cert.pem
CERT_PASSWORD=optional_password

# Option 2: Key Vault certificate (production)
AZURE_KEYVAULT_URL=https://mykeyvault.vault.azure.net
KEYVAULT_CERT_NAME=sharepoint-app-cert
```

## 3. Prerequisites

### Azure AD App Registration

1. **Create App Registration**
   - Azure Portal > Microsoft Entra ID > App registrations > New registration
   - Name: "SharePoint Crawler App" (or similar)
   - Supported account types: Single tenant (recommended)
   - No redirect URI needed for app-only

2. **Generate Certificate**
   ```powershell
   # Create self-signed certificate
   $cert = New-SelfSignedCertificate `
       -Subject "CN=SharePointCrawlerApp" `
       -CertStoreLocation "Cert:\CurrentUser\My" `
       -KeyExportPolicy Exportable `
       -KeySpec Signature `
       -KeyLength 2048 `
       -KeyAlgorithm RSA `
       -HashAlgorithm SHA256 `
       -NotAfter (Get-Date).AddYears(2)
   
   # Export PFX (with private key)
   $pwd = ConvertTo-SecureString -String "YourPassword" -Force -AsPlainText
   Export-PfxCertificate -Cert $cert -FilePath ".\app_cert.pfx" -Password $pwd
   
   # Export CER (public key only, for Azure upload)
   Export-Certificate -Cert $cert -FilePath ".\app_cert.cer"
   ```

3. **Upload Certificate to App Registration**
   - App registration > Certificates & secrets > Certificates > Upload certificate
   - Upload the `.cer` file (public key)
   - Note the **Thumbprint** displayed

4. **Configure API Permissions**
   - App registration > API permissions > Add a permission
   - Microsoft Graph or SharePoint (depending on API used)
   - Application permissions (not delegated)
   - Common permissions:
     - `Sites.Read.All` - Read all sites
     - `Sites.ReadWrite.All` - Read/write all sites
     - `Sites.Selected` - Access to specific sites only (recommended)
   - Click "Grant admin consent"

5. **For Sites.Selected: Grant Per-Site Access**
   ```powershell
   # Using Microsoft Graph PowerShell
   Connect-MgGraph -Scopes "Sites.FullControl.All"
   
   $siteId = "contoso.sharepoint.com,<site-guid>,<web-guid>"
   $appId = "your-app-client-id"
   
   New-MgSitePermission -SiteId $siteId -Body @{
       roles = @("write")
       grantedToIdentities = @(@{
           application = @{
               id = $appId
               displayName = "SharePoint Crawler App"
           }
       })
   }
   ```

### Azure Key Vault Setup (Production)

1. **Create Key Vault**
   - Azure Portal > Key Vaults > Create
   - Enable RBAC authorization (recommended)

2. **Import Certificate**
   - Key Vault > Certificates > Generate/Import
   - Import the PFX file
   - Note the certificate name

3. **Grant App Service Access**
   - Key Vault > Access control (IAM)
   - Add role assignment: "Key Vault Secrets User"
   - Assign to App Service's managed identity

## 4. Dependencies and Maintenance Problems

### Required Packages

```txt
# requirements.txt
azure-identity>=1.15.0
azure-keyvault-certificates>=4.8.0
azure-keyvault-secrets>=4.8.0
msal>=1.26.0
Office365-REST-Python-Client>=2.5.0
cryptography>=41.0.0
```

### Maintenance Concerns

| Issue | Impact | Mitigation |
|-------|--------|------------|
| Certificate expiration | **Auth fails completely** | Set calendar reminder 30 days before expiry; implement monitoring |
| Key Vault access revoked | Cannot retrieve certificate | Use managed identity; monitor access policies |
| Private key compromise | Security breach | Use Key Vault; never commit to source control |
| Certificate rotation | Temporary auth failures | Add new cert first, update app, remove old cert |
| PEM format issues | Auth failures | Ensure PEM includes private key; check encoding |

### Certificate Rotation Strategy

```python
# Support multiple certificates during rotation
class CertificateRotationService:
    def __init__(self):
        self.credentials = []
        
        # Load primary certificate
        primary = self._load_cert("primary-cert")
        self.credentials.append(primary)
        
        # Load secondary (during rotation)
        secondary = self._load_cert("secondary-cert")
        if secondary:
            self.credentials.append(secondary)
    
    def get_token(self, scope: str) -> str:
        """Try credentials in order until one succeeds."""
        for cred in self.credentials:
            try:
                return cred.get_token(scope).token
            except Exception:
                continue
        raise Exception("All certificates failed")
```

### Monitoring Recommendations

```python
# Health check endpoint
@app.get("/health/sharepoint")
async def health_check():
    try:
        service = SharePointAuthService()
        token = service.get_token()
        
        # Decode token to check expiry
        import jwt
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp = datetime.fromtimestamp(decoded["exp"])
        
        return {
            "status": "healthy",
            "token_expires": exp.isoformat(),
            "expires_in_minutes": (exp - datetime.utcnow()).total_seconds() / 60
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## 5. Code Examples

### Basic Token Acquisition

```python
from azure.identity import CertificateCredential

credential = CertificateCredential(
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    certificate_path="./cert.pem"
)

token = credential.get_token("https://contoso.sharepoint.com/.default")
print(f"Token: {token.token[:50]}...")
print(f"Expires: {token.expires_on}")
```

### With MSAL for More Control

```python
from msal import ConfidentialClientApplication

app = ConfidentialClientApplication(
    client_id="your-client-id",
    authority="https://login.microsoftonline.com/your-tenant-id",
    client_credential={
        "thumbprint": "ABCD1234...",
        "private_key": open("private_key.pem").read()
    }
)

# Check cache first
result = app.acquire_token_silent(
    scopes=["https://contoso.sharepoint.com/.default"],
    account=None
)

if not result:
    result = app.acquire_token_for_client(
        scopes=["https://contoso.sharepoint.com/.default"]
    )

if "access_token" in result:
    print(f"Token acquired: {result['access_token'][:50]}...")
else:
    print(f"Error: {result.get('error_description')}")
```

### SharePoint Operations

```python
from office365.sharepoint.client_context import ClientContext

def get_sharepoint_context(site_url: str) -> ClientContext:
    credential = CertificateCredential(
        tenant_id=os.environ["AZURE_TENANT_ID"],
        client_id=os.environ["AZURE_CLIENT_ID"],
        certificate_path=os.environ["CERT_PATH"]
    )
    
    def token_provider():
        return credential.get_token(
            f"https://{site_url.split('/')[2]}/.default"
        ).token
    
    return ClientContext(site_url).with_access_token(token_provider)

# List all lists
ctx = get_sharepoint_context("https://contoso.sharepoint.com/sites/hr")
lists = ctx.web.lists.get().execute_query()
for lst in lists:
    print(f"- {lst.properties['Title']}")

# Get items from a list
list_obj = ctx.web.lists.get_by_title("Documents")
items = list_obj.items.get().execute_query()
```

### Error Handling

```python
from azure.identity import CredentialUnavailableError
from azure.core.exceptions import ClientAuthenticationError

def acquire_token_safely():
    try:
        credential = CertificateCredential(
            tenant_id=os.environ["AZURE_TENANT_ID"],
            client_id=os.environ["AZURE_CLIENT_ID"],
            certificate_path=os.environ["CERT_PATH"]
        )
        return credential.get_token("https://contoso.sharepoint.com/.default")
    
    except FileNotFoundError as e:
        logger.error(f"Certificate file not found: {e}")
        raise
    
    except CredentialUnavailableError as e:
        logger.error(f"Credential unavailable: {e}")
        raise
    
    except ClientAuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        # Check common causes
        if "AADSTS700027" in str(e):
            logger.error("Invalid certificate signature - check thumbprint")
        elif "AADSTS700016" in str(e):
            logger.error("Application not found - check client_id")
        raise
```

## 6. Gotchas and Quirks

### Common Pitfalls

1. **PEM file must contain private key**
   ```
   -----BEGIN PRIVATE KEY-----
   MIIEvg...
   -----END PRIVATE KEY-----
   -----BEGIN CERTIFICATE-----
   MIID...
   -----END CERTIFICATE-----
   ```
   If you only have the certificate (no private key), auth will fail.

2. **Thumbprint format varies**
   - Azure Portal shows: `AB:CD:EF:12:34...` (colon-separated)
   - MSAL expects: `ABCDEF1234...` (no colons, uppercase)
   - Always strip colons and uppercase the thumbprint

3. **PFX password handling**
   ```python
   # Wrong - passing empty string for no password
   certificate_data=pfx_bytes, password=""  # May fail
   
   # Correct - pass None for no password
   certificate_data=pfx_bytes, password=None
   ```

4. **Certificate must be uploaded BEFORE use**
   - Azure AD validates the signature against uploaded certificates
   - If certificate not uploaded, you get: `AADSTS700027`

5. **SharePoint requires certificate, not secret**
   ```python
   # This FAILS for SharePoint REST API
   credential = ClientSecretCredential(...)
   token = credential.get_token("https://contoso.sharepoint.com/.default")
   # Token acquired but API returns 401/403
   ```

6. **Token resource URL must match exactly**
   ```python
   # Wrong
   credential.get_token("https://contoso.sharepoint.com")  # Missing /.default
   
   # Correct
   credential.get_token("https://contoso.sharepoint.com/.default")
   ```

7. **Self-signed certificates work but...**
   - Must be RSA 2048-bit or higher
   - Must use SHA256 or higher for signature
   - Validity period matters (don't set too long or Azure may reject)

8. **Clock skew issues**
   - Certificate auth uses timestamps
   - If server clock is off by >5 minutes, auth may fail
   - Use NTP on all servers

### Performance Considerations

```python
# BAD - Creates new credential per request
@app.get("/api/data")
async def get_data():
    credential = CertificateCredential(...)  # New instance each time
    token = credential.get_token(...)  # Bypasses cache
    ...

# GOOD - Reuse credential instance
_credential = None

def get_credential():
    global _credential
    if _credential is None:
        _credential = CertificateCredential(...)
    return _credential

@app.get("/api/data")
async def get_data():
    credential = get_credential()  # Reuses cached instance
    token = credential.get_token(...)  # Uses token cache
    ...
```

## Sources

**Primary:**
- SPAUTH-SC-MSFT-CERTCREDS: Certificate credentials documentation
- SPAUTH-SC-MSFT-AZIDREADME: Azure Identity client library

**Related Documents:**
- `_INFO_SPAUTH-IN03_CRYPTO_OPERATIONS.md` - Certificate thumbprint calculation, PFX conversion

## Document History

**[2026-03-14 17:00]**
- Initial document created
- FastAPI integration patterns documented
- Prerequisites and maintenance guidance added
