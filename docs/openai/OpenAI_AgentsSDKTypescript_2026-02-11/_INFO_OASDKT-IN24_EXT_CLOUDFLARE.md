# INFO: Cloudflare Workers Extension

**Doc ID**: OASDKT-IN24
**Goal**: Deploy agents on Cloudflare Workers
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-EXT-CFLARE` - Cloudflare extension documentation

## Summary

The Cloudflare Workers extension enables deploying agents on Cloudflare's edge network. This is experimental and provides low-latency agent execution at the edge. The extension adapts the SDK for Cloudflare Workers' runtime environment.

## Status

**Experimental** - Cloudflare Workers support is under active development.

## Installation

```bash
npm install @openai/agents
```

## Basic Usage

```typescript
import { Agent, run } from '@openai/agents';

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const agent = new Agent({
      name: 'Edge Agent',
      instructions: 'You are a helpful assistant.',
    });

    const body = await request.json();
    const result = await run(agent, body.message);

    return new Response(JSON.stringify({
      response: result.finalOutput,
    }), {
      headers: { 'Content-Type': 'application/json' },
    });
  },
};
```

## Environment Variables

Configure via wrangler.toml:

```toml
[vars]
OPENAI_API_KEY = "sk-..."
```

Or use secrets:

```bash
wrangler secret put OPENAI_API_KEY
```

## Considerations

### Supported Features

- Basic agent execution
- Tool calling
- Streaming responses

### Limitations

- Some features may not work in edge environment
- Memory constraints of Workers runtime
- Cold start considerations

## Durable Objects Integration

For stateful agents, use Durable Objects:

```typescript
export class AgentSession {
  private agent: Agent;

  constructor(state: DurableObjectState, env: Env) {
    this.agent = new Agent({
      name: 'Stateful Agent',
      instructions: 'You remember conversation history.',
    });
  }

  async fetch(request: Request): Promise<Response> {
    // Handle session-based conversations
  }
}
```

## Best Practices

- Test thoroughly in Workers environment
- Handle timeouts gracefully
- Use streaming for long responses
- Monitor execution time limits

## Related Topics

- `_INFO_OASDKT-IN25_CONFIG.md` [OASDKT-IN25] - SDK configuration

## Document History

**[2026-02-11 21:30]**
- Initial document created
- Cloudflare Workers integration documented
