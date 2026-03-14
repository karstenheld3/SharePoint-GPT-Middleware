# INFO: External Tracing Processors

**Doc ID**: OASDKP-IN20
**Goal**: Document external tracing integrations
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-TRACING` - External processors

## Summary

The SDK supports external tracing processors for sending trace data to observability platforms beyond OpenAI's dashboard. Community-maintained integrations include Logfire (Pydantic), AgentOps, Braintrust, Scorecard, and Keywords AI. Custom processors can be implemented by subclassing `TracingProcessor`. Multiple processors can run simultaneously using `MultiTracingProcessor`. [VERIFIED]

## Available Integrations

### Logfire (Pydantic)

```python
from agents.tracing import set_tracing_processor
from agents_logfire import LogfireProcessor

processor = LogfireProcessor(
    api_key="your-logfire-key",
)
set_tracing_processor(processor)
```

### AgentOps

```python
from agents_agentops import AgentOpsProcessor

processor = AgentOpsProcessor(
    api_key="your-agentops-key",
)
set_tracing_processor(processor)
```

### Braintrust

```python
from agents_braintrust import BraintrustProcessor

processor = BraintrustProcessor(
    api_key="your-braintrust-key",
    project_name="my-agent-project",
)
set_tracing_processor(processor)
```

### Scorecard

```python
from agents_scorecard import ScorecardProcessor

processor = ScorecardProcessor(
    api_key="your-scorecard-key",
)
set_tracing_processor(processor)
```

### Keywords AI

```python
from agents_keywords import KeywordsProcessor

processor = KeywordsProcessor(
    api_key="your-keywords-key",
)
set_tracing_processor(processor)
```

## Multi-Processor Setup

Send to multiple destinations:

```python
from agents.tracing import (
    set_tracing_processor,
    MultiTracingProcessor,
    DefaultTracingProcessor,
)

processor = MultiTracingProcessor([
    DefaultTracingProcessor(),  # OpenAI dashboard
    LogfireProcessor(...),      # Logfire
    CustomProcessor(),          # Your system
])

set_tracing_processor(processor)
```

## Custom Processor

Implement your own processor:

```python
from agents.tracing import TracingProcessor

class CustomProcessor(TracingProcessor):
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
    
    def on_trace_start(self, trace):
        print(f"Trace started: {trace.trace_id}")
    
    def on_span_start(self, span):
        print(f"Span started: {span.name}")
    
    def on_span_end(self, span):
        print(f"Span ended: {span.name}")
        # Send to your observability system
        send_to_system(self.endpoint, span.to_dict())
    
    def on_trace_end(self, trace):
        print(f"Trace ended: {trace.trace_id}")
        # Final trace data
        send_to_system(self.endpoint, trace.to_dict())

set_tracing_processor(CustomProcessor("https://my-obs.example.com"))
```

## Processor Lifecycle

```
Runner.run() starts
    │
    ▼
on_trace_start(trace)
    │
    ├─► on_span_start(agent_span)
    │       │
    │       ├─► on_span_start(generation_span)
    │       │       │
    │       │       └─► on_span_end(generation_span)
    │       │
    │       ├─► on_span_start(function_span)
    │       │       │
    │       │       └─► on_span_end(function_span)
    │       │
    │       └─► on_span_end(agent_span)
    │
    └─► on_trace_end(trace)
```

## Trace Data Structure

```python
trace = {
    "trace_id": "trace_abc123...",
    "workflow_name": "Customer Service",
    "group_id": "session_xyz",
    "started_at": "2026-02-11T12:00:00Z",
    "ended_at": "2026-02-11T12:00:05Z",
    "metadata": {"user_id": "123"},
    "spans": [...],
}

span = {
    "span_id": "span_def456...",
    "trace_id": "trace_abc123...",
    "parent_id": "span_parent...",
    "name": "generation",
    "started_at": "2026-02-11T12:00:01Z",
    "ended_at": "2026-02-11T12:00:02Z",
    "span_data": {
        "type": "generation",
        "model": "gpt-5",
        "input_tokens": 150,
        "output_tokens": 50,
    },
}
```

## Best Practices

- Use MultiTracingProcessor for redundancy
- Filter sensitive data in custom processors
- Handle processor errors gracefully
- Consider async processing for performance

## Related Topics

- `_INFO_OASDKP-IN19_TRACING.md` [OASDKP-IN19] - Core tracing

## API Reference

### Classes

- **TracingProcessor**
  - Import: `from agents.tracing import TracingProcessor`
  - Methods: `on_trace_start`, `on_span_start`, `on_span_end`, `on_trace_end`

- **MultiTracingProcessor**
  - Import: `from agents.tracing import MultiTracingProcessor`

- **DefaultTracingProcessor**
  - Import: `from agents.tracing import DefaultTracingProcessor`

### Functions

- **set_tracing_processor()**
  - Import: `from agents.tracing import set_tracing_processor`

## Document History

**[2026-02-11 13:45]**
- Initial external tracing documentation created
