# INFO: Vercel AI SDK Extension

**Doc ID**: OASDKT-IN22
**Goal**: Use non-OpenAI models via Vercel AI SDK adapter
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-EXT-AISDK` - AI SDK extension documentation

## Summary

The Vercel AI SDK adapter allows using non-OpenAI models with the Agents SDK. This enables broader model support including Anthropic Claude, Google Gemini, and other providers supported by the Vercel AI SDK. The adapter wraps AI SDK models to implement the Agents SDK Model interface.

## Installation

```bash
npm install @openai/agents ai @ai-sdk/anthropic
```

## Basic Usage

```typescript
import { Agent, run } from '@openai/agents';
import { createAISDKModel } from '@openai/agents/extensions/ai-sdk';
import { anthropic } from '@ai-sdk/anthropic';

const model = createAISDKModel(anthropic('claude-3-5-sonnet-20241022'));

const agent = new Agent({
  name: 'Claude Agent',
  instructions: 'You are a helpful assistant.',
  model: model,
});

const result = await run(agent, 'Hello!');
console.log(result.finalOutput);
```

## Supported Providers

The AI SDK supports many providers:

- **Anthropic** - Claude models
- **Google** - Gemini models
- **Mistral** - Mistral models
- **Cohere** - Command models
- **Groq** - Fast inference
- **Fireworks** - Open models

## Provider Examples

### Anthropic Claude

```typescript
import { anthropic } from '@ai-sdk/anthropic';

const model = createAISDKModel(anthropic('claude-3-5-sonnet-20241022'));
```

### Google Gemini

```typescript
import { google } from '@ai-sdk/google';

const model = createAISDKModel(google('gemini-1.5-pro'));
```

## Runner-Level Model

Set default model at Runner level:

```typescript
import { Runner } from '@openai/agents';

const runner = new Runner({
  model: createAISDKModel(anthropic('claude-3-5-sonnet-20241022')),
});
```

## Limitations

- Not all features may be supported by all providers
- Tool calling support varies by model
- Streaming behavior may differ
- Structured outputs depend on provider support

## Best Practices

- Test thoroughly with chosen provider
- Check provider-specific limitations
- Use OpenAI for full feature support
- Fall back gracefully if features unavailable

## Related Topics

- `_INFO_OASDKT-IN03_MODELS.md` [OASDKT-IN03] - Model configuration
- `_INFO_OASDKT-IN09_TOOLS.md` [OASDKT-IN09] - Tools

## API Reference

### Functions

- **createAISDKModel(aiSdkModel)**
  - Import: `import { createAISDKModel } from "@openai/agents/extensions/ai-sdk"`
  - Returns: Model compatible with Agents SDK

## Document History

**[2026-02-11 21:20]**
- Initial document created
- AI SDK adapter usage documented
