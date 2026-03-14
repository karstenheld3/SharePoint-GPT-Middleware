# INFO: Microsoft Graph API for SharePoint and OneDrive

**Doc ID**: MSGRAPH-IN01
**Goal**: Exhaustive reference for all MS Graph API endpoints relevant to SharePoint and OneDrive
**Research Type**: MCPI (exhaustive by user request)
**Timeline**: Created 2026-01-28, Updates: 2
**Verification**: All endpoints verified against Microsoft Learn documentation (January 2026). See `_INFO_MSGRAPH_SHAREPOINT_ONEDRIVE_SOURCES.md` [MSGRAPH-IN01] for complete source list.

## Quick Reference Summary

### Permission Scopes (Copy/Paste Ready)

**Files (OneDrive/SharePoint Document Libraries):**
- `Files.Read` - Read user files (Delegated)
- `Files.Read.All` - Read all files user can access (Delegated/Application)
- `Files.ReadWrite` - Read/write user files (Delegated)
- `Files.ReadWrite.All` - Read/write all files (Delegated/Application)
- `Files.ReadWrite.AppFolder` - App-specific folder access (Delegated)

**Sites (SharePoint):**
- `Sites.Read.All` - Read all site collections (Delegated/Application)
- `Sites.ReadWrite.All` - Read/write all site collections (Delegated/Application)
- `Sites.FullControl.All` - Full control of all sites (Application only)
- `Sites.Selected` - Access to specific sites only (Application) **Note: Requires admin site-level grants via PowerShell or Admin API. See [Selected Permissions](https://learn.microsoft.com/en-us/graph/permissions-selected-overview)**

**Groups (for Group-connected sites):**
- `Group.Read.All` - Read group info including files (Delegated/Application)
- `Group.ReadWrite.All` - Read/write group info (Delegated/Application)

### Base URL

```
https://graph.microsoft.com/v1.0
```

### Throttling Warning

SharePoint and OneDrive APIs are subject to throttling. Handle HTTP 429 responses with exponential backoff using the `Retry-After` header. See [Throttling guidance](https://learn.microsoft.com/en-us/graph/throttling) and [SharePoint limits](https://learn.microsoft.com/en-us/sharepoint/dev/general-development/how-to-avoid-getting-throttled-or-blocked-in-sharepoint-online).

### Pagination

All list endpoints return paginated results. Use `@odata.nextLink` to fetch subsequent pages:
```http
GET {nextLink-value}
```
Default page size varies by endpoint (typically 200 items). Use `$top` to control page size.

### Resource Hierarchy

```
tenant
├── sites (SharePoint)
│   ├── drives (document libraries)
│   │   └── driveItems (files/folders)
│   ├── lists
│   │   └── listItems
│   ├── contentTypes
│   ├── columns
│   └── permissions
├── users
│   └── drive (OneDrive)
│       └── driveItems
└── groups
    └── drive (Group drive)
        └── driveItems
```

## Table of Contents

1. [Sites API](#1-sites-api)
2. [Lists API](#2-lists-api)
3. [ListItems API](#3-listitems-api)
4. [Drives API](#4-drives-api)
5. [DriveItems API](#5-driveitems-api)
6. [Permissions API](#6-permissions-api)
7. [Search API](#7-search-api)
8. [Content Types API](#8-content-types-api)
9. [Columns API](#9-columns-api)
10. [Addressing Patterns](#10-addressing-patterns)
11. [Sources](#11-sources)

## 1. Sites API

The `site` resource represents a SharePoint site (team site, communication site, etc.).

### 1.1 Site Methods

#### Get Root Site [VERIFIED]
```http
GET /sites/root
```
**Permissions**: Sites.Read.All (Delegated/Application)

#### Get Site by ID [VERIFIED]
```http
GET /sites/{site-id}
```
**Permissions**: Sites.Read.All (Delegated/Application)

#### Get Site by Path [VERIFIED]
```http
GET /sites/{hostname}:/{site-path}
```
**Example**:
```http
GET /sites/contoso.sharepoint.com:/sites/marketing
```
**Permissions**: Sites.Read.All (Delegated/Application)

#### Get Site for a Group [VERIFIED]
```http
GET /groups/{group-id}/sites/root
```
**Permissions**: Sites.Read.All, Group.Read.All (Delegated/Application)

#### List Sites (Search) [VERIFIED]
```http
GET /sites?search={query}
```
**Example**:
```http
GET /sites?search=contoso
```
**Permissions**: Sites.Read.All (Delegated/Application)

#### List All Sites Across Geographies [VERIFIED]
```http
GET /sites/getAllSites
```
**Permissions**: Sites.Read.All (Application only)

#### List Subsites [VERIFIED]
```http
GET /sites/{site-id}/sites
```
**Permissions**: Sites.Read.All (Delegated/Application)

#### Get Site Delta (Changes) [VERIFIED]
```http
GET /sites/delta
```
**Permissions**: Sites.Read.All (Application only)

#### Follow/Unfollow Site [VERIFIED]
```http
POST /users/{user-id}/followedSites/add
POST /users/{user-id}/followedSites/remove
```
**Body**:
```json
{
  "value": [
    { "id": "{site-id}" }
  ]
}
```
**Permissions**: Sites.ReadWrite.All (Delegated)

#### List Followed Sites [VERIFIED]
```http
GET /me/followedSites
```
**Permissions**: Sites.Read.All (Delegated)

### 1.2 Site Analytics

#### Get Site Analytics [VERIFIED]
```http
GET /sites/{site-id}/analytics
```
**Permissions**: Sites.Read.All (Delegated/Application)

#### Get Activities by Interval [VERIFIED]
```http
GET /sites/{site-id}/getActivitiesByInterval(startDateTime='{start}',endDateTime='{end}',interval='{interval}')
```
**Permissions**: Sites.Read.All (Delegated/Application)

### 1.3 Site Permissions

#### List Site Permissions [VERIFIED]
```http
GET /sites/{site-id}/permissions
```
**Permissions**: Sites.FullControl.All (Application only)

#### Get Site Permission [VERIFIED]
```http
GET /sites/{site-id}/permissions/{permission-id}
```
**Permissions**: Sites.FullControl.All (Application only)

#### Create Site Permission [VERIFIED]
```http
POST /sites/{site-id}/permissions
```
**Body**:
```json
{
  "roles": ["write"],
  "grantedToIdentities": [{
    "application": {
      "id": "{app-id}",
      "displayName": "App Name"
    }
  }]
}
```
**Permissions**: Sites.FullControl.All (Application only)

#### Update Site Permission [VERIFIED]
```http
PATCH /sites/{site-id}/permissions/{permission-id}
```
**Permissions**: Sites.FullControl.All (Application only)

#### Delete Site Permission [VERIFIED]
```http
DELETE /sites/{site-id}/permissions/{permission-id}
```
**Permissions**: Sites.FullControl.All (Application only)

### 1.4 Site ID Format

Site IDs use a composite format:
```
{hostname},{site-collection-id},{web-id}
```
**Example**: `contoso.sharepoint.com,da60e844-ba1d-49bc-b4d4-d5e36bae9019,712a596e-90a1-49e3-9b48-bfa80bee8740`

## 2. Lists API

The `list` resource represents a SharePoint list (including document libraries).

### 2.1 List Methods

#### Get Lists in Site [VERIFIED]
```http
GET /sites/{site-id}/lists
```
**Permissions**: Sites.Read.All (Delegated/Application)

#### Get List by ID [VERIFIED]
```http
GET /sites/{site-id}/lists/{list-id}
```
**Permissions**: Sites.Read.All (Delegated/Application)

#### Get List by Title [VERIFIED]
```http
GET /sites/{site-id}/lists/{list-title}
```
**Note**: Can use display name instead of ID
**Permissions**: Sites.Read.All (Delegated/Application)

#### Create List [VERIFIED]
```http
POST /sites/{site-id}/lists
```
**Body**:
```json
{
  "displayName": "My List",
  "list": {
    "template": "genericList"
  }
}
```
**List Templates**: `genericList`, `documentLibrary`, `events`, `tasks`, `contacts`, `announcements`, `links`, `survey`, `discussionBoard`

**Permissions**: Sites.ReadWrite.All (Delegated/Application)

#### Update List [VERIFIED]
```http
PATCH /sites/{site-id}/lists/{list-id}
```
**Permissions**: Sites.ReadWrite.All (Delegated/Application)

### 2.2 List Operations

#### List Long-Running Operations [VERIFIED]
```http
GET /sites/{site-id}/lists/{list-id}/operations
```
**Permissions**: Sites.Read.All (Delegated/Application)

#### Get WebSocket Endpoint [VERIFIED]
```http
GET /sites/{site-id}/lists/{list-id}/subscriptions/socketIo/getConnection
```
**Permissions**: Sites.Read.All (Delegated)

## 3. ListItems API

The `listItem` resource represents an item in a SharePoint list.

### 3.1 ListItem Methods

#### List Items [VERIFIED]
```http
GET /sites/{site-id}/lists/{list-id}/items
```
**With Field Expansion**:
```http
GET /sites/{site-id}/lists/{list-id}/items?expand=fields
```
**With Specific Fields**:
```http
GET /sites/{site-id}/lists/{list-id}/items?expand=fields(select=Title,Status)
```
**Permissions**: Sites.Read.All (Delegated/Application)

#### Get Item [VERIFIED]
```http
GET /sites/{site-id}/lists/{list-id}/items/{item-id}
```
**Permissions**: Sites.Read.All (Delegated/Application)

#### Create Item [VERIFIED]
```http
POST /sites/{site-id}/lists/{list-id}/items
```
**Body**:
```json
{
  "fields": {
    "Title": "New Item",
    "Status": "Active"
  }
}
```
**Permissions**: Sites.ReadWrite.All (Delegated/Application)

#### Update Item [VERIFIED]
```http
PATCH /sites/{site-id}/lists/{list-id}/items/{item-id}
```
**Body**:
```json
{
  "fields": {
    "Status": "Completed"
  }
}
```
**Permissions**: Sites.ReadWrite.All (Delegated/Application)

#### Delete Item [VERIFIED]
```http
DELETE /sites/{site-id}/lists/{list-id}/items/{item-id}
```
**Permissions**: Sites.ReadWrite.All (Delegated/Application)

#### Get Item Delta (Changes) [VERIFIED]
```http
GET /sites/{site-id}/lists/{list-id}/items/delta
```
**Permissions**: Sites.Read.All (Delegated/Application)

### 3.2 ListItem Analytics

#### Get Item Analytics [VERIFIED]
```http
GET /sites/{site-id}/lists/{list-id}/items/{item-id}/analytics
```
**Permissions**: Sites.Read.All (Delegated/Application)

### 3.3 Document Set Versions

#### List Document Set Versions [VERIFIED]
```http
GET /sites/{site-id}/lists/{list-id}/items/{item-id}/documentSetVersions
```
**Permissions**: Sites.Read.All (Delegated/Application)

#### Create Document Set Version [VERIFIED]
```http
POST /sites/{site-id}/lists/{list-id}/items/{item-id}/documentSetVersions
```
**Permissions**: Sites.ReadWrite.All (Delegated/Application)

#### Restore Document Set Version [VERIFIED]
```http
POST /sites/{site-id}/lists/{list-id}/items/{item-id}/documentSetVersions/{version-id}/restore
```
**Permissions**: Sites.ReadWrite.All (Delegated/Application)

## 4. Drives API

The `drive` resource represents a OneDrive or SharePoint document library.

### 4.1 Drive Access Patterns

#### Current User's OneDrive [VERIFIED]
```http
GET /me/drive
```
**Permissions**: Files.Read, Files.ReadWrite (Delegated)

#### Specific User's OneDrive [VERIFIED]
```http
GET /users/{user-id}/drive
```
**Permissions**: Files.Read.All, Files.ReadWrite.All (Delegated/Application)

#### Group's Drive [VERIFIED]
```http
GET /groups/{group-id}/drive
```
**Permissions**: Files.Read.All, Group.Read.All (Delegated/Application)

#### Site's Default Drive [VERIFIED]
```http
GET /sites/{site-id}/drive
```
**Permissions**: Sites.Read.All, Files.Read.All (Delegated/Application)

#### All Drives in Site [VERIFIED]
```http
GET /sites/{site-id}/drives
```
**Permissions**: Sites.Read.All (Delegated/Application)

#### Get Drive by ID [VERIFIED]
```http
GET /drives/{drive-id}
```
**Permissions**: Files.Read.All (Delegated/Application)

### 4.2 Drive Methods

#### List Drives [VERIFIED]
```http
GET /me/drives
GET /users/{user-id}/drives
GET /sites/{site-id}/drives
GET /groups/{group-id}/drives
```
**Permissions**: Files.Read.All (Delegated/Application)

#### Get Drive Root [VERIFIED]
```http
GET /drives/{drive-id}/root
```
**Permissions**: Files.Read (Delegated), Files.Read.All (Application)

#### List Children of Root [VERIFIED]
```http
GET /drives/{drive-id}/root/children
```
**Permissions**: Files.Read (Delegated), Files.Read.All (Application)

#### List Followed Items [VERIFIED]
```http
GET /drives/{drive-id}/following
```
**Permissions**: Files.Read (Delegated)

#### Get Special Folders [VERIFIED]
```http
GET /me/drive/special/{name}
```
**Special Names**: `approot`, `cameraroll`, `desktop`, `documents`, `downloads`, `music`, `photos`, `public`, `videos`

**Permissions**: Files.Read (Delegated)

#### Search in Drive [VERIFIED]
```http
GET /drives/{drive-id}/root/search(q='{search-text}')
```
**Permissions**: Files.Read (Delegated), Files.Read.All (Application)

#### Get Changes (Delta) [VERIFIED]
```http
GET /drives/{drive-id}/root/delta
```
**Permissions**: Files.Read (Delegated), Files.Read.All (Application)

## 5. DriveItems API

The `driveItem` resource represents files, folders, and other items in a drive.

### 5.1 Addressing DriveItems

#### By ID [VERIFIED]
```http
GET /drives/{drive-id}/items/{item-id}
GET /me/drive/items/{item-id}
```

#### By Path [VERIFIED]
```http
GET /drives/{drive-id}/root:/{path}
GET /me/drive/root:/Documents/file.docx
```

#### By Path with Continuation [VERIFIED]
```http
GET /drives/{drive-id}/root:/{path}:/children
GET /me/drive/root:/Documents:/children
```

### 5.2 Read Operations

#### Get Item [VERIFIED]
```http
GET /drives/{drive-id}/items/{item-id}
```
**Permissions**: Files.Read (Delegated), Files.Read.All (Application)

#### List Children [VERIFIED]
```http
GET /drives/{drive-id}/items/{folder-id}/children
```
**Permissions**: Files.Read (Delegated), Files.Read.All (Application)

#### Get Thumbnails [VERIFIED]
```http
GET /drives/{drive-id}/items/{item-id}/thumbnails
```
**Permissions**: Files.Read (Delegated), Files.Read.All (Application)

#### Download File Content [VERIFIED]
```http
GET /drives/{drive-id}/items/{item-id}/content
```
**Returns**: 302 redirect to download URL
**Permissions**: Files.Read (Delegated), Files.Read.All (Application)

#### Download in Specific Format [VERIFIED]
```http
GET /drives/{drive-id}/items/{item-id}/content?format={format}
```
**Formats**: `pdf`, `html`, `jpg`, `glb`
**Permissions**: Files.Read (Delegated), Files.Read.All (Application)

#### List Versions [VERIFIED]
```http
GET /drives/{drive-id}/items/{item-id}/versions
```
**Permissions**: Files.Read (Delegated), Files.Read.All (Application)

#### Get Version Content [VERIFIED]
```http
GET /drives/{drive-id}/items/{item-id}/versions/{version-id}/content
```
**Permissions**: Files.Read (Delegated), Files.Read.All (Application)

### 5.3 Create/Upload Operations

#### Create Folder [VERIFIED]
```http
POST /drives/{drive-id}/items/{parent-id}/children
```
**Body**:
```json
{
  "name": "New Folder",
  "folder": {},
  "@microsoft.graph.conflictBehavior": "rename"
}
```
**Conflict Behaviors**: `fail`, `replace`, `rename`
**Permissions**: Files.ReadWrite (Delegated), Files.ReadWrite.All (Application)

#### Upload Small File [VERIFIED]
```http
PUT /drives/{drive-id}/items/{parent-id}:/{filename}:/content
```
**Size Limit**: Up to 4MB. For larger files (4MB-250GB on SharePoint, 4MB-60GB on OneDrive), use upload session.
**Body**: Binary file content
**Permissions**: Files.ReadWrite (Delegated), Files.ReadWrite.All (Application)

#### Create Upload Session (Large Files) [VERIFIED]
```http
POST /drives/{drive-id}/items/{parent-id}:/{filename}:/createUploadSession
```
**Body**:
```json
{
  "item": {
    "@microsoft.graph.conflictBehavior": "rename",
    "name": "largefile.zip"
  }
}
```
**Response includes upload URL for chunked uploads (up to 60MB chunks)**
**Permissions**: Files.ReadWrite (Delegated), Files.ReadWrite.All (Application)

### 5.4 Update Operations

#### Update Item Metadata [VERIFIED]
```http
PATCH /drives/{drive-id}/items/{item-id}
```
**Body**:
```json
{
  "name": "new-name.docx",
  "description": "Updated description"
}
```
**Permissions**: Files.ReadWrite (Delegated), Files.ReadWrite.All (Application)

#### Move Item [VERIFIED]
```http
PATCH /drives/{drive-id}/items/{item-id}
```
**Body**:
```json
{
  "parentReference": {
    "id": "{new-parent-id}"
  },
  "name": "new-name.docx"
}
```
**Permissions**: Files.ReadWrite (Delegated), Files.ReadWrite.All (Application)

#### Copy Item [VERIFIED]
```http
POST /drives/{drive-id}/items/{item-id}/copy
```
**Body**:
```json
{
  "parentReference": {
    "driveId": "{target-drive-id}",
    "id": "{target-folder-id}"
  },
  "name": "copied-file.docx"
}
```
**Returns**: 202 Accepted with Location header for monitoring
**Permissions**: Files.ReadWrite (Delegated), Files.ReadWrite.All (Application)

### 5.5 Delete Operations

#### Delete Item (to Recycle Bin) [VERIFIED]
```http
DELETE /drives/{drive-id}/items/{item-id}
```
**Permissions**: Files.ReadWrite (Delegated), Files.ReadWrite.All (Application)

#### Restore from Recycle Bin [VERIFIED]
```http
POST /drives/{drive-id}/items/{item-id}/restore
```
**Permissions**: Files.ReadWrite (Delegated), Files.ReadWrite.All (Application)

#### Permanently Delete [VERIFIED]
```http
POST /drives/{drive-id}/items/{item-id}/permanentDelete
```
**Permissions**: Files.ReadWrite.All (Application only)

### 5.6 Check In/Out Operations (SharePoint)

#### Check Out [VERIFIED]
```http
POST /drives/{drive-id}/items/{item-id}/checkout
```
**Permissions**: Files.ReadWrite (Delegated), Files.ReadWrite.All (Application)

#### Check In [VERIFIED]
```http
POST /drives/{drive-id}/items/{item-id}/checkin
```
**Body**:
```json
{
  "comment": "Check-in comment",
  "checkInAs": "published"
}
```
**checkInAs options**: `published`, `minor`
**Permissions**: Files.ReadWrite (Delegated), Files.ReadWrite.All (Application)

#### Discard Checkout [VERIFIED]
```http
POST /drives/{drive-id}/items/{item-id}/discardCheckout
```
**Permissions**: Files.ReadWrite (Delegated), Files.ReadWrite.All (Application)

### 5.7 Preview and Embeds

#### Get Preview [VERIFIED]
```http
POST /drives/{drive-id}/items/{item-id}/preview
```
**Body**:
```json
{
  "page": 1,
  "zoom": 1
}
```
**Permissions**: Files.Read (Delegated), Files.Read.All (Application)

### 5.8 Follow/Unfollow

#### Follow Item [VERIFIED]
```http
POST /drives/{drive-id}/items/{item-id}/follow
```
**Permissions**: Files.Read (Delegated)

#### Unfollow Item [VERIFIED]
```http
POST /drives/{drive-id}/items/{item-id}/unfollow
```
**Permissions**: Files.Read (Delegated)

### 5.9 Sensitivity and Retention Labels

#### Extract Sensitivity Labels [VERIFIED]
```http
POST /drives/{drive-id}/items/{item-id}/extractSensitivityLabels
```
**Permissions**: Files.Read.All (Application)

#### Assign Sensitivity Label [VERIFIED]
```http
POST /drives/{drive-id}/items/{item-id}/assignSensitivityLabel
```
**Permissions**: Files.ReadWrite.All (Application)

#### Get Retention Label [VERIFIED]
```http
GET /drives/{drive-id}/items/{item-id}/retentionLabel
```
**Permissions**: Files.Read.All (Application)

#### Set Retention Label [VERIFIED]
```http
PATCH /drives/{drive-id}/items/{item-id}/retentionLabel
```
**Permissions**: Files.ReadWrite.All, RecordsManagement.ReadWrite.All (Application)

#### Remove Retention Label [VERIFIED]
```http
DELETE /drives/{drive-id}/items/{item-id}/retentionLabel
```
**Permissions**: Files.ReadWrite.All, RecordsManagement.ReadWrite.All (Application)

#### Lock/Unlock Record [VERIFIED]
```http
POST /drives/{drive-id}/items/{item-id}/retentionLabel/lockedForRecordState
```
**Permissions**: RecordsManagement.ReadWrite.All (Application)

## 6. Permissions API

The `permission` resource represents sharing permissions on files and folders.

### 6.1 Permission Methods

#### List Permissions [VERIFIED]
```http
GET /drives/{drive-id}/items/{item-id}/permissions
```
**Permissions**: Files.Read (Delegated), Files.Read.All (Application)

#### Get Permission [VERIFIED]
```http
GET /drives/{drive-id}/items/{item-id}/permissions/{permission-id}
```
**Permissions**: Files.Read (Delegated), Files.Read.All (Application)

#### Create Sharing Link [VERIFIED]
```http
POST /drives/{drive-id}/items/{item-id}/createLink
```
**Body**:
```json
{
  "type": "view",
  "scope": "organization",
  "expirationDateTime": "2024-12-31T23:59:59Z",
  "password": "optionalPassword"
}
```
**Link Types**: `view`, `edit`, `embed`
**Scopes**: `anonymous`, `organization`, `users`
**Permissions**: Files.ReadWrite (Delegated), Files.ReadWrite.All (Application)

#### Invite Users (Add Permissions) [VERIFIED]
```http
POST /drives/{drive-id}/items/{item-id}/invite
```
**Body**:
```json
{
  "recipients": [
    { "email": "user@example.com" }
  ],
  "roles": ["read"],
  "sendInvitation": true,
  "message": "Please review this document"
}
```
**Roles**: `read`, `write`, `sp.full control` (SharePoint only)
**Permissions**: Files.ReadWrite (Delegated), Files.ReadWrite.All (Application)

#### Update Permission [VERIFIED]
```http
PATCH /drives/{drive-id}/items/{item-id}/permissions/{permission-id}
```
**Body**:
```json
{
  "roles": ["write"]
}
```
**Permissions**: Files.ReadWrite (Delegated), Files.ReadWrite.All (Application)

#### Delete Permission [VERIFIED]
```http
DELETE /drives/{drive-id}/items/{item-id}/permissions/{permission-id}
```
**Permissions**: Files.ReadWrite (Delegated), Files.ReadWrite.All (Application)

#### Grant Access via Sharing Link [VERIFIED]
```http
POST /shares/{encoded-sharing-url}/permission/grant
```
**Permissions**: Files.ReadWrite.All (Application)

### 6.2 Accessing Shared Items

#### Decode Sharing URL [VERIFIED]
```http
GET /shares/{encoded-sharing-url}/driveItem
```
**Encoding**: Base64url encode the sharing URL, prefix with `u!`

**Example**:
```
Original URL: https://contoso.sharepoint.com/:w:/s/team/...
Encoded: u!aHR0cHM6Ly9jb250b3NvLnNoYXJlcG9pbnQuY29tLzp3Oi9zL3RlYW0v
```
**Permissions**: Files.Read (Delegated), Files.Read.All (Application)

## 7. Search API

The Microsoft Search API provides unified search across SharePoint and OneDrive.

### 7.1 Search Query [VERIFIED]

```http
POST /search/query
```
**Body**:
```json
{
  "requests": [
    {
      "entityTypes": ["driveItem"],
      "query": {
        "queryString": "contoso report"
      },
      "from": 0,
      "size": 25
    }
  ]
}
```

**Entity Types for SharePoint/OneDrive**:
- `driveItem` - Files and folders
- `listItem` - List items
- `list` - Lists
- `site` - Sites

**Permissions**: Files.Read.All, Sites.Read.All (Delegated/Application)

### 7.2 Search with KQL Filters [VERIFIED]

```json
{
  "requests": [
    {
      "entityTypes": ["driveItem"],
      "query": {
        "queryString": "contoso filetype:docx"
      }
    }
  ]
}
```

**Common KQL Filters**:
- `filetype:docx` - Filter by file type
- `path:"https://..."` - Filter by path
- `author:"John Doe"` - Filter by author
- `LastModifiedTime>2024-01-01` - Filter by date
- `isDocument:true` - Only documents (exclude folders)
- `contentclass:STS_List_Events` - SharePoint list type

### 7.3 Search with Property Selection [VERIFIED]

```json
{
  "requests": [
    {
      "entityTypes": ["driveItem"],
      "query": { "queryString": "quarterly report" },
      "fields": ["name", "createdDateTime", "lastModifiedDateTime", "webUrl"]
    }
  ]
}
```

### 7.4 Search Hidden Content [VERIFIED]

```json
{
  "requests": [
    {
      "entityTypes": ["listItem"],
      "query": { "queryString": "*" },
      "sharePointOneDriveOptions": {
        "includeHiddenContent": true
      }
    }
  ]
}
```

## 8. Content Types API

The `contentType` resource represents SharePoint content types.

### 8.1 Content Type Methods

#### List Content Types in Site [VERIFIED]
```http
GET /sites/{site-id}/contentTypes
```
**Permissions**: Sites.Read.All (Delegated/Application)

#### List Content Types in List [VERIFIED]
```http
GET /sites/{site-id}/lists/{list-id}/contentTypes
```
**Permissions**: Sites.Read.All (Delegated/Application)

#### Get Content Type [VERIFIED]
```http
GET /sites/{site-id}/contentTypes/{contentType-id}
```
**Permissions**: Sites.Read.All (Delegated/Application)

#### Create Content Type [VERIFIED]
```http
POST /sites/{site-id}/contentTypes
```
**Body**:
```json
{
  "name": "Custom Document",
  "description": "Custom document type",
  "base": {
    "id": "0x0101"
  },
  "group": "Custom Content Types"
}
```
**Permissions**: Sites.ReadWrite.All (Delegated/Application)

#### Update Content Type [VERIFIED]
```http
PATCH /sites/{site-id}/contentTypes/{contentType-id}
```
**Permissions**: Sites.ReadWrite.All (Delegated/Application)

#### Delete Content Type [VERIFIED]
```http
DELETE /sites/{site-id}/contentTypes/{contentType-id}
```
**Permissions**: Sites.ReadWrite.All (Delegated/Application)

#### Publish Content Type [VERIFIED]
```http
POST /sites/{site-id}/contentTypes/{contentType-id}/publish
```
**Permissions**: Sites.FullControl.All (Application)

#### Unpublish Content Type [VERIFIED]
```http
POST /sites/{site-id}/contentTypes/{contentType-id}/unpublish
```
**Permissions**: Sites.FullControl.All (Application)

#### Check if Published [VERIFIED]
```http
GET /sites/{site-id}/contentTypes/{contentType-id}/isPublished
```
**Permissions**: Sites.Read.All (Delegated/Application)

#### Add Content Type Copy [VERIFIED]
```http
POST /sites/{site-id}/contentTypes/addCopy
```
**Body**:
```json
{
  "contentType": "https://graph.microsoft.com/v1.0/sites/{hub-site-id}/contentTypes/{contentType-id}"
}
```
**Permissions**: Sites.ReadWrite.All (Delegated/Application)

#### Associate with Hub Sites [VERIFIED]
```http
POST /sites/{site-id}/contentTypes/{contentType-id}/associateWithHubSites
```
**Permissions**: Sites.FullControl.All (Application)

## 9. Columns API

The `columnDefinition` resource represents columns in sites, lists, or content types.

### 9.1 Column Methods

#### List Columns in Site [VERIFIED]
```http
GET /sites/{site-id}/columns
```
**Permissions**: Sites.Read.All (Delegated/Application)

#### List Columns in List [VERIFIED]
```http
GET /sites/{site-id}/lists/{list-id}/columns
```
**Permissions**: Sites.Read.All (Delegated/Application)

#### List Columns in Content Type [VERIFIED]
```http
GET /sites/{site-id}/contentTypes/{contentType-id}/columns
```
**Permissions**: Sites.Read.All (Delegated/Application)

#### Get Column [VERIFIED]
```http
GET /sites/{site-id}/columns/{column-id}
```
**Permissions**: Sites.Read.All (Delegated/Application)

#### Create Column in Site [VERIFIED]
```http
POST /sites/{site-id}/columns
```
**Body Example (Text Column)**:
```json
{
  "name": "CustomField",
  "text": {
    "maxLength": 255
  }
}
```
**Permissions**: Sites.ReadWrite.All (Delegated/Application)

#### Create Column in List [VERIFIED]
```http
POST /sites/{site-id}/lists/{list-id}/columns
```
**Body Example (Choice Column)**:
```json
{
  "name": "Status",
  "choice": {
    "choices": ["Active", "Pending", "Closed"],
    "displayAs": "dropDownMenu"
  }
}
```
**Permissions**: Sites.ReadWrite.All (Delegated/Application)

#### Update Column [VERIFIED]
```http
PATCH /sites/{site-id}/columns/{column-id}
```
**Permissions**: Sites.ReadWrite.All (Delegated/Application)

#### Delete Column [VERIFIED]
```http
DELETE /sites/{site-id}/columns/{column-id}
```
**Permissions**: Sites.ReadWrite.All (Delegated/Application)

### 9.2 Column Types

Columns support these type-specific properties:
- `boolean` - Yes/No field
- `calculated` - Calculated field with formula
- `choice` - Choice/dropdown field
- `currency` - Currency field
- `dateTime` - Date/time field
- `lookup` - Lookup to another list
- `number` - Numeric field
- `personOrGroup` - People picker
- `text` - Single line text
- `hyperlinkOrPicture` - URL/image
- `thumbnail` - Thumbnail image
- `contentApprovalStatus` - Approval status
- `term` - Managed metadata

## 10. Addressing Patterns

### 10.1 Site Addressing

```http
# By hostname only (root site)
GET /sites/contoso.sharepoint.com

# By hostname and site collection ID
GET /sites/contoso.sharepoint.com,{site-collection-id}

# By full composite ID
GET /sites/contoso.sharepoint.com,{site-collection-id},{web-id}

# By path
GET /sites/contoso.sharepoint.com:/sites/marketing

# By path with resource continuation
GET /sites/contoso.sharepoint.com:/sites/marketing:/lists
```

### 10.2 Drive Item Path Addressing

```http
# From root by path
GET /drives/{drive-id}/root:/{path-to-item}

# Path with resource continuation
GET /drives/{drive-id}/root:/{path-to-folder}:/children

# Nested path
GET /me/drive/root:/Documents/Reports/Q1:/children
```

### 10.3 Cross-Tenant Access

For multi-geo tenants:
```http
# List all sites across geographies
GET /sites/getAllSites

# Site in specific geography
GET /sites/{geo-code}.sharepoint.com:/sites/teamsite
```

## 11. Sources

### Primary Documentation

- **MSGRAPH-IN01-SC-MSLEARN-SPOV**: [SharePoint sites and content API overview](https://learn.microsoft.com/en-us/graph/sharepoint-concept-overview)
- **MSGRAPH-IN01-SC-MSLEARN-SPRES**: [Working with SharePoint sites in Microsoft Graph](https://learn.microsoft.com/en-us/graph/api/resources/sharepoint?view=graph-rest-1.0)
- **MSGRAPH-IN01-SC-MSLEARN-ODOV**: [OneDrive file storage API overview](https://learn.microsoft.com/en-us/graph/onedrive-concept-overview)
- **MSGRAPH-IN01-SC-MSLEARN-ODRES**: [Working with files in Microsoft Graph](https://learn.microsoft.com/en-us/graph/api/resources/onedrive?view=graph-rest-1.0)

### Resource Type Documentation

- **MSGRAPH-IN01-SC-MSLEARN-SITE**: [site resource type](https://learn.microsoft.com/en-us/graph/api/resources/site?view=graph-rest-1.0)
- **MSGRAPH-IN01-SC-MSLEARN-LIST**: [list resource type](https://learn.microsoft.com/en-us/graph/api/resources/list?view=graph-rest-1.0)
- **MSGRAPH-IN01-SC-MSLEARN-LSTITM**: [listItem resource type](https://learn.microsoft.com/en-us/graph/api/resources/listitem?view=graph-rest-1.0)
- **MSGRAPH-IN01-SC-MSLEARN-DRIVE**: [drive resource type](https://learn.microsoft.com/en-us/graph/api/resources/drive?view=graph-rest-1.0)
- **MSGRAPH-IN01-SC-MSLEARN-DRITM**: [driveItem resource type](https://learn.microsoft.com/en-us/graph/api/resources/driveitem?view=graph-rest-1.0)
- **MSGRAPH-IN01-SC-MSLEARN-PERM**: [permission resource type](https://learn.microsoft.com/en-us/graph/api/resources/permission?view=graph-rest-1.0)
- **MSGRAPH-IN01-SC-MSLEARN-CTYPE**: [contentType resource type](https://learn.microsoft.com/en-us/graph/api/resources/contenttype?view=graph-rest-1.0)
- **MSGRAPH-IN01-SC-MSLEARN-COLDEF**: [columnDefinition resource type](https://learn.microsoft.com/en-us/graph/api/resources/columndefinition?view=graph-rest-1.0)

### Permissions Documentation

- **MSGRAPH-IN01-SC-MSLEARN-PERMS**: [Microsoft Graph permissions reference](https://learn.microsoft.com/en-us/graph/permissions-reference)
- **MSGRAPH-IN01-SC-MSLEARN-ODPERM**: [Understanding OneDrive API permission scopes](https://learn.microsoft.com/en-us/onedrive/developer/rest-api/concepts/permissions_reference?view=odsp-graph-online)
- **MSGRAPH-IN01-SC-MSLEARN-SELPR**: [Overview of Selected Permissions in OneDrive and SharePoint](https://learn.microsoft.com/en-us/graph/permissions-selected-overview)

### Search Documentation

- **MSGRAPH-IN01-SC-MSLEARN-SRCHOV**: [Microsoft Search API overview](https://learn.microsoft.com/en-us/graph/search-concept-overview)
- **MSGRAPH-IN01-SC-MSLEARN-SRCHFL**: [Search OneDrive and SharePoint content](https://learn.microsoft.com/en-us/graph/search-concept-files)

### Additional Resources

- **MSGRAPH-IN01-SC-MSLEARN-RESTV2**: [Operations using SharePoint REST v2 (Microsoft Graph) endpoints](https://learn.microsoft.com/en-us/sharepoint/dev/apis/sharepoint-rest-graph)
- **MSGRAPH-IN01-SC-MSLEARN-ADDR**: [Addressing driveItems](https://learn.microsoft.com/en-us/graph/onedrive-addressing-driveitems)

## Document History

**[2026-01-28 16:35]**
- Added: Verification basis note in header
- Added: Sites.Selected warning with link to setup docs
- Added: Throttling warning section with links
- Added: Pagination section with nextLink pattern
- Added: Upload size limits (4MB PUT, 250GB session)

**[2026-01-28 16:05]**
- Fixed: Removed duplicate Search Sites entry
- Added: Timeline field

**[2026-01-28 15:30]**
- Initial document created with exhaustive endpoint coverage
- Added: Sites, Lists, ListItems, Drives, DriveItems, Permissions, Search, ContentTypes, Columns APIs
- Added: Permission requirements for all endpoints
- Added: Syntax examples and use cases
- Added: Addressing patterns section
- Added: Complete source documentation
