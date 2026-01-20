---
description: Start a new feature with session-based BUILD workflow
phase: EXPLORE
---

# New Feature Workflow

Session-based BUILD workflow for implementing new features.

## Required Skills

- @session-management for session setup
- @edird-phase-model for phase details
- @write-documents for document templates

## Usage

```
/new-feature "Add user authentication API"
```

## Step 1: Initialize Session

Run `/session-init` with feature name as topic.

Creates session folder with:
- NOTES.md (with Current Phase tracking)
- PROGRESS.md (with Phase Plan)
- PROBLEMS.md

## Step 2: EXPLORE Phase

1. [ASSESS] complexity: COMPLEXITY-LOW / MEDIUM / HIGH
2. [ANALYZE] existing code and patterns
3. [GATHER] requirements from user
4. [SCOPE] define boundaries

### Gate Check: EXPLORE→DESIGN

- [ ] Problem or goal clearly understood
- [ ] Workflow type: BUILD confirmed
- [ ] Complexity assessed
- [ ] Scope boundaries defined
- [ ] No blocking unknowns

**Pass**: Proceed to DESIGN | **Fail**: Continue EXPLORE

## Step 3: DESIGN Phase

1. [PLAN] structured approach
2. [WRITE-SPEC] → `_SPEC_[FEATURE].md`
3. [PROVE] risky parts with POC (if COMPLEXITY-MEDIUM or higher)
4. [WRITE-IMPL-PLAN] → `_IMPL_[FEATURE].md`
5. [WRITE-TEST-PLAN] → `_TEST_[FEATURE].md` (optional for LOW)
6. [DECOMPOSE] into small testable steps

### Gate Check: DESIGN→IMPLEMENT

- [ ] Spec document created
- [ ] POC completed (if MEDIUM+)
- [ ] Impl plan with testable steps
- [ ] No open questions

**Pass**: Proceed to IMPLEMENT | **Fail**: Continue DESIGN

## Step 4: IMPLEMENT Phase

For each step in IMPL plan:

1. [IMPLEMENT] code changes
2. [TEST] verify step works
3. [FIX] if tests fail (max 3 retries, then [CONSULT])
4. [COMMIT] when green
5. Update PROGRESS.md

### Gate Check: IMPLEMENT→REFINE

- [ ] All IMPL steps complete
- [ ] Tests pass
- [ ] No TODO/FIXME unaddressed
- [ ] Progress committed

**Pass**: Proceed to REFINE | **Fail**: Continue IMPLEMENT

## Step 5: REFINE Phase

1. [REVIEW] self-review of work
2. [VERIFY] against spec/rules
3. [TEST] regression testing
4. [CRITIQUE] and [RECONCILE] (if MEDIUM+)
5. [FIX] issues found

### Gate Check: REFINE→DELIVER

- [ ] Self-review complete
- [ ] Verification passed
- [ ] Critique/reconcile done (if MEDIUM+)
- [ ] All issues fixed

**Pass**: Proceed to DELIVER | **Fail**: Continue REFINE

## Step 6: DELIVER Phase

1. [VALIDATE] with user (final approval)
2. [MERGE] branches if applicable
3. [FINALIZE] documentation
4. [CLOSE] mark as done
5. Run `/session-close`

## Phase Tracking

Update NOTES.md after each phase:

```markdown
## Current Phase

**Phase**: IMPLEMENT
**Last verb**: [TEST]-OK
**Gate status**: 3/4 items checked
```

## Stuck Detection

If 3 consecutive [FIX] attempts fail:
1. Document in PROBLEMS.md
2. [CONSULT] with user
3. Wait for guidance or [DEFER]
