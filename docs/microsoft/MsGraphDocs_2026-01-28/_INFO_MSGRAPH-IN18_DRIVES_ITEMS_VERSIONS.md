# INFO: Microsoft Graph API - DriveItem Version Methods

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for DriveItem version management methods
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `_INFO_MSGRAPH_DRIVEITEMS_CORE.md [MSGRAPH-IN01]` for core driveItem operations

## Summary

**Use cases**:
- Implement version history viewer for document management apps
- Download previous versions for comparison or recovery
- Restore accidentally overwritten files to earlier state
- Build audit trails showing document change history
- Implement "undo" functionality for document edits
- Archive specific versions before major changes
- Compare version metadata (size, modifier, date) for change tracking

**Key findings**:
- Version IDs differ by platform: numeric for OneDrive Personal, Major.Minor for Business/SharePoint
- Use `current` as version-id to get the latest version without knowing its ID
- Restore creates NEW version with old content; does NOT delete existing versions
- Version retention configurable by admin; default 500 major versions in SharePoint
- Versions count against storage quota - many versions = more storage used
- No API to delete specific versions; only restore is supported
- publication.level shows `published`, `checkout`, or `draft` status (SharePoint)
- Version content download returns 302 redirect like regular file download

## Quick Reference Summary

**Endpoints covered**: 4 version management methods

- `GET /drives/{id}/items/{id}/versions` - List all versions
- `GET /drives/{id}/items/{id}/versions/{id}` - Get specific version
- `GET /drives/{id}/items/{id}/versions/{id}/content` - Download version content
- `POST /drives/{id}/items/{id}/versions/{id}/restoreVersion` - Restore version

**Permissions required**:
- Delegated: `Files.Read`, `Files.ReadWrite`, `Files.Read.All`, `Files.ReadWrite.All`
- Application: `Files.Read.All`, `Files.ReadWrite.All`
- **Least privilege**: `Files.Read` for read; `Files.ReadWrite` for restore

## driveItemVersion Resource Type

### JSON Schema [VERIFIED]

```json
{
  "id": "string",
  "lastModifiedBy": { "@odata.type": "microsoft.graph.identitySet" },
  "lastModifiedDateTime": "datetime",
  "publication": { "@odata.type": "microsoft.graph.publicationFacet" },
  "size": "int64",
  "@odata.type": "microsoft.graph.driveItemVersion"
}
```

### Properties [VERIFIED]

- **id** - Version identifier (e.g., "1.0", "2.0", "512")
- **lastModifiedBy** - Identity who created this version
- **lastModifiedDateTime** - When version was created
- **publication** - Publication state (for SharePoint):
  ```json
  {
    "level": "published",
    "versionId": "1.0"
  }
  ```
- **size** - Size of this version in bytes

### publication Facet [VERIFIED]

- **level** - `published`, `checkout`, `draft`
- **versionId** - Version string

## 1. GET /drives/{id}/items/{id}/versions - List Versions

### Description [VERIFIED]

Retrieve all versions of a file. Version history retention depends on admin settings and may vary per user or location.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{item-id}/versions
```

Alternative paths:
```http
GET /me/drive/items/{item-id}/versions
GET /sites/{site-id}/drive/items/{item-id}/versions
GET /groups/{group-id}/drive/items/{item-id}/versions
```

### OData Query Parameters

- **$select** - Select properties
- **$top** - Limit results
- **$orderby** - Sort results

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "3.0",
      "lastModifiedBy": {
        "user": {
          "displayName": "Jane Smith",
          "email": "jane@contoso.com"
        }
      },
      "lastModifiedDateTime": "2026-01-28T15:00:00Z",
      "size": 28672
    },
    {
      "id": "2.0",
      "lastModifiedBy": {
        "user": {
          "displayName": "John Doe"
        }
      },
      "lastModifiedDateTime": "2026-01-25T10:30:00Z",
      "size": 25600
    },
    {
      "id": "1.0",
      "lastModifiedBy": {
        "user": {
          "displayName": "John Doe"
        }
      },
      "lastModifiedDateTime": "2026-01-20T09:00:00Z",
      "size": 20480
    }
  ]
}
```

### Version ID Formats [VERIFIED]

- **OneDrive Personal**: Numeric (e.g., "512", "1024")
- **OneDrive Business/SharePoint**: Major.Minor (e.g., "1.0", "2.0", "1.5")

### SDK Examples

**PowerShell**:
```powershell
Get-MgDriveItemVersion -DriveId $driveId -DriveItemId $itemId
```

**C#**:
```csharp
var versions = await graphClient.Drives["{drive-id}"].Items["{item-id}"].Versions.GetAsync();
```

**JavaScript**:
```javascript
let versions = await client.api('/me/drive/items/{item-id}/versions').get();
```

**Python**:
```python
result = await graph_client.drives.by_drive_id('drive-id').items.by_drive_item_id('item-id').versions.get()
```

## 2. GET /drives/{id}/items/{id}/versions/{id} - Get Version

### Description [VERIFIED]

Retrieve metadata for a specific version of a driveItem.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{item-id}/versions/{version-id}
```

### Path Parameters

- **drive-id** (`string`) - Drive GUID
- **item-id** (`string`) - DriveItem ID
- **version-id** (`string`) - Version ID

### Get Current Version

Use `current` as version-id:
```http
GET /drives/{drive-id}/items/{item-id}/versions/current
```

### Response JSON [VERIFIED]

```json
{
  "id": "2.0",
  "lastModifiedBy": {
    "user": {
      "displayName": "John Doe",
      "email": "john@contoso.com",
      "id": "user-guid"
    }
  },
  "lastModifiedDateTime": "2026-01-25T10:30:00Z",
  "size": 25600,
  "publication": {
    "level": "published",
    "versionId": "2.0"
  }
}
```

### SDK Examples

**C#**:
```csharp
var version = await graphClient.Drives["{drive-id}"].Items["{item-id}"]
    .Versions["{version-id}"].GetAsync();
```

## 3. GET /drives/{id}/items/{id}/versions/{id}/content - Download Version Content

### Description [VERIFIED]

Download the content of a specific version of a file.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{item-id}/versions/{version-id}/content
```

### Response [VERIFIED]

- **302 Found** - Redirect to pre-authenticated download URL
- **200 OK** - File content (after redirect)

### SDK Examples

**PowerShell**:
```powershell
Get-MgDriveItemVersionContent -DriveId $driveId -DriveItemId $itemId -DriveItemVersionId $versionId -OutFile "version-backup.docx"
```

**C#**:
```csharp
var stream = await graphClient.Drives["{drive-id}"].Items["{item-id}"]
    .Versions["{version-id}"].Content.GetAsync();
    
using var fileStream = File.Create("version-backup.docx");
await stream.CopyToAsync(fileStream);
```

**JavaScript**:
```javascript
// Get download URL
const response = await client.api('/me/drive/items/{item-id}/versions/{version-id}/content')
    .responseType(ResponseType.RAW)
    .get();
```

## 4. POST /drives/{id}/items/{id}/versions/{id}/restoreVersion - Restore Version

### Description [VERIFIED]

Restore a previous version to be the current version. Creates a **new version** with the old content - does not delete any existing versions.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{item-id}/versions/{version-id}/restoreVersion
```

### Request Body

None.

### Response [VERIFIED]

- **204 No Content** - Success

### Behavior [VERIFIED]

1. Content from specified version becomes new current content
2. A new version is created (version number increments)
3. All previous versions are preserved
4. File metadata (name, location) is unchanged

### SDK Examples

**PowerShell**:
```powershell
Restore-MgDriveItemVersion -DriveId $driveId -DriveItemId $itemId -DriveItemVersionId $versionId
```

**C#**:
```csharp
await graphClient.Drives["{drive-id}"].Items["{item-id}"]
    .Versions["{version-id}"].RestoreVersion.PostAsync();
```

**JavaScript**:
```javascript
await client.api('/me/drive/items/{item-id}/versions/{version-id}/restoreVersion')
    .post({});
```

**Python**:
```python
await graph_client.drives.by_drive_id('drive-id').items.by_drive_item_id('item-id').versions.by_drive_item_version_id('version-id').restore_version.post()
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid version ID
- **401 Unauthorized** - Missing or invalid authentication
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Item or version does not exist
- **429 Too Many Requests** - Rate limit exceeded

### Error Response Format

```json
{
  "error": {
    "code": "itemNotFound",
    "message": "The specified version was not found.",
    "innerError": {
      "request-id": "guid",
      "date": "datetime"
    }
  }
}
```

## Version Retention [VERIFIED]

**OneDrive Personal**:
- Major versions retained for 30 days by default
- Configurable by user

**OneDrive for Business / SharePoint**:
- Major versions: Configurable (default 500)
- Minor versions: Configurable (default 0 or limited)
- Admin-controlled retention policies

**When Versions Are Created**:
- OneDrive: On each save (auto-coalesced)
- SharePoint: On check-in, or automatic with co-authoring
- Configuration varies by library settings

## Best Practices [VERIFIED]

1. **Version comparison**: Download multiple versions and diff locally
2. **Restore carefully**: Restoring creates new version, doesn't delete others
3. **Check quotas**: Versions count against storage quota
4. **Use publication facet**: Check `publication.level` for draft vs published

## Sources

- **MSGRAPH-VERS-SC-01**: https://learn.microsoft.com/en-us/graph/api/driveitem-list-versions?view=graph-rest-1.0
- **MSGRAPH-VERS-SC-02**: https://learn.microsoft.com/en-us/graph/api/driveitemversion-get?view=graph-rest-1.0
- **MSGRAPH-VERS-SC-03**: https://learn.microsoft.com/en-us/graph/api/driveitemversion-get-contents?view=graph-rest-1.0
- **MSGRAPH-VERS-SC-04**: https://learn.microsoft.com/en-us/graph/api/driveitemversion-restore?view=graph-rest-1.0

## Document History

**[2026-01-28 19:00]**
- Initial creation with 4 version management endpoints
- Full JSON request/response examples
- SDK examples for PowerShell, C#, JavaScript, Python
- Version retention policies documented
