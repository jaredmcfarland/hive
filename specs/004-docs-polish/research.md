# Research: Documentation and Polish

**Branch**: `004-docs-polish` | **Date**: 2026-01-24

## Documentation Generation

### Jinja2 Templates

**Decision**: Use Jinja2 with `PackageLoader` for template management.

**Rationale**: Standard Python templating, IDE support for `.j2` files, template inheritance for consistent output.

**Alternatives Considered**:
- f-strings: Too verbose for multi-format output
- Mako: Less common, similar capabilities

**Structure**:
```
src/hive/docs/templates/
├── markdown/
│   ├── base.md.j2      # Base template with common structure
│   ├── command.md.j2   # Command documentation
│   ├── query.md.j2     # Query documentation
│   ├── entity.md.j2    # Entity documentation
│   └── index.md.j2     # Table of contents
└── manpage/
    └── command.1.j2    # Man page template
```

### Man Page Format

**Decision**: Generate troff/groff format directly using templates.

**Rationale**: Man pages use a simple macro format. No need for external libraries.

**Key Macros**:
- `.TH` - Title header (NAME section number date)
- `.SH` - Section header
- `.TP` - Tagged paragraph (for options)
- `.B` - Bold text
- `.I` - Italic text
- `.BR` - Bold/roman alternation

**Structure**:
```
.TH COMMAND 1 "2026-01-24" "hive" "Hive Application"
.SH NAME
command \- short description
.SH SYNOPSIS
.B command
[\fB\-\-option\fR \fIvalue\fR]
.SH DESCRIPTION
Full description here.
.SH OPTIONS
.TP
\fB\-\-option\fR \fIvalue\fR
Option description
```

## Testing Utilities

### TestClient Design

**Decision**: Async context manager wrapping MockExecutionContext.

**Rationale**: Matches existing async command pattern, provides cleanup guarantees.

**API Design**:
```python
async with TestClient(app) as client:
    result = await client.invoke("command_name", arg1="value")
    assert result.success
```

**Key Features**:
- Auto-provisions SQLite in-memory database
- Service mock injection via constructor
- Typed return values from registry metadata
- Exception capture with helpful messages

### Conformance Test Generation

**Decision**: Generate pytest functions from registry contracts.

**Rationale**: pytest is the project's test runner; generated code should be idiomatic.

**Pattern**:
```python
# For @requires(lambda ctx, x: x > 0)
def test_command_requires_x_positive():
    """Verify precondition: x must be positive."""
    with pytest.raises(CommandError):
        await client.invoke("command", x=-1)

# For @ensures(lambda ctx, x, result: result.id == x)
def test_command_ensures_result_id_matches():
    """Verify postcondition: result.id equals input."""
    result = await client.invoke("command", x=5)
    assert result.id == 5
```

### Property Test Generation

**Decision**: Generate hypothesis tests using existing `strategy_for_type()`.

**Rationale**: Leverages existing infrastructure, no new dependencies.

**Pattern**:
```python
@given(x=strategy_for_type(PositiveInt))
async def test_command_with_positive_int(x):
    """Property: command accepts any valid PositiveInt."""
    result = await client.invoke("command", x=x)
    assert result is not None
```

## Example Applications

### Project Structure

**Decision**: Each example is a standalone uv project in `examples/` directory.

**Rationale**: Demonstrates real-world usage; users can copy as starting point.

**Common Structure**:
```
examples/<name>/
├── pyproject.toml      # uv project with hive dependency
├── README.md           # Setup, features, learning objectives
├── src/<name>/
│   ├── __init__.py     # App definition with decorators
│   ├── commands.py     # Command implementations
│   └── entities.py     # Entity definitions (if applicable)
└── tests/
    └── test_commands.py  # Tests using TestClient
```

### Feature Coverage Matrix

| Example | CLI | TUI | Entity | Service | Types | Contracts |
|---------|-----|-----|--------|---------|-------|-----------|
| minimal | ✓ | | | | | |
| crud | ✓ | ✓ | ✓ | | ✓ | ✓ |
| api-client | ✓ | | | ✓ | ✓ | |
| analytics | ✓ | | ✓ | | ✓ | ✓ |

### DuckDB Integration (Analytics Example)

**Decision**: Use DuckDB via SQLModel with custom engine configuration.

**Rationale**: Demonstrates pluggable database support without new abstractions.

**Pattern**:
```python
from sqlalchemy import create_engine

engine = create_engine("duckdb:///analytics.db")
```
