# INFO: Introduction to OpenAI Agents SDK TypeScript

**Doc ID**: OASDKT-IN01
**Goal**: Provide SDK overview, design principles, installation, and hello world example
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-DOCS-HOME` - Main documentation homepage
- `OASDKT-SC-NPM-AGENTS` - npm package info
- `OASDKT-SC-GH-MAIN` - GitHub repository README

## Summary

The OpenAI Agents SDK for TypeScript is a lightweight, production-ready framework for building multi-agent AI applications in JavaScript and TypeScript environments. It evolved from the experimental Swarm project and is designed with two key principles: providing enough features to be worth using while keeping primitives minimal for quick learning, and working great out of the box while allowing deep customization. The SDK offers three core primitives: Agents (LLMs with instructions and tools), Handoffs (agent-to-agent delegation), and Guardrails (input/output validation). It uses Zod v4 for schema validation instead of Pydantic, leverages native async/await patterns, and runs on Node.js 22+, Deno, or Bun. The package is available on npm as `@openai/agents` with 338K weekly downloads. Built-in tracing enables visualization, debugging, evaluation, and fine-tuning of agent workflows through the OpenAI platform.

## Overview

### What is the Agents SDK?

The OpenAI Agents SDK for TypeScript enables building agentic AI applications with minimal abstractions. [VERIFIED]

**Core Primitives:**
- **Agents** - LLMs equipped with instructions and tools
- **Handoffs** - Allow agents to delegate to other agents for specific tasks
- **Guardrails** - Enable input validation for agents

### Design Principles

1. **Enough features to be worth using, but few enough primitives to make it quick to learn** [VERIFIED]
2. **Works great out of the box, but you can customize exactly what happens** [VERIFIED]

### Key Features

- **Agent loop** - Built-in loop handles tool invocation, sends results to LLM, continues until task complete [VERIFIED]
- **TypeScript-first** - Orchestrate agents using native TypeScript features without new abstractions [VERIFIED]
- **Agents as tools / Handoffs** - Coordinate and delegate work across multiple agents [VERIFIED]
- **Guardrails** - Run input validation in parallel with agent execution, fail fast on check failure [VERIFIED]
- **Function tools** - Turn any TypeScript function into a tool with automatic schema generation and Zod validation [VERIFIED]
- **MCP server tool calling** - Built-in Model Context Protocol server integration [VERIFIED]
- **Sessions** - Persistent memory layer for maintaining context within agent loop [VERIFIED]
- **Human in the loop** - Built-in mechanisms for involving humans across agent runs [VERIFIED]
- **Tracing** - Built-in tracing for visualizing, debugging, and monitoring workflows [VERIFIED]
- **Realtime Agents** - Build voice agents with interruption detection, context management, guardrails [VERIFIED]

## Installation

### Requirements

- **Node.js 22+** (or Deno, Bun) [VERIFIED]
- **Zod v4** - Required for schema validation [VERIFIED]

### Install Command

```bash
npm install @openai/agents zod
```

### Environment Setup

Set your OpenAI API key:

```bash
export OPENAI_API_KEY=sk-...
```

## Hello World Example

### Basic Usage

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

### Voice Agent Example

```typescript
import { RealtimeAgent, RealtimeSession } from '@openai/agents/realtime';

const agent = new RealtimeAgent({
  name: 'Assistant',
  instructions: 'You are a helpful assistant.',
});

// Automatically connects microphone and audio output in browser via WebRTC
const session = new RealtimeSession(agent);
await session.connect({
  apiKey: '<client-api-key>',
});
```

## Package Architecture

The SDK is split into multiple packages: [VERIFIED]

- **@openai/agents** - Main package, re-exports from core
- **@openai/agents-core** - Core agent functionality
- **@openai/agents-openai** - OpenAI-specific implementations
- **@openai/agents-realtime** - Realtime/voice agent support
- **@openai/agents-extensions** - Third-party integrations

## Supported Environments

- **Node.js 22+** [VERIFIED]
- **Deno** [VERIFIED]
- **Bun** [VERIFIED]
- **Cloudflare Workers** (experimental, with `nodejs_compat` enabled) [VERIFIED]

## Limitations and Known Issues

- Requires Node.js 22 or later - older Node.js versions not supported [VERIFIED]
- Zod v4 is required - Zod v3 not compatible [VERIFIED]
- Browser support limited to realtime agents package [VERIFIED]

## Gotchas and Quirks

- Must install `zod` as a peer dependency separately [VERIFIED]
- Voice agents require separate import from `@openai/agents/realtime` [VERIFIED]
- `Agent.create()` method needed for typed handoff outputs instead of `new Agent()` [VERIFIED]

## Best Practices

- Set `OPENAI_API_KEY` environment variable rather than hardcoding [VERIFIED]
- Use `Agent.create()` when working with handoffs for proper TypeScript typing [VERIFIED]
- Enable tracing for debugging - traces appear in OpenAI Dashboard [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN02_QUICKSTART.md` [OASDKT-IN02] - Step-by-step quickstart guide
- `_INFO_OASDKT-IN04_AGENTS.md` [OASDKT-IN04] - Agent configuration in detail

## API Reference

### Classes

- **Agent**
  - Import: `import { Agent } from "@openai/agents"`
  - Purpose: Define an agent with name, instructions, tools, handoffs
  - Key methods: `Agent.create()` for typed handoffs

- **RealtimeAgent**
  - Import: `import { RealtimeAgent } from "@openai/agents/realtime"`
  - Purpose: Define a voice/realtime agent

- **RealtimeSession**
  - Import: `import { RealtimeSession } from "@openai/agents/realtime"`
  - Purpose: Manage realtime agent connection

### Functions

- **run()**
  - Import: `import { run } from "@openai/agents"`
  - Parameters: `(agent: Agent, input: string, options?: RunOptions)`
  - Returns: `Promise<RunResult>` - Contains finalOutput and execution details

## Verification Labels

- `[VERIFIED]` - Confirmed against official documentation
- `[CODE-VERIFIED]` - Tested with actual code execution
- `[INFERRED]` - Logical inference from verified information
- `[UNVERIFIED]` - Needs verification

## Document History

**[2026-02-11 19:05]**
- Initial document created
- All core features documented from official sources
- Installation and hello world examples included
