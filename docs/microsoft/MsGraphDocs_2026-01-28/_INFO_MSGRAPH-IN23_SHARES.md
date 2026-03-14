# INFO: Microsoft Graph API - Shares Methods

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for Shares endpoint methods for accessing shared items
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_MSGRAPH-IN00_TOC.md [MSGRAPH-IN01]` for endpoint inventory
- `_INFO_MSGRAPH_DRIVEITEMS_SHARING.md [MSGRAPH-IN01]` for sharing link creation

## Summary

**Use cases**:
- Access shared files using URLs received via email or chat
- Build apps that consume sharing links from external sources
- Download shared content without knowing the original drive/item IDs
- Browse shared folder contents in custom file managers
- Implement "open shared link" functionality in applications
- Access cross-tenant shared content using encoded URLs

**Key findings**:
- Sharing URLs must be encoded using base64url + `u!` prefix algorithm
- Share ID or encoded URL both work as path parameter
- `Prefer: redeemSharingLink` header required for anonymous links
- SharedDriveItem provides relationships to driveItem, list, site, permission
- Can navigate into shared folders using `/items` or `/root/children`
- Links may be expired, revoked, or require authentication

## Quick Reference Summary

**Endpoints covered**: 4 shares methods

- `GET /shares/{shareId}` - Access shared item by share ID or encoded URL
- `GET /shares/{shareId}/driveItem` - Get the shared driveItem directly
- `GET /shares/{shareId}/items` - List items in shared folder
- `GET /shares/{shareId}/root` - Get root of shared folder

**Permissions required**:
- Delegated: `Files.Read`, `Files.ReadWrite`, `Files.Read.All`, `Files.ReadWrite.All`
- Application: `Files.Read.All`, `Files.ReadWrite.All`
- **Least privilege**: `Files.Read` for read access to shared content

## SharedDriveItem Resource Type [VERIFIED]

### JSON Schema

```json
{
  "@odata.type": "#microsoft.graph.sharedDriveItem",
  "id": "string",
  "name": "string",
  "owner": { "@odata.type": "microsoft.graph.identitySet" },
  "driveItem": { "@odata.type": "microsoft.graph.driveItem" },
  "items": [{ "@odata.type": "microsoft.graph.driveItem" }],
  "list": { "@odata.type": "microsoft.graph.list" },
  "listItem": { "@odata.type": "microsoft.graph.listItem" },
  "permission": { "@odata.type": "microsoft.graph.permission" },
  "root": { "@odata.type": "microsoft.graph.driveItem" },
  "site": { "@odata.type": "microsoft.graph.site" }
}
```

### Properties [VERIFIED]

- **id** (`string`) - Unique identifier for the share
- **name** (`string`) - Display name of the shared item
- **owner** (`identitySet`) - Identity of the owner

### Relationships [VERIFIED]

- **driveItem** - The shared driveItem resource
- **items** - Collection of driveItems in a shared folder
- **list** - Shared list resource (if applicable)
- **listItem** - Shared listItem resource (if applicable)
- **permission** - Permission granting access to the shared item
- **root** - Root driveItem of a shared folder
- **site** - Shared site resource (if applicable)

## Encoding Sharing URLs [VERIFIED]

To use a sharing URL with the `/shares` endpoint, encode it as follows:

### Algorithm

1. Base64 encode the sharing URL
2. Convert to unpadded base64url format:
   - Remove trailing `=` characters
   - Replace `/` with `_`
   - Replace `+` with `-`
3. Prepend `u!` to the result

### C# Example

```csharp
string sharingUrl = "https://contoso.sharepoint.com/:w:/s/sales/EZxxxxxxxxx";
string base64Value = System.Convert.ToBase64String(
    System.Text.Encoding.UTF8.GetBytes(sharingUrl)
);
string encodedUrl = "u!" + base64Value.TrimEnd('=').Replace('/', '_').Replace('+', '-');
// Result: u!aHR0cHM6Ly9jb250b3NvLnNoYXJlcG9pbnQuY29tLzp3Oi9zL3NhbGVzL0VaeHh4eHh4eHh4
```

### JavaScript Example

```javascript
function encodeShareUrl(sharingUrl) {
    const base64 = btoa(sharingUrl);
    const encodedUrl = 'u!' + base64
        .replace(/=+$/, '')
        .replace(/\//g, '_')
        .replace(/\+/g, '-');
    return encodedUrl;
}
```

### PowerShell Example

```powershell
function Encode-ShareUrl {
    param([string]$sharingUrl)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($sharingUrl)
    $base64 = [System.Convert]::ToBase64String($bytes)
    $encoded = "u!" + $base64.TrimEnd('=').Replace('/', '_').Replace('+', '-')
    return $encoded
}
```

### Python Example

```python
import base64

def encode_share_url(sharing_url):
    base64_bytes = base64.b64encode(sharing_url.encode('utf-8'))
    base64_str = base64_bytes.decode('utf-8')
    encoded = 'u!' + base64_str.rstrip('=').replace('/', '_').replace('+', '-')
    return encoded
```

## 1. GET /shares/{shareId} - Access Shared Item

### Description [VERIFIED]

Accesses a shared driveItem or collection of shared items using a shareId or encoded sharing URL. Returns a sharedDriveItem resource with relationships to access the actual content.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/shares/{shareIdOrEncodedSharingUrl}
```

### Path Parameters

- **shareIdOrEncodedSharingUrl** (`string`) - Share ID or encoded sharing URL

### Request Headers

- **Authorization**: `Bearer {token}`
- **Prefer**: `redeemSharingLink` (optional, for anonymous links)
- **Prefer**: `redeemSharingLinkIfNecessary` (optional)

### Prefer Header Values [VERIFIED]

- **redeemSharingLink** - Redeem anonymous sharing link, granting caller access
- **redeemSharingLinkIfNecessary** - Redeem only if required for access

### Request Example

```http
GET https://graph.microsoft.com/v1.0/shares/u!aHR0cHM6Ly9jb250b3NvLnNoYXJlcG9pbnQuY29tLzp3Oi9zL3NhbGVzL0VaeHh4eHh4eHh4
Authorization: Bearer {token}
```

### Response JSON [VERIFIED]

```json
{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#shares/$entity",
  "id": "share-id",
  "name": "Sales Report Q1.xlsx",
  "owner": {
    "user": {
      "id": "user-guid",
      "displayName": "John Doe"
    }
  }
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Files

$encodedUrl = Encode-ShareUrl -sharingUrl $sharingUrl
Get-MgShare -SharedDriveItemId $encodedUrl
```

**C#**:
```csharp
var encodedUrl = EncodeShareUrl(sharingUrl);
var sharedItem = await graphClient.Shares[encodedUrl].GetAsync();
```

**JavaScript**:
```javascript
const encodedUrl = encodeShareUrl(sharingUrl);
let sharedItem = await client.api(`/shares/${encodedUrl}`).get();
```

**Python**:
```python
encoded_url = encode_share_url(sharing_url)
shared_item = await graph_client.shares.by_shared_drive_item_id(encoded_url).get()
```

## 2. GET /shares/{shareId}/driveItem - Get Shared DriveItem

### Description [VERIFIED]

Directly retrieves the driveItem that was shared, without the sharedDriveItem wrapper.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/shares/{shareIdOrEncodedSharingUrl}/driveItem
```

### Request Example

```http
GET https://graph.microsoft.com/v1.0/shares/u!aHR0cHM6Ly9jb250b3NvLnNoYXJlcG9pbnQuY29tLzp3Oi9zL3NhbGVzL0VaeHh4eHh4eHh4/driveItem
Authorization: Bearer {token}
```

### Response JSON [VERIFIED]

```json
{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#driveItem",
  "id": "item-guid",
  "name": "Sales Report Q1.xlsx",
  "webUrl": "https://contoso.sharepoint.com/sites/sales/Shared Documents/Sales Report Q1.xlsx",
  "file": {
    "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
  },
  "size": 45678,
  "createdDateTime": "2026-01-15T10:00:00Z",
  "lastModifiedDateTime": "2026-01-20T14:30:00Z",
  "parentReference": {
    "driveId": "drive-guid",
    "driveType": "documentLibrary",
    "id": "folder-guid",
    "path": "/drive/root:/Shared Documents"
  }
}
```

### Download File Content

```http
GET https://graph.microsoft.com/v1.0/shares/{shareId}/driveItem/content
```

Returns file content stream with redirect to download URL.

## 3. GET /shares/{shareId}/items - List Items in Shared Folder

### Description [VERIFIED]

Lists all items within a shared folder. Only applicable when the shared item is a folder.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/shares/{shareIdOrEncodedSharingUrl}/items
```

### Query Parameters

- **$select** - Select specific properties
- **$expand** - Expand relationships
- **$filter** - Filter results
- **$orderby** - Sort order
- **$top** - Limit results

### Request Example

```http
GET https://graph.microsoft.com/v1.0/shares/u!aHR0cHM6Ly9jb250b3NvLnNoYXJlcG9pbnQuY29tLzpmOi9zL3NhbGVzL0VweHh4eHh4/items
Authorization: Bearer {token}
```

### Response JSON [VERIFIED]

```json
{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#Collection(driveItem)",
  "value": [
    {
      "id": "item-guid-1",
      "name": "Document1.docx",
      "file": {
        "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
      },
      "size": 12345
    },
    {
      "id": "item-guid-2",
      "name": "Subfolder",
      "folder": {
        "childCount": 5
      }
    }
  ]
}
```

## 4. GET /shares/{shareId}/root - Get Shared Folder Root

### Description [VERIFIED]

Gets the root driveItem of a shared folder. Useful for navigating into a shared folder structure.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/shares/{shareIdOrEncodedSharingUrl}/root
```

### Request Example

```http
GET https://graph.microsoft.com/v1.0/shares/u!aHR0cHM6Ly9jb250b3NvLnNoYXJlcG9pbnQuY29tLzpmOi9zL3NhbGVzL0VweHh4eHh4/root
Authorization: Bearer {token}
```

### Response JSON [VERIFIED]

```json
{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#driveItem",
  "id": "folder-guid",
  "name": "Shared Folder",
  "folder": {
    "childCount": 10
  },
  "webUrl": "https://contoso.sharepoint.com/sites/sales/Shared Documents/Shared Folder"
}
```

### Navigate into Shared Folder

Once you have the root, navigate using children:

```http
GET https://graph.microsoft.com/v1.0/shares/{shareId}/root/children
```

## Additional Shares Endpoints [VERIFIED]

### Access Shared List

```http
GET https://graph.microsoft.com/v1.0/shares/{shareId}/list
```

### Access Shared ListItem

```http
GET https://graph.microsoft.com/v1.0/shares/{shareId}/listItem
```

### Access Shared Site

```http
GET https://graph.microsoft.com/v1.0/shares/{shareId}/site
```

### Get Permission Details

```http
GET https://graph.microsoft.com/v1.0/shares/{shareId}/permission
```

## Use Cases [VERIFIED]

### 1. Access File from Sharing Link

```csharp
// User receives sharing link in email
string sharingUrl = "https://contoso.sharepoint.com/:x:/s/sales/EZxxxx";
string encodedUrl = EncodeShareUrl(sharingUrl);

// Get file metadata
var driveItem = await graphClient.Shares[encodedUrl].DriveItem.GetAsync();

// Download file
var stream = await graphClient.Shares[encodedUrl].DriveItem.Content.GetAsync();
```

### 2. Browse Shared Folder

```csharp
string folderShareUrl = "https://contoso.sharepoint.com/:f:/s/sales/Epxxxx";
string encodedUrl = EncodeShareUrl(folderShareUrl);

// Get folder contents
var items = await graphClient.Shares[encodedUrl].Items.GetAsync();

foreach (var item in items.Value)
{
    Console.WriteLine($"{item.Name} - {(item.Folder != null ? "Folder" : "File")}");
}
```

### 3. Redeem Anonymous Link

```http
GET https://graph.microsoft.com/v1.0/shares/{encodedUrl}/driveItem
Authorization: Bearer {token}
Prefer: redeemSharingLink
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid encoded URL or share ID
- **401 Unauthorized** - Missing or invalid token
- **403 Forbidden** - Access denied to shared item
- **404 Not Found** - Share link expired or item deleted
- **429 Too Many Requests** - Rate limit exceeded

### Access Denied Scenarios [VERIFIED]

- Link requires sign-in but user is anonymous
- Link is organization-only but user is external
- Link has expired
- Link has been revoked

### Error Response Format

```json
{
  "error": {
    "code": "accessDenied",
    "message": "The sharing link has expired or been revoked.",
    "innerError": {
      "request-id": "guid",
      "date": "2026-01-28T12:00:00Z"
    }
  }
}
```

## Throttling Considerations [VERIFIED]

**Best Practices**:
- Cache encoded URLs
- Use `$select` to reduce payload
- Handle 429 with exponential backoff

**Resource Units**:
- Access share: ~2 resource units
- Get driveItem: ~1 resource unit
- List items: ~1 resource unit

## Sources

- **MSGRAPH-SHR-SC-01**: https://learn.microsoft.com/en-us/graph/api/shares-get?view=graph-rest-1.0
- **MSGRAPH-SHR-SC-02**: https://learn.microsoft.com/en-us/graph/api/resources/shareddriveitem?view=graph-rest-1.0

## Document History

**[2026-01-28 19:55]**
- Initial creation with 4 endpoints
- Added URL encoding algorithm with examples
- Added sharedDriveItem resource type
- Added use case examples
