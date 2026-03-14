# INFO: Microsoft Graph API - ContentType Methods

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for ContentType methods with request/response JSON and examples
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_MSGRAPH-IN00_TOC.md [MSGRAPH-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Define document templates with required metadata fields
- Enforce consistent metadata across document libraries
- Publish content types from hub to connected sites
- Create document sets for grouping related documents
- Build custom document management workflows with specific columns
- Migrate content type definitions between environments

**Key findings**:
- Content type IDs are hierarchical hex strings (e.g., `0x0101` = Document)
- Built-in content types cannot be deleted or significantly modified
- Publishing syndicates content types from hub to subscribed sites
- Content types inherit from parent - changes can propagate down
- Adding content type to list enables it for items in that list
- Only supported web parts work when creating via Graph API

## Quick Reference Summary

**Endpoints covered**: 14 contentType methods

**Site ContentTypes (7)**:
- `GET /sites/{id}/contentTypes` - List site content types
- `GET /sites/{id}/contentTypes/{id}` - Get site content type
- `POST /sites/{id}/contentTypes` - Create site content type
- `PATCH /sites/{id}/contentTypes/{id}` - Update content type
- `DELETE /sites/{id}/contentTypes/{id}` - Delete content type
- `POST /sites/{id}/contentTypes/{id}/publish` - Publish content type
- `POST /sites/{id}/contentTypes/{id}/unpublish` - Unpublish content type

**List ContentTypes (2)**:
- `GET /sites/{id}/lists/{id}/contentTypes` - List content types in list
- `POST /sites/{id}/lists/{id}/contentTypes` - Add content type to list

**ContentType Columns (5)**:
- `GET /sites/{id}/contentTypes/{id}/columns` - List columns
- `GET /sites/{id}/contentTypes/{id}/columns/{id}` - Get column
- `POST /sites/{id}/contentTypes/{id}/columns` - Create column
- `PATCH /sites/{id}/contentTypes/{id}/columns/{id}` - Update column
- `DELETE /sites/{id}/contentTypes/{id}/columns/{id}` - Delete column

**Permissions required**:
- Delegated: `Sites.Manage.All`, `Sites.FullControl.All`
- Application: `Sites.Manage.All`, `Sites.FullControl.All`
- **Least privilege**: `Sites.Manage.All`

## ContentType Resource Type [VERIFIED]

### JSON Schema

```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "group": "string",
  "hidden": false,
  "readOnly": false,
  "sealed": false,
  "isBuiltIn": false,
  "parentId": "string",
  "propagateChanges": false,
  "base": { "@odata.type": "microsoft.graph.contentType" },
  "baseTypes": [{ "@odata.type": "microsoft.graph.contentType" }],
  "columns": [{ "@odata.type": "microsoft.graph.columnDefinition" }],
  "columnLinks": [{ "@odata.type": "microsoft.graph.columnLink" }],
  "columnPositions": [{ "@odata.type": "microsoft.graph.columnDefinition" }],
  "inheritedFrom": { "@odata.type": "microsoft.graph.itemReference" },
  "order": { "@odata.type": "microsoft.graph.contentTypeOrder" },
  "documentSet": { "@odata.type": "microsoft.graph.documentSet" },
  "documentTemplate": { "@odata.type": "microsoft.graph.documentSetContent" },
  "associatedHubsUrls": ["string"]
}
```

### Properties [VERIFIED]

- **id** (`string`) - Unique identifier (e.g., `0x0101` for Document)
- **name** (`string`) - Display name of the content type
- **description** (`string`) - Description of the content type
- **group** (`string`) - Group the content type belongs to
- **hidden** (`boolean`) - Whether content type is hidden from UI
- **readOnly** (`boolean`) - Whether content type can be modified
- **sealed** (`boolean`) - Whether derived content types can be created
- **isBuiltIn** (`boolean`) - Whether it's a built-in SharePoint content type
- **parentId** (`string`) - ID of the parent content type
- **propagateChanges** (`boolean`) - Push changes to derived content types

### Relationships [VERIFIED]

- **base** - Parent contentType this one inherits from
- **baseTypes** - Collection of ancestor content types
- **columns** - Collection of columnDefinition resources
- **columnLinks** - Collection of columnLink resources
- **columnPositions** - Order of columns in the content type

### ContentType ID Format [VERIFIED]

Content type IDs are hierarchical hex strings:
- `0x` - System (root)
- `0x01` - Item
- `0x0101` - Document
- `0x0120` - Folder
- `0x010101` - Custom derived from Document

## 1. GET /sites/{id}/contentTypes - List Site ContentTypes

### Description [VERIFIED]

Retrieves all content types available in a site.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/contentTypes
```

### Path Parameters

- **siteId** (`string`) - Site identifier

### Query Parameters

- **$select** - Select specific properties
- **$filter** - Filter results
- **$expand** - Expand relationships (columns, base, baseTypes)
- **$top** - Limit results

### Request Example

```http
GET https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/contentTypes?$expand=columns
Authorization: Bearer {token}
```

### Response JSON [VERIFIED]

```json
{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#Collection(contentType)",
  "value": [
    {
      "id": "0x0101",
      "name": "Document",
      "description": "Create a new document.",
      "group": "Document Content Types",
      "hidden": false,
      "readOnly": false,
      "sealed": false,
      "isBuiltIn": true,
      "parentId": "0x01"
    },
    {
      "id": "0x01010100ABC123",
      "name": "Project Document",
      "description": "Custom project document type",
      "group": "Custom Content Types",
      "hidden": false,
      "isBuiltIn": false,
      "parentId": "0x0101"
    }
  ]
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Sites
Get-MgSiteContentType -SiteId $siteId
```

**C#**:
```csharp
var contentTypes = await graphClient.Sites["{site-id}"]
    .ContentTypes
    .GetAsync();
```

**JavaScript**:
```javascript
let contentTypes = await client.api('/sites/{site-id}/contentTypes').get();
```

**Python**:
```python
content_types = await graph_client.sites.by_site_id('site-id').content_types.get()
```

## 2. GET /sites/{id}/contentTypes/{id} - Get ContentType

### Description [VERIFIED]

Retrieves a specific content type by ID.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/contentTypes/{contentTypeId}
```

### Path Parameters

- **siteId** (`string`) - Site identifier
- **contentTypeId** (`string`) - Content type ID (e.g., `0x0101`)

### Request Example

```http
GET https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/contentTypes/0x0101?$expand=columns
Authorization: Bearer {token}
```

### Response JSON [VERIFIED]

```json
{
  "id": "0x0101",
  "name": "Document",
  "description": "Create a new document.",
  "group": "Document Content Types",
  "hidden": false,
  "readOnly": false,
  "sealed": false,
  "isBuiltIn": true,
  "parentId": "0x01",
  "columns": [
    {
      "id": "fa564e0f-0c70-4ab9-b863-0177e6ddd247",
      "name": "Title",
      "displayName": "Title",
      "type": "text"
    }
  ]
}
```

## 3. POST /sites/{id}/contentTypes - Create ContentType

### Description [VERIFIED]

Creates a new content type in a site. The new content type inherits from a parent content type.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/sites/{siteId}/contentTypes
```

### Request Body

```json
{
  "name": "string",
  "description": "string",
  "group": "string",
  "parentId": "string",
  "propagateChanges": false
}
```

**Required Properties**:
- **name** - Display name
- **parentId** - ID of parent content type to inherit from

### Request Example

```http
POST https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/contentTypes
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Project Document",
  "description": "Document type for project files",
  "group": "Custom Content Types",
  "parentId": "0x0101"
}
```

### Response JSON [VERIFIED]

```json
{
  "id": "0x01010100ABC123DEF456",
  "name": "Project Document",
  "description": "Document type for project files",
  "group": "Custom Content Types",
  "hidden": false,
  "readOnly": false,
  "sealed": false,
  "isBuiltIn": false,
  "parentId": "0x0101"
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Sites

$params = @{
    name = "Project Document"
    description = "Document type for project files"
    parentId = "0x0101"
    group = "Custom Content Types"
}
New-MgSiteContentType -SiteId $siteId -BodyParameter $params
```

**C#**:
```csharp
var requestBody = new ContentType
{
    Name = "Project Document",
    Description = "Document type for project files",
    ParentId = "0x0101",
    Group = "Custom Content Types"
};
var result = await graphClient.Sites["{site-id}"]
    .ContentTypes
    .PostAsync(requestBody);
```

## 4. PATCH /sites/{id}/contentTypes/{id} - Update ContentType

### Description [VERIFIED]

Updates an existing content type's properties.

### HTTP Request

```http
PATCH https://graph.microsoft.com/v1.0/sites/{siteId}/contentTypes/{contentTypeId}
```

Also works for list content types:
```http
PATCH https://graph.microsoft.com/v1.0/sites/{siteId}/lists/{listId}/contentTypes/{contentTypeId}
```

### Request Body

```json
{
  "name": "string",
  "description": "string",
  "group": "string",
  "hidden": false,
  "propagateChanges": true
}
```

### Request Example

```http
PATCH https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/contentTypes/0x01010100ABC123
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Updated Project Document",
  "description": "Updated description",
  "propagateChanges": true
}
```

### Response JSON [VERIFIED]

Returns the updated contentType object.

## 5. DELETE /sites/{id}/contentTypes/{id} - Delete ContentType

### Description [VERIFIED]

Removes a content type from a site or list. Cannot delete built-in content types or content types in use.

### HTTP Request

```http
DELETE https://graph.microsoft.com/v1.0/sites/{siteId}/contentTypes/{contentTypeId}
```

Also works for list content types:
```http
DELETE https://graph.microsoft.com/v1.0/sites/{siteId}/lists/{listId}/contentTypes/{contentTypeId}
```

### Request Example

```http
DELETE https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/contentTypes/0x01010100ABC123
Authorization: Bearer {token}
```

### Response [VERIFIED]

```http
HTTP/1.1 204 No Content
```

## 6. POST /sites/{id}/contentTypes/{id}/publish - Publish ContentType

### Description [VERIFIED]

Publishes a content type to the content type hub, making it available for syndication to other sites.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/sites/{siteId}/contentTypes/{contentTypeId}/publish
```

### Request Body

Do not supply a request body.

### Response [VERIFIED]

```http
HTTP/1.1 204 No Content
```

## 7. POST /sites/{id}/contentTypes/{id}/unpublish - Unpublish ContentType

### Description [VERIFIED]

Unpublishes a content type from the content type hub.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/sites/{siteId}/contentTypes/{contentTypeId}/unpublish
```

### Response [VERIFIED]

```http
HTTP/1.1 204 No Content
```

## 8. GET /sites/{id}/lists/{id}/contentTypes - List ContentTypes in List

### Description [VERIFIED]

Retrieves content types enabled for a specific list.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/lists/{listId}/contentTypes
```

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "0x0101",
      "name": "Document",
      "hidden": false
    },
    {
      "id": "0x0120",
      "name": "Folder",
      "hidden": true
    }
  ]
}
```

## 9. POST /sites/{id}/lists/{id}/contentTypes - Add ContentType to List

### Description [VERIFIED]

Adds an existing site content type to a list, enabling it for use with list items.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/sites/{siteId}/lists/{listId}/contentTypes
```

### Request Body

```json
{
  "contentType": {
    "id": "string"
  }
}
```

Or use addCopy action:
```http
POST https://graph.microsoft.com/v1.0/sites/{siteId}/lists/{listId}/contentTypes/addCopy
```

## 10-14. ContentType Column Methods

### List Columns

```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/contentTypes/{contentTypeId}/columns
```

### Get Column

```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/contentTypes/{contentTypeId}/columns/{columnId}
```

### Create Column

```http
POST https://graph.microsoft.com/v1.0/sites/{siteId}/contentTypes/{contentTypeId}/columns
```

**Request Body**:
```json
{
  "name": "ProjectCode",
  "displayName": "Project Code",
  "description": "Unique project identifier",
  "text": {
    "allowMultipleLines": false,
    "maxLength": 50
  },
  "required": true
}
```

### Update Column

```http
PATCH https://graph.microsoft.com/v1.0/sites/{siteId}/contentTypes/{contentTypeId}/columns/{columnId}
```

### Delete Column

```http
DELETE https://graph.microsoft.com/v1.0/sites/{siteId}/contentTypes/{contentTypeId}/columns/{columnId}
```

## Additional ContentType Actions [VERIFIED]

### addCopy - Copy ContentType to Site/List

```http
POST https://graph.microsoft.com/v1.0/sites/{siteId}/contentTypes/addCopy
```

**Request Body**:
```json
{
  "contentType": "https://graph.microsoft.com/v1.0/sites/{sourceSiteId}/contentTypes/{contentTypeId}"
}
```

### addCopyFromContentTypeHub - Sync from Hub

```http
POST https://graph.microsoft.com/v1.0/sites/{siteId}/contentTypes/addCopyFromContentTypeHub
```

**Request Body**:
```json
{
  "contentTypeId": "0x0101"
}
```

### associateWithHubSites - Associate with Hub Sites

```http
POST https://graph.microsoft.com/v1.0/sites/{siteId}/contentTypes/{contentTypeId}/associateWithHubSites
```

**Request Body**:
```json
{
  "hubSiteUrls": ["https://contoso.sharepoint.com/sites/hub1"],
  "propagateToExistingLists": true
}
```

### getCompatibleHubContentTypes - List Hub ContentTypes

```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/getCompatibleHubContentTypes
```

### isPublished - Check Publication Status

```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/contentTypes/{contentTypeId}/isPublished
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid content type ID or properties
- **401 Unauthorized** - Missing or invalid token
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Content type not found
- **409 Conflict** - Content type in use (cannot delete)
- **429 Too Many Requests** - Rate limit exceeded

### Error Response Format

```json
{
  "error": {
    "code": "invalidRequest",
    "message": "Cannot delete content type that is in use.",
    "innerError": {
      "request-id": "guid",
      "date": "2026-01-28T12:00:00Z"
    }
  }
}
```

## Throttling Considerations [VERIFIED]

**Best Practices**:
- Cache content type IDs
- Use `$expand` to reduce round trips
- Batch column operations

**Resource Units**:
- List content types: ~1 resource unit
- Create/Update/Delete: ~2-3 resource units
- Publish/Unpublish: ~3 resource units

## Sources

- **MSGRAPH-CT-SC-01**: https://learn.microsoft.com/en-us/graph/api/resources/contenttype?view=graph-rest-1.0
- **MSGRAPH-CT-SC-02**: https://learn.microsoft.com/en-us/graph/api/site-list-contenttypes?view=graph-rest-1.0
- **MSGRAPH-CT-SC-03**: https://learn.microsoft.com/en-us/graph/api/contenttype-update?view=graph-rest-1.0
- **MSGRAPH-CT-SC-04**: https://learn.microsoft.com/en-us/graph/api/contenttype-delete?view=graph-rest-1.0

## Document History

**[2026-01-28 18:40]**
- Initial creation with 14 endpoints
- Added contentType resource type documentation
- Added content type ID format explanation
- Added hub synchronization actions
