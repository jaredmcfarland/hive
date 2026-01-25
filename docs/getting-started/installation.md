# Installation

This guide covers installing the Hive framework and its optional dependencies.

## Prerequisites

!!! info "Python Version"
    Hive requires **Python 3.12** or later. This enables modern type syntax like
    `class Foo[T]:` and improved performance.

Verify your Python version:

```bash
python --version
# Python 3.12.0 or higher
```

## Installing Hive

### Using pip

```bash
pip install hive
```

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package manager that Hive uses
internally for development.

```bash
uv pip install hive
```

Or add to your project:

```bash
uv add hive
```

## Optional Dependencies

Hive provides optional dependency groups for additional features:

### MCP Server Support

For [Model Context Protocol](https://modelcontextprotocol.io/) server generation:

```bash
pip install hive[mcp]
# or
uv add hive[mcp]
```

### REST API Support

For FastAPI REST endpoint generation:

```bash
pip install hive[rest]
# or
uv add hive[rest]
```

### Development Tools

For testing utilities, contract verification, and property-based testing:

```bash
pip install hive[dev]
# or
uv add hive[dev]
```

### All Optional Dependencies

Install everything:

```bash
pip install hive[mcp,rest,dev]
# or
uv add hive[mcp,rest,dev]
```

## Verifying Installation

After installation, verify Hive is working:

```bash
hive --version
```

You should see output like:

```
hive 0.1.0
```

!!! success "Ready to Go"
    If you see the version number, Hive is installed correctly.
    Continue to the [Quick Start](quickstart.md) to create your first project.

## Troubleshooting

### Command Not Found

If `hive` is not found, ensure your Python scripts directory is in your PATH:

```bash
# Check where pip installs scripts
python -m site --user-base
# Add the bin subdirectory to your PATH
```

### Python Version Errors

If you see import errors related to type syntax, verify you're using Python 3.12+:

```bash
python --version
```

!!! tip "Virtual Environments"
    We recommend using virtual environments to isolate your Hive projects:

    ```bash
    # Using uv
    uv venv
    source .venv/bin/activate

    # Using standard venv
    python -m venv .venv
    source .venv/bin/activate
    ```
