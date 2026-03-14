# INFO: SharePoint REST API - Group

**Doc ID**: SPAPI-IN01
**Goal**: Detailed reference for Group (SP.Group) endpoints with request/response JSON and examples
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_SHAREPOINT_API_TOC.md [SPAPI-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Create and manage SharePoint groups
- Add and remove users from groups
- Get group membership information
- Configure group settings (owner, permissions)

**Key findings**:
- SharePoint groups are site-specific, not tenant-wide [VERIFIED]
- Default groups: Owners, Members, Visitors [VERIFIED]
- Groups can only contain users, not other groups [VERIFIED]
- PrincipalType=8 indicates SharePoint group [VERIFIED]

## Quick Reference Summary

**Endpoints covered**: 8 group endpoints

- `GET /_api/web/sitegroups` - Get all site groups
- `GET /_api/web/sitegroups({id})` - Get group by ID
- `GET /_api/web/sitegroups/getbyname('{name}')` - Get group by name
- `POST /_api/web/sitegroups` - Create group
- `PATCH /_api/web/sitegroups({id})` - Update group
- `DELETE /_api/web/sitegroups/removebyid({id})` - Delete group
- `GET /_api/web/sitegroups({id})/users` - Get group members
- `POST /_api/web/sitegroups({id})/users` - Add user to group
- `DELETE /_api/web/sitegroups({id})/users/removebyid({userid})` - Remove user

**Permissions required**:
- Application: `Sites.Read.All` (read), `Sites.FullControl.All` (manage groups)
- Delegated: `Sites.Read.All` (read), `Sites.Manage.All` (manage groups)

## SP.Group Resource Type

### Properties [VERIFIED]

- **Id** (`Edm.Int32`) - Group ID
- **Title** (`Edm.String`) - Group display name
- **Description** (`Edm.String`) - Group description
- **LoginName** (`Edm.String`) - Login name for the group
- **OwnerTitle** (`Edm.String`) - Owner display name
- **PrincipalType** (`Edm.Int32`) - Always 8 for SP groups
- **AllowMembersEditMembership** (`Edm.Boolean`) - Members can edit membership
- **AllowRequestToJoinLeave** (`Edm.Boolean`) - Allow join/leave requests
- **AutoAcceptRequestToJoinLeave** (`Edm.Boolean`) - Auto-accept requests
- **OnlyAllowMembersViewMembership** (`Edm.Boolean`) - Members-only view

## 1. GET /_api/web/sitegroups - Get All Groups

### Description [VERIFIED]

Returns all SharePoint groups in the site.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/sitegroups
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "results": [
      {
        "__metadata": { "type": "SP.Group" },
        "Id": 5,
        "Title": "Team Site Owners",
        "Description": "Use this group to grant people full control permissions",
        "LoginName": "Team Site Owners",
        "OwnerTitle": "Team Site Owners",
        "PrincipalType": 8
      },
      {
        "__metadata": { "type": "SP.Group" },
        "Id": 6,
        "Title": "Team Site Members",
        "Description": "Use this group to grant people contribute permissions",
        "LoginName": "Team Site Members",
        "PrincipalType": 8
      },
      {
        "__metadata": { "type": "SP.Group" },
        "Id": 7,
        "Title": "Team Site Visitors",
        "Description": "Use this group to grant people read permissions",
        "LoginName": "Team Site Visitors",
        "PrincipalType": 8
      }
    ]
  }
}
```

## 2. GET /_api/web/sitegroups({id}) - Get Group by ID

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/sitegroups({group_id})
```

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/web/sitegroups(5)
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

## 3. GET /_api/web/sitegroups/getbyname('{name}') - Get Group by Name

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/sitegroups/getbyname('{group_name}')
```

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/web/sitegroups/getbyname('Team Site Owners')
```

## 4. POST /_api/web/sitegroups - Create Group

### Description [VERIFIED]

Creates a new SharePoint group.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/sitegroups
```

### Request Body

```json
{
  "__metadata": {
    "type": "SP.Group"
  },
  "Title": "New Custom Group",
  "Description": "A custom group for project team"
}
```

### Response

Returns the created SP.Group object with HTTP 201 Created.

## 5. PATCH /_api/web/sitegroups({id}) - Update Group

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/sitegroups({group_id})
X-HTTP-Method: MERGE
IF-MATCH: *
```

### Request Body

```json
{
  "__metadata": { "type": "SP.Group" },
  "Title": "Updated Group Name",
  "Description": "Updated description"
}
```

## 6. DELETE /_api/web/sitegroups/removebyid({id}) - Delete Group

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/sitegroups/removebyid({group_id})
X-RequestDigest: {form_digest}
```

## 7. GET /_api/web/sitegroups({id})/users - Get Group Members

### Description [VERIFIED]

Returns all users in a group.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/sitegroups({group_id})/users
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
        "Email": "john.smith@contoso.com"
      }
    ]
  }
}
```

## 8. POST /_api/web/sitegroups({id})/users - Add User to Group

### Description [VERIFIED]

Adds a user to a group.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/sitegroups({group_id})/users
```

### Request Body

```json
{
  "__metadata": { "type": "SP.User" },
  "LoginName": "i:0#.f|membership|john.smith@contoso.com"
}
```

## 9. POST .../users/removebyid({userid}) - Remove User from Group

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/sitegroups({group_id})/users/removebyid({user_id})
```

## Associated Groups

### Get Associated Owner Group

```http
GET /_api/web/associatedownergroup
```

### Get Associated Member Group

```http
GET /_api/web/associatedmembergroup
```

### Get Associated Visitor Group

```http
GET /_api/web/associatedvisitorgroup
```

## Error Responses

- **400** - Invalid group name
- **403** - Insufficient permissions to manage groups
- **404** - Group not found

## SDK Examples

**PnP PowerShell**:
```powershell
Connect-PnPOnline -Url "https://contoso.sharepoint.com/sites/TeamSite" -Interactive
Get-PnPGroup
Get-PnPGroup -Identity "Team Site Owners"
New-PnPGroup -Title "Custom Group"
Add-PnPGroupMember -Group "Custom Group" -LoginName "john@contoso.com"
Remove-PnPGroupMember -Group "Custom Group" -LoginName "john@contoso.com"
```

## Sources

- **SPAPI-GROUP-SC-01**: https://learn.microsoft.com/en-us/previous-versions/office/developer/sharepoint-rest-reference/dn531432(v=office.15)

## Document History

**[2026-01-28 19:25]**
- Initial creation with 8 endpoints
- Documented group CRUD and membership operations
