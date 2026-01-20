---
description: Initialize a new development session
auto_execution_mode: 1
---

## Required Skills

Invoke these skills before proceeding:
- @session-management for session folder structure and tracking files

## Step 1: Check for Existing Session

Check if the user has given you a [SESSION_FOLDER] to work in.
If path already contains NOTES.md, PROGRESS.md, PROBLEMS.md: Execute /session-resume instead.

## Step 2: Create Session Folder

If no [SESSION_FOLDER] provided, create one in the default sessions folder with naming scheme:
`_YYYY-MM-DD_[PROBLEM_DESCRIPTION]/`
[PROBLEM_DESCRIPTION] should contain only alphanumerical characters without spaces.

## Step 3: Create Session Documents

In the [SESSION_FOLDER], create tracking files from @session-management templates:

- `NOTES.md` - Include "Current Phase" section for EDIRD tracking
- `PROGRESS.md` - Include "Phase Plan" section with 5 phases
- `PROBLEMS.md` - Track issues discovered during session

## Step 4: Initialize Phase Tracking

Add to NOTES.md:
```markdown
## Current Phase

**Phase**: EXPLORE
**Workflow**: (pending assessment)
**Assessment**: (pending)
```

Add to PROGRESS.md:
```markdown
## Phase Plan

- [ ] **EXPLORE** - in_progress
- [ ] **DESIGN** - pending
```

## Step 5: Document Agent Instructions

Read rules and write key instructions into NOTES.md under "IMPORTANT: Cascade Agent Instructions".

**[SESSION_DOCUMENTS]**:
- Information Document: `INFO_[SPEC_TOPIC].md`
- Specifications: `SPEC_[SPEC_TOPIC].md`
- Implementation plans: `IMPL_[SPEC_TOPIC].md`
- Test plans: `TEST_[SPEC_TOPIC].md`
- Problem tracker: `PROBLEMS.md` - to keep track of all problems that the user brings in and that pop up in the session
- Progress tracker: `PROGRESS.md` - to keep track of 1) all things to do, 2) already done, 3) already tried but not used
- Knowledge tracker: `NOTES.md` - to keep track of all information and code that need to be remembered across sessions and agents. 

Read the rules in the windsurf rules folder again and write the most important rules into the `NOTES.md` file into a section at the top `# IMPORTANT: Cascade Agent Instructions`
Example: Don't use tables in markdown files.