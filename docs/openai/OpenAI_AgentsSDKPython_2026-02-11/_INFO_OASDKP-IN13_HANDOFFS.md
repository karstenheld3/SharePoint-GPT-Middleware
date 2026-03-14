# INFO: Handoffs

**Doc ID**: OASDKP-IN13
**Goal**: Complete documentation of agent handoffs and delegation patterns
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-HANDOFFS` - Official handoffs documentation

## Summary

Handoffs allow an agent to delegate tasks to another agent, enabling modular multi-agent systems where specialized agents handle specific domains. When a handoff occurs, the delegated agent receives the conversation history and takes control. Handoffs are represented as tools to the LLM - a handoff to "Refund Agent" becomes a tool called `transfer_to_refund_agent`. The SDK provides the `handoff()` function for customizing handoff behavior, including input filters to modify what context is passed to the target agent. This pattern supports decentralized multi-agent architectures where peer agents collaborate. [VERIFIED]

## Basic Handoff

### Adding Handoffs to an Agent

```python
from agents import Agent

# Specialist agents
booking_agent = Agent(
    name="Booking Agent",
    instructions="Handle all booking-related requests"
)

refund_agent = Agent(
    name="Refund Agent",
    instructions="Process refund requests"
)

# Triage agent with handoffs
triage_agent = Agent(
    name="Triage Agent",
    instructions=(
        "Help users with their questions. "
        "If they ask about booking, hand off to the booking agent. "
        "If they ask about refunds, hand off to the refund agent."
    ),
    handoffs=[booking_agent, refund_agent],
)
```

### How Handoffs Work

1. Handoffs are exposed as tools to the LLM
2. Tool names are auto-generated: `transfer_to_<agent_name>`
3. When called, the target agent takes over
4. Conversation history is passed to the new agent

## Handoff Descriptions

Use `handoff_description` to hint when the model should use a handoff:

```python
billing_agent = Agent(
    name="Billing Agent",
    instructions="Handle billing questions",
    handoff_description="Use for payment issues, invoices, and billing disputes",
)

support_agent = Agent(
    name="Support Agent",
    handoffs=[billing_agent],
)
```

The `handoff_description` is appended to the default tool description. [VERIFIED]

## Custom Handoffs with handoff()

For more control, use the `handoff()` function:

```python
from agents import Agent, handoff

refund_agent = Agent(name="Refund Agent", instructions="...")

triage_agent = Agent(
    name="Triage Agent",
    handoffs=[
        handoff(
            agent=refund_agent,
            tool_name="escalate_to_refunds",
            tool_description="Transfer to refund specialist for complex cases",
        ),
    ],
)
```

### handoff() Parameters

- **agent** (required)
  - Type: `Agent`
  - Purpose: Target agent to hand off to

- **tool_name**
  - Type: `str`
  - Default: `transfer_to_<agent_name>`
  - Purpose: Custom tool name

- **tool_description**
  - Type: `str`
  - Default: Auto-generated
  - Purpose: Description shown to LLM

- **input_filter**
  - Type: `Callable`
  - Purpose: Transform input before handoff

## Handoff Inputs

Pass structured data to the target agent:

```python
from agents import Agent, handoff
from pydantic import BaseModel

class RefundRequest(BaseModel):
    order_id: str
    reason: str
    amount: float

refund_agent = Agent(name="Refund Agent", instructions="...")

triage_agent = Agent(
    name="Triage Agent",
    handoffs=[
        handoff(
            agent=refund_agent,
            input_type=RefundRequest,
        ),
    ],
)
```

The LLM will be prompted to provide the structured input when initiating the handoff. [VERIFIED]

## Input Filters

Transform the conversation history before passing to the target agent:

```python
from agents import Agent, handoff

def summarize_for_specialist(input_data):
    """Keep only the last few messages for the specialist."""
    messages = input_data.get("messages", [])
    return {
        "messages": messages[-5:],  # Only last 5 messages
        "summary": "Customer needs help with refund"
    }

refund_agent = Agent(name="Refund Agent", instructions="...")

triage_agent = Agent(
    name="Triage Agent",
    handoffs=[
        handoff(
            agent=refund_agent,
            input_filter=summarize_for_specialist,
        ),
    ],
)
```

### Filter Use Cases

- Summarize long conversations
- Remove sensitive information
- Add context from external sources
- Translate between formats

## Handoff vs Agents as Tools

| Aspect | Handoff | Agent as Tool |
|--------|---------|---------------|
| Control | Target takes over | Caller retains control |
| History | Full conversation passed | Scoped to tool call |
| Pattern | Decentralized | Centralized (manager) |
| Use Case | Specialist routing | Sub-task delegation |

```python
# Handoff: Target agent takes over conversation
triage_agent = Agent(
    handoffs=[specialist_agent],  # Transfers control
)

# Agent as Tool: Caller retains control
manager_agent = Agent(
    tools=[
        specialist_agent.as_tool(
            tool_name="consult_specialist",
            tool_description="Get specialist input"
        ),
    ],  # Manager keeps control
)
```

## Recommended Prompts

Structure handoff agents for clear routing:

```python
triage_agent = Agent(
    name="Customer Service",
    instructions="""
    You are the first point of contact for customers.
    
    Routing rules:
    - Billing questions → hand off to Billing Agent
    - Technical issues → hand off to Tech Support Agent
    - General questions → answer directly
    
    Always greet the customer first, then determine the appropriate action.
    """,
    handoffs=[billing_agent, tech_support_agent],
)
```

## Chained Handoffs

Agents can hand off to other agents that also have handoffs:

```python
# Level 1: Triage
triage = Agent(
    name="Triage",
    handoffs=[billing, technical],
)

# Level 2: Billing can escalate
billing = Agent(
    name="Billing",
    handoffs=[billing_supervisor],
)

# Level 3: Supervisor
billing_supervisor = Agent(
    name="Billing Supervisor",
    instructions="Handle escalated billing issues",
)
```

## Circular Handoff Prevention

Be careful with circular handoffs:

```python
# CAUTION: Could create infinite loop
agent_a = Agent(name="A", handoffs=[agent_b])
agent_b = Agent(name="B", handoffs=[agent_a])  # Circular!
```

Use clear instructions to prevent unnecessary back-and-forth.

## Limitations

- Handoff history can grow large for long conversations
- Input filters run synchronously
- Circular handoffs possible if not careful

## Best Practices

- Use descriptive `handoff_description` for clear routing
- Apply input filters to manage context size
- Design clear routing rules in instructions
- Avoid circular handoff patterns
- Use structured inputs for complex handoffs

## Related Topics

- `_INFO_OASDKP-IN14_MULTIAGENT.md` [OASDKP-IN14] - Multi-agent patterns
- `_INFO_OASDKP-IN12_TOOLS_AGENTSASTOOLS.md` [OASDKP-IN12] - Alternative pattern

## API Reference

### Functions

- **handoff()**
  - Import: `from agents import handoff`
  - Params: `agent`, `tool_name`, `tool_description`, `input_filter`, `input_type`

### Agent Properties

- **handoffs**
  - Type: `list[Agent | Handoff]`
  - Purpose: Define delegation targets

- **handoff_description**
  - Type: `str`
  - Purpose: Hint for when to use this agent as handoff target

## Document History

**[2026-02-11 12:10]**
- Initial document created
- Complete handoff patterns documented
