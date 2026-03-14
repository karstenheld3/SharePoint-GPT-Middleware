<DevSystem MarkdownTablesAllowed=true />

# INFO: Username/Password (ROPC) Authentication

**Doc ID**: SPAUTH-AM07
**Goal**: Detailed guide for username/password authentication (ROPC) - legacy and deprecated
**Version Scope**: MSAL Python 1.x, Microsoft Entra ID (2026)

**Depends on:**
- `__AUTH_MECHANISMS_SOURCES.md [SPAUTH-SOURCES]` for source references

## 1. Intended Scenario and Recommended Use

### DEPRECATED - Use Only for Legacy Migration

```
┌────────────────────────────────────────────────────────────────┐
│ ⚠️ WARNING: Resource Owner Password Credentials (ROPC) is      │
│ DEPRECATED and NOT RECOMMENDED for new applications.           │
│                                                                │
│ - Cannot support MFA                                           │
│ - Cannot support Conditional Access                            │
│ - Exposes credentials to the application                       │
│ - Microsoft may block in future                                │
└────────────────────────────────────────────────────────────────┘
```

### Extremely Limited Use Cases

Only consider ROPC when ALL of the following are true:

- **Legacy migration** - Migrating from old system that used username/password
- **No MFA requirement** - User account has MFA disabled
- **No Conditional Access** - Tenant has no CA policies blocking ROPC
- **Temporary measure** - Plan to migrate to proper auth flow
- **Fully trusted app** - App is internal and highly trusted

### When NOT to Use (Almost Always)

- **New applications** - Use any other method instead
- **MFA-enabled accounts** - ROPC cannot complete MFA
- **External/public apps** - Credential exposure risk
- **Conditional Access environments** - Will be blocked
- **SharePoint Online** - Often blocked by default

### Recommendation Level

| Scenario                                   | Recommendation                              |
|--------------------------------------------|---------------------------------------------|
| New applications                           | **DO NOT USE**                              |
| Multi-Factor Authentication environments   | **BLOCKED**                                 |
| Legacy migration (temporary)               | Acceptable with plan to migrate             |
| Automated testing                          | Consider, but service principal better      |

## 2. How to Use in FastAPI Azure Web App

### Architecture Warning

```
┌─────────────────────────────────────────────────────────────────┐
│ SECURITY WARNING                                                │
│                                                                 │
│ Using ROPC means your application handles user credentials:     │
│                                                                 │
│  User ──[username/password]──> Your App ──> Microsoft           │
│                                   │                             │
│                                   └── Credentials visible       │
│                                       to your code!             │
│                                                                 │
│ Better alternatives:                                            │
│ - Interactive Browser (user enters creds at Microsoft)          │
│ - Device Code (user enters creds on separate device)            │
│ - Certificate/Managed Identity (no user creds needed)           │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation (Legacy Systems Only)

```python
# app/auth/legacy_ropc.py
import os
from msal import PublicClientApplication
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class LegacyROPCService:
    """
    DEPRECATED: Username/password authentication.
    Only for legacy migration scenarios.
    """
    
    def __init__(self):
        self._client_id = os.environ["AZURE_CLIENT_ID"]
        self._tenant_id = os.environ["AZURE_TENANT_ID"]
        self._authority = f"https://login.microsoftonline.com/{self._tenant_id}"
        
        # ROPC requires PublicClientApplication
        self._app = PublicClientApplication(
            client_id=self._client_id,
            authority=self._authority
        )
        
        logger.warning(
            "ROPC authentication initialized - this is deprecated! "
            "Plan migration to modern auth."
        )
    
    def authenticate(self, username: str, password: str) -> dict:
        """
        Authenticate with username/password.
        
        WARNING: This method is deprecated and has security concerns.
        """
        result = self._app.acquire_token_by_username_password(
            username=username,
            password=password,
            scopes=["https://graph.microsoft.com/.default"]
        )
        
        if "error" in result:
            error = result.get("error")
            error_desc = result.get("error_description", "")
            
            if "AADSTS50076" in error_desc:
                raise HTTPException(
                    status_code=400,
                    detail="MFA required - ROPC cannot handle MFA. Use interactive login."
                )
            elif "AADSTS50079" in error_desc:
                raise HTTPException(
                    status_code=400,
                    detail="MFA enrollment required. Use interactive login."
                )
            elif "AADSTS53003" in error_desc:
                raise HTTPException(
                    status_code=400,
                    detail="Conditional Access policy blocked ROPC."
                )
            else:
                raise HTTPException(
                    status_code=401,
                    detail=f"Authentication failed: {error_desc}"
                )
        
        return result


# app/main.py
class LoginRequest(BaseModel):
    username: str
    password: str

app = FastAPI()
ropc_service = LegacyROPCService()

@app.post("/api/legacy/login")
async def legacy_login(request: LoginRequest):
    """
    DEPRECATED: Legacy username/password login.
    
    This endpoint exists only for migration purposes.
    New clients should use /auth/login (interactive).
    """
    logger.warning(f"ROPC login attempt for: {request.username}")
    
    result = ropc_service.authenticate(request.username, request.password)
    
    return {
        "access_token": result["access_token"],
        "expires_in": result.get("expires_in"),
        "warning": "This authentication method is deprecated"
    }
```

### Environment Variables

```bash
AZURE_TENANT_ID=12345678-1234-1234-1234-123456789012
AZURE_CLIENT_ID=abcdefab-1234-5678-abcd-abcdefabcdef
# No client secret needed for public client ROPC
```

## 3. Prerequisites

### Azure AD App Registration

1. **Create App Registration**
   - Azure Portal > Microsoft Entra ID > App registrations
   - Name: "Legacy Migration App"
   - Account type: Single tenant

2. **Enable Public Client**
   - App registration > Authentication
   - Advanced settings > Allow public client flows: **Yes**

3. **Enable ROPC (If Blocked)**
   - Some tenants block ROPC by default
   - May need admin to enable via PowerShell:
   ```powershell
   # Not recommended, but if required:
   Set-MsolCompanySettings -EnableROPCFlow $true
   ```

4. **User Account Requirements**
   - MFA must be **disabled** for the user
   - Conditional Access policies must not block ROPC
   - Password must not be expired

### Pre-Flight Check

```python
def check_ropc_compatibility(username: str) -> dict:
    """Check if ROPC is likely to work for this user."""
    issues = []
    
    # These are just warnings - actual check requires attempt
    warnings = [
        "MFA enabled on account will cause failure",
        "Conditional Access policies may block",
        "Password expiration will cause failure",
        "B2B/guest accounts may not work"
    ]
    
    return {
        "username": username,
        "likely_issues": warnings,
        "recommendation": "Use interactive authentication instead"
    }
```

## 4. Dependencies and Maintenance Problems

### Required Packages

```txt
# requirements.txt
msal>=1.26.0
fastapi>=0.100.0
```

### Maintenance Concerns

| Issue                              | Impact                                                   | Mitigation                                                        |
|------------------------------------|----------------------------------------------------------|-------------------------------------------------------------------|
| Multi-Factor Authentication rollout| **All Resource Owner Password Credentials breaks**       | Migrate to modern authentication before rollout                   |
| Conditional Access                 | Resource Owner Password Credentials blocked              | Exempt service accounts or migrate                                |
| Password expiration                | Authentication fails                                     | Use service accounts with no expiry                               |
| Microsoft deprecation              | May be disabled                                          | Plan migration timeline                                           |
| Credential exposure                | Security risk                                            | Audit access, use secrets management                              |

### Migration Path

```
Current State: ROPC
        │
        v
Step 1: Implement modern auth alongside ROPC
        │
        v
Step 2: Migrate clients to modern auth
        │
        v
Step 3: Monitor ROPC usage
        │
        v
Step 4: Remove ROPC endpoint
        │
        v
Target State: Interactive/Certificate/Managed Identity
```

## 5. Code Examples

### Basic MSAL ROPC

```python
from msal import PublicClientApplication

app = PublicClientApplication(
    client_id="your-client-id",
    authority="https://login.microsoftonline.com/your-tenant-id"
)

result = app.acquire_token_by_username_password(
    username="user@contoso.com",
    password="userpassword",
    scopes=["https://graph.microsoft.com/.default"]
)

if "access_token" in result:
    print(f"Token: {result['access_token'][:50]}...")
else:
    print(f"Error: {result.get('error_description')}")
```

### With Error Handling

```python
def ropc_login(username: str, password: str) -> str:
    """Attempt ROPC login with detailed error handling."""
    app = PublicClientApplication(
        client_id=os.environ["AZURE_CLIENT_ID"],
        authority=f"https://login.microsoftonline.com/{os.environ['AZURE_TENANT_ID']}"
    )
    
    result = app.acquire_token_by_username_password(
        username=username,
        password=password,
        scopes=["https://graph.microsoft.com/.default"]
    )
    
    if "access_token" in result:
        return result["access_token"]
    
    error = result.get("error", "unknown")
    desc = result.get("error_description", "")
    
    # Map common errors
    if "AADSTS50076" in desc or "AADSTS50079" in desc:
        raise ValueError("MFA required - cannot use username/password")
    elif "AADSTS53003" in desc:
        raise ValueError("Conditional Access blocked this login")
    elif "AADSTS50126" in desc:
        raise ValueError("Invalid username or password")
    elif "AADSTS50057" in desc:
        raise ValueError("Account is disabled")
    elif "AADSTS50055" in desc:
        raise ValueError("Password expired")
    else:
        raise ValueError(f"Login failed: {desc}")
```

### SharePoint Access (If Not Blocked)

```python
from office365.sharepoint.client_context import ClientContext

def get_sharepoint_via_ropc(username: str, password: str, site_url: str):
    """
    Get SharePoint context using ROPC.
    Note: Often blocked by SharePoint policies.
    """
    app = PublicClientApplication(
        client_id=os.environ["AZURE_CLIENT_ID"],
        authority=f"https://login.microsoftonline.com/{os.environ['AZURE_TENANT_ID']}"
    )
    
    result = app.acquire_token_by_username_password(
        username=username,
        password=password,
        scopes=[f"{site_url.split('/sites')[0]}/.default"]
    )
    
    if "error" in result:
        raise ValueError(result.get("error_description"))
    
    ctx = ClientContext(site_url).with_access_token(
        lambda: result["access_token"]
    )
    return ctx
```

## 6. Gotchas and Quirks

### MFA Always Breaks ROPC

```python
# If user has MFA enabled, you'll get:
# AADSTS50076: Due to a configuration change made by your administrator,
# or because you moved to a new location, you must use multi-factor
# authentication to access...

# There is NO workaround - user must complete MFA interactively
```

### Conditional Access Can Block Silently

Conditional Access policies can block ROPC without clear error messages. Check for:
- Named location restrictions
- Device compliance requirements
- Risk-based policies

### Password Changes Break Cached Flows

Unlike token-based auth, password changes immediately break ROPC:

```python
# Day 1: Password = "OldPassword123"
# ROPC works

# Day 2: User changes password to "NewPassword456"
# ROPC with old password fails immediately
# No refresh token mechanism
```

### B2B/Guest Accounts Often Fail

Guest users (B2B) often cannot use ROPC:

```python
# Home tenant: contoso.com
# Guest in: fabrikam.com

# This often fails:
result = app.acquire_token_by_username_password(
    username="guest@contoso.com",
    password="...",
    scopes=["https://graph.microsoft.com/.default"]
)
# Error: AADSTS50020 or AADSTS90072
```

### Rate Limiting / Lockout

Microsoft applies rate limiting to password attempts:

```python
# Too many failed attempts = account lockout
# Typically: 10 failed attempts in 60 seconds

# Implement backoff:
import time

MAX_RETRIES = 3
for attempt in range(MAX_RETRIES):
    result = app.acquire_token_by_username_password(...)
    if "error" not in result:
        break
    if "AADSTS50053" in result.get("error_description", ""):
        # Account locked
        raise ValueError("Account locked due to too many failed attempts")
    time.sleep(2 ** attempt)  # Exponential backoff
```

### Federation Complications

Federated identities (ADFS, PingFederate, etc.) may not support ROPC:

```python
# Error: AADSTS50126 with federated user
# The identity provider doesn't support password auth

# Only cloud-only accounts reliably support ROPC
```

## Sources

**Primary:**
- SPAUTH-SC-RFC-6749: OAuth 2.0 specification (ROPC grant)
- SPAUTH-SC-MSFT-PROTOCOLS: Microsoft identity protocols

**Note:** Microsoft does not provide extensive ROPC documentation because it's deprecated.

## Document History

**[2026-03-14 17:30]**
- Initial document created
- Heavily emphasized deprecated status
- Migration guidance included
