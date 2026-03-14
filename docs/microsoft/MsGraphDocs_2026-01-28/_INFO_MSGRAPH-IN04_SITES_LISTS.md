# INFO: Microsoft Graph API - List Core Methods

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for SharePoint List API core methods with request/response JSON and examples
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_MSGRAPH-IN00_TOC.md [MSGRAPH-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Create custom business applications with structured data (CRM, inventory, tracking)
- Build Power Apps-style solutions with Graph API backend
- Manage document libraries programmatically (lists with template "documentLibrary")
- Extend list schemas with custom columns for business requirements
- Subscribe to real-time list changes via WebSocket notifications
- Sync content types from hub sites to team site lists
- Build list-driven workflows and approval systems

**Key findings**:
- Lists can be accessed by GUID or display name (title) - IDs are more reliable
- Document libraries are lists with `template: "documentLibrary"` - dual access via List or Drive API
- System lists (hidden=true) are excluded by default; use `$select=system` to include
- WebSocket endpoint requires Files.Read.All, not Sites.Read.All permissions
- Content types must exist at site level before adding to list
- List operations return richLongRunningOperation for async content type sync
- Column definitions can be created inline during list creation
- List template determines available features (events, tasks have special behaviors)

## Quick Reference Summary

**Endpoints covered**: 8 List API methods

- `GET /sites/{id}/lists` - Get all lists in a site
- `GET /sites/{id}/lists/{id}` - Get list by ID or title
- `POST /sites/{id}/lists` - Create a new list
- `PATCH /sites/{id}/lists/{id}` - Update list properties
- `GET /sites/{id}/lists/{id}/operations` - List long-running operations
- `GET /sites/{id}/lists/{id}/subscriptions/socketIo` - Get WebSocket endpoint
- `GET /sites/{id}/lists/{id}/contentTypes` - List content types in list
- `POST /sites/{id}/lists/{id}/contentTypes` - Add content type to list

**Permissions required**:
- Delegated: `Sites.Read.All`, `Sites.ReadWrite.All`
- Application: `Sites.Read.All`, `Sites.ReadWrite.All`, `Sites.Selected`
- **Least privilege**: `Sites.Read.All` for read operations; `Sites.ReadWrite.All` for create/update
- Note: WebSocket requires `Files.Read.All` or `Files.ReadWrite.All`

**List ID format**: GUID or list title (display name)
- Example ID: `b57af081-936c-4803-a120-d94887b03864`
- Example title: `Documents`

## List Resource Type

### JSON Schema [VERIFIED]

```json
{
  "id": "string (guid)",
  "displayName": "string",
  "name": "string",
  "description": "string",
  "webUrl": "url",
  "createdDateTime": "datetime",
  "lastModifiedDateTime": "datetime",
  "createdBy": { "@odata.type": "microsoft.graph.identitySet" },
  "lastModifiedBy": { "@odata.type": "microsoft.graph.identitySet" },
  "eTag": "string",
  "list": { "@odata.type": "microsoft.graph.listInfo" },
  "parentReference": { "@odata.type": "microsoft.graph.itemReference" },
  "sharepointIds": { "@odata.type": "microsoft.graph.sharepointIds" },
  "system": { "@odata.type": "microsoft.graph.systemFacet" },
  "@odata.type": "microsoft.graph.list"
}
```

### Properties [VERIFIED]

- **id** - Unique identifier (GUID)
- **displayName** - Human-readable title of the list
- **name** - URL-safe name
- **description** - List description text
- **webUrl** - Full URL to list in browser
- **createdDateTime** - ISO 8601 creation timestamp
- **lastModifiedDateTime** - ISO 8601 last modified timestamp
- **createdBy** - Identity of creator
- **lastModifiedBy** - Identity of last modifier
- **eTag** - Entity tag for concurrency
- **list** - List-specific metadata:
  ```json
  {
    "contentTypesEnabled": true,
    "hidden": false,
    "template": "genericList"
  }
  ```
- **parentReference** - Reference to parent site
- **sharepointIds** - SharePoint REST API identifiers
- **system** - Present if list is system-managed (hidden by default)

### listInfo Properties [VERIFIED]

- **contentTypesEnabled** - Whether content types are enabled
- **hidden** - Whether list is hidden in UI
- **template** - List template type: `genericList`, `documentLibrary`, `survey`, `announcements`, `contacts`, `events`, `tasks`, `discussionBoard`, `pictureLibrary`, `dataSources`, `webTemplateCatalog`, `userInformation`, `webPartCatalog`, `listTemplateCatalog`, `xmlForm`, `masterPageCatalog`, `noCodeWorkflows`, `workflowProcess`, `webPageLibrary`, `customGrid`, `solutionCatalog`, `noCodePublic`, `themeCatalog`, `designCatalog`, `appDataCatalog`

### Relationships (expandable via $expand)

- **columns** - Collection of `columnDefinition`
- **contentTypes** - Collection of `contentType`
- **drive** - Associated document library drive (if documentLibrary)
- **items** - Collection of `listItem`
- **operations** - Collection of `richLongRunningOperation`
- **subscriptions** - Collection of `subscription`

## 1. GET /sites/{id}/lists - Get Lists in Site

### Description [VERIFIED]

Get the collection of lists for a site. Lists with the `system` facet are hidden by default - include `system` in `$select` to show them.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists
```

### Path Parameters

- **site-id** (`string`) - Site composite ID

### Query Parameters

- **$select** - Select properties (include `system` to show system lists)
- **$expand** - Expand relationships (`columns`, `items`, `contentTypes`)
- **$filter** - Filter results
- **$top** - Limit results

### Request Example

```http
GET https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,guid,guid/lists?$select=id,displayName,list,system
```

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "b57af081-936c-4803-a120-d94887b03864",
      "displayName": "Documents",
      "name": "Documents",
      "webUrl": "https://contoso.sharepoint.com/sites/team/Shared Documents",
      "list": {
        "contentTypesEnabled": false,
        "hidden": false,
        "template": "documentLibrary"
      }
    },
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "displayName": "Tasks",
      "name": "Tasks",
      "list": {
        "hidden": false,
        "template": "tasks"
      }
    }
  ]
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Sites
Get-MgSiteList -SiteId $siteId
```

**C#**:
```csharp
var lists = await graphClient.Sites["{site-id}"].Lists.GetAsync();
```

**JavaScript**:
```javascript
let lists = await client.api('/sites/{site-id}/lists').get();
```

**Python**:
```python
result = await graph_client.sites.by_site_id('site-id').lists.get()
```

## 2. GET /sites/{id}/lists/{id} - Get List by ID

### Description [VERIFIED]

Returns the metadata for a list. Can use list ID (GUID) or list title.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}
```

By title:
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-title}
```

### Path Parameters

- **site-id** (`string`) - Site composite ID
- **list-id** (`string`) - List GUID or display name

### OData Query Parameters

- **$select** - Select specific properties
- **$expand** - Expand relationships

### Common Expand Patterns [VERIFIED]

```http
# Get list with columns
GET /sites/{id}/lists/{id}?$expand=columns

# Get list with items and their fields
GET /sites/{id}/lists/{id}?$expand=items(expand=fields)

# Get list with columns and first 100 items
GET /sites/{id}/lists/{id}?$expand=columns,items($top=100;expand=fields)
```

### Response JSON [VERIFIED]

```json
{
  "id": "b57af081-936c-4803-a120-d94887b03864",
  "displayName": "Documents",
  "name": "Documents",
  "description": "Team shared documents",
  "webUrl": "https://contoso.sharepoint.com/sites/team/Shared Documents",
  "createdDateTime": "2020-01-15T10:30:00Z",
  "lastModifiedDateTime": "2026-01-28T15:45:00Z",
  "list": {
    "contentTypesEnabled": true,
    "hidden": false,
    "template": "documentLibrary"
  },
  "sharepointIds": {
    "listId": "b57af081-936c-4803-a120-d94887b03864",
    "listItemUniqueId": null,
    "siteId": "da60e844-ba1d-49bc-b4d4-d5e36bae9019",
    "siteUrl": "https://contoso.sharepoint.com/sites/team",
    "webId": "712a596e-90a1-49e3-9b48-bfa80bee8740"
  }
}
```

### SDK Examples

**PowerShell**:
```powershell
Get-MgSiteList -SiteId $siteId -ListId $listId
# Or by title
Get-MgSiteList -SiteId $siteId -ListId "Documents"
```

**C#**:
```csharp
var list = await graphClient.Sites["{site-id}"].Lists["{list-id}"].GetAsync();
```

## 3. POST /sites/{id}/lists - Create List

### Description [VERIFIED]

Create a new list in a site. Can define columns inline during creation.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/sites/{site-id}/lists
```

### Request Headers

- **Authorization**: `Bearer {token}`
- **Content-Type**: `application/json`

### Request Body

Minimal:
```json
{
  "displayName": "My List",
  "list": {
    "template": "genericList"
  }
}
```

With columns:
```json
{
  "displayName": "Books",
  "columns": [
    {
      "name": "Author",
      "text": {}
    },
    {
      "name": "PageCount",
      "number": {}
    },
    {
      "name": "PublishDate",
      "dateTime": {}
    }
  ],
  "list": {
    "template": "genericList"
  }
}
```

### List Templates [VERIFIED]

- **genericList** - Custom list
- **documentLibrary** - Document library
- **events** - Calendar/events list
- **tasks** - Task list
- **contacts** - Contacts list
- **announcements** - Announcements list
- **survey** - Survey list
- **discussionBoard** - Discussion board

### Response JSON [VERIFIED]

Returns 201 Created with the list object:

```json
{
  "id": "new-list-guid",
  "displayName": "Books",
  "name": "Books",
  "webUrl": "https://contoso.sharepoint.com/sites/team/Lists/Books",
  "createdDateTime": "2026-01-28T16:00:00Z",
  "list": {
    "contentTypesEnabled": false,
    "hidden": false,
    "template": "genericList"
  }
}
```

### SDK Examples

**PowerShell**:
```powershell
$params = @{
  displayName = "Books"
  list = @{
    template = "genericList"
  }
  columns = @(
    @{ name = "Author"; text = @{} }
    @{ name = "PageCount"; number = @{} }
  )
}
New-MgSiteList -SiteId $siteId -BodyParameter $params
```

**JavaScript**:
```javascript
const list = {
  displayName: 'Books',
  columns: [
    { name: 'Author', text: {} },
    { name: 'PageCount', number: {} }
  ],
  list: { template: 'genericList' }
};
await client.api('/sites/{site-id}/lists').post(list);
```

**C#**:
```csharp
var list = new List
{
    DisplayName = "Books",
    ListInfo = new ListInfo { Template = "genericList" },
    Columns = new List<ColumnDefinition>
    {
        new ColumnDefinition { Name = "Author", Text = new TextColumn() }
    }
};
var result = await graphClient.Sites["{site-id}"].Lists.PostAsync(list);
```

## 4. PATCH /sites/{id}/lists/{id} - Update List

### Description [VERIFIED]

Update the properties of a list. Can update displayName, description, and list settings.

### HTTP Request

```http
PATCH https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}
```

### Request Headers

- **Authorization**: `Bearer {token}`
- **Content-Type**: `application/json`
- **If-Match**: `{etag}` (optional, for optimistic concurrency)

### Request Body

```json
{
  "displayName": "Updated List Name",
  "description": "New description for the list"
}
```

### Updatable Properties [VERIFIED]

- **displayName** - List title
- **description** - List description

### Response JSON [VERIFIED]

Returns 200 OK with updated list object.

### SDK Examples

**PowerShell**:
```powershell
$params = @{
  displayName = "Updated Books"
  description = "Library of technical books"
}
Update-MgSiteList -SiteId $siteId -ListId $listId -BodyParameter $params
```

## 5. GET /sites/{id}/lists/{id}/operations - List Operations

### Description [VERIFIED]

Get a list of rich long-running operations associated with a list. Operations include content type sync, column creation, etc.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/operations
```

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "contentTypeCopy,0x0101",
      "createdDateTime": "2026-01-24T16:28:23Z",
      "resourceId": "0x0101",
      "resourceLocation": "https://graph.microsoft.com/v1.0/sites/.../contentTypes/0x0101",
      "status": "succeeded",
      "type": "contentTypeCopy"
    }
  ]
}
```

### Operation Status Values

- **notStarted** - Operation queued
- **running** - In progress
- **succeeded** - Completed successfully
- **failed** - Failed (check `error` property)

### SDK Examples

**Python**:
```python
result = await graph_client.sites.by_site_id('site-id').lists.by_list_id('list-id').operations.get()
```

## 6. GET /sites/{id}/lists/{id}/subscriptions/socketIo - WebSocket Endpoint

### Description [VERIFIED]

Get a WebSocket endpoint URL for receiving near-real-time change notifications for a list using socket.io. Useful for building real-time collaborative applications.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/drive/root/subscriptions/socketIo
```

Alternative paths:
```http
GET /drives/{driveId}/root/subscriptions/socketIo
GET /drives/{driveId}/list/subscriptions/socketIo
```

### Permissions [VERIFIED]

- Delegated: `Files.Read`, `Files.ReadWrite`, `Files.Read.All`, `Files.ReadWrite.All`
- Application: `Files.Read.All`, `Files.ReadWrite.All`

### Response JSON [VERIFIED]

```json
{
  "notificationUrl": "https://notifications.graph.microsoft.com/v1.0/socketio/..."
}
```

### Usage Pattern [VERIFIED]

1. Call endpoint to get `notificationUrl`
2. Connect using socket.io client library
3. Listen for change events
4. Reconnect if connection drops

### SDK Examples

**JavaScript**:
```javascript
// Get socket URL
const subscription = await client.api('/drives/{driveId}/root/subscriptions/socketIo').get();

// Connect with socket.io
const socket = io(subscription.notificationUrl);
socket.on('notification', (data) => {
  console.log('Change detected:', data);
});
```

## 7. GET /sites/{id}/lists/{id}/contentTypes - List Content Types

### Description [VERIFIED]

Get the collection of contentType resources in a list. Content types define the metadata schema for list items.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/contentTypes
```

### OData Query Parameters

- **$select** - Select properties
- **$filter** - Filter results
- **$expand** - Expand relationships (`columns`, `columnLinks`)

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "0x0101",
      "name": "Document",
      "description": "Create a new document.",
      "hidden": false,
      "group": "Document Content Types",
      "parentId": "0x0101"
    },
    {
      "id": "0x0120",
      "name": "Folder",
      "description": "Create a new folder.",
      "hidden": false,
      "group": "Folder Content Types"
    }
  ]
}
```

### SDK Examples

**PowerShell**:
```powershell
Get-MgSiteListContentType -SiteId $siteId -ListId $listId
```

**C#**:
```csharp
var contentTypes = await graphClient.Sites["{site-id}"].Lists["{list-id}"].ContentTypes.GetAsync();
```

## 8. POST /sites/{id}/lists/{id}/contentTypes - Add Content Type

### Description [VERIFIED]

Add an existing site content type to a list. The content type must exist at the site level first.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/contentTypes
```

### Request Body

Reference existing content type:
```json
{
  "contentType": {
    "id": "0x0101009D1CB255DA76424F860D91F20E6C4118"
  }
}
```

### Response JSON [VERIFIED]

Returns 201 Created with the content type object.

### SDK Examples

**PowerShell**:
```powershell
$params = @{
  contentType = @{
    id = "0x0101009D1CB255DA76424F860D91F20E6C4118"
  }
}
New-MgSiteListContentType -SiteId $siteId -ListId $listId -BodyParameter $params
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid list template or column definition
- **401 Unauthorized** - Missing or invalid authentication token
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - List does not exist
- **409 Conflict** - List with same name already exists
- **412 Precondition Failed** - ETag mismatch
- **429 Too Many Requests** - Rate limit exceeded

### Error Response Format

```json
{
  "error": {
    "code": "nameAlreadyExists",
    "message": "A list with the specified name already exists.",
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
- List operations with many items may take longer

**Best Practices**:
- Use `$select` to limit returned properties
- Use `$top` with pagination for large lists
- Cache list IDs and schemas
- Use delta queries for sync scenarios
- Batch item operations when possible

**Resource Units**:
- List GET: ~1 resource unit
- List GET with $expand: ~2-5 resource units
- List POST/PATCH: ~2 resource units
- Item operations: See ListItem documentation

## List Templates Reference [VERIFIED]

Common templates for `list.template`:

- **genericList** - Custom list (most flexible)
- **documentLibrary** - Document library with file support
- **events** - Calendar events
- **tasks** - Task tracking
- **contacts** - Contact list
- **announcements** - News/announcements
- **links** - Link list
- **survey** - Survey/poll
- **discussionBoard** - Discussion forum
- **issueTracking** - Issue/bug tracking
- **pictureLibrary** - Image gallery

## Sources

- **MSGRAPH-LIST-SC-01**: https://learn.microsoft.com/en-us/graph/api/resources/list?view=graph-rest-1.0
- **MSGRAPH-LIST-SC-02**: https://learn.microsoft.com/en-us/graph/api/list-list?view=graph-rest-1.0
- **MSGRAPH-LIST-SC-03**: https://learn.microsoft.com/en-us/graph/api/list-get?view=graph-rest-1.0
- **MSGRAPH-LIST-SC-04**: https://learn.microsoft.com/en-us/graph/api/list-create?view=graph-rest-1.0
- **MSGRAPH-LIST-SC-05**: https://learn.microsoft.com/en-us/graph/api/list-list-operations?view=graph-rest-1.0
- **MSGRAPH-LIST-SC-06**: https://learn.microsoft.com/en-us/graph/api/subscriptions-socketio?view=graph-rest-1.0
- **MSGRAPH-LIST-SC-07**: https://learn.microsoft.com/en-us/graph/api/list-list-contenttypes?view=graph-rest-1.0

## Document History

**[2026-01-28 17:55]**
- Initial creation with 8 List API endpoints
- Full JSON request/response examples
- SDK examples for PowerShell, C#, JavaScript, Python
- List templates reference documented
