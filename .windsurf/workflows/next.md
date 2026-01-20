---
description: Start any task - ensures planning, self-review, and compliance tracking
phase: EXPLORE
---

# Next Task

**Purpose:** Universal entry point with structured planning and compliance output.

**Usage:** `/next [your task description]`

## Step 1: Assess (EXPLORE Phase Entry)

**Before planning, determine workflow type and complexity:**

1. [ASSESS] workflow type: BUILD (code output) or SOLVE (knowledge/decision output)
2. [ASSESS] complexity/problem-type:
   - BUILD: COMPLEXITY-LOW / MEDIUM / HIGH
   - SOLVE: RESEARCH / ANALYSIS / EVALUATION / WRITING / DECISION

## Step 2: Create Plan (Before Execution)

**Before implementing anything, create a plan.**

### For Small Tasks (inline)

```
[PLAN]
1. [Step description] - Decision: [what needs deciding]
2. [Next step] - Decision: [what needs deciding]
```

### For Larger Tasks (create file)

Create plan in session folder or `PROGRESS.md`:
- Multiple files to change
- Architectural decisions needed
- Will take >15 minutes

### Why Plan First

1. Think through approach before coding
2. Catch missing information early
3. Verify dependencies exist

## Step 3: Execute Task

Proceed with task following your plan.

**For significant decisions**, briefly note reasoning:
- Design choices (how to structure something)
- Behavioral choices (how something should work)
- Trade-offs (option A vs B)

## Step 4: Self-Review (Before Completing)

Before marking complete, switch to critical reviewer mindset:

1. **Re-read outputs** - Scan as if seeing for first time
2. **Challenge assumptions** - List assumptions made, are any unverified?
3. **Look for shortcuts** - Did I defer work that should be done now?

### Quick Questions

- Would a careful reviewer catch something I missed?
- Did I stop at "good enough" or push for "actually good"?
- If this fails later, what would I wish I had checked?

## Step 5: Compliance Output (REQUIRED)

**At the end of EVERY response using this workflow:**

```markdown
---
## Compliance

**Decision points:** [key decisions made and reasoning]
**Assumptions:** [things taken as true without verifying]
**Missed:** [anything that should have been done - be honest]
```

## Notes

- Use `/next` for any task where structured planning matters
- For quick questions without decisions, skip this workflow
