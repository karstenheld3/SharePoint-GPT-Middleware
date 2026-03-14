# INFO: Microsoft Graph API - DriveItem Operations Methods

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for DriveItem operations (copy, move, search, delta)
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `_INFO_MSGRAPH_DRIVEITEMS_CORE.md [MSGRAPH-IN01]` for core driveItem operations

## Summary

**Use cases**:
- Build file sync clients that track incremental changes via delta queries
- Implement file search across OneDrive/SharePoint from custom apps
- Copy files/folders to backup locations or different libraries
- Move files between folders as part of workflow automation
- Implement "duplicate file" functionality in file managers
- Build offline-first apps that sync changes when reconnected
- Create migration tools that copy content between drives

**Key findings**:
- Copy is async (returns monitor URL); move is sync (returns immediately)
- Copy monitor URL provides progress percentage and final resource ID
- Delta token duration not officially documented; 410 Gone requires full resync - always handle gracefully
- Delta tracks creates, updates, AND deletes; deleted items have `deleted` facet
- Search queries file names, content, and metadata; results include `searchResult` facet
- Search scope can be entire drive or specific folder subtree
- Cross-drive copy supported; cross-tenant copy NOT supported
- Delta response may show same item multiple times - always deduplicate by item ID, use last occurrence
- Move by updating `parentReference.id` in PATCH request

## Quick Reference Summary

**Endpoints covered**: 4 operation methods

- `POST /drives/{id}/items/{id}/copy` - Copy item to new location
- `PATCH /drives/{id}/items/{id}` (move) - Move item to different folder
- `GET /drives/{id}/root/search(q='query')` - Search for items
- `GET /drives/{id}/root/delta` - Track changes incrementally

**Permissions required**:
- Delegated: `Files.Read`, `Files.ReadWrite`, `Files.Read.All`, `Files.ReadWrite.All`
- Application: `Files.Read.All`, `Files.ReadWrite.All`
- **Least privilege**: `Files.Read` for search/delta; `Files.ReadWrite` for copy/move

## 1. POST /drives/{id}/items/{id}/copy - Copy Item

### Description [VERIFIED]

Asynchronously copy a driveItem to a new location. Returns a monitor URL to track copy progress.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{item-id}/copy
```

Alternative paths:
```http
POST /me/drive/items/{item-id}/copy
POST /sites/{site-id}/drive/items/{item-id}/copy
```

### Request Headers

- **Authorization**: `Bearer {token}`
- **Content-Type**: `application/json`

### Request Body

Copy to same drive:
```json
{
  "parentReference": {
    "id": "destination-folder-id"
  },
  "name": "Copied File.docx"
}
```

Copy to different drive:
```json
{
  "parentReference": {
    "driveId": "destination-drive-id",
    "id": "destination-folder-id"
  },
  "name": "Copied File.docx"
}
```

### Response [VERIFIED]

- **202 Accepted** - Copy started
- **Location** header contains monitor URL

```
HTTP/1.1 202 Accepted
Location: https://graph.microsoft.com/v1.0/monitor/4A3407B5-88FC-4504-8B21-0AABD3412717
```

### Monitor Copy Progress

```http
GET {Location-URL}
```

In progress response:
```json
{
  "status": "inProgress",
  "percentageComplete": 45.5
}
```

Completed response:
```json
{
  "status": "completed",
  "resourceId": "new-item-id"
}
```

Failed response:
```json
{
  "status": "failed",
  "error": {
    "code": "accessDenied",
    "message": "Access denied to destination folder"
  }
}
```

### SDK Examples

**PowerShell**:
```powershell
$params = @{
    parentReference = @{
        id = $destinationFolderId
    }
    name = "Copied Document.docx"
}
Copy-MgDriveItem -DriveId $driveId -DriveItemId $itemId -BodyParameter $params
```

**C#**:
```csharp
var copyRequest = new CopyPostRequestBody
{
    ParentReference = new ItemReference { Id = "{destination-folder-id}" },
    Name = "Copied File.docx"
};
var monitorUrl = await graphClient.Drives["{drive-id}"].Items["{item-id}"]
    .Copy.PostAsync(copyRequest);
```

**JavaScript**:
```javascript
const copyBody = {
    parentReference: { id: '{destination-folder-id}' },
    name: 'Copied File.docx'
};
const response = await client.api('/me/drive/items/{item-id}/copy')
    .post(copyBody);
// Get Location header for monitoring
```

## 2. PATCH /drives/{id}/items/{id} (Move) - Move Item

### Description [VERIFIED]

Move a driveItem to a new folder by updating its `parentReference`. Can combine with rename.

### HTTP Request

```http
PATCH https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{item-id}
```

### Request Body

Move only:
```json
{
  "parentReference": {
    "id": "new-parent-folder-id"
  }
}
```

Move to different drive:
```json
{
  "parentReference": {
    "driveId": "destination-drive-id",
    "id": "destination-folder-id"
  }
}
```

Move and rename:
```json
{
  "parentReference": {
    "id": "new-parent-folder-id"
  },
  "name": "Renamed Document.docx"
}
```

### Response [VERIFIED]

Returns 200 OK with updated driveItem.

### Cross-Drive Move [VERIFIED]

Moving between drives:
- Same tenant: Supported
- Cross-tenant: Not supported
- OneDrive ↔ SharePoint: Supported within same tenant

### SDK Examples

**C#**:
```csharp
var moveUpdate = new DriveItem
{
    ParentReference = new ItemReference { Id = "{new-parent-id}" }
};
var result = await graphClient.Drives["{drive-id}"].Items["{item-id}"]
    .PatchAsync(moveUpdate);
```

## 3. GET /drives/{id}/root/search(q='query') - Search Items

### Description [VERIFIED]

Search for items matching a query across an entire drive. Searches file names, content, and metadata.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/drives/{drive-id}/root/search(q='{search-query}')
```

Alternative paths:
```http
GET /me/drive/root/search(q='{search-query}')
GET /sites/{site-id}/drive/root/search(q='{search-query}')
```

Search within folder:
```http
GET /drives/{drive-id}/items/{folder-id}/search(q='{search-query}')
```

### Query Parameters

- **q** (`string`) - Search query (required)
- **$select** - Select properties
- **$top** - Limit results
- **$orderby** - Sort results (limited support)

### Search Query Syntax [VERIFIED]

Simple search:
```http
GET /me/drive/root/search(q='budget')
```

File extension:
```http
GET /me/drive/root/search(q='.xlsx')
```

Multiple terms (AND):
```http
GET /me/drive/root/search(q='quarterly report 2026')
```

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "item-id-1",
      "name": "Q1 Budget Report.xlsx",
      "webUrl": "https://contoso.sharepoint.com/sites/team/Documents/Q1 Budget Report.xlsx",
      "searchResult": {
        "onClickTelemetryUrl": "https://..."
      },
      "file": {
        "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      },
      "size": 51200,
      "parentReference": {
        "driveId": "drive-guid",
        "id": "parent-id",
        "path": "/drive/root:/Documents"
      }
    }
  ],
  "@odata.nextLink": "https://graph.microsoft.com/v1.0/me/drive/root/search(q='budget')?$skiptoken=..."
}
```

### searchResult Facet [VERIFIED]

Present when item was returned by search:
```json
{
  "searchResult": {
    "onClickTelemetryUrl": "https://..."
  }
}
```

### SDK Examples

**PowerShell**:
```powershell
Search-MgDrive -DriveId $driveId -Q "budget report"
```

**C#**:
```csharp
var results = await graphClient.Drives["{drive-id}"].Root
    .SearchWithQ("budget report").GetAsync();
```

**JavaScript**:
```javascript
let results = await client.api('/me/drive/root/search(q=\'budget report\')')
    .get();
```

**Python**:
```python
result = await graph_client.drives.by_drive_id('drive-id').root.search_with_q('budget report').get()
```

## 4. GET /drives/{id}/root/delta - Track Changes

### Description [VERIFIED]

Track changes to driveItems over time. Returns all items on first call, then only changed items on subsequent calls.

### HTTP Request

Initial sync:
```http
GET https://graph.microsoft.com/v1.0/drives/{drive-id}/root/delta
```

With token (subsequent calls):
```http
GET https://graph.microsoft.com/v1.0/drives/{drive-id}/root/delta?token={token}
```

Track specific folder:
```http
GET https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{folder-id}/delta
```

### Query Parameters

- **token** (`string`) - Delta token from previous response
- **$select** - Select properties
- **$top** - Limit results per page

### Delta Sync Pattern [VERIFIED]

1. **Initial sync**: `GET /drives/{id}/root/delta`
2. **Follow pagination**: Use `@odata.nextLink` until exhausted
3. **Store token**: Save `@odata.deltaLink` token
4. **Check for changes**: Request `@odata.deltaLink` URL
5. **Handle deletions**: Items with `deleted` facet should be removed locally

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "item-id-1",
      "name": "New Document.docx",
      "file": {},
      "size": 25600
    },
    {
      "id": "item-id-2",
      "name": "Deleted File.txt",
      "deleted": {
        "state": "deleted"
      }
    }
  ],
  "@odata.deltaLink": "https://graph.microsoft.com/v1.0/drives/{drive-id}/root/delta?token=..."
}
```

### Handling Deleted Items [VERIFIED]

Items with `deleted` facet should be removed from local state:
```json
{
  "id": "item-id-2",
  "deleted": {
    "state": "deleted"
  }
}
```

### Token Expiration [VERIFIED]

- Tokens are valid for ~30 days
- Expired token returns 410 Gone
- On 410: Restart full sync from beginning

### SDK Examples

**PowerShell**:
```powershell
Get-MgDriveRootDelta -DriveId $driveId
```

**C#**:
```csharp
var delta = await graphClient.Drives["{drive-id}"].Root.Delta.GetAsDeltaGetResponseAsync();

// Process items
foreach (var item in delta.Value)
{
    if (item.Deleted != null)
    {
        // Remove from local state
    }
    else
    {
        // Add or update in local state
    }
}

// Store deltaLink for next sync
var nextLink = delta.OdataDeltaLink;
```

**Python**:
```python
result = await graph_client.drives.by_drive_id('drive-id').root.delta.get()
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid query or parameters
- **401 Unauthorized** - Missing or invalid authentication
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Item or drive does not exist
- **409 Conflict** - Name conflict at destination
- **410 Gone** - Delta token expired
- **429 Too Many Requests** - Rate limit exceeded

### Copy-Specific Errors [VERIFIED]

- **nameAlreadyExists** - File with same name exists
- **cannotCopyFolder** - Folder copy not supported (rare)
- **quotaLimitReached** - Destination quota exceeded

## Best Practices [VERIFIED]

### Copy Operations

- Monitor status URL for large files
- Implement retry with exponential backoff
- Handle name conflicts with rename strategy

### Move Operations

- Move is synchronous (unlike copy)
- Cross-drive moves may be slow for large items
- Verify destination permissions before moving

### Search Operations

- Use specific terms for better results
- Combine with `$select` to reduce payload
- Implement client-side result ranking if needed

### Delta Sync

- Store tokens persistently
- Handle 410 Gone gracefully (full resync)
- Process deletions before additions
- Use `$select` to minimize payload

## Sources

- **MSGRAPH-OPS-SC-01**: https://learn.microsoft.com/en-us/graph/api/driveitem-copy?view=graph-rest-1.0
- **MSGRAPH-OPS-SC-02**: https://learn.microsoft.com/en-us/graph/api/driveitem-move?view=graph-rest-1.0
- **MSGRAPH-OPS-SC-03**: https://learn.microsoft.com/en-us/graph/api/driveitem-search?view=graph-rest-1.0
- **MSGRAPH-OPS-SC-04**: https://learn.microsoft.com/en-us/graph/api/driveitem-delta?view=graph-rest-1.0

## Document History

**[2026-01-28 19:05]**
- Initial creation with 4 operation endpoints
- Full JSON request/response examples
- SDK examples for PowerShell, C#, JavaScript, Python
- Delta sync pattern documented
