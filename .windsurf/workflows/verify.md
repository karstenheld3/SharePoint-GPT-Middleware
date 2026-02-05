---
description: Verify work against specs and rules
auto_execution_mode: 1
---

# Verify Workflow

Verify work against specs, rules, and quality standards.

## Required Skills

Invoke these skills based on context:
- @write-documents for document verification
- @coding-conventions for code verification

**CRITICAL**: Skill invocation returns instructions only. You MUST also read the supporting files listed in skill output (e.g., `PYTHON-RULES.md`, `WORKFLOW-RULES.md`) to get actual verification rules.

## Mandatory Re-read

**SESSION-BASED mode** - Re-read session folder documents:
- NOTES.md
- PROBLEMS.md
- PROGRESS.md
- FAILS.md
- LEARNINGS.md (if exists)

**PROJECT-WIDE mode** - Re-read workspace-level documents:
- README.md
- !NOTES.md or NOTES.md
- !PROBLEMS.md or PROBLEMS.md (if exists)
- !PROGRESS.md or PROGRESS.md (if exists)
- FAILS.md
- LEARNINGS.md (if exists)

## Workflow

1. First find out what the context is (INFO, SPEC, IMPL, Code, TEST, Session)
2. Read GLOBAL-RULES and Verification Labels
3. Read the relevant Context-Specific section
4. Create a verification task list
5. Work through verification task list
6. Run Final Steps

## GLOBAL-RULES

Apply to ALL document types and contexts:

- Avoid excessive acronyms. Write out acronyms on first usage.
  - BAD: `SPN not supported.`
  - GOOD: `Service Principal Name (SPN) not supported.`
- Use verification labels consistently (see below)
- Re-read relevant rules and session files before verifying
- Make internal "MUST-NOT-FORGET" list and check after each step
- If product names are used, make sure there are spelled correctly. Do web research when needed.
  - BAD: Sharepoint -> GOOD: SharePoint
  - BAD: AI Foundry Remote SharePoint -> GOOD: "SharePoint tool" for Azure AI Foundry Agent Service
- **Avoid Markdown tables** - Convert to lists:
  - Tables found? → Convert to unnumbered lists with bold labels
  - Exception: README.md may use tables without `<DevSystem>` tag
  - Only [ACTOR] may add `<DevSystem MarkdownTablesAllowed=true />` exception to other files
- **Avoid emojis** - Remove or replace with text:
  - Emojis found? → Replace with text equivalents (Yes/No/Warning)
  - Exception: README.md may use emojis without `<DevSystem>` tag
  - Only [ACTOR] may add `<DevSystem EmojisAllowed=true />` exception to other files

## Verification Labels

Apply these labels to findings, requirements, and decisions in all document types:

- `[ASSUMED]` - Unverified assumption, needs validation
- `[VERIFIED]` - Finding verified by re-reading source or comparing with other sources
- `[TESTED]` - Tested in POC (Proof-Of-Concept) or minimal test script
- `[PROVEN]` - Proven to work in actual project via implementation or tests

**Usage by document type:**
- INFO: Label key findings and source claims
- SPEC: Label design decisions and assumptions
- IMPL: Label edge case handling and implementation choices
- TEST: Label expected behaviors and test assertions

**Progression:** `[ASSUMED]` → `[VERIFIED]` → `[TESTED]` → `[PROVEN]`

## Final Steps

1. Re-read previous conversation, provided and relevant files
2. Identify de-prioritized or violated instructions
3. Add tasks to verification task list
4. Work through verification task list
5. Verify again against MUST-NOT-FORGET list

# CONTEXT-SPECIFIC

## Information Gathering (INFO)

- Think first: How would another person approach this? Is scope aligned with problem?
- Verify Summary section exists with copy/paste-ready key findings (mandatory)
- Verify sources. Read them again and verify or complete findings.
- Drop all sources that can't be found.
- Ask questions that a reader might ask and clarify them.
- Verify Timeline field is present and accurate (Created date, update count, date range)
- Verify Document History section exists and is up to date
- Read `[AGENT_FOLDER]/workflows/research.md` again and verify against instructions.

## Specifications (SPEC)

- Verify Timeline field is present and accurate (Created date, update count, date range)
- Verify MUST-NOT-FORGET section exists and rules are followed
- Verify against spec requirements and existing code.
- Look for bugs, inconsistencies, contradictions, ambiguities, underspeced behavior.
- Think of corner cases we haven't covered yet.
- Ensure detailed changes/additions plan exists.
- Ensure exhaustive implementation verification checklist at end.
- Verify Document History section exists and is up to date
- Read @write-documents skill again and verify against rules.
- Verify against @write-documents `SPEC_RULES.md` (required for all SPEC documents)

## Implementation Plans (IMPL)

- Verify Timeline field is present and accurate (Created date, update count, date range)
- Verify MUST-NOT-FORGET section exists and rules are followed
- Read spec again and verify against spec.
- Anything forgotten or not implemented as in SPEC?
- Verify Document History section exists and is up to date
- Read @coding-conventions skill again and verify against rules.

## Implementations (Code)

- Read specs and plans again and verify against specs.
- Are there existing tests that we can run to verify?
- Can we do quick one-off tests to verify we did not break things?
- Read @coding-conventions skill again and verify against rules.

## Testing (TEST)

- Verify Timeline field is present and accurate (Created date, update count, date range)
- Verify MUST-NOT-FORGET section exists and rules are followed
- Verify test strategy matches spec requirements
- Check test priority matrix:
  - MUST TEST: Critical business logic covered?
  - SHOULD TEST: Important workflows included?
  - DROP: Justified reasons for skipping?
- Verify test cases:
  - All edge cases from IMPL plan have corresponding TC-XX
  - Format: Description -> ok=true/false, expected result
  - Grouped by category
- Check test data:
  - Required fixtures defined?
  - Setup/teardown procedures clear?
- Verify test phases:
  - Ordered execution sequence logical?
  - Dependencies between phases documented?
- Cross-check against spec:
  - Every FR-XX has at least one TC-XX
  - Every EC-XX has corresponding test
- Verify Document History section exists and is up to date

## Workflows

- Verify structure follows GLOBAL-RULES + CONTEXT-SPECIFIC pattern (recommended)
- Verify workflow references use inline code format: `/verify`, `/research`
- Verify AGEN verb format: `[VERB](params)`
- Read @coding-conventions `WORKFLOW-RULES.md` and verify against rules

## Session Tracking (NOTES, PROBLEMS, PROGRESS)

**Verify NOTES.md:**
- Session Info complete (Started date, Goal)?
- Key Decisions documented?
- Important Findings recorded?
- Workflows to Run on Resume listed?
- Agent instructions still valid?

**Verify PROBLEMS.md:**
- All discovered issues documented?
- Status marked (Open/Resolved/Deferred)?
- Root cause identified for resolved items?
- Deferred items have justification?
- **Sync check**: Which problems should move to project-level PROBLEMS.md?

**Verify PROGRESS.md:**
- To Do list current?
- Done items marked with [x]?
- Tried But Not Used documented (avoid re-exploring)?
- Test coverage analysis up to date?
- **Sync check**: Which findings should move to project-level docs?

**Session Close Sync Checklist:**
- [ ] Resolved problems with project impact → sync to project PROBLEMS.md
- [ ] Reusable patterns/decisions → sync to project NOTES.md
- [ ] Discovered bugs in unrelated code → create issues or sync to PROBLEMS.md
- [ ] New agent instructions → sync to project rules or NOTES.md

## STRUT Plans (Planning Phase)

Verify when STRUT plan is created or updated:

- [ ] Every Objective links to at least one Deliverable (`← P1-Dx`)
- [ ] Unlinked Objectives flagged - require [ACTOR] confirmation at transition
- [ ] All Deliverables have clear completion criteria
- [ ] Transitions reference Deliverables (not Objectives)
- [ ] Steps use valid AGEN verbs with `[VERB](params)` format
- [ ] Problem/goal addressed by Objectives?
- [ ] Strategy includes approach summary (AWT estimate optional)

## STRUT Plans (Transition Phase)

Verify before phase transition (when evaluating Transitions):

- [ ] All Deliverables in Transition condition are checked?
- [ ] For each Objective: are ALL linked Deliverables checked?
- [ ] Deliverable evidence supports Objective claim?
- [ ] Unlinked Objectives: [ACTOR] confirmation obtained?
- [ ] Transition target is valid (`[PHASE-NAME]`, `[CONSULT]`, or `[END]`)?

**Objective Verification Rule:**
- Objective is verified when ALL linked Deliverables are checked
- Check Objective checkbox only after confirming linked Deliverables
- If Objective has no links (`←`), require explicit [ACTOR] confirmation

