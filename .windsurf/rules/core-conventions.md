---
trigger: always_on
---

# Core Conventions

Universal formatting and writing conventions for all documents.

## Text Style

- Use ASCII "double quotes" or 'single quotes'. Never use Non-ASCII quotes unless explicitly asked.
- No emojis in documentation (see Document Rule Exceptions below)
- Avoid Markdown tables; use unnumbered lists with indented properties (see Document Rule Exceptions below)
- Use Unicode box-drawing characters for structures:
  - Trees and flows: `├─>` `└─>` `│` (2-space indentation compatible)
  - Boxes and diagrams (non-UI): `┌─` `├─` `└─` `│` `─` `┐` `┤` `┘`
  - UI diagrams and designs: Keep ASCII `+` `-` `|` for compatibility and easy manual editing
- Try to fit single statements/decisions/objects on a single line

## Document Structure

- Place Table of Contents after header block (or after MUST-NOT-FORGET if present)
- No `---` markers between sections
- One empty line between sections
- Most recent changes at top in changelog sections

## Header Block

All documents start with:

```
# [Document Type]: [Title]

**Doc ID**: [TOPIC]-[TYPE][NN]
**Goal**: Single sentence describing purpose
**Target file**: `/path/to/file.py` (or list for multiple)

**Depends on:**
- `_SPEC_[X].md [TOPIC-SP01]` for [what it provides]

**Does not depend on:**
- `_SPEC_[Y].md [TOPIC-SP02]` (explicitly exclude if might seem related)
```

- Doc ID is required for all documents
- Reference other docs by filename AND Doc ID: `_SPEC_CRAWLER.md [CRWL-SP01]`
- Omit optional fields if not applicable: Target file, Depends on, Does not depend on

## Document History Section

Always at document end, reverse chronological order:

```
## Document History

**[2026-01-12 14:30]**
- Added: "Scenario" section with Problem/Solution/What we don't want
- Changed: Placeholder standardized to `{itemId}` (camelCase)
- Fixed: Modal OK button signature

**[2026-01-12 10:00]**
- Initial specification created
```

**Action prefixes:** Added, Changed, Fixed, Removed, Moved

## Document Rule Exceptions

Documents may opt-in to use Markdown tables or emojis by adding a DevSystem tag as the **first line** of the document (before the title).

**Syntax:**
```html
<DevSystem MarkdownTablesAllowed=true EmojisAllowed=true />
```

**Attributes:**
- `MarkdownTablesAllowed=true` - Allow Markdown tables in this document
- `EmojisAllowed=true` - Allow emojis in this document

**Allowed emojis (when enabled):**
- ✅ - Yes, supported, pass, enabled
- ❌ - No, unsupported, fail, disabled
- ⚠️ - Warning, partial, caution
- ★ - Filled star (rating)
- ☆ - Outlined star (rating)
- ⯪ - Half-filled star (rating)

**Usage pattern:** Emoji first, then textual equivalent
```markdown
- **MCP** - ✅ Yes
- **Hooks** - ❌ No
- **Data** - ⚠️ Partial (read-only)
- **Quality** - ★★★☆☆ (3)
- **Docs** - ★★★★⯪ (4.5)
```

**When to use exceptions:**
- Comparison documents where tables improve readability
- Feature matrices and compatibility charts
- Status dashboards
