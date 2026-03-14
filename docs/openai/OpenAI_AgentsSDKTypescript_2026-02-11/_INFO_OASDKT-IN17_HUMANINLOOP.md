# INFO: Human in the Loop

**Doc ID**: OASDKT-IN17
**Goal**: Pause and resume agent runs based on human intervention
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-DOCS-HITL` - Human-in-the-loop documentation

## Summary

The SDK provides built-in human-in-the-loop support to pause and resume agent runs based on human intervention. The primary use case is asking for approval for sensitive tool executions. Tools can require approval by setting `needsApproval` to `true` or an async function. When approval is needed, the run interrupts and returns an `interruptions` array. You can approve or reject via `result.state.approve(interruption)` or `result.state.reject(interruption)`, then resume by passing `result.state` back to `run()`.

## Approval Requests

### Defining Tools That Require Approval

Set `needsApproval` to `true` or an async function: [VERIFIED]

```typescript
import { tool } from '@openai/agents';
import z from 'zod';

// Always requires approval
const sensitiveTool = tool({
  name: 'cancelOrder',
  description: 'Cancel order',
  parameters: z.object({
    orderId: z.number(),
  }),
  needsApproval: true,
  execute: async ({ orderId }) => {
    // Cancel order
    return `Order ${orderId} cancelled`;
  },
});

// Conditionally requires approval
const sendEmail = tool({
  name: 'sendEmail',
  description: 'Send an email',
  parameters: z.object({
    to: z.string(),
    subject: z.string(),
    body: z.string(),
  }),
  needsApproval: async (_context, { subject }) => {
    // Check if the email might be spam
    return subject.includes('spam');
  },
  execute: async ({ to, subject, body }) => {
    // Send email
    return `Email sent to ${to}`;
  },
});
```

## Approval Flow

1. Agent decides to call a tool, checks if `needsApproval` returns true [VERIFIED]
2. If approval required, checks if already granted or rejected [VERIFIED]
3. If approval/rejection missing, triggers tool approval request [VERIFIED]
4. Agent gathers all approval requests and interrupts execution [VERIFIED]
5. Result contains `interruptions` array with pending steps [VERIFIED]
6. `ToolApprovalItem` with `type: "tool_approval_item"` appears when confirmation needed [VERIFIED]
7. Call `result.state.approve(interruption)` or `result.state.reject(interruption)` [VERIFIED]
8. Resume by passing `result.state` to `runner.run(agent, state)` [VERIFIED]
9. Flow restarts from step 1 [VERIFIED]

## Example Implementation

```typescript
import { Agent, run, tool } from '@openai/agents';
import z from 'zod';

const deleteTool = tool({
  name: 'deleteFile',
  description: 'Delete a file',
  parameters: z.object({ path: z.string() }),
  needsApproval: true,
  execute: async ({ path }) => {
    // Delete file
    return `Deleted ${path}`;
  },
});

const agent = new Agent({
  name: 'File Manager',
  instructions: 'Manage files for the user.',
  tools: [deleteTool],
});

async function main() {
  let result = await run(agent, 'Delete temp.txt');

  // Check for interruptions
  while (result.interruptions && result.interruptions.length > 0) {
    for (const interruption of result.interruptions) {
      if (interruption.type === 'tool_approval_item') {
        console.log(`Approve deletion of ${interruption.toolCall.arguments}?`);
        
        // Get user approval (simplified)
        const approved = await getUserApproval();
        
        if (approved) {
          result.state.approve(interruption);
        } else {
          result.state.reject(interruption);
        }
      }
    }
    
    // Resume execution
    result = await run(agent, result.state);
  }

  console.log(result.finalOutput);
}
```

## Dealing with Longer Approval Times

For approvals that take extended time (human review): [VERIFIED]

### Versioning Pending Tasks

Store and version pending tasks for later resumption. [VERIFIED]

### Serializing State

The `result.state` can be serialized and stored for later resumption. [VERIFIED]

## Limitations and Known Issues

- Approval flow pauses the entire run [VERIFIED]
- Long-running approvals require state persistence [VERIFIED]

## Gotchas and Quirks

- `needsApproval` can be boolean or async function [VERIFIED]
- Must pass original agent to resumed run [VERIFIED]
- State must be passed back to resume, not just input [VERIFIED]

## Best Practices

- Use `needsApproval: true` for destructive operations [VERIFIED]
- Use async function for conditional approval [VERIFIED]
- Provide clear context to users for approval decisions [VERIFIED]
- Implement proper state persistence for long approvals [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN09_TOOLS.md` [OASDKT-IN09] - Tool definitions
- `_INFO_OASDKT-IN07_RESULTS.md` [OASDKT-IN07] - Run results
- `_INFO_OASDKT-IN15_SESSIONS.md` [OASDKT-IN15] - Sessions for persistence

## API Reference

### Tool Options

- **needsApproval** - `boolean | ((context, args) => Promise<boolean>)`

### Result Properties

- **interruptions** - Array of pending approval items
- **state** - RunState for resumption

### RunState Methods

- **approve(interruption)** - Approve a tool call
- **reject(interruption)** - Reject a tool call

### Types

- **ToolApprovalItem**
  - type: `"tool_approval_item"`
  - toolCall: Tool call details

## Document History

**[2026-02-11 20:35]**
- Initial document created
- Approval flow and implementation documented
