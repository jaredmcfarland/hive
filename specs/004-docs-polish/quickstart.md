# Quickstart: Documentation and Polish

**Branch**: `004-docs-polish` | **Date**: 2026-01-24

## Prerequisites

- Hive framework installed with core features (Phases 1-3)
- Python 3.12+
- uv package manager

## Quick Verification

After implementation, verify each milestone:

### Milestone 4.1: Documentation Generation

```bash
# Generate markdown docs for a Hive app
cd examples/crud
uv run hive docs --format markdown --output docs/

# Verify output
ls docs/
# Expected: index.md, commands/*.md, queries/*.md, entities/*.md

# Generate man pages
uv run hive docs --format manpage --output man/

# Test man page
man -l man/crud.1
```

### Milestone 4.2: Testing Utilities

```python
# tests/test_with_client.py
from hive.testing import TestClient

async def test_create_task():
    async with TestClient(app) as client:
        result = await client.invoke("create_task", title="Test")
        assert result.id is not None

# Run tests
uv run pytest tests/test_with_client.py
```

**Generate conformance tests**:
```bash
uv run hive test generate-conformance --output tests/test_conformance.py
uv run pytest tests/test_conformance.py
```

**Generate property tests**:
```bash
uv run hive test generate-properties --output tests/test_properties.py
uv run pytest tests/test_properties.py
```

### Milestone 4.3: Example Applications

```bash
# Run minimal example
cd examples/minimal
uv sync
uv run minimal hello --name World
# Expected: Hello, World!

# Run CRUD example
cd examples/crud
uv sync
uv run crud create --title "My Task" --priority 3
uv run crud list --json
uv run crud tui  # Opens TUI interface

# Run API client example
cd examples/api-client
uv sync
uv run api-client configure --api-key <key>
uv run api-client fetch --endpoint users

# Run analytics example
cd examples/analytics
uv sync
uv run analytics import data.csv
uv run analytics query "SELECT * FROM datapoints LIMIT 10"
```

## Development Workflow

### Adding Documentation Templates

1. Create template in `src/hive/docs/templates/`
2. Register in generator's template loader
3. Add tests for template rendering

### Extending TestClient

1. Add method to `hive.testing.TestClient`
2. Update `__init__.py` exports
3. Add unit test in `tests/unit/test_testclient.py`

### Creating New Example

1. Copy `examples/minimal/` as starting point
2. Update `pyproject.toml` with new name
3. Implement commands/entities
4. Write tests using TestClient
5. Generate docs
6. Update README with features demonstrated

## Common Issues

**Q: Documentation shows "[missing description]" for a command**
A: Add a docstring to the command function.

**Q: TestClient can't find my command**
A: Ensure the app is imported before creating TestClient.

**Q: Property tests fail with "No strategy found"**
A: Register a custom strategy with `register_strategy_for_type()`.

**Q: Man pages show formatting errors**
A: Check for unescaped special characters (backslash, hyphen).
