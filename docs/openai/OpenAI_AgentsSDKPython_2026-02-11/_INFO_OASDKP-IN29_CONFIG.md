# INFO: SDK Configuration

**Doc ID**: OASDKP-IN29
**Goal**: Document global SDK configuration options
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-CONFIG` - SDK configuration documentation

## Summary

The OpenAI Agents SDK provides global configuration functions for API keys, clients, tracing, and logging. By default, the SDK uses the `OPENAI_API_KEY` environment variable and the Responses API. Configuration can be customized at startup using `set_default_*` functions or per-run via `RunConfig`. Debug logging can be enabled for troubleshooting, with options to exclude sensitive data. [VERIFIED]

## API Key Configuration

### Environment Variable (Default)

```bash
export OPENAI_API_KEY=sk-your-key-here
```

### Programmatic Configuration

```python
from agents import set_default_openai_key

set_default_openai_key("sk-...")
```

## Custom OpenAI Client

Use a custom `AsyncOpenAI` client:

```python
from openai import AsyncOpenAI
from agents import set_default_openai_client

custom_client = AsyncOpenAI(
    base_url="https://custom-endpoint.example.com",
    api_key="sk-...",
)
set_default_openai_client(custom_client)
```

### Use Cases

- Custom base URL (proxies, Azure)
- Custom timeouts
- Custom HTTP settings

## API Selection

Switch between Responses API and Chat Completions API:

```python
from agents import set_default_openai_api

# Use Responses API (default)
set_default_openai_api("responses")

# Use Chat Completions API
set_default_openai_api("chat_completions")
```

## Tracing Configuration

### Set Tracing API Key

```python
from agents import set_tracing_export_api_key

set_tracing_export_api_key("sk-tracing-key")
```

### Organization and Project

```bash
export OPENAI_ORG_ID="org_..."
export OPENAI_PROJECT_ID="proj_..."
```

### Per-Run Tracing

```python
from agents import Runner, RunConfig

await Runner.run(
    agent,
    input="Hello",
    run_config=RunConfig(
        tracing={"api_key": "sk-tracing-123"}
    ),
)
```

### Disable Tracing

```python
from agents import set_tracing_disabled

set_tracing_disabled(True)
```

Or via environment variable:

```bash
export OPENAI_AGENTS_DISABLE_TRACING=1
```

## Debug Logging

### Enable Verbose Logging

```python
from agents import enable_verbose_stdout_logging

enable_verbose_stdout_logging()
```

### Custom Logger Configuration

```python
import logging

logger = logging.getLogger("openai.agents")

# Set log level
logger.setLevel(logging.DEBUG)  # All logs
logger.setLevel(logging.INFO)   # Info and above
logger.setLevel(logging.WARNING) # Warnings and errors only

# Add handler
logger.addHandler(logging.StreamHandler())
```

### Logger Names

- `openai.agents` - Main SDK logger
- `openai.agents.tracing` - Tracing-specific logger

## Sensitive Data in Logs

Disable sensitive data logging:

```bash
# Disable LLM inputs/outputs in logs
export OPENAI_AGENTS_DONT_LOG_MODEL_DATA=1

# Disable tool inputs/outputs in logs
export OPENAI_AGENTS_DONT_LOG_TOOL_DATA=1
```

## Configuration Summary

| Setting | Function/Variable | Default |
|---------|------------------|---------|
| API Key | `OPENAI_API_KEY` or `set_default_openai_key()` | env var |
| Client | `set_default_openai_client()` | Auto-created |
| API Type | `set_default_openai_api()` | `"responses"` |
| Tracing | `set_tracing_disabled()` | Enabled |
| Logging | `enable_verbose_stdout_logging()` | Warnings only |

## Best Practices

- Set API key via environment variable in production
- Use custom client for Azure or proxy setups
- Disable tracing in development if not needed
- Enable verbose logging only for debugging
- Disable sensitive data logging in production logs

## Related Topics

- `_INFO_OASDKP-IN19_TRACING.md` [OASDKP-IN19] - Tracing details
- `_INFO_OASDKP-IN26_NONOPENAI.md` [OASDKP-IN26] - Non-OpenAI providers

## API Reference

### Functions

- **set_default_openai_key()**
  - Import: `from agents import set_default_openai_key`

- **set_default_openai_client()**
  - Import: `from agents import set_default_openai_client`

- **set_default_openai_api()**
  - Import: `from agents import set_default_openai_api`
  - Values: `"responses"`, `"chat_completions"`

- **set_tracing_disabled()**
  - Import: `from agents import set_tracing_disabled`

- **set_tracing_export_api_key()**
  - Import: `from agents import set_tracing_export_api_key`

- **enable_verbose_stdout_logging()**
  - Import: `from agents import enable_verbose_stdout_logging`

## Document History

**[2026-02-11 11:48]**
- Initial SDK configuration documentation created
