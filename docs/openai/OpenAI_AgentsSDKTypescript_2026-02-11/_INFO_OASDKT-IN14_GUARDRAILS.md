# INFO: Guardrails

**Doc ID**: OASDKT-IN14
**Goal**: Validate or transform agent input and output
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-DOCS-GUARD` - Guardrails documentation page

## Summary

Guardrails run alongside agents or block execution until complete, allowing checks and validations on user input or agent output. Common use case: run a lightweight model as a guardrail before invoking an expensive model - if the guardrail detects malicious usage, it triggers an error and stops the costly model. Two kinds of guardrails exist: Input guardrails run on initial user input, and Output guardrails run on final agent output. Guardrails can run in parallel with agent execution or block until complete. When a guardrail's `tripwireTriggered` is true, an `InputGuardrailTripwireTriggered` or `OutputGuardrailTripwireTriggered` error is thrown.

## Types of Guardrails

### Input Guardrails

Run on initial user input: [VERIFIED]

1. Guardrail receives same input passed to agent
2. Guardrail function executes, returns `GuardrailFunctionOutput` wrapped in `InputGuardrailResult`
3. If `tripwireTriggered` is true, `InputGuardrailTripwireTriggered` error is thrown

**Important:** Input guardrails only run if the agent is the first agent in the workflow. [VERIFIED]

### Output Guardrails

Run on final agent output: [VERIFIED]

1. Guardrail receives agent's final output
2. Guardrail function executes, returns result
3. If `tripwireTriggered` is true, `OutputGuardrailTripwireTriggered` error is thrown

### Tool Guardrails

Run on tool inputs/outputs. [VERIFIED]

## Execution Modes

Guardrails support different execution strategies: [VERIFIED]

- **Parallel** - Run alongside agent execution
- **Blocking** - Block execution until guardrail completes

## Tripwires

When a guardrail detects an issue, it triggers a tripwire: [VERIFIED]

```typescript
import { Agent, inputGuardrail, run } from '@openai/agents';
import { z } from 'zod';

const contentFilter = inputGuardrail({
  name: 'content_filter',
  async execute(context, input) {
    // Check for malicious content
    const isMalicious = await checkContent(input);
    
    return {
      tripwireTriggered: isMalicious,
      outputInfo: isMalicious ? 'Malicious content detected' : null,
    };
  },
});

const agent = new Agent({
  name: 'Protected Agent',
  instructions: 'You are a helpful assistant.',
  inputGuardrails: [contentFilter],
});

try {
  const result = await run(agent, userInput);
} catch (error) {
  if (error instanceof InputGuardrailTripwireTriggered) {
    console.log('Guardrail blocked this request');
  }
}
```

## Implementing a Guardrail

### Input Guardrail Example

```typescript
import { inputGuardrail } from '@openai/agents';

const profanityFilter = inputGuardrail({
  name: 'profanity_filter',
  async execute(context, input) {
    const hasProfanity = containsProfanity(input);
    
    return {
      tripwireTriggered: hasProfanity,
      outputInfo: hasProfanity ? 'Profanity detected' : null,
    };
  },
});
```

### Output Guardrail Example

```typescript
import { outputGuardrail } from '@openai/agents';

const sensitiveDataFilter = outputGuardrail({
  name: 'sensitive_data_filter',
  async execute(context, output) {
    const containsSensitive = checkForSensitiveData(output);
    
    return {
      tripwireTriggered: containsSensitive,
      outputInfo: containsSensitive ? 'Sensitive data in output' : null,
    };
  },
});
```

## Configuring Guardrails on Agents

```typescript
import { Agent } from '@openai/agents';

const agent = new Agent({
  name: 'Protected Agent',
  instructions: 'You are a helpful assistant.',
  inputGuardrails: [profanityFilter, contentFilter],
  outputGuardrails: [sensitiveDataFilter],
});
```

## Runner-Level Guardrails

Apply guardrails to all agents via Runner config: [VERIFIED]

```typescript
import { Runner } from '@openai/agents';

const runner = new Runner({
  inputGuardrails: [globalInputGuardrail],
  outputGuardrails: [globalOutputGuardrail],
});
```

## Limitations and Known Issues

- Input guardrails only run on first agent in workflow [VERIFIED]
- Guardrails configured per-agent may differ [VERIFIED]

## Gotchas and Quirks

- `tripwireTriggered: true` immediately throws exception [VERIFIED]
- Guardrails receive context object with runner info [VERIFIED]
- Different agents may need different guardrails [VERIFIED]

## Best Practices

- Use lightweight models for guardrails to minimize latency [VERIFIED]
- Return descriptive `outputInfo` for debugging [VERIFIED]
- Apply critical guardrails at Runner level for consistency [VERIFIED]
- Handle guardrail exceptions gracefully in application [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN04_AGENTS.md` [OASDKT-IN04] - Agent configuration
- `_INFO_OASDKT-IN27_ERRORS.md` [OASDKT-IN27] - Error handling

## API Reference

### Functions

- **inputGuardrail()**
  - Import: `import { inputGuardrail } from "@openai/agents"`
  - Parameters: `{ name, execute }`
  - Returns: Input guardrail definition

- **outputGuardrail()**
  - Import: `import { outputGuardrail } from "@openai/agents"`
  - Parameters: `{ name, execute }`
  - Returns: Output guardrail definition

### Interfaces

- **GuardrailFunctionOutput**
  - Properties: `tripwireTriggered`, `outputInfo`

- **InputGuardrailResult**
  - Wraps `GuardrailFunctionOutput` for input guardrails

### Exceptions

- **InputGuardrailTripwireTriggered**
  - Thrown when input guardrail tripwire activates

- **OutputGuardrailTripwireTriggered**
  - Thrown when output guardrail tripwire activates

## Document History

**[2026-02-11 19:50]**
- Initial document created
- Input and output guardrails documented
- Tripwire mechanics explained
