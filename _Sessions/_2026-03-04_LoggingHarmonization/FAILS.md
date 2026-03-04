# Session Failures

**Doc ID**: LOG-FAILS

## Active Failures

### LOG-FL-001: Overwrote user edits during batch update

**Severity:** [HIGH]
**When:** 2026-03-04 18:39
**Where:** `LOGGING-RULES.md:L47-67`

**What happened:**
When user requested "adapt all examples accordingly", agent read the file but used stale content from checkpoint summary instead of current file state. The multi_edit replaced user's carefully structured status patterns with a simpler version.

**User's version (correct):**
```
**Item-level status** (for individual operations within an activity):
Each separately logged item level action finishes with either 
- `OK.` or `OK: <what, details>`
or
- `SKIP: <why>`
or
- `ERROR: <what> -> <system error>`
and can log additional
- `WARNING: <non-breaking problem>`
```

**Agent's version (incorrect - overwrote user):**
```
**Item-level status** (for individual operations within an activity):
- `OK.` or `OK: <what, details>`
- `WARNING: <non-breaking problem>`
- `SKIP: <why>`
- `ERROR: <what> -> <system error>`
```

**Root cause:**
Agent did not re-read the specific section being edited before constructing the edit. Used content from earlier read or checkpoint context.

**Fix:**
Always re-read the exact lines being modified immediately before editing, especially when user has been making concurrent changes.

## Resolved Failures

(none yet)
