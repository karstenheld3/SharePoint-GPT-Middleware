# INFO: Voice Agents Overview

**Doc ID**: OASDKT-IN18
**Goal**: Build realtime voice assistants using RealtimeAgent and RealtimeSession
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-VOICE-OVER` - Voice Agents documentation

## Summary

Voice Agents use OpenAI speech-to-speech models to provide realtime voice chat. These models support streaming audio, text, and tool calls, making them ideal for voice/phone customer support, mobile app experiences, and voice chat applications. The SDK provides a TypeScript client for the OpenAI Realtime API. By using speech-to-speech models, the system processes audio in realtime without needing to transcribe and reconvert text back to audio.

## Key Features

- **WebSocket or WebRTC connection** - Multiple transport options [VERIFIED]
- **Browser and backend support** - Works in both environments [VERIFIED]
- **Audio and interruption handling** - Built-in audio management [VERIFIED]
- **Multi-agent orchestration** - Through handoffs [VERIFIED]
- **Tool definition and calling** - Same tool patterns as text agents [VERIFIED]
- **Custom guardrails** - Monitor model output [VERIFIED]
- **Callbacks for streamed events** - React to real-time events [VERIFIED]
- **Component reuse** - Same components for text and voice agents [VERIFIED]

## Basic Usage

```typescript
import { RealtimeAgent, RealtimeSession } from '@openai/agents/realtime';

const agent = new RealtimeAgent({
  name: 'Voice Assistant',
  instructions: 'You are a helpful voice assistant.',
});

const session = new RealtimeSession(agent);

await session.connect({
  apiKey: '<client-api-key>',
});
```

## Use Cases

- Voice/phone customer support [VERIFIED]
- Mobile app voice experiences [VERIFIED]
- Voice chat applications [VERIFIED]
- Interactive voice response (IVR) systems

## Transport Options

### WebSocket

Standard WebSocket connection for server-side applications.

### WebRTC

Real-time communication for browser-based applications with lower latency.

## Browser Package

For browser-based voice agents, use the dedicated browser package:

```typescript
import { RealtimeAgent, RealtimeSession } from '@openai/agents/realtime';
```

## Limitations and Known Issues

- Requires OpenAI Realtime API access [VERIFIED]
- Speech-to-speech models have specific requirements [VERIFIED]

## Gotchas and Quirks

- Import from `@openai/agents/realtime` not main package [VERIFIED]
- Audio handling differs from text agents [VERIFIED]

## Best Practices

- Use WebRTC for browser applications (lower latency) [VERIFIED]
- Use WebSocket for server-side applications [VERIFIED]
- Reuse tool definitions from text agents where possible [VERIFIED]

## Related Topics

- `_INFO_OASDKT-IN19_VOICE_QUICKSTART.md` [OASDKT-IN19] - Voice quickstart
- `_INFO_OASDKT-IN09_TOOLS.md` [OASDKT-IN09] - Tool definitions

## API Reference

### Classes

- **RealtimeAgent**
  - Import: `import { RealtimeAgent } from "@openai/agents/realtime"`
  - Similar to Agent but for voice

- **RealtimeSession**
  - Import: `import { RealtimeSession } from "@openai/agents/realtime"`
  - Manages voice session lifecycle

## Document History

**[2026-02-11 20:40]**
- Initial document created
- Voice agent overview and features documented
