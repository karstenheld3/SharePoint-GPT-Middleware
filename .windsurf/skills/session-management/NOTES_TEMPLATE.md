# Session Notes

Populated by `/session-new` workflow. Captures session context, decisions, and agent instructions for a specific development task.

**Doc ID**: YYYY-MM-DD_[SessionTopicCamelCase]-NOTES

## Initial Request

**MANDATORY**: Record the user's session-starting prompt verbatim. This preserves intent and prevents drift.

````text
[Paste user's exact prompt here - do not summarize]
````

**Agent rule**: Copy-paste the user's first substantive message that defines the session goal. If prompt is trivial (<20 tokens), write "See Goal above" instead.

## Session Info

- **Started**: 2026-01-15
- **Goal**: Fix authentication token expiration handling in API client
- **Operation Mode**: IMPL-CODEBASE | IMPL-ISOLATED
- **Output Location**: src/features/auth/ | [SESSION_FOLDER]/poc/

## Agent Instructions

- Use exponential backoff for retry logic (1s, 2s, 4s)
- All token operations must be thread-safe

## Key Decisions

- **AUTH-DD-01**: Store refresh token in secure storage instead of localStorage. Rationale: localStorage is vulnerable to XSS attacks.
- **AUTH-DD-02**: Implement token refresh 5 minutes before expiration. Rationale: Prevents race conditions from on-demand refresh.

## Important Findings

- Current implementation has race condition when multiple requests trigger refresh simultaneously [VERIFIED]
- Token expiration check uses client-side time - vulnerable to clock skew [VERIFIED]
- Server returns 401 for both expired and invalid tokens - need to distinguish [ASSUMED]

## Topic Registry

Maintain list of TOPIC IDs used in this session/project:

- `AUTH` - Authentication and authorization system
- `API` - API client and request handling

## Significant Prompts Log

**Agent rule**: Record prompts that change direction, add requirements, or clarify intent. Use 4-backtick fence with `text` language tag.

**Format**: `[YYYY-MM-DD HH:MM]` + one-line context, then fenced prompt.

[2026-01-20 12:24] User clarified retry requirements
````text
Actually, use exponential backoff starting at 500ms, not 1s. And cap at 3 retries.
````

[2026-01-21 09:52] User added thread-safety constraint
````text
I forgot to mention - this runs in a multi-threaded environment. All token ops must be thread-safe.
````