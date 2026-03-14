# INFO: Models and Model Settings

**Doc ID**: OASDKP-IN03
**Goal**: Document supported models and ModelSettings configuration
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-AGENTS` - Agent model configuration

## Summary

The OpenAI Agents SDK supports multiple LLM providers through its model abstraction layer. By default, agents use OpenAI models via the Responses API, but the SDK is provider-agnostic and supports Chat Completions API providers through adapters. ModelSettings provides fine-grained control over model behavior including temperature, top_p, tool_choice, and parallel tool calls. The SDK automatically selects appropriate defaults but allows full customization. [VERIFIED]

## Specifying Models

### Default Model

```python
from agents import Agent

# Uses SDK default model
agent = Agent(
    name="Assistant",
    instructions="Be helpful",
)
```

### Specific OpenAI Model

```python
agent = Agent(
    name="Assistant",
    instructions="Be helpful",
    model="gpt-5-nano",  # Fast, cost-effective
)

agent = Agent(
    name="Advanced Assistant",
    model="gpt-5.2",  # Most capable
)
```

### Available OpenAI Models

- **gpt-5-nano** - Fast, cost-effective for simple tasks
- **gpt-5-mini** - Balanced performance and cost
- **gpt-5** - Standard model
- **gpt-5.2** - Most capable
- **gpt-realtime** - For realtime/voice agents

## ModelSettings

Fine-tune model behavior:

```python
from agents import Agent, ModelSettings

agent = Agent(
    name="Creative Writer",
    instructions="Write creative stories",
    model="gpt-5",
    model_settings=ModelSettings(
        temperature=0.9,
        top_p=0.95,
        max_tokens=2000,
    ),
)
```

### Configuration Options

- **temperature**
  - Type: `float`
  - Range: 0.0 - 2.0
  - Default: Model default (~1.0)
  - Higher = more creative, lower = more deterministic

- **top_p**
  - Type: `float`
  - Range: 0.0 - 1.0
  - Purpose: Nucleus sampling threshold

- **max_tokens**
  - Type: `int`
  - Purpose: Maximum response length

- **tool_choice**
  - Type: `str | dict`
  - Values: `"auto"`, `"required"`, `"none"`, or specific tool name
  - Purpose: Control tool usage

- **parallel_tool_calls**
  - Type: `bool`
  - Default: `True`
  - Purpose: Allow multiple simultaneous tool calls

- **response_format**
  - Type: `dict`
  - Purpose: Force JSON mode or specific format

## Tool Choice Options

```python
from agents import Agent, ModelSettings

# Auto (default) - model decides
agent = Agent(
    model_settings=ModelSettings(tool_choice="auto"),
    tools=[my_tool],
)

# Required - must use a tool
agent = Agent(
    model_settings=ModelSettings(tool_choice="required"),
    tools=[my_tool],
)

# None - no tools allowed
agent = Agent(
    model_settings=ModelSettings(tool_choice="none"),
    tools=[my_tool],
)

# Specific tool
agent = Agent(
    model_settings=ModelSettings(tool_choice="my_tool"),
    tools=[my_tool],
)
```

## Non-OpenAI Models

### Using LiteLLM

```python
from agents import Agent
from agents.models import LiteLLMModel

agent = Agent(
    name="Claude Agent",
    model=LiteLLMModel(model="anthropic/claude-3-opus"),
)
```

### Using Chat Completions API

```python
from agents import Agent
from agents.models import ChatCompletionsModel

agent = Agent(
    name="Custom Model",
    model=ChatCompletionsModel(
        base_url="https://api.example.com/v1",
        api_key="your-key",
        model="custom-model",
    ),
)
```

### Ollama

```python
from agents.models import ChatCompletionsModel

agent = Agent(
    name="Local Agent",
    model=ChatCompletionsModel(
        base_url="http://localhost:11434/v1",
        model="llama2",
    ),
)
```

## Model Selection Guidelines

| Use Case | Recommended Model | Settings |
|----------|------------------|----------|
| Simple Q&A | gpt-5-nano | Default |
| Complex reasoning | gpt-5.2 | Default |
| Creative writing | gpt-5 | temperature=0.9 |
| Code generation | gpt-5 | temperature=0.2 |
| Data extraction | gpt-5-mini | temperature=0 |
| Voice agents | gpt-realtime | - |

## Best Practices

- Use smaller models for guardrails and screening
- Match model capability to task complexity
- Lower temperature for deterministic outputs
- Use `tool_choice="required"` when tool use is mandatory

## Related Topics

- `_INFO_OASDKP-IN04_AGENTS.md` [OASDKP-IN04] - Agent configuration
- `_INFO_OASDKP-IN26_NONOPENAI.md` [OASDKP-IN26] - Non-OpenAI providers

## API Reference

### Classes

- **ModelSettings**
  - Import: `from agents import ModelSettings`
  - Properties: `temperature`, `top_p`, `max_tokens`, `tool_choice`

- **LiteLLMModel**
  - Import: `from agents.models import LiteLLMModel`

- **ChatCompletionsModel**
  - Import: `from agents.models import ChatCompletionsModel`

## Document History

**[2026-02-11 12:50]**
- Initial models documentation created
