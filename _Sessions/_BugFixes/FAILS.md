# Failure Log

**Goal**: Document failures, mistakes, and lessons learned to prevent repetition

## Table of Contents

1. [Active Issues](#active-issues)
2. [Resolved Issues](#resolved-issues)
3. [Document History](#document-history)

## Active Issues

(none)

## Resolved Issues

### 2026-02-05 - Domains UI Cache Fix

#### [RESOLVED] `V2FX-FL-001` reloadItems Override Caused Infinite Recursion

- **Original severity**: HIGH
- **When**: 2026-02-05 15:15
- **Where**: `src/routers_v2/domains.py` lines 323-328 (additional_js)
- **What**: Override of `reloadItems()` using function declaration caused infinite recursion (`RangeError: Maximum call stack size exceeded`)
- **Why it went wrong**: `[VERIFIED-WRONG]` JavaScript function declarations are hoisted. When using `async function reloadItems()`, the declaration is hoisted, so `_originalReloadItems` captures the NEW function (the override itself), not the original.
- **Evidence**: Console error "RangeError: Maximum call stack size exceeded" with stack trace showing `reloadItems` calling itself
- **Resolved**: 2026-02-05 15:52
- **Solution**: Use function expression assignment instead of function declaration:

**Before (wrong - infinite recursion):**
```javascript
const _originalReloadItems = typeof reloadItems === 'function' ? reloadItems : null;
async function reloadItems() {  // HOISTED - captures itself!
  if (_originalReloadItems) await _originalReloadItems();
  await cacheDomains();
}
```

**After (correct):**
```javascript
const _originalReloadItems = reloadItems;  // Captures original
reloadItems = async function() {  // Assignment, not declaration
  await _originalReloadItems();
  await cacheDomains();
};
```

- **Verification**: Tested with Playwright - create domain updates table immediately, Crawl button works

## Document History

**[2026-02-05 15:18]**
- Added: V2FX-FL-001 - reloadItems override did not execute
