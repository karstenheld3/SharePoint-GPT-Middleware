---
description: Close a development session, sync findings, and archive
auto_execution_mode: 1
---

# Close Session Workflow

Use this workflow when a session is complete and verified working.

## Steps

1. **Sync ALL problems to project !PROBLEMS.md**
   - Read session PROBLEMS.md completely
   - For EACH problem listed:
     - If RESOLVED: Mark corresponding item in `!PROBLEMS.md` as GELOEST/FIXED with date
     - If OPEN/DEFERRED: Add to `!PROBLEMS.md` (German first, then English)
     - If new issue discovered: Add as new numbered item
   - Follow bilingual rule: German summary, then English summary
   - Update `!PROBLEMS_GER.md` to stay in sync

2. **Update session PROBLEMS.md**
   - Change status from `Open` to `RESOLVED` for fixed problems
   - Add final resolution notes if needed

3. **Update session PROGRESS.md**
   - Keep To Do list intact - do NOT delete it
   - Mark completed To Do items as done: `- [x]`
   - Ensure all completed tasks are in "Done" section

4. **Sync long-term findings to project !NOTES.md**
   - Review session NOTES.md for reusable patterns
   - Review session's `_INFO_*.md` files
   - Add important findings: problem, solution, usage example, key facts

5. **Archive session**
   - Run `/session-archive` workflow to move folder and commit
