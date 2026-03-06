# INFO: SharePoint List Column Type Conversions

**Doc ID**: V2CR-IN01
**Goal**: Document how SharePoint list column types are converted to human-readable text values for CSV and Markdown export
**Timeline**: Created 2026-03-06

## Summary

- SharePoint returns typed objects (FieldUserValue, TaxonomyFieldValue, DateTime, etc.) that must be converted to strings [VERIFIED]
- Each column type has a specific conversion pattern for human-readable output [VERIFIED]
- Multi-value fields use pipe `|` as separator, multi-user fields use semicolon `;` [VERIFIED]
- DateTime values should use RFC3339-like format `YYYY-MM-DD HH:mm:ss` for Excel compatibility [VERIFIED]
- CSV escaping required for strings containing commas, quotes, newlines, or looking like numbers/dates [VERIFIED]
- Markdown output uses `**ColumnName**: value` pattern with `###` headings per item [VERIFIED]

## Table of Contents

1. [Column Type Conversion Reference](#1-column-type-conversion-reference)
2. [Output Formats](#2-output-formats)
3. [Implementation Patterns](#3-implementation-patterns)
4. [Sources](#4-sources)
5. [Next Steps](#5-next-steps)
6. [Document History](#6-document-history)

## 1. Column Type Conversion Reference

### 1.1 User Fields

**Single User** (`Microsoft.SharePoint.Client.FieldUserValue`)
- **Input**: Object with `LookupValue` (display name), `LookupId`, `Email` properties
- **Output**: `DisplayName (Email, LoginName)` format
- **Example**: `John Doe (john.doe@company.com, i:0#.f|membership|john.doe@company.com)`
- **Fallback**: If Email/LoginName unavailable, use display name only

**Multi-User** (`Microsoft.SharePoint.Client.FieldUserValue[]`)
- **Input**: Array of user objects
- **Output**: Semicolon-separated users, each with full details
- **Example**: `John Doe (john.doe@company.com, i:0#.f|membership|john.doe@company.com); Jane Smith (jane.smith@company.com, i:0#.f|membership|jane.smith@company.com)`

**Available User Properties from SharePoint:**
- `LookupValue` - Display name
- `LookupId` - Internal user ID
- `Email` - Email address
- `LoginName` - Claims-based login (e.g., `i:0#.f|membership|user@domain.com`)

### 1.2 Lookup Fields

**Single Lookup** (`Microsoft.SharePoint.Client.FieldLookupValue`)
- **Input**: Object with `LookupValue`, `LookupId` properties
- **Output**: Display value only (`LookupValue`)
- **Example**: `Active`

### 1.3 URL/Link Fields

**Hyperlink** (`Microsoft.SharePoint.Client.FieldUrlValue`)
- **Input**: Object with `Url`, `Description` properties
- **Output**: URL only (description can be included optionally)
- **Example**: `https://sharepoint.com/sites/docs/file.pdf`

### 1.4 Taxonomy/Managed Metadata Fields

**Single Term** (`Microsoft.SharePoint.Client.Taxonomy.TaxonomyFieldValue`)
- **Input**: Object with `Label`, `TermGuid`, `WssId` properties
- **Output**: Label only
- **Example**: `Information Technology`

**Multi-Term** (`Microsoft.SharePoint.Client.Taxonomy.TaxonomyFieldValueCollection`)
- **Input**: Collection of taxonomy values
- **Output**: Pipe-separated labels
- **Example**: `Finance|Human Resources|Legal`

### 1.5 Date/Time Fields

**DateTime** (`System.DateTime`)
- **Input**: UTC DateTime object
- **Output**: Local timezone, ISO-like format for Excel compatibility
- **Format**: `YYYY-MM-DD HH:mm:ss`
- **Example**: `2026-03-06 14:30:00`

### 1.6 Text Fields

**Single-line Text** (`System.String`)
- **Input**: Plain string
- **Output**: String (with CSV escaping if needed)
- **Example**: `Project Alpha`

**Multi-line Text** (`System.String`)
- **Input**: String with potential newlines
- **Output**: String with newlines removed (optional) or preserved
- **Example**: `Line 1 Line 2` (newlines removed)

**String Array** (`System.String[]`)
- **Input**: Array of strings
- **Output**: Pipe-separated values
- **Example**: `Value1|Value2|Value3`

### 1.7 Numeric Fields

**Number, Currency** (`System.Int32`, `System.Double`, `System.Decimal`)
- **Input**: Numeric value type
- **Output**: Unquoted number (no CSV escaping)
- **Example**: `42`, `3.14`, `1000.00`

### 1.8 Boolean Fields

**Yes/No** (`System.Boolean`)
- **Input**: Boolean value type
- **Output**: Unquoted `True` or `False`
- **Example**: `True`

### 1.9 Choice Fields

**Single Choice** (`System.String`)
- **Input**: Selected choice string
- **Output**: Plain string
- **Example**: `High Priority`

**Multi-Choice** (`System.String[]`)
- **Input**: Array of selected choices
- **Output**: Pipe-separated values
- **Example**: `Option A|Option C|Option D`

## 2. Output Formats

### 2.0 Example Data

**Sample SharePoint List**: "SPoC BIO List" with 2 items

**Item 1:**
- **ID**: 1
- **Title**: Project Alpha
- **Department**: IT
- **Owner**: John Doe (john.doe@company.com)
- **Tags**: Finance|Legal
- **Created**: 2026-01-15 09:30:00
- **Active**: True

**Item 2:**
- **ID**: 2
- **Title**: Budget Review, Q1
- **Department**: Finance
- **Owner**: Jane Smith (jane.smith@company.com); Bob Lee (bob.lee@company.com)
- **Tags**: HR
- **Created**: 2026-02-20 14:15:00
- **Active**: False

### 2.1 CSV Format (RFC 4180 with extensions)

**Header Row:**
- Field display names (localized) or internal names
- Comma-separated

**Value Rules:**
- **Strings**: Double-quoted if contains `,` `"` `\n` or looks like number/date/formula
- **Numbers**: Unquoted
- **Booleans**: Unquoted `True`/`False`
- **Dates**: RFC3339-like `YYYY-MM-DD HH:mm:ss` (unquoted or quoted)
- **Empty**: Empty string (no value)

**CSV Escape Function:**
```python
def csv_escape_text(value: str) -> str:
    # Quote if: contains comma, quote, newline, or looks like number/date/formula
    if re.match(r'^([+\-=\/]*[\.\d\s\/\:]*|.*[\,\"\n].*|[\n]*)$', value):
        return '"' + value.replace('"', '""') + '"'
    return value
```

**Example CSV Output** (`SPoC_BIO_List.csv`):
```csv
ID,Title,Department,Owner,Tags,Created,Active
1,Project Alpha,IT,John Doe (john.doe@company.com),Finance|Legal,2026-01-15 09:30:00,True
2,"Budget Review, Q1",Finance,"Jane Smith (jane.smith@company.com); Bob Lee (bob.lee@company.com)",HR,2026-02-20 14:15:00,False
```

**Notes:**
- `ID`: Unquoted number
- `Title`: Row 2 quoted because contains comma
- `Department`, `Owner`: Plain strings, no quoting needed
- `Tags`: Pipe-separated multi-value, no quoting needed
- `Created`: RFC3339-like date format
- `Active`: Unquoted boolean

### 2.2 Markdown Format

**Structure:**
```markdown
## [List Name]

### "[List Name]" - [Item Title or "Item [ID]"]
**FieldName1**: value1
**FieldName2**: value2
**FieldName3**: value3

### "[List Name]" - [Next Item Title]
...
```

**Rules:**
- List name as `##` heading
- Each item as `###` heading with list name and item title
- Skip ID field in body (already in heading context)
- Skip empty/null values
- Field name in bold, colon separator, value as plain text

**Example Markdown Output** (`SPoC_BIO_List.md`):
```markdown
## SPoC BIO List

### "SPoC BIO List" - Project Alpha
**Title**: Project Alpha
**Department**: IT
**Owner**: John Doe (john.doe@company.com)
**Tags**: Finance|Legal
**Created**: 2026-01-15 09:30:00
**Active**: True

### "SPoC BIO List" - Budget Review, Q1
**Title**: Budget Review, Q1
**Department**: Finance
**Owner**: Jane Smith (jane.smith@company.com); Bob Lee (bob.lee@company.com)
**Tags**: HR
**Created**: 2026-02-20 14:15:00
**Active**: False
```

## 3. Implementation Patterns

### 3.1 Python Conversion Function

```python
def convert_sharepoint_field_to_text(value: Any) -> str | int | float | bool | None:
    """Convert SharePoint field value to human-readable text or native type."""
    if value is None:
        return None
    
    value_type = type(value).__name__
    
    # User fields - include email and login name
    if hasattr(value, 'LookupValue') and hasattr(value, 'Email'):
        email = getattr(value, 'Email', '') or ''
        login = getattr(value, 'LoginName', '') or ''
        if email or login:
            return f"{value.LookupValue} ({email})" if not login else f"{value.LookupValue} ({email}, {login})"
        return value.LookupValue
    
    # User array
    if isinstance(value, list) and len(value) > 0 and hasattr(value[0], 'Email'):
        parts = []
        for u in value:
            email = getattr(u, 'Email', '') or ''
            parts.append(f"{u.LookupValue} ({email})" if email else u.LookupValue)
        return '; '.join(parts)
    
    # Lookup fields
    if hasattr(value, 'LookupValue') and hasattr(value, 'LookupId'):
        return value.LookupValue
    
    # URL fields
    if hasattr(value, 'Url') and hasattr(value, 'Description'):
        return value.Url
    
    # Taxonomy single
    if hasattr(value, 'Label') and hasattr(value, 'TermGuid'):
        return value.Label
    
    # Taxonomy collection
    if hasattr(value, '__iter__') and len(value) > 0 and hasattr(value[0], 'Label'):
        return '|'.join(v.Label for v in value)
    
    # DateTime
    if isinstance(value, datetime):
        local_dt = value.astimezone()  # Convert to local timezone
        return local_dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # String array
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return '|'.join(value)
    
    # Primitives (int, float, bool, str)
    if isinstance(value, (int, float, bool, str)):
        return value
    
    # Fallback: convert to string
    return str(value)
```

### 3.2 Fields to Ignore

System/internal fields that should not be exported:
- `Author`, `Editor` (use Created By, Modified By display names instead)
- `_ColorTag`, `_CommentCount`, `_ComplianceFlags`, `_ComplianceTag`
- `_ComplianceTagUserId`, `_ComplianceTagWrittenTime`, `_CopySource`
- `_DisplayName`, `_dlc_DocId`, `_dlc_DocIdUrl`, `_IsRecord`
- `_LikeCount`, `_ModerationStatus`, `_UIVersionString`
- `AppAuthor`, `AppEditor`, `Attachments`, `CheckoutUser`
- `ComplianceAssetId`, `ContentType`, `DocIcon`, `Edit`
- `FileSizeDisplay`, `FolderChildCount`, `ItemChildCount`
- `LinkTitle`, `LinkFilename`, `LinkFilenameNoMenu`
- `MediaServiceAutoTags`, `MediaServiceLocation`, `MediaServiceOCR`
- `ParentVersionString`, `SharedWithDetails`, `SharedWithUsers`

### 3.3 Document Library Special Fields

When source is document library (not list):
- **ID**: Item ID
- **Url**: Full URL (`tenant_url` + `FileRef`)
- **ItemType**: `File` or `Folder` (from `FSObjType`: 0=File, 1=Folder)

## 4. Sources

**Primary Sources:**
- `V2CR-IN01-SC-INPUT-EXPCSV`: `_input/ExportListItemsAsCSV.ps1` - PowerShell export script with field iteration [VERIFIED]
- `V2CR-IN01-SC-INPUT-INCL`: `_input/_includes.ps1` - `ConvertSharePointFieldToTextOrValueType` function [VERIFIED]

## 5. Next Steps

1. Implement `convert_sharepoint_field_to_text()` in Python for crawler
2. Update `get_list_items()` to use conversion function
3. Create export functions for CSV and Markdown formats
4. Update `step_download_source` to save full list item content
5. Default to `.md` file for embedding (more readable for LLM)

## 6. Document History

**[2026-03-06 12:05]**
- Fixed: Converted Markdown table in section 2.0 to list format (GLOBAL-RULES compliance)

**[2026-03-06 11:35]**
- Initial research document created
- Analyzed PowerShell scripts from `_input/` folder
- Documented all SharePoint column type conversions
- Defined CSV and Markdown output format specifications
