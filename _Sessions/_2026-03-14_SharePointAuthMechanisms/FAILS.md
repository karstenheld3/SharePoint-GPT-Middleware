# Session Failures

**Doc ID**: 2026-03-14_SharePointAuthMechanisms-FAILS

## Active Issues

### [MEDIUM] `SPAUTH-FL-004` Ambiguous Abbreviation "SP" Used in Logging

- **When**: 2026-03-15 20:01
- **Where**: `AddRemoveCrawlerSharePointSites.ps1` (lines 146, 488, 512, 530, 545, 628)
- **What**: Used "SP" abbreviation in logging output. In this codebase, "SP" could mean "SharePoint" OR "Service Principal" - both are core concepts.

**Evidence**:
```powershell
Write-Host "  Scanning SP permissions..." -ForegroundColor Gray
Write-Host "Testing SP access..."
Write-Host "  SP: $certRoles    MI: $miRoles"
```

**Workflow re-read findings** (core-conventions.md, SPAUTH-FL-002):
- Rule: Acronyms must be written out on first use
- SPAUTH-FL-002 already documented this exact pattern for MI/OBO/Cert
- "SP" is especially problematic because BOTH meanings exist in this project

**Root cause**: Applied ASANAP (brevity) without considering clarity. "SP" seemed obvious in context but creates confusion when reading logs. Did not check FAILS.md for prior similar issues.

**Suggested fix**: Always use full terms in logging:
- "Service Principal" (not "SP")
- "SharePoint" (spell out, or use "SPO" for SharePoint Online if needed)
- Never use ambiguous single abbreviations

**Before (wrong):**
```powershell
Write-Host "  Scanning SP permissions..."
Write-Host "  SP: $certRoles    MI: $miRoles"
```

**After (correct):**
```powershell
Write-Host "  Scanning Service Principal..."
Write-Host "  Service Principal: $certRoles | Managed Identity: $miRoles"
```

### [LOW] `SPAUTH-FL-003` Proceeded to Create When Asked to Read

- **When**: 2026-03-15 17:39
- **Where**: Session conversation (IMPL plan preparation)
- **What**: User asked to "read everything you need to create an IMPL plan" - I proceeded to invoke write-documents skill and marked "Create IMPL plan" as in_progress

**Workflow re-read findings** (agent-behavior.md):
- Rule: `"Propose", "suggest", "draft", "outline" = talk ABOUT, don't modify`
- Rule: `"Implement", "fix", "change", "update" = modify the object`
- User said "read everything you need" = preparation, NOT execution

**Root cause**: Interpreted "to create" as instruction to create, rather than as purpose of reading. Rushed past the verb distinction. Should have stopped after reading and summarized findings.

**Suggested fix**: After reading, summarize what was found and wait for explicit instruction to proceed with creation.

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

**[2026-03-15 20:05]**
- Added: SPAUTH-FL-004 - Ambiguous "SP" abbreviation (SharePoint vs Service Principal)

**[2026-03-15 17:39]**
- Added: SPAUTH-FL-003 - Proceeded to create when asked to read

**[2026-03-14 20:06]**
- Added: SPAUTH-FL-002 - Acronyms not written out in INFO document

**[2026-03-14 16:18]**
- Added: SPAUTH-FL-001 - Incorrect headless assumption
