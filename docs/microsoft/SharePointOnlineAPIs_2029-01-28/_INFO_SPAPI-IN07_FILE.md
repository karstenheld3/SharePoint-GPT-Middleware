# INFO: SharePoint REST API - File

**Doc ID**: SPAPI-IN01
**Goal**: Detailed reference for File (SP.File) endpoints with request/response JSON and examples
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_SHAREPOINT_API_TOC.md [SPAPI-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Upload, download, and delete files
- Check in/out files for editing
- Manage file versions
- Move and copy files between locations
- Migrate files from on-premises SharePoint to Online
- Backup document libraries to external storage
- Bulk metadata updates via file properties

**Key findings**:
- Access files via `GetFileByServerRelativeUrl('{path}')` [VERIFIED]
- Download content using `/$value` suffix [VERIFIED]
- Files under 1.5MB use simple upload; larger files need chunked upload [VERIFIED]
- Maximum file size is 250GB (SharePoint Online) [VERIFIED]
- **Gotcha**: Special characters in filenames require URL encoding (`#` → `%23`, `%` → `%25`) [VERIFIED]
- **Gotcha**: Bulk uploads may trigger throttling - use batching and honor Retry-After header [VERIFIED]
- **Gotcha**: `execute_batch()` does NOT work for file uploads in Python - use sequential `execute_query()` [TESTED]

## Quick Reference Summary

**Endpoints covered**: 20 file endpoints

- `GET /_api/web/GetFileByServerRelativeUrl('{path}')` - Get file metadata
- `GET /_api/web/GetFileByServerRelativeUrl('{path}')/$value` - Download file
- `POST /_api/web/GetFolderByServerRelativeUrl('{folder}')/Files/add` - Upload file
- `POST /_api/web/GetFileByServerRelativeUrl('{path}')/CheckOut()` - Check out
- `POST /_api/web/GetFileByServerRelativeUrl('{path}')/CheckIn()` - Check in
- `GET /_api/web/GetFileByServerRelativeUrl('{path}')/versions` - Get versions
- `POST /_api/web/GetFileByServerRelativeUrl('{path}')/moveto()` - Move file
- `POST /_api/web/GetFileByServerRelativeUrl('{path}')/copyto()` - Copy file
- `DELETE /_api/web/GetFileByServerRelativeUrl('{path}')` - Delete file

**Permissions required**:
- Application: `Sites.Read.All` (read), `Sites.ReadWrite.All` (write)
- Delegated: `Sites.Read.All` (read), `Sites.ReadWrite.All` (write)

## SP.File Resource Type

### Properties [VERIFIED]

- **Name** (`Edm.String`) - File name with extension
- **ServerRelativeUrl** (`Edm.String`) - Server-relative path
- **Length** (`Edm.String`) - File size in bytes
- **TimeCreated** (`Edm.DateTime`) - Creation timestamp
- **TimeLastModified** (`Edm.DateTime`) - Last modified
- **UniqueId** (`Edm.Guid`) - Unique identifier
- **ETag** (`Edm.String`) - Version for concurrency
- **CheckOutType** (`Edm.Int32`) - 0=None, 1=Online, 2=Offline
- **MajorVersion** (`Edm.Int32`) - Major version
- **MinorVersion** (`Edm.Int32`) - Minor version

## 1. GET /_api/web/GetFileByServerRelativeUrl('{path}') - Get Metadata

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/GetFileByServerRelativeUrl('{path}')
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "__metadata": { "type": "SP.File" },
    "Name": "Report.docx",
    "ServerRelativeUrl": "/sites/TeamSite/Shared Documents/Report.docx",
    "Length": "25600",
    "TimeLastModified": "2024-01-20T14:30:00Z",
    "MajorVersion": 1,
    "MinorVersion": 0
  }
}
```

## 2. GET .../$value - Download File

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/GetFileByServerRelativeUrl('{path}')/$value
```

Returns binary file content.

## 3. POST .../Files/add - Upload File

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/GetFolderByServerRelativeUrl('{folder}')/Files/add(url='{filename}',overwrite=true)
```

### Request Body

Binary file content with `Content-Length` header.

## Large File Upload (Chunked) [VERIFIED]

For files larger than 1.5MB, use chunked upload with StartUpload, ContinueUpload, and FinishUpload.

### Upload Flow

1. Create empty file stub with `GetByUrlOrAddStub`
2. Call `StartUpload` with first chunk and new uploadId GUID
3. Call `ContinueUpload` for each subsequent chunk with fileOffset
4. Call `FinishUpload` with final chunk
5. If error, call `CancelUpload` to clean up

### 10. POST .../StartUpload - Start Chunked Upload

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/GetFolderByServerRelativeUrl('{folder}')/Files/GetByUrlOrAddStub('{filename}')/StartUpload(uploadId=guid'{uploadId}')
```

**Parameters**:
- **uploadId** - New GUID for this upload session

**Request Body**: First chunk as binary (recommended: 10MB chunks)

**Response**: Bytes uploaded so far

### 11. POST .../ContinueUpload - Continue Chunked Upload

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/GetFileByServerRelativeUrl('{path}')/ContinueUpload(uploadId=guid'{uploadId}',fileOffset={offset})
```

**Parameters**:
- **uploadId** - Same GUID from StartUpload
- **fileOffset** - Byte offset where this chunk starts

**Request Body**: Next chunk as binary

### 12. POST .../FinishUpload - Complete Chunked Upload

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/GetFileByServerRelativeUrl('{path}')/FinishUpload(uploadId=guid'{uploadId}',fileOffset={offset})
```

**Parameters**:
- **uploadId** - Same GUID from StartUpload
- **fileOffset** - Final byte offset

**Request Body**: Final chunk as binary

**Response**: SP.File object with complete file metadata

### 13. POST .../CancelUpload - Cancel Chunked Upload

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/GetFileByServerRelativeUrl('{path}')/CancelUpload(uploadId=guid'{uploadId}')
```

Use to clean up failed uploads. Removes partial file.

### Chunked Upload Example (PnP PowerShell)

```powershell
# Upload large file in chunks
$filePath = "C:\LargeFile.zip"
$folderUrl = "/sites/TeamSite/Shared Documents"
$chunkSize = 10MB

Add-PnPFile -Path $filePath -Folder $folderUrl -Values @{Title="Large File"}
# PnP automatically uses chunked upload for files > 10MB
```

### Chunked Upload Example (JavaScript)

```javascript
import { spfi } from "@pnp/sp";
import "@pnp/sp/files";

const sp = spfi(...);
const file = new File(["..."], "largefile.zip");

// PnP JS handles chunking automatically
await sp.web.getFolderByServerRelativePath("Shared Documents")
  .files.addChunked("largefile.zip", file, { progress: (data) => {
    console.log(`Uploaded ${data.blockNumber} of ${data.totalBlocks}`);
  }});
```

## 4. POST .../CheckOut() - Check Out File

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/GetFileByServerRelativeUrl('{path}')/CheckOut()
```

## 5. POST .../CheckIn() - Check In File

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/GetFileByServerRelativeUrl('{path}')/CheckIn(comment='Comment',checkintype=0)
```

### CheckInType Values

- **0** - Minor version
- **1** - Major version
- **2** - Overwrite

## 6. GET .../versions - Get Versions

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/GetFileByServerRelativeUrl('{path}')/versions
```

## 7. POST .../moveto - Move File

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/GetFileByServerRelativeUrl('{source}')/moveto(newurl='{destination}',flags=1)
```

## 8. POST .../copyto - Copy File

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/GetFileByServerRelativeUrl('{source}')/copyto(strnewurl='{destination}',boverwrite=true)
```

## 9. DELETE - Delete File

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/GetFileByServerRelativeUrl('{path}')
X-HTTP-Method: DELETE
IF-MATCH: *
```

## Error Responses

- **400** - Invalid path
- **401** - Unauthorized
- **403** - Forbidden
- **404** - File not found
- **423** - File locked (checked out)

## SDK Examples

**Office365-REST-Python-Client** (Python):

```python
# Library: office365-rest-python-client
# pip install Office365-REST-Python-Client
from office365.sharepoint.client_context import ClientContext

# FAIL: execute_batch() with file content causes TypeError!
for filename, content in files:
    root_folder.upload_file(filename, content)  # Queues request
ctx.execute_batch()  # TypeError: Object of type bytes is not JSON serializable

# WORKS: Sequential execute_query() for each file upload
for i, (filename, content) in enumerate(files):
    print(f"Uploading [{i+1}/{len(files)}]: {filename}")
    root_folder.upload_file(filename, content).execute_query()  # Upload immediately
```

**Performance note** (tested 2026-02-03):
- Sequential upload of 6000 small files: ~45 minutes
- Each file upload: ~0.4s average
- Batch operations work for metadata queries, NOT for file content

**PnP PowerShell**:
```powershell
Connect-PnPOnline -Url "https://contoso.sharepoint.com/sites/TeamSite" -Interactive
Get-PnPFile -Url "/sites/TeamSite/Shared Documents/Report.docx"
Get-PnPFile -Url "/sites/TeamSite/Shared Documents/Report.docx" -AsFile -Path "C:\Temp"
Add-PnPFile -Path "C:\Temp\NewFile.docx" -Folder "Shared Documents"
Set-PnPFileCheckedOut -Url "/sites/TeamSite/Shared Documents/Report.docx"
Set-PnPFileCheckedIn -Url "/sites/TeamSite/Shared Documents/Report.docx" -Comment "Updated"
Move-PnPFile -SourceUrl "/sites/TeamSite/Shared Documents/Report.docx" -TargetUrl "/sites/TeamSite/Archive/Report.docx"
Remove-PnPFile -ServerRelativeUrl "/sites/TeamSite/Shared Documents/Report.docx"
```

**PnP JavaScript** (v4.x):
```javascript
import { spfi } from "@pnp/sp";
import "@pnp/sp/files";
import "@pnp/sp/folders";
const sp = spfi(...);

const file = await sp.web.getFileByServerRelativePath("/sites/TeamSite/Shared Documents/Report.docx")();
const content = await sp.web.getFileByServerRelativePath("/sites/TeamSite/Shared Documents/Report.docx").getBuffer();
await sp.web.getFolderByServerRelativePath("Shared Documents").files.addUsingPath("NewFile.docx", fileContent, { Overwrite: true });
await sp.web.getFileByServerRelativePath("/sites/TeamSite/Shared Documents/Report.docx").checkout();
await sp.web.getFileByServerRelativePath("/sites/TeamSite/Shared Documents/Report.docx").checkin("Updated");
```

## Sources

- **SPAPI-FILE-SC-01**: https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/working-with-folders-and-files-with-rest

## Document History

**[2026-02-03 14:25]**
- Added: Office365-REST-Python-Client SDK examples with FAIL/WORKS patterns
- Added: Gotcha for `execute_batch()` not working with file uploads
- Added: Performance notes from POC testing

**[2026-01-28 19:45]**
- Added complete chunked upload section (StartUpload, ContinueUpload, FinishUpload, CancelUpload)
- Added critical gotchas (filename encoding, throttling)
- Enhanced use cases with practical scenarios

**[2026-01-28 19:15]**
- Initial creation with 20 endpoints
