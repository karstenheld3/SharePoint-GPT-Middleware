---
trigger: always_on
---

# DevSystem Core

Core definitions and structure for the development system.

## Definitions

### Core Concepts

- **[WORKSPACE]**: The Windsurf/VSCode workspace root folder
- **[PROJECT]**: If Monorepo (workspace contains multiple projects), the project subfolder. No Monorepo: Workspace = Project
- **[SESSION]**: All context belonging to a work session - folder, files, conversations, commits, and tracking files (notes, problems, progress)

### Agent Folder

**[AGENT_FOLDER]** location depends on agent:
- Windsurf: `.windsurf/`
- Claude Code: `.claude/`

### Configuration

- **[RULES]**: The current set of agent rules in `[AGENT_FOLDER]/rules/`
- **[WORKFLOWS]**: The current set of agent workflows in `[AGENT_FOLDER]/workflows/`
- **[SKILLS]**: Agent Skills in `[AGENT_FOLDER]/skills/`

### Document Types

- **[INFO]** (IN): Information gathering from web research, option and code analysis, reading documents
  - Example: `AUTH-IN01`, `CRWL-IN02`
- **[SPEC]** (SP): A specification conforming to defined rules. When implemented, must be reverse-updated (synced) from verified code changes
  - Example: `CRWL-SP01`, `AUTH-SP01`
- **[IMPL]** (IP): An implementation plan. When implemented, must be reverse-updated (synced) from verified code changes
  - Example: `CRWL-IP01`, `AUTH-IP02`
- **[TEST]** (TP): Test plans suffixed to corresponding SPEC or IMPL
  - Example: `CRWL-TP01`, `AUTH-TP01`

### Tracking Documents

Tracking documents exist at workspace, project, or session level. Only one of each type per scope.

- **[NOTES]**: Important information. Agent MUST read to avoid unintentional behavior
- **[PROGRESS]**: Progress tracking. Agent MUST read to avoid unintentional behavior
- **[PROBLEMS]**: Problem tracking. Each session tracks issues in its own `PROBLEMS.md`. On `/session-close`, sync to project [PROBLEMS]

## Workspace Scenarios

Three dimensions define how the agent should behave:

### Dimension 1: Project Structure

- **SINGLE-PROJECT** - Workspace contains one project
- **MONOREPO** - Workspace contains multiple independent projects

### Dimension 2: Version Strategy

- **SINGLE-VERSION** - One active version, no migration
- **MULTI-VERSION** - Side-by-side versions (e.g., V1 and V2 coexisting)

### Dimension 3: Work Mode

- **SESSION-BASED** - Time-limited session with specific goals
- **PROJECT-WIDE** - Work spans entire project without session boundaries

## Folder Structure

### Single Project (No Monorepo)

```
[WORKSPACE_FOLDER]/
├── [AGENT_FOLDER]/
│   ├── rules/              # Agent rules (.md files)
│   ├── workflows/          # Agent workflows (.md files)
│   └── skills/             # Agent Skills (folders with SKILL.md)
├── _Archive/               # Archived sessions
├── _[SESSION_FOLDER]/      # Session folders start with underscore
│   ├── _IMPL_*.md          # Implementation plans
│   ├── _INFO_*.md          # Information documents
│   ├── _SPEC_*.md          # Specifications
│   ├── NOTES.md            # Session notes
│   ├── PROBLEMS.md         # Session problems
│   └── PROGRESS.md         # Session progress
├── src/                    # Source code
├── !NOTES.md               # Workspace notes (priority file)
├── !PROBLEMS.md            # Known problems
└── !PROGRESS.md            # Overall progress
```

### Monorepo (Multiple Projects)

```
[WORKSPACE_FOLDER]/
├── [AGENT_FOLDER]/
│   ├── rules/              # Workspace-level rules
│   ├── workflows/          # Workspace-level workflows
│   └── skills/             # Workspace-level skills
├── _Archive/               # Archived sessions (all projects)
├── [PROJECT_A]/
│   ├── _Archive/           # Project A archived sessions
│   ├── _[SESSION_FOLDER]/  # Project A sessions
│   ├── src/                # Project A source code
│   ├── NOTES.md            # Project A notes
│   ├── PROBLEMS.md         # Project A problems
│   └── PROGRESS.md         # Project A progress
├── [PROJECT_B]/
│   └── ...                 # Same structure
├── !NOTES.md               # Workspace-level notes
├── !PROBLEMS.md            # Workspace-level problems
└── !PROGRESS.md            # Workspace-level progress
```

## File Naming Conventions

### Priority Files (! prefix)

Files starting with `!` indicate high relevance. Must be treated with extra attention during `/prime`.

### Ignored Files (_ prefix)

Files starting with `_` are skipped by automatic priming workflows. Use for session-specific, WIP, or archived content.

### Hidden Files (. prefix)

Files starting with `.` follow Unix convention - hidden from directory listings.

## Placeholders

- **[WORKSPACE_FOLDER]**: Absolute path of root folder where Windsurf operates
- **[PROJECT_FOLDER]**: Absolute path of project folder (same as workspace if no monorepo)
- **[SRC_FOLDER]**: Absolute path of source folder
- **[SESSION_FOLDER]**: Absolute path of currently active session folder

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

- `/write-spec` - Create specification from requirements
- `/write-impl-plan` - Create implementation plan from spec
- `/write-test-plan` - Create test plan from spec
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
