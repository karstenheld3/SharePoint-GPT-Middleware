# INFO: SharePoint REST API - Utility

**Doc ID**: SPAPI-IN01
**Goal**: Detailed reference for Utility REST API endpoints (contextinfo, batch, getchanges, regional settings)
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_SHAREPOINT_API_TOC.md [SPAPI-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Get form digest for write operations
- Execute multiple requests in a single batch
- Track changes to sites, lists, and items
- Get and set regional settings

**Key findings**:
- ContextInfo returns form digest required for POST/PATCH/DELETE [VERIFIED]
- Batch requests use OData $batch with multipart/mixed content type [VERIFIED]
- GetChanges uses change tokens for incremental sync [VERIFIED]
- Form digest expires after ~30 minutes [VERIFIED]

## Quick Reference Summary

**Endpoints covered**: 6 utility endpoints

- `POST /_api/contextinfo` - Get form digest and site info
- `POST /_api/$batch` - Execute batch requests
- `POST /_api/web/getchanges` - Get site changes
- `POST /_api/web/lists/getbytitle('{list}')/getchanges` - Get list changes
- `GET /_api/web/regionalsettings` - Get regional settings
- `PATCH /_api/web/regionalsettings` - Update regional settings

**Permissions required**:
- Application: `Sites.Read.All` (read), `Sites.ReadWrite.All` (write)
- Delegated: `Sites.Read.All` (read), `Sites.ReadWrite.All` (write)

## 1. POST /_api/contextinfo - Get Form Digest

### Description [VERIFIED]

Returns context information including the form digest value required for write operations.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/contextinfo
```

### Request Example

```http
POST https://contoso.sharepoint.com/sites/TeamSite/_api/contextinfo
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "GetContextWebInformation": {
      "__metadata": {
        "type": "SP.ContextWebInformation"
      },
      "FormDigestTimeoutSeconds": 1800,
      "FormDigestValue": "0x1234567890ABCDEF...,28 Jan 2026 19:00:00 -0000",
      "LibraryVersion": "16.0.24322.12000",
      "SiteFullUrl": "https://contoso.sharepoint.com/sites/TeamSite",
      "SupportedSchemaVersions": {
        "results": ["14.0.0.0", "15.0.0.0"]
      },
      "WebFullUrl": "https://contoso.sharepoint.com/sites/TeamSite"
    }
  }
}
```

### Key Properties [VERIFIED]

- **FormDigestValue** - Use in `X-RequestDigest` header for write operations
- **FormDigestTimeoutSeconds** - Digest validity (default 1800 = 30 minutes)
- **SiteFullUrl** - Site collection URL
- **WebFullUrl** - Web URL

### Usage Note

**OAuth Exception**: When using OAuth Bearer tokens, form digest is NOT required for most operations. It's primarily needed for:
- Legacy authentication
- Some specific operations (file upload, site design)

## 2. POST /_api/$batch - Batch Requests

### Description [VERIFIED]

Combines multiple REST requests into a single HTTP call.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/$batch
Content-Type: multipart/mixed; boundary=batch_{guid}
```

### Request Body Structure [VERIFIED]

```
--batch_{guid}
Content-Type: application/http
Content-Transfer-Encoding: binary

GET https://contoso.sharepoint.com/sites/TeamSite/_api/web/title HTTP/1.1
Accept: application/json;odata=verbose

--batch_{guid}
Content-Type: application/http
Content-Transfer-Encoding: binary

GET https://contoso.sharepoint.com/sites/TeamSite/_api/web/lists HTTP/1.1
Accept: application/json;odata=verbose

--batch_{guid}--
```

### Batch with Changeset (Write Operations)

```
--batch_{guid}
Content-Type: multipart/mixed; boundary=changeset_{guid2}

--changeset_{guid2}
Content-Type: application/http
Content-Transfer-Encoding: binary

POST https://contoso.sharepoint.com/_api/web/lists HTTP/1.1
Content-Type: application/json;odata=verbose
Accept: application/json;odata=verbose

{"__metadata":{"type":"SP.List"},"Title":"New List","BaseTemplate":100}

--changeset_{guid2}--
--batch_{guid}--
```

### Response Structure

```
--batchresponse_{guid}
Content-Type: application/http
Content-Transfer-Encoding: binary

HTTP/1.1 200 OK
Content-Type: application/json;odata=verbose

{"d":{"Title":"Team Site"}}

--batchresponse_{guid}
Content-Type: application/http
Content-Transfer-Encoding: binary

HTTP/1.1 200 OK
Content-Type: application/json;odata=verbose

{"d":{"results":[...]}}

--batchresponse_{guid}--
```

### Batch Limits [VERIFIED]

- Max 100 requests per batch
- Max 1000 operations in changesets
- Changesets are atomic (all succeed or all fail)

## 3. POST /_api/web/getchanges - Get Site Changes

### Description [VERIFIED]

Returns changes to the site based on a change query.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/getchanges
```

### Request Body [VERIFIED]

```json
{
  "query": {
    "__metadata": {
      "type": "SP.ChangeQuery"
    },
    "Web": true,
    "Update": true,
    "Add": true,
    "DeleteObject": true,
    "List": true,
    "Item": true,
    "File": true,
    "Folder": true,
    "User": true,
    "Group": true,
    "SecurityPolicy": true,
    "RoleDefinitionAdd": true,
    "RoleDefinitionUpdate": true,
    "RoleDefinitionDelete": true,
    "RoleAssignmentAdd": true,
    "RoleAssignmentDelete": true
  }
}
```

### With Change Token (Incremental)

```json
{
  "query": {
    "__metadata": {
      "type": "SP.ChangeQuery"
    },
    "Item": true,
    "Add": true,
    "Update": true,
    "DeleteObject": true,
    "ChangeTokenStart": {
      "__metadata": {
        "type": "SP.ChangeToken"
      },
      "StringValue": "1;3;5C77031A-9621-4DFC-BB5D-57803A94E91D;637123456789000000;123456"
    }
  }
}
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "results": [
      {
        "__metadata": {
          "type": "SP.ChangeItem"
        },
        "ChangeToken": {
          "StringValue": "1;3;5C77031A-9621-4DFC-BB5D-57803A94E91D;637123456789100000;123457"
        },
        "ChangeType": 1,
        "ItemId": 42,
        "ListId": "5C77031A-9621-4DFC-BB5D-57803A94E91D",
        "Time": "2026-01-28T20:00:00Z",
        "WebId": "dbc5a806-e4d4-46e5-951c-6344d70b62fa"
      }
    ]
  }
}
```

### ChangeType Values [VERIFIED]

- **1** - Add
- **2** - Update
- **3** - Delete
- **4** - Rename
- **5** - Move away
- **6** - Move into
- **7** - Restore
- **8** - Role add
- **9** - Role delete
- **10** - Role update
- **11** - Assignment add
- **12** - Assignment delete
- **13** - System update

## 4. POST List GetChanges

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/lists/getbytitle('{list}')/getchanges
```

### Request Body

```json
{
  "query": {
    "__metadata": {
      "type": "SP.ChangeQuery"
    },
    "Item": true,
    "Add": true,
    "Update": true,
    "DeleteObject": true
  }
}
```

## 5. GET /_api/web/regionalsettings - Get Regional Settings

### Description [VERIFIED]

Returns regional settings for the web.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/regionalsettings
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "__metadata": {
      "type": "SP.RegionalSettings"
    },
    "AdjustHijriDays": 0,
    "AlternateCalendarType": 0,
    "AM": "AM",
    "CalendarType": 1,
    "Collation": 25,
    "CollationLCID": 2070,
    "DateFormat": 0,
    "DateSeparator": "/",
    "DecimalSeparator": ".",
    "DigitGrouping": "3;0",
    "FirstDayOfWeek": 0,
    "FirstWeekOfYear": 0,
    "IsEastAsia": false,
    "IsRightToLeft": false,
    "IsUIRightToLeft": false,
    "ListSeparator": ",",
    "LocaleId": 1033,
    "NegativeSign": "-",
    "NegNumberMode": 1,
    "PM": "PM",
    "PositiveSign": "",
    "ShowWeeks": false,
    "ThousandSeparator": ",",
    "Time24": false,
    "TimeMarkerPosition": 0,
    "TimeSeparator": ":",
    "WorkDayEndHour": 1020,
    "WorkDays": 62,
    "WorkDayStartHour": 480
  }
}
```

### Get Time Zone

```http
GET /_api/web/regionalsettings/timezone
```

### Get Time Zones

```http
GET /_api/web/regionalsettings/timezones
```

## 6. PATCH /_api/web/regionalsettings - Update Regional Settings

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/regionalsettings
X-HTTP-Method: MERGE
IF-MATCH: *
```

### Request Body

```json
{
  "__metadata": {
    "type": "SP.RegionalSettings"
  },
  "LocaleId": 1031,
  "Time24": true,
  "FirstDayOfWeek": 1
}
```

## Additional Utility Endpoints

### Get Site Usage

```http
GET /_api/site/usage
```

### Get Web Templates

```http
GET /_api/web/getavailablewebtemplates(lcid=1033)
```

### Ensure User

```http
POST /_api/web/ensureuser('{loginname}')
```

### Does User Have Permissions

```http
POST /_api/web/doesuserhavepermissions(@v)?@v={'High':'value','Low':'value'}
```

## Error Responses

- **400** - Invalid request or change query
- **401** - Unauthorized
- **403** - Insufficient permissions
- **429** - Throttled (too many requests)

## SDK Examples

**PnP PowerShell**:
```powershell
Connect-PnPOnline -Url "https://contoso.sharepoint.com/sites/TeamSite" -Interactive

# Get changes
$changes = Get-PnPChangeLog -List "Documents"

# Batch via PnP Batch
$batch = New-PnPBatch
Add-PnPListItem -List "Tasks" -Values @{Title="Task 1"} -Batch $batch
Add-PnPListItem -List "Tasks" -Values @{Title="Task 2"} -Batch $batch
Invoke-PnPBatch -Batch $batch
```

**PnP JavaScript** (v4.x):
```javascript
import { spfi } from "@pnp/sp";
import "@pnp/sp/batching";
const sp = spfi(...);

// Batch requests
const [batchedSP, execute] = sp.batched();
const p1 = batchedSP.web.lists.getByTitle("Documents")();
const p2 = batchedSP.web.lists.getByTitle("Tasks")();
await execute();
const [docs, tasks] = await Promise.all([p1, p2]);

// Get changes
const changes = await sp.web.getChanges({
  Item: true,
  Add: true,
  Update: true
});
```

## Sources

- **SPAPI-UTIL-SC-01**: https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/make-batch-requests-with-the-rest-apis
- **SPAPI-UTIL-SC-02**: https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/complete-basic-operations-using-sharepoint-rest-endpoints

## Document History

**[2026-01-28 21:15]**
- Initial creation with 6 endpoints
- Documented batch request structure
- Added change query and ChangeType values
