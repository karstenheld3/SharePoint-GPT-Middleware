---
description: Autonomous loop until goal reached
auto_execution_mode: 1
---

# Go Workflow

Autonomous execution loop using `/recap` and `/continue`.

**Principle:** Work completely autonomously until goal is reached. Use all available tools proactively. Never sacrifice requirements for task completion. No shortcuts allowed. All requirements must be implemented 100%. All problems or bugs must be first understood and then fixed. No lazy programming allowed. 

## Step 0: Completion Check

Before any work, check if goal is already reached:

1. Read STRUT plan (PROGRESS.md or session document)
2. Run `/verify` (STRUT Transition Phase) to check:
   - All Deliverables in final phase checked?
   - All Objectives verified via linked Deliverables?
   - Final Transition points to `[END]`?

**If already complete:**
```
Goal already reached. No further work needed.
Last completed: [final deliverable]
```
→ Stop. Do not execute. Do not re-verify on subsequent `/go` calls.

**If not complete:** Proceed to Pre-Flight Check.

## Step 1: Recap

Run `/recap` to determine:
- Last completed action
- Current state
- Any blockers


## Step 2: Pre-Flight Check

1. Do we have enough context? If unclear, gather more.
2. Do we have stop or acceptance criteria?
3. Re-read conversation, make internal MUST-NOT-FORGET list.
4. Research and list all scripts and skills that should be used for task completion and add them to internal MUST-NOT-FORGET list.

## Step 3: Continue

Run `/continue` to:
- Execute next task from plan
- Update progress
- Check for completion

## Step 4: Execution Loop

````
iteration_count = 0
WHILE goal not reached AND iteration_count < 5:
    iteration_count += 1
    /recap   # Assess current state
    /continue # Execute next item
    
    IF iteration_count >= 5:
        STOP - Ask user: "Reached 5 iterations without goal completion. Continue?"
    
    IF blocker:
        Invent id [BLOCKER] for blocker 
        Log to PROBLEMS.md
        /write-info `.tmp_INFO_[BLOCKER].md` about your current approach, why it does fail (root cause analysis)
        /critique your current approach and research more information. Maybe we need to go slower and test our assumptions and implementation steps in more detail. 
        /reconcile the critics findings
        /write-task-plan `.tmp_TASK_[BLOCKER].md` with modified approach based on revised findings
        run /verify -> /critique -> /reconcile -> /implement -> /verify on `.tmp_TASK_[BLOCKER].md`: will that address the blocker and reach the goal
        /write-test-plan `.tmp_TEST_[BLOCKER].md` based on IMPL plan for fully autonomous test
        run /verify -> /critique -> /reconcile -> /implement -> /verify on `.tmp_TASK_[BLOCKER].md`: How can we reach 100% test coverage and test every detail
````

## Step 5: Loop or Stop

- **Goal reached?** Stop, output summary
- **Blocker?** Log to PROBLEMS.md, ask user
- **More work?** Return to Step 3

## Stopping Conditions

- All tasks complete (final Transition = `[END]` checked)
- Blocker requires user input
- User interruption
- Retry limit exceeded (5 attempts for MEDIUM/HIGH complexity)

## Idempotent Behavior

Multiple `/go` commands on completed work:

1. First `/go` after completion: Output "Goal already reached" message
2. Subsequent `/go`: Same message, no re-verification, no action

This prevents:
- Wasted tokens on redundant verification
- Misinterpreting queued `/go` as dissatisfaction
- Overengineering completed deliverables