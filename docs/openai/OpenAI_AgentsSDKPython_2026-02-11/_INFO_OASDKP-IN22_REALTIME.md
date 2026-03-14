# INFO: Realtime Voice Agents

**Doc ID**: OASDKP-IN22
**Goal**: Document realtime/voice agent capabilities
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-REALTIME` - Realtime agents documentation

## Summary

Realtime agents enable conversational voice applications with natural speech interaction, processing audio and text inputs in real time. They maintain persistent connections with OpenAI's Realtime API for low-latency voice conversations with automatic interruption handling. The SDK provides `RealtimeRunner` and `RealtimeAgent` classes specifically for voice use cases, supporting function tools, hosted MCP tools, handoffs, guardrails, and customizable audio settings. Voice agents require the `[voice]` extra during installation. [VERIFIED]

## Installation

```bash
pip install 'openai-agents[voice]'
```

## Basic Voice Agent

```python
from agents.realtime import RealtimeAgent, RealtimeRunner

# Create voice agent
agent = RealtimeAgent(
    name="Voice Assistant",
    instructions="You are a helpful voice assistant. Keep responses brief and conversational.",
    voice="alloy",  # Voice selection
)

# Run realtime session
runner = RealtimeRunner(starting_agent=agent)
await runner.start()
```

## RealtimeAgent Configuration

```python
from agents.realtime import RealtimeAgent

agent = RealtimeAgent(
    name="Customer Service Voice",
    instructions="Help customers with their orders. Be friendly and concise.",
    model="gpt-realtime",
    voice="nova",
    tools=[lookup_order, check_status],
    handoffs=[specialist_agent],
)
```

### Configuration Options

- **name**: Agent identifier
- **instructions**: Voice-optimized system prompt
- **model**: Realtime model (e.g., `gpt-realtime`)
- **voice**: Voice selection (alloy, echo, fable, onyx, nova, shimmer)
- **tools**: Function tools available to the agent
- **handoffs**: Other agents for delegation

## Voice Options

Available voices:

- **alloy** - Neutral, balanced
- **echo** - Warm, conversational
- **fable** - Expressive, storytelling
- **onyx** - Deep, authoritative
- **nova** - Friendly, upbeat
- **shimmer** - Clear, professional

```python
agent = RealtimeAgent(
    name="Assistant",
    voice="nova",  # Friendly voice
)
```

## Session Configuration

```python
from agents.realtime import RealtimeRunner, RealtimeConfig

config = RealtimeConfig(
    model_settings={
        "model_name": "gpt-realtime",
        "temperature": 0.7,
    },
    audio_settings={
        "input_format": "pcm16",
        "output_format": "pcm16",
        "sample_rate": 24000,
    },
)

runner = RealtimeRunner(
    starting_agent=agent,
    config=config,
)
```

## Tools in Voice Agents

Function tools work the same as text agents:

```python
from agents import function_tool
from agents.realtime import RealtimeAgent

@function_tool
def check_weather(city: str) -> str:
    """Check weather for a city."""
    return f"It's sunny in {city}"

agent = RealtimeAgent(
    name="Weather Voice",
    instructions="Help users check weather. Be brief.",
    tools=[check_weather],
)
```

## Handoffs in Voice

Voice agents support handoffs:

```python
from agents.realtime import RealtimeAgent

sales_agent = RealtimeAgent(
    name="Sales",
    instructions="Handle sales inquiries",
)

support_agent = RealtimeAgent(
    name="Support",
    instructions="Handle support questions",
)

triage_agent = RealtimeAgent(
    name="Triage",
    instructions="Route to sales or support",
    handoffs=[sales_agent, support_agent],
)
```

## Interruption Handling

Voice agents handle interruptions automatically:

- User can interrupt mid-response
- Agent stops speaking and listens
- Context is maintained
- Agent responds to interruption

## Guardrails for Voice

```python
from agents import InputGuardrail, GuardrailFunctionOutput
from agents.realtime import RealtimeAgent

async def voice_content_filter(input_text: str) -> GuardrailFunctionOutput:
    # Filter inappropriate content
    is_inappropriate = check_content(input_text)
    return GuardrailFunctionOutput(
        tripwire_triggered=is_inappropriate,
    )

agent = RealtimeAgent(
    name="Safe Voice",
    input_guardrails=[InputGuardrail(guardrail_function=voice_content_filter)],
)
```

## Event Handling

Handle voice session events:

```python
from agents.realtime import RealtimeRunner

runner = RealtimeRunner(starting_agent=agent)

@runner.on("audio_input")
async def handle_audio(audio_data):
    print("Received audio input")

@runner.on("transcription")
async def handle_transcript(text):
    print(f"User said: {text}")

@runner.on("response")
async def handle_response(text):
    print(f"Agent responding: {text}")

await runner.start()
```

## Audio Processing

### Input Configuration

```python
config = RealtimeConfig(
    audio_settings={
        "input_format": "pcm16",  # PCM 16-bit
        "sample_rate": 24000,     # 24kHz
        "channels": 1,            # Mono
    },
)
```

### Output Configuration

```python
config = RealtimeConfig(
    audio_settings={
        "output_format": "pcm16",
        "sample_rate": 24000,
    },
)
```

## Best Practices for Voice

- Keep instructions concise for spoken delivery
- Use short, conversational responses
- Handle interruptions gracefully
- Test with various accents/speeds
- Consider network latency

## Voice-Specific Tips

- Use contractions ("I'm", "you're") for natural speech
- Avoid long lists - summarize instead
- Include verbal confirmations ("Got it", "Sure")
- Keep sentences short

## Limitations

- Requires stable network connection
- Audio quality affects recognition
- Some languages may have limited support
- Higher latency than text-only

## Related Topics

- `_INFO_OASDKP-IN23_REALTIME_ADVANCED.md` [OASDKP-IN23] - Advanced features
- `_INFO_OASDKP-IN04_AGENTS.md` [OASDKP-IN04] - Base agent configuration

## API Reference

### Classes

- **RealtimeAgent**
  - Import: `from agents.realtime import RealtimeAgent`

- **RealtimeRunner**
  - Import: `from agents.realtime import RealtimeRunner`

- **RealtimeConfig**
  - Import: `from agents.realtime import RealtimeConfig`

## Document History

**[2026-02-11 13:25]**
- Initial realtime voice agents documentation created
