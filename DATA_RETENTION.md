# Data Retention

## Middleware Data Retention

### Downloaded Files

### Map Files

### Metadata Files

## Backend Data Retention

- The responses `store` flag must be set to `false` (default: `true`) [Link](https://platform.openai.com/docs/api-reference/responses/create#responses_create-store)
- Files uploaded for temporary use cases in the user context must be set to expire within the next 8 hours
- Temporary vector stores must be must be set to expire within the next 8 hours

### Assistants
- Assistant threads that are older than 8 hours must be deleted by jobs running every 8 hours
- Assistant messages that are older than 8 hours must be deleted by jobs running every 8 hours
  - All message attachments must be deleted with a message	