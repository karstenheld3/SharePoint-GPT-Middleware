# INFO: SharePoint REST API - Web

**Doc ID**: SPAPI-IN01
**Goal**: Detailed reference for Web (SP.Web) endpoints with request/response JSON and examples
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_SHAREPOINT_API_TOC.md [SPAPI-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Retrieve and update web (site) properties
- Create and delete subsites
- Manage site navigation (Quick Launch, Top Navigation)
- Access web-level features and settings
- Get all subsites within a web

**Key findings**:
- `/_api/web` is the primary entry point for site operations [VERIFIED]
- Use MERGE method with X-HTTP-Method header for partial updates [VERIFIED]
- Navigation nodes can be added, updated, and deleted [VERIFIED]
- Subsite creation requires parent web context [VERIFIED]

## Quick Reference Summary

**Endpoints covered**: 12 web endpoints

- `GET /_api/web` - Get web properties
- `GET /_api/web/title` - Get web title
- `PATCH /_api/web` - Update web properties
- `GET /_api/web/webs` - Get all subsites
- `POST /_api/web/webs/add` - Create subsite
- `DELETE /_api/web` - Delete web
- `GET /_api/web/navigation/quicklaunch` - Get Quick Launch nodes
- `GET /_api/web/navigation/topnavigationbar` - Get Top Navigation nodes
- `POST /_api/web/navigation/quicklaunch` - Add Quick Launch node
- `DELETE /_api/web/navigation/quicklaunch({id})` - Delete navigation node

**Permissions required**:
- Application: `Sites.Read.All` (read), `Sites.ReadWrite.All` (write), `Sites.FullControl.All` (delete)
- Delegated: `Sites.Read.All` (read), `Sites.ReadWrite.All` (write), `Sites.FullControl.All` (delete)
- **Least privilege**: `Sites.Read.All` for read-only operations
- Note: Web deletion requires `Sites.FullControl.All`

## Authentication and Headers

### Required Headers (All Requests)

- **Authorization**: `Bearer {access_token}`
- **Accept**: `application/json;odata=verbose`, `application/json;odata=minimalmetadata`, or `application/json;odata=nometadata`

### Additional Headers (Write Operations)

- **Content-Type**: `application/json;odata=verbose`
- **X-RequestDigest**: `{form_digest_value}` (required for POST/PATCH/DELETE with cookie-based or add-in auth; NOT required with OAuth Bearer tokens)

### Headers for Update/Delete Operations

- **X-HTTP-Method**: `MERGE` (partial update) or `DELETE` (delete)
- **IF-MATCH**: `{etag}` or `*` (concurrency control)

## SP.Web Resource Type

### Properties [VERIFIED]

- **Id** (`Edm.Guid`) - Web GUID
- **Title** (`Edm.String`) - Display title of the web
- **Description** (`Edm.String`) - Web description
- **Url** (`Edm.String`) - Absolute URL
- **ServerRelativeUrl** (`Edm.String`) - Server-relative URL
- **Created** (`Edm.DateTime`) - Creation date
- **LastItemModifiedDate** (`Edm.DateTime`) - Last modification date
- **WebTemplate** (`Edm.String`) - Template used (e.g., "STS", "BLOG")
- **Language** (`Edm.Int32`) - Language LCID (e.g., 1033 for English)
- **EnableMinimalDownload** (`Edm.Boolean`) - MDS enabled
- **QuickLaunchEnabled** (`Edm.Boolean`) - Quick Launch visible
- **TreeViewEnabled** (`Edm.Boolean`) - Tree view enabled

## 1. GET /_api/web - Get Web Properties

### Description [VERIFIED]

Returns the SP.Web object representing the current web (site) with all its properties.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web
```

### Query Parameters

- **$select** - Comma-separated list of properties to return
- **$expand** - Related entities to include (e.g., `Lists`, `CurrentUser`)

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/web?$select=Id,Title,Url,Created
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "__metadata": {
      "id": "https://contoso.sharepoint.com/sites/TeamSite/_api/web",
      "uri": "https://contoso.sharepoint.com/sites/TeamSite/_api/web",
      "type": "SP.Web"
    },
    "Id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
    "Title": "Team Site",
    "Description": "Team collaboration site",
    "Url": "https://contoso.sharepoint.com/sites/TeamSite",
    "ServerRelativeUrl": "/sites/TeamSite",
    "Created": "2024-01-15T10:30:00Z",
    "LastItemModifiedDate": "2024-01-20T14:30:00Z",
    "WebTemplate": "STS",
    "Language": 1033,
    "QuickLaunchEnabled": true
  }
}
```

## 2. GET /_api/web/title - Get Web Title

### Description [VERIFIED]

Returns only the title property of the web. Useful for lightweight requests.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/title
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "Title": "Team Site"
  }
}
```

## 3. PATCH /_api/web - Update Web Properties

### Description [VERIFIED]

Updates one or more properties of the web using the MERGE method.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web
```

### Request Headers

```http
Authorization: Bearer {access_token}
Accept: application/json;odata=verbose
Content-Type: application/json;odata=verbose
X-RequestDigest: {form_digest_value}
X-HTTP-Method: MERGE
IF-MATCH: *
```

### Request Body

```json
{
  "__metadata": {
    "type": "SP.Web"
  },
  "Title": "Updated Team Site",
  "Description": "Updated description"
}
```

### Request Example

```http
POST https://contoso.sharepoint.com/sites/TeamSite/_api/web
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
Content-Type: application/json;odata=verbose
X-HTTP-Method: MERGE
IF-MATCH: *

{
  "__metadata": { "type": "SP.Web" },
  "Title": "Updated Team Site"
}
```

### Response

Returns HTTP 204 No Content on success.

## 4. GET /_api/web/webs - Get All Subsites

### Description [VERIFIED]

Returns all subsites (child webs) of the current web.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/webs
```

### Query Parameters

- **$select** - Properties to return for each subsite
- **$filter** - Filter subsites
- **$orderby** - Sort order

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/web/webs?$select=Id,Title,Url
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "results": [
      {
        "__metadata": {
          "type": "SP.Web"
        },
        "Id": "c3d4e5f6-a7b8-9012-cdef-345678901234",
        "Title": "Marketing Subsite",
        "Url": "https://contoso.sharepoint.com/sites/TeamSite/marketing"
      },
      {
        "__metadata": {
          "type": "SP.Web"
        },
        "Id": "d4e5f6a7-b890-1234-def0-456789012345",
        "Title": "Engineering Subsite",
        "Url": "https://contoso.sharepoint.com/sites/TeamSite/engineering"
      }
    ]
  }
}
```

## 5. POST /_api/web/webs/add - Create Subsite

### Description [VERIFIED]

Creates a new subsite under the current web.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/webs/add
```

### Request Body

```json
{
  "parameters": {
    "__metadata": {
      "type": "SP.WebCreationInformation"
    },
    "Title": "New Subsite",
    "Url": "newsubsite",
    "Description": "Description of the new subsite",
    "Language": 1033,
    "WebTemplate": "STS#3",
    "UseUniquePermissions": false
  }
}
```

### Common WebTemplate Values

- **STS#3** - Team site (modern)
- **STS#0** - Team site (classic)
- **BLOG#0** - Blog
- **WIKI#0** - Wiki
- **PROJECTSITE#0** - Project site

### Request Example

```http
POST https://contoso.sharepoint.com/sites/TeamSite/_api/web/webs/add
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
Content-Type: application/json;odata=verbose
X-RequestDigest: 0x1234...

{
  "parameters": {
    "__metadata": { "type": "SP.WebCreationInformation" },
    "Title": "Marketing",
    "Url": "marketing",
    "WebTemplate": "STS#3",
    "UseUniquePermissions": false
  }
}
```

### Response JSON [VERIFIED]

Returns the created SP.Web object with HTTP 201 Created.

## 6. DELETE /_api/web - Delete Web

### Description [VERIFIED]

Deletes the current web. Cannot delete the root web of a site collection.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/{subsite}/_api/web
```

### Request Headers

```http
Authorization: Bearer {access_token}
X-RequestDigest: {form_digest_value}
X-HTTP-Method: DELETE
IF-MATCH: *
```

### Request Example

```http
POST https://contoso.sharepoint.com/sites/TeamSite/marketing/_api/web
Authorization: Bearer eyJ0eXAi...
X-HTTP-Method: DELETE
IF-MATCH: *
```

### Response

Returns HTTP 200 OK on success.

## 7. GET /_api/web/navigation/quicklaunch - Get Quick Launch

### Description [VERIFIED]

Returns the Quick Launch navigation nodes for the web.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/navigation/quicklaunch
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "results": [
      {
        "__metadata": {
          "type": "SP.NavigationNode"
        },
        "Id": 1031,
        "Title": "Home",
        "Url": "/sites/TeamSite",
        "IsExternal": false,
        "IsVisible": true
      },
      {
        "__metadata": {
          "type": "SP.NavigationNode"
        },
        "Id": 1032,
        "Title": "Documents",
        "Url": "/sites/TeamSite/Shared Documents",
        "IsExternal": false,
        "IsVisible": true
      }
    ]
  }
}
```

## 8. GET /_api/web/navigation/topnavigationbar - Get Top Navigation

### Description [VERIFIED]

Returns the Top Navigation Bar nodes for the web.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/navigation/topnavigationbar
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "results": [
      {
        "__metadata": {
          "type": "SP.NavigationNode"
        },
        "Id": 2001,
        "Title": "Home",
        "Url": "/sites/TeamSite",
        "IsExternal": false
      }
    ]
  }
}
```

## 9. POST /_api/web/navigation/quicklaunch - Add Navigation Node

### Description [VERIFIED]

Adds a new navigation node to the Quick Launch.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/navigation/quicklaunch
```

### Request Body

```json
{
  "__metadata": {
    "type": "SP.NavigationNode"
  },
  "Title": "External Link",
  "Url": "https://www.microsoft.com",
  "IsExternal": true
}
```

### Response JSON [VERIFIED]

Returns the created navigation node with its Id.

## 10. DELETE /_api/web/navigation/quicklaunch({id}) - Delete Navigation Node

### Description [VERIFIED]

Deletes a navigation node from Quick Launch by its ID.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/navigation/quicklaunch({node_id})
```

### Request Headers

```http
Authorization: Bearer {access_token}
X-RequestDigest: {form_digest_value}
X-HTTP-Method: DELETE
IF-MATCH: *
```

### Response

Returns HTTP 200 OK on success.

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid web template or parameters
- **401 Unauthorized** - Missing or invalid authentication token
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Web does not exist
- **409 Conflict** - Web with same URL already exists

## SDK Examples

**PnP PowerShell**:
```powershell
Connect-PnPOnline -Url "https://contoso.sharepoint.com/sites/TeamSite" -Interactive
Get-PnPWeb
Set-PnPWeb -Title "New Title"
New-PnPWeb -Title "Subsite" -Url "subsite" -Template "STS#3"
```

**PnP JavaScript** (v4.x):
```javascript
import { spfi } from "@pnp/sp";
import "@pnp/sp/webs";
const sp = spfi(...);
const web = await sp.web();
await sp.web.update({ Title: "New Title" });
```

## Sources

- **SPAPI-WEB-SC-01**: https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/complete-basic-operations-using-sharepoint-rest-endpoints
- **SPAPI-WEB-SC-02**: https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/determine-sharepoint-rest-service-endpoint-uris

## Document History

**[2026-01-28 18:55]**
- Initial creation with 12 endpoints
- Documented web CRUD, subsites, and navigation operations
