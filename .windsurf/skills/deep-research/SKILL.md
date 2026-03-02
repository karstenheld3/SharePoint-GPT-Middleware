---
name: deep-research
description: Apply when conducting deep research on technologies, APIs, frameworks, or other software development topics requiring systematic investigation
---

# Deep Research Skill

Systematic research using MCPI (Most Complete Point of Information) or MEPI (Most Executable Point of Information) approaches.

## When to Use

**Use this skill** when the user's intent requires:
- Making an informed decision between alternatives
- Understanding something deeply before acting
- Preparing for a complex undertaking
- Evaluating risks, trade-offs, or consequences
- Gathering exhaustive knowledge on a topic

## Quick Start

1. Read this SKILL.md for core principles
2. Read the appropriate strategy file (MCPI or MEPI)
3. Follow Phases 1-4 systematically
4. Output findings as INFO document

## Phase Model (Global)

All research (MCPI and MEPI) follows these 4 phases:

**Phase 1 - Preflight**: Decompose prompt, document assumptions, collect sources, verify/correct assumptions, create STRUT with QA pipelines, run first VCRIV

**Phase 2 - Planning**: Create TOC, topic template, TASKS plan, run second VCRIV

**Phase 3 - Research**: Topic-by-topic file-by-file research per TASKS/STRUT, run VCRIV per granularity rules

**Phase 4 - Final Verification and Sync**: Dimension coverage, completeness check, metadata, final VCRIV

Strategy files (MCPI/MEPI) define the details for each phase.

## Prompt Decomposition (Phase 1, Step 1)

Answer these 7 questions before any source collection:

1. **Q1 - Goal**: What is the user's intent? (1-2 sentences)
2. **Q2 - Scope**: NARROW (1 dim), FOCUSED (2-4 dim), or EXPLORATORY (5-9 dim)?
3. **Q3 - Dimensions**: Which apply? (legal, financial, administrative, practical, technical, professional, medical, psychological, personal, organizational, strategic, security, cultural, educational, historical, or custom)
4. **Q4 - Topics**: 3-5 topics per dimension
5. **Q5 - Strategy**: MCPI (exhaustive) or MEPI (curated)?
6. **Q6 - Domain**: Which profile? (SOFTWARE, MARKET_INTEL, DOCUMENT_INTEL, LEGAL, or DEFAULT)
7. **Q7 - Discovery Platforms**: What databases/platforms index this entity type? Test each, classify access level.

Store PromptDecomposition in STRUT plan. Do NOT proceed to source collection until all 7 questions are answered.

### PromptDecomposition Schema

```json
{
  "goal": "string (1-2 sentences)",
  "scope": "NARROW | FOCUSED | EXPLORATORY",
  "dimensions": ["list of dimension names"],
  "topics_per_dimension": { "dimension": ["topics"] },
  "strategy": "MCPI | MEPI",
  "strategy_rationale": "string (WHY this strategy fits the prompt)",
  "domain": "DEFAULT | SOFTWARE | MARKET_INTEL | DOCUMENT_INTEL | LEGAL",
  "domain_rationale": "string (WHY this domain profile applies)",
  "effort_estimate": "N hours minimum",
  "discovery_platforms": {
    "identified": ["list of platforms that index this entity type"],
    "tested": { "platform_name": "FREE | PAID | PARTIAL" },
    "selected": ["platforms to use (FREE or PARTIAL only)"]
  }
}
```

### Scope Examples

- NARROW: "What are the rate limits for the Microsoft Graph API?" -> 1 dimension (technical)
- FOCUSED: "Should we use PostgreSQL or MongoDB for our event sourcing system?" -> 3 dimensions (technical, operational, financial)
- EXPLORATORY: "How should our startup approach SOC 2 compliance?" -> 6 dimensions (legal, technical, organizational, financial, operational, educational)

## MUST-NOT-FORGET

- **STRUT required** for all research sessions (include pipeline steps and time log)
- **Assumptions check first** - write down what you think you know before researching
- **Discovery platforms tested** - identify, test, classify (FREE/PAID/PARTIAL) before source collection
- **Primary sources > secondary > community** - verify tier 1-3 before accepting tier 6-8
- **Access dates required**: `Accessed: YYYY-MM-DD` on all sources
- **Track time** - log task start/end for net research time calculation
- **Quality pipeline 3x** (not optional): TOC+template, each topic, complete set
- **Source completeness**: Full PDF transcription via pipeline, no agent-selected chunks
- **Download and store** all sources in session folder (web content changes)
- **Inline citations** on critical conclusions: `[LABEL] (SOURCE_ID | URL or filename)`
- **Identify domain** during Preflight, read corresponding DOMAIN_*.md profile
- **Document strategy choice** - OUTPUT document must include strategy (MEPI/MCPI) + domain + rationale for both in header block
- **Distinguish** facts from opinions from assumptions
- **Autonomous after Phase 1** - no user interaction until delivery (except [CONSULT])

## Strategy Selection

**MEPI** (Default) - curated options, deeply researched, compare and recommend
- Use for: User intent is specific, danger of analysis-paralysis and introducing irrelevant options
- Strategy file: [RESEARCH_STRATEGY_MEPI.md](RESEARCH_STRATEGY_MEPI.md)

**MCPI** (Exception) - exhaustive coverage, document everything
- Use for: User intent is broad, wants to see the whole picture
- Strategy file: [RESEARCH_STRATEGY_MCPI.md](RESEARCH_STRATEGY_MCPI.md)

## Source Hierarchy

1. Official PDFs/papers (legislation, specs, whitepapers)
2. Official documentation
3. Official blog/changelog
4. GitHub repo
5. Conference talks by maintainers
6. Reputable tech blogs
7. Stack Overflow
8. Community forums/Discord

**Enforcement** (legal/financial/medical): MUST cite tier 1-3 for critical claims. Label tier 6-8 as `[COMMUNITY]`. Violation triggers `[CONSULT]` to user.

## Verification Labels

- `[VERIFIED]` - Confirmed from official docs
- `[ASSUMED]` - Inferred, not explicit
- `[TESTED]` - Manually tested
- `[PROVEN]` - Multiple independent sources
- `[COMMUNITY]` - Community sources (cite ID)

## Quality Pipeline (VCRIV)

```
verify → critique → reconcile → implement → verify
```

- **V** - Verify: Formal correctness check (`/verify` workflow)
- **C** - Critique: Find gaps, reasoning flaws; produces `*_REVIEW.md` (`/critique` workflow)
- **R** - Reconcile: Prioritize findings (`/reconcile` workflow)
- **I** - Implement: Apply findings, delete `*_REVIEW.md` (`/implement` workflow)
- **V** - Verify (final): Confirm corrections complete

**Four mandatory checkpoints:**
1. Preflight deliverables (STRUT, SOURCES, PromptDecomposition)
2. Planning deliverables (TOC, template, TASKS)
3. Each research output (per VCRIV granularity rules)
4. Complete research set ex-post (after all topics complete)

**Granularity** (scope-based):
- NARROW: VCRIV per topic file
- FOCUSED/EXPLORATORY: VCRIV per dimension
- Final VCRIV on synthesis document

**Termination**: Max 2 cycles per checkpoint, then [CONSULT].

## Inline Citations

Critical conclusions MUST have: `[VERIFICATION_LABEL] (SOURCE_ID | URL or filename)`

Examples:
- `[VERIFIED] (GRPH-SC-MSFT-RATELMT | https://learn.microsoft.com/graph/throttling)`
- `[VERIFIED] (ANTH-SC-ANTH-MDLCRD | _SOURCES/anthropic-model-card-2025.pdf)`

Referenced files MUST exist in `_SOURCES/` subfolder.

## Domain Profiles

Read one profile per session based on Q6:
- [DOMAIN_SOFTWARE.md](DOMAIN_SOFTWARE.md) - APIs, frameworks, libraries
- [DOMAIN_MARKET_INTEL.md](DOMAIN_MARKET_INTEL.md) - Companies, financials
- [DOMAIN_DOCUMENT_INTEL.md](DOMAIN_DOCUMENT_INTEL.md) - Table extraction
- [DOMAIN_LEGAL.md](DOMAIN_LEGAL.md) - Legislation, case law
- [DOMAIN_DEFAULT.md](DOMAIN_DEFAULT.md) - Generic (use when none match)

## Output Format

INFO document with:
1. Research Question
2. **Strategy & Domain** (MEPI/MCPI + domain profile + rationale for each choice)
3. Key Findings (curated for MEPI, exhaustive for MCPI)
4. Detailed Analysis
5. Limitations and Known Issues
6. Sources (with verification labels)
7. Recommendations

MEPI uses its own output format (see RESEARCH_STRATEGY_MEPI.md) with Comparison and Recommendation sections.

## Planning Structure

**STRUT** (high-level, REQUIRED): Phases, objectives, deliverables, transitions, time log. File: `STRUT_[TOPIC].md`

**TASKS** (low-level, Phase 2): Flat task list with durations and done-when criteria. File: `TASKS.md`

## Reference Files

- [RESEARCH_TOOLS.md](RESEARCH_TOOLS.md) - Tools, source processing, configuration
- [RESEARCH_TOC_TEMPLATE.md](RESEARCH_TOC_TEMPLATE.md) - TOC structure
- [RESEARCH_CREATE_TOC.md](RESEARCH_CREATE_TOC.md) - TOC creation workflow

**File naming**: `__[SUBJECT]_TOC.md`, `__[SUBJECT]_SOURCES.md`, `_INFO_[SUBJECT]-IN[XX]_[TOPIC].md`

**Source ID format**: `[SUBJECT]-SC-[SOURCE]-[DOCNAME]`
