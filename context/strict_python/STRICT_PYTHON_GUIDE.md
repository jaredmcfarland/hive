# Strict Python Project Configuration Guide

## Purpose and Philosophy

This document defines the standards, tooling, and patterns for creating **agent-ready Python codebases**—projects optimized for both human developers and AI coding agents to understand, navigate, and modify with high confidence.

### Core Thesis

AI coding agents and human developers share the same fundamental needs when working with code:

1. **Unambiguous contracts** — Know what a function expects and returns without reading implementation
2. **Predictable structure** — Find things where you expect them to be
3. **Immediate feedback** — Know when you've broken something before runtime
4. **Traceable dependencies** — Understand how components connect
5. **Self-documenting code** — Understand intent without external documentation

The difference is that agents can't ask clarifying questions mid-task, can't intuit unwritten conventions, and work from static context windows. What helps agents helps everyone—but agents expose the gaps that humans paper over with tribal knowledge.

**Strict typing, comprehensive linting, and enforced documentation aren't bureaucratic overhead—they're executable specifications that make code reliably modifiable by any agent, human or AI.**

---

## Design Goals

### 1. Zero Ambiguity at Boundaries

Every function signature should be a complete contract:

```python
# ❌ Ambiguous - agent must read implementation to understand
def process(data):
    ...

# ✅ Self-documenting - signature tells the full story
def process(event: UserEvent) -> AnalyticsPayload:
    """Transform a raw user event into an analytics payload.

    Args:
        event: The incoming user event to process.

    Returns:
        A validated analytics payload ready for ingestion.

    Raises:
        ValidationError: If the event contains invalid data.
    """
    ...
```

### 2. Fail Fast, Fail Loudly

Errors should surface at the earliest possible moment:

| Error Type | When Caught | Tool |
|------------|-------------|------|
| Type mismatches | Edit time | Pyright + IDE |
| Import errors | Edit time | Pyright |
| Style violations | Pre-commit | Ruff |
| Missing docs | Pre-commit | Interrogate |
| Dead code | CI | Vulture |
| Architecture violations | CI | Import-linter |
| Runtime type errors | Test time | Pydantic + pytest |
| Security issues | CI | Bandit + pip-audit |
| Untested code paths | CI | Coverage |
| Tests that don't catch bugs | CI | Mutmut |

### 3. Maximum Grep-ability

Code should be searchable and traceable:

```python
# ❌ Hard to trace
from models import *
result = getattr(handler, action_name)()

# ✅ Explicit and traceable
from myproject.models import User, Event
result = handler.create_user()
```

### 4. Mechanical Verifiability

Every quality standard must be automatically enforceable—no "best practices" that require human judgment to verify.

---

## Tool Selection Rationale

### Static Type Checking: Pyright (not mypy)

**Why Pyright over mypy:**

| Factor | Pyright | mypy |
|--------|---------|------|
| Speed | 10-100x faster | Slower |
| Strictness | Stricter defaults | More permissive |
| Type narrowing | More accurate | Less precise |
| IDE integration | Native (Pylance) | Separate tool |
| Modern typing | Earlier adoption | Lags slightly |
| Error messages | More actionable | Sometimes cryptic |

**Why this matters for agents:** Most AI coding tools (Cursor, Claude Code, GitHub Copilot) use Pylance/Pyright under the hood. Aligning your project's type checker with the agent's analyzer eliminates false positive/negative mismatches.

**Configuration philosophy:**

We use `strict` mode plus additional checks. The goal is zero `# type: ignore` comments—every suppression should have a specific error code:

```python
# ❌ Opaque - what are we ignoring?
x = foo()  # type: ignore

# ✅ Specific and auditable
x = foo()  # type: ignore[arg-type]
```

### Linting and Formatting: Ruff (unified)

**Why Ruff over separate tools:**

Previously, a Python project needed:
- Black (formatting)
- isort (import sorting)
- Flake8 (linting)
- pylint (additional linting)
- pyupgrade (syntax modernization)
- autoflake (unused import removal)
- pydocstyle (docstring linting)
- bandit (security)

Ruff consolidates all of these into a single tool that's 10-100x faster than the tools it replaces. This means:

1. **Faster feedback** — Sub-second linting on large codebases
2. **Consistent configuration** — One `pyproject.toml` section
3. **No tool conflicts** — Unified rule resolution
4. **Simpler CI** — One tool to install and run

**Configuration philosophy:**

We start with `select = ["ALL"]` (every rule) and explicitly disable only rules that:
- Conflict with other rules (e.g., D203 vs D211)
- Conflict with the formatter
- Are inappropriate for our specific use case

This "allowlist by exclusion" approach means new rules are automatically enforced when Ruff adds them.

### Runtime Validation: Pydantic v2

**Why Pydantic:**

1. **Schema introspection** — Agents can call `.model_json_schema()` to understand data structures
2. **Descriptive fields** — `Field(description="...")` becomes agent-readable documentation
3. **Discriminated unions** — Clean pattern matching on `type` or `kind` fields
4. **Serialization** — Automatic JSON/dict conversion
5. **Ecosystem** — FastAPI, SQLModel, and most Python tools integrate natively

**Configuration philosophy:**

We use maximum strictness:

```python
from pydantic import BaseModel, ConfigDict

class StrictBase(BaseModel):
    """Base model with maximum validation strictness."""

    model_config = ConfigDict(
        strict=True,           # No type coercion
        frozen=True,           # Immutable after creation
        extra="forbid",        # No undeclared fields
        validate_default=True, # Validate default values
        use_enum_values=True,  # Serialize enums to values
    )
```

**Why `frozen=True`:** Immutable models are easier to reason about. An agent modifying code doesn't have to trace mutation paths.

**Why `extra="forbid"`:** Silently accepting unknown fields hides bugs. If a field isn't in the schema, it should error.

### Testing: pytest + hypothesis + mutmut

**Why this combination:**

| Tool | Purpose | What it catches |
|------|---------|-----------------|
| pytest | Example-based testing | Known edge cases |
| hypothesis | Property-based testing | Edge cases you didn't think of |
| mutmut | Mutation testing | Tests that don't actually verify behavior |

**Property-based testing example:**

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_is_idempotent(xs: list[int]) -> None:
    """Sorting twice should equal sorting once."""
    assert sorted(sorted(xs)) == sorted(xs)

@given(st.lists(st.integers()))
def test_sort_preserves_length(xs: list[int]) -> None:
    """Sorting should not change list length."""
    assert len(sorted(xs)) == len(xs)
```

Hypothesis generates thousands of random inputs and finds minimal failing cases. This catches edge cases that example-based tests miss.

**Mutation testing:**

Mutmut modifies your code (e.g., changes `>` to `>=`, `+` to `-`) and verifies that tests fail. If a mutation survives, your tests don't actually verify that code path.

```bash
# Run mutation testing
mutmut run

# View surviving mutants (tests that should fail but don't)
mutmut results
```

### Documentation Coverage: Interrogate

**Why enforce docstring coverage:**

Docstrings are the primary way agents understand code intent. A function without a docstring forces the agent to read the implementation—which may be wrong, outdated, or intentionally obscure.

**Configuration philosophy:**

We require 95% coverage with sensible exclusions:
- `__init__` methods (class docstring suffices)
- Magic methods (`__repr__`, etc.)
- Private methods (`__private`)
- Test files

### Architecture Enforcement: import-linter

**Why this matters:**

Circular imports and architectural violations create dependency tangles that are hard for agents to navigate. Import-linter enforces rules like:

- Models cannot import from services
- Services can import from models but not vice versa
- CLI cannot import from web handlers

```python
# Caught at CI time, not runtime
[[tool.importlinter.contracts]]
name = "Models should not import from services"
type = "forbidden"
source_modules = ["myproject.models"]
forbidden_modules = ["myproject.services"]
```

### Security: Bandit + pip-audit

**Why both:**

- **Bandit** — Finds security issues in your code (hardcoded passwords, SQL injection patterns, unsafe deserialization)
- **pip-audit** — Finds known vulnerabilities in your dependencies

These run in CI to catch issues before deployment.

---

## Project Structure

```
your-project/
├── pyproject.toml          # All tool configuration (single source of truth)
├── README.md               # Project overview and quickstart
├── AGENTS.md               # Agent-specific context (this document, condensed)
├── .pre-commit-config.yaml # Git hooks configuration
├── .python-version         # Python version (for pyenv/asdf)
├── py.typed                # PEP 561 marker (typed package)
│
├── src/
│   └── your_project/
│       ├── __init__.py     # Explicit re-exports only
│       ├── py.typed        # PEP 561 marker (also here for installed packages)
│       │
│       ├── models/         # Data structures (Pydantic models, dataclasses)
│       │   ├── __init__.py
│       │   ├── user.py     # One primary model per file
│       │   └── event.py
│       │
│       ├── services/       # Business logic
│       │   ├── __init__.py
│       │   └── user_service.py
│       │
│       ├── _internal/      # Private implementation details
│       │   └── ...         # Underscore prefix = not part of public API
│       │
│       └── utils/          # Shared utilities
│           ├── __init__.py
│           └── validation.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Shared fixtures
│   ├── unit/               # Fast, isolated tests
│   │   └── test_user.py
│   └── integration/        # Tests with external dependencies
│       └── test_api.py
│
└── scripts/                # Development and deployment scripts
    └── ...
```

### Structure Principles

1. **src layout** — Prevents accidental imports from the project root
2. **One model per file** — Easy to find, grep, and navigate
3. **Explicit re-exports** — `__init__.py` files only re-export public API with explicit `as` syntax
4. **Underscore prefixes** — `_internal/` and `_private` methods signal "don't touch"
5. **Matching names** — `user.py` model → `user_service.py` service → `test_user.py` test

---

## Patterns for Agent-Friendly Code

### 1. Discriminated Unions over Inheritance

```python
# ❌ Hard for agents to enumerate possibilities
class Message(ABC):
    @abstractmethod
    def process(self) -> None: ...

class TextMessage(Message): ...
class ImageMessage(Message): ...
# Agent must search codebase for all subclasses

# ✅ All variants visible at definition site
class TextMessage(BaseModel):
    type: Literal["text"] = "text"
    content: str

class ImageMessage(BaseModel):
    type: Literal["image"] = "image"
    url: HttpUrl
    alt_text: str

Message = TextMessage | ImageMessage  # Complete union visible here
```

### 2. Exhaustiveness Checking with assert_never

```python
from typing import assert_never

def handle_message(msg: Message) -> str:
    match msg:
        case TextMessage():
            return msg.content
        case ImageMessage():
            return f"[Image: {msg.alt_text}]"
        case _ as unreachable:
            assert_never(unreachable)  # Type error if cases are missing
```

If you add a new message type, Pyright immediately errors on the `assert_never` line until you handle it.

### 3. NewType for Semantic Meaning

```python
from typing import NewType
from uuid import UUID

UserId = NewType("UserId", UUID)
EventId = NewType("EventId", UUID)
SessionId = NewType("SessionId", UUID)

def get_user_events(user_id: UserId) -> list[Event]:
    ...

# Now an agent can grep for "UserId" to find all user ID handling
# And Pyright prevents mixing up UserId with EventId
```

### 4. Explicit Re-exports

```python
# myproject/__init__.py

# ❌ Implicit - agent doesn't know what's public
from myproject.models import User
from myproject.services import create_user

# ✅ Explicit - the `as X` syntax marks intentional re-export
from myproject.models import User as User
from myproject.services import create_user as create_user

__all__ = ["User", "create_user"]  # Belt and suspenders
```

### 5. Protocols for Structural Typing

```python
from typing import Protocol

class Serializable(Protocol):
    """Any object that can be serialized to a dictionary."""

    def to_dict(self) -> dict[str, Any]: ...

def save_to_json(obj: Serializable, path: Path) -> None:
    """Save any serializable object to JSON."""
    path.write_text(json.dumps(obj.to_dict()))

# Any class with a to_dict method works - no inheritance required
```

### 6. Descriptive Pydantic Fields

```python
from pydantic import BaseModel, Field

class UserEvent(BaseModel):
    """An event triggered by user action."""

    event_id: UUID = Field(
        description="Unique identifier for this event instance"
    )
    user_id: UserId = Field(
        description="The user who triggered this event"
    )
    event_type: EventType = Field(
        description="Category of event (click, view, purchase, etc.)"
    )
    timestamp: datetime = Field(
        description="UTC timestamp when the event occurred"
    )
    properties: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional event-specific properties"
    )
```

Agents can inspect `UserEvent.model_json_schema()` and see all descriptions.

---

## Anti-Patterns to Avoid

### Dynamic Attribute Access

```python
# ❌ Breaks static analysis
handler = getattr(module, handler_name)
result = handler(**kwargs)

# ✅ Explicit dispatch
handlers: dict[str, Callable[..., Result]] = {
    "create": handle_create,
    "update": handle_update,
    "delete": handle_delete,
}
result = handlers[action_name](**kwargs)
```

### Star Imports

```python
# ❌ Agent can't determine what names are available
from myproject.models import *

# ✅ Explicit imports are traceable
from myproject.models import User, Event, Session
```

### Untyped kwargs Pass-through

```python
# ❌ Type information lost
def wrapper(**kwargs: Any) -> Result:
    return inner_function(**kwargs)

# ✅ Explicit parameters or TypedDict
class InnerParams(TypedDict):
    user_id: UserId
    include_deleted: bool

def wrapper(params: InnerParams) -> Result:
    return inner_function(**params)
```

### String-Based Type References

```python
# ❌ Requires string parsing
def get_user() -> "User":
    ...

# ✅ Use future annotations (at top of file)
from __future__ import annotations

def get_user() -> User:
    ...
```

### Mutable Default Arguments

```python
# ❌ Classic Python footgun
def process(items: list[str] = []) -> None:
    items.append("x")  # Mutates the default!

# ✅ Use None and create new instance
def process(items: list[str] | None = None) -> None:
    if items is None:
        items = []
    items.append("x")

# ✅ Or use default_factory with Pydantic
class Config(BaseModel):
    items: list[str] = Field(default_factory=list)
```

### Bare type: ignore

```python
# ❌ Opaque - suppresses all errors on this line
x = problematic_call()  # type: ignore

# ✅ Specific - documents what we're suppressing and why
x = problematic_call()  # type: ignore[arg-type]  # Third-party lib has wrong stubs
```

---

## Pre-commit Configuration

Create `.pre-commit-config.yaml` in the project root:

```yaml
# See https://pre-commit.com for more information
# See https://pre-commit.com/hooks.html for more hooks
repos:
  # Ruff - linting and formatting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  # Pyright - type checking
  - repo: https://github.com/RobertCraigie/pyright-python
    rev: v1.1.390
    hooks:
      - id: pyright
        additional_dependencies:
          - pydantic>=2.10.0
          # Add other type-checked dependencies here

  # Interrogate - docstring coverage
  - repo: https://github.com/econchick/interrogate
    rev: 1.7.0
    hooks:
      - id: interrogate
        args: [-vv, --fail-under=95]

  # Standard pre-commit hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-added-large-files
        args: [--maxkb=1000]
      - id: check-merge-conflict
      - id: detect-private-key
      - id: no-commit-to-branch
        args: [--branch, main, --branch, master]

  # Security
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.10
    hooks:
      - id: bandit
        args: [-c, pyproject.toml]
        additional_dependencies: ["bandit[toml]"]

# CI configuration
ci:
  autofix_commit_msg: "style: auto-fix from pre-commit hooks"
  autoupdate_commit_msg: "chore: update pre-commit hooks"
```

Install hooks:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files  # Initial run
```

---

## CI Pipeline Stages

Recommended CI stages in order:

```yaml
# Example GitHub Actions workflow structure
jobs:
  lint:
    # Fast feedback - runs in seconds
    - ruff check .
    - ruff format --check .

  typecheck:
    # Catches type errors
    - pyright

  test:
    # Unit and integration tests with coverage
    - pytest --cov --cov-fail-under=90

  docs:
    # Documentation coverage
    - interrogate --fail-under=95

  security:
    # Security scanning
    - bandit -c pyproject.toml -r src/
    - pip-audit --strict

  architecture:
    # Dependency rules
    - lint-imports

  dead-code:
    # Unused code detection
    - vulture src/ --min-confidence=80

  mutation:
    # Optional - slower, run on merge to main
    - mutmut run --CI
```

---

## Quick Start for New Projects

```bash
# 1. Create project structure
mkdir -p my-project/src/my_project my-project/tests
cd my-project

# 2. Copy pyproject.toml and customize
#    - Update project name, description, author
#    - Update package name in [tool.hatch.build.targets.wheel]
#    - Update root_package in [tool.importlinter]
#    - Update known-first-party in [tool.ruff.lint.isort]

# 3. Create py.typed marker
touch src/my_project/py.typed

# 4. Create minimal __init__.py
echo '"""My project."""' > src/my_project/__init__.py

# 5. Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# 6. Install dependencies
pip install -e ".[dev]"

# 7. Set up pre-commit
pre-commit install
pre-commit run --all-files

# 8. Verify tools work
pyright
ruff check .
pytest
```

---

## Summary

This configuration creates a Python codebase where:

1. **Every type error is caught before runtime** (Pyright strict mode)
2. **Every style inconsistency is auto-fixed** (Ruff)
3. **Every public function is documented** (Interrogate)
4. **Every dependency flow is explicit** (import-linter)
5. **Every security issue is flagged** (Bandit + pip-audit)
6. **Every code path is tested** (pytest + coverage)
7. **Every test actually verifies behavior** (mutmut)

The result is a codebase that an AI agent—or a new team member—can navigate, understand, and modify with confidence.

---

## Agent Instructions

When scaffolding a new project using this configuration:

1. **Copy `pyproject.toml`** and customize the project metadata
2. **Create the src layout** with `py.typed` markers
3. **Set up `.pre-commit-config.yaml`** and install hooks
4. **Create a base Pydantic model** with strict configuration
5. **Create `conftest.py`** with common fixtures
6. **Run all tools** to verify the setup works

When working in an existing project with this configuration:

1. **Trust the type checker** — If Pyright says it's wrong, it's wrong
2. **Read docstrings first** — They describe intent, implementation may be wrong
3. **Follow existing patterns** — Grep for similar code before inventing new patterns
4. **Run pre-commit before committing** — Fix issues before they reach CI
5. **Add tests for new code** — Maintain coverage requirements
6. **Document public interfaces** — Interrogate will enforce this anyway
