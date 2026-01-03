---
trigger: always_on
---

# Commit Message Rules

Use **Conventional Commits** format for all commit messages.

## Format

```
<type>(<scope>): <description>
```

## Components

- **type** (required): Category of change
- **scope** (optional): Affected module or component
- **description** (required): Imperative mood, what the commit does

## Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **test**: Adding or updating tests
- **chore**: Maintenance tasks, dependencies, build changes
- **style**: Formatting, whitespace (no code logic change)
- **perf**: Performance improvement

## Examples

```
feat(crawler): add incremental crawl mode
fix(auth): handle expired tokens
docs: update README installation steps
refactor(domains): simplify source validation logic
test(selftest): add integrity check tests
chore: update dependencies to latest versions
```

## Guidelines

1. Use imperative mood ("add" not "added" or "adds")
2. Keep description under 72 characters
3. No period at the end
4. Scope should match module/folder name when applicable
