# INFO: Context and Dependency Injection

**Doc ID**: OASDKP-IN06
**Goal**: Document the context system for dependency injection
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-AGENTS` - Context documentation

## Summary

Context is the SDK's dependency injection mechanism. It allows passing any Python object to agents, tools, handoffs, and other components during a run. Agents are generic on their context type (`Agent[TContext]`), enabling type-safe access to dependencies. Context is created by the caller and passed to `Runner.run()`, then automatically propagated to all components. This pattern enables clean separation of concerns, testability, and access to runtime state like user information, database connections, or configuration. [VERIFIED]

## Basic Usage

### Defining Context

```python
from dataclasses import dataclass
from agents import Agent

@dataclass
class AppContext:
    user_id: str
    user_name: str
    is_admin: bool
    db_connection: any  # Database connection

# Type-safe agent with context
agent = Agent[AppContext](
    name="Context-Aware Agent",
    instructions="Help users with their requests",
)
```

### Passing Context

```python
from agents import Runner

context = AppContext(
    user_id="123",
    user_name="Alice",
    is_admin=False,
    db_connection=get_db_connection(),
)

result = await Runner.run(
    agent,
    "What can I do?",
    context=context,
)
```

## RunContextWrapper

Context is wrapped in `RunContextWrapper` when accessed in tools and dynamic functions:

```python
from agents import function_tool, RunContextWrapper

@function_tool
def get_user_data(context: RunContextWrapper[AppContext]) -> dict:
    """Get current user's data."""
    user = context.context  # Access the actual context
    return {
        "id": user.user_id,
        "name": user.user_name,
        "admin": user.is_admin,
    }
```

### RunContextWrapper Properties

- **context** - The actual context object you passed
- **agent** - Current agent being executed
- **run_config** - Current run configuration

## Accessing Context in Components

### In Function Tools

```python
@function_tool
def admin_action(context: RunContextWrapper[AppContext]) -> str:
    """Perform admin action."""
    if not context.context.is_admin:
        return "Error: Admin access required"
    return "Admin action completed"
```

### In Dynamic Instructions

```python
def personalized_instructions(
    context: RunContextWrapper[AppContext],
    agent: Agent[AppContext]
) -> str:
    user = context.context
    return f"You are helping {user.user_name}. Be friendly and helpful."

agent = Agent[AppContext](
    name="Personal Assistant",
    instructions=personalized_instructions,
)
```

### In Guardrails

```python
async def admin_only_guardrail(
    input_text: str,
    context: RunContextWrapper[AppContext]
) -> GuardrailFunctionOutput:
    if not context.context.is_admin:
        return GuardrailFunctionOutput(
            tripwire_triggered=True,
            output_info={"reason": "Admin access required"}
        )
    return GuardrailFunctionOutput(tripwire_triggered=False)
```

## Context Patterns

### User Session Context

```python
@dataclass
class SessionContext:
    session_id: str
    user: User
    preferences: dict
    cart: ShoppingCart
```

### Multi-Service Context

```python
@dataclass
class ServiceContext:
    db: DatabaseConnection
    cache: RedisClient
    email_service: EmailService
    payment_processor: PaymentProcessor
```

### Feature Flags Context

```python
@dataclass
class FeatureContext:
    user_id: str
    features: dict[str, bool]
    
    def is_enabled(self, feature: str) -> bool:
        return self.features.get(feature, False)
```

## Context Propagation

Context flows through the entire agent run:

```
Runner.run(agent, input, context=ctx)
    │
    ├── Agent receives context
    │   ├── Dynamic instructions(context, agent)
    │   ├── Tools receive context
    │   └── Guardrails receive context
    │
    ├── Handoff to another agent
    │   └── Target agent receives same context
    │
    └── Agent as tool
        └── Tool-agent receives same context
```

## Type Safety

Generic agents provide type checking:

```python
# Correct: Type-safe access
agent = Agent[AppContext](...)

@function_tool
def my_tool(context: RunContextWrapper[AppContext]) -> str:
    user_id = context.context.user_id  # Type checker knows this exists
    return f"User: {user_id}"

# Wrong: Type mismatch caught by type checker
agent = Agent[AppContext](...)
Runner.run(agent, "hello", context=DifferentContext())  # Type error!
```

## Testing with Context

Mock context for testing:

```python
def test_admin_tool():
    # Arrange
    mock_context = AppContext(
        user_id="test",
        user_name="Test User",
        is_admin=True,
        db_connection=MockDatabase(),
    )
    
    # Act
    result = Runner.run_sync(agent, "Do admin thing", context=mock_context)
    
    # Assert
    assert "completed" in result.final_output
```

## Best Practices

- Use dataclasses or Pydantic models for context
- Keep context immutable during runs
- Include only what components need
- Use type hints for safety
- Create test contexts for testing

## Related Topics

- `_INFO_OASDKP-IN04_AGENTS.md` [OASDKP-IN04] - Agent configuration
- `_INFO_OASDKP-IN10_TOOLS_FUNCTION.md` [OASDKP-IN10] - Function tools

## API Reference

### Classes

- **RunContextWrapper[T]**
  - Import: `from agents import RunContextWrapper`
  - Properties: `context`, `agent`, `run_config`

## Document History

**[2026-02-11 12:55]**
- Initial context documentation created
