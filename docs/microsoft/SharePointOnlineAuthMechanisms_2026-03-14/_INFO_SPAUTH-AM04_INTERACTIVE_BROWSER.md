<DevSystem MarkdownTablesAllowed=true />

# INFO: Interactive Browser Authentication

**Doc ID**: SPAUTH-AM04
**Goal**: Detailed guide for interactive browser authentication in FastAPI Azure Web Apps
**Version Scope**: Azure Identity 1.x, MSAL Python 1.x, Microsoft Entra ID (2026)

**Depends on:**
- `__AUTH_MECHANISMS_SOURCES.md [SPAUTH-SOURCES]` for source references

## 1. Intended Scenario and Recommended Use

### When to Use Interactive Browser

Interactive browser authentication is for **delegated** scenarios where a user is present:

- **Admin tools/dashboards** - User logs in to perform administrative tasks
- **User-initiated operations** - Operations that should run as the signed-in user
- **Personal account fallback** - When managed identity isn't available
- **Development/testing** - Quick auth without setting up service principals
- **Web applications with UI** - Users accessing via browser

### User Flow

```
┌──────────────┐    ┌─────────────────┐    ┌──────────────────┐
│ User clicks  │───>│ Browser opens   │───>│ User logs in     │
│ "Login"      │    │ login.microsoft │    │ (may have MFA)   │
└──────────────┘    └─────────────────┘    └──────────────────┘
                                                   │
                    ┌─────────────────┐            │
                    │ Token returned  │<───────────┘
                    │ to application  │
                    └─────────────────┘
```

### When NOT to Use

- **Background services** - No user present (use certificate/managed identity)
- **Automated jobs** - Cannot interact with browser (use app-only)
- **Headless servers** - No browser available (use device code)
- **API-to-API calls** - Use app credentials or on-behalf-of

### Recommendation Level

| Scenario | Recommendation |
|----------|----------------|
| Admin dashboard (user logs in) | **RECOMMENDED** |
| User-specific operations | **RECOMMENDED** |
| Local development | Good for testing |
| Production background jobs | **NOT RECOMMENDED** |
| Azure App Service (API only) | **NOT RECOMMENDED** |

## 2. How to Use in FastAPI Azure Web App

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ User's Browser                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ FastAPI Web UI                                              │ │
│ │                                                             │ │
│ │  ┌───────────┐    ┌──────────────────────────────────────┐  │ │
│ │  │ Login Btn │───>│ /auth/login endpoint                 │  │ │
│ │  └───────────┘    │ Redirects to Microsoft login         │  │ │
│ │                   └──────────────────────────────────────┘  │ │
│ │                              │                              │ │
│ │                              v                              │ │
│ │  ┌──────────────────────────────────────────────────────┐   │ │
│ │  │ Microsoft Login Page (login.microsoftonline.com)     │   │ │
│ │  │ User enters credentials, completes MFA               │   │ │
│ │  └──────────────────────────────────────────────────────┘   │ │
│ │                              │                              │ │
│ │                              v                              │ │
│ │  ┌──────────────────────────────────────────────────────┐   │ │
│ │  │ /auth/callback - Receives auth code                  │   │ │
│ │  │ Exchanges for tokens, stores in session              │   │ │
│ │  └──────────────────────────────────────────────────────┘   │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Complete FastAPI Implementation

```python
# app/auth/interactive_auth.py
import os
import secrets
from urllib.parse import urlencode
from msal import ConfidentialClientApplication
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import logging

logger = logging.getLogger(__name__)

class InteractiveAuthService:
    """
    MSAL-based interactive authentication for FastAPI.
    Uses Authorization Code flow with PKCE.
    """
    
    def __init__(self):
        self._client_id = os.environ["AZURE_CLIENT_ID"]
        self._client_secret = os.environ.get("AZURE_CLIENT_SECRET")
        self._tenant_id = os.environ["AZURE_TENANT_ID"]
        self._redirect_uri = os.environ["AUTH_REDIRECT_URI"]
        
        self._authority = f"https://login.microsoftonline.com/{self._tenant_id}"
        self._scopes = [
            "https://contoso.sharepoint.com/Sites.Read.All",
            "offline_access"  # For refresh tokens
        ]
        
        self._app = ConfidentialClientApplication(
            client_id=self._client_id,
            authority=self._authority,
            client_credential=self._client_secret
        )
    
    def get_auth_url(self, state: str) -> str:
        """Generate authorization URL for user login."""
        result = self._app.get_authorization_request_url(
            scopes=self._scopes,
            state=state,
            redirect_uri=self._redirect_uri
        )
        return result
    
    def acquire_token_by_code(self, code: str) -> dict:
        """Exchange authorization code for tokens."""
        result = self._app.acquire_token_by_authorization_code(
            code=code,
            scopes=self._scopes,
            redirect_uri=self._redirect_uri
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=400,
                detail=f"Token error: {result.get('error_description')}"
            )
        
        return result
    
    def get_token_silent(self, account: dict) -> dict:
        """Get token from cache or refresh."""
        accounts = self._app.get_accounts()
        matching = [a for a in accounts if a.get("username") == account.get("username")]
        
        if not matching:
            return None
        
        result = self._app.acquire_token_silent(
            scopes=self._scopes,
            account=matching[0]
        )
        return result


# app/main.py
from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.environ["SESSION_SECRET"])

auth_service = InteractiveAuthService()

@app.get("/auth/login")
async def login(request: Request):
    """Initiate login flow."""
    state = secrets.token_urlsafe(32)
    request.session["auth_state"] = state
    
    auth_url = auth_service.get_auth_url(state)
    return RedirectResponse(url=auth_url)

@app.get("/auth/callback")
async def auth_callback(request: Request, code: str = None, state: str = None, error: str = None):
    """Handle OAuth callback."""
    if error:
        raise HTTPException(status_code=400, detail=f"Auth error: {error}")
    
    # Verify state
    expected_state = request.session.get("auth_state")
    if state != expected_state:
        raise HTTPException(status_code=400, detail="Invalid state")
    
    # Exchange code for tokens
    result = auth_service.acquire_token_by_code(code)
    
    # Store in session
    request.session["user"] = {
        "name": result.get("id_token_claims", {}).get("name"),
        "email": result.get("id_token_claims", {}).get("preferred_username"),
        "access_token": result["access_token"]
    }
    
    return RedirectResponse(url="/")

@app.get("/auth/logout")
async def logout(request: Request):
    """Clear session and logout."""
    request.session.clear()
    return RedirectResponse(url="/")

def get_current_user(request: Request):
    """Dependency to get current user."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@app.get("/api/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Get current user info."""
    return {"name": user["name"], "email": user["email"]}

@app.get("/api/sharepoint/lists")
async def get_lists(
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Get SharePoint lists as current user."""
    from office365.sharepoint.client_context import ClientContext
    
    token = user["access_token"]
    ctx = ClientContext("https://contoso.sharepoint.com/sites/hr").with_access_token(lambda: token)
    
    lists = ctx.web.lists.get().execute_query()
    return {"lists": [{"title": l.title} for l in lists]}
```

### Using Azure Identity (Simpler for Desktop/CLI)

```python
from azure.identity import InteractiveBrowserCredential

# For desktop apps or CLI tools
credential = InteractiveBrowserCredential(
    client_id="your-client-id",
    tenant_id="your-tenant-id",
    redirect_uri="http://localhost:8400"
)

# Opens browser, user logs in
token = credential.get_token("https://contoso.sharepoint.com/.default")
```

### Environment Variables

```bash
AZURE_TENANT_ID=12345678-1234-1234-1234-123456789012
AZURE_CLIENT_ID=abcdefab-1234-5678-abcd-abcdefabcdef
AZURE_CLIENT_SECRET=your-secret  # Optional for public clients
AUTH_REDIRECT_URI=https://myapp.azurewebsites.net/auth/callback
SESSION_SECRET=random-secret-for-session-encryption
```

## 3. Prerequisites

### Azure AD App Registration

1. **Create App Registration**
   - Azure Portal > Microsoft Entra ID > App registrations > New registration
   - Name: "SharePoint User App"
   - Supported account types: Single tenant (or multi-tenant if needed)
   - Redirect URI: `https://myapp.azurewebsites.net/auth/callback`

2. **Configure Redirect URIs**
   - App registration > Authentication > Platform configurations
   - Add platform: Web
   - Redirect URIs:
     - `https://myapp.azurewebsites.net/auth/callback` (production)
     - `http://localhost:8000/auth/callback` (development)
   - Enable "ID tokens" under Implicit grant

3. **Configure API Permissions (Delegated)**
   
   This method uses **Delegated permissions** (user context). User's SharePoint permissions apply.
   
   - **Read-only apps:** `Sites.Read.All`
   - **Read-write apps:** `Sites.ReadWrite.All`
   - **Note:** `Sites.Selected` is NOT available for delegated permissions
   
   See [`_INFO_SPAUTH-IN07_AZURE_PERMISSION_REQUIREMENTS.md`](_INFO_SPAUTH-IN07_AZURE_PERMISSION_REQUIREMENTS.md) for full details.

4. **Create Client Secret (For Confidential Client)**
   - App registration > Certificates & secrets > Client secrets
   - New client secret
   - Copy the value immediately

### Token Configuration (Optional)

- App registration > Token configuration
- Add optional claims for ID token:
  - `email`
  - `preferred_username`
  - `name`

## 4. Dependencies and Maintenance Problems

### Required Packages

```txt
# requirements.txt
azure-identity>=1.15.0
msal>=1.26.0
fastapi>=0.100.0
starlette>=0.27.0
itsdangerous>=2.1.0  # For session middleware
python-multipart>=0.0.6  # For form handling
```

### Maintenance Concerns

| Issue                          | Impact                              | Mitigation                                                        |
|--------------------------------|-------------------------------------|-------------------------------------------------------------------|
| Redirect URI mismatch          | Authentication fails completely     | Keep Uniform Resource Identifiers in sync between code and Azure  |
| Session expiration             | User logged out unexpectedly        | Implement refresh token handling                                  |
| Consent prompt changes         | Users see unexpected prompts        | Pre-consent via administrator grant                               |
| Multi-Factor Authentication    | Additional friction for users       | Document user flow                                                |
| Token expiration               | API calls fail                      | Implement silent token refresh                                    |

### Token Refresh Implementation

```python
async def get_valid_token(request: Request) -> str:
    """Get valid token, refreshing if needed."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if token is expired
    import jwt
    from datetime import datetime
    
    try:
        decoded = jwt.decode(
            user["access_token"],
            options={"verify_signature": False}
        )
        exp = datetime.fromtimestamp(decoded["exp"])
        
        # Refresh if expires within 5 minutes
        if exp < datetime.utcnow() + timedelta(minutes=5):
            result = auth_service.get_token_silent(user)
            if result and "access_token" in result:
                user["access_token"] = result["access_token"]
                request.session["user"] = user
        
        return user["access_token"]
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=401, detail="Session expired")
```

## 5. Code Examples

### Basic Interactive Login (Azure Identity)

```python
from azure.identity import InteractiveBrowserCredential

credential = InteractiveBrowserCredential(
    client_id="your-client-id",
    tenant_id="your-tenant-id",
    redirect_uri="http://localhost:8400"
)

# Opens browser, user authenticates
token = credential.get_token("https://contoso.sharepoint.com/.default")
print(f"Token acquired for user")
```

### With Login Hint

```python
credential = InteractiveBrowserCredential(
    client_id="your-client-id",
    tenant_id="your-tenant-id",
    login_hint="user@contoso.com"  # Pre-fill username
)
```

### Using Office365-REST-Python-Client

```python
from office365.sharepoint.client_context import ClientContext

ctx = ClientContext("https://contoso.sharepoint.com/sites/hr").with_interactive(
    tenant_name_or_id="your-tenant-id",
    client_id="your-client-id"
)

# Opens browser for login
web = ctx.web.get().execute_query()
print(f"Site: {web.title}")
```

### Full MSAL Flow

```python
from msal import PublicClientApplication

app = PublicClientApplication(
    client_id="your-client-id",
    authority="https://login.microsoftonline.com/your-tenant-id"
)

# Check cache first
accounts = app.get_accounts()
if accounts:
    result = app.acquire_token_silent(
        scopes=["https://contoso.sharepoint.com/.default"],
        account=accounts[0]
    )
else:
    result = None

# Interactive login if needed
if not result:
    result = app.acquire_token_interactive(
        scopes=["https://contoso.sharepoint.com/.default"]
    )

if "access_token" in result:
    print(f"Logged in as: {result.get('id_token_claims', {}).get('name')}")
else:
    print(f"Error: {result.get('error_description')}")
```

### Token Caching with Persistence

```python
from msal import PublicClientApplication, SerializableTokenCache
import os

cache_file = "token_cache.json"

# Load cache
cache = SerializableTokenCache()
if os.path.exists(cache_file):
    cache.deserialize(open(cache_file).read())

app = PublicClientApplication(
    client_id="your-client-id",
    authority="https://login.microsoftonline.com/your-tenant-id",
    token_cache=cache
)

# Acquire token...
result = app.acquire_token_interactive(scopes=["..."])

# Save cache
if cache.has_state_changed:
    with open(cache_file, "w") as f:
        f.write(cache.serialize())
```

## 6. Gotchas and Quirks

### Redirect URI Must Match Exactly

```python
# In Azure Portal: http://localhost:8000/auth/callback

# WRONG - trailing slash
redirect_uri = "http://localhost:8000/auth/callback/"  # FAILS

# WRONG - different port
redirect_uri = "http://localhost:8080/auth/callback"  # FAILS

# CORRECT - exact match
redirect_uri = "http://localhost:8000/auth/callback"
```

### Production Redirect URI Must Be HTTPS

```python
# Development (OK)
redirect_uri = "http://localhost:8000/auth/callback"

# Production (MUST be HTTPS)
redirect_uri = "https://myapp.azurewebsites.net/auth/callback"
```

### Popup Blockers

Interactive browser may open a popup. Users with popup blockers will have issues:

```python
# Consider providing instructions
@app.get("/auth/login-help")
async def login_help():
    return HTMLResponse("""
        <h1>Login Help</h1>
        <p>If login doesn't work, please:</p>
        <ol>
            <li>Disable popup blockers for this site</li>
            <li>Try a different browser</li>
            <li>Contact IT support</li>
        </ol>
    """)
```

### Session Security

```python
# WRONG - insecure session
app.add_middleware(SessionMiddleware, secret_key="hardcoded")

# CORRECT - secure random secret
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ["SESSION_SECRET"],
    same_site="lax",
    https_only=True  # In production
)
```

### MFA and Conditional Access

Users may be prompted for MFA. This is normal and handled by Microsoft's login page:

```python
# No special code needed - Microsoft handles MFA
# But inform users this may happen
```

### Token vs ID Token Claims

```python
# Access token - for API calls (don't parse in client)
access_token = result["access_token"]

# ID token claims - for user info
claims = result.get("id_token_claims", {})
user_name = claims.get("name")
user_email = claims.get("preferred_username")
```

### Multi-Tenant Considerations

```python
# Single tenant (your org only)
authority = "https://login.microsoftonline.com/your-tenant-id"

# Multi-tenant (any Azure AD)
authority = "https://login.microsoftonline.com/common"

# Consumer accounts (personal Microsoft)
authority = "https://login.microsoftonline.com/consumers"
```

## Sources

**Primary:**
- SPAUTH-SC-MSFT-AUTHCODE: Authorization code flow
- SPAUTH-SC-MSFT-MSALPYTHON: MSAL for Python
- SPAUTH-SC-MSFT-AZIDREADME: Azure Identity client library

## Document History

**[2026-03-14 17:15]**
- Initial document created
- FastAPI OAuth integration documented
- Session handling and token refresh patterns included
