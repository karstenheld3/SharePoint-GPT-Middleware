# INFO: Agents as Tools

**Doc ID**: OASDKT-IN10
**Goal**: Use agents as callable tools within other agents
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-DOCS-TOOLS` - Tools documentation (Agents as tools section)

## Summary

The SDK allows exposing an entire agent as a callable tool using `agent.asTool()`. This pattern enables a main agent to delegate specific tasks to specialized sub-agents without fully handing off the conversation. When the tool is called, the SDK creates a function tool with a single input parameter, runs the sub-agent with that input, and returns either the last message or output via customOutputExtractor. This differs from handoffs where control transfers completely to the target agent.

## Basic Usage

```typescript
import { Agent } from '@openai/agents';

const summarizer = new Agent({
  name: 'Summarizer',
  instructions: 'Generate a concise summary of the supplied text.',
});

const summarizerTool = summarizer.asTool({
  toolName: 'summarize_text',
  toolDescription: 'Generate a concise summary of the supplied text.',
});

const mainAgent = new Agent({
  name: 'Research assistant',
  tools: [summarizerTool],
});
```

## How It Works

1. Creates a function tool with single `input` parameter [VERIFIED]
2. Runs sub-agent with that input when tool is called [VERIFIED]
3. Returns last message or output via `customOutputExtractor` [VERIFIED]

## asTool() Options

- **toolName** - Name for the tool [VERIFIED]
- **toolDescription** - Description for the tool [VERIFIED]
- **customOutputExtractor** - Custom function to extract output
- **inputBuilder** - Maps structured args to nested agent input [VERIFIED]
- **includeInputSchema** - Includes JSON schema in nested run [VERIFIED]
- **resumeState** - Context reconciliation strategy [VERIFIED]
- **needsApproval** - Require human approval [VERIFIED]
- **isEnabled** - Conditional availability [VERIFIED]
- **runConfig** - Runner configuration for sub-agent
- **runOptions** - Run options for sub-agent

## Comparison: Agents as Tools vs Handoffs

| Aspect | Agents as Tools | Handoffs |
|--------|-----------------|----------|
| Control | Main agent retains control | Target agent takes over |
| Conversation | Main agent continues | Target agent owns conversation |
| Output | Returns to main agent | Final output from target |
| Use case | Subtask delegation | Domain specialization |

## Advanced: Structured Input

```typescript
import { Agent, tool } from '@openai/agents';
import { z } from 'zod';

const analysisAgent = new Agent({
  name: 'Analysis Agent',
  instructions: 'Analyze the provided data.',
});

const analysisTool = analysisAgent.asTool({
  toolName: 'analyze_data',
  toolDescription: 'Analyze data and return insights.',
  inputBuilder: (args) => `Analyze: ${JSON.stringify(args)}`,
  includeInputSchema: true,
});
```

## Streaming Events from Agent Tools

Agent tools emit streaming events during execution. [VERIFIED]

## Limitations and Known Issues

- Sub-agent runs with default runner settings unless overridden [VERIFIED]
- Output extraction may need customization for complex outputs [VERIFIED]

## Gotchas and Quirks

- Different from handoffs - main agent retains control [VERIFIED]
- Sub-agent result returns as tool output [VERIFIED]
- Can pass runConfig and runOptions for customization [VERIFIED]

## Best Practices

- Use for subtask delegation where main agent needs result [VERIFIED]
- Provide clear toolName and toolDescription [VERIFIED]
- Use customOutputExtractor for structured outputs [VERIFIED]
- Consider handoffs for domain specialization instead [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN09_TOOLS.md` [OASDKT-IN09] - Tools overview
- `_INFO_OASDKT-IN12_HANDOFFS.md` [OASDKT-IN12] - Handoff patterns
- `_INFO_OASDKT-IN13_MULTIAGENT.md` [OASDKT-IN13] - Multi-agent orchestration

## API Reference

### Agent Methods

- **asTool(options)**
  - Returns: Tool definition wrapping the agent
  - Options: `{ toolName, toolDescription, customOutputExtractor?, ... }`

## Document History

**[2026-02-11 20:55]**
- Initial document created
- Agent as tool pattern documented
