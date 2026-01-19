# Quickstart: Specification and Distribution

**Branch**: `003-spec-distribution` | **Date**: 2026-01-18

## Prerequisites

```bash
# Ensure Hive is installed with development dependencies
uv sync --dev

# Verify installation
uv run hive --version
```

---

## Milestone 3.1: Specification Export

### Export to JSON Schema

```bash
# Export full specification
uv run hive spec export --format json -o spec.json

# Export to stdout
uv run hive spec export --format json

# Include hidden commands
uv run hive spec export --format json --include-internal
```

**Example output** (`spec.json`):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "metadata": {
    "name": "myapp",
    "version": "0.1.0",
    "generated_at": "2026-01-18T10:30:00Z",
    "hive_version": "0.1.0"
  },
  "commands": {
    "create_task": {
      "name": "create_task",
      "description": "Create a new task.",
      "parameters": [
        {
          "name": "title",
          "type": "string",
          "required": true,
          "minLength": 1
        },
        {
          "name": "priority",
          "type": "integer",
          "required": false,
          "default": 1,
          "minimum": 1,
          "maximum": 5
        }
      ],
      "return_type": { "$ref": "#/$defs/Task" }
    }
  },
  "queries": { ... },
  "entities": { ... },
  "$defs": {
    "Task": {
      "type": "object",
      "properties": {
        "id": { "type": "integer" },
        "title": { "type": "string" }
      }
    }
  }
}
```

### Export to TOML

```bash
uv run hive spec export --format toml -o spec.toml
```

### Compare Specifications

```bash
# Compare two versions
uv run hive spec diff v1.json v2.json

# Output as JSON
uv run hive spec diff v1.json v2.json --format json

# Exit with error on breaking changes (for CI)
uv run hive spec diff v1.json v2.json --fail-on-breaking
```

**Example diff output**:

```
Comparing v1.json (v0.1.0) → v2.json (v0.2.0)

BREAKING CHANGES (1):
  ✗ commands.delete_task: REMOVED

Changes (3):
  + commands.archive_task: ADDED
  ~ commands.create_task.parameters.priority.maximum: 5 → 10
  ~ entities.Task.fields: added 'archived' field

Summary: +1 -1 ~2 (1 breaking)
```

### Programmatic API

```python
from hive import App
from hive.spec import export_specification, diff_specifications

app = App("myapp")

# Export specification
spec = export_specification(app, format="json")
print(spec)

# Compare specifications
with open("v1.json") as f1, open("v2.json") as f2:
    diff = diff_specifications(f1.read(), f2.read())
    print(f"Breaking changes: {len(diff.breaking_changes)}")
```

---

## Milestone 3.2: MCP Server

### Start MCP Server

```bash
# Default: stdio transport (for Claude Desktop subprocess)
uv run hive mcp serve

# SSE transport for network access
uv run hive mcp serve --transport sse --port 8080

# Include queries as tools
uv run hive mcp serve --include-queries
```

### Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "myapp": {
      "command": "uv",
      "args": ["run", "hive", "mcp", "serve"],
      "cwd": "/path/to/myapp"
    }
  }
}
```

For SSE transport:

```json
{
  "mcpServers": {
    "myapp": {
      "url": "http://localhost:8080/sse"
    }
  }
}
```

### Tool Usage from Claude

Once connected, Claude can discover and use your commands:

```
Claude: I'll create a task for you using the myapp tools.

[Using create_task tool with: {"title": "Review PR", "priority": 2}]

Task created successfully:
- ID: 42
- Title: Review PR
- Priority: 2
```

### Programmatic API

```python
from hive import App
from hive.generators.mcp import MCPGenerator

app = App("myapp")

# Generate MCP server
mcp = MCPGenerator(app).generate()

# Run with stdio
mcp.run(transport="stdio")

# Run with SSE
mcp.run(transport="sse", host="127.0.0.1", port=8080)
```

---

## Milestone 3.3: REST API

### Start REST Server

```bash
# Development server with hot reload
uv run hive serve --reload

# Production server
uv run hive serve --host 0.0.0.0 --port 8000 --workers 4

# With API key authentication
HIVE_API_KEY=secret123 uv run hive serve --auth api_key
```

### Access the API

```bash
# View OpenAPI docs
open http://localhost:8000/docs

# Execute a command
curl -X POST http://localhost:8000/commands/create_task \
  -H "Content-Type: application/json" \
  -d '{"title": "Test task", "priority": 1}'

# Execute a query
curl "http://localhost:8000/queries/list_tasks?status=pending"

# Health check
curl http://localhost:8000/health

# Get specification
curl http://localhost:8000/spec
```

### Authentication Examples

```bash
# API key auth
curl -X POST http://localhost:8000/commands/create_task \
  -H "X-API-Key: secret123" \
  -H "Content-Type: application/json" \
  -d '{"title": "Secure task"}'

# Bearer token auth
curl -X POST http://localhost:8000/commands/create_task \
  -H "Authorization: Bearer eyJhbGci..." \
  -H "Content-Type: application/json" \
  -d '{"title": "Secure task"}'
```

### Programmatic API

```python
from hive import App
from hive.generators.rest import RESTGenerator

app = App("myapp")

# Generate FastAPI app
api = RESTGenerator(app).generate()

# Run with uvicorn
import uvicorn
uvicorn.run(api, host="127.0.0.1", port=8000)
```

---

## Milestone 3.4: Project Tooling

### Create New Project

```bash
# Basic project
uv run hive new myproject

# With all features
uv run hive new myproject --features all

# Specific features
uv run hive new myproject --features tui,mcp

# Custom template
uv run hive new myproject --template fastapi-app
```

**Generated structure**:

```
myproject/
├── pyproject.toml
├── README.md
├── src/
│   └── myproject/
│       ├── __init__.py
│       ├── app.py          # App definition
│       ├── commands.py     # Example commands
│       └── entities.py     # Example entities
└── tests/
    ├── __init__.py
    └── test_commands.py
```

### Development Server

```bash
cd myproject

# Start development server (auto-detects interfaces)
uv run hive dev

# Specific interfaces
uv run hive dev --interfaces cli,tui

# Custom ports
uv run hive dev --rest-port 8000 --mcp-port 8080
```

### Build and Publish

```bash
# Build wheel
uv run hive build

# Build wheel and sdist
uv run hive build --format wheel,sdist

# Publish to PyPI
uv run hive publish

# Publish to TestPyPI
uv run hive publish --repository testpypi

# Dry run
uv run hive publish --dry-run
```

---

## Full Example: Task Manager

### Step 1: Create Project

```bash
uv run hive new taskmanager --features all
cd taskmanager
```

### Step 2: Define Commands

```python
# src/taskmanager/app.py
from hive import App, command, query, entity
from hive.types import PositiveInt, NonEmptyStr
from sqlmodel import Field

app = App("taskmanager")

@entity(app)
class Task:
    id: int | None = Field(default=None, primary_key=True)
    title: str
    priority: int = 1
    completed: bool = False

@command(app, entities=[Task])
async def create_task(ctx, title: NonEmptyStr, priority: PositiveInt = 1) -> Task:
    """Create a new task."""
    task = Task(title=title, priority=priority)
    ctx.db.add(task)
    await ctx.db.commit()
    return task

@query(app, entities=[Task])
async def list_tasks(ctx, completed: bool = False) -> list[Task]:
    """List tasks by completion status."""
    return await ctx.db.query(Task).filter(Task.completed == completed).all()
```

### Step 3: Export Specification

```bash
uv run hive spec export --format json -o spec.json
```

### Step 4: Start All Interfaces

```bash
# Terminal 1: CLI (always available)
uv run python -m taskmanager create_task "My first task" --priority 2

# Terminal 2: Development server (TUI + REST + MCP)
uv run hive dev --interfaces tui,rest,mcp
```

### Step 5: Test Integration

```bash
# REST API
curl -X POST http://localhost:8000/commands/create_task \
  -H "Content-Type: application/json" \
  -d '{"title": "REST task", "priority": 3}'

# MCP (configure Claude Desktop, then ask Claude)
# "Create a high priority task called 'Urgent review'"

# TUI (opens in terminal)
uv run python -m taskmanager --tui
```

---

## Troubleshooting

### Common Issues

**"Module 'fastmcp' not found"**
```bash
# MCP features require optional dependency
uv sync --extra mcp
```

**"Module 'fastapi' not found"**
```bash
# REST features require optional dependency
uv sync --extra rest
```

**"Permission denied on port 80"**
```bash
# Use non-privileged port
uv run hive serve --port 8000
```

**"MCP server not appearing in Claude"**
1. Check `claude_desktop_config.json` syntax
2. Restart Claude Desktop
3. Check MCP server logs: `uv run hive mcp serve 2>&1 | tee mcp.log`

### Debug Mode

```bash
# Verbose logging
HIVE_LOG_LEVEL=debug uv run hive serve

# JSON error details
uv run hive spec export --format json 2>&1 | jq .
```
