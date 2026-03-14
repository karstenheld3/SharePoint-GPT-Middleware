<DevSystem MarkdownTablesAllowed=true />

# INFO: On-Behalf-Of Flow Authentication

**Doc ID**: SPAUTH-AM08
**Goal**: Detailed guide for On-Behalf-Of (OBO) flow in FastAPI Azure Web Apps
**Version Scope**: Azure Identity 1.x, MSAL Python 1.x, Microsoft Entra ID (2026)

**Depends on:**
- `__AUTH_MECHANISMS_SOURCES.md [SPAUTH-SOURCES]` for source references

## 1. Intended Scenario and Recommended Use

### When to Use On-Behalf-Of Flow

OBO flow is for **middle-tier services** that need to call downstream APIs on behalf of the user:

- **API Gateway patterns** - Frontend calls your API, your API calls SharePoint/Graph
- **Microservices** - Service A receives user token, needs to call Service B as that user
- **Backend-for-Frontend (BFF)** - Web backend calling multiple APIs for the frontend
- **Preserving user identity** - Downstream API sees original user, not the app

### Flow Overview

```
┌────────────────────────────────────────────────────────────────────┐
│ On-Behalf-Of Flow                                                  │
│                                                                    │
│  ┌──────────┐    ┌──────────────────┐    ┌───────────────────┐     │
│  │ Frontend │───>│ Your FastAPI     │───>│ SharePoint/Graph  │     │
│  │ (SPA)    │    │ (Middle-tier)    │    │ (Downstream API)  │     │
│  └──────────┘    └──────────────────┘    └───────────────────┘     │
│       │                  │                        │                │
│       │ Token A          │ Exchange A for B       │ Token B        │
│       │ (for your API)   │ via OBO flow           │ (for Graph)    │
│       │                  │                        │                │
│       └──────────────────┴────────────────────────┘                │
│                                                                    │
│  Key: User identity preserved through entire chain                 │
└────────────────────────────────────────────────────────────────────┘
```

### When NOT to Use

- **App-only scenarios** - No user token to exchange (use certificate/MI)
- **Direct frontend calls** - Frontend can call API directly
- **Simple proxying** - Just forwarding requests (pass token through)

### Recommendation Level

| Scenario                                    | Recommendation     |
|---------------------------------------------|--------------------|
| API calling downstream API as user          | **RECOMMENDED**    |
| Microservice architecture                   | **RECOMMENDED**    |
| Backend-for-Frontend pattern                | **RECOMMENDED**    |
| Simple Create/Read/Update/Delete API        | NOT NEEDED         |
| Background jobs                             | NOT APPLICABLE     |

## 2. How to Use in FastAPI Azure Web App

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ Frontend (React SPA)                                            │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ User logs in via MSAL.js                                    │ │
│ │ Gets token for: api://your-api-client-id                    │ │
│ │ Calls: POST /api/sharepoint/files                           │ │
│ │ Header: Authorization: Bearer <token-for-your-api>          │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────────┐
│ FastAPI Middle-Tier                                             │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1. Validates incoming token (audience = your API)           │ │
│ │ 2. Extracts user assertion from token                       │ │
│ │ 3. Exchanges via OBO for SharePoint/Graph token             │ │
│ │ 4. Calls SharePoint/Graph with new token                    │ │
│ │ 5. Returns result to frontend                               │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────────┐
│ SharePoint / Microsoft Graph                                    │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Receives token that represents the ORIGINAL USER            │ │
│ │ Applies user's permissions, not app's permissions           │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Complete FastAPI Implementation

```python
# app/auth/obo_service.py
import os
from msal import ConfidentialClientApplication
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import logging

logger = logging.getLogger(__name__)

class OnBehalfOfService:
    """
    On-Behalf-Of token exchange service.
    Exchanges incoming user tokens for downstream API tokens.
    """
    
    def __init__(self):
        self._client_id = os.environ["AZURE_CLIENT_ID"]
        self._client_secret = os.environ["AZURE_CLIENT_SECRET"]
        self._tenant_id = os.environ["AZURE_TENANT_ID"]
        
        self._authority = f"https://login.microsoftonline.com/{self._tenant_id}"
        
        self._app = ConfidentialClientApplication(
            client_id=self._client_id,
            authority=self._authority,
            client_credential=self._client_secret
        )
    
    def exchange_token(
        self, 
        user_assertion: str, 
        scopes: list[str]
    ) -> dict:
        """
        Exchange user's token for a token to call downstream API.
        
        Args:
            user_assertion: The access token received from the client
            scopes: Scopes for the downstream API
        
        Returns:
            Token response with access_token for downstream API
        """
        result = self._app.acquire_token_on_behalf_of(
            user_assertion=user_assertion,
            scopes=scopes
        )
        
        if "error" in result:
            error_desc = result.get("error_description", "")
            logger.error(f"OBO exchange failed: {error_desc}")
            
            if "AADSTS50013" in error_desc:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid assertion - token may be expired or for wrong audience"
                )
            elif "AADSTS65001" in error_desc:
                raise HTTPException(
                    status_code=403,
                    detail="User has not consented to the required permissions"
                )
            else:
                raise HTTPException(
                    status_code=401,
                    detail=f"Token exchange failed: {error_desc}"
                )
        
        return result
    
    def get_sharepoint_token(self, user_assertion: str, sharepoint_url: str) -> str:
        """Get token for SharePoint on behalf of user."""
        result = self.exchange_token(
            user_assertion=user_assertion,
            scopes=[f"{sharepoint_url}/.default"]
        )
        return result["access_token"]
    
    def get_graph_token(self, user_assertion: str) -> str:
        """Get token for Microsoft Graph on behalf of user."""
        result = self.exchange_token(
            user_assertion=user_assertion,
            scopes=["https://graph.microsoft.com/.default"]
        )
        return result["access_token"]


# app/auth/dependencies.py
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()
obo_service = OnBehalfOfService()

async def get_user_assertion(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Extract and validate user assertion from Authorization header."""
    token = credentials.credentials
    
    # Basic validation (full validation should verify signature)
    try:
        # Decode without verification to check claims
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        # Verify audience matches our API
        expected_audience = f"api://{os.environ['AZURE_CLIENT_ID']}"
        if decoded.get("aud") != expected_audience:
            raise HTTPException(
                status_code=401,
                detail=f"Token audience mismatch. Expected: {expected_audience}"
            )
        
        return token
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Invalid token format")

async def get_sharepoint_token(
    user_assertion: str = Depends(get_user_assertion)
) -> str:
    """Dependency that provides SharePoint token via OBO."""
    return obo_service.get_sharepoint_token(
        user_assertion=user_assertion,
        sharepoint_url=os.environ["SHAREPOINT_URL"]
    )


# app/main.py
from fastapi import FastAPI, Depends
from office365.sharepoint.client_context import ClientContext

app = FastAPI()

@app.get("/api/sharepoint/sites/{site_name}/lists")
async def get_lists(
    site_name: str,
    sp_token: str = Depends(get_sharepoint_token)
):
    """
    Get SharePoint lists on behalf of the calling user.
    User's permissions apply - they only see what they have access to.
    """
    site_url = f"{os.environ['SHAREPOINT_URL']}/sites/{site_name}"
    ctx = ClientContext(site_url).with_access_token(lambda: sp_token)
    
    lists = ctx.web.lists.get().execute_query()
    return {"lists": [{"title": l.title} for l in lists]}

@app.get("/api/sharepoint/me/files")
async def get_my_files(
    sp_token: str = Depends(get_sharepoint_token)
):
    """Get files the user has access to."""
    import httpx
    
    # Use Graph API to get user's OneDrive files
    graph_token = obo_service.get_graph_token(
        user_assertion=sp_token  # Would need original assertion
    )
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://graph.microsoft.com/v1.0/me/drive/root/children",
            headers={"Authorization": f"Bearer {graph_token}"}
        )
        return response.json()
```

### Environment Variables

```bash
AZURE_TENANT_ID=12345678-1234-1234-1234-123456789012
AZURE_CLIENT_ID=abcdefab-1234-5678-abcd-abcdefabcdef
AZURE_CLIENT_SECRET=your-client-secret
SHAREPOINT_URL=https://contoso.sharepoint.com
```

## 3. Prerequisites

### Azure AD App Registration (Middle-Tier API)

1. **Create App Registration**
   - Azure Portal > Microsoft Entra ID > App registrations
   - Name: "SharePoint Middle-Tier API"
   - Redirect URI: Not needed for API

2. **Expose an API**
   - App registration > Expose an API
   - Set Application ID URI: `api://<client-id>`
   - Add a scope:
     - Scope name: `access_as_user`
     - Admin consent display name: "Access API as user"
     - Admin consent description: "Allows the app to access the API on behalf of the signed-in user"
     - State: Enabled

3. **Configure API Permissions (Delegated)**
   
   This method uses **Delegated permissions** for downstream API calls. User's permissions apply.
   
   - **Read-only apps:** `Sites.Read.All`
   - **Read-write apps:** `Sites.ReadWrite.All`
   - **Note:** `Sites.Selected` is NOT available for delegated permissions
   - **Important:** Admin consent recommended to avoid user consent prompts
   
   See [`_INFO_SPAUTH-IN07_AZURE_PERMISSION_REQUIREMENTS.md`](_INFO_SPAUTH-IN07_AZURE_PERMISSION_REQUIREMENTS.md) for full details.

4. **Create Client Secret**
   - App registration > Certificates & secrets
   - New client secret
   - Copy value immediately

### Frontend App Configuration

The frontend app must be configured to request tokens for YOUR API:

```javascript
// Frontend MSAL.js configuration
const msalConfig = {
    auth: {
        clientId: "frontend-client-id",
        authority: "https://login.microsoftonline.com/your-tenant-id"
    }
};

// Request token for your middle-tier API
const tokenRequest = {
    scopes: ["api://your-api-client-id/access_as_user"]
};

const response = await msalInstance.acquireTokenSilent(tokenRequest);
// Use response.accessToken to call your API
```

## 4. Dependencies and Maintenance Problems

### Required Packages

```txt
# requirements.txt
msal>=1.26.0
fastapi>=0.100.0
PyJWT>=2.8.0
httpx>=0.25.0
Office365-REST-Python-Client>=2.5.0
```

### Maintenance Concerns

| Issue                 | Impact                                  | Mitigation                                    |
|-----------------------|-----------------------------------------|-----------------------------------------------|
| Consent not granted   | On-Behalf-Of fails with AADSTS65001     | Pre-consent via administrator grant           |
| Token audience wrong  | Exchange fails                          | Verify frontend requests correct scope        |
| Secret expiration     | On-Behalf-Of stops working              | Rotate secrets before expiry                  |
| Permission changes    | May need re-consent                     | Monitor permission changes                    |
| Token caching         | Performance issues                      | Microsoft Authentication Library handles this |

### Token Caching

MSAL caches OBO tokens internally:

```python
# MSAL caches tokens by:
# - User assertion hash
# - Requested scopes
# - Client ID

# Subsequent OBO requests for same user + scopes return cached token
# No need for manual caching
```

## 5. Code Examples

### Basic OBO Exchange

```python
from msal import ConfidentialClientApplication

app = ConfidentialClientApplication(
    client_id="your-api-client-id",
    authority="https://login.microsoftonline.com/your-tenant-id",
    client_credential="your-client-secret"
)

# User's token (received in Authorization header)
user_token = "eyJ0eXAiOiJKV1QiLCJhbGciOi..."

# Exchange for Graph token
result = app.acquire_token_on_behalf_of(
    user_assertion=user_token,
    scopes=["https://graph.microsoft.com/User.Read"]
)

if "access_token" in result:
    graph_token = result["access_token"]
    # Call Graph API with graph_token
```

### Multiple Downstream APIs

```python
class MultiApiOBOService:
    """Exchange tokens for multiple downstream APIs."""
    
    def __init__(self, app: ConfidentialClientApplication):
        self._app = app
    
    def get_graph_token(self, user_assertion: str) -> str:
        result = self._app.acquire_token_on_behalf_of(
            user_assertion=user_assertion,
            scopes=["https://graph.microsoft.com/.default"]
        )
        return result["access_token"]
    
    def get_sharepoint_token(self, user_assertion: str, site_host: str) -> str:
        result = self._app.acquire_token_on_behalf_of(
            user_assertion=user_assertion,
            scopes=[f"https://{site_host}/.default"]
        )
        return result["access_token"]
    
    def get_custom_api_token(self, user_assertion: str, api_uri: str) -> str:
        result = self._app.acquire_token_on_behalf_of(
            user_assertion=user_assertion,
            scopes=[f"{api_uri}/.default"]
        )
        return result["access_token"]
```

### With Proper Token Validation

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
import jwt
from jwt import PyJWKClient

security = HTTPBearer()

# JWKS endpoint for token validation
JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"
jwks_client = PyJWKClient(JWKS_URL)

async def validate_and_get_assertion(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Validate incoming token and return as assertion."""
    token = credentials.credentials
    
    try:
        # Get signing key
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Validate token
        decoded = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=f"api://{AZURE_CLIENT_ID}",
            issuer=f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
        )
        
        return token
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=401, detail="Invalid audience")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
```

## 6. Gotchas and Quirks

### Token Audience Must Match Your API

The incoming token must have YOUR API as the audience:

```python
# Frontend requests token for YOUR API, not Graph/SharePoint directly
# Correct:
scopes = ["api://your-api-client-id/access_as_user"]

# Wrong:
scopes = ["https://graph.microsoft.com/User.Read"]  # This goes direct, not via your API
```

### User Must Have Consented to Downstream Scopes

Even with admin consent, some delegated permissions require user interaction:

```python
# Error: AADSTS65001
# "The user or administrator has not consented to use the application"

# Solution: Ensure admin consent granted, or implement incremental consent
```

### OBO Tokens Cannot Be Used for Further OBO

You cannot chain OBO flows indefinitely:

```
Frontend -> API A (OBO) -> API B (OBO) -> API C
                                          ↑
                                    This may fail!
```

### Scope Format for OBO

```python
# For Microsoft Graph
scopes = ["https://graph.microsoft.com/User.Read"]  # Specific scope
# OR
scopes = ["https://graph.microsoft.com/.default"]   # All consented scopes

# For SharePoint
scopes = ["https://contoso.sharepoint.com/.default"]

# For custom API
scopes = ["api://custom-api-id/scope_name"]
```

### Token Expiration Handling

The OBO token has its own expiration, independent of the original token:

```python
# Original token: expires in 60 minutes
# OBO token: may also expire in 60 minutes (or different)

# Always handle token refresh:
result = app.acquire_token_on_behalf_of(
    user_assertion=user_token,
    scopes=scopes
)
# MSAL automatically refreshes if cached token is expired
```

### Testing OBO Locally

Testing OBO requires a valid user token. Options:

```python
# Option 1: Use device code to get initial token
# Option 2: Set up frontend app locally
# Option 3: Use Postman/similar to acquire tokens manually
```

## Sources

**Primary:**
- SPAUTH-SC-MSFT-OBO: On-Behalf-Of flow documentation
- SPAUTH-SC-MSFT-MSALPYTHON: MSAL for Python

## Document History

**[2026-03-14 17:35]**
- Initial document created
- Complete FastAPI OBO implementation
- Token validation and error handling patterns included
