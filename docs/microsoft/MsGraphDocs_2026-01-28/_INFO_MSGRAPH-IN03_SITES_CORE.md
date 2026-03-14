# INFO: Microsoft Graph API - Site Core Methods

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for Site API core methods with request/response JSON and examples
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

## Quick Reference Summary

**Endpoints covered**: 7 core Site API methods

- `GET /sites/root` - Get tenant root site
- `GET /sites/{site-id}` - Get site by composite ID
- `GET /sites/{hostname}:/{server-relative-path}` - Get site by URL path
- `GET /sites/getAllSites` - List all sites across geographies (App-only)
- `GET /sites?search={query}` - Search for sites by keyword
- `GET /sites/{site-id}/sites` - List subsites
- `GET /groups/{group-id}/sites/root` - Get Microsoft 365 group's team site

**Permissions required**:
- Delegated: `Sites.Read.All`, `Sites.ReadWrite.All`, `Sites.Selected`
- Application: `Sites.Read.All`, `Sites.ReadWrite.All`, `Sites.Selected`
- **Least privilege**: Use `Sites.Selected` for single-site access (requires explicit permission grant via POST to `/sites/{id}/permissions`)
- Note: `Sites.Selected` NOT supported for search endpoint

**Site ID format**: `{hostname},{site-collection-id},{site-id}`
- Example: `contoso.sharepoint.com,2C712604-1370-44E7-A1F5-426573FDA80A,2D2244C3-251A-49EA-93A8-39E1C3A060FE`

## Site Resource Type

### JSON Schema [VERIFIED]

```json
{
  "id": "string",
  "isPersonalSite": "bool",
  "displayName": "string",
  "name": "string",
  "description": "string",
  "webUrl": "url",
  "createdDateTime": "datetime",
  "lastModifiedDateTime": "datetime",
  "eTag": "string",
  "root": { "@odata.type": "microsoft.graph.root" },
  "sharepointIds": { "@odata.type": "microsoft.graph.sharepointIds" },
  "siteCollection": { "@odata.type": "microsoft.graph.siteCollection" }
}
```

### Properties [VERIFIED]

- **id** - Composite identifier: `{hostname},{siteCollection-id},{site-id}`
- **isPersonalSite** - Boolean indicating if this is a OneDrive personal site. Personal sites are user OneDrives, accessed via `/users/{id}/drive` or `/me/drive`
- **displayName** - Human-readable title of the site
- **name** - URL-safe name (slug) of the site
- **description** - Site description text
- **webUrl** - Full URL to access the site in browser
- **createdDateTime** - ISO 8601 timestamp when site was created
- **lastModifiedDateTime** - ISO 8601 timestamp of last modification
- **eTag** - Entity tag for optimistic concurrency
- **root** - Present only on root sites (empty object `{}`)
- **sharepointIds** - SharePoint-specific identifiers for REST API interop:
  ```json
  {
    "siteId": "guid",
    "siteUrl": "https://contoso.sharepoint.com/sites/team",
    "webId": "guid",
    "listId": "guid",
    "tenantId": "guid"
  }
  ```
- **siteCollection** - Site collection metadata (hostname, dataLocationCode for multi-geo)

### Relationships (expandable via $expand)

- **analytics** - `itemAnalytics` resource
- **columns** - Collection of `columnDefinition`
- **contentTypes** - Collection of `contentType`
- **drive** - Default document library (`drive`)
- **drives** - All document libraries (`drive` collection)
- **items** - Collection of `baseItem`
- **lists** - Collection of `list`
- **operations** - Long-running operations (`richLongRunningOperation`)
- **pages** - Site pages (`baseSitePage`)
- **permissions** - Site permissions (`permission` collection)
- **sites** - Subsites (`site` collection)
- **termStore** - Default term store
- **termStores** - All term stores

## 1. GET /sites/root - Get Tenant Root Site

### Description [VERIFIED]

Returns the root SharePoint site for the tenant. This is the top-level site collection.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/root
```

Alternative:
```http
GET https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com
```

### Request Headers

- **Authorization**: `Bearer {token}`
- **Accept**: `application/json`

### Request Body

None.

### Response JSON [VERIFIED]

```json
{
  "id": "contoso.sharepoint.com,2C712604-1370-44E7-A1F5-426573FDA80A,2D2244C3-251A-49EA-93A8-39E1C3A060FE",
  "isPersonalSite": false,
  "displayName": "Contoso",
  "name": "root",
  "createdDateTime": "2017-05-09T20:56:00Z",
  "lastModifiedDateTime": "2017-05-09T20:56:01Z",
  "webUrl": "https://contoso.sharepoint.com",
  "root": {},
  "siteCollection": {
    "hostName": "contoso.sharepoint.com",
    "root": {}
  }
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Sites
Get-MgSite -SiteId "root"
```

**C#**:
```csharp
var result = await graphClient.Sites["root"].GetAsync();
```

**JavaScript**:
```javascript
let site = await client.api('/sites/root').get();
```

**Python**:
```python
result = await graph_client.sites.by_site_id('root').get()
```

## 2. GET /sites/{site-id} - Get Site by ID

### Description [VERIFIED]

Retrieves a specific site by its composite site ID.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}
```

### Path Parameters

- **site-id** (`string`) - Composite ID: `{hostname},{siteCollection-id},{site-id}`

### Request Example

```http
GET https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,2C712604-1370-44E7-A1F5-426573FDA80A,2D2244C3-251A-49EA-93A8-39E1C3A060FE
```

### Response JSON [VERIFIED]

```json
{
  "id": "contoso.sharepoint.com,2C712604-1370-44E7-A1F5-426573FDA80A,2D2244C3-251A-49EA-93A8-39E1C3A060FE",
  "isPersonalSite": false,
  "displayName": "OneDrive Team Site",
  "name": "1drvteam",
  "createdDateTime": "2017-05-09T20:56:00Z",
  "lastModifiedDateTime": "2017-05-09T20:56:01Z",
  "webUrl": "https://contoso.sharepoint.com/teams/1drvteam"
}
```

### OData Query Parameters

- **$select** - `$select=id,displayName,webUrl` - Return only specified properties
- **$expand** - `$expand=drives,lists` - Include related resources

**Common OData Patterns**:
```http
# Minimal response
GET /sites/{id}?$select=id,displayName,webUrl

# Include document libraries
GET /sites/{id}?$expand=drives

# Include lists with selected properties
GET /sites/{id}?$expand=lists($select=id,displayName,webUrl)

# Include default drive with quota info
GET /sites/{id}?$expand=drive($select=id,webUrl,quota)
```

### SDK Examples

**PowerShell**:
```powershell
Get-MgSite -SiteId "contoso.sharepoint.com,2C712604-1370-44E7-A1F5-426573FDA80A,2D2244C3-251A-49EA-93A8-39E1C3A060FE"
```

**C#**:
```csharp
var result = await graphClient.Sites["{site-id}"].GetAsync();
```

## 3. GET /sites/{hostname}:/{server-relative-path} - Get Site by Path

### Description [VERIFIED]

Retrieves a site using its hostname and server-relative URL path. Useful when you know the site URL but not the composite ID.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{hostname}:/{relative-path}
```

### Path Parameters

- **hostname** (`string`) - SharePoint tenant hostname (e.g., `contoso.sharepoint.com`)
- **relative-path** (`string`) - Server-relative path to site (e.g., `teams/marketing`)

### Request Example

```http
GET https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com:/teams/1drvteam
```

### Response JSON [VERIFIED]

```json
{
  "id": "contoso.sharepoint.com,2C712604-1370-44E7-A1F5-426573FDA80A,2D2244C3-251A-49EA-93A8-39E1C3A060FE",
  "isPersonalSite": false,
  "displayName": "OneDrive Team Site",
  "name": "1drvteam",
  "createdDateTime": "2017-05-09T20:56:00Z",
  "lastModifiedDateTime": "2017-05-09T20:56:01Z",
  "webUrl": "https://contoso.sharepoint.com/teams/1drvteam"
}
```

### Common Path Patterns

- **Team site** - `/teams/{site-name}`
- **Communication site** - `/sites/{site-name}`
- **Hub site** - `/sites/{hub-name}`
- **Project site** - `/sites/{project-name}`

### SDK Examples

**JavaScript**:
```javascript
let site = await client.api('/sites/contoso.sharepoint.com:/teams/marketing').get();
```

## 4. GET /sites/getAllSites - List All Sites

### Description [VERIFIED]

Lists all sites across all geographies in the organization. Returns paginated results with `@odata.nextLink` for continuation. **Application permission only**.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/getAllSites
```

### Permissions [VERIFIED]

- **Delegated**: Not supported
- **Application**: `Sites.Read.All`, `Sites.ReadWrite.All`

### Request Headers

- **Authorization**: `Bearer {token}`
- **Accept**: `application/json`

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "contoso-apc.sharepoint.com,bf6fb551-d508-4946-a439-b2a6154fc1d9,65a04b8b-1f44-442b-a1fc-9e5852fb946c",
      "name": "Root Site",
      "isPersonalSite": false,
      "root": {},
      "siteCollection": {
        "hostName": "contoso-apc.sharepoint.com",
        "dataLocationCode": "APC",
        "root": {}
      },
      "webUrl": "https://contoso-apc.sharepoint.com"
    },
    {
      "id": "contoso-apc.sharepoint.com,d9ecf079-9b13-4376-ac5d-f242dda55626,746dbcc1-fa2b-4120-b657-2670bae5bb6f",
      "name": "Site A",
      "isPersonalSite": false,
      "root": {},
      "siteCollection": {
        "hostName": "contoso-apc.sharepoint.com"
      },
      "webUrl": "https://contoso-apc.sharepoint.com/sites/siteA"
    }
  ],
  "@odata.nextLink": "https://graph.microsoft.com/v1.0/sites/getAllSites?$skiptoken=U1BHZW9EYXRhTG9jYXRpb25Db2RlYU5BTQ"
}
```

### Pagination [VERIFIED]

- Response includes `@odata.nextLink` when more pages exist
- Continue requesting `@odata.nextLink` URL until no more pages
- `dataLocationCode` in `siteCollection` indicates geographic location for multi-geo tenants

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Sites
Get-MgAllSite
```

**C#**:
```csharp
var result = await graphClient.Sites.GetAllSites.GetAsGetAllSitesGetResponseAsync();
```

**Python**:
```python
result = await graph_client.sites.get_all_sites.get()
```

## 5. GET /sites?search={query} - Search for Sites

### Description [VERIFIED]

Searches across a SharePoint tenant for sites matching the provided keywords. Uses free-text search across multiple properties.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites?search={query}
```

### Query Parameters

- **search** (`string`) - Search keywords (free-text)

### Request Example

```http
GET https://graph.microsoft.com/v1.0/sites?search=marketing
```

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "contoso.sharepoint.com,da60e844-ba1d-49bc-b4d4-d5e36bae9019,712a596e-90a1-49e3-9b48-bfa80bee8740",
      "name": "Team A Site",
      "description": "",
      "createdDateTime": "2016-10-18T03:05:59Z",
      "lastModifiedDateTime": "2016-10-18T10:40:59Z",
      "webUrl": "https://contoso.sharepoint.com/sites/siteA"
    },
    {
      "id": "contoso.sharepoint.com,da60e844-ba1d-49bc-b4d4-d5e36bae9019,0271110f-634f-4300-a841-3a8a2e851851",
      "name": "Team B Site",
      "description": "",
      "createdDateTime": "2016-10-18T03:05:59Z",
      "lastModifiedDateTime": "2016-10-18T10:40:59Z",
      "webUrl": "https://contoso.sharepoint.com/sites/siteB"
    }
  ]
}
```

### Limitations [VERIFIED]

- Only `createdDateTime` works for sorting via `$orderby`
- `Sites.Selected` permission NOT supported
- Search is free-text across multiple properties (name, description, etc.)

### SDK Examples

**PowerShell**:
```powershell
Get-MgSite -Search "marketing"
```

**C#**:
```csharp
var result = await graphClient.Sites.GetAsync((requestConfiguration) => {
    requestConfiguration.QueryParameters.Search = "marketing";
});
```

**JavaScript**:
```javascript
let sites = await client.api('/sites?search=marketing').get();
```

## 6. GET /sites/{site-id}/sites - List Subsites

### Description [VERIFIED]

Returns a collection of subsites defined under a parent site.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/sites
```

### Path Parameters

- **site-id** (`string`) - Parent site's composite ID

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "contoso.sharepoint.com,da60e844-ba1d-49bc-b4d4-d5e36bae9019,712a596e-90a1-49e3-9b48-bfa80bee8740",
      "name": "Team A Subsite",
      "isPersonalSite": false,
      "description": "",
      "createdDateTime": "2016-10-18T03:05:59Z",
      "lastModifiedDateTime": "2016-10-18T10:40:59Z",
      "webUrl": "https://contoso.sharepoint.com/sites/site/subsiteA"
    },
    {
      "id": "contoso.sharepoint.com,da60e844-ba1d-49bc-b4d4-d5e36bae9019,0271110f-634f-4300-a841-3a8a2e851851",
      "name": "Team B Subsite",
      "isPersonalSite": false,
      "description": "",
      "createdDateTime": "2016-10-18T03:05:59Z",
      "lastModifiedDateTime": "2016-10-18T10:40:59Z",
      "webUrl": "https://contoso.sharepoint.com/sites/site/subsiteB"
    }
  ]
}
```

### SDK Examples

**Python**:
```python
result = await graph_client.sites.by_site_id('site-id').sites.get()
```

**C#**:
```csharp
var result = await graphClient.Sites["{site-id}"].Sites.GetAsync();
```

## 7. GET /groups/{group-id}/sites/root - Get Group Team Site

### Description [VERIFIED]

Retrieves the team site associated with a Microsoft 365 group. Every M365 group has an associated SharePoint team site.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/groups/{group-id}/sites/root
```

### Path Parameters

- **group-id** (`string`) - Microsoft 365 group ID (GUID)

### Request Example

```http
GET https://graph.microsoft.com/v1.0/groups/2C712604-1370-44E7-A1F5-426573FDA80A/sites/root
```

### Response JSON [VERIFIED]

Same structure as other site responses - returns a `site` resource.

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Sites
Get-MgGroupSite -GroupId $groupId -SiteId "root"
```

**C#**:
```csharp
var result = await graphClient.Groups["{group-id}"].Sites["root"].GetAsync();
```

**JavaScript**:
```javascript
let site = await client.api('/groups/2C712604-1370-44E7-A1F5-426573FDA80A/sites/root').get();
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid site ID format or malformed request
- **401 Unauthorized** - Missing or invalid authentication token
- **403 Forbidden** - Insufficient permissions or access denied
- **404 Not Found** - Site does not exist or user lacks access
- **429 Too Many Requests** - Rate limit exceeded (check Retry-After header)

### Error Response Format

```json
{
  "error": {
    "code": "itemNotFound",
    "message": "The resource could not be found.",
    "innerError": {
      "request-id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "date": "2026-01-28T15:30:00"
    }
  }
}
```

## Throttling Considerations [VERIFIED]

Microsoft Graph implements throttling to protect service health. Site API calls count toward your tenant's resource unit quota.

**Throttling Behavior**:
- HTTP 429 (Too Many Requests) returned when throttled
- `Retry-After` header indicates seconds to wait before retrying
- SharePoint-specific throttling may return HTTP 503 with `Retry-After`

**Best Practices**:
- Implement exponential backoff with jitter
- Honor `Retry-After` header values
- Use `$select` to reduce response payload
- Batch multiple requests using JSON batching (`/$batch`)
- Cache site IDs after first lookup

**Resource Units**:
- Simple GET: ~1 resource unit
- GET with $expand: ~2-5 resource units depending on expansion
- Limits vary by license tier and tenant size

## Multi-Geo Considerations [VERIFIED]

- `getAllSites` returns sites across all geographies
- `siteCollection.dataLocationCode` indicates geographic location (e.g., "APC", "NAM", "EUR")
- Users accessing cross-geo sites need "Limited access" permission on target geo's root site
- Use `@odata.nextLink` pagination to iterate through all geos

## Sources

- **MSGRAPH-SITES-SC-01**: https://learn.microsoft.com/en-us/graph/api/resources/site?view=graph-rest-1.0
- **MSGRAPH-SITES-SC-02**: https://learn.microsoft.com/en-us/graph/api/site-get?view=graph-rest-1.0
- **MSGRAPH-SITES-SC-03**: https://learn.microsoft.com/en-us/graph/api/site-getbypath?view=graph-rest-1.0
- **MSGRAPH-SITES-SC-04**: https://learn.microsoft.com/en-us/graph/api/site-getallsites?view=graph-rest-1.0
- **MSGRAPH-SITES-SC-05**: https://learn.microsoft.com/en-us/graph/api/site-search?view=graph-rest-1.0
- **MSGRAPH-SITES-SC-06**: https://learn.microsoft.com/en-us/graph/api/site-list-subsites?view=graph-rest-1.0

## Document History

**[2026-01-28 17:27]**
- Changed: Converted all markdown tables to lists per workspace conventions
- Removed: DevSystem tag (no longer needed)

**[2026-01-28 17:25]**
- Added: Sites.Selected permission guidance (least privilege)
- Added: sharepointIds expanded JSON structure
- Added: Practical OData $expand/$select examples
- Added: Throttling Considerations section
- Added: Personal site clarification (OneDrive access paths)
- Reconcile: 6 confirmed, 4 dismissed from RV01 review

**[2026-01-28 17:30]**
- Initial creation with 7 core Site API endpoints
- Full JSON request/response examples
- SDK examples for PowerShell, C#, JavaScript, Python
- Error handling and multi-geo considerations documented
