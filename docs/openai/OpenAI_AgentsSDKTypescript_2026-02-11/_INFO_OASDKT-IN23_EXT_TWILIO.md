# INFO: Twilio Extension

**Doc ID**: OASDKT-IN23
**Goal**: Integrate voice agents with Twilio for phone calls
**SDK Version**: @openai/agents 0.4.6

**Sources:**
- `OASDKT-SC-EXT-TWILIO` - Twilio extension documentation

## Summary

The Twilio extension enables voice agents to handle phone calls via Twilio. This allows building IVR systems, customer support hotlines, and phone-based AI assistants. The extension bridges Twilio's Media Streams with the Agents SDK RealtimeSession.

## Installation

```bash
npm install @openai/agents twilio
```

## Basic Setup

```typescript
import { RealtimeAgent, RealtimeSession } from '@openai/agents/realtime';
import { TwilioAdapter } from '@openai/agents/extensions/twilio';

const agent = new RealtimeAgent({
  name: 'Phone Agent',
  instructions: 'You are a helpful phone assistant.',
});

const adapter = new TwilioAdapter({
  agent,
  twilioAccountSid: process.env.TWILIO_ACCOUNT_SID,
  twilioAuthToken: process.env.TWILIO_AUTH_TOKEN,
});
```

## Twilio Webhook Handler

Handle incoming calls:

```typescript
import express from 'express';

const app = express();

app.post('/incoming-call', (req, res) => {
  const twiml = adapter.generateTwiML({
    streamUrl: 'wss://your-server.com/media-stream',
  });
  res.type('text/xml').send(twiml);
});

app.ws('/media-stream', (ws, req) => {
  adapter.handleMediaStream(ws);
});
```

## Configuration Options

- **twilioAccountSid** - Twilio account SID
- **twilioAuthToken** - Twilio auth token
- **agent** - RealtimeAgent instance
- **voiceSettings** - Voice configuration

## Call Flow

1. Twilio receives incoming call
2. Webhook returns TwiML pointing to media stream
3. Twilio connects WebSocket to your server
4. Adapter bridges audio to RealtimeSession
5. Agent responds via audio stream

## Voice Settings

```typescript
const adapter = new TwilioAdapter({
  agent,
  voiceSettings: {
    voice: 'alloy',
    speed: 1.0,
  },
});
```

## Best Practices

- Handle connection errors gracefully
- Implement call transfer for complex scenarios
- Log calls for quality assurance
- Test with Twilio's test credentials first

## Related Topics

- `_INFO_OASDKT-IN18_VOICE_OVERVIEW.md` [OASDKT-IN18] - Voice overview
- `_INFO_OASDKT-IN21_VOICE_TRANSPORT.md` [OASDKT-IN21] - Transport layers

## Document History

**[2026-02-11 21:25]**
- Initial document created
- Twilio integration documented
