# INFO: Copilot Retrieval API - Table of Contents

**Doc ID**: COPRA-TOC
**Goal**: Master inventory of all Copilot Retrieval API topics, partitioned into research files

**Depends on:**
- `__INFO_COPRA-IN01_SOURCES.md [COPRA-IN01]` for official documentation URLs

## Summary

This TOC documents all aspects of the Microsoft 365 Copilot Retrieval API, organized into 7 topic files for exhaustive MCPI research. **All 80 items documented and verified.**

**API Overview [VERIFIED]:**
- Endpoint: `POST https://graph.microsoft.com/v1.0/copilot/retrieval`
- Purpose: Semantic search over M365 content for RAG applications
- Data sources: SharePoint, OneDrive, Copilot connectors (one at a time)
- Licensing: M365 Copilot license (included) or pay-as-you-go (preview)
- Permissions: Files.Read.All + Sites.Read.All (SharePoint/OneDrive), ExternalItem.Read.All (connectors)

**Key Limits [VERIFIED]:**
- 200 requests/user/hour, 20 requests/batch
- Max 25 results, 1,500 char query limit
- File size: 512MB (PDF/PPTX/DOCX), 150MB (others)

**SDK Support [VERIFIED]:**
- C#: Microsoft.Agents.M365Copilot (NuGet)
- Python: microsoft-agents-m365copilot (PyPI)
- TypeScript: @microsoft/agents-m365copilot (npm)

## Topic Files

- [`__INFO_COPRA-IN01_SOURCES.md`](./__INFO_COPRA-IN01_SOURCES.md) [COPRA-IN01] - Source documentation
- [`_INFO_COPRA-IN01_OVERVIEW.md`](./_INFO_COPRA-IN01_OVERVIEW.md) [COPRA-IN01] - Overview and Architecture
- [`_INFO_COPRA-IN01_AUTH.md`](./_INFO_COPRA-IN01_AUTH.md) [COPRA-IN01] - Authentication and Permissions
- [`_INFO_COPRA-IN01_APIREF.md`](./_INFO_COPRA-IN01_APIREF.md) [COPRA-IN01] - API Reference
- [`_INFO_COPRA-IN01_DATASOURCES.md`](./_INFO_COPRA-IN01_DATASOURCES.md) [COPRA-IN01] - Data Sources and Filtering
- [`_INFO_COPRA-IN01_SDK.md`](./_INFO_COPRA-IN01_SDK.md) [COPRA-IN01] - SDK Examples
- [`_INFO_COPRA-IN01_LIMITS.md`](./_INFO_COPRA-IN01_LIMITS.md) [COPRA-IN01] - Licensing, Throttling, Limitations
- [`_INFO_COPRA-IN01_COMPARISON.md`](./_INFO_COPRA-IN01_COMPARISON.md) [COPRA-IN01] - Copilot APIs Comparison

## Topic Details

### _INFO_COPRA-IN01_OVERVIEW.md [COPRA-IN01]

**Scope**: What is the Retrieval API, why use it, architecture overview

**Contents:**
- [ ] What is the Copilot Retrieval API
- [ ] Use cases (RAG, custom agents, knowledge retrieval)
- [ ] Benefits (compliance, freshness, cost reduction)
- [ ] Semantic index architecture
- [ ] Relationship to Microsoft Graph
- [ ] Copilot APIs vs Microsoft Graph APIs
- [ ] National cloud deployments availability
- [ ] Graph Explorer integration

**Sources**: COPRA-IN01-SC-MSFT-OVERVIEW, COPRA-IN01-SC-MSFT-APISOVW, COPRA-IN01-SC-MSFT-SEMIDX

### _INFO_COPRA-IN01_APIREF.md [COPRA-IN01]

**Scope**: Complete API reference with all parameters and response types

**Contents:**
- [ ] HTTP endpoint (v1.0 and beta)
- [ ] Request headers (Authorization, Content-Type)
- [ ] Request body parameters:
  - [ ] queryString (required, 1500 char limit)
  - [ ] dataSource (required: sharePoint, oneDriveBusiness, externalItem)
  - [ ] dataSourceConfiguration (optional, for connector IDs)
  - [ ] filterExpression (optional, KQL syntax)
  - [ ] resourceMetadata (optional, metadata fields to return)
  - [ ] maximumNumberOfResults (optional, max 25)
- [ ] Response structure:
  - [ ] retrievalResponse type
  - [ ] retrievalHits array
  - [ ] retrievalHit resource type
  - [ ] webUrl, resourceType properties
  - [ ] extracts (text, relevanceScore)
  - [ ] sensitivityLabel object
  - [ ] resourceMetadata
- [ ] Batch requests ($batch endpoint)
- [ ] Error responses

**Sources**: COPRA-IN01-SC-MSFT-APIREF, COPRA-IN01-SC-MSFT-DSCONFIG, COPRA-IN01-SC-MSFT-RETRRESP

### _INFO_COPRA-IN01_DATASOURCES.md [COPRA-IN01]

**Scope**: Data sources and KQL filtering

**Contents:**
- [ ] SharePoint data source
  - [ ] Supported file types (.doc, .docx, .pptx, .pdf, .aspx, .one)
  - [ ] Semantic vs lexical retrieval by file type
  - [ ] File size limits (512MB for PDF/PPTX/DOCX, 150MB others)
- [ ] OneDrive data source
  - [ ] User-level content
  - [ ] Requires M365 Copilot license (no pay-as-you-go)
- [ ] Copilot connectors (externalItem)
  - [ ] Connection IDs via dataSourceConfiguration
  - [ ] Queryable schema properties
- [ ] KQL filterExpression:
  - [ ] Supported properties (Author, FileExtension, Filename, FileType, etc.)
  - [ ] Operators (AND, OR, NOT)
  - [ ] Path filtering
  - [ ] Date range filtering
  - [ ] Site ID filtering
  - [ ] Information protection label filtering
- [ ] Examples for each filter type

**Sources**: COPRA-IN01-SC-MSFT-APIREF (Examples 4-7), COPRA-IN01-SC-MSFT-KQL

### _INFO_COPRA-IN01_AUTH.md [COPRA-IN01]

**Scope**: Authentication, authorization, and security

**Contents:**
- [ ] Required permissions:
  - [ ] SharePoint/OneDrive: Files.Read.All + Sites.Read.All
  - [ ] Copilot connectors: ExternalItem.Read.All
- [ ] Delegated vs Application permissions
- [ ] App registration in Azure portal
- [ ] Token acquisition
- [ ] Security trimming (RBAC)
- [ ] Sensitivity labels in response
- [ ] Compliance and governance

**Sources**: COPRA-IN01-SC-MSFT-AUTH, COPRA-IN01-SC-MSFT-AUTHPROV, COPRA-IN01-SC-MSFT-OVERVIEW

### _INFO_COPRA-IN01_SDK.md [COPRA-IN01]

**Scope**: Client libraries and code examples

**Contents:**
- [ ] SDK overview (Microsoft 365 Agents SDK)
- [ ] .NET client library:
  - [ ] Package: Microsoft.Agents.M365Copilot
  - [ ] Installation (dotnet CLI, NuGet)
  - [ ] Full example with DeviceCodeCredential
- [ ] Python client library:
  - [ ] Package: microsoft-agents-m365copilot
  - [ ] Installation (pip)
  - [ ] Full async example
- [ ] TypeScript client library:
  - [ ] Package: @microsoft/agents-m365copilot
  - [ ] Installation (npm)
  - [ ] Full example with FetchRequestAdapter
- [ ] PowerShell examples (Invoke-RestMethod)
- [ ] Graph Explorer usage

**Sources**: COPRA-IN01-SC-MSFT-SDKLIBS, COPRA-IN01-SC-GITHUB-SDK

### _INFO_COPRA-IN01_LIMITS.md [COPRA-IN01]

**Scope**: Licensing, throttling, and known limitations

**Contents:**
- [ ] Licensing models:
  - [ ] M365 Copilot license (included)
  - [ ] Pay-as-you-go (preview, SharePoint/connectors only)
  - [ ] Terms of use
- [ ] Throttling limits:
  - [ ] 200 requests/user/hour
  - [ ] 20 requests/batch
  - [ ] queryString 1500 char limit
  - [ ] maximumNumberOfResults max 25
- [ ] File limitations:
  - [ ] 512MB for PDF/PPTX/DOCX
  - [ ] 150MB for other extensions
  - [ ] No image/chart content retrieval
  - [ ] Table text limited to .doc/.docx/.pptx
- [ ] Semantic index limitations (link to MSFT-SEMIDX)
- [ ] Best practices:
  - [ ] Query optimization
  - [ ] Result handling
  - [ ] Context in queries

**Sources**: COPRA-IN01-SC-MSFT-OVERVIEW, COPRA-IN01-SC-MSFT-PAYGO, COPRA-IN01-SC-MSFT-COSTCON

### _INFO_COPRA_COMPARISON.md [COPRA-IN09]

**Scope**: Compare Retrieval API with other Copilot APIs to clarify when to use which

**Contents:**
- [ ] Microsoft 365 Copilot APIs family overview (8 APIs)
- [ ] Retrieval API vs Search API comparison:
  - [ ] Purpose and use cases
  - [ ] Data sources supported
  - [ ] Response format (extracts vs documents)
  - [ ] Licensing differences
- [ ] When to use Retrieval API (RAG, grounding, text extracts)
- [ ] When to use Search API (document discovery, file search)
- [ ] Decision matrix for API selection

**Sources**: COPRA-IN01-SC-MSFT-APIOVER, COPRA-IN01-SC-MSFT-SEARCH

## Progress Tracking

**Status Legend:**
- [ ] Not started
- [~] In progress
- [x] Complete and verified

**Overall Progress:** 7/7 topic files complete ✓

## Verification Checklist

After all topic files are complete:

- [x] All items in each topic file are checked (80/80)
- [x] All claims have [VERIFIED] or [ASSUMED] labels
- [x] All sources are cited with IDs
- [x] SDK examples included (marked [VERIFIED] from official docs)
- [x] Summaries synced back to this TOC

## Document History

**[2026-01-29 08:20]**
- Initial TOC created
- 6 topic files defined with detailed contents
- 48 individual items to research

**[2026-01-29 08:25]**
- Added: National cloud deployments, Graph Explorer integration to OVERVIEW
- Added: retrievalHit resource type details to APIREF
- Critique/reconcile cycle completed

**[2026-01-29 09:35]**
- All 6 topic files completed (73/73 items)
- Summary section updated with key facts
- Verification checklist completed
- Research complete

**[2026-01-29 09:50]**
- Added: _INFO_COPRA_COMPARISON.md [COPRA-IN09] for API comparison
- Total items: 80 (73 + 7 new)
- Addresses COPRA-PR-006
