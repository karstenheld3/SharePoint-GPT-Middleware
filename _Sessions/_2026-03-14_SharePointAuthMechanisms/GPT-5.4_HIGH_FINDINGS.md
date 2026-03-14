# Findings: SharePoint Authentication Session Review

## Context

- **Session folder**: `_Sessions/_2026-03-14_SharePointAuthMechanisms/`
- **Reviewed documents**:
  - `_INFO_SPAUTH_REQUIREMENTS.md [SPAUTH-IN10]`
  - `_INFO_SPAUTH_TOKEN_SHARING.md [SPAUTH-IN11]`
- **Cross-checked against code**:
  - `src/routers_v2/common_sharepoint_functions_v2.py`
  - `src/routers_v2/crawler.py`
  - `src/routers_v2/common_security_scan_functions_v2.py`
  - `src/app.py`
  - Supporting V2 router/spec documents

## Session-Load Summary

Read 11 `.md` files (1 priority), 7 code files (7 `.py`). Mode: SINGLE-PROJECT + SINGLE-VERSION + SESSION-MODE

## Executive Assessment

- **Overall**: The session is generally on track for the original goal, but the current design has expanded beyond the minimum scope needed to unblock the client.
- **What is on track**:
  - Keep existing certificate authentication for current clients
  - Add Managed Identity as the primary new app-only mechanism
  - Avoid silent auto-failover
  - Use a single default/override mechanism for non-user-token requests
- **What is drifting**:
  - The design now includes a broader multi-auth platform: Device Code, Interactive Browser, On-Behalf-Of, auth switching, token sharing, new endpoints, and support for a future separate SPA
- **Conclusion**: Good research foundation, but the scope should be reduced before implementation starts

## Initial Goal vs Current Design

## Initial Goal From Session Notes

1. Implement Managed Identity authentication
2. After that, explore manual/personal-account login fallback

## Current Document Direction

The current research/design direction now includes:

- Managed Identity
- Certificate
- Device Code
- Interactive Browser
- On-Behalf-Of
- Global auth override state
- Cross-worker token sharing
- New auth management endpoints
- New auth UI flows
- Separate SPA architecture support

## Assessment

- **Yes**: The work still supports the initial goal
- **No**: The work is no longer minimal for the initial goal
- **Risk**: Implementation could become an auth-platform project instead of a targeted unblock for the client

## What Is Solid

- **Managed Identity as primary new mechanism**
  - This is aligned with the original blocker and should remain the first implementation target.

- **Certificate support retained**
  - This matches the requirement that certificate auth remains valid for other clients.

- **No automatic failover**
  - This is a good decision. It avoids hard-to-debug runtime behavior and hidden privilege changes.

- **Need for auth abstraction**
  - The code currently calls `connect_to_site_using_client_id_and_certificate()` directly in multiple places. A central auth abstraction is justified.

## Important Gaps

- **Admin authorization model is missing**
  - The docs define auth switching, override files, Device Code initiation, and reset behavior, but do not define who is allowed to perform those actions.
  - This is a major product and security gap.

- **Graph authentication scope is not fully addressed**
  - Current crawler-related code is not only SharePoint REST.
  - `common_security_scan_functions_v2.py` also creates a certificate-based `GraphServiceClient`.
  - A new auth abstraction must either:
    - support both SharePoint REST and Graph use cases, or
    - explicitly limit phase 1 to crawler SharePoint access only and defer Graph-related auth refactoring.

- **On-Behalf-Of for long-running jobs is unresolved**
  - The design assumes OBO can be triggered by the presence of an `Authorization` header.
  - That may be acceptable for request/response operations.
  - It is not yet proven for long-running crawl jobs that continue after request initiation, especially if tokens expire during execution.

- **Delegated override lifecycle is underspecified**
  - If Device Code override is global, the system needs metadata such as:
    - who activated it
    - when it was activated
    - when it expires
    - when it was last validated
    - what the current effective auth method is

- **Single-tenant expectation should be explicit**
  - The session is about a specific client environment.
  - The docs imply this, but should state it directly as a constraint.

## Flawed or Weak Decisions

- **OBO determined only by header presence is too weak**
  - The proposed rule is: if `Authorization` header exists, use OBO.
  - That is too simplistic.
  - The middleware should also validate:
    - token issuer
    - token audience
    - token type/claims suitability for delegated downstream exchange
    - whether the endpoint is allowed to use OBO
  - Otherwise this becomes a fragile and potentially unsafe trigger.

- **"No endpoint design changes needed" is too absolute**
  - It is true that existing crawler endpoints could stay mostly unchanged if auth is abstracted.
  - But the overall API surface still changes because auth management endpoints and status endpoints would be added.
  - So the statement should be softened.

- **Global delegated override carries a high security cost**
  - The docs already note the core issue: any caller could get the admin user's SharePoint access.
  - That makes Device Code override acceptable only as an emergency/manual mode, not a normal steady-state production pattern.

## Contradictions and Ambiguities

- **App-only wording conflict**
  - `_INFO_SPAUTH_REQUIREMENTS.md` says certificate is required for SharePoint REST app-only access.
  - The same doc also treats Managed Identity as a valid app-only alternative.
  - These statements are not clearly reconciled.
  - The wording should be narrowed so it is clear that certificate is required for the current app-registration certificate path, while Managed Identity is a separate app-only path.

- **"One mechanism for all workers" vs OBO always available**
  - These are not exactly the same model.
  - More precise wording:
    - one default/override mechanism for requests without user tokens
    - optional per-request OBO path when explicitly supported and validated

- **Both UI architectures are treated as current requirement**
  - The current session goal does not require full support for a separate SPA frontend.
  - That is a future-facing requirement, not a proven immediate need.

## Unnecessary Complexity

- **OBO in the first implementation phase**
  - This is not needed to unblock the client who disabled certificate auth.
  - It should be deferred unless a separate SPA requirement is confirmed as immediate.

- **Interactive Browser in the first implementation phase**
  - Useful for development convenience, but not necessary for the first unblock.

- **Cross-worker delegated token cache before Managed Identity is delivered**
  - This adds meaningful complexity before the simplest new auth path is in place.

- **Full auth switching UI before basic Managed Identity support exists**
  - This is likely premature.

## Recommended Scope Reduction

## Phase 1

- Implement a small auth abstraction that supports:
  - Certificate
  - Managed Identity
- Replace direct calls to `connect_to_site_using_client_id_and_certificate()` in crawler SharePoint paths with the abstraction
- Keep selection simple:
  - default method from config/env
  - no delegated flows yet

## Phase 2

- Add one delegated fallback only:
  - Device Code
- Add explicit admin-only controls
- Add token/status visibility
- Add expiration/error reporting

## Phase 3

- Add Interactive Browser only if still needed
- Position it mainly for local development or attended operation

## Phase 4

- Revisit On-Behalf-Of only if separate SPA support becomes a real requirement
- Resolve background-job semantics before implementation

## Concrete Items To Add To The Future SPEC

- **Auth abstraction boundaries**
  - Which components use it
  - Whether it covers Graph as well as SharePoint REST

- **Admin control model**
  - Who can switch auth mode
  - Who can initiate Device Code
  - Who can clear override
  - Who can view auth status

- **Override file schema**
  - `method`
  - `set_by`
  - `set_at_utc`
  - `expires_at_utc`
  - `notes` or `reason`
  - validation/version fields

- **Auth status endpoint semantics**
  - effective method
  - default method
  - override present or absent
  - token health state for delegated flows

- **Error model**
  - clear distinction between:
    - method unavailable
    - permission denied
    - token expired
    - invalid override config
    - misconfigured environment

- **Background job behavior**
  - what happens when delegated token expires mid-crawl
  - whether background jobs are allowed to use OBO at all

## Code Reality Check

The research matches several real code constraints:

- `common_sharepoint_functions_v2.py` currently only exposes certificate-based SharePoint connection via `with_client_certificate()`
- `crawler.py` directly depends on that certificate path
- `common_security_scan_functions_v2.py` also uses certificate-based Graph credentials
- `app.py` already has Azure identity usage for OpenAI, which means Azure identity is not foreign to the codebase
- Research docs already capture the `ClientContext(...).with_access_token(...)` path, which is the likely integration route for Managed Identity and delegated token-based SharePoint auth

## Final Answer

- **Are we on track with the initial goal?**
  - Yes, generally.
  - But the design has expanded well beyond the minimum scope needed for the original goal.

- **Anything missed?**
  - Yes:
    - admin authorization model
    - Graph-related auth scope
    - delegated override lifecycle metadata
    - explicit single-tenant constraint
    - long-running job behavior for delegated flows, especially OBO

- **Any flawed decisions?**
  - Yes:
    - OBO triggered by header presence alone is too weak
    - "no endpoint design changes needed" is too absolute
    - global delegated override is security-heavy and should be treated as emergency-only

- **Contradicting requirements?**
  - Some wording conflicts and ambiguities exist:
    - certificate-required wording vs Managed Identity app-only path
    - one mechanism for all workers vs OBO always available
    - future SPA support being treated like a current requirement

- **Do we introduce unnecessary complexity?**
  - Yes.
  - The main complexity drivers are OBO, Interactive Browser, delegated cross-worker cache, and auth-management UI before Managed Identity is implemented.

## Recommended Decision

Reduce scope and proceed in this order:

1. Certificate + Managed Identity only
2. Device Code fallback
3. Interactive Browser if still needed
4. OBO only if separate SPA support becomes an actual near-term requirement

## Status

- **Completed**:
  - session load
  - workspace priming
  - review of `_INFO_SPAUTH_REQUIREMENTS.md`
  - review of `_INFO_SPAUTH_TOKEN_SHARING.md`
  - cross-check against current code paths
- **Recommendation**:
  - lock the next SPEC to a minimal phase-1 goal centered on Managed Identity plus existing Certificate auth
