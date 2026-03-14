# INFO: REPL Utility

**Doc ID**: OASDKP-IN31
**Goal**: Document the interactive REPL for testing agents
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-REPL` - REPL documentation

## Summary

The SDK provides a built-in REPL (Read-Eval-Print Loop) utility for interactive testing of agents during development. The REPL allows you to chat with an agent in your terminal, test tool calls, observe handoffs, and debug behavior without writing application code. It automatically handles conversation history and displays structured output. [VERIFIED]

## Basic Usage

```python
from agents import Agent
from agents.repl import run_demo_loop

agent = Agent(
    name="Test Agent",
    instructions="You are a helpful assistant.",
)

# Start interactive REPL
run_demo_loop(agent)
```

## Running the REPL

```bash
python my_agent.py
```

Output:
```
Agent: Test Agent
Type 'quit' to exit.

You: Hello!
Agent: Hi! How can I help you today?

You: What can you do?
Agent: I can help you with...

You: quit
Goodbye!
```

## REPL with Tools

```python
from agents import Agent, function_tool
from agents.repl import run_demo_loop

@function_tool
def calculate(expression: str) -> str:
    """Evaluate a math expression."""
    return str(eval(expression))

agent = Agent(
    name="Calculator",
    instructions="Help with math. Use the calculate tool.",
    tools=[calculate],
)

run_demo_loop(agent)
```

## REPL with Handoffs

```python
from agents import Agent
from agents.repl import run_demo_loop

specialist = Agent(name="Specialist", instructions="...")
triage = Agent(name="Triage", handoffs=[specialist])

run_demo_loop(triage)
```

The REPL displays handoff events:
```
You: I need specialized help
[Handoff to Specialist]
Agent: I'm the specialist...
```

## Configuration Options

```python
from agents.repl import run_demo_loop

run_demo_loop(
    agent,
    show_tool_calls=True,   # Display tool invocations
    show_handoffs=True,     # Display handoff events
    stream=True,            # Stream responses
)
```

## Async REPL

```python
from agents.repl import run_demo_loop_async

async def main():
    await run_demo_loop_async(agent)

asyncio.run(main())
```

## Use Cases

- Quick agent testing during development
- Debugging tool behavior
- Testing handoff routing
- Demonstrating agent capabilities
- Interactive prototyping

## Best Practices

- Use REPL for rapid iteration
- Test edge cases interactively
- Observe tool call patterns
- Verify handoff conditions

## Related Topics

- `_INFO_OASDKP-IN04_AGENTS.md` [OASDKP-IN04] - Agent configuration
- `_INFO_OASDKP-IN05_RUNNER.md` [OASDKP-IN05] - Running agents

## API Reference

### Functions

- **run_demo_loop()**
  - Import: `from agents.repl import run_demo_loop`
  - Params: `agent`, `show_tool_calls`, `show_handoffs`, `stream`

- **run_demo_loop_async()**
  - Import: `from agents.repl import run_demo_loop_async`

## Document History

**[2026-02-11 11:52]**
- Initial REPL documentation created
