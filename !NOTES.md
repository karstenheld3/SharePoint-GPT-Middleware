# Workspace Notes

[DEFAULT_SESSIONS_FOLDER]: [WORKSPACE_FOLDER]\_Sessions
[SESSION_ARCHIVE_FOLDER]: [SESSION_FOLDER]\_Archive

## Test Configuration

**Test Domain for Playwright MCP**: `AiSearchTest01`
- 5 sources configured (SharedDocuments, DocumentLibrary01, DocumentLibrary02, SecurityTrainingCatalog, SitePages)
- Use for automated testing with Playwright MCP

## Patterns

**Async Generator for Realtime SSE Streaming**
- Step functions use `AsyncGenerator[str, None]` return type
- Yield SSE events via `for sse in writer.drain_sse_queue(): yield sse`
- Store result via `writer.set_step_result(result)`
- Caller retrieves via `writer.get_step_result()` after iteration
- See `_V2_IMPL_CRAWLER.md` "Step function result handling" section

**Report Type Naming Convention**
- Use **singular** form for `report_type` parameter: `"site_scan"`, `"crawl"`, `"custom"`
- `get_folder_for_type()` in `common_report_functions_v2.py` adds the 's' suffix automatically
- Passing plural form (e.g., `"site_scans"`) results in double suffix (`"site_scanss"`)

## Dependency Management

**Always run `InstallAndCompileDependencies.bat` after adding new imports**
- Updates `pyproject.toml` dependencies
- Regenerates `requirements.txt` via `uv pip compile`
- Required for Azure deployment (Oryx build uses requirements.txt)

## Environment

**Windows - No grep**: Use PowerShell alternatives:
- `Select-String "pattern" file.txt` (like grep)
- `Get-Content file.txt | Select-String "pattern"` (piped)
- `(Get-Content file.txt -Raw) -match "pattern"` (regex match)

## Batch Files

All batch files are in the workspace root. Double-click to run or execute from terminal.

**Development:**
- `InstallAndCompileDependencies.bat` - Install dependencies, regenerate `requirements.txt`
- `Windsurf.bat` - Launch Windsurf IDE with workspace

**Azure Deployment:**
- `CreateAzureAppService.bat` - Create new Azure App Service (first-time setup)
- `DeployAzureAppService.bat` - Deploy code to Azure App Service
- `DeleteAzureAppService.bat` - Delete Azure App Service

**Configuration:**
- `AddRemoveCrawlerPermissions.bat` - Manage Entra ID app permissions
- `AddRemoveCrawlerSharePointSites.bat` - Manage Sites.Selected permissions
- `CreateSelfSignedCertificateRunAsAdmin.bat` - Generate certificate (run as admin)

**Environment Switching:**
- `Set-OpenAi-Env.bat` - Use OpenAI API
- `Set-AzureOpenAiService-Env.bat` - Use Azure OpenAI Service
- `Set-AzureOpenAiProject-Env.bat` - Use Azure OpenAI Project

## Folder Conventions

**POC Scripts**: All Proof of Concept scripts go in `./src/pocs/[poc_name]/`
- NOT under routers_v2 or other folders
- Each POC gets its own subfolder

## Topic Registry

- `SSE` - Server-Sent Events streaming
- `CRWL` - Crawler operations
- `GLOB` - Global/workspace-wide
- `SITE` - SharePoint Sites management
- `PSCP` - Permission Scanner POC
- `V2FX` - V2 Endpoint Fixes
