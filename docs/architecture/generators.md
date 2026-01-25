# Generators

Generators are the bridge between Hive's specification layer and runtime interfaces. Each generator reads from the application registry and produces a specific interface type.

## Overview

```
ApplicationRegistry
       │
       ├──► CLIGenerator ───► Typer App
       ├──► TUIGenerator ───► Textual App
       ├──► MCPGenerator ───► FastMCP Server
       ├──► RESTGenerator ──► FastAPI App
       └──► SchemaGenerator ► JSON Schema
```

## CLI Generator

The CLI generator creates a Typer application with proper argument handling, help text, and output formatting.

**Location:** `src/hive/generators/cli.py`

### Features

- Converts Python type hints to CLI arguments
- Handles refinement types (PositiveInt, NonEmptyStr, etc.)
- Adds `--json` flag to every command
- Formats validation errors user-friendly

### Generation Process

```python
from hive.generators.cli import CLIGenerator

generator = CLIGenerator(app)
typer_app = generator.generate()
```

**What happens:**

1. Iterates over registered commands and queries
2. For each command:
   - Extracts parameter types and defaults
   - Creates Typer Option/Argument for each parameter
   - Builds wrapper function with proper signature
   - Registers with Typer app

### Type Mapping

| Python Type | CLI Representation |
|-------------|-------------------|
| `str` | `TEXT` |
| `int` | `INTEGER` |
| `float` | `FLOAT` |
| `bool` | `--flag/--no-flag` |
| `PositiveInt` | `INTEGER` (validated) |
| `Optional[T]` | Optional argument |

### Output Handling

Commands receive an `ExecutionContext` with format-aware output:

```python
@command(app)
async def list_tasks(ctx) -> list[Task]:
    tasks = await ctx.db.exec(select(Task))
    return tasks.all()  # Automatically formatted
```

- Default: Rich table formatting
- `--json`: JSON output

---

## TUI Generator

The TUI generator creates a Textual application with screens, keybindings, and data binding.

**Location:** `src/hive/generators/tui.py`

### Features

- Binds registered screens with keybindings
- Validates query references
- Supports custom CSS

### Generation Process

```python
from hive.generators.tui import generate_tui_app

tui_app = generate_tui_app(app, css_path="custom.tcss")
tui_app.run()
```

**What happens:**

1. Lists all registered screens
2. Validates that referenced queries exist
3. Creates HiveApp with screen bindings
4. Configures keybindings from decorators

### Screen Registration

```python
from hive import App
from hive.core.decorators import screen
from hive.tui.screens import HiveScreen

@screen(app, default=True, keybinding="d")
class DashboardScreen(HiveScreen):
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self):
        yield Header()
        yield DataTable()
```

---

## MCP Generator

The MCP generator creates a FastMCP server that exposes commands as tools for AI agents.

**Location:** `src/hive/generators/mcp.py`

### Features

- Converts commands to MCP tools
- Generates JSON Schema input schemas
- Supports stdio and SSE transports

### Generation Process

```python
from hive.generators.mcp import MCPGenerator

generator = MCPGenerator()
config = generator.generate(app)  # MCPServerConfig
generator.serve(app, transport="stdio")
```

**What happens:**

1. Iterates over registered commands
2. For each command:
   - Builds input schema from parameters
   - Creates MCPTool with name, description, schema
3. Returns MCPServerConfig with all tools

### Tool Schema

Commands become MCP tools with proper schemas:

```python
@command(app)
async def create_task(ctx, title: str, priority: int = 1) -> Task:
    """Create a new task with the given title."""
    ...
```

Becomes:

```json
{
  "name": "create_task",
  "description": "Create a new task with the given title.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "title": {"type": "string"},
      "priority": {"type": "integer", "default": 1}
    },
    "required": ["title"]
  }
}
```

### Transport Options

| Transport | Use Case |
|-----------|----------|
| `stdio` | Claude Desktop, local agents |
| `sse` | Web clients, remote agents |

---

## REST Generator

The REST generator creates a FastAPI application with endpoints for commands and queries.

**Location:** `src/hive/generators/rest.py`

### Features

- Commands become POST endpoints
- Queries become GET endpoints
- Automatic OpenAPI documentation
- Multiple authentication options

### Generation Process

```python
from hive.generators.rest import RESTGenerator

generator = RESTGenerator()
config = generator.generate(app)  # RESTAPIConfig
fastapi_app = generator.create_app(app, auth_type="api_key")
generator.serve(app, host="0.0.0.0", port=8000)
```

**What happens:**

1. Creates FastAPI application with metadata
2. For each command:
   - Creates POST endpoint at `/commands/{name}`
   - Builds Pydantic request model from parameters
3. For each query:
   - Creates GET endpoint at `/queries/{name}`
   - Maps parameters to query string

### Endpoint Structure

| Endpoint | Method | Source |
|----------|--------|--------|
| `/health` | GET | Built-in health check |
| `/spec` | GET | Application specification |
| `/commands/{name}` | POST | @command functions |
| `/queries/{name}` | GET | @query functions |
| `/docs` | GET | OpenAPI documentation |

### Authentication

```python
# No authentication
generator.serve(app, auth_type="none")

# API key in header
HIVE_API_KEY=secret generator.serve(app, auth_type="api_key")

# Bearer token
generator.serve(app, auth_type="bearer")

# Basic auth
generator.serve(app, auth_type="basic")
```

---

## Schema Generator

The Schema generator produces JSON Schema (Draft 2020-12) from Pydantic models and type hints.

**Location:** `src/hive/generators/schema.py`

### Features

- Supports all Python basic types
- Maps refinement types to constraints
- Handles Optional and Union types
- Includes `$schema` dialect URI

### Type Mapping

| Python Type | JSON Schema |
|-------------|-------------|
| `str` | `{"type": "string"}` |
| `int` | `{"type": "integer"}` |
| `float` | `{"type": "number"}` |
| `bool` | `{"type": "boolean"}` |
| `datetime` | `{"type": "string", "format": "date-time"}` |
| `UUID` | `{"type": "string", "format": "uuid"}` |
| `list[T]` | `{"type": "array", "items": {...}}` |
| `dict[str, T]` | `{"type": "object", "additionalProperties": {...}}` |
| `Optional[T]` | `{"anyOf": [{...}, {"type": "null"}]}` |

### Refinement Type Mapping

| Hive Type | JSON Schema |
|-----------|-------------|
| `PositiveInt` | `{"type": "integer", "minimum": 1}` |
| `NonNegativeInt` | `{"type": "integer", "minimum": 0}` |
| `Percentage` | `{"type": "number", "minimum": 0, "maximum": 100}` |
| `Port` | `{"type": "integer", "minimum": 1, "maximum": 65535}` |
| `NonEmptyStr` | `{"type": "string", "minLength": 1}` |
| `Email` | `{"type": "string", "format": "email"}` |
| `Url` | `{"type": "string", "format": "uri"}` |
| `Slug` | `{"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$"}` |

### Usage

```python
from hive.generators.schema import python_type_to_json_schema, HiveSchemaGenerator

# Convert a single type
schema = python_type_to_json_schema(PositiveInt)
# {"type": "integer", "minimum": 1}

# Generate schema for Pydantic model
generator = HiveSchemaGenerator()
schema = generator.generate_schema(Task)
```

---

## Extension Points

### Custom Generators

Create custom generators by implementing the generator pattern:

```python
class CustomGenerator:
    def __init__(self, app: App) -> None:
        self._app = app
        self._registry = app.registry

    def generate(self) -> CustomConfig:
        config = CustomConfig(name=self._app.name)

        for cmd in self._registry.list_commands():
            # Process each command
            config.add_item(self._process_command(cmd))

        return config

    def _process_command(self, cmd: CommandRegistration) -> CustomItem:
        # Convert command to custom format
        ...
```

### Hooking into Generation

Override generator methods for customization:

```python
class CustomCLIGenerator(CLIGenerator):
    def _create_command_wrapper(self, func, name, parameters):
        # Add custom logic
        wrapper = super()._create_command_wrapper(func, name, parameters)
        return self._add_logging(wrapper)
```
