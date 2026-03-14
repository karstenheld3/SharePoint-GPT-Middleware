# INFO: Building Voice Agents

**Doc ID**: OASDKT-IN20
**Goal**: Advanced patterns for building voice agents
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-VOICE-BUILD` - Voice agents build guide

## Summary

Building production voice agents involves configuring RealtimeAgent with tools, handoffs, and guardrails similar to text agents. Voice agents support the same tool patterns, multi-agent handoffs, and lifecycle callbacks. Key considerations include audio handling, interruption management, and transport layer selection (WebRTC for browsers, WebSocket for backends).

## RealtimeAgent Configuration

```typescript
import { RealtimeAgent } from '@openai/agents/realtime';
import { z } from 'zod';

const agent = new RealtimeAgent({
  name: 'Customer Support',
  instructions: 'Help customers with their inquiries.',
  model: 'gpt-realtime',
  tools: [orderLookupTool, accountInfoTool],
  handoffs: [billingAgent, technicalAgent],
});
```

## Adding Tools to Voice Agents

Voice agents support the same tool patterns as text agents:

```typescript
import { tool } from '@openai/agents';
import { z } from 'zod';

const lookupOrder = tool({
  name: 'lookup_order',
  description: 'Look up order status',
  parameters: z.object({
    orderId: z.string(),
  }),
  execute: async ({ orderId }) => {
    return `Order ${orderId} is in transit`;
  },
});

const agent = new RealtimeAgent({
  name: 'Order Agent',
  instructions: 'Help with order inquiries.',
  tools: [lookupOrder],
});
```

## Voice Agent Handoffs

Multi-agent orchestration via handoffs:

```typescript
import { RealtimeAgent } from '@openai/agents/realtime';

const billingAgent = new RealtimeAgent({
  name: 'Billing',
  instructions: 'Handle billing questions.',
});

const supportAgent = new RealtimeAgent({
  name: 'Support',
  instructions: 'Route to billing for payment issues.',
  handoffs: [billingAgent],
});
```

## Session Events and Callbacks

```typescript
const session = new RealtimeSession(agent);

session.on('audio_started', () => {
  console.log('User started speaking');
});

session.on('audio_ended', () => {
  console.log('User stopped speaking');
});

session.on('response_started', () => {
  console.log('Agent is responding');
});
```

## Audio Configuration

Configure audio input/output settings:

```typescript
const session = new RealtimeSession(agent, {
  audioConfig: {
    inputSampleRate: 16000,
    outputSampleRate: 24000,
  },
});
```

## Interruption Handling

Voice agents support interruption - user can interrupt agent mid-response. Session handles this automatically.

## Guardrails for Voice

Apply guardrails to voice agent responses:

```typescript
const agent = new RealtimeAgent({
  name: 'Safe Agent',
  instructions: 'Be helpful and appropriate.',
  outputGuardrails: [contentFilter],
});
```

## Best Practices

- Use clear, conversational instructions
- Keep tool responses concise for voice
- Test interruption handling thoroughly
- Consider latency in tool execution

## Related Topics

- `_INFO_OASDKT-IN18_VOICE_OVERVIEW.md` [OASDKT-IN18] - Voice overview
- `_INFO_OASDKT-IN21_VOICE_TRANSPORT.md` [OASDKT-IN21] - Transport layers

## Document History

**[2026-02-11 21:10]**
- Initial document created
- Voice agent building patterns documented
