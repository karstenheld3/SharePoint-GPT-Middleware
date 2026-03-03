# Review: SSE Streaming Harmonization Plan

**Reviewed**: 2026-03-03 09:55
**Document**: `_IMPL_SSE_STREAMING_HARMONIZATION.md` [STRM-IP01]
**Question**: Will this solve the problem of 1 implementation pattern across the app?

## Summary

**Answer**: Yes, with minor enhancements.

The `stream_with_flush()` wrapper pattern is a sound solution that balances pragmatism with correctness. It addresses the root cause identified in SITE-FL-002 and SCAN-FL-005.

## Findings

### STRM-RV-01: Mechanism explanation imprecise (LOW)

**Issue**: Document states `asyncio.sleep(0)` "forces event loop flush" - this is imprecise.

**Reality**: `asyncio.sleep(0)` yields control to event loop, allowing pending I/O (including HTTP chunk sending) to be processed. It doesn't directly "flush".

**Impact**: Documentation clarity only, fix works correctly.

**Recommendation**: Update explanation in IMPL to be more precise.

### STRM-RV-02: No double-wrap protection (MEDIUM)

**Issue**: If developer accidentally wraps generator twice, no protection exists.

**Code example**:
```python
# Accidental double-wrap
return StreamingResponse(stream_with_flush(stream_with_flush(gen())), ...)
```

**Impact**: Events would be yielded correctly but with unnecessary overhead.

**Recommendation**: Add guard to `stream_with_flush()`:
```python
async def stream_with_flush(generator):
  # Could add marker attribute to detect double-wrap
  async for event in generator:
    yield event
    await asyncio.sleep(0)
```

### STRM-RV-03: No enforcement for future endpoints (MEDIUM)

**Issue**: New developers creating streaming endpoints may not know to use the wrapper.

**Impact**: Future endpoints could have same buffering bug.

**Recommendations**:
1. Add prominent docstring in `common_job_functions_v2.py`
2. Add comment in each router's imports section
3. Consider adding to NOTES.md or project README

### STRM-RV-04: Alternative approaches not evaluated (INFO)

**Alternatives considered but not documented**:

- **Thread pool executor**: Run blocking I/O in executor instead of wrapper
  - More invasive, requires changing all SharePoint SDK calls
  - Would be "correct" async but high refactoring cost

- **sse-starlette library**: Purpose-built SSE support
  - New dependency
  - Different API, requires endpoint refactoring

- **Middleware approach**: Auto-wrap all StreamingResponse
  - Hides behavior, harder to debug
  - May conflict with non-SSE streaming (file downloads)

**Verdict**: Wrapper pattern is pragmatic middle ground.

## Questions That Need Answers

1. Should we add a linter rule or grep check to CI to catch missing wrappers?
2. Should `stream_with_flush` be the default export, making raw `StreamingResponse` harder to accidentally use?

## Conclusion

The proposed solution **will work** and **will achieve the goal** of one consistent pattern. The risks identified are minor and manageable.

**Proceed with implementation**, optionally incorporating:
- [ ] Enhanced docstring for discoverability
- [ ] Double-wrap protection (optional, low priority)
- [ ] Add to project onboarding docs

## Document History

**[2026-03-03 09:55]**
- Initial review created
