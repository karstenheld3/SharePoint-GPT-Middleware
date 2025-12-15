### Question 1 - Endpoint Semantics & Self-Documentation

A developer opens a browser and navigates to:

```
GET /v2/domains
```

No query parameters are provided.
What **must** the response be, and why?

------

### Question 2 - Action-Suffixed Behavior Validation

Given the shorthand specification:

```
L(jhu)C(j)G(jh)U(j)D(jh): /v2/icecreams
```

What should happen if a client sends:

```
PUT /v2/icecreams/create
```

------

### Question 3 - Format Handling & Error Discipline

An endpoint supports `G(jh)` only.
 A client sends:

```
GET /v2/resource/get?resource_id=123&format=ui
```

What is the correct behavior?

------

### Question 4 - Uniform Query Param Contract

Why does the specification insist on explicit query parameters like `domain_id`, `vector_store_id`, instead of generic `id`?

------

### Question 5 - Streaming vs Non-Streaming Endpoints

An endpoint supports `U(js)` and receives:

```
PUT /v2/resource/update?format=stream
```

What is the expected response type and MIME type?

------

### Question 6 - Job File Lifecycle & Control

A crawling job was started using this HTTP endpoint:
`GET /v2/crawler/crawl?domain_id=TEST01` -> returned in the JSON `"job_id": "jb_42"`
The job needs to be paused. What action enables this, and how is it detected?
Use the full storage path for example files.

------

### Question 7 - `jb_id` Generation Correctness

Describe the exact algorithm used to generate the next `jb_id`.

------

### Question 8 - Dry-Run Semantics

What must `dry_run=true` guarantee for a `DELETE` endpoint that supports it?

------

### Question 9 - Nested Resource Endpoint Interpretation

Interpret the meaning of this endpoint:

```
DELETE /v2/inventory/vector_stores/files/delete?vector_store_id=vs_1&file_id=f_9&mode=delete_globally
```

------

### Question 10 - Shorthand Specification to Behavior Mapping

Given:

```
L(jhu)G(jh): /v2/icecreams/flavours
```

List **all valid GET endpoints**, **all invalid format query params**, and **all invalid HTTP methods** that are used elsewhere in the spec but are not supported here.
