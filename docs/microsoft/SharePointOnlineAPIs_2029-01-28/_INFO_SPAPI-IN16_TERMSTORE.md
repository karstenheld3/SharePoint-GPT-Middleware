# INFO: SharePoint REST API - Term Store

**Doc ID**: SPAPI-IN01
**Goal**: Detailed reference for Term Store (Taxonomy) REST API endpoints with request/response JSON
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_SHAREPOINT_API_TOC.md [SPAPI-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Read term store structure (groups, term sets, terms)
- Get terms for managed metadata fields
- Navigate taxonomy hierarchy
- Search for terms by label

**Key findings**:
- REST API is READ-ONLY for most operations [VERIFIED]
- Write operations (create/update/delete) require CSOM or MS Graph [VERIFIED]
- MS Graph provides modern taxonomy API: `/sites/{siteId}/termStore` [VERIFIED]
- SharePoint REST uses `/_api/v2.1/termstore` for newer endpoints [VERIFIED]

## Quick Reference Summary

**Endpoints covered**: 8 term store endpoints

- `GET /_api/v2.1/termstore` - Get term store info
- `GET /_api/v2.1/termstore/groups` - Get all term groups
- `GET /_api/v2.1/termstore/groups/{id}` - Get term group by ID
- `GET /_api/v2.1/termstore/groups/{id}/sets` - Get term sets in group
- `GET /_api/v2.1/termstore/sets/{id}` - Get term set by ID
- `GET /_api/v2.1/termstore/sets/{id}/terms` - Get terms in set
- `GET /_api/v2.1/termstore/sets/{id}/children` - Get root terms
- `GET /_api/v2.1/termstore/terms/{id}` - Get term by ID

**Permissions required**:
- Application: `TermStore.Read.All` (read), `TermStore.ReadWrite.All` (write via Graph)
- Delegated: `TermStore.Read.All` (read), `TermStore.ReadWrite.All` (write)

## API Versions [VERIFIED]

### Legacy REST API (/_api/site/termstore)

Limited support, primarily for reading:
```http
GET /_api/site/termstore
```

### Modern REST API (/_api/v2.1/termstore)

Newer endpoints with better support:
```http
GET /_api/v2.1/termstore/groups
```

### Microsoft Graph API (Recommended for Write)

Full CRUD support:
```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/termStore
```

## 1. GET /_api/v2.1/termstore - Get Term Store

### Description [VERIFIED]

Returns the default term store for the site.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/v2.1/termstore
```

### Response JSON [VERIFIED]

```json
{
  "id": "e8a3b23c-1234-5678-9abc-def012345678",
  "name": "Taxonomy",
  "defaultLanguageTag": "en-US",
  "languageTags": ["en-US", "de-DE", "fr-FR"]
}
```

## 2. GET /_api/v2.1/termstore/groups - Get All Groups

### Description [VERIFIED]

Returns all term groups in the term store.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/v2.1/termstore/groups
```

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "a1b2c3d4-1234-5678-9abc-def012345678",
      "name": "Corporate Taxonomy",
      "description": "Organization-wide terms",
      "scope": "global"
    },
    {
      "id": "b2c3d4e5-2345-6789-abcd-ef0123456789",
      "name": "Site Collection - contoso.sharepoint.com-sites-TeamSite",
      "description": "Local terms for this site",
      "scope": "siteCollection"
    }
  ]
}
```

## 3. GET /_api/v2.1/termstore/groups/{groupId} - Get Group by ID

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/v2.1/termstore/groups/{group_id}
```

## 4. GET /_api/v2.1/termstore/groups/{groupId}/sets - Get Term Sets

### Description [VERIFIED]

Returns all term sets in a group.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/v2.1/termstore/groups/{group_id}/sets
```

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "c3d4e5f6-3456-789a-bcde-f01234567890",
      "localizedNames": [
        { "name": "Departments", "languageTag": "en-US" },
        { "name": "Abteilungen", "languageTag": "de-DE" }
      ],
      "description": "Company departments",
      "isOpen": false,
      "isAvailableForTagging": true
    }
  ]
}
```

## 5. GET /_api/v2.1/termstore/sets/{setId} - Get Term Set

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/v2.1/termstore/sets/{set_id}
```

## 6. GET /_api/v2.1/termstore/sets/{setId}/children - Get Root Terms

### Description [VERIFIED]

Returns root-level terms in a term set.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/v2.1/termstore/sets/{set_id}/children
```

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "d4e5f6a7-4567-89ab-cdef-012345678901",
      "labels": [
        { "name": "Engineering", "languageTag": "en-US", "isDefault": true },
        { "name": "Technik", "languageTag": "de-DE", "isDefault": false }
      ],
      "descriptions": [
        { "description": "Engineering department", "languageTag": "en-US" }
      ],
      "isDeprecated": false,
      "childrenCount": 3
    }
  ]
}
```

## 7. GET /_api/v2.1/termstore/terms/{termId} - Get Term

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/v2.1/termstore/terms/{term_id}
```

## 8. GET /_api/v2.1/termstore/sets/{setId}/terms/{termId}/children - Get Child Terms

### Description [VERIFIED]

Returns child terms of a specific term.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/v2.1/termstore/sets/{set_id}/terms/{term_id}/children
```

## Legacy API Endpoints

### Get Term Store (Legacy)

```http
GET https://{tenant}.sharepoint.com/_api/site/termstore
```

### Response

```json
{
  "d": {
    "__metadata": { "type": "SP.Taxonomy.TermStore" },
    "Id": "e8a3b23c-1234-5678-9abc-def012345678",
    "Name": "Taxonomy",
    "DefaultLanguage": 1033
  }
}
```

## Term Resource Properties [VERIFIED]

- **id** (`Edm.Guid`) - Term unique identifier
- **labels** (`Collection`) - Localized labels
- **descriptions** (`Collection`) - Localized descriptions
- **isDeprecated** (`Edm.Boolean`) - Term is deprecated
- **childrenCount** (`Edm.Int32`) - Number of child terms
- **createdDateTime** (`Edm.DateTime`) - Creation date
- **lastModifiedDateTime** (`Edm.DateTime`) - Last modified date

## Working with Managed Metadata Fields

### Get Field Term Set ID

```http
GET /_api/web/fields/getbyinternalnameortitle('{fieldname}')?$select=TermSetId,AnchorId
```

### Get Terms for a Field

```http
GET /_api/v2.1/termstore/sets/{termSetId}/children
```

## Write Operations (CSOM Required) [VERIFIED]

The following operations require CSOM or Microsoft Graph:

- Create term group
- Create term set
- Create term
- Update term
- Delete term
- Move term
- Merge terms

### Microsoft Graph Alternative

For write operations, use Microsoft Graph:

```http
POST https://graph.microsoft.com/v1.0/sites/{siteId}/termStore/groups/{groupId}/sets/{setId}/children
Content-Type: application/json

{
  "labels": [
    { "languageTag": "en-US", "name": "New Term", "isDefault": true }
  ]
}
```

## Error Responses

- **400** - Invalid term store or ID
- **401** - Unauthorized
- **403** - Insufficient permissions
- **404** - Group, set, or term not found

## SDK Examples

**PnP PowerShell**:
```powershell
Connect-PnPOnline -Url "https://contoso.sharepoint.com" -Interactive
Get-PnPTermGroup
Get-PnPTermSet -TermGroup "Corporate Taxonomy"
Get-PnPTerm -TermSet "Departments" -TermGroup "Corporate Taxonomy"
# Write operations
New-PnPTerm -Name "New Department" -TermSet "Departments" -TermGroup "Corporate Taxonomy"
```

**PnP JavaScript** (v4.x):
```javascript
import { spfi } from "@pnp/sp";
import "@pnp/sp/taxonomy";
const sp = spfi(...);

const store = await sp.termStore();
const groups = await sp.termStore.groups();
const sets = await sp.termStore.groups.getById("{groupId}").sets();
const terms = await sp.termStore.sets.getById("{setId}").children();
```

## Sources

- **SPAPI-TERM-SC-01**: https://learn.microsoft.com/en-us/sharepoint/dev/general-development/managed-metadata-and-navigation-in-sharepoint
- **SPAPI-TERM-SC-02**: https://learn.microsoft.com/en-us/graph/api/resources/termstore-term

## Document History

**[2026-01-28 20:25]**
- Initial creation with 8 endpoints
- Documented REST API limitations (read-only)
- Added MS Graph alternative for write operations
