# INFO: Quickstart Guide

**Doc ID**: OASDKP-IN02
**Goal**: Step-by-step guide to get started with the OpenAI Agents SDK
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-QUICKSTART` - Official quickstart

## Summary

This quickstart guide walks through setting up the OpenAI Agents SDK, creating your first agent, and building progressively more complex applications. The SDK requires Python 3.9+ and an OpenAI API key. Installation is simple via pip. The guide covers basic agents, adding tools, multi-agent handoffs, and guardrails in a progressive learning path. [VERIFIED]

## Prerequisites

- **Python**: 3.9 or newer
- **OpenAI API Key**: Get from https://platform.openai.com/api-keys
- **pip**: Python package manager

## Installation

### Basic Installation

```bash
pip install openai-agents
```

### With Voice Support

```bash
pip install 'openai-agents[voice]'
```

### Verify Installation

```python
import agents
print(agents.__version__)  # Should print version
```

## Environment Setup

Set your OpenAI API key:

```bash
# Linux/macOS
export OPENAI_API_KEY=sk-your-key-here

# Windows (PowerShell)
$env:OPENAI_API_KEY = "sk-your-key-here"

# Windows (CMD)
set OPENAI_API_KEY=sk-your-key-here
```

Or in Python:

```python
import os
os.environ["OPENAI_API_KEY"] = "sk-your-key-here"
```

## Step 1: Hello World Agent

Create a simple agent that responds to messages:

```python
from agents import Agent, Runner

# Create an agent
agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant. Be concise."
)

# Run synchronously
result = Runner.run_sync(agent, "Hello! What can you do?")
print(result.final_output)
```

## Step 2: Agent with Tools

Add a function tool to give your agent capabilities:

```python
from agents import Agent, Runner, function_tool

@function_tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {e}"

agent = Agent(
    name="Calculator",
    instructions="Help users with calculations. Use the calculate tool.",
    tools=[calculate],
)

result = Runner.run_sync(agent, "What is 25 * 4 + 10?")
print(result.final_output)
```

## Step 3: Async Execution

Use async/await for better performance:

```python
import asyncio
from agents import Agent, Runner

agent = Agent(
    name="Assistant",
    instructions="You are helpful and concise."
)

async def main():
    result = await Runner.run(agent, "Tell me a fun fact.")
    print(result.final_output)

asyncio.run(main())
```

## Step 4: Multi-Agent with Handoffs

Create specialized agents that can hand off to each other:

```python
from agents import Agent, Runner

# Specialist agents
math_agent = Agent(
    name="Math Expert",
    instructions="You are a math expert. Solve math problems step by step."
)

writing_agent = Agent(
    name="Writing Expert",
    instructions="You are a writing expert. Help with essays and creative writing."
)

# Triage agent routes to specialists
triage_agent = Agent(
    name="Triage",
    instructions=(
        "Determine what the user needs. "
        "Hand off to Math Expert for math problems. "
        "Hand off to Writing Expert for writing help. "
        "For other questions, answer directly."
    ),
    handoffs=[math_agent, writing_agent],
)

# Run with triage as entry point
result = Runner.run_sync(triage_agent, "Can you help me solve 3x + 5 = 20?")
print(f"Handled by: {result.last_agent.name}")
print(result.final_output)
```

## Step 5: Structured Output

Get structured responses using Pydantic:

```python
from pydantic import BaseModel
from agents import Agent, Runner

class TaskAnalysis(BaseModel):
    task_type: str
    priority: str
    estimated_time: str
    steps: list[str]

agent = Agent(
    name="Task Analyzer",
    instructions="Analyze tasks and break them into steps.",
    output_type=TaskAnalysis,
)

result = Runner.run_sync(agent, "Plan a birthday party for 20 people")
print(f"Type: {result.final_output.task_type}")
print(f"Priority: {result.final_output.priority}")
print(f"Time: {result.final_output.estimated_time}")
for i, step in enumerate(result.final_output.steps, 1):
    print(f"  {i}. {step}")
```

## Step 6: Adding Guardrails

Protect your agent with input validation:

```python
from agents import Agent, Runner, InputGuardrail, GuardrailFunctionOutput
from agents.exceptions import InputGuardrailTripwireTriggered

async def check_appropriate(input_text: str) -> GuardrailFunctionOutput:
    """Block off-topic requests."""
    off_topic_keywords = ["homework", "cheat", "hack"]
    is_inappropriate = any(kw in input_text.lower() for kw in off_topic_keywords)
    return GuardrailFunctionOutput(
        tripwire_triggered=is_inappropriate,
        output_info={"reason": "Off-topic request"} if is_inappropriate else None
    )

agent = Agent(
    name="Customer Service",
    instructions="Help customers with product questions.",
    input_guardrails=[
        InputGuardrail(guardrail_function=check_appropriate),
    ],
)

try:
    result = Runner.run_sync(agent, "Help me with my homework")
except InputGuardrailTripwireTriggered as e:
    print(f"Blocked: {e.guardrail_result.output_info}")
```

## Step 7: Streaming Responses

Stream responses for better UX:

```python
import asyncio
from agents import Agent, Runner

agent = Agent(
    name="Storyteller",
    instructions="Tell engaging stories."
)

async def main():
    result = await Runner.run_streamed(agent, "Tell me a short story about a robot.")
    
    async for event in result.stream_events():
        if hasattr(event, 'delta'):
            print(event.delta, end='', flush=True)
    
    print("\n\n--- Story complete ---")

asyncio.run(main())
```

## Common Patterns

### Context Injection

```python
from dataclasses import dataclass
from agents import Agent, Runner

@dataclass
class UserContext:
    user_id: str
    name: str
    subscription: str

agent = Agent[UserContext](
    name="Personalized Assistant",
    instructions="Greet users by name and consider their subscription level.",
)

result = await Runner.run(
    agent,
    "What features do I have access to?",
    context=UserContext(user_id="123", name="Alice", subscription="pro"),
)
```

### Conversation History

```python
agent = Agent(name="Assistant", instructions="...")

# First message
result1 = Runner.run_sync(agent, "My name is Bob")

# Continue conversation
result2 = Runner.run_sync(
    agent,
    result1.to_input_list() + [{"role": "user", "content": "What's my name?"}]
)
print(result2.final_output)  # Should mention "Bob"
```

## Next Steps

- Read `_INFO_OASDKP-IN04_AGENTS.md` for detailed agent configuration
- Explore `_INFO_OASDKP-IN10_TOOLS_FUNCTION.md` for advanced tool creation
- Check `_INFO_OASDKP-IN19_TRACING.md` for debugging and monitoring
- See `_INFO_OASDKP-IN27_EXAMPLES.md` for complete application examples

## Troubleshooting

### API Key Not Found

```
openai.AuthenticationError: No API key provided
```

**Solution**: Set `OPENAI_API_KEY` environment variable

### Module Not Found

```
ModuleNotFoundError: No module named 'agents'
```

**Solution**: Install with `pip install openai-agents`

### Python Version

```
This package requires Python 3.9 or later
```

**Solution**: Upgrade Python to 3.9+

## Document History

**[2026-02-11 12:35]**
- Initial quickstart guide created
- Progressive learning path with 7 steps
