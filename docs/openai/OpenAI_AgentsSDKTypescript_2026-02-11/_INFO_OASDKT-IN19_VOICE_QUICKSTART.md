# INFO: Voice Agents Quickstart

**Doc ID**: OASDKT-IN19
**Goal**: Build first realtime voice assistant in minutes
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-VOICE-QUICK` - Voice Agents Quickstart documentation

## Summary

This quickstart demonstrates building a browser-based voice agent. The process involves creating a project (Vite or Next.js), installing the SDK with Zod, generating an ephemeral client token for secure browser connections, creating a RealtimeAgent, establishing a RealtimeSession, and connecting. The SDK automatically configures microphone and speaker for audio I/O in browsers (WebRTC) and uses WebSocket for backend servers.

## Step-by-Step Guide

### 1. Create a Project

```bash
npm create vite@latest my-project -- --template vanilla-ts
```

Or use Next.js for full-stack applications.

### 2. Install the SDK

```bash
npm install @openai/agents zod
```

Alternative: Install `@openai/agents-realtime` for standalone browser package. [VERIFIED]

### 3. Generate Ephemeral Client Token

For browser applications, generate a secure ephemeral key: [VERIFIED]

```bash
export OPENAI_API_KEY="sk-proj-..."
curl -X POST https://api.openai.com/v1/realtime/client_secrets \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "session": {
      "type": "realtime",
      "model": "gpt-realtime"
    }
  }'
```

Response contains a `value` string starting with `ek_` prefix. This key is short-lived. [VERIFIED]

### 4. Create a RealtimeAgent

```typescript
import { RealtimeAgent } from '@openai/agents/realtime';

const agent = new RealtimeAgent({
  name: 'Assistant',
  instructions: 'You are a helpful assistant.',
});
```

Creating a RealtimeAgent is similar to creating a regular Agent. [VERIFIED]

### 5. Create a RealtimeSession

```typescript
import { RealtimeSession } from '@openai/agents/realtime';

const session = new RealtimeSession(agent, {
  model: 'gpt-realtime',
});
```

The session handles conversation, connection, audio processing, and interruptions. [VERIFIED]

### 6. Connect to the Session

```typescript
await session.connect({
  apiKey: 'ek_...',
});
```

- **Browser**: Uses WebRTC, auto-configures microphone and speaker [VERIFIED]
- **Backend (Node.js)**: Automatically uses WebSocket [VERIFIED]

### 7. Complete Example

```typescript
import { RealtimeAgent, RealtimeSession } from '@openai/agents/realtime';

const agent = new RealtimeAgent({
  name: 'Assistant',
  instructions: 'You are a helpful assistant.',
});

const session = new RealtimeSession(agent);

try {
  await session.connect({
    apiKey: 'ek_...',
  });
  console.log('You are connected!');
} catch (e) {
  console.error(e);
}
```

### 8. Run and Test

```bash
npm run dev
```

Navigate to the page, grant microphone access, and start talking. [VERIFIED]

## Connection Types

| Environment | Transport | Configuration |
|-------------|-----------|---------------|
| Browser | WebRTC | Auto microphone/speaker |
| Node.js | WebSocket | Manual audio handling |

## Ephemeral Keys

- Generated via `/v1/realtime/client_secrets` endpoint [VERIFIED]
- Prefix: `ek_` [VERIFIED]
- Short-lived, must regenerate periodically [VERIFIED]
- Should be generated on backend for production [VERIFIED]

## Limitations and Known Issues

- Ephemeral keys expire quickly [VERIFIED]
- Browser requires microphone permission [VERIFIED]
- Requires Realtime API access [VERIFIED]

## Gotchas and Quirks

- Import from `@openai/agents/realtime` not main package [VERIFIED]
- RealtimeSession takes agent as first argument [VERIFIED]
- Connection auto-detects environment (browser vs Node.js) [VERIFIED]

## Best Practices

- Generate ephemeral keys on backend, not frontend [VERIFIED]
- Handle connection errors gracefully [VERIFIED]
- Request microphone permission early in UX flow [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN18_VOICE_OVERVIEW.md` [OASDKT-IN18] - Voice overview
- `_INFO_OASDKT-IN20_VOICE_BUILD.md` [OASDKT-IN20] - Building voice agents

## API Reference

### Classes

- **RealtimeAgent**
  - Import: `import { RealtimeAgent } from "@openai/agents/realtime"`

- **RealtimeSession**
  - Import: `import { RealtimeSession } from "@openai/agents/realtime"`
  - Methods: `connect({ apiKey })`

## Document History

**[2026-02-11 20:50]**
- Initial document created
- Step-by-step quickstart documented
