# Endpoint CRUD Specification V2

## Why Action-Suffixed (Option 2) over RESTful (Option 1)

**Option 1 (RESTful)** uses HTTP methods on resource URLs:
- `GET /domains/{id}` - get single
- `POST /domains` - create
- `PUT /domains/{id}` - update
- `DELETE /domains/{id}` - delete

**Problems with Option 1 for this project:**
- Self-documentation conflicts with list: `GET /domains` should return list, not docs
- Path params (`{id}`) require different routing than query params
- No natural place for long-running action endpoints like `/domains/crawl`
- HTMX form actions are simpler with explicit action URLs than path params
- Adding non-CRUD operations (crawl, sync, validate) breaks the REST model

**Option 2 (Action-Suffixed)** uses explicit action names:
- `GET /domains/get?id={id}` - get single
- `POST /domains/create` - create
- `PUT /domains/update?id={id}` - update
- `DELETE /domains/delete?id={id}` - delete

**Why Option 2 fits better:**
- Hybrid API: same endpoints serve both programmatic API (JSON) and interactive UI (HTMX)
- Single endpoint accepts both JSON body and form data (content-type detection)
- Bare `GET /endpoint` always returns documentation (consistent behavior)
- All endpoints use query params (uniform parsing)
- Easy to add action endpoints: `/domains/crawl`, `/domains/sync`
- HTMX forms work naturally with explicit URLs
- Self-documenting: URL shows intent without needing to check HTTP method

## Design Pattern

- Action-suffixed endpoints: `/resource`, `/resource/get`, `/resource/create`, `/resource/update`, `/resource/delete`
- Self-documentation on bare GET (no query params)
- Format param controls response: `json`, `html`, `ui` (list only), `stream` (long-running)
- Body accepts JSON or form data (content-type detection)

## Format Parameter

- **(none)** - Documentation: HTML with endpoint description
- **json** - API consumption: JSON object
- **html** - Read-only display / HTMX response: HTML content
- **ui** - Interactive UI (list endpoints only): HTML with HTMX forms and buttons
- **stream** - Long-running operations: SSE with `<start_json>`, `<log>`, `<end_json>`

## CRUD Endpoints Summary

### /domains - List

- `GET /domains` -> Documentation
- `GET /domains?format=json` -> `{"data": [...], "count": N}`
- `GET /domains?format=html` -> HTML table
- `GET /domains?format=ui` -> Interactive UI with [Create], [Edit], [Delete] buttons

### /domains/get - Get Single

- `GET /domains/get` -> Documentation
- `GET /domains/get?id={id}&format=json` -> `{"data": {...}}`
- `GET /domains/get?id={id}&format=html` -> HTML detail view
- `GET /domains/get?format=json` -> Error: missing id

### /domains/create - Create

- `GET /domains/create` -> Documentation
- `GET /domains/create?format=ui` -> Create form (HTMX modal)
- `POST /domains/create` + JSON body -> `{"message": "...", "data": {...}}`
- `POST /domains/create` + form body -> `{"message": "...", "data": {...}}`
- `POST /domains/create?format=html` + body -> HTML success message
- `POST /domains/create?format=stream` + body -> SSE stream (if long-running)

### /domains/update - Update

- `GET /domains/update` -> Documentation
- `GET /domains/update?id={id}&format=ui` -> Pre-filled update form
- `PUT /domains/update?id={id}` + JSON body -> `{"message": "...", "data": {...}}`
- `PUT /domains/update?id={id}` + form body -> `{"message": "...", "data": {...}}`
- `PUT /domains/update?id={id}&format=html` + body -> HTML success message

### /domains/delete - Delete

- `GET /domains/delete` -> Documentation
- `DELETE /domains/delete?id={id}` -> `{"message": "..."}`
- `DELETE /domains/delete?id={id}&format=html` -> Empty (HTMX row removal)

## Control Flow

### Documentation Flow
```
GET /domains/create
  └─> No format param?
      └─> Return HTML documentation
```

### Create Flow
```
POST /domains/create?format=json
  └─> Detect Content-Type header
      ├─> application/json -> Parse JSON body
      └─> form-urlencoded -> Parse form body
  └─> Validate required fields
      └─> Missing? -> Return 400 error
  └─> Check duplicates
      └─> Exists? -> Return 409 error
  └─> Save to storage
  └─> Return success response (format-dependent)
```

### Update Flow
```
PUT /domains/update?id=example01&format=json
  └─> Check id param
      └─> Missing? -> Return 400 error
  └─> Load existing item
      └─> Not found? -> Return 404 error
  └─> Parse body (JSON or form)
  └─> Validate fields
  └─> Save updated item
  └─> Return success response
```

### Delete Flow
```
DELETE /domains/delete?id=example01&format=html
  └─> Check id param
      └─> Missing? -> Return 400 error
  └─> Delete from storage
      └─> Not found? -> Return 404 error
  └─> Return success response
      └─> format=html -> Empty response (HTMX removes row)
      └─> format=json -> {"message": "..."}
```

## Data Flow Examples

### JSON Create
```
Request:
  POST /domains/create
  Content-Type: application/json
  {"id": "newdomain", "name": "New Domain", "vector_store_id": "vs_123"}

Response (200):
  {"message": "Domain 'newdomain' created successfully!", "data": {"id": "newdomain", ...}}

Response (409):
  {"error": "Domain 'newdomain' already exists"}
```

### Form Create (HTMX)
```
Request:
  POST /domains/create?format=html
  Content-Type: application/x-www-form-urlencoded
  id=newdomain&name=New Domain&vector_store_id=vs_123

Response (200):
  <div class="success-message">Domain created!<script>reload()</script></div>
```

### Delete (HTMX)
```
Request:
  DELETE /domains/delete?id=example01&format=html

Response (200):
  (empty - triggers hx-swap="outerHTML" to remove row)

Response (404):
  <tr><td colspan="5" class="error">Domain not found</td></tr>
```

## HTTP Status Codes

- `200` - Success
- `400` - Missing required parameter
- `404` - Resource not found
- `409` - Duplicate (create)
- `415` - Unsupported content type
- `500` - Server error
