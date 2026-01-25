# Runtime

The runtime layer provides execution context to commands and queries. It manages database sessions, configuration, service instantiation, and output formatting.

## ExecutionContext

The `ExecutionContext` is the central runtime object provided to every command and query. It implements the async context manager protocol for automatic resource management.

**Location:** `src/hive/runtime/context.py`

### Basic Usage

```python
from hive.runtime.context import ExecutionContext

async with ExecutionContext() as ctx:
    # Access database
    result = await ctx.db.exec(select(Task))

    # Access configuration
    if ctx.config.debug:
        print("Debug mode enabled")

    # Format output
    ctx.output.result(result.all())
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `ctx.db` | `AsyncSession` | SQLAlchemy async session |
| `ctx.config` | `AppSettings` | Application configuration |
| `ctx.output` | `OutputFormatter` | Format-aware output handler |
| `ctx.services` | `ServiceProxy` | Lazy service accessor |
| `ctx.command_name` | `str` | Name of executing command |
| `ctx.output_format` | `OutputFormat` | Requested output format |
| `ctx.interactive` | `bool` | True if TTY attached |

### Transaction Management

The context automatically manages database transactions:

```python
async with ExecutionContext() as ctx:
    # Transaction started
    ctx.db.add(Task(title="New task"))
    # Committed on successful exit

async with ExecutionContext() as ctx:
    ctx.db.add(Task(title="New task"))
    raise ValueError("Something went wrong")
    # Rolled back on exception
```

Manual control is available:

```python
async with ExecutionContext() as ctx:
    ctx.db.add(Task(title="First"))
    await ctx.commit()  # Explicit commit

    ctx.db.add(Task(title="Second"))
    await ctx.rollback()  # Explicit rollback
```

### Contract Enforcement

Context methods are protected by contracts (via `deal`):

```python
@deal.pre(lambda self: not self._closed, message="Context is closed")
def db(self) -> AsyncSession:
    ...

@deal.pre(lambda self: not self._committed, message="Already committed")
async def commit(self) -> None:
    ...
```

---

## Database Session Management

Database sessions are created using SQLAlchemy's async session factory with automatic SQLite async driver configuration.

**Location:** `src/hive/runtime/database.py`

### Session Factory

```python
from hive.runtime.database import create_session_factory

factory = create_session_factory(
    database_url="sqlite+aiosqlite:///app.db",
    echo=True  # Log SQL statements
)

session = factory()
```

### SQLite Configuration

SQLite URLs are automatically configured for async support:

| Input | Transformed To |
|-------|----------------|
| `sqlite:///app.db` | `sqlite+aiosqlite:///app.db` |
| `sqlite:///:memory:` | `sqlite+aiosqlite:///:memory:` |

Additional configuration:
- `check_same_thread=False` for SQLite
- `StaticPool` for in-memory databases
- `expire_on_commit=False` for detached object access

### Other Databases

PostgreSQL and other async-compatible databases work directly:

```python
# PostgreSQL
factory = create_session_factory("postgresql+asyncpg://user:pass@localhost/db")

# MySQL
factory = create_session_factory("mysql+aiomysql://user:pass@localhost/db")
```

---

## Configuration

Application settings are managed via Pydantic Settings with environment variable support.

**Location:** `src/hive/runtime/config.py`

### AppSettings

```python
from hive.runtime.config import AppSettings

settings = AppSettings()  # Loads from environment

print(settings.database_url)
print(settings.debug)
print(settings.log_level)
```

### Configuration Options

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `database_url` | `HIVE_DATABASE_URL` | `sqlite+aiosqlite:///$HOME/.hive/data.db` | Database connection URL |
| `debug` | `HIVE_DEBUG` | `false` | Enable debug mode |
| `log_level` | `HIVE_LOG_LEVEL` | `INFO` | Logging level |

### Configuration Sources

Settings are loaded in order (later sources override):

1. Default values in class
2. `.env` file in current directory
3. Environment variables (prefixed with `HIVE_`)

### Custom Settings

Extend `AppSettings` for application-specific configuration:

```python
from hive.runtime.config import AppSettings
from pydantic import Field

class MyAppSettings(AppSettings):
    api_timeout: int = Field(
        default=30,
        description="API request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts"
    )
```

---

## Service Layer

Services provide lazy-loaded access to external API clients with credential management.

**Location:** `src/hive/runtime/services.py`

### ServiceProxy

The `ServiceProxy` provides attribute-based access to registered services:

```python
# In command
@command(app)
async def sync_issues(ctx) -> dict:
    # Service instantiated on first access
    client = ctx.services.github_client
    issues = await client.list_issues()
    return {"synced": len(issues)}
```

### Credential Resolution

Credentials are resolved using a chain:

1. **Keyring**: System keyring (macOS Keychain, Windows Credential Manager, etc.)
2. **Environment**: Fallback to `HIVE_{SERVICE}_CREDENTIAL`

```python
# Service registration
@service(app, credentials="keyring:github_token")
def github_client(credentials: str) -> GitHubClient:
    return GitHubClient(token=credentials)
```

Resolution order for `keyring:github_token`:
1. Check `hive.github_token` in system keyring
2. Fall back to `HIVE_GITHUB_CLIENT_CREDENTIAL` environment variable
3. Raise `CredentialError` if not found

### Credential Specification

| Format | Description |
|--------|-------------|
| `keyring:key` | System keyring with fallback to env |
| `env:VAR_NAME` | Direct environment variable |

### Service Cleanup

Services are cleaned up when the context exits:

```python
@service(app, credentials="keyring:api_key", cleanup=close_client)
def api_client(credentials: str) -> APIClient:
    return APIClient(api_key=credentials)

async def close_client(client: APIClient) -> None:
    await client.close()
```

---

## Output Formatting

The `OutputFormatter` provides format-aware output that respects the `--json` flag and quiet mode.

**Location:** `src/hive/runtime/output.py`

### OutputFormat

```python
from hive.runtime.output import OutputFormat

class OutputFormat(Enum):
    JSON = "json"   # Machine-parseable JSON
    TABLE = "table" # Rich tables
    CSV = "csv"     # CSV format
```

### OutputFormatter Methods

| Method | Description | JSON Mode | Quiet Mode |
|--------|-------------|-----------|------------|
| `result(data)` | Main command output | JSON | Shown |
| `table(items)` | Tabular data | JSON array | Shown |
| `info(message)` | Informational | Suppressed | Suppressed |
| `warning(message)` | Warning (stderr) | Shown | Shown |
| `error(message)` | Error (stderr) | Shown | Shown |
| `confirm(prompt)` | User confirmation | Returns default | Returns default |

### Usage Examples

```python
@command(app)
async def list_tasks(ctx) -> list[Task]:
    tasks = await ctx.db.exec(select(Task))
    result = tasks.all()

    # Informational message (suppressed in JSON mode)
    ctx.output.info(f"Found {len(result)} tasks")

    # Main result (always shown)
    return result  # Automatically formatted
```

### Custom Table Output

```python
@command(app)
async def task_summary(ctx) -> None:
    tasks = await ctx.db.exec(select(Task))

    ctx.output.table(
        items=tasks.all(),
        columns=["id", "title", "status"]  # Specific columns
    )
```

---

## Context Lifecycle

```
┌─────────────────────────────────────────────────┐
│                 async with ctx:                 │
│                                                 │
│  1. __aenter__()                               │
│     └── Create database session                │
│                                                 │
│  2. Command execution                          │
│     ├── ctx.db operations                      │
│     ├── ctx.services access                    │
│     └── ctx.output formatting                  │
│                                                 │
│  3. __aexit__()                                │
│     ├── Clean up services                      │
│     ├── Success → commit transaction           │
│     └── Exception → rollback transaction       │
│     └── Close session                          │
└─────────────────────────────────────────────────┘
```

### State Tracking

The context tracks its state to prevent invalid operations:

| State | Description |
|-------|-------------|
| `_closed` | Context has exited |
| `_committed` | Transaction committed |
| `_rolled_back` | Transaction rolled back |

Attempting invalid operations raises contract violations:

```python
async with ExecutionContext() as ctx:
    await ctx.commit()
    await ctx.commit()  # Raises: "Already committed"
```
