# V2 Demo Router UI Specification

This document specifies the interactive UI for the `/v2/demorouter?format=ui` endpoint.

**Depends on:** `_V2_SPEC_ROUTERS.md` for endpoint design, streaming job infrastructure, and SSE format.

## Overview

A reactive web UI for managing demo items with CRUD operations and streaming job support. The UI displays an item table with inline actions and a resizable console panel for viewing streaming job output.

**Key Technologies:**
- HTMX for declarative HTTP interactions (included but minimally used)
- Native JavaScript for SSE streaming via `EventSource` and `fetch()` with `ReadableStream`
- CSS for styling (reuses `/static/css/styles.css` with inline additions)
- Modal dialogs for Create/Edit forms

## Scenario

**Problem:** Developers need a reference implementation demonstrating V2 router patterns including CRUD operations, streaming endpoints, and reactive UI components.

**Solution:** A fully functional demo router UI that:
- Lists all demo items with Create, Edit, Delete actions
- Provides bulk selection and bulk delete
- Runs streaming endpoints (selftest, create_demo_items) with console output
- Supports pause/resume control for active streaming jobs
- Shows toast notifications for action feedback

**What we don't want:**
- Complex state management libraries (use simple JavaScript)
- External dependencies beyond HTMX and standard browser APIs
- Polling-based updates (use SSE for streaming)

## Domain Object Model

**Demo Item** (as displayed in UI)
- `item_id` - Unique identifier (user-defined string)
- `name` - Display name (optional)
- `version` - Version number (optional integer)

**SSE Event Types** (for streaming endpoints)
- `start_json` - Job metadata at stream start (JSON with `job_id`)
- `log` - Log line (plain text)
- `end_json` - Job metadata at stream end (JSON with `result`)

**Connection State**
- `disconnected` - No active streaming connection
- `connecting` - Connection being established
- `connected` - Connection active, receiving events

**Pause State** (for active streaming job)
- `isPaused` - Boolean tracking if current job is paused
- `currentJobId` - ID of currently streaming job (null if none)

## User Actions

1. **View item list** - Page load: server returns HTML with pre-rendered table rows
2. **Reload items** - Click [Reload] to fetch items via JSON and re-render table
3. **Create item** - Click [Create] to open modal form, submit to create new item
4. **Edit item** - Click [Edit] on row to open modal form with current values, submit to update
5. **Delete item** - Click [Delete] on row with confirmation dialog
6. **Select items** - Click checkbox to select items for bulk operations
7. **Bulk delete** - Click [Delete (N)] to delete all selected items
8. **Run selftest** - Click [Run Selftest] to start streaming selftest in console
9. **Create demo items** - Click [Create Demo Items] to open modal with count/delay params, start streaming creation
10. **Pause job** - Click [Pause] in console header to pause current streaming job
11. **Resume job** - Click [Resume] in console header to resume paused job
12. **Clear console** - Click [Clear] to empty console output
13. **Close console** - Click [X] to hide console panel

## UX Design

```
Main Page: /v2/demorouter?format=ui
+-------------------------------------------------------------------------------------------+
| Demo Items (3)  [Reload]                                                                  |
| <- Back to Demo Router                                                                    |
|                                                                                           |
| [Create] [Create Demo Items] [Run Selftest] [Delete (0)]                                  |
|                                                                                           |
| +---+-------------+------------+---------+-------------------+                            |
| |[x]| ID          | Name       | Version | Actions           |                            |
| +---+-------------+------------+---------+-------------------+                            |
| |[ ]| demo_001    | Item One   | 1       | [Edit] [Delete]   |                            |
| |[ ]| demo_002    | Item Two   | 2       | [Edit] [Delete]   |                            |
| |[x]| demo_003    | Item Three | 1       | [Edit] [Delete]   |                            |
| +---+-------------+------------+---------+-------------------+                            |
|                                                                                           |
+-- [Resize Handle] ------------------------------------------------------------------------+
| Console Output (connected)                                            [Pause] [Clear] [X] |
|-------------------------------------------------------------------------------------------|
| ===== START: Job ID='jb_42'                                                               |
| Creating 10 demo items (batch ID='abc123', delay=300ms each)...                           |
| [ 1 / 10 ] Creating item 'demo_abc123_001'...                                             |
|   OK.                                                                                     |
| [ 2 / 10 ] Creating item 'demo_abc123_002'...                                             |
|                                                                                           |
+-------------------------------------------------------------------------------------------+

Toast Container (top-right, fixed position):
+-----------------------------------------------+
| Job Finished | jb_42                     [x]  |
+-----------------------------------------------+

Modal (Create Item):
+-----------------------------------------------+
|                                          [x]  |
| Create Demo Item                              |
|                                               |
| Item ID *                                     |
| [________________________]                    |
|                                               |
| Name                                          |
| [________________________]                    |
|                                               |
| Version                                       |
| [_1_______________________]                   |
|                                               |
|                      [Create] [Cancel]        |
+-----------------------------------------------+

Modal (Create Demo Items):
+-----------------------------------------------+
|                                          [x]  |
| Create Demo Items                             |
|                                               |
| Count (1-100)                                 |
| [_10______________________]                   |
|                                               |
| Delay per item (ms)                           |
| [_300_____________________]                   |
|                                               |
|                       [Start] [Cancel]        |
+-----------------------------------------------+
```

## Key Mechanisms and Design Decisions

### SSE Implementation: Dual Approach

The demorouter uses two SSE approaches depending on the use case:

**1. Native EventSource** - For monitoring existing jobs via `connectStream()`:
```javascript
function connectStream(url) {
  currentEventSource = new EventSource(url);
  currentEventSource.addEventListener('start_json', ...);
  currentEventSource.addEventListener('log', ...);
  currentEventSource.addEventListener('end_json', ...);
}
```

**2. Fetch with ReadableStream** - For POST/PUT endpoints via `streamRequestWithOptions()`:
```javascript
fetch(url, fetchOptions).then(response => {
  const reader = response.body.getReader();
  // Manual SSE parsing of event:/data: lines
});
```

### Console Panel Behavior

- Fixed position at bottom of viewport
- Resizable via drag handle (min: 45px, max: viewport height - 30px)
- Hidden by default, shown when streaming starts
- [X] button hides console (keeps content)
- [Clear] empties console output
- [Pause]/[Resume] button controls current streaming job
- Auto-scroll to bottom on new log lines
- Max 1,000,000 characters with truncation prefix

### Console Header Controls

```
[Pause] | [Clear] | [X]
```

- **[Pause]** - Disabled when no job running; toggles to [Resume] when paused
- **[Clear]** - Always enabled, clears console output
- **[X]** - Hides console panel

### Pause/Resume via Console

Unlike the jobs UI where pause/resume buttons are per-row, demorouter has a single Pause/Resume button in the console header that controls the currently streaming job:

```javascript
let currentJobId = null;
let isPaused = false;

async function togglePauseResume() {
  const action = isPaused ? 'resume' : 'pause';
  const response = await fetch(`/v2/jobs/control?job_id=${currentJobId}&action=${action}`);
  const result = await response.json();
  if (result.ok) {
    isPaused = !isPaused;
    showToast(isPaused ? 'Paused' : 'Resumed', currentJobId, 'info');
  } else {
    showToast('Control Failed', result.error, 'error');
  }
  updatePauseResumeButton();
}
```

### Console Output Formatting

JSON events are formatted as human-readable lines in the console:

```javascript
function handleSSEData(eventType, data) {
  if (eventType === 'log') {
    appendToConsole(data);
  } else if (eventType === 'start_json') {
    const json = JSON.parse(data);
    currentJobId = json.job_id;
    appendToConsole("===== START: Job ID='" + json.job_id + "'");
  } else if (eventType === 'end_json') {
    const json = JSON.parse(data);
    const status = json.result?.ok ? 'OK' : 'FAIL';
    appendToConsole("===== END: Job ID='" + json.job_id + "' Result='" + status + "'");
  }
}
```

### Modal Dialog Pattern

Single modal element reused for all forms:

```html
<div id="modal" class="modal-overlay">
  <div class="modal-content">
    <button class="modal-close" onclick="closeModal()">&times;</button>
    <div class="modal-body"><!-- Content injected by JavaScript --></div>
  </div>
</div>
```

**Functions:**
- `openModal()` - Shows modal, adds ESC key listener
- `closeModal()` - Hides modal, removes ESC key listener
- `showCreateForm()` - Injects create form HTML
- `showUpdateForm(itemId)` - Fetches item data, injects edit form HTML
- `showCreateDemoItemsForm()` - Injects streaming config form HTML

### Form Validation

Inline validation errors shown below fields:

```javascript
function showFieldError(input, message) {
  const error = document.createElement('div');
  error.className = 'form-error';
  error.textContent = message;
  input.parentElement.appendChild(error);
}
```

### Toast Notifications

```javascript
function showToast(title, message, type = 'info', autoDismiss = 5000) {
  const toast = document.createElement('div');
  toast.className = 'toast toast-' + type;
  toast.innerHTML = '...';
  container.appendChild(toast);
  if (autoDismiss > 0) setTimeout(() => toast.remove(), autoDismiss);
}
```

**Types:** `info` (blue), `success` (green), `error` (red), `warning` (yellow)

**Security:** Uses `escapeHtml()` for all user-provided content.

### Bulk Delete

Single summary toast instead of per-item toasts:

```javascript
async function bulkDelete() {
  let deleted = 0, failed = 0;
  for (const itemId of itemIds) {
    const result = await fetch(...).then(r => r.json());
    if (result.ok) { deleted++; row.remove(); }
    else { failed++; }
  }
  if (failed === 0) {
    showToast('Bulk Delete', deleted + ' items deleted', 'success');
  } else {
    showToast('Bulk Delete', deleted + ' deleted, ' + failed + ' failed', 'warning');
  }
}
```

### Declarative Data Attributes

Buttons use `data-*` attributes for endpoint configuration:

```html
<button data-url="/v2/demorouter/delete?item_id={itemId}" 
        data-method="DELETE" 
        data-format="json"
        onclick="callItemEndpoint(this, 'demo_001')">Delete</button>
```

- `data-url` - Endpoint URL with `{itemId}` placeholder
- `data-method` - HTTP method (GET, POST, PUT, DELETE)
- `data-format` - Response format (json, stream)
- `data-reload-on-finish` - If true, reload items after stream completes

### Reload on Stream Finish

Streaming operations can trigger item list reload on completion:

```javascript
function streamRequestWithOptions(url, options = {}) {
  const reloadOnFinish = options.reloadOnFinish !== false;
  // ... on stream complete:
  if (reloadOnFinish) reloadItems();
}
```

### Item Row Rendering

Server-side initial render, client-side re-render on reload:

```javascript
function renderItemRow(item) {
  return `<tr id="item-${item.item_id}">
    <td><input type="checkbox" class="item-checkbox" data-item-id="${item.item_id}"></td>
    <td>${item.item_id}</td>
    <td>${item.name || '-'}</td>
    <td>${item.version || '-'}</td>
    <td class="actions">
      <button onclick="showUpdateForm('${item.item_id}')">Edit</button>
      <button onclick="callItemEndpoint(this, '${item.item_id}')">Delete</button>
    </td>
  </tr>`;
}
```

### Empty State

When no items exist:
```html
<tr><td colspan="5" class="empty-state">No demo items found</td></tr>
```

## Action Flow

### Create Item
```
User clicks [Create]
  |-> showCreateForm() injects form HTML into modal
  |-> openModal() shows modal
  |-> User fills form, clicks [Create]
  |-> submitCreateForm() validates, extracts data
  |-> callEndpoint() sends POST to /demorouter/create
  |-> On success: showToast('OK'), reloadItems()
  |-> On error: showToast('Failed', error)
```

### Edit Item (with rename support)
```
User clicks [Edit] on row (item_id = demo_001)
  |-> showUpdateForm('demo_001') fetches item data
  |-> Modal shows with current values
  |-> User modifies fields, clicks [Save]
  |-> submitUpdateForm() checks if item_id changed
      |-> If changed: includes item_id in body (triggers rename per DD-E014)
      |-> If same: omits item_id from body
  |-> callItemEndpoint() sends PUT to /demorouter/update?item_id=demo_001
  |-> On success: showToast('Updated'), reloadItems()
```

### Run Streaming Endpoint
```
User clicks [Run Selftest]
  |-> clearConsole()
  |-> connectStream('/demorouter/selftest?format=stream')
  |-> EventSource receives start_json
      |-> Set currentJobId, enable Pause button
      |-> Append "===== START..." to console
  |-> EventSource receives log events
      |-> Append each line to console
  |-> EventSource receives end_json
      |-> Append "===== END..." to console
      |-> showToast('Job finished')
      |-> Reset currentJobId, disable Pause button
```

### Pause/Resume Job
```
User clicks [Pause] in console header
  |-> togglePauseResume() sends GET /v2/jobs/control?job_id=jb_42&action=pause
  |-> On success: isPaused = true, button text changes to [Resume]
  |-> On error: showToast('Control Failed', error)
```

## Data Structures

### HTML Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Demo Items</title>
  <link rel="stylesheet" href="/static/css/styles.css">
  <script src="/static/js/htmx.js"></script>
  <style>/* Toast, Modal, Console, Form styles */</style>
</head>
<body>
  <div id="toast-container"></div>
  
  <div id="modal" class="modal-overlay">
    <div class="modal-content">
      <button class="modal-close">&times;</button>
      <div class="modal-body"></div>
    </div>
  </div>
  
  <div class="container">
    <h1>Demo Items (<span id="item-count">3</span>)</h1> [Reload]
    <div class="toolbar">[Create] [Create Demo Items] [Run Selftest] [Delete (0)]</div>
    <table>
      <thead><tr><th></th><th>ID</th><th>Name</th><th>Version</th><th>Actions</th></tr></thead>
      <tbody id="items-tbody"><!-- Item rows --></tbody>
    </table>
  </div>
  
  <div id="console-panel" class="console-panel">
    <div class="console-resize-handle"></div>
    <div class="console-header">
      <span id="console-title">Console Output</span>
      <span id="console-status">(disconnected)</span>
      <div class="console-controls">
        <button id="btn-pause-resume" disabled>Pause</button>
        <button onclick="clearConsole()">Clear</button>
        <button onclick="hideConsole()">&times;</button>
      </div>
    </div>
    <pre id="console-output" class="console-output"></pre>
  </div>
  
  <script>/* JavaScript functions */</script>
</body>
</html>
```

### CSS Classes

All V2 UI component styles are defined in `/static/css/styles.css` under the "V2 UI Components" section:

- **Toast notifications:** `#toast-container`, `.toast`, `.toast-info`, `.toast-success`, `.toast-error`, `.toast-warning`
- **Modal overlay:** `.modal-overlay`, `.modal-overlay.visible`, `.modal-content`, `.modal-close`
- **Console panel:** `.console-panel`, `.console-panel.hidden`, `.console-resize-handle`, `.console-header`, `.console-output`
- **Form elements:** `.form-error`, `.empty-state`
- **Body margin:** `body.has-console` (adds margin-bottom when console is visible)

## Differences from Jobs UI

| Aspect | Jobs UI | Demorouter UI |
|--------|---------|---------------|
| SSE Method | HTMX SSE extension | Native EventSource / fetch |
| Pause/Resume | Per-row buttons | Console header button |
| Console Close | [Disconnect] | [X] (hide) |
| JSON Events | Hidden from console | Formatted as readable lines |
| Bulk Toast | Per-item toasts | Single summary toast |
| Data Source | Fetch on DOMContentLoaded | Server-rendered initial |
| Item Actions | View, Monitor, Pause, Cancel | Edit, Delete |
