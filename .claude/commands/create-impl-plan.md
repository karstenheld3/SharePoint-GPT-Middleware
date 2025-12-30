
# Create Implementation Plan Workflow

Creates a `_VX_IMPL_[COMPONENT].md` file following project conventions.

## Prerequisites

1. Read `.windsurf/rules/implementation-specification-rules.md` for formatting rules
2. Identify source spec: `_VX_SPEC_[COMPONENT].md` or user task description
3. Read related specs listed in "Depends on" section of source spec

## Workflow Steps

### Step 1: Analyze Scope

**Type** (determines backward compat requirement):
- **New feature**: Creates new files/functions
- **Modification**: Changes existing code (requires backward compatibility test)
- **Fix**: Bug fix or correction (requires backward compatibility test)

**Complexity** (determines plan depth):
- **Small**: Single file, <50 lines changed, ~500 line plan
- **Medium**: 2-3 files, <200 lines changed, ~1000 line plan
- **Complex**: 4+ files or architectural change, ~2500 line plan

If modification or fix:
- Add "Backward Compatibility Test" section (see Step 8)
- Name the test `[EXISTING_CODE_FILE]_test_fix.py` (choose main changed code file)
- If `[EXISTING_CODE_FILE]_test_fix.py` exists, use `[EXISTING_CODE_FILE]_test_fix2.py`

### Step 2: Determine Plan ID

Derive a unique Plan ID prefix:

**If source spec uses IDs** (e.g., `[SPEC_ID]-FR-01`):
1. Extract prefix from spec (e.g., `[SPEC_ID]` from `[SPEC_ID]-FR-01`)

**If no spec exists or spec has no IDs**:
1. Create a fitting `[SPEC_ID]`: 2-4 uppercase letters describing the component
   - Examples: `AUTH` for authentication, `SYNC` for sync feature, `RPTS` for reports

**Then determine plan number:**
2. Grep workspace for existing plan IDs: `grep -r "[SPEC_ID]-IP" --include="*.md"`
3. Assign next available: `IP01` if none found, else increment (IP02, IP03, ...)
4. For A/B comparison plans: use `IP01A` and `IP01B`

Note: `[SPEC_ID]` in examples below is a placeholder - replace with your actual prefix.

**ID suffixes for plan items:**
- **EC**: Edge Case (e.g., `[SPEC_ID]-IP01-EC-01`)
- **IS**: Implementation Step (e.g., `[SPEC_ID]-IP01-IS-01`)
- **VC**: Verification Checklist item (e.g., `[SPEC_ID]-IP01-VC-01`)
- **TST**: Test item or script (e.g., `[SPEC_ID]-IP01-TST-01`)

Note: Plan ID is NOT used in filename. User defines filename.

### Step 3: Create Header Block

```markdown
# Implementation Plan: [Feature Name]

**Plan ID**: [SPEC_ID]-IP01 (or leave blank if spec has no IDs)
**Goal**: Single sentence describing what will be implemented
**Target files**:
- `/path/to/file1.py` (NEW | EXTEND | MODIFY)
- `/path/to/file2.py` (NEW | EXTEND | MODIFY)

**Depends on:**
- `_VX_SPEC_[X].md` for [what it provides]

**Does not depend on:**
- `_VX_SPEC_[Y].md` (explicitly exclude if might seem related)
```

### Step 4: Identify Domain Objects and Actions

Before implementation, list what exists and what operations apply:

```markdown
## Domain Objects

- **[Object1]**: Description, key fields
- **[Object2]**: Description, relationships

## Actions

- **[Action1]**: Input -> Output, who triggers it
- **[Action2]**: Input -> Output, preconditions
```

This drives edge case identification in Step 5.

### Step 5: Identify Edge Cases

Derive edge cases from domain objects and actions. Categories:

**Input boundaries**:
- Empty/null/missing required fields
- Max length, invalid format, special characters
- Duplicate values, conflicting inputs

**State transitions**:
- Invalid state for action (e.g., pause already-paused job)
- Concurrent modifications
- Interrupted operations (crash mid-process)

**External failures**:
- Network timeout, API rate limit
- File locked, permission denied
- Disk full, path too long

**Data anomalies**:
- Referenced item missing
- Corrupt/malformed data
- Orphan records

Format (use IDs if spec has them):
```markdown
## Edge Cases

- **[SPEC_ID]-IP01-EC-01**: [Scenario] -> [Expected handling]
- **[SPEC_ID]-IP01-EC-02**: [Scenario] -> [Expected handling]
```

### Step 6: Write Implementation Steps

For each step:
- **Location**: File and function/class where change goes
- **Action**: What to add/modify/remove
- **Code snippet**: Minimal example showing the change
- **Dependencies**: Any imports or helpers needed

Format:
```markdown
### [SPEC_ID]-IP01-IS-01: [Action Description]

**Location**: `filename.py` > `function_name()` or after `existing_function()`

**Action**: [Add | Modify | Remove] [description]

**Code**:
```python
def new_function(...):
  ...
```

**Note**: [Any gotchas or important details]
```

### Step 7: Define Test Cases

Group by category. Use list format:

```markdown
## Test Cases

### Category 1: [Name] (N tests)

- **[SPEC_ID]-IP01-TST-01**: Description -> ok=true, specific result
- **[SPEC_ID]-IP01-TST-02**: Error case -> ok=false, error message
```

For selftest endpoints: Include error cases, CRUD operations, edge cases.

### Step 8: Backward Compatibility Test (if modifying existing code)

**REQUIRED** when the change might break existing functionality.

```markdown
## Backward Compatibility Test

**Purpose**: Verify existing behavior is preserved after changes.

**Test script**: `_VX_IMPL_[COMPONENT]_backcompat_test.py`

**Run BEFORE implementation**:
```bash
python _VX_IMPL_[COMPONENT]_backcompat_test.py > backcompat_before.txt
```

**Run AFTER implementation**:
```bash
python _VX_IMPL_[COMPONENT]_backcompat_test.py > backcompat_after.txt
diff backcompat_before.txt backcompat_after.txt
```

**Test coverage**:
- [ ] Existing endpoint X returns same structure
- [ ] Existing function Y produces same output for inputs A, B, C
- [ ] Existing behavior Z unchanged

**Script template**:
```python
# _VX_IMPL_[COMPONENT]_backcompat_test.py
import httpx, json

BASE_URL = "http://localhost:8000"

def test_existing_endpoint():
  r = httpx.get(f"{BASE_URL}/path?param=value")
  print(f"GET /path: {r.status_code}")
  print(json.dumps(r.json(), indent=2))

def test_existing_function():
  from module import function
  result = function(input)
  print(f"function(input): {result}")

if __name__ == "__main__":
  test_existing_endpoint()
  test_existing_function()
```
```

### Step 9: Create Final Checklist

Group by phase. Use checkbox format:

```markdown
## Checklist

### Prerequisites
- [ ] **[SPEC_ID]-IP01-VC-01**: Related specs read and understood
- [ ] **[SPEC_ID]-IP01-VC-02**: Backward compatibility test created (if applicable)
- [ ] **[SPEC_ID]-IP01-VC-03**: Backward compatibility test run BEFORE changes

### Implementation
- [ ] **[SPEC_ID]-IP01-VC-04**: IS-01 completed
- [ ] **[SPEC_ID]-IP01-VC-05**: IS-02 completed
- [ ] ...

### Verification
- [ ] **[SPEC_ID]-IP01-VC-XX**: All test cases pass
- [ ] **[SPEC_ID]-IP01-VC-XX**: Backward compatibility test run AFTER (diff empty or expected)
- [ ] **[SPEC_ID]-IP01-VC-XX**: Manual verification in UI (if applicable)
```

### Step 10: Final Review - No Tables

**IMPORTANT**: Review the entire plan and convert any tables to list format.

Tables are **NOT ALLOWED** in implementation plans. Use lists instead:

**BAD (table):**
```markdown
| Test | Expected | HTTP |
|------|----------|------|
| GET /get without job_id | ok=false | 200 |
```

**GOOD (list):**
```markdown
- **[SPEC_ID]-IP01-TST-01**: GET /get without job_id -> ok=false (200)
```

Common sections that accidentally use tables:
- Test cases
- Edge cases / corner cases
- Router changes by file
- Parameter lists
- Verification matrices

## Output File

Save as: `_VX_IMPL_[COMPONENT].md` in workspace root

For complex implementations with alternatives:
- `_VX_IMPL_[COMPONENT]_A.md`
- `_VX_IMPL_[COMPONENT]_B.md`
- `_VX_IMPL_[COMPONENT]_AB_COMPARISON.md`

## Quality Criteria

The plan is complete when:
1. **Traceable**: Every spec requirement has a corresponding implementation step
2. **Executable**: An AI agent can follow steps without asking questions
3. **Verifiable**: Checklist covers all changes
4. **Safe**: Backward compatibility test exists for modifications
5. **Formatted**: No tables - all data in list format