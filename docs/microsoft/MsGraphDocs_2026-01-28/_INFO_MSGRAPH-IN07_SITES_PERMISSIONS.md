# INFO: Microsoft Graph API - Permissions Resource and Sites.Selected

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for permission management endpoints and Sites.Selected mechanics
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_MSGRAPH-IN00_TOC.md [MSGRAPH-IN01]` for endpoint inventory
- `_INFO_MSGRAPH_DRIVEITEMS_SHARING.md [MSGRAPH-IN01]` for driveItem permissions

## Summary

**Use cases**:
- Grant application-only access to specific SharePoint sites (Sites.Selected)
- Build multi-tenant apps with granular per-site permissions
- Implement least-privilege access patterns for enterprise applications
- Audit which apps have access to which sites programmatically
- Revoke application access when integrations are decommissioned
- Manage permissions at site, list, and item levels

**Key findings**:
- Sites.Selected requires 3 steps: consent scope, grant permission, acquire token
- Sites.Selected does NOT work with Search API or some delta queries - use broader scopes
- Site permissions API creates app permissions only, not user permissions
- Assigning permissions at list/item level breaks inheritance (50K limit)
- Site-level permissions do NOT break inheritance (root of hierarchy)
- Delegated calls require SharePoint Administrator role for site permissions
- Three roles available: read, write, fullcontrol

## Quick Reference Summary

**Endpoints covered**: 7 permission-related methods

**Site Permissions**:
- `GET /sites/{id}/permissions` - List site permissions
- `GET /sites/{id}/permissions/{id}` - Get site permission
- `POST /sites/{id}/permissions` - Create site permission (app only)
- `PATCH /sites/{id}/permissions/{id}` - Update site permission
- `DELETE /sites/{id}/permissions/{id}` - Delete site permission

**DriveItem Permissions** (covered in MSGRAPH-IN01):
- `GET /drives/{id}/items/{id}/permissions` - List item permissions
- `PATCH /drives/{id}/items/{id}/permissions/{id}` - Update item permission
- `DELETE /drives/{id}/items/{id}/permissions/{id}` - Delete item permission

**Required Permissions**:
- Site permissions: `Sites.FullControl.All` (delegated requires SharePoint Admin role)
- DriveItem permissions: `Files.ReadWrite.All`, `Sites.ReadWrite.All`
- Sites.Selected: Application-only, grants access to specific sites

## Sites.Selected Permission Model [VERIFIED]

### Overview

Sites.Selected is a granular permission model that allows applications to access specific SharePoint sites rather than all sites in the tenant.

**Key Characteristics**:
- Application-only permission (not delegated)
- Requires explicit grant per site
- Three-step access model
- Supports multiple resource levels (site, list, listItem, folder, file)

### Three-Step Access Model [VERIFIED]

1. **Consent** - Admin consents `Sites.Selected` scope in Microsoft Entra ID
2. **Grant** - Site owner grants app permission via `POST /sites/{id}/permissions`
3. **Token** - App acquires token with `Sites.Selected` scope

All three steps must complete for access. Missing any step = no access.

### Available Selected Scopes [VERIFIED]

- `Sites.Selected` - Site-level access
- `Lists.SelectedOperations.Selected` - List-level access
- `ListItems.SelectedOperations.Selected` - ListItem-level access
- `Files.SelectedOperations.Selected` - File-level access (document libraries only)

### Roles [VERIFIED]

- **read** - Read access to the resource
- **write** - Read and write access
- **fullcontrol** - Full control including permission management

### Access Inheritance [VERIFIED]

**Important**: Assigning permissions at list/item level breaks inheritance. Be mindful of SharePoint's unique permissions limits (50,000 per list).

Site-level permissions do NOT break inheritance (this is the root).

## Permission Resource Type [VERIFIED]

### JSON Schema

```json
{
  "id": "string",
  "roles": ["read | write | fullcontrol"],
  "grantedTo": { "@odata.type": "microsoft.graph.identitySet" },
  "grantedToIdentities": [{ "@odata.type": "microsoft.graph.identitySet" }],
  "grantedToIdentitiesV2": [{ "@odata.type": "microsoft.graph.sharePointIdentitySet" }],
  "grantedToV2": { "@odata.type": "microsoft.graph.sharePointIdentitySet" },
  "inheritedFrom": { "@odata.type": "microsoft.graph.itemReference" },
  "link": { "@odata.type": "microsoft.graph.sharingLink" },
  "invitation": { "@odata.type": "microsoft.graph.sharingInvitation" },
  "expirationDateTime": "datetime",
  "hasPassword": true
}
```

### Properties [VERIFIED]

- **id** (`string`) - Unique identifier
- **roles** (`string[]`) - Permission level: `read`, `write`, `fullcontrol`
- **grantedTo** (`identitySet`) - Deprecated, use grantedToV2
- **grantedToV2** (`sharePointIdentitySet`) - User, group, or application
- **grantedToIdentitiesV2** (`sharePointIdentitySet[]`) - Collection of identities
- **inheritedFrom** (`itemReference`) - Reference if inherited from parent

### SharePointIdentitySet Object [VERIFIED]

```json
{
  "application": {
    "id": "app-guid",
    "displayName": "Contoso App"
  },
  "user": {
    "id": "user-guid",
    "displayName": "John Doe",
    "email": "john@contoso.com"
  },
  "group": {
    "id": "group-guid",
    "displayName": "Sales Team"
  },
  "siteUser": {
    "id": "123",
    "displayName": "John Doe",
    "loginName": "i:0#.f|membership|john@contoso.com"
  },
  "siteGroup": {
    "id": "5",
    "displayName": "Site Members"
  }
}
```

## 1. GET /sites/{id}/permissions - List Site Permissions

### Description [VERIFIED]

Retrieves all permission objects for a site. Lists applications that have been granted access via Sites.Selected.

**Limitation**: Does not support retrieving permissions from SharePoint subsites.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/permissions
```

### Path Parameters

- **siteId** (`string`) - Site identifier (hostname,site-guid,web-guid format or just site GUID)

### Query Parameters

- **$select** - Select specific properties
- **$filter** - Filter results
- **$top** - Limit results
- **$skip** - Pagination offset

### Request Headers

- **Authorization**: `Bearer {token}`

### Request Example

```http
GET https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/permissions
Authorization: Bearer {token}
```

### Response JSON [VERIFIED]

```json
{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#Collection(permission)",
  "value": [
    {
      "id": "1",
      "roles": ["write"],
      "grantedToIdentitiesV2": [
        {
          "application": {
            "id": "89ea5c94-7736-4e25-95ad-3fa95f62b66e",
            "displayName": "Contoso Time Manager App"
          }
        }
      ]
    },
    {
      "id": "2",
      "roles": ["read"],
      "grantedToIdentitiesV2": [
        {
          "application": {
            "id": "12345678-abcd-efgh-ijkl-mnopqrstuvwx",
            "displayName": "Reporting Dashboard"
          }
        }
      ]
    }
  ]
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Sites
Get-MgSitePermission -SiteId $siteId
```

**C#**:
```csharp
var permissions = await graphClient.Sites["{site-id}"]
    .Permissions
    .GetAsync();
```

**JavaScript**:
```javascript
let permissions = await client.api('/sites/{site-id}/permissions').get();
```

**Python**:
```python
permissions = await graph_client.sites.by_site_id('site-id').permissions.get()
```

## 2. GET /sites/{id}/permissions/{id} - Get Site Permission

### Description [VERIFIED]

Retrieves a specific permission object from a site by permission ID.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/permissions/{permissionId}
```

### Path Parameters

- **siteId** (`string`) - Site identifier
- **permissionId** (`string`) - Permission identifier

### Request Headers

- **Authorization**: `Bearer {token}`

### Request Example

```http
GET https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/permissions/1
Authorization: Bearer {token}
```

### Response JSON [VERIFIED]

```json
{
  "id": "1",
  "roles": ["write"],
  "grantedToIdentitiesV2": [
    {
      "application": {
        "id": "89ea5c94-7736-4e25-95ad-3fa95f62b66e",
        "displayName": "Contoso Time Manager App"
      }
    }
  ]
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Sites
Get-MgSitePermission -SiteId $siteId -PermissionId $permissionId
```

**C#**:
```csharp
var permission = await graphClient.Sites["{site-id}"]
    .Permissions["{permission-id}"]
    .GetAsync();
```

**JavaScript**:
```javascript
let permission = await client.api('/sites/{site-id}/permissions/{perm-id}').get();
```

**Python**:
```python
permission = await graph_client.sites.by_site_id('site-id').permissions.by_permission_id('perm-id').get()
```

## 3. POST /sites/{id}/permissions - Create Site Permission

### Description [VERIFIED]

Creates a new permission object on a site. This endpoint is used to grant application access via Sites.Selected.

**Important**: This method can ONLY create application permissions, not user permissions.

**Delegated Access**: User must have SharePoint Administrator role or higher.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/sites/{siteId}/permissions
```

### Path Parameters

- **siteId** (`string`) - Site identifier

### Request Headers

- **Authorization**: `Bearer {token}`
- **Content-Type**: `application/json`

### Request Body

```json
{
  "roles": ["read | write | fullcontrol"],
  "grantedToIdentities": [
    {
      "application": {
        "id": "application-client-id",
        "displayName": "Application Name"
      }
    }
  ]
}
```

**Properties**:
- **roles** (`string[]`, required) - Permission level to grant
- **grantedToIdentities** (`identitySet[]`, required) - Application to grant access

### Request Example

```http
POST https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/permissions
Authorization: Bearer {token}
Content-Type: application/json

{
  "roles": ["write"],
  "grantedToIdentities": [
    {
      "application": {
        "id": "89ea5c94-7736-4e25-95ad-3fa95f62b66e",
        "displayName": "Contoso Time Manager App"
      }
    }
  ]
}
```

### Response JSON [VERIFIED]

```json
{
  "id": "1",
  "@deprecated.GrantedToIdentities": "GrantedToIdentities has been deprecated. Refer to GrantedToIdentitiesV2",
  "roles": ["write"],
  "grantedToIdentities": [
    {
      "application": {
        "id": "89ea5c94-7736-4e25-95ad-3fa95f62b66e",
        "displayName": "Contoso Time Manager App"
      }
    }
  ],
  "grantedToIdentitiesV2": [
    {
      "application": {
        "id": "89ea5c94-7736-4e25-95ad-3fa95f62b66e",
        "displayName": "Contoso Time Manager App"
      }
    }
  ]
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Sites

$params = @{
    roles = @("write")
    grantedToIdentities = @(
        @{
            application = @{
                id = "89ea5c94-7736-4e25-95ad-3fa95f62b66e"
                displayName = "Contoso Time Manager App"
            }
        }
    )
}
New-MgSitePermission -SiteId $siteId -BodyParameter $params
```

**C#**:
```csharp
var requestBody = new Permission
{
    Roles = new List<string> { "write" },
    GrantedToIdentities = new List<IdentitySet>
    {
        new IdentitySet
        {
            Application = new Identity
            {
                Id = "89ea5c94-7736-4e25-95ad-3fa95f62b66e",
                DisplayName = "Contoso Time Manager App"
            }
        }
    }
};
var result = await graphClient.Sites["{site-id}"]
    .Permissions
    .PostAsync(requestBody);
```

**JavaScript**:
```javascript
let result = await client.api('/sites/{site-id}/permissions')
    .post({
        roles: ['write'],
        grantedToIdentities: [{
            application: {
                id: '89ea5c94-7736-4e25-95ad-3fa95f62b66e',
                displayName: 'Contoso Time Manager App'
            }
        }]
    });
```

**Python**:
```python
request_body = Permission(
    roles=["write"],
    granted_to_identities=[
        IdentitySet(
            application=Identity(
                id="89ea5c94-7736-4e25-95ad-3fa95f62b66e",
                display_name="Contoso Time Manager App"
            )
        )
    ]
)
result = await graph_client.sites.by_site_id('site-id').permissions.post(request_body)
```

## 4. PATCH /sites/{id}/permissions/{id} - Update Site Permission

### Description [VERIFIED]

Updates an existing permission on a site. Only the `roles` property can be modified.

### HTTP Request

```http
PATCH https://graph.microsoft.com/v1.0/sites/{siteId}/permissions/{permissionId}
```

### Path Parameters

- **siteId** (`string`) - Site identifier
- **permissionId** (`string`) - Permission identifier to update

### Request Headers

- **Authorization**: `Bearer {token}`
- **Content-Type**: `application/json`

### Request Body

```json
{
  "roles": ["read | write | fullcontrol"]
}
```

### Request Example

```http
PATCH https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/permissions/1
Authorization: Bearer {token}
Content-Type: application/json

{
  "roles": ["fullcontrol"]
}
```

### Response JSON [VERIFIED]

```json
{
  "id": "1",
  "roles": ["fullcontrol"],
  "grantedToIdentitiesV2": [
    {
      "application": {
        "id": "89ea5c94-7736-4e25-95ad-3fa95f62b66e",
        "displayName": "Contoso Time Manager App"
      }
    }
  ]
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Sites

$params = @{
    roles = @("fullcontrol")
}
Update-MgSitePermission -SiteId $siteId -PermissionId $permissionId -BodyParameter $params
```

**C#**:
```csharp
var requestBody = new Permission
{
    Roles = new List<string> { "fullcontrol" }
};
var result = await graphClient.Sites["{site-id}"]
    .Permissions["{permission-id}"]
    .PatchAsync(requestBody);
```

**JavaScript**:
```javascript
let result = await client.api('/sites/{site-id}/permissions/{perm-id}')
    .patch({ roles: ['fullcontrol'] });
```

**Python**:
```python
request_body = Permission(roles=["fullcontrol"])
result = await graph_client.sites.by_site_id('site-id').permissions.by_permission_id('perm-id').patch(request_body)
```

## 5. DELETE /sites/{id}/permissions/{id} - Delete Site Permission

### Description [VERIFIED]

Removes a permission from a site, revoking application access.

### HTTP Request

```http
DELETE https://graph.microsoft.com/v1.0/sites/{siteId}/permissions/{permissionId}
```

### Path Parameters

- **siteId** (`string`) - Site identifier
- **permissionId** (`string`) - Permission identifier to delete

### Request Headers

- **Authorization**: `Bearer {token}`

### Request Example

```http
DELETE https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/permissions/1
Authorization: Bearer {token}
```

### Response [VERIFIED]

```http
HTTP/1.1 204 No Content
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Sites
Remove-MgSitePermission -SiteId $siteId -PermissionId $permissionId
```

**C#**:
```csharp
await graphClient.Sites["{site-id}"]
    .Permissions["{permission-id}"]
    .DeleteAsync();
```

**JavaScript**:
```javascript
await client.api('/sites/{site-id}/permissions/{perm-id}').delete();
```

**Python**:
```python
await graph_client.sites.by_site_id('site-id').permissions.by_permission_id('perm-id').delete()
```

## List and ListItem Permissions [VERIFIED]

Similar endpoints exist for lists and list items:

### List Permissions

```http
GET /sites/{siteId}/lists/{listId}/permissions
GET /sites/{siteId}/lists/{listId}/permissions/{permId}
POST /sites/{siteId}/lists/{listId}/permissions
PATCH /sites/{siteId}/lists/{listId}/permissions/{permId}
DELETE /sites/{siteId}/lists/{listId}/permissions/{permId}
```

### ListItem Permissions

```http
GET /sites/{siteId}/lists/{listId}/items/{itemId}/permissions
POST /sites/{siteId}/lists/{listId}/items/{itemId}/permissions
DELETE /sites/{siteId}/lists/{listId}/items/{itemId}/permissions/{permId}
```

## Permission Management Requirements [VERIFIED]

**Permissions needed to manage permissions**:

- **Site level**: `Sites.FullControl.All` scope
- **List level**: `Sites.Selected` + FullControl role at site OR `Lists.SelectedOperations.Selected` + FullControl role at list
- **ListItem level**: `ListItems.SelectedOperations.Selected` + FullControl role

**Delegated scenarios**: Current user must also have sufficient permissions in SharePoint.

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid request format
- **401 Unauthorized** - Missing or invalid token
- **403 Forbidden** - Insufficient permissions or not admin
- **404 Not Found** - Site or permission not found
- **409 Conflict** - Permission already exists
- **429 Too Many Requests** - Rate limit exceeded

### Error Response Format

```json
{
  "error": {
    "code": "accessDenied",
    "message": "Access denied. You do not have permission to perform this action.",
    "innerError": {
      "request-id": "guid",
      "date": "2026-01-28T12:00:00Z"
    }
  }
}
```

## Throttling Considerations [VERIFIED]

**Best Practices**:
- Cache permission IDs after listing
- Batch permission checks where possible
- Implement exponential backoff for 429 errors

**Resource Units**:
- List permissions: ~1 resource unit
- Create/Update/Delete permission: ~2-3 resource units

## Sites.Selected vs Other Permission Models [VERIFIED]

**Sites.Selected** (Application-only):
- Granular per-site access
- Requires explicit grant per site
- Admin controls which apps access which sites

**Sites.Read.All / Sites.ReadWrite.All**:
- Access to ALL sites in tenant
- No per-site control
- Simpler but less secure

**Delegated (Files.Read, Sites.Read)**:
- Access based on user's permissions
- App acts on behalf of signed-in user
- User must have access to resource

## Sources

- **MSGRAPH-PERM-SC-01**: https://learn.microsoft.com/en-us/graph/permissions-selected-overview
- **MSGRAPH-PERM-SC-02**: https://learn.microsoft.com/en-us/graph/api/site-list-permissions?view=graph-rest-1.0
- **MSGRAPH-PERM-SC-03**: https://learn.microsoft.com/en-us/graph/api/site-post-permissions?view=graph-rest-1.0
- **MSGRAPH-PERM-SC-04**: https://learn.microsoft.com/en-us/graph/api/site-delete-permission?view=graph-rest-1.0

## Document History

**[2026-01-28 18:25]**
- Initial creation with 5 site permission endpoints
- Added Sites.Selected permission model overview
- Added permission management requirements
- Added list/listItem permission endpoints reference
