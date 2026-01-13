---
auto_execution_mode: 1
---

First find out what the context is:

- Information Gathering
- Specifications
- Implementation Plans
- Implementations
- Testing

Then read relevant section below and create a verification task list.

**Information Gathering:**
- Think first: How would another person approach this? Is the scope and trajectory aligned with the problem or question?
- Verify sources. Read them again and verify or complete findings. Drop all sources that can't be found. 
- Ask questions that a reader might ask and clarify them.
- Read do-research.md and again and verify against instructions.

**Specifications:**
- Verify against the spec requirements and the existing code.
- Look for bugs, inconsistencies, contradictions, ambiguities, underspeced behavior
- Think of corner cases we haven't covered yet.
- Ensure we have a detailed changes / additions plan.
- Ensure we have en exhausting implementation verification checklist at the end.
- Read implementation-specification-rules.md again and verify against rules.

**Implementation Plans:**
- Read spec again and verify against spec. Anything forgotten or not implemented as in SPEC?
- Read coding rules again (python-rules.md) and verify against rules.

**Implementations:**
- Read specs and plans again and verify against specs.
- Are there existing tests that we can run to verify?
- Can we do quick one-off tests to verify we did not break things?
- Read coding rules again (python-rules.md) and verify against rules.

Then re-read the previous conversation, provided and relevant files. Make an internal "MUST-NOT_FORGET" list and review / edit it after each step.

FINALLY:

Re-read relevant rules and session files. Identify de-prioritized or violated instructions. Add tasks to verification task list.

Work through verification task list.

After reaching the goal, verify again against MUST-NOT_FORGET list.
