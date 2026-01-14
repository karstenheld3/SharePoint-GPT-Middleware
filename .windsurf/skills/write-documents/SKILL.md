---
name: write-documents
description: Apply when creating or editing INFO, SPEC, IMPL, TEST, or FIX documents
---

# Document Writing Guide

This skill contains document templates and formatting rules.

## MUST-NOT-FORGET

- Use lists, not Markdown tables
- No emojis - ASCII only, no `---` markers between sections
- Header block: Doc ID (required), Goal (required), Target file, Depends on (omit if N/A)
- Every document MUST have a unique ID
- Reference other docs by filename AND Doc ID: `_SPEC_CRAWLER.md [CRWL-SP01]`
- Be exhaustive: list ALL domain objects, actions, functions
- Document History section at end, reverse chronological
- Use box-drawing characters (├── └── │) for trees

## Document Writing Rules

- Enumerations: use comma-separated format (`.pdf, .docx, .ppt`), NOT slash-separated (`.pdf/.docx/.ppt`)
- Ambiguous modifiers: when a clause can attach to multiple nouns, split into separate sentences
  - BAD: "Files starting with '!' signify high relevance that must be treated with extra attention."
  - GOOD: "Files starting with '!' indicate high relevance. This information must be treated with extra attention."

## Available Templates

Read the appropriate template for the document type you are creating:
- `INFO_TEMPLATE.md` - Research and analysis documents
- `SPEC_TEMPLATE.md` - Technical specifications
- `SPEC_RULES.md` - SPEC writing rules with GOOD/BAD examples
- `IMPL_TEMPLATE.md` - Implementation plans
- `TEST_TEMPLATE.md` - Test plans
- `FIXES_TEMPLATE.md` - Fix tracking documents

## Usage

1. Read this SKILL.md for core rules
2. Read the appropriate template for your document type
3. Follow the template structure

## File Naming

- `_INFO_[TOPIC].md` - Research, analysis, preparation documents
- `_SPEC_[COMPONENT].md` - Technical specifications
- `_SPEC_[COMPONENT]_UI.md` - UI specifications
- `_IMPL_[COMPONENT].md` - Implementation plans
- `_IMPL_[COMPONENT]_FIXES.md` - Fix tracking during implementation
- `SPEC_[COMPONENT]_TEST.md` - Test plan for specification
- `IMPL_[COMPONENT]_TEST.md` - Test plan for implementation
- `!` prefix for priority docs that must be read first

## Agent Behavior

- Be extremely concise. Sacrifice grammar for concision.
- NEVER ask for continuations when following plans.
- Before assumptions, propose 2-3 implementation alternatives.
- List assumptions at spec start for user verification.
- Optimize for simplicity.
- Re-use existing code by default (DRY principle).
- Research APIs before suggesting; rely on primary sources only.
- Document user decisions in "Key Mechanisms" and "What we don't want" sections.

## ID System

See `[AGENT_FOLDER]/rules/devsystem-ids.md` rule (always-on) for complete ID system.

**Quick Reference:**
- Document: `[TOPIC]-[DOC][NN]` (IN = Info, SP = Spec, IP = Impl Plan, TP = Test Plan)
  - Example: `CRWL-SP01`, `AUTH-IP01`
- Spec-Level: `[TOPIC]-[TYPE]-[NN]` (FR = Functional Requirement, IG = Implementation Guarantee, DD = Design Decision)
  - Example: `CRWL-FR-01`, `AUTH-DD-03`
- Plan-Level: `[TOPIC]-[DOC][NN]-[TYPE]-[NN]` (EC = Edge Case, IS = Implementation Step, VC = Verification Checklist, TC = Test Case)
  - Example: `CRWL-IP01-EC-01`, `AUTH-TP01-TC-05`
- Source: `[TOPIC]-[DOC]-SC-[SOURCE_ID]-[SOURCE_REF]`
  - Example: `AGSK-IN01-SC-ASIO-HOME`
- Tracking: `[TOPIC]-[TYPE]-[NNN]` (BG = Bug, FT = Feature, PR = Problem, FX = Fix, TK = Task)
  - Example: `SAP-BG-001`, `UI-FT-003`