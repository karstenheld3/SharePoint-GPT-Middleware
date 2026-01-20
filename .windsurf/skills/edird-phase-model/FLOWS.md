# Workflow Flows

Verb sequences for BUILD and SOLVE workflows.

## BUILD COMPLEXITY-HIGH Flow

```
[EXPLORE]
├─> [RESEARCH] → [ANALYZE] → [GATHER] → [ASSESS] → [SCOPE] → [DECIDE]
└─> Gate check

[DESIGN]
├─> [PLAN] → [OUTLINE] → [WRITE-SPEC] → [PROVE] → [PROPOSE] → [VALIDATE]
├─> [WRITE-IMPL-PLAN] → [WRITE-TEST-PLAN]
└─> Gate check

[IMPLEMENT]
├─> [IMPLEMENT] → [CONFIGURE] → [INTEGRATE] → [TEST] → [COMMIT]
└─> Gate check

[REFINE]
├─> [REVIEW] → [VERIFY] → [TEST] → [CRITIQUE] → [RECONCILE] → [FIX]
└─> Gate check

[DELIVER]
├─> [VALIDATE] → [MERGE] → [DEPLOY] → [FINALIZE] → [HANDOFF] → [CLOSE]
└─> [ARCHIVE] if session-based
```

## BUILD COMPLEXITY-LOW Flow

```
[EXPLORE]
├─> [ANALYZE] → [ASSESS] → [DECIDE]
└─> Gate check

[DESIGN]
├─> [OUTLINE]
└─> Gate check

[IMPLEMENT]
├─> [IMPLEMENT] → [TEST] → [COMMIT]
└─> Gate check

[REFINE]
├─> [REVIEW] → [FIX]
└─> Gate check

[DELIVER]
├─> [MERGE] → [CLOSE]
└─> Done
```

## SOLVE EVALUATION Flow

```
[EXPLORE]
├─> [RESEARCH] → [ANALYZE] → [ASSESS] → EVALUATION → [SCOPE] → [ENUMERATE]
└─> Gate check

[DESIGN]
├─> [FRAME] → [OUTLINE] criteria → [DEFINE] evaluation framework → [VALIDATE]
└─> Gate check

[IMPLEMENT]
├─> [RESEARCH] each option → [ANALYZE] against criteria → [EVALUATE] → [SYNTHESIZE]
└─> Gate check

[REFINE]
├─> [REVIEW] → [VERIFY] claims → [CRITIQUE] → [RECONCILE] → [IMPROVE]
└─> Gate check

[DELIVER]
├─> [CONCLUDE] → [RECOMMEND] with rationale → [PRESENT] → [VALIDATE] → [ARCHIVE]
└─> Done
```

## SOLVE WRITING Flow

```
[EXPLORE]
├─> [RESEARCH] topic → [ANALYZE] audience needs → [ASSESS] → WRITING → [SCOPE]
└─> Gate check

[DESIGN]
├─> [FRAME] → [OUTLINE] structure → [PLAN] examples → [VALIDATE] with [ACTOR]
└─> Gate check

[IMPLEMENT]
├─> [DRAFT] → [WRITE] sections → [RESEARCH] additional details → [COMMIT]
└─> Gate check

[REFINE]
├─> [REVIEW] → [CRITIQUE] → [VERIFY] facts → [IMPROVE] prose → [FIX]
└─> Gate check

[DELIVER]
├─> [FINALIZE] → [VALIDATE] with [ACTOR] → [HANDOFF] → [ARCHIVE]
└─> Done
```

## SOLVE HOTFIX Flow

```
[EXPLORE]
├─> [ANALYZE] identify root cause
├─> [GATHER] logs and context
├─> [ASSESS] → HOTFIX
└─> [DECIDE] fix approach
    └─> Gate: Root cause identified

[DESIGN]
├─> [PROVE] fix works
└─> [VALIDATE] with [ACTOR] (if time permits)
    └─> Gate: Fix proven

[IMPLEMENT]
├─> [FIX] apply fix
├─> [TEST] verify fix
└─> [COMMIT] with hotfix message
    └─> Gate: Fix applied, tests pass

[REFINE]
├─> [VERIFY] no regressions
├─> [TEST] regression testing
└─> [REVIEW] quick review
    └─> Gate: No regressions

[DELIVER]
├─> [DEPLOY] immediately
├─> [STATUS] notify stakeholders
└─> [CLOSE] mark resolved
```

## Hybrid Situations

### SOLVE then BUILD

Research best approach, then build it:

```
SOLVE Workflow → Output: Decision/recommendation
        │
        ▼
BUILD Workflow → Use decision as input → Output: Working code
```

Example: "Should we use PostgreSQL or MongoDB?" (SOLVE: EVALUATION) → decision made → "Implement PostgreSQL integration" (BUILD)

### BUILD with Embedded SOLVE

Building requires investigation mid-workflow:

```
BUILD Workflow
├─> [EXPLORE] → [DESIGN]
│                  │
│                  ▼ Encounter unknown
│           ┌─ Mini SOLVE ──────────┐
│           │ [EXPLORE] → [DESIGN]  │
│           │ → [IMPLEMENT] → ...   │
│           │ → [DELIVER](insight)  │
│           └───────────────────────┘
│                  │
│                  ▼ Resume with knowledge
└─> [DESIGN] continued → [IMPLEMENT] → [REFINE] → [DELIVER]
```

Note: Mini SOLVE can also be a POC with full INFO, SPEC, IMPL, TEST documents when the unknown requires validation.

### Switching Workflows

```
IF during [EXPLORE]:
    initial_assessment = BUILD
    BUT primary_output_changes_to_document
THEN:
    [CONSULT] with [ACTOR]: "This looks more like a SOLVE workflow. Confirm?"
    IF confirmed:
        workflow_type = SOLVE
        restart_with_appropriate_verbs
```
