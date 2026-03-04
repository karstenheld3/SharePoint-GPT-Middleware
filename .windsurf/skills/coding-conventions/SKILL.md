---
name: coding-conventions
description: Provides coding style rules for Python and PowerShell. Apply when writing, editing, reviewing, or debugging code.
---

# Coding Conventions

## Files

PYTHON-RULES.md - Python (formatting, imports, naming, comments)
JSON-RULES.md - JSON (field naming, 2-space indent)
WORKFLOW-RULES.md - Workflow documents (structure, token optimization)
AGENT-SKILL-RULES.md - Agent skill development (structure, setup, token optimization)

## Logging Files (read when writing or reviewing logging/output code)

LOGGING-RULES.md - General logging rules, philosophy, type overview (read first)
LOGGING-RULES-APP-LEVEL.md - System/debug logging for technical staff (LOG-AP rules)
LOGGING-RULES-SCRIPT-LEVEL.md - Script output for QA and automation verification (LOG-SC rules)
LOGGING-RULES-USER-FACING.md - End-user visible output via console or SSE (LOG-UF rules)

## Tools

reindent.py - Convert Python indentation to target spaces

```powershell
python reindent.py folder/ --to 2 --recursive
python reindent.py folder/ --to 2 --recursive --dry-run
python reindent.py script.py --to 2
```
