# V2 Common UI Functions Specification

## Overview

This specification defines a reusable UI library for V2 routers, following the pattern established by V1's `common_ui_functions.py` but extended to support the richer feature set demonstrated in `demorouter1.py` (the self-contained version).

**Goal**: Enable any V2 router to provide a full-featured interactive UI with minimal boilerplate code by calling shared Python functions that generate consistent HTML/JavaScript.

**Target file**: `/src/routers_v2/common_ui_functions_v2.py`
**Styles file**: `/static/css/routers_v2.css` (already exists, to be extended)

---

### Functional Requirements

**UI-FR-01: Toast Notifications**
- Support info, success, error, warning message types
- Auto-dismiss configurable per toast (default 5000ms)
- Manual close via X button
- Stack multiple toasts vertically (new toasts appear at bottom)

**UI-FR-02: Modal Dialogs**
- Overlay with centered content panel
- Close on Escape key or X button
- ENTER key submits form (use `type="submit"` on OK button with `form="formId"`, `onsubmit` on form)
- Auto-focus first visible input field when modal opens
- Width configurable per modal instance (default 900px, `openModal(width)` or `setModalWidth(width)`)
- Internal structure: `.modal-header` (fixed title), `.modal-scroll` (scrollable form), `.modal-footer` (fixed buttons)
- Only `.modal-scroll` area scrolls when content exceeds max-height; title and buttons remain fixed

**UI-FR-03: Console Panel**
- Fixed position at bottom of viewport
- Always included in UI pages (body has `has-console` class)
- Initial visibility configurable via `console_initially_hidden` parameter
- Auto-shows when streaming starts (calls `showConsole()`)
- Resizable via drag handle (min 45px, max viewport-30px)
- SSE streaming output with auto-scroll
- Status indicator: connecting, connected, disconnected
- Truncation at 1,000,000 chars with "[truncated]" prefix
- Module-level state: `currentStreamUrl`, `currentJobId`, `isPaused`, `MAX_CONSOLE_CHARS`

**UI-FR-04: SSE Streaming**
- Connect to stream endpoints via fetch API
- Handle event types: start_json, log, end_json
- Parse job_id from start_json for control operations
- Show result in modal or toast on stream end
- `connectStream(url, options)` options:
  - `method`: HTTP method (GET/POST/PUT/DELETE, default GET)
  - `bodyData`: JSON body for POST/PUT requests
  - `clearConsole`: Clear console before connecting (default true)
  - `reloadOnFinish`: Reload table after stream ends (default true)
  - `showResult`: Where to display result ('toast' | 'modal' | 'none', default 'toast')

**UI-FR-05: Job Control**
- Pause/Resume button during active stream
- Button state reflects job state (disabled when no active job)
- Integrate with `/v2/jobs/control` endpoint

**UI-FR-06: Data Tables**
- Column headers with optional select-all checkbox
- Data rows with row ID attribute for targeting
- Dynamic item count in header
- Empty state message when no items

**UI-FR-07: Bulk Operations**
- Select-all checkbox toggles all row checkboxes
- Selected count display updates on change
- Bulk delete button enabled only when items selected

**UI-FR-08: Form Validation**
- Inline field error messages below input
- Clear error on field correction
- `showFieldError(input, message)` and `clearFieldError(input)` functions

**UI-FR-09: Result Display**
- Configurable per action: show in modal or toast
- Modal shows formatted JSON with OK/FAIL status
- Toast shows brief success/error message

**UI-FR-10: Confirm Dialogs**
- `confirm()` prompt before destructive actions (delete)
- Handled inline in onclick: `if(confirm('message')) callEndpoint(this, itemId)`
- NOT a data-* attribute; part of onclick handler

**UI-FR-11: Page Initialization**
- `DOMContentLoaded` handler initializes console resize
- All event listeners attached after DOM ready

**UI-FR-12: Reload Button**
- Inline reload button next to page title
- Calls `reloadItems()` to refresh table data

### Implementation Guarantees

**UI-IG-01:** All routers use same CSS classes from `routers_v2.css`
**UI-IG-02:** Same JavaScript functions for same interactions across all routers
**UI-IG-03:** Same HTML structure for same components
**UI-IG-04:** z-index hierarchy: Toast (10001) > Modal (1100) > Console (900) > Content (default)
**UI-IG-05:** Create/Update forms are NOT generalized; only styles shared
**UI-IG-06:** Routers can add inline styles for one-off customization
**UI-IG-07:** Column and button configuration is declarative (like V1)
**UI-IG-08:** Router provides its own endpoint URLs via configuration
**UI-IG-09:** Functions support format=json, format=html, format=ui
**UI-IG-10:** Generated HTML works with HTMX where applicable
**UI-IG-11:** If `enable_bulk_delete=True`, `delete_endpoint` must be provided
**UI-IG-12:** If any button has `reloadOnFinish=true`, `list_endpoint` must be provided

---

## Architecture and Design

### UI design decisions

**DD-UI-01:** Server-rendered initial data. The `generate_ui_page()` function requires `items` parameter - server already has data at render time, avoids blank table -> AJAX flash.
**DD-UI-02:** Single rendering logic. Python generates initial rows using column config, JS `renderItemRow()` uses same config for client-side updates.
**DD-UI-03:** Declarative button configuration. Buttons use `data-*` attributes for endpoint URL, method, format, result handling - no custom JS per action.
**DD-UI-04:** Unified endpoint caller. Single `callEndpoint()` function handles all button clicks, routes to `fetch()` or `connectStream()` based on `data-format`.
**DD-UI-05:** Console always included. No `enable_console` toggle - prevents broken state when streaming buttons exist but console HTML is missing.
**DD-UI-06:** Placeholder standardization. Use `{itemId}` (camelCase) for item IDs in URLs, `{router_prefix}` for API prefix.
**DD-UI-07:** Confirm via inline onclick. Destructive actions use `if(confirm('msg')) callEndpoint(...)` pattern, not a data-* attribute.
**DD-UI-08:** Modal button order. OK / Cancel (Windows/Android convention) - primary action first in left-to-right reading flow.
**DD-UI-09:** Toast stacking. New toasts appear at bottom of container.
**DD-UI-10:** Forms are router-specific. Create/Update forms not generalized - only styles shared. Routers provide via `additional_js`.
**DD-UI-11:** Single active stream. Only one streaming job at a time per page - `currentJobId` is overwritten if new stream starts. Intentional simplification.
**DD-UI-12:** XSS prevention. All user data in `renderItemRow()` must be escaped via `escapeHtml()` before inserting into HTML.
**DD-UI-13:** Row ID sanitization. Row IDs derived from `row_id_field` must be sanitized (alphanumeric + underscore only) to prevent broken `id` attributes.
**DD-UI-14:** Router-level navigation. Each router defines navigation constant (e.g., `main_page_nav_html`) as raw HTML string, passed to `generate_ui_page(navigation_html=...)`. Keeps navigation logic in router, not UI library.

---

## Artifacts and Components

### Component Inventory

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Page Shell                                                                 │
│  ├─ Toast Container (#toast-container)                                      │
│  ├─ Modal Overlay (#modal > .modal-content > .modal-body)                   │
│  │   ├─ Modal Header (.modal-header > h3)                                   │
│  │   ├─ Modal Scroll (.modal-scroll) - scrollable form content              │
│  │   └─ Modal Footer (.modal-footer) - fixed OK/Cancel buttons              │
│  ├─ Main Content (.container)                                               │
│  │   ├─ Page Header (h1 + reload button)                                    │
│  │   ├─ Back Link                                                           │
│  │   ├─ Toolbar (.toolbar)                                                  │
│  │   │   ├─ Primary buttons (.btn-primary)                                  │
│  │   │   └─ Delete selected button (#btn-delete-selected)                   │
│  │   └─ Data Table (table > thead + tbody)                                  │
│  │       ├─ Select-all checkbox (#select-all)                               │
│  │       ├─ Column headers (th)                                             │
│  │       └─ Data rows (tr#item-{id})                                        │
│  │           ├─ Checkbox (.item-checkbox)                                   │
│  │           ├─ Data cells (td)                                             │
│  │           └─ Actions cell (td.actions)                                   │
│  └─ Console Panel (#console-panel)                                          │
│      ├─ Resize Handle (#console-resize-handle)                              │
│      ├─ Console Header (.console-header)                                    │
│      │   ├─ Title + Status (#console-title, #console-status)                │
│      │   └─ Controls (.console-controls)                                    │
│      │       ├─ Pause/Resume (#btn-pause-resume)                            │
│      │       ├─ Clear button                                                │
│      │       └─ Close button (.console-close)                               │
│      └─ Console Output (#console-output)                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CSS Classes (routers_v2.css)

**Existing styles** (keep as-is):
- Toast: `#toast-container`, `.toast`, `.toast-info/success/error/warning`, `.toast-content`, `.toast-title`, `.toast-close`, `@keyframes toast-slide-in`
- Modal: `.modal-overlay`, `.modal-overlay.visible`, `.modal-content`, `.modal-close`, `.modal-body`, `.modal-header`, `.modal-scroll`, `.modal-footer`
- Console: `.console-panel`, `.console-panel.hidden`, `.console-resize-handle`, `.console-resize-handle.dragging`, `.console-header`, `.console-status`, `.console-controls`, `.console-close`, `.console-output`
- Form: `.form-error`
- Table: `.empty-state`
- Body: `body.has-console`

**Styles to add**:

```css
/* Toolbar */
.toolbar {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

/* Page header with inline reload */
.page-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.page-header h1 {
  margin: 0;
}

/* Table enhancements */
table th input[type="checkbox"],
table td input[type="checkbox"] {
  width: 1rem;
  height: 1rem;
  cursor: pointer;
}

td.actions {
  white-space: nowrap;
}

td.actions button {
  margin-right: 0.25rem;
}

td.actions button:last-child {
  margin-right: 0;
}

/* Form groups (for modal forms) */
.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: 500;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: #0078d4;
  box-shadow: 0 0 0 2px rgba(0,120,212,0.2);
}

/* Form actions (button row) */
.form-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 1rem;
}

/* Button variants */
.btn-secondary {
  background: #6c757d;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.btn-secondary:hover {
  background: #5a6268;
}

/* Result output in modal */
.result-output {
  max-height: 400px;
  overflow: auto;
  background: #f5f5f5;
  border: 1px solid #ddd;
  padding: 1rem;
  border-radius: 4px;
  margin: 0 0 1rem 0;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.875rem;
  white-space: pre-wrap;
}
```

---

## Key Mechanisms

### Implementation Goal

The V2 UI implementation separates **what to call** (endpoint configuration) from **how to call** (fetch vs stream logic):

- **Buttons declare intent** via `data-*` attributes (URL, method, format, result handling)
- **Generic functions execute** the actual HTTP calls based on those attributes
- **Post-call behavior** (reload, toast, modal) is also declarative, not hardcoded

This allows routers to define UI behavior entirely through HTML attributes and column/button configuration, without writing custom JavaScript for each action.

### Call Mechanisms Overview

Three JavaScript functions handle all HTTP communication:

- **`callEndpoint(btn, itemId, bodyData)`** - Unified entry point for button clicks; use for all button-triggered actions
- **`fetch()` (direct)** - Standard HTTP request with JSON response; called by `callEndpoint` for `format=json`
- **`connectStream(url, options)`** - SSE streaming with console output; called by `callEndpoint` for `format=stream`

```
User clicks button
       │
       ▼
┌──────────────────┐
│  callEndpoint()  │  Reads data-* attributes from button
└────────┬─────────┘
         │
         ▼
    ┌────────────┐
    │ format=?   │
    └─────┬──────┘
          │
    ┌─────┴─────┐
    │           │
    ▼           ▼
┌────────┐  ┌─────────────┐
│ "json" │  │  "stream"   │
└───┬────┘  └──────┬──────┘
    │              │
    ▼              ▼
┌────────┐  ┌───────────────┐
│ fetch()│  │connectStream()│
└───┬────┘  └──────┬────────┘
    │              │
    ▼              ▼
┌────────────┐  ┌─────────────────┐
│ JSON result│  │ SSE events:     │
│ {ok, data} │  │ start_json      │
└─────┬──────┘  │ log (multiple)  │
      │         │ end_json        │
      │         └────────┬────────┘
      │                  │
      ▼                  ▼
┌─────────────────────────────────┐
│  Post-call behavior:            │
│  - Show toast or modal          │
│  - Reload table (if configured) │
│  - Remove row (DELETE + json)   │
└─────────────────────────────────┘
```

### format=json Code Path

**Trigger:** Button with `data-format="json"` (or no data-format, as json is default)

**Use cases:**
- Delete single item
- Create/Update item (from modal form)
- Any quick operation with immediate result

**Flow:**
```javascript
// 1. User clicks button
onclick="callEndpoint(this, 'item_123')"

// 2. callEndpoint reads attributes, calls fetch
const response = await fetch(url, { method, headers, body });
const result = await response.json();

// 3. Check result.ok
if (result.ok) {
  // 4a. Success path
  if (method === 'DELETE' && itemId) {
    document.getElementById('item-' + itemId).remove();  // Remove row
    updateItemCount();
  } else if (reloadOnFinish) {
    reloadItems();  // Refresh entire table
  }
  // 5. Show result based on data-show-result
  if (showResult === 'modal') showResultModal(result);
  else if (showResult === 'toast') showToast('Success', itemId, 'success');
} else {
  // 4b. Error path
  showToast('Failed', result.error, 'error');
}
```

**Key behaviors:**
- Synchronous feel (await completes before UI updates)
- DELETE with itemId removes row immediately, skips reload (row already gone)
- Other methods reload table if `reloadOnFinish=true` (default)
- Error shown as toast regardless of `data-show-result`
- HTTP headers: `Content-Type: application/json` for POST/PUT with body

### format=stream Code Path

**Trigger:** Button with `data-format="stream"`

**Use cases:**
- Long-running operations (selftest, bulk create)
- Operations that emit progress logs
- Operations supporting pause/resume/cancel

**Flow:**
```javascript
// 1. User clicks button
onclick="callEndpoint(this)"

// 2. callEndpoint detects format=stream, calls connectStream
connectStream(url, { method, bodyData, reloadOnFinish, showResult });

// 3. connectStream opens console, connects via fetch
showConsole();
clearConsole();
updateConsoleStatus('connecting');

fetch(url, fetchOptions).then(response => {
  updateConsoleStatus('connected');
  const reader = response.body.getReader();
  
  // 4. Process SSE events in loop
  function read() {
    reader.read().then(({ done, value }) => {
      if (done) {
        // 6. Stream ended - show result
        updateConsoleStatus('disconnected');
        if (showResult === 'modal') showResultModal(lastEndJson);
        else showToast('Job Finished', jobId, resultType);
        if (reloadOnFinish) reloadItems();
        return;
      }
      // 5. Parse SSE lines, handle events
      parseSSE(value);  // Calls handleSSEData for each event
      read();  // Continue reading
    });
  }
  read();
});
```

**SSE Event Handling:**
```javascript
function handleSSEData(eventType, data) {
  if (eventType === 'start_json') {
    const json = JSON.parse(data);
    currentJobId = json.job_id;        // Enable pause/resume
    appendToConsole("===== START: Job ID='" + json.job_id + "'");
  } else if (eventType === 'log') {
    appendToConsole(data);             // Plain text to console
  } else if (eventType === 'end_json') {
    const json = JSON.parse(data);
    lastEndJson = json;                // Store for result display
    appendToConsole("===== END: Job ID='" + json.job_id + "' Result='" + status + "'");
  }
}
```

**Key behaviors:**
- Console panel shown immediately
- Progress visible in real-time
- Pause/Resume button enabled after `start_json`
- Result shown after stream ends (not during)
- Table reload happens after stream ends

**Error handling:**
- Network errors caught in `.catch()` block
- Shows error toast: `showToast('Job Error', err.message, 'error')`
- Resets state: `currentJobId = null`, `isPaused = false`
- Updates console status to 'disconnected'

### UI Trigger Points

| UI Element | Trigger | Function Called | Typical Format |
|------------|---------|-----------------|----------------|
| Row [Delete] button | `onclick` | `callEndpoint(this, itemId)` | json |
| Row [Edit] button | `onclick` | `showUpdateForm(itemId)` | N/A (modal) |
| Toolbar [New Item] | `onclick` | `showNewItemForm()` | N/A (modal) |
| Toolbar [Run Selftest] | `onclick` | `callEndpoint(this)` | stream |
| Toolbar [Delete (N)] | `onclick` | `bulkDelete()` | json (loop) |
| Modal [OK] (create) | `onclick` | `callEndpoint(this, null, bodyData)` | json |
| Modal [OK] (update) | `onclick` | `callEndpoint(this, sourceItemId, bodyData)` | json |
| Header [Reload] button | `onclick` | `reloadItems()` | json (direct) |
| Console [Pause/Resume] | `onclick` | `togglePauseResume()` | json (control) |

### Direct fetch() Calls

Some operations bypass `callEndpoint()` and call `fetch()` directly:

**`reloadItems()`** - Fetches list endpoint, re-renders table
```javascript
const response = await fetch(listEndpoint);  // e.g., /v2/demorouter1?format=json
const result = await response.json();
renderItemsTable(result.data);
```

**`bulkDelete()`** - Loops through selected items
```javascript
for (const itemId of selectedIds) {
  const response = await fetch(deleteUrl.replace('{itemId}', itemId), { method: 'DELETE' });
  // Handle per-item result, remove row
}
showToast('Bulk Delete', deleted + ' items deleted', 'success');  // Single summary toast
```

**`togglePauseResume()`** - Job control endpoint
```javascript
const response = await fetch(`/v2/jobs/control?job_id=${currentJobId}&action=${action}`);
const result = await response.json();
if (result.ok) isPaused = !isPaused;
```

**`showUpdateForm(itemId)`** - Fetches item data for edit form
```javascript
const response = await fetch(getEndpoint + '?item_id=' + itemId + '&format=json');
const result = await response.json();
// Populate modal form with result.data
```

### Declarative Button Pattern

Buttons use `data-*` attributes for endpoint configuration instead of inline JavaScript logic:

```html
<button data-url="/v2/demorouter1/delete?item_id={itemId}" 
        data-method="DELETE" 
        data-format="json"
        data-show-result="toast"
        data-reload-on-finish="true"
        onclick="callEndpoint(this, 'demo_001')">Delete</button>
```

**Attributes:**
- `data-url` - Endpoint URL with `{itemId}` and `{router_prefix}` placeholders
- `data-method` - HTTP method (GET, POST, PUT, DELETE)
- `data-format` - Response handling: `json` (fetch) or `stream` (SSE via `connectStream()`)
- `data-show-result` - Where to display result: `toast` (default), `modal`, or `none`
- `data-reload-on-finish` - Whether to reload table after completion (`true`/`false`)

**Not a data-* attribute:**
- `confirm_message` - Used to generate inline onclick: `if(confirm('message')) callEndpoint(this, 'itemId')`

**Benefits:**
- Single `callEndpoint()` function handles all button actions
- Button configuration is visible in HTML, not buried in JS
- Easy to generate from Python (just set attributes)
- Supports both sync (JSON) and async (SSE stream) endpoints

**Complex buttons:** Buttons requiring pre-processing (form validation, parameter building, confirmation dialogs) may deviate from the declarative pattern by using custom `onclick` handlers. These handlers should still use the same underlying functions for server interaction:
- Call `connectStream(url, options)` for streaming endpoints
- Call `fetch()` directly for JSON endpoints, following the same result handling pattern
- Use `showToast()`, `showResultModal()`, `reloadItems()` for consistent UI feedback

Example (modal form submission):
```javascript
function submitForm(btn) {
  const data = gatherFormData();          // Custom pre-processing
  if (!validateForm(data)) return;        // Custom validation
  closeModal();
  callEndpoint(btn, data.item_id, data);  // Standard endpoint call
}
```

### Unified Endpoint Caller

```javascript
async function callEndpoint(btn, itemId = null, bodyData = null) {
  let url = btn.dataset.url;
  if (itemId) url = url.replace('{itemId}', itemId);
  
  const method = btn.dataset.method || 'GET';
  const format = btn.dataset.format || 'json';
  const showResult = btn.dataset.showResult || 'toast';
  const reloadOnFinish = btn.dataset.reloadOnFinish !== 'false';
  
  if (format === 'stream') {
    connectStream(url, { method, bodyData, reloadOnFinish, showResult });
  } else {
    // Standard fetch with JSON response handling
    const response = await fetch(url, { method, body: bodyData ? JSON.stringify(bodyData) : null });
    const result = await response.json();
    // Handle success/error, reload if needed, show result
  }
}
```

### Placeholder Substitution

Button URLs support placeholders replaced at render time or call time:

| Placeholder | Replaced By | When |
|-------------|-------------|------|
| `{router_prefix}` | Router's API prefix (e.g., `/v2`) | Render time (Python) |
| `{itemId}` | Row's item ID | Call time (JavaScript) |

**Note:** Use `{itemId}` (camelCase) as the canonical placeholder for item IDs in URLs.

### Stream vs JSON Format

The `data-format` attribute determines how responses are handled:

**`format="json"`** (default):
- Uses `fetch()` with JSON parsing
- Shows result immediately via toast or modal
- Row removal for DELETE actions

**`format="stream"`**:
- Routes to `connectStream()` for SSE handling
- Opens console panel, displays streaming output
- Shows result after stream ends

---

## JavaScript Functions

All JavaScript functions are generated as part of the UI page. The library provides these as string templates.

### Function Categories

#### 1. Toast Functions
- `showToast(title, message, type, autoDismiss)` - Display notification
- `escapeHtml(text)` - Sanitize text for HTML

#### 2. Modal Functions
- `openModal()` - Show modal overlay, auto-focus first input field
- `closeModal()` - Hide modal, reset width
- `handleEscapeKey(event)` - Close on Escape key
- `showResultModal(data)` - Display job result in modal

#### 3. Console/SSE Functions
- `connectStream(url, options)` - Connect to SSE endpoint
- `handleSSEData(eventType, data)` - Process SSE events
- `appendToConsole(text)` - Add text to console output
- `clearConsole()` - Clear console output
- `showConsole()` - Show console panel
- `hideConsole()` - Hide console panel
- `updateConsoleStatus(state)` - Update status indicator
- `initConsoleResize()` - Enable drag-to-resize

#### 4. Job Control Functions
- `togglePauseResume()` - Send pause/resume command
- `updatePauseResumeButton()` - Update button state

#### 5. Generic Endpoint Functions
- `callEndpoint(btn, itemId, bodyData)` - Unified endpoint caller

#### 6. Table Functions
- `reloadItems()` - Fetch and re-render table
- `renderItemsTable(items)` - Render tbody from data
- `renderItemRow(item)` - Generate single row HTML
- `updateItemCount()` - Update count display

#### 7. Selection Functions
- `updateSelectedCount()` - Update selected count
- `toggleSelectAll()` - Toggle all checkboxes
- `getSelectedItemIds()` - Get array of selected IDs
- `bulkDelete()` - Delete all selected items

#### 8. Form Functions
- `showFieldError(input, message)` - Display inline error
- `clearFieldError(input)` - Remove inline error

---

## Python UI Generation Functions

### Layer Architecture (following V1 pattern)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Router (e.g., demorouter.py, crawler.py)                                    │
│  └─> Calls high-level page generators with config                            │
├──────────────────────────────────────────────────────────────────────────────┤
│  High-Level Page Generators                                                  │
│  └─> generate_ui_page()            # Complete UI page with all features      │
│  └─> generate_list_page()          # Simpler list without full UI            │
│  └─> generate_router_docs_page()   # Router root docs (HTML)                 │
│  └─> generate_endpoint_docs_page() # Action endpoint docs (plain text)       │
├──────────────────────────────────────────────────────────────────────────────┤
│  Component Generators                                                        │
│  └─> generate_html_head()          # <head> with CSS/JS links                │
│  └─> generate_toast_container()    # Toast notification area                 │
│  └─> generate_modal_structure()    # Modal overlay + content shell           │
│  └─> generate_console_panel()      # Console with resize/controls            │
│  └─> generate_toolbar()            # Button toolbar                          │
│  └─> generate_table()              # Table with headers and rows             │
│  └─> generate_table_row()          # Single data row                         │
├──────────────────────────────────────────────────────────────────────────────┤
│  JavaScript Generators                                                       │
│  └─> generate_core_js()            # Toast, modal, escape utilities          │
│  └─> generate_console_js()         # SSE streaming, console management       │
│  └─> generate_table_js()           # Table rendering, reload                 │
│  └─> generate_selection_js()       # Checkbox selection, bulk actions        │
│  └─> generate_form_js()            # Form validation helpers                 │
├──────────────────────────────────────────────────────────────────────────────┤
│  Response Helpers                                                            │
│  └─> json_result()                 # Consistent JSON response                │
│  └─> html_result()                 # Simple HTML response                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Function Signatures

#### High-Level Page Generator

```python
def generate_ui_page(
  title: str,
  router_prefix: str,
  items: List[Dict],
  columns: List[Dict],
  row_id_field: str,
  row_id_prefix: str = "item",
  navigation_html: str = "",
  toolbar_buttons: List[Dict] = None,
  enable_selection: bool = True,
  enable_bulk_delete: bool = True,
  console_initially_hidden: bool = False,  # True = hidden until stream starts
  list_endpoint: str = None,           # e.g., "{router_prefix}/demorouter1?format=json"
  delete_endpoint: str = None,         # e.g., "{router_prefix}/demorouter1/delete?item_id={itemId}"
  jobs_control_endpoint: str = None,   # e.g., "{router_prefix}/jobs/control"
  render_row_js: str = None,           # Custom renderItemRow function body
  additional_js: str = "",             # Router-specific JS
  additional_css: str = ""             # Router-specific inline CSS
) -> str:
  """
  Generate complete UI page with all V2 features.
  
  Args:
    title: Page title (e.g., "Demo Items")
    router_prefix: API prefix (e.g., "/v2")
    items: List of data dictionaries
    columns: Column configuration (see below)
    row_id_field: Field name for row ID (e.g., "item_id")
    row_id_prefix: Prefix for row ID attribute (e.g., "item" -> id="item-123")
    navigation_html: Raw HTML for navigation links (e.g., '<a href="/">Back to Main Page</a>')
    toolbar_buttons: List of toolbar button configs
    enable_selection: Show checkboxes for selection
    enable_bulk_delete: Show bulk delete button
    console_initially_hidden: If True, console starts hidden and auto-shows on stream
    list_endpoint: Endpoint for reloading items (JSON format)
    delete_endpoint: Endpoint template for delete ({itemId} placeholder)
    jobs_control_endpoint: Endpoint for pause/resume/cancel
    render_row_js: Custom JS for renderItemRow (receives 'item' object)
    additional_js: Extra JavaScript to include
    additional_css: Extra CSS to include inline
    
  Returns:
    Complete HTML page string
  """
```

#### Self-Documentation Generators

Two formats per `_V2_SPEC_ROUTERS.md`:

```python
def generate_router_docs_page(
  title: str,
  description: str,
  router_prefix: str,
  endpoints: List[Dict],      # [{"path": "/get", "desc": "Get item", "formats": ["json", "html"]}]
  navigation_html: str = ""
) -> str:
  """
  Generate router root documentation page (HTML).
  
  Returns minimalistic HTML with:
  - Title
  - Navigation links (under title)
  - Description
  - List of endpoints with links to each supported format
  - Standard CSS/JS includes
  """

def generate_endpoint_docs_page(
  docstring: str,
  router_prefix: str
) -> str:
  """
  Generate action endpoint documentation (plain text UTF-8).
  
  Simply returns docstring with {router_prefix} placeholder replaced.
  Use with PlainTextResponse(result, media_type="text/plain; charset=utf-8")
  """
```

#### Column Configuration

```python
columns = [
  {
    "field": "item_id",         # Field name in data dict
    "header": "ID",             # Column header text
    "format": None,             # Optional: Python format function (value -> str)
    "js_format": None,          # Optional: JS expression (item.field -> display)
    "default": "-"              # Default if field missing
  },
  {
    "field": "name",
    "header": "Name"
  },
  {
    "field": "actions",
    "header": "Actions",
    "buttons": [                # Action buttons for this column
      {
        "text": "Edit",
        "onclick": "showUpdateForm('{itemId}')",  # JS with placeholder
        "class": "btn-small"
      },
      {
        "text": "Delete",
        "data_url": "{router_prefix}/delete?item_id={itemId}",
        "data_method": "DELETE",
        "data_format": "json",
        "confirm_message": "Delete {itemId}?",  # Used in onclick: if(confirm(msg)) callEndpoint(...)
        "class": "btn-small btn-delete"
      }
    ]
  }
]
```

#### Toolbar Button Configuration

```python
toolbar_buttons = [
  {
    "text": "New Item",
    "onclick": "showNewItemForm()",
    "class": "btn-primary"
  },
  {
    "text": "Run Selftest",
    "data_url": "{router_prefix}/selftest?format=stream",
    "data_method": "GET",              # HTTP method (default: GET)
    "data_format": "stream",           # 'json' or 'stream'
    "data_show_result": "modal",       # 'toast', 'modal', or 'none'
    "data_reload_on_finish": "true",   # Reload table after completion
    "class": "btn-primary"
  }
]
```

#### Component Generators

```python
def generate_html_head(
  title: str,
  include_htmx: bool = True,
  include_v2_css: bool = True,
  additional_css: str = ""
) -> str:
  """Generate <head> section with standard resources."""

def generate_toast_container() -> str:
  """Generate toast notification container div."""

def generate_modal_structure() -> str:
  """Generate modal overlay with content shell."""

def generate_console_panel(
  title: str = "Console Output",
  include_pause_resume: bool = True
) -> str:
  """Generate console panel with resize handle and controls."""

def generate_toolbar(
  buttons: List[Dict],
  router_prefix: str,
  enable_bulk_delete: bool = True
) -> str:
  """Generate toolbar with action buttons."""

def generate_table(
  columns: List[Dict],
  rows_html: str,
  enable_selection: bool = True,
  empty_message: str = "No items found"
) -> str:
  """Generate table with headers and tbody."""

def generate_table_row(
  item: Dict,
  columns: List[Dict],
  row_id_field: str,
  row_id_prefix: str,
  router_prefix: str,
  enable_selection: bool = True
) -> str:
  """Generate single table row."""
```

#### JavaScript Generators

```python
def generate_core_js() -> str:
  """Generate toast, modal, escapeHtml functions."""

def generate_console_js(
  router_prefix: str,
  jobs_control_endpoint: str
) -> str:
  """Generate SSE streaming and console management functions."""

def generate_table_js(
  router_prefix: str,
  list_endpoint: str,
  columns: List[Dict],
  row_id_field: str,
  row_id_prefix: str,
  render_row_js: str = None
) -> str:
  """Generate table rendering and reload functions."""

def generate_selection_js(
  router_prefix: str,
  delete_endpoint: str
) -> str:
  """Generate checkbox selection and bulk delete functions."""

def generate_form_js() -> str:
  """Generate form validation helper functions."""
```

#### Response Helpers

```python
def json_result(ok: bool, error: str, data: Any) -> JSONResponse:
  """Generate consistent JSON response: {ok, error, data}."""

def html_result(
  title: str,
  data: Any,
  navigation_html: str = ""
) -> HTMLResponse:
  """
  Generate simple HTML page with data table.
  
  Args:
    title: Page title
    data: Data to display in table
    navigation_html: Raw HTML for navigation links (e.g., '<a href="...">Back</a> | <a href="/">Back to Main Page</a>')
  
  Navigation is placed under the title, before the data table.
  """
```

---

## Router Integration Example

```python
# In demorouter.py (after refactoring)

from routers_v2.common_ui_functions_v2 import (
  generate_ui_page, json_result, html_result
)

@router.get("/demorouter1")
async def demorouter_root(request: Request):
  # ... logging, param handling ...
  
  if format_param == "ui":
    columns = [
      {"field": "item_id", "header": "ID"},
      {"field": "name", "header": "Name"},
      {"field": "version", "header": "Version"},
      {
        "field": "actions",
        "header": "Actions",
        "buttons": [
          {"text": "Edit", "onclick": "showUpdateForm('{itemId}')", "class": "btn-small"},
          {"text": "Delete", "data_url": f"{router_prefix}/demorouter1/delete?item_id={{itemId}}", 
           "data_method": "DELETE", "data_format": "json", "confirm_message": "Delete {itemId}?",
           "class": "btn-small btn-delete"}
        ]
      }
    ]
    
    toolbar = [
      {"text": "New Item", "onclick": "showNewItemForm()", "class": "btn-primary"},
      {"text": "Create Demo Items", "onclick": "showCreateDemoItemsForm()", "class": "btn-primary"},
      {"text": "Run Selftest", "data_url": f"{router_prefix}/demorouter1/selftest?format=stream",
       "data_format": "stream", "data_show_result": "modal", "class": "btn-primary"}
    ]
    
    # Router provides custom form functions
    custom_js = '''
function showNewItemForm() { /* ... router-specific form ... */ }
function showUpdateForm(itemId) { /* ... router-specific form ... */ }
function showCreateDemoItemsForm() { /* ... router-specific form ... */ }
'''
    
    html = generate_ui_page(
      title="Demo Items",
      router_prefix=router_prefix,
      items=items,
      columns=columns,
      row_id_field="item_id",
      navigation_html=main_page_nav_html,
      toolbar_buttons=toolbar,
      list_endpoint=f"{router_prefix}/demorouter1?format=json",
      delete_endpoint=f"{router_prefix}/demorouter1/delete?item_id={{itemId}}",
      jobs_control_endpoint=f"{router_prefix}/jobs/control",
      additional_js=custom_js
    )
    return HTMLResponse(html)
```

---

## What is NOT Generalized

The following remain router-specific (only styles are shared):

1. **Create/Update forms** - Each router has different fields
2. **Form submission handlers** - `submitNewItemForm()`, `submitUpdateForm()`
3. **Router-specific dialogs** - e.g., `showCreateDemoItemsForm()`
4. **Data validation logic** - Field-specific validation rules
5. **Custom result displays** - Router-specific result formatting
6. **Navigation HTML** - Defined via router-level constant (e.g., `main_page_nav_html`), passed to page generators. Example: `main_page_nav_html = '<a href="/">Back to Main Page</a>'`
   - Router root: `generate_router_docs_page(..., navigation_html=main_page_nav_html)`
   - format=ui: `generate_ui_page(..., navigation_html=main_page_nav_html)`
   - format=html: `html_result(..., navigation_html=f'<a href="...">Back</a> | {main_page_nav_html}')`

Routers implement 1-5 as `additional_js` parameter or in separate JS files.

---

## Implementation Order

1. Create `/src/routers_v2/common_ui_functions_v2.py` with basic structure
2. Implement response helpers (`json_result`, `html_result`)
3. Implement component generators (head, toast, modal, console, table)
4. Implement JavaScript generators (core, console, table, selection, form)
5. Implement high-level `generate_ui_page()`
6. Extend `/static/css/routers_v2.css` with missing styles
7. Create `demorouter2.py` using the library (refactored from demorouter1.py)
8. Verify all features work identically to current implementation

---

## Implementation Details

### Button JS Generation - Escaping for Nested Contexts

When generating button HTML inside a JS string literal, there are multiple nested contexts requiring careful escaping:

```
Context layers (outside → inside):
1. Python string
2. JS string literal (single quotes)
3. HTML attribute value (double quotes)
4. JS code inside onclick (may have string literals)
```

**Escaping constants:**
- `esc_dq = '\\"'` - escaped double quote for HTML attributes inside JS string
- `esc_sq = "\\'"` - escaped single quote for JS strings inside onclick

**Template-based approach:**
```python
template = "<button [CLASS][DATA_URL][DATA_METHOD][DATA_FORMAT][ONCLICK]>[TEXT]</button>"

# Step by step replacement - if attribute exists, replace with value; else empty string
if btn_class:
  template = template.replace("[CLASS]", f'class={esc_dq}{btn_class}{esc_dq} ')
else:
  template = template.replace("[CLASS]", "")
```

**itemId placeholder replacement:**

Two patterns depending on context:
- Function arguments (need quoted string in output): `'{itemId}'` → `\'' + itemId + \'`
- String concatenation (confirm message): `'{itemId}'` → `' + itemId + '`

**confirm() escaping:**

Since confirm() is inside a JS string literal, its quotes must be escaped:
```python
# Wrong: if(confirm('text'))  - inner ' closes outer JS string
# Right: if(confirm(\'text\')) - escaped quotes stay inside string
onclick_value = f"if(confirm({esc_sq}{confirm_text}{esc_sq})) {call_endpoint}"
```

**renderItemRow step-by-step structure:**

Generated JS uses arrays for maintainability:
```javascript
function renderItemRow(item) {
  const itemId = item.item_id || '';
  const rowId = escapeHtml(String(itemId).replace(/[^a-zA-Z0-9_]/g, '_'));
  const cells = [];
  
  cells.push('<td>...</td>');  // checkbox
  cells.push('<td>...</td>');  // each data column
  
  const btns = [];
  btns.push('<button ...>Edit</button>');
  btns.push('<button ...>Delete</button>');
  cells.push('<td class="actions">' + btns.join('') + '</td>');
  
  return '<tr id="item-' + rowId + '">' + cells.join('') + '</tr>';
}
```

**Docstring Placeholder Replacement:**

Endpoint docstrings use `{router_prefix}` and `{router_name}` placeholders for self-documentation. Since docstrings are regular strings (not f-strings), placeholders must be replaced at runtime:

```python
doc = func.__doc__.replace("{router_prefix}", router_prefix).replace("{router_name}", router_name)
return PlainTextResponse(generate_endpoint_docs(doc, router_prefix), ...)
```

---

## Spec Changes

**[2024-12-17 12:00]**
- Added: UI-IG-11/12 for required endpoints validation
- Added: DD-UI-11/12/13 for edge cases (single stream, XSS, row ID sanitization)

**[2024-12-17 11:30]**
- Changed: Replaced `enable_console` with `console_initially_hidden` to prevent broken state
- Fixed: Modal OK button calls to use correct signature `callEndpoint(btn, itemId, bodyData)`

**[2024-12-17 11:00]**
- Added: Console visible by default, error handling, HTTP headers
- Changed: Standardized placeholder to `{itemId}` (camelCase)
- Fixed: Clarified confirm is inline onclick, not data-* attribute

**[2024-12-17 10:30]**
- Added: Key Mechanisms section with call patterns, declarative button pattern

**[2024-12-17 10:00]**
- Initial specification created
