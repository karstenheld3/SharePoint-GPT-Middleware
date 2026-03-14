# INFO: Usage Tracking

**Doc ID**: OASDKP-IN33
**Goal**: Document token and cost usage tracking
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-USAGE` - Usage documentation

## Summary

The SDK tracks token usage and provides utilities for monitoring costs across agent runs. Usage information includes input tokens, output tokens, and total tokens per run. This data is available in RunResult and can be aggregated for billing analysis. Usage tracking helps optimize agent efficiency and manage API costs. [VERIFIED]

## Accessing Usage Data

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="...")

result = await Runner.run(agent, "Hello!")

# Access usage
print(f"Input tokens: {result.usage.input_tokens}")
print(f"Output tokens: {result.usage.output_tokens}")
print(f"Total tokens: {result.usage.total_tokens}")
```

## Usage Object

```python
@dataclass
class Usage:
    input_tokens: int
    output_tokens: int
    total_tokens: int
```

## Aggregating Usage

```python
from agents import Agent, Runner

total_usage = {"input": 0, "output": 0, "total": 0}

async def tracked_run(agent, input):
    result = await Runner.run(agent, input)
    total_usage["input"] += result.usage.input_tokens
    total_usage["output"] += result.usage.output_tokens
    total_usage["total"] += result.usage.total_tokens
    return result

# After multiple runs
print(f"Session total: {total_usage}")
```

## Usage with Streaming

```python
result = await Runner.run_streamed(agent, input)

async for event in result.stream_events():
    # Process events
    pass

# Usage available after streaming completes
print(result.usage)
```

## Multi-Agent Usage

Usage accumulates across handoffs:

```python
triage = Agent(name="Triage", handoffs=[specialist])
result = await Runner.run(triage, "Help me")

# Includes tokens from all agents in the run
print(result.usage.total_tokens)
```

## Tool Usage

Tool calls consume tokens:

```python
agent = Agent(name="Tool Agent", tools=[my_tool])
result = await Runner.run(agent, input)

# Includes tool call/result tokens
print(result.usage)
```

## Cost Estimation

```python
def estimate_cost(usage, model="gpt-5"):
    # Example pricing (check current rates)
    prices = {
        "gpt-5": {"input": 0.01, "output": 0.03},
        "gpt-5-mini": {"input": 0.001, "output": 0.002},
    }
    rate = prices.get(model, prices["gpt-5"])
    
    input_cost = (usage.input_tokens / 1000) * rate["input"]
    output_cost = (usage.output_tokens / 1000) * rate["output"]
    return input_cost + output_cost

# Estimate cost
cost = estimate_cost(result.usage)
print(f"Estimated cost: ${cost:.4f}")
```

## Best Practices

- Track usage per session/user
- Set usage budgets and alerts
- Optimize prompts to reduce tokens
- Use smaller models where appropriate
- Monitor tool call frequency

## Related Topics

- `_INFO_OASDKP-IN07_RESULTS.md` [OASDKP-IN07] - Run results
- `_INFO_OASDKP-IN19_TRACING.md` [OASDKP-IN19] - Observability

## API Reference

### Classes

- **Usage**
  - Properties: `input_tokens`, `output_tokens`, `total_tokens`

### Result Properties

- **RunResult.usage** - Usage for the run

## Document History

**[2026-02-11 11:54]**
- Initial usage tracking documentation created
