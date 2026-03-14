# INFO: SharePoint REST API - Webhook

**Doc ID**: SPAPI-IN01
**Goal**: Detailed reference for SharePoint Webhook subscription endpoints with request/response JSON
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_SHAREPOINT_API_TOC.md [SPAPI-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Subscribe to list/library change notifications
- Build event-driven integrations
- Sync external systems with SharePoint changes
- Replace polling with push notifications

**Key findings**:
- Webhooks only supported for SharePoint lists and document libraries [VERIFIED]
- Max subscription expiration is 180 days [VERIFIED]
- Notifications are batched and asynchronous (only -ed events) [VERIFIED]
- Your endpoint must respond to validation request during creation [VERIFIED]
- Retry mechanism: 5 attempts with 5-minute intervals [VERIFIED]
- **Gotcha**: Notification does NOT include change details - you must call GetChanges to get actual data [VERIFIED]
- **Gotcha**: Must renew subscriptions before expiration or recreate from scratch [VERIFIED]
- **Gotcha**: Cannot subscribe to sites, webs, or folders - lists/libraries only [VERIFIED]

## Quick Reference Summary

**Endpoints covered**: 5 webhook endpoints

- `GET /_api/web/lists('{id}')/subscriptions` - Get all subscriptions
- `GET /_api/web/lists('{id}')/subscriptions('{subId}')` - Get subscription by ID
- `POST /_api/web/lists('{id}')/subscriptions` - Create subscription
- `PATCH /_api/web/lists('{id}')/subscriptions('{subId}')` - Update subscription
- `DELETE /_api/web/lists('{id}')/subscriptions('{subId}')` - Delete subscription

**Permissions required**:
- Application: `Sites.Manage.All` (manage subscriptions)
- Delegated: `Sites.Manage.All`
- Note: Your notification endpoint must be HTTPS

## Webhook Limitations [VERIFIED]

- **Supported resources**: Lists and document libraries only
- **Max expiration**: 180 days
- **Events**: Asynchronous only (item added, changed, deleted)
- **No synchronous events**: Cannot cancel/modify operations
- **Notification URL**: Must be HTTPS
- **Batching**: Multiple notifications may be batched in single request

## Subscription Resource Type [VERIFIED]

### Properties

- **id** (`Edm.Guid`) - Subscription ID
- **resource** (`Edm.String`) - Resource URL being monitored
- **notificationUrl** (`Edm.String`) - Your endpoint URL
- **expirationDateTime** (`Edm.DateTime`) - Expiration date/time
- **clientState** (`Edm.String`) - Optional client state for validation

## 1. GET /subscriptions - Get All Subscriptions

### Description [VERIFIED]

Returns all webhook subscriptions for a list.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/lists('{list_id}')/subscriptions
```

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/web/lists('5C77031A-9621-4DFC-BB5D-57803A94E91D')/subscriptions
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=nometadata
```

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "a]a]ec1b-a]ec7c9-4cf9-85b7-a]ec1ba]ec1b",
      "resource": "https://contoso.sharepoint.com/_api/web/lists('5C77031A-9621-4DFC-BB5D-57803A94E91D')",
      "notificationUrl": "https://myapp.azurewebsites.net/api/webhook",
      "expirationDateTime": "2026-07-27T00:00:00.000Z",
      "clientState": "MySecretState123"
    }
  ]
}
```

## 2. GET /subscriptions('{id}') - Get Subscription by ID

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/lists('{list_id}')/subscriptions('{subscription_id}')
```

## 3. POST /subscriptions - Create Subscription

### Description [VERIFIED]

Creates a new webhook subscription. SharePoint validates your notification URL during creation.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/lists('{list_id}')/subscriptions
```

### Request Body [VERIFIED]

```json
{
  "resource": "https://contoso.sharepoint.com/_api/web/lists('5C77031A-9621-4DFC-BB5D-57803A94E91D')",
  "notificationUrl": "https://myapp.azurewebsites.net/api/webhook",
  "expirationDateTime": "2026-07-27T00:00:00.000Z",
  "clientState": "MySecretState123"
}
```

### Request Example

```http
POST https://contoso.sharepoint.com/sites/TeamSite/_api/web/lists('5C77031A-9621-4DFC-BB5D-57803A94E91D')/subscriptions
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=nometadata
Content-Type: application/json
X-RequestDigest: 0x1234...

{
  "resource": "https://contoso.sharepoint.com/sites/TeamSite/_api/web/lists('5C77031A-9621-4DFC-BB5D-57803A94E91D')",
  "notificationUrl": "https://myapp.azurewebsites.net/api/webhook",
  "expirationDateTime": "2026-07-27T00:00:00.000Z",
  "clientState": "MySecretState123"
}
```

### Response (201 Created)

```json
{
  "id": "a1ec1b7c-a1ec-4cf9-85b7-a1ec1ba1ec1b",
  "resource": "https://contoso.sharepoint.com/sites/TeamSite/_api/web/lists('5C77031A-9621-4DFC-BB5D-57803A94E91D')",
  "notificationUrl": "https://myapp.azurewebsites.net/api/webhook",
  "expirationDateTime": "2026-07-27T00:00:00.000Z",
  "clientState": "MySecretState123"
}
```

## Validation Request [VERIFIED]

During subscription creation, SharePoint sends a validation request to your endpoint:

### Validation Request from SharePoint

```http
POST https://myapp.azurewebsites.net/api/webhook?validationtoken={token}
```

### Required Response

Your endpoint must respond within 5 seconds with:
- HTTP 200 OK
- Content-Type: text/plain
- Body: The validation token (exactly as received)

```http
HTTP/1.1 200 OK
Content-Type: text/plain

{validationtoken_value}
```

## 4. PATCH /subscriptions('{id}') - Update Subscription

### Description [VERIFIED]

Updates subscription expiration date.

### HTTP Request

```http
PATCH https://{tenant}.sharepoint.com/{site}/_api/web/lists('{list_id}')/subscriptions('{subscription_id}')
```

### Request Body

```json
{
  "expirationDateTime": "2026-12-31T00:00:00.000Z"
}
```

## 5. DELETE /subscriptions('{id}') - Delete Subscription

### HTTP Request

```http
DELETE https://{tenant}.sharepoint.com/{site}/_api/web/lists('{list_id}')/subscriptions('{subscription_id}')
```

### Response

HTTP 204 No Content

## Notification Payload [VERIFIED]

When changes occur, SharePoint sends notifications to your endpoint:

### Notification Request from SharePoint

```http
POST https://myapp.azurewebsites.net/api/webhook
Content-Type: application/json

{
  "value": [
    {
      "subscriptionId": "a1ec1b7c-a1ec-4cf9-85b7-a1ec1ba1ec1b",
      "clientState": "MySecretState123",
      "expirationDateTime": "2026-07-27T00:00:00.000Z",
      "resource": "5C77031A-9621-4DFC-BB5D-57803A94E91D",
      "tenantId": "contoso.onmicrosoft.com",
      "siteUrl": "/sites/TeamSite",
      "webId": "dbc5a806-e4d4-46e5-951c-6344d70b62fa"
    }
  ]
}
```

**Note**: The notification does NOT include change details. You must call GetChanges() API to get actual changes.

### Required Response

Your endpoint must respond within 5 seconds with HTTP 200 OK.

## Processing Changes with GetChanges [VERIFIED]

After receiving notification, call GetChanges to get actual changes:

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/lists('{list_id}')/getchanges
Content-Type: application/json

{
  "query": {
    "__metadata": { "type": "SP.ChangeQuery" },
    "Item": true,
    "Add": true,
    "Update": true,
    "DeleteObject": true
  }
}
```

### Using Change Token

Store and use change tokens for incremental changes:

```json
{
  "query": {
    "__metadata": { "type": "SP.ChangeQuery" },
    "Item": true,
    "Add": true,
    "Update": true,
    "DeleteObject": true,
    "ChangeTokenStart": {
      "__metadata": { "type": "SP.ChangeToken" },
      "StringValue": "1;3;5C77031A-9621-4DFC-BB5D-57803A94E91D;637123456789000000;123456"
    }
  }
}
```

## Error Handling [VERIFIED]

### Subscription Creation Errors

- **400** - Invalid request (bad URL, expired date)
- **401** - Unauthorized
- **403** - Insufficient permissions
- **404** - List not found
- **422** - Validation failed (endpoint didn't respond correctly)

### Notification Delivery

- Retries 5 times with 5-minute intervals
- Notifications dropped after 5 failed attempts
- Future notifications still attempted

## Best Practices

1. **Validate clientState** - Verify notifications match your subscription
2. **Respond quickly** - Return HTTP 200 within 5 seconds
3. **Process asynchronously** - Queue notifications, process separately
4. **Renew before expiration** - Update subscription before 180 days
5. **Use change tokens** - Track incremental changes efficiently
6. **Handle batched notifications** - Multiple changes may arrive together

## SDK Examples

**PnP PowerShell**:
```powershell
Connect-PnPOnline -Url "https://contoso.sharepoint.com/sites/TeamSite" -Interactive
Get-PnPWebhookSubscriptions -List "Documents"
Add-PnPWebhookSubscription -List "Documents" -NotificationUrl "https://myapp.azurewebsites.net/api/webhook"
Set-PnPWebhookSubscription -List "Documents" -Subscription $subId -ExpirationDate (Get-Date).AddDays(180)
Remove-PnPWebhookSubscription -List "Documents" -Subscription $subId
```

**PnP JavaScript** (v4.x):
```javascript
import { spfi } from "@pnp/sp";
import "@pnp/sp/subscriptions";
const sp = spfi(...);

const subs = await sp.web.lists.getByTitle("Documents").subscriptions();
const newSub = await sp.web.lists.getByTitle("Documents").subscriptions.add(
  "https://myapp.azurewebsites.net/api/webhook",
  "2026-07-27T00:00:00.000Z",
  "MyClientState"
);
```

## Sources

- **SPAPI-WEBHOOK-SC-01**: https://learn.microsoft.com/en-us/sharepoint/dev/apis/webhooks/overview-sharepoint-webhooks
- **SPAPI-WEBHOOK-SC-02**: https://learn.microsoft.com/en-us/sharepoint/dev/apis/webhooks/lists/create-subscription

## Document History

**[2026-01-28 19:45]**
- Added critical gotchas (GetChanges requirement, renewal, scope limitations)

**[2026-01-28 20:05]**
- Initial creation with 5 endpoints
- Documented subscription lifecycle and validation flowpayload
- Added GetChanges integration pattern
