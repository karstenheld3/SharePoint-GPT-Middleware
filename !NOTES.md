# Workspace Notes

[DEFAULT_SESSIONS_FOLDER]: [WORKSPACE_FOLDER]\_Sessions
[SESSION_ARCHIVE_FOLDER]: [SESSION_FOLDER]\_Archive
[BUGFIXES_FOLDER]: [DEFAULT_SESSIONS_FOLDER]\_BugFixes

## Test Configuration

**Selftest Configuration** (from `.env` file):
- `CRAWLER_SELFTEST_SHAREPOINT_SITE` - SharePoint site URL for crawler selftest
- `CRAWLER_SELFTEST_DOMAIN` - Domain name configured for selftest
- Used by `/v2/crawler/selftest` and Playwright MCP automated testing

## Patterns

**Async Generator / Step Function Result Pattern**
- See `docs/V2_INFO_IMPLEMENTATION_PATTERNS.md` "Step Function Result Pattern" section

**Report Type Naming Convention**
- See `docs/V2_INFO_IMPLEMENTATION_PATTERNS.md` "Report Type Naming Convention" section

## Dependency Management

**Always run `InstallAndCompileDependencies.bat` after adding new imports**
- Updates `pyproject.toml` dependencies
- Regenerates `requirements.txt` via `uv pip compile`
- Required for Azure deployment (Oryx build uses requirements.txt)

## Development Server

**Server restart only needed when startup sequence is affected**
- Router endpoint changes: NO restart needed (uvicorn `--reload` handles it)
- Changes to `app.py` startup code: Restart needed
- Changes to module imports in `create_app()`: Restart needed
- New routers or middleware: Restart needed

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
- `LOG` - Logging harmonization
- `V2CR` - V2 Crawler Endpoint

## Session Patterns

### V2 Doc-Sync Sessions

Sessions working on V2 routers copy SPEC/IMPL docs from `docs/routers_v2/` into the session folder for local editing.

**Pattern:**
- **Init**: Copy `docs/routers_v2/_V2_*.md` to session folder
- **Work**: Edit docs in session folder
- **Save/Close**: Copy modified `_V2_*.md` back to `docs/routers_v2/`

**Files to load on `/session-load`:**
- `docs/V2_INFO_IMPLEMENTATION_PATTERNS.md`
- `SOPS.md`

**Active sessions using this pattern:**
- `_Sessions/_2026-03-06_V2CrawlerEndpoint/`

### Bug and Issue Fixing

Run `/fix` workflow. See `.windsurf/workflows/fix.md` for 11-step process.

**Inputs**: Problem description or discovery mode (no args)

**Outputs by context**:

| Context | Folder | ID Format | Docs Updated |
|---------|--------|-----------|--------------|
| SESSION-MODE | `[SESSION_FOLDER]/BG-NNN_*/` | 3-digit (session-local) | SPEC, IMPL, TEST |
| PROJECT-MODE | `[BUGFIXES_FOLDER]/BG-NNNN_*/` | 4-digit (project-global) | SPEC, IMPL, TEST + `*_FIXES.md` |

**Guarantees**:
- `[BUG_FOLDER]` created with all artifacts (both contexts)
- Impact assessment before fix
- All impacted functionality tested before commit
- Commit message format: `fix(BG-NNN):` or `fix(BG-NNNN):`

**`_BugFixes` session** is persistent (never archived).