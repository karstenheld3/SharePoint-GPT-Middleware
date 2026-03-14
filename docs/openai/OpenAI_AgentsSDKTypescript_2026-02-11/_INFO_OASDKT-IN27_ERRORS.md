# INFO: Error Handling

**Doc ID**: OASDKT-IN27
**Goal**: Handle errors and exceptions in agent workflows
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-GH-MAIN` - GitHub main documentation

## Summary

The SDK provides several error types for different failure scenarios. Key exceptions include MaxTurnsExceededError (when agent loop exceeds maxTurns limit), InputGuardrailTripwireTriggered and OutputGuardrailTripwireTriggered (when guardrails detect issues), and ModelBehaviorError for unexpected model responses. Tool errors can be formatted using toolErrorFormatter option. The SDK supports custom error handlers via the errorHandlers run option.

## Common Error Types

### MaxTurnsExceededError

Thrown when agent loop exceeds `maxTurns` limit (default: 10): [VERIFIED]

```typescript
import { Agent, run, MaxTurnsExceededError } from '@openai/agents';

try {
  const result = await run(agent, input, { maxTurns: 5 });
} catch (error) {
  if (error instanceof MaxTurnsExceededError) {
    console.log('Agent exceeded maximum turns');
  }
}
```

### InputGuardrailTripwireTriggered

Thrown when input guardrail detects an issue: [VERIFIED]

```typescript
import { InputGuardrailTripwireTriggered } from '@openai/agents';

try {
  const result = await run(agent, input);
} catch (error) {
  if (error instanceof InputGuardrailTripwireTriggered) {
    console.log('Input blocked by guardrail');
  }
}
```

### OutputGuardrailTripwireTriggered

Thrown when output guardrail detects an issue: [VERIFIED]

```typescript
import { OutputGuardrailTripwireTriggered } from '@openai/agents';

try {
  const result = await run(agent, input);
} catch (error) {
  if (error instanceof OutputGuardrailTripwireTriggered) {
    console.log('Output blocked by guardrail');
  }
}
```

## Tool Error Handling

### toolErrorFormatter

Format tool errors before returning to the model: [VERIFIED]

```typescript
const result = await run(agent, input, {
  toolErrorFormatter: (context, error) => {
    return `Tool error: ${error.message}. Please try a different approach.`;
  },
});
```

### Tool-Level Error Function

```typescript
const myTool = tool({
  name: 'risky_tool',
  parameters: z.object({ ... }),
  execute: async (args) => { ... },
  errorFunction: (context, error) => {
    return `Failed: ${error.message}`;
  },
});
```

## Custom Error Handlers

Pass error handlers via run options: [VERIFIED]

```typescript
const result = await run(agent, input, {
  errorHandlers: {
    onToolError: (error, toolCall) => {
      console.error(`Tool ${toolCall.name} failed:`, error);
    },
  },
});
```

## Error Recovery Patterns

### Retry Logic

```typescript
async function runWithRetry(agent, input, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await run(agent, input);
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      console.log(`Retry ${i + 1}/${maxRetries}`);
    }
  }
}
```

### Graceful Degradation

```typescript
try {
  const result = await run(agent, input);
  return result.finalOutput;
} catch (error) {
  if (error instanceof MaxTurnsExceededError) {
    return 'I need more time to complete this task.';
  }
  throw error;
}
```

## Limitations and Known Issues

- Some errors may not be recoverable [VERIFIED]
- Tool errors are passed back to model by default [VERIFIED]

## Gotchas and Quirks

- MaxTurnsExceededError thrown at limit, not before [VERIFIED]
- Guardrail errors stop execution immediately [VERIFIED]
- Tool errors can be formatted for model consumption [VERIFIED]

## Best Practices

- Always wrap run() in try-catch [VERIFIED]
- Use appropriate maxTurns for complex workflows [VERIFIED]
- Implement toolErrorFormatter for better model recovery [VERIFIED]
- Log errors for debugging and monitoring [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN14_GUARDRAILS.md` [OASDKT-IN14] - Guardrails
- `_INFO_OASDKT-IN05_RUNNER.md` [OASDKT-IN05] - Running agents

## API Reference

### Exceptions

- **MaxTurnsExceededError**
- **InputGuardrailTripwireTriggered**
- **OutputGuardrailTripwireTriggered**
- **ModelBehaviorError**

### Run Options

- **toolErrorFormatter** - `(context, error) => string`
- **errorHandlers** - Custom error handler functions

## Document History

**[2026-02-11 21:00]**
- Initial document created
- Error types and handling patterns documented
