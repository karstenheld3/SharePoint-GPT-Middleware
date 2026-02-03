# Learnings

**Goal**: Extract transferable lessons from resolved problems

## Table of Contents

1. [Learnings](#learnings-1)
2. [Document History](#document-history)

## Learnings

### `SITE-LN-001` Quote Escaping in Generated JavaScript

**Source**: `SITE-FL-001` (JavaScript syntax error from unescaped quotes)

#### Problem Classification

- **Workflow**: BUILD
- **Complexity**: COMPLEXITY-MEDIUM (new router, multiple files)
- **Pattern**: Copying existing code without understanding generation pipeline

#### Context at Decision Time

- **Available**: `domains.py` as reference pattern with working onclick handlers
- **Not available**: Understanding of how `common_ui_functions_v2.py` generates button onclick in `renderItemRow()`
- **Constraints**: User requested "copy domains.py patterns exactly"

#### Assumptions Made

- `[VERIFIED]` Standard onclick handlers like `showEditSiteForm('{itemId}')` work correctly
- `[UNVERIFIED]` All onclick string patterns would be handled the same way
- `[CONTRADICTS]` Single quotes in `showNotImplemented('File Scan')` would work like other buttons

#### Rationale

- **Decision**: Copy domains.py pattern, add new placeholder buttons with `showNotImplemented()` function
- **Trade-off**: Speed of implementation over deep understanding of JS generation pipeline
- **Gap**: domains.py has no placeholder buttons with static string arguments

#### Outcome Gap

- **Expected**: All buttons work, JS loads correctly
- **Actual**: Entire router-specific JS failed to parse
- **Divergence point**: The `showNotImplemented('...')` pattern was new - not copied from domains.py

#### Evidence

```
Browser console:
- "missing ) after argument list"
- "ReferenceError: showNewSiteForm is not defined"

Generated JS (wrong):
btns.push('<button ... onclick=\"showNotImplemented('File Scan')\">...');
                                               ^-- quote collision
```

#### Problem Dependency Tree

```
[Root: Quote collision in generated JS]
├─> [Factor: Using single quotes in onclick value]
│   └─> [Symptom: JS syntax error breaks entire script block]
└─> [Factor: common_ui_functions_v2 wraps onclick in single quotes]
    └─> [Symptom: All functions in script block become undefined]
```

#### Root Cause Analysis

1. **Root cause**: When `common_ui_functions_v2.py` generates button onclick handlers in `renderItemRow()`, it wraps the onclick value in single quotes. Using single quotes inside that value causes quote collision.

2. **Counterfactual**: If I had inspected the generated HTML/JS output (via curl or view-source) before browser testing, the syntax error would have been immediately visible.

3. **Prevention**: When adding onclick handlers with string arguments:
   - Use escaped double quotes `\"...\"` for inner strings
   - Or verify generated output before browser testing
   - Or check how the generation function handles the onclick value

#### Transferable Lesson

**Pattern**: Python-to-JS string generation  
**Rule**: Always use escaped double quotes `\"...\"` for string literals inside onclick handlers that will be processed by UI generation functions.

**Applies to**:
- `common_ui_functions_v2.py` button definitions
- Any dict-based UI configuration that generates JS
- Similar patterns in other V2 routers

**Quick check**: If your onclick contains `('...')`, change to `(\"...\")`.

## Document History

**[2026-02-03 09:33]**
- Added SITE-LN-001: Quote escaping in generated JavaScript
