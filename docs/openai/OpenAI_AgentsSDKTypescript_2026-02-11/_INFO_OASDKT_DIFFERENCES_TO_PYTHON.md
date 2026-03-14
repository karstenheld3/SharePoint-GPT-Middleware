# INFO: OpenAI Agents SDK - TypeScript vs Python Differences

**Doc ID**: OASDKT-IN29
**Goal**: Compare TypeScript and Python SDK features, identify gaps and platform-specific capabilities
**Timeline**: Created 2026-02-11

## Summary

- Python SDK has 34 topics, TypeScript SDK has 28 topics [VERIFIED]
- Most "missing" TypeScript features actually exist but under different names or locations [VERIFIED]
- TypeScript has unique extensions: Twilio, Cloudflare Workers, Vercel AI SDK [VERIFIED]
- Python has REPL and Visualization features not available in TypeScript [VERIFIED]
- Both SDKs support tool choice, external tracing, and computer use [VERIFIED]

## Table of Contents

1. [Topic Count Comparison](#1-topic-count-comparison)
2. [Features in Both SDKs](#2-features-in-both-sdks)
3. [Python-Only Features](#3-python-only-features)
4. [TypeScript-Only Features](#4-typescript-only-features)
5. [Naming Differences](#5-naming-differences)
6. [Sources](#6-sources)
7. [Document History](#7-document-history)

## 1. Topic Count Comparison

**Python SDK**: 34 INFO files
**TypeScript SDK**: 28 INFO files
**Difference**: 6 topics

### Python Topic Categories

- Getting Started: 3
- Core Concepts: 5
- Tools: 4
- Multi-Agent: 2
- Safety: 2
- State: 2
- Observability: 2
- MCP: 1
- Realtime: 2
- Advanced: 3
- Examples: 1
- Voice Pipeline: 1
- SDK Configuration: 1
- Computer Use: 1
- Developer Tools: 2 (REPL, Visualization)
- Monitoring: 1
- Advanced Sessions: 1

### TypeScript Topic Categories

- Getting Started: 3
- Core Concepts: 5
- Tools: 3
- Multi-Agent: 2
- Safety: 1
- State: 1
- Observability: 1
- Human-in-the-Loop: 1
- Voice Agents: 4
- Extensions: 3
- SDK Configuration: 2
- Error Handling: 1
- Examples: 1

## 2. Features in Both SDKs

### Tool Choice (modelSettings.toolChoice)

**Python**: `ModelSettings.tool_choice` with values `auto`, `required`, `none`, specific tool name
**TypeScript**: `modelSettings.toolChoice` with same values [VERIFIED]

**TypeScript Source**: https://openai.github.io/openai-agents-js/guides/agents#forcing-tool-use

```typescript
const agent = new Agent({
  name: 'Strict tool user',
  tools: [calculatorTool],
  modelSettings: { toolChoice: 'required' },
});
```

### Tool Use Behavior

**Python**: `tool_use_behavior` with `run_llm_again`, `stop_on_first_tool`, `StopAtTools`
**TypeScript**: `toolUseBehavior` with same options [VERIFIED]

**TypeScript Source**: https://openai.github.io/openai-agents-js/guides/agents#preventing-infinite-loops

```typescript
const agent = new Agent({
  toolUseBehavior: 'stop_on_first_tool',
});
// Or: { stopAtToolNames: ['my_tool'] }
```

### External Tracing Processors

**Python**: Logfire, AgentOps, Braintrust, Scorecard, Keywords AI
**TypeScript**: AgentOps, Keywords AI [VERIFIED]

**TypeScript Source**: https://openai.github.io/openai-agents-js/guides/tracing#external-tracing-processors-list

### Computer Use Tool

**Python**: `ComputerTool` class
**TypeScript**: `computerTool()` function with `Computer` interface [VERIFIED]

**TypeScript Source**: https://openai.github.io/openai-agents-js/guides/tools#2-local-built-in-tools

```typescript
import { computerTool, Computer } from '@openai/agents';

const computer: Computer = {
  environment: 'browser',
  dimensions: [1024, 768],
  screenshot: async () => '',
  click: async () => {},
  // ... other methods
};

const agent = new Agent({
  tools: [computerTool({ computer })],
});
```

### Shell Tool

**Python**: Not a separate topic (possibly in Computer Use)
**TypeScript**: `shellTool()` function with `Shell` interface [VERIFIED]

```typescript
import { shellTool, Shell } from '@openai/agents';

const shell: Shell = {
  run: async () => ({ output: [{ stdout: '', stderr: '', outcome: { type: 'exit', exitCode: 0 } }] }),
};

const agent = new Agent({
  tools: [shellTool({ shell, needsApproval: true })],
});
```

### Apply Patch Tool (Editor)

**Python**: Not documented as separate feature
**TypeScript**: `applyPatchTool()` function with `Editor` interface [VERIFIED]

```typescript
import { applyPatchTool, Editor } from '@openai/agents';

const editor: Editor = {
  createFile: async () => ({ status: 'completed' }),
  updateFile: async () => ({ status: 'completed' }),
  deleteFile: async () => ({ status: 'completed' }),
};
```

### Codex Tool (Experimental)

**Python**: Not documented
**TypeScript**: `codexTool()` in `@openai/agents-extensions/experimental/codex` [VERIFIED]

**TypeScript Source**: https://openai.github.io/openai-agents-js/guides/tools#6-experimental-codex-tool

## 3. Python-Only Features

### REPL (Interactive Testing)

**Python**: `run_demo_loop` for interactive agent testing in terminal
**TypeScript**: Not available [VERIFIED]

**Python Source**: https://openai.github.io/openai-agents-python/repl/

**Why Missing**: Node.js has different REPL patterns; users typically test via script files or browser.

### Visualization (Agent Graphs)

**Python**: Mermaid diagram generation, Jupyter integration
**TypeScript**: Not available [VERIFIED]

**Python Source**: https://openai.github.io/openai-agents-python/agent_visualization/

**Why Missing**: Python's Jupyter ecosystem is more mature for visual debugging.

### Usage Tracking (Token Monitoring)

**Python**: Dedicated usage tracking and cost estimation APIs
**TypeScript**: Not documented as separate feature [ASSUMED]

**Python Source**: https://openai.github.io/openai-agents-python/usage/

### Advanced Sessions (SQLAlchemy, Encryption)

**Python**: SQLAlchemySession, EncryptedSession, compression options
**TypeScript**: Custom `Session` interface supports Redis, DynamoDB, SQLite [VERIFIED]

**Python Source**: https://openai.github.io/openai-agents-python/sessions/

**Note**: Both SDKs support custom session backends. Python has more pre-built options.

### Voice Pipeline (Speech-to-Text Chain)

**Python**: VoicePipeline, SingleAgentVoiceWorkflow, AudioInput for chaining text agents
**TypeScript**: Marked as "Future" in roadmap [VERIFIED]

**Python Source**: https://openai.github.io/openai-agents-python/voice/

**TypeScript Roadmap**: https://github.com/openai/openai-agents-js - "Voice pipeline" listed as Future feature

### Conversations (Manual Management)

**Python**: `to_input_list()` for manual conversation management
**TypeScript**: Covered in Runner/Results, not separate topic [ASSUMED]

### Non-OpenAI Models (LiteLLM, Ollama)

**Python**: Dedicated guide for LiteLLM and Ollama integration
**TypeScript**: Covered via Vercel AI SDK adapter extension [VERIFIED]

## 4. TypeScript-Only Features

### Vercel AI SDK Extension

**TypeScript**: Use non-OpenAI models (Anthropic, Google, etc.) via AI SDK adapter
**Python**: Uses LiteLLM instead

**TypeScript Source**: https://openai.github.io/openai-agents-js/extensions/ai-sdk

### Twilio Extension

**TypeScript**: Direct Twilio integration for realtime voice agents
**Python**: Not available as built-in extension

**TypeScript Source**: https://openai.github.io/openai-agents-js/extensions/twilio

### Cloudflare Workers Extension

**TypeScript**: Edge deployment on Cloudflare Workers
**Python**: Not applicable (different runtime)

**TypeScript Source**: https://openai.github.io/openai-agents-js/extensions/cloudflare

### Voice Transport Comparison

**TypeScript**: Dedicated guide comparing WebRTC vs WebSocket
**Python**: Less detailed transport documentation

**TypeScript Source**: https://openai.github.io/openai-agents-js/guides/voice-agents/transport

### Browser Package

**TypeScript**: `@openai/agents-realtime` optimized for browser environments
**Python**: Server-side only

## 5. Naming Differences

- **Schema validation** - Python: Pydantic, TypeScript: Zod v4
- **Async pattern** - Python: asyncio, TypeScript: async/await (native)
- **Tool decorator** - Python: `@function_tool`, TypeScript: `tool()` function
- **Model settings** - Python: `ModelSettings`, TypeScript: `modelSettings` object
- **Tool choice** - Python: `tool_choice`, TypeScript: `toolChoice` (camelCase)
- **Run method** - Python: `Runner.run()`, TypeScript: `run()` function
- **Realtime agent** - Python: `RealtimeRunner`, TypeScript: `RealtimeSession`

## 6. Sources

**Primary Sources:**

- `OASDKT-IN29-SC-TSDOCS-TOOLS`: https://openai.github.io/openai-agents-js/guides/tools - Local tools, computerTool, shellTool [VERIFIED]
- `OASDKT-IN29-SC-TSDOCS-AGENTS`: https://openai.github.io/openai-agents-js/guides/agents - Tool choice, toolUseBehavior [VERIFIED]
- `OASDKT-IN29-SC-TSDOCS-TRACE`: https://openai.github.io/openai-agents-js/guides/tracing - External processors [VERIFIED]
- `OASDKT-IN29-SC-GH-README`: https://github.com/openai/openai-agents-js - Roadmap, supported features [VERIFIED]
- `OASDKT-IN29-SC-PYDOCS-REPL`: https://openai.github.io/openai-agents-python/repl/ - Python REPL [VERIFIED]
- `OASDKT-IN29-SC-PYDOCS-VIZ`: https://openai.github.io/openai-agents-python/agent_visualization/ - Python Visualization [VERIFIED]

## 7. Document History

**[2026-02-11 19:45]**
- Fixed: Python SDK URLs (removed `/guides/` prefix)
- Fixed: Session comparison - both SDKs support custom backends
- Fixed: Converted Markdown table to list format

**[2026-02-11 19:30]**
- Initial comparison document created
- Researched 6 potential gaps from Python SDK
- Found most features exist in both SDKs
- Identified 5 true Python-only features: REPL, Visualization, Usage, Advanced Sessions, Voice Pipeline
- Identified 4 TypeScript-only features: Vercel AI SDK, Twilio, Cloudflare, Browser Package
