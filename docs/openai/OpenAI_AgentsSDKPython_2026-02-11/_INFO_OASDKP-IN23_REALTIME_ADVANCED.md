# INFO: Realtime Agents - Advanced

**Doc ID**: OASDKP-IN23
**Goal**: Document advanced realtime/voice agent features
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-REALTIME` - Advanced realtime features

## Summary

Advanced realtime features include SIP integration for telephony, direct model access for custom implementations, Azure OpenAI endpoint support, and fine-grained event handling. These features enable production voice applications with phone system integration, custom audio pipelines, and enterprise deployments. [VERIFIED]

## SIP Integration

Connect voice agents to phone systems:

```python
from agents.realtime import RealtimeRunner, SIPConfig

sip_config = SIPConfig(
    server="sip.example.com",
    username="agent",
    password="secret",
    port=5060,
)

runner = RealtimeRunner(
    starting_agent=voice_agent,
    sip_config=sip_config,
)

await runner.start()
```

### SIP Events

```python
@runner.on("call_started")
async def on_call(call_info):
    print(f"Incoming call from: {call_info.caller_id}")

@runner.on("call_ended")
async def on_hangup(call_info):
    print(f"Call ended: {call_info.duration}s")
```

## Event Handling

Fine-grained event control:

```python
from agents.realtime import RealtimeRunner

runner = RealtimeRunner(starting_agent=agent)

@runner.on("audio_input_started")
async def on_audio_start():
    print("User started speaking")

@runner.on("audio_input_ended")
async def on_audio_end():
    print("User stopped speaking")

@runner.on("transcription")
async def on_transcript(text):
    print(f"Transcribed: {text}")
    # Can modify or filter here

@runner.on("response_started")
async def on_response_start():
    print("Agent starting response")

@runner.on("response_delta")
async def on_delta(text):
    print(f"Speaking: {text}")

@runner.on("response_ended")
async def on_response_end():
    print("Agent finished response")

@runner.on("interrupted")
async def on_interrupt():
    print("User interrupted agent")
```

## Direct Model Access

Bypass agent abstraction for custom implementations:

```python
from agents.realtime import RealtimeClient

client = RealtimeClient(
    model="gpt-realtime",
    api_key="your-key",
)

await client.connect()

# Send audio directly
await client.send_audio(audio_bytes)

# Receive events
async for event in client.events():
    if event.type == "transcript":
        print(event.text)
    elif event.type == "audio":
        play_audio(event.audio_data)

await client.disconnect()
```

## Azure OpenAI Endpoint

Use Azure-hosted realtime models:

```python
from agents.realtime import RealtimeAgent, RealtimeRunner, RealtimeConfig

config = RealtimeConfig(
    azure_endpoint="https://your-resource.openai.azure.com",
    azure_deployment="your-realtime-deployment",
    api_key="your-azure-key",
    api_version="2024-10-01-preview",
)

agent = RealtimeAgent(
    name="Azure Voice Agent",
    instructions="Help users via voice",
)

runner = RealtimeRunner(
    starting_agent=agent,
    config=config,
)
```

### Azure Endpoint Format

```
https://{resource-name}.openai.azure.com/openai/realtime?api-version={version}&deployment={deployment-name}
```

## Custom Audio Pipeline

Process audio before/after:

```python
from agents.realtime import RealtimeRunner, AudioProcessor

class NoiseReducer(AudioProcessor):
    def process_input(self, audio: bytes) -> bytes:
        # Apply noise reduction
        return reduce_noise(audio)
    
    def process_output(self, audio: bytes) -> bytes:
        # Normalize volume
        return normalize_audio(audio)

runner = RealtimeRunner(
    starting_agent=agent,
    audio_processor=NoiseReducer(),
)
```

## Context Management

Manage conversation context in voice:

```python
from agents.realtime import RealtimeRunner

runner = RealtimeRunner(starting_agent=agent)

# Inject context mid-conversation
await runner.inject_context("User is a premium member")

# Clear context
await runner.clear_context()

# Get current context
context = await runner.get_context()
```

## Guardrails in Realtime

Real-time content filtering:

```python
from agents import InputGuardrail, GuardrailFunctionOutput
from agents.realtime import RealtimeAgent

async def realtime_filter(text: str) -> GuardrailFunctionOutput:
    # Fast check for voice
    is_inappropriate = quick_check(text)
    return GuardrailFunctionOutput(tripwire_triggered=is_inappropriate)

agent = RealtimeAgent(
    name="Safe Voice",
    input_guardrails=[
        InputGuardrail(
            guardrail_function=realtime_filter,
            # Use parallel mode for low latency
            execution_mode="parallel",
        ),
    ],
)
```

## Advanced Configuration

```python
from agents.realtime import RealtimeConfig

config = RealtimeConfig(
    model_settings={
        "model_name": "gpt-realtime",
        "temperature": 0.7,
        "max_response_tokens": 500,
    },
    audio_settings={
        "input_format": "pcm16",
        "output_format": "pcm16",
        "sample_rate": 24000,
        "channels": 1,
    },
    session_settings={
        "turn_detection": "server_vad",  # Voice activity detection
        "silence_duration_ms": 500,
        "threshold": 0.5,
    },
    connection_settings={
        "timeout_ms": 30000,
        "keepalive_ms": 5000,
    },
)
```

## Best Practices

- Use parallel guardrails for low latency
- Implement proper error handling for connection issues
- Test with various network conditions
- Monitor audio quality metrics
- Handle disconnections gracefully

## Related Topics

- `_INFO_OASDKP-IN22_REALTIME.md` [OASDKP-IN22] - Basic realtime

## API Reference

### Classes

- **RealtimeClient**
  - Import: `from agents.realtime import RealtimeClient`
  - Direct model access

- **SIPConfig**
  - Import: `from agents.realtime import SIPConfig`

- **AudioProcessor**
  - Import: `from agents.realtime import AudioProcessor`

## Document History

**[2026-02-11 13:50]**
- Initial advanced realtime documentation created
