# INFO: Copilot Retrieval API - Authentication and Permissions

**Doc ID**: COPRA-IN01
**Goal**: Document authentication methods, permissions, and security model

**Depends on:**
- `_INFO_COPRA_SOURCES.md [COPRA-IN01]` for source URLs
- `__INFO_COPRA-IN00_TOC.md [COPRA-IN01]` for topic scope

## Summary

The Retrieval API uses standard Microsoft Graph authentication with OAuth 2.0. It requires specific Microsoft Graph permissions depending on the data source. Security trimming via RBAC ensures users only retrieve content they have access to.

**Key Facts [VERIFIED]:**
- Uses Microsoft Graph authentication (same as other Graph APIs)
- SharePoint/OneDrive: Files.Read.All + Sites.Read.All
- Copilot connectors: ExternalItem.Read.All
- Supports both delegated and application permissions
- RBAC security trimming at query time

**Use Cases:**
- User-context retrieval (delegated permissions)
- Service-to-service retrieval (application permissions)
- Multi-tenant applications

## Quick Reference

**Permissions by Data Source:**
- SharePoint: `Files.Read.All` + `Sites.Read.All`
- OneDrive: `Files.Read.All` + `Sites.Read.All`
- Copilot connectors: `ExternalItem.Read.All`

**Token endpoint:** `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token`

**Scopes:** `https://graph.microsoft.com/.default` or specific permissions

## Required Permissions

### SharePoint and OneDrive [VERIFIED]

Both data sources require the same permissions:

**Required permissions (both needed):**
- `Files.Read.All` - Read files in all site collections
- `Sites.Read.All` - Read items in all site collections

**Permission types supported:**
- Delegated (user context)
- Application (service context)

### Copilot Connectors [VERIFIED]

**Required permission:**
- `ExternalItem.Read.All` - Read external items

**Permission types supported:**
- Delegated (user context)
- Application (service context)

### Permission Selection Guidance [VERIFIED]

Choose the least privileged permission that meets your needs:
- Use delegated permissions when acting on behalf of a signed-in user
- Use application permissions for background services/daemons
- Higher privileged permissions only if app requires broader access

## Delegated vs Application Permissions

### Delegated Permissions [VERIFIED]

**When to use:**
- User is signed in and present
- Results should be scoped to user's access
- Interactive applications (web apps, desktop apps)

**Behavior:**
- Token represents both app and user
- Results filtered by user's RBAC permissions
- Requires user consent or admin consent

### Application Permissions [VERIFIED]

**When to use:**
- No user signed in (daemon, service)
- Background processing
- Admin-level operations

**Behavior:**
- Token represents only the application
- Requires admin consent
- Still respects RBAC for result filtering

## App Registration in Azure Portal

### Registration Steps [VERIFIED]

1. Go to Azure Portal > Microsoft Entra ID > App registrations
2. Click "New registration"
3. Enter application name
4. Select supported account types:
   - Single tenant: This organization only
   - Multi-tenant: Any Microsoft Entra directory
5. Configure redirect URI (for delegated flow)
6. Click "Register"

### Configure API Permissions [VERIFIED]

1. Go to "API permissions" in app registration
2. Click "Add a permission"
3. Select "Microsoft Graph"
4. Choose permission type:
   - Delegated permissions (user context)
   - Application permissions (service context)
5. Search and add required permissions:
   - Files.Read.All
   - Sites.Read.All
   - ExternalItem.Read.All (if using connectors)
6. Click "Grant admin consent" (for application permissions)

### Client Credentials [VERIFIED]

For application permissions, create a client secret or certificate:

**Client Secret:**
1. Go to "Certificates & secrets"
2. Click "New client secret"
3. Set description and expiration
4. Copy the secret value immediately (shown only once)

**Certificate (recommended for production):**
1. Go to "Certificates & secrets"
2. Upload a certificate (.cer, .pem, or .crt)

## Token Acquisition

### Delegated Flow (Authorization Code) [VERIFIED]

For interactive user authentication:

```
GET https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize
?client_id={client_id}
&response_type=code
&redirect_uri={redirect_uri}
&scope=Files.Read.All Sites.Read.All
```

Exchange code for token:
```
POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

client_id={client_id}
&scope=https://graph.microsoft.com/.default
&code={authorization_code}
&redirect_uri={redirect_uri}
&grant_type=authorization_code
&client_secret={client_secret}
```

### Application Flow (Client Credentials) [VERIFIED]

For service-to-service authentication:

```
POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

client_id={client_id}
&scope=https://graph.microsoft.com/.default
&client_secret={client_secret}
&grant_type=client_credentials
```

### Device Code Flow [VERIFIED]

For devices without browser (CLI tools, IoT):

```
POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/devicecode
Content-Type: application/x-www-form-urlencoded

client_id={client_id}
&scope=Files.Read.All Sites.Read.All
```

User visits the verification URL and enters the code.

## Security Trimming (RBAC) [VERIFIED]

The Retrieval API enforces role-based access control at query time.

**How it works:**
- Results only returned if user has access to the content
- SharePoint permissions honored
- Sensitivity labels respected
- Information barriers enforced

**Implications:**
- Same query, different users = different results
- No data leakage between users/departments
- Organizational boundaries within tenant respected

## Sensitivity Labels in Response [VERIFIED]

When retrieving from SharePoint/OneDrive, the response includes sensitivity label information:

```json
{
  "sensitivityLabel": {
    "sensitivityLabelId": "f71f1f74-bf1f-4e6b-b266-c777ea76e2s8",
    "displayName": "Confidential\\Any User (No Protection)",
    "toolTip": "Data is classified as Confidential...",
    "priority": 4,
    "color": "#FF8C00"
  }
}
```

**Use case:** Display label to users, make decisions based on sensitivity level.

## Compliance and Governance [VERIFIED]

The Retrieval API inherits Microsoft 365 compliance features:

**Automatic enforcement:**
- Existing permissions respected
- Sensitivity labels honored
- Compliance controls active
- Audit logging enabled
- Monitoring and policy enforcement

**Data Loss Prevention (DLP):**
- Files excluded by DLP policies are not indexed
- Not returned in retrieval results

**No data egress:**
- Content stays in Microsoft 365
- Only text extracts returned (not full documents)

## Sources

**Primary:**
- `COPRA-IN01-SC-MSFT-AUTH`: https://learn.microsoft.com/en-us/graph/auth/auth-concepts
- `COPRA-IN01-SC-MSFT-AUTHPROV`: https://learn.microsoft.com/en-us/graph/sdks/choose-authentication-providers
- `COPRA-IN01-SC-MSFT-OVERVIEW`: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api/ai-services/retrieval/overview

## Document History

**[2026-01-29 09:10]**
- Initial document created
- All 7 TOC items documented
- Token acquisition flows documented
- Security trimming explained
