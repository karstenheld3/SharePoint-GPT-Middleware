---
auto_execution_mode: 1
description: Full EDIRD cycle for autonomous implementation
workflow_type: BUILD
---

# Go Autonomous Workflow

Executes full EDIRD phase cycle autonomously with [ACTOR] = Agent.

## Pre-Flight Check

1. Do we have enough context? If unclear, [CONSULT] with user.
2. Do we have stop or acceptance criteria?
3. Re-read conversation, make internal MUST-NOT-FORGET list.

## EDIRD Cycle

### EXPLORE
1. [ASSESS] workflow type (BUILD/SOLVE) and complexity
2. [SCOPE] define boundaries
3. [DECIDE] approach

### DESIGN
1. [PLAN] structured approach
2. [DECOMPOSE] into small testable steps
3. Create SPEC, IMPL, TEST documents (depth per complexity)

### IMPLEMENT
1. For each step:
   - [IMPLEMENT] changes
   - [TEST] verify
   - [FIX] if needed (per retry limits)
   - [COMMIT] when green
2. Run `/verify` after each step

### REFINE
1. [REVIEW] self-review
2. [VERIFY] against spec/rules
3. [FIX] issues found

### DELIVER
1. [VALIDATE] against MUST-NOT-FORGET list
2. [COMMIT] final changes
3. [CLOSE] mark complete

## Retry Limits

- COMPLEXITY-LOW: Infinite retries
- COMPLEXITY-MEDIUM/HIGH: Max 5 per phase, then [CONSULT]

## Stuck Detection

If no progress after retry limit:
1. Document in PROBLEMS.md
2. [CONSULT] with user
3. Wait for guidance or [DEFER]