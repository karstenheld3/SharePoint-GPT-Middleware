# INFO: Microsoft Graph API - SitePage Methods

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for SitePage methods for SharePoint page management
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_MSGRAPH-IN00_TOC.md [MSGRAPH-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Automate news article creation and publishing workflows
- Build content management systems that create SharePoint pages
- Migrate page content between sites or tenants
- Create templated pages with consistent layouts
- Implement page approval workflows with draft/publish states
- Generate landing pages dynamically from external data

**Key findings**:
- Pages created as drafts - must explicitly call publish endpoint
- Only specific web parts supported via Graph API (text, image, standard)
- Must include `@odata.type=#microsoft.graph.sitePage` in update requests
- Two promotion types: `page` (standard) and `newsPost` (appears in news feeds)
- Canvas layout defines page structure with sections and web parts
- Title area supports gradient effects, author display, and header images

## Quick Reference Summary

**Endpoints covered**: 6 sitePage methods

- `GET /sites/{id}/pages` - List all pages
- `GET /sites/{id}/pages/{id}` - Get page
- `POST /sites/{id}/pages` - Create page
- `PATCH /sites/{id}/pages/{id}` - Update page
- `DELETE /sites/{id}/pages/{id}` - Delete page
- `POST /sites/{id}/pages/{id}/publish` - Publish page

**Permissions required**:
- Delegated: `Sites.Read.All` (read), `Sites.ReadWrite.All` (write)
- Application: `Sites.Read.All` (read), `Sites.ReadWrite.All` (write)
- **Least privilege**: `Sites.Read.All` for read operations

## SitePage Resource Type [VERIFIED]

### JSON Schema

```json
{
  "@odata.type": "#microsoft.graph.sitePage",
  "id": "string",
  "name": "string",
  "title": "string",
  "description": "string",
  "webUrl": "string",
  "createdBy": { "@odata.type": "microsoft.graph.identitySet" },
  "createdDateTime": "datetime",
  "lastModifiedBy": { "@odata.type": "microsoft.graph.identitySet" },
  "lastModifiedDateTime": "datetime",
  "contentType": { "@odata.type": "microsoft.graph.contentTypeInfo" },
  "pageLayout": "microsoftReserved | article | home | unknownFutureValue",
  "promotionKind": "page | newsPost | unknownFutureValue",
  "publishingState": { "@odata.type": "microsoft.graph.publicationFacet" },
  "reactions": { "@odata.type": "microsoft.graph.reactionsFacet" },
  "showComments": true,
  "showRecommendedPages": true,
  "titleArea": { "@odata.type": "microsoft.graph.titleArea" },
  "canvasLayout": { "@odata.type": "microsoft.graph.canvasLayout" }
}
```

### Properties [VERIFIED]

**Inherited from baseSitePage**:
- **id** (`string`) - Unique identifier
- **name** (`string`) - File name (e.g., `mypage.aspx`)
- **title** (`string`) - Page title
- **description** (`string`) - Page description
- **webUrl** (`string`) - URL of the page
- **createdBy** (`identitySet`) - Creator identity
- **createdDateTime** (`dateTimeOffset`) - Creation time
- **lastModifiedBy** (`identitySet`) - Last modifier
- **lastModifiedDateTime** (`dateTimeOffset`) - Last modification time
- **pageLayout** (`pageLayoutType`) - Layout type

**SitePage-specific**:
- **promotionKind** (`pagePromotionType`) - `page` or `newsPost`
- **publishingState** (`publicationFacet`) - Publication status
- **showComments** (`boolean`) - Enable comments
- **showRecommendedPages** (`boolean`) - Show recommendations
- **titleArea** (`titleArea`) - Title area configuration
- **canvasLayout** (`canvasLayout`) - Page canvas with web parts

### Page Layout Types [VERIFIED]

- **microsoftReserved** - System pages
- **article** - Article/news page
- **home** - Site home page
- **unknownFutureValue** - Future layouts

### Promotion Types [VERIFIED]

- **page** - Standard site page
- **newsPost** - News article (appears in news feeds)
- **unknownFutureValue** - Future types

### Publishing State [VERIFIED]

```json
{
  "level": "draft | published | checkout",
  "versionId": "string",
  "checkedOutBy": { "@odata.type": "microsoft.graph.identitySet" }
}
```

## 1. GET /sites/{id}/pages - List Pages

### Description [VERIFIED]

Gets the collection of site pages from a site. Returns all pages with pagination, sorted alphabetically by name.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/pages
```

### Path Parameters

- **siteId** (`string`) - Site identifier

### Query Parameters

- **$count** - Include count of items
- **$expand** - Expand relationships
- **$filter** - Filter results
- **$orderBy** - Sort order
- **$select** - Select properties
- **$top** - Limit results

### Request Example

```http
GET https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/pages?$select=id,name,title,webUrl
Authorization: Bearer {token}
```

### Response JSON [VERIFIED]

```json
{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#Collection(sitePage)",
  "value": [
    {
      "@odata.type": "#microsoft.graph.sitePage",
      "id": "page-guid-1",
      "name": "home.aspx",
      "title": "Home",
      "webUrl": "https://contoso.sharepoint.com/sites/sales/SitePages/home.aspx",
      "pageLayout": "home"
    },
    {
      "@odata.type": "#microsoft.graph.sitePage",
      "id": "page-guid-2",
      "name": "quarterly-report.aspx",
      "title": "Q1 Quarterly Report",
      "webUrl": "https://contoso.sharepoint.com/sites/sales/SitePages/quarterly-report.aspx",
      "pageLayout": "article",
      "promotionKind": "newsPost"
    }
  ]
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Sites
Get-MgSitePage -SiteId $siteId
```

**C#**:
```csharp
var pages = await graphClient.Sites["{site-id}"].Pages.GetAsync();
```

**JavaScript**:
```javascript
let pages = await client.api('/sites/{site-id}/pages').get();
```

**Python**:
```python
pages = await graph_client.sites.by_site_id('site-id').pages.get()
```

## 2. GET /sites/{id}/pages/{id} - Get Page

### Description [VERIFIED]

Retrieves a specific site page by ID including its canvas layout and web parts.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/pages/{pageId}
```

To get as sitePage type:
```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/pages/{pageId}/microsoft.graph.sitePage
```

### Request Example

```http
GET https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/pages/page-guid/microsoft.graph.sitePage?$expand=canvasLayout
Authorization: Bearer {token}
```

### Response JSON [VERIFIED]

```json
{
  "@odata.type": "#microsoft.graph.sitePage",
  "id": "page-guid",
  "name": "quarterly-report.aspx",
  "title": "Q1 Quarterly Report",
  "description": "Summary of Q1 results",
  "webUrl": "https://contoso.sharepoint.com/sites/sales/SitePages/quarterly-report.aspx",
  "createdDateTime": "2026-01-15T10:00:00Z",
  "lastModifiedDateTime": "2026-01-28T14:30:00Z",
  "pageLayout": "article",
  "promotionKind": "newsPost",
  "publishingState": {
    "level": "published",
    "versionId": "1.0"
  },
  "titleArea": {
    "enableGradientEffect": true,
    "imageWebUrl": "https://contoso.sharepoint.com/sites/sales/SiteAssets/header.jpg",
    "layout": "imageAndTitle",
    "showAuthor": true,
    "showPublishedDate": true,
    "textAboveTitle": "News",
    "textAlignment": "left"
  },
  "canvasLayout": {
    "horizontalSections": [
      {
        "layout": "oneColumn",
        "columns": [
          {
            "width": 12,
            "webparts": [
              {
                "@odata.type": "#microsoft.graph.textWebPart",
                "id": "webpart-guid",
                "innerHtml": "<p>Content here</p>"
              }
            ]
          }
        ]
      }
    ]
  }
}
```

## 3. POST /sites/{id}/pages - Create Page

### Description [VERIFIED]

Creates a new site page. The page is created as a draft and must be published separately.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/sites/{siteId}/pages
```

### Request Headers

- **Authorization**: `Bearer {token}`
- **Content-Type**: `application/json`

### Request Body

```json
{
  "@odata.type": "#microsoft.graph.sitePage",
  "name": "page-name.aspx",
  "title": "Page Title",
  "pageLayout": "article",
  "promotionKind": "page",
  "showComments": true,
  "showRecommendedPages": true,
  "titleArea": {
    "enableGradientEffect": true,
    "layout": "plain",
    "showAuthor": true
  },
  "canvasLayout": {
    "horizontalSections": []
  }
}
```

### Request Example

```http
POST https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/pages
Authorization: Bearer {token}
Content-Type: application/json

{
  "@odata.type": "#microsoft.graph.sitePage",
  "name": "new-announcement.aspx",
  "title": "Important Announcement",
  "pageLayout": "article",
  "promotionKind": "newsPost",
  "titleArea": {
    "enableGradientEffect": true,
    "layout": "plain",
    "showAuthor": true,
    "showPublishedDate": true
  },
  "canvasLayout": {
    "horizontalSections": [
      {
        "layout": "oneColumn",
        "columns": [
          {
            "width": 12,
            "webparts": [
              {
                "@odata.type": "#microsoft.graph.textWebPart",
                "innerHtml": "<h2>Welcome</h2><p>This is our announcement.</p>"
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### Response JSON [VERIFIED]

Returns the created sitePage object with `publishingState.level` = `draft`.

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Sites

$params = @{
    "@odata.type" = "#microsoft.graph.sitePage"
    name = "new-page.aspx"
    title = "New Page"
    pageLayout = "article"
}
New-MgSitePage -SiteId $siteId -BodyParameter $params
```

**C#**:
```csharp
var page = new SitePage
{
    Name = "new-page.aspx",
    Title = "New Page",
    PageLayout = PageLayoutType.Article
};
var result = await graphClient.Sites["{site-id}"].Pages.PostAsync(page);
```

## 4. PATCH /sites/{id}/pages/{id} - Update Page

### Description [VERIFIED]

Updates an existing site page's properties, title area, or canvas layout.

**Important**:
- Must include `@odata.type=#microsoft.graph.sitePage` in request body
- Only supported web parts can be added/modified
- Use `Accept: application/json;odata.metadata=none` header when using GET response as update body

### HTTP Request

```http
PATCH https://graph.microsoft.com/v1.0/sites/{siteId}/pages/{pageId}/microsoft.graph.sitePage
```

### Updatable Properties [VERIFIED]

- **title** - Page title
- **description** - Page description
- **showComments** - Enable/disable comments
- **showRecommendedPages** - Enable/disable recommendations
- **promotionKind** - Change to `page` or `newsPost`
- **titleArea** - Title area configuration
- **canvasLayout** - Page content and web parts

### Request Example

```http
PATCH https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/pages/page-guid/microsoft.graph.sitePage
Authorization: Bearer {token}
Content-Type: application/json

{
  "@odata.type": "#microsoft.graph.sitePage",
  "title": "Updated Title",
  "description": "Updated description",
  "showComments": false
}
```

### Response [VERIFIED]

Returns the updated sitePage object.

## 5. DELETE /sites/{id}/pages/{id} - Delete Page

### Description [VERIFIED]

Deletes a site page permanently.

### HTTP Request

```http
DELETE https://graph.microsoft.com/v1.0/sites/{siteId}/pages/{pageId}
```

### Request Example

```http
DELETE https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/pages/page-guid
Authorization: Bearer {token}
```

### Response [VERIFIED]

```http
HTTP/1.1 204 No Content
```

## 6. POST /sites/{id}/pages/{id}/publish - Publish Page

### Description [VERIFIED]

Publishes a draft page, making it visible to users with read access.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/sites/{siteId}/pages/{pageId}/microsoft.graph.sitePage/publish
```

### Request Example

```http
POST https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com,site-guid,web-guid/pages/page-guid/microsoft.graph.sitePage/publish
Authorization: Bearer {token}
```

### Response [VERIFIED]

```http
HTTP/1.1 204 No Content
```

After publishing, `publishingState.level` changes to `published`.

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Sites
Publish-MgSitePage -SiteId $siteId -BaseSitePageId $pageId
```

**C#**:
```csharp
await graphClient.Sites["{site-id}"].Pages["{page-id}"]
    .GraphSitePage
    .Publish
    .PostAsync();
```

## Supported Web Parts [VERIFIED]

Only these web parts can be added via Graph API:

- **textWebPart** - Rich text content
- **imageWebPart** - Images
- **standardWebPart** - Standard SharePoint web parts with specific IDs

Attempting to add unsupported web parts results in an error.

### TextWebPart Example

```json
{
  "@odata.type": "#microsoft.graph.textWebPart",
  "innerHtml": "<h2>Heading</h2><p>Paragraph text</p>"
}
```

### ImageWebPart Example

```json
{
  "@odata.type": "#microsoft.graph.imageWebPart",
  "serverProcessedContent": {
    "imageSources": [
      {
        "key": "imageSource",
        "value": "https://contoso.sharepoint.com/sites/sales/SiteAssets/image.jpg"
      }
    ]
  }
}
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid page structure or unsupported web part
- **401 Unauthorized** - Missing or invalid token
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Page not found
- **409 Conflict** - Page name conflict
- **429 Too Many Requests** - Rate limit exceeded

### Error Response Format

```json
{
  "error": {
    "code": "invalidRequest",
    "message": "Unsupported web part type.",
    "innerError": {
      "request-id": "guid",
      "date": "2026-01-28T12:00:00Z"
    }
  }
}
```

## Throttling Considerations [VERIFIED]

**Best Practices**:
- Cache page IDs
- Use `$select` to reduce payload
- Batch operations where possible

**Resource Units**:
- List pages: ~1 resource unit
- Get/Create/Update page: ~2-3 resource units
- Publish page: ~2 resource units

## Sources

- **MSGRAPH-PAGE-SC-01**: https://learn.microsoft.com/en-us/graph/api/resources/sitepage?view=graph-rest-1.0
- **MSGRAPH-PAGE-SC-02**: https://learn.microsoft.com/en-us/graph/api/basesitepage-list?view=graph-rest-1.0
- **MSGRAPH-PAGE-SC-03**: https://learn.microsoft.com/en-us/graph/api/sitepage-update?view=graph-rest-1.0
- **MSGRAPH-PAGE-SC-04**: https://learn.microsoft.com/en-us/graph/api/sitepage-publish?view=graph-rest-1.0

## Document History

**[2026-01-28 19:35]**
- Initial creation with 6 endpoints
- Added sitePage resource type
- Added supported web parts documentation
- Added canvas layout examples
