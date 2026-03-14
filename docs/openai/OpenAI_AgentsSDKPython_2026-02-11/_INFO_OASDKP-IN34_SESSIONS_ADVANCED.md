# INFO: Advanced Session Types

**Doc ID**: OASDKP-IN34
**Goal**: Document SQLAlchemy, Encrypted, and Advanced SQLite sessions
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-SESSIONS` - Sessions documentation

## Summary

Beyond the basic SQLiteSession and RedisSession, the SDK provides advanced session implementations: SQLAlchemySession for database-agnostic persistence using SQLAlchemy ORM, EncryptedSession for secure storage of sensitive conversations, and AdvancedSQLiteSession for enhanced SQLite features like compression and automatic cleanup. These are available in the `agents.extensions` package. [VERIFIED]

## SQLAlchemy Session

Database-agnostic session storage using SQLAlchemy:

```python
from agents.extensions.memory import SQLAlchemySession

# PostgreSQL
session = SQLAlchemySession(
    connection_string="postgresql://user:pass@localhost/db",
    session_id="user_123",
)

# MySQL
session = SQLAlchemySession(
    connection_string="mysql://user:pass@localhost/db",
    session_id="user_123",
)

# SQLite (file)
session = SQLAlchemySession(
    connection_string="sqlite:///sessions.db",
    session_id="user_123",
)
```

### Configuration

```python
SQLAlchemySession(
    connection_string="...",
    session_id="unique_id",
    table_name="agent_sessions",  # Custom table name
    echo=False,                    # SQLAlchemy echo mode
)
```

### Async Support

```python
from agents.extensions.memory import AsyncSQLAlchemySession

session = AsyncSQLAlchemySession(
    connection_string="postgresql+asyncpg://user:pass@localhost/db",
    session_id="user_123",
)
```

## Encrypted Session

Secure session storage with encryption:

```python
from agents.extensions.memory import EncryptedSession

session = EncryptedSession(
    db_path="./secure_sessions.db",
    session_id="user_123",
    encryption_key="your-32-byte-key-here",
)
```

### Key Generation

```python
from cryptography.fernet import Fernet

# Generate a new key
key = Fernet.generate_key()
print(key.decode())  # Store securely

# Use in session
session = EncryptedSession(
    db_path="./sessions.db",
    session_id="123",
    encryption_key=key,
)
```

### What's Encrypted

- Message content
- Tool call arguments
- Tool results
- Session metadata

### What's Not Encrypted

- Session ID (used for lookup)
- Timestamps
- Message count

## Advanced SQLite Session

Enhanced SQLite with additional features:

```python
from agents.extensions.memory import AdvancedSQLiteSession

session = AdvancedSQLiteSession(
    db_path="./sessions.db",
    session_id="user_123",
    compression=True,          # Compress messages
    auto_cleanup=True,         # Remove old messages
    max_messages=100,          # Keep last N messages
    ttl_days=30,               # Auto-expire after N days
)
```

### Features

- **Compression**: Reduce storage size for long conversations
- **Auto-cleanup**: Automatically remove old messages
- **TTL**: Time-based expiration
- **Message limits**: Keep only recent messages

## Session Comparison

| Feature | SQLite | SQLAlchemy | Encrypted | Advanced SQLite |
|---------|--------|------------|-----------|-----------------|
| Simple setup | Yes | No | Yes | Yes |
| Multi-database | No | Yes | No | No |
| Encryption | No | No | Yes | No |
| Compression | No | No | No | Yes |
| Auto-cleanup | No | No | No | Yes |
| Async | No | Yes | No | No |

## Migration Between Sessions

```python
# Export from one session
old_session = SQLiteSession(...)
messages = await old_session.get_messages()

# Import to another
new_session = EncryptedSession(...)
for msg in messages:
    await new_session.add_message(msg)
```

## Best Practices

- Use SQLAlchemy for production with existing databases
- Use Encrypted for sensitive/regulated data
- Use Advanced SQLite for long-running local apps
- Always secure encryption keys properly
- Set appropriate TTLs and limits

## Related Topics

- `_INFO_OASDKP-IN17_SESSIONS.md` [OASDKP-IN17] - Basic sessions
- `_INFO_OASDKP-IN18_CONVERSATIONS.md` [OASDKP-IN18] - Conversation management

## API Reference

### Classes

- **SQLAlchemySession**
  - Import: `from agents.extensions.memory import SQLAlchemySession`

- **AsyncSQLAlchemySession**
  - Import: `from agents.extensions.memory import AsyncSQLAlchemySession`

- **EncryptedSession**
  - Import: `from agents.extensions.memory import EncryptedSession`

- **AdvancedSQLiteSession**
  - Import: `from agents.extensions.memory import AdvancedSQLiteSession`

## Document History

**[2026-02-11 11:55]**
- Initial advanced sessions documentation created
