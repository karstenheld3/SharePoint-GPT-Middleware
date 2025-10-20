# SharePoint-GPT-Middleware

A FastAPI-based middleware application that bridges SharePoint content with OpenAI's AI capabilities. It crawls SharePoint sites (document libraries, lists, and site pages), processes the content, and manages OpenAI vector stores for intelligent search and retrieval.

## Features

- **SharePoint Crawler**: Automated crawling of SharePoint document libraries, lists, and site pages
- **OpenAI Proxy**: Full proxy for OpenAI APIs (Files, Vector Stores, Responses)
- **Intelligent Search**: AI-powered search across SharePoint content using OpenAI's file search
- **Domain Management**: Multi-domain support with isolated vector stores per SharePoint site
- **Inventory Management**: Track and manage vector stores, files, and assistants
- **Flexible Authentication**: Support for Azure OpenAI (key, managed identity, service principal) and OpenAI API
- **Persistent Storage**: Organized file structure for crawled content and metadata (see [PERSISTENT_STORAGE_STRUCTURE.md](PERSISTENT_STORAGE_STRUCTURE.md))

## Architecture

### Application Structure

```
src/
├── app.py                          # FastAPI application entry point
├── hardcoded_config.py             # Configuration constants
├── common_openai_functions.py      # OpenAI client utilities
├── common_crawler_functions.py     # SharePoint crawler utilities
├── utils.py                        # Helper functions
└── routers/
    ├── openai_proxy.py             # OpenAI API proxy endpoints
    ├── sharepoint_search.py        # AI-powered search endpoints
    ├── domains.py                  # Domain management endpoints
    ├── crawler.py                  # SharePoint crawler endpoints
    └── inventory.py                # Vector store inventory endpoints
```

### Storage Structure

The application uses a persistent storage system to organize domains, crawled content, and logs. For detailed information about the storage structure, see **[PERSISTENT_STORAGE_STRUCTURE.md](PERSISTENT_STORAGE_STRUCTURE.md)**.

```
PERSISTENT_STORAGE_PATH/
├── domains/          # Domain configurations and metadata
├── crawler/          # Crawled SharePoint content
└── logs/            # Application logs
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

### Domain Management (`/domains`)

Manage SharePoint domains and their vector stores:

| Endpoint | Method | Description |
| --- | --- | --- |
| `/domains` | GET | List all domains (HTML/JSON/UI) |
| `/domains/create` | GET/POST | Create new domain |
| `/domains/update` | GET/POST | Update domain configuration |
| `/domains/delete` | GET/POST | Delete domain |

### Crawler (`/crawler`)

SharePoint content crawling and synchronization:

| Endpoint | Method | Description |
| --- | --- | --- |
| `/crawler/updatemaps` | GET/POST | Crawl and update vector stores |
| `/crawler/localstorage` | GET | Download local storage as ZIP |
| `/crawler/getlogfile` | GET | Retrieve crawler log files |

### Inventory (`/inventory`)

Manage and inspect OpenAI resources:

| Endpoint | Method | Description |
| --- | --- | --- |
| `/inventory/vectorstores` | GET | List vector stores (HTML/JSON) |
| `/inventory/files` | GET | List files (HTML/JSON) |
| `/inventory/assistants` | GET | List assistants (HTML/JSON) |

### Health & Status

| Endpoint | Method | Description |
| --- | --- | --- |
| `/` | GET | Application home page with links |
| `/alive` | GET | Health check endpoint |
| `/openaiproxyselftest` | GET | Run OpenAI proxy self-test |


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
curl -X POST "http://localhost:8000/domains/create" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "MYSITE",
    "name": "My SharePoint Site",
    "description": "Project documentation site",
    "file_sources": [{
      "source_id": "docs",
      "site_url": "https://contoso.sharepoint.com/sites/MyProject",
      "sharepoint_url_part": "/Shared Documents"
    }]
  }'
```

### Crawl and Update Vector Store

```bash
curl -X POST "http://localhost:8000/crawler/updatemaps?domain_id=MYSITE"
```

## License

See [LICENSE](LICENSE) file for details.

## Related Documentation

- **[PERSISTENT_STORAGE_STRUCTURE.md](PERSISTENT_STORAGE_STRUCTURE.md)** - Detailed storage structure documentation
- **[SecureAzureAppService.md](SecureAzureAppService.md)** - Azure App Service security configuration
