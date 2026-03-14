# INFO: Models

**Doc ID**: OASDKT-IN03
**Goal**: Configure language models for agents
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-DOCS-MODELS` - Models documentation page

## Summary

The OpenAI Agents SDK abstracts models behind two interfaces: Model (makes API requests) and ModelProvider (resolves model names to instances). The default model is gpt-4.1 for compatibility and low latency, though gpt-5.2 is recommended for higher quality when available. Models can be configured per-agent, per-runner, or via the OPENAI_DEFAULT_MODEL environment variable. GPT-5.x models support special modelSettings including reasoning effort and text verbosity. Non-GPT-5 models use generic settings. The SDK handles authentication via OPENAI_API_KEY environment variable and supports custom model providers for non-OpenAI models through the Vercel AI SDK adapter.

## Model Configuration

### Basic Usage

```typescript
import { Agent } from '@openai/agents';

const agent = new Agent({
  name: 'Creative writer',
  model: 'gpt-5.2',
});
```

### Model Interfaces

- **Model** - Knows how to make one request against a specific API [VERIFIED]
- **ModelProvider** - Resolves human-readable model names to Model instances [VERIFIED]

## Default Model

### Current Default

The default model is `gpt-4.1` for compatibility and low latency. [VERIFIED]

### Recommended Model

For higher quality, use `gpt-5.2` when available. [VERIFIED]

### Setting Default Model

**Environment Variable:**
```bash
export OPENAI_DEFAULT_MODEL=gpt-5.2
node my-awesome-agent.js
```

**Per-Runner:**
```typescript
import { Runner } from '@openai/agents';

const runner = new Runner({ model: 'gpt-4.1-mini' });
```

## GPT-5.x Models

### Model Settings

GPT-5.x models support special settings: [VERIFIED]

```typescript
import { Agent } from '@openai/agents';

const myAgent = new Agent({
  name: 'My Agent',
  instructions: "You're a helpful agent.",
  model: 'gpt-5.2',
  modelSettings: {
    reasoning: { effort: 'high' },
    text: { verbosity: 'low' },
  },
});
```

### Reasoning Effort

- **effort: 'high'** - Maximum reasoning capability
- **effort: 'none'** - Lower latency, recommended for interactive apps [VERIFIED]

### Model Variants

- **gpt-5.2** - Full capability model
- **gpt-4.1** - Default, good compatibility
- **gpt-4.1-mini** - Smaller, faster variant
- **gpt-5-nano** - Lightweight variant

## Non-GPT-5 Models

Non-GPT-5 models use generic modelSettings compatible with any model. [VERIFIED]

## Authentication

### OpenAI Provider

Set the API key via environment variable:

```bash
export OPENAI_API_KEY=sk-...
```

## Custom Model Providers

For non-OpenAI models, use the Vercel AI SDK adapter. [VERIFIED]

See: `_INFO_OASDKT-IN22_EXT_AISDK.md` [OASDKT-IN22]

## Limitations and Known Issues

- GPT-5.x modelSettings not supported on non-GPT-5 models [VERIFIED]
- Custom model providers require additional adapter setup [VERIFIED]

## Gotchas and Quirks

- Default model is gpt-4.1, not the latest GPT-5 [VERIFIED]
- Environment variable OPENAI_DEFAULT_MODEL overrides agent-level defaults [VERIFIED]

## Best Practices

- Use `gpt-5.2` with `reasoning.effort: 'none'` for low latency [VERIFIED]
- Set model explicitly on agents for predictable behavior [VERIFIED]
- Use Runner-level defaults for consistent model across agents [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN04_AGENTS.md` [OASDKT-IN04] - Agent configuration
- `_INFO_OASDKT-IN22_EXT_AISDK.md` [OASDKT-IN22] - AI SDK for non-OpenAI models

## API Reference

### Interfaces

- **Model**
  - Import: `import type { Model } from "@openai/agents"`
  - Purpose: Makes requests against specific API

- **ModelProvider**
  - Import: `import type { ModelProvider } from "@openai/agents"`
  - Purpose: Resolves model names to Model instances

### Configuration

- **modelSettings**
  - For GPT-5.x: `{ reasoning: { effort }, text: { verbosity } }`
  - For others: Generic settings

## Document History

**[2026-02-11 19:20]**
- Initial document created
- Model configuration and settings documented
