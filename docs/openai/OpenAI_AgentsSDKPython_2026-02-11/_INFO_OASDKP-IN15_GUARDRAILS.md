# INFO: Guardrails

**Doc ID**: OASDKP-IN15
**Goal**: Complete documentation of input/output guardrails and tripwires
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-GUARDRAILS` - Official guardrails documentation

## Summary

Guardrails enable checks and validations on user input and agent output to ensure safety, relevance, and compliance. The SDK supports three types: input guardrails (validate user input), output guardrails (validate agent responses), and tool guardrails (validate tool inputs/outputs). Guardrails can run in blocking mode (before agent) or parallel mode (alongside agent). When a guardrail fails, it triggers a tripwire that raises an exception, allowing fast-fail behavior. This is particularly useful for preventing malicious usage, filtering off-topic requests, and ensuring output quality without running expensive model calls unnecessarily. [VERIFIED]

## Guardrail Types

### 1. Input Guardrails

Run on the initial user input before or alongside agent execution:

```python
from agents import Agent, InputGuardrail, GuardrailFunctionOutput

async def check_relevance(input_text: str) -> GuardrailFunctionOutput:
    """Check if input is relevant to customer service."""
    # Use a fast/cheap model for screening
    is_relevant = "help" in input_text.lower() or "order" in input_text.lower()
    return GuardrailFunctionOutput(
        tripwire_triggered=not is_relevant,
        output_info={"reason": "Off-topic request"} if not is_relevant else None
    )

agent = Agent(
    name="Customer Service",
    instructions="Help customers with orders",
    input_guardrails=[
        InputGuardrail(guardrail_function=check_relevance),
    ],
)
```

### 2. Output Guardrails

Run on the final agent output:

```python
from agents import Agent, OutputGuardrail, GuardrailFunctionOutput

async def check_no_pii(output_text: str) -> GuardrailFunctionOutput:
    """Ensure output doesn't contain PII."""
    has_pii = detect_pii(output_text)  # Your PII detection logic
    return GuardrailFunctionOutput(
        tripwire_triggered=has_pii,
        output_info={"reason": "PII detected"} if has_pii else None
    )

agent = Agent(
    name="Assistant",
    output_guardrails=[
        OutputGuardrail(guardrail_function=check_no_pii),
    ],
)
```

### 3. Tool Guardrails

Validate tool inputs and outputs:

```python
from agents import Agent, ToolGuardrail

async def validate_tool_call(tool_name: str, tool_input: dict) -> GuardrailFunctionOutput:
    """Validate tool calls before execution."""
    if tool_name == "delete_record" and not is_authorized():
        return GuardrailFunctionOutput(
            tripwire_triggered=True,
            output_info={"reason": "Unauthorized deletion attempt"}
        )
    return GuardrailFunctionOutput(tripwire_triggered=False)

agent = Agent(
    name="Admin Assistant",
    tool_guardrails=[
        ToolGuardrail(guardrail_function=validate_tool_call),
    ],
)
```

## Execution Modes

### Blocking Mode (Default)

Guardrail runs before agent execution. If tripwire triggers, agent never runs:

```python
from agents import InputGuardrail, GuardrailExecutionMode

guardrail = InputGuardrail(
    guardrail_function=check_relevance,
    execution_mode=GuardrailExecutionMode.BLOCKING,
)
```

**Pros**: Saves cost by preventing expensive model calls
**Cons**: Adds latency to every request

### Parallel Mode

Guardrail runs alongside agent execution:

```python
guardrail = InputGuardrail(
    guardrail_function=check_relevance,
    execution_mode=GuardrailExecutionMode.PARALLEL,
)
```

**Pros**: No additional latency for valid requests
**Cons**: Agent may start before guardrail completes

## Tripwires

When `tripwire_triggered=True`, an exception is raised:

```python
from agents import Runner
from agents.exceptions import InputGuardrailTripwireTriggered

try:
    result = await Runner.run(agent, "Do my math homework")
except InputGuardrailTripwireTriggered as e:
    print(f"Request blocked: {e.guardrail_result.output_info}")
    # Handle blocked request appropriately
```

## GuardrailFunctionOutput

The return type for guardrail functions:

```python
from agents import GuardrailFunctionOutput

# Passing guardrail
output = GuardrailFunctionOutput(
    tripwire_triggered=False,
    output_info=None,
)

# Failing guardrail
output = GuardrailFunctionOutput(
    tripwire_triggered=True,
    output_info={
        "reason": "Content policy violation",
        "category": "inappropriate",
        "confidence": 0.95,
    },
)
```

### Properties

- **tripwire_triggered**
  - Type: `bool`
  - Purpose: Whether the guardrail failed

- **output_info**
  - Type: `Any`
  - Purpose: Additional context about the decision

## Implementing a Guardrail

### Using an LLM for Classification

```python
from agents import Agent, InputGuardrail, GuardrailFunctionOutput, Runner

# Fast screening agent
screener = Agent(
    name="Screener",
    model="gpt-5-nano",  # Fast/cheap model
    instructions="Classify if input is appropriate for customer service. Return 'yes' or 'no'.",
)

async def llm_screen(input_text: str) -> GuardrailFunctionOutput:
    result = await Runner.run(screener, input_text)
    is_appropriate = result.final_output.strip().lower() == "yes"
    return GuardrailFunctionOutput(
        tripwire_triggered=not is_appropriate,
        output_info={"classification": result.final_output}
    )

main_agent = Agent(
    name="Customer Service",
    model="gpt-5.2",  # Expensive model
    instructions="Help customers",
    input_guardrails=[
        InputGuardrail(guardrail_function=llm_screen),
    ],
)
```

### Using External Services

```python
async def moderation_guardrail(input_text: str) -> GuardrailFunctionOutput:
    """Use OpenAI moderation API."""
    from openai import AsyncOpenAI
    
    client = AsyncOpenAI()
    response = await client.moderations.create(input=input_text)
    
    is_flagged = response.results[0].flagged
    return GuardrailFunctionOutput(
        tripwire_triggered=is_flagged,
        output_info={"categories": response.results[0].categories}
    )
```

## Multiple Guardrails

Guardrails run in order; first tripwire wins:

```python
agent = Agent(
    name="Secure Assistant",
    input_guardrails=[
        InputGuardrail(guardrail_function=check_auth),      # First
        InputGuardrail(guardrail_function=check_rate_limit), # Second
        InputGuardrail(guardrail_function=check_content),    # Third
    ],
)
```

## Important Notes

**Input guardrails only run on the first agent**. If a handoff occurs, the target agent's guardrails don't run on the original input. This is intentional - the guardrails property is on the agent for colocation, but they're meant to screen initial user input. [VERIFIED]

## Limitations

- Input guardrails only run on first agent
- Parallel mode may allow some processing before tripwire
- Guardrail latency affects overall response time

## Best Practices

- Use cheap/fast models for guardrail classification
- Use blocking mode for security-critical checks
- Use parallel mode for quality checks that can fail gracefully
- Log guardrail decisions for monitoring
- Return detailed `output_info` for debugging
- Layer multiple guardrails for defense in depth

## Related Topics

- `_INFO_OASDKP-IN25_ERRORS.md` [OASDKP-IN25] - Exception handling
- `_INFO_OASDKP-IN04_AGENTS.md` [OASDKP-IN04] - Agent configuration

## API Reference

### Classes

- **InputGuardrail**
  - Import: `from agents import InputGuardrail`
  - Params: `guardrail_function`, `execution_mode`

- **OutputGuardrail**
  - Import: `from agents import OutputGuardrail`

- **ToolGuardrail**
  - Import: `from agents import ToolGuardrail`

- **GuardrailFunctionOutput**
  - Import: `from agents import GuardrailFunctionOutput`
  - Properties: `tripwire_triggered`, `output_info`

- **GuardrailExecutionMode**
  - Import: `from agents import GuardrailExecutionMode`
  - Values: `BLOCKING`, `PARALLEL`

### Exceptions

- **InputGuardrailTripwireTriggered**
  - Import: `from agents.exceptions import InputGuardrailTripwireTriggered`
  - Properties: `guardrail_result`

- **OutputGuardrailTripwireTriggered**
  - Import: `from agents.exceptions import OutputGuardrailTripwireTriggered`

## Document History

**[2026-02-11 12:15]**
- Initial document created
- All guardrail types and patterns documented
