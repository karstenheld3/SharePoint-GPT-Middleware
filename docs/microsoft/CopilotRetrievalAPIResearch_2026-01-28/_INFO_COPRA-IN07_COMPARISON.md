# INFO: Copilot APIs Comparison

**Doc ID**: COPRA-IN01
**Goal**: Compare Retrieval API with other Copilot APIs to clarify when to use which

**Depends on:**
- `_INFO_COPRA_SOURCES.md [COPRA-IN01]` for official documentation URLs
- `_INFO_COPRA-IN01_OVERVIEW.md [COPRA-IN01]` for Retrieval API details

## Summary

Microsoft 365 offers **8 Copilot APIs** under the `/copilot` namespace. The **Retrieval API** and **Search API** are both for content discovery but serve different purposes. This document clarifies when to use each.

**Key Distinction [VERIFIED]:**
- **Retrieval API** - Returns text **extracts** (chunks) for RAG/grounding
- **Search API** - Returns **documents** (files) for discovery

**Quick Decision:**
- Need text chunks for LLM grounding? → **Retrieval API**
- Need to find and list documents? → **Search API**

## Microsoft 365 Copilot APIs Family

The Copilot APIs provide access to components that power Microsoft 365 Copilot experiences. [VERIFIED]

**Available APIs (8 total):**

1. **Retrieval API** (v1.0 + beta)
   - Purpose: Semantic search returning text extracts for RAG
   - Data sources: SharePoint, OneDrive, Copilot connectors
   - Status: Generally available

2. **Search API** (beta only, preview)
   - Purpose: Hybrid search returning documents for discovery
   - Data sources: OneDrive only (SharePoint planned)
   - Status: Preview

3. **Chat API** (beta only, preview)
   - Purpose: Conversational AI experiences
   - Status: Preview

4. **Interaction Export API**
   - Purpose: Export Copilot interaction data
   - Status: Available

5. **Change Notifications API** (preview)
   - Purpose: Subscribe to Copilot interaction changes
   - Status: Preview

6. **Meeting Insights API**
   - Purpose: AI-generated meeting insights and transcriptions
   - Status: Available

7. **Copilot Usage Reports API**
   - Purpose: Admin reports on Copilot usage
   - Status: Available

8. **Package Management API**
   - Purpose: Manage Copilot extensions and packages
   - Status: Available

**Source:** [COPRA-IN01-SC-MSFT-APIOVER]

## Retrieval API vs Search API Comparison

### Purpose and Use Cases

**Retrieval API** [VERIFIED]:
- Designed for **RAG (Retrieval Augmented Generation)** pipelines
- Returns **text extracts** (chunks) with relevance scores
- Optimized for **context recall** - finding relevant passages
- Use case: Grounding LLM responses with enterprise data

**Search API** [VERIFIED]:
- Designed for **document discovery**
- Returns **file references** with metadata and previews
- Optimized for **document ranking** - finding relevant files
- Use case: Building search interfaces, file browsers

### Data Sources Supported

**Retrieval API** [VERIFIED]:
- SharePoint Online
- OneDrive for Business
- Copilot connectors (external data)
- One data source per request (no interleaving)

**Search API** [VERIFIED]:
- OneDrive for work or school only (currently)
- SharePoint and Copilot connectors **not yet supported**
- Additional data sources planned for future releases

### Response Format

**Retrieval API Response:**
```json
{
  "retrievalHits": [
    {
      "resource": { "id": "...", "webUrl": "..." },
      "relevanceScore": 0.85,
      "extracts": [
        { "text": "Relevant text passage...", "startIndex": 100 }
      ],
      "sensitivityLabel": { "id": "...", "name": "Confidential" }
    }
  ]
}
```
- Returns: Text extracts (passages) from within documents
- Includes: relevanceScore (0-1), sensitivityLabel
- Max results: 25 per request

**Search API Response:**
```json
{
  "hits": [
    {
      "resource": {
        "id": "...",
        "name": "Document.docx",
        "webUrl": "...",
        "size": 12345
      },
      "preview": "First 200 characters of document...",
      "rank": 1
    }
  ]
}
```
- Returns: File/document references
- Includes: File metadata, preview text
- Max results: Configurable

### Licensing Differences

**Retrieval API** [VERIFIED]:
- M365 Copilot license: Full access (all data sources)
- Pay-as-you-go (preview): SharePoint and connectors only (no OneDrive)

**Search API** [VERIFIED]:
- M365 Copilot license: Required
- Pay-as-you-go: Not mentioned in docs (likely not available)

### Permissions

**Retrieval API:**
- Files.Read.All + Sites.Read.All (SharePoint/OneDrive)
- ExternalItem.Read.All (Copilot connectors)

**Search API:**
- Files.Read.All (OneDrive)

## When to Use Each API

### Use Retrieval API When:

- Building **RAG pipelines** that need text chunks for LLM context
- Creating **custom agents** that answer questions from enterprise data
- Need **relevance scores** to rank extracted passages
- Working with **SharePoint** or **Copilot connectors** data
- Building **Azure AI Foundry** agents with SharePoint grounding
- Need **sensitivity label** information on content

### Use Search API When:

- Building **document search** interfaces
- Creating **file discovery** experiences
- Need **file metadata** (size, modified date, author)
- Only working with **OneDrive** content
- Building **document browsers** or file managers
- Want **document-level** results, not text extracts

## Decision Matrix

**Choose Retrieval API if:**
- Output needed: Text passages/chunks
- Use case: LLM grounding, Q&A, RAG
- Data source: SharePoint, OneDrive, or connectors
- Response: Extracts with relevance scores

**Choose Search API if:**
- Output needed: Document/file references
- Use case: Search UI, file browser, discovery
- Data source: OneDrive only (currently)
- Response: Files with metadata and previews

**Choose Neither (Use Microsoft Graph Search) if:**
- Need broader search across M365 (mail, calendar, people)
- Don't need semantic/AI capabilities
- Need application permissions (service-to-service)

## Limitations Comparison

| Aspect | Retrieval API | Search API |
|--------|--------------|------------|
| Status | GA (v1.0) | Preview (beta only) |
| SharePoint | Yes | No (planned) |
| OneDrive | Yes | Yes |
| Connectors | Yes | No (planned) |
| Returns | Text extracts | Documents |
| Pay-as-you-go | Yes (limited) | No |

## Sources

- **COPRA-IN01-SC-MSFT-APIOVER**: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/copilot-apis-overview
- **COPRA-IN01-SC-MSFT-SEARCH**: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api/ai-services/search/overview
- **COPRA-IN01-SC-MSFT-OVERVIEW**: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api/ai-services/retrieval/overview

## Document History

**[2026-01-29 09:50]**
- Initial document created
- Addresses COPRA-PR-006 (Search API vs Retrieval API comparison)
- All 8 Copilot APIs documented
- Decision matrix added
