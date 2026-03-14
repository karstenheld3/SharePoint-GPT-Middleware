# INFO: Voice Pipeline

**Doc ID**: OASDKP-IN28
**Goal**: Document the Voice Pipeline system for audio-based agent interactions
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-VOICE` - Voice agents documentation

## Summary

Voice Pipeline is a separate system from Realtime agents that provides a 3-step process for audio-based interactions: speech-to-text transcription, agent workflow execution, and text-to-speech output. Unlike Realtime agents which maintain persistent WebSocket connections, Voice Pipeline processes discrete audio inputs through a traditional request-response pattern. It uses `VoicePipeline` as the main orchestrator and `SingleAgentVoiceWorkflow` or custom workflows for agent execution. This approach is simpler than Realtime but has higher latency due to the sequential processing steps. [VERIFIED]

## Installation

```bash
pip install 'openai-agents[voice]'
```

## Voice Pipeline Concept

The pipeline follows a 3-step process:

```
Audio Input → [Speech-to-Text] → [Your Agent Code] → [Text-to-Speech] → Audio Output
```

1. **Transcribe**: Convert audio input to text using STT model
2. **Process**: Run your agent workflow on the transcribed text
3. **Synthesize**: Convert agent response to audio using TTS model

## Basic Usage

```python
from agents import Agent
from agents.voice import VoicePipeline, SingleAgentVoiceWorkflow, AudioInput

# Create agent
agent = Agent(
    name="Voice Assistant",
    instructions="You're speaking to a human, so be polite and concise.",
    model="gpt-5.2",
)

# Create voice pipeline
pipeline = VoicePipeline(workflow=SingleAgentVoiceWorkflow(agent))

# Run with audio input
audio_input = AudioInput(buffer=audio_data)
result = await pipeline.run(audio_input)

# Stream audio output
async for event in result.stream():
    if event.type == "voice_stream_event_audio":
        play_audio(event.data)
```

## AudioInput

Wrap raw audio data for pipeline input:

```python
import numpy as np
from agents.voice import AudioInput

# From numpy array (16-bit PCM, 24kHz)
buffer = np.zeros(24000 * 3, dtype=np.int16)  # 3 seconds
audio_input = AudioInput(buffer=buffer)

# From microphone (using sounddevice)
import sounddevice as sd
recording = sd.rec(int(3 * 24000), samplerate=24000, channels=1, dtype=np.int16)
sd.wait()
audio_input = AudioInput(buffer=recording.flatten())
```

## SingleAgentVoiceWorkflow

Simple workflow for single-agent interactions:

```python
from agents.voice import SingleAgentVoiceWorkflow

workflow = SingleAgentVoiceWorkflow(agent)
pipeline = VoicePipeline(workflow=workflow)
```

Supports:
- Tools and function calls
- Handoffs to other agents
- Full agent capabilities

## Custom Workflows

Create custom voice workflows:

```python
from agents.voice import VoiceWorkflow, VoicePipeline

class MyCustomWorkflow(VoiceWorkflow):
    async def run(self, transcription: str) -> str:
        # Custom logic
        result = await Runner.run(self.agent, transcription)
        return result.final_output

pipeline = VoicePipeline(workflow=MyCustomWorkflow(agent))
```

## Complete Example

```python
import asyncio
import numpy as np
import sounddevice as sd
from agents import Agent, function_tool
from agents.voice import (
    AudioInput,
    SingleAgentVoiceWorkflow,
    VoicePipeline,
)
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

@function_tool
def get_weather(city: str) -> str:
    """Get the weather for a given city."""
    return f"The weather in {city} is sunny."

agent = Agent(
    name="Assistant",
    instructions=prompt_with_handoff_instructions(
        "You're speaking to a human, so be polite and concise."
    ),
    model="gpt-5.2",
    tools=[get_weather],
)

async def main():
    # Create pipeline
    pipeline = VoicePipeline(workflow=SingleAgentVoiceWorkflow(agent))
    
    # Record audio (3 seconds)
    print("Recording...")
    recording = sd.rec(int(3 * 24000), samplerate=24000, channels=1, dtype=np.int16)
    sd.wait()
    print("Processing...")
    
    # Run pipeline
    audio_input = AudioInput(buffer=recording.flatten())
    result = await pipeline.run(audio_input)
    
    # Play response
    player = sd.OutputStream(samplerate=24000, channels=1, dtype=np.int16)
    player.start()
    
    async for event in result.stream():
        if event.type == "voice_stream_event_audio":
            player.write(event.data)
    
    player.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Voice Pipeline vs Realtime

| Aspect | Voice Pipeline | Realtime Agents |
|--------|---------------|-----------------|
| Connection | Request/response | Persistent WebSocket |
| Latency | Higher (3 steps) | Lower (streaming) |
| Interruption | Not supported | Automatic |
| Complexity | Simpler | More complex |
| Use Case | Batch audio | Live conversation |

## Handoff Prompt Helper

Use `prompt_with_handoff_instructions` for voice-optimized prompts:

```python
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

agent = Agent(
    instructions=prompt_with_handoff_instructions(
        "Your custom instructions here."
    ),
)
```

## Tracing

Voice pipelines are automatically traced:

```python
from agents.tracing import trace

with trace(workflow_name="Voice Session"):
    result = await pipeline.run(audio_input)
```

## Audio Format

- **Sample rate**: 24000 Hz (24kHz)
- **Channels**: 1 (mono)
- **Format**: 16-bit PCM (int16)

## Best Practices

- Use `prompt_with_handoff_instructions` for voice agents
- Keep responses concise for spoken delivery
- Test with various audio quality levels
- Handle empty/silent audio gracefully

## Related Topics

- `_INFO_OASDKP-IN22_REALTIME.md` [OASDKP-IN22] - WebSocket-based realtime
- `_INFO_OASDKP-IN04_AGENTS.md` [OASDKP-IN04] - Agent configuration

## API Reference

### Classes

- **VoicePipeline**
  - Import: `from agents.voice import VoicePipeline`
  - Methods: `run(audio_input)`

- **SingleAgentVoiceWorkflow**
  - Import: `from agents.voice import SingleAgentVoiceWorkflow`

- **AudioInput**
  - Import: `from agents.voice import AudioInput`
  - Params: `buffer` (numpy array)

### Events

- `voice_stream_event_audio` - Audio data chunk
- `voice_stream_event_lifecycle` - Pipeline state changes

## Document History

**[2026-02-11 11:45]**
- Initial voice pipeline documentation created
