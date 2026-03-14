# Session Notes

**Doc ID**: 2026-03-14_SharePointAuthMechanisms-NOTES

## Initial Request

````text
Currently we have just 1 authentication method for the crawler to connect to SharePoint sites: Via Client ID and Certificate.

Problem: The client has disabled this

Solution:

1) We need a second authentication mechanism via managed identity
2) If the cawler fails to connect to SharePoint I want to explore possibilities to log in manually via personal account

Create a new session and these 2 problems.

First we have to implement 1)
Then we explore and implement 2)
````

## Session Info

- **Started**: 2026-03-14
- **Goal**: Add managed identity authentication for SharePoint crawler; explore personal account login as fallback
- **Operation Mode**: IMPL-CODEBASE
- **Output Location**: src/

## Current Phase

**Phase**: EXPLORE
**Workflow**: (pending assessment)
**Assessment**: (pending)

## Agent Instructions

- Research Azure Managed Identity authentication for SharePoint
- Maintain backward compatibility with existing certificate authentication
- Document findings in INFO document before implementation

## Key Decisions

(none yet)

## Important Findings

(none yet)

## Topic Registry

- `SPAUTH` - SharePoint authentication mechanisms
- `CRWL` - Crawler operations

## Files to Read on Session Load

- `docs/V2_INFO_IMPLEMENTATION_PATTERNS.md`
- `docs/routers_v2/_V2_SPEC_ROUTERS.md`
- `docs/routers_v2/_V2_SPEC_CRAWLER.md`
- `docs/routers_v2/_V2_IMPL_CRAWLER.md`
- `docs/routers_v2/_V2_IMPL_CRAWLER_SELFTEST.md`

## Significant Prompts Log

(none yet)
