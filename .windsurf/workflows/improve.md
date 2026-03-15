---
description: Find and fix contradictions, inconsistencies, and improvement opportunities
---

# Improve Workflow

Autonomous self-improvement. Find issues, fix immediately. No user consultation.

## Issue Categories

1. Contradictions
2. Inconsistencies
3. Ambiguities
4. Underspecified behavior
5. Broken dependencies
6. Incorrect/unverified assumptions
7. Flawed logic/thinking
8. Unnecessary complexity
9. new solutions for already solved problems
10. Concept overlap
11. Broken rules

## Workflow

1. Scope: file path → that file; folder → all .md/code; none → conversation context
2. Re-read dependencies before assessing:
   - Rules: `[AGENT_FOLDER]/rules/*.md`
   - Workspace: README, NOTES, ID-REGISTRY, FAILS, LEARNINGS
   - Scope-specific: SPEC→INFO, IMPL→SPEC, TEST→SPEC+IMPL, workflow→`WORKFLOW-RULES.md`
   - Session: NOTES, PROBLEMS, PROGRESS (if SESSION-MODE)
3. Build internal issue list with location, severity, fix
4. Create fix plan (CRITICAL first, then HIGH, group related)
5. Execute fixes, update Document History
6. Verify: re-read, check for regressions

## Fix Rules

- Preserve IDs (FR-XX, DD-XX)
- Pick simplest fix when multiple valid options
- Remove broken refs or add missing targets
