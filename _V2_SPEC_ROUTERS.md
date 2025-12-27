# Routers Technical Specification Version 2

**Goal**: Specify V2 routers with consistent endpoint patterns, interactive UI, and streaming job support for the SharePoint-GPT-Middleware.

**Depends on:**
- `hardcoded_config.py` for `PERSISTENT_STORAGE_LOG_EVENTS_PER_WRITE` and path constants
- `_V2_SPEC_COMMON_UI_FUNCTIONS.md` for UI generation patterns
- `_V2_SPEC_DEMOROUTER_UI.md` for demo router UI specification

**Does not depend on:**
- V1 router implementations (`/src/routers_v1/`)
- `_V1_SPEC_COMMON_UI_FUNCTIONS.md`

## Table of Contents

1. Scenario
2. Context
3. Domain Objects
4. Endpoint Architecture and Design
   - Domain Object Schemas
   - Endpoint Design Decisions
   - Action-Suffixed Syntax
   - Query Params Syntax
   - Shorthand Notation
   - Specification of Endpoints
   - Endpoint Return Formats
5. Crawling Process
   - Local Files
   - Map Files
   - Source-Specific Processing
   - Crawling Process Steps
6. Logging Specification
   - Functional Requirements
   - Implementation Guarantees
   - MiddlewareLogger Class
   - Log Output Formats
7. Job Streaming Specification
   - Functional Requirements
   - Implementation Guarantees
   - StreamingJobWriter
   - Examples
8. Spec Changes

This document describes the design and implementation of the **second generation** routers used for crawling, access to domain objects, and long-running job management. First generation routers and endpoints are out of scope and should remain untouched to ensure backwards compatibility.

## Scenario

**Problem:** The V1 routers evolved organically, leading to inconsistent endpoint patterns, duplicated code, and limited UI capabilities. Administrators need a simple way to manage domains, crawl SharePoint content, and monitor jobs without programming skills.

**Solution:** A unified V2 router architecture with:
- Consistent action-suffixed endpoints (`/resource/get`, `/resource/create`, etc.)
- Self-documenting endpoints (bare GET returns documentation)
- Interactive UI via `format=ui` parameter
- Streaming support for long-running jobs via SSE

**What we don't want:**
- Major changes to V1 endpoints philosophy
- Complex client-side state management (server renders initial data)
- Multiple endpoint patterns for the same action
- Separate API and UI codebases (single endpoint serves both)
- Paging and limit functionality for list endpoints

## Context

**Project:** SharePoint-GPT-Middleware

A FastAPI-based middleware application that bridges SharePoint content with OpenAI's AI capabilities. It crawls SharePoint sites (document libraries, lists, and site pages), processes the content, and manages OpenAI vector stores for intelligent search and retrieval.

## Domain objects

**Crawler** - Performs the crawling of SharePoint sites to enable semantic search and other AI use cases
- Uses domains as an entity that can be crawled
- Uses jobs for long-running operations
- The crawling is done in multiple steps:
  1) Downloading data from sources to local storage
  2) Processing and converting data to LLM friendly formats
  3) Uploading files to OpenAI file storage
  4) Adding files to vector stores for embedding / vectorization
- Creates map files in local storage to cache data and ids across systems
  - Allows comparison against new data in the sources
  - `sharepoint_map.csv` - caches file metadata from SharePoint
  - `files_map.csv` - caches local storage, contains file download and processing status
  - `vectorstore_map.csv`- caches vector store data, contains everything in other map files + upload and embedding status

**Domain** - Knownledge domain to be used for RAG use cases
- To be crawled (downloaded and embedded) from SharePoint into a single vector store
- Maps to exactly one vector store (1:1 relation)
- Supports many sources in different SharePoint sites and SharePoint filters
- Contains different categories of SharePoint sources: `file_sources`, `list_sources`, `sitepage_sources`
- Schema: See "Domain object schemas" section below

**Local storage** - Folders and files used to store information that can't be kept in the backend
- Contains files and data downloaded from SharePoint
- Contains map files created during crawling that cache data across systems for faster responses
- Contains cached metadata (retrieved and AI extracted) to allow external filtering

**Inventory** - Access to objects and data stored in the OpenAI backend
- `files` - File storage for files with different purposes
- `vector_stores` - Contain embedded / vectorizes files for semantic search
- `assistants` - Legacy way to interact with models and tools for RAG use cases

**Query API** - Legacy semantic search API offering `query` and `describe` endpoints
- `/describe` and `/describe2` - list all domains
- `/query` and `/query2` - semantic search results for query with cached metadata

**OpenAI proxy** - Replicates behavior of a number of OpenAI API endpoints
- Allows porting of applications to a security-controlled environment where Open AI or Azure OpenAI backends must not be exposed directly

**Report** - Timestamped zip archive of operation results for auditing and debugging
- Created by internal endpoint functions (no create endpoint exposed)
- Contains `report.json` with mandatory fields: `report_id`, `title`, `type`, `created_utc`, `ok`, `error`, `files`
- Contains operation-specific files (map files, logs, etc.)
- Storage: `PERSISTENT_STORAGE_PATH/reports/[folder]/` where folder = plural of type
- Types: `crawl` (folder: `crawls`), `site_scan` (folder: `site_scans`)
- Specification: See `_V2_SPEC_REPORTS.md`

## Endpoint architecture and design

In the following sections `resource` acts as a placeholder for the individual domain objects: `domain`, `vector_store`, etc. while `action` acts as a placeholder for Create, List, Update, Delete, and other actions. The combination of resources and actions is called an endpoint and is implemented as a HTTP/HTTPS URL.

### Domain object schemas

**Domain (`domain.json`)**

Note: `domain_id` is not stored in the JSON file. It is derived from the containing folder name at runtime.
Path: `PERSISTENT_STORAGE_PATH/domains/{domain_id}/domain.json`

```json
{
  "vector_store_name": "SharePoint-DOMAIN01",
  "vector_store_id": "vs_xxxxxxxxxxxxxxxxxxxxx",
  "name": "Example Domain 01",
  "description": "Description of the SharePoint site and its purpose",
  "file_sources": [ { "source_id": "...", "site_url": "...", "sharepoint_url_part": "...", "filter": "" } ],
  "sitepage_sources": [ { "source_id": "...", "site_url": "...", "sharepoint_url_part": "...", "filter": "" } ],
  "list_sources": [ { "source_id": "...", "site_url": "...", "list_name": "...", "filter": "" } ]
}
```

**File Source**
- `source_id` - unique identifier for this source within the domain
- `site_url` - full SharePoint site URL (e.g., `https://contoso.sharepoint.com/sites/ExampleSite`)
- `sharepoint_url_part` - path to document library (e.g., `/Shared Documents`)
- `filter` - optional OData filter expression

**Sitepage Source**
- `source_id` - unique identifier for this source within the domain
- `site_url` - full SharePoint site URL
- `sharepoint_url_part` - path to site pages (usually `/SitePages`)
- `filter` - optional OData filter expression

**List Source**
- `source_id` - unique identifier for this source within the domain
- `site_url` - full SharePoint site URL
- `list_name` - name of the SharePoint list
- `filter` - optional OData filter expression

**Job Metadata (returned in `start_json` and `end_json` events)**

Note: The `result` field uses the same `{ok, error, data}` format as defined in "Consistent JSON result format" section.

Example `start_json`:
```json
{
  "job_id": "jb_42",
  "state": "running",
  "source_url": "/v2/crawler/crawl?domain_id=TEST01&format=stream",
  "monitor_url": "/v2/jobs/monitor?job_id=jb_42",
  "started_utc": "2024-01-15T10:30:00.000000Z",
  "finished_utc": null,
  "last_modified_utc": "2024-01-15T10:30:05.000000Z",
  "result": null
}
```

Example `end_json`:
```json
{
  "job_id": "jb_42",
  "state": "completed",
  "source_url": "/v2/crawler/crawl?domain_id=TEST01&format=stream",
  "monitor_url": "/v2/jobs/monitor?job_id=jb_42",
  "started_utc": "2024-01-15T10:30:00.000000Z",
  "finished_utc": "2024-01-15T12:23:34.000000Z",
  "last_modified_utc": "2024-01-15T12:23:34.000000Z",
  "result": { "ok": true, "error": "", "data": {...} }
}
```

### Endpoint design decisions

**DD-E001:** Self-documentation on bare GET (no query params, including `format`). When documentation is needed, it's where the developer is working.
**DD-E002:** Action-suffixed endpoints: `/resource`, `/resource/get`, `/resource/create`, `/resource/update`, `/resource/delete`. Allows self-documentation.
**DD-E003:** Backend ships simple interactive UI. Admins need no programming skills. Changes can be implemented and tested fast and in one place.
**DD-E004:** Format param controls response: `json`, `html`, `ui` (resource root only), `stream` (long-running jobs), `raw` (file content with original Content-Type). 
**DD-E005:** Body accepts JSON or form data (content-type detection). Principle of least surprise: No need to look up documentation, it just works.
**DD-E006:** Triggering, monitoring and management of crawling and other jobs via HTTP GET requests. Allows automation via single URL calls (low technology barrier).
**DD-E007:** Semantic identifier names like `job_id`, `domain_id`, `source_id` that explicitly name the resource. Disambiguates object types and allow for actions that require multiple ids.
**DD-E008:** Semantic entity identifyers for interally created ids like `jb_[JOB_NUMBER]` for a job. Self-explanatory system: disambiguates object types, simplifies support. Exceptions: Domain ids (derived from folder name, not stored in `domain.json`) and source ids (user-defined in `domain.json`)
**DD-E009:** Plural naming for resources: `/domains`, `/vector_stores`. Exceptions possible: `/crawler`
**DD-E010:** HTTP semantics exception for `/resource/delete` endpoints: `GET [R]/delete`
**DD-E011:** Control parameters (`format`, `dry_run`) are always passed via query string.
**DD-E012:** `/create` endpoints receive all resource data including the identifier from the request body.
**DD-E013:** `/get` and `/delete` endpoints receive the resource identifier via query string.
**DD-E014:** `/update` endpoints receive the identifier via query string and update data from the body. If the endpoint supports identifier modification and the body contains a different identifier than the query string, this triggers an ID change: the resource identifier changes from the query string value to the body value, then remaining body fields are applied. Otherwise, any identifier in the body is ignored.
**DD-E015:** All textual response formats use UTF-8 encoding.
**DD-E016:** Response objects include relative backend URLs (e.g., `monitor_url`, `source_url`, `report_url`) to enable client navigation without hardcoding host/port.
**DD-E017:** `/delete` endpoints return the full resource object (same as `/get` would return) before deletion.

### Why Action-Suffixed over RESTful?

- RESTful was tried in the initial version and led to duplication of endpoints: `/query` -> `/query2`
- Hybrid API: same endpoints serve both programmatic API (JSON) and interactive UI (HTMX)
- Self-documenting: URL reflects developer intent via action and query params while still implementing HTTP semantics via POST, PUT, DELETE
- Bare `GET /resource` without params always returns documentation (consistent behavior)
- Developers can easily inspect content, try out query params and choose return types via HTTP GET in the browser without additional tooling
- All endpoints use query params (uniform parsing, generalized predictable behavior)
- Single endpoint accepts both JSON body and form data (content-type detection)
- Easy to add new action endpoints that do not map to HTTP methods: `/domains/crawl?domain_id={id}&mode=incremental`, `/domains/source?domain_id={id}`
- Simplified implementation: HTMX forms work naturally with explicit URLs

### Endpoint versioning

There are two types of endpoints:
1. Unversioned (mostly in the root)
2. Versioned (prefixed with `/v1/`, `/v2/`, etc.)

**Unversioned endpoints - Query API and OpenAI Proxy**

- Everything under `/openai/` - Necessary as the original OpenAI REST API is being proxied.
- `POST /describe` - Returns metadata describing the SharePoint content search tool, including available domains and content root (JSON format)
- `GET /describe2` - Returns metadata describing the SharePoint content search tool, including available domains and content root
  - `GET /describe2?format=json` - Get metadata in JSON format
  - `GET /describe2?format=html` - Get metadata in HTML format (default)
- `POST /query` - Execute a search query against SharePoint documents (JSON request/response)
  - Request body: `{"data": {"query": "[SEARCH_TEXT]", "vsid": "[VECTOR_STORE_ID]", "results": [MAX_RESULTS]}}`
- `GET /query2` - Endpoint self-documentation as text (UTF-8)
  - `GET /query2?query={text}&vsid={vector_store_id}` - Execute search query with HTML response (default)
  - `GET /query2?query={text}&vsid={vector_store_id}&format=json` - Execute search query with JSON response
  - `GET /query2?query={text}&vsid={vector_store_id}&results={max_results}` - Execute search query with custom result limit

**Versioned endpoints - Crawler, Job Management, and new endpoints**

Version 1 routers (untouched by this document):
- inventory router - implements everything under `/v1/inventory/`
- crawler router - implements everything under `/v1/crawler/`
- domains router - implements everything under `/v1/domains/`
- testrouter router - implements everything under `/v1/testrouter/` (streaming test endpoints: `/streaming01`, `/control`, `/operations`)
- testrouter2 router - implements everything under `/v1/testrouter2/` (V2 streaming with file-based jobs: `/streaming01`, `/monitor`, `/control`, `/jobs`)
- testrouter3 router - implements everything under `/v1/testrouter3/` (V3 streaming with reactive UI: `/streaming01`, `/monitor`, `/control`, `/jobs`)

Version 2 routers (as specified in this document):
- inventory router - implements everything under `/v2/inventory/`
- crawler router - implements everything under `/v2/crawler/`
- domains router - implements everything under `/v2/domains/`
- jobs router - implements everything under `/v2/jobs/`


### Action-Suffixed syntax uses explicit action names

**Endpoint format**
- List top-level resource: `/v2/[RESOURCE]?[PARAM_1]=[VALUE_1]&[PARAM_2]=[VALUE_2]`
- Perform action with top-level resource: `/v2/[RESOURCE]/[ACTION]?[PARAM_1]=[VALUE_1]&[PARAM_2]=[VALUE_2]`
- Perform action nested resource: `/v2/[RESOURCE]/[RESOURCE]/[ACTION]?[PARAM_1]=[VALUE_1]&[PARAM_2]=[VALUE_2]`

**Actions**
- `GET /v2/resource` -> Self-documentation (UTF-8 text)
- `GET /v2/resource?format=json` - Get all
- `GET /v2/resource/get?item_id={id}` - Get single
  - Example variant: `GET /v2/resource/get_content?item_id={id}` - Retrieve content of single item
- `POST /v2/resource/create` - Create
- `PUT /v2/resource/update?item_id={id}` - Update
  - Example variant: `PUT /v2/resource/ensure_attributes?item_id={id}` - Create or update item attributes
- `DELETE, GET /v2/resource/delete?item_id={id}` - Delete

### Query params syntax uses explicit query params for ids and data format:

**/resource** - List
- `GET /v2/resource` -> -> Self-documentation (UTF-8 text)
- `GET /v2/resource?format=json` -> JSON result with `"data": [...]`
- `GET /v2/resource?format=html` -> HTML table (nested or flat)
- `GET /v2/resource?format=ui` -> Interactive UI listing all items with [Create], [Edit] / [View], [Delete] buttons for each item if supported by endpoint

**/resource/get** - Get single
- `GET /v2/resource/get` -> -> Self-documentation (UTF-8 text)
- `GET /v2/resource/get?item_id={id}` -> JSON result with `"data": {...}`
- `GET /v2/resource/get?item_id={id}&format=json` -> JSON result with `"data": {...}`
- `GET /v2/resource/get?item_id={id}&format=html` -> HTML detail view
- `GET /v2/resource/get?format=json` -> HTTP 400: JSON error result "Missing 'item_id'."
- `GET /v2/resource/get?format=ui` -> HTTP 400: "Format 'ui' not supported".

### Common query params

**`format` query param**
- Specifies the returned data format.
- All endpoints returning data are required to support this query param.
- Endpoints are NOT required to support all available options. At least one option must be supported.
- Note: `format=json` is the default **when query params are provided**. Bare GET (no params) always returns self-documentation regardless of format support (see DD-E001).
- Available options:
  - `json` (default) -> JSON result with `"data": {...}` for Create, Get, Update, Delete actions. JSON result with `"data": [...]` for List and other action returning collections.
  - `html` -> HTML detail view (JSON converted to flat or nested HTML table)
  - `ui` -> Interactive UI listing all items with [Create], [Edit] / [View], [Delete] buttons for each item if supported by endpoint
  - `stream` ->  Server-Sent Events (SSE) stream with HTMX compatible syntax (`event:` and `data:` lines) with MIME type `Content-Type: text/event-stream`

**`dry_run` query param**
- Specifies if an action is allowed to delete or modify data.
- Used to verify the configuration and predict the result of actions that can't be undone.
- Supported by Create, Update, Delete, and endpoints that trigger long-running jobs.
- Exception: Only complex or long-running operations require `dry_run`. Simple CRUD endpoints may opt out (e.g., `/v2/domains`).
- Response uses the same schema as normal operation (no special `dry_run` flag or `would_create` fields).
- Available options:
  - `false` (default) - Allowed to delete or modify data: perform the action as specified.
  - `true` - NOT allowed to delete or modify data: simulate the action, return same response schema.

### LCGUD Endpoint Examples (format=json)

**L - List** `GET /v2/resource?format=json`
```
GET /v2/resource?format=json
Response: {"ok": true, "error": "", "data": [{...}, {...}]}
```

**C - Create** `POST /v2/resource/create` with body
```
POST /v2/resource/create?format=json
Body: {"item_id": "item1", "name": "New Item"}
Response: {"ok": true, "error": "", "data": {"item_id": "item1", "name": "New Item"}}
```

**G - Get** `GET /v2/resource/get?item_id={id}&format=json`
```
GET /v2/resource/get?item_id=item1&format=json
Response: {"ok": true, "error": "", "data": {"item_id": "item1", "name": "New Item"}}
```

**U - Update** `PUT /v2/resource/update?item_id={id}` with body
```
PUT /v2/resource/update?item_id=item1&format=json
Body: {"name": "Updated Item"}
Response: {"ok": true, "error": "", "data": {"item_id": "item1", "name": "Updated Item"}}
```

**U - Update with ID change** `PUT /v2/resource/update?item_id={old_id}` with `item_id` in body

Per DD-E014, if the body contains a different `item_id` than the query string, this triggers an ID change.

```
PUT /v2/resource/update?item_id=old_item&format=json
Body: {"item_id": "new_item", "name": "Updated Name"}
Response: {"ok": true, "error": "", "data": {"item_id": "new_item", "name": "Updated Name"}}
```

**ID change flow:**
1. Query string `item_id` = current identifier
2. Body `item_id` = new identifier
3. If current == new: normal update (no ID change)
4. If current != new:
   - Validate current exists (404 if not)
   - Validate new does not exist (400 if collision)
   - Change item identifier from current to new
   - Apply remaining body fields to item
5. Response contains final `item_id`

**D - Delete** `DELETE, GET /v2/resource/delete?item_id={id}&format=json`
```
DELETE, GET /v2/resource/delete?item_id=item1&format=json
Response: {"ok": true, "error": "", "data": {"item_id": "item1", "name": "Deleted Item"}}
```

### Use HTTP status codes for high-level success/failure

- 2xx – the operation was successfully processed (even if result is 'no-op').
  - 200 - OK
- 4xx – client did something wrong (validation error, missing field, bad state).
  - 400 - Bad Request for invalid parameters
  - 404 - Not Found for missing objects
- 5xx – server or unknown error
  - 500 - Internal Server Error for unforseen exceptions and server errors

### Consistent JSON result format

- Endpoints that return data guarantee a minimal JSON format. 
- Streaming endpoints (`format=stream`) and self-documentation endpoints are excluded from this guarantee.

**Core principles**
- Every response is structured JSON when `format=json` (or default JSON).
- HTML/UI formats are just renderings of the same structured JSON. When `format=html` or `format=ui`, the server still constructs the same {ok,error,data} object internally.
- HTTP status code conveys broad class; JSON `error` attribute contains detailed error message.

**Consistent minimal pattern:**
- `ok` - `true` for success, `false` for failure
- `error` - what went wrong (string)
- `data` - success: result, failure: best effort result (may be {} or [] if nothing is available)

**Success Examples:**
```
{ "ok": true, "error": "", "data": {...} }
or
{ "ok": true, "error": "", "data": [...] }
```

**Failure Examples:**
```
{ "ok": false, "error": "<error_message>", "data": {} }
or 
{ "ok": false, "error": "<error_message>", "data": [] }
or 
{ "ok": false, "error": "<error_message>", "data": { "vector_store_id": "vs_2343453245", ... } }
or 
{ "ok": false, "error": "<error_message>", "data": [ {"vector_store_id": "vs_2343453245", ... }, {"vector_store_id": "vs_3872455464", ... }, ... } }
```

### Streaming and job files

The `format=stream`query param combines the management and monitoring of long-running jobs with logging.
Endpoints that support `format=stream` write their event stream into job files into the local storage.
Long-running jobs can be monitored, paused, resumed, cancelled by independent processes via the common file system.

#### Streaming endpoint result format

- Format: Server-Sent Events (SSE) stream with HTMX compatible syntax
- MIME type: `Content-Type: text/event-stream`
- Encoding: `UTF-8`
- Support of `event:` and `data:` lines. See HTMX Server Sent Event (SSE) Extension documentation: https://htmx.org/extensions/sse/
- Each event is terminated by an empty line (**LF** or **CRLF**)
- Each stream starts with a `start_json` event and ends with a `end_json` event
- Even if the streaming job is cancelled, an `end_json` event containing the status and result is guaranteed (except on crashes)
- Between the `start_json` and `end_json` events, `log` and `state_json` events are allowed
- `state_json` events are emitted when job state changes (pause/resume/cancel) for UI synchronization
- The `start_json` event contains a JSON object with the job metadata

Example *stream output* for `start_json` event with job metadata as JSON
```
event: start_json
data: { "job_id": "jb_2", "state": "running", "source_url": "/v2/crawler/crawl?domain_id=TEST01&format=stream", "monitor_url": "/v2/jobs/monitor?job_id=jb_2", "started_utc": "2024-01-15T10:30:00.000000Z", "finished_utc": null, "last_modified_utc": "...", "result": null}
data: { "job_id": "jb_2", "state": "running", "source_url": "/v2/crawler/crawl?domain_id=TEST01&format=stream", "last_modified_utc": "..."}

```

Example *multiline stream output* for `start_json` event with job metadata as JSON
```
event: start_json
data: {
data:   "job_id": 'jb_2'
data:   "state": "running",
data:   "source_url": "/v2/crawler/crawl?domain_id=TEST01&format=stream",
data:   "monitor_url": "/v2/jobs/monitor?job_id=jb_2",
data:   "started_utc": "2024-01-15T10:30:00.000000Z",
data:   "finished_utc": null
data:   "result": null
data: }

```

Example *stream output* for `log` event with single line of text
```
event: log
data: [ 2 / 4 ] Processing file 'document.docx'...

```

Example *stream output* for `state_json` event (emitted on pause/resume/cancel)
```
event: state_json
data: {"state": "paused", "job_id": "jb_42"}

```

Valid `state` values: `running` (on resume), `paused` (on pause), `cancelled` (on cancel)

Example *multiline stream output* for `end_json` event with job metadata as JSON
```
event: end_json
data: {
data:   "job_id": 'jb_2'
data:   "source_url": "/v2/crawler/crawl?domain_id=TEST01&format=stream",
data:   "state": "completed",
data:   "started_utc": "2024-01-15T10:30:00.000000Z",
data:   "finished_utc": "2024-01-15T12:23:34.000000Z",
data    "result": { "ok": true, "error": "", "data": {...} }
data: }

```

Example *multiline stream output* for `log` event multiple lines of text
```
event: log
data: Total files: 146 using 624.95 MB.
data: ------------------------------------------------------------------------------------------------
data: Index | ID                               | Filename                                 | Size      
data: ----- | -------------------------------- | ---------------------------------------- | ----------
data: 00000 | assistant-86Bsp9rZQevLksitUBBPEn | GlobalEnergyReview2025.pdf               | 929.32 KB 
data: 00001 | assistant-3t52LP8M4t7iWecR2DYW7w | THEGRI~1.PDF                             | 3.04 MB   
data: 00002 | assistant-B8XZtxgQe4aSQwsF5GcbdH | EnergyOverview.pdf                       | 202.80 KB 

```

#### Job file format

Job files serve two purposes:
1. **State tracking** - The file extension indicates current job state
2. **Stream storage** - The file content is the complete SSE stream (identical to `/v2/jobs/monitor?job_id={id}&format=stream` output)

**File Content Format (SSE stream):**

Note: Format `[ current / total ]` after `data:` is mandatory when logging steps or collections of known size. This way the HTTP client can detect progress at any time.

```
event: start_json
data: {"job_id": "jb_42", "state": "running", "source_url": "...", "monitor_url": "...", "started_utc": "...", "finished_utc": null, "last_modified_utc": "...", "result": null}

event: log
data: [ 1 / 2 ] Processing file 'document1.pdf'...

event: log
data:   OK.

event: log
data: [ 2 / 2 ] Processing file 'document2.docx'...

event: log
data:   OK.

event: end_json
data: {"job_id": "jb_42", "state": "completed", "source_url": "...", "monitor_url": "...", "started_utc": "...", "finished_utc": "...", "last_modified_utc": "...", "result": {"ok": true, "error": "", "data": {...}}}

```

**Disk Write Optimization:**

To prevent heavy disk I/O when emitting many log events, implementations should batch log events before writing to the job file:
- `PERSISTENT_STORAGE_LOG_EVENTS_PER_WRITE` (default: 5) - Number of log events to buffer before flushing to disk
- The buffer is always flushed immediately for `start_json` and `end_json` events
- The buffer is also flushed when checking for control files (pause/cancel requests)

**Filename Format:** `[TIMESTAMP]_[[ENDPOINT_ACTION]]_[[JB_ID]]_[[OBJECT_ID_OR_NAME]].[state]`
**Example:** `2025-11-26_14-20-30_[crawl]_[jb_42]_[TEST01].running`
**Example without object id:** `2025-11-26_14-20-30_[global_cleanup]_[jb_42].running`

**Components:**
- `[TIMESTAMP]` - When the job was created (YYYY-MM-DD_HH-MM-SS)
- `[ENDPOINT_NAME]` - Name of the streaming endpoint
- `[JB_ID]` - Global sequential streaming job ID
- `[OBJECT_ID_OR_NAME]` - Optional: ID or name of object being processed

**Job States:**
- `.running` - Active job, contains log content
- `.completed` - Finished job
- `.paused` - Paused job
- `.cancelled` - Cancelled job

**Job Control States:**
- `.pause_requested` - Control: request pause
- `.resume_requested` - Control: request resume
- `.cancel_requested` - Control: request cancel

**Control File Lifecycle:**

Control files are ephemeral signals. The job process is responsible for cleanup:

1. Job process periodically checks for control files matching its `jb_id`
2. When a control file is detected, the job:
   a. Logs the control action (e.g., "Pause requested, pausing...")
   b. **Deletes the control file immediately**
   c. Transitions to the new state (renames job file extension)

Example - Pause flow:
```
1. Control endpoint creates: [jb_42].pause_requested
2. Job detects .pause_requested file
3. Job deletes .pause_requested file
4. Job renames .running -> .paused
```

Example - Cancel while paused:
```
1. Control endpoint creates: [jb_42].cancel_requested
2. Job detects .cancel_requested file
3. Job deletes .cancel_requested file
4. Job deletes .paused file
5. Job creates .cancelled file with final state
```

**Valid State Transitions:**
- `running` -> `paused`, `cancelled`, `completed`
- `paused` -> `running` (via resume), `cancelled`
- `completed` -> (terminal, no transitions)
- `cancelled` -> (terminal, no transitions)

**Job Files Location**

The folder structure reflects how resources are exposed as routers and endpoints.

```
PERSISTENT_STORAGE_PATH/jobs/
├── inventory/
│   └── vector_stores/
│       ├── 2025-11-26_14-20-30_[create]_[jb_1]_[VS01].completed                       # Completed job
│       ├── 2025-11-26_14-21-00_[replicate]_[jb_2]_[vs_123].cancelled                  # Cancelled job
│       ├── 2025-11-26_14-22-00_[delete_failed_files]_[jb_3]_[vs_456].running          # Running job
│       ├── 2025-11-26_14-24-00_[delete_failed_files]_[jb_4]_[vs_456].pause_requested  # Control file
└── crawler/
    ├── 2025-11-26_14-25-00_[crawl]_[jb_5]_[DOMAIN01].completed                        # Completed job
    ├── 2025-11-26_14-25-00_[crawl]_[jb_6]_[DOMAIN01].paused                           # A paused job 
    └── 2025-11-26_14-26-00_[crawl]_[jb_6].resume_requested                            # Control file
```

**`jb_id` Generation Algorithm**

Format: `jb_[NUMBER]` where `[NUMBER]` is an ascending integer starting with 1 

1. Scan all files in `PERSISTENT_STORAGE_PATH/jobs/**/*` (recursive)
2. Filter files with valid extensions (`.running`, `.completed`, `.cancelled`, `.paused`)
3. Sort by modification time (newest first)
4. Take the first 1000 files (most recent)
5. Extract `jb_id_number` from filenames using regex pattern
6. Find maximum `jb_id_number`
7. Return `max_jb_id_number + 1` (or `1` if no files found)

**Why limit to 1000 files?**
- Performance: Avoids scanning entire history on systems with many completed jobs
- Correctness: Recent files contain the highest IDs; older files are irrelevant for max calculation
- The limit is intentionally high (1000) to handle burst scenarios safely

**Race Condition Handling**

If two workers generate the same `job_id` simultaneously:

```python
# Worker 1: job_id = 'jb_1', creates file successfully
# File: 2025-11-26_14-20-30_[crawl]_[jb_1]_[TEST01].running
success = create_streaming_job_file(..., job_number=1)  # Returns True

# Worker 2: job_id = 'jb_1', file already exists (same timestamp collision)
success = create_streaming_job_file(..., job_number=1)  # Returns False

# Worker 2 retries: job_id = 'jb_1', job_number=2
job_number = generate_streaming_job_number(...)  # Returns 2 (scans again)
# File: 2025-11-26_14-20-30_[crawl]_[jb_2]_[TEST02]
success = create_streaming_job_file(..., job_number=2)  # Returns True
```

#### Controlling jobs via endpoints

Long-running jobs are controlled via the `/v2/jobs/` router. 

**Control Operation**

```
GET /v2/jobs/control?job_id={job_id}&action={action}
```

- Available actions:
  - `cancel` - requests cancellation of the job
  - `pause` - requests the job to be paused
  - `resume` - requests the job to be resumed

**Monitoring**

```
GET /v2/jobs/monitor?job_id={job_id}&format=stream
```

Returns full stream (from start) as Server-Sent Events (SSE), MIME type: `Content-Type: text/event-stream`, UTF-8 encoded

## Endpoint specification

### Self-Documentation Format

Two types of self-documentation exist:

1. **Router root endpoints** (e.g., `/v2/demorouter1`, `/v2/inventory`) return **minimalistic HTML** with:
   - Title and description
   - List of available endpoints with links to each supported format
   - Back navigation link
   - Required elements for consistent look and feel:
     - Stylesheet: `/static/css/styles.css`
     - Script: `/static/js/htmx.js` (include for HTMX interactivity)
     - Standard HTML5 doctype: `<!doctype html><html lang="en">`
     - Viewport meta tag for responsive design

2. **Action endpoints** (e.g., `/v2/demorouter1/demo_endpoint`, `/v2/domains/get`) return **plain text (UTF-8)** with:
   - Docstring content with `{router_prefix}` placeholder replaced at runtime

The `router_prefix` variable is set via `set_config()` when the router is initialized.

**Recommended module-level constants:**

```python
router = APIRouter()
config = None
router_prefix = None
router_name = "demorouter1"  # Used for job file folder naming and route decorators
```

- `router_prefix` - Injected via `set_config()`, used for URL generation in self-documentation and UI links
- `router_name` - Constant matching the router's identity, used for:
  - Route decorators: `@router.get(f"/{router_name}")` (f-string required)
  - `StreamingJobWriter` parameter to organize job files by router (e.g., `jobs/demorouter1/`)
  - Self-documentation f-strings: `f"{router_prefix}/{router_name}"`

Using a `router_name` constant avoids hardcoding the router name in multiple places and ensures consistency.

**Router root endpoint pattern (HTML):**
```python
from fastapi.responses import HTMLResponse

@router.get(f"/{router_name}")
async def demorouter_root(request: Request):
  """Router root docstring for reference."""
  return HTMLResponse(f"""
<!doctype html><html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Demo Router</title>
  <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
  <h1>Demo Router</h1>
  <p>Description of the router and its purpose.</p>

  <h4>Available Endpoints</h4>
  <ul>
    <li><a href="{router_prefix}/demorouter1/demo_endpoint">{router_prefix}/demorouter1/demo_endpoint</a> - Process files (<a href="{router_prefix}/demorouter1/demo_endpoint?format=stream&files=5">Stream</a>)</li>
  </ul>

  <p><a href="/">← Back to main page</a></p>
</body>
</html>
""")
```

**Action endpoint pattern (plain text):**
```python
import textwrap
from fastapi.responses import PlainTextResponse

# Module-level example data for self-documentation
example_item_json = """
{
  "item_id": "demo_abc123",
  "name": "Example Item",
  "version": 1
}
"""

@router.get(f'/{router_name}/demo_endpoint')
async def demo_endpoint(request: Request):
  """
  Description of the endpoint.
  
  Parameters:
  - param1: Description
  - format: Response format (json, html)
  
  Examples:
  {router_prefix}/{router_name}/demo_endpoint?param1=value&format=json

  Example item:
  {example_item_json}
  """
  # Return documentation if no params
  if len(request.query_params) == 0:
    doc = textwrap.dedent(demo_endpoint.__doc__).replace("{router_prefix}", router_prefix).replace("{router_name}", router_name).replace("{example_item_json}", example_item_json.strip())
    return PlainTextResponse(doc, media_type="text/plain; charset=utf-8")
  # ... handle request
```

### Shorthand specification notation

This specification uses a shorthand notation to make it easy for AI code generation to
- quickly implement common endpoint features
- verify existing implementation against this specification

**Format**
[ACTION_LIST]: `[RESOURCE]` - [DESCRIPTION]

**Explanation**
- [ACTION_LIST] - a sequence of uppercase action letters, followed by lowercase response format letters in parentheses.
  - Example: `G(jh)` -> GET action supporting JSON and HTML as return formats
  - Example: `L(jhu)` -> LIST action supporting JSON, HTML, UI as return formats
  - Example: `L(jhus)` -> LIST action supporting JSON, HTML, UI, and Server-Sent Events (SSE) stream as return formats
  - Example: `U(js)` -> LIST action supporting JSON and Server-Sent Events (SSE) stream as return formats
  - No space allowed between action and format letters
  - Available common actions:
    - L -> implements List via `GET [R]/` -> returns collection of items
    - C -> implements Create via `POST [R]/create` -> returns created item
    - G -> implements Get single via `GET [R]/get` -> returns single item
    - U -> implements Update via `PUT [R]/update` -> returns modified item
    - D -> implements Delete via `DELETE [R]/delete` and `GET [R]/delete` -> returns deleted item
    - X -> implements custom action via `GET [R]/[action_name]` -> for stream-only or non-CRUD endpoints (e.g., `/selftest`, `/create_demo_items`)
  - Available common formats:
    - `...(j)` -> supports `format=json` (default when object id given)
    - `...(h)` -> supports `format=html`
    - `...(u)` -> supports `format=ui`
    - `...(s)` -> supports `format=stream`
    - `...(r)` -> supports `format=raw`
	- `...()`  -> supports only self-documentation with `GET [R]/`

**Examples**

Example 1: This specification
L(jhu)C(j)G(jh)U(j)D(jh): `/v2/icecreams` - Icecream stock

translates into this implemented behavior:
- `GET /v2/icecreams` - Self-documentation of `icecreams` endpoint with all actions
- `GET /v2/icecreams?format=json` -> JSON result with `"data": [...]`
- `GET /v2/icecreams?format=html` -> HTML detail view
- `GET /v2/icecreams?format=ui` -> Interactive UI listing all icecreams with [Create], [Edit], [Delete] buttons for each item

- `GET /v2/icecreams/create` - Self-documentation of `create` action
- `POST /v2/icecreams/create` with JSON or form data -> Creates new icecream item and returns it as JSON result with `"data": {...}`
- `POST /v2/icecreams/create?dry_run=true` with JSON or form data -> [HERE]
- `POST /v2/icecreams/create?format=json` with JSON or form data -> Creates new icecream item and returns it as JSON result with `"data": {...}`
- `POST /v2/icecreams/create?format=html` with JSON or form data -> HTTP 400: "Format 'html' not supported."
- `PUT /v2/icecreams/create` with JSON or form data -> HTTP 400: "HTTP method 'PUT' not supported."

- `GET /v2/icecreams/get` - Self-documentation of `get` action
- `GET /v2/icecreams/get?icecream_id={id}` -> JSON result with `"data": {...}`
- `GET /v2/icecreams/get?icecream_id={id}&format=json` -> JSON result with `"data": {...}`
- `GET /v2/icecreams/get?icecream_id={id}format=html` -> HTML detail view
- `GET /v2/icecreams/get?icecream_id={id}format=ui` -> HTTP 400: "Format 'ui' not supported."
- `GET /v2/icecreams/get?icecream_id={id}format=stream` -> HTTP 400: "Format 'stream' not supported."

- `GET /v2/icecreams/update` - Self-documentation of `update` action
- `PUT /v2/icecreams/update` with JSON or form data -> Updates icecream item and returns it as JSON result with `"data": {...}`
- `PUT /v2/icecreams/update?format=json` with JSON or form data -> Updates icecream itemand returns it as JSON result with `"data": {...}`
- `PUT /v2/icecreams/update?format=html` -> HTTP 400: "Format 'html' not supported."
- `POST /v2/icecreams/update` with JSON or form data -> HTTP 400: "HTTP method 'POST' not supported."
- `PATCH /v2/icecreams/update` with JSON or form data -> HTTP 400: "HTTP method 'PATCH' not supported."

- `GET /v2/icecreams/delete` - Self-documentation of `delete` action
- `DELETE, GET /v2/icecreams/delete?icecream_id={id}` -> Deletes icecream item and returns it as JSON result with `"data": {...}`
- `DELETE, GET /v2/icecreams/delete?icecream_id={id}&format=json` -> Deletes icecream item and returns it as JSON result with `"data": {...}`
- `DELETE, GET /v2/icecreams/delete?icecream_id={id}&format=html` -> Deletes icecream item and returns it as HTML detail view
- `DELETE, GET /v2/icecreams/delete?icecream_id={id}format=stream` -> HTTP 400: "Format 'stream' not supported."
- `PATCH /v2/icecreams/delete?icecream_id={id}` with JSON or form data -> HTTP 400: "HTTP method 'PATCH' not supported."

Example 2: This specification
L(jhu)G(jh): `/v2/icecreams/flavours` - Available icecream flavours

translates into this implemented behavior:
- `GET /v2/icecreams/flavours` - Self-documentation of `flavours` endpoint
- `GET /v2/icecreams/flavours?format=json` -> JSON result with `"data": [...]`
- `GET /v2/icecreams/flavours?format=html` -> HTML detail view
- `GET /v2/icecreams/flavours?format=ui` -> Interactive UI listing all items with [View] button for each item
- `GET /v2/icecreams/flavours/get`  - Self-documentation of `get` endpoint
- `GET /v2/icecreams/flavours/get?flavour_id={id}` -> JSON result with `"data": {...}`
- `GET /v2/icecreams/flavours/get?flavour_id={id}&format=json` -> JSON result with `"data": {...}`
- `GET /v2/icecreams/flavours/get?flavour_id={id}&format=html` -> HTML detail view

### Specification of endpoints

Additions and exceptions are listed below the endpoint specification.
Create, Update, Delete operations usually support the `format=stream` query param to ensure logging of changes.

**Inventory**
- L(u): `/v2/inventory` - UI for managing inventory 
- L(jhu)G(jh)D(jhs): `/v2/inventory/files` - Files in the connected Open AI backend
- L(jhu)C(jhs)G(jh)U(jhs)D(jhs): `/v2/inventory/vector_stores` - Vector stores in the connected Open AI backend
  - `DELETE, GET /v2/inventory/vector_stores/delete?vector_store_id={id}&mode=[default|with_files]`
    - `mode=default` (default) - deletes vector store
    - `mode=with_files` - removes all files referenced by the vector store globally and then deletes vector store
  - `GET /v2/inventory/vector_stores/replicate?source_vector_store_ids={id1},{id2},...&target_vector_store_ids={id3},{id4},...&remove_target_files_not_in_sources=[true|false]`
    - Collects all files in the source vector stores (incl. de-duplication) and ensures all target vector stores contain all collected files
    - `source_vector_store_ids={id1},{id2},...` - one or many source vector stores
	  - `target_vector_store_ids={id3},{id4},...` - one or many target vector stores
	  - `remove_target_files_not_in_sources=false` (default) - only adds missing files to the target vector stores
	  - `remove_target_files_not_in_sources=true` - after adding missing files, removes all files in the targets that are not part of the files collected from sources
- L(jh)G(jh)D(jhs): `/v2/inventory/vector_stores/files` - Embedded files in vector stores in the connected Open AI backend
  - `DELETE, GET /v2/inventory/vector_stores/files/delete?vector_store_id={id}&file_id={id}&mode=[default|delete_globally]`
    - `mode=default` (default) - removes file reference from vector store
    - `mode=delete_globally` - removes file reference from vector store and then deletes file globally
- L(jhu)C(jhs)G(jh)U(jhs)D(jhs): `/v2/inventory/assistants` - Assistants in the connected Open AI backend
  - `DELETE, GET /v2/inventory/assistants/delete?assistant_id={id}&mode=[default|with_files]`
    - `mode=default` (default) - deletes assistant
    - `mode=with_files` - if vector store is attached: deletes vector files globally, then vector store, then assistant
- L()C(jh)G(jh)D(jh): `/v2/inventory/responses` - Model responses in the connected Open AI backend
  - `DELETE, GET /v2/inventory/responses/delete?response_id={id}&mode=[default|with_conversation]`
    - `mode=default` (default) - deletes model response
    - `mode=with_conversation` - if response has stored conversation: deletes stored conversation, then model response

**Domains**
- L(jhu)C(jh)G(jh)U(jh)D(jh): `/v2/domains` - Knowledge domains to be used for crawling and semantic search
  - Exception: no `dry_run` flag needed here
  - `PUT /v2/domains/update?domain_id={id}` supports rename via `domain_id` in body (per DD-E014)
- X(s): `/v2/domains/selftest` - Self-test for domains CRUD operations
  - Only supports `format=stream`
  - Tests: error cases, create, create with sources, update, rename (ID change), delete
  - Result: `{ok, error, data: {passed, failed, passed_tests, failed_tests}}`

**Crawler**
- L(u): `/v2/crawler` - UI for crawling SharePoint sites and see current status
- L(jhs): `/v2/crawler/download_data?domain_id={id}&mode=[full|incremental]&scope=[all|files|lists|sitepages]&source_id={id}&dry_run=false`
  - Downloads data from source to local storage
  - `domain_id` - domain to be crawled
  - `mode=full` (default) - performs full crawl of domain, deletes all previously downloaded files in local storage first  
  - `mode=incremental` - performs incremental crawl, fallback to `mode=full` if no `files_map.csv` file found
  - `scope=all` (default) - downloads all: files, lists, sitepages
  - `scope=files` - downloads only files, operating ONLY on `01_files/` local storage
  - `scope=lists` - downloads only lists, operating ONLY on `02_lists/` local storage
  - `scope=sitepages` - downloads only sitepages, operating ONLY on `03_sitepages/` local storage
  - Optional: `source_id={id}` - if a scope other than `all` is given, the action can be further limited to individual sources
  - `dry_run=false` (default) - performs action as specified
  - `dry_run=true` - simulates action without writing / modifying data
- L(jhs): `/v2/crawler/process_data?domain_id={id}&mode=[full|incremental]&scope=[all|files|lists|sitepages]&source_id={id}&dry_run=false`
  - Performs preprocessing of downloaded data
  - `domain_id` - domain to be crawled
  - `mode=full` (default) - performs full processing of domain, deletes all previously processed files in local storage first
  - `mode=incremental` - performs incremental processing, fallback to `mode=full` if no `files_map.csv` file found
  - `scope=all` (default) - process all: files, lists, sitepages
  - `scope=files` - processes only files (nothing implemented at the moment), operating ONLY on `01_files/` local storage
  - `scope=lists` - processes only lists, operating ONLY on `02_lists/` local storage
  - `scope=sitepages` - processes only sitepages, operating ONLY on `03_sitepages/` local storage
  - Optional: `source_id={id}` - if a scope other than `all` is given, the action can be further limited to individual sources
  - `dry_run=false` (default) - performs action as specified
  - `dry_run=true` - simulates action without writing / modifying data
- L(jhs): `/v2/crawler/embed_data?domain_id={id}&vector_store_id={id}&mode=[full|incremental]&scope=[all|files|lists|sitepages]&source_id={id}&dry_run=false`
  - Performs embedding of processed data by uploading files to the Open AI file storage and then adding them to a vector store
  - `domain_id` - domain to be crawled
  - Optional: `vector_store_id` - embed files into this vector store, ignoring configured domain vector store in `domain.json`
  - `mode=full` (default) - performs full embedding of processed files
  - `mode=incremental` - performs incremental embedding (only changes)
  - `scope=all` (default) - embeds all: files, lists, sitepages
  - `scope=files` - embeds only files, operating ONLY on `01_files/` local storage
  - `scope=lists` - embeds only lists, operating ONLY on `02_lists/` local storage
  - `scope=sitepages` - embeds only sitepages, operating ONLY on `03_sitepages/` local storage
  - Optional: `source_id={id}` - if a scope other than `all` is given, the action can be further limited to individual sources
  - `dry_run=false` (default) - performs action as specified
  - `dry_run=true` - simulates action without writing / modifying data
- L(jhs): `/v2/crawler/crawl?domain_id={id}&vector_store_id={id}&mode=[full|incremental]&scope=[all|files|lists|sitepages]&source_id={id}&dry_run=false`
  - Performs the following steps: 1) download, 2) processing, 3) embedding
  - `domain_id` - domain to be crawled
  - Optional: `vector_store_id` - embed files into this vector store, ignoring configured domain vector store in `domain.json`
  - `mode=full` (default) - performs full crawl
  - `mode=incremental` - performs incremental crawl (only changes)
  - `scope=all` (default) - crawls all: files, lists, sitepages
  - `scope=files` - crawls only files, operating ONLY on `01_files/` local storage
  - `scope=lists` - crawls only lists, operating ONLY on `02_lists/` local storage
  - `scope=sitepages` - crawls only sitepages, operating ONLY on `03_sitepages/` local storage
  - Optional: `source_id={id}` - if a scope other than `all` is given, the action can be further limited to individual sources
  - `dry_run=false` (default) - performs action as specified
  - `dry_run=true` - simulates action without writing / modifying data
  - Creates report archive after completion (see `_V2_SPEC_REPORTS.md`)
- X(jhs): `/v2/crawler/cleanup_metadata?domain_id={id}` - Remove stale entries from `files_metadata.json`
  - Removes entries where `openai_file_id` no longer exists in any vector store
  - Removes entries where `sharepoint_unique_file_id` no longer exists in any `vectorstore_map.csv`

**Jobs**
- L(jhu)G(jh)D(jh): `/v2/jobs` - Manage long-running jobs that are triggered by other endpoints (crawler, inventory)
  - `DELETE, GET /v2/jobs/delete` - endpoint does intentionally not support streaming
  - `GET /v2/jobs/get?job_id={id}`  -  Return job metadata with status in same format as in `start_json` event of the stream
- L(): `/v2/jobs/control?job_id={id}&action=[pause|resume|cancel]`
  - `GET /v2/jobs/control?job_id={id}&action=pause` - Requests the job to be paused
  - `GET /v2/jobs/control?job_id={id}&action=resume` - Requests the job to be resumed
  - `GET /v2/jobs/control?job_id={id}&action=cancel` - Requests the job to be cancelled
  - `GET /v2/jobs/control?job_id={id}&action=cancel&force=true` - Force cancels a stalled job (directly renames .running -> .cancelled)
  - Error handling:
    - HTTP 404 if `job_id` does not exist: "Job 'jb_42' does not exist."
    - HTTP 400 if `action` is missing or invalid: "Param 'action' is missing." or "Invalid value '<value>' for 'action' param."
    - HTTP 400 if job is in terminal state (`completed`, `cancelled`): "Job '<job_id>' is already completed.", "Job '<job_id>' is already cancelled."
    - HTTP 400 if action is invalid for current state (e.g., `resume` on a `running` job): "Cannot resume running job '<job_id>'."
- L(jhs): `/v2/jobs/monitor?job_id={id}` - Monitor long-running jobs
  - `GET /v2/jobs/monitor?job_id={id}&format=json` -> JSON `{ [JOB_METADATA], "log" : "[LAST_LOG_EVENT_DATA]"}`
  - `GET /v2/jobs/monitor?job_id={id}&format=html` -> JSON converted to nested HTML table
  - `GET /v2/jobs/monitor?job_id={id}&format=stream` -> Full stream (from first event) as Server-Sent Events
- L(jh): `/v2/jobs/results?job_id={id}` - Return `result` JSON from `end_json` event of the stream

**Reports**
- L(jhu)G(jh)D(j): `/v2/reports` - Report archives for auditing and debugging (see `_V2_SPEC_REPORTS.md`)
  - `GET /v2/reports?type={type}` - Filter by report type (crawl, site_scan)
  - `GET /v2/reports/get?report_id={id}` - Get report metadata (report.json content)
- X(jhr): `/v2/reports/file?report_id={id}&file_path={path}` - Get specific file from report archive
  - `format=raw` (default) - Returns file content with appropriate Content-Type
  - `format=json` - Returns file content wrapped in JSON result
  - `format=html` - Returns file content as HTML
- X(): `/v2/reports/download?report_id={id}` - Download report archive as ZIP
  - Returns ZIP file with Content-Disposition header

**Local Storage**
- L(jhu)G(j): `/v2/local_storage` - Browse files and folders in the persistent storage path
  - `GET /v2/local_storage` -> Self-documentation (UTF-8 text)
  - `GET /v2/local_storage?format=json` -> JSON result with root directory listing `{"ok": true, "error": "", "data": [...]}`
  - `GET /v2/local_storage?format=ui` -> Interactive UI with folder tree navigation
  - `GET /v2/local_storage/get` -> Self-documentation (UTF-8 text)
  - `GET /v2/local_storage/get?path={relative_path}&format=json` -> JSON listing of file/folder at path (contents if folder, metadata if file)
  - Note: Read-only. No create, update, or delete operations exposed via this router

### Endpoint return formats

#### `/v2/jobs?format=json`


Returns standard JSON result where `data` is an array of job objects:
```json
{
  "ok": true,
  "error": "",
  "data": [
    {"job_id": "jb_44", "state": "running", "source_url": "...", "monitor_url": "...", "started_utc": "...", "finished_utc": null, "last_modified_utc": "...", "result": null},
    {"job_id": "jb_42", "state": "completed", "source_url": "...", "monitor_url": "...", "started_utc": "...", "finished_utc": "...", "last_modified_utc": "...", "result": {"ok": true, "error": "", "data": {...}}}
  ]
}
```

Each job object uses the same schema as `start_json`/`end_json` events:
- For running/paused jobs: `finished_utc` and `result` are null
- For completed/failed/cancelled jobs: `finished_utc` and `result` are populated

#### `/v2/jobs/get?job_id={id}&format=json`

Returns standard JSON result where `data` is a single job object:
```json
{
  "ok": true,
  "error": "",
  "data": {
    "job_id": "jb_42",
    "state": "running",
    "source_url": "/v2/crawler/crawl?domain_id=DOMAIN01&format=stream",
    "monitor_url": "/v2/jobs/monitor?job_id=jb_42",
    "started_utc": "2025-01-15T14:00:00.000000Z",
    "finished_utc": null,
    "last_modified_utc": "2025-01-15T14:00:05.000000Z",
    "result": null
  }
}
```

#### `/v2/jobs/control?job_id={id}&action={action}`

Returns standard JSON result confirming the control action was requested:
```json
{"ok": true, "error": "", "data": {"job_id": "jb_42", "action": "pause", "message": "Pause requested for job 'jb_42'."}}
```

#### `/v2/jobs/control?job_id={id}&action=cancel&force=true`

Force cancels a stalled job by directly renaming the job file from `.running` to `.cancelled`. Used when the job process has crashed and is no longer checking for control files. Also cleans up any lingering control files.

```json
{"ok": true, "error": "", "data": {"job_id": "jb_42", "action": "cancel", "force": true, "message": "Job 'jb_42' force cancelled."}}
```

#### `/v2/jobs/monitor?job_id={id}&format=json`

- Returns standard JSON result with job metadata and last log line.
- The `data` in `result` can be a JSON object or JSON array.

**Running job:**
```json
{"ok": true, "error": "", "data": {"job_id": "jb_42", "state": "running", "source_url": "...", "monitor_url": "...", "started_utc": "...", "finished_utc": null, "last_modified_utc": "...", "result": null, "log": "[ 15 / 20 ] Processing 'document_015.pdf'..."}}
```

**Paused job:**
```json
{"ok": true, "error": "", "data": {"job_id": "jb_42", "state": "paused", "source_url": "...", "monitor_url": "...", "started_utc": "...", "finished_utc": null, "last_modified_utc": "...", "result": null, "log": "  Pause requested, pausing..."}}
```

**Completed job:**
```json
{"ok": true, "error": "", "data": {"job_id": "jb_42", "state": "completed", "source_url": "...", "monitor_url": "...", "started_utc": "...", "finished_utc": "...", "last_modified_utc": "...", "result": {"ok": true, "error": "", "data": {...}}, "log": "  OK."}}
```

**Cancelled job:**
```json
{"ok": true, "error": "", "data": {"job_id": "jb_42", "state": "cancelled", "source_url": "...", "monitor_url": "...", "started_utc": "...", "finished_utc": "...", "last_modified_utc": "...", "result": {"ok": false, "error": "Cancelled by user.", "data": {...}}, "log": "  Cancel requested, stopping..."}}
```

#### `/v2/jobs/monitor?job_id={id}&format=stream`

Returns Server-Sent Events stream (Content-Type: `text/event-stream`):
```
event: start_json
data: {"job_id": "jb_42", "state": "running", "source_url": "...", "monitor_url": "...", "started_utc": "...", "finished_utc": null, "last_modified_utc": "...", "result": null}

event: log
data: [ 1 / 20 ] Processing 'document_001.pdf'...

event: log
data:   OK.

event: log
data: [ 2 / 20 ] Processing 'document_002.pdf'...

event: end_json
data: {"job_id": "jb_42", "state": "completed", "source_url": "...", "monitor_url": "...", "started_utc": "...", "finished_utc": "...", "last_modified_utc": "...", "result": {"ok": true, "error": "", "data": {...}}}

```

#### `/v2/jobs/results?job_id={id}&format=json`

Returns standard JSON result where `data` is the `result` object from `end_json`:
```json
{"ok": true, "error": "", "data": {...}}
```

Returns error if job is not in terminal state ('completed' or 'cancelled'):
```json
{"ok": false, "error": "Results not available. Job 'jb_42' state is 'running'.", "data": {}}
```

### Crawling Process

See `_V2_SPEC_CRAWLER.md` for complete crawling process specification including:
- Local storage structure and folder layout
- Map file definitions (`sharepoint_map.csv`, `files_map.csv`, `vectorstore_map.csv`)
- Source-specific processing (file_sources, list_sources, sitepage_sources)
- Download, process, and embed data steps
- Complete list of edge cases (A1-A16, B1-B7, C1-C5, D1-D6, E1-E6)
- Edge case handling mechanism using `sharepoint_unique_file_id`
- Integrity check and recovery procedures
- `files_metadata.json` update logic

## Logging Specification

This section specifies the unified logging system for both non-streaming and streaming endpoints.

### Functional Requirements

**V2LG-FR-01: Unified Logger Class**
- Single `MiddlewareLogger` class handles all endpoint logging
- Three methods: `log_function_header()`, `log_function_output()`, `log_function_footer()`
- Replaces separate `log_data` dict pattern with stateful object

**V2LG-FR-02: Nested Function Support**
- Logger tracks nesting depth via internal counter
- Same logger instance passed to nested function calls
- Outer function controls inner function logging behavior

**V2LG-FR-03: Configurable Inner Function Logging**
- `log_inner_function_headers_and_footers` property controls if nested START/END lines are logged
- When False: inner `log_function_header()` and `log_function_footer()` produce no output
- `log_function_output()` always produces output regardless of nesting depth

**V2LG-FR-04: Indentation for Nested Logs**
- `inner_log_indentation` property specifies spaces per nesting level (default: 2)
- Indentation applied to MESSAGE portion only, not the bracket prefix

**V2LG-FR-05: Optional Streaming Integration**
- `stream_job_writer` property optionally holds a `StreamingJobWriter` instance
- When set: log methods call `writer.emit_log()` internally for dual output compliance (V2JB-FR-01) and return SSE-formatted strings for yielding
- When None: log methods return None (server console only)

**V2LG-FR-06: Central Logger Configuration**
- `MiddlewareLogger` uses module-level `logger` from `utils.py`
- `logging.basicConfig()` in `utils.py` remains the single configuration point
- Changes to log level, handlers, format apply to all `MiddlewareLogger` instances

### Implementation Guarantees

**V2LG-IG-01:** Non-streaming endpoints have zero streaming overhead - no StreamingJobWriter created, no SSE formatting
**V2LG-IG-02:** All log output uses the same `logger.info()` call regardless of streaming mode
**V2LG-IG-03:** Server log format unchanged: `[TIMESTAMP,process PID,request N,top_function] MESSAGE`
**V2LG-IG-04:** Request counter is global and monotonically increasing across all endpoints
**V2LG-IG-05:** Nesting depth correctly tracks even with early returns or exceptions

### MiddlewareLogger Class Definition

```python
# src/utils.py (add to existing file, after existing log functions)

from dataclasses import dataclass, field
from typing import Optional, List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
  from routers_v2.router_job_functions import StreamingJobWriter

@dataclass
class MiddlewareLogger:
  """Unified logger for FastAPI endpoints with optional streaming support."""
  
  # Configuration (set at creation)
  log_inner_function_headers_and_footers: bool = True
  inner_log_indentation: int = 2
  stream_job_writer: Optional["StreamingJobWriter"] = None
  
  # State (managed internally)
  _function_name: str = ""                                    # Top-level function name
  _start_time: Optional[datetime.datetime] = None             # Top-level start time
  _request_number: int = 0                                    # From global counter
  _nesting_depth: int = 0                                     # 0 = top-level
  _inner_stack: List[Tuple[str, datetime.datetime]] = field(default_factory=list)
  
  @classmethod
  def create(cls,
             log_inner_function_headers_and_footers: bool = True,
             inner_log_indentation: int = 2,
             stream_job_writer: Optional["StreamingJobWriter"] = None) -> "MiddlewareLogger":
    """Factory method. Increments global request counter."""
    global _request_counter
    _request_counter += 1
    instance = cls(
      log_inner_function_headers_and_footers=log_inner_function_headers_and_footers,
      inner_log_indentation=inner_log_indentation,
      stream_job_writer=stream_job_writer,
      _request_number=_request_counter
    )
    return instance
  
  def log_function_header(self, function_name: str) -> Optional[str]:
    """
    Log function start.
    - depth=0: Always logs, sets top-level function name and start time
    - depth>0: Logs only if log_inner_function_headers_and_footers=True
    Returns: SSE event string if stream_job_writer set and output logged, else None
    """
  
  def log_function_output(self, output: str) -> Optional[str]:
    """
    Log intermediate output. Always logs regardless of nesting depth.
    Applies indentation based on current nesting depth.
    Returns: SSE event string if stream_job_writer set, else None
    """
  
  def log_function_footer(self) -> Optional[str]:
    """
    Log function end.
    - depth>0: Pops from stack, logs if log_inner_function_headers_and_footers=True
    - depth=0: Logs total duration (should not decrement below 0)
    Returns: SSE event string if stream_job_writer set and output logged, else None
    """
  
  def _apply_indentation(self, output: str) -> str:
    """Apply indentation based on nesting depth."""
  
  def _log_to_console(self, message: str) -> None:
    """Write to server console using standard format."""
  
  def _emit_to_stream(self, message: str) -> Optional[str]:
    """Emit to stream if writer is set. Calls writer.emit_log() for dual output (V2JB-FR-01)."""
```

### Log Output Formats

**Server console logs** (full context for debugging):
```
[YYYY-MM-DD HH:MM:SS,process PID,request N,top_function] MESSAGE
```

**SSE events and job files** (timestamp only, context implicit from job):
```
[YYYY-MM-DD HH:MM:SS] MESSAGE
```

### Example: Server Console Output (log_inner=True, indent=2)

```
[2025-01-15 10:30:00,process 1234,request 1,crawl()] START: crawl()...
[2025-01-15 10:30:00,process 1234,request 1,crawl()] Fetching file list...
[2025-01-15 10:30:01,process 1234,request 1,crawl()]   START: process_file()...
[2025-01-15 10:30:01,process 1234,request 1,crawl()]   [ 1 / 10 ] Processing 'doc.pdf'...
[2025-01-15 10:30:02,process 1234,request 1,crawl()]     START: upload_to_openai()...
[2025-01-15 10:30:03,process 1234,request 1,crawl()]     Uploading...
[2025-01-15 10:30:03,process 1234,request 1,crawl()]     END: upload_to_openai() (1.0 sec).
[2025-01-15 10:30:03,process 1234,request 1,crawl()]   OK.
[2025-01-15 10:30:03,process 1234,request 1,crawl()]   END: process_file() (2.0 secs).
[2025-01-15 10:30:04,process 1234,request 1,crawl()] END: crawl() (4.0 secs).
```
### Example: Server Console Output (log_inner=False, indent=2)

```
[2025-01-15 10:30:00,process 1234,request 1,crawl()] START: crawl()...
[2025-01-15 10:30:00,process 1234,request 1,crawl()] Fetching file list...
[2025-01-15 10:30:01,process 1234,request 1,crawl()]   [ 1 / 10 ] Processing 'doc.pdf'...
[2025-01-15 10:30:03,process 1234,request 1,crawl()]     Uploading...
[2025-01-15 10:30:03,process 1234,request 1,crawl()]   OK.
[2025-01-15 10:30:04,process 1234,request 1,crawl()] END: crawl() (4.0 secs).
```

### Example: SSE/Job File Output (log_inner=True, indent=2)

```
[2025-01-15 10:30:00] START: crawl()...
[2025-01-15 10:30:00] Fetching file list...
[2025-01-15 10:30:01]   START: process_file()...
[2025-01-15 10:30:01]   [ 1 / 10 ] Processing 'doc.pdf'...
[2025-01-15 10:30:02]     START: upload_to_openai()...
[2025-01-15 10:30:03]     Uploading...
[2025-01-15 10:30:03]     END: upload_to_openai() (1.0 sec).
[2025-01-15 10:30:03]   OK.
[2025-01-15 10:30:03]   END: process_file() (2.0 secs).
[2025-01-15 10:30:04] END: crawl() (4.0 secs).
```

## Job streaming specification

This section specifies the server-side implementation for streaming endpoints and job management.

### Functional Requirements

**V2JB-FR-01: Dual Output**
- Streaming endpoints must simultaneously: 1) yield SSE to HTTP response, 2) write same SSE to job file

**V2JB-FR-02: Atomic Job Creation**
- Job file creation must use exclusive mode to prevent race conditions
- On collision: regenerate job_id and retry

**V2JB-FR-03: Buffered Disk Writes**
- Log events buffered until `PERSISTENT_STORAGE_LOG_EVENTS_PER_WRITE` reached
- `start_json` and `end_json` always flush immediately
- Buffer flushed when checking control files

**V2JB-FR-04: Control File Polling**
- Iterative/long-running jobs must check for control files at regular intervals (e.g., after each item processed)
- Instantaneous operations (single CRUD, < 100ms) may skip control file checking
- Detection order: `cancel_requested` > `pause_requested` > `resume_requested`
- Job deletes control file immediately after detection

**V2JB-FR-05: Graceful Pause**
- On pause: flush buffer, write pause log, rename `.running` -> `.paused`
- While paused: poll for `resume_requested` or `cancel_requested` using `await asyncio.sleep()` to avoid blocking event loop
- On resume: rename `.paused` -> `.running`, continue processing

**V2JB-FR-06: Graceful Cancel**
- On cancel: flush buffer, emit `end_json` with `result.ok=false`, rename to `.cancelled`
- Partial results should be included in `result.data` if available

**V2JB-FR-07: Job Completion**
- On completion: emit `end_json` with final result, rename `.running` -> `.completed`
- `finished_utc` must be set in `end_json`

**V2JB-FR-08: Crash Recovery**
- Orphaned `.running` files indicate crashed jobs
- No automatic recovery - manual cleanup or re-run required

### Implementation Guarantees

**V2JB-IG-01:** Every job file contains exactly one `start_json` event as first content
**V2JB-IG-02:** Every completed/cancelled job file contains exactly one `end_json` event as last content
**V2JB-IG-03:** Job ID is unique across all routers for the lifetime of the jobs folder
**V2JB-IG-04:** Control files are ephemeral - never persist after job processes them
**V2JB-IG-05:** HTTP stream and job file content are byte-identical
**V2JB-IG-06:** StreamingJobWriter has no dependency on MiddlewareLogger or FastAPI logging

### File Organization

V2 router files are located in `src/routers_v2/`:
- `demorouter1.py` - Demo router implementation
- `router_job_functions.py` - Shared streaming job infrastructure (StreamingJobWriter, ControlAction, job file operations)

### Example: Non-Streaming Endpoint

Shows MiddlewareLogger usage without streaming (V2LG-IG-01 compliance):

```python
# routers_v2/inventory.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from utils import MiddlewareLogger

router = APIRouter()
config = None

def set_config(app_config, prefix):
  global config
  config = app_config

@router.get("/inventory/list")
async def list_inventory(request: Request):
  logger = MiddlewareLogger.create()  # No stream_job_writer = no streaming overhead
  logger.log_function_header("list_inventory()")
  
  logger.log_function_output("Fetching inventory...")
  items = await fetch_items(logger)  # Pass logger to nested function
  logger.log_function_output(f"Found {len(items)} items.")
  
  logger.log_function_footer()
  return JSONResponse({"ok": True, "data": items})

async def fetch_items(logger: MiddlewareLogger):
  logger.log_function_header("fetch_items()")  # Logs if log_inner=True (default)
  logger.log_function_output("Querying database...")
  items = [...]  # do work
  logger.log_function_footer()
  return items
```

### Example: Streaming Endpoint

Shows MiddlewareLogger with StreamingJobWriter integration:

```python
# routers_v2/demorouter1.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from utils import MiddlewareLogger
from routers_v2.router_job_functions import StreamingJobWriter, ControlAction

router = APIRouter()
config = None
router_prefix = None

def set_config(app_config, prefix):
  global config, router_prefix
  config = app_config
  router_prefix = prefix

@router.get("/demorouter1/process_files")
async def process_files(request: Request):
  """
  Demo streaming endpoint - simulates file processing with streaming output.
  
  Parameters:
  - format: Must be 'stream' for this endpoint
  - files: Number of files to simulate (default: 20)
  
  Examples:
  {router_prefix}/demorouter1/process_files?format=stream
  {router_prefix}/demorouter1/process_files?format=stream&files=10
  """
  function_name = "process_files()"
  request_params = dict(request.query_params)
  endpoint = function_name.replace("()", "")
  endpoint_documentation = process_files.__doc__.replace("{router_prefix}", router_prefix)
  documentation_HTML = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>/{endpoint} - Documentation</title></head><body><pre>{endpoint_documentation}</pre></body></html>"
  
  if len(request_params) == 0: return HTMLResponse(documentation_HTML)
  
  format = request_params.get("format", None)
  file_count = int(request_params.get("files", "20"))
  
  if format != "stream": return JSONResponse({"ok": False, "error": "Use format=stream", "data": {}})
  source_url = f"{router_prefix}/demorouter1/process_files?format=stream&files={file_count}"
  
  async def stream_generator():
    # Create writer first (no logging dependency)
    writer = StreamingJobWriter(
      persistent_storage_path=config.persistent_storage_path,
      router_name="demorouter1",
      action=endpoint,
      object_id=None,
      source_url=source_url,
      router_prefix=router_prefix,
      buffer_size=PERSISTENT_STORAGE_LOG_EVENTS_PER_WRITE
    )
    
    # Create logger with writer attached
    logger = MiddlewareLogger.create(
      log_inner_function_headers_and_footers=False,
      stream_job_writer=writer
    )
    
    try:
      yield writer.emit_start()  # Must be first (V2JB-IG-01)
      
      sse = logger.log_function_header(function_name)
      if sse: yield sse
      
      sse = logger.log_function_output(f"Created job '{writer.job_id}' for {file_count} files")
      if sse: yield sse
      
      simulated_files = [f"document_{i:03d}.pdf" for i in range(1, file_count + 1)]
      total = len(simulated_files)
      
      for i, filename in enumerate(simulated_files, 1):
        control_logs, control = await writer.check_control()
        for log in control_logs: yield log
        if control == ControlAction.CANCEL:
          sse = logger.log_function_footer()
          if sse: yield sse
          yield writer.emit_end(ok=False, error="Cancelled by user", data={"processed": i-1, "total": total})
          return
        
        sse = logger.log_function_output(f"[ {i} / {total} ] Processing '{filename}'...")
        if sse: yield sse
        await asyncio.sleep(0.2)  # Simulate work
        sse = logger.log_function_output(f"  OK.")
        if sse: yield sse
      
      sse = logger.log_function_footer()
      if sse: yield sse
      
      yield writer.emit_end(ok=True, data={"processed": total, "total": total})
      
    except Exception as e:
      sse = logger.log_function_footer()
      if sse: yield sse
      yield writer.emit_end(ok=False, error=str(e), data={})
    
    finally:
      writer.finalize()
  
  return StreamingResponse(stream_generator(), media_type="text/event-stream")

### Example: Instantaneous Streaming Endpoint

For quick single-operation endpoints (create, update, delete), control file checking is unnecessary since the operation completes before any control action could be processed:

```python
# routers_v2/demorouter1.py - Instantaneous streaming (no control file checking)

@router.post("/demorouter1/create")
async def demorouter_create(request: Request):
  """Create a new demo item. Supports format=json, html, stream."""
  logger = MiddlewareLogger.create()
  logger.log_function_header("demorouter_create")
  
  # Control params from query string per DD-E011
  query_params = dict(request.query_params)
  format_param = query_params.get("format", "json")
  
  # All data from body per DD-E012
  item_data = {}
  content_type = request.headers.get("content-type", "")
  if "application/json" in content_type:
    item_data = await request.json()
  elif "application/x-www-form-urlencoded" in content_type:
    form = await request.form()
    item_data = dict(form)
  
  item_id = item_data.get("item_id", None)
  
  # Validation (non-streaming logger for early returns)
  if not item_id:
    logger.log_function_footer()
    return JSONResponse({"ok": False, "error": "Missing 'item_id' in request body.", "data": {}})
  
  # format=stream - uses StreamingJobWriter for dual output
  if format_param == "stream":
    writer = StreamingJobWriter(
      persistent_storage_path=get_persistent_storage_path(),
      router_name="demorouter",
      action="create",
      object_id=item_id,
      source_url=str(request.url),
      router_prefix=router_prefix
    )
    stream_logger = MiddlewareLogger.create(stream_job_writer=writer)
    stream_logger.log_function_header("demorouter_create")
    
    async def stream_create():
      try:
        yield writer.emit_start()
        
        # No check_control() - operation is instantaneous
        sse = stream_logger.log_function_output(f"Creating item '{item_id}'...")
        if sse: yield sse
        
        save_demo_item(item_id, item_data)  # Single operation
        
        sse = stream_logger.log_function_output("  OK.")
        if sse: yield sse
        
        stream_logger.log_function_footer()
        yield writer.emit_end(ok=True, data={"item_id": item_id, **item_data})
        
      except Exception as e:
        stream_logger.log_function_footer()
        yield writer.emit_end(ok=False, error=str(e), data={})
      finally:
        writer.finalize()
    
    return StreamingResponse(stream_create(), media_type="text/event-stream")
  
  # Non-streaming formats (json, html)
  save_demo_item(item_id, item_data)
  logger.log_function_footer()
  return JSONResponse({"ok": True, "error": "", "data": {"item_id": item_id, **item_data}})
```

**When to use control file checking:**
- Iterative operations (processing N files, crawling pages)
- Long-running operations (> 1 second)
- Operations with natural pause points (between iterations)

**When to skip control file checking:**
- Single CRUD operations (create, update, delete one item)
- Instantaneous operations (< 100ms)
- No loop/iteration in the operation

### Function Definitions

```python
# routers_v2/router_job_functions.py

from dataclasses import dataclass
from enum import Enum
from typing import Literal, Optional

# Type definitions
JobState = Literal["running", "paused", "completed", "cancelled"]
ControlState = Literal["pause_requested", "resume_requested", "cancel_requested"]

@dataclass
class JobMetadata:
  job_id: str                           # "jb_42"
  state: JobState
  source_url: str                       # "/v2/crawler/crawl?domain_id=TEST01&format=stream"
  monitor_url: str                      # "/v2/jobs/monitor?job_id=jb_42&format=stream"
  started_utc: str                      # ISO 8601: "2025-01-15T14:20:30.000000Z"
  finished_utc: str | None              # ISO 8601 or None if running
  result: dict | None                   # {ok, error, data} or None if running

class ControlAction(Enum):
  CANCEL = "cancel"
  # PAUSE handled internally by check_control()

class StreamingJobWriter:
  """Buffered writer for streaming job files. Handles dual output to HTTP and file."""
  
  def __init__(self, persistent_storage_path: str, router_name: str, action: str, 
               object_id: Optional[str], source_url: str, router_prefix: str,
               buffer_size: int = PERSISTENT_STORAGE_LOG_EVENTS_PER_WRITE):
    """
    Create job file and initialize writer.
    - router_prefix: Injected from app.py (e.g., '/v2') for constructing monitor_url
    - Generates unique job_id (jb_[NUMBER])
    - Creates job file: [TIMESTAMP]_[[ACTION]]_[[JB_ID]]_[[OBJECT_ID]].running
    - Retries with new job_id on collision (V2JB-FR-02)
    """
  
  @property
  def job_id(self) -> str:
    """Returns job_id string, e.g., 'jb_42'"""
  
  @property
  def monitor_url(self) -> str:
    """Returns monitor URL: {router_prefix}/jobs/monitor?job_id={job_id}&format=stream"""
  
  def emit_start(self) -> str:
    """
    Emit start_json event. Immediate flush to file. (V2JB-FR-03)
    Returns SSE-formatted string for HTTP response.
    """
  
  def emit_log(self, message: str) -> str:
    """
    Emit log event. Buffered write to file. (V2JB-FR-03)
    Returns SSE-formatted string for HTTP response.
    """
  
  def emit_end(self, ok: bool, error: str = "", data: dict = None) -> str:
    """
    Emit end_json event. Immediate flush to file. (V2JB-FR-03, V2JB-FR-07)
    Sets finished_utc timestamp.
    Returns SSE event string for HTTP response.
    """
  
  async def check_control(self) -> tuple[list[str], Optional[ControlAction]]:
    """
    Check for control files and handle pause loop. (V2JB-FR-04, V2JB-FR-05)
    - Flushes buffer before checking
    - If pause_requested: emits pause log, enters async pause loop, renames to .paused
    - If cancel_requested: returns ControlAction.CANCEL
    - If resume_requested (while paused): emits resume log, renames to .running
    Returns (log_events, control_action):
    - log_events: list of SSE-formatted strings for pause/resume (already written to file)
    - control_action: ControlAction.CANCEL if cancelled, None otherwise
    Caller must yield all log_events to maintain FR-01/IG-05 compliance.
    """
  
  def finalize(self) -> None:
    """
    Finalize job file state. (V2JB-FR-06, V2JB-FR-07)
    - If end_json emitted: rename to .completed or .cancelled
    - Flushes any remaining buffer
    Called automatically in finally block.
    """

# Standalone functions for /v2/jobs endpoints

def generate_job_id(persistent_storage_path: str) -> str:
  """Generate next job ID: 'jb_[NUMBER]'. Scans existing files to find max."""

def find_job_by_id(persistent_storage_path: str, job_id: str) -> Optional[JobMetadata]:
  """Find job across all routers. Returns JobMetadata or None."""

def list_jobs(persistent_storage_path: str, router_filter: str = None, state_filter: str = None) -> list[JobMetadata]:
  """List all jobs. Returns list of JobMetadata, newest first."""

def get_job_metadata(persistent_storage_path: str, job_id: str) -> Optional[JobMetadata]:
  """Parse job file and return JobMetadata from start_json/end_json."""

def read_job_log(persistent_storage_path: str, job_id: str) -> str:
  """Read full SSE content from job file for monitoring."""

def read_job_result(persistent_storage_path: str, job_id: str) -> Optional[dict]:
  """Extract result from end_json. Returns None if job not completed/cancelled."""

def create_control_file(persistent_storage_path: str, job_id: str, action: str) -> bool:
  """Create control file (.pause_requested, .resume_requested, .cancel_requested)."""

def delete_job(persistent_storage_path: str, job_id: str) -> bool:
  """Delete job file. Returns True if deleted."""

def force_cancel_job(persistent_storage_path: str, job_id: str) -> bool:
  """Force cancel stalled job by renaming .running -> .cancelled. Cleans up control files."""
```

### Spec Changes

**[2024-12-17 12:10]**
- Added: "Scenario" section with Problem/Solution/What we don't want
- Added: Spec Changes section