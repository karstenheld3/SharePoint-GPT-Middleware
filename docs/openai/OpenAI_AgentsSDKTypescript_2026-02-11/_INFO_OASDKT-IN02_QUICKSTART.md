# INFO: Quickstart Guide

**Doc ID**: OASDKT-IN02
**Goal**: Step-by-step guide to build first agent with tools and handoffs
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-DOCS-QUICK` - Quickstart documentation page

## Summary

The quickstart guide walks through creating a multi-agent homework tutoring system in TypeScript. It covers project setup, creating a basic agent, running agents, adding tools with Zod validation, creating specialized agents (Math Tutor, History Tutor), defining handoffs between agents, and viewing traces in the OpenAI Dashboard. The guide demonstrates the core SDK patterns: Agent creation, the run() function, tool definition with the tool() helper, and multi-agent orchestration via handoffs. By the end, developers have a working triage agent that routes homework questions to appropriate specialist agents.

## Project Setup

### Initialize Project

```bash
mkdir my_project
cd my_project
npm init -y
npm pkg set type=module
npm install @openai/agents zod
```

### Set API Key

```bash
export OPENAI_API_KEY=sk-...
```

## Create Your First Agent

### Basic Agent Definition

```typescript
import { Agent, run } from '@openai/agents';

const agent = new Agent({
  name: 'Assistant',
  instructions: 'You are a helpful assistant',
});
```

**Agent Parameters:**
- **name** - Identifier for the agent
- **instructions** - System prompt defining agent behavior

## Run Your First Agent

### Using the run() Function

```typescript
async function main() {
  const result = await run(agent, 'Hello, how are you?');
  console.log(result.finalOutput);
}

main().catch(console.error);
```

**Key Points:**
- `run()` returns a Promise with the result [VERIFIED]
- `result.finalOutput` contains the agent's response [VERIFIED]
- The agent loop continues until final output is produced [VERIFIED]

## Give Your Agent Tools

### Defining Tools with Zod

```typescript
import { z } from 'zod';
import { Agent, run, tool } from '@openai/agents';

const getWeatherTool = tool({
  name: 'get_weather',
  description: 'Get the weather for a given city',
  parameters: z.object({
    city: z.string(),
  }),
  execute: async (input) => {
    return `The weather in ${input.city} is sunny`;
  },
});
```

### Agent with Tools

```typescript
const agent = new Agent({
  name: 'Data agent',
  instructions: 'You are a data agent',
  tools: [getWeatherTool],
});

async function main() {
  const result = await run(agent, 'What is the weather in Tokyo?');
  console.log(result.finalOutput);
}

main().catch(console.error);
```

**Tool Definition:**
- **name** - Tool identifier for LLM
- **description** - Explains when to use the tool
- **parameters** - Zod schema for input validation
- **execute** - Async function that performs the tool action

## Add Multiple Agents

### Specialized Agents

```typescript
const historyTutorAgent = new Agent({
  name: 'History Tutor',
  instructions:
    'You provide assistance with historical queries. Explain important events and context clearly.',
});

const mathTutorAgent = new Agent({
  name: 'Math Tutor',
  instructions:
    'You provide help with math problems. Explain your reasoning at each step and include examples',
});
```

**Best Practice:** Define focused instructions for each specialized agent [VERIFIED]

## Define Handoffs

### Triage Agent with Handoffs

```typescript
// Using Agent.create ensures type safety for the final output
const triageAgent = Agent.create({
  name: 'Triage Agent',
  instructions:
    "You determine which agent to use based on the user's homework question",
  handoffs: [historyTutorAgent, mathTutorAgent],
});
```

**Key Points:**
- Use `Agent.create()` instead of `new Agent()` for typed handoff outputs [VERIFIED]
- `handoffs` array lists agents that can receive delegation [VERIFIED]
- Triage agent automatically routes to appropriate specialist [VERIFIED]

## Run the Agent Orchestration

### Complete Example

```typescript
import { Agent, run } from '@openai/agents';

const historyTutorAgent = new Agent({
  name: 'History Tutor',
  instructions:
    'You provide assistance with historical queries. Explain important events and context clearly.',
});

const mathTutorAgent = new Agent({
  name: 'Math Tutor',
  instructions:
    'You provide help with math problems. Explain your reasoning at each step and include examples',
});

const triageAgent = new Agent({
  name: 'Triage Agent',
  instructions:
    "You determine which agent to use based on the user's homework question",
  handoffs: [historyTutorAgent, mathTutorAgent],
});

async function main() {
  const result = await run(triageAgent, 'What is the capital of France?');
  console.log(result.finalOutput);
}

main().catch((err) => console.error(err));
```

### Checking Which Agent Responded

After the run, check `result.finalAgent` to see which agent produced the final output [VERIFIED]

## View Your Traces

### OpenAI Dashboard

The SDK automatically generates traces for agent runs. [VERIFIED]

Navigate to: https://platform.openai.com/traces

**Trace Information:**
- Which agents executed
- What tools were called
- Handoff decisions made
- Input/output for each step

## Limitations and Known Issues

- Requires Node.js 22+ [VERIFIED]
- Must use ESM modules (`"type": "module"` in package.json) [VERIFIED]

## Gotchas and Quirks

- Use `Agent.create()` for typed handoffs, not `new Agent()` [VERIFIED]
- Tool parameters must be Zod schemas, not plain objects [VERIFIED]
- The `execute` function receives validated input matching the Zod schema [VERIFIED]

## Best Practices

- Start with a triage agent for multi-agent systems [VERIFIED]
- Keep agent instructions focused and specific [VERIFIED]
- Use tracing to debug agent behavior [VERIFIED]
- Handle errors with `.catch()` on the main function [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN01_INTRODUCTION.md` [OASDKT-IN01] - SDK overview
- `_INFO_OASDKT-IN04_AGENTS.md` [OASDKT-IN04] - Agent configuration details
- `_INFO_OASDKT-IN05_RUNNER.md` [OASDKT-IN05] - Running agents in depth
- `_INFO_OASDKT-IN09_TOOLS.md` [OASDKT-IN09] - Tool definition guide
- `_INFO_OASDKT-IN12_HANDOFFS.md` [OASDKT-IN12] - Handoff patterns

## API Reference

### Functions

- **run()**
  - Import: `import { run } from "@openai/agents"`
  - Parameters: `(agent, input, options?)`
  - Returns: `Promise<RunResult>`

- **tool()**
  - Import: `import { tool } from "@openai/agents"`
  - Parameters: `{ name, description, parameters, execute }`
  - Returns: Tool definition for agent

### Classes

- **Agent**
  - Import: `import { Agent } from "@openai/agents"`
  - Constructor: `new Agent({ name, instructions, tools?, handoffs? })`
  - Static: `Agent.create()` for typed outputs

## Document History

**[2026-02-11 19:10]**
- Initial document created from quickstart guide
- Complete multi-agent example documented
- Tool definition pattern included
