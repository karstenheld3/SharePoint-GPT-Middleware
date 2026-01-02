# V2 Crawler UI Specification

**Goal**: Provide monitoring and control UI for running crawler jobs
**Target file**: `/src/routers_v2/crawler.py`

**Depends on:**
- `_V2_SPEC_ROUTERS.md` for endpoint design, streaming job infrastructure, and SSE format
- `_V2_SPEC_COMMON_UI_FUNCTIONS.md` for UI generation functions
- `_V2_SPEC_CRAWLER.md` for crawler domain objects and actions

**Does not depend on:**
- `_V2_SPEC_CRAWLER_RESULTS_UI.md` (separate router)

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
- No toolbar buttons (crawl initiated from domains UI)

## Scenario

**Real-world problem:**
Users need to monitor crawler progress, view real-time output, and control running jobs (pause/resume/cancel).

**What we don't want:**
- Ability to start crawls from this UI (that's in domains UI)
- Complex filtering or search
- Showing non-crawler jobs

## User Actions

| Action | Trigger | Effect |
|--------|---------|--------|
| Result | Click [Result] button | Show job result in modal dialog |
| Monitor | Click [Monitor] button | Stream live output to console panel |
| Pause | Click [Pause] button | Pause running job, button changes to [Resume] |
| Resume | Click [Resume] button | Resume paused job, button changes to [Pause] |
| Cancel | Click [Cancel] button | Stop job permanently |
| Refresh | Click [Refresh] link | Reload jobs table |

## UX Design

### Main Layout

```
+---------------------------------------------------------------------------------------------------------------------+
| Running Crawler Jobs (2) [Refresh]                                                                                  |
|                                                                                                                     |
| Back to Main Page | Domains | Crawl Results                                                                         |
|                                                                                                                     |
| +---+-------------+-----------+-----------------+-------------+--------+-----------+--------------------------------+
| |ID | Action      | Domain ID | Vector Store ID | Mode        | Scope  | Source ID | Actions                        |
| +---+-------------+-----------+-----------------+-------------+--------+-----------+--------------------------------+
| |42 | crawl       | domain_01 | vs_abc123       | full        | all    | -         | [Monitor] [Pause] [Cancel]     |
| |41 | embed_data  | domain_02 | vs_def456       | incremental | all    | -         | [Monitor] [Resume] [Cancel]    |
| +---+-------------+-----------+-----------------+-------------+--------+-----------+--------------------------------+
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

| Column | Source | Notes |
|--------|--------|-------|
| ID | `job.id` | Job ID |
| Action | `job.endpoint` | `crawl`, `download_data`, `process_data`, `embed_data` |
| Domain ID | `job.metadata.domain_id` | From job metadata |
| Vector Store ID | `job.metadata.vector_store_id` | From job metadata |
| Mode | `job.metadata.mode` | `full` or `incremental` |
| Scope | `job.metadata.scope` | `all` or `source` |
| Source ID | `job.metadata.source_id` | Source ID or `-` if scope=all |
| Actions | - | Context-sensitive buttons |

### Action Buttons

| State | Available Actions |
|-------|-------------------|
| `running` | [Monitor] [Pause] [Cancel] |
| `paused` | [Monitor] [Resume] [Cancel] |
| `completed` | [Result] [Monitor] |
| `cancelled` | [Result] [Monitor] |

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

### Navigation Links

- **Back to Main Page** - `/` root endpoint
- **Domains** - `/v2/domains?format=ui`
- **Crawl Results** - `/v2/crawl-results?format=ui`

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
- `runSelftest()` - start crawler selftest

Most functionality reuses common UI functions.
