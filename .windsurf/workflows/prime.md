---
auto_execution_mode: 1
description: Prime context with workspace files
---

# Prime Context Workflow

## Step 1: Find and Read Priority Documentation (! prefix)

Search for .md files starting with "!" - these contain critical specifications:
```
find_by_name Pattern="!*.md" SearchDirectory="[WORKSPACE_ROOT]" Type="file"
```
Read each file found and **summarize key points internally** to better remember content.

## Step 2: Find and Read Standard Documentation

Search for .md files NOT starting with "_" or "!":
```
find_by_name Pattern="*.md" SearchDirectory="[WORKSPACE_ROOT]" Type="file" Excludes=["_*", "!*"]
```

## Exclusions

- Skip .md files starting with "_"
- Skip ALL folders starting with "_" (task folders, archive, temp, tools, etc.)

## Final Output

Answer in single row: "Read [a] .md files ([b] priority), [c] code files ( [d] .py, [e] ...)"