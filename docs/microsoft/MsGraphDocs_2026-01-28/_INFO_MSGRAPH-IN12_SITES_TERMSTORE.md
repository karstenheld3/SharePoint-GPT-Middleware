# INFO: Microsoft Graph API - TermStore Methods

**Doc ID**: MSGRAPH-IN01
**Goal**: Detailed reference for TermStore (Managed Metadata) methods
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_MSGRAPH-IN00_TOC.md [MSGRAPH-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Create and manage enterprise taxonomies programmatically
- Build metadata-driven navigation and filtering systems
- Implement controlled vocabularies for document tagging
- Migrate term store configurations between environments
- Create hierarchical classification schemes (e.g., departments, locations)
- Enable faceted search using managed metadata columns

**Key findings**:
- Hierarchy: Store > Groups > Sets > Terms (with child terms)
- Terms support multiple labels in different languages (localization)
- Term relations enable reuse and pinning across term sets
- Groups can be global (tenant-wide) or site collection scoped
- Terms have properties (key-value pairs) for custom attributes
- Managed metadata columns link to term sets for document classification

## Quick Reference Summary

**Endpoints covered**: 10 termStore methods

**Store**:
- `GET /sites/{id}/termStore` - Get term store

**Groups**:
- `GET /sites/{id}/termStore/groups` - List groups
- `GET /sites/{id}/termStore/groups/{id}` - Get group

**Sets**:
- `GET /sites/{id}/termStore/sets` - List sets
- `GET /sites/{id}/termStore/sets/{id}` - Get set
- `POST /sites/{id}/termStore/sets` - Create set
- `PATCH /sites/{id}/termStore/sets/{id}` - Update set
- `DELETE /sites/{id}/termStore/sets/{id}` - Delete set

**Terms**:
- `GET /sites/{id}/termStore/sets/{id}/terms` - List terms
- `GET /sites/{id}/termStore/groups/{id}/sets/{id}/terms/{id}` - Get term
- `POST /sites/{id}/termStore/sets/{id}/terms` - Create term
- `PATCH /sites/{id}/termStore/groups/{id}/sets/{id}/terms/{id}` - Update term
- `DELETE /sites/{id}/termStore/groups/{id}/sets/{id}/terms/{id}` - Delete term

**Permissions required**:
- Delegated: `TermStore.Read.All` (read), `TermStore.ReadWrite.All` (write)
- Application: `TermStore.Read.All` (read), `TermStore.ReadWrite.All` (write)
- **Least privilege**: `TermStore.Read.All` for read operations

## TermStore Hierarchy [VERIFIED]

```
Store (termStore)
├── Group (termStore.group)
│   └── Set (termStore.set)
│       └── Term (termStore.term)
│           └── Child Terms (hierarchical)
```

## Store Resource Type [VERIFIED]

### JSON Schema

```json
{
  "@odata.type": "#microsoft.graph.termStore.store",
  "id": "string",
  "defaultLanguageTag": "string",
  "languageTags": ["string"]
}
```

### Properties

- **id** (`string`) - Unique identifier
- **defaultLanguageTag** (`string`) - Default language (e.g., `en-US`)
- **languageTags** (`string[]`) - Supported languages

## Group Resource Type [VERIFIED]

### JSON Schema

```json
{
  "@odata.type": "#microsoft.graph.termStore.group",
  "id": "string",
  "displayName": "string",
  "description": "string",
  "scope": "global | siteCollection | unknownFutureValue",
  "createdDateTime": "datetime",
  "parentSiteId": "string"
}
```

### Properties

- **id** (`string`) - Unique identifier
- **displayName** (`string`) - Group name
- **description** (`string`) - Group description
- **scope** (`termGroupScope`) - `global` or `siteCollection`
- **createdDateTime** (`dateTimeOffset`) - Creation time
- **parentSiteId** (`string`) - Parent site for local groups

## Set Resource Type [VERIFIED]

### JSON Schema

```json
{
  "@odata.type": "#microsoft.graph.termStore.set",
  "id": "string",
  "localizedNames": [
    {
      "name": "string",
      "languageTag": "string"
    }
  ],
  "description": "string",
  "createdDateTime": "datetime",
  "properties": [
    {
      "key": "string",
      "value": "string"
    }
  ]
}
```

### Properties

- **id** (`string`) - Unique identifier
- **localizedNames** (`localizedName[]`) - Names in multiple languages
- **description** (`string`) - Set description
- **createdDateTime** (`dateTimeOffset`) - Creation time
- **properties** (`keyValue[]`) - Custom key-value properties

### Relationships

- **terms** - Collection of term resources
- **parentGroup** - Parent group
- **children** - Child terms at root level
- **relations** - Term relations (reuse, pin)

## Term Resource Type [VERIFIED]

### JSON Schema

```json
{
  "@odata.type": "#microsoft.graph.termStore.term",
  "id": "string",
  "labels": [
    {
      "name": "string",
      "isDefault": true,
      "languageTag": "string"
    }
  ],
  "descriptions": [
    {
      "description": "string",
      "languageTag": "string"
    }
  ],
  "createdDateTime": "datetime",
  "lastModifiedDateTime": "datetime",
  "properties": [
    {
      "key": "string",
      "value": "string"
    }
  ]
}
```

### Properties

- **id** (`string`) - Unique identifier
- **labels** (`localizedLabel[]`) - Labels in multiple languages
- **descriptions** (`localizedDescription[]`) - Descriptions in multiple languages
- **createdDateTime** (`dateTimeOffset`) - Creation time
- **lastModifiedDateTime** (`dateTimeOffset`) - Last modification
- **properties** (`keyValue[]`) - Custom key-value properties

### Relationships

- **children** - Child terms
- **relations** - Relations to other terms
- **set** - Parent set

## 1. GET /sites/{id}/termStore - Get Store

### Description [VERIFIED]

Retrieves the default term store for a site.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/termStore
```

### Response JSON [VERIFIED]

```json
{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#termStore",
  "id": "store-guid",
  "defaultLanguageTag": "en-US",
  "languageTags": ["en-US", "de-DE", "fr-FR"]
}
```

## 2. GET /sites/{id}/termStore/groups - List Groups

### Description [VERIFIED]

Lists all term groups in the term store.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/termStore/groups
```

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "group-guid-1",
      "displayName": "Corporate",
      "description": "Corporate taxonomy",
      "scope": "global",
      "createdDateTime": "2025-01-01T00:00:00Z"
    },
    {
      "id": "group-guid-2",
      "displayName": "Site Collection Group",
      "scope": "siteCollection",
      "parentSiteId": "site-guid"
    }
  ]
}
```

## 3. GET /sites/{id}/termStore/sets - List Sets

### Description [VERIFIED]

Lists all term sets in the term store.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/termStore/sets
```

Or within a group:
```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/termStore/groups/{groupId}/sets
```

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "set-guid",
      "localizedNames": [
        { "name": "Departments", "languageTag": "en-US" },
        { "name": "Abteilungen", "languageTag": "de-DE" }
      ],
      "description": "List of company departments",
      "createdDateTime": "2025-01-01T00:00:00Z"
    }
  ]
}
```

## 4. POST /sites/{id}/termStore/sets - Create Set

### Description [VERIFIED]

Creates a new term set in a group.

### HTTP Request

```http
POST https://graph.microsoft.com/v1.0/sites/{siteId}/termStore/sets
```

### Request Body

```json
{
  "parentGroup": {
    "id": "group-guid"
  },
  "localizedNames": [
    {
      "name": "Projects",
      "languageTag": "en-US"
    }
  ],
  "description": "Project codes and names"
}
```

### Response JSON [VERIFIED]

Returns the created set object.

### SDK Examples

**PowerShell**:
```powershell
Import-Module Microsoft.Graph.Sites

$params = @{
    parentGroup = @{ id = "group-guid" }
    localizedNames = @(
        @{ name = "Projects"; languageTag = "en-US" }
    )
}
New-MgSiteTermStoreSet -SiteId $siteId -BodyParameter $params
```

**C#**:
```csharp
var set = new Microsoft.Graph.Models.TermStore.Set
{
    ParentGroup = new Microsoft.Graph.Models.TermStore.Group { Id = "group-guid" },
    LocalizedNames = new List<LocalizedName>
    {
        new LocalizedName { Name = "Projects", LanguageTag = "en-US" }
    }
};
var result = await graphClient.Sites["{site-id}"].TermStore.Sets.PostAsync(set);
```

## 5. GET /sites/{id}/termStore/sets/{id}/terms - List Terms

### Description [VERIFIED]

Lists all terms at the root level of a term set.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/termStore/sets/{setId}/terms
```

Or with full path:
```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/termStore/groups/{groupId}/sets/{setId}/terms
```

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "id": "term-guid-1",
      "labels": [
        { "name": "Engineering", "isDefault": true, "languageTag": "en-US" }
      ],
      "descriptions": [
        { "description": "Engineering department", "languageTag": "en-US" }
      ],
      "createdDateTime": "2025-01-01T00:00:00Z"
    },
    {
      "id": "term-guid-2",
      "labels": [
        { "name": "Marketing", "isDefault": true, "languageTag": "en-US" }
      ]
    }
  ]
}
```

## 6. POST /sites/{id}/termStore/sets/{id}/terms - Create Term

### Description [VERIFIED]

Creates a new term in a term set or as a child of another term.

### HTTP Request

At set root:
```http
POST https://graph.microsoft.com/v1.0/sites/{siteId}/termStore/sets/{setId}/terms
```

As child of term:
```http
POST https://graph.microsoft.com/v1.0/sites/{siteId}/termStore/sets/{setId}/terms/{termId}/children
```

### Request Body

```json
{
  "labels": [
    {
      "name": "Sales",
      "isDefault": true,
      "languageTag": "en-US"
    },
    {
      "name": "Vertrieb",
      "isDefault": true,
      "languageTag": "de-DE"
    }
  ],
  "descriptions": [
    {
      "description": "Sales department",
      "languageTag": "en-US"
    }
  ]
}
```

### Response JSON [VERIFIED]

Returns the created term object.

## 7. GET /sites/{id}/termStore/groups/{id}/sets/{id}/terms/{id} - Get Term

### Description [VERIFIED]

Retrieves a specific term by ID.

### HTTP Request

```http
GET https://graph.microsoft.com/v1.0/sites/{siteId}/termStore/groups/{groupId}/sets/{setId}/terms/{termId}
```

### Query Parameters

- **$expand** - Expand children, relations, set

### Response JSON [VERIFIED]

```json
{
  "id": "term-guid",
  "labels": [
    { "name": "Engineering", "isDefault": true, "languageTag": "en-US" }
  ],
  "descriptions": [
    { "description": "Engineering department", "languageTag": "en-US" }
  ],
  "createdDateTime": "2025-01-01T00:00:00Z",
  "lastModifiedDateTime": "2026-01-15T10:00:00Z",
  "properties": [
    { "key": "costCenter", "value": "CC-100" }
  ]
}
```

## 8. PATCH /sites/{id}/termStore/groups/{id}/sets/{id}/terms/{id} - Update Term

### Description [VERIFIED]

Updates an existing term's labels, descriptions, or properties.

### HTTP Request

```http
PATCH https://graph.microsoft.com/v1.0/sites/{siteId}/termStore/groups/{groupId}/sets/{setId}/terms/{termId}
```

### Request Body

```json
{
  "labels": [
    {
      "name": "Software Engineering",
      "isDefault": true,
      "languageTag": "en-US"
    }
  ],
  "properties": [
    { "key": "costCenter", "value": "CC-101" }
  ]
}
```

### Response [VERIFIED]

Returns the updated term object.

## 9. DELETE /sites/{id}/termStore/groups/{id}/sets/{id}/terms/{id} - Delete Term

### Description [VERIFIED]

Deletes a term from the term store.

### HTTP Request

```http
DELETE https://graph.microsoft.com/v1.0/sites/{siteId}/termStore/groups/{groupId}/sets/{setId}/terms/{termId}
```

### Response [VERIFIED]

```http
HTTP/1.1 204 No Content
```

## 10. DELETE /sites/{id}/termStore/sets/{id} - Delete Set

### Description [VERIFIED]

Deletes a term set from the term store.

### HTTP Request

```http
DELETE https://graph.microsoft.com/v1.0/sites/{siteId}/termStore/sets/{setId}
```

### Response [VERIFIED]

```http
HTTP/1.1 204 No Content
```

## Term Relations [VERIFIED]

Terms can have relations (reuse, pin) to other terms:

### List Relations

```http
GET /sites/{siteId}/termStore/groups/{groupId}/sets/{setId}/terms/{termId}/relations
```

### Create Relation

```http
POST /sites/{siteId}/termStore/sets/{setId}/relations
```

**Request Body**:
```json
{
  "relationship": "pin | reuse",
  "fromTerm": {
    "id": "source-term-guid"
  },
  "set": {
    "id": "target-set-guid"
  }
}
```

## Error Responses

### Common Error Codes [VERIFIED]

- **400 Bad Request** - Invalid term or set data
- **401 Unauthorized** - Missing or invalid token
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Store, group, set, or term not found
- **409 Conflict** - Duplicate term name
- **429 Too Many Requests** - Rate limit exceeded

## Throttling Considerations [VERIFIED]

**Best Practices**:
- Cache term IDs for frequently used terms
- Use `$expand` to reduce round trips
- Batch term operations where possible

**Resource Units**:
- List operations: ~1 resource unit
- Create/Update/Delete: ~2 resource units

## Sources

- **MSGRAPH-TS-SC-01**: https://learn.microsoft.com/en-us/graph/api/resources/termstore-store?view=graph-rest-1.0
- **MSGRAPH-TS-SC-02**: https://learn.microsoft.com/en-us/graph/api/resources/termstore-group?view=graph-rest-1.0
- **MSGRAPH-TS-SC-03**: https://learn.microsoft.com/en-us/graph/api/resources/termstore-set?view=graph-rest-1.0
- **MSGRAPH-TS-SC-04**: https://learn.microsoft.com/en-us/graph/api/resources/termstore-term?view=graph-rest-1.0

## Document History

**[2026-01-28 19:45]**
- Initial creation with 10 endpoints
- Added termStore hierarchy documentation
- Added resource types for store, group, set, term
- Added term relations documentation
