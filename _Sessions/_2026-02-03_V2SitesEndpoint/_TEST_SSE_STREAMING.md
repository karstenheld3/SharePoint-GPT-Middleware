# TEST: SSE Streaming Real-Time Verification

**Doc ID**: STRM-TP01
**Feature**: SSE_REALTIME_VERIFICATION
**Goal**: Verify SSE events arrive in browser in real-time (not buffered) using Playwright UI automation
**Timeline**: Created 2026-03-03

**Target file**: `tests/test_sse_streaming.py`

## MUST-NOT-FORGET

- Test in BROWSER context (Playwright), not curl - curl doesn't expose buffering issue
- Poll console at 500ms intervals to prove incremental arrival
- Each test must show events arriving BEFORE request completes
- Use `page.on('console')` to capture SSE events as they arrive
- Cleanup test artifacts after each test

## Table of Contents

1. [Overview](#1-overview)
2. [Scenario](#2-scenario)
3. [Test Strategy](#3-test-strategy)
4. [Test Priority Matrix](#4-test-priority-matrix)
5. [Test Data](#5-test-data)
6. [Test Cases](#6-test-cases)
7. [Test Phases](#7-test-phases)
8. [Helper Functions](#8-helper-functions)
9. [Cleanup](#9-cleanup)
10. [Verification Checklist](#10-verification-checklist)
11. [Document History](#11-document-history)

## 1. Overview

This test plan verifies that SSE (Server-Sent Events) streaming endpoints deliver events to the browser in real-time rather than buffering them until completion. The tests use Playwright to automate browser interaction and capture console output timestamps to prove incremental delivery.

**Key insight**: The buffering issue only manifests in browsers, not in curl. Curl processes data at TCP level while browser fetch API buffers until explicit flush. Our `stream_with_flush()` wrapper forces flushes via `asyncio.sleep(0)`.

## 2. Scenario

**Problem:** SSE events were arriving all at once after endpoint completion instead of streaming in real-time. This made long-running operations appear frozen to users.

**Solution:** Prove real-time streaming by:
1. Triggering endpoint via UI button
2. Capturing console.log timestamps as events arrive
3. Asserting events arrive incrementally (time gaps between events)
4. Asserting first event arrives before last event (not all at once)

**What we don't want:**
- Tests that pass with curl but fail in browser
- Tests that only check final result, not incremental arrival
- Flaky timing-based tests (use relative timing, not absolute)

## 3. Test Strategy

**Approach**: Integration (Playwright browser automation)

**Dual-Layer Verification:**

We test TWO independent failure points:

**Layer 1 - SSE Protocol (EventSource)**:
- Use `page.evaluate()` to create EventSource directly
- Capture timestamps when each SSE event arrives
- Proves: Server streams events incrementally

**Layer 2 - UI Console Integration**:
- Use `page.on('console')` to capture console output
- Trigger via UI button click (real user flow)
- Proves: UI correctly dispatches events to console in realtime

**Why both layers?**
- Layer 1 can pass but Layer 2 can fail (UI bug in event dispatching)
- If only Layer 2 fails, we know the problem is UI code, not SSE
- If Layer 1 fails, SSE streaming itself is broken

**Pass Criteria (both layers):**
- At least 3 events captured with distinct timestamps
- Time span from first to last event > 500ms (proves not instant batch)
- Events arrive at intervals (not all within 100ms)

## 4. Test Priority Matrix

### MUST TEST (Critical Business Logic)

- **`/v2/sites/selftest`** - sites.py
  - Testability: **EASY**, Effort: Low
  - Has blocking I/O (httpx async but multiple operations)
  - UI button available at `/v2/sites?format=ui`

- **`/v2/domains/selftest`** - domains.py
  - Testability: **EASY**, Effort: Low
  - Has async I/O (httpx)
  - UI button available at `/v2/domains?format=ui`

- **`/v2/jobs/selftest`** - jobs.py
  - Testability: **EASY**, Effort: Low
  - Has file I/O and async operations
  - UI button available at `/v2/jobs?format=ui`

### SHOULD TEST (Important Workflows)

- **`/v2/demorouter1/create_demo_items`** - demorouter1.py
  - Testability: Medium, Effort: Low
  - Long-running with multiple events
  - Good for timing analysis

- **`/v2/reports/create_demo_reports`** - reports.py
  - Testability: Medium, Effort: Low
  - File I/O based streaming

### DROP (Not Worth Testing in Automation)

- **`/v2/sites/security_scan/selftest`** - Reason: Requires SharePoint credentials
- **`/v2/crawler/selftest`** - Reason: Requires SharePoint credentials, long runtime
- **`/v2/crawler/crawl`** - Reason: Requires configured domain and SharePoint access

## 5. Test Data

**Required Fixtures:**
- Running server at `http://127.0.0.1:8000`
- Browser context (Playwright Chromium)

**Environment Variables:**
- None required for MUST TEST endpoints
- SharePoint credentials only for SHOULD TEST with real data

**Setup:**
```python
import asyncio
from playwright.async_api import async_playwright

async def setup_browser():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()
    return playwright, browser, page
```

**Teardown:**
```python
async def teardown_browser(playwright, browser):
    await browser.close()
    await playwright.stop()
```

## 6. Test Cases

### Category 1: Real-Time Event Delivery (5 tests)

- **STRM-TP01-TC-01**: `/v2/sites/selftest` streams events incrementally
  - Trigger via UI button click
  - Capture console timestamps
  - -> ok=true, events arrive with time gaps > 100ms between at least 3 events

- **STRM-TP01-TC-02**: `/v2/domains/selftest` streams events incrementally
  - Trigger via UI button click
  - -> ok=true, events arrive incrementally, total span > 500ms

- **STRM-TP01-TC-03**: `/v2/jobs/selftest` streams events incrementally
  - Trigger via UI button click
  - -> ok=true, events arrive incrementally

- **STRM-TP01-TC-04**: `/v2/demorouter1/create_demo_items` streams events during long operation
  - Trigger via UI form submission
  - -> ok=true, progress events arrive before completion

- **STRM-TP01-TC-05**: `/v2/reports/create_demo_reports` streams events incrementally
  - Trigger via UI
  - -> ok=true, events arrive incrementally

### Category 2: Event Structure Verification (3 tests)

- **STRM-TP01-TC-06**: SSE events contain valid JSON
  - Parse each captured event as JSON
  - -> ok=true, all events parse successfully

- **STRM-TP01-TC-07**: First event is `start_json`, last is `end_json`
  - Check event types in order
  - -> ok=true, proper event sequence

- **STRM-TP01-TC-08**: `end_json` contains `ok: true` for successful selftests
  - Parse final event
  - -> ok=true, selftest completed successfully

### Category 3: Edge Cases (2 tests)

- **STRM-TP01-TC-09**: Cancelled stream stops event delivery
  - Click button, then navigate away mid-stream
  - -> ok=true, no errors, clean cancellation [ASSUMED]

- **STRM-TP01-TC-10**: Multiple concurrent streams don't interfere
  - Open two browser tabs, trigger selftests simultaneously
  - -> ok=true, both complete independently [ASSUMED]

### Category 4: Direct SSE Protocol Verification (3 tests)

Tests SSE streaming at protocol level, independent of UI console integration.

- **STRM-TP01-TC-11**: `/v2/sites/selftest` SSE events arrive incrementally via EventSource
  - Use `page.evaluate()` to create EventSource directly (bypass UI)
  - Capture event timestamps in page context
  - -> ok=true, events arrive with time gaps > 100ms [ASSUMED]

- **STRM-TP01-TC-12**: `/v2/domains/selftest` SSE events arrive incrementally via EventSource
  - Same approach as TC-11
  - -> ok=true, events arrive incrementally [ASSUMED]

- **STRM-TP01-TC-13**: `/v2/jobs/selftest` SSE events arrive incrementally via EventSource
  - Same approach as TC-11
  - -> ok=true, events arrive incrementally [ASSUMED]

**Layer comparison**: If TC-01 to TC-03 (console) fail but TC-11 to TC-13 (EventSource) pass, the bug is in UI code, not SSE streaming.

## 7. Test Phases

Ordered execution sequence:

1. **Phase 1: Server Health** - Verify server is running and responsive
2. **Phase 2: UI Navigation** - Navigate to each router UI page
3. **Phase 3: Selftest Streaming** - Run TC-01 through TC-03 (critical)
4. **Phase 4: Long-Running Streams** - Run TC-04, TC-05
5. **Phase 5: Event Validation** - Run TC-06 through TC-08
6. **Phase 6: Edge Cases** - Run TC-09, TC-10
7. **Phase 7: Direct SSE Protocol** - Run TC-11 through TC-13
8. **Phase 8: Cleanup** - Close browsers, report results

## 8. Helper Functions

### Event Capture Setup

```python
import time
from dataclasses import dataclass
from typing import List

@dataclass
class CapturedEvent:
    timestamp: float
    message: str
    event_type: str  # 'start_json', 'log', 'state', 'end_json'

class SSEEventCapture:
    def __init__(self):
        self.events: List[CapturedEvent] = []
        self.start_time: float = 0
    
    def start(self):
        self.events = []
        self.start_time = time.time()
    
    def capture(self, msg):
        """Called from page.on('console') handler"""
        text = msg.text
        if 'event:' in text or 'data:' in text:
            event_type = self._parse_event_type(text)
            self.events.append(CapturedEvent(
                timestamp=time.time() - self.start_time,
                message=text,
                event_type=event_type
            ))
    
    def _parse_event_type(self, text: str) -> str:
        if 'start_json' in text: return 'start_json'
        if 'end_json' in text: return 'end_json'
        if 'state' in text: return 'state'
        return 'log'
    
    def get_time_span(self) -> float:
        """Return time between first and last event"""
        if len(self.events) < 2:
            return 0
        return self.events[-1].timestamp - self.events[0].timestamp
    
    def get_event_gaps(self) -> List[float]:
        """Return time gaps between consecutive events"""
        gaps = []
        for i in range(1, len(self.events)):
            gaps.append(self.events[i].timestamp - self.events[i-1].timestamp)
        return gaps
    
    def assert_realtime_streaming(self, min_events=3, min_span_ms=500, min_gap_ms=50):
        """Assert events arrived in real-time (not batched)"""
        assert len(self.events) >= min_events, \
            f"Expected at least {min_events} events, got {len(self.events)}"
        
        span_ms = self.get_time_span() * 1000
        assert span_ms >= min_span_ms, \
            f"Expected time span >= {min_span_ms}ms, got {span_ms:.0f}ms (events arrived too fast = batched)"
        
        gaps = self.get_event_gaps()
        significant_gaps = [g for g in gaps if g * 1000 >= min_gap_ms]
        assert len(significant_gaps) >= 2, \
            f"Expected at least 2 gaps >= {min_gap_ms}ms, got {len(significant_gaps)} (events batched)"
```

### Test Runner

```python
async def run_selftest_streaming_test(page, ui_url: str, button_selector: str, capture: SSEEventCapture):
    """
    Generic test runner for selftest streaming verification.
    
    Args:
        page: Playwright page object
        ui_url: URL of the UI page (e.g., '/v2/sites?format=ui')
        button_selector: CSS selector for the selftest button
        capture: SSEEventCapture instance
    """
    # Navigate to UI page
    await page.goto(f"http://127.0.0.1:8000{ui_url}")
    await page.wait_for_load_state('networkidle')
    
    # Setup console capture
    capture.start()
    page.on('console', lambda msg: capture.capture(msg))
    
    # Click selftest button
    await page.click(button_selector)
    
    # Poll for completion (check for end_json event)
    max_wait = 60  # seconds
    poll_interval = 0.5  # 500ms
    elapsed = 0
    
    while elapsed < max_wait:
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
        
        # Check if we have end_json
        if any(e.event_type == 'end_json' for e in capture.events):
            break
        
        # Log progress for debugging
        print(f"[{elapsed:.1f}s] Captured {len(capture.events)} events so far...")
    
    # Verify real-time streaming
    capture.assert_realtime_streaming()
    
    # Return final event for additional assertions
    return capture.events[-1] if capture.events else None
```

### Polling Verification (Layer 2 - Console)

```python
async def poll_and_verify_incremental(page, capture: SSEEventCapture, timeout_sec=60):
    """
    Poll console output at 500ms intervals and verify events arrive incrementally.
    
    Thresholds rationale:
    - poll_interval=0.5: Balance between detection granularity and overhead
    - timeout_sec=60: Longest selftest (jobs) takes ~30s, 2x safety margin
    
    Returns dict with verification results.
    """
    snapshots = []  # (timestamp, event_count) tuples
    poll_interval = 0.5
    elapsed = 0
    
    while elapsed < timeout_sec:
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
        
        current_count = len(capture.events)
        snapshots.append((elapsed, current_count))
        
        # Check for completion
        if any(e.event_type == 'end_json' for e in capture.events):
            break
    
    # Analyze snapshots to prove incremental delivery
    # Events should increase over time, not jump from 0 to N at once
    incremental = False
    for i in range(1, len(snapshots)):
        prev_count = snapshots[i-1][1]
        curr_count = snapshots[i][1]
        if 0 < prev_count < curr_count:
            incremental = True
            break
    
    return {
        'total_events': len(capture.events),
        'time_span_ms': capture.get_time_span() * 1000,
        'snapshots': snapshots,
        'incremental': incremental,
        'passed': incremental and len(capture.events) >= 3
    }
```

### Direct EventSource Test (Layer 1 - SSE Protocol)

```python
async def test_sse_direct(page, endpoint_url: str, timeout_sec=60):
    """
    Test SSE streaming directly via EventSource (bypasses UI console).
    
    This tests Layer 1: Does the server stream events incrementally?
    Independent of whether UI correctly dispatches to console.
    
    Args:
        page: Playwright page object
        endpoint_url: Full URL to SSE endpoint (e.g., 'http://127.0.0.1:8000/v2/sites/selftest')
        timeout_sec: Maximum time to wait for completion
    
    Returns dict with captured events and timing analysis.
    """
    result = await page.evaluate(f"""
        async () => {{
            return new Promise((resolve) => {{
                const events = [];
                const startTime = Date.now();
                const es = new EventSource('{endpoint_url}');
                
                const timeout = setTimeout(() => {{
                    es.close();
                    resolve({{ events, error: 'timeout', timedOut: true }});
                }}, {timeout_sec * 1000});
                
                es.onmessage = (e) => {{
                    events.push({{
                        time: Date.now() - startTime,
                        data: e.data,
                        type: e.type || 'message'
                    }});
                    
                    // Check for end_json to close connection
                    if (e.data.includes('end_json')) {{
                        clearTimeout(timeout);
                        es.close();
                        resolve({{ events, error: null, timedOut: false }});
                    }}
                }};
                
                es.onerror = (err) => {{
                    clearTimeout(timeout);
                    es.close();
                    resolve({{ events, error: 'connection_error', timedOut: false }});
                }};
            }});
        }}
    """)
    
    # Analyze timing
    events = result.get('events', [])
    if len(events) >= 2:
        time_span_ms = events[-1]['time'] - events[0]['time']
        gaps = [events[i]['time'] - events[i-1]['time'] for i in range(1, len(events))]
        significant_gaps = [g for g in gaps if g >= 50]  # 50ms threshold
    else:
        time_span_ms = 0
        gaps = []
        significant_gaps = []
    
    return {
        'events': events,
        'total_events': len(events),
        'time_span_ms': time_span_ms,
        'gaps': gaps,
        'incremental': len(significant_gaps) >= 2,
        'error': result.get('error'),
        'passed': len(events) >= 3 and time_span_ms >= 500 and len(significant_gaps) >= 2
    }
```

### Layer Comparison Helper

```python
async def compare_layers(page, ui_url: str, button_selector: str, endpoint_url: str):
    """
    Run both Layer 1 (EventSource) and Layer 2 (Console) tests and compare results.
    
    Helps diagnose where streaming breaks:
    - Both pass: Everything works
    - Layer 1 passes, Layer 2 fails: UI bug (console dispatch broken)
    - Layer 1 fails: SSE streaming itself is broken
    - Both fail: Server-side streaming broken
    """
    # Layer 1: Direct EventSource
    layer1 = await test_sse_direct(page, endpoint_url)
    
    # Layer 2: Console capture via UI
    capture = SSEEventCapture()
    await page.goto(f"http://127.0.0.1:8000{ui_url}")
    await page.wait_for_load_state('networkidle')
    capture.start()
    page.on('console', lambda msg: capture.capture(msg))
    await page.click(button_selector)
    layer2 = await poll_and_verify_incremental(page, capture)
    
    return {
        'layer1_sse': layer1,
        'layer2_console': layer2,
        'diagnosis': _diagnose_layers(layer1, layer2)
    }

def _diagnose_layers(layer1: dict, layer2: dict) -> str:
    if layer1['passed'] and layer2['passed']:
        return "PASS: Both SSE streaming and console dispatch working"
    elif layer1['passed'] and not layer2['passed']:
        return "UI_BUG: SSE streams correctly but console dispatch is broken"
    elif not layer1['passed'] and layer2['passed']:
        return "UNEXPECTED: Console works but EventSource fails (check test logic)"
    else:
        return "SSE_BROKEN: Server-side streaming is not working"
```

## 9. Cleanup

- Close all browser contexts after each test
- No server-side cleanup needed for selftest endpoints (they self-cleanup)
- For `create_demo_items` tests, items are created in memory only (no persistence)

## 10. Verification Checklist

### Implementation
- [ ] **STRM-TP01-VC-01**: Test file created at `tests/test_sse_streaming.py`
- [ ] **STRM-TP01-VC-02**: SSEEventCapture helper class implemented
- [ ] **STRM-TP01-VC-03**: run_selftest_streaming_test helper implemented
- [ ] **STRM-TP01-VC-04**: poll_and_verify_incremental helper implemented

### Test Coverage - Layer 2 (Console)
- [ ] **STRM-TP01-VC-05**: TC-01 (sites/selftest console) implemented and passes
- [ ] **STRM-TP01-VC-06**: TC-02 (domains/selftest console) implemented and passes
- [ ] **STRM-TP01-VC-07**: TC-03 (jobs/selftest console) implemented and passes
- [ ] **STRM-TP01-VC-08**: TC-04 (demorouter1/create_demo_items) implemented and passes
- [ ] **STRM-TP01-VC-09**: TC-05 (reports/create_demo_reports) implemented and passes
- [ ] **STRM-TP01-VC-10**: TC-06 through TC-08 (event validation) implemented
- [ ] **STRM-TP01-VC-11**: TC-09, TC-10 (edge cases) implemented

### Test Coverage - Layer 1 (Direct SSE)
- [ ] **STRM-TP01-VC-12**: TC-11 (sites/selftest EventSource) implemented and passes
- [ ] **STRM-TP01-VC-13**: TC-12 (domains/selftest EventSource) implemented and passes
- [ ] **STRM-TP01-VC-14**: TC-13 (jobs/selftest EventSource) implemented and passes

### Final Verification
- [ ] **STRM-TP01-VC-15**: All tests pass with `pytest tests/test_sse_streaming.py`
- [ ] **STRM-TP01-VC-16**: Tests prove incremental delivery (not batched)
- [ ] **STRM-TP01-VC-17**: No flaky tests (run 3x to confirm stability)
- [ ] **STRM-TP01-VC-18**: Layer comparison diagnoses correctly (UI_BUG vs SSE_BROKEN)

## 11. Document History

**[2026-03-03 22:27]**
- Removed: Dependencies section (made self-consistent)

**[2026-03-03 15:20]**
- Added: Dual-layer test strategy (Layer 1: SSE Protocol, Layer 2: Console)
- Added: Category 4 - Direct SSE Protocol Verification (TC-11 to TC-13)
- Added: `test_sse_direct()` helper for EventSource testing
- Added: `compare_layers()` helper for diagnosing failures
- Changed: Removed TC-11 exception test (moved to DROP)
- Changed: Total test cases now 13 across 4 categories

**[2026-03-03 15:15]**
- Added: [ASSUMED] labels to edge case test assertions

**[2026-03-03 15:10]**
- Initial test plan created
- Defined real-time verification strategy using Playwright
- Added helper functions for event capture and polling
