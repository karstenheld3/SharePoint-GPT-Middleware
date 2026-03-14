# INFO: SharePoint REST API - Folder

**Doc ID**: SPAPI-IN01
**Goal**: Detailed reference for Folder (SP.Folder) endpoints with request/response JSON and examples
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_SHAREPOINT_API_TOC.md [SPAPI-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Navigate folder hierarchies in document libraries
- Create, rename, and delete folders
- Move and copy folders between locations
- List folder contents (files and subfolders)

**Key findings**:
- Access folders via `GetFolderByServerRelativeUrl('{path}')` [VERIFIED]
- Folder rename requires updating `ListItemAllFields` properties [VERIFIED]
- Move/Copy operations use `moveto` and `copyto` methods [VERIFIED]
- Special characters (%, #) require ResourcePath API [VERIFIED]

## Quick Reference Summary

**Endpoints covered**: 8 folder endpoints

- `GET /_api/web/folders` - Get root folders
- `GET /_api/web/GetFolderByServerRelativeUrl('{path}')` - Get folder by path
- `GET /_api/web/GetFolderByServerRelativeUrl('{path}')/folders` - Get subfolders
- `GET /_api/web/GetFolderByServerRelativeUrl('{path}')/files` - Get files in folder
- `POST /_api/web/folders` - Create folder
- `POST /_api/web/GetFolderByServerRelativeUrl('{path}')` - Delete folder
- `POST /_api/web/GetFolderByServerRelativeUrl('{path}')/moveto` - Move folder
- `POST /_api/web/GetFolderByServerRelativeUrl('{path}')/copyto` - Copy folder

**Permissions required**:
- Application: `Sites.Read.All` (read), `Sites.ReadWrite.All` (write)
- Delegated: `Sites.Read.All` (read), `Sites.ReadWrite.All` (write)
- **Least privilege**: `Sites.Read.All` for read-only operations

## Authentication and Headers

### Required Headers (All Requests)

- **Authorization**: `Bearer {access_token}`
- **Accept**: `application/json;odata=verbose`, `application/json;odata=minimalmetadata`, or `application/json;odata=nometadata`

### Additional Headers (Write Operations)

- **Content-Type**: `application/json;odata=verbose`
- **X-RequestDigest**: `{form_digest_value}` (required for POST with cookie-based or add-in auth; NOT required with OAuth Bearer tokens)

## SP.Folder Resource Type

### Properties [VERIFIED]

- **Name** (`Edm.String`) - Folder name
- **ServerRelativeUrl** (`Edm.String`) - Server-relative URL path
- **ItemCount** (`Edm.Int32`) - Number of items in folder
- **TimeCreated** (`Edm.DateTime`) - Creation timestamp
- **TimeLastModified** (`Edm.DateTime`) - Last modification timestamp
- **UniqueId** (`Edm.Guid`) - Unique identifier
- **WelcomePage** (`Edm.String`) - Default page (if set)
- **Exists** (`Edm.Boolean`) - Whether folder exists

## 1. GET /_api/web/folders - Get Root Folders

### Description [VERIFIED]

Returns all root-level folders in the web.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/folders
```

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/web/folders
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "results": [
      {
        "__metadata": {
          "type": "SP.Folder"
        },
        "Name": "Shared Documents",
        "ServerRelativeUrl": "/sites/TeamSite/Shared Documents",
        "ItemCount": 15
      },
      {
        "__metadata": {
          "type": "SP.Folder"
        },
        "Name": "SiteAssets",
        "ServerRelativeUrl": "/sites/TeamSite/SiteAssets",
        "ItemCount": 3
      }
    ]
  }
}
```

## 2. GET /_api/web/GetFolderByServerRelativeUrl('{path}') - Get Folder

### Description [VERIFIED]

Returns a folder by its server-relative URL path.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/GetFolderByServerRelativeUrl('{server_relative_path}')
```

### Path Parameters

- **server_relative_path** (`string`) - Server-relative URL of folder (URL encoded)

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/web/GetFolderByServerRelativeUrl('/sites/TeamSite/Shared Documents/Projects')
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "__metadata": {
      "type": "SP.Folder"
    },
    "Name": "Projects",
    "ServerRelativeUrl": "/sites/TeamSite/Shared Documents/Projects",
    "ItemCount": 8,
    "TimeCreated": "2024-01-15T10:30:00Z",
    "TimeLastModified": "2024-01-20T14:30:00Z",
    "UniqueId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "Exists": true
  }
}
```

## 3. GET /.../GetFolderByServerRelativeUrl('{path}')/folders - Get Subfolders

### Description [VERIFIED]

Returns all subfolders within a folder.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/GetFolderByServerRelativeUrl('{path}')/folders
```

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/web/GetFolderByServerRelativeUrl('/sites/TeamSite/Shared Documents')/folders
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "results": [
      {
        "__metadata": {
          "type": "SP.Folder"
        },
        "Name": "Projects",
        "ServerRelativeUrl": "/sites/TeamSite/Shared Documents/Projects",
        "ItemCount": 8
      },
      {
        "__metadata": {
          "type": "SP.Folder"
        },
        "Name": "Archive",
        "ServerRelativeUrl": "/sites/TeamSite/Shared Documents/Archive",
        "ItemCount": 24
      }
    ]
  }
}
```

## 4. GET /.../GetFolderByServerRelativeUrl('{path}')/files - Get Files in Folder

### Description [VERIFIED]

Returns all files within a folder.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/GetFolderByServerRelativeUrl('{path}')/files
```

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/web/GetFolderByServerRelativeUrl('/sites/TeamSite/Shared Documents')/files
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "results": [
      {
        "__metadata": {
          "type": "SP.File"
        },
        "Name": "Report.docx",
        "ServerRelativeUrl": "/sites/TeamSite/Shared Documents/Report.docx",
        "Length": "25600",
        "TimeCreated": "2024-01-15T10:30:00Z",
        "TimeLastModified": "2024-01-20T14:30:00Z"
      }
    ]
  }
}
```

## 5. POST /_api/web/folders - Create Folder

### Description [VERIFIED]

Creates a new folder.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/folders
```

### Request Body

```json
{
  "__metadata": {
    "type": "SP.Folder"
  },
  "ServerRelativeUrl": "/sites/TeamSite/Shared Documents/New Folder"
}
```

### Request Example

```http
POST https://contoso.sharepoint.com/sites/TeamSite/_api/web/folders
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
Content-Type: application/json;odata=verbose
X-RequestDigest: 0x1234...

{
  "__metadata": { "type": "SP.Folder" },
  "ServerRelativeUrl": "/sites/TeamSite/Shared Documents/New Project"
}
```

### Response JSON [VERIFIED]

Returns the created folder with HTTP 201 Created.

## 6. Rename Folder (via ListItemAllFields)

### Description [VERIFIED]

Renames a folder by updating its ListItemAllFields. First get the odata.type, then MERGE.

### Step 1: Get odata.type

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/GetFolderByServerRelativeUrl('{path}')/ListItemAllFields
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

### Step 2: MERGE with new name

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/GetFolderByServerRelativeUrl('{path}')/ListItemAllFields
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
Content-Type: application/json;odata=verbose
X-RequestDigest: 0x1234...
X-HTTP-Method: MERGE
IF-MATCH: *

{
  "__metadata": { "type": "SP.Data.Shared_x0020_DocumentsItem" },
  "Title": "New Folder Name",
  "FileLeafRef": "New Folder Name"
}
```

## 7. POST /.../GetFolderByServerRelativeUrl('{path}') - Delete Folder

### Description [VERIFIED]

Deletes a folder. Folder goes to recycle bin.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/GetFolderByServerRelativeUrl('{path}')
```

### Request Headers

```http
Authorization: Bearer {access_token}
X-RequestDigest: {form_digest_value}
X-HTTP-Method: DELETE
IF-MATCH: *
```

### Request Example

```http
POST https://contoso.sharepoint.com/sites/TeamSite/_api/web/GetFolderByServerRelativeUrl('/sites/TeamSite/Shared Documents/Old Folder')
Authorization: Bearer eyJ0eXAi...
X-HTTP-Method: DELETE
IF-MATCH: *
```

## 8. POST /.../moveto(newurl='{path}') - Move Folder

### Description [VERIFIED]

Moves a folder to a new location.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/GetFolderByServerRelativeUrl('{source}')/moveto(newurl='{destination}')
```

### Request Example

```http
POST https://contoso.sharepoint.com/sites/TeamSite/_api/web/GetFolderByServerRelativeUrl('/sites/TeamSite/Shared Documents/Source')/moveto(newurl='/sites/TeamSite/Archive/Source')
Authorization: Bearer eyJ0eXAi...
X-RequestDigest: 0x1234...
```

## 9. POST /.../copyto(newurl='{path}') - Copy Folder

### Description [VERIFIED]

Copies a folder to a new location.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/GetFolderByServerRelativeUrl('{source}')/copyto(newurl='{destination}')
```

## Special Characters (% and #)

### Description [VERIFIED]

Folders with `%` or `#` in names require the ResourcePath API.

### Example

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/GetFolderByServerRelativePath(decodedurl='/sites/TeamSite/Shared Documents/Folder%23Name')
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid path format
- **401 Unauthorized** - Missing or invalid authentication token
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Folder does not exist

## SDK Examples

**PnP PowerShell**:
```powershell
Connect-PnPOnline -Url "https://contoso.sharepoint.com/sites/TeamSite" -Interactive
Get-PnPFolder -Url "Shared Documents/Projects"
Add-PnPFolder -Name "New Folder" -Folder "Shared Documents"
Remove-PnPFolder -Name "Old Folder" -Folder "Shared Documents" -Force
Move-PnPFolder -Folder "Shared Documents/Source" -TargetFolder "Archive"
```

**PnP JavaScript** (v4.x):
```javascript
import { spfi } from "@pnp/sp";
import "@pnp/sp/folders";
const sp = spfi(...);
const folder = await sp.web.getFolderByServerRelativePath("/sites/TeamSite/Shared Documents")();
await sp.web.folders.addUsingPath("Shared Documents/New Folder");
```

## Sources

- **SPAPI-FOLDER-SC-01**: https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/working-with-folders-and-files-with-rest

## Document History

**[2026-01-28 19:10]**
- Initial creation with 8 endpoints
- Documented folder CRUD, navigation, move/copy operations
