# INFO: Microsoft Graph API - Subscription (Webhook) Methods

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for Subscription methods for SharePoint/OneDrive change notifications
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_MSGRAPH-IN00_TOC.md [MSGRAPH-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Build real-time sync engines reacting to file changes
- Implement document workflow triggers when files are modified
- Create backup solutions notified of new or changed content
- Build audit trails tracking document modifications
- Implement approval workflows triggered by document uploads
- Sync external systems with SharePoint content changes

**Key findings**:
- Subscriptions expire (max 30 days for driveItem/list) - must renew proactively
- OneDrive for Business: can only subscribe to root folder, not subfolders or individual files
- Notifications indicate "something changed" - use delta query for actual changes
- Notification URL must be HTTPS and respond within 10 seconds
- Lifecycle notifications alert on subscription issues (removed, reauth needed)
- Security webhooks available for permission change notifications

## Quick Reference Summary

**Endpoints covered**: 5 subscription methods

- `GET /subscriptions` - List subscriptions
- `GET /subscriptions/{id}` - Get subscription
- `POST /subscriptions` - Create subscription
- `PATCH /subscriptions/{id}` - Update subscription (renew)
- `DELETE /subscriptions/{id}` - Delete subscription

**Permissions required**:
- DriveItem: `Files.Read`, `Files.ReadWrite`, `Files.Read.All`, `Files.ReadWrite.All`
- List: `Sites.Read.All`, `Sites.ReadWrite.All`
- **Note**: Permissions must match the resource being subscribed to

**Supported SharePoint/OneDrive Resources**:
- `driveItem` - Files and folders (root folder only for OneDrive for Business)
- `list` - SharePoint lists

## Subscription Resource Type [VERIFIED]

### JSON Schema

```json
{
  "id": "string",
  "resource": "string",
  "changeType": "created | updated | deleted",
  "clientState": "string",
  "notificationUrl": "string",
  "expirationDateTime": "datetime",
  "applicationId": "string",
  "creatorId": "string",
  "includeResourceData": false,
  "encryptionCertificate": "string",
  "encryptionCertificateId": "string",
  "latestSupportedTlsVersion": "v1_0 | v1_1 | v1_2 | v1_3",
  "lifecycleNotificationUrl": "string",
  "notificationQueryOptions": "string",
  "notificationUrlAppId": "string"
}
```

### Properties [VERIFIED]

- **id** (`string`) - Unique identifier for the subscription
- **resource** (`string`) - Resource path to monitor (e.g., `/drives/{id}/root`)
- **changeType** (`string`) - Types of changes: `created`, `updated`, `deleted` (comma-separated)
- **clientState** (`string`) - Value sent in notifications for validation (max 128 chars)
- **notificationUrl** (`string`) - HTTPS endpoint to receive notifications
- **expirationDateTime** (`dateTimeOffset`) - When subscription expires
- **applicationId** (`string`, read-only) - App that created the subscription
- **creatorId** (`string`, read-only) - User/app that created the subscription
- **includeResourceData** (`boolean`) - Include resource data in notification payload
- **latestSupportedTlsVersion** (`string`) - TLS version for notification endpoint
- **lifecycleNotificationUrl** (`string`) - Endpoint for lifecycle events

### Maximum Expiration Times [VERIFIED]

- **driveItem**: 30 days (43,200 minutes)
- **list**: 30 days (43,200 minutes)

**Note**: Subscriptions with expirationDateTime under 45 minutes auto-set to 45 minutes.

## 1. GET /subscriptions - List Subscriptions

### Description [VERIFIED]

Retrieves all subscriptions created by the app for the current user or app context.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/subscriptions
```

### Request Headers

- **Authorization**: `Bearer {token}`

### Request Example

```http
GET https://graph.microsoft.com/v1.0/subscriptions
Authorization: Bearer {token}
```

### Response JSON [VERIFIED]

```json
{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#subscriptions",
  "value": [
    {
      "id": "subscription-guid",
      "resource": "/drives/drive-guid/root",
      "changeType": "updated",
      "clientState": "secretValue",
      "notificationUrl": "https://webhook.contoso.com/api/notifications",
      "expirationDateTime": "2026-02-28T12:00:00Z",
      "applicationId": "app-guid",
      "creatorId": "user-guid"
    }
  ]
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.ChangeNotifications
Get-MgSubscription
```

**C#**:
```csharp
var subscriptions = await graphClient.Subscriptions.GetAsync();
```

**JavaScript**:
```javascript
let subscriptions = await client.api('/subscriptions').get();
```

**Python**:
```python
subscriptions = await graph_client.subscriptions.get()
```

## 2. GET /subscriptions/{id} - Get Subscription

### Description [VERIFIED]

Retrieves a specific subscription by ID.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/subscriptions/{subscriptionId}
```

### Request Example

```http
GET https://graph.microsoft.com/v1.0/subscriptions/abc123-def456
Authorization: Bearer {token}
```

### Response JSON [VERIFIED]

```json
{
  "id": "abc123-def456",
  "resource": "/drives/drive-guid/root",
  "changeType": "updated",
  "clientState": "secretValue",
  "notificationUrl": "https://webhook.contoso.com/api/notifications",
  "expirationDateTime": "2026-02-28T12:00:00Z"
}
```

## 3. POST /subscriptions - Create Subscription

### Description [VERIFIED]

Creates a new subscription to receive change notifications for the specified resource.

**DriveItem Limitations**:
- Personal OneDrive: Can subscribe to root folder or any subfolder
- OneDrive for Business: Can subscribe to **root folder only**
- Cannot subscribe to individual files (only folders)
- Notifications include changes to any item in the folder hierarchy

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/subscriptions
```

### Request Headers

- **Authorization**: `Bearer {token}`
- **Content-Type**: `application/json`
- **Prefer**: `includesecuritywebhooks` (optional, for permission change notifications)

### Request Body

```json
{
  "changeType": "created,updated,deleted",
  "notificationUrl": "https://webhook.contoso.com/api/notifications",
  "resource": "/drives/{driveId}/root",
  "expirationDateTime": "2026-02-28T12:00:00Z",
  "clientState": "secretClientValue"
}
```

### DriveItem Subscription Example

```http
POST https://graph.microsoft.com/v1.0/subscriptions
Authorization: Bearer {token}
Content-Type: application/json

{
  "changeType": "updated",
  "notificationUrl": "https://webhook.contoso.com/api/drive-changes",
  "resource": "/drives/b!kGr-22ksSkuABC123/root",
  "expirationDateTime": "2026-02-28T12:00:00Z",
  "clientState": "mySecretState123"
}
```

### List Subscription Example

```http
POST https://graph.microsoft.com/v1.0/subscriptions
Authorization: Bearer {token}
Content-Type: application/json

{
  "changeType": "created,updated,deleted",
  "notificationUrl": "https://webhook.contoso.com/api/list-changes",
  "resource": "/sites/contoso.sharepoint.com,site-guid,web-guid/lists/list-guid",
  "expirationDateTime": "2026-02-28T12:00:00Z",
  "clientState": "myListSecret456"
}
```

### Security Events Subscription

Include permission change notifications:

```http
POST https://graph.microsoft.com/v1.0/subscriptions
Authorization: Bearer {token}
Content-Type: application/json
Prefer: includesecuritywebhooks

{
  "changeType": "updated",
  "notificationUrl": "https://webhook.contoso.com/api/security",
  "resource": "/drives/drive-guid/root",
  "expirationDateTime": "2026-02-28T12:00:00Z",
  "clientState": "securityState"
}
```

### Response JSON [VERIFIED]

```json
{
  "id": "new-subscription-guid",
  "resource": "/drives/b!kGr-22ksSkuABC123/root",
  "changeType": "updated",
  "clientState": "mySecretState123",
  "notificationUrl": "https://webhook.contoso.com/api/drive-changes",
  "expirationDateTime": "2026-02-28T12:00:00Z",
  "applicationId": "app-guid",
  "creatorId": "user-guid"
}
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.ChangeNotifications

$params = @{
    changeType = "updated"
    notificationUrl = "https://webhook.contoso.com/api/notifications"
    resource = "/drives/drive-guid/root"
    expirationDateTime = (Get-Date).AddDays(29).ToString("o")
    clientState = "secretState"
}
New-MgSubscription -BodyParameter $params
```

**C#**:
```csharp
var subscription = new Subscription
{
    ChangeType = "updated",
    NotificationUrl = "https://webhook.contoso.com/api/notifications",
    Resource = "/drives/{drive-id}/root",
    ExpirationDateTime = DateTime.UtcNow.AddDays(29),
    ClientState = "secretState"
};
var result = await graphClient.Subscriptions.PostAsync(subscription);
```

**JavaScript**:
```javascript
let subscription = await client.api('/subscriptions').post({
    changeType: 'updated',
    notificationUrl: 'https://webhook.contoso.com/api/notifications',
    resource: '/drives/{drive-id}/root',
    expirationDateTime: new Date(Date.now() + 29 * 24 * 60 * 60 * 1000).toISOString(),
    clientState: 'secretState'
});
```

**Python**:
```python
from datetime import datetime, timedelta

subscription = Subscription(
    change_type="updated",
    notification_url="https://webhook.contoso.com/api/notifications",
    resource="/drives/drive-id/root",
    expiration_date_time=datetime.utcnow() + timedelta(days=29),
    client_state="secretState"
)
result = await graph_client.subscriptions.post(subscription)
```

## 4. PATCH /subscriptions/{id} - Update Subscription

### Description [VERIFIED]

Renews a subscription by extending its expiration time. This is the primary use case - subscriptions must be renewed before expiration.

### HTTP Request

```http
PATCH https://graph.microsoft.com/v1.0/subscriptions/{subscriptionId}
```

### Request Body

```json
{
  "expirationDateTime": "datetime"
}
```

### Request Example

```http
PATCH https://graph.microsoft.com/v1.0/subscriptions/abc123-def456
Authorization: Bearer {token}
Content-Type: application/json

{
  "expirationDateTime": "2026-03-28T12:00:00Z"
}
```

### Response JSON [VERIFIED]

Returns the updated subscription object.

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.ChangeNotifications

$params = @{
    expirationDateTime = (Get-Date).AddDays(29).ToString("o")
}
Update-MgSubscription -SubscriptionId $subscriptionId -BodyParameter $params
```

**C#**:
```csharp
var subscription = new Subscription
{
    ExpirationDateTime = DateTime.UtcNow.AddDays(29)
};
var result = await graphClient.Subscriptions["{subscription-id}"]
    .PatchAsync(subscription);
```

## 5. DELETE /subscriptions/{id} - Delete Subscription

### Description [VERIFIED]

Removes a subscription, stopping all future notifications.

### HTTP Request

```http
DELETE https://graph.microsoft.com/v1.0/subscriptions/{subscriptionId}
```

### Request Example

```http
DELETE https://graph.microsoft.com/v1.0/subscriptions/abc123-def456
Authorization: Bearer {token}
```

### Response [VERIFIED]

```http
HTTP/1.1 204 No Content
```

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.ChangeNotifications
Remove-MgSubscription -SubscriptionId $subscriptionId
```

**C#**:
```csharp
await graphClient.Subscriptions["{subscription-id}"].DeleteAsync();
```

## Notification Payload [VERIFIED]

When changes occur, Microsoft Graph sends a POST to your notificationUrl:

```json
{
  "value": [
    {
      "subscriptionId": "subscription-guid",
      "subscriptionExpirationDateTime": "2026-02-28T12:00:00Z",
      "changeType": "updated",
      "resource": "drives/drive-guid/root",
      "resourceData": {
        "@odata.type": "#microsoft.graph.driveItem",
        "@odata.id": "drives/drive-guid/items/item-guid",
        "id": "item-guid"
      },
      "clientState": "mySecretState123",
      "tenantId": "tenant-guid"
    }
  ]
}
```

### Validation Request

When creating a subscription, Graph sends a validation request:

```
POST https://webhook.contoso.com/api/notifications?validationToken=abc123
```

Your endpoint must respond with:
- Status: 200 OK
- Content-Type: text/plain
- Body: The validationToken value

## Lifecycle Notifications [VERIFIED]

Receive notifications about subscription status:

- **subscriptionRemoved** - Subscription was removed
- **reauthorizationRequired** - Token needs refresh
- **missed** - Notifications may have been missed

Configure via `lifecycleNotificationUrl` property.

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid subscription parameters
- **401 Unauthorized** - Missing or invalid token
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Subscription not found
- **409 Conflict** - Duplicate subscription
- **429 Too Many Requests** - Rate limit exceeded

### Validation Errors

- Notification URL must be HTTPS
- Notification URL must respond within 10 seconds
- Notification URL must return the validationToken

### Error Response Format

```json
{
  "error": {
    "code": "InvalidRequest",
    "message": "Subscription validation request failed. Must respond within 10 seconds.",
    "innerError": {
      "request-id": "guid",
      "date": "2026-01-28T12:00:00Z"
    }
  }
}
```

## Best Practices [VERIFIED]

**Subscription Management**:
- Renew subscriptions well before expiration (e.g., at 50% lifetime)
- Store subscription IDs for management
- Handle lifecycle notifications
- Validate clientState in received notifications

**Notification Endpoint**:
- Respond quickly (under 3 seconds ideal)
- Return 202 Accepted for async processing
- Queue notifications for processing
- Implement retry logic for failures

**Change Tracking**:
- Use delta queries to get actual changes after notification
- Notifications indicate something changed, not what changed
- Batch delta calls to reduce API calls

## Throttling Considerations [VERIFIED]

**Best Practices**:
- Don't create duplicate subscriptions
- Use lifecycle notifications to handle issues
- Implement exponential backoff for renewals

**Limits**:
- Maximum subscriptions per app per resource type
- Notification delivery attempts: 3 retries

## Sources

- **MSGRAPH-SUB-SC-01**: https://learn.microsoft.com/en-us/graph/api/resources/subscription?view=graph-rest-1.0
- **MSGRAPH-SUB-SC-02**: https://learn.microsoft.com/en-us/graph/api/subscription-post-subscriptions?view=graph-rest-1.0
- **MSGRAPH-SUB-SC-03**: https://learn.microsoft.com/en-us/graph/api/subscription-update?view=graph-rest-1.0

## Document History

**[2026-01-28 19:15]**
- Initial creation with 5 endpoints
- Added subscription resource type
- Added notification payload format
- Added lifecycle notifications
- Added best practices section
