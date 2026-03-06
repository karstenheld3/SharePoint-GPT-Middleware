# SPEC: Crawler List Item Export

**Doc ID**: V2CR-SP01
**Goal**: Specify how SharePoint list items are crawled, converted, and exported to CSV and Markdown formats
**Timeline**: Created 2026-03-06
**Target file**: `src/routers_v2/common_sharepoint_functions_v2.py`, `src/routers_v2/crawler.py`

**Depends on:**
- `_V2_SPEC_ROUTERS.md [V2CR-SP00]` for V2 router patterns
- `_V2_IMPL_CRAWLER.md [V2CR-IP01]` for crawler implementation context
- `_INFO_SHAREPOINT_LIST_COLUMN_TYPES.md [V2CR-IN01]` for column type research

## MUST-NOT-FORGET

- FieldUserValue requires $expand to get Email property - not available in item.properties directly
- TaxonomyFieldValue uses `Label` property, not `LookupValue`
- DateTime values from SharePoint are UTC - convert to local timezone
- Use pipe `|` for multi-value separator, semicolon `;` for multi-user
- Default to `.md` format for embedding (more LLM-readable)
- Skip system fields (fields starting with `_`, internal SharePoint fields)
- Skip ID in body (in heading), Modified, Created (system timestamps)
- Title first in Markdown body (aids search), then other fields

## Table of Contents

1. [Scenario](#1-scenario)
2. [Context](#2-context)
3. [Domain Objects](#3-domain-objects)
4. [Functional Requirements](#4-functional-requirements)
5. [Design Decisions](#5-design-decisions)
6. [Implementation Guarantees](#6-implementation-guarantees)
7. [Key Mechanisms](#7-key-mechanisms)
8. [Data Structures](#8-data-structures)
9. [Document History](#9-document-history)

## 1. Scenario

**Problem:** Current list item crawling loses all column data. Only ID, Title, and Modified date are captured. The `get_list_items()` function returns full item properties, but `get_list_items_as_sharepoint_files()` discards them when converting to `SharePointFile` objects.

**Solution:**
- Preserve full item properties during download step
- Convert SharePoint field types to human-readable text
- Export to both CSV (machine-readable) and Markdown (LLM-readable) formats
- Use Markdown as default for vector store embedding

**What we don't want:**
- Raw JSON dumps with SharePoint internal field names
- Complex nested structures that are hard to read
- Loss of user-friendly display names
- Inconsistent date/number formatting

## 2. Context

The V2 crawler processes three source types: `file_sources` (documents), `sitepage_sources` (pages), and `list_sources` (list items). This spec focuses on `list_sources`.

**Current flow:**
```
get_list_items() -> get_list_items_as_sharepoint_files() -> step_download_source() -> step_process_source() -> step_embed_source()
```

**Problem point:** `get_list_items_as_sharepoint_files()` creates `SharePointFile` with only ID, Title, Modified - discards all column data.

## 3. Domain Objects

### SharePoint Field Types

SharePoint fields are typed objects returned by the REST API. The `FieldTypeKind` enum defines the type.

**User-Editable Field Types** (FieldTypeKind values users can create/edit):

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

**Read-Only/Computed Fields** (system-generated, included in export):
- `1` - **Integer** - Whole number (often system-generated)
- `5` - **Counter** - Auto-increment ID
- `12` - **Computed** - Calculated from other fields
- `17` - **Calculated** - Formula-based value

**Note:** Internal system fields (Threading, Attachments, ContentTypeId, etc.) are filtered out by FR-09

### Python Field Value Classes

From `office365-rest-python-client` library: [VERIFIED]

**FieldLookupValue** (`office365.sharepoint.fields.lookup_value`)
- `LookupId` (int) - Referenced item ID
- `LookupValue` (str) - Display value

**FieldUserValue** (`office365.sharepoint.fields.user_value`)
- Extends `FieldLookupValue`
- `LookupId` (int) - User ID
- `LookupValue` (str) - User login name or display name

**FieldUrlValue** (`office365.sharepoint.fields.url_value`)
- `Url` (str) - URI (max 255 chars)
- `Description` (str) - Description (max 255 chars)

**TaxonomyFieldValue** (`office365.sharepoint.taxonomy.field_value`) [VERIFIED]
- `Label` (str) - Term label (NOT `LookupValue`)
- `TermGuid` (str) - Term GUID
- `WssId` (int) - List item ID

**TaxonomyFieldValueCollection**
- Collection of `TaxonomyFieldValue` objects

### User Object Properties

From `office365.sharepoint.principal.users.user.User`:
- `email` (str) - User email address
- `login_name` (str) - Login name (claims format: `i:0#.f|membership|user@domain.com`)
- `user_principal_name` (str) - UPN (user@domain.com)
- `title` (str) - Display name

**Note:** User email is NOT available on `FieldUserValue` directly. Must expand User object or use separate lookup. [VERIFIED]

### ListItemExport

A **ListItemExport** represents a single list item with all fields converted to human-readable format.

**Properties:**
- `id` (int) - Item ID
- `title` (str) - Item title
- `list_name` (str) - Source list name
- `fields` (dict[str, str]) - Field name -> converted value
- `field_display_names` (dict[str, str]) - Internal name -> display name

### ExportResult

**Properties:**
- `csv_content` (str) - Full CSV file content with header
- `md_content` (str) - Full Markdown file content
- `item_count` (int) - Number of items exported
- `field_count` (int) - Number of fields exported

## 4. Functional Requirements

**V2CR-FR-01: Field Type Conversion**
- Convert all SharePoint field types to human-readable strings
- Preserve numeric types (int, float) for CSV without quoting
- Use American number format (period as decimal separator: `75000.00`, `45.5`)
- Preserve boolean as `True`/`False` without quoting
- Convert DateTime to `YYYY-MM-DD HH:mm:ss` format (local timezone)

**V2CR-FR-02: User Field Format**
- Single user: `DisplayName <email@domain.com>` (Outlook-compatible for copy/paste)
- Multi-user: `DisplayName1 <email1>; DisplayName2 <email2>`
- Fallback to display name only if email unavailable

**V2CR-FR-03: Lookup Field Format**
- Single lookup: Display value only
- Multi-lookup: Pipe-separated values (`Value1|Value2|Value3`)

**V2CR-FR-04: Taxonomy Field Format**
- Single term: Label only
- Multi-term: Pipe-separated labels (`Term1|Term2|Term3`)

**V2CR-FR-05: URL Field Format**
- URL only (description omitted for brevity)

**V2CR-FR-06: Choice Field Format**
- Single choice: Plain string
- Multi-choice: Pipe-separated values

**V2CR-FR-07: CSV Output Format**
- RFC 4180 compliant with extensions
- Header row with field display names
- Column order: ID, Title, user fields (alphabetical by display name), Created, Modified
- No duplicate columns (each field appears exactly once)
- Double-quote strings containing comma, quote, newline, or looking like number/date
- Unquoted numbers and booleans
- UTF-8 encoding without BOM

**V2CR-FR-08: Markdown Output Format**
- List name as `##` heading
- Each item as `###` heading: `"[ListName]" - [Title]`
- Title field always first in body (even though also in heading - aids search)
- Fields as list items: `- FieldName: value` (no bold/italic - saves tokens)
- Currency fields include symbol in Markdown: `- Budget: $ 75000.0` (not in CSV)
- Skip empty/null values
- Skip ID field in body (in heading)
- Skip Modified and Created fields (system timestamps not useful for embedding)
- Plain markdown only - NO triple backtick code fences wrapping content

**V2CR-FR-09: Field Filtering**
- Auto-detect visible fields (Hidden=false, not in ignore list)
- Skip system fields starting with `_`
- Skip system timestamp fields: Modified, Created (not useful for embedding)
- Skip internal fields: Author, Editor, AppAuthor, AppEditor, Attachments, CheckoutUser, ComplianceAssetId, ContentType, DocIcon, Edit, FileSizeDisplay, FolderChildCount, ItemChildCount, LinkTitle, LinkFilename, LinkFilenameNoMenu, MediaServiceAutoTags, MediaServiceLocation, MediaServiceOCR, ParentVersionString, SharedWithDetails, SharedWithUsers

**V2CR-FR-10: Default Export Format**
- Default to `.md` for embedding (more LLM-readable)
- Also generate `.csv` for backup/analysis
- Store both in `originals/` folder

## 5. Design Decisions

**V2CR-DD-01:** Use pipe `|` as multi-value separator. Rationale: Less common in text than comma or semicolon, readable, no escaping needed.

**V2CR-DD-02:** Use semicolon `;` as multi-user separator. Rationale: Distinguishes from pipe-separated values within a single user (if needed).

**V2CR-DD-03:** Convert DateTime to local timezone. Rationale: More meaningful for human readers, matches Excel behavior.

**V2CR-DD-04:** Use RFC 4180 CSV with smart quoting. Rationale: Compatible with Excel, Python csv module, and other tools.

**V2CR-DD-05:** Default to Markdown for embedding. Rationale: More readable for LLMs, preserves structure, searchable headers.

**V2CR-DD-06:** Store full item properties during download, not process. Rationale: Single API call, all data available for both CSV and MD generation.

**V2CR-DD-07:** Use field display names in output. Rationale: More readable than internal names, matches SharePoint UI.

## 6. Implementation Guarantees

**V2CR-IG-01:** All non-empty, non-system fields are included in export.

**V2CR-IG-02:** Field display names are used in both CSV headers and Markdown labels.

**V2CR-IG-03:** DateTime values are converted to local timezone with consistent format.

**V2CR-IG-04:** CSV output can be imported into Excel without data corruption.

**V2CR-IG-05:** Markdown output is valid and renders correctly.

**V2CR-IG-06:** User email addresses are included when available from SharePoint.

## 7. Key Mechanisms

### Field Conversion Function

```python
def convert_field_to_text(value: Any, field_type: int = None) -> str | int | float | bool | None:
    """Convert SharePoint field value to human-readable text or native type."""
    if value is None:
        return None
    
    # FieldUserValue - check for Email attribute
    if hasattr(value, 'LookupValue') and hasattr(value, 'LookupId'):
        email = getattr(value, 'Email', '') or ''
        display = value.LookupValue or ''
        return f"{display} <{email}>" if email else display
    
    # List of FieldUserValue
    if isinstance(value, list) and len(value) > 0 and hasattr(value[0], 'LookupValue'):
        parts = []
        for v in value:
            email = getattr(v, 'Email', '') or ''
            display = v.LookupValue or ''
            parts.append(f"{display} <{email}>" if email else display)
        return '; '.join(parts)
    
    # FieldUrlValue
    if hasattr(value, 'Url') and hasattr(value, 'Description'):
        return value.Url or ''
    
    # TaxonomyFieldValue
    if hasattr(value, 'Label') and hasattr(value, 'TermGuid'):
        return value.Label or ''
    
    # TaxonomyFieldValueCollection or list of TaxonomyFieldValue
    if isinstance(value, (list, tuple)) and len(value) > 0 and hasattr(value[0], 'Label'):
        return '|'.join(v.Label for v in value if v.Label)
    
    # DateTime
    if hasattr(value, 'isoformat'):  # datetime object
        local_dt = value.astimezone() if value.tzinfo else value
        return local_dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # String array (MultiChoice)
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return '|'.join(value)
    
    # Primitives
    if isinstance(value, (int, float, bool)):
        return value
    
    if isinstance(value, str):
        return value
    
    # Fallback
    return str(value) if value else None
```

### CSV Escape Function

```python
import re

def csv_escape(value: Any) -> str:
    """Escape value for CSV output."""
    if value is None:
        return ''
    if isinstance(value, bool):
        return str(value)  # True/False unquoted
    if isinstance(value, (int, float)):
        return str(value)  # Numbers unquoted
    
    s = str(value)
    # Quote if contains comma, quote, newline, or looks like number/date/formula
    if re.match(r'^([+\-=\/]*[\.\d\s\/\:]*|.*[\,\"\n\r].*|[\n\r]*)$', s):
        return '"' + s.replace('"', '""') + '"'
    return s
```

### Export Functions

```python
def export_list_items_to_csv(items: list[dict], field_names: list[str], 
                              display_names: dict[str, str]) -> str:
    """Export list items to CSV string."""
    lines = []
    # Header
    header = ','.join(display_names.get(f, f) for f in field_names)
    lines.append(header)
    # Rows
    for item in items:
        values = [csv_escape(convert_field_to_text(item.get(f))) for f in field_names]
        lines.append(','.join(values))
    return '\n'.join(lines)

def export_list_items_to_markdown(items: list[dict], list_name: str,
                                   field_names: list[str], 
                                   display_names: dict[str, str],
                                   currency_fields: set[str] = None) -> str:
    """Export list items to Markdown string."""
    lines = [f"## {list_name}", ""]
    currency_fields = currency_fields or set()
    # Fields to skip in body (ID/Title in heading, Modified/Created are system fields)
    skip_fields = {'ID', 'Title', 'Modified', 'Created'}
    for item in items:
        title = item.get('Title') or f"Item {item.get('ID', '?')}"
        lines.append(f'### "{list_name}" - {title}')
        for f in field_names:
            if f in skip_fields:
                continue
            value = convert_field_to_text(item.get(f))
            if value is None or value == '':
                continue
            display = display_names.get(f, f)
            # Add $ prefix for currency fields in Markdown
            if f in currency_fields and isinstance(value, (int, float)):
                lines.append(f"- {display}: $ {value}")
            else:
                lines.append(f"- {display}: {value}")
        lines.append("")
    return '\n'.join(lines)
```

## 8. Data Structures

### Comprehensive Example: All Column Types

**List Name**: "Project Tracker"

**Columns defined:**
- **ID** (Counter) - Auto-generated
- **Title** (Text) - Single line
- **Description** (Note) - Multi-line rich text
- **Start Date** (DateTime) - Date only
- **Due Date** (DateTime) - Date and time
- **Status** (Choice) - Single choice: Not Started, In Progress, Completed, On Hold
- **Priority** (Choice) - Single choice: High, Medium, Low
- **Categories** (MultiChoice) - Multiple: Finance, Legal, HR, IT, Operations
- **Project Lead** (User) - Single person
- **Team Members** (User) - Multiple people
- **Related Project** (Lookup) - Reference to another list
- **Budget** (Currency) - Currency value
- **Spent** (Currency) - Amount spent to date
- **Completion %** (Number) - Percentage
- **Active** (Boolean) - Yes/No
- **Project Link** (URL) - Hyperlink
- **Department** (Taxonomy) - Single managed metadata term
- **Tags** (Taxonomy) - Multiple managed metadata terms
- **Calculated Field** (Calculated) - Formula: `=[Due Date]-[Start Date]`

### Example SharePoint List Item (raw JSON)

```json
{
  "ID": 42,
  "Title": "Q1 Budget Review",
  "Description": "<div>Review all department budgets for Q1.\nInclude variance analysis.</div>",
  "Start_x0020_Date": "2026-01-15T00:00:00Z",
  "Due_x0020_Date": "2026-02-28T17:00:00Z",
  "Status": "In Progress",
  "Priority": "High",
  "Categories": ["Finance", "Operations"],
  "Project_x0020_Lead": {"LookupId": 7, "LookupValue": "John Doe", "Email": "john.doe@company.com"},
  "Team_x0020_Members": [
    {"LookupId": 7, "LookupValue": "John Doe", "Email": "john.doe@company.com"},
    {"LookupId": 12, "LookupValue": "Jane Smith", "Email": "jane.smith@company.com"},
    {"LookupId": 15, "LookupValue": "Bob Lee", "Email": "bob.lee@company.com"}
  ],
  "Related_x0020_Project": {"LookupId": 5, "LookupValue": "Annual Planning 2026"},
  "Budget": 75000.00,
  "Spent": 33750.50,
  "Completion_x0020__x0025_": 45.5,
  "Active": true,
  "Project_x0020_Link": {"Url": "https://sharepoint.com/sites/projects/q1review", "Description": "Project Site"},
  "Department": {"Label": "Finance", "TermGuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "WssId": 1},
  "Tags": [
    {"Label": "Budget", "TermGuid": "b2c3d4e5-f6a7-8901-bcde-f23456789012", "WssId": 2},
    {"Label": "Q1", "TermGuid": "c3d4e5f6-a7b8-9012-cdef-345678901234", "WssId": 3},
    {"Label": "Review", "TermGuid": "d4e5f6a7-b8c9-0123-defa-456789012345", "WssId": 4}
  ],
  "Calculated_x0020_Field": 44
}
```

### Example CSV Output (all column types, with escaping)

```csv
ID,Title,Description,Start Date,Due Date,Status,Priority,Categories,Project Lead,Team Members,Related Project,Budget,Spent,Completion %,Active,Project Link,Department,Tags,Calculated Field
42,"Q1 ""Budget"" Review, Phase 1","Review items: A, B, C; check ""quoted"" text. Formula: =SUM(A1:A10)",2026-01-15 00:00:00,2026-02-28 18:00:00,In Progress,High,Finance|Operations,"John ""JD"" Doe <john.doe@company.com>","John Doe <john.doe@company.com>; Jane Smith <jane.smith@company.com>; Bob Lee <bob.lee@company.com>","Annual Planning, 2026",75000.0,33750.50,45.5,True,https://sharepoint.com/sites/projects/q1review,Finance,Budget|Q1|Review,44
```

**Escaping applied in this example:**
- **Title**: `"Q1 ""Budget"" Review, Phase 1"` - contains comma and double quotes
- **Description**: `"Review items: A, B, C; check ""quoted"" text. Formula: =SUM(A1:A10)"` - commas, semicolon, quotes, equals sign
- **Project Lead**: `"John ""JD"" Doe <john.doe@company.com>"` - nickname in quotes
- **Related Project**: `"Annual Planning, 2026"` - contains comma

### Example with Special Characters (escaping required)

**Raw data with problematic characters:**
- **Title**: `Project "Alpha" - Phase 1, 2 & 3`
- **Description**: `Review items: A, B, C; also check "quoted" text and pipe|separated|values`
- **Notes**: `User said: "Don't forget the 50% discount"`
- **Formula**: `=IF(A1>0,"Yes","No")`

**SharePoint JSON (special chars in values):**
```json
{
  "ID": 99,
  "Title": "Project \"Alpha\" - Phase 1, 2 & 3",
  "Description": "Review items: A, B, C; also check \"quoted\" text and pipe|separated|values",
  "Notes": "User said: \"Don't forget the 50% discount\"",
  "Formula": "=IF(A1>0,\"Yes\",\"No\")",
  "Status": "In Progress",
  "Tags": [{"Label": "Q1|Q2", "TermGuid": "abc-123", "WssId": 1}]
}
```

**CSV Output (properly escaped):**
```csv
ID,Title,Description,Notes,Formula,Status,Tags
99,"Project ""Alpha"" - Phase 1, 2 & 3","Review items: A, B, C; also check ""quoted"" text and pipe|separated|values","User said: ""Don't forget the 50% discount""","=IF(A1>0,""Yes"",""No"")",In Progress,Q1|Q2
```

**CSV Escaping Rules Applied:**
- **Double quotes** `"` → Escaped as `""` inside quoted string
- **Commas** `,` → Entire value wrapped in double quotes
- **Semicolons** `;` → No escaping needed (not a CSV delimiter)
- **Pipe** `|` → No escaping needed (our multi-value separator, but in text it's literal)
- **Single quotes** `'` → No escaping needed
- **Equals sign** `=` → Value quoted to prevent Excel formula interpretation

**Markdown Output (no escaping needed):**
```markdown
### "Project Tracker" - Project "Alpha" - Phase 1, 2 & 3
- Title: Project "Alpha" - Phase 1, 2 & 3
- Description: Review items: A, B, C; also check "quoted" text and pipe|separated|values
- Notes: User said: "Don't forget the 50% discount"
- Formula: =IF(A1>0,"Yes","No")
- Status: In Progress
- Tags: Q1|Q2
```

**Note:** In Markdown, special characters are preserved as-is since Markdown doesn't require escaping for these characters in plain text content.

**CSV Column Type Mapping:**
- **ID** (Counter): `42` - unquoted integer
- **Title** (Text): `"Q1 Budget Review"` - quoted (contains space, safe practice)
- **Description** (Note): `"Review all..."` - quoted, newlines removed
- **Start Date** (DateTime): `2026-01-15 00:00:00` - local timezone
- **Due Date** (DateTime): `2026-02-28 18:00:00` - local timezone (+1 hour from UTC)
- **Status** (Choice): `In Progress` - plain string
- **Priority** (Choice): `High` - plain string
- **Categories** (MultiChoice): `Finance|Operations` - pipe-separated
- **Project Lead** (User): `John Doe <john.doe@company.com>` - Outlook-compatible format
- **Team Members** (User[]): `John Doe <john.doe@company.com>; Jane Smith <jane.smith@company.com>; Bob Lee <bob.lee@company.com>` - semicolon-separated, Outlook-compatible format
- **Related Project** (Lookup): `Annual Planning 2026` - display value only
- **Budget** (Currency): `75000.0` - unquoted, American format (period decimal)
- **Spent** (Currency): `33750.50` - unquoted, American format (period decimal)
- **Completion %** (Number): `45.5` - unquoted, American format (period decimal)
- **Active** (Boolean): `True` - unquoted
- **Project Link** (URL): `https://...` - URL only
- **Department** (Taxonomy): `Finance` - label only
- **Tags** (Taxonomy[]): `Budget|Q1|Review` - pipe-separated labels
- **Calculated Field** (Calculated): `44` - computed value

### Example Markdown Output (all column types)

```markdown
## Project Tracker

### "Project Tracker" - Q1 Budget Review
- Description: Review all department budgets for Q1. Include variance analysis.
- Start Date: 2026-01-15 00:00:00
- Due Date: 2026-02-28 18:00:00
- Status: In Progress
- Priority: High
- Categories: Finance|Operations
- Project Lead: John Doe <john.doe@company.com>
- Team Members: John Doe <john.doe@company.com>; Jane Smith <jane.smith@company.com>; Bob Lee <bob.lee@company.com>
- Related Project: Annual Planning 2026
- Budget: $ 75000.0
- Spent: $ 33750.50
- Completion %: 45.5
- Active: True
- Project Link: https://sharepoint.com/sites/projects/q1review
- Department: Finance
- Tags: Budget|Q1|Review
- Calculated Field: 44
```

### Conversion Summary Table

- **Text** (2): String as-is
- **Note** (3): String, newlines removed for CSV
- **DateTime** (4): `YYYY-MM-DD HH:mm:ss` (local timezone)
- **Choice** (6): String as-is
- **Lookup** (7): `LookupValue` (display text only)
- **Boolean** (8): `True` or `False`
- **Number** (9): Unquoted decimal, American format (period separator)
- **Currency** (10): Unquoted decimal in CSV, with `$ ` symbol in Markdown (space after)
- **URL** (11): URL string only (description omitted)
- **MultiChoice** (15): Pipe-separated values
- **User** (20): `DisplayName <email>` or semicolon-separated for multi (Outlook-compatible)
- **Taxonomy**: `Label` or pipe-separated labels for multi
- **Calculated** (17): Computed value as string/number

## 9. Document History

**[2026-03-06 14:16]**
- Changed: FR-07 - CSV column order: ID, Title, alphabetical user fields, Created, Modified
- Changed: FR-08 - Title always first in Markdown body (aids search)
- Changed: MUST-NOT-FORGET - Title first in Markdown body
- Fixed: Duplicate Title column in CSV removed

**[2026-03-06 14:10]**
- Changed: FR-08 - Skip Modified/Created (system fields), no code fences
- Changed: FR-09 - Added Modified, Created to skip list
- Fixed: crawler.py step_process_source() - removed code fence wrapping

**[2026-03-06 12:16]**
- Added: Currency symbol `$` in Markdown output (not in CSV)

**[2026-03-06 12:15]**
- Added: Spent (Currency) field to example data to demonstrate currency format

**[2026-03-06 12:14]**
- Changed: Number/Currency always use American format (period as decimal separator)

**[2026-03-06 12:13]**
- Changed: User field format to Outlook-compatible `DisplayName <email>` for copy/paste

**[2026-03-06 12:12]**
- Changed: Markdown output uses list items `- FieldName: value` (no bold/italic - saves tokens)

**[2026-03-06 12:10]**
- Added: `[VERIFIED]` labels to key technical claims per GLOBAL-RULES

**[2026-03-06 12:08]**
- Added: Special characters escaping example (double quotes, commas, semicolons, pipes, equals signs)
- Added: CSV escaping rules summary

**[2026-03-06 12:05]**
- Changed: Simplified field types to user-editable columns only
- Added: Comprehensive example with ALL 17 column types (Text, Note, DateTime, Choice, MultiChoice, Lookup, User, Boolean, Number, Currency, URL, Taxonomy single/multi, Calculated)
- Added: Full raw JSON, CSV, and Markdown output examples
- Added: Conversion Summary Table

**[2026-03-06 12:00]**
- Initial specification created
- Documented all SharePoint field types from REST API and Python SDK
- Defined CSV and Markdown output formats with examples
- Specified field conversion rules and implementation patterns
