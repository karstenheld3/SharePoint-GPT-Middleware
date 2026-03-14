# INFO: Microsoft Graph API - DriveItem Core Methods

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for DriveItem API core methods with request/response JSON and examples
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `_INFO_MSGRAPH-IN01_DRIVES_CORE.md [MSGRAPH-IN01]` for drive context

## Summary

**Use cases**:
- Build file browser/explorer UIs for OneDrive and SharePoint
- Navigate folder hierarchies and list directory contents
- Create folder structures programmatically for project organization
- Rename files and folders via metadata updates
- Move files between folders (same drive or cross-drive)
- Delete files with recycle bin support for recovery
- Restore accidentally deleted files from recycle bin

**Key findings**:
- Items addressable by ID (stable) or path (human-readable but can change on rename)
- Path syntax uses colon notation: `/root:/{path}` for path, `/root:/{path}:` for metadata
- Delete moves to recycle bin by default; use permanentDelete for immediate removal
- Move is synchronous (PATCH), unlike copy which is async
- Cross-drive moves supported within same tenant; cross-tenant not supported
- eTag changes on metadata updates; cTag changes on content updates (files)
- For folders, cTag changes when ANY descendant changes (useful for sync detection)
- Expand `children` in single request: `?$expand=children` (limited depth)

## Quick Reference Summary

**Endpoints covered**: 8 DriveItem API core methods

- `GET /drives/{id}/items/{id}` - Get item by ID
- `GET /drives/{id}/root:/{path}` - Get item by path
- `GET /drives/{id}/items/{id}/children` - List folder contents
- `POST /drives/{id}/items/{id}/children` - Create folder
- `PATCH /drives/{id}/items/{id}` - Update item (rename/move)
- `DELETE /drives/{id}/items/{id}` - Delete item (to recycle bin)
- `POST /drives/{id}/items/{id}/permanentDelete` - Permanently delete
- `POST /drives/{id}/items/{id}/restore` - Restore from recycle bin

**Permissions required**:
- Delegated: `Files.Read`, `Files.ReadWrite`, `Files.Read.All`, `Files.ReadWrite.All`
- Application: `Files.Read.All`, `Files.ReadWrite.All`, `Sites.Read.All`, `Sites.ReadWrite.All`
- **Least privilege**: `Files.Read` for read; `Files.ReadWrite` for modifications

**DriveItem ID format**: Encoded string (varies by provider)
- Example: `01CYZLVDIZFVN3BFFODBBZHKXV4GKSDHAZ`

## DriveItem Resource Type

### JSON Schema [VERIFIED]

```json
{
  "id": "string",
  "name": "string",
  "size": "int64",
  "createdBy": { "@odata.type": "microsoft.graph.identitySet" },
  "createdDateTime": "datetime",
  "lastModifiedBy": { "@odata.type": "microsoft.graph.identitySet" },
  "lastModifiedDateTime": "datetime",
  "eTag": "string",
  "cTag": "string",
  "parentReference": { "@odata.type": "microsoft.graph.itemReference" },
  "webUrl": "url",
  "file": { "@odata.type": "microsoft.graph.file" },
  "folder": { "@odata.type": "microsoft.graph.folder" },
  "root": { "@odata.type": "microsoft.graph.root" },
  "@odata.type": "microsoft.graph.driveItem"
}
```

### Properties [VERIFIED]

- **id** - Unique identifier
- **name** - File or folder name
- **size** - Size in bytes (for files)
- **createdBy** - Identity who created the item
- **createdDateTime** - Creation timestamp
- **lastModifiedBy** - Identity who last modified
- **lastModifiedDateTime** - Last modification timestamp
- **eTag** - Entity tag for item metadata
- **cTag** - Content tag (changes when content changes)
- **parentReference** - Reference to parent container:
  ```json
  {
    "driveId": "drive-guid",
    "driveType": "documentLibrary",
    "id": "parent-item-id",
    "path": "/drive/root:/Documents"
  }
  ```
- **webUrl** - URL to view in browser

### Type Facets [VERIFIED]

An item is identified by its facets:

- **file** - Present for files:
  ```json
  {
    "mimeType": "application/pdf",
    "hashes": {
      "quickXorHash": "string",
      "sha1Hash": "string",
      "sha256Hash": "string"
    }
  }
  ```
- **folder** - Present for folders:
  ```json
  {
    "childCount": 15
  }
  ```
- **root** - Present for drive root item (empty object `{}`)
- **image** - Present for images with dimensions
- **video** - Present for videos with dimensions/duration
- **audio** - Present for audio files
- **photo** - Present for photos with EXIF data

### Relationships (expandable via $expand)

- **children** - Child items (for folders)
- **listItem** - Associated SharePoint listItem
- **permissions** - Sharing permissions
- **thumbnails** - Image thumbnails
- **versions** - Version history
- **analytics** - Activity analytics

## 1. GET /drives/{id}/items/{id} - Get Item by ID

### Description [VERIFIED]

Retrieve the metadata for a driveItem by its unique ID.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{item-id}
```

Alternative paths:
```http
GET /me/drive/items/{item-id}
GET /users/{user-id}/drive/items/{item-id}
GET /groups/{group-id}/drive/items/{item-id}
GET /sites/{site-id}/drive/items/{item-id}
```

### Path Parameters

- **drive-id** (`string`) - Drive GUID
- **item-id** (`string`) - DriveItem ID

### OData Query Parameters

- **$select** - Select specific properties
- **$expand** - Expand relationships: `children`, `permissions`, `thumbnails`, `versions`

### Request Headers

- **Authorization**: `Bearer {token}`
- **If-None-Match**: `{etag}` (returns 304 if unchanged)

### Response JSON [VERIFIED]

```json
{
  "id": "01CYZLVDIZFVN3BFFODBBZHKXV4GKSDHAZ",
  "name": "Report.docx",
  "size": 25600,
  "createdBy": {
    "user": {
      "displayName": "John Doe",
      "email": "john@contoso.com"
    }
  },
  "createdDateTime": "2026-01-15T10:30:00Z",
  "lastModifiedBy": {
    "user": {
      "displayName": "Jane Smith"
    }
  },
  "lastModifiedDateTime": "2026-01-28T15:45:00Z",
  "file": {
    "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "hashes": {
      "quickXorHash": "aGhhc2g="
    }
  },
  "parentReference": {
    "driveId": "drive-guid",
    "driveType": "documentLibrary",
    "id": "parent-id",
    "path": "/drive/root:/Documents"
  },
  "webUrl": "https://contoso.sharepoint.com/sites/team/Documents/Report.docx"
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Files
Get-MgDriveItem -DriveId $driveId -DriveItemId $itemId
```

**C#**:
```csharp
var item = await graphClient.Drives["{drive-id}"].Items["{item-id}"].GetAsync();
```

**JavaScript**:
```javascript
let item = await client.api('/drives/{drive-id}/items/{item-id}').get();
```

**Python**:
```python
result = await graph_client.drives.by_drive_id('drive-id').items.by_drive_item_id('item-id').get()
```

## 2. GET /drives/{id}/root:/{path} - Get Item by Path

### Description [VERIFIED]

Retrieve a driveItem by its file system path relative to the drive root.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/drives/{drive-id}/root:/{item-path}
```

Alternative paths:
```http
GET /me/drive/root:/{item-path}
GET /sites/{site-id}/drive/root:/{item-path}
```

### Path Addressing Syntax [VERIFIED]

- **Root**: `/drives/{id}/root`
- **By path**: `/drives/{id}/root:/{path}` (colon before path)
- **Path metadata**: `/drives/{id}/root:/{path}:` (trailing colon for metadata)
- **Path children**: `/drives/{id}/root:/{path}:/children`

### Examples

```http
# Get file in Documents folder
GET /me/drive/root:/Documents/Report.docx

# Get folder
GET /me/drive/root:/Projects/2026

# Get metadata (trailing colon)
GET /me/drive/root:/Documents/Report.docx:

# Get children of folder by path
GET /me/drive/root:/Documents:/children
```

### Response JSON [VERIFIED]

Same as GET by ID - returns driveItem resource.

### SDK Examples

**JavaScript**:
```javascript
let item = await client.api('/me/drive/root:/Documents/Report.docx').get();
```

## 3. GET /drives/{id}/items/{id}/children - List Folder Contents

### Description [VERIFIED]

Return a collection of DriveItems in the children relationship of a folder. Only items with `folder` or `package` facets can have children.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{item-id}/children
```

Or for root:
```http
GET https://graph.microsoft.com/v1.0/drives/{drive-id}/root/children
```

By path:
```http
GET https://graph.microsoft.com/v1.0/drives/{drive-id}/root:/{folder-path}:/children
```

### OData Query Parameters

- **$select** - Select properties
- **$expand** - Expand relationships
- **$top** - Limit results
- **$orderby** - Sort: `name`, `lastModifiedDateTime`, `size`
- **$skipToken** - Pagination token

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "item-id-1",
      "name": "Subfolder",
      "folder": {
        "childCount": 5
      },
      "size": 0,
      "lastModifiedDateTime": "2026-01-20T10:00:00Z"
    },
    {
      "id": "item-id-2",
      "name": "Document.pdf",
      "file": {
        "mimeType": "application/pdf"
      },
      "size": 102400,
      "lastModifiedDateTime": "2026-01-25T14:30:00Z"
    }
  ],
  "@odata.nextLink": "https://graph.microsoft.com/v1.0/drives/.../children?$skiptoken=..."
}
```

### SDK Examples

**PowerShell**:
```powershell
Get-MgDriveItemChild -DriveId $driveId -DriveItemId $folderId
```

**C#**:
```csharp
var children = await graphClient.Drives["{drive-id}"].Items["{folder-id}"].Children.GetAsync();
```

## 4. POST /drives/{id}/items/{id}/children - Create Folder

### Description [VERIFIED]

Create a new folder in a drive. Use PUT with content for file upload (see Transfer document).

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{parent-id}/children
```

### Request Body

```json
{
  "name": "New Folder",
  "folder": {},
  "@microsoft.graph.conflictBehavior": "rename"
}
```

### Conflict Behaviors [VERIFIED]

- **fail** - Return error if item exists (default)
- **replace** - Replace existing item
- **rename** - Append number to name if exists

### Response JSON [VERIFIED]

Returns 201 Created with the folder driveItem:

```json
{
  "id": "new-folder-id",
  "name": "New Folder",
  "folder": {
    "childCount": 0
  },
  "createdDateTime": "2026-01-28T16:00:00Z",
  "webUrl": "https://contoso.sharepoint.com/sites/team/Documents/New Folder"
}
```

### SDK Examples

**PowerShell**:
```powershell
$params = @{
    name = "New Folder"
    folder = @{}
    "@microsoft.graph.conflictBehavior" = "rename"
}
New-MgDriveItemChild -DriveId $driveId -DriveItemId $parentId -BodyParameter $params
```

**JavaScript**:
```javascript
const folder = {
    name: 'New Folder',
    folder: {},
    '@microsoft.graph.conflictBehavior': 'rename'
};
await client.api('/drives/{drive-id}/items/{parent-id}/children').post(folder);
```

## 5. PATCH /drives/{id}/items/{id} - Update Item (Rename/Move)

### Description [VERIFIED]

Update the metadata of a driveItem. Use to rename items or move them to different folders.

### HTTP Request

```http
PATCH https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{item-id}
```

### Rename Example

```json
{
  "name": "New Name.docx"
}
```

### Move Example

```json
{
  "parentReference": {
    "id": "new-parent-folder-id"
  }
}
```

### Move and Rename

```json
{
  "name": "Renamed File.docx",
  "parentReference": {
    "id": "new-parent-folder-id"
  }
}
```

### Response JSON [VERIFIED]

Returns 200 OK with updated driveItem.

### SDK Examples

**C#**:
```csharp
var update = new DriveItem
{
    Name = "New Name.docx"
};
var result = await graphClient.Drives["{drive-id}"].Items["{item-id}"].PatchAsync(update);
```

## 6. DELETE /drives/{id}/items/{id} - Delete Item

### Description [VERIFIED]

Delete a DriveItem by ID or path. **Moves to recycle bin** - not permanent deletion.

### HTTP Request

```http
DELETE https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{item-id}
```

### Request Headers

- **Authorization**: `Bearer {token}`
- **If-Match**: `{etag}` (optional, for optimistic concurrency)

### Special Headers [VERIFIED]

- **bypass-shared-lock**: Bypass shared lock on item
- **bypass-checked-out**: Bypass checkout status

### Response [VERIFIED]

- **204 No Content** - Success
- **412 Precondition Failed** - ETag mismatch

### SDK Examples

**PowerShell**:
```powershell
Remove-MgDriveItem -DriveId $driveId -DriveItemId $itemId
```

**C#**:
```csharp
await graphClient.Drives["{drive-id}"].Items["{item-id}"].DeleteAsync();
```

## 7. POST /drives/{id}/items/{id}/permanentDelete - Permanent Delete

### Description [VERIFIED]

Permanently delete a driveItem without sending to recycle bin. **Irreversible**.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{item-id}/permanentDelete
```

### Request Body

None.

### Response [VERIFIED]

- **204 No Content** - Success

### SDK Examples

**C#**:
```csharp
await graphClient.Drives["{drive-id}"].Items["{item-id}"].PermanentDelete.PostAsync();
```

## 8. POST /drives/{id}/items/{id}/restore - Restore from Recycle Bin

### Description [VERIFIED]

Restore a deleted item from the recycle bin to its original location or a new location.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{item-id}/restore
```

### Request Body (Optional)

Restore to original location:
```json
{}
```

Restore to new location:
```json
{
  "parentReference": {
    "id": "new-parent-id"
  },
  "name": "Restored File.docx"
}
```

### Response JSON [VERIFIED]

Returns 200 OK with restored driveItem.

### SDK Examples

**PowerShell**:
```powershell
Restore-MgDriveItem -DriveId $driveId -DriveItemId $deletedItemId
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid request or item path
- **401 Unauthorized** - Missing or invalid authentication
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Item does not exist
- **409 Conflict** - Name conflict (conflictBehavior = fail)
- **412 Precondition Failed** - ETag mismatch
- **423 Locked** - Item is locked
- **429 Too Many Requests** - Rate limit exceeded
- **507 Insufficient Storage** - Quota exceeded

### Error Response Format

```json
{
  "error": {
    "code": "nameAlreadyExists",
    "message": "An item with the same name already exists.",
    "innerError": {
      "request-id": "guid",
      "date": "datetime"
    }
  }
}
```

## Throttling Considerations [VERIFIED]

**Best Practices**:
- Use `$select` to minimize response size
- Cache item IDs after path lookups
- Use delta queries for sync scenarios
- Implement exponential backoff

**Resource Units**:
- Item GET: ~1 resource unit
- Children list: ~1-2 resource units
- Item create/update/delete: ~2 resource units

## Path vs ID Addressing [VERIFIED]

**Use Path When**:
- User provides file path
- Building UI with breadcrumbs
- One-time lookups

**Use ID When**:
- Storing references
- Repeated operations on same item
- Performance-critical scenarios

**Important**: Paths can change (renames/moves), IDs are stable.

## Sources

- **MSGRAPH-DITEM-SC-01**: https://learn.microsoft.com/en-us/graph/api/resources/driveitem?view=graph-rest-1.0
- **MSGRAPH-DITEM-SC-02**: https://learn.microsoft.com/en-us/graph/api/driveitem-get?view=graph-rest-1.0
- **MSGRAPH-DITEM-SC-03**: https://learn.microsoft.com/en-us/graph/api/driveitem-list-children?view=graph-rest-1.0
- **MSGRAPH-DITEM-SC-04**: https://learn.microsoft.com/en-us/graph/api/driveitem-delete?view=graph-rest-1.0
- **MSGRAPH-DITEM-SC-05**: https://learn.microsoft.com/en-us/graph/api/driveitem-update?view=graph-rest-1.0

## Document History

**[2026-01-28 18:40]**
- Initial creation with 8 DriveItem core endpoints
- Full JSON request/response examples
- SDK examples for PowerShell, C#, JavaScript, Python
- Path addressing patterns documented
