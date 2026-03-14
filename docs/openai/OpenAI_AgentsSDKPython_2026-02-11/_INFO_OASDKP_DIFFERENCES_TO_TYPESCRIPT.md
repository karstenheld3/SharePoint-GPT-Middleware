# INFO: OpenAI Agents SDK - Python vs TypeScript Differences

**Doc ID**: OASDKP-IN35
**Goal**: Compare Python and TypeScript SDK features from the Python perspective
**Timeline**: Created 2026-02-11

## Summary

- Python SDK has 34 topics, TypeScript SDK has 28 topics [VERIFIED]
- Python has mature developer tools: REPL, Visualization, Usage tracking [VERIFIED]
- Python has richer session options: SQLAlchemy, encryption, compression [VERIFIED]
- Python has Voice Pipeline for STT/TTS chaining; TypeScript focuses on realtime [VERIFIED]
- TypeScript has unique extensions: Twilio, Cloudflare Workers, browser package [VERIFIED]
- Both SDKs share core primitives: Agents, Tools, Handoffs, Guardrails, Tracing [VERIFIED]

## Table of Contents

1. [Topic Count Comparison](#1-topic-count-comparison)
2. [Features in Both SDKs](#2-features-in-both-sdks)
3. [Python Advantages](#3-python-advantages)
4. [TypeScript Advantages](#4-typescript-advantages)
5. [Naming Differences](#5-naming-differences)
6. [Migration Considerations](#6-migration-considerations)
7. [Sources](#7-sources)
8. [Document History](#8-document-history)

## 1. Topic Count Comparison

**Python SDK**: 34 INFO files (openai-agents 0.8.3)
**TypeScript SDK**: 28 INFO files (@openai/agents 0.4.6)
**Difference**: Python has 6 more documented topics

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

### Core Primitives

Both SDKs implement the same fundamental concepts:

- **Agents** - LLMs with instructions and tools
- **Tools** - Function tools, hosted tools, MCP integration
- **Handoffs** - Agent-to-agent delegation
- **Guardrails** - Input/output validation
- **Tracing** - Built-in debugging and monitoring
- **Sessions** - Conversation memory persistence
- **Human-in-the-Loop** - Approval patterns

### Tool Choice Control

**Python**: `ModelSettings.tool_choice` with `auto`, `required`, `none`, specific tool
**TypeScript**: `modelSettings.toolChoice` with same values [VERIFIED]

```python
from agents import Agent, ModelSettings

agent = Agent(
    name="Strict tool user",
    tools=[calculator_tool],
    model_settings=ModelSettings(tool_choice="required"),
)
```

### Tool Use Behavior

**Python**: `tool_use_behavior` with `run_llm_again`, `stop_on_first_tool`, `StopAtTools`
**TypeScript**: `toolUseBehavior` with same options [VERIFIED]

```python
from agents import Agent

agent = Agent(
    name="Single tool agent",
    tool_use_behavior="stop_on_first_tool",
)
```

### External Tracing

**Python**: Logfire, AgentOps, Braintrust, Scorecard, Keywords AI (5 integrations)
**TypeScript**: AgentOps, Keywords AI (2 integrations) [VERIFIED]

**Python Source**: https://openai.github.io/openai-agents-python/tracing/

### Computer Use

**Python**: `ComputerTool` class for GUI automation
**TypeScript**: `computerTool()` function with `Computer` interface [VERIFIED]

```python
from agents.extensions.computer import ComputerTool

tool = ComputerTool()
agent = Agent(name="Computer user", tools=[tool])
```

## 3. Python Advantages

### REPL (Interactive Testing)

`run_demo_loop` provides interactive terminal testing - not available in TypeScript.

**Source**: https://openai.github.io/openai-agents-python/repl/

```python
from agents import Agent, run_demo_loop
import asyncio

async def main():
    agent = Agent(name="Assistant", instructions="You are helpful.")
    await run_demo_loop(agent)

asyncio.run(main())
```

**Why Python-only**: Node.js ecosystem uses different patterns (script files, browser testing).

### Visualization (Agent Graphs)

Generate Mermaid diagrams of agent relationships, Jupyter notebook integration.

**Source**: https://openai.github.io/openai-agents-python/agent_visualization/

**Why Python-only**: Python's Jupyter ecosystem is more mature for visual debugging.

### Usage Tracking (Token Monitoring)

Dedicated APIs for tracking token usage and estimating costs.

**Source**: https://openai.github.io/openai-agents-python/usage/

```python
result = await Runner.run(agent, "What's the weather?")
usage = result.context_wrapper.usage
print(f"Tokens: {usage.total_tokens}")
print(f"Input: {usage.input_tokens}, Output: {usage.output_tokens}")
```

### Advanced Sessions

Pre-built session implementations beyond basic memory:

- **SQLAlchemySession** - Database-backed sessions
- **AdvancedSQLiteSession** - SQLite with compression
- **EncryptedSession** - Encrypted conversation storage

**Source**: https://openai.github.io/openai-agents-python/sessions/

**Note**: TypeScript supports custom `Session` interface but lacks pre-built implementations.

### Voice Pipeline (STT/TTS Chaining)

Chain text-based agents with speech-to-text and text-to-speech.

**Source**: https://openai.github.io/openai-agents-python/voice/

```python
from agents.voice import VoicePipeline, SingleAgentVoiceWorkflow

workflow = SingleAgentVoiceWorkflow(agent)
pipeline = VoicePipeline(workflow=workflow)
```

**TypeScript status**: Marked as "Future" in roadmap.

### More External Tracing Options

Python has 5 documented external tracers vs TypeScript's 2:

- Logfire (Python-only)
- AgentOps (both)
- Braintrust (Python-only)
- Scorecard (Python-only)
- Keywords AI (both)

### LiteLLM Integration

Direct integration with 100+ LLM providers via LiteLLM.

**Source**: https://openai.github.io/openai-agents-python/models/

```python
from agents import Agent, Runner
from agents.extensions.models.litellm_model import LitellmModel

agent = Agent(name="Claude Agent", model=LitellmModel(model="claude-3-opus"))
```

**TypeScript equivalent**: Vercel AI SDK adapter (different implementation).

## 4. TypeScript Advantages

### Twilio Extension

Direct integration for phone-based realtime voice agents.

**Source**: https://openai.github.io/openai-agents-js/extensions/twilio

**Python equivalent**: Not available as built-in extension.

### Cloudflare Workers Extension

Edge deployment on Cloudflare's global network.

**Source**: https://openai.github.io/openai-agents-js/extensions/cloudflare

**Python equivalent**: Not applicable (different runtime environment).

### Browser Package

`@openai/agents-realtime` optimized for browser environments with WebRTC.

**Python equivalent**: Server-side only; no browser runtime.

### Shell Tool

Explicit `shellTool()` with approval mechanism for command execution.

**Source**: https://openai.github.io/openai-agents-js/guides/tools

**Python equivalent**: Not documented as separate feature.

### Apply Patch Tool

`applyPatchTool()` for file editing with `Editor` interface.

**Source**: https://openai.github.io/openai-agents-js/guides/tools

**Python equivalent**: Not documented as separate feature.

### Codex Tool (Experimental)

Integration with OpenAI Codex for code-related tasks.

**Source**: https://openai.github.io/openai-agents-js/guides/tools#6-experimental-codex-tool

**Python equivalent**: Not documented.

### Vercel AI SDK Adapter

Use non-OpenAI models (Anthropic, Google, etc.) via unified API.

**Source**: https://openai.github.io/openai-agents-js/extensions/ai-sdk

**Python equivalent**: LiteLLM serves similar purpose.

## 5. Naming Differences

- **Schema validation** - Python: Pydantic, TypeScript: Zod v4
- **Async pattern** - Python: asyncio, TypeScript: async/await (native)
- **Tool decorator** - Python: `@function_tool`, TypeScript: `tool()` function
- **Model settings** - Python: `ModelSettings` class, TypeScript: `modelSettings` object
- **Tool choice** - Python: `tool_choice` (snake_case), TypeScript: `toolChoice` (camelCase)
- **Run method** - Python: `Runner.run()`, TypeScript: `run()` function
- **Realtime agent** - Python: `RealtimeRunner`, TypeScript: `RealtimeSession`
- **Package manager** - Python: pip, TypeScript: npm

## 6. Migration Considerations

### Python to TypeScript

When migrating from Python to TypeScript:

1. **Replace Pydantic with Zod** - Schema definitions need rewriting
2. **Replace asyncio with native async** - Simpler in TypeScript
3. **Replace `@function_tool` with `tool()`** - Different decorator pattern
4. **No REPL** - Use script files or browser for testing
5. **No Visualization** - Use tracing dashboard instead
6. **Check session implementation** - May need custom `Session` class

### TypeScript to Python

When migrating from TypeScript to Python:

1. **Replace Zod with Pydantic** - Schema definitions need rewriting
2. **Use asyncio** - Wrap in `async def` and `asyncio.run()`
3. **Replace `tool()` with `@function_tool`** - Decorator pattern
4. **No Twilio/Cloudflare extensions** - May need custom integration
5. **No browser runtime** - Server-side only

## 7. Sources

**Primary Sources:**

- `OASDKP-IN35-SC-PYDOCS-HOME`: https://openai.github.io/openai-agents-python/ - Python SDK documentation [VERIFIED]
- `OASDKP-IN35-SC-PYDOCS-REPL`: https://openai.github.io/openai-agents-python/repl/ - REPL utility [VERIFIED]
- `OASDKP-IN35-SC-PYDOCS-VIZ`: https://openai.github.io/openai-agents-python/agent_visualization/ - Visualization [VERIFIED]
- `OASDKP-IN35-SC-PYDOCS-USAGE`: https://openai.github.io/openai-agents-python/usage/ - Usage tracking [VERIFIED]
- `OASDKP-IN35-SC-TSDOCS-HOME`: https://openai.github.io/openai-agents-js/ - TypeScript SDK documentation [VERIFIED]
- `OASDKP-IN35-SC-TSDOCS-EXT`: https://openai.github.io/openai-agents-js/extensions/ai-sdk - Extensions [VERIFIED]

**Related Document:**
- `_INFO_OASDKT_DIFFERENCES_TO_PYTHON.md` [OASDKT-IN29] - TypeScript perspective comparison

## 8. Document History

**[2026-02-11 19:50]**
- Initial comparison document created from Python perspective
- Documented 6 Python advantages: REPL, Visualization, Usage, Sessions, Voice Pipeline, Tracing
- Documented 7 TypeScript advantages: Twilio, Cloudflare, Browser, Shell, Patch, Codex, AI SDK
- Added migration considerations section
