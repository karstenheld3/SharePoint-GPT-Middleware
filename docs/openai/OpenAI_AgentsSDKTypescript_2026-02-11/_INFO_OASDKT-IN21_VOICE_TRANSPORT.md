# INFO: Voice Transport Layers

**Doc ID**: OASDKT-IN21
**Goal**: Understand WebRTC and WebSocket transport options
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-VOICE-TRANS` - Realtime transport layer guide

## Summary

The SDK supports two transport layers for voice agents: WebRTC (primary for browsers) and WebSocket (for backend servers). WebRTC provides lower latency and automatic audio handling in browsers. WebSocket is used for Node.js servers or when WebRTC is unavailable. The SDK auto-detects the environment and selects the appropriate transport.

## Transport Types

### WebRTC (Browser)

- **Use case**: Browser-based voice applications
- **Latency**: Lower latency
- **Audio**: Automatic microphone/speaker configuration
- **Connection**: Peer-to-peer style

```typescript
// Browser environment - WebRTC used automatically
const session = new RealtimeSession(agent);
await session.connect({ apiKey: 'ek_...' });
```

### WebSocket (Backend)

- **Use case**: Node.js servers, serverless functions
- **Audio**: Manual audio stream handling required
- **Connection**: Standard WebSocket

```typescript
// Node.js environment - WebSocket used automatically
const session = new RealtimeSession(agent);
await session.connect({ apiKey: process.env.OPENAI_API_KEY });
```

## Explicit Transport Selection

Force a specific transport:

```typescript
import { RealtimeSession, WebRTCTransport } from '@openai/agents/realtime';

const session = new RealtimeSession(agent, {
  transport: 'webrtc', // or 'websocket'
});
```

## WebRTC Details

### Browser Audio Handling

WebRTC automatically:
- Requests microphone permission
- Configures audio input stream
- Plays agent audio through speakers
- Handles echo cancellation

### Ephemeral Keys

Browser connections require ephemeral keys (ek_...) for security:

```typescript
// Generate on backend
const response = await fetch('https://api.openai.com/v1/realtime/client_secrets', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${OPENAI_API_KEY}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    session: { type: 'realtime', model: 'gpt-realtime' },
  }),
});
const { value: ephemeralKey } = await response.json();
```

## WebSocket Details

### Server-Side Audio

For WebSocket, handle audio streams manually:

```typescript
const session = new RealtimeSession(agent);

session.on('audio', (audioData) => {
  // Process audio output
  playAudio(audioData);
});

// Send audio input
session.sendAudio(microphoneData);
```

## Comparison

| Feature | WebRTC | WebSocket |
|---------|--------|-----------|
| Environment | Browser | Node.js/Server |
| Latency | Lower | Higher |
| Audio handling | Automatic | Manual |
| Authentication | Ephemeral key | API key |

## Best Practices

- Use WebRTC for browser applications
- Use WebSocket for telephony integrations
- Generate ephemeral keys server-side
- Handle WebSocket audio streams carefully

## Related Topics

- `_INFO_OASDKT-IN18_VOICE_OVERVIEW.md` [OASDKT-IN18] - Voice overview
- `_INFO_OASDKT-IN19_VOICE_QUICKSTART.md` [OASDKT-IN19] - Voice quickstart

## Document History

**[2026-02-11 21:15]**
- Initial document created
- Transport layer options documented
