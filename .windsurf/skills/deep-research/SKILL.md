---
name: deep-research
description: Apply when conducting deep research on technologies, APIs, frameworks, or other software development topics requiring systematic investigation
---

# Deep Research Skill

Systematic research patterns for in-depth investigation using the MCPI (Most Complete Point of Information) approach.

## Table of Contents

**Core**
- [When to Use](#when-to-use)
- [MUST-NOT-FORGET](#must-not-forget)
- [Quality Pipeline](#quality-pipeline) - Mandatory verify → critique → reconcile → implement → verify
- [Output Format](#output-format)

**Patterns**
- [MEPI vs MCPI](#mepi-vs-mcpi) - When to use quick vs exhaustive research
- [Source Hierarchy](#source-hierarchy) - Priority order for sources
- [Verification Labels](#verification-labels) - How to mark claims
- [Inline Citations](#inline-citations) - Mandatory for critical conclusions

**Strategy**
- [MCPI Research Strategy](RESEARCH_STRATEGY_MCPI.md) - 6-phase exhaustive documentation

**Domain Profiles**
- [Domain Profiles](#domain-profiles) - Modular extensions per research domain
- [DOMAIN_SOFTWARE.md](DOMAIN_SOFTWARE.md) - Software API, framework, library
- [DOMAIN_MARKET_INTEL.md](DOMAIN_MARKET_INTEL.md) - Companies, financial reports, press releases
- [DOMAIN_DOCUMENT_INTEL.md](DOMAIN_DOCUMENT_INTEL.md) - Table/data extraction from documents
- [DOMAIN_LEGAL.md](DOMAIN_LEGAL.md) - Legislation, case law, regulatory

**Templates**
- [TOC Template](RESEARCH_TOC_TEMPLATE.md) - Table of Contents structure
- [Create TOC Workflow](RESEARCH_CREATE_TOC.md) - How to create TOC files

**Planning & Tracking**
- [Planning Structure](#planning-structure) - STRUT vs TASKS
- [Time Tracking](#time-tracking) - Net research time calculation

**Reference**
- [Tool Reference](RESEARCH_TOOLS.md) - Source collection, PDF processing, transcription
- [Source Processing Pipeline](#source-processing-pipeline) - Mandatory PDF/image transcription
- [Source ID Format](#source-id-format) - How to cite sources
- [File Naming Conventions](#file-naming-conventions) - Prefix rules for documents
- [Configuration](#configuration) - deep-research-config.json settings

## When to Use

**Deep research (this skill):**
- "Should we use X or Y for our project?"
- "How does X work internally?"
- "What are the production considerations for X?"
- Multi-source synthesis required
- Exhaustive documentation needed

**Quick lookup (not this skill):**
- "What's the syntax for X?"
- "How do I install Y?"
- Single-source answers

## MUST-NOT-FORGET

- Start with assumptions check - write down what you think you know before researching
- Primary sources > secondary sources > community opinions
- Document all sources with URLs and access dates
- Flag information age (APIs change rapidly)
- Distinguish facts from opinions from assumptions
- Version-match community sources to subject version
- Create INFO document for findings
- **Always create STRUT** for research session orchestration
- **Track time** - log task start/end for net research time calculation
- **Quality pipeline runs 3 times** (not optional): TOC+template, each topic doc, complete set (ex-post)
- **Source completeness**: Process all PDFs through transcription pipeline, read fully (not selected chunks)
- **Mandatory inline citations** on critical conclusions: `[LABEL] (SOURCE_ID | URL or filename)`
- **Identify domain** during Preflight and read corresponding DOMAIN_*.md profile
- **Autonomous after Preflight** - No user interaction until delivery of final verified research set (except [CONSULT] from termination criteria)

## Global Patterns

### MEPI vs MCPI

**MEPI** (Most Executable Point of Information) - Default
- Present 2-3 curated options
- Filter and recommend
- Use for: reversible decisions, time-constrained, action-oriented

**MCPI** (Most Complete Point of Information) - Exception
- Present exhaustive options
- Document everything
- Use for: irreversible decisions, high-stakes, archival reference

### Source Hierarchy

1. **Official PDFs/papers** - Legislation, specs, whitepapers, academic papers (often not available as web)
2. **Official documentation** - Authoritative, version-specific
3. **Official blog/changelog** - Announcements, rationale
4. **GitHub repo** - Source code, issues, PRs, discussions
5. **Conference talks by maintainers** - Design decisions, roadmap
6. **Reputable tech blogs** - Analysis, comparisons
7. **Stack Overflow** - Specific problems (verify currency)
8. **Community forums/Discord** - Anecdotes, edge cases

**Source Persistence**: Download and store all sources in session folder for later reference. Web content changes - PDFs and local copies ensure reproducibility.

### Verification Labels

- `[VERIFIED]` - Confirmed from official documentation
- `[ASSUMED]` - Inferred but not explicitly stated
- `[TESTED]` - Manually tested by running code
- `[PROVEN]` - Confirmed from multiple independent sources
- `[COMMUNITY]` - Reported by community sources (cite source ID)

### Source ID Format

```
[SUBJECT]-SC-[SOURCE]-[DOCNAME]
```

Examples:
- `MSGRAPH-SC-MSFT-APIOVERVIEW` - Microsoft Graph official docs
- `MSGRAPH-SC-SO-RATELIMIT` - Stack Overflow rate limit discussion
- `MSGRAPH-SC-GH-ISSUE1234` - GitHub issue #1234

### File Naming Conventions

- `__[SUBJECT]_TOC.md`: Table of Contents (Doc ID: `[SUBJECT]-TOC`)
- `__[SUBJECT]_SOURCES.md`: Source list (Doc ID: `[SUBJECT]-SOURCES`)
- `_INFO_[SUBJECT]-IN[XX]_[TOPIC].md`: Content files with sequential Doc ID
  - XX = two-digit number starting at 01 (01, 02, 03...)
  - Ensures files sort in TOC order when listed alphabetically
  - Example: `_INFO_MSGRAPH-IN05_SITES_LISTS.md`
- No prefix: Tracking files (TASKS, NOTES, PROBLEMS, PROGRESS)

**Doc ID Exceptions:**
- TOC files use `[SUBJECT]-TOC` (not numbered)
- SOURCES files use `[SUBJECT]-SOURCES` (not numbered)
- Content files start at `[SUBJECT]-IN01`

### Information Currency

- Note version numbers for all API/library info
- Check last updated date on documentation
- Cross-reference with changelog for breaking changes
- Mark stale info with `[STALE: YYYY]` tag

## Quality Pipeline

Mandatory pipeline for all research output documents. Runs 3 times (not optional):

```
verify → critique → reconcile → implement → verify
```

- **verify** - Formal and rule-based correctness check (`/verify` workflow)
- **critique** - Find missing pieces, reasoning flaws; mandatory web research; produces `*_REVIEW.md` (`/critique` workflow)
- **reconcile** - Pragmatic prioritization of critique findings (`/reconcile` workflow)
- **implement** - Apply prioritized findings to research document; delete `*_REVIEW.md` after success (`/implement` workflow)
- **verify** (final) - Confirm corrections are complete (`/verify` workflow)

The STRUT plan MUST include these pipeline steps explicitly so the agent always has the workflow available in context.

**Three mandatory checkpoints:**
1. **Checkpoint 1**: TOC and topic template documents (before topic research begins)
2. **Checkpoint 2**: Each topic research output document (before moving to next topic)
3. **Checkpoint 3**: Complete research set ex-post (after all topics complete)

**Termination criteria**: Max 2 cycles per checkpoint. If issues persist after 2 cycles, escalate to [ACTOR] via [CONSULT].

## Inline Citations

Critical conclusions (key findings, limitations, design constraints, numerical claims) MUST include inline citations with both source ID and human-readable locator.

**Citation format**: `[VERIFICATION_LABEL] (SOURCE_ID | URL or filename)`

- URL: `[VERIFIED] (GRPH-SC-MSFT-RATELMT | https://learn.microsoft.com/graph/throttling)`
- File: `[VERIFIED] (ANTH-SC-ANTH-MDLCRD | _SOURCES/anthropic-model-card-2025.pdf)`

Referenced files MUST exist in `_SOURCES/` subfolder. Non-critical statements (background context, widely known facts) may use source ID only.

## Domain Profiles

Modular extensions that inject domain-specific rules into the generic MCPI process. Each domain gets its own `DOMAIN_*.md` file. Agent reads at most one domain profile per research session (identified during Preflight).

**Profile schema** (each `DOMAIN_*.md` follows this structure):
- **When to Use** - Trigger conditions for domain identification
- **Source Tiers** - What counts as tier 1/2/3 for this domain
- **Document Handling** - Rules for processing large/structured documents
- **Template Additions** - Domain-specific sections added to the output template
- **Quality Criteria** - Domain-specific checks added to quality pipeline checkpoints

**Extension points** in the MCPI process:
1. **Source collection** (Phase 1) - Domain profile defines source types and tiers
2. **Document processing** (Phase 4) - Domain profile defines handling rules per document type
3. **Template structure** (Phase 3) - Domain profile adds domain-specific sections
4. **Quality checks** (Checkpoints 1-3) - Domain profile adds domain-specific quality criteria

**Available profiles:**
- `DOMAIN_SOFTWARE.md` - Software API, framework, library research
- `DOMAIN_MARKET_INTEL.md` - Companies, financial reports, tabular data, press releases
- `DOMAIN_DOCUMENT_INTEL.md` - Table/data extraction from transcribed documents
- `DOMAIN_LEGAL.md` - Legislation, case law, regulatory research

If no matching domain profile exists, agent uses generic defaults and documents this in the STRUT plan.

## Research Strategy

- **MCPI Research** - [RESEARCH_STRATEGY_MCPI.md](RESEARCH_STRATEGY_MCPI.md) - 6-phase exhaustive documentation

## Tool Reference

See [RESEARCH_TOOLS.md](RESEARCH_TOOLS.md) for:
- Source collection tools (search_web, read_url_content, Playwright)
- Document processing tools (pdf-tools)
- Transcription tools (llm-transcription)
- Tool selection flowchart
- Common workflows

## Planning Structure

**STRUT** (high-level orchestration) - REQUIRED for all research:
- Tracks phases, objectives, deliverables, transitions
- Contains time log for net research time
- Created at research start, updated at phase transitions
- File: `STRUT_[TOPIC].md` in session folder

**TASKS** (low-level execution) - Created in Phase 4:
- Flat list of individual research tasks with durations
- Each task: file to create, sources to use, done-when criteria
- Tracks task timing: `[HH:MM-HH:MM]` per task
- File: `TASKS.md` in session folder

## Time Tracking

**Net research time** = active work time, excluding pauses.

**STRUT time log format:**
```
## Time Log
Started: 2026-01-30 09:00
Ended: 2026-01-30 14:30

Active intervals:
- 09:00-10:30 (Phase 1-3)
- 11:00-12:15 (Phase 4-5)
- 13:00-14:30 (Phase 5-6)

Net research time: 4h 15m
```

**TASKS timing format:**
```
- [x] TK-01: Research auth [10:00-10:45] 45m
- [x] TK-02: Research limits [10:15-11:00] 45m (parallel)
```

**Rules:**
- Pause detection: Gap > 30min in file timestamps = pause (don't count)
- Parallel tasks: Overlapping intervals count once, not doubled
- Log start time when beginning task, end time when completing

## Source Processing Pipeline

All PDF and image sources MUST be processed through the full transcription pipeline to ensure maximum source completeness. Reading only agent-selected chunks is NOT permitted.

**Before first source processing**: Read `deep-research-config.json` for settings and read `@llm-transcription` SKILL.md + `/transcribe` workflow to understand available options.

**Pipeline steps:**
1. **PDF to JPG** - `@pdf-tools` skill (`convert-pdf-to-jpg.py`)
2. **JPG to Markdown** - `@llm-transcription` skill (`transcribe-image-to-markdown.py`, batch mode)
3. **Stitch pages** - Per `/transcribe` workflow Step 7
4. **Extract structured data** - Grep `<transcription_json>` tags from transcribed markdown

The transcription prompt produces `<transcription_json>` tags for every table and chart - these provide machine-parseable structured data without additional LLM calls.

**Result per document in `_SOURCES/`:**
```
_SOURCES/
├── report.pdf                  # Original source
├── report.md                   # Full markdown transcription
├── report_data.jsonl           # Extracted structured data (tables, charts)
└── report_transcribed/         # Individual page transcriptions
```

**Reading strategy:**
- **Narrative content**: Read relevant sections of `[name].md` (use `<!-- Page NNN -->` markers for navigation)
- **Tabular/numerical data**: Parse `[name]_data.jsonl` for structured access
- **Full completeness**: The transcription covers every page. No content is skipped.

**Mandatory skill usage:**
- PDF sources: `@pdf-tools` (conversion) + `@llm-transcription` (transcription)
- Web sources: `@ms-playwright-mcp` (default, public content) or `@playwriter` (authenticated sessions only)
- **Model selection for transcription**: Use `gpt-5-mini` for legal, regulatory, financial documents. Use `gpt-5-nano` for informal content.

**Multi-document parallel processing**: See `deep-research-config.json` for `concurrent_documents` and `workers_per_document` settings.

## Configuration

Global settings in `deep-research-config.json`:

```json
{
  "transcription": {
    "workers_per_document": 12,
    "concurrent_documents": 3,
    "default_model": "gpt-5-mini",
    "default_model_informal": "gpt-5-nano",
    "default_dpi": 150,
    "keys_file": "[WORKSPACE_FOLDER]\\..\\.tools\\.api-keys.txt"
  },
  "rate_limits": {
    "max_total_workers": 36,
    "delay_between_documents_ms": 2000
  }
}
```

Agent reads this config once before first source processing and uses values throughout the research session.

## Output Format

Deep research outputs an INFO document. Key sections:

1. **Research Question** - What we're investigating
2. **Key Findings** - MEPI-style summary (2-3 main points) or MCPI exhaustive list
3. **Detailed Analysis** - Full investigation results
4. **Limitations and Known Issues** - From community sources
5. **Sources** - All references with quality indicators
6. **Recommendations** - Actionable conclusions

## Usage

1. Determine research type (MEPI quick vs MCPI exhaustive)
2. Read this SKILL.md for core principles
3. Read the appropriate strategy file
4. Read RESEARCH_TOOLS.md for tool guidance
5. Follow the strategy's phases systematically
6. Output findings as INFO document
