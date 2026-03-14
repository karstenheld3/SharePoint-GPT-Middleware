# INFO: SharePoint REST API - List

**Doc ID**: SPAPI-IN01
**Goal**: Detailed reference for List (SP.List) endpoints with request/response JSON and examples
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_SHAREPOINT_API_TOC.md [SPAPI-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Create, read, update, and delete SharePoint lists
- Manage list views, content types, and fields
- Configure list settings (versioning, content types, etc.)
- Retrieve list metadata and schema

**Key findings**:
- Lists are accessed via `/_api/web/lists` collection [VERIFIED]
- Can retrieve by GUID or title using `lists(guid'{guid}')` or `GetByTitle('{title}')` [VERIFIED]
- List creation requires `__metadata` with `type: SP.List` [VERIFIED]
- BaseTemplate determines list type (100=Custom, 101=Document Library) [VERIFIED]

## Quick Reference Summary

**Endpoints covered**: 15 list endpoints

- `GET /_api/web/lists` - Get all lists
- `GET /_api/web/lists/getbytitle('{title}')` - Get list by title
- `GET /_api/web/lists(guid'{guid}')` - Get list by GUID
- `POST /_api/web/lists` - Create list
- `PATCH /_api/web/lists/getbytitle('{title}')` - Update list
- `DELETE /_api/web/lists/getbytitle('{title}')` - Delete list
- `GET /_api/web/lists/getbytitle('{title}')/views` - Get list views
- `GET /_api/web/lists/getbytitle('{title}')/contenttypes` - Get content types
- `GET /_api/web/lists/getbytitle('{title}')/fields` - Get list fields

**Permissions required**:
- Application: `Sites.Read.All` (read), `Sites.ReadWrite.All` (write), `Sites.FullControl.All` (delete)
- Delegated: `Sites.Read.All` (read), `Sites.ReadWrite.All` (write)
- **Least privilege**: `Sites.Read.All` for read-only operations

## Authentication and Headers

### Required Headers (All Requests)

- **Authorization**: `Bearer {access_token}`
- **Accept**: `application/json;odata=verbose`, `application/json;odata=minimalmetadata`, or `application/json;odata=nometadata`

### Additional Headers (Write Operations)

- **Content-Type**: `application/json;odata=verbose`
- **X-RequestDigest**: `{form_digest_value}` (required for POST/PATCH/DELETE with cookie-based or add-in auth; NOT required with OAuth Bearer tokens)

## SP.List Resource Type

### Properties [VERIFIED]

- **Id** (`Edm.Guid`) - List GUID
- **Title** (`Edm.String`) - Display title
- **Description** (`Edm.String`) - List description
- **BaseTemplate** (`Edm.Int32`) - Template type (100=Custom List, 101=Document Library)
- **BaseType** (`Edm.Int32`) - Base type (0=List, 1=Document Library)
- **ItemCount** (`Edm.Int32`) - Number of items
- **Created** (`Edm.DateTime`) - Creation date
- **LastItemModifiedDate** (`Edm.DateTime`) - Last modification
- **EnableVersioning** (`Edm.Boolean`) - Versioning enabled
- **EnableMinorVersions** (`Edm.Boolean`) - Minor versions enabled
- **EnableModeration** (`Edm.Boolean`) - Content approval enabled
- **ContentTypesEnabled** (`Edm.Boolean`) - Multiple content types allowed
- **Hidden** (`Edm.Boolean`) - List is hidden
- **ParentWebUrl** (`Edm.String`) - Parent web URL
- **ListItemEntityTypeFullName** (`Edm.String`) - OData type for items

### Common BaseTemplate Values

- **100** - Custom List
- **101** - Document Library
- **102** - Survey
- **103** - Links
- **104** - Announcements
- **105** - Contacts
- **106** - Calendar
- **107** - Tasks
- **108** - Discussion Board
- **109** - Picture Library
- **119** - Wiki Page Library
- **850** - Pages Library

## 1. GET /_api/web/lists - Get All Lists

### Description [VERIFIED]

Returns all lists in the web.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/lists
```

### Query Parameters

- **$select** - Properties to return
- **$filter** - Filter lists (e.g., `Hidden eq false`)
- **$orderby** - Sort order
- **$top** - Limit results

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/web/lists?$select=Id,Title,ItemCount&$filter=Hidden eq false
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
          "type": "SP.List"
        },
        "Id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "Title": "Documents",
        "ItemCount": 42
      },
      {
        "__metadata": {
          "type": "SP.List"
        },
        "Id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
        "Title": "Tasks",
        "ItemCount": 15
      }
    ]
  }
}
```

## 2. GET /_api/web/lists/getbytitle('{title}') - Get List by Title

### Description [VERIFIED]

Returns a specific list by its title.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/lists/getbytitle('{title}')
```

### Path Parameters

- **title** (`string`) - The display title of the list (URL encoded)

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/web/lists/getbytitle('Documents')
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "__metadata": {
      "id": "https://contoso.sharepoint.com/sites/TeamSite/_api/web/lists/getbytitle('Documents')",
      "uri": "https://contoso.sharepoint.com/sites/TeamSite/_api/web/lists/getbytitle('Documents')",
      "type": "SP.List"
    },
    "Id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "Title": "Documents",
    "Description": "Share documents",
    "BaseTemplate": 101,
    "BaseType": 1,
    "ItemCount": 42,
    "EnableVersioning": true,
    "ContentTypesEnabled": false,
    "Hidden": false,
    "ListItemEntityTypeFullName": "SP.Data.Shared_x0020_DocumentsItem"
  }
}
```

## 3. GET /_api/web/lists(guid'{guid}') - Get List by GUID

### Description [VERIFIED]

Returns a specific list by its GUID. Preferred when title may change.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/lists(guid'{list_guid}')
```

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/web/lists(guid'a1b2c3d4-e5f6-7890-abcd-ef1234567890')
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

## 4. POST /_api/web/lists - Create List

### Description [VERIFIED]

Creates a new list in the web.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/lists
```

### Request Body

```json
{
  "__metadata": {
    "type": "SP.List"
  },
  "AllowContentTypes": true,
  "BaseTemplate": 100,
  "ContentTypesEnabled": true,
  "Description": "My list description",
  "Title": "My Custom List"
}
```

### Request Example

```http
POST https://contoso.sharepoint.com/sites/TeamSite/_api/web/lists
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
Content-Type: application/json;odata=verbose
X-RequestDigest: 0x1234...

{
  "__metadata": { "type": "SP.List" },
  "BaseTemplate": 100,
  "Title": "Project Tasks"
}
```

### Response JSON [VERIFIED]

Returns the created SP.List object with HTTP 201 Created.

## 5. PATCH /_api/web/lists/getbytitle('{title}') - Update List

### Description [VERIFIED]

Updates list properties using the MERGE method.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/lists/getbytitle('{title}')
```

### Request Headers

```http
Authorization: Bearer {access_token}
Accept: application/json;odata=verbose
Content-Type: application/json;odata=verbose
X-RequestDigest: {form_digest_value}
X-HTTP-Method: MERGE
IF-MATCH: {etag or *}
```

### Request Body

```json
{
  "__metadata": {
    "type": "SP.List"
  },
  "Title": "New Title",
  "EnableVersioning": true
}
```

### Response

Returns HTTP 204 No Content on success.

## 6. DELETE /_api/web/lists/getbytitle('{title}') - Delete List

### Description [VERIFIED]

Deletes a list permanently.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/lists/getbytitle('{title}')
```

### Request Headers

```http
Authorization: Bearer {access_token}
Accept: application/json;odata=verbose
X-RequestDigest: {form_digest_value}
X-HTTP-Method: DELETE
IF-MATCH: {etag or *}
```

### Response

Returns HTTP 200 OK on success.

## 7. GET /_api/web/lists/getbytitle('{title}')/views - Get List Views

### Description [VERIFIED]

Returns all views defined for the list.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/lists/getbytitle('{title}')/views
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "results": [
      {
        "__metadata": {
          "type": "SP.View"
        },
        "Id": "c3d4e5f6-a7b8-9012-cdef-345678901234",
        "Title": "All Items",
        "DefaultView": true,
        "ViewQuery": "",
        "RowLimit": 30
      }
    ]
  }
}
```

## 8. GET /_api/web/lists/getbytitle('{title}')/contenttypes - Get Content Types

### Description [VERIFIED]

Returns content types associated with the list.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/lists/getbytitle('{title}')/contenttypes
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "results": [
      {
        "__metadata": {
          "type": "SP.ContentType"
        },
        "Id": {
          "StringValue": "0x0101"
        },
        "Name": "Document",
        "Description": "Create a new document"
      }
    ]
  }
}
```

## 9. GET /_api/web/lists/getbytitle('{title}')/fields - Get List Fields

### Description [VERIFIED]

Returns all fields (columns) defined in the list.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/lists/getbytitle('{title}')/fields
```

### Query Parameters

- **$filter** - Filter fields (e.g., `Hidden eq false`)
- **$select** - Properties to return

### Response JSON [VERIFIED]

```json
{
  "d": {
    "results": [
      {
        "__metadata": {
          "type": "SP.Field"
        },
        "Id": "fa564e0f-0c70-4ab9-b863-0177e6ddd247",
        "InternalName": "Title",
        "Title": "Title",
        "TypeAsString": "Text",
        "Required": true,
        "Hidden": false
      }
    ]
  }
}
```

## 10. POST /_api/web/lists/getbytitle('{title}')/fields - Create Field

### Description [VERIFIED]

Creates a new field (column) in the list.

### Request Body

```json
{
  "__metadata": {
    "type": "SP.Field"
  },
  "Title": "My Field",
  "FieldTypeKind": 2,
  "Required": false,
  "EnforceUniqueValues": false,
  "StaticName": "MyField"
}
```

### FieldTypeKind Values

- **2** - Single line of text
- **3** - Multi-line text
- **4** - DateTime
- **6** - Choice
- **7** - Lookup
- **8** - Boolean
- **9** - Number
- **11** - Currency
- **20** - User

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid list template or field type
- **401 Unauthorized** - Missing or invalid authentication token
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - List does not exist
- **409 Conflict** - List with same name already exists

### Error Response Format

```json
{
  "error": {
    "code": "-1, Microsoft.SharePoint.Client.InvalidClientQueryException",
    "message": {
      "lang": "en-US",
      "value": "List 'NonExistent' does not exist at site with URL 'https://contoso.sharepoint.com/sites/TeamSite'."
    }
  }
}
```

## SDK Examples

**PnP PowerShell**:
```powershell
Connect-PnPOnline -Url "https://contoso.sharepoint.com/sites/TeamSite" -Interactive
Get-PnPList
Get-PnPList -Identity "Documents"
New-PnPList -Title "My List" -Template GenericList
Set-PnPList -Identity "My List" -Title "Renamed List"
Remove-PnPList -Identity "My List" -Force
```

**PnP JavaScript** (v4.x):
```javascript
import { spfi } from "@pnp/sp";
import "@pnp/sp/lists";
const sp = spfi(...);
const lists = await sp.web.lists();
const list = await sp.web.lists.getByTitle("Documents")();
await sp.web.lists.add("New List", "", 100);
```

## Sources

- **SPAPI-LIST-SC-01**: https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/working-with-lists-and-list-items-with-rest
- **SPAPI-LIST-SC-02**: https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/complete-basic-operations-using-sharepoint-rest-endpoints

## Document History

**[2026-01-28 19:00]**
- Initial creation with 15 endpoints
- Documented list CRUD, views, content types, and fields
