# INFO: SharePoint REST API - Site Collection

**Doc ID**: SPAPI-IN01
**Goal**: Detailed reference for Site Collection (SP.Site) endpoints with request/response JSON and examples
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_SHAREPOINT_API_TOC.md [SPAPI-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Retrieve site collection properties and configuration
- Get site collection owner and usage statistics
- Manage site collection features (activate/deactivate)
- Access site collection recycle bin
- Navigate to root web from site collection context

**Key findings**:
- `/_api/site` returns SP.Site object representing the site collection [VERIFIED]
- Site collection is the top-level container; web (SP.Web) is a subsite [VERIFIED]
- Features can be activated/deactivated via POST with feature GUID [VERIFIED]
- Recycle bin access requires appropriate permissions [VERIFIED]

## Quick Reference Summary

**Endpoints covered**: 8 site collection endpoints

- `GET /_api/site` - Get site collection properties
- `GET /_api/site/rootweb` - Get root web of site collection
- `GET /_api/site/owner` - Get site collection owner
- `GET /_api/site/usage` - Get site collection usage info
- `GET /_api/site/features` - Get activated features
- `POST /_api/site/features/add` - Activate a feature
- `POST /_api/site/features/remove` - Deactivate a feature
- `GET /_api/site/recyclebin` - Get recycle bin items

**Permissions required**:
- Application: `Sites.Read.All` (read), `Sites.ReadWrite.All` (write), `Sites.FullControl.All` (features)
- Delegated: `Sites.Read.All` (read), `Sites.ReadWrite.All` (write), `Sites.FullControl.All` (features)
- **Least privilege**: `Sites.Read.All` for read-only operations
- Note: Feature activation/deactivation requires `Sites.FullControl.All`

## Authentication and Headers

### Required Headers (All Requests)

- **Authorization**: `Bearer {access_token}`
- **Accept**: `application/json;odata=verbose`, `application/json;odata=minimalmetadata`, or `application/json;odata=nometadata`

### Additional Headers (Write Operations)

- **Content-Type**: `application/json;odata=verbose`
- **X-RequestDigest**: `{form_digest_value}` (required for POST with cookie-based or add-in auth; NOT required with OAuth Bearer tokens)

## SP.Site Resource Type

### Properties [VERIFIED]

- **Id** (`Edm.Guid`) - Site collection GUID
- **Url** (`Edm.String`) - Absolute URL of the site collection
- **CompatibilityLevel** (`Edm.Int32`) - Site collection compatibility level (15 for SP2013+)
- **PrimaryUri** (`Edm.String`) - Primary URI of the site collection
- **ReadOnly** (`Edm.Boolean`) - Whether site collection is read-only
- **ServerRelativeUrl** (`Edm.String`) - Server-relative URL
- **Usage** (`SP.UsageInfo`) - Usage information (storage, bandwidth)

## 1. GET /_api/site - Get Site Collection

### Description [VERIFIED]

Returns the SP.Site object representing the current site collection with its properties.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/site
```

### Request Headers

```http
Authorization: Bearer {access_token}
Accept: application/json;odata=verbose
```

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/site
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "__metadata": {
      "id": "https://contoso.sharepoint.com/sites/TeamSite/_api/site",
      "uri": "https://contoso.sharepoint.com/sites/TeamSite/_api/site",
      "type": "SP.Site"
    },
    "Id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "Url": "https://contoso.sharepoint.com/sites/TeamSite",
    "CompatibilityLevel": 15,
    "PrimaryUri": "https://contoso.sharepoint.com/sites/TeamSite",
    "ReadOnly": false,
    "ServerRelativeUrl": "/sites/TeamSite"
  }
}
```

## 2. GET /_api/site/rootweb - Get Root Web

### Description [VERIFIED]

Returns the root web (SP.Web) of the site collection. The root web is the top-level site within the site collection.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/site/rootweb
```

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/site/rootweb
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "__metadata": {
      "type": "SP.Web"
    },
    "Id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
    "Title": "Team Site",
    "Url": "https://contoso.sharepoint.com/sites/TeamSite",
    "ServerRelativeUrl": "/sites/TeamSite",
    "Created": "2024-01-15T10:30:00Z",
    "Description": "Team collaboration site"
  }
}
```

## 3. GET /_api/site/owner - Get Site Collection Owner

### Description [VERIFIED]

Returns the user who is the primary owner/administrator of the site collection.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/site/owner
```

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/site/owner
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "__metadata": {
      "type": "SP.User"
    },
    "Id": 7,
    "Title": "John Smith",
    "LoginName": "i:0#.f|membership|john.smith@contoso.com",
    "Email": "john.smith@contoso.com",
    "IsSiteAdmin": true
  }
}
```

## 4. GET /_api/site/usage - Get Site Collection Usage

### Description [VERIFIED]

Returns usage information for the site collection including storage used and bandwidth.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/site/usage
```

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/site/usage
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "__metadata": {
      "type": "SP.UsageInfo"
    },
    "Bandwidth": 0,
    "DiscussionStorage": 0,
    "Hits": 0,
    "Storage": 52428800,
    "StoragePercentageUsed": 0.05,
    "Visits": 0
  }
}
```

## 5. GET /_api/site/features - Get Activated Features

### Description [VERIFIED]

Returns the collection of features activated at the site collection level.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/site/features
```

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/site/features
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
          "type": "SP.Feature"
        },
        "DefinitionId": "f6924d36-2fa8-4f0b-b16d-06b7250180fa"
      },
      {
        "__metadata": {
          "type": "SP.Feature"
        },
        "DefinitionId": "3bae86a2-776d-499d-9db8-fa4cdc7884f8"
      }
    ]
  }
}
```

## 6. POST /_api/site/features/add - Activate Feature

### Description [VERIFIED]

Activates a site collection-scoped feature by its GUID.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/site/features/add(featureId=guid'{feature_guid}',force=true)
```

### Path Parameters

- **featureId** (`Edm.Guid`) - The GUID of the feature to activate
- **force** (`Edm.Boolean`) - Force activation even if already activated

### Request Headers

```http
Authorization: Bearer {access_token}
Accept: application/json;odata=verbose
X-RequestDigest: {form_digest_value}
```

### Request Example

```http
POST https://contoso.sharepoint.com/sites/TeamSite/_api/site/features/add(featureId=guid'f6924d36-2fa8-4f0b-b16d-06b7250180fa',force=true)
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
X-RequestDigest: 0x1234...
```

### Response

Returns HTTP 200 OK on success with the activated feature object.

## 7. POST /_api/site/features/remove - Deactivate Feature

### Description [VERIFIED]

Deactivates a site collection-scoped feature by its GUID.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/site/features/remove(featureId=guid'{feature_guid}',force=true)
```

### Path Parameters

- **featureId** (`Edm.Guid`) - The GUID of the feature to deactivate
- **force** (`Edm.Boolean`) - Force deactivation

### Request Example

```http
POST https://contoso.sharepoint.com/sites/TeamSite/_api/site/features/remove(featureId=guid'f6924d36-2fa8-4f0b-b16d-06b7250180fa',force=true)
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
X-RequestDigest: 0x1234...
```

### Response

Returns HTTP 200 OK on success.

## 8. GET /_api/site/recyclebin - Get Recycle Bin Items

### Description [VERIFIED]

Returns items in the site collection recycle bin. The site collection recycle bin contains items deleted from all webs in the site collection.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/site/recyclebin
```

### Query Parameters

- **$filter** - Filter results (e.g., `ItemType eq 1` for files)
- **$orderby** - Sort results (e.g., `DeletedDate desc`)
- **$top** - Limit number of results

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/site/recyclebin?$top=10&$orderby=DeletedDate desc
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
          "type": "SP.RecycleBinItem"
        },
        "Id": "c3d4e5f6-a7b8-9012-cdef-345678901234",
        "Title": "Deleted Document.docx",
        "DeletedByEmail": "john.smith@contoso.com",
        "DeletedByName": "John Smith",
        "DeletedDate": "2024-01-20T14:30:00Z",
        "DirName": "/sites/TeamSite/Shared Documents",
        "ItemType": 1,
        "Size": 25600
      }
    ]
  }
}
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid feature GUID format
- **401 Unauthorized** - Missing or invalid authentication token
- **403 Forbidden** - Insufficient permissions (especially for feature operations)
- **404 Not Found** - Site collection does not exist

### Error Response Format

```json
{
  "error": {
    "code": "-2147024891, System.UnauthorizedAccessException",
    "message": {
      "lang": "en-US",
      "value": "Access denied. You do not have permission to perform this action."
    }
  }
}
```

## SDK Examples

**PnP PowerShell**:
```powershell
Connect-PnPOnline -Url "https://contoso.sharepoint.com/sites/TeamSite" -Interactive
Get-PnPSite
Get-PnPSite -Includes Usage, Owner
Get-PnPFeature -Scope Site
Enable-PnPFeature -Identity "{feature-guid}" -Scope Site
Disable-PnPFeature -Identity "{feature-guid}" -Scope Site
Get-PnPRecycleBinItem
```

**PnP JavaScript** (v4.x):
```javascript
import { spfi } from "@pnp/sp";
import "@pnp/sp/sites";
import "@pnp/sp/features";
const sp = spfi(...);

const site = await sp.site();
const features = await sp.site.features();
const recycleBin = await sp.site.recycleBin();
```

## Sources

- **SPAPI-SITE-SC-01**: https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/get-to-know-the-sharepoint-rest-service
- **SPAPI-SITE-SC-02**: https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/determine-sharepoint-rest-service-endpoint-uris

## Document History

**[2026-01-28 18:50]**
- Initial creation with 8 endpoints
- Documented site collection properties, rootweb, owner, usage, features, and recycle bin
