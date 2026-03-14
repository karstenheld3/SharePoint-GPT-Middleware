# INFO: Streaming

**Doc ID**: OASDKT-IN08
**Goal**: Stream agent output in real time
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-DOCS-STREAM` - Streaming documentation

## Summary

The Agents SDK delivers output from the model and execution steps incrementally via streaming. Streaming keeps your UI responsive and avoids waiting for the entire final result. Enable streaming by passing `{ stream: true }` to `run()`. The returned stream implements AsyncIterable - each yielded event describes what happened. Three event types exist: `raw_model_stream_event` (model events), `agent_updated_stream_event` (agent switches), and `run_item_stream_event` (SDK-specific events). For just text output, use `stream.toTextStream()` which can produce a Node.js Readable stream. Always await `stream.completed` to ensure all output is finished.

## Enabling Streaming

Pass `{ stream: true }` to `run()`: [VERIFIED]

```typescript
import { Agent, run } from '@openai/agents';

const agent = new Agent({
  name: 'Storyteller',
  instructions: 'You are a storyteller.',
});

const result = await run(agent, 'Tell me a story about a cat.', {
  stream: true,
});
```

The returned stream implements `AsyncIterable`. [VERIFIED]

## Getting Text Output

Use `toTextStream()` for just the text: [VERIFIED]

```typescript
import { Agent, run } from '@openai/agents';

const agent = new Agent({
  name: 'Storyteller',
  instructions: 'You are a storyteller.',
});

const result = await run(agent, 'Tell me a story about a cat.', {
  stream: true,
});

result
  .toTextStream({ compatibleWithNodeStreams: true })
  .pipe(process.stdout);
```

### toTextStream Options

- **compatibleWithNodeStreams** - When `true`, returns Node.js `Readable` [VERIFIED]

### Waiting for Completion

Always await `stream.completed` to ensure no more output: [VERIFIED]

```typescript
await result.completed;
```

## Listening to All Events

Use `for await` loop to inspect each event: [VERIFIED]

```typescript
import { Agent, run } from '@openai/agents';

const agent = new Agent({
  name: 'Storyteller',
  instructions: 'You are a storyteller.',
});

const result = await run(agent, 'Tell me a story about a cat.', {
  stream: true,
});

for await (const event of result) {
  // Raw events from the model
  if (event.type === 'raw_model_stream_event') {
    console.log(`${event.type}`, event.data);
  }

  // Agent updated events
  if (event.type === 'agent_updated_stream_event') {
    console.log(`${event.type}`, event.agent.name);
  }

  // SDK-specific events
  if (event.type === 'run_item_stream_event') {
    console.log(`${event.type}`, event.item);
  }
}
```

## Event Types

### raw_model_stream_event

Low-level events directly from the model. [VERIFIED]

- **data** - The raw event data from OpenAI API

### agent_updated_stream_event

Emitted when the active agent changes. [VERIFIED]

- **agent** - The new active agent

### run_item_stream_event

SDK-specific run information. [VERIFIED]

- **item** - The run item produced

## Human in the Loop While Streaming

Streaming works with human-in-the-loop patterns. [VERIFIED]

See: `_INFO_OASDKT-IN17_HUMANINLOOP.md` [OASDKT-IN17]

## Tips

- Use `toTextStream()` for simple text output scenarios [VERIFIED]
- Use `for await` when you need to process all event types [VERIFIED]
- Always await `completed` before assuming run is finished [VERIFIED]

## Limitations and Known Issues

- Streaming returns StreamedRunResult, not RunResult [VERIFIED]
- Must await `completed` to ensure all output processed [VERIFIED]

## Gotchas and Quirks

- Stream is AsyncIterable, not a Node.js Stream by default [VERIFIED]
- Use `compatibleWithNodeStreams: true` for Node.js pipe compatibility [VERIFIED]
- `finalOutput` is available after streaming completes [VERIFIED]

## Best Practices

- Use streaming for interactive UIs [VERIFIED]
- Pipe `toTextStream()` to stdout for CLI tools [VERIFIED]
- Process events as they arrive for responsive feedback [VERIFIED]
- Always await `completed` before accessing final results [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN05_RUNNER.md` [OASDKT-IN05] - Running agents
- `_INFO_OASDKT-IN07_RESULTS.md` [OASDKT-IN07] - Run results

## API Reference

### Methods

- **toTextStream(options?)**
  - Returns text stream
  - Options: `{ compatibleWithNodeStreams?: boolean }`

### Properties

- **completed** - Promise that resolves when run finishes

### Event Types

- **raw_model_stream_event** - Model events
- **agent_updated_stream_event** - Agent changes
- **run_item_stream_event** - SDK events

## Document History

**[2026-02-11 20:05]**
- Initial document created
- Streaming patterns and events documented
