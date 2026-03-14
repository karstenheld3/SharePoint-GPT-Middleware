# INFO: OpenAI Agents SDK Introduction

**Doc ID**: OASDKP-IN01
**Goal**: Provide comprehensive overview of the OpenAI Agents SDK for Python
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-HOME` - Main SDK documentation
- `OASDKP-SC-PYPI-PKG` - PyPI package info
- `OASDKP-SC-GH-REPO` - GitHub repository

## Summary

The OpenAI Agents SDK is a lightweight, production-ready Python framework for building agentic AI applications. It evolved from OpenAI's experimental Swarm project into a fully supported SDK released in March 2025. The SDK provides a minimal set of primitives - Agents (LLMs with instructions and tools), Handoffs (agent-to-agent delegation), and Guardrails (input/output validation) - that combine with Python's native features to express complex multi-agent relationships without a steep learning curve. [VERIFIED]

The SDK is designed around two principles: (1) enough features to be worth using, but few enough primitives to make it quick to learn, and (2) works great out of the box, but you can customize exactly what happens. It supports both OpenAI's Responses API and Chat Completions API, plus 100+ other LLM providers through adapters. Built-in tracing enables visualization, debugging, and monitoring of agent workflows. [VERIFIED]

## Installation

### Basic Installation

```python
pip install openai-agents
```

### With Voice Support

```python
pip install 'openai-agents[voice]'
```

### Requirements

- **Python**: 3.9 or newer [VERIFIED]
- **OpenAI API Key**: Required for OpenAI models
- **Dependencies**: Automatically installed (openai, pydantic, etc.)

## Hello World Example

```python
from agents import Agent, Runner

# Create a simple agent
agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant"
)

# Run synchronously
result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
print(result.final_output)

# Output:
# Code within the code,
# Functions calling themselves,
# Infinite loop's dance.
```

**Environment Setup:**

```bash
export OPENAI_API_KEY=sk-...
```

## Core Primitives

The SDK has three core primitives that form the foundation of all agent applications:

### 1. Agents

An Agent is an LLM configured with instructions and tools. Agents are the core building block. [VERIFIED]

- **name**: Required identifier string
- **instructions**: System prompt / developer message
- **model**: Which LLM to use (e.g., `gpt-5-nano`)
- **tools**: List of tools the agent can use
- **handoffs**: Other agents this agent can delegate to

### 2. Handoffs

Handoffs allow an agent to delegate tasks to another agent. When a handoff occurs, the delegated agent receives the conversation history and takes over. [VERIFIED]

- Enable modular, specialized agents
- Each agent can excel at a single task
- Supports decentralized multi-agent patterns

### 3. Guardrails

Guardrails enable validation of agent inputs and outputs. They run checks in parallel with agent execution and can fail fast when checks don't pass. [VERIFIED]

- Input guardrails run on initial user input
- Output guardrails run on final agent output
- Can prevent malicious or off-topic usage

## Key Features

### Agent Loop

Built-in agent loop that handles tool invocation, sends results back to the LLM, and continues until the task is complete. No manual orchestration required. [VERIFIED]

### Python-First

Use built-in language features to orchestrate and chain agents, rather than needing to learn new abstractions. [VERIFIED]

### Function Tools

Turn any Python function into a tool with automatic schema generation and Pydantic-powered validation. [VERIFIED]

```python
from agents import Agent, function_tool

@function_tool
def get_weather(city: str) -> str:
    """Returns weather info for the specified city."""
    return f"The weather in {city} is sunny"

agent = Agent(
    name="Weather Agent",
    instructions="Help users with weather information",
    tools=[get_weather]
)
```

### MCP Server Integration

Built-in Model Context Protocol (MCP) server tool integration that works the same way as function tools. [VERIFIED]

### Sessions

Persistent memory layer for maintaining working context within an agent loop. Supports SQLite, Redis, and custom implementations. [VERIFIED]

### Human in the Loop

Built-in mechanisms for involving humans across agent runs, enabling approval workflows and oversight. [VERIFIED]

### Tracing

Built-in tracing for visualizing, debugging, and monitoring workflows. Integrates with OpenAI's evaluation, fine-tuning, and distillation tools. [VERIFIED]

### Realtime Agents

Build powerful voice agents with automatic interruption detection, context management, guardrails, and more. [VERIFIED]

## Design Principles

1. **Minimal Abstractions**: Few primitives to learn, maximum expressiveness
2. **Customizable**: Works out of the box, but every component can be overridden
3. **Provider-Agnostic**: Supports OpenAI and 100+ other LLM providers
4. **Production-Ready**: Evolved from experimental Swarm to supported SDK
5. **Traceable**: Built-in observability for debugging and monitoring

## Package Structure

```
agents/
├── Agent          # Core agent class
├── Runner         # Execution engine
├── function_tool  # Decorator for function tools
├── handoff        # Handoff configuration
├── guardrail      # Guardrail definitions
├── tracing        # Tracing utilities
└── voice          # Realtime/voice agents
```

## Comparison with Swarm

The Agents SDK is the production-ready evolution of OpenAI's experimental Swarm project:

| Aspect | Swarm (Experimental) | Agents SDK (Production) |
|--------|---------------------|------------------------|
| Status | Archived | Actively maintained |
| Support | Community only | Official OpenAI support |
| Features | Basic agents, handoffs | Full tooling, tracing, guardrails |
| Voice | Not supported | Full realtime support |
| MCP | Not supported | Native integration |

## Related Topics

- `_INFO_OASDKP-IN02_QUICKSTART.md` [OASDKP-IN02] - Getting started guide
- `_INFO_OASDKP-IN04_AGENTS.md` [OASDKP-IN04] - Detailed agent configuration
- `_INFO_OASDKP-IN05_RUNNER.md` [OASDKP-IN05] - Running agents

## API Reference

### Classes

- **Agent**
  - Import: `from agents import Agent`
  - Purpose: Define an LLM with instructions and tools
  - Key params: `name`, `instructions`, `model`, `tools`, `handoffs`

- **Runner**
  - Import: `from agents import Runner`
  - Purpose: Execute agent workflows
  - Key methods: `run()`, `run_sync()`, `run_streamed()`

### Decorators

- **@function_tool**
  - Import: `from agents import function_tool`
  - Purpose: Convert Python function to agent tool

## Document History

**[2026-02-11 11:40]**
- Initial document created
- All core concepts documented with verification labels
