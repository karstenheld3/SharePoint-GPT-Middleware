# TEST: SSE Streaming - Option 1: Cascade Agent with MCP Playwright

**Doc ID**: STRM-TP01-OPT1
**Goal**: Verify SSE events arrive in browser in real-time using Cascade agent with Playwright MCP server
**Timeline**: Created 2026-03-03

## Prerequisites

- Server running at `http://127.0.0.1:8000`
- Playwright MCP server connected
- SharePoint credentials configured (for security_scan/selftest)

## Test Execution Instructions

The Cascade agent should execute the following tests using `mcp1_browser_*` tools.

## MUST TEST Endpoints

### TC-01: /v2/sites/selftest

**UI Page**: `http://127.0.0.1:8000/v2/sites?format=ui`
**Button**: "Run Selftest"

**Steps**:
1. `mcp1_browser_navigate` to UI page
2. `mcp1_browser_click` on "Run Selftest" button
3. `mcp1_browser_wait_for` 30 seconds or until completion
4. `mcp1_browser_snapshot` to capture console output

**Pass Criteria**:
- Result shows "OK" with passed tests
- Console output shows timestamps with events arriving over time (not all at once)

### TC-02: /v2/domains/selftest

**UI Page**: `http://127.0.0.1:8000/v2/domains?format=ui`
**Button**: "Run Selftest"

**Steps**:
1. `mcp1_browser_navigate` to UI page
2. `mcp1_browser_click` on "Run Selftest" button
3. `mcp1_browser_wait_for` 30 seconds or until completion
4. `mcp1_browser_snapshot` to capture console output

**Pass Criteria**:
- Result shows "OK"
- Console output shows incremental event delivery

### TC-03: /v2/jobs/selftest

**UI Page**: `http://127.0.0.1:8000/v2/jobs?format=ui`
**Button**: "Run Selftest"

**Steps**:
1. `mcp1_browser_navigate` to UI page
2. `mcp1_browser_click` on "Run Selftest" button
3. `mcp1_browser_wait_for` 60 seconds or until completion
4. `mcp1_browser_snapshot` to capture console output

**Pass Criteria**:
- Result shows "OK"
- Console output shows incremental event delivery

### TC-04: /v2/sites/security_scan/selftest (PRIMARY STREAMING TEST)

**UI Page**: `http://127.0.0.1:8000/v2/sites?format=ui`
**Button**: "Security Scan Selftest"

**Steps**:
1. `mcp1_browser_navigate` to UI page
2. `mcp1_browser_click` on "Security Scan Selftest" button
3. `mcp1_browser_wait_for` 120 seconds or until completion
4. `mcp1_browser_snapshot` to capture console output

**Pass Criteria**:
- Result shows "OK" (10 passed, 1 expected failure)
- Console output shows **visible time gaps** (1-3 seconds between events)
- Total duration > 10 seconds
- Events arrive incrementally during execution, NOT all at once at the end

**This is the most important test** - it uses blocking SharePoint I/O which was the original cause of the buffering issue.

### TC-05: /v2/demorouter1/create_demo_items

**UI Page**: `http://127.0.0.1:8000/v2/demorouter1?format=ui`
**Action**: Fill form and submit

**Steps**:
1. `mcp1_browser_navigate` to UI page
2. Fill in item count (e.g., 10)
3. Submit form
4. `mcp1_browser_wait_for` completion
5. Verify incremental progress events

**Pass Criteria**:
- Progress events arrive incrementally during creation
- Final result shows items created

### TC-06: /v2/reports/create_demo_reports

**UI Page**: `http://127.0.0.1:8000/v2/reports?format=ui`
**Action**: Trigger demo report creation

**Steps**:
1. `mcp1_browser_navigate` to UI page
2. Click appropriate button
3. Wait for completion
4. Verify incremental event delivery

**Pass Criteria**:
- Events arrive incrementally
- Report creation completes successfully

## Event Structure Verification

### TC-07: SSE events contain valid JSON

**How to verify**:
After any selftest completes, examine the console output. Each event line should be parseable JSON.

**Pass Criteria**:
- All event data is valid JSON
- No parse errors in console

### TC-08: First event is start_json, last is end_json

**How to verify**:
Check console output sequence after selftest.

**Pass Criteria**:
- First event contains "===== START" or "start_json"
- Last event contains "===== END" or "end_json"

### TC-09: end_json contains ok: true

**How to verify**:
After successful selftest, click OK on result dialog and examine the JSON.

**Pass Criteria**:
- Result JSON shows `"ok": true`
- No failed tests in result

## Edge Cases

### TC-10: Cancelled stream stops event delivery

**Steps**:
1. `mcp1_browser_click` on "Security Scan Selftest"
2. Wait 2 seconds
3. `mcp1_browser_navigate` away (or click Cancel button)
4. Verify no errors, clean cancellation

**Pass Criteria**:
- No JavaScript errors
- Stream stops cleanly

### TC-11: Multiple concurrent streams don't interfere

**Steps**:
1. Open two browser tabs using `mcp1_browser_tabs` action: "new"
2. Navigate both to `/v2/sites?format=ui`
3. Trigger selftest in both tabs
4. Verify both complete independently

**Pass Criteria**:
- Both selftests complete successfully
- Results don't mix between tabs

## Direct EventSource Tests (Layer 1)

**Note**: These tests may have CORS issues when run via MCP `page.evaluate()`. If they fail with "connection_error", skip and rely on Layer 2 (console) tests instead.

### TC-12: /v2/sites/selftest via EventSource

**Steps**:
```javascript
mcp1_browser_evaluate with:
async () => {
  return new Promise((resolve) => {
    const events = [];
    const es = new EventSource('http://127.0.0.1:8000/v2/sites/selftest?format=stream');
    es.onmessage = (e) => { events.push(e.data); if (e.data.includes('END')) { es.close(); resolve(events); }};
    es.onerror = () => { es.close(); resolve({error: 'connection_error'}); };
  });
}
```

**Pass Criteria**:
- Events array contains multiple entries
- No connection_error (or skip if CORS blocks)

### TC-13: /v2/domains/selftest via EventSource

Same approach as TC-12 with `/v2/domains/selftest?format=stream`

### TC-14: /v2/jobs/selftest via EventSource

Same approach as TC-12 with `/v2/jobs/selftest?format=stream`

## Execution Checklist

Run these commands in sequence:

```
[ ] TC-01: sites/selftest - PASSED / FAILED
[ ] TC-02: domains/selftest - PASSED / FAILED
[ ] TC-03: jobs/selftest - PASSED / FAILED
[ ] TC-04: security_scan/selftest - PASSED / FAILED (most important)
[ ] TC-05: demorouter1/create_demo_items - PASSED / FAILED
[ ] TC-06: reports/create_demo_reports - PASSED / FAILED
[ ] TC-07: SSE events valid JSON - PASSED / FAILED
[ ] TC-08: start_json/end_json sequence - PASSED / FAILED
[ ] TC-09: end_json ok:true - PASSED / FAILED
[ ] TC-10: Cancelled stream - PASSED / FAILED / SKIPPED
[ ] TC-11: Concurrent streams - PASSED / FAILED / SKIPPED
[ ] TC-12: EventSource sites - PASSED / FAILED / SKIPPED (CORS)
[ ] TC-13: EventSource domains - PASSED / FAILED / SKIPPED (CORS)
[ ] TC-14: EventSource jobs - PASSED / FAILED / SKIPPED (CORS)
```

## How to Verify Real-Time Streaming

**IMPORTANT**: Server-side timestamps in log messages do NOT prove real-time streaming. Events can be created with delays on the server but still be buffered and flushed to the browser all at once.

**True verification**: Observe the console output WHILE the test is running. Events should appear incrementally during execution, not all at once when the job completes.

**Method 1: Visual observation during execution**
1. Click the selftest button
2. Watch the console panel - events should appear one-by-one with visible delays
3. If all events appear instantly at the end, streaming is broken

**Method 2: Capture console text at 200ms intervals using page.evaluate()**

Use `mcp1_browser_evaluate` to run JavaScript that captures console text multiple times and compares:

```javascript
async () => {
  // Click the Security Scan Selftest button
  const btn = document.querySelector('button:has-text("Security Scan Selftest")') 
    || [...document.querySelectorAll('button')].find(b => b.textContent.includes('Security Scan Selftest'));
  if (btn) btn.click();
  
  // Capture console text at 200ms intervals
  const snapshots = [];
  const consoleSelector = '[class*="console"], [id*="console"], pre, .output';
  
  for (let i = 0; i < 50; i++) {  // 50 * 200ms = 10 seconds max
    await new Promise(r => setTimeout(r, 200));
    
    // Find console output element and get its text
    const consoleEl = document.querySelector(consoleSelector) 
      || document.evaluate("//div[contains(text(),'START')]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue?.parentElement;
    
    const text = consoleEl ? consoleEl.innerText : '';
    const lineCount = text.split('\\n').filter(l => l.trim()).length;
    
    snapshots.push({ time: i * 200, lineCount, textLength: text.length });
    
    // Stop if we see END marker
    if (text.includes('===== END')) break;
  }
  
  // Analyze: check if line count increased over time
  const firstCount = snapshots[0]?.lineCount || 0;
  const lastCount = snapshots[snapshots.length - 1]?.lineCount || 0;
  const increments = snapshots.filter((s, i) => i > 0 && s.lineCount > snapshots[i-1].lineCount).length;
  
  // Check for "burst" pattern: large jump in single increment (>70% of total lines)
  let maxJump = 0;
  for (let i = 1; i < snapshots.length; i++) {
    const jump = snapshots[i].lineCount - snapshots[i-1].lineCount;
    if (jump > maxJump) maxJump = jump;
  }
  const burstDetected = lastCount > 0 && maxJump > (lastCount * 0.7);
  
  // Streaming is valid if: multiple increments AND no single burst > 70%
  const streaming = increments >= 4 && !burstDetected;
  
  return {
    snapshots: snapshots.slice(0, 10), // First 10 for brevity
    totalSnapshots: snapshots.length,
    firstLineCount: firstCount,
    lastLineCount: lastCount,
    incrementCount: increments,
    maxSingleJump: maxJump,
    burstDetected: burstDetected,
    streaming: streaming
  };
}
```

**Pass Criteria**:
- `incrementCount >= 4` - Console text grew at least 4 times during execution
- `burstDetected: false` - No single increment > 70% of total lines
- `streaming: true` - Events arrived incrementally

**Fail Criteria**:
- `incrementCount < 4` - Too few increments (likely buffered)
- `burstDetected: true` - Large burst at end (e.g., first line immediate, rest buffered)
- `streaming: false` - Events did not arrive incrementally

**GOOD (streaming works)**:
- Console shows 3-5 events after 3 seconds, test still running
- Events appear visually one-by-one with gaps

**BAD (buffered)**:
- Console stays empty during execution
- All events appear instantly when result dialog opens

## Document History

**[2026-03-03 22:54]**
- Fixed: Verification instructions - server timestamps don't prove streaming
- Added: Method 1 (visual observation) and Method 2 (snapshot during execution)

**[2026-03-03 22:50]**
- Added: TC-07 to TC-14 (Event Structure, Edge Cases, EventSource)
- Changed: All endpoints to MUST TEST (removed SHOULD TEST)

**[2026-03-03 22:45]**
- Initial version created
