# Exhaustive Research Strategy (MCPI Approach)

Research **[SUBJECT]** exhaustively using the MCPI (Most Complete Point of Information) approach.

**Before starting**: Create `STRUT_[TOPIC].md` using `/write-strut` with Time Log section and explicit quality pipeline steps:
```
## Time Log
Started: [YYYY-MM-DD HH:MM]
Ended: [pending]

Active intervals:
- [HH:MM-HH:MM] (Phase X-Y)

Net research time: [pending]

## Quality Pipeline
verify → critique → reconcile → implement → verify

- verify: Formal and rule-based correctness check (/verify)
- critique: Find missing pieces, reasoning flaws; mandatory web research; produces *_REVIEW.md (/critique)
- reconcile: Pragmatic prioritization of critique findings (/reconcile)
- implement: Apply prioritized findings; delete *_REVIEW.md after success (/implement)
- verify (final): Confirm corrections are complete (/verify)
```

**Domain identification** (during Phase 0 or Phase 1):
1. Determine research domain from prompt context
2. Read corresponding `DOMAIN_*.md` profile (if available)
3. Incorporate domain-specific rules into STRUT plan (source tiers, document handling, template additions, quality criteria)
4. If no matching domain profile exists, use generic defaults and document this in STRUT

**Phases:**

**Phase 0: STRUT Plan Creation (MANDATORY)**
- Create STRUT plan BEFORE any research activity
- STRUT defines: phases, objectives, steps, deliverables, transitions
- STRUT enforces 3 quality pipeline checkpoints as deliverables
- STRUT MUST include the explicit quality pipeline steps (see above)
- STRUT MUST include the active domain profile and its domain-specific rules
- Store STRUT in session PROGRESS.md or research folder
- Run `/verify` on STRUT plan

**Phase 1: Preflight - Assumptions & Source Collection**
- **Intent extraction** (before asking any question):
  1. Parse prompt for: subject, scope boundaries, output expectations, decision context
  2. Check conversation history and NOTES.md for prior context
  3. Document inferred intent as assumptions with [ASSUMED] label
  4. Proceed with best interpretation - do NOT ask unless genuinely ambiguous
- **Assumptions Check**:
  1. Write down "Pre-research assumptions" about [SUBJECT]
  2. Verify assumptions against primary sources during preflight
  3. If >30% of assumptions are wrong or outdated, re-run preflight with corrected understanding, keep original assumptions (strikethrough). **Max 2 re-runs**, then proceed with corrected assumptions.
  4. Document assumption accuracy in `__[TOPIC]_SOURCES.md` header (e.g., "Preflight accuracy: 7/10 assumptions verified")
  5. **Assumption verification rubric**: CORRECT = matches source exactly. PARTIAL = spirit correct but details differ (counts as wrong for threshold). WRONG = contradicted by source.
- **Document version scope**: Explicitly state the [SUBJECT] version being documented (e.g., `v2.1.0`, `API v3`). If versioning not applicable, use documentation date: `YYYY-MM-DD`
- Create `__[TOPIC]_SOURCES.md` (double underscore = master document)
- Collect ALL official documentation URLs from vendor/project documentation
- Collect community sources (secondary sources) for real-world insights:
  - Stack Overflow questions/answers with high votes
  - GitHub issues (open and closed) revealing bugs, limitations, workarounds
  - Blog posts from recognized experts or official developer advocates
  - Reddit/forum discussions highlighting gotchas
  - Release notes and changelogs for version-specific behavior
- **Community source rule**: Community sources supplement official docs, not replace. Use primarily for limitations, quirks, and real-world gotchas. **Filter community sources to match [SUBJECT] version** - discard outdated version-specific issues.
- **Source collection using domain-specific tiers**: Use source tiers from the active domain profile. If no profile, default: official documentation/publications > vendor/issuer content > community/analyst sources.
- Assign source IDs in format: `[TOPIC]-IN01-SC-[SOURCE]-[DOCNAME]`
  - Official sources: `[TOPIC]-IN01-SC-[VENDOR]-[DOCNAME]`
  - Community sources: `[TOPIC]-IN01-SC-[PLATFORM]-[DOCNAME]` (e.g., `GRPH-IN01-SC-SO-RATELIMIT`, `GRPH-IN01-SC-GH-ISSUE1234`)
- Group sources by category (domain-specific, e.g., Core Docs, SDK/Libraries, Resource Types for software; SEC Filings, Earnings Calls, Press Releases for market intel)
- Include "Related" section listing similar or easily confused alternatives
- **Source processing**: Process all PDF sources through the mandatory source processing pipeline (see SKILL.md FR-07a). Read `deep-research-config.json` for processing settings.
- **Done when**: (a) Official docs main TOC fully enumerated, (b) 15-30 sources collected (minimum 15), (c) All sources have IDs assigned, (d) PDF sources transcribed via pipeline

**Phase 2: TOC Creation**
- Follow [RESEARCH_CREATE_TOC.md](RESEARCH_CREATE_TOC.md) workflow
- Use [RESEARCH_TOC_TEMPLATE.md](RESEARCH_TOC_TEMPLATE.md) as base
- Create `__[TOPIC]_TOC.md` with detailed structure
- **Quality gate**: Run quality pipeline (verify → critique → reconcile → implement → verify)
- **Done when**: TOC covers all major topics from sources, summary is 5-15 sentences, all links resolve

**Phase 3: Template Creation**
- Create `__TEMPLATE_[TOPIC]_TOPIC.md` (double underscore = master template)
- Template structure (base + domain-specific template additions from active domain profile):
  - Header block (Doc ID, Goal, Dependencies, **Version/Date scope**)
  - Summary: **5-15 sentences** (scale with topic complexity, match TOC Summary)
  - Key Facts with [VERIFIED] labels
  - Use Cases
  - Quick Reference (one-screen lookup)
  - Main Sections (follow TOC structure)
  - **Limitations and Known Issues** (from community sources)
  - **Gotchas and Quirks** (undocumented behavior, edge cases)
  - Sources section with **same IDs as `__[TOPIC]_SOURCES.md`**
  - Document History
- Include "Template Instructions" section (to be deleted when using)
- **Quality gate**: Run quality pipeline (verify → critique → reconcile → implement → verify)
- **Done when**: Template has all required sections, instructions are clear

**Phase 4: TASKS Plan**
- Create `TASKS_[TOPIC]_RESEARCH.md`
- Partition TOC topics into discrete tasks
- Each task: Status, Estimated effort, Sources (official + community), Items to document, Done-when criteria
- **Task timing format**: `- [ ] TK-01: [Description] [HH:MM-HH:MM] Xm`
  - Log start time when beginning task, end time when completing
  - Mark parallel tasks with `(parallel)` suffix
  - Example: `- [x] TK-02: Rate limits [10:15-11:00] 45m (parallel)`
- Include Progress Summary section
- **Done when**: All TOC topics have corresponding tasks, effort estimates assigned

**Phase 5: File-by-File Research**
- For each topic file from TASKS:
  1. Research using official source URLs first
  2. Cross-reference with community sources for limitations, bugs, quirks
  3. Process sources per domain profile document handling rules (full read, table extraction, JSON extraction as applicable)
  4. Create `_INFO_[TOPIC]-IN[XX]_[SUBTOPIC].md` using template
     - XX = sequential Doc ID number (01, 02, 03...)
     - Files sort alphabetically in TOC order
     - Example: `_INFO_OASDKP-IN01_INTRODUCTION.md`
  5. Include "Limitations and Known Issues" section with community source citations
  6. **Mandatory inline citations**: Critical conclusions MUST include `[VERIFICATION_LABEL] (SOURCE_ID | URL or filename)`. Referenced files MUST exist in `_SOURCES/`.
  7. **Quality gate**: Run quality pipeline (verify → critique → reconcile → implement → verify)
  8. Update TASKS progress
  9. Update TOC status
- All claims must have verification labels: [VERIFIED], [ASSUMED], [TESTED], [PROVEN], [COMMUNITY]
- **Done when**: All tasks in TASKS plan completed and checked off

**Phase 6: Final Verification and Sync**
- **Verify against this document** (`RESEARCH_STRATEGY_MCPI.md`) - check all phase requirements met
- Cross-verify all topic files against TOC checklist
- Sync summaries from topic files back into TOC Summary section
- Verify all links work
- Ensure community-sourced limitations are included in relevant sections
- **Add Research stats to TOC header block** (copy from STRUT):
  ```
  **Research stats**: 35m net | 62 docs | 79 sources
  ```
- **Quality gate**: Run quality pipeline on complete research set (verify → critique → reconcile → implement → verify)
- Critical questions for ex-post review:
  1. Does research output meet research goal with maximum quality, clarity, correctness?
  2. Does it contain self-critical perspective?
  3. Did it invest substantial effort to identify and evaluate primary sources?
  4. Did it invest substantial effort to identify and evaluate secondary sources?
  5. Were PDFs downloaded and read (not just web research)?
  6. Are all initial research questions answered?
  7. Are findings properly linked in TOC?
- **Done when**: All strategy requirements met, links work, summaries synced, metadata added

**Phase 6.5: Completeness Verification**
- Re-read official documentation structure (main navigation/sidebar)
- Compare against TOC - identify any missed topics
- For each gap:
  1. Assess priority (High: core feature, Medium: useful, Low: niche)
  2. Create INFO files for High/Medium priority gaps
  3. Update TOC with new topics
- Document coverage percentage in TOC header
- **Done when**: All High/Medium priority topics documented, gaps acknowledged

**Termination criteria**: Max 2 cycles per quality checkpoint. If issues persist after 2 cycles, escalate to [ACTOR] via [CONSULT].

**Autonomous operation**: After Preflight, NO user interaction until delivery of final verified research set. All quality checkpoints run autonomously. [CONSULT] (from termination criteria) is the only exception.

**Rollback**: If any phase reveals fundamental error in earlier phase, document in PROBLEMS.md and consult user before rollback.

**File Naming Conventions:**
- `__[SUBJECT]_TOC.md`: Table of Contents (Doc ID: `[SUBJECT]-TOC`)
- `__[SUBJECT]_SOURCES.md`: Source list (Doc ID: `[SUBJECT]-SOURCES`)
- `_INFO_[SUBJECT]-IN[XX]_[TOPIC].md`: Content files (Doc ID: `[SUBJECT]-IN01`, `IN02`, etc.)
- No prefix: Tracking files (TASKS, NOTES, PROBLEMS, PROGRESS)

**Doc ID Exceptions:** TOC and SOURCES use `-TOC` and `-SOURCES` suffixes (not numbered). Content starts at `-IN01`.

**Verification Labels:**
- `[VERIFIED]` - Confirmed from official documentation
- `[ASSUMED]` - Inferred but not explicitly stated
- `[TESTED]` - Manually tested by running code
- `[PROVEN]` - Confirmed from multiple independent sources
- `[COMMUNITY]` - Reported by community sources (cite source ID)

**Source Types:**
- **Primary (Official)**: Vendor documentation, official SDKs, API references, release notes, legislation, SEC filings, annual reports
- **Secondary (Community)**: Stack Overflow, GitHub issues, expert blogs, forums, conference talks, analyst reports

**Anti-patterns to Avoid:**
- Checkboxes in TOC content lists (use links instead)
- Short summaries (2-3 sentences) for complex topics
- Missing Related section
- Source IDs not matching between SOURCES and topic files
- Single underscore for master documents
- Non-clickable references in TOC
- Ignoring community sources for known issues
- Treating community reports as verified without citation
- Non-sequential file numbering (files should sort in TOC order)
- Plain text file references in TOC (use markdown links)
- Skipping completeness verification against source docs
- Reading only agent-selected chunks instead of full source transcription
- Missing inline citations on critical conclusions

**Quality Gates:**
- Every topic file verified against source URLs
- No Markdown tables (use lists)
- No emojis
- All sources cited with IDs
- Critical conclusions have inline citations with URL/filename
- Summary copy/paste ready for executive use
- Limitations section populated from community research
- Known issues cross-referenced with official bug trackers where available
- All PDF sources fully transcribed (not just partially read)
