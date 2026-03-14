# INFO: Model Context Protocol (MCP)

**Doc ID**: OASDKP-IN21
**Goal**: Document MCP integration for connecting external tools and data sources
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-MCP` - Official MCP documentation

## Summary

The Model Context Protocol (MCP) is an open standard that enables AI applications to connect with external tools and data sources. The OpenAI Agents SDK supports multiple MCP transports: Hosted MCP (runs on OpenAI servers), Streamable HTTP, HTTP with SSE, and stdio. MCP integration allows agents to use tools from any MCP-compliant server, enabling access to filesystems, databases, APIs, and custom enterprise tools. The SDK provides approval policies for tool execution, tool filtering for security, and caching for performance. [VERIFIED]

## What is MCP?

From the official documentation:

> MCP is an open protocol that standardizes how applications provide context to LLMs. Think of MCP like a USB-C port for AI applications. Just as USB-C provides a standardized way to connect your devices to various peripherals and accessories, MCP provides a standardized way to connect AI models to different data sources and tools.

## MCP Integration Options

The SDK supports five approaches to MCP:

### 1. Hosted MCP Server Tools

Run on OpenAI's servers alongside the model:

```python
from agents import Agent, HostedMCPTool

agent = Agent(
    name="MCP Agent",
    tools=[
        HostedMCPTool(
            server_url="https://mcp.example.com",
            tool_name="search_documents",
        ),
    ],
)
```

### 2. Streamable HTTP MCP Servers

Connect to HTTP-based MCP servers:

```python
from agents import Agent
from agents.mcp import StreamableHTTPMCPServer

server = StreamableHTTPMCPServer(
    url="https://mcp-server.example.com",
    headers={"Authorization": "Bearer token"},
)

agent = Agent(
    name="HTTP MCP Agent",
    mcp_servers=[server],
)
```

### 3. HTTP with SSE MCP Servers

Server-Sent Events for real-time updates:

```python
from agents.mcp import SSEMCPServer

server = SSEMCPServer(
    url="https://sse-mcp.example.com/events",
)

agent = Agent(
    name="SSE Agent",
    mcp_servers=[server],
)
```

### 4. stdio MCP Servers

Local processes communicating via stdin/stdout:

```python
from agents.mcp import StdioMCPServer

server = StdioMCPServer(
    command="python",
    args=["my_mcp_server.py"],
    env={"API_KEY": "secret"},
)

agent = Agent(
    name="Local MCP Agent",
    mcp_servers=[server],
)
```

### 5. MCP Server Manager

Manage multiple MCP servers:

```python
from agents.mcp import MCPServerManager

manager = MCPServerManager()
manager.add_server("docs", docs_server)
manager.add_server("db", database_server)

agent = Agent(
    name="Multi-MCP Agent",
    mcp_servers=manager.servers,
)
```

## Agent-Level MCP Configuration

Add MCP servers at the agent level:

```python
from agents import Agent
from agents.mcp import StdioMCPServer

# Create MCP server
filesystem_server = StdioMCPServer(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "./data"],
)

# Attach to agent
agent = Agent(
    name="File Agent",
    instructions="Help users manage files",
    mcp_servers=[filesystem_server],
)
```

## Hosted MCP Tools

For OpenAI-hosted MCP servers with streaming support:

```python
from agents import Agent, HostedMCPTool

agent = Agent(
    name="Search Agent",
    tools=[
        HostedMCPTool(
            server_url="mcp://example.com/search",
            tool_name="web_search",
            streaming=True,  # Enable streaming results
        ),
    ],
)
```

### Connector-Backed Hosted Servers

Use OpenAI connectors as MCP sources:

```python
from agents import HostedMCPTool

tool = HostedMCPTool(
    connector_id="conn_abc123",  # OpenAI connector ID
    tool_name="query_database",
)
```

## Approval Policies

Control tool execution with approval flows:

```python
from agents.mcp import ApprovalPolicy

async def require_approval(tool_name: str, arguments: dict) -> bool:
    """Require manual approval for sensitive operations."""
    if tool_name in ["delete_file", "send_email"]:
        # Implement approval logic (e.g., prompt user)
        return await prompt_user_for_approval(tool_name, arguments)
    return True  # Auto-approve other tools

server = StdioMCPServer(
    command="python",
    args=["mcp_server.py"],
    approval_policy=require_approval,
)
```

## Tool Filtering

### Static Tool Filtering

Limit which tools are exposed:

```python
from agents.mcp import StdioMCPServer

server = StdioMCPServer(
    command="python",
    args=["mcp_server.py"],
    tool_filter=["read_file", "list_directory"],  # Only these tools
)
```

### Dynamic Tool Filtering

Filter based on context:

```python
def dynamic_filter(context, tool_name: str) -> bool:
    """Filter tools based on user permissions."""
    if context.context.is_admin:
        return True  # Admins can use all tools
    return tool_name not in ["delete_file", "modify_config"]

server = StdioMCPServer(
    command="python",
    args=["mcp_server.py"],
    tool_filter=dynamic_filter,
)
```

## Per-Call Metadata

Add context to individual tool calls:

```python
from agents.mcp import tool_meta_resolver

def add_metadata(tool_name: str, context) -> dict:
    """Add user context to tool calls."""
    return {
        "user_id": context.context.user_id,
        "session_id": context.context.session_id,
        "timestamp": datetime.now().isoformat(),
    }

server = StdioMCPServer(
    command="python",
    args=["mcp_server.py"],
    tool_meta_resolver=add_metadata,
)
```

## MCP Tool Outputs

### Text Output

```python
# Server returns text
{"type": "text", "content": "File contents here..."}
```

### Image Output

```python
# Server returns image
{"type": "image", "data": "base64...", "media_type": "image/png"}
```

## MCP Prompts

Access MCP-provided prompts:

```python
from agents.mcp import get_mcp_prompts

prompts = await get_mcp_prompts(server)
for prompt in prompts:
    print(f"{prompt.name}: {prompt.description}")
```

## Caching

Enable caching for MCP responses:

```python
from agents.mcp import StdioMCPServer, MCPCache

cache = MCPCache(
    ttl=300,  # 5 minutes
    max_size=1000,
)

server = StdioMCPServer(
    command="python",
    args=["mcp_server.py"],
    cache=cache,
)
```

## Tracing

MCP calls are automatically traced:

```python
# MCP tool calls appear in traces as:
# - tool_name: The MCP tool called
# - server: The MCP server URL/command
# - arguments: Tool arguments
# - result: Tool output
```

## Common MCP Servers

Popular MCP server implementations:

- **Filesystem**: Access local files
- **PostgreSQL**: Query databases
- **Slack**: Send messages, read channels
- **GitHub**: Repository operations
- **Google Drive**: Document access
- **Brave Search**: Web search

## Example: Filesystem MCP

```python
from agents import Agent, Runner
from agents.mcp import StdioMCPServer

# Create filesystem MCP server
fs_server = StdioMCPServer(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "./documents"],
)

# Create agent with MCP
agent = Agent(
    name="Document Assistant",
    instructions="Help users find and read documents.",
    mcp_servers=[fs_server],
)

# Run
result = await Runner.run(agent, "List all PDF files in the documents folder")
print(result.final_output)
```

## Best Practices

- Use tool filtering for security
- Implement approval policies for destructive operations
- Enable caching for frequently-used tools
- Use hosted MCP for lower latency when available
- Monitor MCP calls via tracing

## Related Topics

- `_INFO_OASDKP-IN09_TOOLS_OVERVIEW.md` [OASDKP-IN09] - Tool categories
- `_INFO_OASDKP-IN11_TOOLS_HOSTED.md` [OASDKP-IN11] - HostedMCPTool

## API Reference

### Classes

- **HostedMCPTool**
  - Import: `from agents import HostedMCPTool`

- **StdioMCPServer**
  - Import: `from agents.mcp import StdioMCPServer`

- **StreamableHTTPMCPServer**
  - Import: `from agents.mcp import StreamableHTTPMCPServer`

- **SSEMCPServer**
  - Import: `from agents.mcp import SSEMCPServer`

- **MCPServerManager**
  - Import: `from agents.mcp import MCPServerManager`

## Further Reading

- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP Server List](https://github.com/modelcontextprotocol/servers)

## Document History

**[2026-02-11 12:40]**
- Initial MCP documentation created
- All transport types documented
