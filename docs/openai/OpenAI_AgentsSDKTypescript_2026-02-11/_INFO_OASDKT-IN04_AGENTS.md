# INFO: Agents

**Doc ID**: OASDKT-IN04
**Goal**: Define and configure agents in the SDK
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-DOCS-AGENTS` - Agents documentation page

## Summary

Agents are the main building block of the OpenAI Agents SDK. An Agent is an LLM configured with instructions (system prompt), model selection, and tools. The Agent class is generic on context type (Agent<TContext, TOutput>) for dependency injection. Agents support dynamic instructions via functions, lifecycle hooks for observability, guardrails for validation, and cloning for creating variants. Two multi-agent patterns are common: Manager (agents as tools) where a central agent orchestrates specialists, and Handoffs where control transfers completely to specialists. The Agent.create() method should be used instead of new Agent() when working with handoffs for proper TypeScript typing.

## Basic Configuration

### Agent Constructor

```typescript
import { Agent } from '@openai/agents';

const agent = new Agent({
  name: 'Haiku Agent',
  instructions: 'Always respond in haiku form.',
  model: 'gpt-5-nano', // optional - falls back to default
});
```

### Configuration Properties

- **name** - Agent identifier [VERIFIED]
- **instructions** - System prompt (string or function) [VERIFIED]
- **prompt** - Additional prompt configuration [VERIFIED]
- **handoffDescription** - Description for handoff purposes [VERIFIED]
- **model** - Model name or Model instance [VERIFIED]
- **modelSettings** - Model-specific settings [VERIFIED]
- **providerData** - Provider-specific data [VERIFIED]
- **tools** - Array of Tool definitions [VERIFIED]
- **mcpServers** - MCP server configurations [VERIFIED]
- **resetToolChoice** - Reset tool choice after use [VERIFIED]
- **toolChoice** - Tool selection strategy [VERIFIED]
- **handoffOutputTypeWarningEnabled** - Enable handoff type warnings (default: true) [VERIFIED]

### Agent with Tools

```typescript
import { Agent, tool } from '@openai/agents';
import { z } from 'zod';

const getWeather = tool({
  name: 'get_weather',
  description: 'Return the weather for a given city.',
  parameters: z.object({ city: z.string() }),
  async execute({ city }) {
    return `The weather in ${city} is sunny.`;
  },
});

const agent = new Agent({
  name: 'Weather bot',
  instructions: 'You are a helpful weather bot.',
  model: 'gpt-4.1',
  tools: [getWeather],
});
```

## Context

### Typed Context

Agents are generic on context type: `Agent<TContext, TOutput>` [VERIFIED]

```typescript
import { Agent } from '@openai/agents';

interface Purchase {
  id: string;
  uid: string;
  deliveryStatus: string;
}

interface UserContext {
  uid: string;
  isProUser: boolean;
  fetchPurchases(): Promise<Purchase[]>;
}

const agent = new Agent<UserContext>({
  name: 'Personal shopper',
  instructions: 'Recommend products the user will love.',
});
```

### Passing Context to Run

```typescript
import { run } from '@openai/agents';

const result = await run(agent, 'Find me a new pair of running shoes', {
  context: {
    uid: 'abc',
    isProUser: true,
    fetchPurchases: async () => [],
  },
});
```

## Output Types

### Structured Output with Zod

```typescript
import { Agent } from '@openai/agents';
import { z } from 'zod';

const CalendarEvent = z.object({
  name: z.string(),
  date: z.string(),
  participants: z.array(z.string()),
});

const extractor = new Agent({
  name: 'Calendar extractor',
  instructions: 'Extract calendar events from the supplied text.',
  outputType: CalendarEvent,
});
```

When `outputType` is provided, the SDK uses structured outputs instead of plain text. [VERIFIED]

## Multi-Agent Patterns

### Manager (Agents as Tools)

Central agent orchestrates specialists as tools:

```typescript
import { Agent } from '@openai/agents';

const bookingAgent = new Agent({
  name: 'Booking expert',
  instructions: 'Answer booking questions and modify reservations.',
});

const refundAgent = new Agent({
  name: 'Refund expert',
  instructions: 'Help customers process refunds and credits.',
});

const customerFacingAgent = new Agent({
  name: 'Customer-facing agent',
  instructions: 'Talk to the user directly. When they need booking or refund help, call the matching tool.',
  tools: [
    bookingAgent.asTool({
      toolName: 'booking_expert',
      toolDescription: 'Handles booking questions and requests.',
    }),
    refundAgent.asTool({
      toolName: 'refund_expert',
      toolDescription: 'Handles refund questions and requests.',
    }),
  ],
});
```

### Handoffs

Triage agent routes, specialist owns conversation:

```typescript
import { Agent } from '@openai/agents';

const bookingAgent = new Agent({
  name: 'Booking Agent',
  instructions: 'Help users with booking requests.',
});

const refundAgent = new Agent({
  name: 'Refund Agent',
  instructions: 'Process refund requests politely and efficiently.',
});

// Use Agent.create for typed handoff outputs
const triageAgent = Agent.create({
  name: 'Triage Agent',
  instructions: `Help the user with their questions.
If the user asks about booking, hand off to the booking agent.
If the user asks about refunds, hand off to the refund agent.`,
  handoffs: [bookingAgent, refundAgent],
});
```

## Dynamic Instructions

Instructions can be a function receiving RunContext: [VERIFIED]

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

Both sync and async functions are supported. [VERIFIED]

## Lifecycle Hooks

```typescript
import { Agent } from '@openai/agents';

const agent = new Agent({
  name: 'Verbose agent',
  instructions: 'Explain things thoroughly.',
});

agent.on('agent_start', (ctx, agent) => {
  console.log(`[${agent.name}] started`);
});

agent.on('agent_end', (ctx, output) => {
  console.log(`[agent] produced:`, output);
});
```

## Cloning Agents

```typescript
import { Agent } from '@openai/agents';

const pirateAgent = new Agent({
  name: 'Pirate',
  instructions: 'Respond like a pirate - lots of "Arrr!"',
  model: 'gpt-5-mini',
});

const robotAgent = pirateAgent.clone({
  name: 'Robot',
  instructions: 'Respond like a robot - be precise and factual.',
});
```

## Guardrails

Configure via `inputGuardrails` and `outputGuardrails` arrays. [VERIFIED]

See: `_INFO_OASDKT-IN14_GUARDRAILS.md` [OASDKT-IN14]

## Limitations and Known Issues

- Handoff type inference requires `Agent.create()` not `new Agent()` [VERIFIED]

## Gotchas and Quirks

- Use `Agent.create()` for typed handoff outputs [VERIFIED]
- Dynamic instructions receive RunContext, not raw context [VERIFIED]
- Lifecycle events are instance-based, not global [VERIFIED]

## Best Practices

- Use typed context for dependency injection [VERIFIED]
- Use `Agent.create()` when using handoffs [VERIFIED]
- Keep instructions focused per agent [VERIFIED]
- Use lifecycle hooks for observability [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN09_TOOLS.md` [OASDKT-IN09] - Tool definitions
- `_INFO_OASDKT-IN12_HANDOFFS.md` [OASDKT-IN12] - Handoff patterns
- `_INFO_OASDKT-IN14_GUARDRAILS.md` [OASDKT-IN14] - Input/output validation

## API Reference

### Classes

- **Agent**
  - Import: `import { Agent } from "@openai/agents"`
  - Constructor: `new Agent<TContext, TOutput>(config)`
  - Static: `Agent.create(config)` for typed handoffs
  - Methods: `clone(overrides)`, `asTool(options)`, `on(event, handler)`

### Types

- **RunContext<T>**
  - Import: `import { RunContext } from "@openai/agents"`
  - Properties: `context` (T), agent, runner info

## Document History

**[2026-02-11 19:25]**
- Initial document created
- All agent configuration options documented
- Multi-agent patterns included
