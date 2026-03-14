# INFO: Run Results

**Doc ID**: OASDKP-IN07
**Goal**: Document RunResult, RunResultStreaming, and output handling
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-RESULTS` - Results documentation
- `OASDKP-SC-GHIO-AGENTS` - Output types

## Summary

When you run an agent, the Runner returns a result object containing the final output and execution metadata. `RunResult` is returned by `run()` and `run_sync()`, while `RunResultStreaming` is returned by `run_streamed()`. The `final_output` property contains the agent's response, which can be plain text or a structured Pydantic object when `output_type` is specified. Results also include `new_items` (all items generated during the run), `last_agent` (the final agent that produced output), and `to_input_list()` for continuing conversations. [VERIFIED]

## RunResult

Returned by `Runner.run()` and `Runner.run_sync()`:

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="Be helpful")

# Async
result = await Runner.run(agent, "Hello!")

# Sync
result = Runner.run_sync(agent, "Hello!")

# Access the output
print(result.final_output)
```

### Properties

- **final_output**
  - Type: `str | TOutput`
  - Purpose: The agent's final response
  - Can be string or structured output type

- **new_items**
  - Type: `list[RunItem]`
  - Purpose: All items generated during the run
  - Includes: messages, tool calls, tool results

- **last_agent**
  - Type: `Agent`
  - Purpose: The agent that produced the final output
  - Useful when handoffs occur

- **input_guardrail_results**
  - Type: `list[InputGuardrailResult]`
  - Purpose: Results from input guardrails

- **output_guardrail_results**
  - Type: `list[OutputGuardrailResult]`
  - Purpose: Results from output guardrails

### Methods

- **to_input_list()**
  - Returns: `list[dict]`
  - Purpose: Convert result to input format for conversation continuation

## RunResultStreaming

Returned by `Runner.run_streamed()`:

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="Be helpful")

result = await Runner.run_streamed(agent, "Tell me a story")

# Stream events as they arrive
async for event in result.stream_events():
    if hasattr(event, 'delta'):
        print(event.delta, end='', flush=True)

# After streaming, access final result
print(f"\n\nFinal: {result.final_output}")
```

### Properties

Same as `RunResult`, plus:

- **stream_events()**
  - Type: `AsyncIterator[StreamEvent]`
  - Purpose: Iterate over streaming events

## Output Types

### Plain Text (Default)

```python
agent = Agent(name="Writer", instructions="Write creatively")
result = await Runner.run(agent, "Write a poem")
print(result.final_output)  # str
```

### Structured Output with Pydantic

```python
from pydantic import BaseModel
from agents import Agent, Runner

class Analysis(BaseModel):
    sentiment: str
    confidence: float
    key_points: list[str]

agent = Agent(
    name="Analyzer",
    instructions="Analyze text sentiment",
    output_type=Analysis,
)

result = await Runner.run(agent, "I love this product!")
print(result.final_output.sentiment)     # "positive"
print(result.final_output.confidence)    # 0.95
print(result.final_output.key_points)    # ["enthusiasm", "satisfaction"]
```

### Other Supported Types

`output_type` supports any type that can be wrapped in Pydantic TypeAdapter:

```python
from dataclasses import dataclass
from typing import TypedDict

# Dataclass
@dataclass
class Event:
    title: str
    date: str

# TypedDict
class Person(TypedDict):
    name: str
    age: int

# List
agent = Agent(output_type=list[str])  # Returns list of strings
```

## Continuing Conversations

Use `to_input_list()` to maintain conversation history:

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="Be helpful")

# First turn
result1 = await Runner.run(agent, "My name is Alice")
print(result1.final_output)  # "Nice to meet you, Alice!"

# Continue with history
result2 = await Runner.run(
    agent,
    result1.to_input_list() + [{"role": "user", "content": "What's my name?"}]
)
print(result2.final_output)  # "Your name is Alice."
```

## Accessing Run Items

Inspect all items generated during the run:

```python
result = await Runner.run(agent, "What's the weather?")

for item in result.new_items:
    print(f"Type: {item.type}")
    if item.type == "message":
        print(f"  Role: {item.role}")
        print(f"  Content: {item.content}")
    elif item.type == "tool_call":
        print(f"  Tool: {item.name}")
        print(f"  Args: {item.arguments}")
    elif item.type == "tool_result":
        print(f"  Result: {item.output}")
```

## Handling Handoffs

When handoffs occur, `last_agent` indicates which agent produced the final output:

```python
from agents import Agent, Runner

triage = Agent(name="Triage", handoffs=[specialist])
specialist = Agent(name="Specialist", instructions="...")

result = await Runner.run(triage, "I need specialized help")

print(f"Handled by: {result.last_agent.name}")
# Might be "Triage" or "Specialist" depending on routing
```

## Streaming Events

Event types in `stream_events()`:

```python
async for event in result.stream_events():
    match event:
        case TextDeltaEvent(delta=text):
            print(text, end='')
        case ToolCallEvent(name=name, arguments=args):
            print(f"Calling {name}")
        case ToolResultEvent(output=output):
            print(f"Tool returned: {output}")
        case AgentStartEvent(agent=agent):
            print(f"Agent {agent.name} starting")
        case AgentEndEvent(agent=agent):
            print(f"Agent {agent.name} finished")
```

## Guardrail Results

Access guardrail execution results:

```python
result = await Runner.run(agent, input)

# Input guardrails
for gr in result.input_guardrail_results:
    print(f"Guardrail triggered: {gr.tripwire_triggered}")
    print(f"Info: {gr.output_info}")

# Output guardrails
for gr in result.output_guardrail_results:
    print(f"Guardrail triggered: {gr.tripwire_triggered}")
```

## Best Practices

- Check `last_agent` when using handoffs to know who responded
- Use `output_type` for structured data extraction
- Use `to_input_list()` for multi-turn conversations
- Stream for user-facing applications
- Inspect `new_items` for debugging

## Related Topics

- `_INFO_OASDKP-IN05_RUNNER.md` [OASDKP-IN05] - Running agents
- `_INFO_OASDKP-IN08_STREAMING.md` [OASDKP-IN08] - Streaming details
- `_INFO_OASDKP-IN04_AGENTS.md` [OASDKP-IN04] - Output types

## API Reference

### Classes

- **RunResult**
  - Import: `from agents import RunResult`
  - Properties: `final_output`, `new_items`, `last_agent`
  - Methods: `to_input_list()`

- **RunResultStreaming**
  - Import: `from agents import RunResultStreaming`
  - Methods: `stream_events()`

### Types

- **RunItem**
  - Base type for items in `new_items`
  - Subtypes: MessageItem, ToolCallItem, ToolResultItem

## Document History

**[2026-02-11 12:30]**
- Initial document created
- Result handling patterns documented
