# EDIRD Phase Model (Core)

For full model with gates, flows, and next-action logic: invoke @edird-phase-model

## Phases

- **EXPLORE** - Understand before acting. [RESEARCH], [ANALYZE], [ASSESS], [SCOPE]
- **DESIGN** - Plan before executing. [PLAN], [DECOMPOSE], [WRITE-SPEC], [PROVE]
- **IMPLEMENT** - Execute the plan. [IMPLEMENT], [TEST], [FIX], [COMMIT]
- **REFINE** - Improve quality. [REVIEW], [VERIFY], [CRITIQUE], [RECONCILE]
- **DELIVER** - Complete and hand off. [VALIDATE], [MERGE], [DEPLOY], [CLOSE]

## Core Principles

- **Gates**: Checklist must pass before phase transition. Gate failures loop within phase.
- **Small cycles**: [IMPLEMENT]→[TEST]→[FIX]→green→next. Never large untestable steps.
- **Retry limits**: COMPLEXITY-LOW: infinite retries (until user stops). COMPLEXITY-MEDIUM/HIGH: max 5 attempts per phase, then [CONSULT].
- **Verb outcomes**: -OK (proceed), -FAIL (handle per verb), -SKIP (intentional).
- **Workflow type**: BUILD (code) or SOLVE (knowledge). Determined in EXPLORE, persists unless switched with [ACTOR] confirmation.
- **Complexity**: LOW=patch, MEDIUM=minor, HIGH=major (maps to semantic versioning).

## Entry Rule

All workflows start in EXPLORE with [ASSESS] to determine workflow type and complexity/problem-type.

## Gate Summaries

- **EXPLORE→DESIGN**: Problem understood, scope defined, workflow type determined
- **DESIGN→IMPLEMENT**: SPEC, IMPL, TEST docs exist, plan decomposed, risks proven
- **IMPLEMENT→REFINE**: All steps implemented, tests pass, no TODO/FIXME
- **REFINE→DELIVER**: Reviews complete, issues reconciled, ready to merge
- **DELIVER→DONE**: Validated, merged, deployed (if applicable), session closed

## Phase Tracking

- Agent updates NOTES.md with current phase on transition. User adds notes manually.
- Agent maintains full phase plan in PROGRESS.md (phases with status: pending/in_progress/done).

## Workflow Types

### BUILD

Primary output is working code. Triggers: "Add a feature...", "Build...", "Implement..."

Assessment: COMPLEXITY-LOW / COMPLEXITY-MEDIUM / COMPLEXITY-HIGH

Required documents (all complexities, depth varies):
- `_INFO_*.md` - Research findings (EXPLORE)
- `_SPEC_*.md` - Technical specification (DESIGN)
- `_IMPL_*.md` - Implementation plan (DESIGN)
- `_TEST_*.md` - Test plan (DESIGN)

### SOLVE

Primary output is knowledge, decisions, or documents. Triggers: "Research...", "Evaluate...", "Write...", "Decide..."

Assessment: RESEARCH / ANALYSIS / EVALUATION / WRITING / DECISION / HOTFIX / BUGFIX

Note: HOTFIX/BUGFIX are SOLVE because primary focus is understanding the problem; code fix is secondary.

## Stuck Detection

If no progress after retry limit:
1. [CONSULT] with [ACTOR]
2. Document in PROBLEMS.md
3. Either get guidance or [DEFER] and continue
