# Session Failures

**Doc ID**: 2026-03-14_SharePointAuthMechanisms-FAILS

## Active Issues

### [LOW] `SPAUTH-FL-002` Acronyms Not Written Out

- **When**: 2026-03-14 20:06
- **Where**: `_INFO_SPAUTH_TOKEN_SHARING.md` Key Questions section (lines 23-39)
- **What**: Used abbreviations like "MI", "Cert", "OBO" without writing out full terms first
- **Why it went wrong**: Prioritized brevity over clarity; forgot documentation rule to write out acronyms on first use
- **Evidence**: Line 24: `→ Varies: Nothing (MI), cert path (Cert), tokens (Device Code, Interactive, OBO)`
- **Suggested fix**: Write out full terms: "Managed Identity (MI)", "Certificate (Cert)", "On-Behalf-Of (OBO)" on first use

**Before (wrong):**
```
→ Varies: Nothing (MI), cert path (Cert), tokens (Device Code, Interactive, OBO)
```

**After (correct):**
```
→ Varies: Nothing (Managed Identity), cert path (Certificate), tokens (Device Code, Interactive Browser, On-Behalf-Of)
```

### [LOW] `SPAUTH-FL-001` Incorrect Architecture Assumption

- **When**: 2026-03-14 16:18
- **Where**: Session conversation (auth research)
- **What**: Assumed middleware runs headless on Azure App Service, recommended DeviceCodeCredential as primary fallback

**Wrong Assumption:**
- **Assumed**: Azure App Service = headless server, no browser available
- **Reality**: Middleware has full browser-based UI (FastAPI + HTML pages, modals, SSE console)
- **Why wrong**: Conflated deployment platform with application architecture; did not consider that users access via browser

**Evidence**: 
- `_V2_SPEC_ROUTERS.md` defines `format=ui` parameter for interactive HTML UI
- `_V2_IMPL_CRAWLER.md` specifies modal dialogs, console panels, toolbar buttons
- All V2 endpoints serve HTML/UI responses

**Suggested fix**: 
- For SPAUTH-PR-002, **InteractiveBrowserCredential** is viable since users have browsers
- DeviceCodeCredential still useful for CLI/script scenarios
- Consider offering both options in auth configuration

## Resolved Issues

(none yet)

## Document History

**[2026-03-14 20:06]**
- Added: SPAUTH-FL-002 - Acronyms not written out in INFO document

**[2026-03-14 16:18]**
- Added: SPAUTH-FL-001 - Incorrect headless assumption
