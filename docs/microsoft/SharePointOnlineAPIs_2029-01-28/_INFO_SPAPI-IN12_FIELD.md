# INFO: SharePoint REST API - Field

**Doc ID**: SPAPI-IN01
**Goal**: Detailed reference for Field (SP.Field) endpoints with request/response JSON and examples
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_SHAREPOINT_API_TOC.md [SPAPI-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Create and manage site columns and list columns
- Define field types (text, choice, lookup, user, etc.)
- Configure field validation and formatting
- Control field visibility in forms

**Key findings**:
- FieldTypeKind enum defines field types (2=Text, 6=Choice, 7=Lookup, etc.) [VERIFIED]
- Site columns at `/_api/web/fields`, list columns at `/_api/web/lists/getbytitle()/fields` [VERIFIED]
- CreateFieldAsXml allows complex field creation via XML schema [VERIFIED]
- Use specific type metadata for type-specific properties (e.g., SP.FieldChoice for Choices) [VERIFIED]

## Quick Reference Summary

**Endpoints covered**: 10 field endpoints

- `GET /_api/web/fields` - Get all site columns
- `GET /_api/web/fields/getbyinternalnameortitle('{name}')` - Get field by name
- `GET /_api/web/fields/getbyid('{guid}')` - Get field by ID
- `POST /_api/web/fields` - Create field (simple)
- `POST /_api/web/fields/addfield` - Create field (with parameters)
- `POST /_api/web/fields/createfieldasxml` - Create field from XML schema
- `PATCH /_api/web/fields('{guid}')` - Update field
- `DELETE /_api/web/fields('{guid}')` - Delete field
- `POST .../fields('{guid}')/setshowindisplayform` - Control display form visibility
- `POST .../fields/adddependentlookupfield` - Add dependent lookup

**Permissions required**:
- Application: `Sites.Read.All` (read), `Sites.Manage.All` (manage fields)
- Delegated: `Sites.Read.All` (read), `Sites.Manage.All` (manage)

## FieldTypeKind Enumeration [VERIFIED]

- **0** - Invalid
- **1** - Integer
- **2** - Text (single line)
- **3** - Note (multi-line text)
- **4** - DateTime
- **5** - Counter (auto-increment ID)
- **6** - Choice
- **7** - Lookup
- **8** - Boolean (Yes/No)
- **9** - Number
- **10** - Currency
- **11** - URL
- **12** - Computed
- **15** - MultiChoice
- **17** - Calculated
- **20** - User

## SP.Field Resource Type

### Core Properties [VERIFIED]

- **Id** (`Edm.Guid`) - Field GUID
- **InternalName** (`Edm.String`) - Internal field name (immutable after creation)
- **Title** (`Edm.String`) - Display name
- **StaticName** (`Edm.String`) - Customizable identifier
- **Description** (`Edm.String`) - Field description
- **FieldTypeKind** (`Edm.Int32`) - Field type enumeration
- **TypeAsString** (`Edm.String`) - Field type as string
- **Group** (`Edm.String`) - Field group for organization
- **Required** (`Edm.Boolean`) - Is field required
- **DefaultValue** (`Edm.String`) - Default value
- **Hidden** (`Edm.Boolean`) - Hidden from UI
- **ReadOnlyField** (`Edm.Boolean`) - Read-only
- **Sealed** (`Edm.Boolean`) - Cannot be modified
- **CanBeDeleted** (`Edm.Boolean`) - Can be deleted
- **Indexed** (`Edm.Boolean`) - Is indexed
- **EnforceUniqueValues** (`Edm.Boolean`) - Require unique values
- **Sortable** (`Edm.Boolean`) - Can be sorted
- **Filterable** (`Edm.Boolean`) - Can be filtered
- **ValidationFormula** (`Edm.String`) - Validation formula
- **ValidationMessage** (`Edm.String`) - Validation error message
- **SchemaXml** (`Edm.String`) - XML schema definition

## 1. GET /_api/web/fields - Get All Site Columns

### Description [VERIFIED]

Returns all site columns defined at the web level.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/fields
```

### Query Parameters

- **$filter** - Filter fields (e.g., `Group eq 'Custom Columns'`)
- **$select** - Properties to return
- **$orderby** - Sort order

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/web/fields?$filter=Group eq 'Custom Columns'
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "results": [
      {
        "__metadata": {
          "type": "SP.FieldText"
        },
        "Id": "1d22ea11-1e32-424e-89ab-9fedbadb6ce1",
        "InternalName": "ProjectCode",
        "Title": "Project Code",
        "FieldTypeKind": 2,
        "TypeAsString": "Text",
        "Group": "Custom Columns",
        "Required": false,
        "Hidden": false
      }
    ]
  }
}
```

## 2. GET List Fields

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/lists/getbytitle('{list}')/fields
```

## 3. GET /_api/web/fields/getbyinternalnameortitle('{name}') - Get Field by Name

### Description [VERIFIED]

Returns a field by its internal name or display title.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/fields/getbyinternalnameortitle('{name}')
```

### Request Example

```http
GET https://contoso.sharepoint.com/sites/TeamSite/_api/web/fields/getbyinternalnameortitle('Title')
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

## 4. GET /_api/web/fields/getbyid('{guid}') - Get Field by ID

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/{site}/_api/web/fields/getbyid('{field_guid}')
```

## 5. POST /_api/web/fields - Create Field (Simple)

### Description [VERIFIED]

Creates a new field using direct POST with field properties.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/fields
```

### Request Body - Text Field

```json
{
  "__metadata": {
    "type": "SP.Field"
  },
  "Title": "Project Code",
  "FieldTypeKind": 2,
  "Required": false,
  "Description": "Unique project identifier"
}
```

### Request Body - Choice Field

```json
{
  "__metadata": {
    "type": "SP.FieldChoice"
  },
  "Title": "Priority",
  "FieldTypeKind": 6,
  "Required": true,
  "Choices": {
    "__metadata": {
      "type": "Collection(Edm.String)"
    },
    "results": ["High", "Medium", "Low"]
  },
  "EditFormat": 1
}
```

**EditFormat values**: 0=Dropdown, 1=RadioButtons

## 6. POST /_api/web/fields/addfield - Create Field (Parameters)

### Description [VERIFIED]

Creates a field using SP.FieldCreationInformation.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/fields/addfield
```

### Request Body

```json
{
  "parameters": {
    "__metadata": {
      "type": "SP.FieldCreationInformation"
    },
    "Title": "Impact",
    "FieldTypeKind": 6,
    "Required": true,
    "Choices": {
      "__metadata": {
        "type": "Collection(Edm.String)"
      },
      "results": ["High", "Medium", "Low"]
    }
  }
}
```

## 7. POST /_api/web/fields/createfieldasxml - Create Field from XML

### Description [VERIFIED]

Creates a field from XML schema definition. Most flexible method for complex fields.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/fields/createfieldasxml
```

### Request Body - User Field

```json
{
  "parameters": {
    "__metadata": {
      "type": "SP.XmlSchemaFieldCreationInformation"
    },
    "SchemaXml": "<Field Type=\"UserMulti\" Title=\"Stakeholders\" DisplayName=\"Stakeholders\" Required=\"FALSE\" UserSelectionMode=\"PeopleAndGroups\" UserSelectionScope=\"0\" Mult=\"TRUE\" />"
  }
}
```

### Request Body - Lookup Field

```json
{
  "parameters": {
    "__metadata": {
      "type": "SP.XmlSchemaFieldCreationInformation"
    },
    "SchemaXml": "<Field Type=\"Lookup\" DisplayName=\"Related Project\" Required=\"FALSE\" List=\"{list-guid}\" ShowField=\"Title\" />"
  }
}
```

## 8. PATCH /_api/web/fields('{guid}') - Update Field

### Description [VERIFIED]

Updates field properties. Use specific type for type-specific properties.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/fields('{field_guid}')
X-HTTP-Method: MERGE
IF-MATCH: *
```

### Request Body - General Properties

```json
{
  "__metadata": {
    "type": "SP.Field"
  },
  "Title": "Updated Title",
  "Description": "Updated description"
}
```

### Request Body - Type-Specific Properties

```json
{
  "__metadata": {
    "type": "SP.FieldMultiLineText"
  },
  "Title": "Comments",
  "NumberOfLines": 6
}
```

**Note**: To change inherited properties, use parent type. To change type-specific properties, must specify exact type.

## 9. DELETE /_api/web/fields('{guid}') - Delete Field

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/fields('{field_guid}')
X-HTTP-Method: DELETE
IF-MATCH: *
```

**Note**: Cannot delete sealed fields or fields in use by content types.

## 10. POST .../setshowindisplayform - Control Form Visibility

### Description [VERIFIED]

Controls whether field appears in display, edit, or new forms.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/fields('{field_guid}')/setshowindisplayform(false)
POST https://{tenant}.sharepoint.com/{site}/_api/web/fields('{field_guid}')/setshowineditform(false)
POST https://{tenant}.sharepoint.com/{site}/_api/web/fields('{field_guid}')/setshowinnewform(false)
```

## 11. POST .../adddependentlookupfield - Add Dependent Lookup

### Description [VERIFIED]

Adds a secondary lookup field that depends on a primary lookup field.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/{site}/_api/web/lists('{list}')/fields/adddependentlookupfield(displayname='{title}',primarylookupfieldid='{guid}',showfield='{fieldname}')
```

## Field Type-Specific Properties

### SP.FieldText [VERIFIED]

- **MaxLength** (`Edm.Int32`) - Max characters (default 255)

### SP.FieldMultiLineText [VERIFIED]

- **NumberOfLines** (`Edm.Int32`) - Display lines
- **RichText** (`Edm.Boolean`) - Enable rich text
- **AppendOnly** (`Edm.Boolean`) - Append-only mode

### SP.FieldChoice / SP.FieldMultiChoice [VERIFIED]

- **Choices** (`Collection(Edm.String)`) - Available choices
- **EditFormat** (`Edm.Int32`) - 0=Dropdown, 1=RadioButtons
- **FillInChoice** (`Edm.Boolean`) - Allow custom values

### SP.FieldLookup [VERIFIED]

- **LookupList** (`Edm.String`) - Source list GUID
- **LookupField** (`Edm.String`) - Source field name
- **LookupWebId** (`Edm.Guid`) - Source web ID
- **AllowMultipleValues** (`Edm.Boolean`) - Multi-select
- **RelationshipDeleteBehavior** (`Edm.Int32`) - 0=None, 1=Cascade, 2=Restrict

### SP.FieldUser [VERIFIED]

- **SelectionMode** (`Edm.Int32`) - 0=PeopleOnly, 1=PeopleAndGroups
- **SelectionGroup** (`Edm.Int32`) - Restrict to group ID
- **AllowDisplay** (`Edm.Boolean`) - Show user name
- **Presence** (`Edm.Boolean`) - Show presence indicator

### SP.FieldNumber / SP.FieldCurrency [VERIFIED]

- **MinimumValue** (`Edm.Double`) - Minimum value
- **MaximumValue** (`Edm.Double`) - Maximum value
- **CurrencyLocaleId** (`Edm.Int32`) - Currency locale (FieldCurrency only)

### SP.FieldDateTime [VERIFIED]

- **DateTimeCalendarType** (`Edm.Int32`) - Calendar type
- **DisplayFormat** (`Edm.Int32`) - 0=DateOnly, 1=DateTime
- **FriendlyDisplayFormat** (`Edm.Int32`) - 0=Unspecified, 1=Disabled, 2=Relative

### SP.FieldCalculated [VERIFIED]

- **Formula** (`Edm.String`) - Calculation formula
- **OutputType** (`Edm.Int32`) - Result type

## Error Responses

- **400** - Invalid field type or properties
- **403** - Insufficient permissions
- **404** - Field not found
- **409** - Field name already exists

## SDK Examples

**PnP PowerShell**:
```powershell
Connect-PnPOnline -Url "https://contoso.sharepoint.com/sites/TeamSite" -Interactive
Get-PnPField
Get-PnPField -List "Documents"
Add-PnPField -DisplayName "Project Code" -InternalName "ProjectCode" -Type Text
Add-PnPFieldFromXml -FieldXml '<Field Type="Choice" DisplayName="Priority"><CHOICES><CHOICE>High</CHOICE><CHOICE>Low</CHOICE></CHOICES></Field>'
Set-PnPField -Identity "ProjectCode" -Values @{Description="Updated"}
Remove-PnPField -Identity "ProjectCode"
```

**PnP JavaScript** (v4.x):
```javascript
import { spfi } from "@pnp/sp";
import "@pnp/sp/fields";
const sp = spfi(...);
const fields = await sp.web.fields();
const field = await sp.web.fields.getByInternalNameOrTitle("Title")();
await sp.web.fields.addText("ProjectCode", { MaxLength: 50 });
await sp.web.fields.addChoice("Priority", { Choices: ["High", "Low"] });
```

## Sources

- **SPAPI-FIELD-SC-01**: https://learn.microsoft.com/en-us/previous-versions/office/developer/sharepoint-rest-reference/dn600182(v=office.15)

## Document History

**[2026-01-28 19:45]**
- Initial creation with 10 endpoints
- Documented field types, type-specific properties
- Added FieldTypeKind enumeration
