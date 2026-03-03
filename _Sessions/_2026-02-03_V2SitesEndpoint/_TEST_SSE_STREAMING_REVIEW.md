# Devil's Advocate Review: SSE Streaming Test Plan

**Reviewed**: 2026-03-03 15:20
**Source**: `_TEST_SSE_STREAMING.md` [STRM-TP01]
**Context**: Test plan for verifying SSE real-time streaming via Playwright

## Industry Research Findings

### 1. Playwright SSE/EventSource Limitations

**Source**: GitHub issue microsoft/playwright#15353, Stack Overflow

**Finding**: Playwright does NOT have native SSE/EventSource interception like it does for WebSockets. Key limitations:
- `page.on('websocket')` exists but NO equivalent `page.on('eventsource')`
- `response.body()` blocks until response completes - cannot stream chunks
- Mocking SSE responses is problematic (content-type issues)

**Impact on test plan**: The `page.on('console')` approach is a workaround, not a first-class solution.

### 2. Console Capture Dependency

**Finding**: The test plan assumes the UI logs SSE events to browser console. This is an APPLICATION behavior, not guaranteed by SSE protocol.

**Risk**: If UI code changes to NOT log events, all tests break silently.

### 3. Timing-Based Tests Are Fragile

**Source**: Industry best practices for E2E testing

**Finding**: Tests that depend on timing (500ms polling, 100ms gaps) are inherently flaky:
- CI environments have variable performance
- Headless mode may behave differently
- Network latency affects timing

### 4. Alternative Approaches Found

**Better pattern**: Use `page.evaluate()` to create EventSource directly and capture events in page context, then retrieve via evaluate:

```javascript
const events = await page.evaluate(async () => {
  return new Promise((resolve) => {
    const captured = [];
    const es = new EventSource('/v2/sites/selftest');
    es.onmessage = (e) => {
      captured.push({ time: Date.now(), data: e.data });
    };
    es.onerror = () => {
      es.close();
      resolve(captured);
    };
  });
});
```

This bypasses console capture and directly tests EventSource behavior.

## Critical Issues

### STRM-TP01-RV-01: Console Capture Assumption is Fragile

**Severity**: HIGH
**Location**: Section 8 - SSEEventCapture class

**Problem**: The entire test strategy depends on `page.on('console')` capturing SSE events. This requires:
1. UI JavaScript must log each SSE event to console
2. Log format must contain 'event:' or 'data:' strings
3. Console events must fire synchronously with SSE arrival

**Evidence**: Reviewed UI code - it DOES log to console, but this is implementation detail, not contract.

**Risk**: Future UI refactoring could break all tests without touching SSE code.

**Recommendation**: Use direct EventSource interception via `page.evaluate()` instead of console capture.

### STRM-TP01-RV-02: Timing Thresholds Are Arbitrary

**Severity**: MEDIUM
**Location**: Section 3 - Pass Criteria, Section 8 - `assert_realtime_streaming()`

**Problem**: Magic numbers without justification:
- `min_span_ms=500` - Why 500ms?
- `min_gap_ms=50` - Why 50ms?
- `poll_interval=0.5` - Why 500ms polling?

**Risk**: Tests may be flaky on slow CI runners or pass on buffered implementations with fast I/O.

**Recommendation**: 
1. Document rationale for each threshold
2. Consider relative assertions (e.g., "first 50% of events arrive before last event")
3. Add retry logic for timing-sensitive assertions

### STRM-TP01-RV-03: Headless Mode May Mask Issues

**Severity**: MEDIUM
**Location**: Section 5 - Setup code

**Problem**: `headless=True` may behave differently than real browser:
- Event loop timing differs
- Console capture timing differs
- Some browser features disabled

**Evidence**: GitHub issues report SSE behavior differences in headless mode.

**Recommendation**: Run critical tests (TC-01 to TC-03) in headed mode at least once.

## High Priority Issues

### STRM-TP01-RV-04: No Verification UI Actually Logs Events

**Severity**: HIGH
**Location**: Entire test approach

**Problem**: Test plan assumes UI logs SSE events but doesn't verify this assumption. No test checks that console capture actually works.

**Recommendation**: Add TC-00 (prerequisite test) that verifies:
1. Navigate to UI page
2. Trigger selftest
3. Assert at least 1 console message contains "event:" or "data:"
4. If this fails, skip all other tests with clear error message

### STRM-TP01-RV-05: Event Type Parsing is Fragile

**Severity**: MEDIUM  
**Location**: Section 8 - `_parse_event_type()` method

**Problem**: Simple string matching (`'start_json' in text`) will match false positives:
- Log message "Parsing start_json event..." matches
- Any console.log containing "state" matches

**Recommendation**: Parse actual SSE event format (`event: start_json\ndata: {...}`) not arbitrary strings.

## Medium Priority Issues

### STRM-TP01-RV-06: No Test for "Buffered" Baseline

**Severity**: LOW
**Location**: Test cases

**Problem**: Tests prove streaming works but don't establish baseline. How do we know what "buffered" looks like?

**Recommendation**: Add negative test:
1. Temporarily remove `stream_with_flush()` wrapper
2. Run test - should FAIL (all events arrive at once)
3. This proves the test actually detects the problem

### STRM-TP01-RV-07: TC-11 (Exception Test) Has No Trigger

**Severity**: MEDIUM
**Location**: TC-11 definition

**Problem**: TC-11 says "Trigger endpoint that throws exception mid-stream" but no such endpoint exists in MUST TEST list. Security scan selftest could throw but requires SharePoint credentials.

**Recommendation**: Either:
1. Create a test-only endpoint that throws after N events
2. Move TC-11 to SHOULD TEST with SharePoint credentials
3. Mock exception via route interception

## Questions That Need Answers

1. **Does the UI actually log SSE events to console?** - Need to verify in browser DevTools before implementing tests.

2. **What format are SSE events logged in?** - Need exact string format to write reliable parser.

3. **Do selftest endpoints emit enough events?** - Need at least 3 events with gaps for timing assertions to work.

4. **How long do selftests take?** - 60 second timeout may be too short for jobs/selftest.

## Recommendations Summary

**Immediate Actions (before implementing tests):**
1. Verify UI logs SSE events to console - open browser, run selftest, check DevTools
2. Document exact console log format for SSE events
3. Add TC-00 prerequisite test for console capture verification

**Code Changes:**
1. Consider `page.evaluate()` + EventSource approach instead of console capture
2. Add retry logic for timing-sensitive assertions
3. Parse actual SSE format, not arbitrary strings

**Test Robustness:**
1. Run tests 3x to verify no flakiness before committing
2. Test in both headless and headed mode
3. Add negative test to prove detection works

## Document History

**[2026-03-03 15:20]**
- Initial Devil's Advocate review
- Research findings: Playwright lacks native SSE support
- 7 issues identified (2 critical, 2 high, 3 medium)
- Recommended alternative approach using page.evaluate()
