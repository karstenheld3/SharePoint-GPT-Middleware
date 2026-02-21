# Domain Profile: Legal Research

Research domain for legislation, case law, regulatory frameworks, and legal analysis.

## When to Use

- Research subject is legislation, regulation, legal framework, or case law
- Prompt mentions: law, regulation, article, section, statute, directive, compliance, court decision, legal basis
- Output will be consumed by legal teams, compliance officers, or policy analysts

## Source Tiers

- **Tier 1 (official/primary)**: Full legislation text, court decisions, official gazettes, regulatory body publications
- **Tier 2 (vendor/issuer)**: Legal commentary from law firms, regulatory guidance documents, official FAQs
- **Tier 3 (community/analyst)**: Legal blogs, academic papers, conference presentations, industry compliance guides

## Document Handling

- **Download and transcribe FULL legislation texts** - No summarization, no excerpts. The complete text must be available in `_SOURCES/`.
- For EU/national legislation: Download official PDF from EUR-Lex or national gazette, transcribe fully
- For court decisions: Download full text, transcribe fully
- **Model selection**: Use `gpt-5-mini` exclusively (99.5% accuracy). Legal text requires verbatim transcription - wrong article numbers or terminology have regulatory consequences.
- Cross-reference between statutes and case law
- Store complete texts in `_SOURCES/`:
  ```
  _SOURCES/
  \u251c\u2500\u2500 eu-ai-act-2024.pdf              # Original legislation PDF
  \u251c\u2500\u2500 eu-ai-act-2024.md               # Full verbatim transcription
  \u251c\u2500\u2500 eu-ai-act-2024_data.jsonl       # Extracted tables (if any)
  \u251c\u2500\u2500 eu-ai-act-2024_transcribed/     # Individual pages
  \u2514\u2500\u2500 case-law-c-123-24.md            # Court decision transcription
  ```

## Template Additions

Add these sections to the standard topic template:

- **Statutory References** - Exact article/section numbers with full quoted text
- **Case Law Summary** - Relevant court decisions with citations
- **Regulatory Timeline** - Effective dates, transition periods, deadlines
- **Compliance Requirements** - Actionable obligations derived from legislation
- **Definitions** - Legal definitions as stated in the legislation (verbatim)

## Quality Criteria

Additional checks for legal domain quality pipeline:

- Every legal conclusion MUST cite exact article/section number
- Full source text of cited articles MUST be available in `_SOURCES/` (not just agent memory)
- Regulation numbers verified exactly (e.g., "2024/1689" not "2024/689") - cross-check against source PDF
- Legal terminology used exactly as defined in the legislation (no paraphrasing of defined terms)
- Effective dates and transition periods verified against official publication
- Distinction between "shall" (mandatory), "should" (recommended), "may" (optional) preserved exactly
- No legal advice or interpretation beyond what the source text states - mark any inference as `[ASSUMED]`
