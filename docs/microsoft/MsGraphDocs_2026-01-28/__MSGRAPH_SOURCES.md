# INFO: Microsoft Graph API SharePoint/OneDrive Sources

**Doc ID**: MSGRAPH-SOURCES
**Goal**: Pre-flight source inventory for MS Graph API SharePoint/OneDrive research
**Research Type**: MCPI (exhaustive source collection)
**Timeline**: Created 2026-01-28, Updates: 1

## Quick Reference

- **Total Sources Found**: 85+
- **Primary Documentation**: Microsoft Learn (learn.microsoft.com)
- **Secondary Sources**: GitHub, Developer Blogs, Community Q&A
- **PDF Resources**: None found (Microsoft uses web-based documentation)

## Source Categories

1. Overview Documentation
2. Resource Type References
3. API Method References
4. Permissions Documentation
5. Search API Documentation
6. Delta/Sync Documentation
7. Webhooks/Notifications
8. Throttling/Best Practices
9. SDK and Samples
10. Developer Community

## 1. Overview Documentation

### Conceptual Overviews

- **MSGRAPH-SC-SPOV** - SharePoint sites and content API overview
  - URL: https://learn.microsoft.com/en-us/graph/sharepoint-concept-overview
  - Content: SharePoint Graph API concepts, capabilities

- **MSGRAPH-SC-ODOV** - OneDrive file storage API overview
  - URL: https://learn.microsoft.com/en-us/graph/onedrive-concept-overview
  - Content: OneDrive Graph API concepts, file storage

- **MSGRAPH-SC-SPRES** - Working with SharePoint sites
  - URL: https://learn.microsoft.com/en-us/graph/api/resources/sharepoint?view=graph-rest-1.0
  - Content: SharePoint API root resources, URL mapping

- **MSGRAPH-SC-ODRES** - Working with files in Microsoft Graph
  - URL: https://learn.microsoft.com/en-us/graph/api/resources/onedrive?view=graph-rest-1.0
  - Content: Drive/DriveItem concepts, file operations

- **MSGRAPH-SC-ODDEV** - Access OneDrive and SharePoint via Graph
  - URL: https://learn.microsoft.com/en-us/onedrive/developer/rest-api/?view=odsp-graph-online
  - Content: OneDrive developer center, REST API entry

- **MSGRAPH-SC-RESTV2** - SharePoint REST v2 (Graph) endpoints
  - URL: https://learn.microsoft.com/en-us/sharepoint/dev/apis/sharepoint-rest-graph
  - Content: Native SharePoint REST v2 access

### Getting Started

- **MSGRAPH-SC-START** - Get started using OneDrive API
  - URL: https://learn.microsoft.com/en-us/onedrive/developer/rest-api/getting-started/?view=odsp-graph-online
  - Content: Quick start, authentication setup

- **MSGRAPH-SC-USEAPI** - Use the Microsoft Graph API
  - URL: https://learn.microsoft.com/en-us/graph/use-the-api
  - Content: RESTful API patterns, query parameters

## 2. Resource Type References

### Core Resources

- **MSGRAPH-SC-SITE** - site resource type
  - URL: https://learn.microsoft.com/en-us/graph/api/resources/site?view=graph-rest-1.0
  - Content: Site properties, methods, relationships

- **MSGRAPH-SC-LIST** - list resource type
  - URL: https://learn.microsoft.com/en-us/graph/api/resources/list?view=graph-rest-1.0
  - Content: List properties, templates, methods

- **MSGRAPH-SC-LSTITM** - listItem resource type
  - URL: https://learn.microsoft.com/en-us/graph/api/resources/listitem?view=graph-rest-1.0
  - Content: ListItem CRUD, field values

- **MSGRAPH-SC-DRIVE** - drive resource type
  - URL: https://learn.microsoft.com/en-us/graph/api/resources/drive?view=graph-rest-1.0
  - Content: Drive properties, quota, relationships

- **MSGRAPH-SC-DRITM** - driveItem resource type
  - URL: https://learn.microsoft.com/en-us/graph/api/resources/driveitem?view=graph-rest-1.0
  - Content: DriveItem methods, facets, properties

- **MSGRAPH-SC-PERM** - permission resource type
  - URL: https://learn.microsoft.com/en-us/graph/api/resources/permission?view=graph-rest-1.0
  - Content: Sharing permissions, links, invitations

### Schema Resources

- **MSGRAPH-SC-CTYPE** - contentType resource type
  - URL: https://learn.microsoft.com/en-us/graph/api/resources/contenttype?view=graph-rest-1.0
  - Content: Content types, publishing, columns

- **MSGRAPH-SC-COLDEF** - columnDefinition resource type
  - URL: https://learn.microsoft.com/en-us/graph/api/resources/columndefinition?view=graph-rest-1.0
  - Content: Column types, properties, creation

- **MSGRAPH-SC-FLDVAL** - fieldValueSet resource type
  - URL: https://learn.microsoft.com/en-us/graph/api/resources/fieldvalueset?view=graph-rest-1.0
  - Content: List item field values

### Supporting Resources

- **MSGRAPH-SC-THUMB** - thumbnail resource type
  - URL: https://learn.microsoft.com/en-us/graph/api/resources/thumbnail?view=graph-rest-1.0
  - Content: Thumbnail properties

- **MSGRAPH-SC-THUMBSET** - thumbnailSet resource type
  - URL: https://learn.microsoft.com/en-us/graph/api/resources/thumbnailset?view=graph-rest-1.0
  - Content: Thumbnail set (small, medium, large)

- **MSGRAPH-SC-ITEMREF** - itemReference resource type
  - URL: https://learn.microsoft.com/en-us/graph/api/resources/itemreference?view=graph-rest-1.0
  - Content: Item references for navigation

- **MSGRAPH-SC-SPIDS** - sharepointIds resource type
  - URL: https://learn.microsoft.com/en-us/graph/api/resources/sharepointids?view=graph-rest-1.0
  - Content: SharePoint-specific IDs

- **MSGRAPH-SC-SITECOL** - siteCollection resource type
  - URL: https://learn.microsoft.com/en-us/graph/api/resources/sitecollection?view=graph-rest-1.0
  - Content: Site collection properties

- **MSGRAPH-SC-QUOTA** - quota resource type
  - URL: https://learn.microsoft.com/en-us/graph/api/resources/quota?view=graph-rest-1.0
  - Content: Storage quota information

## 3. API Method References

### Site Methods

- **MSGRAPH-SC-SITEGET** - Get site
  - URL: https://learn.microsoft.com/en-us/graph/api/site-get?view=graph-rest-1.0
  - Content: Get site by ID, path, hostname

- **MSGRAPH-SC-SITELIST** - List sites
  - URL: https://learn.microsoft.com/en-us/graph/api/site-list?view=graph-rest-1.0
  - Content: Search/list sites

- **MSGRAPH-SC-SITEALL** - List all sites
  - URL: https://learn.microsoft.com/en-us/graph/api/site-getallsites?view=graph-rest-1.0
  - Content: Get all sites across geographies

- **MSGRAPH-SC-SITESUB** - List subsites
  - URL: https://learn.microsoft.com/en-us/graph/api/site-list-subsites?view=graph-rest-1.0
  - Content: Get child sites

- **MSGRAPH-SC-SITESRCH** - Search sites
  - URL: https://learn.microsoft.com/en-us/graph/api/site-search?view=graph-rest-1.0
  - Content: Search for sites by keyword

- **MSGRAPH-SC-SITEDELTA** - Site delta
  - URL: https://learn.microsoft.com/en-us/graph/api/site-delta?view=graph-rest-1.0
  - Content: Track site changes

- **MSGRAPH-SC-SITEFOLLOW** - Follow site
  - URL: https://learn.microsoft.com/en-us/graph/api/site-follow?view=graph-rest-1.0
  - Content: Follow/unfollow sites

- **MSGRAPH-SC-SITEPERM** - Site permissions
  - URL: https://learn.microsoft.com/en-us/graph/api/site-list-permissions?view=graph-rest-1.0
  - Content: Site permission management

### List Methods

- **MSGRAPH-SC-LISTGET** - Get list
  - URL: https://learn.microsoft.com/en-us/graph/api/list-get?view=graph-rest-1.0
  - Content: Get list by ID or title

- **MSGRAPH-SC-LISTLST** - List lists
  - URL: https://learn.microsoft.com/en-us/graph/api/list-list?view=graph-rest-1.0
  - Content: Get lists in site

- **MSGRAPH-SC-LISTCRT** - Create list
  - URL: https://learn.microsoft.com/en-us/graph/api/list-create?view=graph-rest-1.0
  - Content: Create new list

### ListItem Methods

- **MSGRAPH-SC-ITMLIST** - List items
  - URL: https://learn.microsoft.com/en-us/graph/api/listitem-list?view=graph-rest-1.0
  - Content: Get items with field expansion

- **MSGRAPH-SC-ITMGET** - Get item
  - URL: https://learn.microsoft.com/en-us/graph/api/listitem-get?view=graph-rest-1.0
  - Content: Get single item

- **MSGRAPH-SC-ITMCRT** - Create item
  - URL: https://learn.microsoft.com/en-us/graph/api/listitem-create?view=graph-rest-1.0
  - Content: Create list item

- **MSGRAPH-SC-ITMUPD** - Update item
  - URL: https://learn.microsoft.com/en-us/graph/api/listitem-update?view=graph-rest-1.0
  - Content: Update item fields

- **MSGRAPH-SC-ITMDEL** - Delete item
  - URL: https://learn.microsoft.com/en-us/graph/api/listitem-delete?view=graph-rest-1.0
  - Content: Delete list item

- **MSGRAPH-SC-ITMDELTA** - Item delta
  - URL: https://learn.microsoft.com/en-us/graph/api/listitem-delta?view=graph-rest-1.0
  - Content: Track item changes

### Drive Methods

- **MSGRAPH-SC-DRVGET** - Get drive
  - URL: https://learn.microsoft.com/en-us/graph/api/drive-get?view=graph-rest-1.0
  - Content: Get drive by various paths

- **MSGRAPH-SC-DRVLIST** - List drives
  - URL: https://learn.microsoft.com/en-us/graph/api/drive-list?view=graph-rest-1.0
  - Content: List available drives

- **MSGRAPH-SC-DRVSPEC** - Get special folder
  - URL: https://learn.microsoft.com/en-us/graph/api/drive-get-specialfolder?view=graph-rest-1.0
  - Content: Access special folders

### DriveItem Methods

- **MSGRAPH-SC-DIGET** - Get driveItem
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-get?view=graph-rest-1.0
  - Content: Get item by ID or path

- **MSGRAPH-SC-DICHLD** - List children
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-list-children?view=graph-rest-1.0
  - Content: List folder contents

- **MSGRAPH-SC-DICRT** - Create folder
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-post-children?view=graph-rest-1.0
  - Content: Create folder

- **MSGRAPH-SC-DIUPD** - Update driveItem
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-update?view=graph-rest-1.0
  - Content: Update metadata, move

- **MSGRAPH-SC-DIDEL** - Delete driveItem
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-delete?view=graph-rest-1.0
  - Content: Delete to recycle bin

- **MSGRAPH-SC-DIPERM** - Permanent delete
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-permanentdelete?view=graph-rest-1.0
  - Content: Permanently delete

- **MSGRAPH-SC-DIRST** - Restore driveItem
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-restore?view=graph-rest-1.0
  - Content: Restore from recycle bin

- **MSGRAPH-SC-DICOPY** - Copy driveItem
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-copy?view=graph-rest-1.0
  - Content: Async copy operation

- **MSGRAPH-SC-DIMOVE** - Move driveItem
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-move?view=graph-rest-1.0
  - Content: Move to new parent

- **MSGRAPH-SC-DISRCH** - Search driveItem
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-search?view=graph-rest-1.0
  - Content: Search within drive

- **MSGRAPH-SC-DIDELTA** - DriveItem delta
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-delta?view=graph-rest-1.0
  - Content: Track file changes

### Upload/Download Methods

- **MSGRAPH-SC-UPLOAD** - Upload small file
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-put-content?view=graph-rest-1.0
  - Content: Upload up to 4MB

- **MSGRAPH-SC-UPLSESS** - Create upload session
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-createuploadsession?view=graph-rest-1.0
  - Content: Large file upload

- **MSGRAPH-SC-DLOAD** - Download content
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-get-content?view=graph-rest-1.0
  - Content: Download file

- **MSGRAPH-SC-DLFMT** - Download format
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-get-content-format?view=graph-rest-1.0
  - Content: Convert and download

### Versioning Methods

- **MSGRAPH-SC-VERLST** - List versions
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-list-versions?view=graph-rest-1.0
  - Content: Get version history

- **MSGRAPH-SC-VERGET** - Get version
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitemversion-get?view=graph-rest-1.0
  - Content: Get specific version

- **MSGRAPH-SC-VERRST** - Restore version
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitemversion-restore?view=graph-rest-1.0
  - Content: Restore previous version

### Check In/Out Methods

- **MSGRAPH-SC-CHKOUT** - Checkout
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-checkout?view=graph-rest-1.0
  - Content: Check out file

- **MSGRAPH-SC-CHKIN** - Checkin
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-checkin?view=graph-rest-1.0
  - Content: Check in file

- **MSGRAPH-SC-DISCARD** - Discard checkout
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-discardcheckout?view=graph-rest-1.0
  - Content: Discard changes

### Preview/Thumbnail Methods

- **MSGRAPH-SC-PREVIEW** - Preview driveItem
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-preview?view=graph-rest-1.0
  - Content: Get embeddable preview

- **MSGRAPH-SC-THUMBS** - List thumbnails
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-list-thumbnails?view=graph-rest-1.0
  - Content: Get thumbnails

### Sharing/Permission Methods

- **MSGRAPH-SC-CRLINK** - Create sharing link
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-createlink?view=graph-rest-1.0
  - Content: Create sharing links

- **MSGRAPH-SC-INVITE** - Invite (add permissions)
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-invite?view=graph-rest-1.0
  - Content: Share with users

- **MSGRAPH-SC-LSTPERM** - List permissions
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-list-permissions?view=graph-rest-1.0
  - Content: Get sharing permissions

- **MSGRAPH-SC-GETPERM** - Get permission
  - URL: https://learn.microsoft.com/en-us/graph/api/permission-get?view=graph-rest-1.0
  - Content: Get specific permission

- **MSGRAPH-SC-UPDPERM** - Update permission
  - URL: https://learn.microsoft.com/en-us/graph/api/permission-update?view=graph-rest-1.0
  - Content: Update permission roles

- **MSGRAPH-SC-DELPERM** - Delete permission
  - URL: https://learn.microsoft.com/en-us/graph/api/permission-delete?view=graph-rest-1.0
  - Content: Remove permission

- **MSGRAPH-SC-GRANT** - Grant access
  - URL: https://learn.microsoft.com/en-us/graph/api/permission-grant?view=graph-rest-1.0
  - Content: Grant via sharing link

### Label Methods

- **MSGRAPH-SC-EXTSENS** - Extract sensitivity labels
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-extractsensitivitylabels?view=graph-rest-1.0
  - Content: Get applied labels

- **MSGRAPH-SC-ASNSENS** - Assign sensitivity label
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-assignsensitivitylabel?view=graph-rest-1.0
  - Content: Apply sensitivity label

- **MSGRAPH-SC-GETRET** - Get retention label
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-getretentionlabel?view=graph-rest-1.0
  - Content: Get retention label

- **MSGRAPH-SC-SETRET** - Set retention label
  - URL: https://learn.microsoft.com/en-us/graph/api/driveitem-setretentionlabel?view=graph-rest-1.0
  - Content: Apply retention label

### Content Type Methods

- **MSGRAPH-SC-CTLIST** - List content types
  - URL: https://learn.microsoft.com/en-us/graph/api/site-list-contenttypes?view=graph-rest-1.0
  - Content: Get site content types

- **MSGRAPH-SC-CTGET** - Get content type
  - URL: https://learn.microsoft.com/en-us/graph/api/contenttype-get?view=graph-rest-1.0
  - Content: Get specific content type

- **MSGRAPH-SC-CTCRT** - Create content type
  - URL: https://learn.microsoft.com/en-us/graph/api/site-post-contenttypes?view=graph-rest-1.0
  - Content: Create content type

- **MSGRAPH-SC-CTPUB** - Publish content type
  - URL: https://learn.microsoft.com/en-us/graph/api/contenttype-publish?view=graph-rest-1.0
  - Content: Publish to hub

### Column Methods

- **MSGRAPH-SC-COLLST** - List columns
  - URL: https://learn.microsoft.com/en-us/graph/api/site-list-columns?view=graph-rest-1.0
  - Content: Get site columns

- **MSGRAPH-SC-COLGET** - Get column
  - URL: https://learn.microsoft.com/en-us/graph/api/columndefinition-get?view=graph-rest-1.0
  - Content: Get column definition

- **MSGRAPH-SC-COLCRT** - Create column
  - URL: https://learn.microsoft.com/en-us/graph/api/site-post-columns?view=graph-rest-1.0
  - Content: Create column

### Page Methods

- **MSGRAPH-SC-PGCRT** - Create page
  - URL: https://learn.microsoft.com/en-us/graph/api/sitepage-create?view=graph-rest-1.0
  - Content: Create SharePoint page

- **MSGRAPH-SC-PGLST** - List pages
  - URL: https://learn.microsoft.com/en-us/graph/api/basesitepage-list?view=graph-rest-1.0
  - Content: List site pages

## 4. Permissions Documentation

- **MSGRAPH-SC-PERMREF** - Microsoft Graph permissions reference
  - URL: https://learn.microsoft.com/en-us/graph/permissions-reference
  - Content: All Graph permissions

- **MSGRAPH-SC-PERMOV** - Permissions overview
  - URL: https://learn.microsoft.com/en-us/graph/permissions-overview
  - Content: Permission types, consent

- **MSGRAPH-SC-ODPERM** - OneDrive permission scopes
  - URL: https://learn.microsoft.com/en-us/onedrive/developer/rest-api/concepts/permissions_reference?view=odsp-graph-online
  - Content: OneDrive-specific scopes

- **MSGRAPH-SC-SELPR** - Selected permissions overview
  - URL: https://learn.microsoft.com/en-us/graph/permissions-selected-overview
  - Content: Sites.Selected, Files.Selected

## 5. Search API Documentation

- **MSGRAPH-SC-SRCHOV** - Microsoft Search API overview
  - URL: https://learn.microsoft.com/en-us/graph/search-concept-overview
  - Content: Search concepts

- **MSGRAPH-SC-SRCHFL** - Search OneDrive and SharePoint
  - URL: https://learn.microsoft.com/en-us/graph/search-concept-files
  - Content: File/folder search, KQL

- **MSGRAPH-SC-SRCHAPI** - Search API overview
  - URL: https://learn.microsoft.com/en-us/graph/api/resources/search-api-overview?view=graph-rest-1.0
  - Content: Search API reference

## 6. Delta/Sync Documentation

- **MSGRAPH-SC-DELTAOV** - Delta query overview
  - URL: https://learn.microsoft.com/en-us/graph/delta-query-overview
  - Content: Track changes concepts

- **MSGRAPH-SC-SCANGD** - Scan guidance best practices
  - URL: https://learn.microsoft.com/en-us/onedrive/developer/rest-api/concepts/scan-guidance?view=odsp-graph-online
  - Content: Large-scale scanning

- **MSGRAPH-SC-DRSYNC** - Sync drive contents
  - URL: https://learn.microsoft.com/en-us/onedrive/developer/rest-api/api/driveitem_delta?view=odsp-graph-online
  - Content: OneDrive delta sync

## 7. Webhooks/Notifications

- **MSGRAPH-SC-CHGOV** - Change notifications overview
  - URL: https://learn.microsoft.com/en-us/graph/api/resources/change-notifications-api-overview?view=graph-rest-1.0
  - Content: Notification concepts

- **MSGRAPH-SC-WEBHOOK** - Webhooks delivery
  - URL: https://learn.microsoft.com/en-us/graph/change-notifications-delivery-webhooks
  - Content: Webhook setup

- **MSGRAPH-SC-SUBSCR** - Subscription resource
  - URL: https://learn.microsoft.com/en-us/graph/api/resources/subscription?view=graph-rest-1.0
  - Content: Subscription properties

- **MSGRAPH-SC-SUBCRT** - Create subscription
  - URL: https://learn.microsoft.com/en-us/graph/api/subscription-post-subscriptions?view=graph-rest-1.0
  - Content: Create webhook

- **MSGRAPH-SC-NOTOV** - Notifications overview
  - URL: https://learn.microsoft.com/en-us/graph/change-notifications-overview
  - Content: Change notification setup

## 8. Throttling/Best Practices

- **MSGRAPH-SC-THRTL** - Throttling guidance
  - URL: https://learn.microsoft.com/en-us/graph/throttling
  - Content: Throttling patterns

- **MSGRAPH-SC-THRLIM** - Throttling limits
  - URL: https://learn.microsoft.com/en-us/graph/throttling-limits
  - Content: Service-specific limits

- **MSGRAPH-SC-SPTHRT** - SharePoint throttling
  - URL: https://learn.microsoft.com/en-us/sharepoint/dev/general-development/how-to-avoid-getting-throttled-or-blocked-in-sharepoint-online
  - Content: Avoid throttling

- **MSGRAPH-SC-BATCH** - JSON batching
  - URL: https://learn.microsoft.com/en-us/graph/json-batching
  - Content: Batch requests

- **MSGRAPH-SC-BATSDK** - SDK batch requests
  - URL: https://learn.microsoft.com/en-us/graph/sdks/batch-requests
  - Content: SDK batching

- **MSGRAPH-SC-LONGOP** - Long-running operations
  - URL: https://learn.microsoft.com/en-us/graph/long-running-actions-overview
  - Content: Monitor async operations

## 9. SDK and Samples

- **MSGRAPH-SC-SAMPLES** - OneDrive sample code
  - URL: https://learn.microsoft.com/en-us/onedrive/developer/sample-code?view=odsp-graph-online
  - Content: Code samples

- **MSGRAPH-SC-GHCOMM** - OneDrive community samples
  - URL: https://github.com/OneDrive/onedrive-community-samples
  - Content: GitHub samples repo

- **MSGRAPH-SC-GHTOPIC** - Microsoft Graph API GitHub topic
  - URL: https://github.com/topics/microsoft-graph-api
  - Content: Community projects

- **MSGRAPH-SC-SPEMB** - SharePoint Embedded preview
  - URL: https://learn.microsoft.com/en-us/sharepoint/dev/embedded/development/tutorials/using-file-preview
  - Content: File preview tutorial

## 10. Developer Community

- **MSGRAPH-SC-DEVBLOG** - Microsoft 365 Dev Blog
  - URL: https://devblogs.microsoft.com/microsoft365dev/
  - Content: Announcements, tutorials

- **MSGRAPH-SC-QA** - Microsoft Q&A
  - URL: https://learn.microsoft.com/en-us/answers/topics/microsoft-graph-api.html
  - Content: Community Q&A

- **MSGRAPH-SC-REDDIT** - r/GraphAPI
  - URL: https://www.reddit.com/r/GraphAPI/
  - Content: Community discussions

## Known Limitations

### Not Available via Graph API [VERIFIED]

- **Create sites** - Cannot create new SharePoint sites (use SharePoint REST or CSOM)
- **Recycle bin management** - Limited recycle bin access (use SharePoint REST API)
- **Managed metadata columns** - Cannot create/update taxonomy fields (known limitation)
- **Wiki page content** - Cannot retrieve wiki page content
- **Full term store management** - Limited taxonomy/term store operations

### Beta-Only Features

- List sensitivity labels: `GET /security/informationProtection/sensitivityLabels` (beta)
- listItem:createLink: Create sharing links for list items (beta)

## PDF Resources

**Finding**: Microsoft does not provide PDF documentation for Graph API. All documentation is web-based on Microsoft Learn with:
- Version selectors (v1.0, beta)
- Language-specific SDK examples
- Interactive try-it features via Graph Explorer

## Recommended Reading Order

1. **Start** - MSGRAPH-SC-SPOV, MSGRAPH-SC-ODOV (conceptual overviews)
2. **Resources** - MSGRAPH-SC-SITE, MSGRAPH-SC-DRIVE, MSGRAPH-SC-DRITM (core types)
3. **Permissions** - MSGRAPH-SC-PERMREF, MSGRAPH-SC-SELPR (permission scopes)
4. **Methods** - Individual API method pages as needed
5. **Best Practices** - MSGRAPH-SC-THRTL, MSGRAPH-SC-SCANGD (throttling, scanning)

## Document History

**[2026-01-28 16:00]**
- Fixed: Converted Markdown tables to lists per GLOBAL-RULES
- Added: Timeline field

**[2026-01-28 15:45]**
- Initial source inventory created
- Documented 85+ sources across 10 categories
- Added known limitations and beta-only features
- Confirmed no PDF documentation available
