# INFO: Sessions

**Doc ID**: OASDKP-IN17
**Goal**: Document session management for persistent agent memory
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GH-REPO` - Session implementation

## Summary

Sessions provide a persistent memory layer for maintaining working context within and across agent runs. The SDK includes built-in session implementations for SQLite and Redis, plus a protocol for custom implementations. Sessions store conversation history, agent state, and metadata, enabling multi-turn conversations without manual history management. Sessions are optional - you can also manage conversation state manually using `to_input_list()`. [VERIFIED]

## Session Protocol

Sessions implement a simple interface:

```python
from typing import Protocol

class Session(Protocol):
    async def get(self, key: str) -> Any:
        """Retrieve a value from the session."""
        ...
    
    async def set(self, key: str, value: Any) -> None:
        """Store a value in the session."""
        ...
    
    async def delete(self, key: str) -> None:
        """Remove a value from the session."""
        ...
    
    async def get_messages(self) -> list[dict]:
        """Get conversation history."""
        ...
    
    async def add_message(self, message: dict) -> None:
        """Add a message to history."""
        ...
```

## SQLite Session

Persistent local storage:

```python
from agents import Agent, Runner
from agents.sessions import SQLiteSession

# Create session
session = SQLiteSession(
    db_path="./sessions.db",
    session_id="user_123_conversation_456",
)

agent = Agent(name="Assistant", instructions="Be helpful")

# First message
result1 = await Runner.run(
    agent,
    "My name is Alice",
    session=session,
)

# Later... session remembers
result2 = await Runner.run(
    agent,
    "What's my name?",
    session=session,
)
print(result2.final_output)  # "Your name is Alice"
```

### SQLiteSession Options

- **db_path**: Path to SQLite database file
- **session_id**: Unique identifier for this session
- **table_name**: Custom table name (optional)

## Redis Session

Distributed session storage:

```python
from agents.sessions import RedisSession

session = RedisSession(
    redis_url="redis://localhost:6379",
    session_id="user_123_conversation_456",
    ttl=3600,  # Expire after 1 hour
)

result = await Runner.run(agent, input, session=session)
```

### RedisSession Options

- **redis_url**: Redis connection URL
- **session_id**: Unique identifier
- **ttl**: Time-to-live in seconds (optional)
- **prefix**: Key prefix (optional)

## Custom Session Implementation

```python
from agents.sessions import Session

class CustomSession(Session):
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages = []
        self.data = {}
    
    async def get(self, key: str):
        return self.data.get(key)
    
    async def set(self, key: str, value):
        self.data[key] = value
    
    async def delete(self, key: str):
        self.data.pop(key, None)
    
    async def get_messages(self):
        return self.messages
    
    async def add_message(self, message: dict):
        self.messages.append(message)

# Use custom session
session = CustomSession("my_session")
result = await Runner.run(agent, input, session=session)
```

## Session vs Manual History

### Using Sessions (Automatic)

```python
session = SQLiteSession(db_path="./db.sqlite", session_id="123")

# Automatic history management
await Runner.run(agent, "Hello", session=session)
await Runner.run(agent, "What did I say?", session=session)  # Knows history
```

### Manual History (to_input_list)

```python
# Manual history management
result1 = await Runner.run(agent, "Hello")

# Continue with explicit history
result2 = await Runner.run(
    agent,
    result1.to_input_list() + [{"role": "user", "content": "What did I say?"}]
)
```

## Session Metadata

Store additional data in sessions:

```python
session = SQLiteSession(db_path="./db.sqlite", session_id="123")

# Store metadata
await session.set("user_preferences", {"theme": "dark"})
await session.set("last_topic", "billing")

# Retrieve later
prefs = await session.get("user_preferences")
```

## Session with Multiple Agents

Sessions work across handoffs:

```python
triage = Agent(name="Triage", handoffs=[specialist])
specialist = Agent(name="Specialist", instructions="...")

session = SQLiteSession(db_path="./db.sqlite", session_id="123")

# Conversation history shared across agents
await Runner.run(triage, "I need help with billing", session=session)
# If handed off, specialist sees history
```

## Session Cleanup

```python
# SQLite - messages persist until deleted
session = SQLiteSession(...)
# Manually clean old sessions via SQL

# Redis - automatic TTL
session = RedisSession(
    redis_url="...",
    session_id="123",
    ttl=86400,  # Auto-expire after 24 hours
)
```

## Best Practices

- Use SQLite for single-instance applications
- Use Redis for distributed/multi-instance
- Set reasonable TTLs to manage storage
- Use unique session_ids per conversation
- Clean up old sessions periodically

## Limitations

- Sessions add I/O latency
- Large histories increase token usage
- No built-in summarization of long histories

## Related Topics

- `_INFO_OASDKP-IN18_CONVERSATIONS.md` [OASDKP-IN18] - Conversation management
- `_INFO_OASDKP-IN05_RUNNER.md` [OASDKP-IN05] - Running agents

## API Reference

### Classes

- **SQLiteSession**
  - Import: `from agents.sessions import SQLiteSession`

- **RedisSession**
  - Import: `from agents.sessions import RedisSession`

- **Session** (Protocol)
  - Import: `from agents.sessions import Session`

## Document History

**[2026-02-11 13:15]**
- Initial sessions documentation created
