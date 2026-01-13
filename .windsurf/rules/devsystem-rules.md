---
trigger: always_on
---

# DevSystem Rules

Rules and definitions for the development system used with Windsurf/Cascade.

## Table of Contents

1. [Definitions](#definitions)
2. [Folder Structure](#folder-structure)
3. [File Naming Conventions](#file-naming-conventions)
4. [Placeholders](#placeholders)
5. [Session Management](#session-management)
6. [Document Types](#document-types)
7. [Workflow Reference](#workflow-reference)
8. [Agent Instructions](#agent-instructions)
9. [MUST-NOT-FORGET-LIST](#must-not-forget-list)

## Definitions

### Core Concepts

- **[WORKSPACE]**: The Windsurf/VSCode workspace root folder
- **[PROJECT]**: If Monorepo (workspace contains multiple projects), the project subfolder. No Monorepo: Workspace = Project
- **[SESSION]**: All context belonging to a work session - folder, files, conversations, commits, and tracking files (notes, problems, progress)

### Configuration

- **[RULES]**: The current set of Windsurf rules in `.windsurf/rules/` or project rules folder
- **[WORKFLOWS]**: The current set of Windsurf workflows in `.windsurf/workflows/`

### Document Types

- **[INFO]**: Information gathering from web research, option and code analysis, reading documents
  - `INFO_MICROSOFT_GRAPH_API.md`, `!INFO_PYTHON_CODE_EXAMPLES.md`, `_INFO_NEW_MICROSOFT_GRAPH_API.md`
- **[SPEC]**: A specification conforming to defined rules. When implemented, must be reverse-updated (synced) from verified code changes
  - `SPEC_MODULE.md`, `!SPEC_ARCHITECTURE.md`, `_SPEC_NEW_FEATURE.md`
- **[IMPL]**: An implementation plan. When implemented, must be reverse-updated (synced) from verified code changes
  - `IMPL_MODULE.md`, `!IMPL_MIGRATION.md`, `_IMPL_REFACTOR_A.md`
- **[TEST]**: Testing strategies and test plans
  - `TEST_MODULE.md`, `!TEST_CRITICAL_PATH.md`, `_TEST_NEW_MODULE.md`

**Note:** Prefixes (`!`, `_`) are explained in [File Naming Conventions](#file-naming-conventions).

### Tracking Documents

Tracking documents exist at workspace, project, or session level. Only one of each type per scope.

- **[NOTES]** / **[WNOTES]** / **[PNOTES]** / **[SNOTES]**: Important information about workspace/project/session. Agent MUST read to avoid unintentional behavior
- **[PROGRESS]** / **[WPROGRESS]** / **[PPROGRESS]** / **[SPROGRESS]**: Progress tracking within workspace/project/session. Agent MUST read to avoid unintentional behavior
- **[PROBLEMS]**: Problem tracking within session

## Folder Structure

### Single Project (No Monorepo)

```
[WORKSPACE_FOLDER]/
├─ .windsurf/
│   ├─ rules/              # Windsurf rules (.md files)
│   └─ workflows/          # Windsurf workflows (.md files)
├─ _Archive/               # Archived sessions
├─ _[SESSION_FOLDER]/      # Session folders start with underscore
│   ├─ _IMPL_*.md          # Implementation plans
│   ├─ _INFO_*.md          # Information documents
│   ├─ _SPEC_*.md          # Specifications
│   ├─ NOTES.md            # Session notes
│   ├─ PROBLEMS.md         # Session problems
│   └─ PROGRESS.md         # Session progress
├─ src/                    # Source code
├─ !NOTES.md               # Workspace notes (priority file)
├─ !PROBLEMS.md            # Known problems
└─ !PROGRESS.md            # Overall progress
```

### Monorepo (Multiple Projects)

```
[WORKSPACE_FOLDER]/
├─ .windsurf/
│   ├─ rules/              # Workspace-level rules
│   └─ workflows/          # Workspace-level workflows
├─ _Archive/               # Archived sessions (all projects)
├─ [PROJECT_A]/
│   ├─ _[SESSION_FOLDER]/  # Project A sessions
│   ├─ src/                # Project A source code
│   ├─ !PNOTES.md          # Project A notes
│   └─ !PPROGRESS.md       # Project A progress
├─ [PROJECT_B]/
│   ├─ _[SESSION_FOLDER]/  # Project B sessions
│   ├─ src/                # Project B source code
│   ├─ !PNOTES.md          # Project B notes
│   └─ !PPROGRESS.md       # Project B progress
├─ !WNOTES.md              # Workspace-level notes
└─ !WPROGRESS.md           # Workspace-level progress
```

## File Naming Conventions

### Priority Files and Folders (! prefix)

Files and folders starting with `!` indicate high relevance. This information must be treated with extra attention during priming workflows like `/prime`.

- `!NOTES.md` - Critical workspace/project notes
- `!PROBLEMS.md` - Known problems and issues
- `!PROGRESS.md` - Overall progress tracking
- `!INFO_[TOPIC].md` - Critical information documents
- `!SPEC_[COMPONENT].md` - Critical specifications
- `!IMPL_[COMPONENT].md` - Critical implementation plans

**Note:** In Windsurf / VS Code, sort order is `_` `!` `.` (not ASCII order). The `!` prefix was chosen because `+` sorts after `_` and `.` in Windsurf. Be aware that `!` may cause issues in bash (history expansion) - use single quotes when referencing in shell commands.

### Ignored Files and Folders (_ prefix)

Files and folders starting with `_` indicate low relevance. This information is **skipped by automatic priming workflows** (`/prime`).
Use for work in progress, session-specific, outdated or archived content:
- `_Archive/` - Archived sessions
- `_YYYY-MM-DD_[Description]/` - Session folders
- `_INFO_[TOPIC].md` - Information documents (session-specific)
- `_SPEC_[COMPONENT].md` - Specifications (session-specific)
- `_IMPL_[COMPONENT].md` - Implementation plans (session-specific)
- `_VX_SPEC_*.md` - Versioned specifications (V1, V2, etc.)
- `_VX_IMPL_*.md` - Versioned implementation plans

**Note:** To load session files, use `/session-resume` or read them explicitly.

### Hidden Files and Folders (. prefix)

Files and folders starting with `.` follow Unix convention - hidden from directory listings by default.
Common uses: configuration, system files, version control, IDE settings.
- `.gitignore` - Git ignore patterns
- `.codeiumignore` - Windsurf/Cascade ignore patterns
- `.windsurf/` - Windsurf configuration folder
- `.vscode/` - VS Code configuration folder
- `.tmp_*` - Temporary test/POC files, **must be deleted after use**

## Placeholders

Use these placeholders in rules and workflows:

- **[WORKSPACE_FOLDER]**: Absolute path of root folder where Windsurf operates
- **[PROJECT_FOLDER]**: Absolute path of project folder (same as workspace if no monorepo)
- **[SRC_FOLDER]**: Absolute path of source folder (usually `[WORKSPACE_FOLDER]\src\` or `[PROJECT_FOLDER]\src\`)
- **[SESSION_FOLDER]**: Absolute path of currently active session folder

## Session Management

### Session Lifecycle

1. **Init** (`/session-init`): Create session folder with NOTES.md, PROBLEMS.md, PROGRESS.md
2. **Work**: Create specs, plans, implement, track progress
3. **Save** (`/session-save`): Document findings, commit changes
4. **Resume** (`/session-resume`): Re-read session documents, continue work
5. **Close** (`/session-close`): Sync findings to project files, archive

### Session Folder Naming

Format: `_YYYY-MM-DD_[ProblemDescription]/`

Example: `_2026-01-12_FixAuthenticationBug/`

### Required Session Files

- **NOTES.md**: Key information, agent instructions, working patterns
- **PROBLEMS.md**: Problems found and their status (Open/Resolved/Deferred)
- **PROGRESS.md**: To-do list, done items, tried-but-not-used approaches

### Assumed Workflow

```
1. INIT: User initializes session (`/session-init`)
   └─ Session folder, NOTES.md, PROBLEMS.md, PROGRESS.md created

2. PREPARE (one of):
   A) User prepares work manually
      └─ Creates INFO / SPEC / IMPL documents, tracks progress
   B) User explains problem, agent assists
      └─ Updates Problems, Progress, Notes → researches → creates documents

3. WORK: User or agent implements
   └─ Makes decisions, creates tests, implements, verifies
   └─ Progress and findings tracked continuously

4. SAVE: User saves session for later (`/session-save`)
   └─ Everything updated and committed

5. RESUME: User resumes session (`/session-resume`)
   └─ Agent primes from session files, executes workflows in Notes
   └─ Continue with steps 2-3

6. CLOSE: User closes session (`/session-close`)
   └─ Everything updated, committed, synced to project/workspace

7. ARCHIVE: User archives session
   └─ Session folder moved to _Archive/
```

## Document Types

### Information Documents (_INFO_*.md)

Purpose: Capture research findings, analysis, options

Contents:
- Research sources with URLs
- Verified findings (marked [TESTED])
- Assumptions (marked [ASSUMED])
- Summary at top, sources at bottom

### Specifications (_SPEC_*.md)

Purpose: Define what to build before implementation

Required sections (when relevant):
- Overview with goal and target files
- Table of Contents
- Scenario with "What we don't want"
- Functional Requirements (numbered: XXXX-FR-01)
- Implementation Guarantees (numbered: XXXX-IG-01)
- Domain Objects
- Key Mechanisms and Design Decisions

Rules:
- No Markdown tables - use lists
- No emojis - ASCII only
- Use box-drawing characters for diagrams
- Keep synced with implementation

### Implementation Plans (_IMPL_*.md)

Purpose: Step-by-step guide for implementation

Required sections:
- Header block with goal and target files
- Edge Cases (numbered: XXXX-IP01-EC-01)
- Implementation Steps (numbered: XXXX-IP01-IS-01)
- Test Cases (numbered: XXXX-IP01-TST-01)
- Verification Checklist (numbered: XXXX-IP01-VC-01)
- Backward Compatibility Test (for modifications)

Rules:
- No tables - use lists
- Include code snippets
- Keep synced with implementation

## Workflow Reference

### Context Workflows

- `/prime` - Load workspace context (priority docs, then standard docs)

### Autonomous Action Workflows

- `/go-autonomous` - Generic autonomous implementation loop
- `/go-research` - Structured research with verification

### Session Workflows

- `/session-init` - Create new session folder with tracking files
- `/session-save` - Document findings and commit
- `/session-resume` - Re-read session docs and continue
- `/session-close` - Sync to project files and archive
- `/session-archive` - Move session folder to archive

### Process Workflows

- `/create-impl-plan` - Create implementation plan from spec
- `/implement` - Autonomous implementation with tracking
- `/verify` - Verify work against specs and rules
- `/commit` - Create conventional commits

## Agent Instructions

### Before Starting Work

1. Run `/prime` to load context
2. Read all `!*.md` files (priority documentation)
3. Read session tracking files if in a session
4. Check for existing specs and plans

### During Work

1. Track progress in PROGRESS.md
2. Document problems in PROBLEMS.md
3. Use small, frequent commits
4. Run `/verify` after significant changes
5. Keep specs and plans synced with code

### Before Ending Session

1. Run `/session-save` to document findings
2. Ensure all changes are committed
3. Update tracking files with current state

## MUST-NOT-FORGET List

A summary section at the top of long documents (rules, specs, plans, notes, problems) containing the most important points that agents tend to forget during long conversations.

### Purpose

- AI agents lose context in long conversations
- Important rules get buried in lengthy documents
- Frequently violated rules need prominent placement

### Usage

1. **In documents**: Summary section at top of rules, specs, plans, notes, problems
2. **In workflows**: Agent creates internal MUST-NOT-FORGET list during autonomous work (see `/go-autonomous`)

### Rules for Creating

1. **Position**: After header block, before TOC
2. **Length**: Max 20 lines
3. **Content**: Imperatives and rules that are frequently violated or forgotten.
4. **Format**: One rule per line, imperative mood ("Use X", "NEVER Y")
5. **No explanations**: Just the rule - details are in the full document
6. **Actionable**: Every line must be directly actionable
7. **Priority**: Most important / most forgotten rules first

### Example

```markdown
---
trigger: always_on
---

# Implementation Specification Rules

## MUST-NOT-FORGET

- Use lists, not Markdown tables
- No emojis - ASCII only, no `---` markers between sections
- Use box-drawing characters (├─ └─ │) for trees
- ASCII UI diagrams have no line width limitation
- Research APIs on official docs before suggesting usage
- List assumptions at start - let user verify before proceeding
- High complexity: propose 2-3 implementation alternatives before committing
- Place TOC at start of spec
- ID-System: `**XXXX-FR-01:**`, `**XXXX-IG-01:**`, `**XXXX-DD-01:**` (FR=Functional, IG=Guarantee, DD=Decision)
- Be exhaustive: list ALL domain objects, actions, buttons, functions
- Auto-verify against [SPEC] after implementation and reverse-update on changes if change was intentional.
- Include "What we don't want" in Scenario section

## Table of Contents
...
```
