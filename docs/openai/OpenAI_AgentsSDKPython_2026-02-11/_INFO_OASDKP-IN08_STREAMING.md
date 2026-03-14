# INFO: Streaming

**Doc ID**: OASDKP-IN08
**Goal**: Document streaming responses and event handling
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-STREAMING` - Streaming documentation

## Summary

Streaming allows receiving agent output progressively as it's generated, providing better user experience for long responses. Use `Runner.run_streamed()` to get a `RunResultStreaming` object, then iterate over `stream_events()` to receive events as they arrive. Event types include text deltas, tool calls, tool results, and agent lifecycle events. After streaming completes, the result object contains the full response. Streaming is essential for chat interfaces and real-time applications. [VERIFIED]

## Basic Streaming

```python
import asyncio
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="Be helpful")

async def main():
    result = await Runner.run_streamed(agent, "Tell me a story")
    
    async for event in result.stream_events():
        if hasattr(event, 'delta'):
            print(event.delta, end='', flush=True)
    
    print(f"\n\nFinal output: {result.final_output}")

asyncio.run(main())
```

## Event Types

### TextDeltaEvent

Text chunks as they're generated:

```python
async for event in result.stream_events():
    if isinstance(event, TextDeltaEvent):
        print(event.delta, end='')
```

### ToolCallEvent

When the agent initiates a tool call:

```python
async for event in result.stream_events():
    if isinstance(event, ToolCallEvent):
        print(f"Calling tool: {event.name}")
        print(f"Arguments: {event.arguments}")
```

### ToolResultEvent

When a tool returns its result:

```python
async for event in result.stream_events():
    if isinstance(event, ToolResultEvent):
        print(f"Tool result: {event.output}")
```

### Agent Lifecycle Events

```python
async for event in result.stream_events():
    if isinstance(event, AgentStartEvent):
        print(f"Agent starting: {event.agent.name}")
    elif isinstance(event, AgentEndEvent):
        print(f"Agent finished: {event.agent.name}")
```

## Complete Event Handling

```python
from agents import Agent, Runner
from agents.streaming import (
    TextDeltaEvent,
    ToolCallEvent,
    ToolResultEvent,
    AgentStartEvent,
    AgentEndEvent,
)

async def handle_stream(result):
    async for event in result.stream_events():
        match event:
            case TextDeltaEvent(delta=text):
                print(text, end='', flush=True)
            
            case ToolCallEvent(name=name, arguments=args):
                print(f"\n[Calling {name}...]")
            
            case ToolResultEvent(output=output):
                print(f"[Tool returned: {output[:50]}...]")
            
            case AgentStartEvent(agent=agent):
                print(f"\n[{agent.name} started]")
            
            case AgentEndEvent(agent=agent):
                print(f"\n[{agent.name} ended]")
```

## Streaming with Tools

```python
from agents import Agent, Runner, function_tool

@function_tool
def search(query: str) -> str:
    """Search for information."""
    return f"Results for: {query}"

agent = Agent(
    name="Search Assistant",
    instructions="Help users search for information",
    tools=[search],
)

async def main():
    result = await Runner.run_streamed(agent, "Find info about Python")
    
    async for event in result.stream_events():
        if hasattr(event, 'delta'):
            print(event.delta, end='')
        elif hasattr(event, 'name'):  # Tool call
            print(f"\n🔍 Searching...")

asyncio.run(main())
```

## Chat Interface Pattern

```python
async def chat_turn(agent, history, user_message):
    """Handle a single chat turn with streaming."""
    messages = history + [{"role": "user", "content": user_message}]
    
    result = await Runner.run_streamed(agent, messages)
    
    # Collect streamed response
    response_text = ""
    async for event in result.stream_events():
        if hasattr(event, 'delta'):
            print(event.delta, end='', flush=True)
            response_text += event.delta
    
    print()  # Newline
    
    # Return updated history
    return result.to_input_list()
```

## Timeout Handling

```python
import asyncio

async def stream_with_timeout(result, timeout=30):
    try:
        async with asyncio.timeout(timeout):
            async for event in result.stream_events():
                if hasattr(event, 'delta'):
                    print(event.delta, end='')
    except asyncio.TimeoutError:
        print("\n[Stream timed out]")
```

## Progress Indicators

```python
async def stream_with_progress(result):
    char_count = 0
    
    async for event in result.stream_events():
        if hasattr(event, 'delta'):
            print(event.delta, end='', flush=True)
            char_count += len(event.delta)
            
            # Update progress every 100 chars
            if char_count % 100 == 0:
                print(f" [{char_count} chars]", end='')
```

## After Streaming

Access the complete result after streaming:

```python
result = await Runner.run_streamed(agent, input)

# Stream events
async for event in result.stream_events():
    ...

# Now access complete result
print(f"Final output: {result.final_output}")
print(f"Handled by: {result.last_agent.name}")
print(f"Items generated: {len(result.new_items)}")

# Continue conversation
next_input = result.to_input_list() + [{"role": "user", "content": "..."}]
```

## Best Practices

- Always flush output when printing deltas
- Handle all event types for complete visibility
- Use streaming for user-facing applications
- Collect full response for logging/analysis
- Set reasonable timeouts

## Limitations

- Events may arrive out of order for parallel tool calls
- Streaming adds complexity vs simple run()
- Some structured outputs may not stream well

## Related Topics

- `_INFO_OASDKP-IN05_RUNNER.md` [OASDKP-IN05] - Running agents
- `_INFO_OASDKP-IN07_RESULTS.md` [OASDKP-IN07] - Result handling

## API Reference

### Methods

- **Runner.run_streamed()**
  - Returns: `RunResultStreaming`
  - Async iterator via `stream_events()`

### Event Classes

- **TextDeltaEvent** - Text chunk
- **ToolCallEvent** - Tool invocation
- **ToolResultEvent** - Tool result
- **AgentStartEvent** - Agent starting
- **AgentEndEvent** - Agent finishing

## Document History

**[2026-02-11 13:00]**
- Initial streaming documentation created
