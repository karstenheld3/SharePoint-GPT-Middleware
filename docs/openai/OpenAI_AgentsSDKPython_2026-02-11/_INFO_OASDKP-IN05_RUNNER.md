# INFO: Runner and Agent Execution

**Doc ID**: OASDKP-IN05
**Goal**: Document the Runner class and agent execution mechanics
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-RUNNING` - Running agents documentation

## Summary

The Runner class is the execution engine for agents in the OpenAI Agents SDK. It provides three methods for running agents: `run()` (async), `run_sync()` (synchronous wrapper), and `run_streamed()` (async with streaming). The Runner implements an agent loop that handles tool invocation, processes results, manages handoffs between agents, and continues until a final output is produced or max_turns is exceeded. The loop terminates when the LLM produces text output with the desired type and no pending tool calls. RunConfig allows customization of execution parameters including tracing, max turns, and model overrides. [VERIFIED]

## Running Agents

### Three Execution Methods

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="You are a helpful assistant")

# 1. Async execution
async def run_async():
    result = await Runner.run(agent, "Write a haiku about recursion.")
    print(result.final_output)

# 2. Synchronous execution
result = Runner.run_sync(agent, "Write a haiku about recursion.")
print(result.final_output)

# 3. Streaming execution
async def run_streamed():
    result = await Runner.run_streamed(agent, "Write a haiku about recursion.")
    async for event in result.stream_events():
        print(event)
    print(result.final_output)
```

### Method Details

- **Runner.run(agent, input, ...)**
  - Type: `async`
  - Returns: `RunResult`
  - Best for: Async applications, when you need the full result

- **Runner.run_sync(agent, input, ...)**
  - Type: `sync`
  - Returns: `RunResult`
  - Best for: Simple scripts, synchronous codebases
  - Internally calls `run()` in an event loop

- **Runner.run_streamed(agent, input, ...)**
  - Type: `async`
  - Returns: `RunResultStreaming`
  - Best for: Real-time UI updates, progressive responses

## The Agent Loop

When you call a run method, the Runner executes a loop: [VERIFIED]

```
┌─────────────────────────────────────────────────┐
│ 1. Call LLM for current agent with current input │
└────────────────────────┬────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│ 2. LLM produces output                          │
└────────────────────────┬────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Final    │   │ Handoff  │   │ Tool     │
    │ Output   │   │          │   │ Calls    │
    └────┬─────┘   └────┬─────┘   └────┬─────┘
         │              │              │
         ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Return   │   │ Update   │   │ Run      │
    │ Result   │   │ agent &  │   │ tools,   │
    │          │   │ input,   │   │ append   │
    │          │   │ re-run   │   │ results, │
    │          │   │ loop     │   │ re-run   │
    └──────────┘   └──────────┘   └──────────┘
```

### Final Output Rule

The LLM output is considered "final" when:
1. It produces text output with the desired type
2. There are no tool calls

### Max Turns Protection

If the loop exceeds `max_turns`, a `MaxTurnsExceeded` exception is raised:

```python
from agents import Runner
from agents.exceptions import MaxTurnsExceeded

try:
    result = await Runner.run(agent, input, max_turns=10)
except MaxTurnsExceeded:
    print("Agent exceeded maximum turns")
```

## Input Types

The `input` parameter accepts multiple formats:

```python
# String input (treated as user message)
result = await Runner.run(agent, "Hello, how are you?")

# List of input items (OpenAI Responses API format)
result = await Runner.run(agent, [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user", "content": "What's the weather?"},
])
```

## Streaming

Streaming allows receiving events as the LLM runs:

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="You are helpful")

async def stream_example():
    result = await Runner.run_streamed(agent, "Tell me a story")
    
    async for event in result.stream_events():
        # Process each streaming event
        if hasattr(event, 'delta'):
            print(event.delta, end='', flush=True)
    
    # After stream completes, access full result
    print(f"\n\nFinal: {result.final_output}")
```

The `RunResultStreaming` contains the complete information about the run once the stream is done. [VERIFIED]

## Run Configuration

Use `RunConfig` to customize execution:

```python
from agents import Agent, Runner
from agents.run import RunConfig

agent = Agent(name="Assistant", instructions="...")

config = RunConfig(
    max_turns=20,
    tracing_disabled=False,
    workflow_name="My Workflow",
    trace_id="trace_abc123",
    group_id="conversation_xyz",
)

result = await Runner.run(agent, "Hello", run_config=config)
```

### RunConfig Parameters

- **max_turns**
  - Type: `int`
  - Default: SDK default
  - Purpose: Maximum agent loop iterations

- **tracing_disabled**
  - Type: `bool`
  - Default: `False`
  - Purpose: Disable tracing for this run

- **workflow_name**
  - Type: `str`
  - Default: `"Agent workflow"`
  - Purpose: Name for the trace

- **trace_id**
  - Type: `str`
  - Default: Auto-generated
  - Format: `trace_<32_alphanumeric>`

- **group_id**
  - Type: `str`
  - Default: `None`
  - Purpose: Link multiple traces (e.g., chat thread ID)

- **model_override**
  - Type: `str`
  - Default: `None`
  - Purpose: Override agent's model for this run

## Conversations and Chat Threads

### Manual Conversation Management

Use `to_input_list()` to continue conversations:

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="...")

# First turn
result1 = await Runner.run(agent, "Hello!")

# Continue conversation with history
result2 = await Runner.run(
    agent,
    result1.to_input_list() + [{"role": "user", "content": "What did I just say?"}]
)
```

### Server-Managed Conversations

Use server-side conversation state:

```python
from agents import Agent, Runner
from agents.run import RunConfig

agent = Agent(name="Assistant", instructions="...")

# Create conversation
config = RunConfig(group_id="conv_123")

result1 = await Runner.run(agent, "Hello!", run_config=config)

# Continue in same conversation
result2 = await Runner.run(agent, "What did I say?", run_config=config)
```

## Error Handlers

Handle errors during agent execution:

```python
from agents import Agent, Runner

async def my_error_handler(error: Exception, context):
    print(f"Error occurred: {error}")
    # Return None to re-raise, or return a value to continue
    return None

result = await Runner.run(
    agent,
    "Hello",
    error_handler=my_error_handler
)
```

## Long-Running Agents and Human-in-the-Loop

For agents that need to persist across sessions or require human approval:

### Temporal Integration

```python
# See Temporal documentation for workflow integration
# Enables durable execution across failures
```

### Restate Integration

```python
# See Restate documentation for stateful agents
# Provides automatic state management
```

### DBOS Integration

```python
# See DBOS documentation for database-backed agents
# Enables persistent agent state
```

## Exceptions

### MaxTurnsExceeded

Raised when agent loop exceeds `max_turns`:

```python
from agents.exceptions import MaxTurnsExceeded

try:
    result = await Runner.run(agent, input, max_turns=5)
except MaxTurnsExceeded as e:
    print(f"Agent took too many turns: {e}")
```

### InputGuardrailTripwireTriggered

Raised when input guardrail fails:

```python
from agents.exceptions import InputGuardrailTripwireTriggered

try:
    result = await Runner.run(agent, malicious_input)
except InputGuardrailTripwireTriggered as e:
    print(f"Input blocked: {e}")
```

## Limitations and Known Issues

- `run_sync()` creates its own event loop; don't call from async context
- Streaming events may arrive out of order for parallel tool calls
- `max_turns` counts each agent invocation, not conversation turns

## Best Practices

- Use `run_streamed()` for user-facing applications
- Set reasonable `max_turns` to prevent runaway agents
- Use `group_id` to link related traces
- Handle `MaxTurnsExceeded` gracefully
- Use `to_input_list()` for conversation continuity

## Related Topics

- `_INFO_OASDKP-IN07_RESULTS.md` [OASDKP-IN07] - Run results
- `_INFO_OASDKP-IN08_STREAMING.md` [OASDKP-IN08] - Streaming details
- `_INFO_OASDKP-IN19_TRACING.md` [OASDKP-IN19] - Tracing configuration

## API Reference

### Classes

- **Runner**
  - Import: `from agents import Runner`
  - Static methods: `run()`, `run_sync()`, `run_streamed()`

- **RunResult**
  - Import: `from agents import RunResult`
  - Properties: `final_output`, `new_items`, `last_agent`
  - Methods: `to_input_list()`

- **RunResultStreaming**
  - Import: `from agents import RunResultStreaming`
  - Methods: `stream_events()`

- **RunConfig**
  - Import: `from agents.run import RunConfig`
  - Properties: `max_turns`, `tracing_disabled`, `workflow_name`, etc.

## Document History

**[2026-02-11 11:50]**
- Initial document created
- Agent loop mechanics documented
- Streaming and configuration options covered
