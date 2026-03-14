# INFO: OAuth 2.0 Protocol Flows

**Doc ID**: SPAUTH-IN01
**Goal**: Document how each OAuth 2.0 flow works internally with step-by-step protocol details
**Version Scope**: OAuth 2.0 (RFC 6749), Microsoft Entra ID (2026)

**Depends on:**
- `__AUTH_MECHANISMS_SOURCES.md [SPAUTH-SOURCES]` for source references

## Summary

OAuth 2.0 defines several authorization flows (grants) for different application types. The Authorization Code flow with PKCE is recommended for public clients (mobile, SPA, desktop), using a temporary code exchanged for tokens. The Client Credentials flow is for server-to-server (app-only) scenarios where the application authenticates with its own identity using a secret or certificate. The Device Code flow enables authentication on browserless devices by displaying a code the user enters on another device. The On-Behalf-Of flow allows middle-tier services to exchange a user's token for a downstream service token. Each flow involves specific HTTP requests to Microsoft Entra ID endpoints, with tokens returned as JWTs containing claims about the authenticated entity.

## Key Facts

- **Authorization Code + PKCE**: Uses code_verifier/code_challenge to prevent interception attacks [VERIFIED] (SPAUTH-SC-MSFT-AUTHCODE)
- **Client Credentials**: No refresh tokens issued; client can always get new access token [VERIFIED] (SPAUTH-SC-MSFT-CLIENTCREDS)
- **Device Code Polling**: Client polls token endpoint every 5 seconds until user completes auth [VERIFIED] (SPAUTH-SC-MSFT-DEVICECODE)
- **Certificate Auth**: Uses client_assertion JWT signed with private key instead of client_secret [VERIFIED] (SPAUTH-SC-MSFT-CLIENTCREDS)
- **Token Endpoint**: `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token` [VERIFIED] (SPAUTH-SC-MSFT-PROTOCOLS)

## Quick Reference

**Endpoints:**
- Authorize: `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize`
- Token: `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token`
- Device Code: `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/devicecode`

**Grant Types:**
- `authorization_code` - Auth code flow
- `client_credentials` - App-only flow
- `urn:ietf:params:oauth:grant-type:device_code` - Device code flow
- `urn:ietf:params:oauth:grant-type:jwt-bearer` - On-behalf-of flow

## 1. Authorization Code Flow with PKCE

### How It Works

The Authorization Code flow with PKCE (Proof Key for Code Exchange) is the recommended flow for public clients that cannot securely store a client secret.

**Step-by-step process:**

1. **Generate PKCE values** (client-side)
   - Create random `code_verifier` (43-128 characters)
   - Compute `code_challenge` = BASE64URL(SHA256(code_verifier))

2. **Redirect to authorize endpoint**
   ```
   GET https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize
   ?client_id={client_id}
   &response_type=code
   &redirect_uri={redirect_uri}
   &scope={scopes}
   &code_challenge={code_challenge}
   &code_challenge_method=S256
   &state={random_state}
   ```

3. **User authenticates** in browser (Microsoft login page)

4. **Redirect back with code**
   ```
   {redirect_uri}?code={authorization_code}&state={state}
   ```

5. **Exchange code for tokens**
   ```
   POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
   Content-Type: application/x-www-form-urlencoded
   
   client_id={client_id}
   &grant_type=authorization_code
   &code={authorization_code}
   &redirect_uri={redirect_uri}
   &code_verifier={code_verifier}
   ```

6. **Receive tokens**
   ```json
   {
     "access_token": "eyJ0eXAi...",
     "token_type": "Bearer",
     "expires_in": 3600,
     "refresh_token": "0.AVYA...",
     "id_token": "eyJ0eXAi..."
   }
   ```

### Why PKCE Prevents Interception

Without PKCE, an attacker who intercepts the authorization code could exchange it for tokens. With PKCE:
- Attacker cannot compute `code_verifier` from `code_challenge` (SHA256 is one-way)
- Token endpoint requires `code_verifier` that only legitimate client knows

[VERIFIED] (SPAUTH-SC-RFC-6749 | SPAUTH-SC-MSFT-AUTHCODE)

## 2. Client Credentials Flow

### How It Works

The Client Credentials flow is for confidential clients (servers, daemons) authenticating as themselves, not on behalf of a user.

**Two authentication methods:**

### Method A: Client Secret

```
POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

client_id={client_id}
&scope=https://graph.microsoft.com/.default
&client_secret={client_secret}
&grant_type=client_credentials
```

**WARNING**: Client secrets do NOT work for SharePoint REST API (`/_api/`). SharePoint requires certificate authentication for app-only access. [VERIFIED] (SPAUTH-SC-MSFT-CLIENTCREDS)

### Method B: Certificate (Client Assertion)

```
POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

client_id={client_id}
&scope=https://graph.microsoft.com/.default
&client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer
&client_assertion={signed_jwt}
&grant_type=client_credentials
```

**Client Assertion JWT Structure:**
```json
// Header
{
  "alg": "RS256",
  "typ": "JWT",
  "x5t": "{base64url_thumbprint}"
}
// Payload
{
  "aud": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
  "iss": "{client_id}",
  "sub": "{client_id}",
  "jti": "{unique_id}",
  "nbf": 1234567890,
  "exp": 1234567890
}
// Signature: RS256 with private key
```

### No Refresh Tokens

Client credentials flow does NOT return refresh tokens. The client can always request a new access token using its credentials. [VERIFIED] (SPAUTH-SC-MSFT-CLIENTCREDS)

## 3. Device Code Flow

### How It Works

The Device Code flow enables authentication on devices without browsers (CLI tools, IoT, smart TVs).

**Step-by-step process:**

1. **Request device code**
   ```
   POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/devicecode
   Content-Type: application/x-www-form-urlencoded
   
   client_id={client_id}
   &scope={scopes}
   ```

2. **Receive device code response**
   ```json
   {
     "device_code": "GMMhmHC...",
     "user_code": "WDJB-MJHT",
     "verification_uri": "https://microsoft.com/devicelogin",
     "expires_in": 900,
     "interval": 5,
     "message": "To sign in, use a web browser to open..."
   }
   ```

3. **Display to user**: Show `verification_uri` and `user_code`

4. **User authenticates**: On another device, user visits URL and enters code

5. **Poll for token** (every `interval` seconds)
   ```
   POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
   Content-Type: application/x-www-form-urlencoded
   
   client_id={client_id}
   &grant_type=urn:ietf:params:oauth:grant-type:device_code
   &device_code={device_code}
   ```

6. **Polling responses**:
   - `authorization_pending`: User hasn't completed auth yet, keep polling
   - `slow_down`: Increase polling interval
   - `expired_token`: Device code expired, restart flow
   - Success: Tokens returned

### Polling Behavior

Default polling interval is 5 seconds. If you poll too fast, you get `slow_down` error and should increase interval. [VERIFIED] (SPAUTH-SC-MSFT-DEVICECODE)

## 4. On-Behalf-Of Flow

### How It Works

The On-Behalf-Of (OBO) flow allows a middle-tier service to call downstream APIs on behalf of the user who called the middle-tier.

**Scenario:** User -> Frontend -> Middle-tier API -> Downstream API

**Step-by-step process:**

1. **Frontend obtains user token** for middle-tier API

2. **Middle-tier receives user's access token** in Authorization header

3. **Middle-tier exchanges token** for downstream API:
   ```
   POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
   Content-Type: application/x-www-form-urlencoded
   
   client_id={middle_tier_client_id}
   &client_secret={middle_tier_secret}
   &grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer
   &assertion={user_access_token}
   &scope={downstream_api_scope}
   &requested_token_use=on_behalf_of
   ```

4. **Receive downstream token**: New access token for downstream API, still representing the user

### Key Points

- User's identity is preserved in the downstream token
- Requires middle-tier app to have permission to call downstream API
- User must have consented to downstream API scopes

[VERIFIED] (SPAUTH-SC-MSFT-OBO)

## 5. Managed Identity (IMDS)

### How It Works

Managed Identity is not a standard OAuth flow but uses a local metadata endpoint (IMDS) to obtain tokens without credentials.

**Step-by-step process:**

1. **Azure provisions identity**: When VM/App Service is configured with managed identity, Azure creates a service principal and provisions a certificate internally

2. **Code requests token from IMDS**:
   ```
   GET http://169.254.169.254/metadata/identity/oauth2/token
   ?api-version=2018-02-01
   &resource=https://graph.microsoft.com
   
   Headers:
   Metadata: true
   ```

3. **IMDS authenticates to Entra ID**: Using the internal certificate, IMDS calls Entra ID token endpoint

4. **Token returned to code**:
   ```json
   {
     "access_token": "eyJ0eXAi...",
     "expires_in": "3599",
     "token_type": "Bearer"
   }
   ```

### Security Model

- IMDS endpoint (169.254.169.254) is only accessible from within the VM/container
- No credentials stored in code or configuration
- Certificate managed and rotated by Azure

**Cold-start note:** IMDS may take 2-5 seconds to respond on first request after VM/container cold start. Azure Identity SDK handles retries internally.

[VERIFIED] (SPAUTH-SC-MSFT-MIWORK | SPAUTH-SC-MSFT-MITOKEN)

## 6. Deprecated Flows

### Implicit Flow (Deprecated)

- Returned access token directly in URL fragment
- Vulnerable to token leakage via browser history, referrer headers
- Replaced by Authorization Code + PKCE

### Resource Owner Password (ROPC) (Deprecated)

- Application collects username/password directly
- Cannot support MFA, Conditional Access
- Only use for legacy migration scenarios

[VERIFIED] (SPAUTH-SC-RFC-6749)

## SDK Examples (Python)

### Authorization Code with MSAL

```python
from msal import PublicClientApplication

app = PublicClientApplication(
    client_id="YOUR_CLIENT_ID",
    authority="https://login.microsoftonline.com/YOUR_TENANT_ID"
)

# Get auth URL
auth_url = app.get_authorization_request_url(
    scopes=["https://graph.microsoft.com/.default"],
    redirect_uri="http://localhost:8400"
)
# Redirect user to auth_url

# After redirect, exchange code
result = app.acquire_token_by_authorization_code(
    code="AUTH_CODE_FROM_REDIRECT",
    scopes=["https://graph.microsoft.com/.default"],
    redirect_uri="http://localhost:8400"
)
access_token = result["access_token"]
```

### Client Credentials with Certificate

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
    scopes=["https://graph.microsoft.com/.default"]
)
access_token = result["access_token"]
```

### Device Code Flow

```python
from msal import PublicClientApplication

app = PublicClientApplication(
    client_id="YOUR_CLIENT_ID",
    authority="https://login.microsoftonline.com/YOUR_TENANT_ID"
)

flow = app.initiate_device_flow(
    scopes=["https://graph.microsoft.com/.default"]
)
print(flow["message"])  # Display to user

# Blocks until user completes auth or timeout
result = app.acquire_token_by_device_flow(flow)
access_token = result["access_token"]
```

### Managed Identity with Azure Identity

```python
from azure.identity import ManagedIdentityCredential

credential = ManagedIdentityCredential()

# SDK handles IMDS call internally
token = credential.get_token("https://graph.microsoft.com/.default")
access_token = token.token
```

## Error Responses

- **invalid_grant**: Authorization code expired or already used
- **invalid_client**: Client authentication failed (wrong secret/cert)
- **authorization_pending**: (Device code) User hasn't completed auth
- **slow_down**: (Device code) Polling too fast
- **expired_token**: (Device code) Device code expired

## Limitations and Known Issues

- [COMMUNITY] PKCE is required for public clients; some legacy apps may not support it (SPAUTH-SC-AUTH0-CLIENTCREDS)
- Client credentials with secret blocked for SharePoint REST API
- Device code flow has 15-minute timeout by default

## Gotchas and Quirks

- `.default` scope required for client credentials to get app permissions
- Token endpoint URL must match exactly (trailing slash matters in some cases)
- `resource` parameter (v1 endpoint) vs `scope` parameter (v2 endpoint)

## Sources

**Primary:**
- SPAUTH-SC-RFC-6749: RFC 6749 - The OAuth 2.0 Authorization Framework
- SPAUTH-SC-MSFT-CLIENTCREDS: OAuth 2.0 client credentials flow
- SPAUTH-SC-MSFT-AUTHCODE: OAuth 2.0 authorization code flow
- SPAUTH-SC-MSFT-DEVICECODE: OAuth 2.0 device authorization grant
- SPAUTH-SC-MSFT-OBO: OAuth 2.0 On-Behalf-Of flow
- SPAUTH-SC-MSFT-MIWORK: How managed identities work with VMs

## Document History

**[2026-03-14 16:50]**
- Initial document created
- All 6 flows documented with step-by-step details
- Python SDK examples added
