# INFO: Sessions

**Doc ID**: OASDKT-IN15
**Goal**: Persist multi-turn conversation history across runs
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-DOCS-SESSIONS` - Sessions documentation

## Summary

Sessions give the Agents SDK a persistent memory layer. Provide any object implementing the Session interface to `run()`, and the SDK automatically fetches previously stored conversation items, prepends them to the next turn, and persists new user input and assistant output after each run. This removes the need to manually call `toInputList()` or stitch history between turns. The SDK ships with `OpenAIConversationsSession` for the Conversations API and `MemorySession` for local development. Because they share the Session interface, you can plug in your own storage backend. Use `OpenAIResponsesCompactionSession` to automatically shrink stored transcripts.

## Quick Start

```typescript
import { Agent, OpenAIConversationsSession, run } from '@openai/agents';

const agent = new Agent({
  name: 'TourGuide',
  instructions: 'Answer with compact travel facts.',
});

// Use built-in OpenAIConversationsSession
const session = new OpenAIConversationsSession();

const firstTurn = await run(agent, 'What city is the Golden Gate Bridge in?', {
  session,
});
console.log(firstTurn.finalOutput); // "San Francisco"

const secondTurn = await run(agent, 'What state is it in?', { session });
console.log(secondTurn.finalOutput); // "California"
```

Reusing the same session instance ensures the agent receives full conversation history. [VERIFIED]

## Built-in Session Implementations

### OpenAIConversationsSession

Syncs memory with OpenAI Conversations API: [VERIFIED]

```typescript
import { OpenAIConversationsSession } from '@openai/agents';

const session = new OpenAIConversationsSession({
  conversationId: 'optional-existing-id',
  apiKey: 'optional-override',
});
```

**Constructor Options:**
- **conversationId** - `string` - Existing conversation ID
- **client** - `OpenAI` - Custom OpenAI client
- **apiKey** - `string` - API key override
- **baseURL** - `string` - Custom base URL
- **organization** - `string` - Organization ID
- **project** - `string` - Project ID

### MemorySession

In-memory session for local development: [VERIFIED]

```typescript
import { MemorySession } from '@openai/agents';

const session = new MemorySession();
```

## How the Runner Uses Sessions

1. **Before each run** - Retrieves session history, merges with new input [VERIFIED]
2. **After non-streaming run** - Calls `session.addItems()` to persist input and output [VERIFIED]
3. **For streaming runs** - Writes user input first, appends outputs when turn completes [VERIFIED]
4. **When resuming from `RunResult.state`** - Adds resumed turn to memory without re-preparing input [VERIFIED]

## Custom Session Implementations

Implement the Session interface for custom storage: [VERIFIED]

```typescript
interface Session {
  getItems(): Promise<AgentInputItem[]>;
  addItems(items: AgentInputItem[]): Promise<void>;
}
```

Sample backends available in `examples/memory/` (Prisma, file-backed, etc.) [VERIFIED]

## History Compaction

### OpenAIResponsesCompactionSession

Wrap any session to auto-shrink transcripts: [VERIFIED]

```typescript
import { 
  OpenAIConversationsSession, 
  OpenAIResponsesCompactionSession 
} from '@openai/agents';

const baseSession = new OpenAIConversationsSession();
const session = new OpenAIResponsesCompactionSession(baseSession);
```

Uses `responses.compact` API to reduce history size. [VERIFIED]

## Inspecting and Editing History

Access stored items via `session.getItems()`. [VERIFIED]

## Control History Merging

Customize how history and new items merge via `sessionInputCallback`. [VERIFIED]

## Handling Approvals and Resumable Runs

When resuming from `RunResult.state` (for approvals or interruptions), keep passing the same session. [VERIFIED]

## Limitations and Known Issues

- `OpenAIConversationsSession` requires OPENAI_API_KEY [VERIFIED]
- Memory sessions don't persist across process restarts [VERIFIED]

## Gotchas and Quirks

- Reuse same session instance across turns for continuity [VERIFIED]
- Session interface is simple - just getItems() and addItems() [VERIFIED]
- Compaction session wraps another session for auto-shrinking [VERIFIED]

## Best Practices

- Use `OpenAIConversationsSession` for production [VERIFIED]
- Use `MemorySession` for local development/testing [VERIFIED]
- Implement custom Session for specialized storage needs [VERIFIED]
- Use compaction session to manage growing history [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN05_RUNNER.md` [OASDKT-IN05] - Running agents
- `_INFO_OASDKT-IN17_HUMANINLOOP.md` [OASDKT-IN17] - Human-in-the-loop

## API Reference

### Classes

- **OpenAIConversationsSession**
  - Import: `import { OpenAIConversationsSession } from "@openai/agents"`

- **MemorySession**
  - Import: `import { MemorySession } from "@openai/agents"`

- **OpenAIResponsesCompactionSession**
  - Import: `import { OpenAIResponsesCompactionSession } from "@openai/agents"`

### Interfaces

- **Session**
  - Methods: `getItems()`, `addItems(items)`

## Document History

**[2026-02-11 20:15]**
- Initial document created
- Session implementations and patterns documented
