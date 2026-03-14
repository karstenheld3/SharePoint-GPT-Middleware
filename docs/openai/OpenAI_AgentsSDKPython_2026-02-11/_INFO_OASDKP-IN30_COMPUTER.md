# INFO: Computer Tool

**Doc ID**: OASDKP-IN30
**Goal**: Document the Computer tool for computer use capabilities
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-TOOLS` - Tools documentation
- `OASDKP-SC-GH-REPO` - Computer tool reference

## Summary

The Computer tool enables agents to interact with computer interfaces through screenshots, mouse clicks, keyboard input, and other GUI operations. This is an experimental/advanced feature that allows agents to automate desktop tasks by perceiving the screen and taking actions. The tool follows OpenAI's computer use API pattern, requiring a local executor to perform actual system interactions. [VERIFIED]

## Overview

Computer use allows an agent to:
- Take screenshots
- Move and click the mouse
- Type text
- Press keyboard shortcuts
- Scroll and drag

## Basic Setup

```python
from agents import Agent
from agents.tools import ComputerTool

# Create computer tool with screen dimensions
computer = ComputerTool(
    display_width=1920,
    display_height=1080,
)

agent = Agent(
    name="Computer Agent",
    instructions="Help users automate desktop tasks.",
    tools=[computer],
)
```

## ComputerTool Configuration

```python
ComputerTool(
    display_width=1920,      # Screen width in pixels
    display_height=1080,     # Screen height in pixels
    display_number=0,        # Display index (multi-monitor)
)
```

## Actions

The Computer tool supports these actions:

- **screenshot** - Capture current screen
- **mouse_move** - Move cursor to coordinates
- **left_click** - Left mouse click
- **right_click** - Right mouse click
- **double_click** - Double left click
- **type** - Type text
- **key** - Press key or key combination
- **scroll** - Scroll up/down
- **drag** - Drag from one point to another

## Executor

You must provide an executor that performs actual system operations:

```python
from agents.tools import ComputerTool, ComputerToolExecutor

class MyExecutor(ComputerToolExecutor):
    async def screenshot(self) -> bytes:
        """Capture and return screenshot as PNG bytes."""
        # Use pyautogui, mss, or similar
        import mss
        with mss.mss() as sct:
            png = sct.shot(output=None)
            return png
    
    async def mouse_move(self, x: int, y: int):
        """Move mouse to coordinates."""
        import pyautogui
        pyautogui.moveTo(x, y)
    
    async def left_click(self):
        """Perform left click."""
        import pyautogui
        pyautogui.click()
    
    async def type(self, text: str):
        """Type text."""
        import pyautogui
        pyautogui.write(text)
    
    async def key(self, key: str):
        """Press key combination."""
        import pyautogui
        pyautogui.hotkey(*key.split('+'))

# Use with tool
computer = ComputerTool(
    display_width=1920,
    display_height=1080,
    executor=MyExecutor(),
)
```

## Example: Web Automation

```python
from agents import Agent, Runner
from agents.tools import ComputerTool

computer = ComputerTool(
    display_width=1920,
    display_height=1080,
    executor=my_executor,
)

agent = Agent(
    name="Web Automator",
    instructions=(
        "You can control the computer to automate web tasks. "
        "Take screenshots to see the screen, then click and type "
        "to interact with applications."
    ),
    tools=[computer],
)

result = await Runner.run(
    agent,
    "Open the browser and search for 'OpenAI Agents SDK'"
)
```

## Safety Considerations

Computer use is powerful and potentially dangerous:

- **Sandboxing**: Run in VM or container
- **Permissions**: Limit file system access
- **Monitoring**: Log all actions
- **Approval**: Consider human-in-the-loop for sensitive actions
- **Scope**: Restrict to specific applications

## Limitations

- Requires local executor implementation
- Screenshot processing adds latency
- Screen resolution changes may confuse agent
- No built-in safety guardrails

## Best Practices

- Always run in sandboxed environment
- Implement approval gates for destructive actions
- Use clear, specific instructions
- Provide context about current application state
- Test thoroughly before production use

## Related Topics

- `_INFO_OASDKP-IN09_TOOLS_OVERVIEW.md` [OASDKP-IN09] - Tool categories
- `_INFO_OASDKP-IN24_HUMANINLOOP.md` [OASDKP-IN24] - Approval patterns

## API Reference

### Classes

- **ComputerTool**
  - Import: `from agents.tools import ComputerTool`
  - Params: `display_width`, `display_height`, `display_number`, `executor`

- **ComputerToolExecutor** (Protocol)
  - Import: `from agents.tools import ComputerToolExecutor`
  - Methods: `screenshot()`, `mouse_move()`, `left_click()`, `type()`, `key()`, etc.

## Document History

**[2026-02-11 11:50]**
- Initial computer tool documentation created
