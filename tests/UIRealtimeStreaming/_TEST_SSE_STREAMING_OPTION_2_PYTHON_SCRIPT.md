# TEST: SSE Streaming - Option 2: Python Script with Playwright

**Doc ID**: STRM-TP01-OPT2
**Goal**: Verify SSE events arrive in browser in real-time using Python pytest with Playwright
**Timeline**: Created 2026-03-03

**Target file**: `tests/UIRealtimeStreaming/test_sse_streaming.py`

## Prerequisites

- Python 3.10+
- `pip install playwright pytest pytest-asyncio`
- `playwright install chromium`
- Server running at `http://127.0.0.1:8000`
- SharePoint credentials configured (for security_scan/selftest)

## How to Run

```bash
# Run all tests
pytest tests/UIRealtimeStreaming/test_sse_streaming.py -v -s

# Run specific test
pytest tests/UIRealtimeStreaming/test_sse_streaming.py::TestSSEStreamingLayer2::test_tc04_security_scan_selftest_console -v -s
```

## MUST TEST Endpoints

### TC-01: /v2/sites/selftest

**Test Function**: `test_tc01_sites_selftest_console`
**Class**: `TestSSEStreamingLayer2`

**What it tests**:
- Navigate to `/v2/sites?format=ui`
- Click "Run Selftest" button
- Capture console events with timestamps
- Assert events arrive incrementally

### TC-02: /v2/domains/selftest

**Test Function**: `test_tc02_domains_selftest_console`
**Class**: `TestSSEStreamingLayer2`

**What it tests**:
- Navigate to `/v2/domains?format=ui`
- Click "Run Selftest" button
- Capture console events with timestamps
- Assert events arrive incrementally

### TC-03: /v2/jobs/selftest

**Test Function**: `test_tc03_jobs_selftest_console`
**Class**: `TestSSEStreamingLayer2`

**What it tests**:
- Navigate to `/v2/jobs?format=ui`
- Click "Run Selftest" button
- Capture console events with timestamps
- Assert events arrive incrementally

### TC-04: /v2/sites/security_scan/selftest (PRIMARY STREAMING TEST)

**Test Function**: `test_tc04_security_scan_selftest_console`
**Class**: `TestSSEStreamingLayer2`

**What it tests**:
- Navigate to `/v2/sites?format=ui`
- Click "Security Scan Selftest" button
- Capture console events with timestamps
- Assert **visible time gaps** (1-3 seconds between events)
- Assert total duration > 10 seconds

**This is the most important test** - it uses blocking SharePoint I/O.

### TC-05: /v2/demorouter1/create_demo_items

**Test Function**: `test_tc05_demorouter1_create_demo_items`
**Class**: `TestSSEStreamingLayer2`

**What it tests**:
- Navigate to `/v2/demorouter1?format=ui`
- Fill form and submit
- Capture console events with timestamps
- Assert events arrive incrementally

### TC-06: /v2/reports/create_demo_reports

**Test Function**: `test_tc06_reports_create_demo_reports`
**Class**: `TestSSEStreamingLayer2`

**What it tests**:
- Navigate to `/v2/reports?format=ui`
- Trigger demo report creation
- Capture console events with timestamps
- Assert events arrive incrementally

## Layer 1 Tests (Direct EventSource)

These tests bypass the UI and test SSE protocol directly:

### TC-12: /v2/sites/selftest via EventSource

**Test Function**: `test_tc12_sites_selftest_eventsource`
**Class**: `TestSSEStreamingLayer1`

### TC-13: /v2/domains/selftest via EventSource

**Test Function**: `test_tc13_domains_selftest_eventsource`
**Class**: `TestSSEStreamingLayer1`

### TC-14: /v2/jobs/selftest via EventSource

**Test Function**: `test_tc14_jobs_selftest_eventsource`
**Class**: `TestSSEStreamingLayer1`

## Test Implementation

The Python test file `test_sse_streaming.py` contains:

### Helper Classes

```python
@dataclass
class CapturedEvent:
    timestamp: float
    message: str
    event_type: str

class SSEEventCapture:
    def start(self): ...
    def capture(self, msg): ...
    def get_time_span(self) -> float: ...
    def get_event_gaps(self) -> List[float]: ...
    def assert_realtime_streaming(self, min_events=3, min_span_ms=500, min_gap_ms=50): ...
```

### Pass Criteria

The `assert_realtime_streaming()` method checks:
1. At least `min_events` events captured (default: 3)
2. Time span from first to last event >= `min_span_ms` (default: 500ms)
3. At least 2 gaps >= `min_gap_ms` between events (default: 50ms)

For TC-04 (security_scan), stricter criteria:
- `min_events=5`
- `min_span_ms=5000` (5 seconds)
- `min_gap_ms=500` (0.5 seconds)

## Expected Output

```
$ pytest tests/UIRealtimeStreaming/test_sse_streaming.py -v -s

test_sse_streaming.py::TestSSEStreamingLayer1::test_tc12_sites_selftest_eventsource PASSED
test_sse_streaming.py::TestSSEStreamingLayer1::test_tc13_domains_selftest_eventsource PASSED
test_sse_streaming.py::TestSSEStreamingLayer1::test_tc14_jobs_selftest_eventsource PASSED
test_sse_streaming.py::TestSSEStreamingLayer2::test_tc01_sites_selftest_console PASSED
test_sse_streaming.py::TestSSEStreamingLayer2::test_tc04_security_scan_selftest_console PASSED

========================= 5 passed in 45.23s =========================
```

## Troubleshooting

### "No module named 'playwright'"
```bash
pip install playwright
playwright install chromium
```

### Connection refused
Start the server first:
```bash
cd src
$env:PYTHONPATH="E:\Dev\SharePoint-GPT-Middleware\src"
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

### Test timeout
Increase timeout in test or check if endpoint is actually streaming.

## Document History

**[2026-03-03 22:45]**
- Initial version created
- 4 MUST TEST endpoints, 2 SHOULD TEST endpoints
- Layer 1 (EventSource) and Layer 2 (Console) tests
