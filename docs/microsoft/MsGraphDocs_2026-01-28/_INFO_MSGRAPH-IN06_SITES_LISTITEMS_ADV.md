# INFO: Microsoft Graph API - ListItem Advanced Methods

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for ListItem advanced methods (analytics, document set versions)
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `_INFO_MSGRAPH_LISTITEMS_CORE.md [MSGRAPH-IN01]` for core listItem operations

## Summary

**Use cases**:
- Track document engagement metrics (views, unique visitors) for reporting
- Build usage analytics dashboards for SharePoint content
- Version control for document sets (groups of related documents)
- Capture point-in-time snapshots of document sets for compliance
- Restore entire document sets to previous states after errors
- Generate activity reports over custom date ranges

**Key findings**:
- Analytics requires `listItemUniqueId` from sharepointIds, not the regular item ID
- Analytics data has 24-48 hour delay; not real-time
- itemAnalytics not available in all national cloud deployments
- getActivitiesByInterval() limited to 90-day maximum range
- Document set versions only work with Document Set content type (0x0120D520 prefix)
- Restoring a version creates NEW versions of all documents; doesn't delete history
- shouldCaptureMinorVersion controls whether draft versions are included in snapshots
- Document set version restore does NOT restore permissions - only content and metadata

## Quick Reference Summary

**Endpoints covered**: 5 ListItem advanced methods

- `GET /sites/{id}/lists/{id}/items/{id}/analytics` - Get item analytics
- `GET /sites/{id}/lists/{id}/items/{id}/getActivitiesByInterval()` - Get activity by interval
- `GET /sites/{id}/lists/{id}/items/{id}/documentSetVersions` - List document set versions
- `POST /sites/{id}/lists/{id}/items/{id}/documentSetVersions` - Create document set version
- `POST /sites/{id}/lists/{id}/items/{id}/documentSetVersions/{id}/restore` - Restore version

**Permissions required**:
- Delegated: `Sites.Read.All`, `Sites.ReadWrite.All`
- Application: `Sites.Read.All`, `Sites.ReadWrite.All`
- **Least privilege**: `Sites.Read.All` for analytics; `Sites.ReadWrite.All` for version operations

## documentSetVersion Resource Type

### JSON Schema [VERIFIED]

```json
{
  "id": "string",
  "createdDateTime": "datetime",
  "createdBy": { "@odata.type": "microsoft.graph.identitySet" },
  "comment": "string",
  "lastModifiedDateTime": "datetime",
  "lastModifiedBy": { "@odata.type": "microsoft.graph.identitySet" },
  "shouldCaptureMinorVersion": "boolean",
  "items": [{ "@odata.type": "microsoft.graph.documentSetVersionItem" }],
  "@odata.type": "microsoft.graph.documentSetVersion"
}
```

### Properties [VERIFIED]

- **id** - Version identifier
- **createdDateTime** - When version was captured
- **createdBy** - Identity who created the version
- **comment** - Version comment/description
- **lastModifiedDateTime** - Last modification timestamp
- **lastModifiedBy** - Identity who last modified
- **shouldCaptureMinorVersion** - Whether to capture minor versions of documents
- **items** - Collection of items in this version snapshot

### documentSetVersionItem [VERIFIED]

```json
{
  "itemId": "string",
  "title": "string",
  "versionId": "string"
}
```

## itemActivityStat Resource Type

### JSON Schema [VERIFIED]

```json
{
  "startDateTime": "datetime",
  "endDateTime": "datetime",
  "access": {
    "actionCount": "int",
    "actorCount": "int"
  },
  "create": {
    "actionCount": "int",
    "actorCount": "int"
  },
  "edit": {
    "actionCount": "int",
    "actorCount": "int"
  },
  "delete": {
    "actionCount": "int",
    "actorCount": "int"
  },
  "move": {
    "actionCount": "int",
    "actorCount": "int"
  },
  "@odata.type": "microsoft.graph.itemActivityStat"
}
```

## 1. GET /sites/{id}/lists/{id}/items/{id}/analytics - Get Item Analytics

### Description [VERIFIED]

Get itemAnalytics about the views that took place on this list item. Returns aggregated statistics for `allTime` and `lastSevenDays`.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items/{item-id}/analytics/allTime
```

Or for last 7 days:
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items/{item-id}/analytics/lastSevenDays
```

### Path Parameters

- **site-id** (`string`) - Site composite ID
- **list-id** (`string`) - List GUID
- **item-id** (`string`) - ListItem ID

### Important Note [VERIFIED]

The `{item-id}` for analytics must be the `listItemUniqueId` from the item's `sharepointIds`. Get it via:
```http
GET /sites/{site-id}/lists/{list-id}/items/{item-id}?$select=sharepointIds
```

### Response JSON [VERIFIED]

```json
{
  "access": {
    "actionCount": 245,
    "actorCount": 18
  }
}
```

### Limitations [VERIFIED]

- itemAnalytics not available in all national deployments
- Only access (view) statistics are returned for list items
- Analytics may have 24-48 hour delay

### SDK Examples

**C#**:
```csharp
var analytics = await graphClient.Sites["{site-id}"].Lists["{list-id}"]
    .Items["{item-id}"].Analytics.AllTime.GetAsync();
```

**PowerShell**:
```powershell
Get-MgSiteListItemAnalytic -SiteId $siteId -ListId $listId -ListItemId $itemId
```

## 2. GET /sites/{id}/lists/{id}/items/{id}/getActivitiesByInterval() - Activity by Interval

### Description [VERIFIED]

Get a collection of itemActivityStats for activities that took place on this list item within a specified time interval. Useful for custom date range reporting.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items/{item-id}/getActivitiesByInterval(startDateTime='2026-01-01',endDateTime='2026-01-28',interval='week')
```

### Function Parameters [VERIFIED]

- **startDateTime** (`string`) - ISO 8601 start date (required)
- **endDateTime** (`string`) - ISO 8601 end date (required)
- **interval** (`string`) - Aggregation interval: `day`, `week`, `month`

**Important**: Maximum time range is 90 days for daily counts.

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "startDateTime": "2026-01-01T00:00:00Z",
      "endDateTime": "2026-01-07T23:59:59Z",
      "access": {
        "actionCount": 45,
        "actorCount": 8
      }
    },
    {
      "startDateTime": "2026-01-08T00:00:00Z",
      "endDateTime": "2026-01-14T23:59:59Z",
      "access": {
        "actionCount": 62,
        "actorCount": 12
      }
    }
  ]
}
```

### Activity Types [VERIFIED]

- **access** - Views/reads
- **create** - Item creation (less common for existing items)
- **edit** - Modifications
- **delete** - Deletions
- **move** - Moves to different location

### SDK Examples

**JavaScript**:
```javascript
let activities = await client.api(
    '/sites/{site-id}/lists/{list-id}/items/{item-id}/getActivitiesByInterval(startDateTime=\'2026-01-01\',endDateTime=\'2026-01-28\',interval=\'week\')'
).get();
```

**Python**:
```python
result = await graph_client.sites.by_site_id('site-id').lists.by_list_id('list-id').items.by_list_item_id('item-id').get_activities_by_interval(
    start_date_time='2026-01-01',
    end_date_time='2026-01-28',
    interval='week'
).get()
```

## 3. GET /sites/{id}/lists/{id}/items/{id}/documentSetVersions - List Versions

### Description [VERIFIED]

Get a list of the versions of a document set item in a list. Document sets are special content types that group related documents together.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items/{item-id}/documentSetVersions
```

### Path Parameters

- **site-id** (`string`) - Site composite ID
- **list-id** (`string`) - List GUID
- **item-id** (`string`) - Document set item ID

### OData Query Parameters

- **$select** - Select properties
- **$expand** - Expand relationships
- **$top** - Limit results
- **$orderby** - Sort results

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "1",
      "createdDateTime": "2026-01-15T10:30:00Z",
      "createdBy": {
        "user": {
          "displayName": "John Doe",
          "email": "john@contoso.com"
        }
      },
      "comment": "Initial version",
      "items": [
        {
          "itemId": "doc1-guid",
          "title": "Document1.docx",
          "versionId": "1.0"
        },
        {
          "itemId": "doc2-guid",
          "title": "Spreadsheet.xlsx",
          "versionId": "1.0"
        }
      ]
    },
    {
      "id": "2",
      "createdDateTime": "2026-01-20T14:00:00Z",
      "comment": "Updated after review",
      "items": [
        {
          "itemId": "doc1-guid",
          "title": "Document1.docx",
          "versionId": "2.0"
        },
        {
          "itemId": "doc2-guid",
          "title": "Spreadsheet.xlsx",
          "versionId": "1.0"
        }
      ]
    }
  ]
}
```

### SDK Examples

**PowerShell**:
```powershell
Get-MgSiteListItemDocumentSetVersion -SiteId $siteId -ListId $listId -ListItemId $itemId
```

**C#**:
```csharp
var versions = await graphClient.Sites["{site-id}"].Lists["{list-id}"]
    .Items["{item-id}"].DocumentSetVersions.GetAsync();
```

## 4. POST /sites/{id}/lists/{id}/items/{id}/documentSetVersions - Create Version

### Description [VERIFIED]

Create a new version snapshot of a document set item. Captures the current state of all documents in the set.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items/{item-id}/documentSetVersions
```

### Request Headers

- **Authorization**: `Bearer {token}`
- **Content-Type**: `application/json`

### Request Body

```json
{
  "comment": "Version snapshot after Q1 review",
  "shouldCaptureMinorVersion": true
}
```

### Request Body Properties [VERIFIED]

- **comment** (`string`) - Description/label for this version
- **shouldCaptureMinorVersion** (`boolean`) - If `true`, captures minor versions of documents; if `false`, only major versions

### Response JSON [VERIFIED]

Returns 201 Created with the documentSetVersion object:

```json
{
  "id": "3",
  "createdDateTime": "2026-01-28T16:00:00Z",
  "createdBy": {
    "user": {
      "displayName": "Jane Smith",
      "email": "jane@contoso.com"
    }
  },
  "comment": "Version snapshot after Q1 review",
  "shouldCaptureMinorVersion": true,
  "items": [
    {
      "itemId": "doc1-guid",
      "title": "Document1.docx",
      "versionId": "2.1"
    },
    {
      "itemId": "doc2-guid",
      "title": "Spreadsheet.xlsx",
      "versionId": "1.2"
    }
  ]
}
```

### SDK Examples

**PowerShell**:
```powershell
$params = @{
    comment = "Version snapshot after Q1 review"
    shouldCaptureMinorVersion = $true
}
New-MgSiteListItemDocumentSetVersion -SiteId $siteId -ListId $listId -ListItemId $itemId -BodyParameter $params
```

**JavaScript**:
```javascript
const version = {
    comment: 'Version snapshot after Q1 review',
    shouldCaptureMinorVersion: true
};
await client.api('/sites/{site-id}/lists/{list-id}/items/{item-id}/documentSetVersions')
    .post(version);
```

## 5. POST /sites/{id}/lists/{id}/items/{id}/documentSetVersions/{id}/restore - Restore Version

### Description [VERIFIED]

Restore a document set to a previous version. All documents in the set are restored to their state at the time that version was captured.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items/{item-id}/documentSetVersions/{version-id}/restore
```

### Path Parameters

- **site-id** (`string`) - Site composite ID
- **list-id** (`string`) - List GUID
- **item-id** (`string`) - Document set item ID
- **version-id** (`string`) - Version ID to restore

### Request Body

None.

### Response [VERIFIED]

- **204 No Content** - Success

### Important Considerations [VERIFIED]

- Restoring creates new versions of all documents in the set
- Current document versions are preserved in version history
- Metadata fields on the document set item are also restored
- Permissions are NOT restored (current permissions remain)

### SDK Examples

**PowerShell**:
```powershell
Restore-MgSiteListItemDocumentSetVersion -SiteId $siteId -ListId $listId -ListItemId $itemId -DocumentSetVersionId $versionId
```

**C#**:
```csharp
await graphClient.Sites["{site-id}"].Lists["{list-id}"]
    .Items["{item-id}"].DocumentSetVersions["{version-id}"]
    .Restore.PostAsync();
```

**Python**:
```python
await graph_client.sites.by_site_id('site-id').lists.by_list_id('list-id').items.by_list_item_id('item-id').document_set_versions.by_document_set_version_id('version-id').restore.post()
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid parameters or item is not a document set
- **401 Unauthorized** - Missing or invalid authentication token
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Item or version does not exist
- **429 Too Many Requests** - Rate limit exceeded

### Error Response Format

```json
{
  "error": {
    "code": "invalidRequest",
    "message": "The item is not a document set.",
    "innerError": {
      "request-id": "guid",
      "date": "datetime"
    }
  }
}
```

## Throttling Considerations [VERIFIED]

**Best Practices**:
- Cache analytics results (data has 24-48h delay anyway)
- Limit getActivitiesByInterval to necessary date ranges
- Use $select to reduce payload size

**Resource Units**:
- Analytics GET: ~1 resource unit
- getActivitiesByInterval: ~2-5 resource units (depends on range)
- Document set version operations: ~2 resource units

## Document Set Prerequisites [VERIFIED]

Document set version APIs only work with items that:
1. Are based on the Document Set content type
2. Exist in a document library (not a generic list)
3. Have the Document Set feature enabled on the site

To check if an item is a document set:
```http
GET /sites/{id}/lists/{id}/items/{id}?$expand=contentType
```

Look for `contentType.id` starting with `0x0120D520` (Document Set base content type).

## Sources

- **MSGRAPH-LIADV-SC-01**: https://learn.microsoft.com/en-us/graph/api/itemanalytics-get?view=graph-rest-1.0
- **MSGRAPH-LIADV-SC-02**: https://learn.microsoft.com/en-us/graph/api/itemactivitystat-getactivitybyinterval?view=graph-rest-1.0
- **MSGRAPH-LIADV-SC-03**: https://learn.microsoft.com/en-us/graph/api/listitem-list-documentsetversions?view=graph-rest-1.0
- **MSGRAPH-LIADV-SC-04**: https://learn.microsoft.com/en-us/graph/api/listitem-post-documentsetversions?view=graph-rest-1.0
- **MSGRAPH-LIADV-SC-05**: https://learn.microsoft.com/en-us/graph/api/documentsetversion-restore?view=graph-rest-1.0

## Document History

**[2026-01-28 18:20]**
- Initial creation with 5 ListItem advanced endpoints
- Full JSON request/response examples
- SDK examples for PowerShell, C#, JavaScript, Python
- Document set prerequisites documented
