## When using OPENAI_SERVICE_TYPE=azure_openai in .env file

### /openaiproxyselftest - PARTIAL ❌ (32 passed, 7 failed)

```
❌ HTTP 404: /vector_stores/{id}/search (POST)
❌ OK: /vector_stores/{id}/files/{file_id} (GET with attributes) - attrs_count: 0; all_match: False
❌ OK: /vector_stores/{id}/files (GET list with attributes) - attrs_count: 0; all_match: False
❌ HTTP 404: /vector_stores/{id}/files/{file_id}/content (GET)
❌ HTTP 404: /vector_stores/{id}/files/{file_id} (POST update attributes)
❌ OK: /vector_stores/{id}/files/{file_id} (GET after update) - attrs_count: 0; all_match: False
❌ OK: /vector_stores/{id}/files (GET list after update) - attrs_count: 0; all_match: False
```


## When using OPENAI_SERVICE_TYPE=openai in .env file

None