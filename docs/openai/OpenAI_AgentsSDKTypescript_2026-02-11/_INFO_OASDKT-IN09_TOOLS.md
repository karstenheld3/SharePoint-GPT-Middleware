# INFO: Tools

**Doc ID**: OASDKT-IN09
**Goal**: Define tools that give agents capabilities
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-DOCS-TOOLS` - Tools documentation page

## Summary

Tools let agents take actions - fetch data, call external APIs, execute code, or use a computer. The SDK supports six tool categories: (1) Hosted OpenAI tools running on OpenAI servers (web search, file search, code interpreter, image generation), (2) Local built-in tools running in your environment (computer use, shell, apply_patch), (3) Function tools wrapping any local function with JSON schema, (4) Agents as tools exposing an entire agent as callable, (5) MCP servers attaching Model Context Protocol servers, and (6) Experimental Codex tool for workspace-aware tasks. Function tools use Zod schemas for parameter validation and support options like needsApproval for human-in-the-loop flows.

## Tool Categories

### 1. Hosted Tools (OpenAI Responses API)

Built-in tools running on OpenAI servers: [VERIFIED]

```typescript
import { Agent, webSearchTool, fileSearchTool } from '@openai/agents';

const agent = new Agent({
  name: 'Travel assistant',
  tools: [webSearchTool(), fileSearchTool('VS_ID')],
});
```

**Available hosted tools:**
- **web_search** - Search the web
- **file_search** - Search files in vector store
- **code_interpreter** - Execute Python code
- **image_generation** - Generate images

### 2. Local Built-in Tools

Run in your environment, require implementations: [VERIFIED]

- **Computer use** - Implement `Computer` interface, pass to `computerTool()`
- **Shell** - Implement `Shell` interface, pass to `shellTool()`
- **Apply patch** - Implement `Editor` interface, pass to `applyPatchTool()`

```typescript
import {
  Agent,
  applyPatchTool,
  computerTool,
  shellTool,
  Computer,
  Editor,
  Shell,
} from '@openai/agents';

const computer: Computer = {
  environment: 'browser',
  dimensions: [1024, 768],
  screenshot: async () => '',
  click: async () => {},
  doubleClick: async () => {},
  scroll: async () => {},
  type: async () => {},
  wait: async () => {},
  move: async () => {},
  keypress: async () => {},
  drag: async () => {},
};

const shell: Shell = {
  run: async () => ({
    output: [
      { stdout: '', stderr: '', outcome: { type: 'exit', exitCode: 0 } },
    ],
  }),
};

const editor: Editor = {
  createFile: async () => ({ status: 'completed' }),
  updateFile: async () => ({ status: 'completed' }),
  deleteFile: async () => ({ status: 'completed' }),
};

const agent = new Agent({
  name: 'Local tools agent',
  tools: [
    computerTool({ computer }),
    shellTool({ shell, needsApproval: true }),
    applyPatchTool({ editor, needsApproval: true }),
  ],
});
```

### 3. Function Tools

Turn any function into a tool with `tool()` helper: [VERIFIED]

```typescript
import { tool } from '@openai/agents';
import { z } from 'zod';

const getWeatherTool = tool({
  name: 'get_weather',
  description: 'Get the weather for a given city',
  parameters: z.object({ city: z.string() }),
  async execute({ city }) {
    return `The weather in ${city} is sunny.`;
  },
});
```

**Options Reference:**

- **name** - Tool identifier (e.g., `'get_weather'`)
- **description** - What the tool does
- **parameters** - Zod schema or JSON schema
- **strict** - Enable strict mode (default: true)
- **execute** - `(args, context) => string | unknown | Promise<...>`
- **errorFunction** - `(context, error) => string`
- **needsApproval** - Require human approval
- **isEnabled** - Conditionally enable tool
- **inputGuardrails** - Input validation
- **outputGuardrails** - Output validation

### Non-Strict JSON Schema Tools

Disable strict mode for lenient parsing: [VERIFIED]

```typescript
import { tool } from '@openai/agents';

interface LooseToolInput {
  text: string;
}

const looseTool = tool({
  description: 'Echo input; be forgiving about typos',
  strict: false,
  parameters: {
    type: 'object',
    properties: { text: { type: 'string' } },
    required: ['text'],
    additionalProperties: true,
  },
  execute: async (input) => {
    if (typeof input !== 'object' || input === null || !('text' in input)) {
      return 'Invalid input. Please try again';
    }
    return (input as LooseToolInput).text;
  },
});
```

### 4. Agents as Tools

Expose an agent as a callable tool: [VERIFIED]

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

**How it works:**
1. Creates a function tool with single `input` parameter
2. Runs sub-agent with that input when called
3. Returns last message or output via `customOutputExtractor`

**Advanced options for `asTool()`:**
- **inputBuilder** - Maps structured args to nested agent input
- **includeInputSchema** - Includes JSON schema in nested run
- **resumeState** - Context reconciliation strategy
- **needsApproval** - Human-in-the-loop integration
- **isEnabled** - Conditional availability

### 5. MCP Servers

Attach Model Context Protocol servers. [VERIFIED]

See: `_INFO_OASDKT-IN11_MCP.md` [OASDKT-IN11]

### 6. Experimental: Codex Tool

Wrap Codex SDK as function tool for workspace-aware tasks. [VERIFIED]

## Limitations and Known Issues

- Hosted tools only work with OpenAIResponsesModel [VERIFIED]
- Local tools require you to implement interfaces [VERIFIED]
- Non-strict mode requires manual input validation [VERIFIED]

## Gotchas and Quirks

- Tool names should be descriptive (LLM uses them to decide) [VERIFIED]
- Zod schemas auto-generate JSON schema for strict mode [VERIFIED]
- `execute` receives `RunContext` as second argument [VERIFIED]

## Best Practices

- Use Zod schemas for type-safe tool parameters [VERIFIED]
- Add `needsApproval: true` for destructive operations [VERIFIED]
- Use `isEnabled` for conditional tool availability [VERIFIED]
- Provide clear descriptions for tool selection [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN10_TOOLS_AGENTSASTOOLS.md` [OASDKT-IN10] - Agents as tools detail
- `_INFO_OASDKT-IN11_MCP.md` [OASDKT-IN11] - MCP integration
- `_INFO_OASDKT-IN17_HUMANINLOOP.md` [OASDKT-IN17] - Human-in-the-loop

## API Reference

### Functions

- **tool()**
  - Import: `import { tool } from "@openai/agents"`
  - Returns: Tool definition

- **webSearchTool()**
  - Import: `import { webSearchTool } from "@openai/agents"`

- **fileSearchTool(vectorStoreId)**
  - Import: `import { fileSearchTool } from "@openai/agents"`

- **computerTool({ computer })**
  - Import: `import { computerTool } from "@openai/agents"`

- **shellTool({ shell, needsApproval? })**
  - Import: `import { shellTool } from "@openai/agents"`

- **applyPatchTool({ editor, needsApproval? })**
  - Import: `import { applyPatchTool } from "@openai/agents"`

### Interfaces

- **Computer** - GUI automation interface
- **Shell** - Command execution interface
- **Editor** - File editing interface

## Document History

**[2026-02-11 19:40]**
- Initial document created
- All six tool categories documented
