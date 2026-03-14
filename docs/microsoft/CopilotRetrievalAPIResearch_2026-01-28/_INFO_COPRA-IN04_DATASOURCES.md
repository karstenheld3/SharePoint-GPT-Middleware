# INFO: Copilot Retrieval API - Data Sources and Filtering

**Doc ID**: COPRA-IN01
**Goal**: Document data source types and KQL filtering capabilities

**Depends on:**
- `_INFO_COPRA_SOURCES.md [COPRA-IN01]` for source URLs
- `__INFO_COPRA-IN00_TOC.md [COPRA-IN01]` for topic scope

## Summary

The Retrieval API supports three data sources: SharePoint, OneDrive, and Copilot connectors. Each source has different file type support, retrieval modes (semantic vs lexical), and licensing requirements. KQL filtering enables scoping results to specific sites, file types, authors, and date ranges.

**Key Facts [VERIFIED]:**
- One data source per request (no interleaved results)
- SharePoint/OneDrive: Semantic retrieval for .doc, .docx, .pptx, .pdf, .aspx, .one
- Other file types: Lexical retrieval only
- File size limits: 512MB (PDF/PPTX/DOCX), 150MB (others)
- 10 KQL filter properties supported

**Use Cases:**
- Scope retrieval to specific SharePoint sites
- Filter by file type, author, or date range
- Retrieve from external systems via Copilot connectors

## Quick Reference

**Data Sources:**
- `sharePoint` - SharePoint Online content (tenant-level)
- `oneDriveBusiness` - OneDrive for Business (user-level, Copilot license only)
- `externalItem` - Copilot connectors (external content)

**Semantic Retrieval Extensions:** `.doc`, `.docx`, `.pptx`, `.pdf`, `.aspx`, `.one`

**KQL Operators:** `AND`, `OR`, `NOT`

## SharePoint Data Source

### Overview [VERIFIED]

SharePoint is the primary data source for tenant-level content retrieval.

**dataSource value:** `sharePoint`

**Permissions required:** `Files.Read.All` + `Sites.Read.All`

### Supported File Types [VERIFIED]

**Semantic + Lexical Retrieval (hybrid):**
- `.doc` - Word 97-2003
- `.docx` - Word documents
- `.pptx` - PowerPoint presentations
- `.pdf` - PDF documents
- `.aspx` - SharePoint pages
- `.one` - OneNote sections

**Lexical Retrieval Only:**
- All other text-based file extensions

### File Size Limits [VERIFIED]

- PDF, PPTX, DOCX: Up to 512 MB
- All other extensions: Up to 150 MB

**Note:** Files exceeding these limits are not indexed and won't return results.

### Table Content [VERIFIED]

Retrieval from text in tables is limited to:
- `.doc` files
- `.docx` files
- `.pptx` files

### Unsupported Content [VERIFIED]

- Images and charts (non-textual content)
- Files excluded by DLP policies
- Non-searchable SharePoint sites
- Sensitivity-labeled content (confidential/highly confidential)

## OneDrive Data Source

### Overview [VERIFIED]

OneDrive provides access to user-level content from personal business storage.

**dataSource value:** `oneDriveBusiness`

**Permissions required:** `Files.Read.All` + `Sites.Read.All`

### Licensing Restriction [VERIFIED]

OneDrive retrieval is **only available** to users with Microsoft 365 Copilot license.

**Not available via pay-as-you-go.**

### User-Level Index [VERIFIED]

OneDrive queries the user-level semantic index which includes:
- User's OneDrive files
- Emails (mailbox content)
- Documents user creates, comments on, or shares

### Update Frequency [VERIFIED]

- User mailbox documents: Near real-time
- User-created documents: Near real-time on first index
- Updated documents: Immediately after change

## Copilot Connectors (externalItem)

### Overview [VERIFIED]

Copilot connectors enable retrieval from external (non-Microsoft 365) content sources.

**dataSource value:** `externalItem`

**Permissions required:** `ExternalItem.Read.All`

### Connection Configuration [VERIFIED]

To retrieve from specific connectors, use `dataSourceConfiguration`:

```json
{
  "dataSource": "externalItem",
  "dataSourceConfiguration": {
    "externalItem": {
      "connections": [
        { "connectionId": "ContosoITServiceNowKB" },
        { "connectionId": "ContosoHRServiceNowKB" }
      ]
    }
  }
}
```

**Without configuration:** Queries all available Copilot connectors the user has access to.

### Queryable Properties [VERIFIED]

Copilot connectors can define custom queryable properties in their schema. Use these properties in `filterExpression` for connector-specific filtering.

**Example:**
```json
{
  "filterExpression": "Label_Title:\"Corporate VPN\""
}
```

### Relevance Score [VERIFIED]

Extracts from Copilot connectors may be returned without a `relevanceScore`.

## KQL Filter Expression

### Syntax [VERIFIED]

The `filterExpression` parameter accepts Keyword Query Language (KQL) syntax.

**Operators:**
- `AND` - Both conditions must match
- `OR` - Either condition must match
- `NOT` - Exclude matching results

**String values:** Enclose in escaped quotes `\"`

### Supported Properties for SharePoint/OneDrive [VERIFIED]

| Property | Description | Example |
|----------|-------------|---------|
| Author | Document author | `Author:\"Megan Bowen\"` |
| FileExtension | File extension | `FileExtension:\"docx\"` |
| Filename | Full filename | `Filename:\"Report.docx\"` |
| FileType | File type | `FileType:\"pdf\"` |
| InformationProtectionLabelId | Sensitivity label GUID | `InformationProtectionLabelId:\"f0dd...\"` |
| LastModifiedTime | Last modified date | `LastModifiedTime>= 2024-07-22` |
| ModifiedBy | Last modifier | `ModifiedBy:\"Adele Vance\"` |
| Path | URL path | `path:\"https://contoso.sharepoint.com/sites/HR/\"` |
| SiteID | SharePoint site GUID | `SiteID:\"e2cf7e40-...\"` |
| Title | Document title | `Title:\"Windows 10 Device\"` |

### Filter Examples

#### Filter by Author [VERIFIED]

```json
{
  "filterExpression": "Author:\"Megan Bowen\""
}
```

#### Filter by Date Range [VERIFIED]

```json
{
  "filterExpression": "LastModifiedTime>= 2024-07-22 AND LastModifiedTime<= 2025-01-08"
}
```

#### Filter by File Extension [VERIFIED]

```json
{
  "filterExpression": "FileExtension:\"docx\" OR FileExtension:\"pdf\" OR FileExtension:\"pptx\""
}
```

#### Filter by File Type [VERIFIED]

```json
{
  "filterExpression": "FileType:\"pdf\" OR FileType:\"pptx\" OR FileType:\"docx\""
}
```

#### Filter by Path (Specific Site) [VERIFIED]

```json
{
  "filterExpression": "path:\"https://contoso.sharepoint.com/sites/HR1/\""
}
```

**Best Practice:** Don't use sharing links or browser URL bar. Go to SharePoint > More Actions > Details > copy the path.

#### Filter by Site ID [VERIFIED]

```json
{
  "filterExpression": "SiteID:\"e2cf7e40-d689-41de-99ee-a423811a253c\""
}
```

#### Filter by Filename [VERIFIED]

```json
{
  "filterExpression": "Filename:\"Contoso Mission Statement.docx\""
}
```

#### Filter by Title [VERIFIED]

```json
{
  "filterExpression": "Title:\"Windows 10 Device\""
}
```

#### Filter by Sensitivity Label [VERIFIED]

```json
{
  "filterExpression": "InformationProtectionLabelId:\"f0ddcc93-d3c0-4993-b5cc-76b0a283e252\""
}
```

#### Filter by Modified By [VERIFIED]

```json
{
  "filterExpression": "ModifiedBy:\"Adele Vance\""
}
```

#### Combined Filters [VERIFIED]

```json
{
  "filterExpression": "Author:\"John Doe\" AND FileExtension:\"docx\" AND LastModifiedTime>= 2024-01-01"
}
```

### Filter Warnings [VERIFIED]

- **Invalid KQL syntax:** Query executes with no scoping (no error returned)
- **Not all properties supported:** Only the 10 listed properties work
- **Path format matters:** Use the Details pane path, not browser URL

## Sources

**Primary:**
- `COPRA-IN01-SC-MSFT-APIREF`: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api/ai-services/retrieval/copilotroot-retrieval
- `COPRA-IN01-SC-MSFT-KQL`: https://learn.microsoft.com/en-us/sharepoint/dev/general-development/keyword-query-language-kql-syntax-reference

**Related:**
- `COPRA-IN01-SC-MSFT-CONNECTORS`: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/overview-copilot-connector

## Document History

**[2026-01-29 09:00]**
- Initial document created
- All 15 TOC items documented
- Filter examples for all 10 properties included
