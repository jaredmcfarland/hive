# Commands

Complete reference for all Hive CLI commands.

## Project Management

### hive new

Create a new Hive project with scaffolding.

```bash
hive new <name> [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `name` | Project name (valid Python identifier, hyphens converted to underscores) |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Directory to create project in | Current directory |
| `--description`, `-d` | Project description | "A Hive application" |
| `--author`, `-a` | Author name | (empty) |
| `--features`, `-f` | Features to enable (comma-separated: `tui`, `mcp`, `rest`, `all`) | (none) |
| `--force` | Overwrite existing directory | `false` |
| `--json` | Output as JSON | `false` |

**Examples:**

```bash
# Basic project
hive new myapp

# With features
hive new myapp --features tui,mcp,rest

# Full specification
hive new myapp \
  --author "Jane Doe" \
  --description "Task management CLI" \
  --features all
```

**Generated Structure:**

```
myapp/
├── pyproject.toml
├── README.md
├── src/
│   └── myapp/
│       ├── __init__.py
│       └── app.py
└── tests/
    ├── __init__.py
    └── test_myapp.py
```

---

### hive dev

Start development server with hot reload.

```bash
hive dev [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--interfaces`, `-i` | Interfaces to enable (comma-separated: `cli`, `tui`, `rest`, `mcp`) | `cli` |
| `--rest-port` | REST API port | `8000` |
| `--mcp-port` | MCP server port | `8080` |

**Examples:**

```bash
# CLI-only development (file watching)
hive dev

# With REST API
hive dev --interfaces cli,rest

# Multiple interfaces with custom ports
hive dev --interfaces rest,mcp --rest-port 3000 --mcp-port 3001
```

!!! note "Hot Reload Behavior"
    - REST and MCP servers restart automatically on file changes
    - CLI mode watches files and reports changes (no server to restart)
    - Only Python files are watched (excludes `__pycache__`, `.venv`)

---

### hive build

Build project distribution artifacts.

```bash
hive build [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--format`, `-f` | Build formats (comma-separated: `wheel`, `sdist`) | `wheel` |
| `--clean`, `-c` | Clean `dist/` before building | `false` |
| `--json` | Output as JSON | `false` |

**Examples:**

```bash
# Build wheel only
hive build

# Build wheel and sdist
hive build --format wheel,sdist

# Clean build
hive build --clean --format wheel,sdist
```

---

### hive publish

Publish package to repository.

```bash
hive publish [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--repository`, `-r` | Target repository (`pypi`, `testpypi`) | `pypi` |
| `--dry-run` | Simulate without uploading | `false` |
| `--json` | Output as JSON | `false` |

**Examples:**

```bash
# Publish to PyPI
hive publish

# Test on TestPyPI first
hive publish --repository testpypi

# Dry run
hive publish --dry-run
```

---

## Specification Management

### hive spec export

Export application specification as JSON Schema or TOML.

```bash
hive spec export [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--format`, `-f` | Output format (`json` or `toml`) | `json` |
| `--output`, `-o` | Output file path (stdout if not specified) | (stdout) |
| `--include-internal` | Include hidden/internal commands | `false` |
| `--json` | Output machine-readable JSON | `false` |

**Examples:**

```bash
# Export to stdout
hive spec export --format json

# Export to file
hive spec export --format json -o spec.json

# Export as TOML
hive spec export --format toml -o spec.toml
```

---

### hive spec diff

Compare two specification files and identify differences.

```bash
hive spec diff <v1_path> <v2_path> [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `v1_path` | Path to first specification file (older version) |
| `v2_path` | Path to second specification file (newer version) |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--format`, `-f` | Output format (`text` or `json`) | `text` |
| `--fail-on-breaking` | Exit with error code if breaking changes detected | `false` |
| `--json` | Output machine-readable JSON | `false` |

**Examples:**

```bash
# Compare specifications
hive spec diff v1.json v2.json

# CI mode - fail on breaking changes
hive spec diff v1.json v2.json --fail-on-breaking

# JSON output for tooling
hive spec diff v1.json v2.json --format json
```

**Output:**

```
Comparing v1.json (1.0.0) → v2.json (1.1.0)

BREAKING CHANGES (1):
  ✗ commands.create_task.parameters.priority: REMOVED

Changes (3):
  + commands.archive_task: ADDED
  ~ commands.create_task.description: MODIFIED
  - queries.get_stats: REMOVED

Summary: 1 breaking change, 3 total changes
```

---

## Server Management

### hive mcp serve

Start MCP (Model Context Protocol) server.

```bash
hive mcp serve [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--transport`, `-t` | Transport protocol (`stdio` or `sse`) | `stdio` |
| `--host`, `-h` | Host to bind (SSE transport only) | `127.0.0.1` |
| `--port`, `-p` | Port to listen on (SSE transport only) | `8080` |
| `--include-queries` | Include queries as read-only tools | `false` |
| `--json` | Output machine-readable JSON on error | `false` |

**Examples:**

```bash
# stdio transport (default, for Claude Desktop)
hive mcp serve

# SSE transport for web clients
hive mcp serve --transport sse

# Custom port
hive mcp serve --transport sse --port 3000
```

!!! info "MCP Dependency"
    MCP server requires the `fastmcp` package:
    ```bash
    pip install hive-framework[mcp]
    ```

---

### hive serve

Start REST API server.

```bash
hive serve [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--host`, `-h` | Host to bind to | `127.0.0.1` |
| `--port`, `-p` | Port to listen on | `8000` |
| `--reload`, `-r` | Enable hot reload on code changes | `false` |
| `--workers`, `-w` | Number of worker processes | `1` |
| `--auth`, `-a` | Authentication type (`none`, `api_key`, `bearer`, `basic`) | `none` |
| `--api-key-header` | Header name for API key auth | `X-API-Key` |
| `--api-key-env` | Environment variable for API key | `HIVE_API_KEY` |
| `--debug`, `-d` | Enable debug mode | `false` |
| `--json` | Output status as JSON | `false` |

**Examples:**

```bash
# Development server
hive serve --reload

# Production server
hive serve --host 0.0.0.0 --port 8000 --workers 4

# With API key authentication
HIVE_API_KEY=secret123 hive serve --auth api_key
```

**Generated Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/spec` | GET | Application specification |
| `/commands/{name}` | POST | Execute command |
| `/queries/{name}` | GET | Execute query |
| `/docs` | GET | OpenAPI documentation |

!!! info "REST Dependency"
    REST server requires FastAPI and uvicorn:
    ```bash
    pip install hive-framework[rest]
    ```

---

## Documentation Generation

### hive docs generate

Generate documentation from application specification.

```bash
hive docs generate [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--format`, `-f` | Output format (`markdown`, `manpage`) | `markdown` |
| `--output`, `-o` | Output directory (stdout if not specified) | (stdout) |
| `--include-private` | Include private commands (underscore-prefixed) | `false` |
| `--include-examples/--no-examples` | Include usage examples from docstrings | `true` |
| `--include-contracts/--no-contracts` | Include @requires/@ensures documentation | `true` |
| `--json` | Output result as JSON | `false` |

**Examples:**

```bash
# Generate markdown to stdout
hive docs generate --format markdown

# Generate to directory
hive docs generate --format markdown --output docs/

# Generate man pages
hive docs generate --format manpage --output man/
```

---

## Test Generation

### hive test generate-conformance

Generate conformance tests from `@requires`/`@ensures` contracts.

```bash
hive test generate-conformance [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--output`, `-o` | Output file path (stdout if not specified) | (stdout) |
| `--json` | Output result as JSON | `false` |

**Examples:**

```bash
# Generate to stdout
hive test generate-conformance

# Generate to file
hive test generate-conformance --output tests/test_conformance.py
```

**Generated Tests:**

- `@requires` tests: Verify preconditions are enforced
- `@ensures` tests: Verify postconditions hold after execution
- `@invariant` tests: Verify class invariants are maintained

---

### hive test generate-properties

Generate property-based tests using Hypothesis.

```bash
hive test generate-properties [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--output`, `-o` | Output file path (stdout if not specified) | (stdout) |
| `--json` | Output result as JSON | `false` |

**Examples:**

```bash
# Generate to stdout
hive test generate-properties

# Generate to file
hive test generate-properties --output tests/test_properties.py
```

**Generated Tests:**

- Use `strategy_for_type()` for parameter generation
- Test that commands accept valid inputs
- Test that type constraints are enforced
