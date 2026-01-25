# Contracts

Hive provides design-by-contract decorators for explicit preconditions, postconditions, and invariants. These complement refinement types by allowing more complex validation logic.

## Overview

Contract decorators integrate with [deal](https://github.com/life4/deal) but provide Hive-specific error handling with proper CLI exit codes and user-friendly messages.

| Decorator | Purpose | Applied To |
|-----------|---------|------------|
| `@requires` | Precondition - validate inputs | Commands, queries |
| `@ensures` | Postcondition - validate outputs | Commands, queries |
| `@invariant` | Class invariant - maintain consistency | Entities |

## @requires

Validate preconditions before command execution.

```python
from hive import App, command
from hive.contracts import requires

app = App("myapp")

@command(app)
@requires(lambda ctx, task_id: task_id > 0, "Task ID must be positive")
async def get_task(ctx, task_id: int) -> dict:
    """Get a task by ID."""
    ...
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `condition` | `Callable[..., bool]` | Lambda that returns True if precondition is met. Receives same arguments as decorated function. |
| `message` | `str` | Error message if precondition fails (default: "Precondition failed") |

### Multiple Preconditions

Stack multiple `@requires` decorators for complex validation:

```python
@command(app)
@requires(lambda ctx, start, end: start >= 0, "Start must be non-negative")
@requires(lambda ctx, start, end: end > start, "End must be greater than start")
@requires(lambda ctx, start, end: end - start <= 100, "Range cannot exceed 100")
async def get_range(ctx, start: int, end: int) -> list[int]:
    """Get a range of items."""
    ...
```

### Context-Aware Validation

Access context in preconditions for authorization checks:

```python
@command(app)
@requires(
    lambda ctx, resource_id: ctx.user.can_access(resource_id),
    "You don't have permission to access this resource"
)
async def access_resource(ctx, resource_id: int) -> dict:
    """Access a protected resource."""
    ...
```

## @ensures

Validate postconditions after command execution.

```python
from hive import App, command
from hive.contracts import ensures

app = App("myapp")

@command(app)
@ensures(lambda ctx, task_id, result: result.id == task_id)
async def get_task(ctx, task_id: int) -> Task:
    """Get a task by ID."""
    ...
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `condition` | `Callable[..., bool]` | Lambda that returns True if postcondition is met. Receives original arguments plus `result` keyword. |
| `message` | `str` | Error message if postcondition fails (default: "Postcondition failed") |

### Examples

```python
@command(app)
@ensures(lambda ctx, items, result: len(result) == len(items), "All items must be processed")
async def process_items(ctx, items: list[str]) -> list[dict]:
    """Process a list of items."""
    ...

@command(app)
@ensures(lambda ctx, amount, result: result.balance >= 0, "Balance cannot go negative")
async def withdraw(ctx, amount: float) -> Account:
    """Withdraw from account."""
    ...
```

### Combining @requires and @ensures

```python
@command(app)
@requires(lambda ctx, user_id: user_id > 0, "User ID must be positive")
@requires(lambda ctx, user_id: ctx.db.exists(User, user_id), "User must exist")
@ensures(lambda ctx, user_id, result: result is not None, "Must return a user")
@ensures(lambda ctx, user_id, result: result.id == user_id, "Must return correct user")
async def get_user(ctx, user_id: int) -> User:
    """Get a user by ID with full contract validation."""
    ...
```

## @invariant

Define class invariants that must hold for entity instances.

```python
from hive import App, entity
from hive.contracts import invariant
from sqlmodel import Field, SQLModel

app = App("myapp")

@entity(app)
@invariant(lambda self: self.balance >= 0, "Balance cannot be negative")
class Account(SQLModel, table=True):
    """Bank account with balance invariant."""
    id: int | None = Field(default=None, primary_key=True)
    balance: float = 0.0
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `condition` | `Callable[[Any], bool]` | Lambda that returns True if invariant holds. Receives `self`. |
| `message` | `str` | Error message if invariant is violated |

### Multiple Invariants

```python
@entity(app)
@invariant(lambda self: self.start_date <= self.end_date, "Start must be before end")
@invariant(lambda self: self.priority >= 1, "Priority must be at least 1")
@invariant(lambda self: self.priority <= 5, "Priority must be at most 5")
class Task(SQLModel, table=True):
    """Task with multiple invariants."""
    id: int | None = Field(default=None, primary_key=True)
    start_date: date
    end_date: date
    priority: int = 3
```

## Error Handling

Contract violations raise `CommandError` with appropriate exit codes:

| Contract | Exit Code | Description |
|----------|-----------|-------------|
| `@requires` | 1 | Precondition failed (user input error) |
| `@ensures` | 70 | Postcondition failed (internal error) |
| `@invariant` | Varies | Invariant violation (data integrity error) |

```bash
$ myapp get-task -5
Error: Task ID must be positive

$ myapp withdraw 1000
Error: Balance cannot go negative
```

## Best Practices

### Use Contracts for Complex Validation

Use refinement types for simple constraints, contracts for complex logic:

```python
from hive.types import PositiveInt
from hive.contracts import requires

# Simple: Use refinement type
@command(app)
async def simple_cmd(ctx, count: PositiveInt) -> None:
    ...

# Complex: Use contract
@command(app)
@requires(
    lambda ctx, start, end: start < end and (end - start) <= 100,
    "Invalid range: end must be greater than start and range <= 100"
)
async def complex_cmd(ctx, start: int, end: int) -> None:
    ...
```

### Document Contract Semantics

Include contract information in docstrings:

```python
@command(app)
@requires(lambda ctx, amount: amount > 0, "Amount must be positive")
@requires(lambda ctx, amount: amount <= ctx.balance, "Insufficient funds")
@ensures(lambda ctx, amount, result: result.balance == ctx.balance - amount)
async def withdraw(ctx, amount: float) -> Account:
    """Withdraw funds from account.

    Requires:
        - amount > 0
        - amount <= current balance

    Ensures:
        - new balance == old balance - amount
    """
    ...
```

### Test Contract Violations

Verify contracts catch invalid inputs:

```python
import pytest
from hive.errors import CommandError
from hive.testing import TestClient

async def test_requires_catches_invalid_input():
    async with TestClient(app) as client:
        with pytest.raises(CommandError, match="Task ID must be positive"):
            await client.invoke("get_task", task_id=-1)

async def test_ensures_catches_invalid_output():
    async with TestClient(app) as client:
        # Mock database to return wrong task
        client.mock_db_get(Task(id=999))
        with pytest.raises(CommandError, match="Must return correct user"):
            await client.invoke("get_task", task_id=1)
```

## Integration with Testing

Contracts are introspectable for test generation:

```python
from hive.testing import ConformanceGenerator

generator = ConformanceGenerator(app)
tests = generator.generate()

# Generated tests verify contract compliance
for test in tests:
    print(f"Test: {test.name}")
    print(f"  Contracts: {test.contracts}")
```

## API Reference

::: hive.contracts.requires
    options:
      show_root_heading: true
      show_source: false

::: hive.contracts.ensures
    options:
      show_root_heading: true
      show_source: false

::: hive.contracts.invariant
    options:
      show_root_heading: true
      show_source: false
