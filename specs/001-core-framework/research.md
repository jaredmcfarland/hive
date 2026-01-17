# Research: Core Framework

**Feature**: 001-core-framework
**Created**: 2026-01-11
**Updated**: 2026-01-17
**Status**: Complete

## Research Areas

### 1. Decorator Pattern for Registration

**Decision**: Use class-based decorator factories that accept configuration and return function decorators.

**Rationale**:
- Decorator factories allow parameters like `@command(app, entities=[Task])`
- Class-based factories can store reference to the App instance for registration
- Python's `inspect` module provides full introspection of decorated functions
- `functools.wraps` preserves metadata (name, docstring, annotations)

**Alternatives Considered**:
- Simple decorators without parameters: Too limited; can't specify app or metadata
- Module-level registration: Requires explicit calls; violates "automatic at import" requirement
- Metaclass-based: Overly complex for function decoration; better suited for class hierarchies

**Implementation Notes**:
```python
# Pattern to follow
def command(app, entities=None, name=None):
    def decorator(func):
        registration = CommandRegistration.from_function(func, entities, name)
        app.registry.register_command(registration)
        @functools.wraps(func)
        async def wrapper(ctx, *args, **kwargs):
            return await func(ctx, *args, **kwargs)
        return wrapper
    return decorator
```

### 2. Type Extraction from Function Signatures

**Decision**: Use `typing.get_type_hints()` with `inspect.signature()` for complete parameter information.

**Rationale**:
- `get_type_hints()` resolves forward references and string annotations
- `inspect.signature()` provides default values and parameter kinds (positional, keyword, etc.)
- Combined, they give full schema information for CLI generation
- Works with Python 3.11+ modern syntax (`int | None` vs `Optional[int]`)

**Alternatives Considered**:
- `__annotations__` directly: Doesn't resolve forward references
- Third-party libraries (pydantic's internals): Adds dependency; may change between versions

**Implementation Notes**:
```python
def extract_parameters(func) -> list[ParameterInfo]:
    hints = get_type_hints(func)
    sig = inspect.signature(func)
    params = []
    for name, param in sig.parameters.items():
        if name == 'ctx':  # Skip context parameter
            continue
        params.append(ParameterInfo(
            name=name,
            type=hints.get(name, Any),
            default=param.default if param.default is not param.empty else REQUIRED,
            kind=param.kind,
        ))
    return params
```

### 3. Async/Sync Bridge for Typer

**Decision**: Use `asyncio.run()` wrapper in CLI layer; commands are async internally.

**Rationale**:
- Typer is synchronous; async commands need bridging
- `asyncio.run()` is the standard way to run async code from sync context
- Single entry point ensures proper event loop lifecycle
- Database operations benefit from async (aiosqlite)

**Alternatives Considered**:
- Make commands sync: Loses async database benefits; harder to add async features later
- Use `nest_asyncio`: Hack for Jupyter; not appropriate for CLI
- Trio instead of asyncio: Non-standard; Typer ecosystem expects asyncio

**Implementation Notes**:
```python
# In CLI generator
def create_sync_wrapper(async_func):
    def sync_wrapper(*args, **kwargs):
        return asyncio.run(async_func(*args, **kwargs))
    return sync_wrapper
```

### 4. Registry Data Structure

**Decision**: Use typed dataclasses for registrations stored in dictionaries keyed by name.

**Rationale**:
- Dataclasses provide clean API with type checking
- Dictionary lookup by name is O(1) and natural for CLI subcommand routing
- Separate dictionaries per registration type (commands, queries, entities, screens)
- Immutable after registration prevents accidental modification

**Alternatives Considered**:
- Single list with type discrimination: Slower lookup; more complex filtering
- Database storage: Overkill for in-memory registry
- Protocol-based (structural typing): Less explicit; harder to validate

**Implementation Notes**:
```python
@dataclass(frozen=True)
class CommandRegistration:
    name: str
    func: Callable
    parameters: list[ParameterInfo]
    return_type: type
    docstring: str | None
    entities: list[type]

class ApplicationRegistry:
    def __init__(self):
        self._commands: dict[str, CommandRegistration] = {}
        self._queries: dict[str, QueryRegistration] = {}
        self._entities: dict[str, EntityRegistration] = {}
        self._screens: dict[str, ScreenRegistration] = {}
```

### 5. Context Injection Pattern

**Decision**: First parameter convention; context created per-invocation with lifecycle management.

**Rationale**:
- First parameter is Python convention for context/self
- Context created fresh per command ensures clean state
- Context manager pattern (`async with`) handles setup/teardown
- Database session bound to context lifecycle

**Alternatives Considered**:
- Global context: Prevents concurrent execution; testing harder
- Dependency injection framework: Overkill; adds complexity
- Thread-local: Doesn't work with async

**Implementation Notes**:
```python
class ExecutionContext:
    db: AsyncSession
    config: AppSettings
    output: OutputFormatter

    async def __aenter__(self):
        self._session = await create_session()
        self.db = self._session
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self._session.rollback()
        else:
            await self._session.commit()
        await self._session.close()
```

### 6. Output Formatting Strategy

**Decision**: OutputFormatter class with format-aware methods; JSON mode suppresses non-data output.

**Rationale**:
- Single class provides consistent API across all commands
- Format determined by CLI flags, passed to context
- JSON mode returns pure data; human mode adds decoration
- Rich integration for tables, progress bars in human mode

**Alternatives Considered**:
- Return raw data, format at CLI level: Loses context about what to format
- Multiple return types: Complex; breaks type consistency
- Middleware pattern: Adds indirection; harder to debug

**Implementation Notes**:
```python
class OutputFormatter:
    def __init__(self, format: OutputFormat, console: Console):
        self.format = format
        self.console = console

    def result(self, data: BaseModel) -> None:
        if self.format == OutputFormat.JSON:
            print(data.model_dump_json())
        else:
            # Rich table rendering
            self.console.print(self._to_table(data))

    def info(self, message: str) -> None:
        if self.format != OutputFormat.JSON:
            self.console.print(f"[dim]{message}[/dim]")
```

### 7. Configuration Loading Order

**Decision**: Environment variables override file config; Pydantic Settings handles merging.

**Rationale**:
- Environment variables are 12-factor app standard
- Pydantic Settings provides validated, typed configuration
- File config useful for development; env vars for deployment
- Prefix prevents collision (e.g., `HIVE_DATABASE_URL`)

**Alternatives Considered**:
- Environment only: No file support limits development ergonomics
- TOML/YAML custom loader: Reinvents Pydantic Settings
- ConfigParser: No type validation; legacy API

**Implementation Notes**:
```python
class AppSettings(BaseSettings):
    database_url: str = "sqlite:///~/.hive/data.db"
    debug: bool = False

    model_config = SettingsConfigDict(
        env_prefix="HIVE_",
        env_file=".env",
        env_file_encoding="utf-8",
    )
```

### 8. Error Handling Architecture

**Decision**: Custom exception hierarchy; errors carry exit codes and user-facing messages.

**Rationale**:
- Custom exceptions enable consistent handling across interfaces
- Exit codes follow Unix conventions (1 for general error, specific codes for specific errors)
- User-facing messages separate from technical details
- CLI catches and formats; other interfaces can handle differently

**Alternatives Considered**:
- Standard exceptions only: No exit code; inconsistent messages
- Result types (Ok/Err): Not Pythonic; verbose
- Error codes as returns: Easy to ignore; breaks type signatures

**Implementation Notes**:
```python
class HiveError(Exception):
    """Base for all Hive errors."""
    exit_code: int = 1

class CommandError(HiveError):
    """User-facing command execution error."""
    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code

class ConfigurationError(HiveError):
    """Missing or invalid configuration."""
    exit_code = 78  # EX_CONFIG from sysexits.h
```

## Technology Decisions Summary

| Area | Decision | Key Library |
|------|----------|-------------|
| Decorators | Class-based factories | functools, inspect |
| Type extraction | get_type_hints + signature | typing, inspect |
| Async bridge | asyncio.run() wrapper | asyncio |
| Registry | Frozen dataclasses + dicts | dataclasses |
| Context | First-param, context manager | N/A (custom) |
| Output | Format-aware OutputFormatter | Rich |
| Config | Pydantic Settings | pydantic-settings |
| Errors | Custom hierarchy | N/A (custom) |

## Open Questions Resolved

1. **Q: How to handle commands that don't return anything?**
   A: Return `None`; output formatter handles gracefully (no output in JSON mode, "Done" in human mode).

2. **Q: How to handle async generators (streaming output)?**
   A: Deferred to future phase. Initial implementation requires complete results.

3. **Q: How to validate entity relationships at registration time?**
   A: Validate when all modules imported (app.validate() call); warn about missing referenced entities.

---

## Verification Stack Research (Added 2026-01-17)

### 9. Refinement Types Implementation

**Decision**: Use `Annotated` with beartype `Is[]` validators for runtime type constraints.

**Rationale**:
- beartype provides zero-cost runtime validation (O(1) type checking)
- `Annotated` is standard Python 3.9+ (PEP 593)
- `Is[]` validators allow arbitrary constraints via lambda predicates
- Type aliases preserve IDE autocomplete and type checker compatibility
- Constraints are introspectable for CLI help and JSON Schema generation

**Alternatives Considered**:
- Pydantic constrained types: Requires model wrapper; doesn't work with plain functions
- NewType: No runtime validation; only static type checking
- Custom validator classes: More boilerplate; less integration with type system
- typeguard: Less performant; fewer constraint options

**Implementation Notes**:
```python
from typing import Annotated
from beartype.vale import Is

PositiveInt = Annotated[int, Is[lambda x: x > 0]]
Port = Annotated[int, Is[lambda x: 1 <= x <= 65535]]
```

### 10. Contract Decorator Pattern

**Decision**: Wrap deal library decorators with Hive-specific error handling.

**Rationale**:
- deal is mature, well-tested design-by-contract library
- Decorators integrate naturally with async functions
- Violations can be caught and converted to CommandError
- deal supports preconditions, postconditions, and invariants
- No runtime overhead when contracts disabled (production mode)

**Alternatives Considered**:
- icontract: Less async support; more verbose syntax
- dpcontracts: Abandoned project; Python 2 era
- Custom implementation: Reinventing the wheel; less tested

**Implementation Notes**:
```python
import deal
from hive.errors import CommandError

def requires(condition, message):
    def decorator(func):
        @deal.pre(condition, message=message)
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except deal.PreContractError as e:
                raise CommandError(str(e))
        return wrapper
    return decorator
```

### 11. Hypothesis Strategy Generation

**Decision**: Generate strategies by introspecting refinement type constraints.

**Rationale**:
- Hypothesis is the standard Python property-based testing library
- Auto-generation reduces test writing burden
- Strategies can be derived from `Is[]` validator constraints
- Consistent with "specification-driven" philosophy

**Alternatives Considered**:
- Manual strategy per type: More work; easy to forget edge cases
- pytest-quickcheck: Less powerful; fewer composability options
- Schemathesis (for API testing): Different use case; not unit testing

**Implementation Notes**:
```python
from hypothesis import strategies as st

def strategy_for_type(typ):
    constraints = extract_constraints(typ)
    if constraints.min_value is not None:
        return st.integers(min_value=constraints.min_value,
                          max_value=constraints.max_value)
    # ... handle other constraint types
```

### 12. CLI Error Message Translation

**Decision**: Catch beartype exceptions in CLI layer and format user-friendly messages.

**Rationale**:
- beartype tracebacks are technical and unfriendly
- User-facing errors should explain constraints clearly
- Translation happens at CLI boundary, not in type system
- Error messages can include constraint descriptions

**Alternatives Considered**:
- Custom exception types: More classes; less standard
- Always-on validation wrapper: Performance overhead
- Let tracebacks through: Poor user experience

**Implementation Notes**:
```python
# In CLI generator
try:
    result = await command_func(ctx, **parsed_args)
except BeartypeCallHintViolation as e:
    constraint = extract_constraint_from_error(e)
    raise typer.BadParameter(
        f"{e.param_name} must be {constraint.description}"
    )
```

## Technology Decisions Summary (Updated)

| Area | Decision | Key Library |
|------|----------|-------------|
| Decorators | Class-based factories | functools, inspect |
| Type extraction | get_type_hints + signature | typing, inspect |
| Async bridge | asyncio.run() wrapper | asyncio |
| Registry | Frozen dataclasses + dicts | dataclasses |
| Context | First-param, context manager | N/A (custom) |
| Output | Format-aware OutputFormatter | Rich |
| Config | Pydantic Settings | pydantic-settings |
| Errors | Custom hierarchy | N/A (custom) |
| Refinement types | Annotated + beartype Is[] | beartype |
| Contracts | deal wrappers | deal |
| Testing | Hypothesis strategies | hypothesis |
