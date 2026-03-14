# INFO: Agents

**Doc ID**: OASDKP-IN04
**Goal**: Complete documentation of the Agent class and configuration options
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-AGENTS` - Official agents documentation

## Summary

Agents are the core building block in the OpenAI Agents SDK. An Agent is a large language model (LLM) configured with instructions and tools. The Agent class is generic on its context type, enabling type-safe dependency injection throughout the agent workflow. Agents support static and dynamic instructions, lifecycle hooks for observability, multiple output types including structured Pydantic models, and can be cloned for creating variations. The SDK provides two multi-agent patterns: Manager (agents as tools) where a central orchestrator invokes sub-agents, and Handoffs where peer agents delegate control to specialists. [VERIFIED]

## Basic Configuration

### Required and Common Properties

```python
from agents import Agent, ModelSettings, function_tool

@function_tool
def get_weather(city: str) -> str:
    """Returns weather info for the specified city."""
    return f"The weather in {city} is sunny"

agent = Agent(
    name="Haiku agent",
    instructions="Always respond in haiku form",
    model="gpt-5-nano",
    tools=[get_weather],
)
```

### Configuration Parameters

- **name** (required)
  - Type: `str`
  - Purpose: Identifies your agent, used in tracing and handoffs

- **instructions**
  - Type: `str | Callable`
  - Purpose: System prompt / developer message
  - Can be static string or dynamic function

- **model**
  - Type: `str`
  - Default: Uses SDK default
  - Purpose: Which LLM to use (e.g., `gpt-5-nano`, `gpt-5.2`)

- **model_settings**
  - Type: `ModelSettings`
  - Purpose: Configure model tuning parameters
  - Includes: `temperature`, `top_p`, `tool_choice`, etc.

- **prompt**
  - Type: `dict | Callable`
  - Purpose: Reference a prompt template by ID (Responses API only)

- **tools**
  - Type: `list[Tool]`
  - Purpose: Tools the agent can use

- **mcp_servers**
  - Type: `list[MCPServer]`
  - Purpose: MCP servers that provide tools to the agent

- **handoffs**
  - Type: `list[Agent | Handoff]`
  - Purpose: Other agents this agent can delegate to

- **guardrails**
  - Type: `list[Guardrail]`
  - Purpose: Input/output validation

- **reset_tool_choice**
  - Type: `bool`
  - Default: `True`
  - Purpose: Reset tool_choice after a tool call to avoid loops

## Prompt Templates

Reference a prompt template created in the OpenAI platform:

```python
from agents import Agent

agent = Agent(
    name="Prompted assistant",
    prompt={
        "id": "pmpt_123",
        "version": "1",
        "variables": {"poem_style": "haiku"},
    },
)
```

### Dynamic Prompt Generation

```python
from dataclasses import dataclass
from agents import Agent, GenerateDynamicPromptData, Runner

@dataclass
class PromptContext:
    prompt_id: str
    poem_style: str

async def build_prompt(data: GenerateDynamicPromptData):
    ctx: PromptContext = data.context.context
    return {
        "id": ctx.prompt_id,
        "version": "1",
        "variables": {"poem_style": ctx.poem_style},
    }

agent = Agent(name="Prompted assistant", prompt=build_prompt)

result = await Runner.run(
    agent,
    "Say hello",
    context=PromptContext(prompt_id="pmpt_123", poem_style="limerick"),
)
```

## Context (Dependency Injection)

Agents are generic on their context type. Context is passed to every agent, tool, handoff, and serves as a dependency container for the agent run. [VERIFIED]

```python
from dataclasses import dataclass
from agents import Agent

@dataclass
class UserContext:
    name: str
    uid: str
    is_pro_user: bool

    async def fetch_purchases(self) -> list:
        # Fetch user's purchases
        return []

# Type-safe agent with context
agent = Agent[UserContext](
    name="User Assistant",
    instructions="Help the user with their account",
)
```

## Dynamic Instructions

Provide instructions via a function that receives the agent and context:

```python
from agents import Agent, RunContextWrapper

def dynamic_instructions(
    context: RunContextWrapper[UserContext],
    agent: Agent[UserContext]
) -> str:
    return f"The user's name is {context.context.name}. Help them with their questions."

agent = Agent[UserContext](
    name="Triage agent",
    instructions=dynamic_instructions,
)
```

Both regular and async functions are accepted. [VERIFIED]

## Output Types

By default, agents produce plain text (`str`) outputs. Use `output_type` for structured outputs:

```python
from pydantic import BaseModel
from agents import Agent

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

agent = Agent(
    name="Calendar extractor",
    instructions="Extract calendar events from text",
    output_type=CalendarEvent,
)
```

When you pass an `output_type`, the model uses structured outputs instead of regular plain text responses. Supports any type that can be wrapped in a Pydantic TypeAdapter: dataclasses, lists, TypedDict, etc. [VERIFIED]

## Multi-Agent Patterns

### Pattern 1: Manager (Agents as Tools)

Central orchestrator invokes specialized sub-agents as tools:

```python
from agents import Agent

booking_agent = Agent(
    name="Booking Expert",
    instructions="Handle booking requests"
)
refund_agent = Agent(
    name="Refund Expert", 
    instructions="Handle refund requests"
)

customer_facing_agent = Agent(
    name="Customer-facing agent",
    instructions=(
        "Handle all direct user communication. "
        "Call the relevant tools when specialized expertise is needed."
    ),
    tools=[
        booking_agent.as_tool(
            tool_name="booking_expert",
            tool_description="Handles booking questions and requests.",
        ),
        refund_agent.as_tool(
            tool_name="refund_expert",
            tool_description="Handles refund questions and requests.",
        )
    ],
)
```

### Pattern 2: Handoffs

Peer agents hand off control to specialists:

```python
from agents import Agent

booking_agent = Agent(name="Booking Agent", instructions="...")
refund_agent = Agent(name="Refund Agent", instructions="...")

triage_agent = Agent(
    name="Triage agent",
    instructions=(
        "Help the user with their questions. "
        "If they ask about booking, hand off to the booking agent. "
        "If they ask about refunds, hand off to the refund agent."
    ),
    handoffs=[booking_agent, refund_agent],
)
```

## Lifecycle Events (Hooks)

Hook into the agent lifecycle with the `hooks` property:

```python
from agents import Agent, AgentHooks

class MyHooks(AgentHooks):
    async def on_start(self, context, agent):
        print(f"Agent {agent.name} starting")
    
    async def on_end(self, context, agent, output):
        print(f"Agent {agent.name} finished")

agent = Agent(
    name="Observable Agent",
    instructions="...",
    hooks=MyHooks(),
)
```

Subclass `AgentHooks` and override methods you're interested in. [VERIFIED]

## Cloning Agents

Duplicate an Agent and optionally change properties:

```python
pirate_agent = Agent(
    name="Pirate",
    instructions="Write like a pirate",
    model="gpt-5.2",
)

robot_agent = pirate_agent.clone(
    name="Robot",
    instructions="Write like a robot",
)
```

## Forcing Tool Use

Control tool usage with `ModelSettings.tool_choice`:

```python
from agents import Agent, ModelSettings, function_tool

@function_tool
def get_weather(city: str) -> str:
    """Returns weather info for the specified city."""
    return f"The weather in {city} is sunny"

agent = Agent(
    name="Weather Agent",
    instructions="Retrieve weather details.",
    tools=[get_weather],
    model_settings=ModelSettings(tool_choice="get_weather")
)
```

### Tool Choice Values

- **auto**: LLM decides whether to use a tool (default)
- **required**: LLM must use a tool (can choose which)
- **none**: LLM must not use a tool
- **specific string**: LLM must use that specific tool (e.g., `"get_weather"`)

## Tool Use Behavior

The `tool_use_behavior` parameter controls how tool outputs are handled:

```python
from agents import Agent, function_tool
from agents.agent import StopAtTools

@function_tool
def get_weather(city: str) -> str:
    return f"The weather in {city} is sunny"

# Option 1: Default - LLM processes tool results
agent1 = Agent(
    name="Weather Agent",
    tools=[get_weather],
    tool_use_behavior="run_llm_again"  # default
)

# Option 2: Stop on first tool output
agent2 = Agent(
    name="Weather Agent",
    tools=[get_weather],
    tool_use_behavior="stop_on_first_tool"
)

# Option 3: Stop at specific tools
agent3 = Agent(
    name="Weather Agent",
    tools=[get_weather],
    tool_use_behavior=StopAtTools(stop_at_tool_names=["get_weather"])
)
```

### Custom Tool Handler

```python
from agents import Agent, FunctionToolResult, RunContextWrapper
from agents.agent import ToolsToFinalOutputResult

def custom_tool_handler(
    context: RunContextWrapper,
    tool_results: list[FunctionToolResult]
) -> ToolsToFinalOutputResult:
    for result in tool_results:
        if result.output and "sunny" in result.output:
            return ToolsToFinalOutputResult(
                is_final_output=True,
                final_output=f"Final weather: {result.output}"
            )
    return ToolsToFinalOutputResult(is_final_output=False, final_output=None)

agent = Agent(
    name="Weather Agent",
    tools=[get_weather],
    tool_use_behavior=custom_tool_handler
)
```

## Limitations and Known Issues

- Guardrails only run on the first agent in a chain [VERIFIED]
- `output_type` requires model support for structured outputs
- Dynamic instructions add latency (function call per agent invocation)

## Best Practices

- Use descriptive `name` values for better tracing
- Keep instructions focused and specific
- Use typed context for dependency injection
- Set `reset_tool_choice=True` (default) to avoid infinite tool loops
- Use `clone()` to create agent variations

## Related Topics

- `_INFO_OASDKP-IN05_RUNNER.md` [OASDKP-IN05] - Running agents
- `_INFO_OASDKP-IN06_CONTEXT.md` [OASDKP-IN06] - Context details
- `_INFO_OASDKP-IN13_HANDOFFS.md` [OASDKP-IN13] - Handoff patterns
- `_INFO_OASDKP-IN12_TOOLS_AGENTSASTOOLS.md` [OASDKP-IN12] - Agents as tools

## API Reference

### Classes

- **Agent[TContext]**
  - Import: `from agents import Agent`
  - Generic type parameter for context
  - Key methods: `clone()`, `as_tool()`

- **ModelSettings**
  - Import: `from agents import ModelSettings`
  - Properties: `temperature`, `top_p`, `tool_choice`, `parallel_tool_calls`

- **AgentHooks**
  - Import: `from agents import AgentHooks`
  - Override: `on_start()`, `on_end()`, `on_tool_start()`, `on_tool_end()`

## Document History

**[2026-02-11 11:45]**
- Initial document created
- All agent configuration options documented
- Multi-agent patterns with code examples
