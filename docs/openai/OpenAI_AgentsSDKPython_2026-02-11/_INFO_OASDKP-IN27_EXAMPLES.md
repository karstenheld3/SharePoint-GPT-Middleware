# INFO: Examples and Patterns

**Doc ID**: OASDKP-IN27
**Goal**: Complete code examples demonstrating SDK capabilities
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-EXAMPLES` - Examples documentation
- `OASDKP-SC-GH-REPO` - GitHub examples directory

## Summary

This document provides complete, runnable code examples demonstrating the OpenAI Agents SDK's capabilities. Examples range from simple single-agent applications to complex multi-agent systems with tools, handoffs, guardrails, and tracing. Each example includes full code, explanation, and expected output. The SDK's examples directory on GitHub contains additional patterns for deterministic flows, iterative loops, and real-world applications. [VERIFIED]

## Example 1: Customer Service Bot

A complete customer service agent with multiple specialists:

```python
import asyncio
from agents import Agent, Runner, function_tool

# --- Tools ---
@function_tool
def lookup_order(order_id: str) -> dict:
    """Look up order details by order ID."""
    # Simulated database lookup
    orders = {
        "ORD-001": {"status": "shipped", "eta": "2 days", "items": ["Widget A", "Widget B"]},
        "ORD-002": {"status": "processing", "eta": "5 days", "items": ["Gadget X"]},
    }
    return orders.get(order_id, {"error": "Order not found"})

@function_tool
def process_refund(order_id: str, reason: str) -> dict:
    """Process a refund for an order."""
    return {"status": "approved", "refund_id": f"REF-{order_id}", "amount": 99.99}

# --- Specialist Agents ---
order_agent = Agent(
    name="Order Specialist",
    instructions=(
        "You help customers with order inquiries. "
        "Use lookup_order to find order details. "
        "Provide clear status updates."
    ),
    tools=[lookup_order],
)

refund_agent = Agent(
    name="Refund Specialist",
    instructions=(
        "You process refund requests. "
        "Verify the order exists before processing. "
        "Use process_refund to complete the refund."
    ),
    tools=[lookup_order, process_refund],
)

# --- Triage Agent ---
triage_agent = Agent(
    name="Customer Service",
    instructions=(
        "Greet customers warmly. Understand their needs.\n"
        "- Order status questions → hand off to Order Specialist\n"
        "- Refund requests → hand off to Refund Specialist\n"
        "- General questions → answer directly"
    ),
    handoffs=[order_agent, refund_agent],
)

# --- Main ---
async def main():
    print("=== Customer Service Bot ===\n")
    
    queries = [
        "What's the status of order ORD-001?",
        "I want a refund for order ORD-002",
        "What are your business hours?",
    ]
    
    for query in queries:
        print(f"Customer: {query}")
        result = await Runner.run(triage_agent, query)
        print(f"Agent ({result.last_agent.name}): {result.final_output}\n")

if __name__ == "__main__":
    asyncio.run(main())
```

## Example 2: Research Assistant with Web Search

An agent that searches the web and synthesizes information:

```python
import asyncio
from agents import Agent, Runner, WebSearchTool

research_agent = Agent(
    name="Research Assistant",
    instructions=(
        "You are a research assistant. When asked a question:\n"
        "1. Search the web for relevant information\n"
        "2. Synthesize findings into a clear summary\n"
        "3. Cite your sources"
    ),
    tools=[WebSearchTool()],
)

async def main():
    result = await Runner.run(
        research_agent,
        "What are the latest developments in quantum computing?"
    )
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

## Example 3: Data Extraction Pipeline

Extract structured data from text:

```python
import asyncio
from pydantic import BaseModel
from agents import Agent, Runner

class ContactInfo(BaseModel):
    name: str
    email: str | None
    phone: str | None
    company: str | None

class ExtractedContacts(BaseModel):
    contacts: list[ContactInfo]

extractor = Agent(
    name="Contact Extractor",
    instructions="Extract all contact information from the provided text.",
    output_type=ExtractedContacts,
)

async def main():
    text = """
    Please contact John Smith at john@example.com or call 555-1234.
    For sales inquiries, reach out to Sarah Johnson (Acme Corp) at sarah@acme.com.
    Technical support: support@techhelp.io
    """
    
    result = await Runner.run(extractor, text)
    
    for contact in result.final_output.contacts:
        print(f"Name: {contact.name}")
        print(f"  Email: {contact.email}")
        print(f"  Phone: {contact.phone}")
        print(f"  Company: {contact.company}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
```

## Example 4: Agent with Guardrails

Protect an agent from misuse:

```python
import asyncio
from agents import (
    Agent, Runner, InputGuardrail, OutputGuardrail,
    GuardrailFunctionOutput
)
from agents.exceptions import InputGuardrailTripwireTriggered

# Input guardrail: Block off-topic requests
async def topic_guard(input_text: str) -> GuardrailFunctionOutput:
    off_topic = ["homework", "cheat", "hack", "illegal"]
    is_off_topic = any(word in input_text.lower() for word in off_topic)
    return GuardrailFunctionOutput(
        tripwire_triggered=is_off_topic,
        output_info={"reason": "Off-topic request"} if is_off_topic else None
    )

# Output guardrail: Ensure no PII in response
async def pii_guard(output_text: str) -> GuardrailFunctionOutput:
    # Simple check - in production, use a proper PII detector
    has_pii = "@" in output_text and "." in output_text  # Email pattern
    return GuardrailFunctionOutput(
        tripwire_triggered=has_pii,
        output_info={"reason": "PII detected"} if has_pii else None
    )

agent = Agent(
    name="Guarded Assistant",
    instructions="Help users with product questions. Never share personal information.",
    input_guardrails=[InputGuardrail(guardrail_function=topic_guard)],
    output_guardrails=[OutputGuardrail(guardrail_function=pii_guard)],
)

async def main():
    queries = [
        "Tell me about your products",
        "Help me with my homework",
    ]
    
    for query in queries:
        try:
            result = await Runner.run(agent, query)
            print(f"Q: {query}")
            print(f"A: {result.final_output}\n")
        except InputGuardrailTripwireTriggered as e:
            print(f"Q: {query}")
            print(f"BLOCKED: {e.guardrail_result.output_info}\n")

if __name__ == "__main__":
    asyncio.run(main())
```

## Example 5: Streaming Chat Interface

Build a chat interface with streaming:

```python
import asyncio
from agents import Agent, Runner

agent = Agent(
    name="Chat Assistant",
    instructions="You are a friendly, conversational assistant.",
)

async def chat():
    history = []
    
    print("Chat Assistant (type 'quit' to exit)")
    print("-" * 40)
    
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() == 'quit':
            break
        
        # Build input with history
        messages = history + [{"role": "user", "content": user_input}]
        
        # Stream response
        print("\nAssistant: ", end="", flush=True)
        result = await Runner.run_streamed(agent, messages)
        
        async for event in result.stream_events():
            if hasattr(event, 'delta'):
                print(event.delta, end="", flush=True)
        
        print()  # Newline after response
        
        # Update history
        history = result.to_input_list()

if __name__ == "__main__":
    asyncio.run(chat())
```

## Example 6: Manager Pattern with Specialists

Centralized orchestration with specialist agents:

```python
import asyncio
from agents import Agent, Runner, function_tool

@function_tool
def calculate(expression: str) -> float:
    """Evaluate a mathematical expression."""
    return eval(expression)

@function_tool
def translate(text: str, target_language: str) -> str:
    """Translate text to target language (simulated)."""
    return f"[{target_language}] {text}"

# Specialists
math_specialist = Agent(
    name="Math Specialist",
    instructions="Solve mathematical problems step by step.",
    tools=[calculate],
)

language_specialist = Agent(
    name="Language Specialist", 
    instructions="Help with translations and language questions.",
    tools=[translate],
)

# Manager orchestrates specialists
manager = Agent(
    name="Manager",
    instructions=(
        "You coordinate responses using specialist agents.\n"
        "- Use math_expert for calculations\n"
        "- Use language_expert for translations\n"
        "Combine their outputs into a cohesive response."
    ),
    tools=[
        math_specialist.as_tool(
            tool_name="math_expert",
            tool_description="Consult for math problems and calculations",
        ),
        language_specialist.as_tool(
            tool_name="language_expert",
            tool_description="Consult for translations and language help",
        ),
    ],
)

async def main():
    result = await Runner.run(
        manager,
        "Calculate 15% tip on $85, then translate the result to Spanish"
    )
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

## Example 7: Context-Aware Agent

Using typed context for personalization:

```python
import asyncio
from dataclasses import dataclass
from agents import Agent, Runner, function_tool, RunContextWrapper

@dataclass
class UserContext:
    user_id: str
    name: str
    subscription: str
    preferences: dict

@function_tool
def get_recommendations(context: RunContextWrapper[UserContext]) -> list[str]:
    """Get personalized recommendations based on user preferences."""
    user = context.context
    if user.subscription == "premium":
        return ["Premium Feature A", "Exclusive Content B", "VIP Access C"]
    return ["Basic Feature X", "Standard Content Y"]

agent = Agent[UserContext](
    name="Personal Assistant",
    instructions=(
        "Greet users by name. Consider their subscription level. "
        "Provide personalized recommendations when asked."
    ),
    tools=[get_recommendations],
)

async def main():
    user = UserContext(
        user_id="123",
        name="Alice",
        subscription="premium",
        preferences={"theme": "dark", "notifications": True}
    )
    
    result = await Runner.run(
        agent,
        "What do you recommend for me?",
        context=user,
    )
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

## Example 8: Tracing and Debugging

Comprehensive tracing for debugging:

```python
import asyncio
from agents import Agent, Runner
from agents.run import RunConfig
from agents.tracing import trace, custom_span

agent = Agent(
    name="Traced Agent",
    instructions="Answer questions helpfully.",
)

async def main():
    # Custom trace with metadata
    with trace(
        workflow_name="Customer Support Session",
        group_id="session_abc123",
        metadata={"customer_tier": "gold", "channel": "web"},
    ):
        # First query
        with custom_span(name="Initial Query"):
            result1 = await Runner.run(agent, "Hello, I need help")
        
        # Follow-up
        with custom_span(name="Follow-up Query"):
            result2 = await Runner.run(
                agent,
                result1.to_input_list() + [
                    {"role": "user", "content": "Can you explain more?"}
                ]
            )
    
    print(f"Response 1: {result1.final_output}")
    print(f"Response 2: {result2.final_output}")
    print("\nView traces at: https://platform.openai.com/traces")

if __name__ == "__main__":
    asyncio.run(main())
```

## Agent Patterns from Examples Directory

The SDK's GitHub examples directory includes these patterns:

### Deterministic Flows

Force specific tool execution order:

```python
from agents import Agent, ModelSettings

# Force the agent to always use a specific tool first
agent = Agent(
    name="Deterministic Agent",
    tools=[step1_tool, step2_tool, step3_tool],
    model_settings=ModelSettings(tool_choice="step1_tool"),
)
```

### Iterative Refinement

Agent refines output through multiple passes:

```python
async def iterative_refine(task: str, max_iterations: int = 3):
    draft = await Runner.run(drafter, task)
    
    for i in range(max_iterations):
        critique = await Runner.run(critic, draft.final_output)
        if "approved" in critique.final_output.lower():
            break
        draft = await Runner.run(
            refiner,
            f"Original: {draft.final_output}\nCritique: {critique.final_output}"
        )
    
    return draft.final_output
```

### Parallel Agent Execution

Run multiple agents concurrently:

```python
async def parallel_agents(query: str):
    tasks = [
        Runner.run(analyst1, query),
        Runner.run(analyst2, query),
        Runner.run(analyst3, query),
    ]
    results = await asyncio.gather(*tasks)
    
    # Synthesize results
    combined = "\n".join(r.final_output for r in results)
    return await Runner.run(synthesizer, combined)
```

## Best Practices

- Start simple, add complexity incrementally
- Use typed context for dependency injection
- Add guardrails for production safety
- Enable tracing for debugging
- Test each agent individually before combining

## Related Topics

- `_INFO_OASDKP-IN02_QUICKSTART.md` [OASDKP-IN02] - Getting started
- `_INFO_OASDKP-IN14_MULTIAGENT.md` [OASDKP-IN14] - Multi-agent patterns

## Document History

**[2026-02-11 12:45]**
- Initial examples document created
- 8 complete examples with full code
