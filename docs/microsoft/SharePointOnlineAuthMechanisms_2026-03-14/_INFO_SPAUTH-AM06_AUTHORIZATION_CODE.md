<DevSystem MarkdownTablesAllowed=true />

# INFO: Authorization Code Flow Authentication

**Doc ID**: SPAUTH-AM06
**Goal**: Detailed guide for authorization code flow in FastAPI Azure Web Apps
**Version Scope**: Azure Identity 1.x, MSAL Python 1.x, Microsoft Entra ID (2026)

**Depends on:**
- `__AUTH_MECHANISMS_SOURCES.md [SPAUTH-SOURCES]` for source references

## 1. Intended Scenario and Recommended Use

### When to Use Authorization Code Flow

Authorization code flow is the **standard OAuth 2.0 flow** for web applications:

- **Web applications** - Server-rendered or SPA with backend
- **User login scenarios** - When user identity is needed
- **Delegated permissions** - Acting on behalf of a user
- **Secure token handling** - Tokens handled server-side

### Flow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ Authorization Code Flow with PKCE                               │
│                                                                 │
│  1. User clicks "Login"                                         │
│     │                                                           │
│     ▼                                                           │
│  2. App redirects to Microsoft login                            │
│     (includes code_challenge for PKCE)                          │
│     │                                                           │
│     ▼                                                           │
│  3. User authenticates (may include MFA)                        │
│     │                                                           │
│     ▼                                                           │
│  4. Microsoft redirects back with authorization code            │
│     │                                                           │
│     ▼                                                           │
│  5. App exchanges code for tokens (with code_verifier)          │
│     (This happens server-side - code never exposed to browser)  │
│     │                                                           │
│     ▼                                                           │
│  6. App receives access_token, refresh_token, id_token          │
└─────────────────────────────────────────────────────────────────┘
```

### Authorization Code vs Interactive Browser

| Aspect           | Authorization Code                     | Interactive Browser                 |
|------------------|----------------------------------------|-------------------------------------|
| Use case         | Web applications with backend          | Desktop and command-line apps       |
| Token exchange   | Server-side                            | Client-side                         |
| Security         | Higher (uses code_verifier)            | Good                                |
| Refresh tokens   | Yes                                    | Yes                                 |
| Implementation   | More complex                           | Simpler                             |

### When NOT to Use

- **Background services** - No user present (use app-only)
- **Simple CLI tools** - Use device code instead
- **Desktop apps** - Interactive browser is simpler

### Recommendation Level

| Scenario                              | Recommendation            |
|---------------------------------------|---------------------------|
| Web application with user login       | **STRONGLY RECOMMENDED**  |
| Single Page Application with backend  | **RECOMMENDED**           |
| FastAPI with user interface           | **RECOMMENDED**           |
| API-only services                     | NOT APPLICABLE            |

## 2. How to Use in FastAPI Azure Web App

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ Browser                                                         │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1. User visits /login                                       │ │
│ │    Redirected to login.microsoftonline.com                  │ │
│ │                                                             │ │
│ │ 2. User authenticates with Microsoft                        │ │
│ │                                                             │ │
│ │ 3. Redirected to /auth/callback?code=xxx                    │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ FastAPI Backend                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ /auth/callback handler:                                     │ │
│ │ 4. Receives authorization code                              │ │
│ │ 5. Exchanges code for tokens (server-side, secure)          │ │
│ │ 6. Stores tokens in session                                 │ │
│ │ 7. Redirects user to protected page                         │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Complete FastAPI Implementation

```python
# app/auth/oauth.py
import os
import secrets
from urllib.parse import urlencode
from typing import Optional
from msal import ConfidentialClientApplication
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
import logging

logger = logging.getLogger(__name__)

class OAuthService:
    """
    OAuth 2.0 Authorization Code Flow with PKCE for FastAPI.
    """
    
    def __init__(self):
        self._client_id = os.environ["AZURE_CLIENT_ID"]
        self._client_secret = os.environ["AZURE_CLIENT_SECRET"]
        self._tenant_id = os.environ["AZURE_TENANT_ID"]
        self._redirect_uri = os.environ["AUTH_REDIRECT_URI"]
        
        self._authority = f"https://login.microsoftonline.com/{self._tenant_id}"
        self._scopes = [
            "User.Read",
            "Sites.Read.All",
            "offline_access"
        ]
        
        self._app = ConfidentialClientApplication(
            client_id=self._client_id,
            authority=self._authority,
            client_credential=self._client_secret
        )
    
    def build_auth_url(self, state: str, code_challenge: str = None) -> str:
        """Build authorization URL with PKCE."""
        params = {
            "client_id": self._client_id,
            "response_type": "code",
            "redirect_uri": self._redirect_uri,
            "scope": " ".join(self._scopes),
            "state": state,
            "response_mode": "query"
        }
        
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"
        
        return f"{self._authority}/oauth2/v2.0/authorize?{urlencode(params)}"
    
    def exchange_code_for_tokens(
        self, 
        code: str, 
        code_verifier: str = None
    ) -> dict:
        """Exchange authorization code for tokens."""
        result = self._app.acquire_token_by_authorization_code(
            code=code,
            scopes=self._scopes,
            redirect_uri=self._redirect_uri,
            # code_verifier=code_verifier  # MSAL handles PKCE internally
        )
        
        if "error" in result:
            logger.error(f"Token error: {result.get('error_description')}")
            raise HTTPException(
                status_code=400,
                detail=f"Authentication failed: {result.get('error_description')}"
            )
        
        return result
    
    def refresh_token(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token."""
        # MSAL handles this via acquire_token_silent with accounts
        accounts = self._app.get_accounts()
        if accounts:
            return self._app.acquire_token_silent(
                scopes=self._scopes,
                account=accounts[0]
            )
        return None
    
    def get_user_info(self, access_token: str) -> dict:
        """Get user info from Microsoft Graph."""
        import httpx
        
        response = httpx.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        response.raise_for_status()
        return response.json()


# app/main.py
from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
import hashlib
import base64

app = FastAPI()
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.environ["SESSION_SECRET"],
    same_site="lax",
    https_only=os.environ.get("HTTPS_ONLY", "true").lower() == "true"
)

oauth = OAuthService()

def generate_pkce_pair():
    """Generate PKCE code verifier and challenge."""
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()
    return code_verifier, code_challenge

@app.get("/")
async def home(request: Request):
    user = request.session.get("user")
    if user:
        return HTMLResponse(f"""
            <h1>Welcome, {user['name']}</h1>
            <p>Email: {user['email']}</p>
            <a href="/logout">Logout</a>
        """)
    return HTMLResponse("""
        <h1>SharePoint App</h1>
        <a href="/login">Login with Microsoft</a>
    """)

@app.get("/login")
async def login(request: Request):
    """Initiate OAuth login."""
    state = secrets.token_urlsafe(32)
    code_verifier, code_challenge = generate_pkce_pair()
    
    request.session["oauth_state"] = state
    request.session["code_verifier"] = code_verifier
    
    auth_url = oauth.build_auth_url(state, code_challenge)
    return RedirectResponse(url=auth_url)

@app.get("/auth/callback")
async def auth_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
    error_description: str = None
):
    """Handle OAuth callback."""
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"Auth error: {error_description or error}"
        )
    
    # Verify state
    expected_state = request.session.get("oauth_state")
    if not state or state != expected_state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # Exchange code for tokens
    code_verifier = request.session.get("code_verifier")
    result = oauth.exchange_code_for_tokens(code, code_verifier)
    
    # Get user info
    user_info = oauth.get_user_info(result["access_token"])
    
    # Store in session
    request.session["user"] = {
        "name": user_info.get("displayName"),
        "email": user_info.get("mail") or user_info.get("userPrincipalName"),
        "id": user_info.get("id")
    }
    request.session["tokens"] = {
        "access_token": result["access_token"],
        "refresh_token": result.get("refresh_token"),
        "expires_in": result.get("expires_in")
    }
    
    # Clear OAuth state
    request.session.pop("oauth_state", None)
    request.session.pop("code_verifier", None)
    
    return RedirectResponse(url="/")

@app.get("/logout")
async def logout(request: Request):
    """Clear session and optionally logout from Microsoft."""
    request.session.clear()
    
    # Optionally redirect to Microsoft logout
    # logout_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/logout"
    # return RedirectResponse(url=logout_url)
    
    return RedirectResponse(url="/")

def require_auth(request: Request):
    """Dependency to require authentication."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@app.get("/api/me")
async def get_me(user: dict = Depends(require_auth)):
    """Protected endpoint - get current user."""
    return user

@app.get("/api/sharepoint/sites")
async def get_sites(request: Request, user: dict = Depends(require_auth)):
    """Get SharePoint sites as current user."""
    tokens = request.session.get("tokens", {})
    access_token = tokens.get("access_token")
    
    if not access_token:
        raise HTTPException(status_code=401, detail="No access token")
    
    import httpx
    response = httpx.get(
        "https://graph.microsoft.com/v1.0/sites?search=*",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    response.raise_for_status()
    return response.json()
```

### Environment Variables

```bash
AZURE_TENANT_ID=12345678-1234-1234-1234-123456789012
AZURE_CLIENT_ID=abcdefab-1234-5678-abcd-abcdefabcdef
AZURE_CLIENT_SECRET=your-client-secret
AUTH_REDIRECT_URI=https://myapp.azurewebsites.net/auth/callback
SESSION_SECRET=random-64-char-secret-for-session-encryption
HTTPS_ONLY=true
```

## 3. Prerequisites

### Azure AD App Registration

1. **Create App Registration**
   - Azure Portal > Microsoft Entra ID > App registrations > New registration
   - Name: "SharePoint Web App"
   - Supported account types: Single tenant
   - Redirect URI: Web > `https://myapp.azurewebsites.net/auth/callback`

2. **Configure Platform**
   - App registration > Authentication > Platform configurations
   - Add platform: Web
   - Redirect URIs:
     - `https://myapp.azurewebsites.net/auth/callback` (production)
     - `http://localhost:8000/auth/callback` (development)
   - Enable: "ID tokens"

3. **Create Client Secret**
   - App registration > Certificates & secrets > Client secrets > New
   - Copy value immediately

4. **Configure API Permissions (Delegated)**
   
   This method uses **Delegated permissions** (user context). User's SharePoint permissions apply.
   
   - **Read-only apps:** `Sites.Read.All` + `offline_access`
   - **Read-write apps:** `Sites.ReadWrite.All` + `offline_access`
   - **Note:** `Sites.Selected` is NOT available for delegated permissions
   
   See [`_INFO_SPAUTH-IN07_AZURE_PERMISSION_REQUIREMENTS.md`](_INFO_SPAUTH-IN07_AZURE_PERMISSION_REQUIREMENTS.md) for full details.

## 4. Dependencies and Maintenance Problems

### Required Packages

```txt
# requirements.txt
msal>=1.26.0
fastapi>=0.100.0
starlette>=0.27.0
itsdangerous>=2.1.0
httpx>=0.25.0
python-multipart>=0.0.6
```

### Maintenance Concerns

| Issue                       | Impact                   | Mitigation                                       |
|-----------------------------|--------------------------|--------------------------------------------------|
| Client secret expiration    | Authentication breaks    | Rotate before expiry                             |
| Redirect URI mismatch       | Authentication fails     | Keep in sync                                     |
| Session hijacking           | Security breach          | Use secure cookies, HTTPS                        |
| Token storage               | Data exposure            | Encrypt session data                             |
| Cross-Site Request Forgery  | Security vulnerability   | Validate state parameter                         |

### Token Refresh

```python
async def get_valid_token(request: Request) -> str:
    """Get valid token, refreshing if needed."""
    tokens = request.session.get("tokens", {})
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check expiration
    import jwt
    from datetime import datetime, timedelta
    
    try:
        decoded = jwt.decode(access_token, options={"verify_signature": False})
        exp = datetime.fromtimestamp(decoded["exp"])
        
        # Refresh if expires within 5 minutes
        if exp < datetime.utcnow() + timedelta(minutes=5):
            if refresh_token:
                new_tokens = oauth.refresh_token(refresh_token)
                if new_tokens and "access_token" in new_tokens:
                    tokens["access_token"] = new_tokens["access_token"]
                    request.session["tokens"] = tokens
                    return new_tokens["access_token"]
            raise HTTPException(status_code=401, detail="Token expired")
        
        return access_token
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
```

## 5. Code Examples

### Basic MSAL Flow

```python
from msal import ConfidentialClientApplication

app = ConfidentialClientApplication(
    client_id="your-client-id",
    authority="https://login.microsoftonline.com/your-tenant-id",
    client_credential="your-secret"
)

# Step 1: Get auth URL
auth_url = app.get_authorization_request_url(
    scopes=["User.Read", "Sites.Read.All"],
    redirect_uri="http://localhost:8000/callback"
)
# Redirect user to auth_url

# Step 2: After callback with code
result = app.acquire_token_by_authorization_code(
    code="received-auth-code",
    scopes=["User.Read", "Sites.Read.All"],
    redirect_uri="http://localhost:8000/callback"
)

if "access_token" in result:
    print(f"Token: {result['access_token'][:50]}...")
```

### With PKCE (Manual)

```python
import hashlib
import base64
import secrets

# Generate PKCE pair
code_verifier = secrets.token_urlsafe(64)
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b'=').decode()

# Include in auth URL
auth_url = (
    f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
    f"?client_id={client_id}"
    f"&response_type=code"
    f"&redirect_uri={redirect_uri}"
    f"&scope=User.Read%20Sites.Read.All"
    f"&code_challenge={code_challenge}"
    f"&code_challenge_method=S256"
)

# When exchanging code, include code_verifier
token_response = requests.post(
    f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
    data={
        "client_id": client_id,
        "client_secret": client_secret,
        "code": auth_code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "code_verifier": code_verifier
    }
)
```

### SharePoint Access

```python
from office365.sharepoint.client_context import ClientContext

def get_sharepoint_context(access_token: str, site_url: str):
    return ClientContext(site_url).with_access_token(lambda: access_token)

# Use in endpoint
@app.get("/api/lists")
async def get_lists(request: Request, user = Depends(require_auth)):
    token = await get_valid_token(request)
    ctx = get_sharepoint_context(token, "https://contoso.sharepoint.com/sites/hr")
    
    lists = ctx.web.lists.get().execute_query()
    return {"lists": [l.title for l in lists]}
```

## 6. Gotchas and Quirks

### State Parameter is Critical

Always validate the state parameter to prevent CSRF attacks:

```python
# Store state before redirect
request.session["oauth_state"] = state

# Validate on callback
if request.query_params.get("state") != request.session.get("oauth_state"):
    raise HTTPException(status_code=400, detail="State mismatch - possible CSRF")
```

### Redirect URI Must Match Exactly

```python
# Azure Portal: https://myapp.azurewebsites.net/auth/callback

# WRONG
redirect_uri = "https://myapp.azurewebsites.net/auth/callback/"  # Trailing slash

# WRONG
redirect_uri = "http://myapp.azurewebsites.net/auth/callback"  # HTTP vs HTTPS

# CORRECT
redirect_uri = "https://myapp.azurewebsites.net/auth/callback"
```

### Scopes Must Include offline_access for Refresh Tokens

```python
# Won't get refresh token
scopes = ["User.Read"]

# Will get refresh token
scopes = ["User.Read", "offline_access"]
```

### Code Can Only Be Used Once

Authorization codes are single-use. If you try to exchange the same code twice, you'll get an error.

### Session Security

```python
# WRONG - insecure session
app.add_middleware(SessionMiddleware, secret_key="fixed-key")

# CORRECT - secure session
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ["SESSION_SECRET"],  # Random, per-deployment
    same_site="lax",  # CSRF protection
    https_only=True,  # Only over HTTPS
    max_age=3600  # 1 hour session
)
```

### Error Handling on Callback

```python
@app.get("/auth/callback")
async def callback(
    code: str = None,
    error: str = None,
    error_description: str = None
):
    # Always check for errors first
    if error:
        if error == "access_denied":
            # User declined consent
            return RedirectResponse(url="/login-cancelled")
        raise HTTPException(status_code=400, detail=error_description)
    
    if not code:
        raise HTTPException(status_code=400, detail="No code received")
    
    # Process code...
```

## Sources

**Primary:**
- SPAUTH-SC-MSFT-AUTHCODE: Authorization code flow
- SPAUTH-SC-MSFT-MSALPYTHON: MSAL for Python
- SPAUTH-SC-RFC-6749: OAuth 2.0 specification

## Document History

**[2026-03-14 17:25]**
- Initial document created
- Complete FastAPI OAuth implementation
- PKCE and security best practices documented
