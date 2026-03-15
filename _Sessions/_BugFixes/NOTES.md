# Session Notes

**Doc ID**: BugFixes-NOTES

## Initial Request

````text
When fixing bugs, the is the way to go:
1) Record problem + verbatim prompt (in quadruple backticks) in PROBLEMS.md (either in session or in separate [BUG_FOLDER] in [BUGFIXES_SESSION_FOLDER] when not working in a session)
2) Analyze the problem: Make several assumptions what it could mean and what the issue could be, search in code, verify, disambiguate the problem description and narrow down the problem -> Add to PROGRESS.md and make [BUG_FOLDER] in [SESSION_FOLDER] (or [BUGFIXES_SESSION_FOLDER]) that will contain all artifacts.
3) Reproduce the bug using .tmp scripts or Playwright. Leave artifacts ONLY in [BUG_FOLDER]. Verify that bug exists on current code.
4) Do a deep analysis, use write-info workflow to record findings in new document in [BUG_FOLDER].
5) Develop a defensive, step-by-step plan using write-strut workflow to keep track of your overall goal, and your actions. Then should break down the entire activity into verifyable and testable phases. It should contain testing actions for each testable change made and include updating PROGRESS.md and PROBLEMS.md in session folder (only short summary). It should also contain the requirement to backup affected files locally in [BUG_FOLDER] to be able to do a final BEFORE / AFTER comparison and a commit strategy. NEVER COMMIT broken code during a bugfix. Keep modified files in [BUG_FOLDER] and then do commits. Assumptions should be verified! Medium complexity ideas should be tested in local POCs before implementation. When finding the root cause or jumping to conclusions, always ask yourself: How easy is it to test this? Choose the easiest testable idea first and then work yourself down to the more complex ideas or conclusions. Avoid blaming hardware or infractructure or libraries. When needed, add detailed logging BEFORE you are jumping to conclusions. You can backup the modfied original files to your [BUG_FOLDER] and easily revert changes. Also BEFORE you make changes, make a list of functionality that might be impacted. These must also be tested as part of the fix. Keep track of artifacts and data you create or leave in the system (not the [BUG_FOLDER]) while testing. These must be deleted after the fix has been successfully applied.
6) Then execute the plan step by step autonomously. If the plan is a bit more complex, use write-tasks-plan and write-test-plan to keep track of detailes. Update the STRUT and all other tracking documents frequently.
7) After the bug is fixed, do a final BEFORE / AFTER comparison. Only if this step confirms that the fix is working, you must do a final test of potentially affected functionality and if everything is OK, document everything in existing of specially created *_FIXES.md documents in [WORKSPACE_FOLDER]/docs and do a final commit.
````

**Refinements from original prompt to workflow below:**
- Two contexts defined: `SESSION-MODE` vs `PROJECT-MODE` bugs
- Always create `[BUG_FOLDER]` (both contexts)
- `SESSION-MODE` bugs reuse PR ID as folder name: `[TOPIC]-PR-NNN_Name/`
- Two-level PROBLEMS.md: short summary in parent, full detail in `[BUG_FOLDER]`
- Doc updates split: ALWAYS update SPEC/IMPL/TEST, `PROJECT-MODE` ALSO creates `*_FIXES.md`
- `*_FIXES.md` placement: next to IMPL doc (preferred) or SPEC doc
- `*_FIXES.md` format defined: tracking ID (`[TOPIC]-BG-NNNN`), Problem, Solution, Changed files

## Session Properties

- **Persistent**: This session is never archived
- **Long-running**: Accumulates bugs over time across all sessions

## Folder Structure

```
_Sessions/_BugFixes/           <- Main bugfixes session folder (persistent)
├── NOTES.md                   <- Session notes (this file)
├── PROBLEMS.md                <- Summary tracking (short entries)
├── PROGRESS.md                <- Overall progress
├── FAILS.md                   <- Lessons learned
└── [TOPIC]-BG-NNNN_Name/      <- Individual [BUG_FOLDER] (artifacts, backups, POCs)
    ├── PROBLEMS.md            <- Full detail problem tracking for this bug
    ├── _INFO_*.md             <- Deep analysis findings
    ├── _STRUT_*.md            <- Fix plan
    ├── backup/                <- Original file backups
    ├── poc/                   <- Proof of concept scripts
    └── test/                  <- Test scripts
```

## When to Use This Folder

**Use `[BUGFIXES_SESSION_FOLDER]` for:**
- Bugs discovered AFTER a session is closed/archived
- Issues found during normal usage (not active development)
- Regression bugs from production

`SESSION-MODE` bugs are fixed in the current session folder, not here.
Both contexts ALWAYS create a `[BUG_FOLDER]` subfolder for artifacts.

## ID Formats

**Problem tracking IDs** (in PROBLEMS.md):
- Follow standard `[TOPIC]-PR-[NNN]` format per `devsystem-ids.md`
- `PROJECT-MODE` bugs in `_BugFixes/PROBLEMS.md`: short summary only
- Full detail in `[BUG_FOLDER]/PROBLEMS.md`

**[BUG_FOLDER] naming**:
- `SESSION-MODE`: reuse PR ID as folder name: `[TOPIC]-PR-NNN_ShortDescription/` (3-digit)
  - Example: `V2CR-PR-003_CrawlerTimeout/`
- `PROJECT-MODE`: `[TOPIC]-BG-NNNN_ShortDescription/` (4-digit)
  - Example: `DOM-BG-0001_DomainsUIRefresh/`

## Bug-Fixing Workflow

**Run `/fix` workflow** - See `.windsurf/workflows/fix.md` for complete 11-step process.

**Quick reference**:
```
SESSION-MODE                          PROJECT-MODE
─────────────────────────────────────────────────────────────────
Found: During active session          Found: After session closed
Folder: [SESSION_FOLDER]/             Folder: _BugFixes/
Bug ID: [TOPIC]-PR-NNN (3-digit)      Bug ID: [TOPIC]-BG-NNNN (4-digit)
Docs: SPEC/IMPL/TEST only             Docs: SPEC/IMPL/TEST + _FIXES.md
Commit: fix([TOPIC]-PR-NNN): ...      Commit: fix([TOPIC]-BG-NNNN): ...
```

**Steps summary**:
1. Determine context (SESSION-MODE or PROJECT-MODE)
2. Ensure _BugFixes session exists (PROJECT-MODE only)
3. Record problem in PROBLEMS.md
4. Analyze and create `[BUG_FOLDER]`
5. Reproduce bug
6. Deep analysis (`/write-info`)
7. Develop plan (`/write-strut`)
8. Impact assessment (MANDATORY)
9. Execute plan (`/implement`)
10. Final verification and documentation
11. Completion checklist

## _FIXES.md Format

Created for `PROJECT-MODE` bug fixes only, placed next to the component's IMPL or SPEC doc.
One `_FIXES.md` per component (e.g., `_V2_IMPL_DOMAINS_FIXES.md`).

**Purpose**: Records what had to be fixed after implementation was done. Provides a chronological audit trail of post-implementation bugs, their solutions, and all affected files (code and docs).

Each entry records:

```
### [TOPIC]-BG-NNNN_ShortDescription

**Problem**: Single sentence describing the bug
**Solution**: Single sentence describing the fix

**Changed or added files**:
- `path/to/file.py`      - What was changed
- `path/to/poc_file.py`  - POC file that was used to prove solution
- `path/to/test_file.py` - Test file that was used to test bugfix
- `path/to/spec.md`      - Added scenario for edge case X
- `path/to/impl.md`      - Updated step Y to handle Z
```

## Key Decisions

- Always create `[BUG_FOLDER]` for every bug (`SESSION-MODE` and `PROJECT-MODE`)
- `SESSION-MODE`: update SPEC/IMPL/TEST only
- `PROJECT-MODE`: update SPEC/IMPL/TEST AND create `*_FIXES.md`
- `*_FIXES.md` records tracking ID, Problem, Solution, Changed files list

## Important Findings

- `domainsState` Map caches domain data for `showCrawlDomainForm()`
- `cacheDomains()` only called on `DOMContentLoaded`
- First fix attempt: Override `reloadItems()` to call `cacheDomains()` - **FAILED**
- Symptoms: File system shows 6 domains, UI shows 5 (LegalOriginalPDFs missing)

## Topic Registry

- `BUGFIXES` - Bug fixes session (`PROJECT-MODE` format: `[TOPIC]-BG-NNNN_ShortDescription`)
- `DOM` - Domains router

## Bug Folder Naming

**`SESSION-MODE` bugs**: Reuse the problem tracking ID as folder name
- Format: `[TOPIC]-PR-NNN_ShortDescription/`
- Examples: `V2CR-PR-003_CrawlerTimeout/`, `SITE-PR-001_PermissionDenied/`
- Maps 1:1 to PROBLEMS.md entry, no separate bug numbering needed

**`PROJECT-MODE` bugs**: Use BG tracking ID per `devsystem-ids.md` (4-digit)
- Format: `[TOPIC]-BG-NNNN_ShortDescription/`
- Examples: `DOM-BG-0001_DomainsUIRefresh/`, `DOM-BG-0002_DomainsStateCacheSync/`

**Rules**:
- Main folder contains shared tracking files
- Each bug gets its own subfolder named after bug ID
- All artifacts for a bug stay in its folder

## Significant Prompts Log

(none yet)
