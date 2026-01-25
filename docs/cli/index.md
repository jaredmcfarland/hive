# CLI Reference

The `hive` command-line interface provides tools for building, managing, and serving Hive applications. All commands support both human-readable (Rich-formatted) output and machine-parseable JSON output.

## Overview

Hive CLI follows a terminal-agent-native design philosophy:

- **Human-friendly by default**: Rich formatting with colors, tables, and progress indicators
- **Machine-parseable on demand**: Every command supports `--json` for automated tooling
- **Headless operation**: Commands work without interactive prompts
- **Confirmation bypass**: `--yes` flags for CI/CD pipelines

## Installation

The CLI is installed automatically with the Hive framework:

```bash
pip install hive-framework
```

Or with optional features:

```bash
pip install hive-framework[tui,mcp,rest]
```

## Output Formats

### Default (Rich)

Human-readable output with colors, tables, and formatting:

```bash
hive new myapp
```

```
Created project: /home/user/myapp

Next steps:
  cd myapp
  uv sync
  myapp hello
```

### JSON Mode

Machine-parseable JSON output for scripting and automation:

```bash
hive new myapp --json
```

```json
{
  "path": "/home/user/myapp",
  "name": "myapp",
  "next_steps": ["cd myapp", "uv sync", "myapp hello"]
}
```

!!! tip "JSON for Automation"
    Always use `--json` when parsing command output in scripts or CI pipelines.
    This ensures stable, structured output that won't break when formatting changes.

## Common Flags

These flags are available on most commands:

| Flag | Description |
|------|-------------|
| `--help`, `-h` | Show command help and usage |
| `--version`, `-V` | Show Hive framework version |
| `--json` | Output as JSON for machine parsing |

## Command Groups

The CLI is organized into logical command groups:

| Group | Description |
|-------|-------------|
| `hive new` | Create new Hive projects |
| `hive dev` | Development server with hot reload |
| `hive build` | Build distribution artifacts |
| `hive publish` | Publish to PyPI |
| `hive spec` | Export and compare specifications |
| `hive mcp` | MCP server management |
| `hive serve` | REST API server |
| `hive docs` | Documentation generation |
| `hive test` | Test generation |

## Quick Start

```bash
# Create a new project with all features
hive new myapp --features all

# Navigate and install
cd myapp
uv sync

# Start development with REST API
hive dev --interfaces cli,rest

# Export specification
hive spec export --format json -o spec.json
```

## Environment Variables

Hive CLI respects the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `HIVE_DATABASE_URL` | Database connection URL | `sqlite+aiosqlite:///$HOME/.hive/data.db` |
| `HIVE_DEBUG` | Enable debug mode | `false` |
| `HIVE_LOG_LEVEL` | Logging level | `INFO` |
| `HIVE_API_KEY` | API key for REST authentication | (none) |

## Error Handling

Commands return appropriate exit codes:

| Exit Code | Meaning |
|-----------|---------|
| `0` | Success |
| `1` | General error |
| `2` | Invalid arguments |

In JSON mode, errors are returned as structured objects:

```json
{
  "error": "Directory already exists: /home/user/myapp"
}
```
