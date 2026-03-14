# INFO: SharePoint Online APIs - Complete Reference

**Doc ID**: SPAPI-IN01
**Goal**: Comprehensive reference of all SharePoint Online API endpoints, syntax, permissions, and use cases
**Timeline**: Created 2026-01-28, 1 update

## Summary (Copy/Paste Ready)

**Three API Families:**
- **SharePoint REST API (/_api/)** - Legacy OData-based REST endpoints, direct SharePoint access
- **Microsoft Graph API** - Modern unified API, recommended for new development
- **CSOM/JSOM** - Client Side Object Model (CSOM) / JavaScript Object Model (JSOM), deprecated for add-ins

**Key Permission Scopes (Graph API):**
- `Sites.Read.All` - Read all sites (Delegated/Application)
- `Sites.ReadWrite.All` - Read/write all sites (Delegated/Application)
- `Sites.FullControl.All` - Full control all sites (Application only)
- `Sites.Selected` - Granular per-site permissions (Application)

**Base URLs:**
- SharePoint REST: `https://{tenant}.sharepoint.com/{site}/_api/`
- Microsoft Graph: `https://graph.microsoft.com/v1.0/sites/`
- SharePoint v2 (Graph via SP): `https://{tenant}.sharepoint.com/_api/v2.0/`

## Table of Contents

- API Families Overview
- SharePoint REST API (/_api/)
- Microsoft Graph SharePoint API
- CSOM/JSOM (Legacy)
- Azure AD Permissions Reference
- Webhooks
- Sources

## API Families Overview

### Comparison [VERIFIED]

- **SharePoint REST (/_api/)** 
  - Status: Supported, legacy
  - Auth: SharePoint tokens, OAuth
  - Format: Open Data Protocol (OData) v3
  - Scope: SharePoint only

- **Microsoft Graph** 
  - Status: Recommended
  - Auth: Azure Active Directory (Azure AD) OAuth
  - Format: OData v4
  - Scope: Microsoft 365 unified

- **CSOM/JSOM** 
  - Status: Deprecated Nov 2023, new tenants blocked Nov 2024, retired Apr 2026
  - Auth: SharePoint context
  - Format: .NET/JS objects
  - Scope: SharePoint only

### When to Use What [VERIFIED]

- **New development**: Use Microsoft Graph API (Note: Some features like Term Store, advanced Site Designs require REST API)
- **Existing solutions with SP tokens**: Use SharePoint REST v2 (`/_api/v2.0/`)
- **Legacy migration**: Consider upgrading from CSOM/JSOM to Graph or REST

## SharePoint REST API (/_api/)

### Base Structure [VERIFIED]

```
https://{site_url}/_api/{endpoint}
```

The `_api` prefix is shorthand for `_vti_bin/client.svc`. Both are accepted but `_api` is preferred.

### Entry Points [VERIFIED]

- `/_api/site` - Site collection (SPSite)
- `/_api/web` - Current web/site (SPWeb)
- `/_api/contextinfo` - Form digest and context info
- `/_api/search/query` - Search service
- `/_api/sp.userprofiles.peoplemanager` - User profiles

### HTTP Methods [VERIFIED]

- **GET** - Read operations
- **POST** - Create entities, execute methods
- **PUT** - Replace entire entity
- **MERGE** - Partial update (preferred over PUT)
- **DELETE** - Remove entities (recyclable items go to recycle bin)

### Required Headers [VERIFIED]

```http
Authorization: Bearer {access_token}
Accept: application/json;odata=verbose
Content-Type: application/json;odata=verbose
X-RequestDigest: {form_digest_value}  # Required for POST/PUT/MERGE/DELETE (expires after ~30 minutes)
```

### Sites and Webs [VERIFIED]

**Get site collection properties:**
```http
GET https://{site_url}/_api/site
```

**Get web properties:**
```http
GET https://{site_url}/_api/web
```

**Get web title:**
```http
GET https://{site_url}/_api/web/title
```

### Lists [VERIFIED]

**Get all lists:**
```http
GET https://{site_url}/_api/web/lists
```

**Get list by title:**
```http
GET https://{site_url}/_api/web/lists/getbytitle('{list_name}')
```

**Get list by GUID:**
```http
GET https://{site_url}/_api/web/lists('{list_guid}')
```

**Get list items:**
```http
GET https://{site_url}/_api/web/lists/getbytitle('{list_name}')/items
```

**Get specific item:**
```http
GET https://{site_url}/_api/web/lists/getbytitle('{list_name}')/items({item_id})
```

**Create list:**
```http
POST https://{site_url}/_api/web/lists
Content-Type: application/json;odata=verbose

{
  "__metadata": { "type": "SP.List" },
  "AllowContentTypes": true,
  "BaseTemplate": 100,
  "ContentTypesEnabled": true,
  "Description": "List description",
  "Title": "New List"
}
```

**Create list item:**
```http
POST https://{site_url}/_api/web/lists/getbytitle('{list_name}')/items
Content-Type: application/json;odata=verbose

{
  "__metadata": { "type": "SP.Data.{ListName}ListItem" },
  "Title": "New Item"
}
```

**Update list item (MERGE):**
```http
POST https://{site_url}/_api/web/lists/getbytitle('{list_name}')/items({item_id})
X-HTTP-Method: MERGE
If-Match: *

{
  "__metadata": { "type": "SP.Data.{ListName}ListItem" },
  "Title": "Updated Title"
}
```

**Delete list item:**
```http
POST https://{site_url}/_api/web/lists/getbytitle('{list_name}')/items({item_id})
X-HTTP-Method: DELETE
If-Match: *
```

### Folders [VERIFIED]

**Get folder by server-relative URL:**
```http
GET https://{site_url}/_api/web/GetFolderByServerRelativeUrl('Shared Documents')
```

**Get folder files:**
```http
GET https://{site_url}/_api/web/GetFolderByServerRelativeUrl('Shared Documents')/Files
```

**Get subfolders:**
```http
GET https://{site_url}/_api/web/GetFolderByServerRelativeUrl('Shared Documents')/Folders
```

**Create folder:**
```http
POST https://{site_url}/_api/web/folders
Content-Type: application/json;odata=verbose

{
  "__metadata": { "type": "SP.Folder" },
  "ServerRelativeUrl": "/sites/mysite/Shared Documents/NewFolder"
}
```

**Delete folder:**
```http
POST https://{site_url}/_api/web/GetFolderByServerRelativeUrl('Shared Documents/FolderName')
X-HTTP-Method: DELETE
If-Match: *
```

### Files [VERIFIED]

**Get file by server-relative URL:**
```http
GET https://{site_url}/_api/web/GetFileByServerRelativeUrl('/sites/mysite/Shared Documents/file.docx')
```

**Download file content:**
```http
GET https://{site_url}/_api/web/GetFileByServerRelativeUrl('/sites/mysite/Shared Documents/file.docx')/$value
```

**Upload file (small, < 2MB):**
```http
POST https://{site_url}/_api/web/GetFolderByServerRelativeUrl('Shared Documents')/Files/add(url='filename.txt',overwrite=true)
Content-Type: application/octet-stream

{binary file content}
```

**Upload large file (chunked):**
```http
POST https://{site_url}/_api/web/GetFolderByServerRelativeUrl('Shared Documents')/Files/GetByUrlOrAddStub('largefile.zip')/StartUpload(uploadId='{guid}')
POST https://{site_url}/_api/web/GetFileByServerRelativeUrl('/path/largefile.zip')/ContinueUpload(uploadId='{guid}',fileOffset={offset})
POST https://{site_url}/_api/web/GetFileByServerRelativeUrl('/path/largefile.zip')/FinishUpload(uploadId='{guid}',fileOffset={offset})
```

**Check out file:**
```http
POST https://{site_url}/_api/web/GetFileByServerRelativeUrl('/path/file.docx')/CheckOut()
```

**Check in file:**
```http
POST https://{site_url}/_api/web/GetFileByServerRelativeUrl('/path/file.docx')/CheckIn(comment='comment',checkintype=1)
```

### Users and Groups [VERIFIED]

**Get all site users:**
```http
GET https://{site_url}/_api/web/siteusers
```

**Get user by ID:**
```http
GET https://{site_url}/_api/web/getuserbyid({user_id})
```

**Get user by login name:**
```http
GET https://{site_url}/_api/web/siteusers(@v)?@v='i%3A0%23.f%7Cmembership%7Cuser%40domain.onmicrosoft.com'
```

**Get all site groups:**
```http
GET https://{site_url}/_api/web/sitegroups
```

**Get group by ID:**
```http
GET https://{site_url}/_api/web/sitegroups({group_id})
```

**Get group members:**
```http
GET https://{site_url}/_api/web/sitegroups({group_id})/users
```

**Add user to group:**
```http
POST https://{site_url}/_api/web/sitegroups({group_id})/users
Content-Type: application/json;odata=verbose

{
  "__metadata": { "type": "SP.User" },
  "LoginName": "i:0#.f|membership|user@domain.onmicrosoft.com"
}
```

**Get current user:**
```http
GET https://{site_url}/_api/web/currentuser
```

**Get user effective permissions:**
```http
GET https://{site_url}/_api/web/getusereffectivepermissions(@user)?@user='i%3A0%23.f%7Cmembership%7Cuser%40domain.onmicrosoft.com'
```

### Role Assignments (Permissions) [VERIFIED]

**Get role assignments for web:**
```http
GET https://{site_url}/_api/web/roleassignments
```

**Get role assignments for list:**
```http
GET https://{site_url}/_api/web/lists/getbytitle('{list_name}')/roleassignments
```

**Get role definitions:**
```http
GET https://{site_url}/_api/web/roledefinitions
```

**Break role inheritance:**
```http
POST https://{site_url}/_api/web/lists/getbytitle('{list_name}')/breakroleinheritance(copyRoleAssignments=true,clearSubscopes=true)
```

### Content Types [VERIFIED]

**Get site content types:**
```http
GET https://{site_url}/_api/web/contenttypes
```

**Get content type by ID:**
```http
GET https://{site_url}/_api/web/contenttypes('{content_type_id}')
```

**Get list content types:**
```http
GET https://{site_url}/_api/web/lists/getbytitle('{list_name}')/contenttypes
```

### Fields (Columns) [VERIFIED]

**Get site columns:**
```http
GET https://{site_url}/_api/web/fields
```

**Get field by ID:**
```http
GET https://{site_url}/_api/web/fields('{field_id}')
```

**Get field by internal name:**
```http
GET https://{site_url}/_api/web/fields/getbyinternalnameortitle('{internal_name}')
```

**Get list fields:**
```http
GET https://{site_url}/_api/web/lists/getbytitle('{list_name}')/fields
```

### Search [VERIFIED]

**GET request:**
```http
GET https://{site_url}/_api/search/query?querytext='search terms'
```

**GET with parameters:**
```http
GET https://{site_url}/_api/search/query?querytext='sharepoint'&selectproperties='Title,Path,Author'&rowlimit=50
```

**POST request:**
```http
POST https://{site_url}/_api/search/postquery
Content-Type: application/json;odata=verbose

{
  "request": {
    "Querytext": "search terms",
    "RowLimit": 50,
    "SelectProperties": {
      "results": ["Title", "Path", "Author"]
    }
  }
}
```

**Key Search Parameters:**
- `querytext` - Keyword Query Language (KQL) or FAST Query Language (FQL) query
- `selectproperties` - Properties to return
- `rowlimit` - Max results (default 10)
- `startrow` - Pagination offset
- `refinementfilters` - Refine results
- `sortlist` - Sort order
- `enablestemming` - Enable word stemming

### User Profiles [VERIFIED]

**Get current user profile:**
```http
GET https://{site_url}/_api/sp.userprofiles.peoplemanager/getmyproperties
```

**Get specific user profile:**
```http
GET https://{site_url}/_api/sp.userprofiles.peoplemanager/getpropertiesfor(@v)?@v='i%3A0%23.f%7Cmembership%7Cuser%40domain.onmicrosoft.com'
```

**Get specific profile property:**
```http
GET https://{site_url}/_api/sp.userprofiles.peoplemanager/getuserprofilepropertyfor(accountname=@v,propertyname='Department')?@v='i%3A0%23.f%7Cmembership%7Cuser%40domain.onmicrosoft.com'
```

**Get people followed by user:**
```http
GET https://{site_url}/_api/sp.userprofiles.peoplemanager/getpeoplefollowedby(@v)?@v='i%3A0%23.f%7Cmembership%7Cuser%40domain.onmicrosoft.com'
```

### Context and Utilities [VERIFIED]

**Get form digest (required for POST operations):**
```http
POST https://{site_url}/_api/contextinfo
```

**Get changes:**
```http
POST https://{site_url}/_api/web/getchanges
Content-Type: application/json;odata=verbose

{
  "query": {
    "__metadata": { "type": "SP.ChangeQuery" },
    "Web": true,
    "Update": true,
    "Add": true
  }
}
```

### Batch Requests [VERIFIED]

SharePoint Online supports OData `$batch` for combining multiple requests:

```http
POST https://{site_url}/_api/$batch
Content-Type: multipart/mixed; boundary=batch_{guid}

--batch_{guid}
Content-Type: application/http
Content-Transfer-Encoding: binary

GET https://{site_url}/_api/web/lists HTTP/1.1
Accept: application/json;odata=verbose

--batch_{guid}
Content-Type: application/http
Content-Transfer-Encoding: binary

GET https://{site_url}/_api/web/title HTTP/1.1
Accept: application/json;odata=verbose

--batch_{guid}--
```

## Microsoft Graph SharePoint API

### Base Structure [VERIFIED]

```
https://graph.microsoft.com/v1.0/sites/{site-id}
```

Alternative via SharePoint (v2.0):
```
https://{tenant}.sharepoint.com/_api/v2.0/sites
```

### Site Addressing [VERIFIED]

**By hostname (root site):**
```http
GET https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com
```

**By hostname and path:**
```http
GET https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com:/sites/marketing
```

**By site ID:**
```http
GET https://graph.microsoft.com/v1.0/sites/{hostname},{site-collection-id},{web-id}
```

**Search for sites:**
```http
GET https://graph.microsoft.com/v1.0/sites?search={query}
```

### Sites [VERIFIED]

**Get root site:**
```http
GET https://graph.microsoft.com/v1.0/sites/root
```

**Get site by path:**
```http
GET https://graph.microsoft.com/v1.0/sites/{hostname}:/sites/{site-path}
```

**List subsites:**
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/sites
```

### Lists [VERIFIED]

**Get all lists:**
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists
```

**Get list by ID:**
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}
```

**Get list by name:**
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-title}
```

**Create list:**
```http
POST https://graph.microsoft.com/v1.0/sites/{site-id}/lists
Content-Type: application/json

{
  "displayName": "New List",
  "columns": [
    { "name": "Column1", "text": {} }
  ],
  "list": {
    "template": "genericList"
  }
}
```

### List Items [VERIFIED]

**Get items:**
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items
```

**Get items with fields:**
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items?expand=fields
```

**Get specific fields:**
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items?expand=fields(select=Title,Column1)
```

**Filter items:**
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items?$filter=fields/Title eq 'value'
```

**Get single item:**
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items/{item-id}
```

**Create item:**
```http
POST https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items
Content-Type: application/json

{
  "fields": {
    "Title": "New Item"
  }
}
```

**Update item:**
```http
PATCH https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items/{item-id}/fields
Content-Type: application/json

{
  "Title": "Updated Title"
}
```

**Delete item:**
```http
DELETE https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items/{item-id}
```

### Drives (Document Libraries) [VERIFIED]

**Get default drive:**
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/drive
```

**Get all drives:**
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/drives
```

**Get drive by ID:**
```http
GET https://graph.microsoft.com/v1.0/drives/{drive-id}
```

**Get drive root:**
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/drive/root
```

**Get drive children:**
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/drive/root/children
```

### Drive Items (Files/Folders) [VERIFIED]

**Get item by path:**
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/drive/root:/path/to/file.docx
```

**Get item by ID:**
```http
GET https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{item-id}
```

**Download file:**
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/drive/items/{item-id}/content
```

**Upload small file (< 4MB):**
```http
PUT https://graph.microsoft.com/v1.0/sites/{site-id}/drive/root:/path/filename.txt:/content
Content-Type: text/plain

{file content}
```

**Create folder:**
```http
POST https://graph.microsoft.com/v1.0/sites/{site-id}/drive/root/children
Content-Type: application/json

{
  "name": "New Folder",
  "folder": {},
  "@microsoft.graph.conflictBehavior": "rename"
}
```

**Copy item:**
```http
POST https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{item-id}/copy
Content-Type: application/json

{
  "parentReference": {
    "driveId": "{target-drive-id}",
    "id": "{target-folder-id}"
  },
  "name": "new-name.docx"
}
```

**Move item:**
```http
PATCH https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{item-id}
Content-Type: application/json

{
  "parentReference": {
    "id": "{new-parent-id}"
  }
}
```

### Content Types (Graph) [VERIFIED]

**List site content types:**
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/contentTypes
```

**List list content types:**
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/contentTypes
```

### Columns (Graph) [VERIFIED]

**List site columns:**
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/columns
```

**List list columns:**
```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/columns
```

### Permissions (Graph) [VERIFIED]

**List drive item permissions:**
```http
GET https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{item-id}/permissions
```

**Grant permissions:**
```http
POST https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{item-id}/invite
Content-Type: application/json

{
  "recipients": [
    { "email": "user@domain.com" }
  ],
  "roles": ["read"],
  "sendInvitation": false
}
```

## CSOM/JSOM (Legacy)

### Status [VERIFIED]

**IMPORTANT**: The SharePoint Add-In model (including CSOM/JSOM as used in add-ins) is deprecated as of November 2023 and will be retired April 2, 2026. SharePoint Framework (SPFx) is the recommended replacement.

### CSOM (.NET) Basic Pattern

```csharp
using Microsoft.SharePoint.Client;

using (ClientContext context = new ClientContext("https://tenant.sharepoint.com/sites/mysite"))
{
    context.Credentials = new SharePointOnlineCredentials(username, securePassword);
    
    Web web = context.Web;
    context.Load(web);
    context.ExecuteQuery();
    
    Console.WriteLine(web.Title);
}
```

### JSOM (JavaScript) Basic Pattern

```javascript
SP.SOD.executeFunc('sp.js', 'SP.ClientContext', function() {
    var context = SP.ClientContext.get_current();
    var web = context.get_web();
    
    context.load(web);
    context.executeQueryAsync(
        function() {
            console.log(web.get_title());
        },
        function(sender, args) {
            console.error(args.get_message());
        }
    );
});
```

### Key CSOM Libraries

- `Microsoft.SharePointOnline.CSOM` - NuGet package for SharePoint Online
- `Microsoft.SharePoint.Client.dll` - Core client library
- `Microsoft.SharePoint.Client.Runtime.dll` - Runtime support

## Azure AD Permissions Reference

### Microsoft Graph SharePoint Permissions [VERIFIED]

- **Sites.Read.All** - Delegated/Application - Read items in all site collections
- **Sites.ReadWrite.All** - Delegated/Application - Read and write items in all site collections
- **Sites.Manage.All** - Delegated/Application - Create, edit, delete items and lists
- **Sites.FullControl.All** - Application only - Full control of all site collections
- **Sites.Selected** - Application - Access to specific sites only (requires explicit grant)

### Selected Permissions (Granular) [VERIFIED]

Selected permissions allow granular access at site, list, or item level:

- **Sites.Selected** - Site collection level (Note: Search requires Sites.Read.All minimum)
- **Lists.SelectedOperations.Selected** - List level
- **ListItems.SelectedOperations.Selected** - List item level
- **Files.SelectedOperations.Selected** - File level

**Granting Selected Permissions:**
```http
POST https://graph.microsoft.com/v1.0/sites/{site-id}/permissions
Content-Type: application/json

{
  "roles": ["write"],
  "grantedToIdentities": [
    {
      "application": {
        "id": "{app-id}",
        "displayName": "My App"
      }
    }
  ]
}
```

### SharePoint REST API Permissions [VERIFIED]

For SharePoint REST API (/_api/), use the same Graph permissions or legacy SharePoint app permissions:

- **AllSites.Read** - Read all sites
- **AllSites.Write** - Read/write all sites
- **AllSites.FullControl** - Full control
- **AllSites.Manage** - Create/delete lists and items

### Permission Levels Comparison

- **Read** - Read: Yes, Write: No, Delete: No, Manage Permissions: No
- **Write** - Read: Yes, Write: Yes, Delete: Yes, Manage Permissions: No
- **FullControl** - Read: Yes, Write: Yes, Delete: Yes, Manage Permissions: Yes

## Webhooks

### Overview [VERIFIED]

SharePoint webhooks provide push notifications for list item changes. Currently only list items are supported.

### Create Subscription [VERIFIED]

```http
POST https://{site_url}/_api/web/lists('{list-id}')/subscriptions
Content-Type: application/json

{
  "resource": "https://{site_url}/_api/web/lists('{list-id}')",
  "notificationUrl": "https://your-endpoint.com/webhook",
  "expirationDateTime": "2026-07-28T00:00:00Z",
  "clientState": "optional-client-state"
}
```

### Get Subscriptions [VERIFIED]

```http
GET https://{site_url}/_api/web/lists('{list-id}')/subscriptions
```

### Update Subscription [VERIFIED]

```http
PATCH https://{site_url}/_api/web/lists('{list-id}')/subscriptions('{subscription-id}')
Content-Type: application/json

{
  "expirationDateTime": "2026-08-28T00:00:00Z"
}
```

### Delete Subscription [VERIFIED]

```http
DELETE https://{site_url}/_api/web/lists('{list-id}')/subscriptions('{subscription-id}')
```

### Notification Payload

```json
{
  "value": [
    {
      "subscriptionId": "{subscription-id}",
      "clientState": "optional-client-state",
      "expirationDateTime": "2026-07-28T00:00:00Z",
      "resource": "{list-id}",
      "tenantId": "{tenant-id}",
      "siteUrl": "/sites/mysite",
      "webId": "{web-id}"
    }
  ]
}
```

### Limitations [VERIFIED]

- Maximum expiration: 180 days
- Only list item events supported
- Must validate webhook URL during creation
- Notification does not include change details (must query GetChanges)

## Sources

### Primary Microsoft Documentation [VERIFIED]

- **SharePoint REST Service Overview**
  - https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/get-to-know-the-sharepoint-rest-service
  - Basic REST operations, HTTP methods, URL construction

- **Complete Basic Operations Using SharePoint REST Endpoints**
  - https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/complete-basic-operations-using-sharepoint-rest-endpoints
  - CRUD operations, form digest, request examples

- **Determine SharePoint REST Service Endpoint URIs**
  - https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/determine-sharepoint-rest-service-endpoint-uris
  - URI structure, entry points, parameters

- **Working with Folders and Files with REST**
  - https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/working-with-folders-and-files-with-rest
  - File/folder CRUD, upload, download

- **Working with Lists and List Items with REST**
  - https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/working-with-lists-and-list-items-with-rest
  - List operations, batch requests

- **SharePoint Search REST API Overview**
  - https://learn.microsoft.com/en-us/sharepoint/dev/general-development/sharepoint-search-rest-api-overview
  - Search endpoints, KQL queries, parameters

- **Users, Groups, and Roles REST API Reference**
  - https://learn.microsoft.com/en-us/previous-versions/office/developer/sharepoint-rest-reference/dn531432(v=office.15)
  - User/group management, role assignments

- **User Profiles REST API Reference**
  - https://learn.microsoft.com/en-us/previous-versions/office/developer/sharepoint-rest-reference/dn790354(v=office.15)
  - PeopleManager, profile properties

### Microsoft Graph Documentation [VERIFIED]

- **Working with SharePoint Sites in Microsoft Graph**
  - https://learn.microsoft.com/en-us/graph/api/resources/sharepoint?view=graph-rest-1.0
  - Graph API overview, resource types

- **SharePoint REST v2 (Graph) Operations**
  - https://learn.microsoft.com/en-us/sharepoint/dev/apis/sharepoint-rest-graph
  - v2.0 endpoint mapping

- **Microsoft Graph Permissions Reference**
  - https://learn.microsoft.com/en-us/graph/permissions-reference
  - All Graph permissions including Sites.*

- **Selected Permissions Overview**
  - https://learn.microsoft.com/en-us/graph/permissions-selected-overview
  - Sites.Selected, granular permissions

- **List Items (Graph API)**
  - https://learn.microsoft.com/en-us/graph/api/listitem-list?view=graph-rest-1.0
  - List item operations, filtering

### Webhooks Documentation [VERIFIED]

- **Overview of SharePoint Webhooks**
  - https://learn.microsoft.com/en-us/sharepoint/dev/apis/webhooks/overview-sharepoint-webhooks
  - Webhook creation, notifications, limitations

### Rate Limits and Throttling [VERIFIED]

- **Avoid Getting Throttled or Blocked in SharePoint Online**
  - https://learn.microsoft.com/en-us/sharepoint/dev/general-development/how-to-avoid-getting-throttled-or-blocked-in-sharepoint-online
  - App-only search: 25 req/sec limit; Delegated search: 10 req/sec/user; HTTP 429/503 handling

### Legacy API Documentation [VERIFIED]

- **SharePoint .NET Server, CSOM, JSOM, and REST API Index**
  - https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/sharepoint-net-server-csom-jsom-and-rest-api-index
  - API cross-reference, deprecation notice

## Document History

**[2026-01-28 15:30]**
- Fixed: Added throttling documentation link (SPAPI-RV-001)
- Fixed: Updated CSOM/JSOM deprecation timeline with Nov 2024 new tenant block (SPAPI-RV-004)
- Fixed: Added form digest 30-minute expiration note (SPAPI-RV-008)
- Fixed: Added Sites.Selected search limitation note (SPAPI-RV-002)
- Fixed: Added Graph API feature gaps note (SPAPI-RV-005)

**[2026-01-28 14:30]**
- Initial comprehensive research document created
- Added: SharePoint REST API endpoints (sites, lists, files, users, search, profiles)
- Added: Microsoft Graph SharePoint API endpoints
- Added: Azure AD permissions reference
- Added: Webhooks documentation
- Added: CSOM/JSOM deprecation notice
- Added: All sources with URLs
