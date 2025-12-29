Sync Claude commands from Windsurf workflows.

1. Find all .md files in `.windsurf/workflows/`
2. For each workflow file:
   - Read the file content
   - Strip any YAML frontmatter (content between `---` markers at the start)
   - Create/overwrite a file in `.claude/commands/` with the same name
   - The new file should contain only the workflow instructions (no frontmatter)
3. Report: "Synced [x] workflows from Windsurf to Claude commands"
