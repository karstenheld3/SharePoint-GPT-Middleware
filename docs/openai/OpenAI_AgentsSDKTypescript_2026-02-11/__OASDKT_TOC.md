# OpenAI Agents SDK TypeScript - Table of Contents

**Doc ID**: OASDKT-TOC
**Goal**: Master index for OpenAI Agents SDK TypeScript documentation (MCPI)
**Version**: @openai/agents 0.4.6 (2026-02-11)
**Package**: `npm install @openai/agents zod`
**Node.js**: 22+ (also Deno, Bun)
**Repository**: https://github.com/openai/openai-agents-js

## Summary

The OpenAI Agents SDK for TypeScript is a lightweight, production-ready framework for building multi-agent AI applications in JavaScript and TypeScript. It evolved from the experimental Swarm project and provides a minimal set of primitives: Agents (LLMs with instructions and tools), Handoffs (agent-to-agent delegation), and Guardrails (input/output validation). The SDK is TypeScript-first with native async/await patterns, using Zod v4 for schema validation instead of Pydantic. Key features include automatic agent loops, function tools with automatic schema generation, MCP server integration, built-in sessions for conversation memory, human-in-the-loop patterns, comprehensive tracing for debugging and monitoring, and realtime voice agent capabilities via WebRTC or WebSockets. The SDK also supports broader model usage through the Vercel AI SDK adapter and includes extensions for Twilio and Cloudflare Workers.

## Topic Files

### Getting Started (3 files)

- [`_INFO_OASDKT-IN01_INTRODUCTION.md`](./_INFO_OASDKT-IN01_INTRODUCTION.md) [OASDKT-IN01]
  - SDK overview, design principles, installation, hello world
  - Sources: OASDKT-SC-DOCS-HOME, OASDKT-SC-NPM-AGENTS

- [`_INFO_OASDKT-IN02_QUICKSTART.md`](./_INFO_OASDKT-IN02_QUICKSTART.md) [OASDKT-IN02]
  - Environment setup, first agent, basic patterns
  - Sources: OASDKT-SC-DOCS-QUICK

- [`_INFO_OASDKT-IN03_MODELS.md`](./_INFO_OASDKT-IN03_MODELS.md) [OASDKT-IN03]
  - Supported models, model configuration, provider settings
  - Sources: OASDKT-SC-DOCS-MODELS

### Core Concepts (5 files)

- [`_INFO_OASDKT-IN04_AGENTS.md`](./_INFO_OASDKT-IN04_AGENTS.md) [OASDKT-IN04]
  - Agent class, name, instructions, model, tools
  - Agent.create() for typed handoffs, cloning
  - Sources: OASDKT-SC-DOCS-AGENTS

- [`_INFO_OASDKT-IN05_RUNNER.md`](./_INFO_OASDKT-IN05_RUNNER.md) [OASDKT-IN05]
  - run() function, Runner class, agent loop mechanics
  - maxTurns, final output rules
  - Sources: OASDKT-SC-DOCS-RUNNER

- [`_INFO_OASDKT-IN06_CONTEXT.md`](./_INFO_OASDKT-IN06_CONTEXT.md) [OASDKT-IN06]
  - Context management, dependency injection, typed context
  - Sources: OASDKT-SC-DOCS-CONTEXT

- [`_INFO_OASDKT-IN07_RESULTS.md`](./_INFO_OASDKT-IN07_RESULTS.md) [OASDKT-IN07]
  - RunResult, finalOutput, outputType
  - Structured outputs with Zod schemas
  - Sources: OASDKT-SC-DOCS-RESULTS

- [`_INFO_OASDKT-IN08_STREAMING.md`](./_INFO_OASDKT-IN08_STREAMING.md) [OASDKT-IN08]
  - Streaming responses, partial results, event handling
  - Sources: OASDKT-SC-DOCS-STREAM

### Tools (3 files)

- [`_INFO_OASDKT-IN09_TOOLS.md`](./_INFO_OASDKT-IN09_TOOLS.md) [OASDKT-IN09]
  - tool() function, Zod parameters, execute callback
  - Built-in tools: web_search, file_search, code_interpreter
  - Sources: OASDKT-SC-DOCS-TOOLS

- [`_INFO_OASDKT-IN10_TOOLS_AGENTSASTOOLS.md`](./_INFO_OASDKT-IN10_TOOLS_AGENTSASTOOLS.md) [OASDKT-IN10]
  - Using agents as tools for other agents
  - Sources: OASDKT-SC-GH-EXAMPLES

- [`_INFO_OASDKT-IN11_MCP.md`](./_INFO_OASDKT-IN11_MCP.md) [OASDKT-IN11]
  - Model Context Protocol integration
  - Local MCP server support
  - Sources: OASDKT-SC-DOCS-MCP

### Multi-Agent Patterns (2 files)

- [`_INFO_OASDKT-IN12_HANDOFFS.md`](./_INFO_OASDKT-IN12_HANDOFFS.md) [OASDKT-IN12]
  - Handoff concept, handoffDescription
  - Agent.create() for typed handoff outputs
  - Sources: OASDKT-SC-DOCS-HANDOFFS

- [`_INFO_OASDKT-IN13_MULTIAGENT.md`](./_INFO_OASDKT-IN13_MULTIAGENT.md) [OASDKT-IN13]
  - Orchestrating multiple agents
  - Routing, parallelization, deterministic flows
  - Sources: OASDKT-SC-DOCS-MULTI

### Safety and Validation (1 file)

- [`_INFO_OASDKT-IN14_GUARDRAILS.md`](./_INFO_OASDKT-IN14_GUARDRAILS.md) [OASDKT-IN14]
  - Input guardrails, output guardrails
  - Parallel execution, tripwires
  - GuardrailTripwireTriggered exception
  - Sources: OASDKT-SC-DOCS-GUARD

### State Management (1 file)

- [`_INFO_OASDKT-IN15_SESSIONS.md`](./_INFO_OASDKT-IN15_SESSIONS.md) [OASDKT-IN15]
  - Session protocol, persistent memory layer
  - Maintaining working context within agent loop
  - Sources: OASDKT-SC-DOCS-SESSIONS

### Observability (1 file)

- [`_INFO_OASDKT-IN16_TRACING.md`](./_INFO_OASDKT-IN16_TRACING.md) [OASDKT-IN16]
  - Built-in tracing for debugging and monitoring
  - OpenAI evaluation, fine-tuning, distillation tools
  - Sources: OASDKT-SC-DOCS-TRACE

### Human-in-the-Loop (1 file)

- [`_INFO_OASDKT-IN17_HUMANINLOOP.md`](./_INFO_OASDKT-IN17_HUMANINLOOP.md) [OASDKT-IN17]
  - Human approval patterns
  - Intervention workflows
  - Sources: OASDKT-SC-DOCS-HITL

### Voice Agents (4 files)

- [`_INFO_OASDKT-IN18_VOICE_OVERVIEW.md`](./_INFO_OASDKT-IN18_VOICE_OVERVIEW.md) [OASDKT-IN18]
  - RealtimeAgent, RealtimeSession overview
  - WebRTC and WebSocket transports
  - Sources: OASDKT-SC-VOICE-OVER

- [`_INFO_OASDKT-IN19_VOICE_QUICKSTART.md`](./_INFO_OASDKT-IN19_VOICE_QUICKSTART.md) [OASDKT-IN19]
  - Voice agent quickstart guide
  - Browser setup, microphone/audio output
  - Sources: OASDKT-SC-VOICE-QUICK

- [`_INFO_OASDKT-IN20_VOICE_BUILD.md`](./_INFO_OASDKT-IN20_VOICE_BUILD.md) [OASDKT-IN20]
  - Building voice agents in detail
  - Interruption detection, context management
  - Sources: OASDKT-SC-VOICE-BUILD

- [`_INFO_OASDKT-IN21_VOICE_TRANSPORT.md`](./_INFO_OASDKT-IN21_VOICE_TRANSPORT.md) [OASDKT-IN21]
  - Transport mechanisms
  - WebRTC vs WebSocket comparison
  - Sources: OASDKT-SC-VOICE-TRANS

### Extensions (3 files)

- [`_INFO_OASDKT-IN22_EXT_AISDK.md`](./_INFO_OASDKT-IN22_EXT_AISDK.md) [OASDKT-IN22]
  - Vercel AI SDK adapter
  - Using non-OpenAI models
  - Sources: OASDKT-SC-EXT-AISDK

- [`_INFO_OASDKT-IN23_EXT_TWILIO.md`](./_INFO_OASDKT-IN23_EXT_TWILIO.md) [OASDKT-IN23]
  - Twilio integration for realtime agents
  - Sources: OASDKT-SC-EXT-TWILIO

- [`_INFO_OASDKT-IN24_EXT_CLOUDFLARE.md`](./_INFO_OASDKT-IN24_EXT_CLOUDFLARE.md) [OASDKT-IN24]
  - Cloudflare Workers transport
  - Edge deployment patterns
  - Sources: OASDKT-SC-EXT-CFLARE

### SDK Configuration (2 files)

- [`_INFO_OASDKT-IN25_CONFIG.md`](./_INFO_OASDKT-IN25_CONFIG.md) [OASDKT-IN25]
  - SDK configuration, API keys, clients
  - OPENAI_API_KEY environment variable
  - Sources: OASDKT-SC-DOCS-CONFIG

- [`_INFO_OASDKT-IN26_TROUBLESHOOT.md`](./_INFO_OASDKT-IN26_TROUBLESHOOT.md) [OASDKT-IN26]
  - Troubleshooting common issues
  - Node.js compatibility, environment setup
  - Sources: OASDKT-SC-DOCS-TROUBLE

### Error Handling (1 file)

- [`_INFO_OASDKT-IN27_ERRORS.md`](./_INFO_OASDKT-IN27_ERRORS.md) [OASDKT-IN27]
  - MaxTurnsExceededError, GuardrailTripwireTriggered
  - Error handling patterns
  - Sources: OASDKT-SC-GH-MAIN

### Examples (1 file)

- [`_INFO_OASDKT-IN28_EXAMPLES.md`](./_INFO_OASDKT-IN28_EXAMPLES.md) [OASDKT-IN28]
  - Complete code examples
  - examples/ directory walkthrough
  - Sources: OASDKT-SC-GH-EXAMPLES

### SDK Comparison (1 file)

- [`_INFO_OASDKT_DIFFERENCES_TO_PYTHON.md`](./_INFO_OASDKT_DIFFERENCES_TO_PYTHON.md) [OASDKT-IN29]
  - TypeScript vs Python SDK feature comparison
  - Platform-specific capabilities, naming differences
  - Sources: OASDKT-SC-DOCS-*, OASDKP-SC-*

## Topic Count

- **Total Topics**: 29
- **Getting Started**: 3
- **Core Concepts**: 5
- **Tools**: 3
- **Multi-Agent**: 2
- **Safety**: 1
- **State**: 1
- **Observability**: 1
- **Human-in-the-Loop**: 1
- **Voice Agents**: 4
- **Extensions**: 3
- **SDK Configuration**: 2
- **Error Handling**: 1
- **Examples**: 1
- **SDK Comparison**: 1

## Package Architecture

The TypeScript SDK is split into multiple packages:

- **@openai/agents** - Main package (re-exports from core)
- **@openai/agents-core** - Core agent functionality
- **@openai/agents-openai** - OpenAI-specific implementations
- **@openai/agents-realtime** - Realtime/voice agent support
- **@openai/agents-extensions** - Third-party integrations (AI SDK, Twilio, Cloudflare)

## Related Technologies

- **OpenAI Responses API** - Primary API for agent execution
- **OpenAI Realtime API** - Voice agent backend (WebRTC/WebSocket)
- **Model Context Protocol (MCP)** - Tool standardization
- **Zod v4** - Schema validation for tools and outputs
- **Vercel AI SDK** - Multi-provider model support
- **OpenAI Swarm** - Predecessor experimental project

## Python SDK Comparison

Key differences from Python SDK (`openai-agents`):

- **Validation**: Zod v4 instead of Pydantic
- **Async**: Native async/await instead of asyncio
- **Runtime**: Node.js 22+, Deno, Bun instead of Python 3.9+
- **Browser**: Dedicated browser package for realtime agents
- **Extensions**: Twilio, Cloudflare, Vercel AI SDK adapters
- **Voice**: Voice agents section expanded (4 topics vs 2)

## Document History

**[2026-02-11 19:35]**
- Added: IN29 SDK Comparison (TypeScript vs Python differences)
- Total topics now 29

**[2026-02-11 18:50]**
- Initial TOC created with 28 topics
- Organized into 13 categories
- All topics mapped to source IDs
- Package architecture documented
