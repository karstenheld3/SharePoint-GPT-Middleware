# Context State Branching

Syntax for conditional logic based on context states.

## Syntax Rules

- **Context states** (no brackets) appear in condition headers
- **Instruction tokens** (brackets) appear in action steps
- Format: `## For CONTEXT-STATE` followed by `[VERB]` instructions

## Examples

### Complexity Branching

```markdown
## For COMPLEXITY-LOW

1. [OUTLINE] brief approach
2. [IMPLEMENT] changes
3. [TEST] and [COMMIT]

## For COMPLEXITY-MEDIUM

1. [WRITE-SPEC] concise specification
2. [PROVE] risky parts with POC
3. [WRITE-IMPL-PLAN] implementation plan
4. [DECOMPOSE] into testable steps
5. [IMPLEMENT] each step with [TEST]

## For COMPLEXITY-HIGH

1. [WRITE-SPEC] comprehensive specification
2. [PROVE] risky parts with POC
3. [PROPOSE] approach to [ACTOR]
4. [WRITE-IMPL-PLAN] detailed plan
5. [DECOMPOSE] into small verifiable steps
6. [IMPLEMENT] with [TEST] after each step
7. [CRITIQUE] and [RECONCILE] in REFINE
```

### Workflow Type Branching

```markdown
## For BUILD

Primary output: Working code
Assessment: COMPLEXITY-LOW/MEDIUM/HIGH
Required: SPEC, IMPL, TEST documents

## For SOLVE

Primary output: Knowledge, decisions, documents
Assessment: RESEARCH/ANALYSIS/EVALUATION/WRITING/DECISION
Focus: Understanding before any code
```

### Problem Type Branching

```markdown
## For HOTFIX

1. [ANALYZE] root cause immediately
2. [PROVE] fix works
3. [FIX] and [DEPLOY] urgently
4. [STATUS] notify stakeholders

## For BUGFIX

1. [INVESTIGATE] to understand behavior
2. [ANALYZE] code path
3. [PROVE] with failing test
4. [FIX] root cause
5. [TEST] regression suite

## For RESEARCH

1. [RESEARCH] topic broadly
2. [SYNTHESIZE] findings
3. [CONCLUDE] with recommendations
4. [WRITE-INFO] to document
```

### Workspace Branching

```markdown
## For SINGLE-PROJECT

[WRITE-INFO] in [WORKSPACE_FOLDER]

## For MONOREPO

[WRITE-INFO] in [PROJECT_FOLDER] for each project
```

## Combining Conditions

Use nested headers for multiple conditions:

```markdown
## For BUILD

### If COMPLEXITY-MEDIUM or higher

[PROVE] with POC before [IMPLEMENT]

### If COMPLEXITY-LOW

Skip [PROVE], proceed directly to [IMPLEMENT]
```
