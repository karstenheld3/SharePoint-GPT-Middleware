# SharePoint-GPT-Middleware

A Python FastAPI-based middleware application that bridges SharePoint content with OpenAI's AI capabilities for Retrieval-Augmented Generation (RAG) use cases. The middleware crawls SharePoint sites (document libraries, lists, and site pages), processes content into LLM-friendly formats, and manages OpenAI vector stores for intelligent semantic search.

**Key Use Cases:**
- Enterprise knowledge bases with AI-powered search
- Document Q&A systems over SharePoint content
- Automated content synchronization between SharePoint and OpenAI
- Secure proxy for OpenAI APIs in controlled environments (where frontend must not store API keys)

## Features

### Core Capabilities

- **SharePoint Crawler**: Multi-step crawling process that downloads files from SharePoint, processes them for embedding, uploads to OpenAI, and creates vector store embeddings. Supports document libraries, lists (exported as Markdown), and site pages (cleaned HTML).
- **Knowledge Domains**: Logical groupings that combine documents, lists, and site pages from multiple SharePoint sites into unified searchable collections. Each domain maps to exactly one OpenAI vector store.
- **Semantic Search**: AI-powered search across embedded SharePoint content using OpenAI's file search capabilities with configurable result limits and temperature.
- **Change Detection**: Incremental crawling using immutable SharePoint file IDs (`sharepoint_unique_file_id`) to detect added, removed, and changed files.

### Administration

- **Interactive Web UI**: Browser-based administration for domains, jobs, and reports without requiring programming skills (V2 routers with `format=ui`).
- **Job Management**: Long-running operations (crawling, vector store updates) run as streaming jobs with pause/resume/cancel controls and real-time SSE monitoring.
- **Crawl Reports**: Timestamped ZIP archives capturing map file state at crawl completion for auditing and debugging.
- **Inventory Management**: Track and manage OpenAI resources (vector stores, files, assistants) with cleanup capabilities.

### Integration

- **OpenAI Proxy**: Full proxy for OpenAI APIs (Files, Vector Stores, Responses) enabling secure, controlled access to OpenAI services.
- **Flexible Authentication**: Support for Azure OpenAI (API key, managed identity, service principal) and direct OpenAI API.
- **Persistent Storage**: Organized file structure for domains, crawled content, map files, and logs (see [PERSISTENT_STORAGE_STRUCTURE.md](PERSISTENT_STORAGE_STRUCTURE.md)).

## Documentation

### User Documentation

- **[PERSISTENT_STORAGE_STRUCTURE.md](PERSISTENT_STORAGE_STRUCTURE.md)** - Detailed folder structure and file formats
- **[DATA_SOURCES.md](DATA_SOURCES.md)** - Data flow between SharePoint, local files, and vector stores
- **[CONFIGURE_CRAWLER.md](CONFIGURE_CRAWLER.md)** - Step-by-step guide to configure SharePoint crawler permissions
- **[SECURE_AZURE_APP_SERVICE.md](SECURE_AZURE_APP_SERVICE.md)** - Azure App Service security configuration

### Technical Specifications (docs/)

- **[docs/routers_v2/](docs/routers_v2/)** - V2 router specifications (crawler, domains, jobs, reports)
- **[docs/routers_v1/](docs/routers_v1/)** - V1 router specifications (legacy)

## Architecture

### Application Structure

```
src/
├── app.py                          # FastAPI application entry point
├── hardcoded_config.py             # Configuration constants
├── common_crawler_functions.py     # SharePoint crawler utilities
├── common_utility_functions.py     # Helper functions
├── routers_static/                 # Static routers (no version prefix)
│   ├── openai_proxy.py             # OpenAI API proxy endpoints
│   └── sharepoint_search.py        # AI-powered search endpoints (/query, /describe)
├── routers_v1/                     # V1 routers (mounted at /v1) - legacy
│   ├── crawler.py                  # SharePoint crawler endpoints
│   ├── domains.py                  # Domain management endpoints
│   ├── inventory.py                # Vector store inventory endpoints
│   ├── common_openai_functions_v1.py   # OpenAI client utilities
│   ├── common_sharepoint_functions_v1.py  # SharePoint access utilities
│   ├── common_ui_functions_v1.py   # Shared UI generation functions
│   └── common_job_functions_v1.py  # Shared job management functions
└── routers_v2/                     # V2 routers (mounted at /v2) - current
    ├── crawler.py                  # Crawling with streaming jobs
    ├── domains.py                  # Domain CRUD with interactive UI
    ├── sites.py                    # SharePoint site registration
    ├── jobs.py                     # Job monitoring and control
    ├── reports.py                  # Crawl report archives
    ├── common_ui_functions_v2.py   # Unified UI generation (HTMX/SSE)
    ├── common_job_functions_v2.py  # Streaming job infrastructure
    ├── common_report_functions_v2.py   # Report archive utilities
    ├── common_sharepoint_functions_v2.py  # SharePoint API access
    └── common_openai_functions_v2.py  # OpenAI API utilities
```

### Storage Structure

The application uses a persistent storage system to organize domains, crawled content, and logs. For detailed information about the storage structure, see **[PERSISTENT_STORAGE_STRUCTURE.md](PERSISTENT_STORAGE_STRUCTURE.md)**.

```
PERSISTENT_STORAGE_PATH/
├── domains/          # Domain configurations (domain.json, files_metadata.json)
├── sites/            # Registered SharePoint sites (site.json per site)
├── crawler/          # Crawled SharePoint content organized by domain/source
├── jobs/             # Streaming job files for long-running operations
├── reports/          # Crawl report archives (ZIP files with map snapshots)
└── logs/             # Application logs
```

## API Endpoints

### OpenAI Proxy (`/openai`)

Full proxy for OpenAI APIs with support for both Azure OpenAI and OpenAI services:

| API | Method | Path | Description |
| --- | --- | --- | --- |
| Responses | POST | `/openai/responses` | Create response |
| Responses | GET | `/openai/responses` | List responses |
| Responses | GET | `/openai/responses/{response_id}` | Get response |
| Responses | DELETE | `/openai/responses/{response_id}` | Delete response |
| Files | POST | `/openai/files` | Upload file |
| Files | GET | `/openai/files` | List files |
| Files | GET | `/openai/files/{file_id}` | Get file |
| Files | DELETE | `/openai/files/{file_id}` | Delete file |
| Files | GET | `/openai/files/{file_id}/content` | Get file content |
| Vector Stores | POST | `/openai/vector_stores` | Create vector store |
| Vector Stores | GET | `/openai/vector_stores` | List vector stores |
| Vector Stores | GET | `/openai/vector_stores/{vector_store_id}` | Get vector store |
| Vector Stores | POST | `/openai/vector_stores/{vector_store_id}` | Update vector store |
| Vector Stores | DELETE | `/openai/vector_stores/{vector_store_id}` | Delete vector store |
| Vector Store Files | POST | `/openai/vector_stores/{vector_store_id}/files` | Create vector store file |
| Vector Store Files | GET | `/openai/vector_stores/{vector_store_id}/files` | List vector store files |
| Vector Store Files | GET | `/openai/vector_stores/{vector_store_id}/files/{file_id}` | Get vector store file |
| Vector Store Files | DELETE | `/openai/vector_stores/{vector_store_id}/files/{file_id}` | Delete vector store file |

### SharePoint Search (`/`)

AI-powered search across SharePoint content:

| Endpoint | Method | Description |
| --- | --- | --- |
| `/query` | POST | Execute search query (JSON) |
| `/query2` | GET/POST | Execute search query (HTML/JSON) |
| `/describe` | GET | Get search configuration |
| `/describe2` | GET | Get search configuration (HTML/JSON) |

### Domain Management (`/v1/domains`)

Manage SharePoint domains and their vector stores:

| Endpoint | Method | Description |
| --- | --- | --- |
| `/v1/domains` | GET | List all domains (HTML/JSON/UI) |
| `/v1/domains/create` | GET/POST | Create new domain |
| `/v1/domains/update` | GET/PUT | Update domain configuration |
| `/v1/domains/delete` | DELETE | Delete domain |

### Crawler (`/v1/crawler`)

SharePoint content crawling and synchronization:

| Endpoint | Method | Description |
| --- | --- | --- |
| `/v1/crawler` | GET | Crawler UI and documentation |
| `/v1/crawler/localstorage` | GET | Local storage inventory (HTML/JSON/ZIP) |
| `/v1/crawler/list_sharepoint_files` | GET | List files from SharePoint source |
| `/v1/crawler/list_local_files` | GET | List local embedded files |
| `/v1/crawler/list_vectorstore_files` | GET | List files in domain vector store |
| `/v1/crawler/download_files` | GET | Download files from SharePoint |
| `/v1/crawler/update_vector_store` | GET | Update vector store with local files |
| `/v1/crawler/replicate_to_global` | GET | Replicate domain stores to global |
| `/v1/crawler/migrate_from_v2_to_v3` | GET | Migrate metadata format |

### Inventory (`/v1/inventory`)

Manage and inspect OpenAI resources:

| Endpoint | Method | Description |
| --- | --- | --- |
| `/v1/inventory` | GET | Inventory documentation |
| `/v1/inventory/vectorstores` | GET | List vector stores (HTML/JSON/UI) |
| `/v1/inventory/vectorstores/delete` | DELETE | Delete vector store |
| `/v1/inventory/vectorstore_files` | GET | List files in vector store |
| `/v1/inventory/vectorstore_files/remove` | DELETE | Remove file from vector store |
| `/v1/inventory/vectorstore_files/delete` | DELETE | Delete file from store and storage |
| `/v1/inventory/files` | GET | List all files (HTML/JSON/UI) |
| `/v1/inventory/files/delete` | DELETE | Delete file from storage |
| `/v1/inventory/assistants` | GET | List assistants (HTML/JSON/UI) |
| `/v1/inventory/assistants/delete` | DELETE | Delete assistant |

### Health & Status

| Endpoint | Method | Description |
| --- | --- | --- |
| `/` | GET | Application home page with links |
| `/alive` | GET | Health check endpoint |
| `/openaiproxyselftest` | GET | Run OpenAI proxy self-test |

### V2 Domains (`/v2/domains`)

Domain management with interactive UI and consistent action-suffixed endpoints:

| Endpoint | Method | Description |
| --- | --- | --- |
| `/v2/domains` | GET | Self-documentation (bare) or list domains (`format=json/html/ui`) |
| `/v2/domains/get` | GET | Get single domain configuration |
| `/v2/domains/create` | POST | Create new domain |
| `/v2/domains/update` | PUT | Update domain (supports ID rename) |
| `/v2/domains/delete` | GET/DELETE | Delete domain |

### V2 Crawler (`/v2/crawler`)

Crawling with streaming job support and map file management:

| Endpoint | Method | Description |
| --- | --- | --- |
| `/v2/crawler` | GET | Crawler UI (`format=ui`) or documentation |
| `/v2/crawler/crawl` | GET | Start crawl job (`format=stream` for SSE monitoring) |
| `/v2/crawler/download_data` | GET | Download step only (SharePoint to local) |
| `/v2/crawler/process_data` | GET | Process step only (convert formats) |
| `/v2/crawler/embed_data` | GET | Embed step only (upload to vector store) |

**Crawl parameters:** `domain_id`, `mode` (full/incremental), `scope` (all/files/lists/sitepages), `dry_run`

### V2 Jobs (`/v2/jobs`)

Monitor and control long-running streaming jobs:

| Endpoint | Method | Description |
| --- | --- | --- |
| `/v2/jobs` | GET | List all jobs (`format=json/html/ui`) |
| `/v2/jobs/get` | GET | Get job metadata |
| `/v2/jobs/monitor` | GET | Stream job output via SSE (`format=stream`) |
| `/v2/jobs/control` | GET | Pause/resume/cancel job (`action=pause/resume/cancel`) |
| `/v2/jobs/delete` | GET/DELETE | Delete job file |

### V2 Reports (`/v2/reports`)

Access crawl report archives for auditing:

| Endpoint | Method | Description |
| --- | --- | --- |
| `/v2/reports` | GET | List all reports (`format=json/html/ui`) |
| `/v2/reports/get` | GET | Get report metadata (report.json) |
| `/v2/reports/file` | GET | Get file from report archive |
| `/v2/reports/download` | GET | Download report as ZIP |
| `/v2/reports/delete` | GET/DELETE | Delete report archive |

### V2 Sites (`/v2/sites`)

Manage SharePoint sites registered with the middleware:

| Endpoint | Method | Description |
| --- | --- | --- |
| `/v2/sites` | GET | List all sites (`format=json/html/ui`) |
| `/v2/sites/get` | GET | Get single site configuration |
| `/v2/sites/create` | POST | Register new SharePoint site |
| `/v2/sites/update` | PUT | Update site configuration |
| `/v2/sites/delete` | GET/DELETE | Delete site registration |
| `/v2/sites/selftest` | GET | Run endpoint self-test (`format=stream` for SSE) |

### V2 Inventory (`/v2/inventory`)

Manage OpenAI backend resources:

| Endpoint | Method | Description |
| --- | --- | --- |
| `/v2/inventory` | GET | Inventory UI (`format=ui`) |
| `/v2/inventory/vector_stores` | GET | List vector stores |
| `/v2/inventory/vector_stores/files` | GET | List files in vector store |

## Dependencies

### Core Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| **fastapi** | 0.116.1 | Web framework for REST API endpoints |
| **uvicorn** | 0.35.0 | ASGI server with hot reload support |
| **openai** | 2.8.0 | OpenAI API client for vector stores and embeddings |
| **Office365-REST-Python-Client** | 2.6.2 | SharePoint REST API access for crawling |
| **azure-identity** | 1.15.0 | Azure AD authentication (managed identity, service principal) |
| **cryptography** | 41.0.7 | Certificate handling for SharePoint auth |
| **httpx** | 0.28.1 | Async HTTP client for API calls |
| **aiohttp** | 3.12.15 | Async HTTP for streaming responses |
| **python-dotenv** | 1.1.1 | Environment variable loading from .env |
| **python-multipart** | 0.0.20 | Form data parsing for file uploads |

### Development Dependencies

| Library | Purpose |
|---------|---------|
| **pytest** | Testing framework |
| **ruff** | Linting and formatting |

### Not Yet Used (Planned for Permission Scanner)

| Library | Purpose |
|---------|---------|
| **msgraph-sdk** | Microsoft Graph API for Azure AD group resolution |

## Configuration

The application is configured via environment variables. Copy `env-file-template.txt` to `.env` and configure:

### OpenAI Service

- **`OPENAI_SERVICE_TYPE`**: `openai` or `azure_openai`
- **Azure OpenAI**:
  - `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL
  - `AZURE_OPENAI_API_KEY`: API key (if using key authentication)
  - `AZURE_OPENAI_API_VERSION`: API version (default: `2025-04-01-preview`)
  - `AZURE_OPENAI_DEFAULT_MODEL_DEPLOYMENT_NAME`: Model deployment name
  - Authentication options:
    - Key: `AZURE_OPENAI_USE_KEY_AUTHENTICATION=true`
    - Service Principal: `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`
    - Managed Identity: `AZURE_OPENAI_USE_MANAGED_IDENTITY=true`, `AZURE_MANAGED_IDENTITY_CLIENT_ID`
- **OpenAI API**:
  - `OPENAI_API_KEY`: OpenAI API key
  - `OPENAI_ORGANIZATION`: Organization ID
  - `OPENAI_DEFAULT_MODEL_NAME`: Model name (default: `gpt-4o-mini`)

### SharePoint Crawler

- **`CRAWLER_CLIENT_ID`**: Azure AD app registration client ID
- **`CRAWLER_CLIENT_CERTIFICATE_PFX_FILE`**: Certificate file for authentication
- **`CRAWLER_CLIENT_CERTIFICATE_PASSWORD`**: Certificate password
- **`CRAWLER_TENANT_ID`**: Azure AD tenant ID

### Search Configuration

- **`SEARCH_DEFAULT_GLOBAL_VECTOR_STORE_ID`**: Default vector store for search
- **`SEARCH_DEFAULT_MAX_NUM_RESULTS`**: Maximum search results (default: 20)
- **`SEARCH_DEFAULT_TEMPERATURE`**: AI temperature (default: 0.0)
- **`SEARCH_DEFAULT_INSTRUCTIONS`**: Default search instructions
- **`SEARCH_DEFAULT_SHAREPOINT_ROOT_URL`**: SharePoint root URL

### Storage

- **`LOCAL_PERSISTENT_STORAGE_PATH`**: Local storage path (for local development)
- **`LOG_QUERIES_AND_RESPONSES`**: Enable detailed logging (default: false)

For complete configuration details, see `env-file-template.txt`.

## Setup and Deployment

### Run Locally

**Prerequisites:**
- Python 3.12
- PowerShell 7+ (Windows)
- Azure AD app registration with SharePoint permissions (for crawler)
- OpenAI API key or Azure OpenAI service

**Steps:**

1. **Create and populate `.env`**
   - Copy `env-file-template.txt` to `.env` at the repo root and fill in your values.

2. **Install dependencies** (choose one)
   
   **Option A:** Use helper batch file (recommended on Windows)
   ```bat
   .\InstallAndCompileDependencies.bat
   ```
   This creates `.venv`, installs uv, installs dependencies from `src/pyproject.toml` (editable), and generates `requirements.txt`.
   
   **Option B:** Manual installation
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -U pip
   pip install -r requirements.txt
   ```

3. **Run the API** (FastAPI/Uvicorn)
   
   From repo root:
   ```powershell
   python -m uvicorn app:app --app-dir src --host 0.0.0.0 --port 8000 --reload
   ```
   
   Access the application:
   - Home: http://localhost:8000/
   - Health check: http://localhost:8000/alive
   - API docs: http://localhost:8000/docs

4. **Run from VS Code** (alternative)
   
   **With debugger:**
   - Press `F5`
   - OR: Run and Debug panel → select `Python: FastAPI (Uvicorn)` → Start
   - Browser opens automatically to `/`
   
   **Without debugger:**
   - Terminal → Run Task → `Run API (Uvicorn)`
   - Optionally run the `Open Browser` task

### Deploy to Azure Web App

**Prerequisites:**
- Azure subscription and resource group
- Azure CLI and Az PowerShell module (scripts install if missing)
- `.env` file configured with Azure settings

**Steps:**

1. **Configure environment**
   - Ensure `.env` contains Azure deployment settings:
     - `AZURE_SUBSCRIPTION_ID`
     - `AZURE_TENANT_ID`
     - `AZURE_RESOURCE_GROUP`
     - `AZURE_APP_SERVICE_NAME`
     - `AZURE_LOCATION` (default: `swedencentral`)

2. **Provision and deploy**
   
   **Option A:** Use helper batch files (recommended)
   
   Create Azure resources (if not already created):
   ```bat
   .\CreateAzureAppService.bat
   ```
   
   Deploy current code to the Web App:
   ```bat
   .\DeployAzureAppService.bat
   ```
   
   (Optional) Delete the Web App and plan:
   ```bat
   .\DeleteAzureAppService.bat
   ```
   
   **Option B:** Run PowerShell script directly
   ```powershell
   .\DeployAzureAppService.ps1
   ```

**What the deployment script does:**
- Reads `.env` and sets app settings (excluding deployment-only keys)
- Sets startup command: `python -m uvicorn app:app --host 0.0.0.0 --port 8000`
- Sets `WEBSITES_PORT=8000` for proper traffic routing
- Packages `src/` plus root `requirements.txt` into `deploy.zip`
- Zip-deploys to Azure Web App (Oryx builds on server)

**Verify deployment:**

- Health check: `https://<APP_NAME>.azurewebsites.net/alive`
- Application: `https://<APP_NAME>.azurewebsites.net/`
- API docs: `https://<APP_NAME>.azurewebsites.net/docs`

**View logs:**
- Portal: `https://<APP_NAME>.scm.azurewebsites.net/api/logs/docker`
- CLI: `az webapp log tail --name <APP_NAME> --resource-group <RESOURCE_GROUP>`

**Troubleshooting:**
- Check Docker logs for Python import errors or missing packages
- Verify `.env` values are correct and complete
- Ensure Azure AD app has proper SharePoint permissions (for crawler)
- If changing port, update both startup command and `WEBSITES_PORT`
- Check persistent storage path is writable (Azure: `/home/data`)

## SharePoint Crawler Setup

To enable SharePoint crawling, you need to:

1. **Create Azure AD App Registration**
   - Register an app in Azure AD
   - Add SharePoint API permissions: `Sites.Read.All`
   - Create a certificate for authentication

2. **Configure Certificate**
   - Use `CreateSelfSignedCertificate.ps1` to generate a certificate
   - Upload certificate to Azure AD app registration
   - Place `.pfx` file in repo root
   - Set `CRAWLER_CLIENT_CERTIFICATE_PFX_FILE` and `CRAWLER_CLIENT_CERTIFICATE_PASSWORD` in `.env`

3. **Grant SharePoint Permissions**
   - Use `AddRemoveCrawlerSharePointSites.ps1` to grant site collection permissions
   - Use `AddRemoveCrawlerPermissions.ps1` to manage app permissions

4. **Create Domain Configuration**
   - Use `/domains/create` endpoint to create domain configurations
   - Configure SharePoint sources (document libraries, lists, site pages)
   - Each domain gets its own vector store

For detailed storage structure, see **[PERSISTENT_STORAGE_STRUCTURE.md](PERSISTENT_STORAGE_STRUCTURE.md)**.

## Usage Examples

### Search SharePoint Content

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find documents about project planning",
    "max_num_results": 10
  }'
```

### Create a Domain

```bash
curl -X POST "http://localhost:8000/v1/domains/create" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "domain_id=MYSITE&name=My SharePoint Site&description=Project documentation site&vector_store_name=SharePoint-MYSITE"
```

### Download Files and Update Vector Store

```bash
# Download files from SharePoint
curl "http://localhost:8000/v1/crawler/download_files?domain_id=MYSITE&format=json"

# Update vector store with downloaded files
curl "http://localhost:8000/v1/crawler/update_vector_store?domain_id=MYSITE&format=json"
```

## License

See [LICENSE](LICENSE) file for details.

## Related Documentation

- **[PERSISTENT_STORAGE_STRUCTURE.md](PERSISTENT_STORAGE_STRUCTURE.md)** - Detailed storage structure documentation
- **[DATA_SOURCES.md](DATA_SOURCES.md)** - Data flow between SharePoint, local files, and vector stores
- **[SECURE_AZURE_APP_SERVICE.md](SECURE_AZURE_APP_SERVICE.md)** - Azure App Service security configuration
