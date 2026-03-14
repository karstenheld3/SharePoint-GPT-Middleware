# INFO: Model Context Protocol (MCP)

**Doc ID**: OASDKT-IN11
**Goal**: Integrate MCP servers as tools for agents
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-DOCS-MCP` - MCP documentation

## Summary

The Model Context Protocol (MCP) is an open protocol standardizing how applications provide tools and context to LLMs - think of it like a USB-C port for AI applications. The SDK supports three types of MCP servers: (1) Hosted MCP server tools - remote servers used by the OpenAI Responses API, (2) Streamable HTTP MCP servers - local or remote servers implementing the Streamable HTTP transport, and (3) Stdio MCP servers - servers accessed via standard input/output. Hosted tools push the entire round-trip into the model, while local servers run in your environment. Use `hostedMcpTool()` for hosted servers and `MCPServerStdio` or `MCPServerStreamableHTTP` for local servers.

## MCP Server Types

### 1. Hosted MCP Server Tools

Remote servers used by OpenAI Responses API: [VERIFIED]

```typescript
import { Agent, hostedMcpTool } from '@openai/agents';

export const agent = new Agent({
  name: 'MCP Assistant',
  instructions: 'You must always use the MCP tools to answer questions.',
  tools: [
    hostedMcpTool({
      serverLabel: 'gitmcp',
      serverUrl: 'https://gitmcp.io/openai/codex',
    }),
  ],
});
```

**How it works:** The OpenAI Responses API invokes the remote tool endpoint and streams the result back to the model. [VERIFIED]

### Running Hosted MCP Agents

```typescript
import { run } from '@openai/agents';
import { agent } from './hostedAgent';

async function main() {
  const result = await run(
    agent,
    'Which language is the repo written in?',
  );
  console.log(result.finalOutput);
}

main().catch(console.error);
```

### Streaming with Hosted MCP

```typescript
const result = await run(agent, 'Question?', { stream: true });

for await (const event of result) {
  if (event.type === 'raw_model_stream_event') {
    console.log(event.data);
  }
}
```

### Optional Approval Flow

For sensitive operations, require human approval: [VERIFIED]

```typescript
hostedMcpTool({
  serverLabel: 'sensitive',
  serverUrl: 'https://example.com/mcp',
  requireApproval: 'always', // or fine-grained object
});
```

Use `onApproval` callback for programmatic approval, or HITL approach with interruptions. [VERIFIED]

### 2. Streamable HTTP MCP Servers

Local or remote servers implementing Streamable HTTP transport: [VERIFIED]

```typescript
import { MCPServerStreamableHTTP } from '@openai/agents';

const server = new MCPServerStreamableHTTP({
  url: 'http://localhost:3000/mcp',
});
```

### 3. Stdio MCP Servers

Servers accessed via standard input/output (simplest option): [VERIFIED]

```typescript
import { MCPServerStdio } from '@openai/agents';

const server = new MCPServerStdio({
  command: 'node',
  args: ['path/to/mcp-server.js'],
});
```

## Using Local MCP Servers

Add local MCP servers to agent's `mcpServers` array: [VERIFIED]

```typescript
import { Agent, MCPServerStdio } from '@openai/agents';

const mcpServer = new MCPServerStdio({
  command: 'npx',
  args: ['@modelcontextprotocol/server-filesystem', '/tmp'],
});

const agent = new Agent({
  name: 'File Agent',
  instructions: 'Use the filesystem tools.',
  mcpServers: [mcpServer],
});
```

## Managing MCP Server Lifecycle

### Connecting and Disconnecting

```typescript
await mcpServer.connect();
// ... use server
await mcpServer.close();
```

### Async Disposal (Optional)

Use `using` syntax for automatic cleanup (TypeScript 5.2+): [VERIFIED]

```typescript
await using server = new MCPServerStdio({ command: 'node', args: [...] });
await server.connect();
// Automatically disposed when scope exits
```

## Tool Filtering

Filter which tools from MCP server are exposed to agents. [VERIFIED]

## Legacy SSE Transport

`MCPServerSSE` is available but deprecated. Prefer Streamable HTTP or stdio. [VERIFIED]

## Limitations and Known Issues

- SSE transport deprecated by MCP project [VERIFIED]
- Hosted MCP requires OpenAI Responses API [VERIFIED]
- Local servers require lifecycle management [VERIFIED]

## Gotchas and Quirks

- Use `hostedMcpTool()` for hosted, `mcpServers` array for local [VERIFIED]
- Must connect local servers before use [VERIFIED]
- Hosted tools have approval flow support [VERIFIED]

## Best Practices

- Use hosted MCP for simpler integration [VERIFIED]
- Use stdio for local development [VERIFIED]
- Implement proper lifecycle management for local servers [VERIFIED]
- Use approval flow for sensitive operations [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN09_TOOLS.md` [OASDKT-IN09] - Tools overview
- `_INFO_OASDKT-IN17_HUMANINLOOP.md` [OASDKT-IN17] - Human-in-the-loop

## API Reference

### Functions

- **hostedMcpTool()**
  - Import: `import { hostedMcpTool } from "@openai/agents"`
  - Options: `{ serverLabel, serverUrl, requireApproval?, onApproval? }`

### Classes

- **MCPServerStdio**
  - Import: `import { MCPServerStdio } from "@openai/agents"`
  - Options: `{ command, args }`

- **MCPServerStreamableHTTP**
  - Import: `import { MCPServerStreamableHTTP } from "@openai/agents"`
  - Options: `{ url }`

- **MCPServerSSE** (deprecated)
  - Import: `import { MCPServerSSE } from "@openai/agents"`

## Document History

**[2026-02-11 20:25]**
- Initial document created
- All three MCP server types documented
