# Testing

Hive provides comprehensive testing utilities for unit testing commands, property-based testing with Hypothesis, and TUI testing with Textual's pilot.

## Overview

| Utility | Purpose |
|---------|---------|
| `TestClient` | High-level testing interface for commands and queries |
| `MockExecutionContext` | Mock context for isolated unit testing |
| `strategy_for_type` | Generate Hypothesis strategies for refinement types |
| `TUITestHelper` | Helper for testing Textual screens |

## TestClient

High-level testing interface that makes it easy to test commands and queries.

```python
from hive.testing import TestClient

async def test_create_task():
    async with TestClient(app) as client:
        result = await client.invoke("create_task", title="Test Task")
        assert result.id is not None
        assert result.title == "Test Task"
```

### Constructor

```python
TestClient(
    app: App,
    *,
    services: dict[str, Any] | None = None,
    db_url: str = "sqlite+aiosqlite:///:memory:",
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `app` | `App` | Hive application to test |
| `services` | `dict` | Dictionary of service mocks to inject |
| `db_url` | `str` | Reserved for future database support |

### Methods

#### `invoke(command_name, **kwargs)`

Execute a command by name:

```python
async with TestClient(app) as client:
    result = await client.invoke("create_task", title="My Task", priority=1)
    assert result.id is not None
```

#### `query(query_name, **kwargs)`

Execute a query by name:

```python
async with TestClient(app) as client:
    tasks = await client.query("list_tasks", status="active")
    assert len(tasks) > 0
```

#### `get_output()`

Get captured output lines:

```python
async with TestClient(app) as client:
    await client.invoke("hello", name="World")
    output = client.get_output()
    assert "Hello, World!" in output
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `invocation_count` | `int` | Number of commands/queries invoked |
| `last_result` | `Any` | Result of the most recent invocation |

### Service Mocking

Inject mock services for isolated testing:

```python
from unittest.mock import MagicMock

async def test_with_mock_service():
    mock_api = MagicMock()
    mock_api.get.return_value = {"data": [1, 2, 3]}

    async with TestClient(app, services={"api_client": mock_api}) as client:
        result = await client.invoke("fetch_data")
        mock_api.get.assert_called_once()
```

## MockExecutionContext

Low-level mock context for unit testing individual commands.

```python
from hive.testing import MockExecutionContext

async def test_my_command():
    async with MockExecutionContext() as ctx:
        result = await my_command(ctx, arg="value")
        assert ctx.db.add.called
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `db` | `AsyncMock` | Mock database session |
| `config` | `MagicMock` | Mock configuration |
| `output` | `MagicMock` | Mock output formatter |

### Methods

| Method | Description |
|--------|-------------|
| `commit()` | Mock commit (no-op) |
| `rollback()` | Mock rollback (no-op) |

### Example: Testing Database Operations

```python
async def test_create_task():
    async with MockExecutionContext() as ctx:
        # Configure mock return value
        ctx.db.execute.return_value.scalar_one_or_none.return_value = None

        result = await create_task(ctx, title="Test")

        # Verify database operations
        ctx.db.add.assert_called_once()
        ctx.db.commit.assert_called_once()
```

## strategy_for_type

Generate Hypothesis strategies that produce valid values for refinement types.

```python
from hypothesis import given
from hive.testing import strategy_for_type
from hive.types import PositiveInt, Email

@given(x=strategy_for_type(PositiveInt))
def test_positive_int(x):
    assert x > 0

@given(email=strategy_for_type(Email))
def test_email(email):
    assert "@" in email
```

### Supported Types

The function handles:

- Plain types (`int`, `str`, `float`, `bool`)
- Annotated types with beartype constraints
- Generic types (`list[T]`, `dict[K, V]`)
- All Hive refinement types

### Pre-Built Strategies

```python
from hive.testing.strategies import (
    positive_integers,     # st.integers(min_value=1)
    non_negative_integers, # st.integers(min_value=0)
    percentages,           # st.floats(0.0, 100.0)
    unit_intervals,        # st.floats(0.0, 1.0)
    ports,                 # st.integers(1, 65535)
    non_empty_strings,     # st.text(min_size=1)
)
```

### Property-Based Testing Example

```python
from hypothesis import given, settings
from hive.testing import strategy_for_type, TestClient
from hive.types import PositiveInt, NonEmptyStr

@given(
    task_id=strategy_for_type(PositiveInt),
    title=strategy_for_type(NonEmptyStr),
)
@settings(max_examples=100)
async def test_create_and_get_task(task_id, title):
    async with TestClient(app) as client:
        created = await client.invoke("create_task", title=title)
        assert created.title == title

        retrieved = await client.query("get_task", task_id=created.id)
        assert retrieved.title == title
```

## TUI Testing

Utilities for testing Textual-based TUI screens.

### TUITestHelper

```python
from hive.testing import TUITestHelper, create_test_app

async def test_dashboard_screen():
    app = create_test_app(screens=[DashboardScreen])
    async with TUITestHelper(app) as helper:
        await helper.navigate_to("DashboardScreen")
        # Test screen interactions
```

### create_test_app

Create a test application with specific screens:

```python
from hive.testing import create_test_app

app = create_test_app(
    screens=[HomeScreen, SettingsScreen],
    default_screen=HomeScreen,
)
```

### register_test_command / register_test_query

Register test commands and queries for TUI testing:

```python
from hive.testing import register_test_command, register_test_query

register_test_command(app, "test_cmd", lambda ctx: {"result": "ok"})
register_test_query(app, "test_query", lambda ctx: [1, 2, 3])
```

## ConformanceGenerator

Generate contract conformance tests automatically.

```python
from hive.testing import ConformanceGenerator

generator = ConformanceGenerator(app)
result = generator.generate()

for test_case in result.test_cases:
    print(f"Test: {test_case.name}")
    print(f"  Command: {test_case.command_name}")
    print(f"  Contracts: {test_case.contracts}")
```

## PropertyGenerator

Generate property-based tests for commands.

```python
from hive.testing import PropertyGenerator

generator = PropertyGenerator(app)
result = generator.generate()

for test_case in result.test_cases:
    print(f"Test: {test_case.name}")
    print(f"  Properties: {test_case.properties}")
```

## Complete Testing Example

```python
import pytest
from hypothesis import given, settings
from hive.testing import TestClient, MockExecutionContext, strategy_for_type
from hive.types import PositiveInt, NonEmptyStr
from hive.errors import CommandError

# Unit test with MockExecutionContext
async def test_create_task_unit():
    async with MockExecutionContext() as ctx:
        result = await create_task(ctx, title="Test Task")
        ctx.db.add.assert_called_once()
        ctx.db.commit.assert_called_once()

# Integration test with TestClient
async def test_create_task_integration():
    async with TestClient(app) as client:
        result = await client.invoke("create_task", title="Test Task")
        assert result.title == "Test Task"
        assert client.invocation_count == 1

# Property-based test
@given(title=strategy_for_type(NonEmptyStr))
@settings(max_examples=50)
async def test_create_task_property(title):
    async with TestClient(app) as client:
        result = await client.invoke("create_task", title=title)
        assert result.title == title

# Contract violation test
async def test_invalid_task_id_raises():
    async with TestClient(app) as client:
        with pytest.raises(CommandError, match="Task ID must be positive"):
            await client.invoke("get_task", task_id=-1)

# Service mock test
async def test_external_service():
    from unittest.mock import MagicMock

    mock_api = MagicMock()
    mock_api.get.return_value = {"status": "ok"}

    async with TestClient(app, services={"external_api": mock_api}) as client:
        result = await client.invoke("check_status")
        mock_api.get.assert_called_once()
        assert result["status"] == "ok"
```

## API Reference

::: hive.testing.TestClient
    options:
      show_root_heading: true
      show_source: false
      members:
        - __init__
        - invoke
        - query
        - get_output
        - invocation_count
        - last_result

::: hive.testing.MockExecutionContext
    options:
      show_root_heading: true
      show_source: false
      members:
        - db
        - config
        - output
        - commit
        - rollback

::: hive.testing.strategy_for_type
    options:
      show_root_heading: true
      show_source: false
