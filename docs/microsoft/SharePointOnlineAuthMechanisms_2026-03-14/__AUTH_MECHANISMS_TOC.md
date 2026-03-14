# TOC: SharePoint/Graph Authentication Mechanisms Deep Dive

**Doc ID**: SPAUTH-TOC
**Goal**: Exhaustive documentation of HOW authentication mechanisms work internally
**Strategy**: MCPI (Most Complete Point of Information)
**Domain**: SOFTWARE
**Research stats**: 50m net | 28 sources | 7 topic files
**Coverage**: 100% (all dimensions covered)

## File Index

### Research Documents (IN = Internal Workings)

- [_INFO_SPAUTH-IN01_OAUTH_FLOWS.md](_INFO_SPAUTH-IN01_OAUTH_FLOWS.md) - OAuth 2.0 protocol flows
- [_INFO_SPAUTH-IN02_TOKEN_STRUCTURE.md](_INFO_SPAUTH-IN02_TOKEN_STRUCTURE.md) - JWT token anatomy
- [_INFO_SPAUTH-IN03_CRYPTO_OPERATIONS.md](_INFO_SPAUTH-IN03_CRYPTO_OPERATIONS.md) - Certificate and signing
- [_INFO_SPAUTH-IN04_SDK_INTERNALS.md](_INFO_SPAUTH-IN04_SDK_INTERNALS.md) - Azure Identity/MSAL internals
- [_INFO_SPAUTH-IN05_SECURITY.md](_INFO_SPAUTH-IN05_SECURITY.md) - Security considerations
- [_INFO_SPAUTH-IN06_OPERATIONAL.md](_INFO_SPAUTH-IN06_OPERATIONAL.md) - Caching, lifetime, debugging
- [_INFO_SPAUTH-IN07_AZURE_PERMISSION_REQUIREMENTS.md](_INFO_SPAUTH-IN07_AZURE_PERMISSION_REQUIREMENTS.md) - API permissions reference

### Implementation Guides (AM = Auth Method)

- [_INFO_SPAUTH-AM01_CERTIFICATE_CREDENTIALS.md](_INFO_SPAUTH-AM01_CERTIFICATE_CREDENTIALS.md) - Certificate auth (SharePoint required)
- [_INFO_SPAUTH-AM02_CLIENT_SECRET.md](_INFO_SPAUTH-AM02_CLIENT_SECRET.md) - Client secret (Graph only)
- [_INFO_SPAUTH-AM03_MANAGED_IDENTITY.md](_INFO_SPAUTH-AM03_MANAGED_IDENTITY.md) - Azure Managed Identity
- [_INFO_SPAUTH-AM04_INTERACTIVE_BROWSER.md](_INFO_SPAUTH-AM04_INTERACTIVE_BROWSER.md) - Browser login flow
- [_INFO_SPAUTH-AM05_DEVICE_CODE.md](_INFO_SPAUTH-AM05_DEVICE_CODE.md) - Device code flow
- [_INFO_SPAUTH-AM06_AUTHORIZATION_CODE.md](_INFO_SPAUTH-AM06_AUTHORIZATION_CODE.md) - OAuth auth code
- [_INFO_SPAUTH-AM07_USERNAME_PASSWORD.md](_INFO_SPAUTH-AM07_USERNAME_PASSWORD.md) - ROPC (deprecated)
- [_INFO_SPAUTH-AM08_ON_BEHALF_OF.md](_INFO_SPAUTH-AM08_ON_BEHALF_OF.md) - OBO flow
- [_INFO_SPAUTH-AM09_DEVELOPMENT_TOOLS.md](_INFO_SPAUTH-AM09_DEVELOPMENT_TOOLS.md) - Dev tool credentials

### Supporting Documents

- [__AUTH_MECHANISMS_SOURCES.md](__AUTH_MECHANISMS_SOURCES.md) - Source references
- [_INFO_SPAUTH_REVIEW.md](_INFO_SPAUTH_REVIEW.md) - Review findings
- [STRUT_AUTH_MECHANISMS.md](STRUT_AUTH_MECHANISMS.md) - Research plan
- [TASKS_AUTH_MECHANISMS_RESEARCH.md](TASKS_AUTH_MECHANISMS_RESEARCH.md) - Task tracking

### Parent Document

- [_INFO_SHAREPOINT_AUTH_MECHANISMS_PYTHON.md](../_INFO_SHAREPOINT_AUTH_MECHANISMS_PYTHON.md) - Quick reference with all auth methods

## Summary

This research documents the internal workings of authentication mechanisms for Microsoft Graph and SharePoint APIs, focusing on OAuth 2.0 protocol flows, JWT token structure, cryptographic operations, and SDK internals. The research covers three dimensions: technical (protocol mechanics), security (token protection and credential security), and operational (caching, lifetime, debugging). Key topics include client credentials flow with certificate assertions, managed identity via IMDS endpoint, device code polling mechanism, token refresh strategies, and the DefaultAzureCredential chain order. Each topic file provides protocol-level detail with Python code examples using MSAL and Azure Identity SDKs.

## Dimension 1: Technical

### Topic 1.1: OAuth 2.0 Protocol Flows
- **File**: [`_INFO_SPAUTH-IN01_OAUTH_FLOWS.md`](_INFO_SPAUTH-IN01_OAUTH_FLOWS.md)
- **Status**: [x] Complete
- **Sources**: SPAUTH-SC-RFC-6749, SPAUTH-SC-MSFT-CLIENTCREDS, SPAUTH-SC-MSFT-AUTHCODE, SPAUTH-SC-MSFT-DEVICECODE, SPAUTH-SC-MSFT-OBO
- **Topics**:
  - Authorization Code Flow with PKCE (step-by-step)
  - Client Credentials Flow (secret vs certificate)
  - Device Code Flow (polling mechanism)
  - On-Behalf-Of Flow (token exchange)
  - Implicit Flow (deprecated, why)
  - Resource Owner Password (ROPC, why deprecated)

### Topic 1.2: JWT Token Structure
- **File**: [`_INFO_SPAUTH-IN02_TOKEN_STRUCTURE.md`](_INFO_SPAUTH-IN02_TOKEN_STRUCTURE.md)
- **Status**: [x] Complete
- **Sources**: SPAUTH-SC-RFC-7519, SPAUTH-SC-RFC-7515, SPAUTH-SC-RFC-7517, SPAUTH-SC-JWTIO
- **Topics**:
  - JWT anatomy (header.payload.signature)
  - Base64URL encoding
  - Standard claims (iss, sub, aud, exp, iat, nbf)
  - Microsoft-specific claims (tid, oid, roles, scp)
  - Access token vs ID token
  - JWS signing algorithms (RS256, ES256)

### Topic 1.3: Cryptographic Operations
- **File**: [`_INFO_SPAUTH-IN03_CRYPTO_OPERATIONS.md`](_INFO_SPAUTH-IN03_CRYPTO_OPERATIONS.md)
- **Status**: [x] Complete
- **Sources**: SPAUTH-SC-MSFT-CERTCREDS, SPAUTH-SC-RFC-7515, SPAUTH-SC-BLOG-GRAPHCERT
- **Topics**:
  - Certificate-based client assertion creation
  - RSA signing with private key
  - X.509 certificate thumbprint calculation
  - PFX to PEM conversion
  - Client assertion JWT structure
  - Key rotation considerations

### Topic 1.4: SDK Internals
- **File**: [`_INFO_SPAUTH-IN04_SDK_INTERNALS.md`](_INFO_SPAUTH-IN04_SDK_INTERNALS.md)
- **Status**: [x] Complete
- **Sources**: SPAUTH-SC-MSFT-AZIDREADME, SPAUTH-SC-GH-AZIDSRC, SPAUTH-SC-MSFT-MSALPYTHON, SPAUTH-SC-GH-MSALSRC
- **Topics**:
  - DefaultAzureCredential chain order
  - MSAL ConfidentialClientApplication internals
  - MSAL PublicClientApplication internals
  - Token acquisition flow in MSAL
  - Azure Identity credential wrapper pattern
  - Office365-REST-Python-Client with_access_token adapter

## Dimension 2: Security

### Topic 2.1: Security Considerations
- **File**: [`_INFO_SPAUTH-IN05_SECURITY.md`](_INFO_SPAUTH-IN05_SECURITY.md)
- **Status**: [x] Complete
- **Sources**: SPAUTH-SC-MSFT-CERTCREDS, SPAUTH-SC-MSFT-MIWORK, SPAUTH-SC-MSFT-PROTOCOLS
- **Topics**:
  - Certificate vs client secret security comparison
  - Token storage best practices
  - Managed Identity security model (no credentials in code)
  - Token revocation mechanisms
  - Conditional Access interaction
  - MFA and authentication flows
  - Scope of access (Sites.Selected vs Sites.FullControl)

## Dimension 3: Operational

### Topic 3.1: Operational Patterns
- **File**: [`_INFO_SPAUTH-IN06_OPERATIONAL.md`](_INFO_SPAUTH-IN06_OPERATIONAL.md)
- **Status**: [x] Complete
- **Sources**: SPAUTH-SC-MSFT-TOKENLIFE, SPAUTH-SC-MSFT-REFRESH, SPAUTH-SC-MSFT-MSALCACHE, SPAUTH-SC-DEV-MSALCACHE
- **Topics**:
  - Token caching strategies (in-memory, persistent)
  - MSAL token cache data structure
  - Token lifetime defaults and configuration
  - Refresh token behavior and rotation
  - Proactive token refresh (before expiration)
  - Error handling and retry patterns
  - Multi-tenant vs single-tenant configuration
  - Debugging authentication issues

## Cross-Cutting Topics

### Managed Identity Deep Dive
- **Covered in**: Topics 1.1, 1.4, 2.1
- **Key sources**: SPAUTH-SC-MSFT-MIWORK, SPAUTH-SC-MSFT-MITOKEN
- **Focus**: IMDS endpoint (169.254.169.254), internal certificate, token acquisition without credentials

### SharePoint-Specific Considerations
- **Covered in**: Topics 1.3, 2.1
- **Key sources**: SPAUTH-SC-MSFT-CLIENTCREDS, SPAUTH-SC-PYPI-O365
- **Focus**: Certificate requirement for app-only, token resource URL differences

### API Permission Requirements
- **File**: [`_INFO_SPAUTH-IN07_AZURE_PERMISSION_REQUIREMENTS.md`](_INFO_SPAUTH-IN07_AZURE_PERMISSION_REQUIREMENTS.md)
- **Status**: [x] Complete
- **Sources**: SPAUTH-SC-MSFT-GRAPHPERM, SPAUTH-SC-MSFT-SPPERM, SPAUTH-SC-MSFT-SITESSELECTED
- **Topics**:
  - Application vs Delegated permissions
  - Microsoft Graph vs SharePoint REST API
  - Sites.Read.All, Sites.ReadWrite.All, Sites.Selected
  - Permission matrix by auth method
  - Sites.Selected configuration (per-site grants)
  - Common permission scenarios

## File Naming Convention

```
_INFO_SPAUTH-IN[XX]_[TOPIC].md
```

- XX = sequential number (01-07)
- TOPIC = descriptive name in SCREAMING_SNAKE_CASE

## Document History

**[2026-03-14 19:30]**
- Added: IN07 Azure Permission Requirements (cross-cutting reference)
- Updated: Research stats to 7 topic files

**[2026-03-14 17:15]**
- Added: File Index with links to all 21 documents
- Added: Links in dimension topic sections
- Added: Implementation Guides section (AM01-AM09)

**[2026-03-14 17:20]**
- All 6 topic files completed
- Research stats added
- Coverage verified at 100%

**[2026-03-14 16:40]**
- Initial TOC created
- 6 topic files planned across 3 dimensions
- Summary written
