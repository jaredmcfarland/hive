# API Reference

This section documents the Python API for building Hive applications.

## Overview

Hive provides a decorator-based framework for building terminal-agent-native applications. The API is organized into the following modules:

| Module | Description |
|--------|-------------|
| [App](app.md) | Main application class and entry point |
| [Decorators](decorators.md) | `@command`, `@query`, `@entity`, `@screen`, `@service` |
| [Types](types.md) | Refinement types for validated parameters |
| [Contracts](contracts.md) | Design-by-contract decorators |
| [Testing](testing.md) | Testing utilities and mocks |

## Quick Start

```python
from hive import App, command, query, entity
from hive.types import PositiveInt, NonEmptyStr

app = App("myapp", description="My application")

@command(app)
async def create_item(ctx, name: NonEmptyStr, count: PositiveInt = 1) -> dict:
    """Create a new item."""
    return {"name": name, "count": count}

@query(app)
async def list_items(ctx, limit: PositiveInt = 10) -> list[dict]:
    """List all items."""
    return []

if __name__ == "__main__":
    app.cli()()
```

## Module Hierarchy

```
hive
├── App                 # Main application class
├── command             # Command decorator
├── query               # Query decorator
├── entity              # Entity decorator
├── screen              # Screen decorator
├── service             # Service decorator
├── types/              # Refinement types
│   ├── PositiveInt
│   ├── NonEmptyStr
│   ├── Email
│   └── ...
├── contracts/          # Contract decorators
│   ├── requires
│   ├── ensures
│   └── invariant
└── testing/            # Testing utilities
    ├── TestClient
    ├── MockExecutionContext
    └── strategy_for_type
```

## Import Patterns

### Core Imports

```python
# Main entry point
from hive import App

# Decorators
from hive import command, query, entity, screen, service

# Types for parameters
from hive.types import PositiveInt, NonEmptyStr, Email, Port

# Contracts for validation
from hive.contracts import requires, ensures, invariant

# Testing utilities
from hive.testing import TestClient, MockExecutionContext, strategy_for_type
```

### Error Types

```python
from hive import (
    HiveError,           # Base exception
    CommandError,        # Command execution errors
    ValidationError,     # Validation failures
    ConfigurationError,  # Configuration issues
    CredentialError,     # Credential lookup failures
    RegistrationError,   # Decorator registration errors
)
```

### Generators (Optional Features)

```python
from hive import MCPGenerator, RESTGenerator
from hive import build_specification, export_specification, diff_specifications
```
