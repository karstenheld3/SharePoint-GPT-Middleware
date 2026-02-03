# Failure Log

**Goal**: Document failures, mistakes, and lessons learned to prevent repetition

## Table of Contents

1. [Resolved Issues](#resolved-issues)
2. [Document History](#document-history)

## Resolved Issues

### 2026-02-03 - V2 Sites Endpoint

#### [RESOLVED] `SITE-FL-001` JavaScript syntax error from unescaped quotes in onclick handlers

- **Original severity**: [MEDIUM]
- **Resolved**: 2026-02-03
- **Solution**: Changed single quotes to escaped double quotes in onclick handlers
- **Link**: Commit `a04dfb9`

**Details:**
- **When**: 2026-02-03 09:29
- **Where**: `src/routers_v2/sites.py:424-425` (button definitions in UI columns)
- **What**: JavaScript "missing ) after argument list" error prevented all router-specific JS functions from loading
- **Why it went wrong**: Used single quotes inside onclick attribute that was already delimited by single quotes in the generated JS string. Quote collision caused syntax error.
- **Evidence**: Browser console showed "missing ) after argument list" and "ReferenceError: showNewSiteForm is not defined"

**Code example:**
```python
# Before (wrong) - single quotes collide
{"text": "File Scan", "onclick": "showNotImplemented('File Scan')", "class": "btn-small btn-disabled"}

# After (correct) - escaped double quotes
{"text": "File Scan", "onclick": "showNotImplemented(\"File Scan\")", "class": "btn-small btn-disabled"}
```

**Lesson**: When defining onclick handlers in Python dicts that get converted to JS, use escaped double quotes `\"...\"` for string arguments to avoid quote collision with the outer string delimiters.

**Learning**: See `SITE-LN-001` in LEARNINGS.md for full analysis.

## Document History

**[2026-02-03 09:31]**
- Added SITE-FL-001: JavaScript quote escaping issue (resolved)
