# Session Failures

**Doc ID**: LOG-FAILS

## Active Failures

### LOG-FL-003: Asking user to do things agent can do itself

**Severity:** [HIGH]
**When:** 2026-03-04 21:03
**Where:** Agent behavior during testing

**What happened:**
Agent asked user to start the server instead of doing it. DevSystem rules state agent should be self-sufficient and execute tasks autonomously.

**Wrong assumptions:**
1. "User needs to start the server" - Agent has run_command tool
2. "I should inform user and wait" - Agent should act, not delegate

**Root cause:**
Learned helplessness pattern. Agent defaulted to asking instead of doing.

**Fix:**
- Execute commands directly using run_command tool
- Only ask user for things agent genuinely cannot do (credentials, approvals)
- Re-read DevSystem rules about agent autonomy

### LOG-FL-002: Assumed server restart needed instead of using hot reload

**Severity:** [MEDIUM]
**When:** 2026-03-04 21:00
**Where:** Agent behavior during testing

**What happened:**
Agent repeatedly stopped and restarted uvicorn server after code changes, assuming restart was necessary. Wasted time and caused confusion when the glob pattern fix should have been picked up automatically.

**Wrong assumptions:**
1. "Server must be restarted after code changes" - FastAPI/uvicorn supports hot reload
2. Started server without `--reload` flag, then blamed caching instead of recognizing the missing flag

**Root cause:**
Agent did not check if user's dev workflow uses `--reload` flag. Should have asked or used `--reload` by default for development.

**Fix:**
- Use `uvicorn app:app --reload` for development servers
- Don't restart servers unnecessarily - check if hot reload is enabled first

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
