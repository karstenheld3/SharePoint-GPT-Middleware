"""
SSE Streaming Real-Time Verification Tests

Tests that SSE events arrive in browser in real-time (not buffered).
Uses Playwright to automate browser interaction and verify incremental delivery.

Test Plan: _TEST_SSE_STREAMING.md [STRM-TP01]
"""
import asyncio
import time
from dataclasses import dataclass
from typing import List

import pytest
from playwright.async_api import async_playwright, Page


BASE_URL = "http://127.0.0.1:8000"


@dataclass
class CapturedEvent:
    timestamp: float
    message: str
    event_type: str


class SSEEventCapture:
    """Captures SSE events from browser console output."""
    
    def __init__(self):
        self.events: List[CapturedEvent] = []
        self.start_time: float = 0
    
    def start(self):
        self.events = []
        self.start_time = time.time()
    
    def capture(self, msg):
        """Called from page.on('console') handler."""
        text = msg.text
        if 'event:' in text or 'data:' in text or '====' in text or '[' in text:
            event_type = self._parse_event_type(text)
            self.events.append(CapturedEvent(
                timestamp=time.time() - self.start_time,
                message=text,
                event_type=event_type
            ))
    
    def _parse_event_type(self, text: str) -> str:
        if 'start_json' in text.lower() or '===== START' in text:
            return 'start_json'
        if 'end_json' in text.lower() or '===== END' in text:
            return 'end_json'
        if 'state' in text.lower():
            return 'state'
        return 'log'
    
    def get_time_span(self) -> float:
        """Return time between first and last event in seconds."""
        if len(self.events) < 2:
            return 0
        return self.events[-1].timestamp - self.events[0].timestamp
    
    def get_event_gaps(self) -> List[float]:
        """Return time gaps between consecutive events in seconds."""
        gaps = []
        for i in range(1, len(self.events)):
            gaps.append(self.events[i].timestamp - self.events[i-1].timestamp)
        return gaps
    
    def assert_realtime_streaming(self, min_events=3, min_span_ms=500, min_gap_ms=50):
        """Assert events arrived in real-time (not batched)."""
        assert len(self.events) >= min_events, \
            f"Expected at least {min_events} events, got {len(self.events)}"
        
        span_ms = self.get_time_span() * 1000
        assert span_ms >= min_span_ms, \
            f"Expected time span >= {min_span_ms}ms, got {span_ms:.0f}ms (events arrived too fast = batched)"
        
        gaps = self.get_event_gaps()
        significant_gaps = [g for g in gaps if g * 1000 >= min_gap_ms]
        assert len(significant_gaps) >= 2, \
            f"Expected at least 2 gaps >= {min_gap_ms}ms, got {len(significant_gaps)} (events batched)"


async def test_sse_direct(page: Page, endpoint_url: str, timeout_sec: int = 60) -> dict:
    """
    Test SSE streaming directly via EventSource (bypasses UI console).
    
    This tests Layer 1: Does the server stream events incrementally?
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
                    
                    if (e.data.includes('end_json') || e.data.includes('END')) {{
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
    
    events = result.get('events', [])
    if len(events) >= 2:
        time_span_ms = events[-1]['time'] - events[0]['time']
        gaps = [events[i]['time'] - events[i-1]['time'] for i in range(1, len(events))]
        significant_gaps = [g for g in gaps if g >= 50]
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


@pytest.fixture
async def browser_page():
    """Fixture to provide a Playwright browser page."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        yield page
        await browser.close()


class TestSSEStreamingLayer1:
    """Layer 1 tests: Direct SSE Protocol verification via EventSource."""
    
    @pytest.mark.asyncio
    async def test_tc12_sites_selftest_eventsource(self, browser_page):
        """TC-12: /v2/sites/selftest SSE events arrive incrementally via EventSource."""
        result = await test_sse_direct(
            browser_page, 
            f"{BASE_URL}/v2/sites/selftest?format=stream"
        )
        assert result['passed'], f"SSE streaming failed: {result}"
        assert result['incremental'], "Events did not arrive incrementally"
        print(f"TC-12 PASSED: {result['total_events']} events, {result['time_span_ms']:.0f}ms span")
    
    @pytest.mark.asyncio
    async def test_tc13_domains_selftest_eventsource(self, browser_page):
        """TC-13: /v2/domains/selftest SSE events arrive incrementally via EventSource."""
        result = await test_sse_direct(
            browser_page,
            f"{BASE_URL}/v2/domains/selftest?format=stream"
        )
        assert result['passed'], f"SSE streaming failed: {result}"
        print(f"TC-13 PASSED: {result['total_events']} events, {result['time_span_ms']:.0f}ms span")
    
    @pytest.mark.asyncio
    async def test_tc14_jobs_selftest_eventsource(self, browser_page):
        """TC-14: /v2/jobs/selftest SSE events arrive incrementally via EventSource."""
        result = await test_sse_direct(
            browser_page,
            f"{BASE_URL}/v2/jobs/selftest?format=stream"
        )
        assert result['passed'], f"SSE streaming failed: {result}"
        print(f"TC-14 PASSED: {result['total_events']} events, {result['time_span_ms']:.0f}ms span")


class TestSSEStreamingLayer2:
    """Layer 2 tests: Console capture via UI button click."""
    
    @pytest.mark.asyncio
    async def test_tc01_sites_selftest_console(self, browser_page):
        """TC-01: /v2/sites/selftest streams events to console incrementally."""
        capture = SSEEventCapture()
        
        await browser_page.goto(f"{BASE_URL}/v2/sites?format=ui")
        await browser_page.wait_for_load_state('networkidle')
        
        capture.start()
        browser_page.on('console', lambda msg: capture.capture(msg))
        
        await browser_page.click('button:has-text("Run Selftest")')
        
        # Wait for completion
        for _ in range(120):
            await asyncio.sleep(0.5)
            if any(e.event_type == 'end_json' for e in capture.events):
                break
        
        capture.assert_realtime_streaming()
        print(f"TC-01 PASSED: {len(capture.events)} events, {capture.get_time_span()*1000:.0f}ms span")
    
    @pytest.mark.asyncio
    async def test_tc02_domains_selftest_console(self, browser_page):
        """TC-02: /v2/domains/selftest streams events to console incrementally."""
        capture = SSEEventCapture()
        
        await browser_page.goto(f"{BASE_URL}/v2/domains?format=ui")
        await browser_page.wait_for_load_state('networkidle')
        
        capture.start()
        browser_page.on('console', lambda msg: capture.capture(msg))
        
        await browser_page.click('button:has-text("Run Selftest")')
        
        for _ in range(120):
            await asyncio.sleep(0.5)
            if any(e.event_type == 'end_json' for e in capture.events):
                break
        
        capture.assert_realtime_streaming()
        print(f"TC-02 PASSED: {len(capture.events)} events, {capture.get_time_span()*1000:.0f}ms span")
    
    @pytest.mark.asyncio
    async def test_tc03_jobs_selftest_console(self, browser_page):
        """TC-03: /v2/jobs/selftest streams events to console incrementally."""
        capture = SSEEventCapture()
        
        await browser_page.goto(f"{BASE_URL}/v2/jobs?format=ui")
        await browser_page.wait_for_load_state('networkidle')
        
        capture.start()
        browser_page.on('console', lambda msg: capture.capture(msg))
        
        await browser_page.click('button:has-text("Run Selftest")')
        
        for _ in range(120):
            await asyncio.sleep(0.5)
            if any(e.event_type == 'end_json' for e in capture.events):
                break
        
        capture.assert_realtime_streaming()
        print(f"TC-03 PASSED: {len(capture.events)} events, {capture.get_time_span()*1000:.0f}ms span")
    
    @pytest.mark.asyncio
    async def test_tc04_security_scan_selftest_console(self, browser_page):
        """TC-04: /v2/sites/security_scan/selftest streams with visible time gaps."""
        capture = SSEEventCapture()
        
        await browser_page.goto(f"{BASE_URL}/v2/sites?format=ui")
        await browser_page.wait_for_load_state('networkidle')
        
        capture.start()
        browser_page.on('console', lambda msg: capture.capture(msg))
        
        await browser_page.click('button:has-text("Security Scan Selftest")')
        
        # Wait for completion (longer timeout for SharePoint operations)
        for _ in range(240):
            await asyncio.sleep(0.5)
            if any(e.event_type == 'end_json' for e in capture.events):
                break
        
        # Security scan should have visible gaps (1-3 seconds between events)
        capture.assert_realtime_streaming(min_events=5, min_span_ms=5000, min_gap_ms=500)
        print(f"TC-04 PASSED: {len(capture.events)} events, {capture.get_time_span()*1000:.0f}ms span")
    
    @pytest.mark.asyncio
    async def test_tc05_demorouter1_create_demo_items(self, browser_page):
        """TC-05: /v2/demorouter1/create_demo_items streams events incrementally."""
        capture = SSEEventCapture()
        
        await browser_page.goto(f"{BASE_URL}/v2/demorouter1?format=ui")
        await browser_page.wait_for_load_state('networkidle')
        
        capture.start()
        browser_page.on('console', lambda msg: capture.capture(msg))
        
        # Fill form with item count and submit
        await browser_page.fill('input[name="count"]', '5')
        await browser_page.click('button:has-text("Create")')
        
        for _ in range(120):
            await asyncio.sleep(0.5)
            if any(e.event_type == 'end_json' for e in capture.events):
                break
        
        capture.assert_realtime_streaming()
        print(f"TC-05 PASSED: {len(capture.events)} events, {capture.get_time_span()*1000:.0f}ms span")
    
    @pytest.mark.asyncio
    async def test_tc06_reports_create_demo_reports(self, browser_page):
        """TC-06: /v2/reports/create_demo_reports streams events incrementally."""
        capture = SSEEventCapture()
        
        await browser_page.goto(f"{BASE_URL}/v2/reports?format=ui")
        await browser_page.wait_for_load_state('networkidle')
        
        capture.start()
        browser_page.on('console', lambda msg: capture.capture(msg))
        
        await browser_page.click('button:has-text("Create Demo")')
        
        for _ in range(120):
            await asyncio.sleep(0.5)
            if any(e.event_type == 'end_json' for e in capture.events):
                break
        
        capture.assert_realtime_streaming()
        print(f"TC-06 PASSED: {len(capture.events)} events, {capture.get_time_span()*1000:.0f}ms span")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
