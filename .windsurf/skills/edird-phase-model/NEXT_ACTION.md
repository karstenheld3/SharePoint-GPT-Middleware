# Next Action Logic

Deterministic logic for autonomous agent operation.

## Decision Tree

1. **Check phase gate** → Does it pass?
   - YES → Transition to next phase, start first verb
   - NO → Execute verb that addresses unchecked item
2. **Last verb outcome?**
   - -OK → Proceed to next verb in phase
   - -FAIL → Handle based on verb (see transitions below)
   - -SKIP → Proceed to next verb
3. **No more verbs?** → Re-evaluate gate
4. **In [DELIVER] and done?** → [CLOSE] and [ARCHIVE] if session-based

## Autonomous Mode Algorithm

```
IF gate_passes(current_phase):
    current_phase = next_phase
    current_verb = first_verb_for(current_phase, workflow_type, complexity)
ELSE:
    unchecked = find_unchecked_gate_items()
    current_verb = verb_that_addresses(unchecked[0])
    
EXECUTE current_verb

IF verb_outcome == OK:
    current_verb = next_verb_in_sequence()
ELIF verb_outcome == FAIL:
    current_verb = failure_handler(current_verb)
ELIF verb_outcome == SKIP:
    current_verb = next_verb_in_sequence()
```

## Verb Outcome Transitions

```
[RESEARCH]-OK   → next verb in sequence
[RESEARCH]-FAIL → [CONSULT] (need help finding info)

[ASSESS]-OK     → [SCOPE] or [DECIDE]
[ASSESS]-FAIL   → [RESEARCH] (need more context)

[PROVE]-OK      → [WRITE-SPEC] or proceed to gate check
[PROVE]-FAIL    → [RESEARCH] (back to explore fundamentals)

[VERIFY]-OK     → next verb or gate check
[VERIFY]-FAIL   → [FIX] → [VERIFY] (loop until OK)

[CRITIQUE]-OK   → [RECONCILE]
[CRITIQUE]-FAIL → [FIX] (immediate issues found)

[TEST]-OK       → next verb or gate check
[TEST]-FAIL     → [FIX] → [TEST] (loop until OK)

[VALIDATE]-OK   → proceed
[VALIDATE]-FAIL → [CONSULT] (clarify requirements)

[CONSULT]-OK    → resume previous activity
[CONSULT]-FAIL  → [QUESTION] more specifically, or escalate
```

## Retry Limits

- **COMPLEXITY-LOW**: Infinite retries (until user stops)
- **COMPLEXITY-MEDIUM/HIGH**: Max 5 attempts per phase, then [CONSULT]

When retry limit reached:
1. Log current state to PROBLEMS.md
2. [CONSULT] with [ACTOR]
3. Wait for guidance or [DEFER] and continue

## State Tracking

Agent always knows next action from:
```
next_action = f(workflow_type, current_phase, last_verb_outcome, gate_status)
```

Track in session files:
- NOTES.md: Current phase, last verb, gate status
- PROGRESS.md: Full phase plan with status per phase
