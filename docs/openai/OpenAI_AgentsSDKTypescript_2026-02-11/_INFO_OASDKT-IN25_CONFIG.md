# INFO: Configuring the SDK

**Doc ID**: OASDKT-IN25
**Goal**: Customize API keys, tracing, and logging behavior
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-DOCS-CONFIG` - Configuration documentation

## Summary

The SDK reads the `OPENAI_API_KEY` environment variable by default when first imported. If setting the variable is not possible, use `setDefaultOpenAIKey()` manually. You can also pass a custom OpenAI client instance via `setDefaultOpenAIClient()`. The SDK supports switching between the Responses API and Chat Completions API via `setOpenAIAPI()`. Tracing is enabled by default and can be configured with a separate key or disabled entirely. Debug logging uses the `debug` package - set `DEBUG=openai-agents*` for verbose logs.

## API Keys and Clients

### Default API Key

SDK reads `OPENAI_API_KEY` environment variable automatically: [VERIFIED]

```bash
export OPENAI_API_KEY=sk-...
```

### Manual Key Setting

```typescript
import { setDefaultOpenAIKey } from '@openai/agents';

setDefaultOpenAIKey(process.env.OPENAI_API_KEY!);
```

### Custom OpenAI Client

```typescript
import { OpenAI } from 'openai';
import { setDefaultOpenAIClient } from '@openai/agents';

const customClient = new OpenAI({
  baseURL: '...',
  apiKey: '...',
});

setDefaultOpenAIClient(customClient);
```

### Switching API Backend

Switch between Responses API and Chat Completions API: [VERIFIED]

```typescript
import { setOpenAIAPI } from '@openai/agents';

setOpenAIAPI('chat_completions');
```

## Tracing Configuration

### Default Behavior

Tracing is enabled by default using the OpenAI key. [VERIFIED]

### Separate Tracing Key

```typescript
import { setTracingExportApiKey } from '@openai/agents';

setTracingExportApiKey('sk-...');
```

### Disabling Tracing

```typescript
import { setTracingDisabled } from '@openai/agents';

setTracingDisabled(true);
```

Or via environment variable:

```bash
export OPENAI_AGENTS_DISABLE_TRACING=1
```

## Debug Logging

### Enabling Debug Logs

Uses the `debug` package: [VERIFIED]

```bash
export DEBUG=openai-agents*
```

### Session Persistence Logging

```bash
export OPENAI_AGENTS__DEBUG_SAVE_SESSION=1
```

### Custom Logger

```typescript
import { getLogger } from '@openai/agents';

const logger = getLogger('my-app');
logger.debug('something happened');
```

## Sensitive Data in Logs

### Disable Model Data Logging

```bash
export OPENAI_AGENTS_DONT_LOG_MODEL_DATA=1
```

### Disable Tool Data Logging

```bash
export OPENAI_AGENTS_DONT_LOG_TOOL_DATA=1
```

## Environment Variables Summary

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Default API key |
| `OPENAI_DEFAULT_MODEL` | Default model override |
| `OPENAI_AGENTS_DISABLE_TRACING` | Disable tracing |
| `DEBUG` | Enable debug logging |
| `OPENAI_AGENTS__DEBUG_SAVE_SESSION` | Log session persistence |
| `OPENAI_AGENTS_DONT_LOG_MODEL_DATA` | Disable model data in logs |
| `OPENAI_AGENTS_DONT_LOG_TOOL_DATA` | Disable tool data in logs |

## Limitations and Known Issues

- Environment variables must be set before SDK import [VERIFIED]
- Custom clients must implement OpenAI interface [VERIFIED]

## Gotchas and Quirks

- SDK reads OPENAI_API_KEY on first import [VERIFIED]
- setDefaultOpenAIKey() must be called before creating agents [VERIFIED]
- debug package namespaces are `openai-agents*` [VERIFIED]

## Best Practices

- Use environment variables for production [VERIFIED]
- Disable sensitive data logging in production [VERIFIED]
- Use separate tracing key if needed [VERIFIED]
- Enable debug logging only in development [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN16_TRACING.md` [OASDKT-IN16] - Tracing details
- `_INFO_OASDKT-IN03_MODELS.md` [OASDKT-IN03] - Model configuration

## API Reference

### Functions

- **setDefaultOpenAIKey(key)**
  - Import: `import { setDefaultOpenAIKey } from "@openai/agents"`

- **setDefaultOpenAIClient(client)**
  - Import: `import { setDefaultOpenAIClient } from "@openai/agents"`

- **setOpenAIAPI(api)**
  - Import: `import { setOpenAIAPI } from "@openai/agents"`
  - Values: `'responses'` | `'chat_completions'`

- **setTracingExportApiKey(key)**
  - Import: `import { setTracingExportApiKey } from "@openai/agents"`

- **setTracingDisabled(disabled)**
  - Import: `import { setTracingDisabled } from "@openai/agents"`

- **getLogger(namespace)**
  - Import: `import { getLogger } from "@openai/agents"`

## Document History

**[2026-02-11 20:45]**
- Initial document created
- API keys, tracing, and logging configuration documented
