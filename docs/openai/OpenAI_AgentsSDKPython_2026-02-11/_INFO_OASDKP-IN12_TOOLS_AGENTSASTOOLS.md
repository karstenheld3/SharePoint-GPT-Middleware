# INFO: Agents as Tools

**Doc ID**: OASDKP-IN12
**Goal**: Document using agents as callable tools within other agents
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-TOOLS` - Agents as tools documentation

## Summary

Agents can be exposed as callable tools using the `as_tool()` method, enabling the Manager pattern where a central orchestrator invokes specialized sub-agents while retaining control of the conversation. Unlike handoffs where control transfers to the target agent, agents as tools return their output to the calling agent which then synthesizes the response. This pattern supports approval gates, structured input, custom output extraction, and conditional enabling. [VERIFIED]

## Basic Usage

```python
from agents import Agent

# Specialist agent
tax_expert = Agent(
    name="Tax Expert",
    instructions="You are a tax specialist. Provide detailed tax advice.",
)

# Manager uses specialist as tool
financial_advisor = Agent(
    name="Financial Advisor",
    instructions="Help clients with financial planning. Consult tax expert for tax questions.",
    tools=[
        tax_expert.as_tool(
            tool_name="consult_tax_expert",
            tool_description="Get expert tax advice for complex tax questions.",
        ),
    ],
)
```

## as_tool() Parameters

- **tool_name**
  - Type: `str`
  - Required: Yes
  - Purpose: Name shown to LLM for tool selection

- **tool_description**
  - Type: `str`
  - Required: Yes  
  - Purpose: Description of when to use this tool

- **input_type**
  - Type: `Type[BaseModel]`
  - Purpose: Structured input schema for the tool call

- **output_extractor**
  - Type: `Callable`
  - Purpose: Custom function to extract/transform output

- **approval_function**
  - Type: `Callable`
  - Purpose: Gate requiring approval before execution

## Customizing Tool-Agents

### With Description

```python
tools=[
    specialist.as_tool(
        tool_name="legal_review",
        tool_description=(
            "Request legal review of a document or contract. "
            "Provide the document text and specific concerns."
        ),
    ),
]
```

### Structured Input

```python
from pydantic import BaseModel

class TaxQuestion(BaseModel):
    income: float
    deductions: list[str]
    filing_status: str
    specific_question: str

tools=[
    tax_expert.as_tool(
        tool_name="tax_consultation",
        tool_description="Get tax advice with structured financial information.",
        input_type=TaxQuestion,
    ),
]
```

## Approval Gates

Require approval before tool-agent execution:

```python
async def require_manager_approval(
    tool_name: str,
    input_data: dict,
    context
) -> bool:
    """Check if manager approves this consultation."""
    # Implement approval logic
    if input_data.get("amount", 0) > 10000:
        return await prompt_for_approval(tool_name, input_data)
    return True  # Auto-approve small amounts

tools=[
    financial_agent.as_tool(
        tool_name="financial_decision",
        tool_description="Make financial decisions.",
        approval_function=require_manager_approval,
    ),
]
```

## Custom Output Extraction

Transform tool-agent output before returning:

```python
def extract_summary(result) -> str:
    """Extract just the summary from detailed output."""
    output = result.final_output
    # Parse and extract key points
    if "Summary:" in output:
        return output.split("Summary:")[1].strip()
    return output[:200] + "..."  # First 200 chars

tools=[
    detailed_analyst.as_tool(
        tool_name="detailed_analysis",
        tool_description="Get detailed analysis (summary returned).",
        output_extractor=extract_summary,
    ),
]
```

## Streaming Nested Agent Runs

Handle streaming from tool-agents:

```python
async def stream_nested_agents(result):
    async for event in result.stream_events():
        if hasattr(event, 'delta'):
            print(event.delta, end='')
        elif hasattr(event, 'nested_agent'):
            print(f"\n[Consulting {event.nested_agent.name}...]")
```

## Conditional Tool Enabling

Enable tools based on context:

```python
from agents import Agent, RunContextWrapper

def get_available_tools(context: RunContextWrapper):
    """Return tools based on user permissions."""
    tools = [basic_tool]
    
    if context.context.is_premium:
        tools.append(premium_agent.as_tool(...))
    
    if context.context.is_admin:
        tools.append(admin_agent.as_tool(...))
    
    return tools

# Dynamic tool list
agent = Agent(
    name="Adaptive Agent",
    tools=get_available_tools,  # Function, not list
)
```

## Agents as Tools vs Handoffs

| Aspect | Agents as Tools | Handoffs |
|--------|-----------------|----------|
| Control | Caller retains | Target takes over |
| Context | Scoped to call | Full history |
| Output | Returns to caller | Direct to user |
| Pattern | Centralized | Decentralized |
| Use Case | Consultation | Specialization |

## Multiple Tool-Agents

```python
manager = Agent(
    name="Project Manager",
    instructions="Coordinate project tasks using specialized teams.",
    tools=[
        dev_team.as_tool(
            tool_name="development",
            tool_description="Assign development tasks.",
        ),
        design_team.as_tool(
            tool_name="design",
            tool_description="Request design work.",
        ),
        qa_team.as_tool(
            tool_name="quality_assurance",
            tool_description="Request testing and QA.",
        ),
    ],
)
```

## Best Practices

- Use clear, descriptive tool names
- Provide detailed descriptions for when to use
- Use structured input for complex consultations
- Implement approval gates for sensitive operations
- Extract/summarize verbose outputs

## Related Topics

- `_INFO_OASDKP-IN14_MULTIAGENT.md` [OASDKP-IN14] - Multi-agent patterns
- `_INFO_OASDKP-IN13_HANDOFFS.md` [OASDKP-IN13] - Alternative pattern
- `_INFO_OASDKP-IN09_TOOLS_OVERVIEW.md` [OASDKP-IN09] - Tool categories

## API Reference

### Methods

- **Agent.as_tool()**
  - Returns: Tool object for use in `tools` list
  - Params: `tool_name`, `tool_description`, `input_type`, `output_extractor`, `approval_function`

## Document History

**[2026-02-11 13:05]**
- Initial agents as tools documentation created
