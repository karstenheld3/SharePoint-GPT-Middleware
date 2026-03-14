# INFO: Human-in-the-Loop and Long-Running Agents

**Doc ID**: OASDKP-IN24
**Goal**: Document patterns for human oversight and persistent agent workflows
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-RUNNING` - Long-running agents documentation

## Summary

For agents that need human oversight or must persist across sessions, the SDK provides patterns for human-in-the-loop workflows and integrations with workflow orchestration systems. Approval gates allow requiring human confirmation before sensitive operations. For long-running agents that may span hours or days, integrations with Temporal, Restate, and DBOS provide durable execution with state persistence across failures. These patterns enable building production agents with proper oversight and reliability. [VERIFIED]

## Human-in-the-Loop Patterns

### Tool Approval Gates

Require approval before tool execution:

```python
from agents import Agent, function_tool

async def require_approval(
    tool_name: str,
    arguments: dict,
    context
) -> bool:
    """Prompt for human approval."""
    print(f"Agent wants to call: {tool_name}")
    print(f"Arguments: {arguments}")
    response = input("Approve? (y/n): ")
    return response.lower() == 'y'

@function_tool(approval_function=require_approval)
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email."""
    # Only executes if approved
    return "Email sent"

agent = Agent(
    name="Email Agent",
    tools=[send_email],
)
```

### Agents as Tools with Approval

```python
sensitive_agent = Agent(name="Sensitive Operations", ...)

async def manager_approval(tool_name, input_data, context):
    # Check with manager
    return await get_manager_decision(tool_name, input_data)

main_agent = Agent(
    tools=[
        sensitive_agent.as_tool(
            tool_name="sensitive_op",
            tool_description="Perform sensitive operations",
            approval_function=manager_approval,
        ),
    ],
)
```

### Output Review

Review agent output before delivery:

```python
async def reviewed_run(agent, input):
    result = await Runner.run(agent, input)
    
    print(f"Agent response: {result.final_output}")
    approved = input("Send to user? (y/n): ")
    
    if approved.lower() != 'y':
        # Re-run with feedback
        return await reviewed_run(
            agent,
            result.to_input_list() + [
                {"role": "user", "content": "Please revise your response"}
            ]
        )
    
    return result
```

## Long-Running Agent Patterns

### Challenge

Standard agent runs are ephemeral - if the process crashes, state is lost. Long-running agents need:

- State persistence across failures
- Resumable execution
- Timeout handling
- Human intervention points

### Temporal Integration

[Temporal](https://temporal.io/) provides durable workflow execution:

```python
from temporalio import workflow, activity
from agents import Agent, Runner

@activity.defn
async def run_agent_step(input: str) -> str:
    agent = Agent(name="Workflow Agent", ...)
    result = await Runner.run(agent, input)
    return result.final_output

@workflow.defn
class AgentWorkflow:
    @workflow.run
    async def run(self, initial_input: str):
        # Step 1: Initial analysis
        analysis = await workflow.execute_activity(
            run_agent_step,
            initial_input,
            start_to_close_timeout=timedelta(minutes=5),
        )
        
        # Step 2: Wait for human review
        approved = await workflow.wait_condition(
            lambda: self.human_approved
        )
        
        # Step 3: Execute approved action
        if approved:
            return await workflow.execute_activity(
                run_agent_step,
                f"Execute: {analysis}",
            )
```

### Restate Integration

[Restate](https://restate.dev/) provides stateful agents:

```python
from restate import Service, Context
from agents import Agent, Runner

service = Service("agent-service")

@service.handler()
async def process_request(ctx: Context, request: dict):
    agent = Agent(name="Stateful Agent", ...)
    
    # State is automatically persisted
    result = await Runner.run(agent, request["input"])
    
    # Wait for human approval (survives restarts)
    approved = await ctx.run("approval", wait_for_approval, result)
    
    if approved:
        return await ctx.run("execute", execute_action, result)
```

### DBOS Integration

[DBOS](https://dbos.dev/) provides database-backed durability:

```python
from dbos import DBOS
from agents import Agent, Runner

@DBOS.workflow()
def agent_workflow(input: str):
    agent = Agent(name="DBOS Agent", ...)
    
    # Automatically persisted to database
    result = DBOS.step(run_agent)(agent, input)
    
    # Wait for approval (stored in DB)
    if DBOS.step(wait_approval)(result):
        return DBOS.step(execute)(result)

@DBOS.step()
def run_agent(agent, input):
    return Runner.run_sync(agent, input).final_output
```

## Checkpoint Pattern

Manual checkpointing for resumable agents:

```python
import json
from pathlib import Path

class CheckpointedAgent:
    def __init__(self, agent, checkpoint_path):
        self.agent = agent
        self.path = Path(checkpoint_path)
        self.state = self._load()
    
    def _load(self):
        if self.path.exists():
            return json.loads(self.path.read_text())
        return {"history": [], "step": 0}
    
    def _save(self):
        self.path.write_text(json.dumps(self.state))
    
    async def run_step(self, input):
        result = await Runner.run(
            self.agent,
            self.state["history"] + [{"role": "user", "content": input}]
        )
        
        self.state["history"] = result.to_input_list()
        self.state["step"] += 1
        self._save()
        
        return result
```

## Best Practices

- Use approval gates for destructive operations
- Checkpoint state for long workflows
- Set reasonable timeouts
- Log all human decisions
- Design for graceful degradation

## Related Topics

- `_INFO_OASDKP-IN15_GUARDRAILS.md` [OASDKP-IN15] - Input/output validation
- `_INFO_OASDKP-IN19_TRACING.md` [OASDKP-IN19] - Workflow monitoring

## Document History

**[2026-02-11 13:30]**
- Initial human-in-the-loop documentation created
