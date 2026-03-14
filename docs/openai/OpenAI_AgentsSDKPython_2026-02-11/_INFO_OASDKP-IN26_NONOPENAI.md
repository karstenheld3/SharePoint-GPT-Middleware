# INFO: Non-OpenAI Model Providers

**Doc ID**: OASDKP-IN26
**Goal**: Document using the SDK with non-OpenAI LLM providers
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-TRACING` - Non-OpenAI models
- `OASDKP-SC-SO-OLLAMA` - Ollama discussions

## Summary

The OpenAI Agents SDK is provider-agnostic and supports 100+ LLM providers through adapters. The SDK provides `ChatCompletionsModel` for any OpenAI-compatible API endpoint and `LiteLLMModel` for broader provider support via LiteLLM. This enables using Anthropic Claude, Google Gemini, local models via Ollama, and many other providers while maintaining the same agent programming model. Some features like hosted tools require OpenAI models specifically. [VERIFIED]

## ChatCompletionsModel

Use any OpenAI-compatible API:

```python
from agents import Agent
from agents.models import ChatCompletionsModel

# Custom endpoint
model = ChatCompletionsModel(
    base_url="https://api.example.com/v1",
    api_key="your-api-key",
    model="custom-model-name",
)

agent = Agent(
    name="Custom Model Agent",
    instructions="Be helpful",
    model=model,
)
```

## LiteLLM Integration

Access 100+ providers via LiteLLM:

```python
from agents import Agent
from agents.models import LiteLLMModel

# Anthropic Claude
claude_agent = Agent(
    name="Claude Agent",
    model=LiteLLMModel(model="anthropic/claude-3-opus"),
)

# Google Gemini
gemini_agent = Agent(
    name="Gemini Agent",
    model=LiteLLMModel(model="gemini/gemini-pro"),
)

# Cohere
cohere_agent = Agent(
    name="Cohere Agent",
    model=LiteLLMModel(model="cohere/command"),
)
```

### LiteLLM Setup

```bash
pip install litellm
```

Set provider API keys:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=...
export COHERE_API_KEY=...
```

## Ollama (Local Models)

Run models locally with Ollama:

```python
from agents import Agent
from agents.models import ChatCompletionsModel

# Ollama uses OpenAI-compatible API
model = ChatCompletionsModel(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # Ollama ignores this but SDK requires it
    model="llama2",
)

agent = Agent(
    name="Local Agent",
    instructions="Be helpful",
    model=model,
)
```

### Ollama Setup

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama2

# Start server (usually auto-started)
ollama serve
```

### Known Ollama Issues

- Function calling may not work with all models
- Some models don't support structured outputs
- Performance varies by model and hardware

## Azure OpenAI

Use Azure-hosted OpenAI models:

```python
from agents import Agent
from agents.models import ChatCompletionsModel

model = ChatCompletionsModel(
    base_url="https://your-resource.openai.azure.com/openai/deployments/your-deployment",
    api_key="your-azure-key",
    model="gpt-4",  # Deployment name
    api_version="2024-02-15-preview",
)

agent = Agent(
    name="Azure Agent",
    model=model,
)
```

## Provider Comparison

| Provider | Tool Calling | Structured Output | Streaming |
|----------|--------------|-------------------|-----------|
| OpenAI | ✅ Full | ✅ Full | ✅ Full |
| Anthropic | ✅ Full | ✅ Full | ✅ Full |
| Google | ✅ Partial | ⚠️ Limited | ✅ Full |
| Ollama | ⚠️ Model-dependent | ⚠️ Limited | ✅ Full |
| Cohere | ✅ Full | ⚠️ Limited | ✅ Full |

## Feature Limitations

When using non-OpenAI providers:

### Not Available

- **Hosted tools** (WebSearchTool, FileSearchTool, etc.) - OpenAI only
- **Prompt templates** - OpenAI Responses API only
- **OpenAI tracing dashboard** - Need custom processor

### Available

- Function tools
- Handoffs
- Guardrails
- Streaming
- Sessions
- Context injection

## Tracing with Non-OpenAI

Configure custom tracing processor:

```python
from agents.tracing import TracingProcessor, set_tracing_processor

class CustomProcessor(TracingProcessor):
    def on_trace_end(self, trace):
        # Send to your observability platform
        send_to_datadog(trace)

set_tracing_processor(CustomProcessor())
```

## Best Practices

- Test tool calling with your specific model
- Use OpenAI for production if tools are critical
- Consider latency differences between providers
- Monitor costs across providers
- Have fallback for provider outages

## Example: Multi-Provider Setup

```python
from agents import Agent
from agents.models import LiteLLMModel, ChatCompletionsModel

# Different agents with different providers
openai_agent = Agent(
    name="OpenAI Agent",
    model="gpt-5",  # Default OpenAI
)

claude_agent = Agent(
    name="Claude Agent",
    model=LiteLLMModel(model="anthropic/claude-3-opus"),
)

local_agent = Agent(
    name="Local Agent",
    model=ChatCompletionsModel(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        model="llama2",
    ),
)

# Use based on requirements
async def smart_route(query, needs_tools=False):
    if needs_tools:
        return await Runner.run(openai_agent, query)  # Best tool support
    elif is_sensitive(query):
        return await Runner.run(local_agent, query)   # Keep local
    else:
        return await Runner.run(claude_agent, query)  # Good general use
```

## Related Topics

- `_INFO_OASDKP-IN03_MODELS.md` [OASDKP-IN03] - Model configuration
- `_INFO_OASDKP-IN19_TRACING.md` [OASDKP-IN19] - Custom tracing

## API Reference

### Classes

- **ChatCompletionsModel**
  - Import: `from agents.models import ChatCompletionsModel`
  - Params: `base_url`, `api_key`, `model`

- **LiteLLMModel**
  - Import: `from agents.models import LiteLLMModel`
  - Param: `model` (LiteLLM model string)

## Document History

**[2026-02-11 13:40]**
- Initial non-OpenAI providers documentation created
