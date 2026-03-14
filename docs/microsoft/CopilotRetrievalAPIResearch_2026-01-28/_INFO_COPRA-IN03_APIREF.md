# INFO: Copilot Retrieval API - API Reference

**Doc ID**: COPRA-IN01
**Goal**: Complete API reference with endpoint, parameters, and response types

**Depends on:**
- `_INFO_COPRA_SOURCES.md [COPRA-IN01]` for source URLs
- `__INFO_COPRA-IN00_TOC.md [COPRA-IN01]` for topic scope

## Summary

The Retrieval API has a single POST endpoint that accepts a natural language query and returns relevant text extracts from Microsoft 365 content. It supports filtering via KQL, metadata selection, and result limits.

**Key Facts [VERIFIED]:**
- Single endpoint: `POST /copilot/retrieval`
- Available in v1.0 (GA) and beta
- Query limit: 1,500 characters
- Max results: 25 per request
- Supports batch requests (up to 20 per batch)

**Use Cases:**
- Semantic search for RAG pipelines
- Grounding LLM responses with M365 content
- Filtered retrieval from specific sites or file types

## Quick Reference

**Endpoint:**
```
POST https://graph.microsoft.com/v1.0/copilot/retrieval
POST https://graph.microsoft.com/beta/copilot/retrieval
```

**Required Headers:**
- `Authorization: Bearer {token}`
- `Content-Type: application/json`

**Required Parameters:**
- `queryString` - Natural language query (max 1,500 chars)
- `dataSource` - One of: `sharePoint`, `oneDriveBusiness`, `externalItem`

## HTTP Endpoint

### v1.0 (General Availability) [VERIFIED]

```http
POST https://graph.microsoft.com/v1.0/copilot/retrieval
Content-Type: application/json
Authorization: Bearer {token}
```

### Beta [VERIFIED]

```http
POST https://graph.microsoft.com/beta/copilot/retrieval
Content-Type: application/json
Authorization: Bearer {token}
```

**Note:** Beta APIs are subject to change. Not supported for production applications.

## Request Headers

| Header | Value | Required |
|--------|-------|----------|
| Authorization | `Bearer {token}` | Yes |
| Content-Type | `application/json` | Yes |

**Authentication:** Uses standard Microsoft Graph authentication. See `_INFO_COPRA-IN01_AUTH.md [COPRA-IN01]` for details.

## Request Body Parameters

### queryString (Required) [VERIFIED]

Natural language query string to search for.

**Constraints:**
- Maximum 1,500 characters
- Should be a single sentence
- Avoid spelling errors in context-rich keywords
- Provide as much context as possible
- Avoid generic queries

**Example:**
```json
{
  "queryString": "How to setup corporate VPN?"
}
```

### dataSource (Required) [VERIFIED]

Specifies which data source to query. Must retrieve from one source at a time.

**Valid values:**
- `sharePoint` - SharePoint Online content
- `oneDriveBusiness` - OneDrive for Business content
- `externalItem` - Copilot connectors content

**Example:**
```json
{
  "dataSource": "sharePoint"
}
```

**Note:** Interleaved results from multiple sources are not supported.

### dataSourceConfiguration (Optional) [VERIFIED]

Configuration for the data source. Currently only used for Copilot connectors.

**Structure for externalItem:**
```json
{
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

**Note:** Only applicable when `dataSource` is `externalItem`.

### filterExpression (Optional) [VERIFIED]

KQL (Keyword Query Language) expression to filter results.

**Supported operators:** `AND`, `OR`, `NOT`

**Supported properties for SharePoint/OneDrive:**
- `Author` - Document author
- `FileExtension` - File extension (e.g., "docx")
- `Filename` - Full filename
- `FileType` - File type (e.g., "pdf")
- `InformationProtectionLabelId` - Sensitivity label GUID
- `LastModifiedTime` - Last modified date
- `ModifiedBy` - Last modifier
- `Path` - URL path to site/folder
- `SiteID` - SharePoint site GUID
- `Title` - Document title

**Examples:**
```json
// Filter by author
{ "filterExpression": "Author:\"Megan Bowen\"" }

// Filter by date range
{ "filterExpression": "LastModifiedTime>= 2024-07-22 AND LastModifiedTime<= 2025-01-08" }

// Filter by file type
{ "filterExpression": "FileExtension:\"docx\" OR FileExtension:\"pdf\"" }

// Filter by path
{ "filterExpression": "path:\"https://contoso.sharepoint.com/sites/HR1/\"" }
```

**Warning:** If filterExpression has incorrect KQL syntax, the query executes with no scoping (no error returned).

### resourceMetadata (Optional) [VERIFIED]

Array of metadata fields to return for each result.

**Common values:**
- `title` - Document title
- `author` - Document author

**Example:**
```json
{
  "resourceMetadata": ["title", "author"]
}
```

### maximumNumberOfResults (Optional) [VERIFIED]

Maximum number of documents to return.

**Constraints:**
- Maximum value: 25
- Default: 10 [ASSUMED]
- Results are unordered

**Best practice:** Don't limit unless you have strict token requirements for your LLM.

**Example:**
```json
{
  "maximumNumberOfResults": "10"
}
```

## Response Structure

### retrievalResponse [VERIFIED]

Top-level response object containing retrieval results.

```json
{
  "retrievalHits": [...]
}
```

**Note:** If `retrievalHits` is empty, no relevant results were found.

### retrievalHit [VERIFIED]

Individual result item within `retrievalHits` array.

**Properties:**
- `webUrl` (string) - URL to the source document
- `resourceType` (string) - Type of resource (`listItem`, `externalItem`)
- `extracts` (array) - Text extracts from the document
- `resourceMetadata` (object) - Requested metadata fields
- `sensitivityLabel` (object) - Information protection label (SharePoint/OneDrive only)

### extracts [VERIFIED]

Array of relevant text snippets from the document.

**Properties:**
- `text` (string) - The extracted text snippet
- `relevanceScore` (number) - Cosine similarity score normalized to 0-1 range

**Note:** Extracts may be returned without relevanceScore when retrieving from Copilot connectors.

### sensitivityLabel [VERIFIED]

Information protection label applied to the document (SharePoint/OneDrive only).

**Properties:**
- `sensitivityLabelId` (string) - GUID of the label
- `displayName` (string) - Human-readable label name
- `toolTip` (string) - Label description
- `priority` (integer) - Label priority
- `color` (string) - Hex color code

### resourceMetadata [VERIFIED]

Object containing requested metadata fields.

**Example response:**
```json
{
  "resourceMetadata": {
    "title": "VPN Access",
    "author": "John Doe"
  }
}
```

## Complete Response Example

```json
{
  "retrievalHits": [
    {
      "webUrl": "https://contoso.sharepoint.com/sites/HR/VPNAccess.docx",
      "extracts": [
        {
          "text": "To configure the VPN, click the Wi-Fi icon on your corporate device and select the VPN option.",
          "relevanceScore": 0.8374363553387588
        },
        {
          "text": "You will need to sign in with 2FA to access the corporate VPN.",
          "relevanceScore": 0.7465472642498679
        }
      ],
      "resourceType": "listItem",
      "resourceMetadata": {
        "title": "VPN Access",
        "author": "John Doe"
      },
      "sensitivityLabel": {
        "sensitivityLabelId": "f71f1f74-bf1f-4e6b-b266-c777ea76e2s8",
        "displayName": "Confidential\\Any User (No Protection)",
        "toolTip": "Data is classified as Confidential but is NOT PROTECTED...",
        "priority": 4,
        "color": "#FF8C00"
      }
    }
  ]
}
```

## Batch Requests [VERIFIED]

Use the Microsoft Graph `$batch` endpoint to send multiple retrieval requests.

**Endpoint:**
```
POST https://graph.microsoft.com/v1.0/$batch
POST https://graph.microsoft.com/beta/$batch
```

**Constraints:**
- Maximum 20 requests per batch
- Each request needs unique `id` (string)

**Example Request:**
```json
{
  "requests": [
    {
      "id": "1",
      "method": "POST",
      "url": "/copilot/retrieval",
      "body": {
        "queryString": "How to setup corporate VPN?",
        "dataSource": "sharePoint"
      },
      "headers": {
        "Content-Type": "application/json"
      }
    },
    {
      "id": "2",
      "method": "POST",
      "url": "/copilot/retrieval",
      "body": {
        "queryString": "How to setup corporate VPN?",
        "dataSource": "externalItem"
      },
      "headers": {
        "Content-Type": "application/json"
      }
    }
  ]
}
```

## Error Responses

### HTTP Status Codes [VERIFIED]

- `200 OK` - Success
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Insufficient permissions
- `429 Too Many Requests` - Throttling limit exceeded

### Error Response Format [ASSUMED]

```json
{
  "error": {
    "code": "InvalidRequest",
    "message": "Description of the error",
    "innerError": {
      "date": "2026-01-29T08:00:00",
      "request-id": "..."
    }
  }
}
```

## Sources

**Primary:**
- `COPRA-IN01-SC-MSFT-APIREF`: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api/ai-services/retrieval/copilotroot-retrieval
- `COPRA-IN01-SC-MSFT-DSCONFIG`: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api/ai-services/retrieval/resources/datasourceconfiguration
- `COPRA-IN01-SC-MSFT-RETRRESP`: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api/ai-services/retrieval/resources/retrievalresponse

## Document History

**[2026-01-29 08:50]**
- Initial document created
- All 14 TOC items documented
- Complete request/response examples included
- Batch requests documented
