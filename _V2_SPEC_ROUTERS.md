# Routers Technical Specification Version 2

This document describes the design and implemenation of the **second generation** routers used for crawling, access to domain objects, and long-running job management. First generation routers and endpoints are out of scope and should remain untouched to ensure backwards compatibility.

**Goal of this document:**
- Specify `/v2/` prefixed routers with interactive UI and CRUD operations (Create, Read, Update, Delete). 'Read' is implemented as 'Get' here.
- Describe solution architecture
- Document requirements and assumptions
- Document design decisions and why they have been made
- Provide enough context to AI so code can be generated and verified

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
- Contains different categories of SharePoint sources:
- `file_sources` - list of file sources with individual`site_url` and `filter` attributes (1:n relation)
- `list_sources` - list of SharePoint list sources with individual `site_url` and `filter` attributes (1:n relation)
- `sitepage_sources` - list of site page with individual `site_url` and `filter` attributes (1:n relation)

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

## Endpoint architecture and design

In the following sections `resource` acts as a placeholder for the individual domain objects: `domain`, `vector_store`, etc. while `action` acts as a placeholder for Create, List, Update, Delete, and other actions. The combination of resources and actions is called an endpoint and is implemented as a HTTP/HTTPS URL.

### Endpoint design decisions

- [DD-E001] Self-documentation on bare GET (no query params, including `format`). When documentation is needed, it's where the developer is working.
- [DD-E002] Action-suffixed endpoints: `/resource`, `/resource/get`, `/resource/create`, `/resource/update`, `/resource/delete`. Allows self-documentation.
- [DD-E003] Backend ships simple interactive UI. Admins need no programming skills. Changes can be implemented and tested fast and in one place.
- [DD-E004] Format param controls response: `json`, `html`, `ui` (resource root only), `stream` (long-running jobs). 
- [DD-E005] Body accepts JSON or form data (content-type detection). Principle of least surprise: No need to look up documentation, it just works.
- [DD-E006] Triggering, monitoring and management of crawling and other jobs via HTTP GET requests. Allows automation via single URL calls (low technology barrier).
- [DD-E007] Semantic identifier names like `job_id`, `domain_id`, `source_id` that explicitly name the resource. Disambiguates object types and allow for actions that require multiple ids.
- [DD-E008] Semantic entity identifyers for interally created ids like `jb_[JOB_NUMBER]` for a job. Self-explanatory system: disambiguates object types, simplifies support. Exceptions: Domain ids (used as folder names and `domain.json`) and source ids (used in `domain.json`)
- [DD-E009] Plural naming for resources: `/domains`, `/vector_stores`. Exceptions possible: `/crawler`
- [DD-E010] HTTP semantics exception for `/resource/delete` endpoints: `GET [R]/delete`

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
- `GET /v2/resource/get?resource_id={id}` - Get single
  - Example variant: `GET /v2/resource/get_content?resource_id={id}` - Retrieve content of single item
- `POST /v2/resource/create` - Create
- `PUT /v2/resource/update?resource_id={id}` - Update
  - Example variant: `PUT /v2/resource/ensure_attributes?resource_id={id}` - Create or update item attributes
- `DELETE, GET /v2/resource/delete?resource_id={id}` - Delete

### Query params syntax uses explicit query params for ids and data format:

**/resource** - List
- `GET /v2/resource` -> -> Self-documentation (UTF-8 text)
- `GET /v2/resource?format=json` -> JSON result with `"data": [...]`
- `GET /v2/resource?format=html` -> HTML table (nested or flat)
- `GET /v2/resource?format=ui` -> Interactive UI listing all items with [Create], [Edit] / [View], [Delete] buttons for each item if supported by endpoint

**/resource/get** - Get single
- `GET /v2/resource/get` -> -> Self-documentation (UTF-8 text)
- `GET /v2/resource/get?resource_id={id}` -> JSON result with `"data": {...}`
- `GET /v2/resource/get?resource_id={id}&format=json` -> JSON result with `"data": {...}`
- `GET /v2/resource/get?resource_id={id}&format=html` -> HTML detail view
- `GET /v2/resource/get?format=json` -> HTTP 400: JSON error result "Missing 'resource_id'."
- `GET /v2/resource/get?format=ui` -> HTTP 400: "Format 'ui' not supported".

### Common query params

**`format` query param**
- Specifies the returned data format.
- All endpoints returning data are required to support this query param.
- Endpoints are NOT required to support all available options. At least one option must be supported.
- Available options:
  - `json` (default) -> JSON result with `"data": {...}` for Create, Get, Update, Delete actions. JSON result with `"data": [...]` for List and other action returning collections.
  - `html` -> HTML detail view (JSON converted to flat or nested HTML table)
  - `ui` -> Interactive UI listing all items with [Create], [Edit] / [View], [Delete] buttons for each item if supported by endpoint
  - `stream` ->  Server-Sent Events (SSE) stream with HTMX compatible syntax (`event:` and `data:` lines) with MIME type `Content-Type: text/event-stream`

**`dry_run` query param**
- Specifies if an action is allowed to delete or modify data.
- Used to verify the configuration and predict the result of actions that can't be undone.
- Supported by Create, Update, Delete, and endpoints that trigger long-running jobs.
- Available options:
  - `false` (default) - Allowed to delete or modify data: perform the action as specified.
  - `true` - NOT allowed to delete or modify data: simulate the action and its outcome.
  
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
- Between the `start_json` and `end_json` events only `log` events are allowed
- The `start_json` event contains a JSON object with the job metadata

Example *stream output* for `start_json` event with job metadata as JSON
```
event: start_json
data: { "job_id": 'jb_2', "endpoint": "/v2/crawler/crawl?domain_id=TEST01&format=stream", "state": "running"}

```

Example *multiline stream output* for `start_json` event with job metadata as JSON
```
event: start_json
data: {
data:   "job_id": 'jb_2'
data:   "endpoint": "/v2/crawler/crawl?domain_id=TEST01&format=stream",
data:   "state": "running",
data:   "start_utc": "2024-01-15T10:30:00.000000Z"
data: }

```

Example *stream output* for `log` event with single line of text
```
event: log
data: [ 2 / 4 ] Processing file 'document.docx' (ID='assistant-86Bsp9rZQevLksitUBBPEn', modified='2025-11-26 14:20:30')...

```

Example *multiline stream output* for `end_json` event with job metadata as JSON
```
event: end_json
data: {
data:   "job_id": 'jb_2'
data:   "endpoint": "/v2/crawler/crawl?domain_id=TEST01&format=stream",
data:   "state": "completed",
data:   "start_utc": "2024-01-15T10:30:00.000000Z",
data:   "end_utc": "2024-01-15T12:23:34.000000Z",
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

**Format:** `[TIMESTAMP]_[[ENDPOINT_ACTION]]_[[JB_ID]]_[[OBJECT_ID_OR_NAME]].[state]`
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

1. Scan all files in `PERSISTENT_STORAGE_PATH/jobs/**/*`
2. Filter files with valid extensions (`.running`, `.completed`, `.cancelled`)
3. Sort by modification time (newest first)
4. Take last 100 files
5. Extract `jb_id_number` from filenames
6. Find maximum `jb_id_number`
7. Return `"jb_" + (max_jb_id_number + 1)`

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
  - Available common formats:
    - `...(j)` -> supports `format=json` (default when object id given)
    - `...(h)` -> supports `format=html`
    - `...(u)` -> supports `format=ui`
    - `...(s)` -> supports `format=stream`
    - `...(z)` -> supports `format=zip`
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

**Domain**
- L(jhu)C(jhs)G(jh)U(jhs)D(jhs): `/v2/domains` - Knowledge domains to be used for crawling and semantic search

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
- L(jhs): `/v2/crawler/crawl?domain_id={id}&mode=[full|incremental]&scope=[all|files|lists|sitepages]&source_id={id}&dry_run=false`
  - Performs the following steps: 1) download, 2) processing, 3) embedding
  - `mode=full` (default) - performs full crawl
  - `mode=incremental` - performs incremental crawl (only changes)
  - `scope=all` (default) - crawls all: files, lists, sitepages
  - `scope=files` - crawls only files, operating ONLY on `01_files/` local storage
  - `scope=lists` - crawls only lists, operating ONLY on `02_lists/` local storage
  - `scope=sitepages` - crawls only sitepages, operating ONLY on `03_sitepages/` local storage
  - Optional: `source_id={id}` - if a scope other than `all` is given, the action can be further limited to individual sources
  - `dry_run=false` (default) - performs action as specified
  - `dry_run=true` - simulates action without writing / modifying data

**Jobs**
- L(jhu)G(jh)D(jh): `/v2/jobs` - Manage long-running jobs that are triggered by other endpoints (crawler, inventory)
  - `DELETE, GET /v2/jobs/delete` - endpoint does intentionally not support streaming
  - `GET /v2/jobs/get?job_id={id}`  -  Return job metadata with status in same format as in `start_json` event of the stream
- L(): `/v2/jobs/control?job_id={id}&action=[pause|resume|cancel]`
  - `GET /v2/jobs/control?job_id={id}&action=pause` - Requests the job to be paused
  - `GET /v2/jobs/control?job_id={id}&action=resume` - Requests the job to be resumed
  - `GET /v2/jobs/control?job_id={id}&action=cancel` - Requests the job to be cancelled
- L(jhs): `/v2/jobs/monitor?job_id={id}` - Monitor long-running jobs
  - `GET /v2/jobs/monitor?job_id={id}&format=json` -> JSON `{ [JOB_METADATA], "log" : "[LAST_LOG_EVENT_DATA]"}`
  - `GET /v2/jobs/monitor?job_id={id}&format=html` -> JSON converted to nested HTML table
  - `GET /v2/jobs/monitor?job_id={id}&format=stream` -> Full stream (from first event) as Server-Sent Events
- L(jh): `/v2/jobs/results?job_id={id}` - Return `result` JSON from `end_json` event of the stream

### Crawling Process

#### Local files (persistent storage)

Data is stored in two top-level folders:

**`PERSISTENT_STORAGE_PATH/crawler/`:**
- Local cache of downloaded files, processed for embedding

**`PERSISTENT_STORAGE_PATH/domains/`:**
- Local storage of domain definitions and embedded file metadata

**Folder Structure**:
```
/domains/
├── DOMAIN01/                 # Domain folder
│   ├── domain.json           # Domain definition file
│   └── files_metadata.json   # Embedded file metadata (joins data from map files and metadata extraction)
├── DOMAIN02/
│   ├── domain.json
│   └── files_metadata.json
└── ...

/crawler/
├── DOMAIN01/                 # Domain folder containing cached crawler files
├── DOMAIN02/                 # Domain folder containing cached crawler files
└── ...

/crawler/[DOMAIN_ID]/
├── 01_files/[SOURCE_ID]/
│   ├── sharepoint_map.csv    # Cached data for data in SharePoint
│   ├── files_map.csv         # Cached data for downloaded and processed files
│   ├── vectorstore_map.csv   # Cached data for embedded files in vector stores + mapping to local storage and SharePoint
│   ├── 02_embedded/          # Successfully embedded files
│   │   ├── Document1.docx
│   │   └── SubFolder/
│   │       └── AnotherDoc1.pdf
│   └── 03_failed/            # Files where embedding failed
│       ├── Document2.docx
│       └── SubFolder/
│           └── AnotherDoc2.pdf
├── 02_lists/[SOURCE_ID]/
│   ├── sharepoint_map.csv
│   ├── files_map.csv
│   ├── vectorstore_map.csv
│   ├── 01_originals/         # Original CSV exports
│   ├── 02_embedded/          # Converted Markdown files
│   └── 03_failed/
└── 03_sitepages/[SOURCE_ID]/
    ├── sharepoint_map.csv
    ├── files_map.csv
    ├── vectorstore_map.csv
    ├── 01_originals/         # Original HTML
    ├── 02_embedded/          # Processed HTML
    └── 03_failed/
```

#### Map files (persistent storage)

Map files allow the crawler to quickly identify changes and analyze errors.
Map file types:
  - `sharepoint_map.csv` - caches file metadata from SharePoint
  - `files_map.csv` - caches local storage, contains file download and processing status
  - `vectorstore_map.csv`- caches vector store data, contains everything in other map files + upload and embedding status

**`sharepoint_map.csv` columns:**
- `sharepoint_listitem_id` - number - SharePoint list item ID (e.g., 123)
- `sharepoint_unique_file_id` - string - GUID unique to this file (e.g., "b!abc123...")
- `filename` - string - file name with extension (e.g., "Document.docx")
- `file_type` - string - file extension without dot (e.g., "docx")
- `file_size` - number - size in bytes (e.g., 864368)
- `url` - string - URL-encoded SharePoint URL (e.g., "https://company.sharepoint.com/sites/demo/Shared%20Documents/Document.docx")
- `raw_url` - string - unencoded SharePoint URL (e.g., "https://company.sharepoint.com/sites/demo/Shared Documents/Document.docx")
- `server_relative_url` - string - path from site root (e.g., "/sites/demo/Shared Documents/Document.docx")
- `last_modified_utc` - string (ISO 8601 / RFC3339) - SharePoint UTC timestamp (e.g., "2024-01-15T10:30:00.000000Z")
- `last_modified_timestamp` - number - SharePoint Unix timestamp in seconds (e.g., 1705319400)

**`files_map.csv` columns:**
- `file_relative_path` - string - path relative to storage root with backslashes
  - Empty if download failed.
  - Processing failed example: "DOMAIN01\01_files\source01\03_failed\Reports\Q1.docx"
  - Succeeded example: "DOMAIN01\01_files\source01\02_embedded\Reports\Q1.docx"
- `file_size` - number - size in bytes (e.g., 864368)
- `last_modified_utc` - string (ISO 8601 / RFC3339) - SharePoint UTC timestamp (e.g., "2024-01-15T10:30:00.000000Z")
- `last_modified_timestamp` - number - SharePoint Unix timestamp in seconds (e.g., 1705319400)
- `downloaded_utc` - string (ISO 8601 / RFC3339) - Download UTC timestamp (e.g., "2024-01-15T10:30:00.000000Z")
- `downloaded_timestamp` - number - Download Unix timestamp in seconds (e.g., 1705319400)
- `sharepoint_error` - string - Any error that might have occurred during the download
- `processing_error` - string - Any error that might have occurred during the processing of the file

**`vectorstore_map.csv` columns:**
- `openai_file_id` - string - OpenAI file ID assigned after upload (e.g., "assistant-BuQoNyXQnoedPjTySDTFU1")
  - empty if file could not be uploaded or embedded
- `vector_store_id` - string - OpenAI vector store ID where the file was embedded last (Domain vector store ID)
  - empty if file could not be uploaded or embedded
- `file_relative_path` - string - path relative to storage root with backslashes
  - Example if succeeded: "DOMAIN01\01_files\source01\02_embedded\Reports\Q1.docx"
  - Example if failed: "DOMAIN01\01_files\source01\03_failed\Reports\Q1.docx"
- `sharepoint_listitem_id` - number - SharePoint list item ID (e.g., 123)
- `sharepoint_unique_file_id` - string - GUID unique to this file (e.g., "b!abc123...")
- `filename` - string - file name with extension (e.g., "Document.docx")
- `file_type` - string - file extension without dot (e.g., "docx")
- `file_size` - number - size in bytes (e.g., 864368)
- `last_modified_utc` - string (ISO 8601 / RFC3339) - UTC timestamp (e.g., "2024-01-15T10:30:00.000000Z")
- `last_modified_timestamp` - number - Unix timestamp in seconds (e.g., 1705319400)
- `downloaded_utc` - string (ISO 8601 / RFC3339) - Download UTC timestamp (e.g., "2024-01-15T10:30:00.000000Z")
- `downloaded_timestamp` - number - Download Unix timestamp in seconds (e.g., 1705319400)
- `uploaded_utc` - string (ISO 8601 / RFC3339) - `created_at` Open AI UTC timestamp returned by file upload (e.g., "2024-01-15T10:30:00.000000Z")
  - empty if file could not be uploaded or embedded
- `uploaded_timestamp` - number - `created_at` Open AI UTC timestamp returned by file upload (e.g., 1705319400)
  - empty if file could not be uploaded or embedded
- `embedded_utc` - string (ISO 8601 / RFC3339) - `created_at` Open AI UTC timestamp returned by file embedding (e.g., "2024-01-15T10:30:00.000000Z")
  - empty if file could not be uploaded or embedded
- `embedded_timestamp` - number - `created_at` Open AI UTC timestamp returned by file upload (e.g., 1705319400)
  - empty if file could not be uploaded or embedded
- `sharepoint_error` - string - Any error that might have occurred during the download
- `processing_error` - string - Any error that might have occurred during the processing of the file
- `embedding_error` - string - Any error that might have occurred during the upload to the Open AI backend or the embedding

#### Crawling process for SharePoint `file_sources`

**Parameters:**
  - `domain_id={id}` - The domain id
  - `mode=[full|incremental]` - Full or incremental crawl
  - Optional: `source_id={id}` - Process only a single source
  - `dry_run=false` (default) - performs action as specified
  - `dry_run=true` - simulates action without writing / modifying data

**Download data:**
1. Crawler loads domain config for `domain_id` and loads all `file_sources` (404 for missing domain)
2. If optional `source_id` is given, filters out all other sources (404 for missing source)
3. Crawler connects to SharePoint source using credentials from config (downstream HTTP errors are logged but do not terminate action)
4. [For each connected source]
    - Loads files list from document library as defined in source (with filter if configured)
    - Writes `sharepoint_map.csv` file gracefully (retries on concurrency problems)
    - If `mode=incremental`:
	    - Loads `files_map.csv` to internal `file_map` (fallback to `mode=full` if file not exists)
	    - Identifies 1) added files, 2) removed files, 3) changed files (based on  `file_size` and `last_modified_utc`)
	    - REMOVED: Deletes all removed files from `02_embedded/` and `03_failed/` folders and from `file_map`. Writes `files_map.csv` gracefully.
	    - ADDED: Downloads added files to `02_embedded/` folder, applying SharePoint last modified timestamp. Writes updated `files_map.csv` gracefully.
	    - CHANGED: Deletes all changed files from `02_embedded/` and `03_failed/` folders.
	    - CHANGED: Downloads changed files to `02_embedded/` folder, applying SharePoint last modified timestamp. Writes updated `files_map.csv` gracefully.
    - If `mode=full`:
	    - Deletes all subfolders in `02_embedded/` and `03_failed/` folders
	    - Deletes `files_map.csv` and creates new internal `file_map`
	    - ADDED: Downloads added files to `02_embedded/` folder, applying SharePoint last modified timestamp. Writes updated `files_map.csv` gracefully.

Expected outcome:
- `sharepoint_map.csv` contains all files (rows) that could be identified in SharePoint
- `sharepoint_map.csv` does not contain files not existing in SharePoint
- `files_map.csv` contains all files (rows) as `sharepoint_map.csv` with additional column data
- `files_map.csv` > `file_relative_path` column is empty if download failed
- `02_embedded/` folder does not contain files not existing in SharePoint
- `02_embedded/` folder might missing files that could not be downloaded from SharePoint
- `03_failed/` folder does not contain files not existing in SharePoint

**Process data:**
- This step is skipped for SharePoint files

**Embed data:**
1. Crawler loads domain config for `domain_id` and loads all `file_sources` (404 for missing domain)
2. If optional `source_id` is given, filters out all other sources (404 for missing source)
3. Get target vector store
    - If `vector_store_id`is given, sets this vector store as target (404 for missing)
    - Otherwise uses `vector_store_id` from `domain.json` to get domain vector store (404 if missing, 500 if not configured)
    - Load all vector store files 
4. [For each source]
    - Loads `files_map.csv` (skip source if not found)
    - Loads `vectorstore_map.csv` (skip source if not found)
    - Cleanup `vectorstore_map.csv`: Removes all files with `openai_file_id` not found in the vector store. Writes `vectorstore_map.csv` gracefully.
    - If `mode=incremental`:
        - Compares the content of `files_map.csv` and `vectorstore_map.csv` while ignoring all files in `03_failed/` folders
        - Identifies 1) added files, 2) removed files, 3) changed files (based on `file_size` and `last_modified_utc`)
		- All changes must be reflected in internal `vectorstore_map`
        - REMOVED: Removes all files from the vector store. Writes updated `vectorstore_map.csv` gracefully.
        - ADDED: For each file, uploads the file to the global file storage and adds it to the vector store. Writes updated `vectorstore_map.csv` gracefully.
        - CHANGED: For each file, removes the file from the vector store, uploads the file to the global file storage and adds it to the vector store. Writes updated `vectorstore_map.csv` gracefully.
    - If `mode=full`:
		- All changes must be reflected in internal `vectorstore_map`
        - Removes all files in `vectorstore_map.csv` from the vector store but leaves file in global storage (other vector stores might still use it)
		- ADD: For each file in `files_map.csv`, uploads the file to the global file storage and adds it to the vector store
	- After modifying the target vector store:
        - WAIT: Waits until the vector store has no files with status = 'in_progress'
		- CLEANUP: Removes files where embedding has failed
		    - Loads all vector store files
			- Filters out files not in scope: neither in added files list, nor in changed files lists
			- Identify files with status != 'completed'
			- For each file
			    - Removes file from vector store and deletes file in the global storage
			    - Moves file from `02_embedded/` to `03_failed/` folder
				- Updates file properties like `embedding_error` and `file_relative_path` in `vectorstore_map`
			- Writes updated `vectorstore_map.csv` gracefully
