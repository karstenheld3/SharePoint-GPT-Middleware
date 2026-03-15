# Session Notes

**Doc ID**: BugFixes-NOTES

## Session Properties

- **Persistent**: This session is never archived
- **Long-running**: Accumulates bugs over time across all sessions
- **Workflow**: Run `/fix` - see `.windsurf/workflows/fix.md`

## Global Bug Number Registry

**Next available BG number**: `0001`

| BG-NNNN | TOPIC | Description | Status |
|---------|-------|-------------|--------|
| (none yet) | | | |

This is the **single source of truth** for PROJECT-MODE bug numbering.
Before creating a new `[BUG_FOLDER]`, get the next number here and update this table.

## Folder Structure

```
_Sessions/_BugFixes/
├── NOTES.md, PROBLEMS.md, PROGRESS.md, FAILS.md
└── BG-NNNN_[TOPIC]_Name/      <- [BUG_FOLDER] (global number)
    ├── PROBLEMS.md            <- Full detail
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
Bug ID: [TOPIC]-PR-NNN (3-digit)      Bug ID: BG-NNNN (global 4-digit)
Docs: SPEC/IMPL/TEST only             Docs: SPEC/IMPL/TEST + *_FIXES.md
```

## Important Findings

- `domainsState` Map caches domain data for `showCrawlDomainForm()`
- `cacheDomains()` only called on `DOMContentLoaded`
- First fix attempt: Override `reloadItems()` to call `cacheDomains()` - **FAILED**
- Symptoms: File system shows 6 domains, UI shows 5 (LegalOriginalPDFs missing)

## Topic Registry

- `BUGFIXES` - Bug fixes session
- `DOM` - Domains router

## Significant Prompts Log

(none yet)
