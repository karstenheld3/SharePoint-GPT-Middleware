# INFO: Microsoft Graph API - DriveItem Media Methods

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for DriveItem media methods (thumbnails, preview, follow) with request/response JSON and examples
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_MSGRAPH-IN00_TOC.md [MSGRAPH-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Display file thumbnails in custom document browsers and galleries
- Embed document previews in web applications without full download
- Build "Recently Viewed" or "Favorites" features using follow/unfollow
- Create visual file pickers with image previews
- Generate document cards showing file previews in dashboards
- Implement notification systems for followed document changes

**Key findings**:
- Thumbnails auto-generated for images, Office docs, PDFs, and videos
- Custom thumbnail sizes supported via `c{width}x{height}` format
- Preview URLs are short-lived (security) - regenerate for each use
- Follow/unfollow is user-centric - requires delegated permissions only
- Preview renders on behalf of caller - respects user permissions
- Not all file types support thumbnails (check supported formats)

## Quick Reference Summary

**Endpoints covered**: 4 media/follow methods

- `GET /drives/{id}/items/{id}/thumbnails` - Retrieve thumbnail images
- `POST /drives/{id}/items/{id}/preview` - Get embeddable preview URL
- `POST /drives/{id}/items/{id}/follow` - Follow a driveItem for updates
- `POST /drives/{id}/items/{id}/unfollow` - Stop following a driveItem

**Permissions required**:
- Delegated: `Files.Read`, `Files.ReadWrite`, `Files.Read.All`, `Files.ReadWrite.All`, `Sites.Read.All`, `Sites.ReadWrite.All`
- Application: `Files.Read.All`, `Files.ReadWrite.All`, `Sites.Read.All`, `Sites.ReadWrite.All`
- **Least privilege**: `Files.Read` (delegated) for read operations
- Note: SharePoint Embedded requires `FileStorageContainer.Selected`

**DriveItem ID format**: `{driveId}` and `{itemId}` are GUIDs
- Example: `b!kGr-22ksSkuABC123/items/01ABC123DEF456`

## ThumbnailSet Resource Type [VERIFIED]

### JSON Schema

```json
{
  "id": "string",
  "small": { "@odata.type": "microsoft.graph.thumbnail" },
  "medium": { "@odata.type": "microsoft.graph.thumbnail" },
  "large": { "@odata.type": "microsoft.graph.thumbnail" },
  "source": { "@odata.type": "microsoft.graph.thumbnail" }
}
```

### Thumbnail Object Properties [VERIFIED]

```json
{
  "height": 100,
  "width": 100,
  "url": "https://...",
  "content": "base64-encoded-binary",
  "sourceItemId": "string"
}
```

- **height** (`int32`) - Height of the thumbnail in pixels
- **width** (`int32`) - Width of the thumbnail in pixels
- **url** (`string`) - URL to fetch the thumbnail content
- **content** (`stream`) - Content stream for the thumbnail (base64)
- **sourceItemId** (`string`) - Unique identifier for the item that provided the thumbnail

### Standard Thumbnail Sizes [VERIFIED]

- **small** - 96x96 cropped
- **medium** - 176x176 cropped
- **large** - 800x800 scaled (aspect ratio preserved)
- **smallSquare** - 48x48 cropped square
- **mediumSquare** - 176x176 cropped square
- **largeSquare** - 800x800 cropped square

## 1. GET /drives/{id}/items/{id}/thumbnails - List Thumbnails

### Description [VERIFIED]

Retrieves a collection of ThumbnailSet resources for a DriveItem. Items can have zero or more thumbnails depending on file type and storage backend.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/drives/{driveId}/items/{itemId}/thumbnails
```

Alternative paths:
```http
GET https://graph.microsoft.com/v1.0/me/drive/items/{itemId}/thumbnails
GET https://graph.microsoft.com/v1.0/users/{userId}/drive/items/{itemId}/thumbnails
GET https://graph.microsoft.com/v1.0/groups/{groupId}/drive/items/{itemId}/thumbnails
GET https://graph.microsoft.com/v1.0/sites/{siteId}/drive/items/{itemId}/thumbnails
```

### Path Parameters

- **driveId** (`string`) - Unique identifier of the drive
- **itemId** (`string`) - Unique identifier of the driveItem

### Query Parameters

- **$select** - Select specific thumbnail sizes: `$select=small,medium`
- **originalOrientation** (`boolean`) - Return with original EXIF orientation (OneDrive Personal only)

### Request Headers

- **Authorization**: `Bearer {token}`

### Request Example

```http
GET https://graph.microsoft.com/v1.0/me/drive/items/01ABC123DEF456/thumbnails
Authorization: Bearer {token}
```

### Response JSON [VERIFIED]

```json
{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#Collection(thumbnailSet)",
  "value": [
    {
      "id": "0",
      "small": {
        "height": 64,
        "width": 96,
        "url": "https://sn3302files.onedrive.com/..."
      },
      "medium": {
        "height": 117,
        "width": 176,
        "url": "https://sn3302files.onedrive.com/..."
      },
      "large": {
        "height": 533,
        "width": 800,
        "url": "https://sn3302files.onedrive.com/..."
      }
    }
  ]
}
```

### Get Single Thumbnail

```http
GET https://graph.microsoft.com/v1.0/drives/{driveId}/items/{itemId}/thumbnails/{thumbId}/{size}
```

**Example**:
```http
GET https://graph.microsoft.com/v1.0/me/drive/items/01ABC123DEF456/thumbnails/0/small
```

### Get Thumbnail Binary Content

```http
GET https://graph.microsoft.com/v1.0/drives/{driveId}/items/{itemId}/thumbnails/{thumbId}/{size}/content
```

Returns: Binary image data with appropriate Content-Type header.

### Custom Thumbnail Sizes [VERIFIED]

Request custom dimensions using `c{width}x{height}` format:

```http
GET https://graph.microsoft.com/v1.0/me/drive/items/{itemId}/thumbnails/0/c300x400/content
```

**Format options**:
- `c{width}x{height}` - Custom cropped size
- `c{width}x{height}_crop` - Explicit crop mode

**Examples**:
- `c100x100` - 100x100 cropped
- `c400x300_crop` - 400x300 cropped

### Include Thumbnails with DriveItem Listing

```http
GET https://graph.microsoft.com/v1.0/me/drive/items/{itemId}/children?$expand=thumbnails
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Files
Get-MgDriveItemThumbnail -DriveId $driveId -DriveItemId $driveItemId
```

**C#**:
```csharp
var thumbnails = await graphClient.Drives["{drive-id}"]
    .Items["{driveItem-id}"]
    .Thumbnails
    .GetAsync();
```

**JavaScript**:
```javascript
let thumbnails = await client.api('/me/drive/items/{item-id}/thumbnails').get();
```

**Python**:
```python
thumbnails = await graph_client.drives.by_drive_id('drive-id').items.by_drive_item_id('item-id').thumbnails.get()
```

## 2. POST /drives/{id}/items/{id}/preview - Get Preview URL

### Description [VERIFIED]

Obtains a short-lived embeddable URL for rendering a temporary preview of the item. Only available on SharePoint and OneDrive for Business.

**Important Security Note**: The preview URL renders on behalf of the calling identity. Anyone who accesses the URL acts as the caller with the caller's permissions. Do not share preview URLs with other users.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/drives/{driveId}/items/{itemId}/preview
```

Alternative paths:
```http
POST https://graph.microsoft.com/v1.0/me/drive/items/{itemId}/preview
POST https://graph.microsoft.com/v1.0/users/{userId}/drive/items/{itemId}/preview
POST https://graph.microsoft.com/v1.0/groups/{groupId}/drive/items/{itemId}/preview
POST https://graph.microsoft.com/v1.0/sites/{siteId}/drive/items/{itemId}/preview
POST https://graph.microsoft.com/v1.0/shares/{shareId}/driveItem/preview
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
  "page": "string",
  "zoom": 1.0
}
```

**Properties**:
- **page** (`string`, optional) - Page number to start preview (for multi-page documents)
- **zoom** (`double`, optional) - Zoom level as a decimal (e.g., 1.0 = 100%)

### Request Example

```http
POST https://graph.microsoft.com/v1.0/me/drive/items/01ABC123DEF456/preview
Authorization: Bearer {token}
Content-Type: application/json

{
  "page": "1",
  "zoom": 1.5
}
```

### Response JSON [VERIFIED]

```json
{
  "getUrl": "https://www.onedrive.com/embed?foo=bar&bar=baz",
  "postParameters": "param1=value&param2=another%20value",
  "postUrl": "https://www.onedrive.com/embed_by_post"
}
```

**Response Properties**:
- **getUrl** (`string`) - URL for GET-based embed
- **postUrl** (`string`) - URL for POST-based embed
- **postParameters** (`string`) - Form parameters for POST (application/x-www-form-urlencoded)

### Using POST-based Preview

```http
POST https://www.onedrive.com/embed_by_post
Content-Type: application/x-www-form-urlencoded

param1=value&param2=another%20value
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Files
Invoke-MgPreviewDriveItem -DriveId $driveId -DriveItemId $driveItemId
```

**C#**:
```csharp
var requestBody = new PreviewPostRequestBody
{
    Page = "1",
    Zoom = 1.0
};
var result = await graphClient.Drives["{drive-id}"]
    .Items["{driveItem-id}"]
    .Preview
    .PostAsync(requestBody);
```

**JavaScript**:
```javascript
let result = await client.api('/me/drive/items/{item-id}/preview')
    .post({ page: '1', zoom: 1.0 });
```

**Python**:
```python
request_body = PreviewPostRequestBody(page="1", zoom=1.0)
result = await graph_client.drives.by_drive_id('drive-id').items.by_drive_item_id('item-id').preview.post(request_body)
```

## 3. POST /drives/{id}/items/{id}/follow - Follow DriveItem

### Description [VERIFIED]

Follows a driveItem to receive notifications about changes. Followed items appear in the user's "Following" list. This is a user-centric operation and requires delegated permissions.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/drives/{driveId}/items/{itemId}/follow
```

Alternative paths:
```http
POST https://graph.microsoft.com/v1.0/me/drive/items/{itemId}/follow
POST https://graph.microsoft.com/v1.0/users/{userId}/drive/items/{itemId}/follow
POST https://graph.microsoft.com/v1.0/groups/{groupId}/drive/items/{itemId}/follow
POST https://graph.microsoft.com/v1.0/sites/{siteId}/drive/items/{itemId}/follow
```

### Path Parameters

- **driveId** (`string`) - Unique identifier of the drive
- **itemId** (`string`) - Unique identifier of the driveItem to follow

### Request Headers

- **Authorization**: `Bearer {token}`

### Request Body

Do not supply a request body for this method.

### Request Example

```http
POST https://graph.microsoft.com/v1.0/me/drive/items/01ABC123DEF456/follow
Authorization: Bearer {token}
```

### Response JSON [VERIFIED]

Returns the followed DriveItem:

```json
{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#driveItem",
  "id": "01ABC123DEF456",
  "name": "Important Document.docx",
  "webUrl": "https://contoso.sharepoint.com/...",
  "file": {
    "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
  }
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Files
Invoke-MgFollowDriveItem -DriveId $driveId -DriveItemId $driveItemId
```

**C#**:
```csharp
var result = await graphClient.Drives["{drive-id}"]
    .Items["{driveItem-id}"]
    .Follow
    .PostAsync();
```

**JavaScript**:
```javascript
let result = await client.api('/me/drive/items/{item-id}/follow').post();
```

**Python**:
```python
result = await graph_client.drives.by_drive_id('drive-id').items.by_drive_item_id('item-id').follow.post()
```

## 4. POST /drives/{id}/items/{id}/unfollow - Unfollow DriveItem

### Description [VERIFIED]

Stops following a driveItem. The item is removed from the user's "Following" list. This is a user-centric operation.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/drives/{driveId}/items/{itemId}/unfollow
```

Alternative paths:
```http
POST https://graph.microsoft.com/v1.0/me/drive/items/{itemId}/unfollow
POST https://graph.microsoft.com/v1.0/users/{userId}/drive/items/{itemId}/unfollow
DELETE https://graph.microsoft.com/v1.0/me/drive/following/{itemId}
DELETE https://graph.microsoft.com/v1.0/users/{userId}/drive/following/{itemId}
```

### Path Parameters

- **driveId** (`string`) - Unique identifier of the drive
- **itemId** (`string`) - Unique identifier of the driveItem to unfollow

### Request Headers

- **Authorization**: `Bearer {token}`

### Request Body

Do not supply a request body for this method.

### Request Example

```http
POST https://graph.microsoft.com/v1.0/me/drive/items/01ABC123DEF456/unfollow
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
Invoke-MgUnfollowDriveItem -DriveId $driveId -DriveItemId $driveItemId
```

**C#**:
```csharp
await graphClient.Drives["{drive-id}"]
    .Items["{driveItem-id}"]
    .Unfollow
    .PostAsync();
```

**JavaScript**:
```javascript
await client.api('/me/drive/items/{item-id}/unfollow').post();
```

**Python**:
```python
await graph_client.drives.by_drive_id('drive-id').items.by_drive_item_id('item-id').unfollow.post()
```

## List Followed Items [VERIFIED]

Retrieve the list of items the user is following:

```http
GET https://graph.microsoft.com/v1.0/me/drive/following
```

**Response**:
```json
{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#Collection(driveItem)",
  "value": [
    {
      "id": "01ABC123DEF456",
      "name": "Important Document.docx",
      "webUrl": "https://contoso.sharepoint.com/..."
    }
  ]
}
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid parameters or unsupported file type for thumbnails
- **401 Unauthorized** - Missing or invalid authentication token
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - DriveItem does not exist or no thumbnails available
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

**Throttling Behavior**:
- HTTP 429 (Too Many Requests) returned when throttled
- `Retry-After` header indicates seconds to wait

**Best Practices**:
- Cache thumbnail URLs (valid for ~24 hours)
- Use `$expand=thumbnails` when listing items to reduce calls
- Request only needed thumbnail sizes with `$select`
- Implement exponential backoff

**Resource Units**:
- GET thumbnails: ~1-2 resource units
- Preview: ~2 resource units
- Follow/Unfollow: ~1 resource unit

## File Type Support [VERIFIED]

**Thumbnails supported for**:
- Images (JPEG, PNG, GIF, BMP, TIFF)
- Office documents (Word, Excel, PowerPoint)
- PDF files
- Videos (first frame)

**Preview supported for**:
- Office documents (Word, Excel, PowerPoint)
- PDF files
- Images
- Text files

**Not supported**:
- Encrypted files
- Files in transit
- Some legacy formats

## Sources

- **MSGRAPH-MEDIA-SC-01**: https://learn.microsoft.com/en-us/graph/api/driveitem-list-thumbnails?view=graph-rest-1.0
- **MSGRAPH-MEDIA-SC-02**: https://learn.microsoft.com/en-us/graph/api/driveitem-preview?view=graph-rest-1.0
- **MSGRAPH-MEDIA-SC-03**: https://learn.microsoft.com/en-us/graph/api/driveitem-follow?view=graph-rest-1.0
- **MSGRAPH-MEDIA-SC-04**: https://learn.microsoft.com/en-us/graph/api/driveitem-unfollow?view=graph-rest-1.0

## Document History

**[2026-01-28 17:55]**
- Initial creation with 4 endpoints
- Added ThumbnailSet resource type documentation
- Added custom thumbnail size patterns
- Added file type support matrix
