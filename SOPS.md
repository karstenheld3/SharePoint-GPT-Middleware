# Standard Operating Procedures

## Adding a new `/v1/` router

1. Ask the user if the new router `/` endpoint (`root()`) should
  a) show the documentation of all router endpoints
  b) show a list of items
2. Create router file in `src/routers_v1/` with `router`, `config`, `router_prefix`, `set_config(app_config, prefix)`
3. Add import in `src/app.py`
4. Add `app.include_router()` and `router.set_config(config, v1_router_prefix)` in `create_app()`
5. Implement code skeleton for 1a) or 1b) depending on the users choice
6. Add link to home page in `app.py` > `root()` available links section

## Adding a new `/v1/` endpoint

1. Add `@router.get()` or `@router.post()` function
2. Add docstring with Parameters and Examples
3. Add `log_function_header()` / `log_function_footer()` calls
4. Return documentation page if no params provided
5. If router `/` endpoint (`root()`) shows documentation, add endpoint link there
6. Add link to home page in `app.py` > `root()` available links section

## V2 Router Navigation Consistency

All V2 routers with UI (`format=ui`) must use identical `main_page_nav_html` containing links to all main V2 endpoints:

```
Back to Main Page | Domains | Sites | Crawler | Jobs | Reports
```

When adding a new V2 router with UI:
1. Add its link to `main_page_nav_html` in ALL existing V2 routers
2. Copy the complete `main_page_nav_html` from an existing router (e.g., `domains.py`)

Files to update: `domains.py`, `sites.py`, `crawler.py`, `jobs.py`, `reports.py`

## Adding a new `/v2/` router

1. Determine router root format support using shorthand notation (see `_V2_SPEC_ROUTERS.md`):
  - `L(u)` = UI only (e.g., `/v2/inventory`, `/v2/crawler`)
  - `L(jhu)` = List with json, html, ui formats (e.g., `/v2/domains`)
  - Bare GET (no params) always returns self-documentation as plain text (UTF-8)
  - If not in spec: 1) ask user, 2) add to spec, 3) get user confirmation before implementation
2. Create router file in `src/routers_v2/[routername].py` with `router`, `config`, `router_prefix`, `set_config(app_config, prefix)`
  - Do NOT create `__init__.py` - use direct imports instead
3. Add import in `src/app.py`: `from routers_v2 import [routername]`
4. Add registration in `app.py` > `create_app()`:
  ```python
  app.include_router([routername].router, tags=["[Tag]"], prefix=v2_router_prefix)
  [routername].set_config(config, v2_router_prefix)
  ```
5. Implement root endpoint supporting formats as determined in step 1:
  - Bare GET (no params) -> minimalistic HTML with title, endpoint list with format links, back link
  - `format=ui` -> interactive UI
  - `format=json` -> JSON result with `{ok, error, data}`
  - `format=html` -> HTML table view
6. Add link to home page in `app.py` > `root()` available links section
7. Verify implementation against Python rules

## Adding a new `/v2/` endpoint

V2 endpoints follow action-suffixed pattern: `/resource/get`, `/resource/create`, `/resource/update`, `/resource/delete`

1. Determine endpoint type using shorthand notation (see `_V2_SPEC_ROUTERS.md`):
  - `L(jhu)` = List with json, html, ui formats
  - `G(jh)` = Get single with json, html formats
  - `C(jhs)` = Create with json, html, stream formats
  - `U(jhs)` = Update with json, html, stream formats
  - `D(jhs)` = Delete with json, html, stream formats
  - If not in spec: 1) ask user, 2) add to spec, 3) get user confirmation before implementation
2. Add `@router.get()`, `@router.post()`, `@router.put()`, or `@router.api_route()` function
3. Add docstring with Parameters and Examples using `{router_prefix}` placeholder
4. Add `log_function_header()` / `log_function_footer()` calls
5. Return plain text self-documentation if no query params: `if len(request.query_params) == 0` -> `PlainTextResponse`
6. Implement consistent JSON result format: `{"ok": true/false, "error": "", "data": {...}}`
7. Document the `format=json` result structure in the endpoint docstring:
    ```
    Result (format=json):
    {
      "ok": true,
      "error": "",
      "data": { ... }
    }
    ```
8. Use semantic identifier names: `job_id`, `domain_id`, `source_id`, `vector_store_id`
9. Support `dry_run=true` param for Create, Update, Delete actions
10. If router `/` endpoint shows documentation, add endpoint link there
11. Add link to home page in `app.py` > `root()` available links section
12. Verify implementation against Python rules

## Adding a `/v2/` streaming endpoint

Streaming endpoints support `format=stream` and create job files for long-running operations.

1. Follow "Adding a new `/v2/` endpoint" steps 1-10
2. Support `format=stream` returning SSE (Content-Type: `text/event-stream`)
3. Create job file using pattern: `[TIMESTAMP]_[[ACTION]]_[[JB_ID]]_[[OBJECT_ID]].[state]`
4. Emit `start_json` event with job metadata at stream start
5. Emit `log` events for progress (use `[ x / n ]` format for iterations)
6. Emit `state_json` events on pause/resume/cancel for UI synchronization
7. Emit `end_json` event with job metadata and result at stream end
8. Check for control files (`.pause_requested`, `.resume_requested`, `.cancel_requested`) periodically
9. Handle state transitions: `running` -> `paused`/`cancelled`/`completed`
10. Yield pause/resume state and log events to HTTP stream (required for IG-05 byte-identical streams)
11. Store job files in `PERSISTENT_STORAGE_PATH/jobs/[router]/`
12. Add link to home page in `app.py` > `root()` available links section
13. Document the `end_json` result format in the endpoint docstring:
    ```
    Result (end_json event):
    {
      "ok": true,
      "error": "",
      "data": { ... }
    }
    ```
14. Verify implementation against Python rules
