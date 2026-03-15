# INFO: SharePoint List Column Types

**Doc ID**: SPAPI-IN01
**Goal**: Document SharePoint list column types, their Python SDK representations, and retrieval patterns
**Timeline**: Created 2026-03-06

**Used by:**
- `_V2_SPEC_CRAWLER_LISTS.md [V2CR-SP01]` for crawler list export

## Summary

- SharePoint returns typed objects (FieldUserValue, TaxonomyFieldValue, DateTime, etc.) that must be converted to strings [VERIFIED]
- Each column type has a specific Python class in `office365-rest-python-client` [VERIFIED]
- FieldUserValue requires `$expand` to get Email property - not available in `item.properties` directly [VERIFIED]
- TaxonomyFieldValue uses `Label` property, not `LookupValue` [VERIFIED]
- DateTime values from SharePoint are UTC [VERIFIED]

## Table of Contents

1. [FieldTypeKind Enumeration](#1-fieldtypekind-enumeration)
2. [Python SDK Classes](#2-python-sdk-classes)
3. [System Fields to Ignore](#3-system-fields-to-ignore)
4. [Sources](#4-sources)
5. [Document History](#5-document-history)

## 1. FieldTypeKind Enumeration

SharePoint fields are typed objects returned by the REST API. The `FieldTypeKind` enum defines the type.

### User-Editable Field Types

Field types users can create/edit in SharePoint:

- `2` - **Text** - Single line of text (max 255 chars)
- `3` - **Note** - Multi-line text (plain or rich text)
- `4` - **DateTime** - Date or date and time
- `6` - **Choice** - Single selection from predefined options
- `7` - **Lookup** - Reference to another list item
- `8` - **Boolean** - Yes/No checkbox
- `9` - **Number** - Decimal number
- `10` - **Currency** - Currency value with locale formatting
- `11` - **URL** - Hyperlink with optional description
- `15` - **MultiChoice** - Multiple selections from predefined options
- `20` - **User** - Person or group picker (single or multi)
- **Taxonomy** - Managed metadata (term picker, single or multi)

### Read-Only/Computed Fields

System-generated fields:

- `1` - **Integer** - Whole number (often system-generated)
- `5` - **Counter** - Auto-increment ID
- `12` - **Computed** - Calculated from other fields
- `17` - **Calculated** - Formula-based value

## 2. Python SDK Classes

From `office365-rest-python-client` library:

### FieldLookupValue

**Module**: `office365.sharepoint.fields.lookup_value`

**Properties:**
- `LookupId` (int) - Referenced item ID
- `LookupValue` (str) - Display value

### FieldUserValue

**Module**: `office365.sharepoint.fields.user_value`

Extends `FieldLookupValue`.

**Properties:**
- `LookupId` (int) - User ID
- `LookupValue` (str) - User login name or display name

**Note:** Email is NOT available on `FieldUserValue` directly. Must expand User object or use separate lookup. [VERIFIED]

### FieldUrlValue

**Module**: `office365.sharepoint.fields.url_value`

**Properties:**
- `Url` (str) - URI (max 255 chars)
- `Description` (str) - Description (max 255 chars)

### TaxonomyFieldValue

**Module**: `office365.sharepoint.taxonomy.field_value`

**Properties:**
- `Label` (str) - Term label (NOT `LookupValue`) [VERIFIED]
- `TermGuid` (str) - Term GUID
- `WssId` (int) - List item ID

### TaxonomyFieldValueCollection

Collection of `TaxonomyFieldValue` objects.

### User Object Properties

**Module**: `office365.sharepoint.principal.users.user.User`

**Properties:**
- `email` (str) - User email address
- `login_name` (str) - Login name (claims format: `i:0#.f|membership|user@domain.com`)
- `user_principal_name` (str) - UPN (user@domain.com)
- `title` (str) - Display name

## 3. System Fields to Ignore

System/internal fields that should not be exported:

**Underscore-prefixed fields:**
- `_ColorTag`, `_CommentCount`, `_ComplianceFlags`, `_ComplianceTag`
- `_ComplianceTagUserId`, `_ComplianceTagWrittenTime`, `_CopySource`
- `_DisplayName`, `_dlc_DocId`, `_dlc_DocIdUrl`, `_IsRecord`
- `_LikeCount`, `_ModerationStatus`, `_UIVersionString`

**Internal fields:**
- `Author`, `Editor` (use Created By, Modified By display names instead)
- `AppAuthor`, `AppEditor`, `Attachments`, `CheckoutUser`
- `ComplianceAssetId`, `ContentType`, `DocIcon`, `Edit`
- `FileSizeDisplay`, `FolderChildCount`, `ItemChildCount`
- `LinkTitle`, `LinkFilename`, `LinkFilenameNoMenu`
- `MediaServiceAutoTags`, `MediaServiceLocation`, `MediaServiceOCR`
- `ParentVersionString`, `SharedWithDetails`, `SharedWithUsers`

### Document Library Special Fields

When source is document library (not list):
- **ID**: Item ID
- **Url**: Full URL (`tenant_url` + `FileRef`)
- **ItemType**: `File` or `Folder` (from `FSObjType`: 0=File, 1=Folder)

## 4. Sources

**Primary Sources:**
- `SPAPI-IN01-SC-INPUT-EXPCSV`: `_input/ExportListItemsAsCSV.ps1` - PowerShell export script with field iteration [VERIFIED]
- `SPAPI-IN01-SC-INPUT-INCL`: `_input/_includes.ps1` - `ConvertSharePointFieldToTextOrValueType` function [VERIFIED]
- `office365-rest-python-client` library documentation

## 5. Document History

**[2026-03-14 09:35]**
- Changed: Refactored to focus on SharePoint column types and Python SDK
- Moved: Output format examples to `_V2_SPEC_CRAWLER_LISTS.md [V2CR-SP01]`
- Changed: Doc ID from V2CR-IN01 to SPAPI-IN01 (general SharePoint API info)

**[2026-03-06 12:05]**
- Fixed: Converted Markdown table in section 2.0 to list format (GLOBAL-RULES compliance)

**[2026-03-06 11:35]**
- Initial research document created
- Analyzed PowerShell scripts from `_input/` folder
- Documented all SharePoint column type conversions
