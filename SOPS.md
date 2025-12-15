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

## Adding a new `/v2/` router

1. Determine router root format support using shorthand notation (see `_V2_SPEC_ROUTERS.md`):
  - `L(u)` = UI only (e.g., `/v2/inventory`, `/v2/crawler`)
  - `L(jhu)` = List with json, html, ui formats (e.g., `/v2/domains`)
  - Bare GET (no params) always returns self-documentation HTML
  - If not in spec: 1) ask user, 2) add to spec, 3) get user confirmation before implementation
2. Create router file in `src/routers_v2/` with `router`, `config`, `router_prefix`, `set_config(app_config, prefix)`
3. Add import in `src/app.py`
4. Add `app.include_router()` and `router.set_config(config, v2_router_prefix)` in `create_app()`
5. Implement root endpoint supporting formats as determined in step 1:
  - Bare GET (no params) -> self-documentation HTML
  - `format=ui` -> interactive UI
  - `format=json` -> JSON result with `{ok, error, data}`
  - `format=html` -> HTML table view
6. Add link to home page in `app.py` > `root()` available links section

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
5. Return self-documentation if no query params: `if len(request.query_params) == 0`
6. Implement consistent JSON result format: `{"ok": true/false, "error": "", "data": {...}}`
7. Use semantic identifier names: `job_id`, `domain_id`, `source_id`, `vector_store_id`
8. Support `dry_run=true` param for Create, Update, Delete actions
9. If router `/` endpoint shows documentation, add endpoint link there
10. Add link to home page in `app.py` > `root()` available links section

## Adding a `/v2/` streaming endpoint

Streaming endpoints support `format=stream` and create job files for long-running operations.

1. Follow "Adding a new `/v2/` endpoint" steps 1-10
2. Support `format=stream` returning SSE (Content-Type: `text/event-stream`)
3. Create job file using pattern: `[TIMESTAMP]_[[ACTION]]_[[JB_ID]]_[[OBJECT_ID]].[state]`
4. Emit `start_json` event with job metadata at stream start
5. Emit `log` events for progress (use `[ x / n ]` format for iterations)
6. Emit `end_json` event with job metadata and result at stream end
7. Check for control files (`.pause_requested`, `.resume_requested`, `.cancel_requested`) periodically
8. Handle state transitions: `running` -> `paused`/`cancelled`/`completed`
9. Yield pause/resume log events to HTTP stream (required for IG-05 byte-identical streams)
10. Store job files in `PERSISTENT_STORAGE_PATH/jobs/[router]/`