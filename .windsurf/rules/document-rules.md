---
trigger: always_on
---

# Document Rules

Rules for writing project documentation: INFO, SPEC, IMPL, TEST, and FIX documents.

## MUST-NOT-FORGET

- Use lists, not Markdown tables
- No emojis - ASCII only, no `---` markers between sections
- Use box-drawing characters (├── └── │) for trees
- ASCII UI diagrams have no line width limitation
- Research APIs on official docs before suggesting usage
- List assumptions at start - let user verify before proceeding
- High complexity: propose 2-3 implementation alternatives before committing
- Place TOC after header block (or after MUST-NOT-FORGET if present)
- ID-System: `**XXXX-FR-01:**`, `**XXXX-IG-01:**`, `**XXXX-DD-01:**` (FR=Functional, IG=Guarantee, DD=Decision)
- Be exhaustive: list ALL domain objects, workflows, actions, ui elements, functions
- Include "What we don't want" in Scenario section
- Spec Changes at end, format: `**[YYYY-MM-DD HH:MM]**`, reverse chronological, prefixes: Added, Changed, Fixed, Removed

## Table of Contents

1. [Common Rules](#1-common-rules)
2. [INFO Documents](#2-info-documents)
3. [SPEC Documents](#3-spec-documents)
4. [IMPL Documents](#4-impl-documents)
5. [TEST Documents](#5-test-documents)
6. [FIX Documents](#6-fix-documents)

## 1. Common Rules

### 1.1 File Naming

- `_INFO_[TOPIC].md` - Research, analysis, preparation documents
- `_SPEC_[COMPONENT].md` - Technical specifications
- `_SPEC_[COMPONENT]_UI.md` - UI specifications
- `_IMPL_[COMPONENT].md` - Implementation plans
- `_IMPL_[COMPONENT]_FIXES.md` - Fix tracking during implementation
- `_TEST_[COMPONENT].md` - Test specifications
- `!` prefix for priority docs that must be read first (e.g., `!NOTES.md`, `!PROBLEMS.md`)

### 1.2 Agent Behavior

- Be extremely concise. Sacrifice grammar for concision.
- NEVER ask for continuations when following plans.
- Before assumptions, propose 2-3 implementation alternatives.
- List assumptions at spec start for user verification.
- Optimize for simplicity.
- Re-use existing code by default (DRY principle).
- Avoid costly infrastructure (extra databases, servers, etc.).
- Research APIs before suggesting; rely on primary sources only.
- Document user decisions in "Key Mechanisms" and "What we don't want" sections.

### 1.3 Formatting

**Text style:**
- Use ASCII "double quotes" or 'single quotes', not "typographic quotes"
- No emojis in documentation (exception: UI may use limited set)
- Avoid Markdown tables; use unnumbered lists with indented properties
- Use Unicode box-drawing characters (├── └── │) for tree structures
- Try to fit single statements/decisions/objects on a single line

**Structure:**
- Place Table of Contents after header block
- No `---` markers between sections
- One empty line between sections
- Most recent changes at top in changelog sections

### 1.4 Header Block

All documents start with:

```
# [Document Type]: [Title]

**Goal**: Single sentence describing purpose
**Target file**: `/path/to/file.py` (or list for multiple)

**Depends on:**
- `_SPEC_[X].md` for [what it provides]

**Does not depend on:**
- `_SPEC_[Y].md` (explicitly exclude if might seem related)
```

Only include "Depends on" / "Does not depend on" if they have items.

### 1.5 ID System

Use consistent ID prefixes for traceability:

**Format:** `[PREFIX]-[TYPE]-[NUMBER]`

**Prefixes:** 2-4 uppercase letters describing component (e.g., `CRWL` for Crawler, `AUTH` for Authentication)

**Types:**
- `FR` - Functional Requirement
- `IG` - Implementation Guarantee
- `DD` - Design Decision
- `EC` - Edge Case
- `IS` - Implementation Step
- `VC` - Verification Checklist item
- `TC` - Test Case

**Examples:**
- `CRWL-FR-01` - Crawler Functional Requirement 1
- `CRWL-DD-03` - Crawler Design Decision 3
- `CRWL-IP01-IS-05` - Crawler Implementation Plan 01, Step 5

### 1.6 Spec Changes Section

Always at document end, reverse chronological order:

```
## Spec Changes

**[2026-01-12 14:30]**
- Added: "Scenario" section with Problem/Solution/What we don't want
- Changed: Placeholder standardized to `{itemId}` (camelCase)
- Fixed: Modal OK button signature

**[2026-01-12 10:00]**
- Initial specification created
```

**Action prefixes:** Added, Changed, Fixed, Removed, Moved

## 2. INFO Documents

**Purpose:** Research, analysis, and preparation before implementation.

**Filename:** `_INFO_[TOPIC].md`

### 2.1 Structure

1. **Header Block** - Goal, context
2. **Table of Contents**
3. **Research Sections** - Organized by subtopic
4. **Approach Comparison** - Options A/B/C with pros/cons
5. **Recommended Approach** - With rationale
6. **Verification Findings** - Bugs, inconsistencies discovered
7. **Sources** - All URLs and documents consulted
8. **Next Steps** - Actionable items

### 2.2 Rules

- Mark findings as `[TESTED]` or `[ASSUMED]`
- Drop sources that cannot be found or verified
- Remove contradicting/unverified findings
- List all read sources with URL and primary findings at end
- Summarize copy/paste-ready findings at top

### 2.3 Example

```
# Preparation: [Topic]

**Goal**: Find the best approach to implement [feature] for [project].

## Table of Contents

1. [Approaches](#1-approaches)
2. [Approach Comparison](#2-approach-comparison)
3. [Recommended Approach](#3-recommended-approach)
4. [Sources](#4-sources)
5. [Next Steps](#5-next-steps)

## 1. Approaches

### Option A: [Name]

**Description**: Brief explanation.

**Pros**:
- Pro 1
- Pro 2

**Cons**:
- Con 1

### Option B: [Name]
...

## 2. Approach Comparison

- **Speed**: A > B > C
- **Coverage**: C > B > A
- **Complexity**: A < B < C

## 3. Recommended Approach

**Option B** with emphasis on [aspect].

### Phase 1: [Name] (Immediate)
- Step 1
- Step 2

### Phase 2: [Name] (Later)
- Step 3

## 4. Sources

**Primary Sources:**
- `filename.py` - Description of what was analyzed
- https://docs.example.com - API documentation

## 5. Next Steps

1. Create [artifact]
2. Implement [feature]
```

## 3. SPEC Documents

**Purpose:** Define what to build before implementation.

**Filename:** `_SPEC_[COMPONENT].md` or `_SPEC_[COMPONENT]_UI.md`

### 3.1 Structure

1. **Header Block** - Goal, Target file, Depends on
2. **Table of Contents**
3. **Scenario** - Problem, Solution, What we don't want
4. **Context** - Project background, related systems
5. **Domain Objects** - Core entities, data structures
6. **Functional Requirements** - Numbered (`XXXX-FR-01`)
7. **Design Decisions** - Numbered (`XXXX-DD-01`)
8. **Implementation Guarantees** - Numbered (`XXXX-IG-01`)
9. **Key Mechanisms** - Technical patterns, algorithms
10. **Action Flow** - Step-by-step event sequences
11. **Data Structures** - Schemas, API contracts
12. **User Actions** (for UI specs) - All interactive operations
13. **UX Design** (for UI specs) - ASCII diagrams with component boundaries
14. **Implementation Details** - Code organization, function signatures
15. **Spec Changes** - Timestamped changelog (most recent on top)

### 3.2 Rules

- Be exhaustive: list all domain objects, buttons, functions
- Document all edge cases
- Spec length guidelines: small ~500 lines, medium ~1000 lines, complex ~2500 lines

### 3.3 Scenario Section

```
## Scenario

**Problem:** [Real-world problem description]

**Solution:** [High-level approach]
- Bullet point 1
- Bullet point 2

**What we don't want:**
- Anti-pattern 1
- Anti-pattern 2
```

### 3.4 Domain Objects

```
## Domain Objects

### [ObjectName]

A **[ObjectName]** represents [description].

**Storage:** `path/to/storage/`
**Definition:** `config.json`

**Key properties:**
- `property_1` - description
- `property_2` - description

**Schema:**
```json
{
  "field1": "value",
  "field2": 123
}
```
```

### 3.5 Requirements Format

**BAD:**
```
- Toast notifications should support info, success, error types
- Auto-dismiss should be configurable
```

**GOOD:**
```
**UI-FR-01: Toast Notifications**
- Support info, success, error, warning message types
- Auto-dismiss configurable per toast (default 5000ms)

**DD-UI-03:** Declarative button configuration. Buttons use `data-*` attributes for endpoint URL, method, format - no custom JS per action.
```

### 3.6 UI Diagrams

Use ASCII box diagrams with component boundaries. Show ALL buttons and actions.

**BAD:**
```
+-------------------------------------------------------------+
|  Jobs Table (Reactive Rendering)                            |
|  +----+---------+----------+---------+------------------+   |
|  | ID | Router  | Endpoint | State   | Actions          |   |
|  +----+---------+----------+---------+------------------+   |
|  | 42 | crawler | update   | running | [Monitor] [Pause]|   |
|  | 41 | crawler | update   | done    | [Monitor]        |   |
|  +----+---------+----------+---------+------------------+   |
|                                                             |
|  +----------------------------------------------------------+
|  | [Resize Handle - Draggable]                              |
|  | Console Output                                   [Clear] |
|  | ---------------------------------------------------------|
|  | [ 1 / 20 ] Processing 'document_001.pdf'...              |
|  |   OK.                                                    |
|  +----------------------------------------------------------+
|                                                             |
|  +----------------------------------------------------------+
|  | Job Started | ID: 42 | Total: 20 items               [x] | <- Toast
|  +----------------------------------------------------------+
+-------------------------------------------------------------+
```

**GOOD:**
```
Main HTML:
+-------------------------------------------------------------------------------+
|  Streaming Jobs (2)                                                           |
|                                                                               |
|  [Start Job]  [Refresh]                                 [Toasts appear here]  |
|                                                                               |
|  +----+---------+----------+---------+-------------------------------------+  |
|  | ID | Router  | Endpoint | State   | Actions                             |  |
|  +----+---------+----------+---------+-------------------------------------+  |
|  | 42 | crawler | update   | running | [Monitor] [Pause / Resume] [Cancel] |  |
|  | 41 | crawler | update   | done    | [Monitor]                           |  |
|  +----+---------+----------+---------+-------------------------------------+  |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  | [Resize Handle - Draggable]                                             |  |
|  | Console Output                                                  [Clear] |  |
|  | ------------------------------------------------------------------------|  |
|  | [ 1 / 20 ] Processing 'document_001.pdf'...                             |  |
|  |   OK.                                                                   |  |
|  | [ 2 / 20 ] Processing 'document_002.pdf'...                             |  |
|  |   OK.                                                                   |  |
|  +-------------------------------------------------------------------------+  |
|                                                                               |
+-------------------------------------------------------------------------------+

Toast:
+-----------------------------------------------+
| Job Started | ID: 42 | Total: 20 items   [x]  |
+-----------------------------------------------+
```

### 3.7 Layer Architecture Diagrams

For multi-layer systems, use ASCII box diagrams showing call hierarchy:

```
+---------------------------------------------------------------------------+
|  High-Level (Router)                                                      |
|  +-> function_a()         # Called by router endpoints                    |
+---------------------------------------------------------------------------+
|  Mid-Level (Components)                                                   |
|  +-> function_b()         # Generates HTML fragments                      |
|  +-> function_c()         # Generates JavaScript                          |
+---------------------------------------------------------------------------+
|  Low-Level (Helpers)                                                      |
|  +-> json_result()        # Response formatting                           |
+---------------------------------------------------------------------------+
```

### 3.8 Summarize Styling

Avoid too much CSS detail in specs.

**BAD:**
```css
.toast {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-left: 4px solid #0078d4;
  padding: 0.75rem 1rem;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  animation: slideIn 0.3s ease-out;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  color: #212529;
}

.toast.toast-info { border-left-color: #0078d4; }
```

**GOOD:**
```css
.toast { /* Individual toast notification with light theme */ }
.toast.toast-info { /* Blue left border */ }
.toast.toast-success { /* Green left border */ }
```

### 3.9 Code Outline Only

Avoid implementation detail. Focus on architecture completeness. Document intention.

**BAD:**
```javascript
// Render functions
function renderJobRow(job) {
  const actions = renderJobActions(job);
  // Format timestamps consistently (handle both ISO format with T and space format)
  const formatTimestamp = (ts) => {
    if (!ts) return '';
    return ts.substring(0, 19).replace('T', ' ');
  };
  const started = formatTimestamp(job.started);
  const finished = job.finished ? formatTimestamp(job.finished) : '-';
  return `
    <tr id="job-${job.id}">
      <td>${job.id}</td>
      <td>${job.router}</td>
      <td>${job.endpoint}</td>
      <td>${job.state}</td>
      <td>${started}</td>
      <td>${finished}</td>
      <td>${actions}</td>
    </tr>
  `;
}
```

**GOOD:**
```javascript
// Generate <tr> HTML for single job
function renderJobRow(job) { ... }
```

### 3.10 Single Line Statements

Fit single statements/decisions/objects on a single line.

**BAD:**
```html
**Pause Button** (requests job pause):
<button class="btn-small" onclick="controlJob(42, 'pause')">
  Pause
</button>
```

**GOOD:**
```html
**Pause Button** (requests job pause):
<button class="btn-small" onclick="controlJob(42, 'pause')"> Pause </button>
```

### 3.11 Event Flow Documentation

Document call chains with indented arrows.

**GOOD:**
```
User clicks [Pause] or [Resume]
  +-> controlJob(jobId, 'pause' | 'resume')
      +-> fetch(`/testrouter3/control?id=${id}&action=${action}`)
          +-> On success (data.success):
              +-> Optimistically updateJob(jobId, { state: 'paused' | 'running' })
                  +-> renderAllJobs()
                      +-> renderJobActions() # Button changes to Resume/Pause
```

### 3.12 Data Structure Examples

Provide examples for JSON, CSV, and other data formats.

**GOOD:**
```
<start_json>
{"id": 42, "router": "testrouter3", "endpoint": "streaming01", "state": "running", "total": 3, "started": "2025-11-27T11:30:00"}
</start_json>
<log>
[ 1 / 3 ] Processing 'doc_001.pdf'...
  OK.
[ 2 / 3 ] Processing 'doc_002.pdf'...
  OK.
[ 3 / 3 ] Processing 'doc_003.pdf'...
  OK.
</log>
<end_json>
{"id": 42, "state": "completed", "result": "ok", "finished": "2025-11-27T11:30:15"}
</end_json>
```

### 3.13 Spec Changes Format

Use timestamped changelog, reverse chronological. Avoid tables.

**BAD:**
```
| Date | Change |
|------|--------|
| 2024-12-17 | Initial specification created |
| 2024-12-17 | Added Key Mechanisms section |
```

**GOOD:**
```
## Spec Changes

**[2024-12-17 14:30]**
- Added: "Scenario" section with Problem/Solution/What we don't want
- Added: Spec Changes section

**[2024-12-17 11:45]**
- Added: "Key Mechanisms" section with declarative button pattern
- Changed: Placeholder standardized to `{itemId}` (camelCase)
- Fixed: Modal OK button signature to match `callEndpoint(btn, itemId, bodyData)`

**[2024-12-17 10:00]**
- Initial specification created
```

### 3.14 Section Order and Header

**BAD:**
```

**Target files**:

## Scenario
...
---



## Architecture
...
---
```

**GOOD:**
```
# V0 Crawler Toolkit - Standalone SharePoint Crawler

**Goal**: Document the architecture and workflow of the standalone SharePoint-GPT-Crawler-Toolkit.

**Does not depend on:**
- Any V2 specifications (this is the predecessor toolkit)
...

## Overview
...

## Table of Contents
...
```

## 4. IMPL Documents

**Purpose:** Step-by-step implementation plan from spec.

**Filename:** `_IMPL_[COMPONENT].md`

### 4.1 Structure

1. **Header Block** - Plan ID, Goal, Target files (NEW/EXTEND/MODIFY)
2. **Table of Contents**
3. **File Structure** - Tree diagram of files to create/modify
4. **Domain Objects and Actions** - What exists, what operations apply
5. **Edge Cases** - Derived from domain objects (`XXXX-IP01-EC-01`)
6. **Implementation Steps** - Detailed steps (`XXXX-IP01-IS-01`)
7. **Test Cases** - Grouped by category (`XXXX-IP01-TC-01`)
8. **Backward Compatibility Test** (if modifying existing code)
9. **Verification Checklist** - Checkbox format (`XXXX-IP01-VC-01`)

### 4.2 Header Block

```
# Implementation Plan: [Feature Name]

**Plan ID**: CRWL-IP01
**Goal**: Single sentence describing what will be implemented
**Target files**:
- `/path/to/file1.py` (NEW)
- `/path/to/file2.py` (EXTEND)
- `/path/to/file3.py` (MODIFY)

**Depends on:**
- `_SPEC_[X].md` for [what it provides]
```

### 4.3 File Structure

```
## File Structure

/src/module/
├── new_file.py           # Description (~N lines) [NEW]
├── existing_file.py      # Description [EXTEND +N lines]
└── helper.py             # Description [MODIFY]
```

### 4.4 Edge Cases

Derive from domain objects and actions:

```
## Edge Cases

- **CRWL-IP01-EC-01**: Empty input list -> Return empty result, log warning
- **CRWL-IP01-EC-02**: Network timeout -> Retry 3 times, then fail with error
- **CRWL-IP01-EC-03**: Duplicate ID -> Skip and log, continue processing
```

**Categories to consider:**
- Input boundaries (empty, null, max length, invalid format)
- State transitions (invalid state, concurrent modifications)
- External failures (network, file locked, permission denied)
- Data anomalies (missing references, corrupt data)

### 4.5 Implementation Steps

````
### CRWL-IP01-IS-01: [Action Description]

**Location**: `filename.py` > `function_name()` or after `existing_function()`

**Action**: [Add | Modify | Remove] [description]

**Code**:
```python
def new_function(...):
  ...
```

**Note**: [Any gotchas or important details]
````

### 4.6 Test Cases

```
## Test Cases

### Category 1: [Name] (N tests)

- **CRWL-IP01-TC-01**: Description -> ok=true, expected result
- **CRWL-IP01-TC-02**: Error case -> ok=false, error message
```

### 4.7 Verification Checklist

```
## Checklist

### Prerequisites
- [ ] **CRWL-IP01-VC-01**: Related specs read and understood
- [ ] **CRWL-IP01-VC-02**: Backward compatibility test created (if applicable)

### Implementation
- [ ] **CRWL-IP01-VC-03**: IS-01 completed
- [ ] **CRWL-IP01-VC-04**: IS-02 completed

### Verification
- [ ] **CRWL-IP01-VC-10**: All test cases pass
- [ ] **CRWL-IP01-VC-11**: Manual verification in UI
```

## 5. TEST Documents

**Purpose:** Define test strategy, test cases, and verification.

**Filename:** `_TEST_[COMPONENT].md` or `_IMPL_[COMPONENT]_SELFTEST.md`

### 5.1 Structure

1. **Header Block** - Goal, Target file, Depends on
2. **Table of Contents**
3. **Overview** - What the test does
4. **Scenario** - Problem, Solution, What we don't want
5. **Design Decisions** - Test-specific decisions
6. **Test Strategy** - Approach (unit, integration, snapshot-based)
7. **Test Data** - Required test data, setup
8. **Test Matrix** - All test cases organized
9. **Test Phases** - Ordered execution
10. **Helper Functions** - Reusable test utilities
11. **Cleanup** - Artifact removal
12. **Implementation Checklist**

### 5.2 Test Priority Matrix

```
## Test Priority Matrix

### MUST TEST (Critical Business Logic)

- **`function_name()`** - module_name
  - Testability: **EASY**, Effort: Low
  - Description of what to test

### SHOULD TEST (Important Workflows)

- **`function_name()`** - module_name
  - Testability: Medium, Effort: Medium

### DROP (Not Worth Testing)

- **`function_name()`** - Reason: External dependency / UI-only
```

### 5.3 Snapshot-Based Verification

```
## Test Strategy

### Snapshot-Based Verification

Every test follows the same pattern:

1. Restore state from snapshot (or clean for first test)
2. Run operation with specific parameters
3. Compare actual state vs expected snapshot
4. Report pass/fail
```

## 6. FIX Documents

**Purpose:** Track changes and fixes during implementation.

**Filename:** `_IMPL_[COMPONENT]_FIXES.md` or `_FIX_[TOPIC].md`

### 6.1 Structure

1. **Header Block** - Goal, Target files
2. **Table of Contents**
3. **Rules Summary** (if fixing rule violations)
4. **Violations by Category** - Grouped findings
5. **Detailed Fix Plan** - BEFORE/AFTER for each fix
6. **TODO Checklist** - All fixes with checkboxes

### 6.2 BEFORE/AFTER Format

````
## Detailed Fix Plan

### Fix 1: [Description]

**Location**: `filename.py:123`

**BEFORE:**
```python
old_code_here
```

**AFTER:**
```python
new_code_here
```

**Reason**: Explanation of why this change is needed.
````

### 6.3 TODO Checklist

```
## TODO Checklist

### File: `module1.py`
- [ ] Fix 1: Description (line 123)
- [ ] Fix 2: Description (line 456)

### File: `module2.py`
- [ ] Fix 3: Description (line 78)
```

## 7. Document Size Guidelines

- **INFO**: As needed, focus on actionable findings
- **SPEC**: Small ~500 lines, Medium ~1000 lines, Complex ~2500 lines
- **IMPL**: Proportional to spec; include all steps for autonomous execution
- **TEST**: Complete test coverage documentation
- **FIX**: Comprehensive BEFORE/AFTER for all changes
