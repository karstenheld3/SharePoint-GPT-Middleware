# INFO: Function Tools

**Doc ID**: OASDKP-IN10
**Goal**: Complete documentation of function tools and the @function_tool decorator
**SDK Version**: openai-agents 0.8.3

**Sources:**
- `OASDKP-SC-GHIO-TOOLS` - Official tools documentation

## Summary

Function tools are the most flexible way to extend agent capabilities in the OpenAI Agents SDK. The `@function_tool` decorator converts any Python function into an agent tool with automatic JSON schema generation from type hints and Pydantic-powered validation. Docstrings are parsed to generate tool and parameter descriptions. Function tools support returning images and files, custom implementations, error handling, and argument constraints via Pydantic Field. Both sync and async functions are supported. [VERIFIED]

## Basic Usage

### Simple Function Tool

```python
from agents import Agent, function_tool

@function_tool
def get_weather(city: str) -> str:
    """Returns weather info for the specified city."""
    return f"The weather in {city} is sunny"

agent = Agent(
    name="Weather Agent",
    instructions="Help users with weather information",
    tools=[get_weather],
)
```

### Async Function Tool

```python
from agents import function_tool
import httpx

@function_tool
async def fetch_data(url: str) -> str:
    """Fetches data from the given URL."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text
```

## Automatic Schema Generation

The decorator automatically generates JSON schemas from:

1. **Type hints** - Parameter and return types
2. **Docstrings** - Tool and parameter descriptions
3. **Default values** - Optional parameters

```python
@function_tool
def search_products(
    query: str,
    category: str = "all",
    max_results: int = 10
) -> list[dict]:
    """
    Search for products in the catalog.
    
    Args:
        query: The search query string
        category: Product category to filter by
        max_results: Maximum number of results to return
    """
    # Implementation
    return []
```

Generated schema includes:
- `query`: required string
- `category`: optional string, default "all"
- `max_results`: optional integer, default 10

## Pydantic Field Constraints

Use Pydantic Field for detailed argument constraints:

```python
from agents import function_tool
from pydantic import Field

@function_tool
def book_flight(
    origin: str = Field(description="Origin airport code (e.g., 'JFK')"),
    destination: str = Field(description="Destination airport code"),
    passengers: int = Field(ge=1, le=9, description="Number of passengers (1-9)"),
    class_type: str = Field(
        default="economy",
        description="Ticket class",
        pattern="^(economy|business|first)$"
    ),
) -> dict:
    """Book a flight reservation."""
    return {"status": "booked", "origin": origin, "destination": destination}
```

### Field Options

- **description** - Parameter description for LLM
- **ge/le/gt/lt** - Numeric constraints
- **min_length/max_length** - String length constraints
- **pattern** - Regex pattern for validation
- **default** - Default value

## Returning Images or Files

Function tools can return images and files:

```python
from agents import function_tool
from agents.tools import ToolResultImage, ToolResultFile

@function_tool
def generate_chart(data: list[float]) -> ToolResultImage:
    """Generate a chart from data."""
    # Create chart image
    image_bytes = create_chart(data)
    return ToolResultImage(
        data=image_bytes,
        media_type="image/png"
    )

@function_tool
def export_report(report_id: str) -> ToolResultFile:
    """Export a report as PDF."""
    pdf_bytes = generate_pdf(report_id)
    return ToolResultFile(
        data=pdf_bytes,
        filename="report.pdf",
        media_type="application/pdf"
    )
```

## Custom Function Tools

For more control, create custom tool classes:

```python
from agents import Agent
from agents.tools import FunctionTool

class CustomWeatherTool(FunctionTool):
    name = "get_weather"
    description = "Get weather for a city"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        super().__init__()
    
    async def run(self, city: str) -> str:
        # Use self.api_key for API call
        return f"Weather in {city}: Sunny"
    
    def get_schema(self):
        return {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"}
            },
            "required": ["city"]
        }

agent = Agent(
    name="Weather Agent",
    tools=[CustomWeatherTool(api_key="sk-...")],
)
```

## Accessing Context in Tools

Tools can access the run context:

```python
from agents import function_tool, RunContextWrapper

@function_tool
def get_user_data(context: RunContextWrapper) -> dict:
    """Get current user's data."""
    user = context.context  # Access the typed context
    return {
        "name": user.name,
        "id": user.uid,
        "is_pro": user.is_pro_user,
    }
```

The context parameter is automatically injected and not exposed to the LLM.

## Error Handling

### Returning Errors

```python
from agents import function_tool
from agents.tools import ToolError

@function_tool
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ToolError("Cannot divide by zero")
    return a / b
```

### Error Recovery

The agent loop handles tool errors gracefully:
1. Error is returned to the LLM
2. LLM can decide to retry with different parameters
3. Or inform the user about the error

## Complex Types

### Pydantic Models as Parameters

```python
from pydantic import BaseModel
from agents import function_tool

class Address(BaseModel):
    street: str
    city: str
    zip_code: str

class OrderRequest(BaseModel):
    product_id: str
    quantity: int
    shipping_address: Address

@function_tool
def place_order(order: OrderRequest) -> dict:
    """Place a new order."""
    return {"order_id": "ORD-123", "status": "placed"}
```

### Lists and Dicts

```python
@function_tool
def analyze_data(
    values: list[float],
    options: dict[str, str] = None
) -> dict:
    """Analyze a list of values."""
    return {
        "mean": sum(values) / len(values),
        "count": len(values),
    }
```

## Limitations and Known Issues

- Complex nested types may not generate optimal schemas
- Very large return values may impact performance
- Streaming not supported for individual tool results

## Gotchas and Quirks

- Context parameter must be named `context` to be auto-injected
- Return type annotation affects how result is serialized
- Docstring format (Google, NumPy, etc.) affects parsing

## Best Practices

- Always include type hints for parameters
- Write clear docstrings with parameter descriptions
- Use Pydantic Field for complex constraints
- Handle errors gracefully with ToolError
- Keep tools focused on single responsibilities
- Use async for I/O-bound operations

## Related Topics

- `_INFO_OASDKP-IN09_TOOLS_OVERVIEW.md` [OASDKP-IN09] - Tool categories
- `_INFO_OASDKP-IN04_AGENTS.md` [OASDKP-IN04] - Adding tools to agents

## API Reference

### Decorators

- **@function_tool**
  - Import: `from agents import function_tool`
  - Purpose: Convert Python function to agent tool

### Classes

- **FunctionTool**
  - Import: `from agents.tools import FunctionTool`
  - Purpose: Base class for custom tools

- **ToolError**
  - Import: `from agents.tools import ToolError`
  - Purpose: Raise recoverable tool errors

- **ToolResultImage**
  - Import: `from agents.tools import ToolResultImage`
  - Purpose: Return image from tool

- **ToolResultFile**
  - Import: `from agents.tools import ToolResultFile`
  - Purpose: Return file from tool

## Document History

**[2026-02-11 12:00]**
- Initial document created
- Comprehensive function tool documentation
