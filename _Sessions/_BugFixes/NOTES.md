# Session Notes

**Doc ID**: BugFixes-NOTES

## Session Properties

- **Persistent**: This session is never archived
- **Long-running**: Accumulates bugs over time across all sessions
- **Workflow**: Run `/fix` - see `.windsurf/workflows/fix.md`

## Global Bug Number Registry

Single source of truth for PROJECT-MODE bug numbering.
Get next number here before creating `[BUG_FOLDER]`.

Format: `GLOB-BG-NNNN` - Description - Status
Next available: `GLOB-BG-0001`

- (none yet)

## Folder Structure

```
_Sessions/_BugFixes/
├── NOTES.md, PROBLEMS.md, PROGRESS.md, FAILS.md
└── GLOB-BG-NNNN_IssueDescription/  <- [BUG_FOLDER]
    ├── PROBLEMS.md                 <- Full detail
    ├── _INFO_*.md, _STRUT_*.md
    └── backup/, poc/, test/
```

## When to Use This Folder

Use for `PROJECT-MODE` bugs only (found AFTER session closed/archived).
`SESSION-MODE` bugs go in current `[SESSION_FOLDER]`.

## Quick Reference

```
SESSION-MODE                          PROJECT-MODE
─────────────────────────────────────────────────────────────────
Found: During active session          Found: After session closed
Folder: [SESSION_FOLDER]/             Folder: _BugFixes/
Bug ID: [TOPIC]-BG-NNNN               Bug ID: GLOB-BG-NNNN
Bug Folder: [TOPIC]-BG-NNNN_*/        Bug Folder: GLOB-BG-NNNN_*/
PR ID: [TOPIC]-PR-NNNN                PR ID: GLOB-PR-NNNN
Docs: SPEC/IMPL/TEST only             Docs: SPEC/IMPL/TEST + *_FIXES.md
Commit: fix([TOPIC]-BG-NNNN): ...     Commit: fix(GLOB-BG-NNNN): ...
```

## Important Findings

- `domainsState` Map caches domain data for `showCrawlDomainForm()`
- `cacheDomains()` only called on `DOMContentLoaded`
- First fix attempt: Override `reloadItems()` to call `cacheDomains()` - **FAILED**
- Symptoms: File system shows 6 domains, UI shows 5 (LegalOriginalPDFs missing)

## Topic Registry

- `BUGFIXES` - Bug fixes session (this session's TOPIC)

## Significant Prompts Log

(none yet)
