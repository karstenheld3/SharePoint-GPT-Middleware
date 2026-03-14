# INFO: Handoffs

**Doc ID**: OASDKT-IN12
**Goal**: Delegate tasks from one agent to another
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-DOCS-HANDOFFS` - Handoffs documentation page

## Summary

Handoffs let an agent delegate part of a conversation to another agent, useful when different agents specialize in specific areas. In a customer support app, you might have agents handling bookings, refunds, or FAQs. Handoffs are represented as tools to the LLM - if you hand off to an agent called "Refund Agent", the tool name would be `transfer_to_refund_agent`. Every agent accepts a `handoffs` option containing Agent instances or Handoff objects from the `handoff()` helper. When using handoffs, use `Agent.create()` instead of `new Agent()` for proper TypeScript type inference on the final output.

## Creating a Handoff

### Basic Usage

Pass Agent instances directly to the `handoffs` array: [VERIFIED]

```typescript
import { Agent } from '@openai/agents';

const bookingAgent = new Agent({
  name: 'Booking Agent',
  instructions: 'Help users with booking requests.',
  handoffDescription: 'Use for booking-related questions',
});

const refundAgent = new Agent({
  name: 'Refund Agent',
  instructions: 'Process refund requests politely.',
  handoffDescription: 'Use for refund-related questions',
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

### Handoff Description

If you pass plain Agent instances, their `handoffDescription` (if provided) is appended to the default tool description. Use it to clarify when the model should pick that handoff. [VERIFIED]

### Customizing Handoffs via handoff()

Use the `handoff()` helper for more control: [VERIFIED]

```typescript
import { Agent, handoff } from '@openai/agents';

const specialistAgent = new Agent({
  name: 'Specialist',
  instructions: 'Handle specialized queries.',
});

const customHandoff = handoff(specialistAgent, {
  toolName: 'transfer_to_specialist',
  toolDescription: 'Transfer when user needs specialized help',
  // Additional options...
});

const mainAgent = Agent.create({
  name: 'Main Agent',
  instructions: 'Help users and transfer when needed.',
  handoffs: [customHandoff],
});
```

## Handoff Mechanics

### How Handoffs Work

1. Handoffs are exposed as tools to the LLM [VERIFIED]
2. Tool name format: `transfer_to_[agent_name]` [VERIFIED]
3. When handoff is triggered, conversation transfers to target agent
4. Target agent owns conversation until it produces final output [VERIFIED]

### Agent Loop Behavior

When a handoff occurs in the agent loop:
1. Current agent decides to hand off
2. Runner switches to new agent
3. Conversation history is preserved
4. New agent continues until final output [VERIFIED]

## Handoff Inputs

Handoffs can pass structured input to the target agent. [VERIFIED]

## Input Filters

Filter or transform conversation history before passing to handoff target. [VERIFIED]

## Recommended Prompts

Include clear handoff instructions in agent prompts: [VERIFIED]

```typescript
const triageAgent = Agent.create({
  name: 'Triage Agent',
  instructions: `You are a customer service triage agent.
- For booking questions: hand off to the booking agent
- For refund requests: hand off to the refund agent
- For general questions: answer directly`,
  handoffs: [bookingAgent, refundAgent],
});
```

## Agent.create() vs new Agent()

Use `Agent.create()` when using handoffs to ensure proper TypeScript type inference for `finalOutput`. [VERIFIED]

```typescript
// Correct - typed output includes handoff possibilities
const agent = Agent.create({
  name: 'Triage',
  handoffs: [bookingAgent, refundAgent],
});

// Less safe - handoff types not properly inferred
const agent2 = new Agent({
  name: 'Triage',
  handoffs: [bookingAgent, refundAgent],
});
```

## Limitations and Known Issues

- Handoff target must be another Agent instance [VERIFIED]
- Once handoff occurs, original agent loses control [VERIFIED]

## Gotchas and Quirks

- Tool name auto-generated: `transfer_to_[name_snake_case]` [VERIFIED]
- Use `Agent.create()` for proper TypeScript inference [VERIFIED]
- `handoffDescription` helps LLM choose correct handoff [VERIFIED]

## Best Practices

- Provide clear `handoffDescription` for each handoff target [VERIFIED]
- Include handoff instructions in triage agent prompts [VERIFIED]
- Use `Agent.create()` for type-safe handoff outputs [VERIFIED]
- Keep handoff targets focused on specific domains [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN04_AGENTS.md` [OASDKT-IN04] - Agent configuration
- `_INFO_OASDKT-IN13_MULTIAGENT.md` [OASDKT-IN13] - Multi-agent orchestration
- `_INFO_OASDKT-IN10_TOOLS_AGENTSASTOOLS.md` [OASDKT-IN10] - Agents as tools (alternative pattern)

## API Reference

### Functions

- **handoff()**
  - Import: `import { handoff } from "@openai/agents"`
  - Parameters: `(agent, options?)`
  - Returns: `Handoff` object

### Agent Options

- **handoffs** - `Agent[] | Handoff[]`
- **handoffDescription** - Description for handoff tool

### Static Methods

- **Agent.create()**
  - Use for typed handoff outputs

## Document History

**[2026-02-11 19:45]**
- Initial document created
- Handoff mechanics and patterns documented
