# INFO: Orchestrating Multiple Agents

**Doc ID**: OASDKT-IN13
**Goal**: Coordinate the flow between several agents
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-DOCS-MULTI` - Multi-agent orchestration documentation

## Summary

Orchestration refers to the flow of agents in your app - which agents run, in what order, and how they decide what happens next. Two main orchestration patterns exist: LLM-driven orchestration where the LLM plans, reasons, and decides what steps to take, and code-driven orchestration where your code determines agent flow. LLM orchestration is powerful for open-ended tasks; code orchestration provides determinism and predictability in speed, cost, and performance. Patterns can be mixed and matched based on use case.

## Orchestration Patterns

### 1. Orchestrating via LLM

Agent is an LLM equipped with instructions, tools, and handoffs. Given an open-ended task, the LLM autonomously plans how to tackle it. [VERIFIED]

**Example: Research Agent Tools:**
- Web search to find information online
- File search for proprietary data
- Computer use to take actions
- Code execution for data analysis
- Handoffs to specialized agents (planning, report writing)

**Best Practices for LLM Orchestration:**

1. **Invest in good prompts** - Make clear what tools are available, how to use them, and operational parameters [VERIFIED]

2. **Monitor and iterate** - See where things go wrong, iterate on prompts [VERIFIED]

3. **Allow introspection** - Run in a loop, let agent critique itself; provide error messages [VERIFIED]

4. **Use specialized agents** - Excel in one task rather than general purpose [VERIFIED]

5. **Invest in evals** - Train agents to improve at tasks [VERIFIED]

### 2. Orchestrating via Code

More deterministic and predictable for speed, cost, and performance. [VERIFIED]

**Common Patterns:**

- **Structured outputs** - Generate well-formed data to inspect with code. Classify task into categories, pick next agent based on category. [VERIFIED]

- **Chaining agents** - Transform output of one into input of next. Decompose tasks (research → outline → write → critique → improve). [VERIFIED]

- **Feedback loops** - Run task agent in while loop with evaluator agent until output passes criteria. [VERIFIED]

- **Parallelization** - Run multiple agents via `Promise.all` when tasks don't depend on each other. [VERIFIED]

## Implementation Examples

### LLM Orchestration with Handoffs

```typescript
import { Agent } from '@openai/agents';

const researchAgent = new Agent({
  name: 'Research Agent',
  instructions: 'Research the topic thoroughly.',
  tools: [webSearchTool, fileSearchTool],
});

const writerAgent = new Agent({
  name: 'Writer Agent',
  instructions: 'Write clear, engaging content.',
});

const triageAgent = Agent.create({
  name: 'Triage Agent',
  instructions: 'Route to appropriate specialist.',
  handoffs: [researchAgent, writerAgent],
});
```

### Code Orchestration with Chaining

```typescript
import { Agent, run } from '@openai/agents';

const researchAgent = new Agent({
  name: 'Researcher',
  instructions: 'Research the topic.',
});

const writerAgent = new Agent({
  name: 'Writer',
  instructions: 'Write based on the research.',
});

// Chain agents
const research = await run(researchAgent, 'Research AI trends');
const article = await run(writerAgent, research.finalOutput);
```

### Parallel Execution

```typescript
import { Agent, run } from '@openai/agents';

const [result1, result2, result3] = await Promise.all([
  run(agent1, 'Task 1'),
  run(agent2, 'Task 2'),
  run(agent3, 'Task 3'),
]);
```

### Feedback Loop

```typescript
import { Agent, run } from '@openai/agents';

let output = await run(taskAgent, input);
let approved = false;

while (!approved) {
  const evaluation = await run(evaluatorAgent, output.finalOutput);
  if (evaluation.finalOutput.includes('APPROVED')) {
    approved = true;
  } else {
    output = await run(taskAgent, `Improve: ${output.finalOutput}`);
  }
}
```

## Comparison

| Pattern | Use Case | Trade-off |
|---------|----------|-----------|
| LLM Orchestration | Open-ended tasks | Flexible but less predictable |
| Code Orchestration | Defined workflows | Deterministic but less adaptive |
| Hybrid | Complex apps | Best of both, more complex |

## Examples Repository

See `examples/agent-patterns` in GitHub repository. [VERIFIED]

## Limitations and Known Issues

- LLM orchestration can be unpredictable [VERIFIED]
- Code orchestration requires upfront workflow design [VERIFIED]

## Gotchas and Quirks

- Handoffs transfer control completely to target agent [VERIFIED]
- Use `Promise.all` for parallel execution, not sequential awaits [VERIFIED]
- Feedback loops need exit conditions to prevent infinite loops [VERIFIED]

## Best Practices

- Use specialized agents over general-purpose agents [VERIFIED]
- Combine patterns based on task requirements [VERIFIED]
- Monitor and iterate on LLM-orchestrated flows [VERIFIED]
- Use structured outputs for code-driven decisions [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN12_HANDOFFS.md` [OASDKT-IN12] - Handoff patterns
- `_INFO_OASDKT-IN10_TOOLS_AGENTSASTOOLS.md` [OASDKT-IN10] - Agents as tools
- `_INFO_OASDKT-IN28_EXAMPLES.md` [OASDKT-IN28] - Example patterns

## Document History

**[2026-02-11 20:30]**
- Initial document created
- LLM and code orchestration patterns documented
