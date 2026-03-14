<DevSystem MarkdownTablesAllowed=true />

# INFO: Cryptographic Operations

**Doc ID**: SPAUTH-IN03
**Goal**: Document certificate-based authentication cryptographic internals
**Version Scope**: X.509 Certificates, RSA/SHA-256, Microsoft Entra ID (2026)

**Depends on:**
- `__AUTH_MECHANISMS_SOURCES.md [SPAUTH-SOURCES]` for source references

## Summary

Certificate-based authentication to Microsoft Entra ID uses asymmetric cryptography where the client proves possession of a private key by signing a JWT assertion. The client creates a JWT with specific claims (audience, issuer, subject, expiration) and signs it using the private key associated with a certificate registered in Azure AD. The certificate's thumbprint (SHA-1 hash of the DER-encoded certificate) is included in the JWT header to identify which certificate was used. Microsoft verifies the signature using the corresponding public key from the registered certificate. This is more secure than client secrets because the private key never leaves the client and cannot be intercepted in transit.

## Key Facts

- **Thumbprint**: SHA-1 hash of DER-encoded certificate, hex-encoded uppercase [VERIFIED] (SPAUTH-SC-MSFT-CERTCREDS)
- **Signing Algorithm**: RS256 (RSASSA-PKCS1-v1_5 with SHA-256) [VERIFIED] (SPAUTH-SC-RFC-7515)
- **Assertion Lifetime**: Recommended 5-10 minutes, max varies by IdP [VERIFIED] (SPAUTH-SC-MSFT-CERTCREDS)
- **Key Size**: Minimum 2048 bits for RSA keys [VERIFIED] (SPAUTH-SC-MSFT-CERTCREDS)
- **PFX/PKCS#12**: Standard format for bundling certificate + private key [VERIFIED] (SPAUTH-SC-BLOG-GRAPHCERT)

## Quick Reference

**Client Assertion JWT:**
```
Header:  {"alg": "RS256", "typ": "JWT", "x5t": "<thumbprint>"}
Payload: {"aud": "<token_endpoint>", "iss": "<client_id>", "sub": "<client_id>", "jti": "<unique_id>", "exp": <expiration>}
Signature: RS256(header.payload, private_key)
```

## 1. Certificate Thumbprint Calculation

The thumbprint uniquely identifies a certificate. It's the SHA-1 hash of the certificate in DER (binary) format.

### Python Implementation

```python
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import hashlib

def get_certificate_thumbprint(cert_path: str) -> str:
    """
    Calculate SHA-1 thumbprint of a certificate.
    Returns uppercase hex string.
    """
    with open(cert_path, 'rb') as f:
        cert_data = f.read()
    
    # Parse certificate (handles both PEM and DER)
    try:
        cert = x509.load_pem_x509_certificate(cert_data, default_backend())
    except ValueError:
        cert = x509.load_der_x509_certificate(cert_data, default_backend())
    
    # Get DER encoding and compute SHA-1
    der_bytes = cert.public_bytes(serialization.Encoding.DER)
    thumbprint = hashlib.sha1(der_bytes).hexdigest().upper()
    
    return thumbprint

# Example
thumbprint = get_certificate_thumbprint("cert.pem")
print(thumbprint)  # "A1B2C3D4E5F6..."
```

### x5t Header Value (Base64URL)

The `x5t` header in JWTs uses Base64URL-encoded thumbprint (not hex):

```python
import base64
import hashlib

def get_x5t_header(cert_der_bytes: bytes) -> str:
    """Get x5t header value (Base64URL of SHA-1)."""
    sha1_hash = hashlib.sha1(cert_der_bytes).digest()
    return base64.urlsafe_b64encode(sha1_hash).rstrip(b'=').decode('ascii')
```

[VERIFIED] (SPAUTH-SC-MSFT-CERTCREDS)

## 2. PFX to PEM Conversion

Azure Portal exports certificates as PFX (PKCS#12). Python libraries often need PEM format.

### Complete Conversion Function

```python
from cryptography.hazmat.primitives.serialization import (
    pkcs12, Encoding, PrivateFormat, NoEncryption
)
from cryptography.hazmat.backends import default_backend
import os

def convert_pfx_to_pem(
    pfx_path: str, 
    pfx_password: str,
    pem_path: str = None
) -> tuple[str, str, bytes]:
    """
    Convert PFX certificate to PEM format.
    
    Returns:
        tuple: (pem_path, thumbprint, pem_bytes)
    """
    # Load PFX
    with open(pfx_path, 'rb') as f:
        pfx_data = f.read()
    
    # Extract components
    private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
        pfx_data,
        pfx_password.encode() if pfx_password else None,
        backend=default_backend()
    )
    
    # Get private key bytes (unencrypted PEM)
    private_key_pem = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption()
    )
    
    # Get certificate bytes (PEM)
    cert_pem = certificate.public_bytes(Encoding.PEM)
    
    # Combine into single PEM file
    pem_bytes = private_key_pem + cert_pem
    
    # Calculate thumbprint
    cert_der = certificate.public_bytes(Encoding.DER)
    thumbprint = hashlib.sha1(cert_der).hexdigest().upper()
    
    # Write PEM file if path provided
    if pem_path is None:
        pem_path = pfx_path.replace('.pfx', '.pem')
    
    with open(pem_path, 'wb') as f:
        f.write(pem_bytes)
    
    return pem_path, thumbprint, pem_bytes

# Usage
pem_path, thumbprint, _ = convert_pfx_to_pem(
    "app_cert.pfx", 
    "password123"
)
print(f"PEM: {pem_path}, Thumbprint: {thumbprint}")
```

[VERIFIED] (SPAUTH-SC-BLOG-GRAPHCERT)

## 3. Client Assertion JWT Creation

The client assertion is a JWT that proves the client possesses the private key.

### Required Claims

| Claim | Value              | Description                                                    |
|-------|--------------------|-----------------------------------------------------------------|
| aud   | Token endpoint URL | `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token` |
| iss   | client_id          | Application (client) ID                                        |
| sub   | client_id          | Same as issuer                                                 |
| jti   | UUID               | Unique identifier (prevents replay)                            |
| nbf   | Unix timestamp     | Current time                                                   |
| exp   | Unix timestamp     | Current time + 5-10 minutes                                    |

### Python Implementation

```python
import jwt
import uuid
import time
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend

def create_client_assertion(
    client_id: str,
    tenant_id: str,
    private_key_pem: bytes,
    thumbprint: str
) -> str:
    """
    Create a signed client assertion JWT.
    
    Args:
        client_id: Azure AD application client ID
        tenant_id: Azure AD tenant ID
        private_key_pem: Private key in PEM format
        thumbprint: Certificate thumbprint (hex, uppercase)
    
    Returns:
        Signed JWT string
    """
    # Token endpoint is the audience
    token_endpoint = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    # Current time
    now = int(time.time())
    
    # JWT payload
    payload = {
        "aud": token_endpoint,
        "iss": client_id,
        "sub": client_id,
        "jti": str(uuid.uuid4()),
        "nbf": now,
        "exp": now + 600  # 10 minutes
    }
    
    # JWT header with thumbprint
    headers = {
        "x5t": thumbprint_to_x5t(thumbprint)
    }
    
    # Load private key
    private_key = load_pem_private_key(
        private_key_pem,
        password=None,
        backend=default_backend()
    )
    
    # Sign JWT
    assertion = jwt.encode(
        payload,
        private_key,
        algorithm="RS256",
        headers=headers
    )
    
    return assertion

def thumbprint_to_x5t(thumbprint_hex: str) -> str:
    """Convert hex thumbprint to Base64URL x5t format."""
    thumbprint_bytes = bytes.fromhex(thumbprint_hex)
    return base64.urlsafe_b64encode(thumbprint_bytes).rstrip(b'=').decode('ascii')
```

### Using the Assertion

```python
import requests

def get_token_with_certificate(
    client_id: str,
    tenant_id: str,
    scope: str,
    assertion: str
) -> dict:
    """Exchange client assertion for access token."""
    
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    data = {
        "client_id": client_id,
        "scope": scope,
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": assertion,
        "grant_type": "client_credentials"
    }
    
    response = requests.post(token_url, data=data)
    return response.json()
```

[VERIFIED] (SPAUTH-SC-MSFT-CERTCREDS)

## 4. RSA Signing Process

### How RS256 Works

1. **Input**: `base64url(header) + "." + base64url(payload)`
2. **Hash**: Compute SHA-256 of input
3. **Sign**: Encrypt hash with RSA private key using PKCS#1 v1.5 padding
4. **Output**: Base64URL-encoded signature

### Python Low-Level Example

```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
import base64
import json

def sign_jwt_manually(header: dict, payload: dict, private_key_pem: bytes) -> str:
    """Create JWT with manual signing (educational example)."""
    
    # Encode header and payload
    header_b64 = base64.urlsafe_b64encode(
        json.dumps(header).encode()
    ).rstrip(b'=').decode()
    
    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).rstrip(b'=').decode()
    
    # Create signing input
    signing_input = f"{header_b64}.{payload_b64}".encode()
    
    # Load private key
    private_key = load_pem_private_key(private_key_pem, password=None)
    
    # Sign with RS256 (RSA + SHA-256)
    signature = private_key.sign(
        signing_input,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    
    # Encode signature
    signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"
```

[VERIFIED] (SPAUTH-SC-RFC-7515)

## 5. Key Rotation Considerations

### Certificate Expiration

- Certificates have validity periods (typically 1-3 years)
- Must rotate before expiration to avoid service disruption
- Azure AD supports multiple certificates per app registration

### Rotation Strategy

1. **Add new certificate** to app registration (before old expires)
2. **Update application** to use new certificate
3. **Test** authentication works with new certificate
4. **Remove old certificate** after transition period

### Python: Check Certificate Expiration

```python
from cryptography import x509
from datetime import datetime, timezone

def check_certificate_expiration(cert_path: str) -> dict:
    """Check certificate validity dates."""
    with open(cert_path, 'rb') as f:
        cert = x509.load_pem_x509_certificate(f.read())
    
    now = datetime.now(timezone.utc)
    
    return {
        "not_valid_before": cert.not_valid_before_utc,
        "not_valid_after": cert.not_valid_after_utc,
        "is_valid": cert.not_valid_before_utc <= now <= cert.not_valid_after_utc,
        "days_until_expiry": (cert.not_valid_after_utc - now).days
    }

# Check
info = check_certificate_expiration("cert.pem")
print(f"Expires in {info['days_until_expiry']} days")
```

## SDK Examples (Python)

### MSAL with Certificate

```python
from msal import ConfidentialClientApplication

# Load certificate
with open("private_key.pem", "r") as f:
    private_key = f.read()

app = ConfidentialClientApplication(
    client_id="YOUR_CLIENT_ID",
    authority="https://login.microsoftonline.com/YOUR_TENANT_ID",
    client_credential={
        "thumbprint": "YOUR_CERT_THUMBPRINT",
        "private_key": private_key
    }
)

# MSAL handles assertion creation internally
result = app.acquire_token_for_client(
    scopes=["https://graph.microsoft.com/.default"]
)
```

### Office365-REST-Python-Client

```python
from office365.sharepoint.client_context import ClientContext

# Library handles PFX loading and assertion creation
ctx = ClientContext(site_url).with_client_certificate(
    tenant="YOUR_TENANT_ID",
    client_id="YOUR_CLIENT_ID",
    thumbprint="YOUR_CERT_THUMBPRINT",
    cert_path="cert.pem"
)
```

## Error Responses

- **AADSTS700027**: Client assertion contains invalid signature
- **AADSTS700016**: Application not found (wrong client_id)
- **AADSTS7000215**: Invalid client secret/certificate
- **AADSTS700024**: Client assertion is not within valid time range

## Limitations and Known Issues

- [COMMUNITY] Self-signed certificates work but require manual trust configuration (SPAUTH-SC-BLOG-GRAPHCERT)
- Certificate must be uploaded to Azure AD before use
- SNI (Server Name Indication) may cause issues with some proxy configurations

## Gotchas and Quirks

- `x5t` is Base64URL of SHA-1, not hex string
- Assertion `exp` should be short (5-10 min) to limit exposure window
- Private key must be RSA; EC keys require different algorithm (ES256)

## Sources

**Primary:**
- SPAUTH-SC-MSFT-CERTCREDS: Certificate credentials
- SPAUTH-SC-RFC-7515: RFC 7515 - JSON Web Signature (JWS)

**Community:**
- SPAUTH-SC-BLOG-GRAPHCERT: Microsoft Graph using MSAL with Python and Certificate Authentication

## Document History

**[2026-03-14 17:00]**
- Initial document created
- Cryptographic operations documented with Python examples
- PFX conversion and assertion creation covered
