# INFO: Microsoft Graph API - Search Methods

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for Microsoft Search API methods for SharePoint/OneDrive content
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_MSGRAPH-IN00_TOC.md [MSGRAPH-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Build enterprise search portals across SharePoint and OneDrive
- Implement document discovery with faceted filtering (file type, date, author)
- Create compliance and eDiscovery solutions searching for sensitive content
- Build intelligent document recommendations based on search relevance
- Implement "search within folder" functionality in custom apps
- Find content using KQL property filters (filetype, path, author, dates)

**Key findings**:
- Search API requires delegated permissions - no app-only for most entity types
- Sites.Selected permission does NOT work with Search API - use Sites.Read.All instead
- Results respect user permissions - users see only what they can access
- KQL syntax supported for advanced queries (AND, OR, property filters)
- Maximum 1000 results per request; use pagination for larger result sets
- Drive search simpler but limited to single drive; Search API spans M365
- Aggregations enable faceted search (group by file type, date ranges)

## Quick Reference Summary

**Endpoints covered**: 3 search-related methods

- `POST /search/query` - Search across Microsoft 365 content
- `GET /drives/{id}/root/search(q='{query}')` - Search within a drive
- Query templates and KQL syntax

**Permissions required**:
- Delegated: `Files.Read.All`, `Sites.Read.All` (for SharePoint/OneDrive content)
- Application: Not supported for most entity types
- **Note**: Search runs in context of signed-in user; results respect item permissions

**Entity Types for SharePoint/OneDrive**:
- `driveItem` - Files and folders in OneDrive/SharePoint
- `listItem` - SharePoint list items
- `list` - SharePoint lists
- `site` - SharePoint sites
- `drive` - Drives (document libraries)

## 1. POST /search/query - Microsoft Search API

### Description [VERIFIED]

Searches across Microsoft 365 content including SharePoint and OneDrive. Results are scoped to items the user has access to. Supports KQL (Keyword Query Language) for advanced queries.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/search/query
```

### Request Headers

- **Authorization**: `Bearer {token}`
- **Content-Type**: `application/json`

### Request Body

```json
{
  "requests": [
    {
      "entityTypes": ["driveItem | listItem | list | site | drive"],
      "query": {
        "queryString": "string",
        "queryTemplate": "string"
      },
      "from": 0,
      "size": 25,
      "fields": ["string"],
      "sortProperties": [
        {
          "name": "string",
          "isDescending": false
        }
      ],
      "aggregations": [
        {
          "field": "string",
          "size": 10,
          "bucketDefinition": {}
        }
      ],
      "aggregationFilters": ["string"],
      "collapseProperties": [
        {
          "fields": ["string"],
          "limit": 1
        }
      ],
      "region": "string"
    }
  ]
}
```

### Request Properties [VERIFIED]

- **entityTypes** (`string[]`, required) - Types to search: `driveItem`, `listItem`, `list`, `site`, `drive`
- **query.queryString** (`string`, required) - Search query (supports KQL)
- **query.queryTemplate** (`string`) - Query template with placeholders
- **from** (`int32`) - 0-based starting index for pagination (default: 0)
- **size** (`int32`) - Number of results per page (default: 25, max: 1000)
- **fields** (`string[]`) - Properties to return in results
- **sortProperties** - Sort order for results
- **aggregations** - Faceted search aggregations
- **aggregationFilters** - Filters based on aggregation values
- **collapseProperties** - Group similar results
- **region** - Geographic region hint

### Search DriveItems Example

```http
POST https://graph.microsoft.com/v1.0/search/query
Authorization: Bearer {token}
Content-Type: application/json

{
  "requests": [
    {
      "entityTypes": ["driveItem"],
      "query": {
        "queryString": "contoso budget"
      },
      "from": 0,
      "size": 25
    }
  ]
}
```

### Response JSON [VERIFIED]

```json
{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#search",
  "value": [
    {
      "searchTerms": ["contoso", "budget"],
      "hitsContainers": [
        {
          "total": 42,
          "moreResultsAvailable": true,
          "hits": [
            {
              "hitId": "FlULeN/ui/1GjLx1rUfio5UAAEl",
              "rank": 1,
              "summary": "<c0>Contoso</c0> <c0>Budget</c0> Report 2026...",
              "resource": {
                "@odata.type": "#microsoft.graph.driveItem",
                "createdDateTime": "2026-01-15T10:30:00Z",
                "lastModifiedDateTime": "2026-01-20T14:45:00Z",
                "name": "Contoso Budget 2026.xlsx",
                "webUrl": "https://contoso.sharepoint.com/sites/finance/budget.xlsx",
                "createdBy": {
                  "user": {
                    "displayName": "John Doe"
                  }
                },
                "lastModifiedBy": {
                  "user": {
                    "displayName": "Jane Smith"
                  }
                },
                "parentReference": {
                  "siteId": "contoso.sharepoint.com,site-guid,web-guid",
                  "driveId": "drive-guid",
                  "sharepointIds": {
                    "listId": "list-guid",
                    "listItemId": "123",
                    "listItemUniqueId": "item-guid"
                  }
                }
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### Search ListItems Example

```http
POST https://graph.microsoft.com/v1.0/search/query
Authorization: Bearer {token}
Content-Type: application/json

{
  "requests": [
    {
      "entityTypes": ["listItem"],
      "query": {
        "queryString": "project status:active"
      },
      "fields": ["title", "status", "assignedTo"]
    }
  ]
}
```

### Search Sites Example

```http
POST https://graph.microsoft.com/v1.0/search/query
Authorization: Bearer {token}
Content-Type: application/json

{
  "requests": [
    {
      "entityTypes": ["site"],
      "query": {
        "queryString": "marketing"
      }
    }
  ]
}
```

### Search All SharePoint/OneDrive Content

```http
POST https://graph.microsoft.com/v1.0/search/query
Authorization: Bearer {token}
Content-Type: application/json

{
  "requests": [
    {
      "entityTypes": ["driveItem", "listItem", "list", "site"],
      "query": {
        "queryString": "annual report"
      }
    }
  ]
}
```

## 2. KQL (Keyword Query Language) Support [VERIFIED]

### Basic Operators

- **AND** - Both terms required: `budget AND 2026`
- **OR** - Either term: `budget OR forecast`
- **NOT** - Exclude term: `budget NOT draft`
- **Quotes** - Exact phrase: `"annual budget"`
- **Wildcards** - Partial match: `bud*` (prefix only)

### Property Filters

```
filetype:docx
filetype:xlsx OR filetype:csv
path:"https://contoso.sharepoint.com/sites/finance"
author:"John Doe"
filename:budget
contentclass:STS_ListItem
isDocument:true
```

### Date Filters

```
LastModifiedTime > 2026-01-01
Created > 2026-01-01 AND Created < 2026-02-01
LastModifiedTime >= 2025-12-01
```

### Combined Example

```json
{
  "query": {
    "queryString": "budget filetype:xlsx (LastModifiedTime > 2026-01-01) path:\"https://contoso.sharepoint.com/sites/finance\""
  }
}
```

## 3. GET /drives/{id}/root/search - Drive Search

### Description [VERIFIED]

Searches for items within a specific drive matching the query. Simpler than the Search API but limited to a single drive.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/drives/{driveId}/root/search(q='{searchText}')
```

Alternative paths:
```http
GET https://graph.microsoft.com/v1.0/me/drive/root/search(q='{searchText}')
GET https://graph.microsoft.com/v1.0/sites/{siteId}/drive/root/search(q='{searchText}')
GET https://graph.microsoft.com/v1.0/groups/{groupId}/drive/root/search(q='{searchText}')
```

### Path Parameters

- **driveId** (`string`) - Drive identifier
- **q** (`string`) - Search query text

### Query Parameters

- **$select** - Properties to return
- **$top** - Limit results
- **$skipToken** - Pagination token

### Request Example

```http
GET https://graph.microsoft.com/v1.0/me/drive/root/search(q='quarterly report')
Authorization: Bearer {token}
```

### Response JSON [VERIFIED]

```json
{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#Collection(driveItem)",
  "value": [
    {
      "id": "item-guid",
      "name": "Q1 Quarterly Report.docx",
      "webUrl": "https://contoso-my.sharepoint.com/personal/user/Documents/Q1 Report.docx",
      "file": {
        "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
      },
      "searchResult": {
        "onClickTelemetryUrl": "https://..."
      }
    }
  ]
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Files
Search-MgDrive -DriveId $driveId -Q "budget report"
```

**C#**:
```csharp
var results = await graphClient.Drives["{drive-id}"]
    .Root
    .Search("quarterly report")
    .GetAsync();
```

**JavaScript**:
```javascript
let results = await client.api("/me/drive/root/search(q='quarterly report')").get();
```

**Python**:
```python
results = await graph_client.drives.by_drive_id('drive-id').root.search_with_q('report').get()
```

## Pagination [VERIFIED]

### Search API Pagination

```json
{
  "requests": [
    {
      "entityTypes": ["driveItem"],
      "query": { "queryString": "budget" },
      "from": 0,
      "size": 25
    }
  ]
}
```

**Page 2**:
```json
{
  "from": 25,
  "size": 25
}
```

**Limits**:
- Maximum `size`: 1000 for SharePoint/OneDrive
- Recommended starting `size`: 25
- Increase page size progressively for better performance

### Drive Search Pagination

Use `$top` and `@odata.nextLink`:

```http
GET /me/drive/root/search(q='report')?$top=25
```

Follow `@odata.nextLink` in response for next page.

## Aggregations (Faceted Search) [VERIFIED]

### Request with Aggregations

```json
{
  "requests": [
    {
      "entityTypes": ["driveItem"],
      "query": { "queryString": "report" },
      "aggregations": [
        {
          "field": "fileType",
          "size": 10
        },
        {
          "field": "lastModifiedTime",
          "size": 5,
          "bucketDefinition": {
            "sortBy": "keyAsString",
            "isDescending": true,
            "minimumCount": 0,
            "ranges": [
              { "from": "2026-01-01" },
              { "from": "2025-07-01", "to": "2025-12-31" },
              { "to": "2025-06-30" }
            ]
          }
        }
      ]
    }
  ]
}
```

### Aggregation Response

```json
{
  "hitsContainers": [
    {
      "aggregations": [
        {
          "field": "fileType",
          "buckets": [
            { "key": "docx", "count": 45 },
            { "key": "xlsx", "count": 32 },
            { "key": "pdf", "count": 18 }
          ]
        }
      ]
    }
  ]
}
```

## Sort Properties [VERIFIED]

```json
{
  "requests": [
    {
      "entityTypes": ["driveItem"],
      "query": { "queryString": "report" },
      "sortProperties": [
        {
          "name": "lastModifiedDateTime",
          "isDescending": true
        }
      ]
    }
  ]
}
```

**Sortable properties**: `lastModifiedDateTime`, `createdDateTime`, `name`, `size`

## Collapse Properties (Deduplication) [VERIFIED]

Group similar results to reduce redundancy:

```json
{
  "requests": [
    {
      "entityTypes": ["driveItem"],
      "query": { "queryString": "report" },
      "collapseProperties": [
        {
          "fields": ["parentReference/driveId"],
          "limit": 3
        }
      ]
    }
  ]
}
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid query syntax or parameters
- **401 Unauthorized** - Missing or invalid token
- **403 Forbidden** - Insufficient permissions
- **429 Too Many Requests** - Rate limit exceeded
- **503 Service Unavailable** - Search service temporarily unavailable

### Error Response Format

```json
{
  "error": {
    "code": "InvalidRequest",
    "message": "The query string contains invalid syntax.",
    "innerError": {
      "request-id": "guid",
      "date": "2026-01-28T12:00:00Z"
    }
  }
}
```

## Known Limitations [VERIFIED]

- Search API requires delegated permissions (no app-only for most entity types)
- Results respect user's access permissions
- Custom properties in listItem require explicit `fields` specification
- Schema changed in beta version (some properties renamed/removed)
- Maximum 1000 results per request for SharePoint/OneDrive

## Throttling Considerations [VERIFIED]

**Best Practices**:
- Start with smaller page sizes (25)
- Implement exponential backoff for 429 errors
- Cache frequently searched terms
- Use aggregation filters to narrow results

**Resource Units**:
- Search query: ~5-10 resource units depending on complexity
- Drive search: ~2-3 resource units

## Sources

- **MSGRAPH-SRCH-SC-01**: https://learn.microsoft.com/en-us/graph/search-concept-files
- **MSGRAPH-SRCH-SC-02**: https://learn.microsoft.com/en-us/graph/api/resources/search-api-overview?view=graph-rest-1.0
- **MSGRAPH-SRCH-SC-03**: https://learn.microsoft.com/en-us/graph/api/driveitem-search?view=graph-rest-1.0

## Document History

**[2026-01-28 19:05]**
- Initial creation with 3 search methods
- Added KQL syntax documentation
- Added aggregations and sort properties
- Added pagination patterns
