<DevSystem MarkdownTablesAllowed=true />

# INFO: Security Considerations

**Doc ID**: SPAUTH-IN05
**Goal**: Document security aspects of authentication mechanisms
**Version Scope**: Microsoft Entra ID (2026), OAuth 2.0

**Depends on:**
- `__AUTH_MECHANISMS_SOURCES.md [SPAUTH-SOURCES]` for source references

## Summary

Authentication security involves protecting credentials, tokens, and the authentication flow itself. Certificates are more secure than client secrets because private keys never leave the client and cannot be intercepted in transit. Managed Identity eliminates credential management entirely by having Azure handle authentication internally. Tokens should be stored securely, transmitted only over HTTPS, and validated properly by APIs. Token revocation can be triggered by password changes, admin actions, or Conditional Access policy violations. Multi-factor authentication (MFA) only applies to delegated (user) flows, not app-only flows. The principle of least privilege should guide permission selection, preferring Sites.Selected over Sites.FullControl.All when possible.

## Key Facts

- **Certificate > Secret**: Private key never transmitted, cannot be intercepted [VERIFIED] (SPAUTH-SC-MSFT-CERTCREDS)
- **Managed Identity**: No credentials in code or config, Azure manages internally [VERIFIED] (SPAUTH-SC-MSFT-MIWORK)
- **Token Revocation**: Triggered by password change, admin revocation, or CAE [VERIFIED] (SPAUTH-SC-MSFT-REFRESH)
- **Access Token Validation**: API must verify signature, issuer, audience, expiration [VERIFIED] (SPAUTH-SC-MSFT-PROTOCOLS)
- **MFA**: Only applies to delegated flows, not client credentials [VERIFIED] (SPAUTH-SC-MSFT-CLIENTCREDS)

## Quick Reference

**Security Hierarchy (best to worst):**
```
1. Managed Identity (no credentials)
2. Workload Identity (federated, no secrets)
3. Certificate (private key stays local)
4. Client Secret (transmitted over network)
5. Username/Password (credentials exposed to app)
```

## 1. Certificate vs Client Secret Security

### Client Secret Risks

- **Transmission risk**: Secret sent over network (even HTTPS can be logged)
- **Storage risk**: Often hardcoded or in config files
- **Rotation complexity**: Must update all instances when rotating
- **Exposure scope**: Anyone with secret can impersonate app

### Certificate Advantages

- **Private key stays local**: Never transmitted, only signatures sent
- **Proof of possession**: Signing proves you have the key
- **Hardware protection**: Can use HSM or TPM for key storage
- **Easier rotation**: Add new cert, update app, remove old cert

### Why SharePoint Requires Certificates

SharePoint Online blocks client secret authentication for app-only access to reduce risk surface. Certificate authentication provides stronger assurance that the calling application is legitimate.

[VERIFIED] (SPAUTH-SC-MSFT-CERTCREDS)

## 2. Managed Identity Security Model

### How It's More Secure

1. **No credentials to manage**: No secrets, certificates, or passwords
2. **No credentials to leak**: Nothing in code, config, or environment variables
3. **Automatic rotation**: Azure rotates the internal certificate automatically
4. **Network isolation**: IMDS endpoint (169.254.169.254) only accessible from within the VM/container

### Internal Security

- Azure creates a service principal for the identity
- An internal certificate is provisioned to the VM/container
- Certificate is stored securely and rotated by Azure
- Token requests to IMDS are authenticated using this internal certificate

### Limitations

- Only works in Azure-hosted environments
- Cannot be used for local development (use DefaultAzureCredential fallback)
- User-assigned identity requires additional configuration

[VERIFIED] (SPAUTH-SC-MSFT-MIWORK)

## 3. Token Storage Best Practices

### Access Tokens

- **Memory only**: Prefer storing in memory, not on disk
- **Short-lived**: 60-90 minute default lifetime limits exposure
- **Encrypted if persisted**: Use OS-level encryption (DPAPI, Keychain)
- **No logging**: Never log token values

### Refresh Tokens

- **More sensitive**: Longer-lived, can get new access tokens
- **Encrypted storage**: Must be encrypted at rest
- **Rotation**: Use sliding expiration, rotate on use
- **Revocation**: Can be revoked by admin or user

### Python Example: Secure Token Storage

```python
import keyring
import json

class SecureTokenStore:
    """Store tokens using OS keychain."""
    
    SERVICE_NAME = "MyApp"
    
    def store_token(self, key: str, token_data: dict):
        """Store token in OS keychain."""
        keyring.set_password(
            self.SERVICE_NAME,
            key,
            json.dumps(token_data)
        )
    
    def get_token(self, key: str) -> dict:
        """Retrieve token from OS keychain."""
        data = keyring.get_password(self.SERVICE_NAME, key)
        return json.loads(data) if data else None
    
    def delete_token(self, key: str):
        """Remove token from OS keychain."""
        try:
            keyring.delete_password(self.SERVICE_NAME, key)
        except keyring.errors.PasswordDeleteError:
            pass
```

## 4. Token Revocation

### When Tokens Are Revoked

1. **Password change**: User's refresh tokens revoked
2. **Admin revocation**: Admin revokes all tokens for user/app
3. **Conditional Access failure**: CAE-enabled tokens revoked when policy violated
4. **App consent revoked**: User removes app permissions
5. **Account disabled/deleted**: All tokens invalidated

### Continuous Access Evaluation (CAE)

CAE allows near real-time token revocation for critical events:

- User account disabled
- User password changed
- User location changed (if location-based CA policy)
- Admin revokes sessions

```python
from azure.identity import InteractiveBrowserCredential

# Enable CAE for proactive revocation handling
credential = InteractiveBrowserCredential(
    client_id="YOUR_CLIENT_ID",
    tenant_id="YOUR_TENANT_ID",
    enable_cae=True  # Enable Continuous Access Evaluation
)
```

[VERIFIED] (SPAUTH-SC-MSFT-REFRESH)

## 5. Conditional Access and MFA

### Conditional Access Policies

Organizational policies that control authentication:
- Require MFA for certain apps or locations
- Block access from untrusted networks
- Require compliant devices
- Require specific authentication methods

### MFA and Authentication Flows

| Flow                | MFA Applicable | Reason                       |
|---------------------|----------------|------------------------------|
| Authorization Code  | Yes            | User is present              |
| Device Code         | Yes            | User authenticates on device |
| Interactive Browser | Yes            | User is present              |
| Client Credentials  | No             | No user, app-only            |
| Managed Identity    | No             | No user, Azure-managed       |

### Handling MFA in Code

```python
from msal import PublicClientApplication

app = PublicClientApplication(
    client_id="YOUR_CLIENT_ID",
    authority="https://login.microsoftonline.com/YOUR_TENANT_ID"
)

# Interactive flow handles MFA automatically
result = app.acquire_token_interactive(
    scopes=["https://graph.microsoft.com/.default"]
)

# If MFA required, user sees MFA prompt in browser
```

[VERIFIED] (SPAUTH-SC-MSFT-PROTOCOLS)

## 6. Permission Scope Security

### Principle of Least Privilege

Request only the permissions your app needs:

| Permission              | Scope                   | Risk     |
|-------------------------|-------------------------|----------|
| Sites.Read.All          | All sites, read         | Medium   |
| Sites.ReadWrite.All     | All sites, read/write   | High     |
| Sites.FullControl.All   | All sites, full control | Critical |
| Sites.Selected          | Specific sites only     | Lowest   |

### Sites.Selected for Granular Access

Instead of tenant-wide permissions:

1. Request `Sites.Selected` application permission
2. Admin grants access to specific sites via Graph API or PowerShell
3. App can only access granted sites

```http
POST https://graph.microsoft.com/v1.0/sites/{site-id}/permissions
Content-Type: application/json

{
  "roles": ["read"],
  "grantedToIdentities": [{
    "application": {
      "id": "{app-client-id}",
      "displayName": "My App"
    }
  }]
}
```

[VERIFIED] (SPAUTH-SC-MSFT-PROTOCOLS)

## 7. Token Validation (API Side)

### Required Validation Steps

1. **Signature**: Verify using issuer's public key
2. **Issuer (iss)**: Must match expected Microsoft Entra endpoint
3. **Audience (aud)**: Must match your API's identifier
4. **Expiration (exp)**: Token must not be expired
5. **Not Before (nbf)**: Token must be valid (not future-dated)

### Python Validation Example

```python
import jwt
import requests

def validate_access_token(token: str, expected_audience: str, tenant_id: str) -> dict:
    """Validate an access token from Microsoft Entra ID."""
    
    # Get JWKS
    jwks_url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
    jwks = requests.get(jwks_url).json()
    
    # Get key ID from token header
    header = jwt.get_unverified_header(token)
    kid = header["kid"]
    
    # Find matching key
    key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
    if not key:
        raise ValueError("Key not found in JWKS")
    
    # Convert to PEM
    from jwt.algorithms import RSAAlgorithm
    public_key = RSAAlgorithm.from_jwk(key)
    
    # Validate token
    decoded = jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        audience=expected_audience,
        issuer=f"https://login.microsoftonline.com/{tenant_id}/v2.0"
    )
    
    return decoded
```

## SDK Examples (Python)

### Secure Credential Configuration

```python
import os
from azure.identity import CertificateCredential, DefaultAzureCredential

def get_credential():
    """Get credential with security best practices."""
    
    # In Azure: use managed identity (most secure)
    if os.getenv("AZURE_FUNCTIONS_ENVIRONMENT"):
        return DefaultAzureCredential(
            exclude_environment_credential=True,
            exclude_cli_credential=True,
            exclude_powershell_credential=True
        )
    
    # Local dev with certificate (more secure than secret)
    cert_path = os.getenv("AZURE_CLIENT_CERTIFICATE_PATH")
    if cert_path:
        return CertificateCredential(
            tenant_id=os.getenv("AZURE_TENANT_ID"),
            client_id=os.getenv("AZURE_CLIENT_ID"),
            certificate_path=cert_path
        )
    
    # Fallback to default chain
    return DefaultAzureCredential()
```

### Token Introspection (Debugging)

```python
import jwt
from datetime import datetime

def inspect_token(token: str):
    """Inspect token claims for debugging (not validation)."""
    
    # Decode without verification (for inspection only)
    decoded = jwt.decode(token, options={"verify_signature": False})
    
    # Check expiration
    exp = decoded.get("exp")
    if exp:
        exp_time = datetime.fromtimestamp(exp)
        is_expired = datetime.now() > exp_time
        print(f"Expires: {exp_time} (Expired: {is_expired})")
    
    # Check permissions
    if "scp" in decoded:
        print(f"Delegated scopes: {decoded['scp']}")
    if "roles" in decoded:
        print(f"App roles: {decoded['roles']}")
    
    return decoded
```

## Error Responses

- **AADSTS50076**: MFA required but not completed
- **AADSTS53003**: Conditional Access policy blocked access
- **AADSTS700082**: Refresh token expired due to inactivity
- **AADSTS50173**: Token revoked (password change, admin action)

## Limitations and Known Issues

- [COMMUNITY] CAE not supported for all apps; requires specific scopes (SPAUTH-SC-MSFT-REFRESH)
- Sites.Selected requires manual per-site grants
- Token validation libraries may have vulnerabilities; keep updated

## Gotchas and Quirks

- Access tokens from Microsoft are NOT meant to be parsed by clients (structure may change)
- Refresh tokens are encrypted; cannot be decoded
- App-only tokens have `idtyp: "app"` claim to distinguish from user tokens

## Sources

**Primary:**
- SPAUTH-SC-MSFT-CERTCREDS: Certificate credentials
- SPAUTH-SC-MSFT-MIWORK: How managed identities work with VMs
- SPAUTH-SC-MSFT-REFRESH: Refresh tokens
- SPAUTH-SC-MSFT-PROTOCOLS: OAuth 2.0 and OpenID Connect protocols

## Document History

**[2026-03-14 17:10]**
- Initial document created
- Security comparison of auth methods documented
- Token storage and validation best practices added
