# Session Notes

**Doc ID**: BugFixes-NOTES

## Initial Request

````text
When fixing bugs, the is the way to go:
1) Record problem + verbatim prompt (in quadruple backticks) in PROBLEMS.md
2) Analyze the problem: Make several assumptions what it could mean and what the issue could be, search in code, verify, disambiguate the problem description and narrow down the problem -> Add to PROGRESS.md and make [BUG_FOLDER] in [SESSION_FOLDER] that will contain all artifacts.
3) Reproduce the bug using .tmp scripts or Playwright. Leave artifacts ONLY in [BUG_FOLDER]. Verify that bug exists on current code.
4) Do a deep analysis, use write-info workflow to record findings in new document in [BUG_FOLDER].
5) Develop a defensive, step-by-step plan using write-strut workflow to keep track of your overall goal, and your actions. Then should break down the entire activity into verifyable and testable phases. It should contain testing actions for each testable change made and include updating PROGRESS.md and PROBLEMS.md in session folder (only short summary). It should also contain the requirement to backup affected files locally in [BUG_FOLDER] to be able to do a final BEFORE / AFTER comparison and a commit strategy. NEVER COMMIT broken code during a bugfix. Keep modified files in [BUG_FOLDER] and then do commits. Assumptions should be verified! Medium complexity ideas should be tested in local POCs before implementation. When finding the root cause or jumping to conclusions, always ask yourself: How easy is it to test this? Choose the easiest testable idea first and then work yourself down to the more complex ideas or conclusions. Avoid blaming hardware or infractructure or libraries. When needed, add detailed logging BEFORE you are jumping to conclusions. You can backup the modfied original files to your [BUG_FOLDER] and easily revert changes. Also BEFORE you make changes, make a list of functionality that might be impacted. These must also be tested as part of the fix. Keep track of artifacts and data you create or leave in the system (not the [BUG_FOLDER]) while testing. These must be deleted after the fix has been successfully applied.
6) Then execute the plan step by step autonomously. If the plan is a bit more complex, use write-tasks-plan and write-test-plan to keep track of detailes. Update the STRUT and all other tracking documents frequently.
7) After the bug is fixed, do a final BEFORE / AFTER comparison. Only if this step confirms that the fix is working, you must do a final test of potentially affected functionality and if everything is OK, document everything in existing of specially created *_FIXES.md documents in [WORKSPACE_FOLDER]/docs and do a final commit.
````

## Session Info

- **Started**: 2026-02-05
- **Goal**: Fix Domains UI cache/reload issues after CRUD operations
- **Operation Mode**: IMPL-CODEBASE
- **Output Location**: `src/routers_v2/domains.py`

## Current Phase

**Phase**: EXPLORE
**Workflow**: /fix (bug investigation)
**Assessment**: Initial fix attempt failed - reloadItems override not working

## Agent Instructions

- Test changes via browser at `http://127.0.0.1:8000/v2/domains?format=ui`
- Domain storage: `.localstorage/OpenAi/domains/`
- V2FX topic for V2 endpoint fixes

## Bug-Fixing Workflow

**1) Record Problem**
- Add to PROBLEMS.md with unique ID
- Include verbatim user prompt in quadruple backticks (````)
- Capture exact error messages and symptoms

**2) Analyze Problem**
- Make several assumptions about possible causes
- Search in code, verify each assumption
- Disambiguate and narrow down the problem
- Update PROGRESS.md with findings
- Create `[BUG_FOLDER]` in `[SESSION_FOLDER]` for all artifacts

**3) Reproduce Bug**
- Use `.tmp` scripts or Playwright MCP
- Leave artifacts ONLY in `[BUG_FOLDER]`
- Verify bug exists on current code before any changes

**4) Deep Analysis**
- Use `/write-info` to record findings in `[BUG_FOLDER]`
- Document all evidence and observations

**5) Develop Plan**
- Use `/write-strut` for step-by-step plan with verifiable phases
- Include testing actions for each testable change
- Include PROGRESS.md and PROBLEMS.md updates (short summaries)
- Backup affected files to `[BUG_FOLDER]` for BEFORE/AFTER comparison
- Define commit strategy - NEVER commit broken code during bugfix
- Keep modified files in `[BUG_FOLDER]` until verified working
- Verify assumptions before acting on them
- Medium complexity ideas: test in local POCs first
- When finding root cause or jumping to conclusions, ask: "How easy is it to test this?"
- Choose easiest testable idea first, then work to more complex
- Avoid blaming hardware/infrastructure/libraries without evidence
- Add detailed logging BEFORE jumping to conclusions
- List functionality that might be impacted - must test these too
- Track artifacts/data created in system during testing - must delete after fix

**6) Execute Plan**
- Execute step by step autonomously
- For complex plans: use `/write-tasks-plan` and `/write-test-plan`
- Update STRUT and tracking documents frequently

**7) Final Verification**
- Do BEFORE/AFTER comparison
- Only proceed if fix confirmed working
- Test all potentially affected functionality
- Document in `*_FIXES.md` in `[WORKSPACE_FOLDER]/docs`
- Final commit only after all verifications pass

**8) Completion Checklist**
- [ ] Updated tracking in `[SESSION_FOLDER]`
- [ ] All artifacts in `[BUG_FOLDER]`
- [ ] Documentation in corresponding `*_FIXES.md`
- [ ] Clean commit with proper message

## Key Decisions

(none yet)

## Important Findings

- `domainsState` Map caches domain data for `showCrawlDomainForm()`
- `cacheDomains()` only called on `DOMContentLoaded`
- First fix attempt: Override `reloadItems()` to call `cacheDomains()` - **FAILED**
- Symptoms: File system shows 6 domains, UI shows 5 (LegalOriginalPDFs missing)

## Topic Registry

- `V2FX` - V2 Endpoint Fixes
- `DOM` - Domains router

## Significant Prompts Log

(none yet)
