# OpenAI Agents SDK Python - Table of Contents

**Doc ID**: OASDKP-TOC
**Goal**: Master index for OpenAI Agents SDK Python documentation (MCPI)
**Version**: openai-agents 0.8.3 (2026-02-11)
**Package**: `pip install openai-agents`
**Python**: 3.9+
**Repository**: https://github.com/openai/openai-agents-python

## Summary

The OpenAI Agents SDK is a lightweight, production-ready Python framework for building multi-agent AI applications. It evolved from the experimental Swarm project and provides a minimal set of primitives: Agents (LLMs with instructions and tools), Handoffs (agent-to-agent delegation), and Guardrails (input/output validation). The SDK is provider-agnostic, supporting OpenAI's Responses and Chat Completions APIs plus 100+ other LLMs. Key features include automatic agent loops, Python-first orchestration, function tools with Pydantic validation, MCP server integration, built-in sessions for conversation memory, human-in-the-loop patterns, comprehensive tracing for debugging and monitoring, and realtime voice agent capabilities. The SDK emphasizes being quick to learn while remaining highly customizable.

## Topic Files

### Getting Started (3 files)

- [`_INFO_OASDKP-IN01_INTRODUCTION.md`](./_INFO_OASDKP-IN01_INTRODUCTION.md) [OASDKP-IN01]
  - SDK overview, design principles, installation, hello world
  - Sources: OASDKP-SC-GHIO-HOME, OASDKP-SC-PYPI-PKG

- [`_INFO_OASDKP-IN02_QUICKSTART.md`](./_INFO_OASDKP-IN02_QUICKSTART.md) [OASDKP-IN02]
  - Environment setup, first agent, basic patterns
  - Sources: OASDKP-SC-GHIO-QUICKSTART

- [`_INFO_OASDKP-IN03_MODELS.md`](./_INFO_OASDKP-IN03_MODELS.md) [OASDKP-IN03]
  - Supported models, ModelSettings, provider configuration
  - Sources: OASDKP-SC-GHIO-AGENTS

### Core Concepts (5 files)

- [`_INFO_OASDKP-IN04_AGENTS.md`](./_INFO_OASDKP-IN04_AGENTS.md) [OASDKP-IN04]
  - Agent class, name, instructions, model, tools, prompt templates
  - Dynamic instructions, lifecycle hooks, cloning
  - Sources: OASDKP-SC-GHIO-AGENTS

- [`_INFO_OASDKP-IN05_RUNNER.md`](./_INFO_OASDKP-IN05_RUNNER.md) [OASDKP-IN05]
  - Runner class, run(), run_sync(), run_streamed()
  - Agent loop mechanics, max_turns, final output rules
  - Sources: OASDKP-SC-GHIO-RUNNING

- [`_INFO_OASDKP-IN06_CONTEXT.md`](./_INFO_OASDKP-IN06_CONTEXT.md) [OASDKP-IN06]
  - RunContextWrapper, dependency injection, typed context
  - Sources: OASDKP-SC-GHIO-AGENTS

- [`_INFO_OASDKP-IN07_RESULTS.md`](./_INFO_OASDKP-IN07_RESULTS.md) [OASDKP-IN07]
  - RunResult, RunResultStreaming, final_output, output_type
  - Structured outputs with Pydantic
  - Sources: OASDKP-SC-GHIO-RESULTS, OASDKP-SC-GHIO-AGENTS

- [`_INFO_OASDKP-IN08_STREAMING.md`](./_INFO_OASDKP-IN08_STREAMING.md) [OASDKP-IN08]
  - stream_events(), streaming patterns, partial results
  - Sources: OASDKP-SC-GHIO-STREAMING

### Tools (4 files)

- [`_INFO_OASDKP-IN09_TOOLS_OVERVIEW.md`](./_INFO_OASDKP-IN09_TOOLS_OVERVIEW.md) [OASDKP-IN09]
  - Tool categories: hosted, local, function, agents-as-tools, experimental
  - Sources: OASDKP-SC-GHIO-TOOLS

- [`_INFO_OASDKP-IN10_TOOLS_FUNCTION.md`](./_INFO_OASDKP-IN10_TOOLS_FUNCTION.md) [OASDKP-IN10]
  - @function_tool decorator, Pydantic Field, docstring parsing
  - Custom function tools, returning images/files, error handling
  - Sources: OASDKP-SC-GHIO-TOOLS

- [`_INFO_OASDKP-IN11_TOOLS_HOSTED.md`](./_INFO_OASDKP-IN11_TOOLS_HOSTED.md) [OASDKP-IN11]
  - WebSearchTool, FileSearchTool, CodeInterpreterTool
  - ImageGenerationTool, HostedMCPTool
  - Sources: OASDKP-SC-GHIO-TOOLS

- [`_INFO_OASDKP-IN12_TOOLS_AGENTSASTOOLS.md`](./_INFO_OASDKP-IN12_TOOLS_AGENTSASTOOLS.md) [OASDKP-IN12]
  - agent.as_tool(), tool_name, tool_description
  - Structured input, approval gates, output extraction
  - Sources: OASDKP-SC-GHIO-TOOLS

### Multi-Agent Patterns (2 files)

- [`_INFO_OASDKP-IN13_HANDOFFS.md`](./_INFO_OASDKP-IN13_HANDOFFS.md) [OASDKP-IN13]
  - Handoff concept, handoff() function, handoff_description
  - Input filters, recommended prompts
  - Sources: OASDKP-SC-GHIO-HANDOFFS

- [`_INFO_OASDKP-IN14_MULTIAGENT.md`](./_INFO_OASDKP-IN14_MULTIAGENT.md) [OASDKP-IN14]
  - Manager pattern vs handoff pattern
  - Triage agents, specialized agents, conversation flow
  - Sources: OASDKP-SC-GHIO-AGENTS, OASDKP-SC-OAIGUIDE-PDF

### Safety and Validation (2 files)

- [`_INFO_OASDKP-IN15_GUARDRAILS.md`](./_INFO_OASDKP-IN15_GUARDRAILS.md) [OASDKP-IN15]
  - Input guardrails, output guardrails, tool guardrails
  - Execution modes (blocking vs parallel), tripwires
  - GuardrailFunctionOutput, InputGuardrailTripwireTriggered
  - Sources: OASDKP-SC-GHIO-GUARDRAILS

- [`_INFO_OASDKP-IN16_TOOLCHOICE.md`](./_INFO_OASDKP-IN16_TOOLCHOICE.md) [OASDKP-IN16]
  - ModelSettings.tool_choice (auto, required, none, specific)
  - tool_use_behavior, reset_tool_choice, StopAtTools
  - Sources: OASDKP-SC-GHIO-AGENTS

### State Management (2 files)

- [`_INFO_OASDKP-IN17_SESSIONS.md`](./_INFO_OASDKP-IN17_SESSIONS.md) [OASDKP-IN17]
  - Session protocol, SQLiteSession, RedisSession
  - Custom session implementations, session options
  - Sources: OASDKP-SC-GH-REPO

- [`_INFO_OASDKP-IN18_CONVERSATIONS.md`](./_INFO_OASDKP-IN18_CONVERSATIONS.md) [OASDKP-IN18]
  - Manual conversation management, to_input_list()
  - Server-managed conversations
  - Sources: OASDKP-SC-GHIO-RUNNING

### Observability (2 files)

- [`_INFO_OASDKP-IN19_TRACING.md`](./_INFO_OASDKP-IN19_TRACING.md) [OASDKP-IN19]
  - Traces, spans, workflow_name, trace_id, group_id
  - Default tracing, custom spans, sensitive data
  - Sources: OASDKP-SC-GHIO-TRACING

- [`_INFO_OASDKP-IN20_TRACING_EXTERNAL.md`](./_INFO_OASDKP-IN20_TRACING_EXTERNAL.md) [OASDKP-IN20]
  - External tracing processors: Logfire, AgentOps, Braintrust
  - Scorecard, Keywords AI, custom processors
  - Sources: OASDKP-SC-GHIO-TRACING

### MCP Integration (1 file)

- [`_INFO_OASDKP-IN21_MCP.md`](./_INFO_OASDKP-IN21_MCP.md) [OASDKP-IN21]
  - Model Context Protocol overview
  - Hosted MCP, Streamable HTTP, SSE, stdio transports
  - Tool filtering, prompts, caching
  - Sources: OASDKP-SC-GHIO-MCP

### Realtime/Voice Agents (2 files)

- [`_INFO_OASDKP-IN22_REALTIME.md`](./_INFO_OASDKP-IN22_REALTIME.md) [OASDKP-IN22]
  - RealtimeRunner, RealtimeAgent, voice configuration
  - Audio processing, interruption handling
  - Sources: OASDKP-SC-GHIO-REALTIME

- [`_INFO_OASDKP-IN23_REALTIME_ADVANCED.md`](./_INFO_OASDKP-IN23_REALTIME_ADVANCED.md) [OASDKP-IN23]
  - SIP integration, event handling, direct model access
  - Azure OpenAI endpoint format
  - Sources: OASDKP-SC-GHIO-REALTIME

### Advanced Topics (3 files)

- [`_INFO_OASDKP-IN24_HUMANINLOOP.md`](./_INFO_OASDKP-IN24_HUMANINLOOP.md) [OASDKP-IN24]
  - Long-running agents, approval patterns
  - Temporal, Restate, DBOS integrations
  - Sources: OASDKP-SC-GHIO-RUNNING

- [`_INFO_OASDKP-IN25_ERRORS.md`](./_INFO_OASDKP-IN25_ERRORS.md) [OASDKP-IN25]
  - Exception types: MaxTurnsExceeded, InputGuardrailTripwireTriggered
  - Error handlers, retry patterns
  - Sources: OASDKP-SC-GHIO-RUNNING

- [`_INFO_OASDKP-IN26_NONOPENAI.md`](./_INFO_OASDKP-IN26_NONOPENAI.md) [OASDKP-IN26]
  - Provider-agnostic usage, Chat Completions API providers
  - LiteLLM integration, Ollama usage
  - Sources: OASDKP-SC-GHIO-TRACING, OASDKP-SC-SO-OLLAMA

### Examples and Patterns (1 file)

- [`_INFO_OASDKP-IN27_EXAMPLES.md`](./_INFO_OASDKP-IN27_EXAMPLES.md) [OASDKP-IN27]
  - agent_patterns directory examples
  - Deterministic flows, iterative loops
  - Complete code examples with explanations
  - Sources: OASDKP-SC-GHIO-EXAMPLES, OASDKP-SC-GH-REPO

### Voice Pipeline (1 file)

- [`_INFO_OASDKP-IN28_VOICE.md`](./_INFO_OASDKP-IN28_VOICE.md) [OASDKP-IN28]
  - VoicePipeline, SingleAgentVoiceWorkflow, AudioInput
  - Speech-to-text and text-to-speech processing
  - Sources: OASDKP-SC-GHIO-VOICE

### SDK Configuration (1 file)

- [`_INFO_OASDKP-IN29_CONFIG.md`](./_INFO_OASDKP-IN29_CONFIG.md) [OASDKP-IN29]
  - API keys, clients, tracing, logging
  - set_default_openai_key, set_default_openai_api
  - Sources: OASDKP-SC-GHIO-CONFIG

### Computer Use (1 file)

- [`_INFO_OASDKP-IN30_COMPUTER.md`](./_INFO_OASDKP-IN30_COMPUTER.md) [OASDKP-IN30]
  - ComputerTool for GUI automation
  - Screenshots, mouse, keyboard actions
  - Sources: OASDKP-SC-GH-REPO

### Developer Tools (2 files)

- [`_INFO_OASDKP-IN31_REPL.md`](./_INFO_OASDKP-IN31_REPL.md) [OASDKP-IN31]
  - Interactive REPL for testing agents
  - run_demo_loop, tool/handoff display
  - Sources: OASDKP-SC-GHIO-REPL

- [`_INFO_OASDKP-IN32_VISUALIZATION.md`](./_INFO_OASDKP-IN32_VISUALIZATION.md) [OASDKP-IN32]
  - Agent graph visualization
  - Mermaid diagrams, Jupyter integration
  - Sources: OASDKP-SC-GHIO-VISUALIZATION

### Monitoring (1 file)

- [`_INFO_OASDKP-IN33_USAGE.md`](./_INFO_OASDKP-IN33_USAGE.md) [OASDKP-IN33]
  - Token usage tracking
  - Cost estimation, usage aggregation
  - Sources: OASDKP-SC-GHIO-USAGE

### Advanced Sessions (1 file)

- [`_INFO_OASDKP-IN34_SESSIONS_ADVANCED.md`](./_INFO_OASDKP-IN34_SESSIONS_ADVANCED.md) [OASDKP-IN34]
  - SQLAlchemySession, EncryptedSession, AdvancedSQLiteSession
  - Compression, encryption, auto-cleanup
  - Sources: OASDKP-SC-GHIO-SESSIONS

## Topic Count

- **Total Topics**: 34
- **Getting Started**: 3
- **Core Concepts**: 5
- **Tools**: 4
- **Multi-Agent**: 2
- **Safety**: 2
- **State**: 2
- **Observability**: 2
- **MCP**: 1
- **Realtime**: 2
- **Advanced**: 3
- **Examples**: 1
- **Voice Pipeline**: 1
- **SDK Configuration**: 1
- **Computer Use**: 1
- **Developer Tools**: 2
- **Monitoring**: 1
- **Advanced Sessions**: 1

## Related Technologies

- **OpenAI Responses API** - Primary API for agent execution
- **OpenAI Chat Completions API** - Alternative API support
- **OpenAI Realtime API** - Voice agent backend
- **Model Context Protocol (MCP)** - Tool standardization
- **Pydantic** - Schema validation for tools and outputs
- **OpenAI Swarm** - Predecessor experimental project

## Document History

**[2026-02-11 11:55]**
- Added remaining 4 topics: REPL, Visualization, Usage, Advanced Sessions
- Total topics now 34

**[2026-02-11 11:50]**
- Added 3 missing topics after verification: Voice, Config, Computer

**[2026-02-11 11:42]**
- Renamed OASDK -> OASDKP (P for Python)

**[2026-02-11 11:40]**
- Added clickable markdown links to all topic files
- Fixed typo: NONPPENAI -> NONOPENAI

**[2026-02-11 11:25]**
- Initial TOC created with 27 topics
- Organized into 11 categories
- All topics mapped to source IDs
