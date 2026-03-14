# INFO: Tracing

**Doc ID**: OASDKP-IN19
**Goal**: Document built-in tracing capabilities for debugging and monitoring
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-TRACING` - Official tracing documentation

## Summary

The OpenAI Agents SDK includes built-in tracing that collects a comprehensive record of events during agent runs: LLM generations, tool calls, handoffs, guardrails, and custom events. Traces are sent to the OpenAI Traces dashboard for visualization, debugging, and monitoring in development and production. Tracing is enabled by default and can be disabled globally via environment variable or per-run via RunConfig. The system uses Traces (end-to-end operations) and Spans (individual operations with timing). Custom tracing processors allow sending data to external observability platforms like Logfire, AgentOps, or Braintrust. [VERIFIED]

## Traces and Spans

### Traces

Represent a single end-to-end operation of a workflow:

- **workflow_name**: Logical workflow or app name (e.g., "Customer service")
- **trace_id**: Unique ID, format `trace_<32_alphanumeric>`
- **group_id**: Optional, links related traces (e.g., chat thread)
- **disabled**: If True, trace not recorded
- **metadata**: Optional metadata dict

### Spans

Represent operations with start and end time:

- **started_at / ended_at**: Timestamps
- **trace_id**: Parent trace ID
- **parent_id**: Parent span ID (for nesting)
- **span_data**: Operation-specific data (AgentSpanData, GenerationSpanData, etc.)

## Default Tracing

The SDK automatically traces: [VERIFIED]

```
Runner.run() / run_sync() / run_streamed()
└── trace()
    ├── agent_span()           # Each agent invocation
    │   ├── generation_span()  # LLM calls
    │   ├── function_span()    # Tool calls
    │   ├── guardrail_span()   # Guardrail checks
    │   └── handoff_span()     # Agent handoffs
    ├── transcription_span()   # Audio input (STT)
    ├── speech_span()          # Audio output (TTS)
    └── speech_group_span()    # Related audio spans
```

## Configuring Traces

### Via RunConfig

```python
from agents import Agent, Runner
from agents.run import RunConfig

agent = Agent(name="Assistant", instructions="...")

result = await Runner.run(
    agent,
    "Hello",
    run_config=RunConfig(
        workflow_name="Customer Support",
        trace_id="trace_abc123def456ghi789jkl012mno",
        group_id="conversation_xyz",
    ),
)
```

### Via Environment Variable

```bash
# Disable tracing globally
export OPENAI_AGENTS_DISABLE_TRACING=1
```

### Via RunConfig (Per-Run)

```python
config = RunConfig(tracing_disabled=True)
result = await Runner.run(agent, input, run_config=config)
```

## Creating Custom Traces

### Manual Trace Context

```python
from agents.tracing import trace

with trace(
    workflow_name="My Custom Workflow",
    trace_id="trace_custom123...",
    metadata={"user_id": "123", "session": "abc"},
):
    # All agent runs inside this block share the trace
    result1 = await Runner.run(agent1, input1)
    result2 = await Runner.run(agent2, input2)
```

### Higher Level Traces

Group multiple runs under a single trace:

```python
from agents.tracing import trace

async def process_order(order_id: str):
    with trace(workflow_name="Order Processing", group_id=order_id):
        # Validate
        await Runner.run(validation_agent, order_data)
        # Process
        await Runner.run(processing_agent, order_data)
        # Confirm
        await Runner.run(confirmation_agent, order_data)
```

## Creating Custom Spans

```python
from agents.tracing import custom_span

async def my_operation():
    with custom_span(name="External API Call"):
        # Your code here
        response = await call_external_api()
        return response
```

## Sensitive Data

Control what data is included in traces:

```python
from agents.run import RunConfig

config = RunConfig(
    trace_include_sensitive_data=False,  # Exclude sensitive fields
)
```

## Viewing Traces

Access the OpenAI Traces dashboard:
1. Go to https://platform.openai.com/traces
2. Filter by workflow_name, trace_id, or group_id
3. Visualize agent flow, timing, and outputs
4. Debug issues and optimize performance

## Custom Tracing Processors

Send traces to external observability platforms:

```python
from agents.tracing import TracingProcessor, set_tracing_processor

class MyProcessor(TracingProcessor):
    def on_trace_start(self, trace):
        print(f"Trace started: {trace.trace_id}")
    
    def on_span_start(self, span):
        print(f"Span started: {span.name}")
    
    def on_span_end(self, span):
        print(f"Span ended: {span.name}")
    
    def on_trace_end(self, trace):
        print(f"Trace ended: {trace.trace_id}")

# Set custom processor
set_tracing_processor(MyProcessor())
```

### Multi-Processor

Send to multiple destinations:

```python
from agents.tracing import MultiTracingProcessor

processor = MultiTracingProcessor([
    DefaultTracingProcessor(),  # OpenAI dashboard
    LogfireProcessor(),          # Logfire
    CustomProcessor(),           # Your system
])

set_tracing_processor(processor)
```

## Tracing with Non-OpenAI Models

When using non-OpenAI models, tracing still works but data goes to your configured processor:

```python
from agents import Agent, Runner
from agents.models import LiteLLMModel

agent = Agent(
    name="Assistant",
    model=LiteLLMModel(model="anthropic/claude-3-opus"),
)

# Tracing captures all events, processed by your configured processor
result = await Runner.run(agent, "Hello")
```

## External Tracing Processors

Community-maintained processors: [VERIFIED]

- **Logfire** - Pydantic's observability platform
- **AgentOps** - Agent monitoring and analytics
- **Braintrust** - Evaluation and monitoring
- **Scorecard** - AI evaluation platform
- **Keywords AI** - LLM monitoring

See SDK documentation for integration guides.

## Notes

- **Zero Data Retention (ZDR)**: Tracing unavailable for ZDR organizations
- **Performance**: Tracing adds minimal overhead
- **Storage**: OpenAI retains trace data per your data retention settings

## Limitations

- ZDR organizations cannot use tracing
- Custom processors must handle their own error handling
- Large traces may be truncated

## Best Practices

- Use descriptive `workflow_name` values
- Set `group_id` for conversation threading
- Use custom spans for external operations
- Disable tracing for sensitive operations if needed
- Monitor trace data for debugging and optimization

## Related Topics

- `_INFO_OASDKP-IN20_TRACING_EXTERNAL.md` [OASDKP-IN20] - External processors
- `_INFO_OASDKP-IN05_RUNNER.md` [OASDKP-IN05] - RunConfig options

## API Reference

### Functions

- **trace()**
  - Import: `from agents.tracing import trace`
  - Context manager for custom traces

- **custom_span()**
  - Import: `from agents.tracing import custom_span`
  - Context manager for custom spans

- **set_tracing_processor()**
  - Import: `from agents.tracing import set_tracing_processor`
  - Set custom tracing processor

### Classes

- **TracingProcessor**
  - Import: `from agents.tracing import TracingProcessor`
  - Base class for custom processors

- **MultiTracingProcessor**
  - Import: `from agents.tracing import MultiTracingProcessor`
  - Combine multiple processors

### Span Types

- `agent_span()` - Agent execution
- `generation_span()` - LLM generation
- `function_span()` - Tool/function call
- `guardrail_span()` - Guardrail check
- `handoff_span()` - Agent handoff
- `transcription_span()` - Speech-to-text
- `speech_span()` - Text-to-speech

## Document History

**[2026-02-11 12:20]**
- Initial document created
- Complete tracing documentation
