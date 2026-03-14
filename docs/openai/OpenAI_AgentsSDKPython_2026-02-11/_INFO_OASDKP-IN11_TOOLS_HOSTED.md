# INFO: Hosted Tools

**Doc ID**: OASDKP-IN11
**Goal**: Document OpenAI-hosted tools available in the Agents SDK
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-TOOLS` - Official tools documentation

## Summary

Hosted tools run alongside the model on OpenAI's servers, providing powerful capabilities without local execution overhead. The SDK offers five hosted tools when using `OpenAIResponsesModel`: WebSearchTool for web searches, FileSearchTool for vector store retrieval, CodeInterpreterTool for sandboxed code execution, ImageGenerationTool for image creation, and HostedMCPTool for remote MCP server integration. These tools are optimized for the OpenAI infrastructure and provide seamless integration with agent workflows. [VERIFIED]

## WebSearchTool

Search the web for information:

```python
from agents import Agent, WebSearchTool

agent = Agent(
    name="Research Assistant",
    instructions="Help users research topics",
    tools=[WebSearchTool()],
)
```

### Configuration

```python
WebSearchTool(
    # Default configuration works for most cases
)
```

### Use Cases

- Current events and news
- Fact-checking
- Research assistance
- Finding URLs and references

## FileSearchTool

Retrieve information from OpenAI Vector Stores:

```python
from agents import Agent, FileSearchTool

agent = Agent(
    name="Document Assistant",
    instructions="Answer questions based on uploaded documents",
    tools=[
        FileSearchTool(
            max_num_results=3,
            vector_store_ids=["vs_abc123"],
        ),
    ],
)
```

### Configuration

- **max_num_results**
  - Type: `int`
  - Purpose: Maximum chunks to retrieve
  - Recommended: 3-10 for focused results

- **vector_store_ids**
  - Type: `list[str]`
  - Purpose: IDs of vector stores to search
  - Note: Create vector stores via OpenAI API

### Creating Vector Stores

```python
from openai import OpenAI

client = OpenAI()

# Create vector store
vector_store = client.vector_stores.create(name="My Documents")

# Add files
client.vector_stores.files.create(
    vector_store_id=vector_store.id,
    file_id="file-abc123"
)
```

## CodeInterpreterTool

Execute code in a sandboxed environment:

```python
from agents import Agent, CodeInterpreterTool

agent = Agent(
    name="Data Analyst",
    instructions="Analyze data and create visualizations",
    tools=[CodeInterpreterTool()],
)
```

### Capabilities

- Python code execution
- Data analysis with pandas, numpy
- Chart generation with matplotlib
- File processing
- Mathematical computations

### Use Cases

- Data analysis and visualization
- Mathematical calculations
- File format conversions
- Code testing and debugging

## ImageGenerationTool

Generate images from text prompts:

```python
from agents import Agent, ImageGenerationTool

agent = Agent(
    name="Creative Assistant",
    instructions="Help users create images",
    tools=[ImageGenerationTool()],
)
```

### Configuration

```python
ImageGenerationTool(
    # Uses DALL-E for generation
)
```

### Use Cases

- Creative content generation
- Illustration creation
- Visual concept exploration
- Design prototyping

## HostedMCPTool

Expose a remote MCP server's tools to the model:

```python
from agents import Agent, HostedMCPTool

agent = Agent(
    name="MCP Agent",
    instructions="Use MCP tools as needed",
    tools=[
        HostedMCPTool(
            server_url="https://mcp.example.com",
            tool_name="custom_tool",
        ),
    ],
)
```

### Use Cases

- Integration with remote services
- Custom enterprise tools
- Third-party API access

## Combining Hosted Tools

```python
from agents import Agent, WebSearchTool, FileSearchTool, CodeInterpreterTool

agent = Agent(
    name="Super Assistant",
    instructions=(
        "Help users with research, document analysis, and data processing. "
        "Use web search for current information, file search for internal docs, "
        "and code interpreter for data analysis."
    ),
    tools=[
        WebSearchTool(),
        FileSearchTool(
            max_num_results=5,
            vector_store_ids=["vs_internal_docs"],
        ),
        CodeInterpreterTool(),
    ],
)
```

## Hosted vs Local Tools

| Aspect | Hosted Tools | Local Function Tools |
|--------|--------------|---------------------|
| Execution | OpenAI servers | Your environment |
| Latency | Lower (co-located) | Higher (round-trip) |
| Access | OpenAI resources | Your resources |
| Customization | Limited | Full control |
| Security | OpenAI managed | Your responsibility |

## Limitations

- Hosted tools require `OpenAIResponsesModel`
- Cannot access local files or databases directly
- Rate limits apply per OpenAI account
- Some tools have usage costs

## Best Practices

- Use FileSearchTool for document Q&A over large corpora
- Combine WebSearchTool with function tools for verification
- Use CodeInterpreterTool for complex calculations
- Monitor usage for cost management

## Related Topics

- `_INFO_OASDKP-IN09_TOOLS_OVERVIEW.md` [OASDKP-IN09] - Tool categories
- `_INFO_OASDKP-IN21_MCP.md` [OASDKP-IN21] - MCP integration

## API Reference

### Classes

- **WebSearchTool**
  - Import: `from agents import WebSearchTool`

- **FileSearchTool**
  - Import: `from agents import FileSearchTool`
  - Params: `max_num_results`, `vector_store_ids`

- **CodeInterpreterTool**
  - Import: `from agents import CodeInterpreterTool`

- **ImageGenerationTool**
  - Import: `from agents import ImageGenerationTool`

- **HostedMCPTool**
  - Import: `from agents import HostedMCPTool`

## Document History

**[2026-02-11 12:05]**
- Initial document created
- All five hosted tools documented
