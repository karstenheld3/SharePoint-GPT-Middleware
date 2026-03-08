# SPEC: Application Startup Sequence

**Doc ID**: STRT-SP01
**Goal**: Define the complete application startup sequence, task ordering, and settings propagation strategy
**Timeline**: Created 2026-03-06
**Target file**: `src/app.py`

**Depends on:**
- None (standalone specification)

## MUST-NOT-FORGET

- Startup order is critical - dependencies must be available before consumers
- Multi-worker environments require coordination via locks
- Config and SystemInfo are computed once at startup, not dynamically refreshed
- Routers receive config via `set_config()` after inclusion

## Table of Contents

1. [Scenario](#1-scenario)
2. [Context](#2-context)
3. [Startup Philosophy](#3-startup-philosophy)
4. [Startup Phases](#4-startup-phases)
5. [Detailed Task Sequence](#5-detailed-task-sequence)
6. [Domain Objects](#6-domain-objects)
7. [Multi-Worker Coordination](#7-multi-worker-coordination)
8. [Settings Propagation Strategy](#8-settings-propagation-strategy)
9. [Error Handling](#9-error-handling)
10. [Action Flow](#10-action-flow)
11. [Design Decisions](#11-design-decisions)
12. [Implementation Guarantees](#12-implementation-guarantees)
13. [Document History](#13-document-history)

## 1. Scenario

**Problem:** The SharePoint-GPT-Middleware application has complex initialization requirements:
- Multiple data sources (environment variables, persistent storage, zip archives)
- Multi-worker deployment on Azure App Service
- Dependencies between components (OpenAI client needs config, routers need config and system info)
- Startup tasks that should only run once across all workers (zip extraction)

**Solution:**
- Sequential initialization in `create_app()` with explicit ordering
- Lock-based coordination for single-execution tasks
- Config/SystemInfo objects populated at startup and shared via `app.state`
- Routers receive config after inclusion via `set_config()` pattern

**What we don't want:**
- Race conditions in multi-worker startup
- Partial initialization states where some routers have config and others don't
- Repeated execution of expensive one-time tasks (zip extraction)
- Silent failures that leave app in broken state

## 2. Context

The application runs as a FastAPI service, typically deployed to Azure App Service with multiple worker processes. Each worker independently executes the startup sequence when the application loads. The startup must:

1. Be deterministic - same inputs produce same outputs
2. Be idempotent for shared resources - safe if multiple workers start simultaneously
3. Be resilient - continue with partial functionality if non-critical components fail
4. Log comprehensively - provide visibility into startup progress

### Local Development vs Azure Web Service

The startup sequence adapts to two primary environments:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LOCAL DEVELOPMENT                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  Detection: WEBSITE_SITE_NAME env var NOT set                               │
│  Workers: Single process (uvicorn --reload)                                 │
│  Storage: LOCAL_PERSISTENT_STORAGE_PATH env var (you configure)             │
│  Auth: Service Principal or API keys from .env file                         │
│  Zip extraction: Runs but typically no zips present                         │
│  Credentials: .env file loaded via load_dotenv()                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  AZURE WEB SERVICE                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  Detection: WEBSITE_SITE_NAME env var IS set                                │
│  Workers: Multiple (2-4 depending on App Service plan)                      │
│  Storage: {HOME}/data (Windows) or /home/data (Linux container)             │
│  Auth: Managed Identity preferred, Service Principal fallback               │
│  Zip extraction: Critical - deploys domain configs, certificates            │
│  Credentials: Azure App Service Configuration (env vars)                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Differences by Startup Task:**

- **Environment Detection**
  - Local: `is_running_on_azure_app_service()` returns `False`
  - Azure: Returns `True` (checks `WEBSITE_SITE_NAME`)
- **PERSISTENT_STORAGE_PATH**
  - Local: From `LOCAL_PERSISTENT_STORAGE_PATH` env var
  - Azure: Auto-computed: `{HOME}/data` or `/home/data`
- **Worker Coordination**
  - Local: Not needed (single process)
  - Azure: Critical - prevents duplicate zip extraction
- **OpenAI Auth**
  - Local: API key or Service Principal
  - Azure: Managed Identity (IMDS) or Service Principal
- **Zip Extraction**
  - Local: Typically skipped (no zips)
  - Azure: Extracts domain configs, certs on deploy
- **Config Source**
  - Local: `.env` file
  - Azure: Azure App Service Configuration

**Environment Detection Logic:**
```python
def is_running_on_azure_app_service() -> bool:
    return os.path.exists("/home/site/wwwroot") or os.path.exists("/opt/startup") or os.path.exists("/home/site")
```

**PERSISTENT_STORAGE_PATH Computation:**
```python
if is_azure_environment:
    # Azure: Use HOME/data (survives deployments, shared across workers)
    if platform.system() == "Windows":
        path = os.path.join(os.getenv("HOME", r"d:\home"), "data")
    else:
        path = "/home/data"  # Linux container
else:
    # Local: Developer configures via env var
    path = os.getenv('LOCAL_PERSISTENT_STORAGE_PATH') or ""
```

**OpenAI Credential Selection:**
```
Local Development:
├─> If AZURE_OPENAI_USE_KEY_AUTHENTICATION: Use API key
├─> Elif Service Principal configured: Use ClientSecretCredential
└─> Else: Use DefaultAzureCredential (Azure CLI login)

Azure Web Service:
├─> If AZURE_OPENAI_USE_KEY_AUTHENTICATION: Use API key
├─> Elif AZURE_OPENAI_USE_MANAGED_IDENTITY: Use ManagedIdentityCredential
├─> Elif Service Principal configured: Use ClientSecretCredential
└─> Else: Use DefaultAzureCredential
```

**What Developers Must Configure (Local):**
- `LOCAL_PERSISTENT_STORAGE_PATH` - Where to store domains, reports, settings
- `.env` file with API keys and service principal credentials
- No zip files needed (data already in persistent storage)

**What DevOps Must Configure (Azure):**
- App Service Configuration with all env vars (no .env file)
- Managed Identity for secure OpenAI access
- Zip files in `src/.unzip_to_*` folders for deployment artifacts

## 3. Startup Philosophy

### Core Principles

**STRT-PH-01: Sequential Dependencies**
Each startup phase depends on the previous phase completing successfully. Configuration must be loaded before system info can use it. System info must exist before zip extraction can determine paths.

**STRT-PH-02: Fail-Safe, Not Fail-Fast**
The application attempts to start even if some components fail. Errors are collected in `initialization_errors` array and displayed on the home page, allowing partial functionality.

**STRT-PH-03: First-Worker-Wins for Shared Tasks**
Tasks that should only run once (zip extraction) use file-based locking. The first worker to acquire the lock performs the task; others skip it.

**STRT-PH-04: Config Immutability During Runtime**
Once `create_app()` completes, config and system info are frozen. They are not dynamically refreshed during request handling.

## 4. Startup Phases

The startup sequence consists of 7 distinct phases:

```
Phase 1: Bootstrap
├─> load_dotenv()           # Load .env file if present
├─> configure_logging()     # Suppress verbose SDK logs
└─> load_config()           # Read environment variables into Config dataclass

Phase 2: System Detection
├─> create_system_info()    # Detect environment, paths, resources
│   ├─> Detect CPU cores
│   ├─> Detect memory
│   ├─> Detect Azure vs Local environment
│   ├─> Determine OS platform
│   ├─> Compute PERSISTENT_STORAGE_PATH
│   ├─> Create directory if needed
│   └─> Get disk space info
└─> Store in app.state.system_info

Phase 3: Resource Extraction (Coordinated)
├─> acquire_startup_lock("zip_extraction")
├─> IF first worker:
│   ├─> Process clear-before folder (clear target, extract)
│   ├─> Process overwrite folder (extract, overwrite existing)
│   └─> Process if-newer folder (extract only newer files)
└─> ELSE: Skip (already done)

Phase 4: Cache Building
├─> build_domains_and_metadata_cache()
│   ├─> Read domain.json files from PERSISTENT_STORAGE_PATH/domains/
│   ├─> Read file_metadata.json from each domain
│   └─> Build in-memory caches
└─> Store in app.state.domains, app.state.metadata_cache

Phase 5: Middleware Setup
└─> Add CORSMiddleware (allow all origins)

Phase 6: Client Creation
├─> Determine OpenAI service type (azure_openai or openai)
├─> Create appropriate credential
│   ├─> Azure Key Authentication
│   ├─> Managed Identity
│   ├─> Service Principal
│   └─> Default Credential Chain
├─> Create async OpenAI client
└─> Store in app.state.openai_client

Phase 7: Router Registration
├─> Static routers (openai_proxy, sharepoint_search)
├─> V1 routers (inventory, crawler, domains)
├─> V2 routers (demorouter1, demorouter2, jobs, domains_v2, sites_v2, reports, crawler_v2)
├─> Mount static files directory
└─> Log initialization summary
```

## 5. Detailed Task Sequence

### Task 1: Environment Loading
```python
load_dotenv()
```
- **Purpose**: Load local `.env` file for development
- **When**: Module import time (before create_app)
- **Dependencies**: None
- **Outputs**: Environment variables available via `os.environ`

### Task 2: Logging Configuration
```python
configure_logging()
```
- **Purpose**: Suppress verbose Azure SDK, OpenAI, and HTTP client logs
- **When**: First action in `create_app()`
- **Loggers suppressed**: azure, msal, urllib3, requests, httpx, openai, httpcore

### Task 3: Config Loading
```python
config = load_config()
```
- **Purpose**: Read all environment variables into typed Config dataclass
- **When**: After logging configured
- **Outputs**: Config object with 30+ fields covering OpenAI, Azure, SharePoint, Crawler settings
- **Storage**: `app.state.config`

### Task 4: FastAPI Instance Creation
```python
app = FastAPI(title="SharePoint-GPT-Middleware")
```
- **Purpose**: Create the FastAPI application instance
- **When**: After config loaded

### Task 5: System Info Detection
```python
system_info = create_system_info()
```
- **Purpose**: Detect runtime environment and compute paths
- **Substeps**:
  - Detect CPU cores (platform-specific)
  - Detect total/free memory (Windows: ctypes, Linux: sysconf)
  - Detect environment (Azure vs Local via `is_running_on_azure_app_service()`)
  - Detect OS platform (Windows vs Linux)
  - Compute `PERSISTENT_STORAGE_PATH`:
    - Azure: `{HOME}/data` or `/home/data`
    - Local: `LOCAL_PERSISTENT_STORAGE_PATH` env var
  - Create directory if missing
  - Get disk space info
- **Storage**: `app.state.system_info`

### Task 6: Path Validation
```python
# Validate APP_SRC_PATH and PERSISTENT_STORAGE_PATH
```
- **Purpose**: Validate APP_SRC_PATH and PERSISTENT_STORAGE_PATH exist
- **On failure**: Add to `initialization_errors`, skip zip extraction

### Task 7: Zip Extraction (Coordinated)
```python
with acquire_startup_lock("zip_extraction", ...) as should_proceed:
```
- **Purpose**: Extract deployment artifacts to persistent storage
- **Coordination**: File-based lock ensures only first worker extracts
- **Three extraction modes**:
  - `clear-before`: Clear target directory, then extract (deployment reset)
  - `overwrite`: Extract and overwrite existing files
  - `if-newer`: Extract only if source file is newer than target
- **Safety check**: Skip clear-before if LOCAL_PERSISTENT_STORAGE_PATH equals PERSISTENT_STORAGE_PATH

### Task 8: Domain/Metadata Cache Building
```python
domains_cache, metadata_cache = build_domains_and_metadata_cache(...)
```
- **Purpose**: Load domain configurations and file metadata into memory
- **Source**: `PERSISTENT_STORAGE_PATH/domains/{domain_id}/domain.json`
- **Storage**: `app.state.domains`, `app.state.metadata_cache`

### Task 9: CORS Middleware
```python
app.add_middleware(CORSMiddleware, ...)
```
- **Purpose**: Enable cross-origin requests
- **Config**: Allow all origins, credentials, methods, headers

### Task 10: OpenAI Client Creation
```python
# Create appropriate async OpenAI client based on config
```
- **Purpose**: Create appropriate async OpenAI client based on config
- **Decision tree**:
  1. If `azure_openai` service type:
     - If key auth: Use API key
     - If managed identity: Use ManagedIdentityCredential (Azure) or fallback (local)
     - If service principal: Use ClientSecretCredential
     - Else: Use DefaultAzureCredential
  2. Else: Use standard OpenAI client
- **Storage**: `app.state.openai_client`

### Task 11: Router Registration
```python
# Register all API routers with their prefixes
```
- **Purpose**: Register all API routers with their prefixes
- **Pattern**: For each router:
  1. `app.include_router(router, tags=[...], prefix="...")`
  2. `router_module.set_config(config, prefix)`
- **Order**:
  - Static: openai_proxy (`/openai`), sharepoint_search (`/`)
  - V1: inventory, crawler, domains (all at `/v1`)
  - V2: demorouter1, demorouter2, jobs, domains_v2, sites_v2, reports, crawler_v2 (all at `/v2`)

### Task 12: Static Files Mount
```python
app.mount("/static", StaticFiles(...), name="static")
```
- **Purpose**: Serve CSS, JS, and other static assets
- **Path**: `{APP_SRC_PATH}/static`

### Task 13: Initialization Summary
```python
# Log final status and any accumulated errors
```
- **Purpose**: Log final status and any accumulated errors
- **Output**: Success message or list of component errors

## 6. Domain Objects

### Config
A **Config** represents the application's runtime configuration loaded from environment variables.

**Definition**: Dataclass in `app.py` (lines 40-70)

**Key properties:**
- `OPENAI_SERVICE_TYPE` - "azure_openai" or "openai"
- `AZURE_OPENAI_*` - Azure OpenAI connection settings
- `CRAWLER_*` - SharePoint crawler authentication
- `SEARCH_DEFAULT_*` - Default search parameters
- `LOCAL_PERSISTENT_STORAGE_PATH` - Override for local development

### SystemInfo
A **SystemInfo** represents runtime environment detection results.

**Definition**: Dataclass in `app.py` (lines 28-38)

**Key properties:**
- `ENVIRONMENT` - "Azure" or "Local"
- `OS_PLATFORM` - "Windows" or "Linux"
- `PERSISTENT_STORAGE_PATH` - Computed path for data storage
- `APP_SRC_PATH` - Path to application source code
- Memory and disk space metrics

### InitializationError
An **InitializationError** tracks a component failure during startup.

**Definition**: Dict with `component` and `error` keys
**Storage**: Global `initialization_errors` list

## 7. Multi-Worker Coordination

### Lock Mechanism

The `acquire_startup_lock()` context manager provides coordination:

```python
with acquire_startup_lock(task_name, log_data, timeout_seconds) as should_proceed:
    if should_proceed:
        # First worker - do the work
    else:
        # Another worker already did it - skip
```

**Implementation** (in `common_utility_functions.py`):
- Lock file: `{tempdir}/{task_name}.lock`
- Done file: `{tempdir}/{task_name}.done`
- If done file exists: Return False (already completed)
- If lock acquired: Do work, create done file, return True
- If lock timeout: Return False (another worker handling it)

### Race Condition Prevention

**Scenario**: 4 workers start simultaneously
1. Worker 1 acquires lock, starts zip extraction
2. Workers 2-4 wait for lock (configurable timeout)
3. Worker 1 completes, creates `.done` file, releases lock
4. Workers 2-4 see `.done` file, skip extraction

## 8. Settings Propagation Strategy

### Current Strategy (V1)

**STRT-PS-01: App State Pattern**
Config and SystemInfo stored in `app.state` for request-time access:
```python
app.state.config = config
app.state.system_info = system_info
app.state.openai_client = openai_client
app.state.domains = domains_cache
app.state.metadata_cache = metadata_cache
```

**STRT-PS-02: Router set_config Pattern**
Each router receives config via module-level function:
```python
app.include_router(router_module.router, ...)
router_module.set_config(config, prefix)
```
Router stores config in module-level variable for endpoint access.

### Implications for Consumers

**Access at request time:**
```python
@router.get("/endpoint")
async def endpoint(request: Request):
    config = request.app.state.config
    system_info = request.app.state.system_info
```

**Access in router module:**
```python
# Module level
_config = None
_router_prefix = ""

def set_config(config, router_prefix):
    global _config, _router_prefix
    _config = config
    _router_prefix = router_prefix

def get_persistent_storage_path():
    return _config.LOCAL_PERSISTENT_STORAGE_PATH or ""
```

### Future Strategy (V2 Settings)

The V2 Settings system (`_SPEC_SETTINGS.md [V2ST-SP01]`) will introduce:
- Settings stored in module-level variable, not app.state
- Hot-reload capability via reload signals
- Bootstrap from environment or stored config file

## 9. Error Handling

### Error Collection Pattern

Errors during startup don't crash the application. Instead:
```python
try:
    # Component initialization
except Exception as e:
    initialization_errors.append({"component": "Component Name", "error": str(e)})
```

### Error Visibility

- Logged at startup completion
- Displayed on home page (`/`) in Errors section
- Accessible via `initialization_errors` global

### Critical vs Non-Critical

**Critical (blocks functionality):**
- PERSISTENT_STORAGE_PATH not set or not found
- APP_SRC_PATH not found

**Non-Critical (partial degradation):**
- OpenAI client creation failed (search won't work)
- Individual router registration failed (that router's endpoints unavailable)
- Static files directory not found (CSS/JS won't load)

## 10. Action Flow

```
Python interpreter loads app.py
├─> load_dotenv()                           # Load .env
├─> Import statements execute
│   └─> Router modules imported (routers define their routes)
└─> app = create_app()                      # Module-level call
    ├─> configure_logging()
    ├─> config = load_config()
    ├─> app = FastAPI(...)
    ├─> app.state.config = config
    ├─> system_info = create_system_info()
    ├─> app.state.system_info = system_info
    ├─> [ZIP EXTRACTION - coordinated]
    ├─> domains_cache, metadata_cache = build_domains_and_metadata_cache()
    ├─> app.state.domains = domains_cache
    ├─> app.state.metadata_cache = metadata_cache
    ├─> app.add_middleware(CORSMiddleware, ...)
    ├─> openai_client = [CREATE CLIENT]
    ├─> app.state.openai_client = openai_client
    ├─> [REGISTER ROUTERS - each with set_config()]
    ├─> app.mount("/static", ...)
    ├─> [LOG SUMMARY]
    └─> return app

Uvicorn receives app
├─> Starts server process
├─> Application startup complete
└─> Ready to handle requests
```

## 11. Design Decisions

**STRT-DD-01:** Use dataclasses for Config and SystemInfo. Rationale: Type safety, IDE support, explicit field definitions.

**STRT-DD-02:** Store config in app.state, not globals. Rationale: FastAPI pattern, testability, request-scoped access.

**STRT-DD-03:** Use file-based locks, not database locks. Rationale: No database dependency at startup, works across processes, simple implementation.

**STRT-DD-04:** Collect errors instead of failing fast. Rationale: Partial functionality better than complete failure, easier debugging via home page error display.

**STRT-DD-05:** Sequential router registration order. Rationale: Deterministic startup, easy to trace in logs.

**STRT-DD-06:** set_config() pattern for routers. Rationale: Routers can use config at module level for path computations, not just request time.

## 12. Implementation Guarantees

**STRT-IG-01:** Config is fully populated before any router receives it via set_config()
**STRT-IG-02:** SystemInfo.PERSISTENT_STORAGE_PATH is computed before zip extraction
**STRT-IG-03:** Zip extraction completes (or skips) before domain cache building
**STRT-IG-04:** All routers registered before static files mounted
**STRT-IG-05:** Initialization errors array populated before create_app() returns
**STRT-IG-06:** Startup sequence is synchronous - no async operations in create_app()

## 13. Document History

**[2026-03-08 16:05]**
- Fixed: Removed dependency on reverted `_SPEC_SETTINGS.md`
- Fixed: Updated `is_running_on_azure_app_service()` to match implementation (path-based detection)
- Fixed: Removed `settings_v2` from V2 router list (reverted feature)
- Fixed: Removed specific line number references (prone to drift)

**[2026-03-06 21:50]**
- Fixed: Converted Markdown table to list format (V-01 from /verify)

**[2026-03-06 21:45]**
- Added: "Local Development vs Azure Web Service" subsection in Context
- Added: Comparison list, code examples, and configuration checklists for both environments

**[2026-03-06 21:40]**
- Initial specification created
- Documented 7 startup phases and 13 tasks
- Added multi-worker coordination section
- Added settings propagation strategy for V1 and V2
