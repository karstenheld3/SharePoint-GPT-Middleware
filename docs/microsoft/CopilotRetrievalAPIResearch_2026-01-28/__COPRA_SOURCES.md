# INFO: Copilot Retrieval API Sources

**Doc ID**: COPRA-SOURCES
**Goal**: Inventory of all official documentation sources for Copilot Retrieval API research

## Summary

The Microsoft 365 Copilot Retrieval API is a REST API under the Microsoft Graph namespace (`/copilot/retrieval`) that enables semantic search over SharePoint, OneDrive, and Copilot connectors content. It provides RAG (Retrieval Augmented Generation) capabilities without requiring separate vector index management.

**Key Facts [VERIFIED]:**
- Single endpoint: `POST https://graph.microsoft.com/v1.0/copilot/retrieval` (also `/beta`)
- Requires M365 Copilot license OR pay-as-you-go (preview)
- Permissions: Files.Read.All + Sites.Read.All (SharePoint/OneDrive), ExternalItem.Read.All (connectors)
- Data sources: SharePoint, OneDrive, Copilot connectors (one at a time)
- Max 25 results per request, 200 requests/user/hour
- Query string limit: 1,500 characters
- Supports KQL filtering on 10 properties

## Primary Sources (API Documentation)

### Core Documentation

- **COPRA-IN01-SC-MSFT-OVERVIEW**: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api/ai-services/retrieval/overview
  - Retrieval API overview, capabilities, licensing, best practices, limitations
  - Last updated: 2026-01-23

- **COPRA-IN01-SC-MSFT-APIREF**: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api/ai-services/retrieval/copilotroot-retrieval
  - API reference: HTTP request, parameters, response format, examples
  - 7 examples covering SharePoint, OneDrive, connectors, batching, filtering

- **COPRA-IN01-SC-MSFT-APIOVER**: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/copilot-apis-overview
  - Copilot APIs overview: All 8 APIs (Retrieval, Search, Chat, etc.)
  - Licensing requirements, REST integration

- **COPRA-IN01-SC-MSFT-SEARCH**: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api/ai-services/search/overview
  - Search API overview (preview, beta only)
  - OneDrive-only hybrid search, returns documents (not extracts)
  - Used for comparison with Retrieval API

### SDK Documentation

- **COPRA-IN01-SC-MSFT-SDKLIBS**: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/sdks/api-libraries
  - Client libraries for C#, Python, TypeScript
  - NuGet: Microsoft.Agents.M365Copilot, PyPI: microsoft-agents-m365copilot, npm: @microsoft/agents-m365copilot
  - Full code examples for all three languages

- **COPRA-IN01-SC-GITHUB-SDK**: https://github.com/microsoft/Agents-M365Copilot
  - Open-source SDK repository
  - Subfolders: /dotnet, /typescript, /python

### Resource Types

- **COPRA-IN01-SC-MSFT-DSCONFIG**: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api/ai-services/retrieval/resources/datasourceconfiguration
  - dataSourceConfiguration resource type
  - Used to specify Copilot connector connection IDs

- **COPRA-IN01-SC-MSFT-RETRRESP**: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api/ai-services/retrieval/resources/retrievalresponse
  - retrievalResponse resource type
  - Contains retrievalHits array

### Licensing and Pricing

- **COPRA-IN01-SC-MSFT-PAYGO**: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api/ai-services/retrieval/paygo-retrieval
  - Pay-as-you-go overview and pricing (preview)
  - For non-Copilot licensed users

- **COPRA-IN01-SC-MSFT-COSTCON**: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/cost-considerations
  - Licensing and cost considerations for Copilot extensibility

## Secondary Sources (Related Documentation)

### Semantic Index

- **COPRA-IN01-SC-MSFT-SEMIDX**: https://learn.microsoft.com/en-us/microsoftsearch/semantic-index-for-copilot
  - Semantic indexing architecture for M365 Copilot
  - Pre-built, persistent index (not just-in-time)
  - Tenant-level and user-level indices

### Authentication

- **COPRA-IN01-SC-MSFT-AUTH**: https://learn.microsoft.com/en-us/graph/auth/auth-concepts
  - Microsoft Graph authentication and authorization
  - Token acquisition for API calls

- **COPRA-IN01-SC-MSFT-AUTHPROV**: https://learn.microsoft.com/en-us/graph/sdks/choose-authentication-providers
  - Authentication provider selection guide
  - DeviceCodeCredential, ClientSecretCredential, etc.

### Related APIs

- **COPRA-IN01-SC-MSFT-SEARCH**: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api/ai-services/search/overview
  - Copilot Search API (preview) - alternative to Retrieval API

- **COPRA-IN01-SC-MSFT-CHAT**: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api/ai-services/chat/overview
  - Copilot Chat API (preview) - for conversational experiences

- **COPRA-IN01-SC-MSFT-CONNECTORS**: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/overview-copilot-connector
  - Copilot connectors overview - for indexing external content

### KQL Reference

- **COPRA-IN01-SC-MSFT-KQL**: https://learn.microsoft.com/en-us/sharepoint/dev/general-development/keyword-query-language-kql-syntax-reference
  - Keyword Query Language syntax reference
  - Used in filterExpression parameter

## Existing Research

- **MSCON-IN02-CRA**: `_Sessions/_2026-01-14_MicrosoftAIConnectorsResearch/INFO_COPILOT_RETRIEVAL_API.md`
  - Prior research on semantic index architecture
  - Covers: pre-built index, update frequency, security model
  - Gap: Does not cover API endpoints, parameters, SDK examples

## Topic Categories for TOC

Based on source analysis, the following topic categories are identified:

1. **Overview and Architecture** - What it is, how it works, semantic index
2. **API Reference** - Endpoint, request/response, parameters
3. **Data Sources** - SharePoint, OneDrive, Copilot connectors
4. **Filtering (KQL)** - filterExpression syntax, supported properties
5. **Authentication** - Permissions, token acquisition, app registration
6. **SDK Examples** - C#, Python, TypeScript client libraries
7. **Licensing** - M365 Copilot license vs pay-as-you-go
8. **Limitations** - Throttling, file size limits, unsupported content
9. **Best Practices** - Query optimization, result handling

## Document History

**[2026-01-29 08:15]**
- Initial sources document created
- 20+ official Microsoft Learn URLs catalogued
- 9 topic categories identified for TOC
- Prior research gap identified (API endpoints not covered)
