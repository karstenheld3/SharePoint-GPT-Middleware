# Create TOC Workflow

Global workflow for creating Table of Contents in deep research. Used by all research strategies.

## Prerequisites

- `__[TOPIC]_SOURCES.md` exists with all sources collected and IDs assigned
- [TOPIC] identifier defined (2-6 uppercase chars)
- [SUBJECT] full name defined

## Workflow

1. **Copy template**: Use `RESEARCH_TOC_TEMPLATE.md` as base
2. **Replace placeholders**:
   - `[TOPIC]` → actual topic ID (e.g., `OAIAPI`)
   - `[SUBJECT]` → full name (e.g., `OpenAI API`)
   - `[VERSION]` → version or documentation date
3. **Create categories**: Group topics logically from sources
4. **List topic files**: One entry per topic with link and brief description
5. **Count total**: Add `**Total topics: XX**` at start of Topic Files section
6. **Write Topic Details**: For each topic add Scope, Contents, Sources
7. **Add Related**: List related/competing technologies with URLs
8. **Write Summary**: 5-15 sentences covering all key facts
9. **Delete template instructions**: Remove the HTML comment block
10. **Run verification**: `/verify` > `/critique` > `/reconcile /implement` > `/verify`

## File Naming

Output: `__[TOPIC]_TOC.md` (double underscore = master document)

## Structure Rules

- **Topic Files section**: Links only, no checkboxes
- **Topic Details section**: Scope + Contents + Sources for each topic
- **NO Progress Tracking**: Progress goes in STRUT or TASKS, not TOC
- **Research stats**: Added in final phase, not during TOC creation

## Quality Gates

**Done when**:
- All sources from `__[TOPIC]_SOURCES.md` covered
- Summary is 5-15 sentences
- All topic links follow format: `[_INFO_[TOPIC]_[SUBTOPIC].md](#topic-subtopic)`
- Related technologies section complete
- `/verify` passes

## Example

Input: `__OAIAPI_SOURCES.md` with 79 sources
Output: `__OAIAPI_TOC.md` with 62 topics in 16 categories
