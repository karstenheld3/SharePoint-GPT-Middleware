---
name: edird-phase-model
description: Apply when doing [PLAN], [DECOMPOSE], or debugging workflow issues
---

# EDIRD Phase Model (Full)

## When to Invoke

- [PLAN] - Read FLOWS.md for workflow type (BUILD/SOLVE)
- [DECOMPOSE] - Read GATES.md for gate requirements
- Stuck or debugging - Read NEXT_ACTION.md for deterministic logic

## Quick Reference

Workflow types: BUILD (code output) | SOLVE (knowledge/decision output)

Assessment: COMPLEXITY-LOW/MEDIUM/HIGH | PROBLEM-TYPE (RESEARCH/ANALYSIS/EVALUATION/WRITING/DECISION/HOTFIX/BUGFIX)

## Files

- **GATES.md** - Full gate checklists for each phase transition
- **FLOWS.md** - Verb sequences for BUILD and SOLVE workflows, hybrid situations
- **NEXT_ACTION.md** - Deterministic next-action logic for autonomous mode
- **BRANCHING.md** - Context state branching syntax

## Phase Overview

```
[EXPLORE] → [DESIGN] → [IMPLEMENT] → [REFINE] → [DELIVER]
```

Each phase has:
- Entry condition (previous gate passed)
- Applicable verbs
- Exit gate (checklist to proceed)
