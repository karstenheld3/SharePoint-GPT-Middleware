# INFO: SharePoint REST API - Role Assignment

**Doc ID**: SPAPI-IN01
**Goal**: Detailed reference for RoleAssignment and RoleDefinition endpoints with request/response JSON and examples
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_SHAREPOINT_API_TOC.md [SPAPI-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Manage permissions on sites, lists, and items
- Break and reset permission inheritance
- Assign roles to users and groups
- Create custom permission levels

**Key findings**:
- RoleAssignment links a principal (user/group) to RoleDefinitions [VERIFIED]
- Objects inherit permissions by default; break inheritance to customize [VERIFIED]
- RoleDefinition defines permission levels (Read, Contribute, Full Control) [VERIFIED]
- PrincipalId in RoleAssignment refers to user or group ID [VERIFIED]

## Quick Reference Summary

**Endpoints covered**: 10 role assignment endpoints

- `GET /_api/web/roleassignments` - Get all role assignments
- `GET /_api/web/roledefinitions` - Get all role definitions
- `GET /_api/web/roledefinitions/getbyname('{name}')` - Get role by name
- `POST /_api/web/roleassignments/addroleassignment` - Add role assignment
- `POST /_api/web/roleassignments/removeroleassignment` - Remove role assignment
- `POST /_api/web/breakroleinheritance` - Break inheritance
- `POST /_api/web/resetroleinheritance` - Reset inheritance

**Permissions required**:
- Application: `Sites.FullControl.All` (manage permissions)
- Delegated: `Sites.Manage.All` or `Sites.FullControl.All`

## Role Definitions (Permission Levels)

### Default Role Definitions [VERIFIED]

- **Full Control** (1073741829) - Has full control
- **Design** (1073741828) - Can view, add, update, delete, approve, and customize
- **Edit** (1073741830) - Can add, edit and delete lists
- **Contribute** (1073741827) - Can view, add, update, and delete list items
- **Read** (1073741826) - Can view pages and list items
- **Limited Access** (1073741825) - Can view specific lists, libraries, items
- **View Only** (1073741924) - Can view pages, list items, and documents

## SP.RoleAssignment Resource Type

### Properties [VERIFIED]

- **PrincipalId** (`Edm.Int32`) - User or group ID
- **Member** (`SP.Principal`) - The user or group (expandable)
- **RoleDefinitionBindings** (`Collection(SP.RoleDefinition)`) - Assigned roles

## SP.RoleDefinition Resource Type

### Properties [VERIFIED]

- **Id** (`Edm.Int32`) - Role definition ID
- **Name** (`Edm.String`) - Role name
- **Description** (`Edm.String`) - Role description
- **BasePermissions** (`SP.BasePermissions`) - Permission flags
- **RoleTypeKind** (`Edm.Int32`) - Role type (0=None, 1=Guest, 2=Reader, etc.)

## 1. GET /_api/web/roleassignments - Get Role Assignments

### Description [VERIFIED]

Returns all role assignments for the web.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/roleassignments
```

### Query Parameters

- **$expand** - Expand `Member` and `RoleDefinitionBindings`

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/web/roleassignments?$expand=Member,RoleDefinitionBindings
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "results": [
      {
        "__metadata": { "type": "SP.RoleAssignment" },
        "PrincipalId": 5,
        "Member": {
          "__metadata": { "type": "SP.Group" },
          "Id": 5,
          "Title": "Team Site Owners",
          "PrincipalType": 8
        },
        "RoleDefinitionBindings": {
          "results": [
            {
              "__metadata": { "type": "SP.RoleDefinition" },
              "Id": 1073741829,
              "Name": "Full Control"
            }
          ]
        }
      }
    ]
  }
}
```

## 2. GET /_api/web/roledefinitions - Get Role Definitions

### Description [VERIFIED]

Returns all permission levels defined in the site.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/roledefinitions
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "results": [
      {
        "__metadata": { "type": "SP.RoleDefinition" },
        "Id": 1073741829,
        "Name": "Full Control",
        "Description": "Has full control.",
        "RoleTypeKind": 5
      },
      {
        "__metadata": { "type": "SP.RoleDefinition" },
        "Id": 1073741827,
        "Name": "Contribute",
        "Description": "Can view, add, update, and delete list items and documents.",
        "RoleTypeKind": 3
      }
    ]
  }
}
```

## 3. GET /_api/web/roledefinitions/getbyname('{name}') - Get Role by Name

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/roledefinitions/getbyname('Contribute')
```

## 4. POST /_api/web/roleassignments/addroleassignment - Add Role Assignment

### Description [VERIFIED]

Assigns a role to a user or group.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/roleassignments/addroleassignment(principalid={principal_id},roledefid={role_def_id})
```

### Parameters

- **principalid** - User or group ID
- **roledefid** - Role definition ID

### Request Example

```http
POST https://contoso.sharepoint.com/sites/TeamSite/_api/web/roleassignments/addroleassignment(principalid=7,roledefid=1073741827)
Authorization: Bearer eyJ0eXAi...
X-RequestDigest: 0x1234...
```

## 5. POST /_api/web/roleassignments/removeroleassignment - Remove Role Assignment

### Description [VERIFIED]

Removes a role assignment from a user or group.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/roleassignments/removeroleassignment(principalid={principal_id},roledefid={role_def_id})
```

## 6. POST /_api/web/breakroleinheritance - Break Inheritance

### Description [VERIFIED]

Breaks permission inheritance from parent. Required before adding unique permissions.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/breakroleinheritance(copyRoleAssignments=true,clearSubscopes=false)
```

### Parameters

- **copyRoleAssignments** - true to copy existing permissions
- **clearSubscopes** - true to clear unique permissions on child objects

## 7. POST /_api/web/resetroleinheritance - Reset Inheritance

### Description [VERIFIED]

Resets permission inheritance from parent, removing unique permissions.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/resetroleinheritance
```

## 8. List-Level Role Assignments

### Get List Permissions

```http
GET /_api/web/lists/getbytitle('{list}')/roleassignments?$expand=Member,RoleDefinitionBindings
```

### Break List Inheritance

```http
POST /_api/web/lists/getbytitle('{list}')/breakroleinheritance(copyRoleAssignments=true,clearSubscopes=false)
```

### Add Role to List

```http
POST /_api/web/lists/getbytitle('{list}')/roleassignments/addroleassignment(principalid={id},roledefid={id})
```

## 9. Item-Level Role Assignments

### Get Item Permissions

```http
GET /_api/web/lists/getbytitle('{list}')/items({id})/roleassignments?$expand=Member,RoleDefinitionBindings
```

### Break Item Inheritance

```http
POST /_api/web/lists/getbytitle('{list}')/items({id})/breakroleinheritance(copyRoleAssignments=true,clearSubscopes=false)
```

## 10. POST /_api/web/roledefinitions - Create Custom Role

### Description [VERIFIED]

Creates a custom permission level.

### Request Body

```json
{
  "__metadata": { "type": "SP.RoleDefinition" },
  "Name": "Custom Contributor",
  "Description": "Can add and edit but not delete",
  "BasePermissions": {
    "__metadata": { "type": "SP.BasePermissions" },
    "High": "0",
    "Low": "1011028719"
  }
}
```

## Error Responses

- **400** - Invalid principal or role ID
- **403** - Insufficient permissions
- **404** - Principal or role not found

## SDK Examples

**Office365-REST-Python-Client** (Python):

```python
# Library: office365-rest-python-client
# pip install Office365-REST-Python-Client
from office365.sharepoint.client_context import ClientContext

# Get items with HasUniqueRoleAssignments flag
items = library.items.get().select(["ID", "FileRef", "HasUniqueRoleAssignments"]).top(5000).execute_query()
broken = [item for item in items if item.properties.get('HasUniqueRoleAssignments') == True]

# Get RoleAssignments with expanded Member (WORKS with execute_batch)
for item in broken:
    ra = item.role_assignments.get().expand(["Member"])
ctx.execute_batch()  # 3.4x faster than sequential execute_query()

# Access role assignment details
for item in broken:
    for ra in item.role_assignments:
        principal_id = ra.properties.get('PrincipalId')
        member = ra.member
        print(f"Principal: {member.properties.get('Title')} (ID: {principal_id})")
```

**Performance metrics** (tested 2026-02-03):
- `execute_batch()` for RoleAssignments: **3.4x speedup** vs sequential (0.8s vs 2.7s for 10 items)
- `$expand=Member` works correctly in batch operations
- `HasUniqueRoleAssignments` is accessible via `$select` [TESTED]

**PnP PowerShell**:
```powershell
Connect-PnPOnline -Url "https://contoso.sharepoint.com/sites/TeamSite" -Interactive
Get-PnPSiteCollectionAdmin
Set-PnPWebPermission -User "john@contoso.com" -AddRole "Contribute"
Set-PnPListPermission -Identity "Documents" -User "john@contoso.com" -AddRole "Read"
```

## Sources

- **SPAPI-ROLE-SC-01**: https://learn.microsoft.com/en-us/previous-versions/office/developer/sharepoint-rest-reference/dn531432(v=office.15)
- **SPAPI-ROLE-SC-02**: https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/set-custom-permissions-on-a-list-by-using-the-rest-interface

## Document History

**[2026-02-03 14:25]**
- Added: Office365-REST-Python-Client SDK examples for RoleAssignments
- Added: Performance metrics (3.4x batch speedup)
- Added: HasUniqueRoleAssignments tested pattern

**[2026-01-28 19:30]**
- Initial creation with 10 endpoints
- Documented role assignments, definitions, and inheritance
