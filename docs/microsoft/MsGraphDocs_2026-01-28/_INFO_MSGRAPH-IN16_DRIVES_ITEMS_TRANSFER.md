# INFO: Microsoft Graph API - DriveItem Upload/Download Methods

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for DriveItem file transfer methods (upload and download)
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `_INFO_MSGRAPH_DRIVEITEMS_CORE.md [MSGRAPH-IN01]` for core driveItem operations

## Summary

**Use cases**:
- Upload documents from web applications or desktop clients
- Implement file sync clients with resumable upload support
- Download files for offline access or processing
- Convert Office documents to PDF on-the-fly during download
- Build backup solutions that transfer files to/from OneDrive/SharePoint
- Implement drag-and-drop file upload in web apps
- Stream large files without loading entire content into memory

**Key findings**:
- Simple PUT upload limited to 4 MB; use upload session for larger files
- Upload session supports files up to 250 GB (OneDrive) / 15 GB (SharePoint)
- Chunk size MUST be multiple of 320 KiB (327,680 bytes) - violations may cause cryptic errors or corrupted files
- Maximum chunk size is 60 MiB per request; recommended 5-10 MiB for stability
- Upload sessions expire; store uploadUrl and check progress before resuming
- Download returns 302 redirect to pre-authenticated URL (short-lived)
- For browser downloads, use `@microsoft.graph.downloadUrl` from item metadata (CORS-safe)
- Format conversion (PDF) only supported for Office documents
- Conflict behavior options: `fail`, `replace`, `rename` - choose based on use case

## Quick Reference Summary

**Endpoints covered**: 4 file transfer methods

- `PUT /drives/{id}/items/{id}:/{filename}:/content` - Upload small file (<4MB)
- `POST /drives/{id}/items/{id}:/{filename}:/createUploadSession` - Create resumable upload session
- `GET /drives/{id}/items/{id}/content` - Download file content
- `GET /drives/{id}/items/{id}/content?format={format}` - Download with format conversion

**Permissions required**:
- Delegated: `Files.ReadWrite`, `Files.ReadWrite.All`
- Application: `Files.ReadWrite.All`, `Sites.ReadWrite.All`
- **Least privilege**: `Files.ReadWrite` for personal; `Sites.ReadWrite.All` for SharePoint

**Size Limits**:
- Simple upload (PUT): Up to 4 MB
- Resumable upload: Up to 250 GB (OneDrive), 15 GB (SharePoint)

## 1. PUT /drives/{id}/items/{parent-id}:/{filename}:/content - Simple Upload

### Description [VERIFIED]

Upload a new file or replace existing file content in a single request. **Limited to 4 MB**. For larger files, use resumable upload.

### HTTP Request - New File

```http
PUT https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{parent-id}:/{filename}:/content
```

Alternative paths:
```http
PUT /me/drive/items/{parent-id}:/{filename}:/content
PUT /sites/{site-id}/drive/items/{parent-id}:/{filename}:/content
PUT /me/drive/root:/{folder-path}/{filename}:/content
```

### HTTP Request - Replace Existing

```http
PUT https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{item-id}/content
```

### Request Headers

- **Authorization**: `Bearer {token}`
- **Content-Type**: File MIME type (e.g., `application/pdf`, `image/png`)
- **Content-Length**: File size in bytes

### Request Body

Binary file content (raw bytes).

### Conflict Behavior

Add query parameter:
```http
PUT /me/drive/items/{parent-id}:/{filename}:/content?@microsoft.graph.conflictBehavior=rename
```

Values: `fail`, `replace`, `rename`

### Response JSON [VERIFIED]

Returns 201 Created (new) or 200 OK (replace) with driveItem:

```json
{
  "id": "new-item-id",
  "name": "document.pdf",
  "size": 102400,
  "file": {
    "mimeType": "application/pdf",
    "hashes": {
      "quickXorHash": "aGFzaA=="
    }
  },
  "createdDateTime": "2026-01-28T16:00:00Z",
  "lastModifiedDateTime": "2026-01-28T16:00:00Z",
  "webUrl": "https://contoso.sharepoint.com/sites/team/Documents/document.pdf"
}
```

### SDK Examples

**PowerShell**:
```powershell
# Read file and upload
$content = Get-Content -Path "C:\file.pdf" -Raw -AsByteStream
Set-MgDriveItemContent -DriveId $driveId -DriveItemId "$parentId`:/$filename`:" -BodyParameter $content
```

**C#**:
```csharp
using var stream = File.OpenRead("file.pdf");
var result = await graphClient.Drives["{drive-id}"]
    .Items["{parent-id}:/{filename}:"]
    .Content
    .PutAsync(stream);
```

**JavaScript**:
```javascript
const content = fs.readFileSync('file.pdf');
await client.api('/me/drive/items/{parent-id}:/{filename}:/content')
    .put(content);
```

## 2. POST createUploadSession - Resumable Upload

### Description [VERIFIED]

Create an upload session for large files (up to 250 GB). Supports resuming interrupted uploads and uploading in chunks.

### Step 1: Create Upload Session

```http
POST https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{parent-id}:/{filename}:/createUploadSession
```

### Request Body

```json
{
  "item": {
    "@microsoft.graph.conflictBehavior": "rename",
    "name": "largefile.zip"
  },
  "deferCommit": false
}
```

### Session Response [VERIFIED]

```json
{
  "uploadUrl": "https://sn3302.up.1drv.com/up/fe6987415ace7X4e1eF86...",
  "expirationDateTime": "2026-01-29T16:00:00Z"
}
```

### Step 2: Upload Bytes

Send file chunks via PUT to the `uploadUrl`:

```http
PUT {uploadUrl}
Content-Length: 26214400
Content-Range: bytes 0-26214399/104857600

<bytes 0-26214399 of file>
```

### Chunk Requirements [VERIFIED]

- **Chunk size**: Must be multiple of **320 KiB** (327,680 bytes)
- **Maximum chunk**: 60 MiB per request
- **Sequential**: Chunks must be uploaded in order
- **Recommended**: 5-10 MiB chunks for stability

### Upload Progress Response

During upload:
```json
{
  "expirationDateTime": "2026-01-29T16:00:00Z",
  "nextExpectedRanges": ["26214400-"]
}
```

Final chunk returns the completed driveItem.

### Resume Interrupted Upload

Check progress:
```http
GET {uploadUrl}
```

Response shows which bytes are missing:
```json
{
  "nextExpectedRanges": ["26214400-52428799", "78643200-"]
}
```

### Cancel Upload Session

```http
DELETE {uploadUrl}
```

Returns 204 No Content.

### SDK Examples

**C#**:
```csharp
// Create upload session
var uploadSession = await graphClient.Drives["{drive-id}"]
    .Items["{parent-id}:/{filename}:"]
    .CreateUploadSession
    .PostAsync(new CreateUploadSessionPostRequestBody
    {
        Item = new DriveItemUploadableProperties
        {
            AdditionalData = new Dictionary<string, object>
            {
                { "@microsoft.graph.conflictBehavior", "rename" }
            }
        }
    });

// Upload using SDK helper
using var stream = File.OpenRead("largefile.zip");
var uploadTask = new LargeFileUploadTask<DriveItem>(uploadSession, stream, maxChunkSize: 320 * 1024 * 10);
var result = await uploadTask.UploadAsync();
```

**Python**:
```python
# Create session
session = await graph_client.drives.by_drive_id('drive-id').items.by_drive_item_id('parent-id:/{filename}:').create_upload_session.post(
    CreateUploadSessionPostRequestBody(
        item=DriveItemUploadableProperties(
            additional_data={"@microsoft.graph.conflictBehavior": "rename"}
        )
    )
)

# Use large file upload task
from msgraph.graph_service_client import GraphServiceClient
upload_result = await LargeFileUploadTask.create_upload_session(session, file_path)
```

## 3. GET /drives/{id}/items/{id}/content - Download File

### Description [VERIFIED]

Download the contents of a file. Returns a 302 redirect to a pre-authenticated download URL.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{item-id}/content
```

By path:
```http
GET https://graph.microsoft.com/v1.0/me/drive/root:/{item-path}:/content
```

### Request Headers

- **Authorization**: `Bearer {token}`
- **If-None-Match**: `{etag}` (returns 304 if unchanged)
- **Range**: `bytes=0-1023` (for partial download)

### Response [VERIFIED]

- **302 Found** - Redirect to download URL (follow automatically)
- **200 OK** - File content (if client follows redirect)
- **304 Not Modified** - If ETag matches

The `Location` header contains a pre-authenticated URL valid for a short time.

### Partial Download (Range Requests) [VERIFIED]

```http
GET /drives/{drive-id}/items/{item-id}/content
Range: bytes=0-1023
```

Response:
```
HTTP/1.1 206 Partial Content
Content-Range: bytes 0-1023/10240
Content-Length: 1024
```

### SDK Examples

**PowerShell**:
```powershell
Get-MgDriveItemContent -DriveId $driveId -DriveItemId $itemId -OutFile "downloaded.pdf"
```

**C#**:
```csharp
var stream = await graphClient.Drives["{drive-id}"].Items["{item-id}"].Content.GetAsync();
using var fileStream = File.Create("downloaded.pdf");
await stream.CopyToAsync(fileStream);
```

**JavaScript (CORS considerations)**:
```javascript
// Get download URL (don't auto-follow redirect)
const response = await client.api('/me/drive/items/{item-id}/content')
    .responseType(ResponseType.RAW)
    .get();
    
// Use @microsoft.graph.downloadUrl from item metadata instead for browser downloads
const item = await client.api('/me/drive/items/{item-id}').get();
window.location = item['@microsoft.graph.downloadUrl'];
```

## 4. GET /drives/{id}/items/{id}/content?format={format} - Download with Conversion

### Description [VERIFIED]

Download file with automatic format conversion. Available for certain file types.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{item-id}/content?format={format}
```

### Supported Conversions [VERIFIED]

**From Office documents**:
- `pdf` - Convert to PDF
- `html` - Convert to HTML (preview)

**Example**:
```http
GET /me/drive/items/{item-id}/content?format=pdf
```

Converts Word, Excel, PowerPoint to PDF.

### Response

Returns 302 redirect to converted file download URL.

### SDK Examples

**C#**:
```csharp
var pdfStream = await graphClient.Drives["{drive-id}"].Items["{item-id}"].Content
    .GetAsync(config => config.QueryParameters.Format = "pdf");
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid request or unsupported format
- **401 Unauthorized** - Missing or invalid authentication
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Item does not exist
- **409 Conflict** - Name conflict (conflictBehavior = fail)
- **413 Request Entity Too Large** - File exceeds 4 MB for simple upload
- **416 Range Not Satisfiable** - Invalid byte range
- **429 Too Many Requests** - Rate limit exceeded
- **507 Insufficient Storage** - Quota exceeded

### Upload-Specific Errors [VERIFIED]

- **fragmentOutOfOrder** - Chunks uploaded out of sequence
- **fragmentOverlap** - Byte ranges overlap
- **fragmentTooLarge** - Chunk exceeds 60 MiB
- **invalidChunkSize** - Chunk not multiple of 320 KiB

## Best Practices [VERIFIED]

### Upload Strategy

1. **< 4 MB**: Use simple PUT upload
2. **4 MB - 250 GB**: Use resumable upload session
3. **Chunk size**: 5-10 MiB for optimal balance
4. **Retry logic**: Implement exponential backoff
5. **Progress tracking**: Use `nextExpectedRanges` to show progress

### Download Strategy

1. **Browser downloads**: Use `@microsoft.graph.downloadUrl` from item metadata
2. **Server-side**: Follow 302 redirect or use stream directly
3. **Large files**: Use Range headers for chunked download
4. **Caching**: Use If-None-Match with ETag for conditional requests

### Chunked Upload Algorithm

```
1. Create upload session
2. Calculate total chunks (file_size / chunk_size)
3. For each chunk:
   a. Read chunk bytes
   b. PUT to uploadUrl with Content-Range header
   c. On failure: retry with backoff
   d. On success: check nextExpectedRanges
4. Final chunk returns completed driveItem
```

## Sources

- **MSGRAPH-XFER-SC-01**: https://learn.microsoft.com/en-us/graph/api/driveitem-put-content?view=graph-rest-1.0
- **MSGRAPH-XFER-SC-02**: https://learn.microsoft.com/en-us/graph/api/driveitem-createuploadsession?view=graph-rest-1.0
- **MSGRAPH-XFER-SC-03**: https://learn.microsoft.com/en-us/graph/api/driveitem-get-content?view=graph-rest-1.0
- **MSGRAPH-XFER-SC-04**: https://learn.microsoft.com/en-us/graph/large-file-upload

## Document History

**[2026-01-28 18:50]**
- Initial creation with 4 file transfer endpoints
- Resumable upload session workflow documented
- Chunk size requirements and best practices
- SDK examples for PowerShell, C#, JavaScript, Python
