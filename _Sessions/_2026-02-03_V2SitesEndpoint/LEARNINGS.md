# Learnings

**Goal**: Extract transferable lessons from resolved problems

## Table of Contents

1. [Learnings](#learnings-1)
2. [Document History](#document-history)

## Learnings

### `SITE-LN-001` Quote Escaping in Generated JavaScript

**Source**: `SITE-FL-001` (JavaScript syntax error from unescaped quotes)

**Pattern**: Python-to-JS string generation  
**Rule**: Always use escaped double quotes `\"...\"` for string literals inside onclick handlers that will be processed by UI generation functions.

**Applies to**:
- `common_ui_functions_v2.py` button definitions
- Any dict-based UI configuration that generates JS
- Similar patterns in other V2 routers

**Quick check**: If your onclick contains `('...')`, change to `(\"...\")`.

## Related Sessions

- Security scanner learnings moved to: `_2026-02-03_V2SiteSecurityScanner`

## Document History

**[2026-03-02 10:45]**
- Split from original session - kept SITE-LN-* entries only

**[2026-02-03 09:33]**
- Added SITE-LN-001: Quote escaping in generated JavaScript
