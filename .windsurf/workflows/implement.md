---
description: Execute implementation from IMPL plan
phase: IMPLEMENT
---

# Implement Workflow

## Required Skills

- @coding-conventions for coding style
- @write-documents for tracking

## Context Branching

Check what documents exist and proceed accordingly:

### No SPEC, IMPL, TEST documents

[IMPLEMENT] whatever was proposed or specified in conversation.

### Existing INFO only

Run `/write-spec` → [WRITE-SPEC](INFO, Problem or Feature)

### Existing SPEC only

Run `/write-impl-plan` → [WRITE-IMPL-PLAN](SPEC)

### Existing IMPL only

Run `/write-test-plan` → [WRITE-TEST-PLAN](IMPL)

### Existing TEST (no test code)

[IMPLEMENT] function skeletons from IMPL, then full failing tests from TEST.

### Existing TEST + test code

[IMPLEMENT] full implementations from IMPL in small verifiable steps.

## Phase: IMPLEMENT

**Entry gate:** DESIGN→IMPLEMENT passed (IMPL plan exists)

### Verb Sequence

1. For each step in IMPL plan:
   - [IMPLEMENT] code changes
   - [TEST] verify step works
   - [FIX] if tests fail (per retry limits)
   - [COMMIT] when green
2. [VERIFY] against IMPL plan

### Gate Check: IMPLEMENT→REFINE

- [ ] All steps from IMPL plan implemented
- [ ] Tests pass
- [ ] No TODO/FIXME left unaddressed
- [ ] Progress committed

**Pass**: Run `/refine` | **Fail**: Continue [IMPLEMENT]

## Stuck Detection

If 3 consecutive [FIX] attempts fail:
1. [CONSULT] with [ACTOR]
2. Document in PROBLEMS.md
3. Either get guidance or [DEFER] and continue

## Attitude

- Senior engineer, anticipating complexity, reducing risks
- Completer / Finisher, never leaves clutter undocumented
- Small cycles: [IMPLEMENT]→[TEST]→[FIX]→green→next

## Rules

- Use small, verifiable steps - never implement large untestable chunks
- Track progress in PROGRESS.md after each [COMMIT]
- Document problems in PROBLEMS.md immediately when found
- Remove temporary `.tmp_*` files after implementation complete