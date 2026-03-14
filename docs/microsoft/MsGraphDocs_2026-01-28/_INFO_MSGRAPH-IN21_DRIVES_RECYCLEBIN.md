# INFO: Microsoft Graph API - RecycleBin Methods

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for RecycleBin methods for deleted item management
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_MSGRAPH-IN00_TOC.md [MSGRAPH-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Implement "undo delete" functionality in custom file managers
- Build data retention compliance by tracking deleted items
- Create self-service recovery portals for end users
- Permanently purge sensitive documents after deletion
- Audit deleted content before retention period expires
- Build migration tools that handle deleted item recovery

**Key findings**:
- Soft delete moves to recycle bin; permanent delete bypasses it entirely
- Restore API currently only works on OneDrive Personal (not Business/SharePoint)
- Retention: 30 days (personal), 93 days (business/SharePoint) in recycle bin
- Use delta query with `includeDeletedItems=true` to track deletions
- SharePoint has two-stage recycle bin (user + site collection admin)
- No Graph API for restoring SharePoint/OneDrive for Business items

## Quick Reference Summary

**Endpoints covered**: 4 recycle bin methods

- `DELETE /drives/{id}/items/{id}` - Delete item (moves to recycle bin)
- `GET /drives/{id}/items/{id}?includeDeletedItems=true` - Get deleted item
- `POST /drives/{id}/items/{id}/restore` - Restore from recycle bin
- `POST /drives/{id}/items/{id}/permanentDelete` - Permanently delete

**Permissions required**:
- Delegated: `Files.ReadWrite`, `Files.ReadWrite.All`
- Application: `Files.ReadWrite.All`
- **Least privilege**: `Files.ReadWrite` for user's own files
- Note: SharePoint Embedded requires `FileStorageContainer.Selected`

**Platform Support**:
- `restore`: OneDrive Personal only (currently)
- `permanentDelete`: All platforms
- `delete`: All platforms

## Recycle Bin Behavior [VERIFIED]

### SharePoint/OneDrive Recycle Bin Stages

1. **First-stage recycle bin** - User-accessible, items can be restored
2. **Second-stage recycle bin** - Site collection admin only
3. **Permanent deletion** - After retention period or manual permanent delete

### Retention Periods [VERIFIED]

- **OneDrive Personal**: 30 days in recycle bin
- **OneDrive for Business**: 93 days total (first + second stage)
- **SharePoint Online**: 93 days total

### Deleted Item Properties

When an item is deleted, it gains these properties:
- `deleted.state` = `deleted`
- `deleted.deletedDateTime` = timestamp of deletion

## 1. DELETE /drives/{id}/items/{id} - Delete DriveItem

### Description [VERIFIED]

Deletes a driveItem by moving it to the recycle bin. The item can be restored within the retention period.

### HTTP Request

```http
DELETE https://graph.microsoft.com/v1.0/drives/{driveId}/items/{itemId}
```

Alternative paths:
```http
DELETE https://graph.microsoft.com/v1.0/me/drive/items/{itemId}
DELETE https://graph.microsoft.com/v1.0/users/{userId}/drive/items/{itemId}
DELETE https://graph.microsoft.com/v1.0/groups/{groupId}/drive/items/{itemId}
DELETE https://graph.microsoft.com/v1.0/sites/{siteId}/drive/items/{itemId}
```

### Path Parameters

- **driveId** (`string`) - Drive identifier
- **itemId** (`string`) - DriveItem identifier

### Request Headers

- **Authorization**: `Bearer {token}`

### Request Example

```http
DELETE https://graph.microsoft.com/v1.0/me/drive/items/01ABC123DEF456
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
Remove-MgDriveItem -DriveId $driveId -DriveItemId $itemId
```

**C#**:
```csharp
await graphClient.Drives["{drive-id}"].Items["{driveItem-id}"].DeleteAsync();
```

**JavaScript**:
```javascript
await client.api('/me/drive/items/{item-id}').delete();
```

**Python**:
```python
await graph_client.drives.by_drive_id('drive-id').items.by_drive_item_id('item-id').delete()
```

## 2. GET /drives/{id}/items/{id} - Get Deleted Item

### Description [VERIFIED]

Retrieves a deleted driveItem from the recycle bin using the `includeDeletedItems` query parameter.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/drives/{driveId}/items/{itemId}?includeDeletedItems=true
```

### Query Parameters

- **includeDeletedItems** (`boolean`) - Include deleted items in response

### Request Example

```http
GET https://graph.microsoft.com/v1.0/me/drive/items/01ABC123DEF456?includeDeletedItems=true
Authorization: Bearer {token}
```

### Response JSON [VERIFIED]

```json
{
  "id": "01ABC123DEF456",
  "name": "Deleted Document.docx",
  "deleted": {
    "state": "deleted",
    "deletedDateTime": "2026-01-28T10:30:00Z"
  },
  "file": {
    "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
  },
  "parentReference": {
    "driveId": "drive-guid",
    "id": "parent-folder-id"
  }
}
```

### List Deleted Items via Delta

Use delta query to find deleted items:

```http
GET https://graph.microsoft.com/v1.0/drives/{driveId}/root/delta?token=latest
```

Deleted items in delta response have `deleted` facet:

```json
{
  "@odata.context": "...",
  "value": [
    {
      "id": "deleted-item-id",
      "name": "Deleted File.txt",
      "deleted": {
        "state": "deleted"
      }
    }
  ],
  "@odata.deltaLink": "..."
}
```

## 3. POST /drives/{id}/items/{id}/restore - Restore DriveItem

### Description [VERIFIED]

Restores a deleted driveItem from the recycle bin to its original location or a specified location.

**Important**: Currently only available for **OneDrive Personal**.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/me/drive/items/{itemId}/restore
```

### Path Parameters

- **itemId** (`string`) - ID of the deleted item to restore

### Request Headers

- **Authorization**: `Bearer {token}`
- **Content-Type**: `application/json`

### Request Body

```json
{
  "parentReference": {
    "id": "parent-folder-id"
  },
  "name": "Restored Document.docx"
}
```

**Properties** (all optional):
- **parentReference** (`itemReference`) - Target folder for restore
- **name** (`string`) - New name for the restored item

If not specified, item restores to original location with original name.

### Request Example - Restore to Original Location

```http
POST https://graph.microsoft.com/v1.0/me/drive/items/01ABC123DEF456/restore
Authorization: Bearer {token}
Content-Type: application/json

{}
```

### Request Example - Restore to Different Location

```http
POST https://graph.microsoft.com/v1.0/me/drive/items/01ABC123DEF456/restore
Authorization: Bearer {token}
Content-Type: application/json

{
  "parentReference": {
    "id": "new-parent-folder-id"
  },
  "name": "Recovered Document.docx"
}
```

### Response JSON [VERIFIED]

Returns the restored driveItem:

```json
{
  "id": "01ABC123DEF456",
  "name": "Restored Document.docx",
  "webUrl": "https://onedrive.live.com/...",
  "file": {
    "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
  },
  "parentReference": {
    "driveId": "drive-guid",
    "id": "parent-folder-id",
    "path": "/drive/root:/Documents"
  }
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Files
Restore-MgDriveItem -DriveId $driveId -DriveItemId $itemId
```

**C#**:
```csharp
var requestBody = new RestorePostRequestBody
{
    ParentReference = new ItemReference
    {
        Id = "new-parent-id"
    },
    Name = "Restored Document.docx"
};
var result = await graphClient.Me.Drive.Items["{driveItem-id}"]
    .Restore
    .PostAsync(requestBody);
```

**JavaScript**:
```javascript
let result = await client.api('/me/drive/items/{item-id}/restore')
    .post({
        parentReference: { id: 'new-parent-id' },
        name: 'Restored Document.docx'
    });
```

**Python**:
```python
request_body = RestorePostRequestBody(
    parent_reference=ItemReference(id="new-parent-id"),
    name="Restored Document.docx"
)
result = await graph_client.me.drive.items.by_drive_item_id('item-id').restore.post(request_body)
```

## 4. POST /drives/{id}/items/{id}/permanentDelete - Permanently Delete

### Description [VERIFIED]

Permanently deletes a driveItem without moving it to the recycle bin. This action is **irreversible** - the item cannot be restored.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/drives/{driveId}/items/{itemId}/permanentDelete
```

Alternative paths:
```http
POST https://graph.microsoft.com/v1.0/me/drive/items/{itemId}/permanentDelete
POST https://graph.microsoft.com/v1.0/users/{userId}/drive/items/{itemId}/permanentDelete
POST https://graph.microsoft.com/v1.0/groups/{groupId}/drive/items/{itemId}/permanentDelete
POST https://graph.microsoft.com/v1.0/sites/{siteId}/drive/items/{itemId}/permanentDelete
```

### Path Parameters

- **driveId** (`string`) - Drive identifier
- **itemId** (`string`) - DriveItem identifier

### Request Headers

- **Authorization**: `Bearer {token}`

### Request Body

Do not supply a request body.

### Request Example

```http
POST https://graph.microsoft.com/v1.0/me/drive/items/01ABC123DEF456/permanentDelete
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
Invoke-MgPermanentDeleteDriveItem -DriveId $driveId -DriveItemId $itemId
```

**C#**:
```csharp
await graphClient.Drives["{drive-id}"].Items["{driveItem-id}"]
    .PermanentDelete
    .PostAsync();
```

**JavaScript**:
```javascript
await client.api('/me/drive/items/{item-id}/permanentDelete').post();
```

**Python**:
```python
await graph_client.drives.by_drive_id('drive-id').items.by_drive_item_id('item-id').permanent_delete.post()
```

## SharePoint List Item Deletion [VERIFIED]

**Note**: SharePoint list items use different deletion semantics:
- No Graph API for permanent deletion of list items
- Use SharePoint REST API or CSOM for hard delete
- Deleted list items go to site recycle bin

### Delete List Item (Soft Delete)

```http
DELETE https://graph.microsoft.com/v1.0/sites/{siteId}/lists/{listId}/items/{itemId}
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid item ID or parameters
- **401 Unauthorized** - Missing or invalid token
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Item not found or already permanently deleted
- **409 Conflict** - Restore conflict (name collision)
- **429 Too Many Requests** - Rate limit exceeded

### Error Response Format

```json
{
  "error": {
    "code": "itemNotFound",
    "message": "The resource could not be found.",
    "innerError": {
      "request-id": "guid",
      "date": "2026-01-28T12:00:00Z"
    }
  }
}
```

## Throttling Considerations [VERIFIED]

**Best Practices**:
- Batch delete operations where possible
- Use delta queries to track deletions
- Implement exponential backoff

**Resource Units**:
- Delete: ~2 resource units
- Restore: ~3 resource units
- Permanent delete: ~2 resource units

## Platform Limitations Summary [VERIFIED]

**OneDrive Personal**:
- Full restore support
- 30-day retention

**OneDrive for Business**:
- No Graph restore API (use SharePoint REST or admin center)
- 93-day retention
- PermanentDelete supported

**SharePoint Online**:
- No Graph restore API for driveItems
- Site recycle bin accessible via SharePoint REST
- 93-day retention
- PermanentDelete supported

## Sources

- **MSGRAPH-RB-SC-01**: https://learn.microsoft.com/en-us/graph/api/driveitem-delete?view=graph-rest-1.0
- **MSGRAPH-RB-SC-02**: https://learn.microsoft.com/en-us/graph/api/driveitem-restore?view=graph-rest-1.0
- **MSGRAPH-RB-SC-03**: https://learn.microsoft.com/en-us/graph/api/driveitem-permanentdelete?view=graph-rest-1.0
- **MSGRAPH-RB-SC-04**: https://learn.microsoft.com/en-us/graph/api/resources/recyclebin?view=graph-rest-1.0

## Document History

**[2026-01-28 19:25]**
- Initial creation with 4 endpoints
- Added recycle bin behavior documentation
- Added platform limitations matrix
- Added delta query pattern for deleted items
