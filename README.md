# SharePoint-GPT-Middleware
An Azure Web App in Python to crawl the content of SharePoint sites into OpenAI Vector Stores

### OpenAI proxy base path

All proxy endpoints are now served under the `/openai` base path. Examples:

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


### How to run and deploy this app

#### Run locally

Prerequisites:
- Python 3.12
- PowerShell 7+

Steps:
1) Create and populate `.env`
   - Copy `env-file-template.txt` to `.env` at the repo root and fill values.

2) Install dependencies (choose one)
   - Option A: Use helper batch file at repo root (recommended on Windows)
     ```bat
     .\InstallAndCompileDependencies.bat
     ```
     This creates `.venv`, installs uv, installs dependencies from `src/pyproject.toml` (editable), generates `requirements.txt` at repo root and also writes a copy to `src\requirements.txt`.
   - Option B: Manual commands
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     pip install -U pip
     pip install -r requirements.txt
     ```

3) Run the API (FastAPI/Uvicorn)
   - From repo root:
     ```powershell
     python -m uvicorn app:app --app-dir src --host 0.0.0.0 --port 8000 --reload
     ```
   - Health check: http://localhost:8000/alive

4) Run from VS Code (alternative)
   - With debugger:
     - Press F5
     - OR: Run and Debug panel → select `Python: FastAPI (Uvicorn)` → Start. The browser opens to `/` automatically.
   - Without debugger:
     - Terminal → Run Task → `Run API (Uvicorn)`.
     - Optionally run the `Open Browser` task to open the site.

#### Deploy to Azure Web App (build on server)

Prerequisites:
- Azure subscription, resource group, and Linux Web App created (or let scripts create them).
- Azure CLI and Az PowerShell module (the deploy script installs them if missing).

Steps:
1) Configure environment
   - Ensure `.env` at repo root contains required values (tenant, subscription, app name, etc.).

2) Provision and deploy (choose one)
   - Option A: Use helper batch files at repo root
     - Create Azure resources (App Service plan + Web App) if not already created:
       ```bat
       .\CreateAzureWebApp.bat
       ```
     - Deploy current code to the Web App:
       ```bat
       .\DeployAzureWebApp.bat
       ```
     - (Optional) Delete the Web App and plan:
       ```bat
       .\DeleteAzureWebApp.bat
       ```
   - Option B: Run PowerShell deploy script directly
     ```powershell
     .\DeployAzureWebApp.ps1
     ```

What the script does:
- Reads `.env` and sets app settings (excluding deployment-only keys).
- Sets startup command to run Uvicorn: `python -m uvicorn app:app --host 0.0.0.0 --port 8000`.
- Sets `WEBSITES_PORT=8000` so the platform routes traffic correctly.
- Packages `src/` plus root `requirements.txt` into `deploy.zip`.
- Zip-deploys to the Web App and lets Oryx build on the server (installs dependencies from `requirements.txt`).

Verify after deploy:
- Health: `https://<APP_NAME>.azurewebsites.net/alive`
- Logs (Docker):
  - Portal: `https://<APP_NAME>.scm.azurewebsites.net/api/logs/docker`
  - CLI: `az webapp log tail --name <APP_NAME> --resource-group <RESOURCE_GROUP>`

Troubleshooting tips:
- If the site fails startup, check Docker logs for Python import errors or missing packages.
- Ensure `.env` values are present and correct.
- If changing the port, update both the startup command and `WEBSITES_PORT`.
