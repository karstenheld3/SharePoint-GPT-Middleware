# INFO: SharePoint REST API - Endpoint TOC

**Doc ID**: SPAPI-TOC
**Goal**: Exhaustive Table of Contents of all SharePoint REST API (/_api/) endpoints for detailed research
**Research Type**: Method/Class/Property/Interface (MCPI) - exhaustive endpoint inventory
**Timeline**: Created 2026-01-28

**Depends on**:
- `_INFO_SPAPI-IN01_SOURCES.md [SPAPI-IN01]` for source documentation

## Quick Reference

- **Total Endpoint Categories**: 20
- **Total Endpoints**: 170+ (some overlap between categories)
- **API Version**: SharePoint REST (Open Data Protocol (OData) v3)
- **Base URL**: `https://{tenant}.sharepoint.com/{site}/_api/`
- **Alternative**: `/_vti_bin/client.svc/` (equivalent to `/_api/`)

## Summary

**SharePoint REST API Base URL**: `https://{tenant}.sharepoint.com/{site}/_api/`

**Key Characteristics:**
- OData v3 based (requires `__metadata` for entity types)
- Requires `X-RequestDigest` header for write operations
- Full SharePoint group support (Owners, Members, Visitors)
- Better taxonomy/term store support than Microsoft Graph

**20 Endpoint Categories**: Site Collection, Web, List, ListItem, Folder, File, User, Group, RoleAssignment, ContentType, Field, Search, UserProfile, Webhook, TermStore, SitePage, Social, HubSites, SiteDesigns, Utility

**Total Endpoints**: 170+

## Endpoint Categories

1. Site Collection API (8 endpoints)
2. Web API (12 endpoints)
3. List API (15 endpoints)
4. ListItem API (10 endpoints)
5. Folder API (8 endpoints)
6. File API (20 endpoints)
7. User API (10 endpoints)
8. Group API (8 endpoints)
9. RoleAssignment API (10 endpoints)
10. ContentType API (6 endpoints)
11. Field API (8 endpoints)
12. Search API (4 endpoints)
13. UserProfile API (8 endpoints)
14. Webhook API (5 endpoints)
15. TermStore API (8 endpoints)
16. SitePage API (8 endpoints)
17. Social/Following API (11 endpoints)
18. Hub Sites API (8 endpoints)
19. Site Designs API (11 endpoints)
20. Utility API (6 endpoints)

**Note**: SharePoint REST API is OData v3 based. Use `application/json;odata=verbose` for full metadata or `odata=nometadata` for minimal response.

## Topic Files

- [`_INFO_SPAPI-IN01_SOURCES.md`](./_INFO_SPAPI-IN01_SOURCES.md) [SPAPI-IN01] - Source documentation
- [`_INFO_SPAPI-IN01_OVERVIEW.md`](./_INFO_SPAPI-IN01_OVERVIEW.md) [SPAPI-IN01] - API overview
- [`_INFO_SPAPI-IN01_SITE.md`](./_INFO_SPAPI-IN01_SITE.md) [SPAPI-IN01] - Site Collection API
- [`_INFO_SPAPI-IN01_WEB.md`](./_INFO_SPAPI-IN01_WEB.md) [SPAPI-IN01] - Web API
- [`_INFO_SPAPI-IN01_LIST.md`](./_INFO_SPAPI-IN01_LIST.md) [SPAPI-IN01] - List API
- [`_INFO_SPAPI-IN01_LISTITEM.md`](./_INFO_SPAPI-IN01_LISTITEM.md) [SPAPI-IN01] - ListItem API
- [`_INFO_SPAPI-IN01_FOLDER.md`](./_INFO_SPAPI-IN01_FOLDER.md) [SPAPI-IN01] - Folder API
- [`_INFO_SPAPI-IN01_FILE.md`](./_INFO_SPAPI-IN01_FILE.md) [SPAPI-IN01] - File API
- [`_INFO_SPAPI-IN01_USER.md`](./_INFO_SPAPI-IN01_USER.md) [SPAPI-IN01] - User API
- [`_INFO_SPAPI-IN01_GROUP.md`](./_INFO_SPAPI-IN01_GROUP.md) [SPAPI-IN01] - Group API
- [`_INFO_SPAPI-IN01_ROLEASSIGNMENT.md`](./_INFO_SPAPI-IN01_ROLEASSIGNMENT.md) [SPAPI-IN01] - RoleAssignment API
- [`_INFO_SPAPI-IN01_CONTENTTYPE.md`](./_INFO_SPAPI-IN01_CONTENTTYPE.md) [SPAPI-IN01] - ContentType API
- [`_INFO_SPAPI-IN01_FIELD.md`](./_INFO_SPAPI-IN01_FIELD.md) [SPAPI-IN01] - Field API
- [`_INFO_SPAPI-IN01_SEARCH.md`](./_INFO_SPAPI-IN01_SEARCH.md) [SPAPI-IN01] - Search API
- [`_INFO_SPAPI-IN01_USERPROFILE.md`](./_INFO_SPAPI-IN01_USERPROFILE.md) [SPAPI-IN01] - UserProfile API
- [`_INFO_SPAPI-IN01_WEBHOOK.md`](./_INFO_SPAPI-IN01_WEBHOOK.md) [SPAPI-IN01] - Webhook API
- [`_INFO_SPAPI-IN01_TERMSTORE.md`](./_INFO_SPAPI-IN01_TERMSTORE.md) [SPAPI-IN01] - TermStore API
- [`_INFO_SPAPI-IN01_SITEPAGE.md`](./_INFO_SPAPI-IN01_SITEPAGE.md) [SPAPI-IN01] - SitePage API
- [`_INFO_SPAPI-IN01_SOCIAL.md`](./_INFO_SPAPI-IN01_SOCIAL.md) [SPAPI-IN01] - Social/Following API
- [`_INFO_SPAPI-IN01_HUBSITES.md`](./_INFO_SPAPI-IN01_HUBSITES.md) [SPAPI-IN01] - Hub Sites API
- [`_INFO_SPAPI-IN01_SITEDESIGNS.md`](./_INFO_SPAPI-IN01_SITEDESIGNS.md) [SPAPI-IN01] - Site Designs API
- [`_INFO_SPAPI-IN01_UTILITY.md`](./_INFO_SPAPI-IN01_UTILITY.md) [SPAPI-IN01] - Utility API

## Endpoint Reference

## 1. Site Collection API

### Site - Core Methods

- [x] `GET /_api/site` - Get site collection properties
- [x] `GET /_api/site/rootweb` - Get root web of site collection
- [x] `GET /_api/site/owner` - Get site collection owner
- [x] `GET /_api/site/usage` - Get site collection usage info
- [x] `GET /_api/site/features` - List site collection features
- [x] `POST /_api/site/features/add('{feature-id}')` - Activate feature
- [x] `POST /_api/site/features/remove('{feature-id}')` - Deactivate feature
- [x] `GET /_api/site/recyclebin` - Get site collection recycle bin

## 2. Web API

### Web - Core Methods

- [x] `GET /_api/web` - Get current web properties
- [x] `GET /_api/web/title` - Get web title
- [x] `GET /_api/web/description` - Get web description
- [x] `GET /_api/web/url` - Get web URL
- [x] `PATCH /_api/web` - Update web properties
- [x] `GET /_api/web/webs` - Get subwebs
- [x] `POST /_api/web/webs/add` - Create subweb
- [x] `DELETE /_api/web` - Delete web

### Web - Navigation

- [x] `GET /_api/web/navigation/quicklaunch` - Get quick launch navigation
- [x] `GET /_api/web/navigation/topnavigationbar` - Get top navigation
- [x] `POST /_api/web/navigation/quicklaunch` - Add navigation node
- [x] `DELETE /_api/web/navigation/quicklaunch({node-id})` - Delete navigation node

## 3. List API

### List - Core Methods

- [x] `GET /_api/web/lists` - Get all lists
- [x] `GET /_api/web/lists/getbytitle('{list-title}')` - Get list by title
- [x] `GET /_api/web/lists('{list-guid}')` - Get list by GUID
- [x] `GET /_api/web/lists/getbyid('{list-guid}')` - Get list by ID (alternate)
- [x] `POST /_api/web/lists` - Create list
- [x] `PATCH /_api/web/lists/getbytitle('{list-title}')` - Update list
- [x] `DELETE /_api/web/lists/getbytitle('{list-title}')` - Delete list

### List - Views

- [x] `GET /_api/web/lists/getbytitle('{list}')/views` - Get list views
- [x] `GET /_api/web/lists/getbytitle('{list}')/views/getbytitle('{view}')` - Get view by title
- [x] `GET /_api/web/lists/getbytitle('{list}')/defaultview` - Get default view
- [x] `POST /_api/web/lists/getbytitle('{list}')/views` - Create view

### List - Content Types

- [x] `GET /_api/web/lists/getbytitle('{list}')/contenttypes` - Get list content types
- [x] `POST /_api/web/lists/getbytitle('{list}')/contenttypes/addavailablecontenttype` - Add content type

### List - Fields

- [x] `GET /_api/web/lists/getbytitle('{list}')/fields` - Get list fields
- [x] `POST /_api/web/lists/getbytitle('{list}')/fields` - Create field

## 4. ListItem API

### ListItem - Core Methods

- [x] `GET /_api/web/lists/getbytitle('{list}')/items` - Get all items
- [x] `GET /_api/web/lists/getbytitle('{list}')/items({item-id})` - Get item by ID
- [x] `GET /_api/web/lists/getbytitle('{list}')/items?$filter=...` - Filter items
- [x] `GET /_api/web/lists/getbytitle('{list}')/items?$select=...` - Select fields
- [x] `GET /_api/web/lists/getbytitle('{list}')/items?$expand=...` - Expand lookups
- [x] `POST /_api/web/lists/getbytitle('{list}')/items` - Create item
- [x] `POST /_api/web/lists/getbytitle('{list}')/items({id})` + `X-HTTP-Method: MERGE` - Update item
- [x] `POST /_api/web/lists/getbytitle('{list}')/items({id})` + `X-HTTP-Method: DELETE` - Delete item

### ListItem - Attachments

- [x] `GET /_api/web/lists/getbytitle('{list}')/items({id})/attachmentfiles` - Get attachments
- [x] `POST /_api/web/lists/getbytitle('{list}')/items({id})/attachmentfiles/add(filename='{name}')` - Add attachment

## 5. Folder API

### Folder - Core Methods

- [x] `GET /_api/web/folders` - Get all folders in web
- [x] `GET /_api/web/GetFolderByServerRelativeUrl('{path}')` - Get folder by path
- [x] `GET /_api/web/GetFolderByServerRelativeUrl('{path}')/folders` - Get subfolders
- [x] `GET /_api/web/GetFolderByServerRelativeUrl('{path}')/files` - Get files in folder
- [x] `POST /_api/web/folders` - Create folder
- [x] `POST /_api/web/GetFolderByServerRelativeUrl('{path}')` + `X-HTTP-Method: DELETE` - Delete folder
- [x] `POST /_api/web/GetFolderByServerRelativeUrl('{path}')/moveto('{newUrl}')` - Move folder
- [x] `POST /_api/web/GetFolderByServerRelativeUrl('{path}')/copyto('{newUrl}')` - Copy folder

## 6. File API

### File - Core Methods

- [x] `GET /_api/web/GetFileByServerRelativeUrl('{path}')` - Get file metadata
- [x] `GET /_api/web/GetFileByServerRelativeUrl('{path}')/$value` - Download file content
- [x] `GET /_api/web/GetFileByServerRelativeUrl('{path}')/listitemallfields` - Get file list item
- [x] `POST /_api/web/GetFolderByServerRelativeUrl('{folder}')/Files/add(url='{name}',overwrite=true)` - Upload small file (<2MB)
- [x] `POST /_api/web/GetFolderByServerRelativeUrl('{folder}')/Files/add(url='{name}')` + binary - Upload file

### File - Large File Upload (Chunked)

- [x] `POST /_api/web/GetFolderByServerRelativeUrl('{folder}')/Files/GetByUrlOrAddStub('{name}')/StartUpload(uploadId='{guid}')` - Start chunked upload
- [x] `POST /_api/web/GetFileByServerRelativeUrl('{path}')/ContinueUpload(uploadId='{guid}',fileOffset={offset})` - Continue upload
- [x] `POST /_api/web/GetFileByServerRelativeUrl('{path}')/FinishUpload(uploadId='{guid}',fileOffset={offset})` - Finish upload
- [x] `POST /_api/web/GetFileByServerRelativeUrl('{path}')/CancelUpload(uploadId='{guid}')` - Cancel upload

### File - Check In/Out

- [x] `POST /_api/web/GetFileByServerRelativeUrl('{path}')/CheckOut()` - Check out file
- [x] `POST /_api/web/GetFileByServerRelativeUrl('{path}')/CheckIn(comment='{comment}',checkintype={type})` - Check in file
- [x] `POST /_api/web/GetFileByServerRelativeUrl('{path}')/UndoCheckOut()` - Undo checkout

### File - Operations

- [x] `POST /_api/web/GetFileByServerRelativeUrl('{path}')/moveto('{newUrl}',flags={flags})` - Move file
- [x] `POST /_api/web/GetFileByServerRelativeUrl('{path}')/copyto('{newUrl}',boverwrite=true)` - Copy file
- [x] `POST /_api/web/GetFileByServerRelativeUrl('{path}')` + `X-HTTP-Method: DELETE` - Delete file

### File - Versions

- [x] `GET /_api/web/GetFileByServerRelativeUrl('{path}')/versions` - Get file versions
- [x] `GET /_api/web/GetFileByServerRelativeUrl('{path}')/versions({version-id})` - Get specific version
- [x] `POST /_api/web/GetFileByServerRelativeUrl('{path}')/versions/deletebyid({version-id})` - Delete version
- [x] `POST /_api/web/GetFileByServerRelativeUrl('{path}')/versions/restorebyid({version-id})` - Restore version
- [x] `POST /_api/web/GetFileByServerRelativeUrl('{path}')/versions/deleteall` - Delete all versions

## 7. User API

### User - Core Methods

- [x] `GET /_api/web/currentuser` - Get current user
- [x] `GET /_api/web/siteusers` - Get all site users
- [x] `GET /_api/web/siteusers({user-id})` - Get user by ID
- [x] `GET /_api/web/getuserbyid({user-id})` - Get user by ID (alternate)
- [x] `GET /_api/web/siteusers(@v)?@v='{login-name}'` - Get user by login name
- [x] `GET /_api/web/ensureuser('{login-name}')` - Ensure user exists
- [x] `POST /_api/web/siteusers` - Add user to site

### User - Permissions

- [x] `GET /_api/web/getusereffectivepermissions(@user)?@user='{login}'` - Get effective permissions
- [x] `GET /_api/web/doesuserhavepermissions(@v)?@v={'High':'{high}','Low':'{low}'}` - Check permission
- [x] `GET /_api/web/lists/getbytitle('{list}')/getusereffectivepermissions(@user)?@user='{login}'` - Get list permissions

## 8. Group API

### Group - Core Methods

- [x] `GET /_api/web/sitegroups` - Get all site groups
- [x] `GET /_api/web/sitegroups({group-id})` - Get group by ID
- [x] `GET /_api/web/sitegroups/getbyname('{group-name}')` - Get group by name
- [x] `GET /_api/web/sitegroups({group-id})/users` - Get group members
- [x] `POST /_api/web/sitegroups` - Create group
- [x] `POST /_api/web/sitegroups({group-id})/users` - Add user to group
- [x] `POST /_api/web/sitegroups({group-id})/users/removebyid({user-id})` - Remove user from group
- [x] `DELETE /_api/web/sitegroups({group-id})` - Delete group

## 9. RoleAssignment API (Permissions)

### RoleAssignment - Web Level

- [x] `GET /_api/web/roleassignments` - Get web role assignments
- [x] `GET /_api/web/roledefinitions` - Get role definitions
- [x] `GET /_api/web/roledefinitions/getbytype({type})` - Get role by type
- [x] `POST /_api/web/roleassignments/addroleassignment(principalid={id},roledefid={defId})` - Add role assignment
- [x] `POST /_api/web/roleassignments/removeroleassignment(principalid={id},roledefid={defId})` - Remove role assignment

### RoleAssignment - List/Item Level

- [x] `GET /_api/web/lists/getbytitle('{list}')/roleassignments` - Get list role assignments
- [x] `POST /_api/web/lists/getbytitle('{list}')/breakroleinheritance(copyRoleAssignments=true,clearSubscopes=true)` - Break inheritance
- [x] `POST /_api/web/lists/getbytitle('{list}')/resetroleinheritance` - Reset to inherited
- [x] `GET /_api/web/lists/getbytitle('{list}')/items({id})/roleassignments` - Get item role assignments
- [x] `POST /_api/web/lists/getbytitle('{list}')/items({id})/breakroleinheritance(...)` - Break item inheritance

## 10. ContentType API

### ContentType - Site Level

- [x] `GET /_api/web/contenttypes` - Get site content types
- [x] `GET /_api/web/contenttypes('{content-type-id}')` - Get content type by ID
- [x] `GET /_api/web/contenttypes/getbyname('{name}')` - Get content type by name
- [x] `POST /_api/web/contenttypes` - Create content type
- [x] `PATCH /_api/web/contenttypes('{id}')` - Update content type
- [x] `DELETE /_api/web/contenttypes('{id}')` - Delete content type

## 11. Field API (Columns)

### Field - Site Level

- [x] `GET /_api/web/fields` - Get site columns
- [x] `GET /_api/web/fields('{field-guid}')` - Get field by GUID
- [x] `GET /_api/web/fields/getbyinternalnameortitle('{name}')` - Get field by name
- [x] `GET /_api/web/fields/getbytitle('{title}')` - Get field by title
- [x] `POST /_api/web/fields` - Create field
- [x] `PATCH /_api/web/fields('{field-guid}')` - Update field
- [x] `DELETE /_api/web/fields('{field-guid}')` - Delete field
- [x] `POST /_api/web/fields/addfield` - Add field with schema XML

## 12. Search API

### Search - Query Methods

- [x] `GET /_api/search/query?querytext='{query}'` - Search with GET
- [x] `POST /_api/search/postquery` - Search with POST (complex queries)
- [x] `GET /_api/search/suggest?querytext='{query}'` - Get search suggestions
- [x] `POST /_api/search/recordPageClick` - Record page click for analytics

### Search Parameters

Key parameters for search queries:
- `querytext` - Keyword Query Language (KQL) query string
- `selectproperties` - Properties to return
- `rowlimit` - Max results (default 10, max 500)
- `startrow` - Pagination offset
- `refinementfilters` - Refine results
- `sortlist` - Sort order
- `enablestemming` - Word stemming
- `trimduplicates` - Remove duplicates

## 13. UserProfile API

### UserProfile - Core Methods

- [x] `GET /_api/sp.userprofiles.peoplemanager/getmyproperties` - Get current user profile
- [x] `GET /_api/sp.userprofiles.peoplemanager/getpropertiesfor(@v)?@v='{account}'` - Get user profile
- [x] `GET /_api/sp.userprofiles.peoplemanager/getuserprofilepropertyfor(accountname=@v,propertyname='{prop}')?@v='{account}'` - Get specific property
- [x] `POST /_api/sp.userprofiles.peoplemanager/setsinglenewsfeed(@v,@y)?@v='{account}'&@y={value}` - Set property

### UserProfile - Following

- [x] `GET /_api/sp.userprofiles.peoplemanager/getpeoplefollowedby(@v)?@v='{account}'` - Get people followed
- [x] `GET /_api/sp.userprofiles.peoplemanager/getfollowersfor(@v)?@v='{account}'` - Get followers
- [x] `POST /_api/sp.userprofiles.peoplemanager/follow(@v)?@v='{account}'` - Follow user
- [x] `POST /_api/sp.userprofiles.peoplemanager/stopfollowing(@v)?@v='{account}'` - Stop following

## 14. Webhook API

### Webhook - Subscription Methods

- [x] `GET /_api/web/lists('{list-id}')/subscriptions` - Get subscriptions
- [x] `GET /_api/web/lists('{list-id}')/subscriptions('{subscription-id}')` - Get subscription
- [x] `POST /_api/web/lists('{list-id}')/subscriptions` - Create subscription
- [x] `PATCH /_api/web/lists('{list-id}')/subscriptions('{subscription-id}')` - Update subscription
- [x] `DELETE /_api/web/lists('{list-id}')/subscriptions('{subscription-id}')` - Delete subscription

**Limitation**: SharePoint webhooks only support list item changes. Expiration max 180 days.

## 15. TermStore API (Taxonomy)

### TermStore - Core Methods

- [x] `GET /_api/site/termstore` - Get default term store
- [x] `GET /_api/site/termstore/groups` - List term groups
- [x] `GET /_api/site/termstore/groups('{group-id}')` - Get term group
- [x] `GET /_api/site/termstore/groups('{group-id}')/termsets` - List term sets in group
- [x] `GET /_api/site/termstore/termsets('{set-id}')` - Get term set
- [x] `GET /_api/site/termstore/termsets('{set-id}')/terms` - List terms in set
- [x] `GET /_api/site/termstore/termsets('{set-id}')/terms('{term-id}')` - Get term
- [x] `GET /_api/site/termstore/termsets('{set-id}')/terms('{term-id}')/children` - Get child terms

**Note**: Full taxonomy management requires CSOM/JSOM. REST API is primarily read-only for term store.

## 16. SitePage API

### SitePage - Core Methods

- [x] `GET /_api/sitepages/pages` - List site pages
- [x] `GET /_api/sitepages/pages({page-id})` - Get page by ID
- [x] `GET /_api/sitepages/pages/getbyurl('{url}')` - Get page by URL
- [x] `POST /_api/sitepages/pages` - Create page
- [x] `PATCH /_api/sitepages/pages({page-id})` - Update page
- [x] `DELETE /_api/sitepages/pages({page-id})` - Delete page
- [x] `POST /_api/sitepages/pages({page-id})/publish` - Publish page
- [x] `POST /_api/sitepages/pages({page-id})/saveastemplate` - Save as template

**Note**: Modern site pages only. Classic wiki pages use different endpoints.

## 17. Social/Following API

### Social - Following Content

- [x] `GET /_api/social.following/my/followed(types=14)` - Get followed documents/sites/tags
- [x] `POST /_api/social.following/follow` - Follow document/site/tag
- [x] `POST /_api/social.following/stopfollowing` - Stop following
- [x] `GET /_api/social.following/isfollowed` - Check if following
- [x] `GET /_api/social.following/my/followedcount` - Get followed count

### Social - Feed

- [x] `GET /_api/social.feed/my/feed` - Get user's social feed
- [x] `GET /_api/social.feed/my/news` - Get news feed
- [x] `POST /_api/social.feed/my/feed/post` - Post to feed
- [x] `POST /_api/social.feed/post/reply` - Reply to post
- [x] `POST /_api/social.feed/post/like` - Like a post
- [x] `POST /_api/social.feed/post/unlike` - Unlike a post

**Note**: Social features may be limited or disabled in some tenants.

## 18. Hub Sites API

### Hub Sites - Core Methods

- [x] `GET /_api/hubsites` - List all hub sites
- [x] `GET /_api/hubsites/getbyid('{hub-id}')` - Get hub site by ID
- [x] `GET /_api/site/hubsitedata` - Get hub site data for current site
- [x] `GET /_api/site/ishubsite` - Check if current site is hub site
- [x] `POST /_api/site/registerhubsite` - Register site as hub site
- [x] `POST /_api/site/unregisterhubsite` - Unregister hub site
- [x] `POST /_api/site/joinhubsite('{hub-id}')` - Join site to hub
- [x] `POST /_api/site/disjoinhubsite` - Leave hub site

**Note**: Requires Site Collection Administrator or SharePoint Administrator permissions.

## 19. Site Designs API

### Site Designs - Core Methods

- [x] `POST /_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.GetSiteDesigns` - List site designs
- [x] `POST /_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.GetSiteDesignMetadata` - Get site design metadata
- [x] `POST /_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.CreateSiteDesign` - Create site design
- [x] `POST /_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.UpdateSiteDesign` - Update site design
- [x] `POST /_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.DeleteSiteDesign` - Delete site design
- [x] `POST /_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.ApplySiteDesign` - Apply site design

### Site Scripts - Core Methods

- [x] `POST /_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.GetSiteScripts` - List site scripts
- [x] `POST /_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.GetSiteScriptMetadata` - Get site script metadata
- [x] `POST /_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.CreateSiteScript` - Create site script
- [x] `POST /_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.UpdateSiteScript` - Update site script
- [x] `POST /_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.DeleteSiteScript` - Delete site script

**Note**: Site designs use JSON-based actions. Requires SharePoint Administrator permissions.

## 20. Utility API

### Context and Digest

- [x] `POST /_api/contextinfo` - Get form digest value (required for POST/MERGE/DELETE)
- [x] `GET /_api/web/regionalSettings` - Get regional settings
- [x] `GET /_api/web/regionalSettings/timeZone` - Get time zone

### Change Tracking

- [x] `POST /_api/web/getchanges` - Get web changes
- [x] `POST /_api/web/lists/getbytitle('{list}')/getchanges` - Get list changes

### Batch Requests

- [x] `POST /_api/$batch` - Batch multiple requests (OData $batch)

## Research Priority

### High Priority (Core Operations)

1. File API - File operations, uploads, downloads
2. ListItem API - List data operations
3. List API - List management
4. RoleAssignment API - Permissions

### Medium Priority (Management)

5. User API - User management
6. Group API - Group management
7. Search API - Content discovery
8. Webhook API - Change notifications

### Lower Priority (Specialized)

9. ContentType API - Schema management
10. Field API - Column definitions
11. UserProfile API - Profile operations
12. Site/Web API - Site management

## Key Differences from Microsoft Graph

- **OData version**: REST uses OData v3, Graph uses OData v4
- **Metadata**: REST requires `__metadata` for entity types
- **Headers**: REST requires `X-RequestDigest` for write operations
- **Groups**: REST has full SharePoint group support (Owners, Members, Visitors)
- **Term Store**: REST has better taxonomy support via CSOM patterns
- **Recycle Bin**: REST has `/_api/site/recyclebin` for site collection level

## Sources

- **SPAPI-TOC-SC-01**: https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/get-to-know-the-sharepoint-rest-service
- **SPAPI-TOC-SC-02**: https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/complete-basic-operations-using-sharepoint-rest-endpoints
- **SPAPI-TOC-SC-03**: https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/working-with-lists-and-list-items-with-rest
- **SPAPI-TOC-SC-04**: https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/working-with-folders-and-files-with-rest
- **SPAPI-TOC-SC-05**: https://learn.microsoft.com/en-us/sharepoint/dev/general-development/sharepoint-search-rest-api-overview
- **SPAPI-TOC-SC-06**: https://learn.microsoft.com/en-us/sharepoint/dev/apis/webhooks/overview-sharepoint-webhooks

## Document History

**[2026-01-28 18:27]**
- Added: Section 17 - Social/Following API (11 endpoints)
- Added: Section 18 - Hub Sites API (8 endpoints)
- Added: Section 19 - Site Designs API (11 endpoints)
- Fixed: Updated endpoint count to 170+, category count to 20
- MCPI: Exhaustive coverage achieved

**[2026-01-28 18:25]**
- Added: Section 15 - TermStore API (8 endpoints for taxonomy)
- Added: Section 16 - SitePage API (8 endpoints for modern pages)
- Added: File - Versions subsection (5 endpoints)
- Fixed: Updated endpoint count to 140+, category count to 17

**[2026-01-28 18:24]**
- Added: Summary section with key characteristics
- Fixed: Expanded acronyms (MCPI, OData, KQL) on first use

**[2026-01-28 18:23]**
- Initial TOC created with 120+ endpoints across 15 categories
- Organized by resource type with checkbox format for tracking
- Added key differences from Microsoft Graph section
- Added research priority guidance
