# Minimal Hive Example

The simplest possible Hive application - a single command that says hello.

## Learning Objectives

After studying this example, you will understand:

1. **Basic App Setup** - How to create a Hive App instance
2. **Command Definition** - How to use the `@command` decorator
3. **Execution Context** - How commands receive an `ExecutionContext`
4. **Testing** - How to test commands with `TestClient`

## Project Structure

```
minimal/
├── src/
│   └── minimal/
│       └── __init__.py    # App definition and hello command
├── tests/
│   └── test_hello.py      # Tests using TestClient
├── pyproject.toml         # Project configuration
└── README.md              # This file
```

## Quick Start

```bash
# Install dependencies
uv sync --dev

# Run the hello command
uv run python -c "
import asyncio
from minimal import app
from hive.runtime.context import ExecutionContext

async def main():
    # Simple direct invocation for demo
    print('Hello, World!')

asyncio.run(main())
"

# Run tests
uv run pytest
```

## Code Walkthrough

### 1. Creating the App

```python
from hive.app import App

app = App("minimal")
```

Every Hive application starts with an `App` instance. The name is used for CLI generation and documentation.

### 2. Defining a Command

```python
from hive.core.decorators import command

@command(app)
async def hello(ctx: ExecutionContext, name: str = "World") -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"
```

The `@command` decorator registers the function with the app. Commands:
- Are async functions
- Receive an `ExecutionContext` as first argument
- Can have typed parameters with defaults
- Return a value (or None)

### 3. Testing with TestClient

```python
from hive.testing import TestClient

async def test_hello():
    async with TestClient(app) as client:
        result = await client.invoke("hello", name="Alice")
        assert result == "Hello, Alice!"
```

`TestClient` provides:
- Automatic in-memory database setup
- Clean isolation between tests
- Simple invoke/query interface

## Next Steps

Once you understand this example, move on to:

1. **CRUD Example** - Entities, queries, and data persistence
2. **API Client Example** - External service integration
3. **Analytics Example** - DuckDB and rich output formatting
