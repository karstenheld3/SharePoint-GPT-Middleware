# INFO: Microsoft Graph API - Drive Core Methods

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for Drive API core methods with request/response JSON and examples
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_MSGRAPH-IN00_TOC.md [MSGRAPH-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Access user's OneDrive for personal file storage integrations
- Enumerate all document libraries in a SharePoint site
- Build multi-tenant apps that access group or site document libraries
- Implement "recently accessed" or "followed files" features
- Check storage quota and usage for capacity planning
- Access special folders (Documents, Photos, App Root) by well-known name
- Build file picker components that browse drive contents

**Key findings**:
- OneDrive auto-provisions on first access (delegated auth only) if user is licensed
- Application permissions do NOT auto-provision OneDrive - returns 404 if not exists
- driveType distinguishes personal/business/documentLibrary - affects available features
- Document libraries are drives with `driveType: "documentLibrary"`
- Sites can have multiple drives (document libraries); use `/sites/{id}/drives` to list all
- Special folders accessed by name without knowing ID; useful for app-specific storage
- Quota state values: `normal`, `nearing`, `critical`, `exceeded` - monitor for alerts
- Following items is user-specific; requires delegated permissions

## Quick Reference Summary

**Endpoints covered**: 10 Drive API methods

- `GET /drives` - List all drives
- `GET /drives/{id}` - Get drive by ID
- `GET /me/drive` - Get current user's OneDrive
- `GET /users/{id}/drive` - Get user's OneDrive
- `GET /groups/{id}/drive` - Get group's document library
- `GET /sites/{id}/drive` - Get site's default document library
- `GET /sites/{id}/drives` - List all document libraries in site
- `GET /me/drive/special/{name}` - Get special folder
- `GET /me/drive/following` - List followed items
- `GET /drives/{id}/bundles` - List bundles in drive

**Permissions required**:
- Delegated: `Files.Read`, `Files.ReadWrite`, `Files.Read.All`, `Files.ReadWrite.All`
- Application: `Files.Read.All`, `Files.ReadWrite.All`, `Sites.Read.All`, `Sites.ReadWrite.All`
- **Least privilege**: `Files.Read` for personal OneDrive; `Sites.Read.All` for SharePoint

**Drive ID format**: GUID
- Example: `b!-RIj2DuyvEyV1T4NlOaMHk8XkS_I8MdFlUCq1BlcjgmhRfAj3-Z8RY2VpuvV_tpd`

## Drive Resource Type

### JSON Schema [VERIFIED]

```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "driveType": "personal | business | documentLibrary",
  "createdBy": { "@odata.type": "microsoft.graph.identitySet" },
  "createdDateTime": "datetime",
  "lastModifiedBy": { "@odata.type": "microsoft.graph.identitySet" },
  "lastModifiedDateTime": "datetime",
  "owner": { "@odata.type": "microsoft.graph.identitySet" },
  "quota": { "@odata.type": "microsoft.graph.quota" },
  "sharepointIds": { "@odata.type": "microsoft.graph.sharepointIds" },
  "system": { "@odata.type": "microsoft.graph.systemFacet" },
  "webUrl": "url",
  "@odata.type": "microsoft.graph.drive"
}
```

### Properties [VERIFIED]

- **id** - Unique identifier (GUID)
- **name** - Display name of the drive
- **description** - Drive description
- **driveType** - Type of drive:
  - `personal` - OneDrive personal
  - `business` - OneDrive for Business
  - `documentLibrary` - SharePoint document library
- **createdBy** - Identity of creator
- **createdDateTime** - Creation timestamp
- **lastModifiedBy** - Identity of last modifier
- **lastModifiedDateTime** - Last modification timestamp
- **owner** - Owner identity (user, group, or site)
- **quota** - Storage quota information:
  ```json
  {
    "deleted": 0,
    "remaining": 1073741824,
    "state": "normal",
    "total": 5368709120,
    "used": 4294967296
  }
  ```
- **sharepointIds** - SharePoint-specific identifiers
- **system** - Present if drive is system-managed
- **webUrl** - URL to access drive in browser

### quota Properties [VERIFIED]

- **deleted** - Bytes in recycle bin
- **remaining** - Bytes available
- **state** - State: `normal`, `nearing`, `critical`, `exceeded`
- **total** - Total quota in bytes
- **used** - Bytes used

### Relationships (expandable via $expand)

- **bundles** - Collection of `bundle` driveItems
- **following** - Items being followed
- **items** - All items in drive
- **list** - Associated SharePoint list
- **root** - Root driveItem
- **special** - Special folders

## 1. GET /drives - List All Drives

### Description [VERIFIED]

List all drives accessible to the application. Typically used with application permissions.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/drives
```

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "drive-guid-1",
      "name": "OneDrive",
      "driveType": "business",
      "owner": {
        "user": {
          "displayName": "John Doe"
        }
      }
    }
  ]
}
```

## 2. GET /drives/{id} - Get Drive by ID

### Description [VERIFIED]

Retrieve a drive by its unique identifier.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/drives/{drive-id}
```

### Path Parameters

- **drive-id** (`string`) - Drive GUID

### Response JSON [VERIFIED]

```json
{
  "id": "b!-RIj2DuyvEyV1T4NlOaMHk8XkS_I8MdFlUCq1BlcjgmhRfAj3-Z8RY2VpuvV_tpd",
  "name": "Documents",
  "driveType": "documentLibrary",
  "owner": {
    "group": {
      "id": "group-guid",
      "displayName": "Marketing Team"
    }
  },
  "quota": {
    "deleted": 0,
    "remaining": 26843545600,
    "state": "normal",
    "total": 27487790694400,
    "used": 644245094400
  },
  "webUrl": "https://contoso.sharepoint.com/sites/marketing/Shared Documents"
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Files
Get-MgDrive -DriveId $driveId
```

**C#**:
```csharp
var drive = await graphClient.Drives["{drive-id}"].GetAsync();
```

## 3. GET /me/drive - Get Current User's OneDrive

### Description [VERIFIED]

Get the current signed-in user's OneDrive. If not provisioned but licensed, auto-provisions the drive (delegated auth only).

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/me/drive
```

### Response JSON [VERIFIED]

```json
{
  "id": "user-drive-guid",
  "name": "OneDrive",
  "driveType": "business",
  "owner": {
    "user": {
      "id": "user-guid",
      "displayName": "John Doe",
      "email": "john@contoso.com"
    }
  },
  "quota": {
    "deleted": 0,
    "remaining": 1073741824000,
    "state": "normal",
    "total": 1099511627776,
    "used": 25769803776
  },
  "webUrl": "https://contoso-my.sharepoint.com/personal/john_contoso_com/Documents"
}
```

### SDK Examples

**PowerShell**:
```powershell
Get-MgDrive
```

**C#**:
```csharp
var drive = await graphClient.Me.Drive.GetAsync();
```

**JavaScript**:
```javascript
let drive = await client.api('/me/drive').get();
```

**Python**:
```python
result = await graph_client.me.drive.get()
```

## 4. GET /users/{id}/drive - Get User's OneDrive

### Description [VERIFIED]

Get a specific user's OneDrive. Auto-provisions if user is licensed (delegated auth only).

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/users/{user-id}/drive
```

Or by UPN:
```http
GET https://graph.microsoft.com/v1.0/users/john@contoso.com/drive
```

### Path Parameters

- **user-id** (`string`) - User GUID or userPrincipalName

### SDK Examples

**PowerShell**:
```powershell
Get-MgUserDrive -UserId $userId
```

## 5. GET /groups/{id}/drive - Get Group's Document Library

### Description [VERIFIED]

Get the default document library for a Microsoft 365 group.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/groups/{group-id}/drive
```

### Path Parameters

- **group-id** (`string`) - Group GUID

### Response JSON [VERIFIED]

```json
{
  "id": "group-drive-guid",
  "name": "Documents",
  "driveType": "documentLibrary",
  "owner": {
    "group": {
      "id": "group-guid",
      "displayName": "Project Alpha Team"
    }
  },
  "webUrl": "https://contoso.sharepoint.com/sites/ProjectAlpha/Shared Documents"
}
```

### SDK Examples

**C#**:
```csharp
var drive = await graphClient.Groups["{group-id}"].Drive.GetAsync();
```

## 6. GET /sites/{id}/drive - Get Site's Default Document Library

### Description [VERIFIED]

Get the default document library for a SharePoint site.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/drive
```

### Path Parameters

- **site-id** (`string`) - Site composite ID

### Response JSON [VERIFIED]

```json
{
  "id": "site-drive-guid",
  "name": "Documents",
  "driveType": "documentLibrary",
  "quota": {
    "deleted": 0,
    "remaining": 27487790694400,
    "state": "normal",
    "total": 27487790694400,
    "used": 0
  },
  "sharepointIds": {
    "listId": "list-guid",
    "siteId": "site-guid",
    "siteUrl": "https://contoso.sharepoint.com/sites/team",
    "webId": "web-guid"
  },
  "webUrl": "https://contoso.sharepoint.com/sites/team/Shared Documents"
}
```

### SDK Examples

**PowerShell**:
```powershell
Get-MgSiteDrive -SiteId $siteId
```

## 7. GET /sites/{id}/drives - List All Document Libraries

### Description [VERIFIED]

List all document libraries in a SharePoint site.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/drives
```

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "drive-guid-1",
      "name": "Documents",
      "driveType": "documentLibrary",
      "webUrl": "https://contoso.sharepoint.com/sites/team/Shared Documents"
    },
    {
      "id": "drive-guid-2",
      "name": "Site Assets",
      "driveType": "documentLibrary",
      "webUrl": "https://contoso.sharepoint.com/sites/team/SiteAssets"
    },
    {
      "id": "drive-guid-3",
      "name": "Project Files",
      "driveType": "documentLibrary",
      "webUrl": "https://contoso.sharepoint.com/sites/team/ProjectFiles"
    }
  ]
}
```

### SDK Examples

**PowerShell**:
```powershell
Get-MgSiteDrive -SiteId $siteId -All
```

**C#**:
```csharp
var drives = await graphClient.Sites["{site-id}"].Drives.GetAsync();
```

## 8. GET /me/drive/special/{name} - Get Special Folder

### Description [VERIFIED]

Access a special folder by name. Special folders provide simple access to well-known folders without knowing their ID.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/me/drive/special/{folder-name}
```

### Special Folder Names [VERIFIED]

- **documents** - Documents folder
- **photos** - Photos folder
- **cameraroll** - Camera Roll folder
- **approot** - Application's personal folder (`/Apps/{AppName}`)
- **music** - Music folder
- **recordings** - Recordings folder (Teams meeting recordings)

### Response JSON [VERIFIED]

Returns a `driveItem` resource:

```json
{
  "id": "item-guid",
  "name": "Documents",
  "folder": {
    "childCount": 15
  },
  "size": 1073741824,
  "webUrl": "https://contoso-my.sharepoint.com/personal/john_contoso_com/Documents"
}
```

### Get Children of Special Folder

```http
GET https://graph.microsoft.com/v1.0/me/drive/special/{folder-name}/children
```

### SDK Examples

**PowerShell**:
```powershell
Get-MgDriveSpecial -DriveId $driveId -DriveItemId "documents"
```

**JavaScript**:
```javascript
let docs = await client.api('/me/drive/special/documents').get();
let children = await client.api('/me/drive/special/documents/children').get();
```

## 9. GET /me/drive/following - List Followed Items

### Description [VERIFIED]

List items the user is following in their OneDrive. Following allows users to track files or folders they're interested in.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/me/drive/following
```

Or for any drive:
```http
GET https://graph.microsoft.com/v1.0/drives/{drive-id}/following
```

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "item-guid-1",
      "name": "Project Plan.xlsx",
      "file": {
        "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      },
      "size": 25600,
      "webUrl": "https://contoso.sharepoint.com/sites/team/Documents/Project Plan.xlsx"
    },
    {
      "id": "item-guid-2",
      "name": "Reports",
      "folder": {
        "childCount": 8
      },
      "webUrl": "https://contoso.sharepoint.com/sites/team/Documents/Reports"
    }
  ]
}
```

### SDK Examples

**C#**:
```csharp
var following = await graphClient.Me.Drive.Following.GetAsync();
```

## 10. GET /drives/{id}/bundles - List Bundles

### Description [VERIFIED]

List all bundles in a drive. Bundles are virtual folders that group items from different locations.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/drives/{drive-id}/bundles
```

Or for current user:
```http
GET https://graph.microsoft.com/v1.0/me/drive/bundles
```

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "bundle-guid",
      "name": "Q1 Reports Bundle",
      "bundle": {
        "childCount": 5,
        "album": null
      },
      "createdDateTime": "2026-01-15T10:00:00Z",
      "webUrl": "https://contoso-my.sharepoint.com/personal/john_contoso_com/_layouts/15/Bundle.aspx?id=bundle-guid"
    }
  ]
}
```

### Bundle Types [VERIFIED]

- **album** - Photo album bundle
- **childCount** - Number of items in bundle

### SDK Examples

**PowerShell**:
```powershell
Get-MgDriveBundle -DriveId $driveId
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid drive ID format
- **401 Unauthorized** - Missing or invalid authentication
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Drive does not exist or user has no OneDrive
- **429 Too Many Requests** - Rate limit exceeded

### Error Response Format

```json
{
  "error": {
    "code": "itemNotFound",
    "message": "The resource could not be found.",
    "innerError": {
      "request-id": "guid",
      "date": "datetime"
    }
  }
}
```

### 404 Scenarios [VERIFIED]

- User has no OneDrive license
- OneDrive not provisioned (app permissions - won't auto-provision)
- Drive deleted or inaccessible

## Throttling Considerations [VERIFIED]

**Throttling Behavior**:
- HTTP 429 returned when throttled
- `Retry-After` header indicates wait time

**Best Practices**:
- Cache drive IDs after first lookup
- Use `$select` to reduce payload
- For batch operations, use JSON batching

**Resource Units**:
- Drive GET: ~1 resource unit
- Drive list: ~1-2 resource units

## Drive Types Reference [VERIFIED]

- **personal** - Consumer OneDrive (Microsoft Account)
- **business** - OneDrive for Business (work/school account)
- **documentLibrary** - SharePoint document library

**Detection pattern**:
```javascript
if (drive.driveType === 'documentLibrary') {
    // SharePoint - use Sites.* permissions
} else {
    // OneDrive - use Files.* permissions
}
```

## Sources

- **MSGRAPH-DRIVE-SC-01**: https://learn.microsoft.com/en-us/graph/api/resources/drive?view=graph-rest-1.0
- **MSGRAPH-DRIVE-SC-02**: https://learn.microsoft.com/en-us/graph/api/drive-list?view=graph-rest-1.0
- **MSGRAPH-DRIVE-SC-03**: https://learn.microsoft.com/en-us/graph/api/drive-get?view=graph-rest-1.0
- **MSGRAPH-DRIVE-SC-04**: https://learn.microsoft.com/en-us/graph/api/drive-get-specialfolder?view=graph-rest-1.0
- **MSGRAPH-DRIVE-SC-05**: https://learn.microsoft.com/en-us/graph/api/drive-list-following?view=graph-rest-1.0

## Document History

**[2026-01-28 18:30]**
- Initial creation with 10 Drive API endpoints
- Full JSON request/response examples
- SDK examples for PowerShell, C#, JavaScript, Python
- Drive types and quota documentation
