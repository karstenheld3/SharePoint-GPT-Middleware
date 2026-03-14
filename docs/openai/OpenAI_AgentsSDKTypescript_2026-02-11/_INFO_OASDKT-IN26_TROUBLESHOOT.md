# INFO: Troubleshooting

**Doc ID**: OASDKT-IN26
**Goal**: Diagnose and resolve common issues
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-DOCS-TROUBLE` - Troubleshooting documentation

## Summary

This guide covers common issues and solutions when working with the Agents SDK. Topics include API key configuration, Zod version conflicts, tool execution errors, streaming issues, and debugging techniques.

## Common Issues

### API Key Not Found

**Symptom:** Error about missing API key

**Solution:**
```bash
export OPENAI_API_KEY=sk-...
```

Or programmatically:
```typescript
import { setDefaultOpenAIKey } from '@openai/agents';
setDefaultOpenAIKey(process.env.OPENAI_API_KEY!);
```

### Zod Version Conflict

**Symptom:** Schema validation errors or type mismatches

**Solution:** Ensure Zod v4 is installed:
```bash
npm install zod@^4.0.0
```

Check for duplicate Zod versions:
```bash
npm ls zod
```

### Tool Not Being Called

**Symptom:** Agent doesn't use available tools

**Solutions:**
- Check tool description is clear and relevant
- Verify tool name is descriptive
- Ensure parameters match expected input
- Add instructions mentioning when to use tools

### MaxTurnsExceededError

**Symptom:** Agent loop exceeds limit

**Solutions:**
- Increase maxTurns: `run(agent, input, { maxTurns: 20 })`
- Simplify task or break into steps
- Check for infinite tool loops

### Streaming Not Working

**Symptom:** No events received while streaming

**Solutions:**
- Ensure `stream: true` is passed
- Await or iterate the result
- Check for early error termination

```typescript
const result = await run(agent, input, { stream: true });
for await (const event of result) {
  console.log(event);
}
```

## Debugging Techniques

### Enable Debug Logging

```bash
export DEBUG=openai-agents*
```

### Disable Sensitive Data Logging

```bash
export OPENAI_AGENTS_DONT_LOG_MODEL_DATA=1
export OPENAI_AGENTS_DONT_LOG_TOOL_DATA=1
```

### Check Tracing

View traces at: https://platform.openai.com/traces

### Inspect Run Results

```typescript
const result = await run(agent, input);
console.log('Final agent:', result.lastAgent.name);
console.log('History length:', result.history.length);
console.log('New items:', result.newItems);
```

## Environment Issues

### Node.js Version

Requires Node.js 22 or later:
```bash
node --version
# Should be v22.x.x or higher
```

### TypeScript Configuration

Ensure tsconfig.json has appropriate settings:
```json
{
  "compilerOptions": {
    "moduleResolution": "bundler",
    "target": "ES2022"
  }
}
```

## Getting Help

- **GitHub Issues**: https://github.com/openai/openai-agents-js/issues
- **Documentation**: https://openai.github.io/openai-agents-js/
- **Examples**: https://github.com/openai/openai-agents-js/tree/main/examples

## Related Topics

- `_INFO_OASDKT-IN25_CONFIG.md` [OASDKT-IN25] - SDK configuration
- `_INFO_OASDKT-IN27_ERRORS.md` [OASDKT-IN27] - Error handling

## Document History

**[2026-02-11 21:35]**
- Initial document created
- Common issues and solutions documented
