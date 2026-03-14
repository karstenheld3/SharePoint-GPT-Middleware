# INFO: SharePoint REST API - User

**Doc ID**: SPAPI-IN01
**Goal**: Detailed reference for User (SP.User) endpoints with request/response JSON and examples
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_SHAREPOINT_API_TOC.md [SPAPI-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Get current user information
- List all site users
- Look up users by ID, login name, or email
- Ensure user exists (resolve from external directory)
- Check user permissions

**Key findings**:
- Login name format varies by auth type (claims, Windows, SAML) [VERIFIED]
- SharePoint Online format: `i:0#.f|membership|user@domain.com` [VERIFIED]
- `ensureuser` resolves users from Azure AD and adds to site [VERIFIED]
- User IDs are site-specific, not tenant-wide [VERIFIED]

## Quick Reference Summary

**Endpoints covered**: 10 user endpoints

- `GET /_api/web/currentuser` - Get current user
- `GET /_api/web/siteusers` - Get all site users
- `GET /_api/web/getuserbyid({id})` - Get user by ID
- `GET /_api/web/siteusers(@v)?@v='{loginname}'` - Get user by login
- `POST /_api/web/ensureuser('{loginname}')` - Ensure user exists
- `GET /_api/web/doesuserhavepermissions` - Check permissions
- `GET /_api/web/getusereffectivepermissions(@user)` - Get effective permissions

**Permissions required**:
- Application: `Sites.Read.All` (read users), `Sites.ReadWrite.All` (ensure user)
- Delegated: `Sites.Read.All` (read), `Sites.ReadWrite.All` (write)
- Note: User.Read.All may be needed for Azure AD lookups

## SP.User Resource Type

### Properties [VERIFIED]

- **Id** (`Edm.Int32`) - Site-specific user ID
- **Title** (`Edm.String`) - Display name
- **LoginName** (`Edm.String`) - Claims login name
- **Email** (`Edm.String`) - Email address
- **IsSiteAdmin** (`Edm.Boolean`) - Is site collection admin
- **UserId** - (`SP.UserIdInfo`) - Contains NameId and NameIdIssuer
- **PrincipalType** (`Edm.Int32`) - 1=User, 2=DL, 4=SecGroup, 8=SPGroup
- **IsHiddenInUI** (`Edm.Boolean`) - Hidden from UI
- **IsEmailAuthenticationGuestUser** (`Edm.Boolean`) - External guest user

### Login Name Formats [VERIFIED]

- **SharePoint Online**: `i:0#.f|membership|user@domain.com`
- **Windows Claims**: `i:0#.w|domain\user`
- **SAML Claims**: `i:05:t|adfs with roles|user@domain.com`

## 1. GET /_api/web/currentuser - Get Current User

### Description [VERIFIED]

Returns the user making the request.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/currentuser
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "__metadata": {
      "type": "SP.User"
    },
    "Id": 7,
    "Title": "John Smith",
    "LoginName": "i:0#.f|membership|john.smith@contoso.com",
    "Email": "john.smith@contoso.com",
    "IsSiteAdmin": false,
    "PrincipalType": 1
  }
}
```

## 2. GET /_api/web/siteusers - Get All Site Users

### Description [VERIFIED]

Returns all users who have access to the site.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/siteusers
```

### Query Parameters

- **$filter** - Filter users (e.g., `IsSiteAdmin eq true`)
- **$select** - Properties to return
- **$top** - Limit results

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/web/siteusers?$filter=IsSiteAdmin eq true
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "results": [
      {
        "__metadata": { "type": "SP.User" },
        "Id": 7,
        "Title": "John Smith",
        "LoginName": "i:0#.f|membership|john.smith@contoso.com",
        "Email": "john.smith@contoso.com",
        "IsSiteAdmin": true
      }
    ]
  }
}
```

## 3. GET /_api/web/getuserbyid({id}) - Get User by ID

### Description [VERIFIED]

Returns a user by their site-specific ID.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/getuserbyid({user_id})
```

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/web/getuserbyid(7)
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

## 4. GET /_api/web/siteusers(@v)?@v='{loginname}' - Get User by Login

### Description [VERIFIED]

Returns a user by their login name. Login name must be URL encoded.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/siteusers(@v)?@v='{encoded_login_name}'
```

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/web/siteusers(@v)?@v='i%3A0%23.f%7Cmembership%7Cjohn.smith%40contoso.com'
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

## 5. POST /_api/web/ensureuser('{loginname}') - Ensure User

### Description [VERIFIED]

Resolves a user from Azure AD and adds them to the site if not present. Returns existing user if already added.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/ensureuser('{login_or_email}')
```

### Request Example

```http
POST https://contoso.sharepoint.com/sites/TeamSite/_api/web/ensureuser('john.smith@contoso.com')
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
X-RequestDigest: 0x1234...
```

### Response JSON [VERIFIED]

Returns the SP.User object with their site-specific ID.

## 6. GET /_api/web/siteusers/getbyemail('{email}') - Get User by Email

### Description [VERIFIED]

Returns a user by their email address.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/siteusers/getbyemail('{email}')
```

## 7. GET /_api/web/doesuserhavepermissions - Check Permissions

### Description [VERIFIED]

Checks if current user has specific permissions.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/doesuserhavepermissions(@v)?@v={'High':'value','Low':'value'}
```

### Permission Values (SP.BasePermissions)

Common permission combinations:
- **View**: High=0, Low=1
- **Add Items**: High=0, Low=2
- **Edit Items**: High=0, Low=4
- **Delete Items**: High=0, Low=8
- **Full Control**: High=2147483647, Low=4294967295

## 8. GET /_api/web/getusereffectivepermissions(@user) - Effective Permissions

### Description [VERIFIED]

Gets the effective permissions for a specific user.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/getusereffectivepermissions(@user)?@user='{login_name}'
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "GetUserEffectivePermissions": {
      "__metadata": { "type": "SP.BasePermissions" },
      "High": "2147483647",
      "Low": "4294967295"
    }
  }
}
```

## 9. PATCH /_api/web/siteusers({id}) - Update User

### Description [VERIFIED]

Updates user properties (limited to Title and IsSiteAdmin).

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/getuserbyid({user_id})
X-HTTP-Method: MERGE
IF-MATCH: *
```

### Request Body

```json
{
  "__metadata": { "type": "SP.User" },
  "IsSiteAdmin": true
}
```

## 10. DELETE /_api/web/siteusers({id}) - Remove User

### Description [VERIFIED]

Removes a user from the site (does not delete from Azure AD).

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/siteusers/removebyid({user_id})
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid login name format
- **401 Unauthorized** - Missing or invalid token
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - User not found in site

## SDK Examples

**PnP PowerShell**:
```powershell
Connect-PnPOnline -Url "https://contoso.sharepoint.com/sites/TeamSite" -Interactive
Get-PnPUser
Get-PnPUser -Identity 7
Get-PnPUser -WithRightsAssigned
New-PnPUser -LoginName "john.smith@contoso.com"
```

## Sources

- **SPAPI-USER-SC-01**: https://learn.microsoft.com/en-us/previous-versions/office/developer/sharepoint-rest-reference/dn531432(v=office.15)

## Document History

**[2026-01-28 19:20]**
- Initial creation with 10 endpoints
- Documented user lookups, permissions, login name formats
