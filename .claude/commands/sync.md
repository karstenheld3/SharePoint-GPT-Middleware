Sync Claude commands from Windsurf workflows by stripping YAML frontmatter.

For each .md file in `.windsurf/workflows/`:
1. Read the file content
2. If it starts with `---`, strip everything up to and including the second `---` line
3. Write the remaining content to `.claude/commands/` with the same filename

Use a simple file-by-file approach with sed or PowerShell. Example with PowerShell:

```powershell
Get-ChildItem .windsurf/workflows/*.md | ForEach-Object { (Get-Content $_.FullName -Raw) -replace '(?s)^---.*?---\r?\n', '' | Set-Content ".claude/commands/$($_.Name)" -NoNewline }
```

Do NOT use temporary files. Do NOT read files individually with tools - use shell commands.
