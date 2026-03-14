# INFO: Microsoft Graph API SharePoint/OneDrive - Endpoint TOC

**Doc ID**: MSGRAPH-TOC
**Goal**: Exhaustive Table of Contents of all MS Graph API endpoints for SharePoint/OneDrive for later detailed research
**Research Type**: MCPI (exhaustive endpoint inventory)
**Timeline**: Created 2026-01-28, Updates: 4

## Quick Reference

- **Total Endpoint Categories**: 14
- **Total Endpoints**: 140+ (some overlap between categories)
- **API Version**: v1.0 (beta endpoints marked with [BETA])
- **Base URL**: `https://graph.microsoft.com/v1.0`
- **National Clouds**: GCC High (`graph.microsoft.us`), DoD (`dod-graph.microsoft.us`), China (`microsoftgraph.chinacloudapi.cn`)

## Endpoint Categories

1. Site API (19 endpoints)
2. List API (8 endpoints)
3. ListItem API (13 endpoints)
4. Drive API (10 endpoints)
5. DriveItem API (35 endpoints)
6. Permission API (7 endpoints)
7. ContentType API (14 endpoints)
8. Column API (8 endpoints)
9. Search API (3 endpoints)
10. Subscription/Webhook API (5 endpoints)
11. RecycleBin API (4 endpoints)
12. SitePage API (6 endpoints)
13. TermStore API (10 endpoints)
14. Shares API (4 endpoints)

**Note**: Cross-tenant migration APIs (`sharePointMigrationTask`) available for tenant-to-tenant migrations - see Microsoft Graph changelog (September 2025 GA).

## Topic Files

- [`__INFO_MSGRAPH-IN01_SOURCES.md`](./__INFO_MSGRAPH-IN01_SOURCES.md) [MSGRAPH-IN01] - Source documentation
- [`_INFO_MSGRAPH-IN01_OVERVIEW.md`](./_INFO_MSGRAPH-IN01_OVERVIEW.md) [MSGRAPH-IN01] - API overview
- [`_INFO_MSGRAPH-IN01_REVIEW.md`](./_INFO_MSGRAPH-IN01_REVIEW.md) [MSGRAPH-IN01] - Review notes
- [`_INFO_MSGRAPH-IN01_SITES_CORE.md`](./_INFO_MSGRAPH-IN01_SITES_CORE.md) [MSGRAPH-IN01] - Sites core API
- [`_INFO_MSGRAPH-IN01_SITES_LISTS.md`](./_INFO_MSGRAPH-IN01_SITES_LISTS.md) [MSGRAPH-IN01] - Lists API
- [`_INFO_MSGRAPH-IN01_SITES_LISTITEMS_CORE.md`](./_INFO_MSGRAPH-IN01_SITES_LISTITEMS_CORE.md) [MSGRAPH-IN01] - ListItems core
- [`_INFO_MSGRAPH-IN01_SITES_LISTITEMS_ADV.md`](./_INFO_MSGRAPH-IN01_SITES_LISTITEMS_ADV.md) [MSGRAPH-IN01] - ListItems advanced
- [`_INFO_MSGRAPH-IN01_SITES_PERMISSIONS.md`](./_INFO_MSGRAPH-IN01_SITES_PERMISSIONS.md) [MSGRAPH-IN01] - Permissions API
- [`_INFO_MSGRAPH-IN01_SITES_CONTENTTYPES.md`](./_INFO_MSGRAPH-IN01_SITES_CONTENTTYPES.md) [MSGRAPH-IN01] - ContentTypes API
- [`_INFO_MSGRAPH-IN01_SITES_COLUMNS.md`](./_INFO_MSGRAPH-IN01_SITES_COLUMNS.md) [MSGRAPH-IN01] - Columns API
- [`_INFO_MSGRAPH-IN01_SITES_PAGES.md`](./_INFO_MSGRAPH-IN01_SITES_PAGES.md) [MSGRAPH-IN01] - SitePages API
- [`_INFO_MSGRAPH-IN01_SITES_MGMT.md`](./_INFO_MSGRAPH-IN01_SITES_MGMT.md) [MSGRAPH-IN01] - Sites management
- [`_INFO_MSGRAPH-IN01_SITES_TERMSTORE.md`](./_INFO_MSGRAPH-IN01_SITES_TERMSTORE.md) [MSGRAPH-IN01] - TermStore API
- [`_INFO_MSGRAPH-IN01_DRIVES_CORE.md`](./_INFO_MSGRAPH-IN01_DRIVES_CORE.md) [MSGRAPH-IN01] - Drives core API
- [`_INFO_MSGRAPH-IN01_DRIVES_ITEMS_CORE.md`](./_INFO_MSGRAPH-IN01_DRIVES_ITEMS_CORE.md) [MSGRAPH-IN01] - DriveItems core
- [`_INFO_MSGRAPH-IN01_DRIVES_ITEMS_OPS.md`](./_INFO_MSGRAPH-IN01_DRIVES_ITEMS_OPS.md) [MSGRAPH-IN01] - DriveItems operations
- [`_INFO_MSGRAPH-IN01_DRIVES_ITEMS_TRANSFER.md`](./_INFO_MSGRAPH-IN01_DRIVES_ITEMS_TRANSFER.md) [MSGRAPH-IN01] - DriveItems transfer
- [`_INFO_MSGRAPH-IN01_DRIVES_ITEMS_SHARING.md`](./_INFO_MSGRAPH-IN01_DRIVES_ITEMS_SHARING.md) [MSGRAPH-IN01] - DriveItems sharing
- [`_INFO_MSGRAPH-IN01_DRIVES_ITEMS_VERSIONS.md`](./_INFO_MSGRAPH-IN01_DRIVES_ITEMS_VERSIONS.md) [MSGRAPH-IN01] - DriveItems versions
- [`_INFO_MSGRAPH-IN01_DRIVES_ITEMS_CHECKINOUT.md`](./_INFO_MSGRAPH-IN01_DRIVES_ITEMS_CHECKINOUT.md) [MSGRAPH-IN01] - Check in/out
- [`_INFO_MSGRAPH-IN01_DRIVES_ITEMS_MEDIA.md`](./_INFO_MSGRAPH-IN01_DRIVES_ITEMS_MEDIA.md) [MSGRAPH-IN01] - Media handling
- [`_INFO_MSGRAPH-IN01_DRIVES_RECYCLEBIN.md`](./_INFO_MSGRAPH-IN01_DRIVES_RECYCLEBIN.md) [MSGRAPH-IN01] - RecycleBin API
- [`_INFO_MSGRAPH-IN01_SEARCH.md`](./_INFO_MSGRAPH-IN01_SEARCH.md) [MSGRAPH-IN01] - Search API
- [`_INFO_MSGRAPH-IN01_SHARES.md`](./_INFO_MSGRAPH-IN01_SHARES.md) [MSGRAPH-IN01] - Shares API
- [`_INFO_MSGRAPH-IN01_SUBSCRIPTIONS.md`](./_INFO_MSGRAPH-IN01_SUBSCRIPTIONS.md) [MSGRAPH-IN01] - Subscriptions/Webhooks

## Endpoint Reference

## 1. Site API

### Site - Core Methods

- [ ] `GET /sites/root` - Get root site
- [ ] `GET /sites/{site-id}` - Get site by ID
- [ ] `GET /sites/{hostname}:/{site-path}` - Get site by path
- [ ] `GET /sites/getAllSites` - List all sites across geographies (App-only)
- [ ] `GET /sites?search={query}` - Search for sites
- [ ] `GET /sites/{site-id}/sites` - List subsites
- [ ] `GET /groups/{group-id}/sites/root` - Get site for a group

### Site - Delta/Changes

- [ ] `GET /sites/delta` - Get site delta (App-only)

### Site - Follow

- [ ] `POST /users/{user-id}/followedSites/add` - Follow site
- [ ] `POST /users/{user-id}/followedSites/remove` - Unfollow site
- [ ] `GET /me/followedSites` - List followed sites

### Site - Analytics

- [ ] `GET /sites/{site-id}/analytics` - Get site analytics
- [ ] `GET /sites/{site-id}/getActivitiesByInterval()` - Get activities by interval

### Site - Permissions

- [ ] `GET /sites/{site-id}/permissions` - List site permissions (App-only)
- [ ] `GET /sites/{site-id}/permissions/{permission-id}` - Get site permission
- [ ] `POST /sites/{site-id}/permissions` - Create site permission
- [ ] `PATCH /sites/{site-id}/permissions/{permission-id}` - Update site permission
- [ ] `DELETE /sites/{site-id}/permissions/{permission-id}` - Delete site permission

### Site - Operations

- [ ] `GET /sites/{site-id}/operations` - List long-running operations

## 2. List API

### List - Core Methods

- [ ] `GET /sites/{site-id}/lists` - Get lists in site
- [ ] `GET /sites/{site-id}/lists/{list-id}` - Get list by ID
- [ ] `POST /sites/{site-id}/lists` - Create list
- [ ] `PATCH /sites/{site-id}/lists/{list-id}` - Update list

### List - Operations

- [ ] `GET /sites/{site-id}/lists/{list-id}/operations` - List long-running operations
- [ ] `GET /sites/{site-id}/lists/{list-id}/subscriptions/socketIo/getConnection` - Get WebSocket endpoint

### List - Content Types

- [ ] `GET /sites/{site-id}/lists/{list-id}/contentTypes` - List content types in list
- [ ] `POST /sites/{site-id}/lists/{list-id}/contentTypes` - Add content type to list

## 3. ListItem API

### ListItem - Core Methods

- [ ] `GET /sites/{site-id}/lists/{list-id}/items` - List items
- [ ] `GET /sites/{site-id}/lists/{list-id}/items/{item-id}` - Get item
- [ ] `POST /sites/{site-id}/lists/{list-id}/items` - Create item
- [ ] `PATCH /sites/{site-id}/lists/{list-id}/items/{item-id}` - Update item
- [ ] `DELETE /sites/{site-id}/lists/{list-id}/items/{item-id}` - Delete item

### ListItem - Field Values

- [ ] `GET /sites/{site-id}/lists/{list-id}/items/{item-id}/fields` - Get column values
- [ ] `PATCH /sites/{site-id}/lists/{list-id}/items/{item-id}/fields` - Update column values

### ListItem - Delta/Changes

- [ ] `GET /sites/{site-id}/lists/{list-id}/items/delta` - Get delta

### ListItem - Analytics

- [ ] `GET /sites/{site-id}/lists/{list-id}/items/{item-id}/analytics` - Get analytics
- [ ] `GET /sites/{site-id}/lists/{list-id}/items/{item-id}/getActivitiesByInterval()` - Get activities by interval

### ListItem - Document Set Versions

- [ ] `GET /sites/{site-id}/lists/{list-id}/items/{item-id}/documentSetVersions` - List document set versions
- [ ] `POST /sites/{site-id}/lists/{list-id}/items/{item-id}/documentSetVersions` - Create document set version
- [ ] `POST /sites/{site-id}/lists/{list-id}/items/{item-id}/documentSetVersions/{version-id}/restore` - Restore document set version

## 4. Drive API

### Drive - Core Methods

- [ ] `GET /drives` - List drives
- [ ] `GET /drives/{drive-id}` - Get drive by ID
- [ ] `GET /me/drive` - Get current user's OneDrive
- [ ] `GET /users/{user-id}/drive` - Get user's OneDrive
- [ ] `GET /groups/{group-id}/drive` - Get group's drive
- [ ] `GET /sites/{site-id}/drive` - Get site's default drive
- [ ] `GET /sites/{site-id}/drives` - List site's drives

### Drive - Special Folders

- [ ] `GET /me/drive/special/{name}` - Get special folder (approot, documents, photos, etc.)

### Drive - Following

- [ ] `GET /me/drive/following` - List followed items

### Drive - Bundles

- [ ] `GET /drives/{drive-id}/bundles` - List bundles (albums, document packages)

### Drive - Deprecated

- [ ] `GET /me/drive/recent` - Recent files [DEPRECATED]
- [ ] `GET /me/drive/sharedWithMe` - Shared with me [DEPRECATED]

## 5. DriveItem API

### DriveItem - Core Methods

- [ ] `GET /drives/{drive-id}/items/{item-id}` - Get item by ID
- [ ] `GET /drives/{drive-id}/root:/{path}` - Get item by path
- [ ] `GET /drives/{drive-id}/items/{item-id}/children` - List children
- [ ] `POST /drives/{drive-id}/items/{parent-id}/children` - Create folder
- [ ] `PATCH /drives/{drive-id}/items/{item-id}` - Update item metadata
- [ ] `DELETE /drives/{drive-id}/items/{item-id}` - Delete item (to recycle bin)
- [ ] `POST /drives/{drive-id}/items/{item-id}/permanentDelete` - Permanently delete
- [ ] `POST /drives/{drive-id}/items/{item-id}/restore` - Restore from recycle bin

### DriveItem - Upload/Download

- [ ] `PUT /drives/{drive-id}/items/{parent-id}:/{filename}:/content` - Upload small file (<4MB)
- [ ] `POST /drives/{drive-id}/items/{parent-id}:/{filename}:/createUploadSession` - Create upload session (large files)
- [ ] `GET /drives/{drive-id}/items/{item-id}/content` - Download file
- [ ] `GET /drives/{drive-id}/items/{item-id}/content?format={format}` - Download in specific format

### DriveItem - Copy/Move

- [ ] `POST /drives/{drive-id}/items/{item-id}/copy` - Copy item (async)
- [ ] `PATCH /drives/{drive-id}/items/{item-id}` - Move item (update parentReference)

### DriveItem - Search/Delta

- [ ] `GET /drives/{drive-id}/root/search(q='{query}')` - Search items
- [ ] `GET /drives/{drive-id}/root/delta` - Track changes (delta)

### DriveItem - Versions

- [ ] `GET /drives/{drive-id}/items/{item-id}/versions` - List versions
- [ ] `GET /drives/{drive-id}/items/{item-id}/versions/{version-id}` - Get version
- [ ] `GET /drives/{drive-id}/items/{item-id}/versions/{version-id}/content` - Download version content
- [ ] `POST /drives/{drive-id}/items/{item-id}/versions/{version-id}/restoreVersion` - Restore version

### DriveItem - Check In/Out

- [ ] `POST /drives/{drive-id}/items/{item-id}/checkout` - Check out file
- [ ] `POST /drives/{drive-id}/items/{item-id}/checkin` - Check in file
- [ ] `POST /drives/{drive-id}/items/{item-id}/discardCheckout` - Discard checkout

### DriveItem - Thumbnails/Preview

- [ ] `GET /drives/{drive-id}/items/{item-id}/thumbnails` - Get thumbnails
- [ ] `POST /drives/{drive-id}/items/{item-id}/preview` - Get preview URL

### DriveItem - Follow

- [ ] `POST /drives/{drive-id}/items/{item-id}/follow` - Follow item
- [ ] `POST /drives/{drive-id}/items/{item-id}/unfollow` - Unfollow item

### DriveItem - Sharing/Permissions

- [ ] `POST /drives/{drive-id}/items/{item-id}/createLink` - Create sharing link
- [ ] `POST /drives/{drive-id}/items/{item-id}/invite` - Add permissions (invite)
- [ ] `GET /drives/{drive-id}/items/{item-id}/permissions` - List permissions
- [ ] `GET /drives/{drive-id}/items/{item-id}/permissions/{perm-id}` - Get permission
- [ ] `PATCH /drives/{drive-id}/items/{item-id}/permissions/{perm-id}` - Update permission
- [ ] `DELETE /drives/{drive-id}/items/{item-id}/permissions/{perm-id}` - Delete permission

### DriveItem - Labels

- [ ] `POST /drives/{drive-id}/items/{item-id}/extractSensitivityLabels` - Extract sensitivity labels
- [ ] `POST /drives/{drive-id}/items/{item-id}/assignSensitivityLabel` - Assign sensitivity label
- [ ] `GET /drives/{drive-id}/items/{item-id}/retentionLabel` - Get retention label
- [ ] `PATCH /drives/{drive-id}/items/{item-id}/retentionLabel` - Set retention label
- [ ] `DELETE /drives/{drive-id}/items/{item-id}/retentionLabel` - Remove retention label
- [ ] `POST /drives/{drive-id}/items/{item-id}/lockOrUnlockRecord` - Lock/unlock record

### DriveItem - Analytics

- [ ] `GET /drives/{drive-id}/items/{item-id}/analytics` - Get analytics

## 6. Permission API

**Note**: DriveItem permission endpoints also listed in Section 5 (DriveItem - Sharing/Permissions). This section consolidates permission-related endpoints.

**LIMITATION - SharePoint Site Groups**: Microsoft Graph API does NOT provide endpoints for SharePoint site groups (Owners, Members, Visitors). To access SharePoint groups and their members, use SharePoint REST API (`/_api/web/sitegroups`) or CSOM.

### Permission - Site Level

- [ ] `GET /sites/{site-id}/permissions` - List site permissions (App-only)
- [ ] `GET /sites/{site-id}/permissions/{permission-id}` - Get site permission
- [ ] `POST /sites/{site-id}/permissions` - Create site permission
- [ ] `PATCH /sites/{site-id}/permissions/{permission-id}` - Update site permission
- [ ] `DELETE /sites/{site-id}/permissions/{permission-id}` - Delete site permission

### Permission - DriveItem Level

- [ ] `POST /drives/{drive-id}/items/{item-id}/permissions/{perm-id}/grant` - Grant access via sharing link

### Permission - ListItem Level [BETA]

- [ ] `POST /sites/{site-id}/lists/{list-id}/items/{item-id}/createLink` - Create sharing link [BETA]

## 7. ContentType API

### ContentType - Site Level

- [ ] `GET /sites/{site-id}/contentTypes` - List content types in site
- [ ] `GET /sites/{site-id}/contentTypes/{contentType-id}` - Get content type
- [ ] `POST /sites/{site-id}/contentTypes` - Create content type
- [ ] `PATCH /sites/{site-id}/contentTypes/{contentType-id}` - Update content type
- [ ] `DELETE /sites/{site-id}/contentTypes/{contentType-id}` - Delete content type

### ContentType - List Level

- [ ] `GET /sites/{site-id}/lists/{list-id}/contentTypes` - List content types in list
- [ ] `POST /sites/{site-id}/lists/{list-id}/contentTypes/addCopy` - Add content type copy to list

### ContentType - Publishing

- [ ] `POST /sites/{site-id}/contentTypes/{contentType-id}/publish` - Publish content type
- [ ] `POST /sites/{site-id}/contentTypes/{contentType-id}/unpublish` - Unpublish content type
- [ ] `GET /sites/{site-id}/contentTypes/{contentType-id}/isPublished` - Check if published
- [ ] `POST /sites/{site-id}/contentTypes/{contentType-id}/associateWithHubSites` - Associate with hub sites
- [ ] `POST /sites/{site-id}/contentTypes/{contentType-id}/copyToDefaultContentLocation` - Copy to default location

### ContentType - Hub

- [ ] `GET /sites/{site-id}/getCompatibleHubContentTypes` - Get compatible hub content types
- [ ] `POST /sites/{site-id}/contentTypes/addCopyFromContentTypeHub` - Add copy from content type hub

## 8. Column API

**Limitation**: Managed Metadata (Taxonomy) columns CANNOT be created or updated via Graph API. Use SharePoint CSOM/REST for taxonomy column operations.

### Column - Site Level

- [ ] `GET /sites/{site-id}/columns` - List site columns
- [ ] `GET /sites/{site-id}/columns/{column-id}` - Get site column
- [ ] `POST /sites/{site-id}/columns` - Create site column
- [ ] `PATCH /sites/{site-id}/columns/{column-id}` - Update site column
- [ ] `DELETE /sites/{site-id}/columns/{column-id}` - Delete site column

### Column - List Level

- [ ] `GET /sites/{site-id}/lists/{list-id}/columns` - List list columns
- [ ] `POST /sites/{site-id}/lists/{list-id}/columns` - Create list column

### Column - ContentType Level

- [ ] `GET /sites/{site-id}/contentTypes/{contentType-id}/columns` - List columns in content type
- [ ] `POST /sites/{site-id}/contentTypes/{contentType-id}/columns` - Add column to content type

## 9. Search API

### Microsoft Search

- [ ] `POST /search/query` - Search across SharePoint/OneDrive (unified search)

### DriveItem Search

- [ ] `GET /drives/{drive-id}/root/search(q='{query}')` - Search within drive
- [ ] `GET /me/drive/root/search(q='{query}')` - Search user's OneDrive

## 10. Subscription/Webhook API

### Subscriptions

- [ ] `GET /subscriptions` - List subscriptions
- [ ] `GET /subscriptions/{subscription-id}` - Get subscription
- [ ] `POST /subscriptions` - Create subscription
- [ ] `PATCH /subscriptions/{subscription-id}` - Update subscription (renew)
- [ ] `DELETE /subscriptions/{subscription-id}` - Delete subscription

### Supported Resources for Subscriptions

- `/drives/{drive-id}/root` - OneDrive/SharePoint drive changes
- `/sites/{site-id}/lists/{list-id}` - SharePoint list changes
- `/users/{user-id}/drive/root` - User's OneDrive changes

## 11. RecycleBin API [BETA]

**Note**: DriveItem restore (`POST .../items/{item-id}/restore`) in Section 5 restores deleted items. This RecycleBin API provides dedicated endpoints for listing and managing recycle bin contents.

### RecycleBin Methods

- [ ] `GET /drives/{drive-id}/recycleBin/items` - List recycle bin items [BETA]
- [ ] `GET /drives/{drive-id}/recycleBin/items/{item-id}` - Get recycle bin item [BETA]
- [ ] `POST /drives/{drive-id}/recycleBin/items/{item-id}/restore` - Restore from recycle bin [BETA]
- [ ] `DELETE /drives/{drive-id}/recycleBin/items/{item-id}` - Permanently delete from recycle bin [BETA]

## 12. SitePage API

### SitePage Methods

- [ ] `GET /sites/{site-id}/pages` - List pages
- [ ] `GET /sites/{site-id}/pages/{page-id}` - Get page
- [ ] `POST /sites/{site-id}/pages` - Create page
- [ ] `PATCH /sites/{site-id}/pages/{page-id}` - Update page
- [ ] `DELETE /sites/{site-id}/pages/{page-id}` - Delete page
- [ ] `POST /sites/{site-id}/pages/{page-id}/publish` - Publish page

## 13. Shares API

### Shares - Access Shared Items

- [ ] `GET /shares/{shareIdOrEncodedUrl}` - Access shared item via sharing URL
- [ ] `GET /shares/{shareId}/driveItem` - Get shared driveItem directly
- [ ] `GET /shares/{shareId}/root` - Get root of shared folder
- [ ] `POST /shares/{shareId}/permission/grant` - Grant access to users via sharing link

**Note**: Sharing URLs must be base64-encoded with `u!` prefix. See Microsoft docs for encoding algorithm.

## 14. TermStore API

### TermStore - Core Methods

- [ ] `GET /sites/{site-id}/termStore` - Get default term store
- [ ] `GET /sites/{site-id}/termStores` - List term stores
- [ ] `GET /sites/{site-id}/termStore/groups` - List term groups
- [ ] `GET /sites/{site-id}/termStore/groups/{group-id}` - Get term group
- [ ] `GET /sites/{site-id}/termStore/groups/{group-id}/sets` - List term sets
- [ ] `GET /sites/{site-id}/termStore/sets/{set-id}` - Get term set
- [ ] `GET /sites/{site-id}/termStore/sets/{set-id}/terms` - List terms
- [ ] `GET /sites/{site-id}/termStore/sets/{set-id}/terms/{term-id}` - Get term
- [ ] `GET /sites/{site-id}/termStore/sets/{set-id}/children` - List child terms
- [ ] `GET /sites/{site-id}/termStore/sets/{set-id}/relations` - List term relations

**Limitation**: Read-only in most scenarios. Creating/updating terms requires specific permissions and may have limited support.

## Research Priority

### High Priority (Core Operations)

1. DriveItem API - File operations, uploads, downloads
2. Site API - Site access and permissions
3. ListItem API - List data operations
4. Permission API - Sharing and access control

### Medium Priority (Management)

5. ContentType API - Schema management
6. Column API - Field definitions
7. Search API - Content discovery
8. Subscription API - Change notifications

### Lower Priority (Specialized)

9. RecycleBin API - Retention and recovery
10. SitePage API - Page management
11. Analytics endpoints - Usage tracking
12. Label endpoints - Compliance

## Sources

- **MSGRAPH-TOC-SC-01**: https://learn.microsoft.com/en-us/graph/api/resources/site?view=graph-rest-1.0
- **MSGRAPH-TOC-SC-02**: https://learn.microsoft.com/en-us/graph/api/resources/driveitem?view=graph-rest-1.0
- **MSGRAPH-TOC-SC-03**: https://learn.microsoft.com/en-us/graph/api/resources/list?view=graph-rest-1.0
- **MSGRAPH-TOC-SC-04**: https://learn.microsoft.com/en-us/graph/api/resources/listitem?view=graph-rest-1.0
- **MSGRAPH-TOC-SC-05**: https://learn.microsoft.com/en-us/graph/api/resources/drive?view=graph-rest-1.0
- **MSGRAPH-TOC-SC-06**: https://learn.microsoft.com/en-us/graph/api/resources/contenttype?view=graph-rest-1.0
- **MSGRAPH-TOC-SC-07**: https://learn.microsoft.com/en-us/graph/api/resources/columndefinition?view=graph-rest-1.0
- **MSGRAPH-TOC-SC-08**: https://learn.microsoft.com/en-us/graph/sharepoint-concept-overview
- **MSGRAPH-TOC-SC-09**: https://learn.microsoft.com/en-us/graph/onedrive-concept-overview
- **MSGRAPH-TOC-SC-10**: https://learn.microsoft.com/en-us/graph/api/resources/permission?view=graph-rest-1.0
- **MSGRAPH-TOC-SC-11**: https://learn.microsoft.com/en-us/graph/api/shares-get?view=graph-rest-1.0
- **MSGRAPH-TOC-SC-12**: https://learn.microsoft.com/en-us/graph/api/driveitem-list-permissions?view=graph-rest-1.0

## Document History

**[2026-01-28 18:00]**
- Added: National cloud endpoints note in Quick Reference
- Added: Cross-tenant migration API note
- Reconcile: 2 confirmed, 6 dismissed from RV02 review

**[2026-01-28 17:50]**
- Added: Section 13 - Shares API (4 endpoints for accessing shared items via URL)
- Added: Permission API limitation note - SharePoint site groups (Owners/Members/Visitors) NOT available via Graph API
- Fixed: Updated endpoint count to 140+, category count to 14
- Research: Verified file/folder/site permission coverage is complete for Graph API

**[2026-01-28 17:20]**
- Added: Section 14 - TermStore API (10 endpoints for taxonomy/managed metadata)
- Added: Column API limitation note about managed metadata columns
- Added: RecycleBin API clarification vs DriveItem restore
- Added: Bundles endpoint to Drive API
- Fixed: Updated endpoint count to 136+, category count to 13

**[2026-01-28 17:00]**
- Fixed: Removed duplicate DriveItem permission endpoints from Permission API section
- Fixed: Clarified Permission API consolidates site-level permissions
- Fixed: Updated endpoint count to 125+

**[2026-01-28 16:45]**
- Initial TOC created with 120+ endpoints across 12 categories
- Organized by resource type with checkbox format for tracking
- Added research priority guidance
- Marked beta-only endpoints with [BETA] label
