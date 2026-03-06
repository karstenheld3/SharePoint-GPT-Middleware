# SPEC: V2 Crawler UI

**Doc ID**: V2CR-SP02
**Goal**: Provide monitoring and control UI for running crawler jobs
**Target file**: `/src/routers_v2/crawler.py`

**Depends on:**
- `_V2_SPEC_ROUTERS.md` for endpoint design, streaming job infrastructure, and SSE format
- `_V2_SPEC_COMMON_UI_FUNCTIONS.md` for UI generation functions
- `_V2_SPEC_CRAWLER.md` for crawler domain objects and actions

**Does not depend on:**
- `_V2_SPEC_CRAWLER_RESULTS_UI.md` (separate router)

## MUST-NOT-FORGET

- Filters to crawler jobs only (not all streaming jobs)
- Same UI pattern as demorouter (console visible by default)
- Uses common UI functions from `common_ui_functions_v2.py`
- Selftest dialog has phase selection and skip_cleanup options
- Bulk delete requires confirmation dialog

## Table of Contents

1. Overview
2. Scenario
3. User Actions
4. UX Design
5. Domain Objects
6. Key Mechanisms
7. Action Flow

## Overview

The `/v2/crawler` router provides a monitoring interface for running crawler jobs. Crawl operations are initiated from the domains UI; this UI focuses on job visibility and control.

**Key characteristics:**
- Single-page UI with jobs table and console panel
- Same UI pattern as demorouter (console visible by default)
- Filters to crawler jobs only (not all streaming jobs)
- [Run Selftest] toolbar button opens options dialog

## Scenario

**Real-world problem:**
Users need to monitor crawler progress, view real-time output, and control running jobs (pause/resume/cancel).

**What we don't want:**
- Complex filtering or search
- Showing non-crawler jobs

## User Actions

- **Run Selftest**: Click [Run Selftest] button -> Open selftest options dialog
- **Delete Selected**: Click [Delete (N)] button -> Delete all checked jobs (with confirmation)
- **View**: Click [View] button -> Open report in Report Viewer (only for jobs with report_id)
- **Result**: Click [Result] button -> Show job result in modal dialog
- **Monitor**: Click [Monitor] button -> Stream live output to console panel
- **Pause**: Click [Pause] button -> Pause running job, button changes to [Resume]
- **Resume**: Click [Resume] button -> Resume paused job, button changes to [Pause]
- **Cancel**: Click [Cancel] button -> Stop job permanently
- **Delete**: Click [Delete] button -> Delete individual job (with confirmation)
- **Refresh**: Click [Refresh] link -> Reload jobs table

## UX Design

### Main Layout

```
+---------------------------------------------------------------------------------------------------------------------+
| Crawler Jobs (2) [Refresh]                                                                                          |
|                                                                                                                     |
| Back to Main Page | Domains | Crawler | Jobs | Reports                                                              |
|                                                                                                                     |
| [Delete (0)] [Run Selftest]                                                                                         |
|                                                                                                                     |
| +---+----+-------------+-----------+--------+--------+---------+---------------------------------------------+      |
| |[x]| ID | Endpoint    | Domain ID | State  | Result | Started | Actions                                     |      |
| +---+----+-------------+-----------+--------+--------+---------+---------------------------------------------+      |
| |[ ]| 42 | crawl       | domain_01 | running| -      | ...     | [Monitor] [Pause] [Cancel] [Delete]         |      |
| |[ ]| 41 | embed_data  | domain_02 | paused | -      | ...     | [Monitor] [Resume] [Cancel] [Delete]        |      |
| |[ ]| 40 | crawl       | domain_01 | done   | OK     | ...     | [View] [Result] [Monitor] [Delete]          |      |
| +---+----+-------------+-----------+--------+--------+---------+---------------------------------------------+      |
|                                                                                                                     |
| +-------------------------------------------------------------------------------------------------------------------+
| | [Resize Handle - Draggable]                                                                                       |
| | Console Output (connected) http://...monitor?job_id=jb_42&format=stream          [Pause] [Cancel] [Clear]     [X] |
| | ----------------------------------------------------------------------------------------------------------------- |
| | [ 1 / 20 ] Downloading 'document_001.pdf'...                                                                      |
| |   OK.                                                                                                             |
| | [ 2 / 20 ] Downloading 'document_002.pdf'...                                                                      |
| +-------------------------------------------------------------------------------------------------------------------+
|                                                                                                                     |
+---------------------------------------------------------------------------------------------------------------------+
```

### Table Columns

- **(checkbox)**: Selection checkbox for bulk operations
- **Job ID**: `job.job_id` - Job identifier
- **Endpoint**: `job.source_url` - Parsed from source URL: `crawl`, `selftest`, etc.
- **Domain ID**: `job.source_url` - Parsed from `domain_id` query param
- **State**: `job.state` - `running`, `paused`, `completed`, `cancelled`
- **Result**: `job.result.ok` - `OK`, `FAIL`, or `-`
- **Started**: `job.started_utc` - Formatted timestamp
- **Finished**: `job.finished_utc` - Formatted timestamp or `-`
- **Actions**: Context-sensitive buttons

### Action Buttons by State

- **running**: [Monitor] [Pause] [Cancel] [Delete]
- **paused**: [Monitor] [Resume] [Cancel] [Delete]
- **completed**: [View]* [Result] [Monitor] [Delete]
- **cancelled**: [View]* [Result] [Monitor] [Delete]

*[View] only appears when job.result.data.report_id exists (crawl jobs create reports)

### Result Modal Dialog

When user clicks [Result] on a completed/cancelled job, fetch result from `/v2/jobs/results?job_id={jobId}&format=json` and display in modal:

```
+------------------------------------------+
|  Job Result                         [x]  |
+------------------------------------------+
|  Job ID: jb_42                           |
|  Status: OK / FAIL                       |
|                                          |
|  Result Data:                            |
|  {                                       |
|    "tests_run": 25,                      |
|    "ok": 20,                             |
|    "fail": 3,                            |
|    "skip": 2                             |
|  }                                       |
|                                          |
|                              [Close]     |
+------------------------------------------+
```

Implementation uses `showResultModal()` from `common_ui_functions_v2.py`:

```javascript
async function showJobResult(jobId) {
  try {
    const response = await fetch('/v2/jobs/results?job_id=' + jobId + '&format=json');
    const result = await response.json();
    if (result.ok) {
      showResultModal(result.data);
    } else {
      showToast('Error', result.error, 'error');
    }
  } catch (e) {
    showToast('Error', e.message, 'error');
  }
}
```

### Selftest Options Dialog

When user clicks [Run Selftest], open modal with phase selection and skip_cleanup option:

```
+----------------------------------------------------------+
|  Selftest Options                                   [x]  |
+----------------------------------------------------------+
|                                                          |
|  Run up to phase *                                       |
|  [Phase 19: Cleanup                              v]      |
|  Phases are cumulative - selecting phase N runs 1..N     |
|                                                          |
|  [ ] Skip cleanup (keep test artifacts after completion) |
|                                                          |
|  Endpoint Preview:                                       |
|  /v2/crawler/selftest?format=stream                      |
|                                                          |
+----------------------------------------------------------+
|                                       [OK] [Cancel]      |
+----------------------------------------------------------+
```

**Phase dropdown options:**
- Phase 1: Pre-flight Validation
- Phase 2: Pre-cleanup
- Phase 3: SharePoint Setup
- Phase 4: Domain Setup
- Phase 5: Error Cases (I1-I4)
- Phase 6: Full Crawl Tests (A1-A4)
- Phase 7: source_id Filter Tests (B1-B5)
- Phase 8: dry_run Tests (D1-D4)
- Phase 9: Individual Steps Tests (E1-E3)
- Phase 10: SharePoint Mutations
- Phase 11: Incremental Tests (F1-F4)
- Phase 12: Incremental source_id Tests (G1-G2)
- Phase 13: Job Control Tests (H1-H2)
- Phase 14: Integrity Check Tests (J1-J4)
- Phase 15: Advanced Edge Cases (K1-K4)
- Phase 16: Metadata & Reports Tests (L1-L3)
- Phase 17: Map File Structure Tests (O1-O3)
- Phase 18: Empty State Tests (N1-N4)
- Phase 19: Cleanup (default)

**Endpoint preview** updates dynamically as options change.

**On OK**: Close modal, show toast, connect stream with `showResult: 'modal'` to display results after completion.

### Navigation Links

- **Back to Main Page** - `/` root endpoint
- **Domains** - `/v2/domains?format=ui`
- **Crawler** - `/v2/crawler?format=ui`
- **Jobs** - `/v2/jobs?format=ui`
- **Reports** - `/v2/reports?format=ui`

## Domain Objects

### Crawler Job (filtered view)

Jobs are filtered by `router == 'crawler'`. Standard job fields plus crawler-specific metadata:

```
CrawlerJob:
  id: string                    # Job ID (e.g., "42")
  router: "crawler"             # Always "crawler" for this UI
  endpoint: string              # "crawl", "download_data", "process_data", "embed_data"
  state: string                 # "running", "paused", "done", "cancelled", "error"
  started: string               # ISO timestamp
  finished: string | null       # ISO timestamp or null if running
  metadata:
    domain_id: string           # Domain being crawled
    vector_store_id: string     # Target vector store
    mode: string                # "full" or "incremental"
    scope: string               # "all" or "source"
    source_id: string | null    # Source ID if scope="source"
```

## Key Mechanisms

### Job Filtering

The UI only displays jobs where `router == 'crawler'`. This is applied when listing jobs.

### Console Panel

Same behavior as demorouter UI:
- Visible by default
- Resizable via drag handle
- [Clear] button clears console content
- SSE streaming for live output
- Auto-scroll to bottom on new content

### Job State Polling

Jobs table refreshes via:
- Manual [Refresh] click
- After job control action (pause/resume/cancel)
- SSE `done` event from monitored job

### Monitor Action

1. User clicks [Monitor] on a job row
2. Console panel clears and connects to SSE endpoint
3. Live output streams to console
4. On `done` event, jobs table refreshes

### Pause/Resume/Cancel Actions

1. User clicks action button
2. POST to job control endpoint
3. Toast confirms action
4. Jobs table refreshes to show new state

## Action Flow

### Monitor Job

```
User clicks [Monitor]
  -> clearConsole()
  -> startSSE(`/v2/jobs/${jobId}/monitor?format=stream`)
  -> SSE events append to console
  -> On 'done' event: refreshJobsTable()
```

### Pause Job

```
User clicks [Pause]
  -> POST /v2/jobs/${jobId}/control?action=pause
  -> showToast("Job paused", "info")
  -> refreshJobsTable()
```

### Resume Job

```
User clicks [Resume]
  -> POST /v2/jobs/${jobId}/control?action=resume
  -> showToast("Job resumed", "info")
  -> refreshJobsTable()
```

### Cancel Job

```
User clicks [Cancel]
  -> POST /v2/jobs/${jobId}/control?action=cancel
  -> showToast("Job cancelled", "info")
  -> refreshJobsTable()
```

## Implementation Notes

### Endpoint

```
GET /v2/crawler?format=ui    -> HTML page with jobs table + console
GET /v2/crawler?format=json  -> JSON list of crawler jobs
```

### Dependencies

- `common_ui_functions_v2.py` for page generation, table, console, SSE
- `common_job_functions_v2.py` for job listing and filtering
- `/v2/jobs` endpoints for job control and monitoring

### Router-Specific JavaScript

Minimal JS needed:
- `refreshJobsTable()` - fetch and re-render jobs
- `monitorJob(jobId)` - connect SSE to console
- `controlJob(jobId, action)` - pause/resume/cancel
- `showJobResult(jobId)` - fetch result and show in modal
- `showSelftestDialog()` - open selftest options modal
- `updateSelftestEndpointPreview()` - update endpoint preview on option change
- `startSelftest(event)` - run selftest with selected options
- `deleteJob(jobId)` - delete individual job
- `bulkDelete()` - delete all selected jobs
- `updateSelectedCount()` - update selection count and button state
- `toggleSelectAll()` - toggle all checkboxes
- `getSelectedJobIds()` - get array of selected job IDs

Most functionality reuses common UI functions.

## Document History

**[2026-02-04 08:01]**
- Changed: Title to `# SPEC: V2 Crawler UI` per template
- Added: Doc ID `V2CR-SP02`
- Added: MUST-NOT-FORGET section with 5 critical rules
- Changed: Section name from "Spec Changes" to "Document History"

**[2026-01-03]**
- Fixed: Table Columns section to match implementation
- Added: Delete functionality (bulk + individual), checkbox column
- Added: Selftest Options Dialog with phase selection and skip_cleanup
- Added: [Run Selftest] toolbar button, updated navigation links
