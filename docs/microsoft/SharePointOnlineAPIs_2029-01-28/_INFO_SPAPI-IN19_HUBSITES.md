# INFO: SharePoint REST API - Hub Sites

**Doc ID**: SPAPI-IN01
**Goal**: Detailed reference for Hub Site REST API endpoints with request/response JSON
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_SHAREPOINT_API_TOC.md [SPAPI-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Register sites as hub sites
- Associate sites with hub sites
- Get hub site information and navigation
- Manage hub site themes

**Key findings**:
- Only tenant admins can register hub sites [VERIFIED]
- JoinHubSite with empty GUID disassociates from hub [VERIFIED]
- HubSiteData returns navigation and theme info [VERIFIED]
- SyncHubSiteTheme applies parent hub theme updates [VERIFIED]

## Quick Reference Summary

**Endpoints covered**: 8 hub site endpoints

- `GET /_api/hubsites` - Get all hub sites
- `GET /_api/hubsites/getbyid('{id}')` - Get hub site by ID
- `GET /_api/web/hubsitedata` - Get hub site data for current web
- `POST /_api/site/registerhubsite` - Register as hub site
- `POST /_api/site/unregisterhubsite` - Unregister hub site
- `POST /_api/site/joinhubsite('{id}')` - Join hub site
- `POST /_api/web/synchubsitetheme` - Sync hub theme
- `GET /_api/sp.hubsites.cancreate` - Check if can create hub

**Permissions required**:
- Application: `Sites.FullControl.All` (register/unregister), `Sites.ReadWrite.All` (join)
- Delegated: SharePoint Admin for register, site owner for join
- Note: RegisterHubSite requires tenant admin

## SP.HubSite Resource Type [VERIFIED]

### Properties

- **ID** (`Edm.Guid`) - Hub site ID
- **Title** (`Edm.String`) - Hub site title
- **SiteId** (`Edm.Guid`) - Site collection ID
- **SiteUrl** (`Edm.String`) - Hub site URL
- **LogoUrl** (`Edm.String`) - Hub logo URL
- **Description** (`Edm.String`) - Hub description
- **Targets** (`Edm.String`) - Target audiences
- **TenantInstanceId** (`Edm.Guid`) - Tenant ID
- **RequiresJoinApproval** (`Edm.Boolean`) - Requires approval to join
- **HideNameInNavigation** (`Edm.Boolean`) - Hide name in navigation
- **ParentHubSiteId** (`Edm.Guid`) - Parent hub (for nested hubs)

## SP.HubSiteData Resource Type [VERIFIED]

### Properties

- **themeKey** (`Edm.String`) - Theme identifier
- **name** (`Edm.String`) - Hub site name
- **url** (`Edm.String`) - Hub site URL
- **logoUrl** (`Edm.String`) - Logo URL
- **usesMetadataNavigation** (`Edm.Boolean`) - Uses metadata nav
- **navigation** (`Collection`) - Navigation nodes
- **relatedHubSiteIds** (`Collection(Edm.Guid)`) - Related hub IDs

## 1. GET /_api/hubsites - Get All Hub Sites

### Description [VERIFIED]

Returns all hub sites the current user can access.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/hubsites
```

### Request Example

```http
GET https://contoso.sharepoint.com/_api/hubsites
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=nometadata
```

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "Description": "Corporate communications hub",
      "ID": "27c5fcba-abfd-4c34-823d-0b4a48f7ffe6",
      "LogoUrl": "https://contoso.sharepoint.com/sites/hub/SiteAssets/logo.png",
      "SiteId": "da2818cf-9d60-4a42-8a04-67f3a6e8f039",
      "SiteUrl": "https://contoso.sharepoint.com/sites/hub",
      "Title": "Corporate Hub",
      "RequiresJoinApproval": false
    }
  ]
}
```

## 2. GET /_api/hubsites/getbyid('{id}') - Get Hub Site by ID

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/hubsites/getbyid('{hub_site_id}')
```

### Request Example

```http
GET https://contoso.sharepoint.com/_api/hubsites/getbyid('27c5fcba-abfd-4c34-823d-0b4a48f7ffe6')
```

### Update Hub Site

Use POST with update body:

```http
POST https://contoso.sharepoint.com/_api/hubsites/getbyid('27c5fcba-abfd-4c34-823d-0b4a48f7ffe6')
Content-Type: application/json

{
  "Title": "Updated Hub Title",
  "Description": "Updated description",
  "LogoUrl": "https://contoso.sharepoint.com/sites/hub/newlogo.png"
}
```

## 3. GET /_api/web/hubsitedata - Get Hub Site Data

### Description [VERIFIED]

Returns hub site data for the current web, including navigation and theme.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/hubsitedata
```

### With Force Refresh

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/hubsitedata(true)
```

### Response JSON [VERIFIED]

```json
{
  "themeKey": "Corporate Theme",
  "name": "Corporate Hub",
  "url": "https://contoso.sharepoint.com/sites/hub",
  "logoUrl": "https://contoso.sharepoint.com/sites/hub/SiteAssets/logo.png",
  "usesMetadataNavigation": false,
  "navigation": [
    {
      "Id": 1,
      "Title": "Home",
      "Url": "https://contoso.sharepoint.com/sites/hub",
      "IsDocLib": false,
      "IsExternal": false,
      "ParentId": 0,
      "Children": []
    },
    {
      "Id": 2,
      "Title": "News",
      "Url": "https://contoso.sharepoint.com/sites/hub/SitePages/News.aspx",
      "Children": []
    }
  ]
}
```

## 4. POST /_api/site/registerhubsite - Register Hub Site

### Description [VERIFIED]

Registers an existing site as a hub site. Requires tenant admin.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/site/registerhubsite
```

### Request Example

```http
POST https://contoso.sharepoint.com/sites/marketing/_api/site/registerhubsite
Authorization: Bearer eyJ0eXAi...
X-RequestDigest: 0x1234...
```

### Response JSON [VERIFIED]

```json
{
  "@odata.type": "#SP.HubSite",
  "Description": null,
  "ID": "27c5fcba-abfd-4c34-823d-0b4a48f7ffe6",
  "LogoUrl": null,
  "SiteId": "da2818cf-9d60-4a42-8a04-67f3a6e8f039",
  "SiteUrl": "https://contoso.sharepoint.com/sites/marketing",
  "Title": "Marketing"
}
```

## 5. POST /_api/site/unregisterhubsite - Unregister Hub Site

### Description [VERIFIED]

Unregisters a hub site. Associated sites become disassociated.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/site/unregisterhubsite
```

## 6. POST /_api/site/joinhubsite('{id}') - Join Hub Site

### Description [VERIFIED]

Associates a site with an existing hub site.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/site/joinhubsite('{hub_site_id}')
```

### Request Example

```http
POST https://contoso.sharepoint.com/sites/advertising/_api/site/joinhubsite('27c5fcba-abfd-4c34-823d-0b4a48f7ffe6')
Authorization: Bearer eyJ0eXAi...
X-RequestDigest: 0x1234...
```

### Disassociate from Hub Site

Use empty GUID to disassociate:

```http
POST https://contoso.sharepoint.com/sites/advertising/_api/site/joinhubsite('00000000-0000-0000-0000-000000000000')
```

## 7. POST /_api/web/synchubsitetheme - Sync Hub Theme

### Description [VERIFIED]

Applies any theme updates from the parent hub site.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/synchubsitetheme
```

## 8. GET /_api/sp.hubsites.cancreate - Check Create Permission

### Description [VERIFIED]

Returns whether current user can create a hub site (tenant admin).

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/sp.hubsites.cancreate
```

### Response

```json
{
  "value": true
}
```

## Hub Site Navigation

### Get Hub Navigation

Hub navigation is returned in HubSiteData response as `navigation` array.

### Structure

```json
{
  "navigation": [
    {
      "Id": 1,
      "Title": "Home",
      "Url": "https://...",
      "IsDocLib": false,
      "IsExternal": false,
      "ParentId": 0,
      "Children": [
        {
          "Id": 2,
          "Title": "Sub Page",
          "Url": "https://...",
          "ParentId": 1
        }
      ]
    }
  ]
}
```

## Error Responses

- **400** - Invalid hub site ID
- **401** - Unauthorized
- **403** - Insufficient permissions (not tenant admin for register)
- **404** - Hub site not found

## SDK Examples

**PnP PowerShell**:
```powershell
Connect-PnPOnline -Url "https://contoso-admin.sharepoint.com" -Interactive

# Get all hub sites
Get-PnPHubSite

# Register hub site (requires admin)
Register-PnPHubSite -Site "https://contoso.sharepoint.com/sites/hub"

# Join hub site
Add-PnPHubSiteAssociation -Site "https://contoso.sharepoint.com/sites/project" -HubSite "https://contoso.sharepoint.com/sites/hub"

# Remove from hub
Remove-PnPHubSiteAssociation -Site "https://contoso.sharepoint.com/sites/project"

# Unregister hub site
Unregister-PnPHubSite -Site "https://contoso.sharepoint.com/sites/hub"
```

**PnP JavaScript** (v4.x):
```javascript
import { spfi } from "@pnp/sp";
import "@pnp/sp/hubsites";
const sp = spfi(...);

const hubSites = await sp.hubSites();
const hubSite = await sp.hubSites.getById("27c5fcba-abfd-4c34-823d-0b4a48f7ffe6")();
const hubData = await sp.web.hubSiteData();

// Join hub site
await sp.site.joinHubSite("27c5fcba-abfd-4c34-823d-0b4a48f7ffe6");
```

## Sources

- **SPAPI-HUB-SC-01**: https://learn.microsoft.com/en-us/sharepoint/dev/features/hub-site/hub-site-rest-api
- **SPAPI-HUB-SC-02**: https://learn.microsoft.com/en-us/sharepoint/dev/features/hub-site/rest-joinhubsite-method

## Document History

**[2026-01-28 20:55]**
- Initial creation with 8 endpoints
- Documented hub site registration and association
- Added navigation structure reference
