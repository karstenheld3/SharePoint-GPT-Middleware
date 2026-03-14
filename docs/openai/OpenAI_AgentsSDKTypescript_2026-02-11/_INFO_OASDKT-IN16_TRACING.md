# INFO: Tracing

**Doc ID**: OASDKT-IN16
**Goal**: Debug and monitor agent workflows with built-in tracing
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-DOCS-TRACE` - Tracing documentation

## Summary

The Agents SDK includes built-in tracing that collects a comprehensive record of events during agent runs: LLM generations, tool calls, handoffs, guardrails, and custom events. Using the OpenAI Traces dashboard, you can debug, visualize, and monitor workflows during development and production. Tracing is enabled by default but can be disabled globally via `OPENAI_AGENTS_DISABLE_TRACING=1` environment variable or per-run via `RunConfig.tracingDisabled`. Traces represent end-to-end operations composed of Spans. The SDK traces the entire run, agent execution, LLM generations, tool calls, guardrails, and handoffs automatically.

## Traces and Spans

### Traces

Traces represent a single end-to-end operation of a workflow: [VERIFIED]

- **workflow_name** - Logical workflow or app name (e.g., "Code generation")
- **trace_id** - Unique ID (format: `trace_<32_alphanumeric>`)
- **group_id** - Optional, links multiple traces from same conversation
- **disabled** - If true, trace not recorded
- **metadata** - Optional metadata

### Spans

Spans represent operations with start and end times: [VERIFIED]

- **started_at** / **ended_at** - Timestamps
- **trace_id** - Parent trace
- **parent_id** - Parent span (if any)
- **span_data** - Information about the span (AgentSpanData, GenerationSpanData, etc.)

## Default Tracing

The SDK automatically traces: [VERIFIED]

- **Trace** - Entire `run()` or `Runner.run()`
- **AgentSpan** - Each agent execution
- **GenerationSpan** - LLM generations
- **FunctionSpan** - Function tool calls
- **GuardrailSpan** - Guardrail execution
- **HandoffSpan** - Handoff operations

Default trace name is "Agent workflow". Configure via `RunConfig.workflowName`. [VERIFIED]

## Enabling/Disabling Tracing

### Globally Disable

```bash
export OPENAI_AGENTS_DISABLE_TRACING=1
```

### Per-Run Disable

```typescript
const runner = new Runner({
  tracingDisabled: true,
});
```

**Note:** Organizations with Zero Data Retention (ZDR) policy cannot use tracing. [VERIFIED]

## Viewing Traces

Navigate to: https://platform.openai.com/traces [VERIFIED]

## RunConfig Tracing Options

- **tracingDisabled** - `boolean` - Disable tracing
- **traceIncludeSensitiveData** - `boolean` - Include sensitive data
- **workflowName** - `string` - Custom workflow name
- **traceId** - Custom trace ID
- **groupId** - `string` - Link related traces
- **traceMetadata** - `Record<string, string>` - Custom metadata

## Custom Tracing

### Creating Custom Traces

Use `withTrace` for custom trace wrappers. [VERIFIED]

### Creating Custom Spans

Add custom spans to trace additional operations. [VERIFIED]

### Sensitive Data

Control whether sensitive data is included in traces via `traceIncludeSensitiveData`. [VERIFIED]

## Custom Tracing Processors

Set up custom trace processors to push traces to other destinations. [VERIFIED]

## Voice Agent Tracing

Realtime/voice agents also support tracing. [VERIFIED]

## Limitations and Known Issues

- ZDR policy organizations cannot use tracing [VERIFIED]
- Tracing adds some overhead (minimal) [VERIFIED]

## Gotchas and Quirks

- Tracing is ON by default [VERIFIED]
- trace_id must match format `trace_<32_alphanumeric>` [VERIFIED]
- group_id useful for linking conversation traces [VERIFIED]

## Best Practices

- Use descriptive workflow_name for each agent workflow [VERIFIED]
- Use group_id to link traces from same conversation [VERIFIED]
- Disable traceIncludeSensitiveData in production if needed [VERIFIED]
- Review traces during development for debugging [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN05_RUNNER.md` [OASDKT-IN05] - Running agents
- `_INFO_OASDKT-IN25_CONFIG.md` [OASDKT-IN25] - SDK configuration

## API Reference

### RunConfig Tracing Properties

- **tracingDisabled** - Disable tracing
- **traceIncludeSensitiveData** - Include sensitive data
- **workflowName** - Workflow name
- **traceId** - Custom trace ID
- **groupId** - Group ID
- **traceMetadata** - Metadata

### Span Types

- **AgentSpan** - Agent execution
- **GenerationSpan** - LLM generation
- **FunctionSpan** - Tool call
- **GuardrailSpan** - Guardrail
- **HandoffSpan** - Handoff

## Document History

**[2026-02-11 20:20]**
- Initial document created
- Tracing concepts and configuration documented
