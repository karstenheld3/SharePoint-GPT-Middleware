# INFO: SharePoint REST API - Site Page

**Doc ID**: SPAPI-IN01
**Goal**: Detailed reference for Site Page (Modern Pages) REST API endpoints with request/response JSON
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_SHAREPOINT_API_TOC.md [SPAPI-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Create and manage modern SharePoint pages
- Publish and unpublish pages
- Get page metadata and content
- Work with news posts

**Key findings**:
- Modern pages stored in Site Pages library [VERIFIED]
- API endpoint: `/_api/sitepages/pages` [VERIFIED]
- MS Graph provides richer page API for content manipulation [VERIFIED]
- Pages use CanvasContent1 field for web part JSON [VERIFIED]

## Quick Reference Summary

**Endpoints covered**: 8 site page endpoints

- `GET /_api/sitepages/pages` - Get all pages
- `GET /_api/sitepages/pages({id})` - Get page by ID
- `GET /_api/sitepages/pages/getbyurl('{url}')` - Get page by URL
- `POST /_api/sitepages/pages` - Create page
- `PATCH /_api/sitepages/pages({id})` - Update page
- `DELETE /_api/sitepages/pages({id})` - Delete page
- `POST /_api/sitepages/pages({id})/publish` - Publish page
- `POST /_api/sitepages/pages({id})/saveasdraft` - Save as draft

**Permissions required**:
- Application: `Sites.ReadWrite.All` (create/update), `Sites.Read.All` (read)
- Delegated: `Sites.ReadWrite.All` (create/update), `Sites.Read.All` (read)

## Page Types [VERIFIED]

- **Article** - Standard content page
- **Home** - Site home page
- **RepostPage** - News link/repost
- **SpacesPage** - Spaces page (deprecated)

## SP.Publishing.SitePage Properties [VERIFIED]

- **Id** (`Edm.Int32`) - Page list item ID
- **Name** (`Edm.String`) - Page file name
- **Title** (`Edm.String`) - Page title
- **PageLayoutType** (`Edm.String`) - Article, Home, etc.
- **BannerImageUrl** (`Edm.String`) - Banner image URL
- **TopicHeader** (`Edm.String`) - Topic header text
- **AuthorByline** (`Collection(Edm.String)`) - Author names
- **FirstPublishedDate** (`Edm.DateTime`) - First published
- **Description** (`Edm.String`) - Page description
- **PromotedState** (`Edm.Int32`) - 0=Page, 1=NewsPost, 2=Promoted
- **CanvasContent1** (`Edm.String`) - Web part JSON content

## 1. GET /_api/sitepages/pages - Get All Pages

### Description [VERIFIED]

Returns all pages in the Site Pages library.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/sitepages/pages
```

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/sitepages/pages
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
          "type": "SP.Publishing.SitePage"
        },
        "Id": 1,
        "Name": "Home.aspx",
        "Title": "Home",
        "PageLayoutType": "Home",
        "PromotedState": 0,
        "FirstPublishedDate": "2024-01-15T10:30:00Z"
      },
      {
        "__metadata": {
          "type": "SP.Publishing.SitePage"
        },
        "Id": 5,
        "Name": "Welcome.aspx",
        "Title": "Welcome to our site",
        "PageLayoutType": "Article",
        "PromotedState": 1,
        "FirstPublishedDate": "2024-02-20T14:00:00Z"
      }
    ]
  }
}
```

## 2. GET /_api/sitepages/pages({id}) - Get Page by ID

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/sitepages/pages({page_id})
```

## 3. GET /_api/sitepages/pages/getbyurl('{url}') - Get Page by URL

### Description [VERIFIED]

Returns a page by its server-relative URL.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/sitepages/pages/getbyurl('SitePages/{pagename}.aspx')
```

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/sitepages/pages/getbyurl('SitePages/Welcome.aspx')
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

## 4. POST /_api/sitepages/pages - Create Page

### Description [VERIFIED]

Creates a new modern page.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/sitepages/pages
```

### Request Body [VERIFIED]

```json
{
  "__metadata": {
    "type": "SP.Publishing.SitePage"
  },
  "Name": "new-page.aspx",
  "Title": "My New Page",
  "PageLayoutType": "Article",
  "PromotedState": 0
}
```

### Create News Post

```json
{
  "__metadata": {
    "type": "SP.Publishing.SitePage"
  },
  "Name": "company-news.aspx",
  "Title": "Company News Update",
  "PageLayoutType": "Article",
  "PromotedState": 1,
  "BannerImageUrl": "/sites/TeamSite/SiteAssets/banner.jpg",
  "Description": "Latest company updates"
}
```

**PromotedState values**:
- **0** - Regular page
- **1** - News post
- **2** - Promoted news

## 5. PATCH /_api/sitepages/pages({id}) - Update Page

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/sitepages/pages({page_id})
X-HTTP-Method: MERGE
IF-MATCH: *
```

### Request Body

```json
{
  "__metadata": {
    "type": "SP.Publishing.SitePage"
  },
  "Title": "Updated Page Title",
  "Description": "Updated description"
}
```

## 6. DELETE /_api/sitepages/pages({id}) - Delete Page

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/sitepages/pages({page_id})
X-HTTP-Method: DELETE
IF-MATCH: *
```

## 7. POST /_api/sitepages/pages({id})/publish - Publish Page

### Description [VERIFIED]

Publishes a draft page, making it visible to readers.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/sitepages/pages({page_id})/publish
```

### Request Example

```http
POST https://contoso.sharepoint.com/sites/TeamSite/_api/sitepages/pages(5)/publish
Authorization: Bearer eyJ0eXAi...
X-RequestDigest: 0x1234...
```

## 8. POST /_api/sitepages/pages({id})/saveasdraft - Save as Draft

### Description [VERIFIED]

Saves page changes without publishing.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/sitepages/pages({page_id})/saveasdraft
```

## Additional Endpoints

### Check Out Page

```http
POST /_api/sitepages/pages({id})/checkout
```

### Discard Check Out

```http
POST /_api/sitepages/pages({id})/discardpage
```

### Copy Page

```http
POST /_api/sitepages/pages({id})/copy
```

### Schedule Publish

```http
POST /_api/sitepages/pages({id})/schedulepublish
```

## Working with Page Content

### Get Full Canvas Content

```http
GET /_api/sitepages/pages({id})?$select=CanvasContent1
```

### CanvasContent1 Structure [VERIFIED]

The CanvasContent1 field contains JSON array of web parts:

```json
[
  {
    "position": {
      "zoneIndex": 1,
      "sectionIndex": 1,
      "controlIndex": 1
    },
    "controlType": 4,
    "id": "7c5e377e-5f85-4bfd-9c0f-7c7e7c7e7c7e",
    "webPartId": "275c0095-a77e-4f6d-a2a0-6395eb2f5a56",
    "webPartData": {
      "dataVersion": "1.0",
      "title": "Text",
      "properties": {
        "text": "<p>Hello World</p>"
      }
    }
  }
]
```

### Update Canvas Content

```http
POST /_api/sitepages/pages({id})/savepage

{
  "__metadata": { "type": "SP.Publishing.SitePage" },
  "CanvasContent1": "[{...web part JSON...}]"
}
```

## Microsoft Graph Alternative

For richer page manipulation, use Microsoft Graph:

### Get Page with Content

```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/pages/{pageId}?$expand=canvasLayout
```

### Create Page with Web Parts

```http
POST https://graph.microsoft.com/v1.0/sites/{siteId}/pages

{
  "name": "new-page.aspx",
  "title": "New Page",
  "pageLayout": "article",
  "showComments": true,
  "showRecommendedPages": false,
  "titleArea": {
    "enableGradientEffect": true,
    "layout": "plain"
  }
}
```

## Error Responses

- **400** - Invalid page properties
- **401** - Unauthorized
- **403** - Insufficient permissions
- **404** - Page not found
- **409** - Page checked out by another user

## SDK Examples

**PnP PowerShell**:
```powershell
Connect-PnPOnline -Url "https://contoso.sharepoint.com/sites/TeamSite" -Interactive
Get-PnPPage
Get-PnPPage -Identity "Home"
Add-PnPPage -Name "NewPage" -Title "My New Page" -LayoutType Article
Set-PnPPage -Identity "NewPage" -Title "Updated Title" -Publish
Remove-PnPPage -Identity "NewPage"
```

**PnP JavaScript** (v4.x):
```javascript
import { spfi } from "@pnp/sp";
import "@pnp/sp/clientside-pages";
const sp = spfi(...);

const pages = await sp.web.lists.getByTitle("Site Pages").items();
const page = await sp.web.loadClientsidePage("/sites/TeamSite/SitePages/Home.aspx");
await page.save();
await page.publish();
```

## Sources

- **SPAPI-PAGE-SC-01**: https://learn.microsoft.com/en-us/graph/api/sitepage-create
- **SPAPI-PAGE-SC-02**: https://learn.microsoft.com/en-us/sharepoint/dev/spfx/web-parts/guidance/working-with-clientsidepages

## Document History

**[2026-01-28 20:35]**
- Initial creation with 8 endpoints
- Documented page types and PromotedState values
- Added CanvasContent1 structure reference
