# INFO: SharePoint REST API - Search

**Doc ID**: SPAPI-IN01
**Goal**: Detailed reference for SharePoint Search REST API endpoints with request/response JSON and KQL syntax
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_SHAREPOINT_API_TOC.md [SPAPI-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Search SharePoint content (sites, lists, files, pages)
- Implement search-driven applications
- Build search refiners and faceted navigation
- Provide query suggestions/autocomplete
- Content discovery for compliance and eDiscovery
- Build custom search portals
- Power enterprise knowledge management

**Key findings**:
- Two endpoints: `/_api/search/query` (GET) and `/_api/search/postquery` (POST) [VERIFIED]
- Suggest endpoint for autocomplete: `/_api/search/suggest` [VERIFIED]
- KQL (Keyword Query Language) is the query syntax [VERIFIED]
- StartRow max is 50,000 for performance [VERIFIED]
- POST required for ReorderingRules and complex parameters [VERIFIED]
- **Gotcha**: Security trimming means users only see results they have access to - may hide expected results [VERIFIED]
- **Gotcha**: App-only (Sites.Read.All) search has specific throttling limits [VERIFIED]
- **Gotcha**: Crawled content may be delayed 15-60 minutes for indexing [VERIFIED]

## Quick Reference Summary

**Endpoints covered**: 4 search endpoints

- `GET /_api/search/query?querytext='{query}'` - Search with GET
- `POST /_api/search/postquery` - Search with POST
- `GET /_api/search/suggest?querytext='{query}'` - Query suggestions
- `POST /_api/search/suggest` - Query suggestions (POST)

**Permissions required**:
- Application: `Sites.Read.All` (search indexed content)
- Delegated: `Sites.Read.All` (search as user)
- Note: Search respects security trimming - users only see results they have access to

## 1. GET /_api/search/query - Search with GET

### Description [VERIFIED]

Executes a search query using URL parameters.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/search/query?querytext='{search_term}'
```

### Query Parameters [VERIFIED]

**Core Parameters**:
- **querytext** - KQL query string (required)
- **selectproperties** - Comma-separated managed properties to return
- **startrow** - First row for paging (0-based, max 50,000)
- **rowlimit** - Max rows returned (default 10, max 500)
- **rowsperpage** - Rows per page for paging

**Query Modification**:
- **querytemplate** - Template with `{searchterms}` placeholder
- **sourceid** - Result source GUID
- **rankingmodelid** - Custom ranking model GUID
- **culture** - Locale ID (LCID)

**Refinement**:
- **refiners** - Comma-separated refiner specs
- **refinementfilters** - Refiner filter values

**Sorting**:
- **sortlist** - Sort specification

**Display Options**:
- **trimduplicates** - Remove duplicates (default true)
- **enablestemming** - Enable word stemming
- **hithighlightedproperties** - Properties to highlight

### Request Example

```http
GET https://contoso.sharepoint.com/_api/search/query?querytext='sharepoint'&selectproperties='Title,Path,Author'&rowlimit=20
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "query": {
      "PrimaryQueryResult": {
        "RelevantResults": {
          "Table": {
            "Rows": {
              "results": [
                {
                  "Cells": {
                    "results": [
                      { "Key": "Title", "Value": "SharePoint Guide" },
                      { "Key": "Path", "Value": "https://contoso.sharepoint.com/sites/..." },
                      { "Key": "Author", "Value": "John Smith" }
                    ]
                  }
                }
              ]
            }
          },
          "TotalRows": 150,
          "TotalRowsIncludingDuplicates": 175
        }
      }
    }
  }
}
```

## 2. POST /_api/search/postquery - Search with POST

### Description [VERIFIED]

Executes a search query using JSON body. Required for complex queries and ReorderingRules.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/search/postquery
```

### Request Body [VERIFIED]

```json
{
  "request": {
    "__metadata": {
      "type": "Microsoft.Office.Server.Search.REST.SearchRequest"
    },
    "Querytext": "sharepoint",
    "SelectProperties": {
      "results": ["Title", "Path", "Author", "LastModifiedTime"]
    },
    "RowLimit": 50,
    "StartRow": 0,
    "TrimDuplicates": true,
    "EnableStemming": true
  }
}
```

### Request Body - With Refiners

```json
{
  "request": {
    "__metadata": {
      "type": "Microsoft.Office.Server.Search.REST.SearchRequest"
    },
    "Querytext": "sharepoint",
    "Refiners": "FileType,Author(filter=100/0/*)",
    "RefinementFilters": {
      "results": ["FileType:equals(\"docx\")"]
    }
  }
}
```

### Request Body - With Sort

```json
{
  "request": {
    "__metadata": {
      "type": "Microsoft.Office.Server.Search.REST.SearchRequest"
    },
    "Querytext": "sharepoint",
    "SortList": {
      "results": [
        {
          "Property": "LastModifiedTime",
          "Direction": 1
        }
      ]
    }
  }
}
```

**Sort Direction**: 0=Ascending, 1=Descending

## 3. GET /_api/search/suggest - Query Suggestions

### Description [VERIFIED]

Returns query suggestions for autocomplete functionality.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/search/suggest?querytext='{partial_query}'
```

### Query Parameters

- **querytext** - Partial query string
- **count** - Number of suggestions (default 5)
- **personalcount** - Personal suggestions count
- **showpeoplenamesuggestions** - Include people names

### Request Example

```http
GET https://contoso.sharepoint.com/_api/search/suggest?querytext='share'&count=10
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "suggest": {
      "Queries": {
        "results": [
          { "Query": "sharepoint" },
          { "Query": "sharepoint online" },
          { "Query": "sharepoint permissions" }
        ]
      },
      "PeopleNames": {
        "results": []
      }
    }
  }
}
```

## 4. POST /_api/search/suggest - Query Suggestions (POST)

### Request Body

```json
{
  "request": {
    "__metadata": {
      "type": "Microsoft.Office.Server.Search.REST.SearchRequest"
    },
    "Querytext": "share",
    "Count": 10,
    "ShowPeopleNameSuggestions": true
  }
}
```

## KQL (Keyword Query Language) Reference [VERIFIED]

### Property Restrictions

```
property:value
property=value
property<>value
property>value
property>=value
```

### Common Properties

- **Title** - Document title
- **Author** - Author name
- **Path** - Full URL path
- **FileExtension** - File type (docx, xlsx, etc.)
- **ContentType** - Content type name
- **LastModifiedTime** - Last modified date
- **Created** - Created date
- **Size** - File size in bytes
- **SiteName** - Site name
- **ListId** - List GUID

### Boolean Operators

```
sharepoint AND online
sharepoint OR teams
sharepoint NOT onpremises
sharepoint -onpremises
```

### Wildcards

```
share*          (prefix wildcard)
*point          (suffix wildcard - limited support)
```

### Phrases

```
"sharepoint online"     (exact phrase)
```

### Date Queries

```
LastModifiedTime>2024-01-01
LastModifiedTime>=2024-01-01T00:00:00Z
Created:today
Created:thisweek
Created:thismonth
```

### Range Queries

```
Size>1000000                    (files > 1MB)
LastModifiedTime:2024-01-01..2024-12-31
```

### Example Queries

```
FileExtension:docx Author:John
contenttype:"Document" Path:"/sites/teamsite/*"
Title:budget AND LastModifiedTime>2024-01-01
IsDocument:true -FileExtension:aspx
```

## Common Managed Properties [VERIFIED]

- **Title** - Item title
- **Path** - Full URL
- **Filename** - File name only
- **FileExtension** - Extension without dot
- **ContentType** - Content type
- **Author** - Author display name
- **LastModifiedTime** - Modified date/time
- **Created** - Created date/time
- **Size** - File size (bytes)
- **IsDocument** - Is a document (true/false)
- **IsContainer** - Is a container (folder/list)
- **SiteName** - Site title
- **SiteTitle** - Site title
- **ListId** - List GUID
- **WebId** - Web GUID
- **SiteId** - Site collection GUID

## Pagination [VERIFIED]

### Standard Pagination (up to 50,000 results)

```http
# Page 1
GET /_api/search/query?querytext='*'&startrow=0&rowlimit=50

# Page 2
GET /_api/search/query?querytext='*'&startrow=50&rowlimit=50
```

### Large Result Sets (beyond 50,000)

For results beyond StartRow 50,000, use sorting with a unique property:

```json
{
  "request": {
    "Querytext": "*",
    "RowLimit": 500,
    "SortList": {
      "results": [{ "Property": "IndexDocId", "Direction": 0 }]
    }
  }
}
```

## Error Responses

- **400** - Invalid KQL syntax
- **401** - Unauthorized
- **403** - Search not enabled or insufficient permissions
- **500** - Search service error

## SDK Examples

**PnP PowerShell**:
```powershell
Connect-PnPOnline -Url "https://contoso.sharepoint.com" -Interactive
Submit-PnPSearchQuery -Query "sharepoint" -MaxResults 100
Submit-PnPSearchQuery -Query "FileExtension:docx" -SelectProperties "Title,Path,Author"
```

**PnP JavaScript** (v4.x):
```javascript
import { spfi } from "@pnp/sp";
import "@pnp/sp/search";
const sp = spfi(...);

const results = await sp.search({
  Querytext: "sharepoint",
  SelectProperties: ["Title", "Path", "Author"],
  RowLimit: 50
});

const suggestions = await sp.searchSuggest({
  querytext: "share"
});
```

## Sources

- **SPAPI-SEARCH-SC-01**: https://learn.microsoft.com/en-us/sharepoint/dev/general-development/sharepoint-search-rest-api-overview
- **SPAPI-SEARCH-SC-02**: https://learn.microsoft.com/en-us/sharepoint/dev/general-development/keyword-query-language-kql-syntax-reference

## Document History

**[2026-01-28 19:45]**
- Added critical gotchas (security trimming, app-only throttling, indexing delay)
- Enhanced use cases with practical scenarios

**[2026-01-28 19:55]**
- Initial creation with 4 endpoints
- Documented query and suggest endpoints
- Added KQL syntax reference
- Documented common managed properties
