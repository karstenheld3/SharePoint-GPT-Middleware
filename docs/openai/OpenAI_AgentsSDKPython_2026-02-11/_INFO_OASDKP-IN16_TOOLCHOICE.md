# INFO: Tool Choice and Tool Use Behavior

**Doc ID**: OASDKP-IN16
**Goal**: Document controlling when and how agents use tools
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-AGENTS` - Tool choice documentation

## Summary

The SDK provides two mechanisms for controlling tool usage: `tool_choice` determines whether/which tools the LLM must use, while `tool_use_behavior` controls what happens after tools execute. Tool choice options include auto (LLM decides), required (must use a tool), none (no tools), or a specific tool name. Tool use behavior options include running the LLM again to process results (default), stopping on first tool output, stopping at specific tools, or custom processing. The `reset_tool_choice` parameter prevents infinite tool loops. [VERIFIED]

## Tool Choice

Control whether and which tools the LLM uses:

### Auto (Default)

LLM decides whether to use tools:

```python
from agents import Agent, ModelSettings

agent = Agent(
    name="Flexible Agent",
    tools=[tool1, tool2],
    model_settings=ModelSettings(tool_choice="auto"),
)
```

### Required

LLM must use a tool (chooses which):

```python
agent = Agent(
    name="Tool-Required Agent",
    tools=[search, calculate],
    model_settings=ModelSettings(tool_choice="required"),
)
```

### None

LLM cannot use tools:

```python
agent = Agent(
    name="No-Tool Agent",
    tools=[tool1],  # Available but disabled
    model_settings=ModelSettings(tool_choice="none"),
)
```

### Specific Tool

LLM must use this specific tool:

```python
agent = Agent(
    name="Search-First Agent",
    tools=[search, analyze],
    model_settings=ModelSettings(tool_choice="search"),
)
```

## Tool Use Behavior

Control what happens after tool execution:

### run_llm_again (Default)

LLM processes tool results and generates response:

```python
agent = Agent(
    name="Standard Agent",
    tools=[get_data],
    tool_use_behavior="run_llm_again",
)
# Flow: User → LLM → Tool → LLM → Response
```

### stop_on_first_tool

Use first tool output as final response:

```python
agent = Agent(
    name="Direct Tool Agent",
    tools=[format_response],
    tool_use_behavior="stop_on_first_tool",
)
# Flow: User → LLM → Tool → Response (tool output)
```

### StopAtTools

Stop at specific tools:

```python
from agents.agent import StopAtTools

agent = Agent(
    name="Selective Stop Agent",
    tools=[search, format, finalize],
    tool_use_behavior=StopAtTools(
        stop_at_tool_names=["finalize"]
    ),
)
# Continues for search/format, stops at finalize
```

### Custom Handler

Full control over tool result processing:

```python
from agents import FunctionToolResult, RunContextWrapper
from agents.agent import ToolsToFinalOutputResult

def custom_handler(
    context: RunContextWrapper,
    tool_results: list[FunctionToolResult]
) -> ToolsToFinalOutputResult:
    for result in tool_results:
        if "FINAL:" in result.output:
            return ToolsToFinalOutputResult(
                is_final_output=True,
                final_output=result.output.replace("FINAL:", "")
            )
    return ToolsToFinalOutputResult(
        is_final_output=False,
        final_output=None
    )

agent = Agent(
    name="Custom Handler Agent",
    tools=[my_tools],
    tool_use_behavior=custom_handler,
)
```

## reset_tool_choice

Prevent infinite tool loops:

```python
agent = Agent(
    name="Safe Agent",
    tools=[recursive_tool],
    reset_tool_choice=True,  # Default: True
)
```

When `True` (default):
- After tool call, `tool_choice` resets to `auto`
- Prevents model from calling same tool repeatedly

When `False`:
- `tool_choice` persists across loop iterations
- Use carefully to avoid infinite loops

## Forcing Deterministic Flows

Create predictable tool sequences:

```python
from agents import Agent, ModelSettings, function_tool

@function_tool
def step1() -> str:
    return "Step 1 complete"

@function_tool  
def step2() -> str:
    return "Step 2 complete"

@function_tool
def step3() -> str:
    return "FINAL: All steps complete"

# Force step1 first
agent = Agent(
    name="Sequential Agent",
    tools=[step1, step2, step3],
    model_settings=ModelSettings(tool_choice="step1"),
    reset_tool_choice=True,  # Allow LLM to choose next
)
```

## Use Case Examples

### Data Pipeline

```python
# Must fetch data, then process
agent = Agent(
    tools=[fetch_data, process_data, format_output],
    model_settings=ModelSettings(tool_choice="fetch_data"),
    tool_use_behavior=StopAtTools(stop_at_tool_names=["format_output"]),
)
```

### API Wrapper

```python
# Tool output is the API response
agent = Agent(
    tools=[api_call],
    tool_use_behavior="stop_on_first_tool",
)
```

### Validation Pipeline

```python
# Custom logic for validation results
def validate_and_decide(context, results):
    for r in results:
        if r.output.get("valid"):
            return ToolsToFinalOutputResult(True, "Validation passed")
    return ToolsToFinalOutputResult(False, None)  # Continue

agent = Agent(
    tools=[validate],
    tool_use_behavior=validate_and_decide,
)
```

## Best Practices

- Use `tool_choice="required"` when tools are essential
- Use `stop_on_first_tool` for simple tool wrappers
- Keep `reset_tool_choice=True` (default) for safety
- Use custom handlers for complex flow control

## Related Topics

- `_INFO_OASDKP-IN04_AGENTS.md` [OASDKP-IN04] - Agent configuration
- `_INFO_OASDKP-IN10_TOOLS_FUNCTION.md` [OASDKP-IN10] - Creating tools

## API Reference

### ModelSettings Properties

- **tool_choice**: `"auto" | "required" | "none" | str`
- **parallel_tool_calls**: `bool`

### Agent Properties

- **tool_use_behavior**: `str | StopAtTools | Callable`
- **reset_tool_choice**: `bool`

### Classes

- **StopAtTools**
  - Import: `from agents.agent import StopAtTools`
  - Param: `stop_at_tool_names: list[str]`

- **ToolsToFinalOutputResult**
  - Import: `from agents.agent import ToolsToFinalOutputResult`
  - Properties: `is_final_output`, `final_output`

## Document History

**[2026-02-11 13:10]**
- Initial tool choice documentation created
