# FAILS: Reports View Session

Lessons learned from failures during this session.

## RPTV-FL-001: Report Viewer not responsive, doesn't use full viewport

- **Severity**: [MEDIUM]
- **When**: 2026-02-04 08:46
- **Where**: `src/routers_v2/reports.py` - `get_report_view_css()`
- **What**: Report viewer UI doesn't fill full width/height. Table panel shows only partial content, large empty space below.
- **Evidence**: Screenshot shows table with only 3 visible rows, significant unused vertical space
- **Root cause**: CSS `height: calc(100vh - 140px)` on `.viewer-container` may not account for actual header heights. Table doesn't expand to fill available space.
- **Suggested fix**: 
  - Ensure `html, body` have `height: 100%`
  - Use flexbox properly on body to fill viewport
  - Table container needs `width: 100%` on table element
- **Status**: Resolved (2026-02-04 08:48)

## Document History

**[2026-02-04 08:46]**
- Added RPTV-FL-001: Layout not responsive
