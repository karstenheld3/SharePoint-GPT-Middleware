---
description: Run tests based on scope and context
phase: IMPLEMENT
---

# Test Workflow

Implements [TEST] verb from EDIRD model.

## Required Skills

- @ms-playwright-mcp for UI testing (SCOPE-UI only)

## Context Branching

Check scope and proceed accordingly:

### SCOPE-UI

Test UI functionality using Playwright MCP server.

1. [GATHER] UI requirements from SPEC or TEST plan
2. [TEST] using `mcp0_execute` for browser automation
3. Use `accessibilitySnapshot` for element discovery
4. Use `screenshotWithAccessibilityLabels` for visual verification
5. Document results in PROGRESS.md

### SCOPE-CODE

Test code against IMPL and TEST plans.

1. [GATHER] test cases from TEST plan (or IMPL if no TEST)
2. [TEST] using existing test framework or temporary scripts
3. For temporary scripts: prefix with `.tmp_` for cleanup
4. [VERIFY] all test cases pass
5. Document failures in PROBLEMS.md

### SCOPE-BUILD

Test if build prerequisites are fulfilled.

1. [GATHER] build requirements from README.md or NOTES.md
2. [VERIFY] dependencies installed (package.json, requirements.txt, etc.)
3. [VERIFY] environment variables configured
4. [TEST] build command executes successfully
5. Document missing prerequisites in PROBLEMS.md

### SCOPE-DEPLOY

Test if deployment succeeded.

1. [VERIFY] deployment target accessible
2. [TEST] health endpoints respond
3. [TEST] core functionality works in deployed environment
4. [VERIFY] no errors in deployment logs
5. Document deployment issues in PROBLEMS.md

## Verb Sequence

1. [ASSESS] which scope applies
2. Execute scope-specific steps above
3. [DOCUMENT] results (pass/fail with details)
4. If failures: [FIX] or escalate to [CONSULT]

## Gate Check: TEST→next

- [ ] All tests executed
- [ ] Results documented
- [ ] Failures addressed or tracked in PROBLEMS.md

**Pass**: Continue workflow | **Fail**: [FIX] and re-run

## Rules

- Always run tests before [COMMIT]
- Use existing test infrastructure when available
- Clean up `.tmp_*` test files after completion
- Document flaky tests in PROBLEMS.md with reproduction steps
