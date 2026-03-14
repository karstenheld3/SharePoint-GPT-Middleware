# INFO: Microsoft Graph API - Column Methods

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for Column (columnDefinition) methods with request/response JSON and examples
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_MSGRAPH-IN00_TOC.md [MSGRAPH-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Add custom metadata fields to SharePoint lists and libraries
- Create reusable site columns for consistent metadata across lists
- Define choice, lookup, person, date, and other field types
- Build custom forms by defining column validation rules
- Extend content types with additional columns
- Migrate list schemas between environments programmatically

**Key findings**:
- Site columns are reusable across lists; list columns are local to one list
- Column types defined by facet objects (text, choice, number, dateTime, etc.)
- Only `required` and `hidden` can be updated on content type columns - to change other properties, update at site/list level
- Some properties (isDeletable, validation) not supported via Graph API
- Lookup columns reference items in another list
- Managed metadata columns use `term` facet linked to term store

## Quick Reference Summary

**Endpoints covered**: 8 column methods

**Site Columns (4)**:
- `GET /sites/{id}/columns` - List site columns
- `GET /sites/{id}/columns/{id}` - Get site column
- `POST /sites/{id}/columns` - Create site column
- `PATCH /sites/{id}/columns/{id}` - Update site column
- `DELETE /sites/{id}/columns/{id}` - Delete site column

**List Columns (4)**:
- `GET /sites/{id}/lists/{id}/columns` - List columns in list
- `GET /sites/{id}/lists/{id}/columns/{id}` - Get list column
- `POST /sites/{id}/lists/{id}/columns` - Create list column
- `PATCH /sites/{id}/lists/{id}/columns/{id}` - Update list column
- `DELETE /sites/{id}/lists/{id}/columns/{id}` - Delete list column

**Permissions required**:
- Delegated: `Sites.Read.All` (read), `Sites.Manage.All` (write)
- Application: `Sites.Read.All` (read), `Sites.Manage.All` (write)
- **Least privilege**: `Sites.Read.All` for read operations

## ColumnDefinition Resource Type [VERIFIED]

### JSON Schema

```json
{
  "id": "string (GUID)",
  "name": "string",
  "displayName": "string",
  "description": "string",
  "type": "string",
  "hidden": false,
  "indexed": false,
  "readOnly": false,
  "required": false,
  "enforceUniqueValues": false,
  "isDeletable": true,
  "isReorderable": true,
  "isSealed": false,
  "propagateChanges": false,
  "defaultValue": { "@odata.type": "microsoft.graph.defaultColumnValue" },
  "columnGroup": "string",
  "sourceColumn": { "@odata.type": "microsoft.graph.columnDefinition" },
  "boolean": { "@odata.type": "microsoft.graph.booleanColumn" },
  "calculated": { "@odata.type": "microsoft.graph.calculatedColumn" },
  "choice": { "@odata.type": "microsoft.graph.choiceColumn" },
  "currency": { "@odata.type": "microsoft.graph.currencyColumn" },
  "dateTime": { "@odata.type": "microsoft.graph.dateTimeColumn" },
  "geolocation": { "@odata.type": "microsoft.graph.geolocationColumn" },
  "lookup": { "@odata.type": "microsoft.graph.lookupColumn" },
  "number": { "@odata.type": "microsoft.graph.numberColumn" },
  "personOrGroup": { "@odata.type": "microsoft.graph.personOrGroupColumn" },
  "text": { "@odata.type": "microsoft.graph.textColumn" },
  "contentApprovalStatus": { "@odata.type": "microsoft.graph.contentApprovalStatusColumn" },
  "hyperlinkOrPicture": { "@odata.type": "microsoft.graph.hyperlinkOrPictureColumn" },
  "term": { "@odata.type": "microsoft.graph.termColumn" },
  "thumbnail": { "@odata.type": "microsoft.graph.thumbnailColumn" }
}
```

### Properties [VERIFIED]

- **id** (`string`) - Unique identifier (GUID)
- **name** (`string`) - Internal name of the column
- **displayName** (`string`) - User-facing display name
- **description** (`string`) - Description of the column
- **type** (`string`) - Column type (see Column Types below)
- **hidden** (`boolean`) - Whether column is hidden from UI
- **indexed** (`boolean`) - Whether column is indexed for search
- **readOnly** (`boolean`) - Whether column value can be modified
- **required** (`boolean`) - Whether column value is required
- **enforceUniqueValues** (`boolean`) - Require unique values
- **isDeletable** (`boolean`) - Whether column can be deleted
- **isReorderable** (`boolean`) - Whether column can be reordered
- **isSealed** (`boolean`) - Whether column schema is locked
- **propagateChanges** (`boolean`) - Push changes to derived columns
- **columnGroup** (`string`) - Group name for organizing columns

### Column Types [VERIFIED]

Each column type has a corresponding facet object:

- **boolean** - True/false values
- **calculated** - Formula-based computed values
- **choice** - Selection from predefined options
- **currency** - Monetary values
- **dateTime** - Date and/or time values
- **geolocation** - Geographic coordinates
- **lookup** - Reference to another list
- **number** - Numeric values
- **personOrGroup** - User or group picker
- **text** - Single or multi-line text
- **hyperlinkOrPicture** - URL or image
- **term** - Managed metadata term
- **thumbnail** - Image thumbnail
- **contentApprovalStatus** - Approval workflow status

## Column Type Facets [VERIFIED]

### Text Column

```json
{
  "text": {
    "allowMultipleLines": false,
    "appendChangesToExistingText": false,
    "linesForEditing": 6,
    "maxLength": 255,
    "textType": "plain | richText"
  }
}
```

### Choice Column

```json
{
  "choice": {
    "allowTextEntry": false,
    "choices": ["Option 1", "Option 2", "Option 3"],
    "displayAs": "checkBoxes | dropDownMenu | radioButtons"
  }
}
```

### Number Column

```json
{
  "number": {
    "decimalPlaces": "automatic | none | one | two | three | four | five",
    "displayAs": "number | percentage | star",
    "maximum": 100,
    "minimum": 0
  }
}
```

### DateTime Column

```json
{
  "dateTime": {
    "displayAs": "default | friendly | standard",
    "format": "dateOnly | dateTime"
  }
}
```

### Lookup Column

```json
{
  "lookup": {
    "allowMultipleValues": false,
    "allowUnlimitedLength": false,
    "columnName": "Title",
    "listId": "list-guid",
    "primaryLookupColumnId": "column-guid"
  }
}
```

### PersonOrGroup Column

```json
{
  "personOrGroup": {
    "allowMultipleSelection": false,
    "chooseFromType": "peopleAndGroups | peopleOnly",
    "displayAs": "account | contentType | created | department | firstName | id | lastName | mri | name | pictureOnly36x36 | pictureOnly48x48 | pictureOnly72x72 | sipAddress | title | userName | workEmail | workPhone"
  }
}
```

### Term Column (Managed Metadata)

```json
{
  "term": {
    "allowMultipleValues": false,
    "parentTerm": { "@odata.type": "microsoft.graph.termStore.term" },
    "showFullyQualifiedName": false,
    "termSet": { "@odata.type": "microsoft.graph.termStore.set" }
  }
}
```

## 1. GET /sites/{id}/columns - List Site Columns

### Description [VERIFIED]

Retrieves all columns defined at the site level. Site columns can be reused across lists and content types.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/columns
```

### Path Parameters

- **siteId** (`string`) - Site identifier

### Query Parameters

- **$select** - Select specific properties
- **$filter** - Filter results
- **$top** - Limit results

### Request Example

```http
GET https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/columns
Authorization: Bearer {token}
```

### Response JSON [VERIFIED]

```json
{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#Collection(columnDefinition)",
  "value": [
    {
      "id": "fa564e0f-0c70-4ab9-b863-0177e6ddd247",
      "name": "Title",
      "displayName": "Title",
      "type": "text",
      "required": true,
      "text": {
        "allowMultipleLines": false,
        "maxLength": 255
      }
    },
    {
      "id": "28cf69c5-fa48-462a-b5cd-27b6f9d2f52e",
      "name": "Modified",
      "displayName": "Modified",
      "type": "dateTime",
      "readOnly": true,
      "dateTime": {
        "displayAs": "default",
        "format": "dateTime"
      }
    }
  ]
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Sites
Get-MgSiteColumn -SiteId $siteId
```

**C#**:
```csharp
var columns = await graphClient.Sites["{site-id}"]
    .Columns
    .GetAsync();
```

**JavaScript**:
```javascript
let columns = await client.api('/sites/{site-id}/columns').get();
```

**Python**:
```python
columns = await graph_client.sites.by_site_id('site-id').columns.get()
```

## 2. GET /sites/{id}/columns/{id} - Get Site Column

### Description [VERIFIED]

Retrieves a specific column by ID from a site.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/columns/{columnId}
```

### Request Example

```http
GET https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/columns/fa564e0f-0c70-4ab9-b863-0177e6ddd247
Authorization: Bearer {token}
```

### Response JSON [VERIFIED]

```json
{
  "id": "fa564e0f-0c70-4ab9-b863-0177e6ddd247",
  "name": "Title",
  "displayName": "Title",
  "description": "Item title",
  "type": "text",
  "required": true,
  "indexed": true,
  "text": {
    "allowMultipleLines": false,
    "maxLength": 255
  }
}
```

## 3. POST /sites/{id}/columns - Create Site Column

### Description [VERIFIED]

Creates a new column at the site level that can be reused across lists and content types.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/sites/{siteId}/columns
```

### Request Body

```json
{
  "name": "string",
  "displayName": "string",
  "description": "string",
  "required": false,
  "hidden": false,
  "enforceUniqueValues": false,
  "[columnType]": { /* type-specific properties */ }
}
```

### Request Example - Text Column

```http
POST https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/columns
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "ProjectCode",
  "displayName": "Project Code",
  "description": "Unique project identifier",
  "required": true,
  "enforceUniqueValues": true,
  "text": {
    "allowMultipleLines": false,
    "maxLength": 20
  }
}
```

### Request Example - Choice Column

```http
POST https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/columns
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Status",
  "displayName": "Status",
  "choice": {
    "choices": ["Not Started", "In Progress", "Completed", "On Hold"],
    "displayAs": "dropDownMenu"
  },
  "defaultValue": {
    "value": "Not Started"
  }
}
```

### Response JSON [VERIFIED]

```json
{
  "id": "newly-created-guid",
  "name": "ProjectCode",
  "displayName": "Project Code",
  "description": "Unique project identifier",
  "type": "text",
  "required": true,
  "enforceUniqueValues": true,
  "text": {
    "allowMultipleLines": false,
    "maxLength": 20
  }
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Sites

$params = @{
    name = "ProjectCode"
    displayName = "Project Code"
    text = @{
        allowMultipleLines = $false
        maxLength = 20
    }
}
New-MgSiteColumn -SiteId $siteId -BodyParameter $params
```

**C#**:
```csharp
var requestBody = new ColumnDefinition
{
    Name = "ProjectCode",
    DisplayName = "Project Code",
    Text = new TextColumn
    {
        AllowMultipleLines = false,
        MaxLength = 20
    }
};
var result = await graphClient.Sites["{site-id}"]
    .Columns
    .PostAsync(requestBody);
```

## 4. PATCH /sites/{id}/columns/{id} - Update Site Column

### Description [VERIFIED]

Updates an existing column's properties. Can update any property except `id`. For contentType columns, only `required` and `hidden` can be updated.

### HTTP Request

```http
PATCH https://graph.microsoft.com/v1.0/sites/{siteId}/columns/{columnId}
```

Also works for list columns:
```http
PATCH https://graph.microsoft.com/v1.0/sites/{siteId}/lists/{listId}/columns/{columnId}
```

### Request Example

```http
PATCH https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/columns/abc123
Authorization: Bearer {token}
Content-Type: application/json

{
  "displayName": "Updated Display Name",
  "description": "Updated description",
  "required": true
}
```

### Response JSON [VERIFIED]

Returns the updated columnDefinition object.

## 5. DELETE /sites/{id}/columns/{id} - Delete Site Column

### Description [VERIFIED]

Removes a column from a site. Cannot delete columns that are in use by content types or lists.

### HTTP Request

```http
DELETE https://graph.microsoft.com/v1.0/sites/{siteId}/columns/{columnId}
```

### Response [VERIFIED]

```http
HTTP/1.1 204 No Content
```

## 6. GET /sites/{id}/lists/{id}/columns - List Columns in List

### Description [VERIFIED]

Retrieves all columns defined in a specific list.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/lists/{listId}/columns
```

### Request Example

```http
GET https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/lists/list-guid/columns
Authorization: Bearer {token}
```

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "column-guid-1",
      "name": "Title",
      "displayName": "Title",
      "type": "text",
      "required": true
    },
    {
      "id": "column-guid-2",
      "name": "DueDate",
      "displayName": "Due Date",
      "type": "dateTime",
      "dateTime": {
        "format": "dateOnly"
      }
    }
  ]
}
```

## 7. POST /sites/{id}/lists/{id}/columns - Create List Column

### Description [VERIFIED]

Creates a new column directly on a list.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/sites/{siteId}/lists/{listId}/columns
```

### Request Example

```http
POST https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/lists/list-guid/columns
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Priority",
  "displayName": "Priority",
  "choice": {
    "choices": ["High", "Medium", "Low"],
    "displayAs": "radioButtons"
  }
}
```

## 8. PATCH/DELETE List Columns

Same patterns as site columns but with list path:

```http
PATCH /sites/{siteId}/lists/{listId}/columns/{columnId}
DELETE /sites/{siteId}/lists/{listId}/columns/{columnId}
```

## API Limitations [VERIFIED]

**Not supported via Graph API**:
- isDeletable, propagateChanges, isReorderable, isSealed properties
- validation rules
- hyperlinkOrPicture, term, sourceContentType facets for site/list columns

These properties may appear in responses but cannot be set or modified via the API.

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid column definition or properties
- **401 Unauthorized** - Missing or invalid token
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Column or site not found
- **409 Conflict** - Column name already exists or column in use
- **429 Too Many Requests** - Rate limit exceeded

### Error Response Format

```json
{
  "error": {
    "code": "invalidRequest",
    "message": "Column name already exists.",
    "innerError": {
      "request-id": "guid",
      "date": "2026-01-28T12:00:00Z"
    }
  }
}
```

## Throttling Considerations [VERIFIED]

**Best Practices**:
- Cache column definitions
- Use `$select` to reduce payload
- Batch column operations

**Resource Units**:
- List columns: ~1 resource unit
- Create/Update/Delete: ~2 resource units

## Sources

- **MSGRAPH-COL-SC-01**: https://learn.microsoft.com/en-us/graph/api/resources/columndefinition?view=graph-rest-1.0
- **MSGRAPH-COL-SC-02**: https://learn.microsoft.com/en-us/graph/api/site-list-columns?view=graph-rest-1.0
- **MSGRAPH-COL-SC-03**: https://learn.microsoft.com/en-us/graph/api/list-list-columns?view=graph-rest-1.0
- **MSGRAPH-COL-SC-04**: https://learn.microsoft.com/en-us/graph/api/columndefinition-update?view=graph-rest-1.0

## Document History

**[2026-01-28 18:55]**
- Initial creation with 8 endpoints
- Added columnDefinition resource type
- Added column type facets documentation
- Added API limitations section
