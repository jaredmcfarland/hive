# Data Model: Documentation and Polish

**Branch**: `004-docs-polish` | **Date**: 2026-01-24

## Overview

This phase primarily extends existing models rather than introducing new entities. The data flow is:

```
ApplicationRegistry → Specification → DocumentationOutput
                   ↓
            TestClient → TestSession → TestResult
```

## Documentation Generation Models

### DocumentationConfig

Configuration for documentation generation. Not persisted; passed to generators.

| Field | Type | Description |
|-------|------|-------------|
| format | Literal["markdown", "manpage"] | Output format |
| output_dir | Path | Directory for generated files |
| include_private | bool | Include private commands (default: False) |
| include_examples | bool | Include usage examples (default: True) |

### DocumentationOutput

Result of documentation generation. Returned by generators.

| Field | Type | Description |
|-------|------|-------------|
| files_generated | list[Path] | Paths to generated files |
| commands_documented | int | Number of commands documented |
| queries_documented | int | Number of queries documented |
| entities_documented | int | Number of entities documented |
| warnings | list[str] | Any warnings (e.g., missing docstrings) |

## Testing Utilities Models

### TestClient

High-level testing interface. Wraps MockExecutionContext.

| Field | Type | Description |
|-------|------|-------------|
| app | App | Hive application to test |
| services | dict[str, Any] | Service mocks to inject |
| db_url | str | Database URL (default: sqlite:///:memory:) |

**Methods**:
- `invoke(command_name, **kwargs) -> Any` - Execute command
- `query(query_name, **kwargs) -> Any` - Execute query
- `get_output() -> list[str]` - Captured output lines

### TestSession

Internal session state. Created by TestClient context manager.

| Field | Type | Description |
|-------|------|-------------|
| context | ExecutionContext | Underlying execution context |
| captured_output | list[str] | Output captured during session |
| invocation_count | int | Number of invocations in session |

### ConformanceTestCase

Generated test case for contract verification.

| Field | Type | Description |
|-------|------|-------------|
| target_name | str | Command/query being tested |
| contract_type | Literal["requires", "ensures", "invariant"] | Contract type |
| test_function_name | str | Generated function name |
| test_code | str | Generated pytest code |
| description | str | From contract message |

### PropertyTestCase

Generated property-based test case.

| Field | Type | Description |
|-------|------|-------------|
| target_name | str | Command/query being tested |
| parameters | list[tuple[str, type]] | Parameter name/type pairs |
| test_function_name | str | Generated function name |
| test_code | str | Generated hypothesis test code |

## Relationships

```
┌─────────────────┐
│ ApplicationRegistry │
└────────┬────────┘
         │ reads
         ▼
┌─────────────────┐       ┌─────────────────┐
│  Specification  │──────▶│ DocumentationOutput │
└────────┬────────┘       └─────────────────┘
         │ provides data
         ▼
┌─────────────────┐       ┌─────────────────┐
│   TestClient    │──────▶│   TestSession   │
└────────┬────────┘       └─────────────────┘
         │ generates
         ▼
┌─────────────────┐       ┌─────────────────┐
│ConformanceTestCase│     │ PropertyTestCase│
└─────────────────┘       └─────────────────┘
```

## Example Application Entities

### Minimal Example
No entities (single command demonstration).

### CRUD Example

**Task Entity**:
| Field | Type | Constraints |
|-------|------|-------------|
| id | int | Primary key |
| title | NonEmptyStr | Required |
| description | str | Optional |
| priority | PositiveInt | 1-5 range |
| completed | bool | Default: False |
| created_at | datetime | Auto-set |

### API Client Example
No entities (service integration demonstration).

### Analytics Example

**DataPoint Entity**:
| Field | Type | Constraints |
|-------|------|-------------|
| id | int | Primary key |
| timestamp | datetime | Required |
| metric_name | NonEmptyStr | Required |
| value | float | Required |
| tags | dict[str, str] | Optional JSON field |

**Report Entity**:
| Field | Type | Constraints |
|-------|------|-------------|
| id | int | Primary key |
| name | NonEmptyStr | Required |
| query | str | SQL/DuckDB query |
| created_at | datetime | Auto-set |
| last_run | datetime | Optional |
