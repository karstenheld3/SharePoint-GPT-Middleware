# Routers Technical Specification

**Goal of this document:**
- Specify implementation of routers with CRUD actions (Create, Read, Update, Delete). 'Read' is implemented as 'Get'.
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
  - `files_map.csv` - caches local storage metadata
  - `vectorstore_map_csv`- caches vector store file metadata and maps it to local storage and SharePoint

**Domain** - Knownledge domain to be used for RAG use cases
- To be crawled (downloaded and embedded) from SharePoint into a single vector store
- Maps to exactly one vector store (1:1 relation)
- Supports many sources in different SharePoint sites and SharePoint filters
- Contains different categories of SharePoint sources:
- `file_sources` - list of file sources with individual`site_url` and `filter` attributes (1:n relation)
- `sitepage_sources` - list of site page with individual `site_url` and `filter` attributes (1:n relation)
- `list_sources` - list of site page with individual `site_url` and `filter` attributes (1:n relation)

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

- [DD-E001] Self-documentation on bare GET (no query params). When documentation is needed, it's where the developer is working (who might not have access to anything else).
- [DD-E002] Action-suffixed endpoints: `/resource`, `/resource/get`, `/resource/create`, `/resource/update`, `/resource/delete`. Allows self-documentation.
- [DD-E003] Backend ships simple interactive UI. Admins need no programming skills. Changes can be implemented and tested fast and in one place.
- [DD-E004] Format param controls response: `json`, `html`, `ui` (resource root only), `stream` (long-running jobs). 
- [DD-E005] Body accepts JSON or form data (content-type detection). Principle of least surprise: No need to look up documentation, it just works.
- [DD-E006] Triggering, monitoring and management of crawling and other jobs via HTTP GET requests. Allows automation via single URL calls (low technology barrier).
- [DD-E007] Semantic identifyer names like `resource_id` or `domain_id` that explicitly name the resource. Disambiguates object types and allow for actions that require multiple ids.
- [DD-E008] Semantic entity identifyers like `rs_[RESOURCE_ID]` for a resource, `dm_[DOMAIN_ID]` for a domain. Self-explanatory system: disambiguates object types, simplifies support.
- [DD-E009] Plural naming for resources: `/domains`, `/vector_stores`. Exceptions possible: `/crawler`

### Why Action-Suffixed over RESTful?

- RESTful was tried in the initial version and led to duplication of endpoints: `/query` -> `/query2`
- Hybrid API: same endpoints serve both programmatic API (JSON) and interactive UI (HTMX)
- Self-documenting: URL reflects developer intent via action and query params without hidden information in HTTP method
- Bare `GET /resource` without params always returns documentation (consistent behavior)
- Developers can easily inspect content, try out query params and choose return types via HTTP GET in the browser without additional tooling
- All endpoints use query params (uniform parsing, generalized predictable behavior)
- Single endpoint accepts both JSON body and form data (content-type detection)
- Easy to add new action endpoints that do not map to HTTP methods: `/domains/crawl?domain_id={id}&mode=incremental`, `/domains/source?domain_id={id}`
- Simplified implementation: HTMX forms work naturally with explicit URLs

### Action-Suffixed syntax uses explicit action names

**Endpoint format**
- List top-level resource: `/[RESOURCE]?[PARAM_1]=[VALUE_1]&[PARAM_2]=[VALUE_2]`
- Perform action with top-level resource: `/[RESOURCE]/[ACTION]?[PARAM_1]=[VALUE_1]&[PARAM_2]=[VALUE_2]`
- Perform action nested resource: `/[RESOURCE]/[RESOURCE]/[ACTION]?[PARAM_1]=[VALUE_1]&[PARAM_2]=[VALUE_2]`

**Actions**
- `GET /resource` - Endpoint self-documentation as text (UTF-8)
- `GET /resource?format=json` - Get all
- `GET /resource/get?resource_id={id}` - Get single
  - Example variant: `GET /resource/get_content?resource_id={id}` - Retrieve content of single item
- `POST /resource/create` - Create
- `PUT /resource/update?resource_id={id}` - Update
  - Example variant: `PUT /resource/ensure_attributes?resource_id={id}` - Create or update item attributes
- `DELETE /resource/delete?resource_id={id}` - Delete

### Query params syntax uses explicit query params for ids and data format:

**/resource** - List
- `GET /resource` -> Documentation
- `GET /resource?format=json` -> JSON array `[...]`
- `GET /resource?format=html` -> HTML table (nested or flat)
- `GET /resource?format=ui` -> Interactive UI listing all items with [Create], [Edit] / [View], [Delete] buttons for each item if supported by endpoint

**/resource/get** - Get single
- `GET /resource/get` -> Documentation
- `GET /resource/get?resource_id={id}` -> JSON object `{...}`
- `GET /resource/get?resource_id={id}&format=json` -> JSON object `{...}`
- `GET /resource/get?resource_id={id}&format=html` -> HTML detail view
- `GET /resource/get?format=json` -> Error: missing resource_id
- `GET /resource/get?format=ui` -> Error: format not supported

### Common query params

**`format` query param**
- Specifies the returned data format.
- All endpoints returning data are required to support this query param.
- Endpoints are NOT required to support all available options. At least one option must be supported.
- Available options:
  - `json` (default) -> JSON object `{...}` for Create, Get, Update, Delete actions. JSON array `[...]` for List and other action returning collections.
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

Example *stream output* for `start_json` event with JSON data
```
event: start_json
data: { "id": 2, "endpoint": "streaming01", "state": "running", ... }

```

Example *multiline stream output* for `start_json` event with JSON data
```
event: start_json
data: {
data:   "id": 2,
data:   "endpoint": "streaming01",
data:   "state": "running",
data    ...
data: }

```

Example *stream output* for `log` event with single line of text
```
event: log
data: [ 2 / 4 ] Processing file 'document.docx' (ID='assistant-86Bsp9rZQevLksitUBBPEn', modified='2025-11-26 14:20:30')...

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

**Format:** `[TIMESTAMP]_[[ENDPOINT_ACTION]]_[[JB_ID]]_[[OBJECT_ID]].[state]`
**Example:** `2025-11-26_14-20-30_[crawl]_[jb_42]_[dm_TEST01].running`
**Example without object id:** `2025-11-26_14-20-30_[global_cleanup]_[jb_42].running`

**Components:**
- `[TIMESTAMP]` - When the job was created (YYYY-MM-DD_HH-MM-SS)
- `[ENDPOINT_NAME]` - Name of the streaming endpoint
- `[JB_ID]` - Global sequential streaming job ID
- `[OBJECT_ID]` - Optional: ID of object being processed

**States:**
- `.running` - Active job, contains log content
- `.completed` - Finished successfully
- `.cancelled` - Stopped by user
- `.pause_requested` - Control: request pause
- `.resume_requested` - Control: request resume
- `.cancel_requested` - Control: request cancel

**Job Files Location**

The folder structure reflects how resources are exposed as routers and endpoints.

```
PERSISTENT_STORAGE_PATH/jobs/
├── example_router/
│   └── example_endpoint/
│       ├── 2025-11-26_14-20-30_[crawl]_[jb_1]_[dm_TEST01].running           # Active job
│       ├── 2025-11-26_14-21-00_[crawl]_[jb_2]_[dm_TEST02].completed         # Finished job
│       ├── 2025-11-26_14-22-00_[global_cleanup]_[jb_3].cancelled            # Cancelled job
│       ├── 2025-11-26_14-23-00_[global_cleanup]_[jb_4].running              # Another active job
│       ├── 2025-11-26_14-24-00_[delete]_[jb_5]_[dm_TEST04].running          # Another active job
│       └── 2025-11-26_14-25-00_[delete]_[jb_5]_[dm_TEST04].pause_requested  # Control file
└── another_router/
    ├── 2025-11-26_14-25-00_[another_action]_[jb_6].running                  # Another active job
    └── 2025-11-26_14-26-00_[another_action]_[jb_7].completed                # Another completed job 
```

**`jb_id` Generation Algorithm**

Format: `jb_[NUMBER]` where `[NUMBER]` is an ascending integer starting with 1 

1. Scan all files in `PERSISTENT_STORAGE_PATH/jobs/**/*`
2. Filter files with valid extensions (`.running`, `.completed`, `.cancelled`)
3. Sort by modification time (newest first)
4. Take last 100 files
5. Extract `jb_id_number` from filenames
6. Find maximum `jb_id_number`
7. Return `"sj_" + (max_jb_id_number + 1)`

### Use HTTP status codes for high-level success/failure

- 2xx – the operation was successfully processed (even if result is 'no-op').
  - 200 - OK
- 4xx – client did something wrong (validation error, missing field, bad state).
  - 400 - Bad Request for invalid parameters
  - 404 - Not Found for missing objects
- 5xx – server or unknown error
  - 500 - Internal Server Error for unforseen exceptions and server errors

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
	- `...()`  -> supports only self-documentation with `GET [R]/`

**Examples**

Example 1: This specification
L(jhu)C(j)G(jh)U(j)D(jh): `/icecreams` - Icecream stock

translates into this implemented behavior:
- `GET /icecreams` - Self-documentation of `icecreams` endpoint with all actions
- `GET /icecreams?format=json` -> JSON array `[...]`
- `GET /icecreams?format=html` -> HTML detail view
- `GET /icecreams?format=ui` -> Interactive UI listing all icecreams with [Create], [Edit], [Delete] buttons for each item

- `GET /icecreams/create` - Self-documentation of `create` action
- `POST /icecreams/create` with JSON or form data -> Creates new icecream item and returns it as JSON object `{...}`
- `POST /icecreams/create?format=json` with JSON or form data -> Creates new icecream item and returns it as JSON object `{...}`
- `POST /icecreams/create?format=html` with JSON or form data -> HTTP 400 "ERROR: Response format 'html' not supported."
- `PUT /icecreams/create` with JSON or form data -> HTTP 400 "ERROR: HTTP method 'PUT' not supported."

- `GET /icecreams/get` - Self-documentation of `get` action
- `GET /icecreams/get?icecream_id={id}` -> JSON object `{...}`
- `GET /icecreams/get?icecream_id={id}?format=json` -> JSON object `{...}`
- `GET /icecreams/get?icecream_id={id}format=html` -> HTML detail view
- `GET /icecreams/get?icecream_id={id}format=ui` -> HTTP 400 "ERROR: Response format 'ui' not supported."
- `GET /icecreams/get?icecream_id={id}format=stream` -> HTTP 400 "ERROR: Response format 'stream' not supported."

- `GET /icecreams/update` - Self-documentation of `update` action
- `PUT /icecreams/update` with JSON or form data -> Updates icecream item and returns it as JSON object `{...}`
- `PUT /icecreams/update?format=json` with JSON or form data -> Updates icecream itemand returns it as JSON object `{...}`
- `PUT /icecreams/update?format=html` -> HTTP 400 "ERROR: Response format 'html' not supported."
- `POST /icecreams/update` with JSON or form data -> HTTP 400 "ERROR: HTTP method 'POST' not supported."
- `PATCH /icecreams/update` with JSON or form data -> HTTP 400 "ERROR: HTTP method 'PATCH' not supported."

- `GET /icecreams/delete` - Self-documentation of `delete` action
- `DELETE /icecreams/delete?icecream_id={id}` -> Deletes icecream item and returns it as JSON object `{...}`
- `GET /icecreams/delete?icecream_id={id}` -> Deletes icecream item and returns it as JSON object `{...}`
- `DELETE /icecreams/delete?icecream_id={id}?format=json` -> Deletes icecream item and returns it as JSON object `{...}`
- `DELETE /icecreams/delete?icecream_id={id}?format=html` -> Deletes icecream item and returns it as HTML detail view
- `GET /icecreams/delete?icecream_id={id}?format=html` -> Deletes icecream item and returns it as HTML detail view
- `DELETE /icecreams/delete?icecream_id={id}format=stream` -> HTTP 400 "ERROR: Response format 'stream' not supported."
- `PATCH /icecreams/delete?icecream_id={id}` with JSON or form data -> HTTP 400 "ERROR: HTTP method 'PATCH' not supported."

Example 2: This specification
L(jhu)G(jh): `/icecreams/flavours` - Available icecream flavours

translates into this implemented behavior:
- `GET /icecreams/flavours` - Self-documentation of `flavours` endpoint
- `GET /icecreams/flavours?format=json` -> JSON `{"data": {...}}`
- `GET /icecreams/flavours?format=html` -> HTML detail view
- `GET /icecreams/flavours?format=ui` -> Interactive UI listing all items with [View] button for each item
- `GET /icecreams/flavours/get`  - Self-documentation of `get` endpoint
- `GET /icecreams/flavours/get?flavour_id={id}` -> JSON `{"data": {...}}`
- `GET /icecreams/flavours/get?flavour_id={id}&format=json` -> JSON `{"data": {...}}`
- `GET /icecreams/flavours/get?flavour_id={id}&format=html` -> HTML detail view

### Specification of standard endpoints

Additions and exceptions are listed below the endpoint specification.

**Inventory**
- L(u): `/inventory` - UI for managing inventory 
- L(jhu)G(jh)D(jhs): `/inventory/files` - Files in the connected Open AI backend
- L(jhu)C(jhs)G(jh)U(jhs)D(jhs): `/inventory/vector_stores` - Vector stores in the connected Open AI backend
  - `DELETE /inventory/vector_stores/delete?vector_store_id={id}?mode={default|with_files}`
    - `mode=default` (default) - deletes vector store
    - `mode=with_files` - removes all files referenced by the vector store globally and then deletes vector store
- L(jh)G(jh)D(jhs): `/inventory/vector_stores/files` - Embedded files in vector stores in the connected Open AI backend
  - `DELETE /inventory/vector_stores/files/delete?vector_store_id={id}?file_id={id}?mode={default|delete_globally}`
    - `mode=default` (default) - removes file reference from vector store
    - `mode=delete_globally` - removes file reference from vector store and then deletes file globally
- L(jhu)C(jhs)G(jh)U(jhs)D(jhs): `/inventory/assistants` - Assistants in the connected Open AI backend
  - `DELETE /inventory/assistants/delete?assistant_id={id}?mode={default|with_files}`
    - `mode=default` (default) - deletes assistant
    - `mode=with_files` - if vector store is attached: deletes vector files globally, then vector store, then assistant
- L()C(jh)G(jh)D(jh): `/inventory/responses` - Model responses in the connected Open AI backend
  - `DELETE /inventory/assistants/delete?response_id={id}?mode={default|with_conversation}`
    - `mode=default` (default) - deletes model response
    - `mode=with_conversation` - if response has stored conversation: deletes stored conversation, then model response

**Domain**
- LCGUD: `/domains` - Knowledge domains to be used for crawling and semantic search

**Crawler**
- L: `/crawler`

**Jobs**
- LGD: `/jobs` - Manage long-running jobs that are triggered by other endpoints (crawler, inventory)
- `/jobs/control?job_id={id}?action=[Pause|Resume|Cancel]`


Action

All endpoints 



to support

The main routers should also support
- format=ui

and should be able to provide methods for the user to do everything: List / Create / update / show / delete objects and trigger lonng-running jobs that can be paused, resumed, canceled. 

We want for ALL endpoints a consistent self-documentation feature with GET.
We want long-running endpoints to provide monitoring and control via /jobs/monitor and /jobs/control endpoints. Those should also provide self-documentation. Another /jobs/result?job_id={job_id}&format=json or html should return only the "data" part in the <end_json>

For example:
- GET /inventory -> returns endpoint documentation
- GET /inventory?format=ui -> returns interactive UI

- GET /inventory/vector_stores -> returns endpoint documentation
- GET /inventory/vector_stores?format=ui -> returns interactive UI
- GET /inventory/vector_stores?format=json -> returns all vector stores as json
- GET /inventory/vector_stores?format=html -> returns all vector stores as html
- GET /inventory/vector_stores?format=stream -> returns all vector stores as stream

- DELETE /vector_stores/delete?vector_store_id=vs_123 -> deletes vector store and returns JSON
- DELETE /vector_stores/delete?vector_store_id=vs_123&format=json -> deletes vector store and returns JSON
- DELETE /vector_stores/delete?vector_store_id=vs_123&delete_files=true -> deletes all files in vector store, deletes vector store and returns JSON



- GET /domains -> returns endpoint documentation
- GET /domains?format=ui -> returns interactive UI
- GET /domains?format=json -> returns JSON
- GET /domains?format=html -> returns JSON formatted as HTML

- GET /domains/get -> returns endpoint documentation
- GET /domains/get?domain_id={domain_id} -> returns single domain as JSON
- GET /domains/get?domain_id={domain_id}&format=json -> returns single domain as JSON

- GET /domains/create -> returns endpoint documentation
- POST /domains/create with body json -> creates domain and returns JSON
- POST /domains/create with form data -> creates domain and returns JSON
- POST /domains/create?format=html with body json -> creates domain and returns HTML
- POST /domains/create?format=stream with body json -> creates domain and returns log stream

- GET /domains/update -> returns endpoint documentation
- PUT /domains/update?domain_id={domain_id} with body json -> updates domain and returns JSON
- PUT /domains/update?domain_id={domain_id} with form data -> updates domain and returns JSON
- PUT /domains/update?domain_id={domain_id}&format=html with body json -> updates domain and returns HTML
- PUT /domains/update?domain_id={domain_id}&format=stream with body json -> creates domain and returns log stream

- GET /domains/delete -> returns endpoint documentation
- DELETE /domains/delete?domain_id={domain_id} -> deletes domain and returns JSON
- DELETE /domains/delete?domain_id={domain_id}&format=html with body json -> deletes domain and returns HTML
- DELETE /domains/delete?domain_id={domain_id}&format=stream with body json -> deletes domain and returns log stream

- GET /domains/crawl  -> returns endpoint documentation
- GET /domains/crawl?domain_id={domain_id} -> returns an error describing the missing arguments (format)
- GET /domains/crawl?domain_id={domain_id}&format=json -> starts crawling and returns result data as JSON (job is logged for later monitoring)
- GET /domains/crawl?domain_id={domain_id}&format=stream -> starts crawling and returns job_id and job_url in <start_json>



Example json for getting a single domain (default format=json):
- GET /domains/get?id=TEST
```
{
  "result": "ok", "id": "TEST", "name": "Test Domain",
  ...
}
```

Example json for crawled domain:
- GET /domains/crawl?id={id}&format=json
```
{
  "result": "partial", "id": "TEST", "name": "Test Domain",
  ... , 
  "crawler": {
	"file_sources": [ ... ],
	"sitepage_sources": [ ... ],
	"list_sources": [ ... ]
  }
}
```

Example stream:
```
<start_json>
{"id": 42, "endpoint": "/resource/action", "state": "running", "job_url": "/jobs/monitor?job_id=42&format=stream" "started": "2025-11-27T11:30:00Z"}
</start_json>
<log>

[DETAILED_ERROR_LOG_TO_MONITOR_PROGRESS]

</log>
<end_json>
{"id": 42, "state": "completed", "finished": "2025-11-27T11:30:15",
  "data": {
	"result": "partial",
	[OTHER_DATA_RETURNED_BY_ENDPOINT]
  }
}
</end_json>
```

**start_json:**
- `id` - number - streaming job id (e.g. 1, 232, 103352)
- `endpoint` - string - endpoint url using slashes (e.g. "/domains/update", e.g. "/domains")
- `state` - string - "running", "paused", "completed", "cancelled"
- `started` - string - timestamp when job was started in UTC RFC3222 format (e.g. "2025-11-27T11:30:00Z")

**end_json:**
- `id` - number - streaming job id (e.g. 1, 232, 103352)
- `endpoint` - string - endpoint url using slashes (e.g. "/domains/update", e.g. "/domains")
- `state` - string - "running", "paused", "completed", "cancelled"
- `finished` - string - timestamp when job has finished in UTC RFC3222 format (e.g. "2025-11-27T11:30:00Z")

**data:** The JSON that is also returned by the endpoint with ?format=json
- `result` - string - "ok", "partial", "fail"
- [OTHER_DATA_RETURNED_BY_ENDPOINT] - returned data and objects