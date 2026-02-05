# IMPL: Domains Router V2 Fixes

**Doc ID**: V2FX-IP02
**Goal**: Document bug fixes for the Domains Router V2

**Target file**: `src/routers_v2/domains.py`

## Table of Contents

1. [FIX-001: Domain Cache Not Updated After Create](#fix-001-domain-cache-not-updated-after-create)
2. [Document History](#document-history)

## FIX-001: Domain Cache Not Updated After Create

**Date**: 2026-02-05
**Status**: RESOLVED

**Symptoms**:
1. Error "Domain not found in cache. Please reload the page." when clicking "Crawl" on a newly created domain
2. Table not updating after domain creation (showing stale count)

**Root Cause**:
- `domainsState` Map is populated by `cacheDomains()` only on `DOMContentLoaded`
- When a new domain is created, `reloadItems()` updates the table HTML but does NOT update `domainsState`
- Initial fix attempt used function declaration which caused infinite recursion due to JavaScript hoisting

**Fix Applied**:
Override `reloadItems()` using function expression assignment (NOT declaration) to avoid hoisting:

```javascript
// Must use assignment (not function declaration) to avoid hoisting issues
const _originalReloadItems = reloadItems;
reloadItems = async function() {
  await _originalReloadItems();
  await cacheDomains();
};
```

**Why function expression, not declaration**:
```javascript
// WRONG - function declaration is hoisted, _originalReloadItems captures itself
async function reloadItems() { ... }

// CORRECT - assignment happens at runtime, captures original first
reloadItems = async function() { ... };
```

**Location**: `src/routers_v2/domains.py` lines 323-329

**Verification**:
1. Create a new domain via UI
2. Table updates immediately showing new domain
3. Click "Crawl" button - form opens with domain selected
4. No console errors (previously showed RangeError: Maximum call stack size exceeded)

## Document History

**[2026-02-05 15:52]**
- Updated: FIX-001 - Corrected fix using function expression instead of declaration

**[2026-02-05 15:10]**
- Added: FIX-001 - Domain cache not updated after create (initial attempt)
