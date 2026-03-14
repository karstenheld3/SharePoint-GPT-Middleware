# INFO: Microsoft Graph API - Site Management Methods

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for Site management methods (delta, followed sites, analytics, permissions, operations)
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_MSGRAPH-IN00_TOC.md [MSGRAPH-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Build incremental sync solutions using delta queries to detect new/changed/deleted sites
- Track user engagement with sites via analytics (views, unique visitors)
- Implement "follow site" functionality in custom portals and apps
- Grant application-only access to specific sites using Sites.Selected pattern
- Monitor long-running operations (content type sync, bulk updates)
- Audit site permission changes for compliance and security
- Build dashboards showing site activity over custom date ranges

**Key findings**:
- Delta queries return changes since last sync; token duration not officially documented - handle 410 Gone gracefully
- Sites.Selected requires two steps: (1) Admin consents to permission, (2) POST /sites/{id}/permissions grants app access to specific site
- Analytics data has 24-48 hour delay; not suitable for real-time dashboards
- Site permissions are application-only (no delegated support) - designed for app access grants
- getActivitiesByInterval() limited to 90-day maximum date range
- Followed sites are user-specific; use delegated permissions only
- Operations endpoint returns richLongRunningOperation for async tasks like content type propagation

## Quick Reference Summary

**Endpoints covered**: 12 Site management methods

- `GET /sites/delta` - Track site changes incrementally
- `POST /users/{id}/followedSites/add` - Follow one or more sites
- `POST /users/{id}/followedSites/remove` - Unfollow one or more sites
- `GET /me/followedSites` - List sites the current user follows
- `GET /sites/{id}/analytics/allTime` - Get all-time analytics
- `GET /sites/{id}/analytics/lastSevenDays` - Get last 7 days analytics
- `GET /sites/{id}/getActivitiesByInterval()` - Get analytics by custom interval
- `GET /sites/{id}/permissions` - List site permissions
- `GET /sites/{id}/permissions/{id}` - Get specific permission
- `POST /sites/{id}/permissions` - Create site permission (app only)
- `PATCH /sites/{id}/permissions/{id}` - Update site permission
- `DELETE /sites/{id}/permissions/{id}` - Delete site permission
- `GET /sites/{id}/operations` - List long-running operations

**Permissions required**:
- Delegated: `Sites.Read.All`, `Sites.ReadWrite.All`, `Sites.Manage.All`, `Sites.FullControl.All`
- Application: `Sites.Read.All`, `Sites.ReadWrite.All`, `Sites.FullControl.All`
- **Least privilege**: `Sites.Read.All` for read operations; `Sites.FullControl.All` for permission management
- Note: Permission management requires `Sites.FullControl.All`; Delta requires App-only context

## Permission Resource Type

### JSON Schema [VERIFIED]

```json
{
  "id": "string",
  "roles": ["read", "write", "owner"],
  "grantedTo": { "@odata.type": "microsoft.graph.identitySet" },
  "grantedToIdentities": [{ "@odata.type": "microsoft.graph.identitySet" }],
  "grantedToIdentitiesV2": [{ "@odata.type": "microsoft.graph.sharePointIdentitySet" }],
  "inheritedFrom": { "@odata.type": "microsoft.graph.itemReference" },
  "@odata.type": "microsoft.graph.permission"
}
```

### Properties [VERIFIED]

- **id** - Unique identifier for the permission
- **roles** - Array of permission roles: `read`, `write`, `owner`
- **grantedTo** - Identity granted direct access (deprecated, use grantedToV2)
- **grantedToIdentities** - Collection of identities (deprecated, use grantedToIdentitiesV2)
- **grantedToIdentitiesV2** - Collection of SharePoint identities:
  ```json
  {
    "application": {
      "id": "89ea5c94-7736-4e25-95ad-3fa95f62b66e",
      "displayName": "Contoso App"
    }
  }
  ```
- **inheritedFrom** - Reference to ancestor if permission is inherited (null if direct)

## itemAnalytics Resource Type

### JSON Schema [VERIFIED]

```json
{
  "allTime": { "@odata.type": "microsoft.graph.itemActivityStat" },
  "lastSevenDays": { "@odata.type": "microsoft.graph.itemActivityStat" },
  "@odata.type": "microsoft.graph.itemAnalytics"
}
```

### itemActivityStat Properties [VERIFIED]

- **access** - Statistics about access actions:
  ```json
  {
    "actionCount": 123,
    "actorCount": 45
  }
  ```
- **startDateTime** - Start of activity period
- **endDateTime** - End of activity period

## richLongRunningOperation Resource Type

### JSON Schema [VERIFIED]

```json
{
  "id": "string",
  "createdDateTime": "datetime",
  "resourceId": "string",
  "resourceLocation": "url",
  "status": "notStarted | running | succeeded | failed",
  "type": "string",
  "error": { "@odata.type": "microsoft.graph.publicError" },
  "@odata.type": "microsoft.graph.richLongRunningOperation"
}
```

## 1. GET /sites/delta - Track Site Changes

### Description [VERIFIED]

Get newly created, updated, or deleted sites without performing a full read of the entire sites collection. Uses delta tokens for incremental sync. **Application permission only**.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/delta
```

With token:
```http
GET https://graph.microsoft.com/v1.0/sites/delta?token={token}
```

### Query Parameters

- **token** (`string`) - Delta token from previous response (optional for initial request)
- **$select** - Select specific properties
- **$expand** - Expand relationships
- **$top** - Limit results per page

### Request Headers

- **Authorization**: `Bearer {token}`
- **Accept**: `application/json`

### Request Body

None.

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "contoso.sharepoint.com,da60e844-ba1d-49bc-b4d4-d5e36bae9019,712a596e-90a1-49e3-9b48-bfa80bee8740",
      "name": "Team A Site",
      "webUrl": "https://contoso.sharepoint.com/sites/siteA",
      "siteCollection": {
        "hostName": "contoso.sharepoint.com"
      }
    }
  ],
  "@odata.nextLink": "https://graph.microsoft.com/v1.0/sites/delta?$skiptoken=...",
  "@odata.deltaLink": "https://graph.microsoft.com/v1.0/sites/delta?token=..."
}
```

### Delta Sync Pattern [VERIFIED]

1. Initial request: `GET /sites/delta` (no token)
2. Follow `@odata.nextLink` until you get `@odata.deltaLink`
3. Store `@odata.deltaLink` token
4. For changes: request `@odata.deltaLink` URL
5. Deleted items have `@removed` annotation

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Sites
Get-MgSiteDelta
```

**C#**:
```csharp
var result = await graphClient.Sites.Delta.GetAsDeltaGetResponseAsync();
```

**JavaScript**:
```javascript
let delta = await client.api('/sites/delta').get();
```

**Python**:
```python
result = await graph_client.sites.delta.get()
```

## 2. POST /users/{id}/followedSites/add - Follow Sites

### Description [VERIFIED]

Follow one or more sites for a user. Followed sites appear in the user's SharePoint home page and can be retrieved via the followedSites endpoint.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/users/{user-id}/followedSites/add
```

Or for current user:
```http
POST https://graph.microsoft.com/v1.0/me/followedSites/add
```

### Path Parameters

- **user-id** (`string`) - User ID or userPrincipalName

### Request Headers

- **Authorization**: `Bearer {token}`
- **Content-Type**: `application/json`

### Request Body

```json
{
  "value": [
    {
      "id": "contoso.sharepoint.com,da60e844-ba1d-49bc-b4d4-d5e36bae9019,712a596e-90a1-49e3-9b48-bfa80bee8740"
    },
    {
      "id": "contoso.sharepoint.com,da60e844-ba1d-49bc-b4d4-d5e36bae9019,0271110f-634f-4300-a841-3a8a2e851851"
    }
  ]
}
```

### Response JSON [VERIFIED]

Success returns array of followed sites. Partial failure returns 207 with error details:

```json
{
  "value": [
    {
      "id": "contoso.sharepoint.com,da60e844-ba1d-49bc-b4d4-d5e36bae9019,712a596e-90a1-49e3-9b48-bfa80bee8740",
      "webUrl": "https://contoso.sharepoint.com/sites/siteA",
      "name": "Site A"
    }
  ]
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Sites
$params = @{
  value = @(
    @{ id = "contoso.sharepoint.com,site-guid-1,web-guid-1" }
  )
}
Add-MgUserFollowedSite -UserId $userId -BodyParameter $params
```

**JavaScript**:
```javascript
const body = {
  value: [{ id: "contoso.sharepoint.com,site-guid-1,web-guid-1" }]
};
await client.api('/me/followedSites/add').post(body);
```

## 3. POST /users/{id}/followedSites/remove - Unfollow Sites

### Description [VERIFIED]

Unfollow one or more sites for a user. Removes sites from the user's followed sites list.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/users/{user-id}/followedSites/remove
```

Or for current user:
```http
POST https://graph.microsoft.com/v1.0/me/followedSites/remove
```

### Path Parameters

- **user-id** (`string`) - User ID or userPrincipalName

### Request Body

```json
{
  "value": [
    {
      "id": "contoso.sharepoint.com,da60e844-ba1d-49bc-b4d4-d5e36bae9019,712a596e-90a1-49e3-9b48-bfa80bee8740"
    }
  ]
}
```

### Response [VERIFIED]

- **204 No Content** - Success
- **207 Multi-Status** - Partial failure with error details

### SDK Examples

**PowerShell**:
```powershell
$params = @{
  value = @(
    @{ id = "contoso.sharepoint.com,site-guid-1,web-guid-1" }
  )
}
Remove-MgUserFollowedSite -UserId $userId -BodyParameter $params
```

## 4. GET /me/followedSites - List Followed Sites

### Description [VERIFIED]

Lists all sites the current user is following.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/me/followedSites
```

Or for specific user:
```http
GET https://graph.microsoft.com/v1.0/users/{user-id}/followedSites
```

### Request Headers

- **Authorization**: `Bearer {token}`
- **Accept**: `application/json`

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "contoso.sharepoint.com,da60e844-ba1d-49bc-b4d4-d5e36bae9019,712a596e-90a1-49e3-9b48-bfa80bee8740",
      "displayName": "Marketing Site",
      "name": "marketing",
      "webUrl": "https://contoso.sharepoint.com/sites/marketing"
    }
  ]
}
```

### SDK Examples

**PowerShell**:
```powershell
Get-MgUserFollowedSite -UserId $userId
```

**C#**:
```csharp
var result = await graphClient.Me.FollowedSites.GetAsync();
```

## 5. GET /sites/{id}/analytics/allTime - Get All-Time Analytics

### Description [VERIFIED]

Get itemAnalytics about all views that took place on a site. Returns aggregated statistics for all time.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/analytics/allTime
```

### Path Parameters

- **site-id** (`string`) - Site composite ID

### Response JSON [VERIFIED]

```json
{
  "access": {
    "actionCount": 1234,
    "actorCount": 56
  }
}
```

### Limitations [VERIFIED]

- itemAnalytics not available in all national deployments
- Only returns access (view) statistics, not edit statistics

### SDK Examples

**C#**:
```csharp
var result = await graphClient.Sites["{site-id}"].Analytics.AllTime.GetAsync();
```

## 6. GET /sites/{id}/analytics/lastSevenDays - Get Recent Analytics

### Description [VERIFIED]

Get itemAnalytics for the last seven days of activity on a site.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/analytics/lastSevenDays
```

### Response JSON [VERIFIED]

```json
{
  "startDateTime": "2026-01-21T00:00:00Z",
  "endDateTime": "2026-01-28T00:00:00Z",
  "access": {
    "actionCount": 89,
    "actorCount": 12
  }
}
```

## 7. GET /sites/{id}/getActivitiesByInterval() - Custom Interval Analytics

### Description [VERIFIED]

Get activity statistics for a site within a specified time interval. Use this for custom date ranges.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/getActivitiesByInterval(startDateTime='2026-01-01',endDateTime='2026-01-28',interval='week')
```

### Function Parameters

- **startDateTime** (`string`) - ISO 8601 start date
- **endDateTime** (`string`) - ISO 8601 end date
- **interval** (`string`) - Aggregation interval: `day`, `week`, `month`

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "startDateTime": "2026-01-01T00:00:00Z",
      "endDateTime": "2026-01-07T00:00:00Z",
      "access": {
        "actionCount": 45,
        "actorCount": 8
      }
    }
  ]
}
```

## 8. GET /sites/{id}/permissions - List Site Permissions

### Description [VERIFIED]

Get the permission resources from the permissions navigation property on a site. Returns application permissions granted to the site.

**Note**: Listing subsites' permissions is NOT supported.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/permissions
```

### Path Parameters

- **site-id** (`string`) - Site composite ID

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "1",
      "roles": ["read"],
      "grantedToIdentitiesV2": [{
        "application": {
          "id": "89ea5c94-7736-4e25-95ad-3fa95f62b66e",
          "displayName": "Contoso Time Manager App"
        }
      }]
    },
    {
      "id": "2",
      "roles": ["write"],
      "grantedToIdentitiesV2": [{
        "application": {
          "id": "22f09bb7-dd29-403e-bec2-ab5cde52c2b3",
          "displayName": "Fabrikam Dashboard App"
        }
      }]
    }
  ]
}
```

### SDK Examples

**PowerShell**:
```powershell
Get-MgSitePermission -SiteId $siteId
```

**Python**:
```python
result = await graph_client.sites.by_site_id('site-id').permissions.get()
```

## 9. GET /sites/{id}/permissions/{id} - Get Site Permission

### Description [VERIFIED]

Return the effective sharing permission for a particular permission resource on a site.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/permissions/{permission-id}
```

### Path Parameters

- **site-id** (`string`) - Site composite ID
- **permission-id** (`string`) - Permission ID

### Response JSON [VERIFIED]

```json
{
  "id": "1",
  "roles": ["read"],
  "grantedToIdentitiesV2": [{
    "application": {
      "id": "89ea5c94-7736-4e25-95ad-3fa95f62b66e",
      "displayName": "Contoso App"
    }
  }]
}
```

## 10. POST /sites/{id}/permissions - Create Site Permission

### Description [VERIFIED]

Create a new application permission on a site. **Cannot be used to create user permissions - only application permissions**.

**Note**: Requires SharePoint Administrator role in delegated workflows.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/sites/{site-id}/permissions
```

### Request Body

```json
{
  "roles": ["write"],
  "grantedTo": {
    "application": {
      "id": "89ea5c94-7736-4e25-95ad-3fa95f62b66e"
    }
  }
}
```

### Valid Roles [VERIFIED]

- **read** - Read access
- **write** - Read and write access
- **owner** - Full control (use with caution)

### Response JSON [VERIFIED]

Returns 201 Created with the permission object:

```json
{
  "id": "1",
  "roles": ["write"],
  "grantedToIdentitiesV2": [{
    "application": {
      "id": "89ea5c94-7736-4e25-95ad-3fa95f62b66e",
      "displayName": "Contoso App"
    }
  }]
}
```

### SDK Examples

**PowerShell**:
```powershell
$params = @{
  roles = @("write")
  grantedTo = @{
    application = @{
      id = "89ea5c94-7736-4e25-95ad-3fa95f62b66e"
    }
  }
}
New-MgSitePermission -SiteId $siteId -BodyParameter $params
```

**JavaScript**:
```javascript
const permission = {
  roles: ['write'],
  grantedTo: {
    application: { id: '89ea5c94-7736-4e25-95ad-3fa95f62b66e' }
  }
};
await client.api('/sites/{siteId}/permissions').post(permission);
```

## 11. PATCH /sites/{id}/permissions/{id} - Update Site Permission

### Description [VERIFIED]

Update the properties of a site permission. Only the **roles** property can be modified.

### HTTP Request

```http
PATCH https://graph.microsoft.com/v1.0/sites/{site-id}/permissions/{permission-id}
```

### Request Headers

- **Authorization**: `Bearer {token}`
- **Content-Type**: `application/json`
- **If-Match**: `{etag}` (optional, for optimistic concurrency)

### Request Body

```json
{
  "roles": ["read"]
}
```

### Limitations [VERIFIED]

- Only `roles` property can be modified
- Cannot modify organizational sharing links
- Cannot modify people sharing links

### Response JSON [VERIFIED]

Returns 200 OK with updated permission object.

## 12. DELETE /sites/{id}/permissions/{id} - Delete Site Permission

### Description [VERIFIED]

Remove an application permission from a site. Only non-inherited permissions can be deleted.

### HTTP Request

```http
DELETE https://graph.microsoft.com/v1.0/sites/{site-id}/permissions/{permission-id}
```

### Request Headers

- **Authorization**: `Bearer {token}`
- **If-Match**: `{etag}` (optional)

### Response [VERIFIED]

- **204 No Content** - Success
- **412 Precondition Failed** - ETag mismatch

### Limitations [VERIFIED]

- Cannot delete inherited permissions (check `inheritedFrom` is null)

## 13. GET /sites/{id}/operations - List Site Operations

### Description [VERIFIED]

Get a list of rich long-running operations associated with a site. Operations include content type copying, site provisioning, etc.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/operations
```

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "contentTypeCopy,0x010100298A15181454D84EBB62EDD7559FCBFE",
      "createdDateTime": "2026-01-24T16:28:23Z",
      "resourceId": "0x010100298A15181454D84EBB62EDD7559FCBFE",
      "resourceLocation": "https://graph.microsoft.com/v1.0/sites/5b3ea0e2-5fed-45ab-a8b8-7f7cd97189d6/contentTypes/0x010100298A15181454D84EBB62EDD7559FCBFE",
      "status": "succeeded",
      "type": "contentTypeCopy"
    }
  ]
}
```

### Operation Status Values [VERIFIED]

- **notStarted** - Operation queued
- **running** - Operation in progress
- **succeeded** - Operation completed successfully
- **failed** - Operation failed (check `error` property)

### SDK Examples

**Python**:
```python
result = await graph_client.sites.by_site_id('site-id').operations.get()
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid request format or parameters
- **401 Unauthorized** - Missing or invalid authentication token
- **403 Forbidden** - Insufficient permissions (need Sites.FullControl.All for permissions)
- **404 Not Found** - Site or permission does not exist
- **207 Multi-Status** - Partial success for batch operations (follow/unfollow)
- **410 Gone** - Delta token expired, restart sync
- **412 Precondition Failed** - ETag mismatch on update/delete
- **429 Too Many Requests** - Rate limit exceeded

### Error Response Format

```json
{
  "error": {
    "code": "accessDenied",
    "message": "Access denied. You do not have permission to perform this action.",
    "innerError": {
      "request-id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "date": "2026-01-28T15:30:00"
    }
  }
}
```

## Throttling Considerations [VERIFIED]

**Throttling Behavior**:
- HTTP 429 (Too Many Requests) returned when throttled
- `Retry-After` header indicates seconds to wait
- Delta operations may return 503 during heavy load

**Best Practices**:
- Implement exponential backoff with jitter
- Honor `Retry-After` header values
- Cache permission IDs after first lookup
- Use delta sync instead of full enumeration
- Batch follow/unfollow operations

**Resource Units**:
- Permission list: ~1 resource unit
- Permission create/update/delete: ~2 resource units
- Delta sync initial: ~5 resource units
- Delta sync incremental: ~1 resource unit

## Sites.Selected Permission Pattern [VERIFIED]

To use `Sites.Selected` for granular site access:

1. Register application with `Sites.Selected` permission
2. Admin grants application access to specific site via POST to `/sites/{id}/permissions`
3. Application can now access only that specific site

This provides least-privilege access without tenant-wide permissions.

## Sources

- **MSGRAPH-SMGMT-SC-01**: https://learn.microsoft.com/en-us/graph/api/site-delta?view=graph-rest-1.0
- **MSGRAPH-SMGMT-SC-02**: https://learn.microsoft.com/en-us/graph/api/site-follow?view=graph-rest-1.0
- **MSGRAPH-SMGMT-SC-03**: https://learn.microsoft.com/en-us/graph/api/site-unfollow?view=graph-rest-1.0
- **MSGRAPH-SMGMT-SC-04**: https://learn.microsoft.com/en-us/graph/api/site-list-permissions?view=graph-rest-1.0
- **MSGRAPH-SMGMT-SC-05**: https://learn.microsoft.com/en-us/graph/api/site-post-permissions?view=graph-rest-1.0
- **MSGRAPH-SMGMT-SC-06**: https://learn.microsoft.com/en-us/graph/api/permission-get?view=graph-rest-1.0
- **MSGRAPH-SMGMT-SC-07**: https://learn.microsoft.com/en-us/graph/api/permission-update?view=graph-rest-1.0
- **MSGRAPH-SMGMT-SC-08**: https://learn.microsoft.com/en-us/graph/api/permission-delete?view=graph-rest-1.0
- **MSGRAPH-SMGMT-SC-09**: https://learn.microsoft.com/en-us/graph/api/site-list-operations?view=graph-rest-1.0
- **MSGRAPH-SMGMT-SC-10**: https://learn.microsoft.com/en-us/graph/api/itemanalytics-get?view=graph-rest-1.0

## Document History

**[2026-01-28 17:45]**
- Initial creation with 13 Site management endpoints
- Full JSON request/response examples
- SDK examples for PowerShell, C#, JavaScript, Python
- Permission management patterns documented
- Delta sync pattern documented
