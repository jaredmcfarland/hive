# Types

Hive provides refinement types with runtime-enforced constraints. Use these in command signatures to get automatic validation with user-friendly error messages.

## Overview

Refinement types are type aliases with additional constraints enforced at runtime by [beartype](https://github.com/beartype/beartype). When a command receives an invalid value, Hive automatically generates a user-friendly CLI error message.

```python
from hive import App, command
from hive.types import PositiveInt, NonEmptyStr, Email

app = App("myapp")

@command(app)
async def create_user(ctx, name: NonEmptyStr, age: PositiveInt, email: Email) -> dict:
    """Create a new user with validated inputs."""
    return {"name": name, "age": age, "email": email}
```

## Numeric Types

### Integer Refinements

| Type | Constraint | Description |
|------|------------|-------------|
| `PositiveInt` | `x > 0` | Integer greater than zero |
| `NonNegativeInt` | `x >= 0` | Integer greater than or equal to zero |
| `NegativeInt` | `x < 0` | Integer less than zero |

```python
from hive.types import PositiveInt, NonNegativeInt, NegativeInt

def example(
    count: PositiveInt,      # 1, 2, 3, ...
    index: NonNegativeInt,   # 0, 1, 2, ...
    offset: NegativeInt,     # -1, -2, -3, ...
) -> None:
    ...
```

### Float Refinements

| Type | Constraint | Description |
|------|------------|-------------|
| `PositiveFloat` | `x > 0.0` | Float greater than zero |
| `NonNegativeFloat` | `x >= 0.0` | Float greater than or equal to zero |
| `UnitInterval` | `0.0 <= x <= 1.0` | Float between 0 and 1 inclusive |
| `Percentage` | `0.0 <= x <= 100.0` | Float between 0 and 100 inclusive |
| `Probability` | `0.0 <= x <= 1.0` | Alias for UnitInterval |

```python
from hive.types import Percentage, UnitInterval, Probability

def example(
    progress: Percentage,    # 0.0 to 100.0
    opacity: UnitInterval,   # 0.0 to 1.0
    chance: Probability,     # 0.0 to 1.0
) -> None:
    ...
```

### Domain-Specific Numeric Types

| Type | Constraint | Description |
|------|------------|-------------|
| `Port` | `1 <= x <= 65535` | Valid TCP/UDP port number |
| `HttpStatusCode` | `100 <= x <= 599` | HTTP status code |
| `UnixTimestamp` | `x >= 0` | Unix timestamp (non-negative) |

```python
from hive.types import Port, HttpStatusCode

@command(app)
async def start_server(ctx, port: Port = 8080) -> dict:
    """Start the server on a valid port."""
    return {"port": port}
```

### Date/Time Components

| Type | Constraint | Description |
|------|------------|-------------|
| `Year` | `1 <= x <= 9999` | Year (1-9999) |
| `Month` | `1 <= x <= 12` | Month (1-12) |
| `Day` | `1 <= x <= 31` | Day of month (1-31) |
| `Hour` | `0 <= x <= 23` | Hour (0-23) |
| `Minute` | `0 <= x <= 59` | Minute (0-59) |
| `Second` | `0 <= x <= 59` | Second (0-59) |

```python
from hive.types import Year, Month, Day

@command(app)
async def set_deadline(ctx, year: Year, month: Month, day: Day) -> dict:
    """Set a deadline with validated date components."""
    return {"year": year, "month": month, "day": day}
```

## String Types

### Basic String Refinements

| Type | Constraint | Description |
|------|------------|-------------|
| `NonEmptyStr` | `len(s) > 0` | Non-empty string |
| `TrimmedStr` | `s == s.strip()` | No leading/trailing whitespace |
| `LowercaseStr` | `s == s.lower()` | All lowercase |
| `UppercaseStr` | `s == s.upper()` | All uppercase |
| `Identifier` | `s.isidentifier()` | Valid Python identifier |

```python
from hive.types import NonEmptyStr, TrimmedStr, Identifier

@command(app)
async def create_variable(ctx, name: Identifier, value: NonEmptyStr) -> dict:
    """Create a variable with a valid Python identifier name."""
    return {"name": name, "value": value}
```

### Format-Validated Strings

| Type | Pattern | Description |
|------|---------|-------------|
| `Slug` | `^[a-z0-9]+(?:-[a-z0-9]+)*$` | URL-safe slug (lowercase, hyphens) |
| `Email` | Email pattern | Email address (basic validation) |
| `Url` | `^https?://...` | HTTP or HTTPS URL |
| `FilePath` | Non-empty, no null bytes | Valid file path |
| `DirectoryPath` | Alias for FilePath | Directory path |

```python
from hive.types import Slug, Email, Url

@command(app)
async def create_post(ctx, slug: Slug, author_email: Email, website: Url) -> dict:
    """Create a blog post with validated fields."""
    return {"slug": slug, "email": author_email, "website": website}
```

## Complete Type Reference

### All Numeric Types

```python
from hive.types import (
    # Integer refinements
    PositiveInt,        # x > 0
    NonNegativeInt,     # x >= 0
    NegativeInt,        # x < 0

    # Float refinements
    PositiveFloat,      # x > 0.0
    NonNegativeFloat,   # x >= 0.0
    UnitInterval,       # 0.0 <= x <= 1.0
    Percentage,         # 0.0 <= x <= 100.0
    Probability,        # Alias for UnitInterval

    # Domain types
    Port,               # 1-65535
    HttpStatusCode,     # 100-599
    UnixTimestamp,      # >= 0

    # Date/Time
    Year,               # 1-9999
    Month,              # 1-12
    Day,                # 1-31
    Hour,               # 0-23
    Minute,             # 0-59
    Second,             # 0-59
)
```

### All String Types

```python
from hive.types import (
    # Basic refinements
    NonEmptyStr,        # len > 0
    TrimmedStr,         # No whitespace padding
    LowercaseStr,       # All lowercase
    UppercaseStr,       # All uppercase
    Identifier,         # Valid Python identifier

    # Format-validated
    Slug,               # URL-safe slug
    Email,              # Email address
    Url,                # HTTP/HTTPS URL
    FilePath,           # Valid file path
    DirectoryPath,      # Valid directory path
)
```

## Error Handling

When validation fails, Hive provides user-friendly error messages:

```bash
$ myapp create-user "" 25 "not-an-email"
Error: name: Value cannot be empty

$ myapp create-user "John" -5 "john@example.com"
Error: age: Value must be greater than 0

$ myapp create-user "John" 25 "not-an-email"
Error: email: Value must be a valid email address
```

## Using with Hypothesis

Refinement types integrate with the Hive testing utilities for property-based testing:

```python
from hypothesis import given
from hive.testing import strategy_for_type
from hive.types import PositiveInt, Email

@given(x=strategy_for_type(PositiveInt))
def test_positive_int_always_positive(x):
    assert x > 0

@given(email=strategy_for_type(Email))
def test_email_contains_at(email):
    assert "@" in email
```

## Creating Custom Types

You can create custom refinement types using `Annotated` and `beartype.vale.Is`:

```python
from typing import Annotated
from beartype.vale import Is

# Custom even integer
EvenInt = Annotated[int, Is[lambda x: x % 2 == 0]]

# Custom string with length constraint
ShortString = Annotated[str, Is[lambda s: len(s) <= 50]]

# Custom domain type
UserId = Annotated[int, Is[lambda x: x > 0]]
```

## API Reference

::: hive.types
    options:
      show_root_heading: true
      show_source: false
      members:
        - PositiveInt
        - NonNegativeInt
        - NegativeInt
        - PositiveFloat
        - NonNegativeFloat
        - UnitInterval
        - Percentage
        - Probability
        - Port
        - HttpStatusCode
        - UnixTimestamp
        - Year
        - Month
        - Day
        - Hour
        - Minute
        - Second
        - NonEmptyStr
        - TrimmedStr
        - LowercaseStr
        - UppercaseStr
        - Identifier
        - Slug
        - Email
        - Url
        - FilePath
        - DirectoryPath
