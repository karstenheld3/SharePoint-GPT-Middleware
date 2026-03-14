# INFO: Multi-Agent Patterns

**Doc ID**: OASDKP-IN14
**Goal**: Document multi-agent system design patterns and architectures
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-AGENTS` - Agent patterns documentation
- `OASDKP-SC-OAIGUIDE-PDF` - Practical guide to building agents

## Summary

The OpenAI Agents SDK supports two primary multi-agent design patterns: Manager (agents as tools) where a central orchestrator invokes specialized sub-agents as tools while retaining control, and Handoffs where peer agents delegate control to specialists who take over the conversation. These patterns can be combined for complex architectures. The Manager pattern is centralized and keeps conversation flow controlled, while Handoffs enable decentralized, modular systems where each agent excels at a specific task. Choosing between them depends on whether you need central control (Manager) or specialized handling (Handoffs). [VERIFIED]

## Pattern 1: Manager (Agents as Tools)

A central manager/orchestrator invokes specialized sub-agents as tools and retains control of the conversation.

### Architecture

```
┌─────────────────────────────────────────┐
│         Customer-Facing Agent           │
│         (Manager/Orchestrator)          │
└───────────────┬─────────────────────────┘
                │ calls as tools
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ Booking │ │ Refund  │ │ Account │
│ Expert  │ │ Expert  │ │ Expert  │
└─────────┘ └─────────┘ └─────────┘
```

### Implementation

```python
from agents import Agent

# Specialist agents
booking_agent = Agent(
    name="Booking Expert",
    instructions="You are a booking specialist. Answer booking questions thoroughly.",
)

refund_agent = Agent(
    name="Refund Expert",
    instructions="You are a refund specialist. Process refund requests.",
)

account_agent = Agent(
    name="Account Expert",
    instructions="You are an account specialist. Help with account issues.",
)

# Manager agent with specialists as tools
customer_facing_agent = Agent(
    name="Customer Service Manager",
    instructions=(
        "You handle all direct customer communication. "
        "Use the appropriate expert tool when specialized knowledge is needed. "
        "Always synthesize expert responses into customer-friendly language."
    ),
    tools=[
        booking_agent.as_tool(
            tool_name="booking_expert",
            tool_description="Consult for booking questions and reservations.",
        ),
        refund_agent.as_tool(
            tool_name="refund_expert",
            tool_description="Consult for refund processing and policies.",
        ),
        account_agent.as_tool(
            tool_name="account_expert",
            tool_description="Consult for account settings and issues.",
        ),
    ],
)
```

### Characteristics

- **Control**: Manager retains full control
- **Context**: Sub-agents receive scoped context (tool call only)
- **Flow**: Manager synthesizes sub-agent responses
- **Best for**: Complex queries needing multiple specialists

## Pattern 2: Handoffs

Peer agents hand off control to a specialized agent that takes over the conversation.

### Architecture

```
┌─────────────────────────────────────────┐
│           Triage Agent                  │
│        (Entry Point)                    │
└───────────────┬─────────────────────────┘
                │ hands off to
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ Booking │ │ Refund  │ │ Account │
│ Agent   │ │ Agent   │ │ Agent   │
└─────────┘ └─────────┘ └─────────┘
    (takes over conversation)
```

### Implementation

```python
from agents import Agent

# Specialist agents (full capability)
booking_agent = Agent(
    name="Booking Agent",
    instructions=(
        "You are the booking department. "
        "Handle all booking requests from start to finish. "
        "You have full authority to make and modify reservations."
    ),
)

refund_agent = Agent(
    name="Refund Agent",
    instructions=(
        "You are the refund department. "
        "Process refund requests completely. "
        "You can approve refunds up to $500."
    ),
)

# Triage agent routes to specialists
triage_agent = Agent(
    name="Triage Agent",
    instructions=(
        "Greet customers and understand their needs. "
        "If they need booking help, hand off to booking agent. "
        "If they need refunds, hand off to refund agent. "
        "For general questions, answer directly."
    ),
    handoffs=[booking_agent, refund_agent],
)
```

### Characteristics

- **Control**: Specialist takes full control
- **Context**: Full conversation history passed
- **Flow**: Clean separation of concerns
- **Best for**: Distinct domains with specialized handling

## Choosing Between Patterns

| Aspect | Manager Pattern | Handoff Pattern |
|--------|-----------------|-----------------|
| Control | Centralized | Decentralized |
| Context | Scoped | Full history |
| Synthesis | Manager combines | Specialist delivers |
| Complexity | Higher coordination | Simpler routing |
| Use Case | Multi-faceted queries | Single-domain depth |

### When to Use Manager

- Query requires multiple specialist inputs
- Need to synthesize responses
- Want consistent customer voice
- Complex orchestration logic needed

### When to Use Handoffs

- Clear domain boundaries
- Specialists need full context
- Deep expertise required
- Simpler routing decisions

## Hybrid Patterns

Combine both patterns for complex systems:

### Hierarchical Handoffs

```python
# Level 1: Department routing
front_desk = Agent(
    name="Front Desk",
    handoffs=[sales_dept, support_dept, billing_dept],
)

# Level 2: Team routing within department
support_dept = Agent(
    name="Support Department",
    handoffs=[tech_support, product_support],
)

# Level 3: Individual specialist
tech_support = Agent(
    name="Tech Support",
    tools=[
        diagnostics_agent.as_tool(...),
        solutions_agent.as_tool(...),
    ],
)
```

### Manager with Escalation

```python
# Manager handles most cases
manager = Agent(
    name="Manager",
    tools=[specialist1.as_tool(...), specialist2.as_tool(...)],
    handoffs=[supervisor],  # Escalation path
)
```

## Triage Agent Pattern

Common pattern for entry-point routing:

```python
triage_agent = Agent(
    name="Customer Service",
    instructions="""
    You are the first point of contact. Your job is to:
    
    1. Greet the customer warmly
    2. Understand their primary need
    3. Route to the appropriate department:
       - Booking questions → Booking Agent
       - Refund requests → Refund Agent
       - Technical issues → Tech Support Agent
    4. For simple questions, answer directly
    
    Always confirm the routing before handing off:
    "I'll connect you with our [department] team who can help with that."
    """,
    handoffs=[booking_agent, refund_agent, tech_support_agent],
)
```

## Context Sharing Strategies

### With Handoffs (Full Context)

```python
# All messages automatically passed
triage = Agent(handoffs=[specialist])
# Specialist receives complete conversation
```

### With Agents as Tools (Scoped Context)

```python
# Only tool call context passed by default
manager = Agent(tools=[specialist.as_tool(...)])

# For more context, include in tool description or use structured input
specialist.as_tool(
    tool_description="Consult for refunds. Include order ID and issue description.",
)
```

### Using Input Filters

```python
from agents import handoff

def add_context(input_data):
    """Enrich handoff with additional context."""
    return {
        **input_data,
        "customer_tier": get_customer_tier(),
        "recent_orders": get_recent_orders(),
    }

triage = Agent(
    handoffs=[
        handoff(agent=specialist, input_filter=add_context),
    ],
)
```

## Best Practices

### Routing

- Use clear, mutually exclusive routing criteria
- Include fallback for unclassified requests
- Log routing decisions for analysis

### Agent Instructions

- Be explicit about each agent's scope
- Include examples of when to use tools/handoffs
- Define escalation criteria

### Testing

- Test each routing path
- Verify context is passed correctly
- Test edge cases and ambiguous requests

## Common Pitfalls

- **Circular handoffs**: Agent A → Agent B → Agent A
- **Lost context**: Not passing enough information to specialists
- **Unclear boundaries**: Overlapping agent responsibilities
- **Missing fallback**: No handling for unclassified requests

## Related Topics

- `_INFO_OASDKP-IN13_HANDOFFS.md` [OASDKP-IN13] - Handoff details
- `_INFO_OASDKP-IN12_TOOLS_AGENTSASTOOLS.md` [OASDKP-IN12] - Agents as tools
- `_INFO_OASDKP-IN04_AGENTS.md` [OASDKP-IN04] - Agent configuration

## Document History

**[2026-02-11 12:25]**
- Initial document created
- Manager and handoff patterns documented
- Hybrid patterns and best practices included
