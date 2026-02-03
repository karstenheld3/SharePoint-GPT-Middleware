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
