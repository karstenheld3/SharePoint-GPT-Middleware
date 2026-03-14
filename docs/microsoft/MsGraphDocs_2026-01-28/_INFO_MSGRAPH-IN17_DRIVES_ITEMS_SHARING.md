# INFO: Microsoft Graph API - DriveItem Sharing Methods

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for DriveItem sharing methods with request/response JSON and examples
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_MSGRAPH-IN00_TOC.md [MSGRAPH-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Share files/folders with external users via anonymous or organization links
- Build custom sharing dialogs with granular permission control
- Audit and manage existing sharing permissions programmatically
- Implement "share with specific people" workflows with email notifications
- Create time-limited or password-protected sharing links
- Revoke access when collaboration ends or employees leave

**Key findings**:
- `createLink` returns existing link if same type already exists for the app
- `invite` cannot add new guest users with app-only permissions
- Permission inheritance: child items inherit from parent unless explicitly set
- Three link scopes: anonymous (anyone), organization (tenant), users (specific)
- Owners see all permissions; non-owners see only their own permissions
- Cannot modify permissions on root driveItem of personal OneDrive

## Quick Reference Summary

**Endpoints covered**: 5 sharing methods

- `POST /drives/{id}/items/{id}/createLink` - Create sharing link
- `POST /drives/{id}/items/{id}/invite` - Send sharing invitation
- `GET /drives/{id}/items/{id}/permissions` - List sharing permissions
- `PATCH /drives/{id}/items/{id}/permissions/{id}` - Update permission
- `DELETE /drives/{id}/items/{id}/permissions/{id}` - Remove permission

**Permissions required**:
- Delegated: `Files.ReadWrite`, `Files.ReadWrite.All`, `Sites.ReadWrite.All`
- Application: `Files.ReadWrite.All`, `Sites.ReadWrite.All`
- **Least privilege**: `Files.ReadWrite` (delegated) for user's own files
- Note: SharePoint Embedded requires `FileStorageContainer.Selected`

**Permission ID format**: GUID string
- Example: `aXNfcm9vdA==` (base64 encoded) or standard GUID

## Permission Resource Type [VERIFIED]

### JSON Schema

```json
{
  "id": "string",
  "grantedTo": { "@odata.type": "microsoft.graph.identitySet" },
  "grantedToIdentities": [{ "@odata.type": "microsoft.graph.identitySet" }],
  "grantedToIdentitiesV2": [{ "@odata.type": "microsoft.graph.sharePointIdentitySet" }],
  "grantedToV2": { "@odata.type": "microsoft.graph.sharePointIdentitySet" },
  "inheritedFrom": { "@odata.type": "microsoft.graph.itemReference" },
  "invitation": { "@odata.type": "microsoft.graph.sharingInvitation" },
  "link": { "@odata.type": "microsoft.graph.sharingLink" },
  "roles": ["string"],
  "shareId": "string",
  "expirationDateTime": "datetime",
  "hasPassword": true
}
```

### Properties [VERIFIED]

- **id** (`string`) - Unique identifier of the permission
- **roles** (`string[]`) - Permission roles: `read`, `write`, `owner`
- **grantedTo** (`identitySet`) - User/app/device with access (deprecated, use grantedToV2)
- **grantedToV2** (`sharePointIdentitySet`) - User/group/app with access
- **inheritedFrom** (`itemReference`) - Reference to ancestor if inherited
- **link** (`sharingLink`) - Details if this is a link-based permission
- **invitation** (`sharingInvitation`) - Details if this is an invitation
- **expirationDateTime** (`dateTimeOffset`) - When permission expires
- **hasPassword** (`boolean`) - Whether link has password protection

### Sharing Link Object [VERIFIED]

```json
{
  "type": "view | edit | embed",
  "scope": "anonymous | organization | users",
  "webUrl": "https://...",
  "webHtml": "<iframe>...</iframe>",
  "application": { "@odata.type": "microsoft.graph.identity" },
  "preventsDownload": false
}
```

## 1. POST /drives/{id}/items/{id}/createLink - Create Sharing Link

### Description [VERIFIED]

Creates a new sharing link for a driveItem. If a sharing link of the specified type already exists for the app, the existing link is returned. DriveItem resources inherit sharing permissions from ancestors.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/drives/{driveId}/items/{itemId}/createLink
```

Alternative paths:
```http
POST https://graph.microsoft.com/v1.0/me/drive/items/{itemId}/createLink
POST https://graph.microsoft.com/v1.0/users/{userId}/drive/items/{itemId}/createLink
POST https://graph.microsoft.com/v1.0/groups/{groupId}/drive/items/{itemId}/createLink
POST https://graph.microsoft.com/v1.0/sites/{siteId}/drive/items/{itemId}/createLink
```

### Path Parameters

- **driveId** (`string`) - Unique identifier of the drive
- **itemId** (`string`) - Unique identifier of the driveItem

### Request Headers

- **Authorization**: `Bearer {token}`
- **Content-Type**: `application/json`

### Request Body

```json
{
  "type": "view | edit | embed",
  "scope": "anonymous | organization | users",
  "password": "string",
  "expirationDateTime": "datetime",
  "retainInheritedPermissions": false
}
```

**Properties**:
- **type** (`string`, required) - Link type:
  - `view` - Read-only link
  - `edit` - Read-write link
  - `embed` - Embeddable link for web apps
- **scope** (`string`, optional) - Link scope:
  - `anonymous` - Anyone with link (no sign-in required)
  - `organization` - Anyone in the organization
  - `users` - Specific people only
- **password** (`string`, optional) - Password to access the link
- **expirationDateTime** (`dateTimeOffset`, optional) - When link expires
- **retainInheritedPermissions** (`boolean`, optional) - Keep inherited permissions

### Request Example

```http
POST https://graph.microsoft.com/v1.0/me/drive/items/01ABC123DEF456/createLink
Authorization: Bearer {token}
Content-Type: application/json

{
  "type": "view",
  "scope": "organization",
  "expirationDateTime": "2026-12-31T23:59:59Z"
}
```

### Response JSON [VERIFIED]

```json
{
  "id": "2!aXNfcm9vdA==",
  "roles": ["read"],
  "link": {
    "type": "view",
    "scope": "organization",
    "webUrl": "https://contoso.sharepoint.com/:w:/s/Sales/EZxxxxxxxx",
    "application": {
      "id": "12345678-90ab-cdef-1234-567890abcdef",
      "displayName": "Contoso App"
    }
  },
  "expirationDateTime": "2026-12-31T23:59:59Z"
}
```

### Embed Link Response [VERIFIED]

For `type: "embed"`:
```json
{
  "id": "3!bXNfcm9vdA==",
  "roles": ["read"],
  "link": {
    "type": "embed",
    "webHtml": "<iframe src=\"https://onedrive.live.com/embed?...\" width=\"98\" height=\"120\"></iframe>",
    "webUrl": "https://onedrive.live.com/embed?..."
  }
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Files

$params = @{
    type = "view"
    scope = "organization"
}
New-MgDriveItemLink -DriveId $driveId -DriveItemId $driveItemId -BodyParameter $params
```

**C#**:
```csharp
var requestBody = new CreateLinkPostRequestBody
{
    Type = "view",
    Scope = "organization"
};
var result = await graphClient.Drives["{drive-id}"]
    .Items["{driveItem-id}"]
    .CreateLink
    .PostAsync(requestBody);
```

**JavaScript**:
```javascript
let result = await client.api('/me/drive/items/{item-id}/createLink')
    .post({ type: 'view', scope: 'organization' });
```

**Python**:
```python
request_body = CreateLinkPostRequestBody(type="view", scope="organization")
result = await graph_client.drives.by_drive_id('drive-id').items.by_drive_item_id('item-id').create_link.post(request_body)
```

## 2. POST /drives/{id}/items/{id}/invite - Send Sharing Invitation

### Description [VERIFIED]

Sends a sharing invitation for a driveItem. Provides permissions to recipients and optionally sends email notification.

**Important Limitations**:
- Cannot modify permissions on root driveItem of personal OneDrive
- Cannot invite new guests with app-only access (existing guests OK)
- Sites.Selected scope cannot use this endpoint

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/drives/{driveId}/items/{itemId}/invite
```

Alternative paths:
```http
POST https://graph.microsoft.com/v1.0/me/drive/items/{itemId}/invite
POST https://graph.microsoft.com/v1.0/users/{userId}/drive/items/{itemId}/invite
POST https://graph.microsoft.com/v1.0/groups/{groupId}/drive/items/{itemId}/invite
POST https://graph.microsoft.com/v1.0/sites/{siteId}/drive/items/{itemId}/invite
```

### Path Parameters

- **driveId** (`string`) - Unique identifier of the drive
- **itemId** (`string`) - Unique identifier of the driveItem

### Request Headers

- **Authorization**: `Bearer {token}`
- **Content-Type**: `application/json`

### Request Body

```json
{
  "recipients": [
    {
      "email": "string",
      "alias": "string",
      "objectId": "string"
    }
  ],
  "roles": ["read | write"],
  "requireSignIn": true,
  "sendInvitation": true,
  "message": "string",
  "password": "string",
  "expirationDateTime": "datetime",
  "retainInheritedPermissions": false
}
```

**Properties**:
- **recipients** (`driveRecipient[]`, required) - Recipients to invite
- **roles** (`string[]`, required) - Permission level: `read` or `write`
- **requireSignIn** (`boolean`) - Require sign-in to access
- **sendInvitation** (`boolean`) - Send email notification
- **message** (`string`) - Custom message in email
- **password** (`string`) - Password for the share
- **expirationDateTime** (`dateTimeOffset`) - When permission expires

### DriveRecipient Object [VERIFIED]

```json
{
  "@odata.type": "microsoft.graph.driveRecipient",
  "email": "user@contoso.com",
  "alias": "user",
  "objectId": "guid"
}
```

Use one of: `email`, `alias`, or `objectId`.

### Request Example

```http
POST https://graph.microsoft.com/v1.0/me/drive/items/01ABC123DEF456/invite
Authorization: Bearer {token}
Content-Type: application/json

{
  "recipients": [
    { "email": "ryan@contoso.com" },
    { "email": "alex@contoso.com" }
  ],
  "roles": ["write"],
  "requireSignIn": true,
  "sendInvitation": true,
  "message": "Here's the file we're collaborating on.",
  "expirationDateTime": "2026-07-15T14:00:00Z"
}
```

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "aTxxxxxxxxx",
      "roles": ["write"],
      "grantedTo": {
        "user": {
          "id": "user-guid",
          "email": "ryan@contoso.com",
          "displayName": "Ryan Gregg"
        }
      },
      "invitation": {
        "email": "ryan@contoso.com",
        "signInRequired": true
      },
      "expirationDateTime": "2026-07-15T14:00:00Z"
    }
  ]
}
```

### Partial Success Response [VERIFIED]

When some invitations fail:
```json
{
  "value": [
    {
      "id": "permission-id",
      "roles": ["write"],
      "grantedTo": { "user": { "email": "ryan@contoso.com" } }
    }
  ],
  "error": {
    "code": "partialSuccess",
    "message": "Some invitations failed",
    "innerError": {
      "failedRecipients": [
        { "email": "invalid@contoso.com", "error": "User not found" }
      ]
    }
  }
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Files

$params = @{
    recipients = @(
        @{ email = "ryan@contoso.com" }
    )
    roles = @("write")
    requireSignIn = $true
    sendInvitation = $true
    message = "Here's the file."
}
Invoke-MgInviteDriveItem -DriveId $driveId -DriveItemId $driveItemId -BodyParameter $params
```

**C#**:
```csharp
var requestBody = new InvitePostRequestBody
{
    Recipients = new List<DriveRecipient>
    {
        new DriveRecipient { Email = "ryan@contoso.com" }
    },
    Roles = new List<string> { "write" },
    RequireSignIn = true,
    SendInvitation = true,
    Message = "Here's the file."
};
var result = await graphClient.Drives["{drive-id}"]
    .Items["{driveItem-id}"]
    .Invite
    .PostAsInvitePostResponseAsync(requestBody);
```

**JavaScript**:
```javascript
let result = await client.api('/me/drive/items/{item-id}/invite')
    .post({
        recipients: [{ email: 'ryan@contoso.com' }],
        roles: ['write'],
        requireSignIn: true,
        sendInvitation: true
    });
```

**Python**:
```python
request_body = InvitePostRequestBody(
    recipients=[DriveRecipient(email="ryan@contoso.com")],
    roles=["write"],
    require_sign_in=True,
    send_invitation=True
)
result = await graph_client.drives.by_drive_id('drive-id').items.by_drive_item_id('item-id').invite.post(request_body)
```

## 3. GET /drives/{id}/items/{id}/permissions - List Permissions

### Description [VERIFIED]

Lists the effective sharing permissions on a driveItem. Includes both direct and inherited permissions.

**Access Rules**:
- Owners see all permissions (including co-owners)
- Non-owners see only their own permissions
- Properties like `shareId` and `webUrl` only returned to callers who can create that permission

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/drives/{driveId}/items/{itemId}/permissions
```

Alternative paths:
```http
GET https://graph.microsoft.com/v1.0/me/drive/items/{itemId}/permissions
GET https://graph.microsoft.com/v1.0/me/drive/root:/{path}:/permissions
GET https://graph.microsoft.com/v1.0/users/{userId}/drive/items/{itemId}/permissions
GET https://graph.microsoft.com/v1.0/groups/{groupId}/drive/items/{itemId}/permissions
GET https://graph.microsoft.com/v1.0/sites/{siteId}/drive/items/{itemId}/permissions
```

### Path Parameters

- **driveId** (`string`) - Unique identifier of the drive
- **itemId** (`string`) - Unique identifier of the driveItem

### Query Parameters

- **$select** - Select specific properties

### Request Headers

- **Authorization**: `Bearer {token}`
- **If-None-Match**: `{etag}` - Returns 304 if unchanged

### Request Example

```http
GET https://graph.microsoft.com/v1.0/me/drive/items/01ABC123DEF456/permissions
Authorization: Bearer {token}
```

### Response JSON [VERIFIED]

```json
{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#Collection(permission)",
  "value": [
    {
      "id": "1",
      "roles": ["owner"],
      "grantedToV2": {
        "user": {
          "id": "user-guid",
          "displayName": "John Doe",
          "email": "john@contoso.com"
        }
      }
    },
    {
      "id": "2",
      "roles": ["write"],
      "grantedToV2": {
        "user": {
          "id": "other-user-guid",
          "displayName": "Jane Smith",
          "email": "jane@contoso.com"
        }
      },
      "inheritedFrom": {
        "driveId": "drive-guid",
        "id": "parent-folder-id",
        "path": "/drive/root:/Documents"
      }
    },
    {
      "id": "3",
      "roles": ["read"],
      "link": {
        "type": "view",
        "scope": "organization",
        "webUrl": "https://contoso.sharepoint.com/:w:/s/site/xxx"
      }
    }
  ]
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Files
Get-MgDriveItemPermission -DriveId $driveId -DriveItemId $driveItemId
```

**C#**:
```csharp
var permissions = await graphClient.Drives["{drive-id}"]
    .Items["{driveItem-id}"]
    .Permissions
    .GetAsync();
```

**JavaScript**:
```javascript
let permissions = await client.api('/me/drive/items/{item-id}/permissions').get();
```

**Python**:
```python
permissions = await graph_client.drives.by_drive_id('drive-id').items.by_drive_item_id('item-id').permissions.get()
```

## 4. PATCH /drives/{id}/items/{id}/permissions/{id} - Update Permission

### Description [VERIFIED]

Updates a sharing permission by patching the permission resource. Only the `roles` property can be modified.

**Not Supported**:
- Organizational sharing links
- People sharing links

### HTTP Request

```http
PATCH https://graph.microsoft.com/v1.0/drives/{driveId}/items/{itemId}/permissions/{permId}
```

Alternative paths:
```http
PATCH https://graph.microsoft.com/v1.0/me/drive/items/{itemId}/permissions/{permId}
PATCH https://graph.microsoft.com/v1.0/users/{userId}/drive/items/{itemId}/permissions/{permId}
PATCH https://graph.microsoft.com/v1.0/groups/{groupId}/drive/items/{itemId}/permissions/{permId}
PATCH https://graph.microsoft.com/v1.0/sites/{siteId}/drive/items/{itemId}/permissions/{permId}
```

### Path Parameters

- **driveId** (`string`) - Unique identifier of the drive
- **itemId** (`string`) - Unique identifier of the driveItem
- **permId** (`string`) - Unique identifier of the permission

### Request Headers

- **Authorization**: `Bearer {token}`
- **Content-Type**: `application/json`
- **If-Match**: `{etag}` - Optional, returns 412 if changed

### Request Body

```json
{
  "roles": ["read | write | owner"]
}
```

### Request Example

```http
PATCH https://graph.microsoft.com/v1.0/me/drive/items/01ABC123DEF456/permissions/abc123
Authorization: Bearer {token}
Content-Type: application/json

{
  "roles": ["read"]
}
```

### Response JSON [VERIFIED]

```json
{
  "id": "abc123",
  "roles": ["read"],
  "grantedTo": {
    "user": {
      "id": "user-guid",
      "displayName": "Ryan Gregg"
    }
  }
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Files

$params = @{
    roles = @("read")
}
Update-MgDriveItemPermission -DriveId $driveId -DriveItemId $driveItemId -PermissionId $permId -BodyParameter $params
```

**C#**:
```csharp
var requestBody = new Permission
{
    Roles = new List<string> { "read" }
};
var result = await graphClient.Drives["{drive-id}"]
    .Items["{driveItem-id}"]
    .Permissions["{permission-id}"]
    .PatchAsync(requestBody);
```

**JavaScript**:
```javascript
let result = await client.api('/me/drive/items/{item-id}/permissions/{perm-id}')
    .patch({ roles: ['read'] });
```

**Python**:
```python
request_body = Permission(roles=["read"])
result = await graph_client.drives.by_drive_id('drive-id').items.by_drive_item_id('item-id').permissions.by_permission_id('perm-id').patch(request_body)
```

## 5. DELETE /drives/{id}/items/{id}/permissions/{id} - Delete Permission

### Description [VERIFIED]

Removes access to a driveItem by deleting the sharing permission.

**Important**: Only non-inherited permissions can be deleted. Check `inheritedFrom` is null before attempting delete.

**SharePoint Embedded**: Container-level permissions cannot be removed from driveItem objects.

### HTTP Request

```http
DELETE https://graph.microsoft.com/v1.0/drives/{driveId}/items/{itemId}/permissions/{permId}
```

Alternative paths:
```http
DELETE https://graph.microsoft.com/v1.0/me/drive/items/{itemId}/permissions/{permId}
DELETE https://graph.microsoft.com/v1.0/users/{userId}/drive/items/{itemId}/permissions/{permId}
DELETE https://graph.microsoft.com/v1.0/groups/{groupId}/drive/items/{itemId}/permissions/{permId}
DELETE https://graph.microsoft.com/v1.0/sites/{siteId}/drive/items/{itemId}/permissions/{permId}
```

### Path Parameters

- **driveId** (`string`) - Unique identifier of the drive
- **itemId** (`string`) - Unique identifier of the driveItem
- **permId** (`string`) - Unique identifier of the permission to delete

### Request Headers

- **Authorization**: `Bearer {token}`
- **If-Match**: `{etag}` - Optional, returns 412 if changed

### Request Example

```http
DELETE https://graph.microsoft.com/v1.0/me/drive/items/01ABC123DEF456/permissions/abc123
Authorization: Bearer {token}
```

### Response [VERIFIED]

```http
HTTP/1.1 204 No Content
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Files
Remove-MgDriveItemPermission -DriveId $driveId -DriveItemId $driveItemId -PermissionId $permId
```

**C#**:
```csharp
await graphClient.Drives["{drive-id}"]
    .Items["{driveItem-id}"]
    .Permissions["{permission-id}"]
    .DeleteAsync();
```

**JavaScript**:
```javascript
await client.api('/me/drive/items/{item-id}/permissions/{perm-id}').delete();
```

**Python**:
```python
await graph_client.drives.by_drive_id('drive-id').items.by_drive_item_id('item-id').permissions.by_permission_id('perm-id').delete()
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid request format or parameters
- **401 Unauthorized** - Missing or invalid authentication token
- **403 Forbidden** - Insufficient permissions or not allowed operation
- **404 Not Found** - DriveItem or permission does not exist
- **409 Conflict** - Permission already exists (createLink returns existing)
- **412 Precondition Failed** - ETag mismatch (item changed)
- **429 Too Many Requests** - Rate limit exceeded

### Error Response Format

```json
{
  "error": {
    "code": "notAllowed",
    "message": "The operation is not allowed on this item.",
    "innerError": {
      "request-id": "guid",
      "date": "2026-01-28T12:00:00Z"
    }
  }
}
```

## Throttling Considerations [VERIFIED]

**Throttling Behavior**:
- HTTP 429 (Too Many Requests) returned when throttled
- `Retry-After` header indicates seconds to wait

**Best Practices**:
- Cache permission IDs after listing
- Batch permission checks using `$batch`
- Use `If-None-Match` for conditional requests
- Implement exponential backoff

**Resource Units**:
- createLink: ~3 resource units
- invite: ~3-5 resource units (per recipient)
- List permissions: ~1 resource unit
- Update/Delete permission: ~2 resource units

## Sharing Link Scope Comparison [VERIFIED]

- **anonymous** - Anyone with link, no sign-in required (if org allows)
- **organization** - Anyone in tenant, must be signed in
- **users** - Only specific invited users

**Organization Settings**: Tenant admins can disable anonymous links or set default sharing scope.

## Sources

- **MSGRAPH-SHARE-SC-01**: https://learn.microsoft.com/en-us/graph/api/driveitem-createlink?view=graph-rest-1.0
- **MSGRAPH-SHARE-SC-02**: https://learn.microsoft.com/en-us/graph/api/driveitem-invite?view=graph-rest-1.0
- **MSGRAPH-SHARE-SC-03**: https://learn.microsoft.com/en-us/graph/api/driveitem-list-permissions?view=graph-rest-1.0
- **MSGRAPH-SHARE-SC-04**: https://learn.microsoft.com/en-us/graph/api/permission-update?view=graph-rest-1.0
- **MSGRAPH-SHARE-SC-05**: https://learn.microsoft.com/en-us/graph/api/permission-delete?view=graph-rest-1.0

## Document History

**[2026-01-28 18:10]**
- Initial creation with 5 endpoints
- Added Permission resource type documentation
- Added sharing link scope comparison
- Added partial success response pattern
