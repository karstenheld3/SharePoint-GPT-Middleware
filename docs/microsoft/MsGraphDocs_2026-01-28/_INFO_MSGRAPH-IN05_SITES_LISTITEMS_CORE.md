# INFO: Microsoft Graph API - ListItem Core Methods

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for SharePoint ListItem API core methods with request/response JSON and examples
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_MSGRAPH-IN00_TOC.md [MSGRAPH-IN01]` for endpoint inventory
- `_INFO_MSGRAPH_LISTS_CORE.md [MSGRAPH-IN01]` for list context

## Summary

**Use cases**:
- CRUD operations on SharePoint list data from custom applications
- Build data entry forms and dashboards backed by SharePoint lists
- Sync list data to external systems (ERP, CRM, databases)
- Implement bulk data import/export via batch operations
- Track item changes incrementally using delta queries for offline sync
- Update specific field values without replacing entire item
- Build approval workflows that modify item status fields

**Key findings**:
- Items returned without fields by default; always use `$expand=fields` to get column values
- Field names in API use internal column names, not display names - check via list columns
- Lookup fields require `LookupId` suffix when setting values (e.g., `CategoryLookupId`)
- Person fields are lookups - use user's lookup ID, not email or UPN
- Delta queries track creates, updates, and deletes; deleted items have `@removed` annotation; always deduplicate by item ID (replays possible)
- Filtering works best on indexed columns; non-indexed may timeout on large lists
- PATCH to `/fields` endpoint is more efficient than PATCH to item for field updates only
- Delete moves to recycle bin; no permanent delete via Graph API for list items

## Quick Reference Summary

**Endpoints covered**: 8 ListItem API methods

- `GET /sites/{id}/lists/{id}/items` - Get all items in a list
- `GET /sites/{id}/lists/{id}/items/{id}` - Get item by ID
- `POST /sites/{id}/lists/{id}/items` - Create new item
- `PATCH /sites/{id}/lists/{id}/items/{id}` - Update item properties
- `DELETE /sites/{id}/lists/{id}/items/{id}` - Delete item
- `GET /sites/{id}/lists/{id}/items/{id}/fields` - Get item field values
- `PATCH /sites/{id}/lists/{id}/items/{id}/fields` - Update item field values
- `GET /sites/{id}/lists/{id}/items/delta` - Track item changes incrementally

**Permissions required**:
- Delegated: `Sites.Read.All`, `Sites.ReadWrite.All`
- Application: `Sites.Read.All`, `Sites.ReadWrite.All`, `Sites.Selected`
- **Least privilege**: `Sites.Read.All` for read; `Sites.ReadWrite.All` for create/update/delete

**ListItem ID format**: Integer (sequential within list)
- Example: `1`, `2`, `123`

## listItem Resource Type

### JSON Schema [VERIFIED]

```json
{
  "id": "string",
  "contentType": { "@odata.type": "microsoft.graph.contentTypeInfo" },
  "fields": { "@odata.type": "microsoft.graph.fieldValueSet" },
  "sharepointIds": { "@odata.type": "microsoft.graph.sharepointIds" },
  "deleted": { "@odata.type": "microsoft.graph.deleted" },
  "createdBy": { "@odata.type": "microsoft.graph.identitySet" },
  "createdDateTime": "datetime",
  "lastModifiedBy": { "@odata.type": "microsoft.graph.identitySet" },
  "lastModifiedDateTime": "datetime",
  "name": "string",
  "description": "string",
  "eTag": "string",
  "parentReference": { "@odata.type": "microsoft.graph.itemReference" },
  "webUrl": "url",
  "@odata.type": "microsoft.graph.listItem"
}
```

### Properties [VERIFIED]

- **id** - Unique identifier (integer as string)
- **contentType** - Content type of this item:
  ```json
  {
    "id": "0x0100...",
    "name": "Item"
  }
  ```
- **fields** - Column values as fieldValueSet (dynamic properties)
- **sharepointIds** - SharePoint REST API identifiers
- **deleted** - Present if item is deleted (includes `state` property)
- **createdBy** - Identity of creator
- **createdDateTime** - ISO 8601 creation timestamp
- **lastModifiedBy** - Identity of last modifier
- **lastModifiedDateTime** - ISO 8601 last modified timestamp
- **name** - Name of item (often same as Title field)
- **eTag** - Entity tag for concurrency
- **parentReference** - Reference to parent list
- **webUrl** - URL to view item in browser

### fieldValueSet [VERIFIED]

Dynamic object containing column values. Properties match column internal names:

```json
{
  "Title": "My Item",
  "Color": "Red",
  "Quantity": 10,
  "DueDate": "2026-02-15T00:00:00Z",
  "AssignedTo": {
    "LookupId": 5,
    "LookupValue": "John Doe",
    "Email": "john@contoso.com"
  }
}
```

### Relationships (expandable via $expand)

- **activities** - Collection of `itemActivity`
- **analytics** - `itemAnalytics` resource
- **documentSetVersions** - Collection of `documentSetVersion`
- **driveItem** - Associated `driveItem` (for document libraries)
- **fields** - `fieldValueSet` with column values
- **versions** - Collection of `listItemVersion`

## 1. GET /sites/{id}/lists/{id}/items - List Items

### Description [VERIFIED]

Get the collection of items in a list. By default returns item metadata only - expand `fields` to get column values.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items
```

With fields:
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items?expand=fields
```

With specific columns:
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items?expand=fields(select=Title,Color,Quantity)
```

### Path Parameters

- **site-id** (`string`) - Site composite ID
- **list-id** (`string`) - List GUID or title

### OData Query Parameters [VERIFIED]

- **$expand** - Expand relationships: `fields`, `driveItem`, `versions`
- **$filter** - Filter items (supports: `eq`, `ne`, `lt`, `gt`, `le`, `ge`, `startswith`)
- **$select** - Select item properties
- **$top** - Limit results
- **$orderby** - Sort results (limited support)

### Filter Examples [VERIFIED]

```http
# Filter by field value
GET /sites/{id}/lists/{id}/items?$filter=fields/Color eq 'Red'

# Filter by multiple conditions
GET /sites/{id}/lists/{id}/items?$filter=fields/Quantity gt 10 and fields/Status eq 'Active'

# Filter with startswith
GET /sites/{id}/lists/{id}/items?$filter=startswith(fields/Title, 'Project')

# Filter by date
GET /sites/{id}/lists/{id}/items?$filter=fields/DueDate lt '2026-03-01T00:00:00Z'
```

**Note**: Filtering works best on indexed columns.

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "1",
      "contentType": {
        "id": "0x0100...",
        "name": "Item"
      },
      "createdDateTime": "2026-01-15T10:30:00Z",
      "lastModifiedDateTime": "2026-01-28T15:45:00Z",
      "webUrl": "https://contoso.sharepoint.com/sites/team/Lists/Tasks/1_.000",
      "fields": {
        "Title": "Complete report",
        "Status": "In Progress",
        "Priority": "High",
        "DueDate": "2026-02-01T00:00:00Z"
      }
    },
    {
      "id": "2",
      "contentType": {
        "id": "0x0100...",
        "name": "Item"
      },
      "fields": {
        "Title": "Review design",
        "Status": "Not Started",
        "Priority": "Normal"
      }
    }
  ],
  "@odata.nextLink": "https://graph.microsoft.com/v1.0/sites/.../items?$skiptoken=..."
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Sites
Get-MgSiteListItem -SiteId $siteId -ListId $listId -ExpandProperty "fields"
```

**C#**:
```csharp
var items = await graphClient.Sites["{site-id}"].Lists["{list-id}"].Items
    .GetAsync(config => {
        config.QueryParameters.Expand = new[] { "fields" };
    });
```

**JavaScript**:
```javascript
let items = await client.api('/sites/{site-id}/lists/{list-id}/items')
    .expand('fields')
    .get();
```

**Python**:
```python
result = await graph_client.sites.by_site_id('site-id').lists.by_list_id('list-id').items.get(
    request_configuration=RequestConfiguration(
        query_parameters=ItemsRequestBuilder.ItemsRequestBuilderGetQueryParameters(
            expand=['fields']
        )
    )
)
```

## 2. GET /sites/{id}/lists/{id}/items/{id} - Get Item

### Description [VERIFIED]

Returns the metadata for a specific item in a SharePoint list.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items/{item-id}
```

With fields:
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items/{item-id}?expand=fields
```

### Path Parameters

- **site-id** (`string`) - Site composite ID
- **list-id** (`string`) - List GUID or title
- **item-id** (`string`) - Item ID (integer)

### Response JSON [VERIFIED]

```json
{
  "id": "1",
  "contentType": {
    "id": "0x0100...",
    "name": "Item"
  },
  "createdBy": {
    "user": {
      "displayName": "John Doe",
      "email": "john@contoso.com",
      "id": "user-guid"
    }
  },
  "createdDateTime": "2026-01-15T10:30:00Z",
  "lastModifiedBy": {
    "user": {
      "displayName": "Jane Smith",
      "email": "jane@contoso.com"
    }
  },
  "lastModifiedDateTime": "2026-01-28T15:45:00Z",
  "eTag": "\"guid,version\"",
  "parentReference": {
    "siteId": "site-guid"
  },
  "webUrl": "https://contoso.sharepoint.com/sites/team/Lists/Tasks/1_.000",
  "fields": {
    "Title": "Complete report",
    "Status": "In Progress",
    "Priority": "High",
    "DueDate": "2026-02-01T00:00:00Z",
    "AssignedTo": {
      "LookupId": 5,
      "LookupValue": "John Doe"
    }
  }
}
```

### SDK Examples

**PowerShell**:
```powershell
Get-MgSiteListItem -SiteId $siteId -ListId $listId -ListItemId $itemId -ExpandProperty "fields"
```

**C#**:
```csharp
var item = await graphClient.Sites["{site-id}"].Lists["{list-id}"].Items["{item-id}"]
    .GetAsync(config => config.QueryParameters.Expand = new[] { "fields" });
```

## 3. POST /sites/{id}/lists/{id}/items - Create Item

### Description [VERIFIED]

Create a new listItem in a list. Provide field values in the `fields` property.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items
```

### Request Headers

- **Authorization**: `Bearer {token}`
- **Content-Type**: `application/json`

### Request Body

```json
{
  "fields": {
    "Title": "New Task",
    "Status": "Not Started",
    "Priority": "High",
    "DueDate": "2026-02-15T00:00:00Z",
    "Description": "Description of the task"
  }
}
```

### Field Types [VERIFIED]

- **Text/Choice**: `"Title": "value"`
- **Number**: `"Quantity": 10`
- **DateTime**: `"DueDate": "2026-02-15T00:00:00Z"` (ISO 8601)
- **Boolean**: `"Completed": true`
- **Lookup**: `"CategoryLookupId": 5` (use LookupId suffix)
- **Person**: `"AssignedToLookupId": 12` (user lookup ID)
- **Multi-value**: `"TagsLookupId@odata.type": "Collection(Edm.Int32)"`, `"TagsLookupId": [1, 2, 3]`

### Response JSON [VERIFIED]

Returns 201 Created with the item object:

```json
{
  "id": "5",
  "createdDateTime": "2026-01-28T16:00:00Z",
  "lastModifiedDateTime": "2026-01-28T16:00:00Z",
  "webUrl": "https://contoso.sharepoint.com/sites/team/Lists/Tasks/5_.000",
  "fields": {
    "Title": "New Task",
    "Status": "Not Started",
    "Priority": "High",
    "DueDate": "2026-02-15T00:00:00Z"
  }
}
```

### SDK Examples

**PowerShell**:
```powershell
$params = @{
  fields = @{
    Title = "New Task"
    Status = "Not Started"
    Priority = "High"
  }
}
New-MgSiteListItem -SiteId $siteId -ListId $listId -BodyParameter $params
```

**JavaScript**:
```javascript
const item = {
  fields: {
    Title: 'New Task',
    Status: 'Not Started',
    Priority: 'High'
  }
};
await client.api('/sites/{site-id}/lists/{list-id}/items').post(item);
```

**C#**:
```csharp
var listItem = new ListItem
{
    Fields = new FieldValueSet
    {
        AdditionalData = new Dictionary<string, object>
        {
            { "Title", "New Task" },
            { "Status", "Not Started" },
            { "Priority", "High" }
        }
    }
};
var result = await graphClient.Sites["{site-id}"].Lists["{list-id}"].Items.PostAsync(listItem);
```

## 4. PATCH /sites/{id}/lists/{id}/items/{id} - Update Item

### Description [VERIFIED]

Update the properties on a listItem. Use this to update item metadata.

### HTTP Request

```http
PATCH https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items/{item-id}
```

### Request Headers

- **Authorization**: `Bearer {token}`
- **Content-Type**: `application/json`
- **If-Match**: `{etag}` (optional, for optimistic concurrency)

### Request Body

```json
{
  "fields": {
    "Status": "Completed",
    "CompletedDate": "2026-01-28T16:30:00Z"
  }
}
```

### Response JSON [VERIFIED]

Returns 200 OK with updated item.

### SDK Examples

**PowerShell**:
```powershell
$params = @{
  fields = @{
    Status = "Completed"
  }
}
Update-MgSiteListItem -SiteId $siteId -ListId $listId -ListItemId $itemId -BodyParameter $params
```

## 5. DELETE /sites/{id}/lists/{id}/items/{id} - Delete Item

### Description [VERIFIED]

Removes an item from a list. Item is moved to recycle bin.

### HTTP Request

```http
DELETE https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items/{item-id}
```

### Request Headers

- **Authorization**: `Bearer {token}`
- **If-Match**: `{etag}` (optional)

### Response [VERIFIED]

- **204 No Content** - Success
- **412 Precondition Failed** - ETag mismatch

### SDK Examples

**PowerShell**:
```powershell
Remove-MgSiteListItem -SiteId $siteId -ListId $listId -ListItemId $itemId
```

**C#**:
```csharp
await graphClient.Sites["{site-id}"].Lists["{list-id}"].Items["{item-id}"].DeleteAsync();
```

## 6. GET /sites/{id}/lists/{id}/items/{id}/fields - Get Fields

### Description [VERIFIED]

Get the column values (fields) for a list item directly.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items/{item-id}/fields
```

### Response JSON [VERIFIED]

```json
{
  "Title": "Complete report",
  "Status": "In Progress",
  "Priority": "High",
  "DueDate": "2026-02-01T00:00:00Z",
  "Quantity": 5,
  "AssignedTo": {
    "LookupId": 5,
    "LookupValue": "John Doe",
    "Email": "john@contoso.com"
  },
  "@odata.etag": "\"guid,version\""
}
```

### SDK Examples

**C#**:
```csharp
var fields = await graphClient.Sites["{site-id}"].Lists["{list-id}"].Items["{item-id}"].Fields.GetAsync();
```

## 7. PATCH /sites/{id}/lists/{id}/items/{id}/fields - Update Fields

### Description [VERIFIED]

Update specific column values on a list item. More efficient than updating the entire item.

### HTTP Request

```http
PATCH https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items/{item-id}/fields
```

### Request Body

```json
{
  "Color": "Blue",
  "Quantity": 25
}
```

### Response JSON [VERIFIED]

Returns 200 OK with updated fieldValueSet:

```json
{
  "Title": "Widget",
  "Color": "Blue",
  "Quantity": 25,
  "@odata.etag": "\"guid,newversion\""
}
```

### SDK Examples

**PowerShell**:
```powershell
$params = @{
  Color = "Blue"
  Quantity = 25
}
Update-MgSiteListItemField -SiteId $siteId -ListId $listId -ListItemId $itemId -BodyParameter $params
```

**JavaScript**:
```javascript
const fields = { Color: 'Blue', Quantity: 25 };
await client.api('/sites/{site-id}/lists/{list-id}/items/{item-id}/fields')
    .patch(fields);
```

## 8. GET /sites/{id}/lists/{id}/items/delta - Delta Query

### Description [VERIFIED]

Get newly created, updated, or deleted list items without performing a full read. Uses delta tokens for incremental sync.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items/delta
```

With token:
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items/delta?token={token}
```

### Query Parameters

- **token** (`string`) - Delta token from previous response
- **$select** - Select properties
- **$expand** - Expand relationships (e.g., `fields`)
- **$top** - Limit results per page

### Delta Sync Pattern [VERIFIED]

1. Initial request: `GET .../items/delta` (no token)
2. Follow `@odata.nextLink` until you get `@odata.deltaLink`
3. Store `@odata.deltaLink` token
4. For changes: request `@odata.deltaLink` URL
5. Deleted items have `@removed` annotation with `reason: "deleted"`

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "1",
      "fields": {
        "Title": "Updated Task"
      }
    },
    {
      "id": "3",
      "@removed": {
        "reason": "deleted"
      }
    }
  ],
  "@odata.deltaLink": "https://graph.microsoft.com/v1.0/sites/.../items/delta?token=..."
}
```

### Handling Deleted Items [VERIFIED]

Items with `@removed` annotation should be deleted from local state:

```json
{
  "id": "3",
  "@removed": {
    "reason": "deleted"
  }
}
```

### SDK Examples

**PowerShell**:
```powershell
Get-MgSiteListItemDelta -SiteId $siteId -ListId $listId
```

**C#**:
```csharp
var delta = await graphClient.Sites["{site-id}"].Lists["{list-id}"].Items.Delta.GetAsDeltaGetResponseAsync();
```

**Python**:
```python
result = await graph_client.sites.by_site_id('site-id').lists.by_list_id('list-id').items.delta.get()
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid field name or value type
- **401 Unauthorized** - Missing or invalid authentication token
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Item does not exist
- **409 Conflict** - Concurrency conflict
- **410 Gone** - Delta token expired
- **412 Precondition Failed** - ETag mismatch
- **429 Too Many Requests** - Rate limit exceeded

### Error Response Format

```json
{
  "error": {
    "code": "invalidRequest",
    "message": "Field 'InvalidColumn' does not exist.",
    "innerError": {
      "request-id": "guid",
      "date": "datetime"
    }
  }
}
```

## Throttling Considerations [VERIFIED]

**Throttling Behavior**:
- HTTP 429 returned when throttled
- `Retry-After` header indicates wait time
- Large lists (>5000 items) may have additional limits

**Best Practices**:
- Use `$select` on fields to limit returned columns
- Use `$filter` to reduce result set
- Use delta queries for sync scenarios instead of full enumeration
- Batch create/update operations when possible
- Index columns used in filters

**Resource Units**:
- Item GET: ~1 resource unit
- Item GET with $expand=fields: ~1-2 resource units
- Item POST/PATCH/DELETE: ~2 resource units
- Delta query: ~1-5 resource units depending on changes

## Column Internal Names [VERIFIED]

When working with fields, use internal column names (not display names):

- Display name: "Due Date" → Internal name: `DueDate`
- Display name: "Assigned To" → Internal name: `AssignedTo`
- Lookup fields: append `LookupId` for setting values

To find internal names, expand columns on the list:
```http
GET /sites/{id}/lists/{id}?$expand=columns
```

## Sources

- **MSGRAPH-LITEM-SC-01**: https://learn.microsoft.com/en-us/graph/api/resources/listitem?view=graph-rest-1.0
- **MSGRAPH-LITEM-SC-02**: https://learn.microsoft.com/en-us/graph/api/listitem-list?view=graph-rest-1.0
- **MSGRAPH-LITEM-SC-03**: https://learn.microsoft.com/en-us/graph/api/listitem-get?view=graph-rest-1.0
- **MSGRAPH-LITEM-SC-04**: https://learn.microsoft.com/en-us/graph/api/listitem-create?view=graph-rest-1.0
- **MSGRAPH-LITEM-SC-05**: https://learn.microsoft.com/en-us/graph/api/listitem-update?view=graph-rest-1.0
- **MSGRAPH-LITEM-SC-06**: https://learn.microsoft.com/en-us/graph/api/listitem-delete?view=graph-rest-1.0
- **MSGRAPH-LITEM-SC-07**: https://learn.microsoft.com/en-us/graph/api/listitem-delta?view=graph-rest-1.0

## Document History

**[2026-01-28 18:10]**
- Initial creation with 8 ListItem API endpoints
- Full JSON request/response examples
- SDK examples for PowerShell, C#, JavaScript, Python
- Field types and lookup patterns documented
- Delta query pattern documented
