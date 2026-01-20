### Question 1 - Endpoint Semantics & Self-Documentation

A developer opens a browser and navigates to:

```
GET /v2/domains
```

No query parameters are provided.
 What **must** the response be, and why?

### Reference Answer 1 - Endpoint Semantics & Self-Documentation

The response **must be self-documentation**, returned as UTF-8 text.

Reason:

- Per DD-E001, a bare `GET /v2/resource` with no query params **always returns documentation**.
- This applies regardless of whether the resource supports listing.
- This enables developers to understand the endpoint directly from the URL without external docs.

------

### Question 2 - Action-Suffixed Behavior Validation

Given the shorthand specification:

```
L(jhu)C(j)G(jh)U(j)D(jh): /v2/icecreams
```

What should happen if a client sends:

```
PUT /v2/icecreams/create
```

### Reference Answer 2 - Action-Suffixed Behavior Validation

The server must return:

- HTTP 400: JSON error result "HTTP method 'PUT' not supported."

Reason:

- `create` supports **POST only**.
- Action-suffixed endpoints strictly define allowed HTTP methods.
- Unsupported methods must not be silently accepted or mapped.

------

### Question 3 - Format Handling & Error Discipline

An endpoint supports `G(jh)` only.
 A client sends:

```
GET /v2/resource/get?resource_id=123&format=ui
```

What is the correct behavior?

### Reference Answer 3 - Format Handling & Error Discipline

Return:

- **HTTP 400 – Bad Request**
- JSON error with result "Format 'ui' not supported".

Reason:

- Endpoints are **not required to support all formats**.
- Unsupported formats must fail explicitly.
- Silent fallbacks or format coercion violate the spec.

------

### Question 4 - Uniform Query Param Contract

Why does the specification insist on explicit query parameters like `domain_id`, `vector_store_id`, instead of generic `id`?

### Reference Answer 4 - Uniform Query Param Contract

Because:

- It disambiguates object types in endpoints requiring multiple identifiers.
- It improves self-documentation and debugging.
- It supports semantic clarity across nested resources.

This is explicitly mandated by DD-E007 and DD-E008 (with exceptions).

------

### Question 5 - Streaming vs Non-Streaming Endpoints

An endpoint supports `U(js)` and receives:

```
PUT /v2/resource/update?format=stream
```

What is the expected response type and MIME type?

### Reference Answer 5 - Streaming vs Non-Streaming Endpoints

The response must be:

- **Server-Sent Events (SSE)**
- MIME type: `Content-Type: text/event-stream`
- UTF-8 encoded
- Using `event:` and `data:` lines compatible with HTMX SSE
- Stream must include `start_json` -> `log` -> `end_json` events

If the endpoint did **not** support `(s)`, it must return HTTP 400.

------

### Question 6 - Job File Lifecycle & Control

A crawling job was started using this HTTP endpoint:
`GET /v2/crawler/crawl?domain_id=TEST01` -> returned in the JSON `"job_id": "jb_42"`
The job needs to be paused. What action enables this, and how is it detected?
Use the full storage path for example files.

### Reference Answer 6 - Job File Lifecycle & Control

The user (or UI) sends:
`GET /v2/jobs/control?job_id=jb_42&action=pause`

This request causes the system to create a pause control file in the same router-specific jobs directory as the running job, using the .pause_requested state extension. For example:
```
PERSISTENT_STORAGE_PATH/jobs/crawler/2025-11-26_14-25-00_[crawl]_[jb_42]_[TEST01].pause_requested
```

Detection:
- The running job process periodically scans its router-specific jobs directory for control files.
- When a `.pause_requested` file for its job_id is detected, the job transitions from the `.running` state to the `.paused state`.

------

### Question 7 - `jb_id` Generation Correctness

Describe the exact algorithm used to generate the next `jb_id`.

### Reference Answer 7 - `jb_id` Generation Correctness

Algorithm:

1. Scan all files under `PERSISTENT_STORAGE_PATH/jobs/**/*` (recursive)
2. Keep files ending in `.running`, `.completed`, `.cancelled`, `.paused`
3. Sort by modification time (newest first)
4. Take the first 1000 files (most recent)
5. Extract numeric part of `jb_[NUMBER]` using regex pattern
6. Find the maximum number
7. Return `max + 1` (or `1` if no files found)

If create fails due to collision, regenerate/retry.

This guarantees:

- Monotonic IDs
- Cross-router uniqueness
- Robustness against deleted or old job files

Why limit to 1000 files?
- Performance: Avoids scanning entire history
- Correctness: Recent files contain the highest IDs
- The limit is intentionally high to handle burst scenarios

------

### Question 8 - Dry-Run Semantics

What must `dry_run=true` guarantee for a `DELETE` endpoint that supports it?

### Reference Answer 8 - Dry-Run Semantics

It must guarantee:

- **No mutation of persistent state**
- No deletion of files, vector stores, or backend objects
- Simulation of logic and outcome to the degree possible
- Return of the **predicted result** as if the action ran

Dry-run is a safety and validation mechanism, not a partial execution.

------

### Question 9 - Nested Resource Endpoint Interpretation

Interpret the meaning of this endpoint:

```
DELETE /v2/inventory/vector_stores/files/delete?vector_store_id=vs_1&file_id=f_9&mode=delete_globally
```

### Reference Answer 9 - Nested Resource Endpoint Interpretation

It performs **two actions in order**:

1. Removes the file reference from the specified vector store
2. Deletes the file **globally** from OpenAI file storage

The behavior is explicitly controlled by `mode=delete_globally`.
 Default mode would only remove the reference.

------

### Question 10 - Shorthand Specification to Behavior Mapping

Given:

```
L(jhu)G(jh): /v2/icecreams/flavours
```

List **all valid GET endpoints**, **all invalid format query params**, and **all invalid HTTP methods** that are used elsewhere in the spec but are not supported here.

### Reference Answer 10 - Shorthand Specification to Behavior Mapping

**Valid:**

- `GET /v2/icecreams/flavours` -> Self-documentation (UTF-8 text)
- `GET /v2/icecreams/flavours?format=json` -> JSON array `[...]` with all flavours
- `GET /v2/icecreams/flavours?format=html` -> HTML table with all flavours
- `GET /v2/icecreams/flavours?format=ui` -> Interactive UI listing with View actions only
- `GET /v2/icecreams/flavours/get` -> Self-documentation (UTF-8 text)
- `GET /v2/icecreams/flavours/get?flavour_id={id}` -> JSON object `{...}`
- `GET /v2/icecreams/flavours/get?flavour_id={id}&format=json` -> JSON object `{...}`
- `GET /v2/icecreams/flavours/get?flavour_id={id}&format=html` -> HTML detail view

**Invalid Format Query Parameters (must return HTTP 400):**

- `format=stream` - no `(s)` in either `L(jhu)` or `G(jh)`
- `format=zip` -  no `(z)`

**Invalid HTTP Methods (must return HTTP 400):**

- `POST` (no `C`)
- `PUT` (no `U`)
- `DELETE` (no `D`)