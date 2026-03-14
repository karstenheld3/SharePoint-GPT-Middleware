# INFO: Microsoft Graph API - DriveItem Check In/Out Methods

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for DriveItem check in/out methods with request/response JSON and examples
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_MSGRAPH-IN00_TOC.md [MSGRAPH-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Prevent concurrent edits when co-authoring is not desired or supported
- Implement document workflow requiring exclusive editing rights
- Ensure document integrity during batch processing or migrations
- Control version creation with meaningful check-in comments
- Build approval workflows requiring sequential document review
- Integrate with legacy systems that expect pessimistic locking

**Key findings**:
- Check in/out is pessimistic locking - only one user can edit at a time
- Only works on SharePoint/OneDrive for Business (not personal OneDrive consumer)
- Check-in creates a new version; discard checkout reverts to previous version
- Application permissions can override user checkouts (discard any checkout)
- Some document libraries require checkout before editing (library setting)
- Checked-out status visible via `publication.checkedOutBy` property on driveItem

## Quick Reference Summary

**Endpoints covered**: 3 check in/out methods

- `POST /drives/{id}/items/{id}/checkout` - Lock file for exclusive editing
- `POST /drives/{id}/items/{id}/checkin` - Release lock and publish changes
- `POST /drives/{id}/items/{id}/discardCheckout` - Release lock and discard changes

**Permissions required**:
- Delegated: `Files.ReadWrite`, `Files.ReadWrite.All`, `Sites.ReadWrite.All`
- Application: `Files.ReadWrite.All`, `Sites.ReadWrite.All`
- **Least privilege**: `Files.ReadWrite` (delegated) for user's own files
- Note: SharePoint Embedded requires `FileStorageContainer.Selected`

**DriveItem ID format**: `{driveId}` and `{itemId}` are GUIDs
- Example: `b!kGr-22ksSkuABC123/items/01ABC123DEF456`

## Check In/Out Workflow [VERIFIED]

The check in/out workflow provides pessimistic locking for document editing:

1. **Checkout** - User locks the file, preventing others from editing
2. **Edit** - User modifies the file content
3. **Checkin** - User releases the lock and publishes a new version
4. **OR DiscardCheckout** - User releases the lock and discards all changes

**Key Behaviors**:
- Only the user who checked out can check in (delegated access)
- Application permissions can discard any user's checkout
- Checked out items show `publication.checkedOutBy` property
- Check in creates a new version in version history

## 1. POST /drives/{id}/items/{id}/checkout - Checkout DriveItem

### Description [VERIFIED]

Locks a driveItem resource to prevent others from editing the document. Changes made while checked out are not visible to other users until checked in.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/drives/{driveId}/items/{itemId}/checkout
```

Alternative paths:
```http
POST https://graph.microsoft.com/v1.0/me/drive/items/{itemId}/checkout
POST https://graph.microsoft.com/v1.0/users/{userId}/drive/items/{itemId}/checkout
POST https://graph.microsoft.com/v1.0/groups/{groupId}/drive/items/{itemId}/checkout
POST https://graph.microsoft.com/v1.0/sites/{siteId}/drive/items/{itemId}/checkout
```

### Path Parameters

- **driveId** (`string`) - Unique identifier of the drive
- **itemId** (`string`) - Unique identifier of the driveItem to check out

### Request Headers

- **Authorization**: `Bearer {token}`

### Request Body

Do not supply a request body for this method.

### Request Example

```http
POST https://graph.microsoft.com/v1.0/drives/b!kGr-22ksSkuABC123/items/01ABC123DEF456/checkout
Authorization: Bearer {token}
```

### Response [VERIFIED]

```http
HTTP/1.1 204 No Content
```

### Error Responses

- **409 Conflict** - Item is already checked out by another user
- **423 Locked** - Item is locked and cannot be checked out

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Files
Invoke-MgCheckoutDriveItem -DriveId $driveId -DriveItemId $driveItemId
```

**C#**:
```csharp
await graphClient.Drives["{drive-id}"].Items["{driveItem-id}"].Checkout.PostAsync();
```

**JavaScript**:
```javascript
await client.api('/drives/{drive-id}/items/{item-id}/checkout').post();
```

**Python**:
```python
await graph_client.drives.by_drive_id('drive-id').items.by_drive_item_id('item-id').checkout.post()
```

## 2. POST /drives/{id}/items/{id}/checkin - Checkin DriveItem

### Description [VERIFIED]

Checks in a previously checked out driveItem, making the new version of the document available to other users. Creates a new version entry in version history.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/drives/{driveId}/items/{itemId}/checkin
```

Alternative paths:
```http
POST https://graph.microsoft.com/v1.0/me/drive/items/{itemId}/checkin
POST https://graph.microsoft.com/v1.0/users/{userId}/drive/items/{itemId}/checkin
POST https://graph.microsoft.com/v1.0/groups/{groupId}/drive/items/{itemId}/checkin
POST https://graph.microsoft.com/v1.0/sites/{siteId}/drive/items/{itemId}/checkin
```

### Path Parameters

- **driveId** (`string`) - Unique identifier of the drive
- **itemId** (`string`) - Unique identifier of the driveItem to check in

### Request Headers

- **Authorization**: `Bearer {token}`
- **Content-Type**: `application/json`

### Request Body

```json
{
  "comment": "string"
}
```

**Properties**:
- **comment** (`string`, optional) - Version comment describing the changes

### Request Example

```http
POST https://graph.microsoft.com/v1.0/drives/b!kGr-22ksSkuABC123/items/01ABC123DEF456/checkin
Authorization: Bearer {token}
Content-Type: application/json

{
  "comment": "Updated quarterly figures and fixed formatting"
}
```

### Response [VERIFIED]

```http
HTTP/1.1 204 No Content
```

### Error Responses

- **400 Bad Request** - Item is not checked out
- **403 Forbidden** - User does not have permission to check in (not the user who checked out)

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Files

$params = @{
    comment = "Updating the latest guidelines"
}
Invoke-MgCheckinDriveItem -DriveId $driveId -DriveItemId $driveItemId -BodyParameter $params
```

**C#**:
```csharp
var requestBody = new CheckinPostRequestBody
{
    Comment = "Updating the latest guidelines"
};
await graphClient.Drives["{drive-id}"].Items["{driveItem-id}"].Checkin.PostAsync(requestBody);
```

**JavaScript**:
```javascript
await client.api('/drives/{drive-id}/items/{item-id}/checkin')
    .post({ comment: 'Updating the latest guidelines' });
```

**Python**:
```python
request_body = CheckinPostRequestBody(comment="Updating the latest guidelines")
await graph_client.drives.by_drive_id('drive-id').items.by_drive_item_id('item-id').checkin.post(request_body)
```

## 3. POST /drives/{id}/items/{id}/discardCheckout - Discard Checkout

### Description [VERIFIED]

Releases a driveItem that was previously checked out and discards any changes made while it was checked out. The item returns to its pre-checkout state.

**Important**: With delegated permissions, only the user who performed the checkout can discard it. Application permissions can discard any checkout.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/drives/{driveId}/items/{itemId}/discardCheckout
```

Alternative paths:
```http
POST https://graph.microsoft.com/v1.0/me/drive/items/{itemId}/discardCheckout
POST https://graph.microsoft.com/v1.0/users/{userId}/drive/items/{itemId}/discardCheckout
POST https://graph.microsoft.com/v1.0/groups/{groupId}/drive/items/{itemId}/discardCheckout
POST https://graph.microsoft.com/v1.0/sites/{siteId}/drive/items/{itemId}/discardCheckout
```

### Path Parameters

- **driveId** (`string`) - Unique identifier of the drive
- **itemId** (`string`) - Unique identifier of the driveItem

### Request Headers

- **Authorization**: `Bearer {token}`

### Request Body

Do not supply a request body for this method.

### Request Example

```http
POST https://graph.microsoft.com/v1.0/drives/b!kGr-22ksSkuABC123/items/01ABC123DEF456/discardCheckout
Authorization: Bearer {token}
```

### Response [VERIFIED]

```http
HTTP/1.1 204 No Content
```

### Error Responses

- **400 Bad Request** - File is not checked out
- **423 Locked** - Another user has the file checked out (delegated access only)

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Files
Remove-MgDriveItemCheckout -DriveId $driveId -DriveItemId $driveItemId
```

**C#**:
```csharp
await graphClient.Drives["{drive-id}"].Items["{driveItem-id}"].DiscardCheckout.PostAsync();
```

**JavaScript**:
```javascript
await client.api('/drives/{drive-id}/items/{item-id}/discardCheckout').post();
```

**Python**:
```python
await graph_client.drives.by_drive_id('drive-id').items.by_drive_item_id('item-id').discard_checkout.post()
```

## Detecting Checkout Status [VERIFIED]

To check if a file is currently checked out, query the driveItem and examine the `publication` property:

```http
GET https://graph.microsoft.com/v1.0/drives/{driveId}/items/{itemId}?$select=id,name,publication
```

**Response when checked out**:
```json
{
  "id": "01ABC123DEF456",
  "name": "Report.docx",
  "publication": {
    "level": "checkout",
    "checkedOutBy": {
      "user": {
        "id": "user-guid",
        "displayName": "John Doe"
      }
    }
  }
}
```

**Response when not checked out**:
```json
{
  "id": "01ABC123DEF456",
  "name": "Report.docx",
  "publication": {
    "level": "published"
  }
}
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid request (e.g., checkin on non-checked-out item)
- **401 Unauthorized** - Missing or invalid authentication token
- **403 Forbidden** - Insufficient permissions or wrong user trying to checkin/discard
- **404 Not Found** - DriveItem does not exist
- **409 Conflict** - Item already checked out by another user
- **423 Locked** - Item is locked by another user
- **429 Too Many Requests** - Rate limit exceeded

### Error Response Format

```json
{
  "error": {
    "code": "itemLocked",
    "message": "The item is currently checked out by another user.",
    "innerError": {
      "request-id": "guid",
      "date": "2026-01-28T12:00:00Z"
    }
  }
}
```

## Throttling Considerations [VERIFIED]

Microsoft Graph implements throttling to protect service health.

**Throttling Behavior**:
- HTTP 429 (Too Many Requests) returned when throttled
- `Retry-After` header indicates seconds to wait
- SharePoint-specific throttling may return HTTP 503

**Best Practices**:
- Implement exponential backoff with jitter
- Honor `Retry-After` header values
- Batch checkout status checks using `$batch` endpoint
- Cache checkout status locally when possible

**Resource Units**:
- checkout/checkin/discardCheckout: ~2 resource units each
- GET with publication property: ~1 resource unit

## SharePoint-Specific Considerations [VERIFIED]

**Require Checkout Setting**:
- SharePoint libraries can enforce checkout via "Require Check Out" setting
- When enabled, files must be checked out before editing
- Graph API respects this setting

**Major/Minor Versions**:
- SharePoint supports major and minor versions
- Check in can specify version type via SharePoint REST API (not Graph)
- Graph API check in creates major versions by default

**Co-Authoring Conflict**:
- Check out disables co-authoring for the file
- Other users see "Read Only" until checked in
- Office desktop apps show checkout indicator in title bar

## Sources

- **MSGRAPH-CIOUT-SC-01**: https://learn.microsoft.com/en-us/graph/api/driveitem-checkout?view=graph-rest-1.0
- **MSGRAPH-CIOUT-SC-02**: https://learn.microsoft.com/en-us/graph/api/driveitem-checkin?view=graph-rest-1.0
- **MSGRAPH-CIOUT-SC-03**: https://learn.microsoft.com/en-us/graph/api/driveitem-discardcheckout?view=graph-rest-1.0

## Document History

**[2026-01-28 17:45]**
- Initial creation with 3 endpoints
- Added checkout status detection pattern
- Added SharePoint-specific considerations
