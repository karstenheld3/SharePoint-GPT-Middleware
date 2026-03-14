# INFO: Results

**Doc ID**: OASDKT-IN07
**Goal**: Access results and output from agent runs
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-DOCS-RESULTS` - Results documentation

## Summary

When you run an agent, you receive either a `RunResult` (non-streaming) or `StreamedRunResult` (streaming). The `finalOutput` property contains the final output of the last agent that ran - this can be a string (default), unknown (JSON schema output), `z.infer<outputType>` (Zod schema output), or undefined. When using handoffs with different output types, use `Agent.create()` for proper TypeScript type inference - the SDK will provide a union type for finalOutput. The `history` property contains both your input and agent output, useful for maintaining chat threads. The `output` property contains just the agent's output for the current run.

## Result Types

### RunResult

Returned when streaming is disabled (default): [VERIFIED]

```typescript
import { Agent, run } from '@openai/agents';

const result = await run(agent, 'Hello');
console.log(result.finalOutput);
```

### StreamedRunResult

Returned when `stream: true`: [VERIFIED]

```typescript
const result = await run(agent, 'Hello', { stream: true });
// result implements AsyncIterable
```

## Final Output

The `finalOutput` property type depends on agent configuration: [VERIFIED]

- **string** - Default for agents without outputType
- **unknown** - JSON schema output (manual type verification needed)
- **z.infer<outputType>** - Zod schema output (auto-parsed)
- **undefined** - Agent didn't produce output

### Typed Output with Handoffs

Use `Agent.create()` for proper union types with handoffs: [VERIFIED]

```typescript
import { Agent, run } from '@openai/agents';
import { z } from 'zod';

const refundAgent = new Agent({
  name: 'Refund Agent',
  instructions: 'You are a refund agent.',
  outputType: z.object({
    refundApproved: z.boolean(),
  }),
});

const orderAgent = new Agent({
  name: 'Order Agent',
  instructions: 'You are an order agent.',
  outputType: z.object({
    orderId: z.string(),
  }),
});

const triageAgent = Agent.create({
  name: 'Triage Agent',
  instructions: 'You are a triage agent.',
  handoffs: [refundAgent, orderAgent],
});

const result = await run(triageAgent, 'I need a refund');

const output = result.finalOutput;
// Type: { refundApproved: boolean } | { orderId: string } | string | undefined
```

## Inputs for Next Turn

### history

Contains both your input and the output of agents: [VERIFIED]

```typescript
import { Agent, user, run } from '@openai/agents';
import type { AgentInputItem } from '@openai/agents';

const agent = new Agent({
  name: 'Assistant',
  instructions: 'You are a helpful assistant.',
});

let history: AgentInputItem[] = [
  user('Are we there yet?'),
];

for (let i = 0; i < 10; i++) {
  const result = await run(agent, history);
  history = result.history;
  history.push(user('How about now?'));
}
```

### output

Contains just the output of the full agent run. [VERIFIED]

## Other Result Properties

### lastAgent

The agent that produced the final output. [VERIFIED]

### newItems

Items generated during the run. [VERIFIED]

### state

Current run state (for human-in-the-loop). [VERIFIED]

### interruptions

Any interruptions that occurred. [VERIFIED]

### rawResponses

Raw API responses. [VERIFIED]

### lastResponseId

ID of the last API response. [VERIFIED]

### guardrailResults

Results from any guardrails that ran. [VERIFIED]

### usage

Token usage statistics. [VERIFIED]

### originalInput

The original input provided to the run. [VERIFIED]

## Limitations and Known Issues

- finalOutput can be undefined if agent didn't complete [VERIFIED]
- JSON schema outputs require manual type verification [VERIFIED]

## Gotchas and Quirks

- Use `Agent.create()` for typed handoff outputs [VERIFIED]
- `history` includes full conversation, `output` is just agent output [VERIFIED]
- Zod schemas provide automatic type inference [VERIFIED]

## Best Practices

- Use Zod schemas for type-safe outputs [VERIFIED]
- Use `Agent.create()` when working with handoffs [VERIFIED]
- Carry over `result.history` for multi-turn conversations [VERIFIED]
- Check for undefined finalOutput before using [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN05_RUNNER.md` [OASDKT-IN05] - Running agents
- `_INFO_OASDKT-IN08_STREAMING.md` [OASDKT-IN08] - Streaming results
- `_INFO_OASDKT-IN12_HANDOFFS.md` [OASDKT-IN12] - Handoff patterns

## API Reference

### Classes

- **RunResult**
  - Import: `import { RunResult } from "@openai/agents"`
  - Properties: `finalOutput`, `history`, `output`, `lastAgent`, etc.

- **StreamedRunResult**
  - Import: `import { StreamedRunResult } from "@openai/agents"`
  - Implements: `AsyncIterable`

### Types

- **AgentInputItem**
  - Import: `import type { AgentInputItem } from "@openai/agents"`

### Helper Functions

- **user(text)**
  - Creates user message input item

## Document History

**[2026-02-11 20:00]**
- Initial document created
- Result types and properties documented
