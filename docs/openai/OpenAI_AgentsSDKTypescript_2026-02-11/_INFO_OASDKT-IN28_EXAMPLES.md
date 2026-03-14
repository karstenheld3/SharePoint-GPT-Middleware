# INFO: Examples

**Doc ID**: OASDKT-IN28
**Goal**: Reference examples and patterns from the SDK repository
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-GH-EXAMPLES` - GitHub examples directory

## Summary

The SDK repository includes extensive examples demonstrating various patterns and use cases. Examples are organized into categories: basic usage, agent patterns, memory/sessions, MCP integration, voice agents, and extensions. The examples directory provides working code that can be run directly or adapted for production use.

## Example Categories

### Basic Examples

Located in `examples/basic/`:

- **hello-world.ts** - Minimal agent setup
- **chat.ts** - Interactive chat loop
- **tools.ts** - Function tool definition
- **structured-output.ts** - Zod schema outputs
- **streaming.ts** - Streaming responses

### Agent Patterns

Located in `examples/agent-patterns/`:

- **handoffs.ts** - Multi-agent handoff example
- **agents-as-tools.ts** - Using agents as tools
- **parallelization.ts** - Parallel agent execution
- **chaining.ts** - Sequential agent chaining
- **feedback-loop.ts** - Evaluation and improvement loop

### Memory/Sessions

Located in `examples/memory/`:

- **conversations-session.ts** - OpenAI Conversations API
- **memory-session.ts** - In-memory session
- **prisma-session.ts** - Database-backed session
- **file-session.ts** - File-based persistence

### MCP Integration

Located in `examples/mcp/`:

- **hosted-mcp.ts** - Hosted MCP server
- **stdio-mcp.ts** - Local stdio MCP server
- **streamable-http.ts** - HTTP MCP server

### Voice Agents

Located in `examples/voice/`:

- **browser-quickstart/** - Browser voice agent
- **node-websocket/** - Node.js WebSocket voice
- **with-tools/** - Voice agent with tools
- **with-handoffs/** - Voice agent handoffs

### Extensions

Located in `examples/extensions/`:

- **ai-sdk/** - Vercel AI SDK integration
- **twilio/** - Twilio voice integration
- **cloudflare/** - Cloudflare Workers

## Running Examples

```bash
# Clone repository
git clone https://github.com/openai/openai-agents-js.git
cd openai-agents-js

# Install dependencies
npm install

# Set API key
export OPENAI_API_KEY=sk-...

# Run example
npx tsx examples/basic/hello-world.ts
```

## Key Patterns Demonstrated

### Hello World

```typescript
import { Agent, run } from '@openai/agents';

const agent = new Agent({
  name: 'Assistant',
  instructions: 'You are a helpful assistant.',
});

const result = await run(agent, 'Hello!');
console.log(result.finalOutput);
```

### Multi-Agent Handoff

```typescript
import { Agent } from '@openai/agents';

const specialist = new Agent({
  name: 'Specialist',
  instructions: 'Handle specialized queries.',
});

const triage = Agent.create({
  name: 'Triage',
  instructions: 'Route to specialist when needed.',
  handoffs: [specialist],
});
```

### Streaming

```typescript
import { Agent, run } from '@openai/agents';

const result = await run(agent, input, { stream: true });

for await (const event of result) {
  if (event.type === 'raw_model_stream_event') {
    process.stdout.write(event.data.delta || '');
  }
}
```

## Limitations and Known Issues

- Examples may require specific environment setup [VERIFIED]
- Some examples need additional dependencies [VERIFIED]

## Best Practices

- Start with basic examples before complex patterns [VERIFIED]
- Adapt examples for your use case [VERIFIED]
- Check example README for specific requirements [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN02_QUICKSTART.md` [OASDKT-IN02] - SDK quickstart
- `_INFO_OASDKT-IN13_MULTIAGENT.md` [OASDKT-IN13] - Multi-agent patterns

## Repository Links

- **Examples**: https://github.com/openai/openai-agents-js/tree/main/examples
- **Basic**: https://github.com/openai/openai-agents-js/tree/main/examples/basic
- **Agent Patterns**: https://github.com/openai/openai-agents-js/tree/main/examples/agent-patterns

## Document History

**[2026-02-11 21:05]**
- Initial document created
- Example categories and patterns documented
