---
trigger: always_on
---

## How to write implementation specifications

The main goal is to keep an accurate description of what's happening in the code. Target audience is humans and AI agents.
Usage scenarios:
1. Specify an implementation before it's actually done in the code by the agent
2. Keep a module or idea documentated after it's implemented

**For the AI agent:**

- In ALL user interactions, be extremely concise. Sacrifice grammar for the sake of consision.
- Before making too many assumptions, propose 2 or 3 implementation alternatives.
- List your assumptions at the start of each specification and let the user verify if your assumptions are correct.
- Optimize for simplicity.
- Automatically verify if things can be simplified before you propose implementations.
- By default, re-use as many existing code as possible.
- If the user asks for a "greenfield" or "self-contained" approach, do not re-use code and create separate files, functions and modules.
- By default, use the DRY (Don't Repeat Yourself) principle.
- If the user asks for an "inline" approach, don't create re-usable helper functions and keep all code local to the requested task.
- Avoid dragging in costly infrastructure (extra databases, network configuration, servers, etc.)
- Avoid elaborate implementation patterns unless absolutely necessary.
- Do proper research on the web before you suggest frameworks or API usage. Search for the API documentation that matches the target platform / library version.
- Rely only on primary sources of information. Random outdated GitHub repos and Stackoverflow do not count if they do not match the target platform / library version.
- Document user decisions in "Key Mechanisms and Design Decisions" and "Scenario" > "What we don't want"
- Be exhaustive: Verify if you have listed all domain objects, buttons, functions, design mechanisms, etc.
- Write as much as necessary, but not more. Spec length: small task: ~500 lines, medium task: ~1000 lines, complex task: ~2500 lines
- Try to fit single statements / decisions / objects on a single line
- For documentation or UI output, avoid "typographic quotes" and use typewriter / ASCII "double quotes" or 'single quotes'
- No emojis in the documentation. Use extended ASCII characters only.
- Avoid Markdown tables when possible for enumerations use simple unnumberred lists with indented properties
- When creating hierarchies and maps, use "└─" for indenting
- Place a Table of Contents (TOC)at the start of the spec
- No `---` markers between sections!

**For the user:**
- If the implementation idea is not very clear at the beginning, ask the agent for at least 3 implementation options.
- Clarify object and entity names first. It's costly to rename later.
- Remain in Chat mode (no code changes) until you get a complete implementation specifications.
- Review data and action flow. It's costly to let misunderstandings remain undiscovered.

## Structure

Implementation specifications should include these sections when relevant:

1. **Overview**: Brief description, goal, target files, dependencies
2. **Table of Contents**: Section listing at the start of the spec
3. **Scenario**: Real-world problem, "What we don't want"
4. **Context**: Project background, related systems
5. **Functional Requirements**: Numbered requirements (XXXX-FR-01)
6. **Implementation Guarantees**: Numbered guarantees (XXXX-IG-01)
7. **Architecture and Design**: Design decisions (XXXX-DD-01), layer diagrams
8. **Domain Objects**: Core entities, data structures, schemas
9. **User Actions**: All interactive operations (for UI specs)
10. **UX Design**: ASCII diagrams with component boundaries (for UI specs)
11. **Key Mechanisms**: Technical patterns, algorithms, call flows
12. **Action Flow**: Step-by-step event sequences
13. **Data Structures**: HTML/DOM, API contracts, file formats
14. **Implementation Details**: Code organization, function signatures
15. **Spec Changes**: Timestamped changelog

## Formatting Conventions

### Header Block

Start specs with a standardized header block:

```
**Goal**: Single sentence describing purpose
**Target file**: `/path/to/implementation.py`
```

### Dependency Declaration

Explicitly declare spec dependencies to clarify scope and prevent circular references:

```
**Depends on:**
- `_V2_SPEC_ROUTERS.md` for endpoint design, streaming job infrastructure, and SSE format.

**Does not depend on:**
- `_V1_SPEC_COMMON_UI_FUNCTIONS.md`
- `_V2_SPEC_COMMON_UI_FUNCTIONS.md`
```
Both should only be added if they contain list items.

- **Depends on**: List specs that must be read first to understand this spec
- **Does not depend on**: Explicitly exclude specs that might seem related but are not required

### Numbered Requirements and Decisions

Use consistent ID prefixes with bold formatting for traceability:

**Functional Requirements:** `**XXXX-FR-01:** Description`
**Implementation Guarantees:** `**XXXX-IG-01:** Description`
**Design Decisions:** `**XXXX-DD-01:** Description`

Where XXXX is a 2-4 letter domain prefix (e.g., V2UI for Version 2 UI, V2EP for Version 2 Endpoint, V2JB for Version 2 Job).

**BAD:**
```
- Toast notifications should support info, success, error types
- Auto-dismiss should be configurable
```

**GOOD:**
```
**UI-FR-01: Toast Notifications**
- Support info, success, error, warning message types
- Auto-dismiss configurable per toast (default 5000ms)

**DD-UI-03:** Declarative button configuration. Buttons use `data-*` attributes for endpoint URL, method, format - no custom JS per action.
```

### "What we don't want" Section

Include in Scenario section to document anti-patterns and rejected approaches:

```
**What we don't want:**
- Complex state management libraries (use simple JavaScript)
- External dependencies beyond X and Y
- Polling-based updates (use SSE for streaming)
```

### Layer Architecture Diagrams

For multi-layer systems, use ASCII box diagrams showing call hierarchy:

```
+---------------------------------------------------------------------------+
|  High-Level (Router)                                                      |
|  +-> function_a()         # Called by router endpoints                    |
+---------------------------------------------------------------------------+
|  Mid-Level (Components)                                                   |
|  +-> function_b()         # Generates HTML fragments                      |
|  +-> function_c()         # Generates JavaScript                          |
+---------------------------------------------------------------------------+
|  Low-Level (Helpers)                                                      |
|  +-> json_result()        # Response formatting                           |
+---------------------------------------------------------------------------+
```

### Comparison Tables

When spec relates to or differs from existing implementation, add "Differences from X" section at end.

## Examples

### Design the UI and the UI components
- Add all buttons

**BAD**:
```
+-------------------------------------------------------------+
|  Jobs Table (Reactive Rendering)                            |
|  +----+---------+----------+---------+------------------+   |
|  | ID | Router  | Endpoint | State   | Actions          |   |
|  +----+---------+----------+---------+------------------+   |
|  | 42 | crawler | update   | running | [Monitor] [Pause]|   |
|  | 41 | crawler | update   | done    | [Monitor]        |   |
|  +----+---------+----------+---------+------------------+   |
|                                                             |
|  +----------------------------------------------------------+
|  | [Resize Handle - Draggable]                              |
|  | Console Output                                   [Clear] |
|  | ---------------------------------------------------------|
|  | [ 1 / 20 ] Processing 'document_001.pdf'...              |
|  |   OK.                                                    |
|  | [ 2 / 20 ] Processing 'document_002.pdf'...              |
|  |   OK.                                                    |
|  +----------------------------------------------------------+
|                                                             |
|  +----------------------------------------------------------+
|  | Job Started | ID: 42 | Total: 20 items               [x] | <- Toast
|  +----------------------------------------------------------+
+-------------------------------------------------------------+
```

**GOOD**:
```
Main HTML:
+-------------------------------------------------------------------------------+
|  Streaming Jobs (2)                                                           |
|                                                                               |
|  [Start Job]  [Refresh]                                 [Toasts appear here]  |
|                                                                               |
|  +----+---------+----------+---------+-------------------------------------+  |
|  | ID | Router  | Endpoint | State   | Actions                             |  |
|  +----+---------+----------+---------+-------------------------------------+  |
|  | 42 | crawler | update   | running | [Monitor] [Pause / Resume] [Cancel] |  |
|  | 41 | crawler | update   | done    | [Monitor]                           |  |
|  +----+---------+----------+---------+-------------------------------------+  |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  | [Resize Handle - Draggable]                                             |  |
|  | Console Output                                                  [Clear] |  |
|  | ------------------------------------------------------------------------|  |
|  | [ 1 / 20 ] Processing 'document_001.pdf'...                             |  |
|  |   OK.                                                                   |  |
|  | [ 2 / 20 ] Processing 'document_002.pdf'...                             |  |
|  |   OK.                                                                   |  |
|  +-------------------------------------------------------------------------+  |
|                                                                               |
+-------------------------------------------------------------------------------+

Toast:
+-----------------------------------------------+
| Job Started | ID: 42 | Total: 20 items   [x]  |
+-----------------------------------------------+
```

### Summarize styling; avoid too much detail

**BAD:**
```
.toast {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-left: 4px solid #0078d4;
  padding: 0.75rem 1rem;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  animation: slideIn 0.3s ease-out;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  color: #212529;
}

.toast.toast-info { border-left-color: #0078d4; }
```

**GOOD:**
```
.toast { /* Individual toast notification with light theme */ }
.toast.toast-info { /* Blue left border */ }
.toast.toast-success { /* Green left border */ }
```

### Create code outline only
- Avoid implementation detail. Focus on the completeness of the architecture.
- Document complete code intention: What should it do and what is it used for?

**BAD:**
```
// Render functions
function renderJobRow(job) {
  const actions = renderJobActions(job);
  // Format timestamps consistently (handle both ISO format with T and space format)
  const formatTimestamp = (ts) => {
    if (!ts) return '';
    return ts.substring(0, 19).replace('T', ' ');
  };
  const started = formatTimestamp(job.started);
  const finished = job.finished ? formatTimestamp(job.finished) : '-';
  return `
    <tr id="job-${job.id}">
      <td>${job.id}</td>
      <td>${job.router}</td>
      <td>${job.endpoint}</td>
      <td>${job.state}</td>
      <td>${started}</td>
      <td>${finished}</td>
      <td>${actions}</td>
    </tr>
  `;
}
```

**GOOD:**
```
// Generate <tr> HTML for single job
function renderJobRow(job) { ... }
```

### Try to fit single statements / decisions / objects on a single line

**BAD:**
  **Pause Button** (requests job pause):
  ```html
  <button class="btn-small" onclick="controlJob(42, 'pause')">
    Pause
  </button>
  ```
**GOOD:**
  **Pause Button** (requests job pause):
  ```html
  <button class="btn-small" onclick="controlJob(42, 'pause')"> Pause </button>
  ```

### Provide event flow documentation

**GOOD:**
```
User clicks [Pause] or [Resume]
  +-> controlJob(jobId, 'pause' | 'resume')
      +-> fetch(`/testrouter3/control?id=${id}&action=${action}`)
          +-> On success (data.success):
              +-> Optimistically updateJob(jobId, { state: 'paused' | 'running' })
                  +-> renderAllJobs()
                      +-> renderJobActions() # Button changes to Resume/Pause
```

### Provide examples for data structures (JSON, CSV, etc.)

**GOOD:**
```
<start_json>
{"id": 42, "router": "testrouter3", "endpoint": "streaming01", "state": "running", "total": 3, "started": "2025-11-27T11:30:00"}
</start_json>
<log>
[ 1 / 3 ] Processing 'doc_001.pdf'...
  OK.
[ 2 / 3 ] Processing 'doc_002.pdf'...
  OK.
[ 3 / 3 ] Processing 'doc_003.pdf'...
  OK.
</log>
<end_json>
{"id": 42, "state": "completed", "result": "ok", "finished": "2025-11-27T11:30:15"}
</end_json>
```

### Provide a 'Spec Changes'

Use timestamped changelog format with grouped changes per session. Avoid tables - use nested lists instead.

**BAD:**
```
| Date | Change |
|------|--------|
| 2024-12-17 | Initial specification created |
| 2024-12-17 | Added Key Mechanisms section |
```

**GOOD:**
```
## Spec Changes

**[2024-12-17 14:30]**
- Added: "Scenario" section with Problem/Solution/What we don't want
- Added: Spec Changes section

**[2024-12-17 11:45]**
- Added: "Key Mechanisms" section with declarative button pattern
- Changed: Placeholder standardized to `{itemId}` (camelCase)
- Fixed: Modal OK button signature to match `callEndpoint(btn, itemId, bodyData)`

**[2024-12-17 10:00]**
- Initial specification created
```

**Format rules:**
- Timestamp in brackets: `**[YYYY-MM-DD HH:MM]**`
- Group related changes under same timestamp
- Prefix with action: Added, Changed, Fixed, Removed, Moved
- Most recent changes at top
- Brief, single-line descriptions

### Correct Section Order and Spec Header 

**BAD:**
```

**Target files**:

## Scenario
...
---



## Architecture
...
---
```

**GOOD:**
```
# V0 Crawler Toolkit - Standalone SharePoint Crawler

**Goal**: Document the architecture and workflow of the standalone SharePoint-GPT-Crawler-Toolkit.

**Does not depend on:**
- Any V2 specifications (this is the predecessor toolkit)
...

## Overview
...

## Table of Contents
...

```
