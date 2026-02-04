# Session Failures

**Doc ID**: 2026-02-04_V2EndpointFixes-FAILS

## Active Failures

(none)

## Resolved Failures

### V2FX-FL-001: Missing bold formatting for running/stalled jobs in /v2/crawler [RESOLVED]

**Severity**: [MEDIUM]
**When**: 2026-02-04 13:34
**Where**: `src/routers_v2/crawler.py` - `renderJobRow()` function

**What happened**:
Implemented stalled job detection and Force Cancel button but missed the bold formatting requirement. Running and stalled jobs should display with bold text (font-weight: bold) to match /v2/jobs behavior.

**Evidence**:
Screenshot shows jb_14 with "running (stalled)" state but row text is not bold like other active jobs in /v2/jobs.

**Root cause**:
Focused on state text and button changes, overlooked the CSS styling requirement in the original request.

**Fix**:
Add `style="font-weight: bold"` to the `<tr>` element when job state is "running" or "stalled".

**Resolution**: Added `rowStyle` variable with `font-weight: bold` for running/stalled jobs. Verified with Playwright screenshot. Commit amended: 50dccfe

## Document History

**[2026-02-04 13:34]**
- Created with V2FX-FL-001: Missing bold formatting for running jobs
