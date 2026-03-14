# Sources: SharePoint/Graph Authentication Mechanisms Deep Dive

**Doc ID**: SPAUTH-SOURCES
**Research Date**: 2026-03-14
**Version Scope**: Microsoft Entra ID / Azure AD (2026), OAuth 2.0/2.1, MSAL Python 1.x, Azure Identity 1.x
**Preflight Accuracy**: [pending verification]

## Source Statistics

- Total sources: 28
- Tier 1 (Official/RFCs): 12
- Tier 2 (Vendor blogs/GitHub): 8
- Tier 3 (Community): 8

## Tier 1: Official Documentation and RFCs

### OAuth 2.0 Protocol Specifications

- **SPAUTH-SC-RFC-6749**: RFC 6749 - The OAuth 2.0 Authorization Framework
  - https://datatracker.ietf.org/doc/html/rfc6749
  - Accessed: 2026-03-14
  - Covers: Authorization code, implicit, client credentials, resource owner password flows

- **SPAUTH-SC-RFC-7519**: RFC 7519 - JSON Web Token (JWT)
  - https://datatracker.ietf.org/doc/html/rfc7519
  - Accessed: 2026-03-14
  - Covers: JWT structure, claims, encoding, signature

- **SPAUTH-SC-RFC-7515**: RFC 7515 - JSON Web Signature (JWS)
  - https://datatracker.ietf.org/doc/html/rfc7515
  - Accessed: 2026-03-14
  - Covers: JWS structure, signing algorithms

- **SPAUTH-SC-RFC-7517**: RFC 7517 - JSON Web Key (JWK)
  - https://datatracker.ietf.org/doc/html/rfc7517
  - Accessed: 2026-03-14
  - Covers: Key representation, key sets

### Microsoft Identity Platform Documentation

- **SPAUTH-SC-MSFT-CLIENTCREDS**: OAuth 2.0 client credentials flow
  - https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-client-creds-grant-flow
  - Accessed: 2026-03-14
  - Covers: Client credentials with secret, certificate, federated credential

- **SPAUTH-SC-MSFT-AUTHCODE**: OAuth 2.0 authorization code flow
  - https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow
  - Accessed: 2026-03-14
  - Covers: Auth code flow, PKCE, refresh tokens

- **SPAUTH-SC-MSFT-DEVICECODE**: OAuth 2.0 device authorization grant
  - https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-device-code
  - Accessed: 2026-03-14
  - Covers: Device code flow for browserless devices

- **SPAUTH-SC-MSFT-OBO**: OAuth 2.0 On-Behalf-Of flow
  - https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-on-behalf-of-flow
  - Accessed: 2026-03-14
  - Covers: Token exchange for downstream APIs

- **SPAUTH-SC-MSFT-PROTOCOLS**: OAuth 2.0 and OpenID Connect protocols
  - https://learn.microsoft.com/en-us/entra/identity-platform/v2-protocols
  - Accessed: 2026-03-14
  - Covers: Protocol overview, endpoints, token types

- **SPAUTH-SC-MSFT-CERTCREDS**: Certificate credentials
  - https://learn.microsoft.com/en-us/entra/identity-platform/certificate-credentials
  - Accessed: 2026-03-14
  - Covers: Creating client assertions with certificates

- **SPAUTH-SC-MSFT-TOKENLIFE**: Configurable token lifetimes
  - https://learn.microsoft.com/en-us/entra/identity-platform/configurable-token-lifetimes
  - Accessed: 2026-03-14
  - Covers: Access token, refresh token, session token lifetimes

- **SPAUTH-SC-MSFT-REFRESH**: Refresh tokens
  - https://learn.microsoft.com/en-us/entra/identity-platform/refresh-tokens
  - Accessed: 2026-03-14
  - Covers: Refresh token behavior, rotation, lifetime

### Managed Identity Documentation

- **SPAUTH-SC-MSFT-MIWORK**: How managed identities work with VMs
  - https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/how-managed-identities-work-vm
  - Accessed: 2026-03-14
  - Covers: IMDS endpoint, system vs user-assigned, internal certificate

- **SPAUTH-SC-MSFT-MITOKEN**: Use managed identities to acquire access token
  - https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/how-to-use-vm-token
  - Accessed: 2026-03-14
  - Covers: REST call to IMDS, token acquisition

- **SPAUTH-SC-MSFT-MIOVERVIEW**: What are managed identities?
  - https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview
  - Accessed: 2026-03-14
  - Covers: Managed identity concepts, supported services

## Tier 2: Vendor Blogs and GitHub

### Azure Identity SDK

- **SPAUTH-SC-MSFT-AZIDREADME**: Azure Identity client library for Python
  - https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme
  - Accessed: 2026-03-14
  - Covers: Credential classes, DefaultAzureCredential chain

- **SPAUTH-SC-GH-AZIDSRC**: Azure Identity Python source code
  - https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/identity/azure-identity
  - Accessed: 2026-03-14
  - Covers: Credential implementation internals

- **SPAUTH-SC-MSFT-CREDCHAINS**: Credential chains in Azure Identity
  - https://learn.microsoft.com/en-us/azure/developer/python/sdk/authentication/credential-chains
  - Accessed: 2026-03-14
  - Covers: DefaultAzureCredential order, ChainedTokenCredential

### MSAL Python

- **SPAUTH-SC-MSFT-MSALPYTHON**: MSAL for Python overview
  - https://learn.microsoft.com/en-us/entra/msal/python/
  - Accessed: 2026-03-14
  - Covers: PublicClientApplication, ConfidentialClientApplication

- **SPAUTH-SC-MSFT-MSALCACHE**: MSAL Python token cache serialization
  - https://learn.microsoft.com/en-us/entra/msal/python/advanced/msal-python-token-cache-serialization
  - Accessed: 2026-03-14
  - Covers: Custom token cache, persistence

- **SPAUTH-SC-GH-MSALSRC**: MSAL Python source code
  - https://github.com/AzureAD/microsoft-authentication-library-for-python
  - Accessed: 2026-03-14
  - Covers: Token cache internals, auth flows implementation

- **SPAUTH-SC-GH-MSALCACHE**: MSAL Python token_cache.py
  - https://github.com/AzureAD/microsoft-authentication-library-for-python/blob/dev/msal/token_cache.py
  - Accessed: 2026-03-14
  - Covers: Token cache data structure, serialization

### Office365-REST-Python-Client

- **SPAUTH-SC-PYPI-O365**: Office365-REST-Python-Client PyPI
  - https://pypi.org/project/Office365-REST-Python-Client/
  - Accessed: 2026-03-14
  - Covers: Auth methods, ClientContext usage

- **SPAUTH-SC-GH-O365**: Office365-REST-Python-Client GitHub
  - https://github.com/vgrem/Office365-REST-Python-Client
  - Accessed: 2026-03-14
  - Covers: Auth examples, with_access_token pattern

## Tier 3: Community Sources

- **SPAUTH-SC-SO-IMDS**: Stack Overflow - How does IMDS get tokens
  - https://stackoverflow.com/questions/77400613/how-does-azure-instance-metadata-service-imds-gets-the-token-from-aad-for-mana
  - Accessed: 2026-03-14
  - Covers: [COMMUNITY] IMDS internal workings

- **SPAUTH-SC-DEV-MSALCACHE**: DEV.to - Python MSAL Token Cache for Confidential Clients
  - https://dev.to/425show/a-python-msal-token-cache-for-confidential-clients-29c9
  - Accessed: 2026-03-14
  - Covers: [COMMUNITY] Token cache persistence patterns

- **SPAUTH-SC-BLOG-GRAPHCERT**: Blog - Microsoft Graph using MSAL with Python and Certificate
  - https://blog.darrenjrobinson.com/microsoft-graph-using-msal-with-python-and-certificate-authentication/
  - Accessed: 2026-03-14
  - Covers: [COMMUNITY] Certificate auth implementation

- **SPAUTH-SC-JWTIO**: JWT.io - JWT Debugger
  - https://jwt.io/
  - Accessed: 2026-03-14
  - Covers: [COMMUNITY] Token inspection, claims visualization

- **SPAUTH-SC-STYTCH-JWT**: Stytch Blog - Developer's guide to RFC 7519
  - https://stytch.com/blog/rfc-7519-jwt-part-1/
  - Accessed: 2026-03-14
  - Covers: [COMMUNITY] JWT structure explanation

- **SPAUTH-SC-CITADEL-MI**: Azure Citadel - Managed Identities
  - https://www.azurecitadel.com/vm/identity/
  - Accessed: 2026-03-14
  - Covers: [COMMUNITY] IMDS endpoint usage examples

- **SPAUTH-SC-AUTH0-CLIENTCREDS**: Auth0 Docs - Client Credentials Flow
  - https://auth0.com/docs/get-started/authentication-and-authorization-flow/client-credentials-flow
  - Accessed: 2026-03-14
  - Covers: [COMMUNITY] Client credentials flow explanation

- **SPAUTH-SC-OAUTHNET**: OAuth.net - OAuth 2.0
  - https://oauth.net/2/
  - Accessed: 2026-03-14
  - Covers: [COMMUNITY] OAuth 2.0 overview, grant types

## Related Topics (Not In Scope)

- SharePoint App-Only via ACS (legacy, deprecated)
- PnP PowerShell authentication (different SDK)
- Microsoft Graph SDK for Python (separate client)
- Azure AD B2C flows (consumer identity)

## Document History

**[2026-03-14 16:35]**
- Initial source collection
- 28 sources identified across 3 tiers
- Discovery platforms tested (all FREE access)
