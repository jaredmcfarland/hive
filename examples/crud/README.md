# CRUD Task Manager Example

A complete CRUD (Create, Read, Update, Delete) application demonstrating
entities, commands, queries, contracts, and refinement types.

## Learning Objectives

After studying this example, you will understand:

1. **Entity Definition** - Using `@entity` with SQLModel
2. **Refinement Types** - Type-safe validation with `NonEmptyStr`, `PositiveInt`
3. **Contract Decorators** - `@requires` and `@ensures` for pre/postconditions
4. **Commands vs Queries** - State modification vs read-only operations
5. **TestClient Integration** - Full CRUD testing patterns

## Project Structure

```
crud/
├── src/
│   └── crud/
│       ├── __init__.py    # App definition and exports
│       ├── entities.py    # Task entity with SQLModel
│       ├── commands.py    # create, update, delete commands
│       └── queries.py     # list, get queries
├── tests/
│   ├── test_commands.py   # Command tests
│   └── test_queries.py    # Query tests
├── pyproject.toml
└── README.md
```

## Quick Start

```bash
# Install dependencies
uv sync --dev

# Run tests
uv run pytest

# Example usage
uv run python -c "
import asyncio
from hive.testing import TestClient
from crud import app

async def demo():
    async with TestClient(app) as client:
        # Create a task
        task = await client.invoke('create_task', title='Learn Hive', priority=1)
        print(f'Created: {task}')

        # List tasks
        tasks = await client.query('list_tasks')
        print(f'All tasks: {tasks}')

asyncio.run(demo())
"
```

## Code Walkthrough

### 1. Entity Definition

```python
from hive.core.decorators import entity
from sqlmodel import Field, SQLModel
from hive.types import NonEmptyStr, PositiveInt

@entity(app)
class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: NonEmptyStr = Field(description="Task title")
    priority: PositiveInt = Field(default=1, description="Priority level")
    completed: bool = Field(default=False)
```

Entities are SQLModel classes decorated with `@entity`. Refinement types
like `NonEmptyStr` and `PositiveInt` provide automatic validation.

### 2. Commands with Contracts

```python
from hive.contracts import requires, ensures

@command(app, entities=[Task])
@requires(lambda ctx, title: len(title) > 0, "Title cannot be empty")
@ensures(lambda ctx, title, priority, result: result.title == title)
async def create_task(ctx, title: str, priority: int = 1) -> Task:
    ...
```

Contracts document and enforce business rules:
- `@requires`: Preconditions that must be true before execution
- `@ensures`: Postconditions that must be true after execution

### 3. Queries with Caching

```python
@query(app, entities=[Task], cache_ttl=60)
async def list_tasks(ctx) -> list[Task]:
    ...
```

Queries are read-only and can be cached for performance.

## Next Steps

1. **API Client Example** - External service integration
2. **Analytics Example** - DuckDB and advanced queries
