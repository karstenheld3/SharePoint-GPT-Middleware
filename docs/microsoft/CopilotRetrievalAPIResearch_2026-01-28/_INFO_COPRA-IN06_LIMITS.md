# INFO: Copilot Retrieval API - Licensing, Throttling, and Limitations

**Doc ID**: COPRA-IN01
**Goal**: Document licensing models, rate limits, and known limitations

**Depends on:**
- `_INFO_COPRA_SOURCES.md [COPRA-IN01]` for source URLs
- `__INFO_COPRA-IN00_TOC.md [COPRA-IN01]` for topic scope

## Summary

The Retrieval API requires either a Microsoft 365 Copilot license (included) or pay-as-you-go billing (preview). It has specific throttling limits, file size restrictions, and content type limitations that affect what can be retrieved.

**Key Facts [VERIFIED]:**
- M365 Copilot license: Full access included
- Pay-as-you-go: SharePoint and connectors only (no OneDrive)
- Rate limit: 200 requests/user/hour
- Batch limit: 20 requests per batch
- Max results: 25 per request
- Query limit: 1,500 characters

**Use Cases:**
- Choosing licensing model for your application
- Designing within throttling constraints
- Understanding content coverage limitations

## Quick Reference

**Licensing:**
- M365 Copilot license: All features included
- Pay-as-you-go (preview): Tenant-level only, no OneDrive

**Throttling:**
- 200 requests/user/hour
- 20 requests/batch
- 25 max results
- 1,500 char query limit

**File Limits:**
- 512 MB: PDF, PPTX, DOCX
- 150 MB: All other types

## Licensing Models

### Microsoft 365 Copilot License (Included) [VERIFIED]

**Access:** Full Retrieval API access at no extra cost

**Requirements:**
- Microsoft 365 E3 or E5 subscription (or equivalent)
- Microsoft 365 Copilot add-on license per user

**Features:**
- SharePoint retrieval
- OneDrive retrieval (user-level)
- Copilot connectors retrieval
- All filtering capabilities

**Terms:** By using the API, you agree to the Microsoft 365 Copilot APIs Terms of Use (preview).

### Pay-As-You-Go (Preview) [VERIFIED]

**Access:** Usage-based billing for non-Copilot licensed users

**Availability:**
- Currently in preview
- Tenant-level data sources only

**Supported sources:**
- SharePoint Online
- Copilot connectors

**Not supported:**
- OneDrive for Business (user-level sources)

**Terms:** Separate terms of use apply (Microsoft 365 Copilot Retrieval API pay-as-you-go Terms of Use).

**Use case:** Organizations wanting to test or use limited retrieval without full Copilot licensing.

### Microsoft Foundry Integration [VERIFIED]

Non-Copilot licensed users with pay-as-you-go enabled can use the SharePoint tool in Microsoft Foundry via pay-as-you-go consumption.

### Licensing Decision Guide

**Choose M365 Copilot license when:**
- Users need OneDrive access
- Heavy API usage expected
- Full Copilot features desired
- Predictable costs preferred

**Choose pay-as-you-go when:**
- Testing/evaluation phase
- Low-volume usage
- SharePoint/connectors only needed
- Variable usage patterns

## Throttling Limits

### Request Limits [VERIFIED]

| Limit | Value | Scope |
|-------|-------|-------|
| Requests per hour | 200 | Per user |
| Requests per batch | 20 | Per batch call |
| Maximum results | 25 | Per request |
| Query string length | 1,500 | Characters |

### Throttling Behavior [VERIFIED]

When limits are exceeded:
- HTTP 429 (Too Many Requests) returned
- Retry-After header indicates wait time [ASSUMED]

### Mitigation Strategies

**Reduce request frequency:**
- Cache results when appropriate
- Batch related queries
- Implement exponential backoff

**Optimize queries:**
- Use specific filters to reduce result sets
- Avoid overly broad queries
- Don't request unnecessary metadata

**Batch effectively:**
- Group related queries (max 20)
- Use batch endpoint for multiple data sources

## File Limitations

### File Size Limits [VERIFIED]

**Large file support (up to 512 MB):**
- `.pdf` - PDF documents
- `.pptx` - PowerPoint presentations
- `.docx` - Word documents

**Standard limit (up to 150 MB):**
- All other supported file extensions

**Oversized files:**
- Files exceeding limits are not indexed
- Will not appear in retrieval results

### Semantic vs Lexical Retrieval [VERIFIED]

**Semantic + Lexical (hybrid):**
- `.doc`, `.docx` - Word documents
- `.pptx` - PowerPoint presentations
- `.pdf` - PDF documents
- `.aspx` - SharePoint pages
- `.one` - OneNote sections

**Lexical only:**
- All other text-based file extensions
- Less accurate for conceptual queries

### Table Content Limitations [VERIFIED]

Text in tables can only be retrieved from:
- `.doc` files
- `.docx` files
- `.pptx` files

Tables in other formats (PDF, etc.) may not be fully indexed.

### Unsupported Content [VERIFIED]

**Not indexed or retrieved:**
- Images and charts (non-textual content)
- Content in other visual elements
- Files excluded by DLP policies
- Non-searchable SharePoint sites
- Highly sensitive labeled content

## Semantic Index Limitations [VERIFIED]

The Retrieval API inherits all limitations of the Microsoft 365 Copilot semantic index:

**Index scope:**
- Tenant-level: SharePoint Online text-based files
- User-level: Mailbox and interacted documents

**Excluded content:**
- DLP-excluded files
- Non-searchable sites
- Sensitivity-labeled content (confidential/highly confidential)

**Update delays:**
- New SharePoint docs (shared): Daily indexing
- User mailbox: Near real-time
- Updated docs: Immediate

## Best Practices

### Query Optimization [VERIFIED]

**Do:**
- Provide as much context as possible
- Use single, clear sentences
- Include relevant keywords
- Spell context-rich words correctly

**Don't:**
- Use generic, broad queries
- Send very short queries
- Include spelling errors in key terms

### Result Handling [VERIFIED]

**Best practices:**
- Send ALL extracts to your LLM (results are unordered)
- Don't limit `maximumNumberOfResults` unless token-constrained
- Handle empty `retrievalHits` gracefully (no results found)
- Check for missing `relevanceScore` (connectors may omit)

### Filter Expression [VERIFIED]

**Best practices:**
- Use Details pane path, not browser URL for Path filter
- Test filter syntax separately before production
- Remember: invalid KQL runs without scoping (no error)
- Combine filters with AND/OR for precision

### Error Handling [ASSUMED]

**Implement:**
- Retry logic with exponential backoff
- Handle 429 responses gracefully
- Log failed requests for debugging
- Validate inputs before API calls

## Sources

**Primary:**
- `COPRA-IN01-SC-MSFT-OVERVIEW`: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api/ai-services/retrieval/overview
- `COPRA-IN01-SC-MSFT-PAYGO`: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api/ai-services/retrieval/paygo-retrieval
- `COPRA-IN01-SC-MSFT-COSTCON`: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/cost-considerations

## Document History

**[2026-01-29 09:30]**
- Initial document created
- All 15 TOC items documented
- Licensing comparison included
- Best practices from official docs
