# INFO: Running Agents

**Doc ID**: OASDKT-IN05
**Goal**: Configure and execute agent workflows with the Runner class
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-DOCS-RUNNER` - Running agents documentation page

## Summary

Agents are executed using the Runner class or the run() utility function. The runner executes an agent loop that calls the model, inspects responses, handles tool calls, processes handoffs, and returns when final output is produced. The run() function uses a singleton default Runner for simple scripts. Input can be a string (user message) or array of input items. Key options include maxTurns (default 10), context for dependency injection, stream for real-time events, and session for persistent memory. Conversation threads are managed by passing result.history to subsequent runs. The Runner should be created once at app start and reused across requests.

## Basic Usage

### Using run() Utility

```typescript
import { Agent, run } from '@openai/agents';

const agent = new Agent({
  name: 'Assistant',
  instructions: 'You are a helpful assistant',
});

const result = await run(
  agent,
  'Write a haiku about recursion in programming.',
);

console.log(result.finalOutput);
// Code within the code,
// Functions calling themselves,
// Infinite loop's dance.
```

### Using Runner Class

```typescript
import { Agent, Runner } from '@openai/agents';

const agent = new Agent({
  name: 'Assistant',
  instructions: 'You are a helpful assistant',
});

// Create runner with custom configuration
const runner = new Runner();

const result = await runner.run(
  agent,
  'Write a haiku about recursion in programming.',
);

console.log(result.finalOutput);
```

## The Agent Loop

When you call `run()`, the runner executes a loop: [VERIFIED]

1. Call the current agent's model with the current input
2. Inspect the LLM response:
   - **Final output** → return result
   - **Handoff** → switch to new agent, keep conversation history, go to 1
   - **Tool calls** → execute tools, append results to conversation, go to 1
3. Throw `MaxTurnsExceededError` once maxTurns is reached

### Final Output Rule

Output is "final" when it produces text with the desired type AND there are no tool calls. [VERIFIED]

## Runner Lifecycle

Create a Runner when your app starts and reuse it across requests. [VERIFIED]

```typescript
// Create once at app start
const runner = new Runner({
  model: 'gpt-5.2',
  tracingDisabled: false,
});

// Reuse across requests
async function handleRequest(userInput: string) {
  const result = await runner.run(agent, userInput);
  return result.finalOutput;
}
```

For simple scripts, use `run()` which uses a default runner internally. [VERIFIED]

## Run Arguments

### Input Types

- **String** - Treated as user message [VERIFIED]
- **Array of input items** - OpenAI Responses API format [VERIFIED]
- **RunState object** - For human-in-the-loop agents [VERIFIED]

### Run Options

- **stream** - Boolean, enables streaming (returns StreamedRunResult) [VERIFIED]
- **context** - Dependency injection object [VERIFIED]
- **maxTurns** - Maximum loop iterations, default 10 [VERIFIED]
- **signal** - AbortSignal for cancellation [VERIFIED]
- **session** - Session for persistent memory [VERIFIED]
- **sessionInputCallback** - Callback for session input [VERIFIED]
- **callModelInputFilter** - Filter model input [VERIFIED]
- **toolErrorFormatter** - Format tool errors [VERIFIED]
- **tracing** - Tracing configuration [VERIFIED]
- **errorHandlers** - Custom error handlers [VERIFIED]
- **conversationId** - Conversation identifier [VERIFIED]
- **previousResponseId** - Previous response for continuation [VERIFIED]

## Run Config

Configuration for Runner instance: [VERIFIED]

- **model** - `string | Model`
- **modelProvider** - `ModelProvider`
- **modelSettings** - `ModelSettings`
- **handoffInputFilter** - `HandoffInputFilter`
- **inputGuardrails** - `InputGuardrail[]`
- **outputGuardrails** - `OutputGuardrail[]`
- **tracingDisabled** - `boolean`
- **traceIncludeSensitiveData** - `boolean`
- **workflowName** - `string`
- **traceId** - Trace identifier
- **groupId** - `string`
- **traceMetadata** - `Record<string, string>`

## Streaming

Enable streaming for real-time events: [VERIFIED]

```typescript
const result = await run(agent, input, { stream: true });

for await (const event of result) {
  console.log(event);
}

// After streaming completes
console.log(result.finalOutput);
```

See: `_INFO_OASDKT-IN08_STREAMING.md` [OASDKT-IN08]

## Conversations / Chat Threads

Manage multi-turn conversations by carrying over history: [VERIFIED]

```typescript
import { Agent, run } from '@openai/agents';
import type { AgentInputItem } from '@openai/agents';

let thread: AgentInputItem[] = [];

const agent = new Agent({
  name: 'Assistant',
});

async function userSays(text: string) {
  const result = await run(
    agent,
    thread.concat({ role: 'user', content: text }),
  );
  thread = result.history; // Carry over history + new items
  return result.finalOutput;
}

await userSays('What city is the Golden Gate Bridge in?');
// -> "San Francisco"

await userSays('What state is it in?');
// -> "California"
```

## Limitations and Known Issues

- maxTurns default is 10, may need increase for complex workflows [VERIFIED]
- MaxTurnsExceededError thrown when limit reached [VERIFIED]

## Gotchas and Quirks

- run() uses singleton Runner, create own for custom config [VERIFIED]
- Input can be string OR array, not both [VERIFIED]
- result.history includes all generated items, not just final [VERIFIED]

## Best Practices

- Create Runner once at app start, reuse across requests [VERIFIED]
- Use run() utility for simple scripts [VERIFIED]
- Carry over result.history for multi-turn conversations [VERIFIED]
- Set appropriate maxTurns for complex workflows [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN07_RESULTS.md` [OASDKT-IN07] - Run results
- `_INFO_OASDKT-IN08_STREAMING.md` [OASDKT-IN08] - Streaming responses
- `_INFO_OASDKT-IN15_SESSIONS.md` [OASDKT-IN15] - Persistent sessions
- `_INFO_OASDKT-IN17_HUMANINLOOP.md` [OASDKT-IN17] - Human-in-the-loop

## API Reference

### Classes

- **Runner**
  - Import: `import { Runner } from "@openai/agents"`
  - Constructor: `new Runner(config?: RunConfig)`
  - Methods: `run(agent, input, options?)`

### Functions

- **run()**
  - Import: `import { run } from "@openai/agents"`
  - Parameters: `(agent, input, options?)`
  - Returns: `Promise<RunResult>` or `Promise<StreamedRunResult>` if streaming

### Types

- **RunResult**
  - Properties: `finalOutput`, `history`, `finalAgent`

- **AgentInputItem**
  - Import: `import type { AgentInputItem } from "@openai/agents"`

### Exceptions

- **MaxTurnsExceededError**
  - Thrown when maxTurns limit reached

## Document History

**[2026-02-11 19:30]**
- Initial document created
- Agent loop, run options, and conversation management documented
