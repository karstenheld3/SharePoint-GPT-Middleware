# INFO: SharePoint REST API - Content Type

**Doc ID**: SPAPI-IN01
**Goal**: Detailed reference for ContentType (SP.ContentType) endpoints with request/response JSON and examples
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_SHAREPOINT_API_TOC.md [SPAPI-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Define and manage content types for lists and libraries
- Associate fields with content types
- Control document templates and metadata
- Inherit from parent content types

**Key findings**:
- Content types define metadata schema for items/documents [VERIFIED]
- Site content types are inherited by list content types [VERIFIED]
- Content type IDs follow hierarchical naming (0x0101 = Document) [VERIFIED]
- List must have ContentTypesEnabled=true to support multiple types [VERIFIED]

## Quick Reference Summary

**Endpoints covered**: 6 content type endpoints

- `GET /_api/web/contenttypes` - Get site content types
- `GET /_api/web/contenttypes('{id}')` - Get content type by ID
- `GET /_api/web/availablecontenttypes` - Get available content types
- `POST /_api/web/contenttypes` - Create content type
- `PATCH /_api/web/contenttypes('{id}')` - Update content type
- `DELETE /_api/web/contenttypes('{id}')` - Delete content type

**Permissions required**:
- Application: `Sites.Read.All` (read), `Sites.Manage.All` (manage)
- Delegated: `Sites.Read.All` (read), `Sites.Manage.All` (manage)

## Content Type ID Format [VERIFIED]

Content type IDs are hierarchical hex strings:
- **0x** - System base
- **0x01** - Item
- **0x0101** - Document
- **0x0102** - Event
- **0x0103** - Issue
- **0x0104** - Announcement
- **0x0105** - Link
- **0x0106** - Contact
- **0x0107** - Message
- **0x0108** - Task
- **0x0120** - Folder

Custom content types append to parent ID (e.g., `0x010100...`).

## SP.ContentType Resource Type

### Properties [VERIFIED]

- **Id** (`SP.ContentTypeId`) - Content type ID (has StringValue)
- **Name** (`Edm.String`) - Display name
- **Description** (`Edm.String`) - Description
- **Group** (`Edm.String`) - Content type group
- **Hidden** (`Edm.Boolean`) - Hidden from UI
- **ReadOnly** (`Edm.Boolean`) - Read-only
- **Sealed** (`Edm.Boolean`) - Cannot be modified
- **DocumentTemplate** (`Edm.String`) - Template URL for documents
- **SchemaXml** (`Edm.String`) - XML schema definition

## 1. GET /_api/web/contenttypes - Get Site Content Types

### Description [VERIFIED]

Returns all content types defined at the site level.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/contenttypes
```

### Query Parameters

- **$filter** - Filter content types (e.g., `Group eq 'Custom'`)
- **$select** - Properties to return

### Response JSON [VERIFIED]

```json
{
  "d": {
    "results": [
      {
        "__metadata": { "type": "SP.ContentType" },
        "Id": {
          "__metadata": { "type": "SP.ContentTypeId" },
          "StringValue": "0x0101"
        },
        "Name": "Document",
        "Description": "Create a new document.",
        "Group": "Document Content Types",
        "Hidden": false,
        "ReadOnly": false,
        "Sealed": false
      },
      {
        "__metadata": { "type": "SP.ContentType" },
        "Id": {
          "StringValue": "0x0120"
        },
        "Name": "Folder",
        "Description": "Create a new folder.",
        "Group": "Folder Content Types"
      }
    ]
  }
}
```

## 2. GET /_api/web/contenttypes('{id}') - Get Content Type by ID

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/contenttypes('{content_type_id}')
```

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/web/contenttypes('0x0101')
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

## 3. GET /_api/web/availablecontenttypes - Get Available Content Types

### Description [VERIFIED]

Returns all content types available to the site, including inherited types.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/availablecontenttypes
```

## 4. POST /_api/web/contenttypes - Create Content Type

### Description [VERIFIED]

Creates a new site content type.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/contenttypes
```

### Request Body

```json
{
  "__metadata": {
    "type": "SP.ContentType"
  },
  "Name": "Custom Document",
  "Description": "A custom document type",
  "Group": "Custom Content Types",
  "ParentContentType": {
    "__metadata": { "type": "SP.ContentType" },
    "Id": {
      "__metadata": { "type": "SP.ContentTypeId" },
      "StringValue": "0x0101"
    }
  }
}
```

### Alternative: Using ContentTypeCreationInformation

```http
POST /_api/web/contenttypes/addavailablecontenttypeid(contentTypeId='{parent_id}')
```

## 5. PATCH /_api/web/contenttypes('{id}') - Update Content Type

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/contenttypes('{content_type_id}')
X-HTTP-Method: MERGE
IF-MATCH: *
```

### Request Body

```json
{
  "__metadata": { "type": "SP.ContentType" },
  "Name": "Updated Name",
  "Description": "Updated description"
}
```

## 6. DELETE /_api/web/contenttypes('{id}') - Delete Content Type

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/contenttypes('{content_type_id}')
X-HTTP-Method: DELETE
IF-MATCH: *
```

**Note**: Cannot delete content types that are in use or sealed.

## List Content Types

### Get List Content Types

```http
GET /_api/web/lists/getbytitle('{list}')/contenttypes
```

### Add Content Type to List

```http
POST /_api/web/lists/getbytitle('{list}')/contenttypes/addavailablecontenttypeid(contentTypeId='{id}')
```

### Remove Content Type from List

```http
POST /_api/web/lists/getbytitle('{list}')/contenttypes('{id}')
X-HTTP-Method: DELETE
```

## Content Type Fields

### Get Content Type Fields

```http
GET /_api/web/contenttypes('{id}')/fields
```

### Add Field to Content Type

```http
POST /_api/web/contenttypes('{id}')/fieldlinks
```

### Request Body

```json
{
  "__metadata": { "type": "SP.FieldLink" },
  "FieldInternalName": "MyField"
}
```

## Error Responses

- **400** - Invalid content type ID format
- **403** - Insufficient permissions
- **404** - Content type not found
- **409** - Content type already exists or in use

## SDK Examples

**PnP PowerShell**:
```powershell
Connect-PnPOnline -Url "https://contoso.sharepoint.com/sites/TeamSite" -Interactive
Get-PnPContentType
Get-PnPContentType -Identity "Document"
Add-PnPContentType -Name "Custom Document" -Group "Custom" -ParentContentType "Document"
Add-PnPContentTypeToList -List "Documents" -ContentType "Custom Document"
```

**PnP JavaScript** (v4.x):
```javascript
import { spfi } from "@pnp/sp";
import "@pnp/sp/content-types";
const sp = spfi(...);
const cts = await sp.web.contentTypes();
const ct = await sp.web.contentTypes.getById("0x0101")();
```

## Sources

- **SPAPI-CT-SC-01**: https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/complete-basic-operations-using-sharepoint-rest-endpoints

## Document History

**[2026-01-28 19:35]**
- Initial creation with 6 endpoints
- Documented content type CRUD and field associations
