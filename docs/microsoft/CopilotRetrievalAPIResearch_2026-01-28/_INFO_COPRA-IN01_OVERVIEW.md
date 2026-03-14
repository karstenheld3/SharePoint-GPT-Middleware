# INFO: Copilot Retrieval API - Overview

**Doc ID**: COPRA-IN01
**Goal**: Document what the Retrieval API is, why to use it, and its architecture

**Depends on:**
- `_INFO_COPRA_SOURCES.md [COPRA-IN01]` for source URLs
- `__INFO_COPRA-IN00_TOC.md [COPRA-IN01]` for topic scope

## Summary

The Microsoft 365 Copilot Retrieval API enables generative AI solutions to retrieve relevant text chunks from SharePoint, OneDrive, and Copilot connectors without building separate vector indexes. It leverages Microsoft's pre-built semantic index that powers Microsoft 365 Copilot, providing RAG (Retrieval Augmented Generation) capabilities with built-in security trimming.

**Key Facts [VERIFIED]:**
- REST API under Microsoft Graph namespace: `POST /copilot/retrieval`
- Available in both v1.0 and beta endpoints
- Queries the same semantic index that powers Microsoft 365 Copilot
- Security trimming via RBAC - users only see content they have access to
- No data egress - content stays in Microsoft 365

**Use Cases:**
- Custom AI agents requiring M365 knowledge grounding
- Finance/legal applications needing high-precision retrieval
- Multi-source applications combining SharePoint with external connectors
- RAG pipelines without infrastructure management

## Quick Reference

- **Endpoint**: `POST https://graph.microsoft.com/v1.0/copilot/retrieval`
- **Licensing**: M365 Copilot license (included) or pay-as-you-go (preview)
- **Graph Explorer**: https://aka.ms/try_copilot_retrieval_API_overview
- **National clouds**: Global, US Government, China (21Vianet) [VERIFIED]

## What is the Copilot Retrieval API

[VERIFIED] The Microsoft 365 Copilot Retrieval API is a REST API that allows applications to ground generative AI solutions with Microsoft 365 and non-Microsoft knowledge by returning relevant text chunks from the hybrid index that powers Microsoft 365 Copilot.

**Core Capability:**
- Retrieval Augmented Generation (RAG) without data replication
- Returns text extracts with relevance scores
- Respects existing permissions, sensitivity labels, and compliance controls

**What it is NOT:**
- Not a full-text search API (use Microsoft Search for that)
- Not a document download API (returns text chunks only)
- Not a vector database you manage (Microsoft manages the index)

## Use Cases

[VERIFIED] The Retrieval API addresses these enterprise scenarios:

**Custom Knowledge Applications:**
- Ground LLM responses on organization-specific information
- Retrieve context from SharePoint, OneDrive, and external connectors
- Same grounding approach as Microsoft 365 Copilot

**Compliance-Critical Applications:**
- Finance and legal requiring high precision retrieval
- Filter to specific document libraries or content types
- Respect information barriers and access controls

**Multi-Source Applications:**
- Combine SharePoint/OneDrive with Copilot connector content
- Unified knowledge base spanning M365 and third-party repositories
- Consistent security and compliance controls across sources

## Benefits

### Manage Compliance and Safety Risks [VERIFIED]

- Built-in security and compliance features from Microsoft 365
- Data source permissions and compliance settings preserved
- No data egress - retrieval happens in place
- Prevents data leaks between clients/departments
- Permission model ensures users only access authorized content

### Solve for Relevancy and Freshness [VERIFIED]

- No data duplication means results stay fresh
- Eliminates separate, costly data pipelines
- Near real-time for user mailbox documents
- Daily updates for shared SharePoint documents
- Immediate updates for already-indexed documents

### Lower Cost of Ownership [VERIFIED]

Eliminates need to build:
- Search provider management
- Crawlers and data connectors
- Data storage infrastructure
- Content parsers
- Indexing pipelines
- Security layer

## Semantic Index Architecture

[VERIFIED] The Retrieval API queries Microsoft's pre-built semantic index, not a just-in-time embedding system.

### What is the Semantic Index

Microsoft 365 Copilot maps organizational data into an advanced lexical and semantic index:
- **Vectorized indices**: Numerical representations of words, content, relationships
- **Multi-dimensional spaces**: Similar data points clustered together
- **Hybrid retrieval**: Combines semantic understanding with lexical matching

### Capabilities Enabled

- Understanding relationships between word forms (tech, technology, technologies)
- Capturing synonyms and intent (USA, U.S.A, United States)
- Identifying related assets based on semantic meaning
- Fast similarity search based on vector distance

### Index Levels

**Tenant-Level Index [VERIFIED]:**
- Automatically created for every M365 Copilot subscription
- Organization-wide index from text-based SharePoint Online files
- No administrative involvement required
- Results gated by RBAC
- Cannot be disabled

**User-Level Index [VERIFIED]:**
- Personalized index of user's working set
- Includes emails, documents created/commented/shared
- Being expanded over time by Microsoft

## Relationship to Microsoft Graph

[VERIFIED] The Retrieval API is part of the Microsoft Graph namespace:

**Endpoint Structure:**
```
https://graph.microsoft.com/v1.0/copilot/retrieval
https://graph.microsoft.com/beta/copilot/retrieval
```

**Integration:**
- Uses same authentication as other Graph APIs
- Same token acquisition process
- Same permission model (delegated and application)

## Copilot APIs vs Microsoft Graph APIs

[VERIFIED] Key distinction:

**Microsoft Graph APIs:**
- Provide CRUD operations on Microsoft 365 data
- Available under standard Microsoft 365 license terms
- For manipulating and accessing data

**Copilot APIs:**
- Deliver AI-powered capabilities built on Microsoft 365 data
- Require Microsoft 365 Copilot license
- For AI reasoning over data

The Retrieval API is a Copilot API - it provides AI-enhanced retrieval, not just data access.

## National Cloud Deployments

[VERIFIED] The Retrieval API is available in Microsoft's national cloud deployments:
- Global (commercial)
- US Government (GCC, GCC High, DoD)
- China (21Vianet)

Endpoint URLs vary by cloud. See Microsoft Graph national cloud documentation for specific URLs.

## Graph Explorer Integration

[VERIFIED] You can test the Retrieval API directly in Graph Explorer:
- URL: https://aka.ms/try_copilot_retrieval_API_overview
- Requires sign-in with M365 Copilot license
- Consent to required permissions (Files.Read.All, Sites.Read.All)

## Sources

**Primary:**
- `COPRA-IN01-SC-MSFT-OVERVIEW`: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api/ai-services/retrieval/overview
- `COPRA-IN01-SC-MSFT-APISOVW`: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/copilot-apis-overview
- `COPRA-IN01-SC-MSFT-SEMIDX`: https://learn.microsoft.com/en-us/microsoftsearch/semantic-index-for-copilot

**Related:**
- `MSCON-IN02-CRA`: Prior research on semantic index architecture

## Document History

**[2026-01-29 08:40]**
- Initial document created
- All 8 TOC items documented with [VERIFIED] labels
- Semantic index architecture section added from prior research
