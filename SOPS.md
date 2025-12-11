# Standard Operating Procedures

## Adding a New Router

1. Ask the user if the new router `/` endpoint (`root()`) should
  a) show the documentation of all router endpoints
  b) show a list of items
2. Create router file in `src/routers/` with `router`, `config`, `set_config()`
3. Add import in `src/app.py`
4. Add `app.include_router()` in `create_app()`
5. Implement code skeleton for 1a) or 1b) depending on the users choice
6. Add link to home page in `app.py` > `root()` available links section

## Adding a New Endpoint

1. Add `@router.get()` or `@router.post()` function
2. Add docstring with Parameters and Examples
3. Add `log_function_header()` / `log_function_footer()` calls
4. Return documentation page if no params provided
5. If router `/` endpoint (`root()`) shows documentation, add endpoint link there
5. Add link to home page in `app.py` > `root()` available links section