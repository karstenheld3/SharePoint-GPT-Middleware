# INFO: Tools Overview

**Doc ID**: OASDKP-IN09
**Goal**: Overview of tool categories in the OpenAI Agents SDK
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-TOOLS` - Official tools documentation

## Summary

Tools let agents take actions: fetching data, running code, calling external APIs, and even using a computer. The OpenAI Agents SDK supports five categories of tools: Hosted OpenAI tools (run on OpenAI servers), Local runtime tools (run in your environment), Function calling (wrap any Python function), Agents as tools (expose agents as callable tools), and Experimental Codex tool. Each category serves different use cases and has distinct execution characteristics. Tools are defined on agents and automatically exposed to the LLM with generated schemas. [VERIFIED]

## Tool Categories

### 1. Hosted OpenAI Tools

Run alongside the model on OpenAI servers. Available when using `OpenAIResponsesModel`:

- **WebSearchTool** - Search the web
- **FileSearchTool** - Retrieve from OpenAI Vector Stores
- **CodeInterpreterTool** - Execute code in sandbox
- **HostedMCPTool** - Remote MCP server tools
- **ImageGenerationTool** - Generate images from prompts

```python
from agents import Agent, WebSearchTool, FileSearchTool

agent = Agent(
    name="Research Assistant",
    tools=[
        WebSearchTool(),
        FileSearchTool(
            max_num_results=3,
            vector_store_ids=["vs_abc123"],
        ),
    ],
)
```

### 2. Local Runtime Tools

Run in your local environment:

- **Computer use** - Control computer interface
- **Shell** - Execute shell commands
- **Apply patch** - Apply code patches

### 3. Function Tools

Wrap any Python function as a tool with automatic schema generation:

```python
from agents import Agent, function_tool

@function_tool
def get_weather(city: str) -> str:
    """Returns weather info for the specified city."""
    return f"The weather in {city} is sunny"

agent = Agent(
    name="Weather Agent",
    tools=[get_weather],
)
```

Features:
- Automatic JSON schema generation from type hints
- Pydantic-powered validation
- Docstring parsing for descriptions

### 4. Agents as Tools

Expose an agent as a callable tool without a full handoff:

```python
from agents import Agent

specialist = Agent(name="Tax Expert", instructions="...")

main_agent = Agent(
    name="Financial Advisor",
    tools=[
        specialist.as_tool(
            tool_name="tax_expert",
            tool_description="Consult on tax questions",
        ),
    ],
)
```

The manager agent retains control; sub-agent runs and returns result.

### 5. Experimental: Codex Tool

Run workspace-scoped Codex tasks from a tool call:

```python
from agents import Agent
from agents.tools import CodexTool

agent = Agent(
    name="Code Assistant",
    tools=[CodexTool()],
)
```

**Note**: Experimental feature, API may change. [INFERRED]

## Tool Comparison

| Category | Execution | Use Case |
|----------|-----------|----------|
| Hosted | OpenAI servers | Web search, file search, code execution |
| Local Runtime | Your environment | System control, shell access |
| Function | Your environment | Custom business logic |
| Agents as Tools | Your environment | Sub-agent delegation |
| Codex | OpenAI servers | Code generation tasks |

## Common Patterns

### Multiple Tool Types

```python
from agents import Agent, WebSearchTool, function_tool

@function_tool
def calculate_tax(income: float, rate: float) -> float:
    """Calculate tax amount."""
    return income * rate

agent = Agent(
    name="Financial Assistant",
    tools=[
        WebSearchTool(),  # Hosted
        calculate_tax,     # Function
    ],
)
```

### Conditional Tool Enabling

```python
from agents import Agent, function_tool

@function_tool
def admin_action() -> str:
    """Admin-only action."""
    return "Action completed"

def get_tools(context):
    tools = [basic_tool]
    if context.context.is_admin:
        tools.append(admin_action)
    return tools

# Tools can be dynamically determined
```

## Related Topics

- `_INFO_OASDKP-IN10_TOOLS_FUNCTION.md` [OASDKP-IN10] - Function tools details
- `_INFO_OASDKP-IN11_TOOLS_HOSTED.md` [OASDKP-IN11] - Hosted tools details
- `_INFO_OASDKP-IN12_TOOLS_AGENTSASTOOLS.md` [OASDKP-IN12] - Agents as tools

## Document History

**[2026-02-11 11:55]**
- Initial document created
- All five tool categories documented
