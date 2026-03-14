<DevSystem MarkdownTablesAllowed=true />

# INFO: JWT Token Structure

**Doc ID**: SPAUTH-IN02
**Goal**: Document JWT token anatomy, encoding, claims, and signature verification
**Version Scope**: RFC 7519 (JWT), Microsoft Entra ID (2026)

**Depends on:**
- `__AUTH_MECHANISMS_SOURCES.md [SPAUTH-SOURCES]` for source references

## Summary

JSON Web Tokens (JWTs) are the token format used by Microsoft Entra ID for access tokens, ID tokens, and client assertions. A JWT consists of three Base64URL-encoded parts separated by dots: header, payload, and signature. The header specifies the signing algorithm and key identifier. The payload contains claims about the authenticated entity (user or application) including issuer, subject, audience, and expiration. Microsoft adds custom claims like tenant ID (tid), object ID (oid), roles, and scopes. Access tokens authorize API calls while ID tokens provide user identity information. The signature is computed using RS256 (RSA with SHA-256) and can be verified using Microsoft's public keys from the JWKS endpoint.

## Key Facts

- **Structure**: `header.payload.signature` separated by dots [VERIFIED] (SPAUTH-SC-RFC-7519)
- **Encoding**: Base64URL (URL-safe Base64 without padding) [VERIFIED] (SPAUTH-SC-RFC-7519)
- **Signing Algorithm**: RS256 (RSA Signature with SHA-256) for Entra ID tokens [VERIFIED] (SPAUTH-SC-MSFT-PROTOCOLS)
- **Access Token Lifetime**: Default 60-90 minutes for Microsoft Graph [VERIFIED] (SPAUTH-SC-MSFT-TOKENLIFE)
- **ID Token Purpose**: Contains user identity claims, not for API authorization [VERIFIED] (SPAUTH-SC-MSFT-PROTOCOLS)

## Quick Reference

**JWT Parts:**
```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2xvZ2...
|_____________Header______________|.|___________Payload___________|.Sig
```

**JWKS Endpoint (Public Keys):**
```
https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys
```

## 1. JWT Anatomy

### Header

The header is a JSON object specifying token type and signing algorithm:

```json
{
  "typ": "JWT",
  "alg": "RS256",
  "kid": "nOo3ZDrODXEK1jKWhXslHR_KXEg"
}
```

**Header Claims:**
- **typ**: Token type, always "JWT"
- **alg**: Signing algorithm (RS256 = RSA with SHA-256)
- **kid**: Key ID - identifies which key from JWKS was used to sign
- **x5t**: (Optional) X.509 certificate thumbprint (Base64URL of SHA-1)

### Payload

The payload contains claims about the token:

```json
{
  "aud": "https://graph.microsoft.com",
  "iss": "https://login.microsoftonline.com/{tenant}/v2.0",
  "iat": 1710425600,
  "nbf": 1710425600,
  "exp": 1710429200,
  "sub": "AAAAAAAAAAAAAAAAAAAAAIkzqFVrSaSaFHy782bbtaQ",
  "oid": "00000000-0000-0000-0000-000000000000",
  "tid": "00000000-0000-0000-0000-000000000000",
  "scp": "User.Read Files.Read",
  "roles": ["Sites.Read.All"]
}
```

### Signature

The signature is computed over the encoded header and payload:

```
RSASHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  privateKey
)
```

[VERIFIED] (SPAUTH-SC-RFC-7519 | SPAUTH-SC-RFC-7515)

## 2. Base64URL Encoding

JWT uses Base64URL encoding, which differs from standard Base64:

**Differences from Base64:**
- `+` replaced with `-`
- `/` replaced with `_`
- No padding (`=` characters removed)

**Python Implementation:**

```python
import base64
import json

def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')

def base64url_decode(data: str) -> bytes:
    # Add padding back
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data)

# Decode a JWT payload
token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ0ZXN0In0.sig"
parts = token.split('.')
payload = json.loads(base64url_decode(parts[1]))
print(payload)  # {"iss": "test"}
```

[VERIFIED] (SPAUTH-SC-RFC-7519)

## 3. Standard Claims (RFC 7519)

| Claim | Name       | Description                                                              |
|-------|------------|--------------------------------------------------------------------------|
| iss   | Issuer     | Who issued the token (e.g., `https://login.microsoftonline.com/{tid}/v2.0`) |
| sub   | Subject    | Unique identifier for the entity (user or app)                           |
| aud   | Audience   | Intended recipient (API resource URL or client_id)                       |
| exp   | Expiration | Unix timestamp when token expires                                        |
| nbf   | Not Before | Unix timestamp when token becomes valid                                  |
| iat   | Issued At  | Unix timestamp when token was issued                                     |
| jti   | JWT ID     | Unique identifier for the token (prevents replay)                        |

[VERIFIED] (SPAUTH-SC-RFC-7519)

## 4. Microsoft-Specific Claims

### User Token Claims (Delegated)

| Claim              | Description                                 |
|--------------------|---------------------------------------------|
| tid                | Tenant ID (Azure AD tenant GUID)            |
| oid                | Object ID (user's unique ID in tenant)      |
| preferred_username | User's email/UPN                            |
| name               | User's display name                         |
| scp                | Scopes (space-separated delegated perms)    |
| upn                | User Principal Name                         |
| unique_name        | (v1 tokens) Same as preferred_username      |

### App Token Claims (Application)

| Claim  | Description                               |
|--------|-------------------------------------------|
| tid    | Tenant ID                                 |
| oid    | Object ID (app's service principal ID)    |
| azp    | Authorized party (client_id of the app)   |
| roles  | Application permissions (array)           |
| idtyp  | Identity type ("app" for app-only tokens) |

### Example: User Access Token Payload

```json
{
  "aud": "https://graph.microsoft.com",
  "iss": "https://login.microsoftonline.com/contoso.onmicrosoft.com/v2.0",
  "iat": 1710425600,
  "nbf": 1710425600,
  "exp": 1710429200,
  "sub": "AAAAAAAAAAAAAAAAAAAAAIkzqFVrSaSaFHy782bbtaQ",
  "oid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "tid": "12345678-1234-1234-1234-123456789012",
  "preferred_username": "user@contoso.com",
  "name": "John Doe",
  "scp": "User.Read Files.ReadWrite.All Sites.Read.All"
}
```

### Example: App Access Token Payload

```json
{
  "aud": "https://graph.microsoft.com",
  "iss": "https://login.microsoftonline.com/contoso.onmicrosoft.com/v2.0",
  "iat": 1710425600,
  "exp": 1710429200,
  "azp": "11111111-2222-3333-4444-555555555555",
  "oid": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "tid": "12345678-1234-1234-1234-123456789012",
  "idtyp": "app",
  "roles": ["Sites.Read.All", "Files.Read.All"]
}
```

[VERIFIED] (SPAUTH-SC-MSFT-PROTOCOLS)

## 5. Access Token vs ID Token

| Aspect     | Access Token                 | ID Token             |
|------------|------------------------------|----------------------|
| Purpose    | Authorize API calls          | Prove user identity  |
| Audience   | API resource URL             | Client application   |
| Contains   | Permissions (scp/roles)      | User profile info    |
| Validation | By API/resource              | By client app        |
| Sent to    | APIs in Authorization header | Client app only      |

**Key Rule**: Never use ID tokens to call APIs. ID tokens prove identity to YOUR app. Access tokens authorize calls to OTHER apps/APIs.

[VERIFIED] (SPAUTH-SC-MSFT-PROTOCOLS)

## 6. Signature Verification

### How Verification Works

1. **Decode header** to get `kid` (key ID) and `alg`
2. **Fetch JWKS** from Microsoft's endpoint
3. **Find matching key** by `kid`
4. **Verify signature** using public key

### JWKS Endpoint

```
GET https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys
```

Response contains array of public keys:

```json
{
  "keys": [
    {
      "kty": "RSA",
      "kid": "nOo3ZDrODXEK1jKWhXslHR_KXEg",
      "use": "sig",
      "n": "0vx7agoeb...",
      "e": "AQAB"
    }
  ]
}
```

### Python Verification Example

```python
import jwt
import requests

def verify_token(token: str, tenant_id: str) -> dict:
    # Get JWKS
    jwks_url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
    jwks = requests.get(jwks_url).json()
    
    # Decode header to get kid
    header = jwt.get_unverified_header(token)
    kid = header["kid"]
    
    # Find matching key
    key = next(k for k in jwks["keys"] if k["kid"] == kid)
    
    # Convert to PEM and verify
    from jwt.algorithms import RSAAlgorithm
    public_key = RSAAlgorithm.from_jwk(key)
    
    # Verify token
    decoded = jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        audience="https://graph.microsoft.com"
    )
    return decoded
```

[VERIFIED] (SPAUTH-SC-RFC-7515 | SPAUTH-SC-RFC-7517)

## SDK Examples (Python)

### Decode Token Without Verification

```python
import jwt

# Decode without verification (for debugging)
token = "eyJ0eXAiOiJKV1QiLCJhbGci..."
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded)
```

### Check Token Expiration

```python
import jwt
from datetime import datetime

token = "eyJ0eXAiOiJKV1QiLCJhbGci..."
decoded = jwt.decode(token, options={"verify_signature": False})

exp = decoded["exp"]
exp_time = datetime.fromtimestamp(exp)
is_expired = datetime.now() > exp_time

print(f"Expires: {exp_time}, Expired: {is_expired}")
```

## Error Responses

- **invalid_token**: Token signature invalid or malformed
- **token_expired**: Token `exp` claim is in the past
- **invalid_audience**: Token `aud` doesn't match expected resource

## Limitations and Known Issues

- [COMMUNITY] Access tokens are not meant to be parsed by clients; Microsoft can change internal structure (SPAUTH-SC-JWTIO)
- Token size can exceed URL length limits for complex permission sets
- v1 vs v2 tokens have different claim structures

## Gotchas and Quirks

- `sub` claim is different between ID tokens and access tokens for same user
- `aud` for Graph API is the URL, not a GUID
- Token validation should check `iss`, `aud`, `exp`, `nbf`, and signature

## Sources

**Primary:**
- SPAUTH-SC-RFC-7519: RFC 7519 - JSON Web Token (JWT)
- SPAUTH-SC-RFC-7515: RFC 7515 - JSON Web Signature (JWS)
- SPAUTH-SC-RFC-7517: RFC 7517 - JSON Web Key (JWK)
- SPAUTH-SC-MSFT-PROTOCOLS: OAuth 2.0 and OpenID Connect protocols

**Community:**
- SPAUTH-SC-JWTIO: JWT.io - JWT Debugger
- SPAUTH-SC-STYTCH-JWT: Developer's guide to RFC 7519

## Document History

**[2026-03-14 16:55]**
- Initial document created
- JWT anatomy documented with examples
- Standard and Microsoft claims catalogued
