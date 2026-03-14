# INFO: Context Management

**Doc ID**: OASDKT-IN06
**Goal**: Provide local data via RunContext and expose context to the LLM
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-DOCS-CONTEXT` - Context management documentation

## Summary

Context is an overloaded term in the SDK with two meanings: Local context that your code can access during a run (dependencies, data, callbacks), and Agent/LLM context that the language model sees when generating responses. Local context is represented by `RunContext<T>` - you create an object to hold state or dependencies and pass it to `run()`. All tool calls and hooks receive a RunContext wrapper to read from or modify that object. The context object is NOT sent to the LLM - it is purely local. To make information available to the LLM, add it to agent instructions, include in input, expose via tools, or use retrieval/search tools.

## Local Context

### RunContext<T>

Local context is represented by `RunContext<T>`: [VERIFIED]

```typescript
import { Agent, run, RunContext, tool } from '@openai/agents';
import { z } from 'zod';

interface UserInfo {
  name: string;
  uid: number;
}

const fetchUserAge = tool({
  name: 'fetch_user_age',
  description: 'Return the age of the current user',
  parameters: z.object({}),
  execute: async (
    _args,
    runContext?: RunContext<UserInfo>,
  ): Promise<string> => {
    return `User ${runContext?.context.name} is 47 years old`;
  },
});

async function main() {
  const userInfo: UserInfo = { name: 'John', uid: 123 };

  const agent = new Agent<UserInfo>({
    name: 'Assistant',
    tools: [fetchUserAge],
  });

  const result = await run(agent, 'What is the age of the user?', {
    context: userInfo,
  });

  console.log(result.finalOutput);
  // The user John is 47 years old.
}
```

### Use Cases for Local Context

- Data about the run (user name, IDs, etc.) [VERIFIED]
- Dependencies such as loggers or data fetchers [VERIFIED]
- Helper functions [VERIFIED]

### Important Note

The context object is NOT sent to the LLM. It is purely local and you can read from or write to it freely. [VERIFIED]

### Context Type Consistency

Every agent, tool, and hook participating in a single run must use the same type of context. [VERIFIED]

## Agent/LLM Context

When the LLM is called, the only data it can see comes from the conversation history. [VERIFIED]

### Options to Make Information Available to LLM

1. **Add to Agent instructions** - System or developer message. Can be static string or function receiving context. [VERIFIED]

2. **Include in input** - Pass when calling `run()`. Places message lower in chain of command. [VERIFIED]

3. **Expose via function tools** - LLM can fetch data on demand. [VERIFIED]

4. **Use retrieval or web search tools** - Ground responses in relevant data from files, databases, or web. [VERIFIED]

### Dynamic Instructions Example

```typescript
import { Agent, RunContext } from '@openai/agents';

interface UserContext {
  name: string;
}

function buildInstructions(runContext: RunContext<UserContext>) {
  return `The user's name is ${runContext.context.name}. Be extra friendly!`;
}

const agent = new Agent<UserContext>({
  name: 'Personalized helper',
  instructions: buildInstructions,
});
```

## Limitations and Known Issues

- Context type must be consistent across all participants in a run [VERIFIED]
- Context is not automatically serialized or persisted [VERIFIED]

## Gotchas and Quirks

- Context is NOT sent to LLM - purely local [VERIFIED]
- RunContext wraps your context object with additional runner info [VERIFIED]
- Tools receive RunContext as optional second argument [VERIFIED]

## Best Practices

- Define a TypeScript interface for your context type [VERIFIED]
- Use context for dependency injection (loggers, database clients) [VERIFIED]
- Use dynamic instructions to personalize LLM behavior based on context [VERIFIED]
- Expose context data to LLM via tools when needed [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN04_AGENTS.md` [OASDKT-IN04] - Agent configuration
- `_INFO_OASDKT-IN09_TOOLS.md` [OASDKT-IN09] - Tool definitions

## API Reference

### Types

- **RunContext<T>**
  - Import: `import { RunContext } from "@openai/agents"`
  - Properties: `context` (T), plus runner metadata

### Run Options

- **context** - Your custom context object passed to `run()`

## Document History

**[2026-02-11 19:55]**
- Initial document created
- Local and LLM context patterns documented
