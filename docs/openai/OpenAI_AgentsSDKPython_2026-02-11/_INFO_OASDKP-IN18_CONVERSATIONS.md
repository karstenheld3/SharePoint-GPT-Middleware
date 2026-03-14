# INFO: Conversation Management

**Doc ID**: OASDKP-IN18
**Goal**: Document conversation history and multi-turn management
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-RUNNING` - Conversation documentation

## Summary

The SDK provides three approaches to conversation management: manual management using `to_input_list()`, automatic management using Sessions, and server-managed conversations using `group_id`. Manual management gives full control but requires explicit history tracking. Sessions automate history storage in SQLite or Redis. Server-managed conversations use OpenAI's infrastructure to maintain state. Choose based on your deployment needs and control requirements. [VERIFIED]

## Manual Conversation Management

Use `to_input_list()` to continue conversations:

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="Be helpful and remember context")

# First message
result1 = await Runner.run(agent, "My favorite color is blue")

# Continue with history
result2 = await Runner.run(
    agent,
    result1.to_input_list() + [{"role": "user", "content": "What's my favorite color?"}]
)
print(result2.final_output)  # "Your favorite color is blue"

# Continue further
result3 = await Runner.run(
    agent,
    result2.to_input_list() + [{"role": "user", "content": "Thanks!"}]
)
```

### Input List Format

The input list follows OpenAI's message format:

```python
[
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help?"},
    {"role": "user", "content": "What's the weather?"},
]
```

## Automatic Session Management

Let sessions handle history:

```python
from agents import Agent, Runner
from agents.sessions import SQLiteSession

session = SQLiteSession(db_path="./chat.db", session_id="user_123")
agent = Agent(name="Assistant", instructions="...")

# Session tracks history automatically
await Runner.run(agent, "Hello", session=session)
await Runner.run(agent, "Remember my name is Bob", session=session)
await Runner.run(agent, "What's my name?", session=session)  # Knows it's Bob
```

## Server-Managed Conversations

Use OpenAI's infrastructure for state:

```python
from agents import Agent, Runner
from agents.run import RunConfig

agent = Agent(name="Assistant", instructions="...")

# Use group_id to link conversation turns
config = RunConfig(group_id="conversation_abc123")

result1 = await Runner.run(agent, "Hello", run_config=config)
result2 = await Runner.run(agent, "Remember this", run_config=config)
result3 = await Runner.run(agent, "What did I say?", run_config=config)
```

## Comparison

| Approach | Storage | Control | Complexity |
|----------|---------|---------|------------|
| Manual | Your code | Full | Low |
| Sessions | SQLite/Redis | High | Medium |
| Server-Managed | OpenAI | Limited | Low |

## Multi-Turn Chat Pattern

```python
async def chat_loop(agent):
    history = []
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == "quit":
            break
        
        # Build messages with history
        messages = history + [{"role": "user", "content": user_input}]
        
        # Run agent
        result = await Runner.run(agent, messages)
        print(f"Assistant: {result.final_output}")
        
        # Update history
        history = result.to_input_list()
```

## History Truncation

Manage token limits with truncation:

```python
def truncate_history(history, max_messages=20):
    """Keep only recent messages."""
    if len(history) > max_messages:
        # Keep first message (context) and last N-1
        return [history[0]] + history[-(max_messages-1):]
    return history

# Use in chat loop
history = truncate_history(result.to_input_list())
```

## History with Handoffs

History persists across handoffs:

```python
triage = Agent(name="Triage", handoffs=[specialist])

# Full conversation passes to specialist on handoff
result = await Runner.run(triage, "I need technical help")
# If handed off, specialist sees: "I need technical help" + triage response
```

## Conversation Context Injection

Add context to conversation start:

```python
# Inject context as first message
context_message = {
    "role": "system",
    "content": f"Current date: {date.today()}. User timezone: PST."
}

result = await Runner.run(
    agent,
    [context_message, {"role": "user", "content": user_input}]
)
```

## Best Practices

- Use sessions for production multi-turn apps
- Truncate long histories to manage tokens
- Use `group_id` for simple server-side persistence
- Clear history when starting new topics

## Related Topics

- `_INFO_OASDKP-IN17_SESSIONS.md` [OASDKP-IN17] - Session implementations
- `_INFO_OASDKP-IN05_RUNNER.md` [OASDKP-IN05] - Runner configuration
- `_INFO_OASDKP-IN07_RESULTS.md` [OASDKP-IN07] - to_input_list()

## Document History

**[2026-02-11 13:20]**
- Initial conversation management documentation created
