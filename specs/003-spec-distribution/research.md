# Research: Specification and Distribution

**Branch**: `003-spec-distribution` | **Date**: 2026-01-18

## Research Questions Resolved

### 1. JSON Schema Draft 2020-12 Compliance

**Decision**: Use Pydantic's built-in `model_json_schema()` + custom constraint mapping from `hive.types.introspection`

**Rationale**:
- Pydantic v2's default schema dialect is `https://json-schema.org/draft/2020-12/schema`
- Pydantic automatically maps Python types to JSON Schema types
- Custom refinement types (beartype `Annotated[]`) need manual constraint extraction

**Constraint Mapping Strategy**:

| Hive Constraint | JSON Schema | Source |
|-----------------|-------------|--------|
| `min_value` | `minimum` | `ConstraintInfo.min_value` |
| `max_value` | `maximum` | `ConstraintInfo.max_value` |
| `min_length` | `minLength` | `ConstraintInfo.min_length` |
| `max_length` | `maxLength` | `ConstraintInfo.max_length` |
| `pattern` | `pattern` | `ConstraintInfo.pattern` |
| `description` | `description` | Docstring + constraint description |

**Implementation Approach**:
```python
from pydantic.json_schema import GenerateJsonSchema

class HiveSchemaGenerator(GenerateJsonSchema):
    def generate(self, schema, mode='validation'):
        json_schema = super().generate(schema, mode=mode)
        json_schema['$schema'] = self.schema_dialect
        # Add Hive-specific extensions
        return json_schema
```

**Alternatives Considered**:
1. Raw `json` module - Rejected: No schema generation capability
2. `jsonschema` library - Rejected: For validation, not generation
3. Manual schema construction - Rejected: Duplicates Pydantic's work

**Sources**: [Pydantic JSON Schema Docs](https://docs.pydantic.dev/latest/concepts/json_schema/)

---

### 2. FastMCP Integration Best Practices

**Decision**: Use FastMCP 2.x with `@mcp.tool` decorator pattern, pin to `fastmcp<3`

**Rationale**:
- FastMCP 2.0 is production-ready and actively maintained
- Decorators match Hive's existing `@command` pattern
- Automatic parameter validation from type hints
- Supports both stdio and SSE transports

**Key Implementation Patterns**:

```python
from fastmcp import FastMCP

mcp = FastMCP("hive-app")

@mcp.tool
async def create_task(title: str, priority: int = 1) -> dict:
    """Create a new task."""
    # Tool implementation
    return {"id": 1, "title": title}
```

**Transport Configuration**:
- **stdio**: Default, process isolation (Claude Desktop subprocess)
- **sse**: Network access via `--transport sse --port 8080`

**Security Considerations**:
- Never write to stdout in stdio mode (breaks protocol)
- Use logging library with stderr/file output
- Implement rate limiting for SSE transport
- Path validation for file operations

**Alternatives Considered**:
1. Official MCP Python SDK - Rejected: FastMCP provides better DX
2. Manual MCP protocol - Rejected: Error-prone, unnecessary

**Sources**:
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [MCP Build Server Guide](https://modelcontextprotocol.io/docs/develop/build-server)

---

### 3. FastAPI Dynamic Endpoint Generation

**Decision**: Generate routes at app startup using `app.add_api_route()` from registry

**Rationale**:
- FastAPI supports runtime route registration
- Pydantic models can be created dynamically with `create_model()`
- MCPO project demonstrates this exact pattern for MCP→REST

**Implementation Pattern**:

```python
from fastapi import FastAPI
from pydantic import create_model

def generate_rest_api(app_instance) -> FastAPI:
    api = FastAPI(title=f"{app_instance.name} API")

    for cmd in app_instance.registry.list_commands():
        # Create request model from command parameters
        fields = {p.name: (p.type, ...) for p in cmd.parameters if p.name != "ctx"}
        RequestModel = create_model(f"{cmd.name}Request", **fields)

        # Register endpoint
        api.add_api_route(
            f"/commands/{cmd.name}",
            create_command_handler(cmd),
            methods=["POST"],
            response_model=cmd.return_type,
        )

    return api
```

**URL Structure**:
- Commands: `POST /commands/{command_name}`
- Queries: `GET /queries/{query_name}`
- OpenAPI: `GET /docs`

**Alternatives Considered**:
1. Code generation - Rejected: Runtime generation simpler, no build step
2. APIRouter per command - Rejected: Overhead for many commands
3. Single catch-all endpoint - Rejected: Poor OpenAPI documentation

**Sources**:
- [FastAPI Dynamic Routes](https://github.com/skitsanos/fastapi-dynamic-routes)
- [Schema-Driven FastAPI](https://medium.com/@connect.hashblock/schema-driven-fastapi-how-i-auto-generated-endpoints-from-dynamic-models-44377c17d0e6)

---

### 4. Specification Diff Algorithm

**Decision**: Use DeepDiff library with custom JSON Schema diff post-processing

**Rationale**:
- DeepDiff handles nested structures and type changes
- Provides detailed change paths (added/removed/changed)
- Security-patched and actively maintained (v8.6.1)
- Supports ignoring order in lists

**Breaking Change Detection**:

| Change Type | Breaking? | Detection |
|-------------|-----------|-----------|
| Command removed | YES | `dictionary_item_removed` in commands |
| Parameter removed | YES | `dictionary_item_removed` in params |
| Parameter type changed | YES | `type_changes` in params |
| Required → Optional | NO | `values_changed` + default added |
| Optional → Required | YES | `values_changed` + default removed |
| Return type changed | MAYBE | `type_changes` (warn) |
| Command added | NO | `dictionary_item_added` |

**Implementation Pattern**:

```python
from deepdiff import DeepDiff

def diff_specifications(v1: dict, v2: dict) -> SpecificationDiff:
    diff = DeepDiff(v1, v2, ignore_order=True)

    breaking_changes = []
    for path in diff.get('dictionary_item_removed', []):
        if 'commands' in path or 'parameters' in path:
            breaking_changes.append(f"REMOVED: {path}")

    return SpecificationDiff(
        added=diff.get('dictionary_item_added', []),
        removed=diff.get('dictionary_item_removed', []),
        changed=diff.get('values_changed', {}),
        breaking_changes=breaking_changes,
    )
```

**Alternatives Considered**:
1. `jsondiff` - Rejected: Less capable with complex structures
2. Custom implementation - Rejected: DeepDiff covers edge cases
3. Git diff - Rejected: Not semantic, line-based

**Sources**:
- [DeepDiff PyPI](https://pypi.org/project/deepdiff/)
- [DeepDiff Medium Guide](https://medium.com/@ssspidersilk/debugging-with-deepdiff-deep-differences-in-python-json-dicts-objects-51b5647d4ea9)

---

### 5. Hot Reload Implementation

**Decision**: Use `watchfiles` library (Rust-based, same author as Pydantic)

**Rationale**:
- Written in Rust for performance (rust-notify backend)
- Same author as Pydantic (Samuel Colvin) - ecosystem alignment
- Used by Uvicorn for `--reload`
- Supports async watching with `awatch`

**Implementation Pattern**:

```python
from watchfiles import awatch, run_process

# For process-based reload (CLI dev server)
async def dev_server(app_path: str):
    run_process(
        app_path,
        target=start_server,
        callback=on_reload,
    )

# For in-process detection
async def watch_for_changes(path: str):
    async for changes in awatch(path):
        for change_type, file_path in changes:
            print(f"Detected {change_type} in {file_path}")
            # Trigger reload
```

**Configuration**:
- Watch paths: `src/` directory by default
- Ignore patterns: `__pycache__`, `.git`, `*.pyc`
- Debounce: 50ms default (configurable)

**Alternatives Considered**:
1. `watchdog` - Rejected: Pure Python, slower on large codebases
2. `jurigged` - Rejected: Hot-patches live code (risky for production patterns)
3. Textual's built-in - Rejected: TUI-specific, not general purpose

**Sources**:
- [watchfiles GitHub](https://github.com/samuelcolvin/watchfiles)
- [watchfiles PyPI](https://pypi.org/project/watchgod/)

---

## New Dependencies Required

| Package | Version | Purpose |
|---------|---------|---------|
| `fastmcp` | `>=2.0,<3` | MCP server generation |
| `fastapi` | `>=0.100.0` | REST API generation |
| `uvicorn` | `>=0.23.0` | ASGI server for REST |
| `deepdiff` | `>=8.0.0` | Specification diffing |
| `watchfiles` | `>=1.0.0` | Hot reload detection |
| `tomli-w` | `>=1.0.0` | TOML export |

## Existing Infrastructure Leveraged

- `hive.types.introspection.extract_constraints()` - Constraint extraction ready
- `hive.core.types.ConstraintMetadata` - Constraint data structure ready
- `hive.runtime.output.OutputFormatter` - JSON output already supported
- `hive.generators.cli.CLIGenerator` - Pattern to follow for new generators
