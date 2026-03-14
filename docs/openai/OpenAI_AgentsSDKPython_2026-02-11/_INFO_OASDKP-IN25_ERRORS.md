# INFO: Errors and Exception Handling

**Doc ID**: OASDKP-IN25
**Goal**: Document exception types and error handling patterns
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-RUNNING` - Exceptions documentation

## Summary

The SDK defines specific exception types for common error conditions: `MaxTurnsExceeded` when the agent loop exceeds the configured limit, `InputGuardrailTripwireTriggered` when input validation fails, `OutputGuardrailTripwireTriggered` when output validation fails, and `ToolError` for recoverable tool failures. Understanding these exceptions enables proper error handling and graceful degradation. The SDK also supports custom error handlers for centralized error management. [VERIFIED]

## Exception Types

### MaxTurnsExceeded

Raised when agent loop exceeds `max_turns`:

```python
from agents import Agent, Runner
from agents.exceptions import MaxTurnsExceeded

agent = Agent(name="Assistant", tools=[recursive_tool])

try:
    result = await Runner.run(agent, input, max_turns=10)
except MaxTurnsExceeded as e:
    print(f"Agent took too many turns: {e}")
    # Handle gracefully - maybe summarize partial progress
```

### InputGuardrailTripwireTriggered

Raised when input guardrail fails:

```python
from agents.exceptions import InputGuardrailTripwireTriggered

try:
    result = await Runner.run(agent, user_input)
except InputGuardrailTripwireTriggered as e:
    print(f"Input blocked: {e.guardrail_result.output_info}")
    # Respond to user appropriately
```

### OutputGuardrailTripwireTriggered

Raised when output guardrail fails:

```python
from agents.exceptions import OutputGuardrailTripwireTriggered

try:
    result = await Runner.run(agent, input)
except OutputGuardrailTripwireTriggered as e:
    print(f"Output blocked: {e.guardrail_result.output_info}")
    # May need to regenerate or filter response
```

### ToolError

Raise from tools for recoverable errors:

```python
from agents import function_tool
from agents.tools import ToolError

@function_tool
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ToolError("Cannot divide by zero")
    return a / b
```

The LLM receives the error message and can retry or inform the user.

## Custom Error Handlers

Centralized error handling:

```python
from agents import Agent, Runner

async def my_error_handler(error: Exception, context):
    """Handle errors during agent execution."""
    print(f"Error: {type(error).__name__}: {error}")
    
    # Log to monitoring system
    log_error(error, context)
    
    # Return None to re-raise, or return value to continue
    if isinstance(error, ToolError):
        return "Tool failed, please try again"
    
    return None  # Re-raise other errors

result = await Runner.run(
    agent,
    input,
    error_handler=my_error_handler,
)
```

## Error Handling Patterns

### Graceful Degradation

```python
async def robust_run(agent, input, fallback_response):
    try:
        result = await Runner.run(agent, input, max_turns=5)
        return result.final_output
    except MaxTurnsExceeded:
        return fallback_response
    except InputGuardrailTripwireTriggered:
        return "I can't help with that request."
    except Exception as e:
        log_error(e)
        return "Something went wrong. Please try again."
```

### Retry with Backoff

```python
import asyncio

async def run_with_retry(agent, input, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await Runner.run(agent, input)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # Exponential backoff
            await asyncio.sleep(wait_time)
```

### Partial Result Recovery

```python
from agents.exceptions import MaxTurnsExceeded

try:
    result = await Runner.run(agent, input, max_turns=10)
except MaxTurnsExceeded as e:
    # Access partial results
    partial_items = e.partial_result.new_items
    last_output = extract_last_output(partial_items)
    return f"Partial result: {last_output}"
```

## Tool Error Best Practices

### Informative Error Messages

```python
@function_tool
def get_user(user_id: str) -> dict:
    """Get user by ID."""
    user = db.find_user(user_id)
    if not user:
        raise ToolError(f"User '{user_id}' not found. Check the ID and try again.")
    return user
```

### Categorized Errors

```python
class ValidationError(ToolError):
    pass

class NotFoundError(ToolError):
    pass

@function_tool
def process_order(order_id: str) -> dict:
    if not order_id.startswith("ORD-"):
        raise ValidationError("Order ID must start with 'ORD-'")
    
    order = db.find_order(order_id)
    if not order:
        raise NotFoundError(f"Order {order_id} not found")
    
    return order
```

## Logging and Monitoring

```python
import logging

logger = logging.getLogger("agents")

async def monitored_run(agent, input):
    try:
        result = await Runner.run(agent, input)
        logger.info(f"Success: {agent.name}")
        return result
    except MaxTurnsExceeded as e:
        logger.warning(f"Max turns: {agent.name}")
        raise
    except InputGuardrailTripwireTriggered as e:
        logger.warning(f"Input blocked: {e.guardrail_result}")
        raise
    except Exception as e:
        logger.error(f"Error: {agent.name}: {e}")
        raise
```

## Best Practices

- Catch specific exceptions, not bare `Exception`
- Provide helpful error messages to users
- Use ToolError for recoverable tool failures
- Log errors with context for debugging
- Implement fallbacks for critical paths

## Related Topics

- `_INFO_OASDKP-IN15_GUARDRAILS.md` [OASDKP-IN15] - Guardrail configuration
- `_INFO_OASDKP-IN05_RUNNER.md` [OASDKP-IN05] - Run configuration

## API Reference

### Exceptions

- **MaxTurnsExceeded**
  - Import: `from agents.exceptions import MaxTurnsExceeded`

- **InputGuardrailTripwireTriggered**
  - Import: `from agents.exceptions import InputGuardrailTripwireTriggered`
  - Property: `guardrail_result`

- **OutputGuardrailTripwireTriggered**
  - Import: `from agents.exceptions import OutputGuardrailTripwireTriggered`

- **ToolError**
  - Import: `from agents.tools import ToolError`

## Document History

**[2026-02-11 13:35]**
- Initial errors documentation created
