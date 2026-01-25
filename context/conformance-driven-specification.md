# Conformance-Driven Specification (CDS)

A methodology for defining application behavior through schemas and test fixtures, enabling verifiable multi-implementation development.

## Overview

Conformance-Driven Specification (CDS) is a methodology for defining application behavior through two artifacts: schemas that describe data structures, and fixtures that specify expected behavior. Together, these artifacts form a verifiable contract that any implementation must satisfy.

The primary goal of CDS is to maximize the verifiability of a codebase. A verifiable codebase is one where correctness can be mechanically checked rather than inferred, argued, or trusted. This property is essential for agent-readiness—the capacity for AI coding agents to understand a system, implement against its contracts, and verify their own work without human supervision.

When an AI agent scaffolds a new implementation or modifies an existing one, it needs unambiguous answers to two questions: "What should this system do?" and "How do I know if I did it correctly?" CDS answers both. The schema defines structure, the fixtures define behavior, and conformance testing provides verification. An agent that can read the spec, generate code, and run the fixtures has everything it needs to work autonomously and confirm its own correctness.

CDS also enables parallel implementation across languages and technology stacks. Because the specification is language-agnostic and correctness is defined by fixture conformance, multiple implementations can be developed simultaneously and evaluated on non-functional criteria (performance, ergonomics, ecosystem fit) while functional correctness is guaranteed by the shared test suite.

This guide provides the principles, artifacts, structure, and patterns needed to apply CDS when scaffolding new projects.

## Core Principles

CDS is built on eight principles that inform every aspect of the methodology. These principles should guide decisions when scaffolding projects and extending specifications.

### Principle 1: Specification Independence

The specification exists independently of any implementation. It is the source of truth for what the system does, not a description of how any particular implementation works. The spec format must not presuppose language, framework, or technology choices. A specification written today should be implementable in languages and frameworks that do not yet exist.

### Principle 2: Verifiability as Purpose

Specifications exist to be verified against, not merely documented. The purpose of a spec is not to communicate intent to human readers (though it may do that incidentally), but to provide a formal contract that can be mechanically checked. An implementation is correct if and only if it passes all specified fixtures. Given the same specification and fixtures, any observer—human or machine—must be able to independently verify correctness and arrive at the same conclusion.

### Principle 3: Fixtures as First-Class Artifacts

Test fixtures are part of the specification, not an afterthought or implementation detail. The schema defines what data looks like; the fixtures define what the system does with that data. A specification without fixtures is incomplete. Fixtures should be version-controlled alongside schemas and treated with the same rigor.

### Principle 4: Separation of Shape and Behavior

Schemas define data structure (the "shape" of inputs and outputs). Fixtures define behavior (what happens when operations are performed). These concerns are distinct and should remain separate in the specification artifacts. A schema answers "what does a Task look like?" while a fixture answers "what happens when I create a Task with these inputs?"

### Principle 5: Implementation as Adapter

Each implementation is an adapter between the specification contract and a particular runtime environment. The implementation's job is to satisfy the contract, not to extend or interpret it. Multiple implementations may coexist, each adapting the same contract to different languages, platforms, or persistence mechanisms. Implementations that pass the same fixtures are functionally equivalent by definition.

### Principle 6: Specification Gravity

Changes to the specification carry significant weight. A schema change or fixture modification is a breaking change that affects all implementations. Specifications should be treated with the same gravity as public API contracts. Adding a new required field, changing validation rules, or modifying expected outputs will break conformance across all implementations simultaneously.

### Principle 7: Minimal Specification

Specify only what is necessary to define correctness. Everything not specified is implementation freedom. The specification should constrain behavior where consistency matters and remain silent where it does not. Non-functional concerns such as performance, memory usage, and ergonomics are implementation choices, not specification concerns. This preserves room for implementations to optimize and differentiate.

### Principle 8: Machine and Agent Readability

Specifications must be parseable by tooling and comprehensible to AI agents. Human readability is necessary but not sufficient. The spec format should support automated code generation, validation, and verification. AI coding agents should be able to read the specification, understand what is required, scaffold an implementation, and verify their own work against the fixtures without human intervention. This property—agent-readability—is what makes a codebase "agent-ready."

## Specification Artifacts

A CDS project consists of three artifact types: schemas, an operations specification, and fixtures. Each serves a distinct purpose and all three are required for a complete specification.

### Schemas

Schemas define the structure of data entities using JSON Schema. JSON Schema is the recommended format because it is language-agnostic, widely supported by code generation tools, and machine-readable.

A schema defines what an entity looks like—its fields, types, constraints, and relationships. It does not define behavior.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "task.schema.json",
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "Unique identifier for the task"
    },
    "title": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500
    },
    "status": {
      "type": "string",
      "enum": ["pending", "in_progress", "completed"]
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": ["id", "title", "status", "created_at"]
}
```

Schemas should be organized as one file per entity, with a dedicated file for shared definitions that are referenced across multiple entities.

```
spec/schemas/
├── _definitions.schema.json   # shared types (e.g., timestamp, uuid)
├── task.schema.json
├── project.schema.json
└── user.schema.json
```

Shared definitions use JSON Schema's `$ref` mechanism for reuse:

```json
{
  "$id": "_definitions.schema.json",
  "$defs": {
    "uuid": {
      "type": "string",
      "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

### Operations Specification

The operations specification documents the behavior of each operation in prose. While fixtures define specific input/output pairs, the operations spec explains the rules, invariants, and edge cases that govern behavior.

The prescribed format is a markdown file organized by entity, then by operation:

```markdown
# Operations Specification

## Task

### create

Creates a new task with the provided attributes.

**Required fields:** title
**Generated fields:** id (UUID v4), created_at (current timestamp)
**Default values:** status defaults to "pending" if not provided

**Invariants:**
- Title must be between 1 and 500 characters
- Status must be one of: pending, in_progress, completed

**Error conditions:**
- Missing title: returns error with code MISSING_REQUIRED_FIELD
- Title exceeds 500 characters: returns error with code VALIDATION_FAILED

### update

Updates an existing task by ID.

**Updatable fields:** title, status
**Immutable fields:** id, created_at

**Invariants:**
- Task must exist
- At least one field must be provided for update

**Error conditions:**
- Task not found: returns error with code NOT_FOUND
- No fields provided: returns error with code INVALID_REQUEST

### delete

Removes a task by ID.

**Behavior:** Hard delete; task is permanently removed.

**Error conditions:**
- Task not found: returns error with code NOT_FOUND

### query

Retrieves tasks matching filter criteria.

**Supported filters:** status, created_after, created_before
**Default behavior:** Returns all tasks if no filters provided
**Ordering:** Results are ordered by created_at descending
```

The operations spec serves as authoritative documentation for implementers. It captures behavior that is difficult to express through fixtures alone, such as default values, ordering guarantees, and the rationale behind error conditions.

### Fixtures

Fixtures are concrete input/output pairs that define expected behavior. Each fixture specifies an operation, provides input data, and declares the expected result. Fixtures are the executable component of the specification—they are what conformance tests run against.

A fixture consists of up to three parts: input (required), seed state (optional, for operations that depend on existing data), and expected output (required).

**Basic fixture (create operation):**

```json
{
  "input": {
    "title": "Buy milk"
  },
  "expected": {
    "success": true,
    "result": {
      "id": "@uuid",
      "title": "Buy milk",
      "status": "pending",
      "created_at": "@timestamp"
    }
  }
}
```

**Fixture with seed state (query operation):**

```json
{
  "seed": {
    "tasks": [
      {"id": "1", "title": "Task A", "status": "completed", "created_at": "2024-01-01T00:00:00Z"},
      {"id": "2", "title": "Task B", "status": "pending", "created_at": "2024-01-02T00:00:00Z"},
      {"id": "3", "title": "Task C", "status": "completed", "created_at": "2024-01-03T00:00:00Z"}
    ]
  },
  "input": {
    "status": "completed"
  },
  "expected": {
    "success": true,
    "results": [
      {"id": "3", "title": "Task C", "status": "completed", "created_at": "2024-01-03T00:00:00Z"},
      {"id": "1", "title": "Task A", "status": "completed", "created_at": "2024-01-01T00:00:00Z"}
    ]
  }
}
```

**Error fixture (invalid input):**

```json
{
  "input": {
    "title": ""
  },
  "expected": {
    "success": false,
    "error": {
      "code": "VALIDATION_FAILED",
      "field": "title",
      "message": "@any"
    }
  }
}
```

Wildcards handle non-deterministic values that cannot be specified in advance. The conformance harness interprets these matchers:

| Wildcard | Matches |
|----------|---------|
| `@uuid` | Any valid UUID |
| `@timestamp` | Any valid ISO 8601 datetime |
| `@any` | Any value (type-agnostic) |
| `@string` | Any string |
| `@number` | Any number |
| `@positive` | Any positive number |

Fixtures are organized by entity, then by operation, with descriptive filenames:

```
spec/fixtures/
├── task/
│   ├── create/
│   │   ├── valid_minimal.json
│   │   ├── valid_with_status.json
│   │   ├── invalid_missing_title.json
│   │   └── invalid_title_too_long.json
│   ├── update/
│   │   ├── valid_update_title.json
│   │   ├── valid_update_status.json
│   │   ├── invalid_not_found.json
│   │   └── invalid_no_fields.json
│   ├── delete/
│   │   ├── valid_existing.json
│   │   └── invalid_not_found.json
│   └── query/
│       ├── all_tasks.json
│       ├── filter_by_status.json
│       └── empty_result.json
└── project/
    └── ...
```

Naming conventions should be consistent: `valid_` prefix for success cases, `invalid_` prefix for error cases, followed by a descriptor of what makes the case notable.

### Versioning

Specification artifacts should be version-controlled in the same repository as implementations. Changes to schemas or fixtures should be treated as potentially breaking changes. Consider semantic versioning for the specification itself: breaking changes to schemas or fixtures increment the major version, new fixtures or optional schema fields increment the minor version.

## Project Structure

A CDS project separates specification artifacts from implementation code. The specification lives in a dedicated directory that serves as the single source of truth. Implementations reference the specification but do not modify it.

### Canonical Layout

```
project/
├── README.md
├── spec/
│   ├── README.md
│   ├── schemas/
│   │   ├── _definitions.schema.json
│   │   ├── task.schema.json
│   │   └── project.schema.json
│   ├── operations.md
│   └── fixtures/
│       ├── README.md
│       ├── task/
│       │   ├── create/
│       │   │   ├── valid_minimal.json
│       │   │   ├── valid_with_status.json
│       │   │   └── invalid_missing_title.json
│       │   ├── update/
│       │   │   └── ...
│       │   ├── delete/
│       │   │   └── ...
│       │   └── query/
│       │       └── ...
│       └── project/
│           └── ...
└── implementations/
    ├── python/
    │   ├── README.md
    │   ├── src/
    │   │   ├── models/
    │   │   ├── repository/
    │   │   └── operations/
    │   └── tests/
    │       └── test_conformance.py
    ├── swift/
    │   ├── README.md
    │   ├── Sources/
    │   │   ├── Models/
    │   │   ├── Repository/
    │   │   └── Operations/
    │   └── Tests/
    │       └── ConformanceTests.swift
    └── kotlin/
        └── ...
```

### Specification Directory

The `spec/` directory contains all specification artifacts and nothing else. No implementation code, no build artifacts, no generated files. This directory should be readable and understandable in isolation.

The `spec/README.md` documents the specification itself: what entities exist, what operations are supported, and how to interpret the fixtures. This is the entry point for anyone (human or agent) seeking to understand or implement against the specification.

The `spec/fixtures/README.md` documents the fixture format: the structure of fixture files, the meaning of each field, and the available wildcards. This enables conformance test harnesses to be written without ambiguity.

### Implementation Directory

Each implementation lives in its own subdirectory under `implementations/`. The internal structure of each implementation is not prescribed—different languages and frameworks have different conventions. However, each implementation should maintain a clear separation between three concerns:

**Models** contain the data structures that correspond to schema entities. These are typically generated from the JSON Schema definitions, though they may be hand-written if generation is impractical.

**Repository** handles persistence. This layer is responsible for storing and retrieving entities. The persistence mechanism (SQLite, filesystem, in-memory) is an implementation choice not governed by the specification.

**Operations** implement the behaviors defined in the operations specification. This layer contains the business logic and is the primary subject of conformance testing.

Each implementation should include its own README documenting how to generate models (if applicable), run conformance tests, and any implementation-specific considerations.

### Generated Files

Files generated from the specification (such as model classes produced by code generation tools) should be clearly identified. Common approaches include placing generated files in a dedicated directory (e.g., `src/generated/`), using a naming convention (e.g., `*.generated.py`), or documenting the generation process such that files can be regenerated from source. Generated files should not be manually edited; changes should flow from the specification through the generation process.

## Conformance Testing

Conformance testing is the mechanism by which implementations are verified against the specification. A conformance test harness loads fixtures, executes operations, and compares actual results against expected outputs. An implementation is conformant if and only if it passes all fixtures.

### Test Harness Architecture

The conformance test harness is responsible for four tasks: discovering fixtures, preparing state, executing operations, and asserting results. Each implementation provides its own harness that adapts these tasks to the implementation's runtime environment while following a common structure.

The harness discovers fixtures by traversing the `spec/fixtures/` directory. The directory structure encodes metadata: the first level identifies the entity, the second level identifies the operation. Each `.json` file within an operation directory is a single test case. The fixture filename becomes the test name, enabling clear identification of failures.

```
spec/fixtures/task/create/valid_minimal.json
    → entity: task
    → operation: create
    → test name: valid_minimal
```

### Test Isolation

Each fixture must execute in isolation. The state of the system before a fixture runs must be either empty or explicitly defined by the fixture's seed data. No fixture should depend on side effects from a previous fixture. This property ensures that fixtures can run in any order and that failures are attributable to specific cases rather than accumulated state.

For implementations backed by a database, isolation typically means starting each test with an empty database or using transactions that roll back after each fixture. For implementations with in-memory state, isolation means constructing a fresh instance for each fixture.

### Seed State Handling

Fixtures that test operations depending on existing data include a `seed` field that defines the required state before the operation executes. The harness must populate this state before executing the operation.

```python
def run_fixture(fixture, operations, repository):
    # Reset to clean state
    repository.clear()

    # Apply seed data if present
    if "seed" in fixture:
        for entity_type, records in fixture["seed"].items():
            for record in records:
                repository.insert(entity_type, record)

    # Execute the operation
    result = operations.execute(
        fixture["entity"],
        fixture["operation"],
        fixture["input"]
    )

    # Assert against expected output
    assert_matches(result, fixture["expected"])
```

The seed data structure mirrors the entity organization: each key is an entity type, and the value is an array of records to insert. The harness must insert seed data in a way that bypasses normal validation and generation logic—seed records are pre-formed and should be stored exactly as specified.

### Wildcard Matching

Expected outputs may contain wildcards for values that cannot be determined in advance. The assertion logic must recognize these wildcards and substitute appropriate matchers.

```python
def assert_matches(actual, expected, path=""):
    if isinstance(expected, str) and expected.startswith("@"):
        assert_wildcard(actual, expected, path)
    elif isinstance(expected, dict):
        assert isinstance(actual, dict), f"Expected dict at {path}"
        for key, value in expected.items():
            assert key in actual, f"Missing key {key} at {path}"
            assert_matches(actual[key], value, f"{path}.{key}")
    elif isinstance(expected, list):
        assert isinstance(actual, list), f"Expected list at {path}"
        assert len(actual) == len(expected), f"Length mismatch at {path}"
        for i, (a, e) in enumerate(zip(actual, expected)):
            assert_matches(a, e, f"{path}[{i}]")
    else:
        assert actual == expected, f"Value mismatch at {path}: {actual} != {expected}"

def assert_wildcard(actual, wildcard, path):
    matchers = {
        "@any": lambda v: True,
        "@string": lambda v: isinstance(v, str),
        "@number": lambda v: isinstance(v, (int, float)),
        "@positive": lambda v: isinstance(v, (int, float)) and v > 0,
        "@uuid": lambda v: is_valid_uuid(v),
        "@timestamp": lambda v: is_valid_iso8601(v),
    }
    matcher = matchers.get(wildcard)
    assert matcher is not None, f"Unknown wildcard {wildcard} at {path}"
    assert matcher(actual), f"Wildcard {wildcard} failed at {path}: {actual}"
```

The matching logic performs deep equality comparison, recursively traversing objects and arrays. When a wildcard is encountered in the expected value, the corresponding actual value is checked against the wildcard's predicate rather than compared for equality.

### Unordered Matching

Some operations return collections where order is not guaranteed or not significant. Fixtures can indicate unordered comparison by wrapping the expected array in an `@unordered` marker or by convention based on the operation type.

For unordered matching, the harness must verify that the actual array contains exactly the same elements as the expected array, regardless of order. This requires matching each expected element to exactly one actual element, accounting for wildcards.

```python
def assert_unordered_matches(actual, expected, path):
    assert len(actual) == len(expected), f"Length mismatch at {path}"
    used = set()
    for exp_item in expected:
        matched = False
        for i, act_item in enumerate(actual):
            if i not in used and matches(act_item, exp_item):
                used.add(i)
                matched = True
                break
        assert matched, f"No match found for {exp_item} at {path}"
```

### Error Case Assertions

Fixtures specifying error conditions set `success` to `false` and include an `error` object in the expected output. Error assertions typically verify the error code and optionally the affected field. Error messages are usually matched with `@any` or `@string` since exact message text is an implementation detail.

```json
{
  "input": { "title": "" },
  "expected": {
    "success": false,
    "error": {
      "code": "VALIDATION_FAILED",
      "field": "title",
      "message": "@string"
    }
  }
}
```

The error structure should be consistent across all error fixtures. The `code` field is the primary identifier and should match exactly. Additional fields like `field` or `details` provide context and should match when specified.

### Debugging Failures

When a fixture fails, the harness should report the fixture path, the point of divergence, and both the expected and actual values at that point. A well-structured failure message enables rapid diagnosis:

```
FAILED: task/create/valid_minimal
  Path: .result.status
  Expected: "pending"
  Actual: "active"
```

For complex mismatches, showing the full actual output alongside the expected output helps identify whether the divergence is a single incorrect value or a structural difference. Implementations may provide additional debugging hooks such as logging the sequence of operations performed or dumping the database state after fixture execution.

## Implementation Guidelines

This section provides guidance for scaffolding a new implementation against a CDS specification. The goal is to produce a conformant implementation efficiently while maintaining flexibility for language-specific conventions and architectural choices.

### Starting a New Implementation

When beginning a new implementation, follow this sequence:

First, read the specification thoroughly. Review all schemas to understand the data model, read the operations specification to understand expected behavior, and examine several fixtures from each operation to see concrete examples. This investment pays dividends in reduced rework.

Second, set up the project structure. Create the implementation directory under `implementations/`, establish the language-appropriate project configuration (package manager, build tool, test framework), and configure the project to reference the specification directory for fixtures and schemas.

Third, generate or write the model layer. This gives you the data structures to work with before implementing behavior.

Fourth, implement a minimal conformance test harness. Even before implementing operations, having the harness in place enables a test-driven workflow where you run fixtures and watch them progress from failing to passing.

Fifth, implement operations one at a time, running conformance tests after each to verify correctness.

### Code Generation from Schemas

JSON Schema supports code generation across many languages. Tools such as quicktype (multi-language), datamodel-code-generator (Python/Pydantic), and json-schema-to-typescript (TypeScript) can produce model classes directly from schema definitions.

A typical generation workflow:

```bash
# Generate Python models from all schemas
quicktype \
  --src spec/schemas/*.schema.json \
  --src-lang schema \
  --lang python \
  --out implementations/python/src/models/generated.py

# Generate Swift models
quicktype \
  --src spec/schemas/*.schema.json \
  --src-lang schema \
  --lang swift \
  --out implementations/swift/Sources/Models/Generated.swift
```

Configure generation to match language conventions: use snake_case for Python, camelCase for Swift and Kotlin, and appropriate date/time types for each language. Document the generation command in the implementation's README so it can be reproduced when schemas change.

Generated models should be treated as derived artifacts. When schemas change, regenerate rather than manually edit. If the generator produces incorrect or suboptimal code, prefer configuring the generator or post-processing the output over manual edits that will be lost on regeneration.

### When to Deviate from Generated Code

Code generation is a starting point, not a constraint. There are legitimate reasons to hand-write models or modify generated output.

Hand-write models when the generator does not support your target language, when generated code conflicts with framework requirements (such as ORM annotations), or when the generated code is substantially worse than idiomatic hand-written code for your language.

Modify generated code through post-processing scripts rather than manual editing. For example, a script might add serialization annotations, adjust import statements, or wrap generated classes with additional methods. This preserves the ability to regenerate from updated schemas.

Extend generated models through inheritance or composition rather than modification. A generated `TaskBase` class can be subclassed by a hand-written `Task` class that adds implementation-specific methods without touching the generated file.

The key constraint is that models must accurately represent the schema. Field names, types, and constraints must match. How that representation is achieved—generated, hand-written, or hybrid—is an implementation choice.

### Repository Layer

The repository layer handles persistence. Its interface should provide the operations needed by the business logic layer: creating, reading, updating, deleting, and querying entities.

The specification does not prescribe repository design. Different implementations may use different persistence mechanisms (SQLite, PostgreSQL, filesystem, in-memory) and different access patterns (repository per entity, unit of work, active record). Choose the approach that fits the implementation's language and intended use case.

The repository must support two additional operations for conformance testing: clearing all data (for test isolation) and inserting seed data without validation (for fixture setup). These may be exposed only in test configurations.

### Operations Layer

The operations layer implements the behaviors defined in the operations specification. This is where business logic lives: validation beyond what the schema enforces, default value assignment, relationship management, and error handling.

Each operation defined in the specification should map to a function or method in the operations layer. The mapping should be direct and traceable: someone reading the operations specification should be able to locate the corresponding implementation code without difficulty.

Operations should be implemented in terms of the repository interface, not directly against the persistence mechanism. This separation enables testing operations with an in-memory repository and swapping persistence mechanisms without changing business logic.

### Writing the Conformance Test Harness

Each implementation needs a conformance test harness that loads fixtures from the shared specification and executes them against the implementation. The harness structure follows the pattern described in the Conformance Testing section.

The harness should integrate with the implementation's standard test framework. In Python, this means pytest discovers and runs conformance tests alongside unit tests. In Swift, XCTest runs conformance tests. In Kotlin, JUnit does the same. This integration ensures conformance tests run as part of normal development and CI workflows.

Parameterize tests by fixture path. Most test frameworks support parameterized tests that generate one test case per fixture file. This produces clear output showing which specific fixtures pass or fail.

```python
# Python example using pytest
import pytest
from pathlib import Path

FIXTURES = Path(__file__).parents[3] / "spec" / "fixtures"

def discover_fixtures():
    for entity_dir in FIXTURES.iterdir():
        if not entity_dir.is_dir():
            continue
        for operation_dir in entity_dir.iterdir():
            if not operation_dir.is_dir():
                continue
            for fixture_file in operation_dir.glob("*.json"):
                yield pytest.param(
                    fixture_file,
                    id=f"{entity_dir.name}/{operation_dir.name}/{fixture_file.stem}"
                )

@pytest.mark.parametrize("fixture_path", discover_fixtures())
def test_conformance(fixture_path, db):
    fixture = load_fixture(fixture_path)
    entity = fixture_path.parent.parent.name
    operation = fixture_path.parent.name

    repository = Repository(db)
    repository.clear()

    if "seed" in fixture:
        apply_seed(repository, fixture["seed"])

    result = execute_operation(entity, operation, fixture["input"], repository)
    assert_matches(result, fixture["expected"])
```

### Handling Specification Evolution

When the specification changes, implementations must be updated to maintain conformance. The workflow depends on the nature of the change.

For new fixtures added to existing operations, run conformance tests to identify failures, then update the implementation to handle the new cases.

For new operations, implement the operation following the operations specification, then verify with the new fixtures.

For schema changes, regenerate models (if using code generation), update any hand-written code that depends on the changed fields, and run conformance tests to verify nothing broke.

For fixture changes that modify expected outputs, investigate whether the change reflects a specification correction or a behavioral change. If the previous implementation was incorrect, fix it. If the specification behavior changed, update the implementation to match.

### Implementation-Specific Tests

Conformance tests verify functional correctness against the specification. Implementations may include additional tests for concerns not covered by the specification.

Unit tests for internal helper functions, edge cases in parsing or serialization, and error handling for infrastructure failures (database unavailable, disk full) are appropriate candidates for implementation-specific tests.

Performance tests, load tests, and benchmarks are implementation-specific by nature since the specification does not constrain non-functional behavior.

Keep conformance tests and implementation-specific tests clearly separated. Conformance tests should be identifiable as such (by directory, naming convention, or test markers) so that specification compliance can be assessed independently.

### Validating Fixtures Against Schemas

Before running conformance tests, validate that fixtures themselves are well-formed. The input field of each fixture should validate against the corresponding schema's input constraints. The expected result (when successful) should validate against the entity schema.

This pre-validation catches specification errors early: a fixture that specifies an invalid input or an impossible output indicates a problem with the specification, not the implementation. Some implementations build this validation into the conformance harness; others run it as a separate specification-level check.

## Anti-Patterns

The following anti-patterns undermine the effectiveness of CDS. They are ordered by severity, with the most damaging patterns listed first.

### Don't Write the Specification After the Implementation

Writing implementation code first and then documenting it as a specification inverts the intended workflow. The resulting "specification" merely describes what the code happens to do rather than defining what it should do. This eliminates the specification's value as an independent contract and makes the implementation the de facto source of truth.

A related mistake is writing fixtures based on observed implementation behavior. When a fixture is created by running the implementation and capturing its output, the fixture cannot catch bugs—it merely enshrines whatever the implementation currently does, correct or not.

**Instead:** Write schemas and fixtures before implementation. Define what the system should do, then build an implementation that satisfies that definition. When behavior is ambiguous, resolve the ambiguity in the specification first, then implement accordingly.

### Don't Let Implementation Details Leak into the Specification

A specification that references specific technologies, languages, or implementation mechanisms is no longer language-agnostic. Examples include SQL syntax in the operations specification, language-specific type names in schemas (e.g., `int64` instead of `integer`), framework-specific validation rules, or database-specific constraints.

**Instead:** Express everything in terms of the specification's own vocabulary. Use JSON Schema types and formats. Describe behavior in terms of inputs, outputs, and invariants rather than implementation mechanisms. If a constraint is difficult to express without referencing implementation details, consider whether it belongs in the specification at all or should be left to implementation discretion.

### Don't Modify the Specification Directory from Implementations

The `spec/` directory should be treated as read-only by implementations. Implementations that modify fixtures to match their behavior, add implementation-specific test cases to the shared fixtures directory, or check in generated files alongside specification artifacts corrupt the separation between contract and implementation.

A related mistake is duplicating fixtures into implementation directories rather than reading from the shared location. This creates drift: the duplicated fixtures diverge from the specification over time, and the implementation may pass its local fixtures while failing the actual specification.

**Instead:** Implementations read from `spec/` but never write to it. All fixtures live in the specification directory. If an implementation needs additional test cases beyond conformance, those tests live in the implementation's own test directory and are clearly distinguished from conformance tests.

### Don't Leave Fixtures Incomplete

A specification with schemas but sparse or missing fixtures provides structure without verifiable behavior. Implementations can claim conformance simply because there are few fixtures to fail. This is particularly problematic for error cases: specifications often define happy paths thoroughly while leaving error conditions unspecified.

**Instead:** Every operation should have fixtures covering its significant cases. At minimum, include fixtures for the basic success case, boundary conditions (minimum and maximum valid inputs), and each documented error condition. The operations specification's error conditions section provides a checklist: each error code mentioned should have at least one fixture that triggers it.

### Don't Leave Behavior Implicit

Operations with undocumented side effects, hidden behaviors, or assumed context create ambiguity that different implementations resolve differently. If creating a task also updates a project's task count, but this behavior is not specified, some implementations will do it and others will not. Both may pass the existing fixtures while behaving inconsistently.

**Instead:** Document all significant behavior in the operations specification. If an operation has side effects, state them explicitly. If behavior depends on context or configuration, document the dependency. If behavior is intentionally left to implementation discretion, state that explicitly so implementers know they have freedom.

### Don't Over-Specify Implementation Details

The opposite of implicit behavior is over-specification: constraining details that should be left to implementers. Specifying that IDs must be UUID v4 generated by a specific algorithm, that timestamps must use a specific clock source, or that internal data structures must follow a specific shape constrains implementations without improving correctness.

**Instead:** Specify what matters for interoperability and correctness. An ID must be unique and stable; whether it's a UUID, ULID, or integer sequence is often an implementation choice. A timestamp must accurately reflect when an event occurred; the clock source and precision are implementation concerns. Apply Principle 7 (Minimal Specification): constrain where consistency matters, remain silent elsewhere.

### Don't Skip Failing Fixtures

When a fixture fails and the cause is unclear or the fix is difficult, marking the fixture as skipped or excluding it from the test run is tempting. This erodes conformance: the implementation is no longer verified against the full specification, and the skipped fixtures tend to accumulate.

**Instead:** Treat fixture failures as bugs to be fixed, not inconveniences to be hidden. If a fixture is failing, either the implementation is wrong (fix the implementation) or the fixture is wrong (fix the fixture in the specification, with appropriate consideration for other implementations). If a fixture represents behavior that is intentionally not yet implemented, track it explicitly as a known gap rather than silently skipping it.

### Don't Create Order-Dependent Fixtures

Fixtures that only pass when run in a specific sequence violate test isolation. This typically happens when fixtures rely on side effects from previous fixtures: a "delete" fixture that assumes the "create" fixture ran first and left a record in the database. Order-dependent fixtures are fragile, difficult to debug, and may pass or fail unpredictably depending on test runner behavior.

**Instead:** Each fixture must be self-contained. Use seed data to establish required preconditions. A "delete" fixture should seed the record it intends to delete rather than assuming it exists. Run fixtures in randomized order during development to catch accidental dependencies.

### Don't Manually Edit Generated Code

Manually editing files produced by code generation creates a maintenance burden. When schemas change and models are regenerated, manual edits are lost. This leads to either avoiding regeneration (causing models to drift from schemas) or repeatedly re-applying manual edits (wasting effort and risking inconsistency).

**Instead:** Configure the generator to produce the desired output, post-process generated files with scripts, or extend generated classes through inheritance or composition. Keep a clear boundary between generated and hand-written code. If generation consistently produces inadequate results for your use case, consider hand-writing models entirely rather than maintaining a fragile hybrid.

### Don't Use Inconsistent Wildcard Conventions

Wildcards enable matching non-deterministic values, but using them inconsistently creates confusion. If some fixtures use `@uuid` and others use `@generated` for the same concept, or if some use `@any` where a more specific wildcard would be appropriate, the fixtures become harder to read and the harness becomes more complex.

**Instead:** Define the wildcard vocabulary in `spec/fixtures/README.md` and use it consistently across all fixtures. Prefer specific wildcards (`@uuid`, `@timestamp`) over generic ones (`@any`) when the type is known. If a new wildcard is needed, add it to the vocabulary with a clear definition and update the harness to support it.

### Don't Overload Operations

Operations that do too many things produce complex fixtures and ambiguous behavior. An "update" operation that also handles creation (upsert), deletion (when passed null), and notification triggers becomes difficult to specify completely and verify correctly.

**Instead:** Keep operations focused on a single responsibility. Prefer separate create, update, and delete operations over a multipurpose save operation. If an operation has multiple modes or behaviors depending on input, consider whether it should be split into distinct operations with clearer contracts.

## Worked Example

This section presents a complete CDS specification for a minimal domain: a note-taking system with a single entity supporting create, read, update, delete, and list operations. The example demonstrates all specification artifacts and their relationships.

### Domain Description

The system manages notes. Each note has a unique identifier, a title, a body, and timestamps for creation and last modification. Notes can be created, retrieved by ID, updated, deleted, and listed with optional filtering by a search term.

### Directory Structure

```
spec/
├── README.md
├── schemas/
│   ├── _definitions.schema.json
│   └── note.schema.json
├── operations.md
└── fixtures/
    ├── README.md
    └── note/
        ├── create/
        │   ├── valid_minimal.json
        │   ├── valid_full.json
        │   └── invalid_missing_title.json
        ├── get/
        │   ├── valid_existing.json
        │   └── invalid_not_found.json
        ├── update/
        │   ├── valid_update_title.json
        │   ├── valid_update_body.json
        │   └── invalid_not_found.json
        ├── delete/
        │   ├── valid_existing.json
        │   └── invalid_not_found.json
        └── list/
            ├── all_notes.json
            ├── filter_by_search.json
            └── empty_result.json
```

### Specification README

The `spec/README.md` file introduces the domain and serves as the entry point for implementers and agents.

```markdown
# Note System Specification

This specification defines a note-taking system supporting basic CRUD operations and search functionality.

## Domain Overview

The system manages **notes**. A note is a piece of text content with a title, used for capturing and organizing information.

## Entities

| Entity | Description |
|--------|-------------|
| Note | A text record with title, body, and timestamps |

## Operations

| Entity | Operation | Description |
|--------|-----------|-------------|
| Note | create | Create a new note |
| Note | get | Retrieve a note by ID |
| Note | update | Modify an existing note |
| Note | delete | Remove a note |
| Note | list | Retrieve notes with optional search filter |

## Specification Structure

- `schemas/` — JSON Schema definitions for all entities
- `operations.md` — Behavioral specification for all operations
- `fixtures/` — Test fixtures organized by entity and operation

## Implementing Against This Specification

1. Read `schemas/note.schema.json` to understand the data model
2. Read `operations.md` for behavioral requirements and error conditions
3. Examine fixtures in `fixtures/note/` for concrete input/output examples
4. Implement operations and validate using the conformance test fixtures
5. An implementation is conformant when all fixtures pass

## Fixture Format

See `fixtures/README.md` for fixture structure, wildcards, and conventions.
```

### Schema: Shared Definitions

The `_definitions.schema.json` file defines reusable types referenced by entity schemas.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "_definitions.schema.json",
  "$defs": {
    "id": {
      "type": "string",
      "minLength": 1,
      "description": "Unique identifier"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 datetime"
    }
  }
}
```

### Schema: Note Entity

The `note.schema.json` file defines the structure of a note.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "note.schema.json",
  "type": "object",
  "properties": {
    "id": { "$ref": "_definitions.schema.json#/$defs/id" },
    "title": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200,
      "description": "Note title"
    },
    "body": {
      "type": "string",
      "maxLength": 10000,
      "description": "Note content"
    },
    "created_at": { "$ref": "_definitions.schema.json#/$defs/timestamp" },
    "updated_at": { "$ref": "_definitions.schema.json#/$defs/timestamp" }
  },
  "required": ["id", "title", "body", "created_at", "updated_at"]
}
```

### Operations Specification

The `operations.md` file documents the behavior of each operation.

```markdown
# Operations Specification

## Note

### create

Creates a new note.

**Required fields:** title
**Optional fields:** body
**Generated fields:** id, created_at, updated_at
**Default values:** body defaults to empty string if not provided

**Invariants:**
- Title must be between 1 and 200 characters
- Body must not exceed 10000 characters
- created_at and updated_at are set to the current timestamp

**Error conditions:**
- Missing title: MISSING_REQUIRED_FIELD
- Title empty or exceeds 200 characters: VALIDATION_FAILED
- Body exceeds 10000 characters: VALIDATION_FAILED

### get

Retrieves a note by ID.

**Required fields:** id

**Error conditions:**
- Note not found: NOT_FOUND

### update

Updates an existing note.

**Required fields:** id
**Updatable fields:** title, body
**Behavior:** updated_at is set to the current timestamp on any successful update

**Invariants:**
- At least one of title or body must be provided
- Title constraints apply if title is provided
- Body constraints apply if body is provided

**Error conditions:**
- Note not found: NOT_FOUND
- No updatable fields provided: INVALID_REQUEST
- Title empty or exceeds 200 characters: VALIDATION_FAILED
- Body exceeds 10000 characters: VALIDATION_FAILED

### delete

Deletes a note by ID.

**Required fields:** id
**Behavior:** Hard delete; note is permanently removed

**Error conditions:**
- Note not found: NOT_FOUND

### list

Retrieves all notes, optionally filtered.

**Optional fields:** search
**Behavior:**
- If search is provided, returns notes where title or body contains the search term (case-insensitive)
- Results are ordered by created_at descending (newest first)
- Returns empty array if no notes match

**Error conditions:** None; empty input returns all notes
```

### Fixtures README

The `fixtures/README.md` file documents the fixture format and wildcards.

```markdown
# Fixture Format

Each fixture is a JSON file with the following structure:

- `seed` (optional): Object mapping entity types to arrays of records to insert before the operation
- `input`: The input to the operation
- `expected`: The expected result

## Expected Result Structure

Success case:
```json
{
  "success": true,
  "result": { ... }
}
```

Error case:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "field": "field_name",
    "message": "..."
  }
}
```

## Wildcards

| Wildcard | Description |
|----------|-------------|
| `@any` | Matches any value |
| `@string` | Matches any string |
| `@id` | Matches any valid identifier |
| `@timestamp` | Matches any valid ISO 8601 datetime |
```

### Fixture: Create (Success)

The `note/create/valid_minimal.json` fixture tests creating a note with only required fields.

```json
{
  "input": {
    "title": "My First Note"
  },
  "expected": {
    "success": true,
    "result": {
      "id": "@id",
      "title": "My First Note",
      "body": "",
      "created_at": "@timestamp",
      "updated_at": "@timestamp"
    }
  }
}
```

### Fixture: Create (Error)

The `note/create/invalid_missing_title.json` fixture tests the error when title is omitted.

```json
{
  "input": {
    "body": "Some content without a title"
  },
  "expected": {
    "success": false,
    "error": {
      "code": "MISSING_REQUIRED_FIELD",
      "field": "title",
      "message": "@string"
    }
  }
}
```

### Fixture: Get (With Seed)

The `note/get/valid_existing.json` fixture tests retrieving an existing note. It uses seed data to establish the note before the operation.

```json
{
  "seed": {
    "note": [
      {
        "id": "note-001",
        "title": "Seeded Note",
        "body": "This note exists before the test runs.",
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z"
      }
    ]
  },
  "input": {
    "id": "note-001"
  },
  "expected": {
    "success": true,
    "result": {
      "id": "note-001",
      "title": "Seeded Note",
      "body": "This note exists before the test runs.",
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    }
  }
}
```

### Fixture: List (With Filter)

The `note/list/filter_by_search.json` fixture tests listing notes with a search filter.

```json
{
  "seed": {
    "note": [
      {
        "id": "note-001",
        "title": "Meeting Notes",
        "body": "Discussed project timeline.",
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z"
      },
      {
        "id": "note-002",
        "title": "Shopping List",
        "body": "Milk, eggs, bread.",
        "created_at": "2024-01-16T10:00:00Z",
        "updated_at": "2024-01-16T10:00:00Z"
      },
      {
        "id": "note-003",
        "title": "Project Ideas",
        "body": "New meeting scheduler app.",
        "created_at": "2024-01-17T10:00:00Z",
        "updated_at": "2024-01-17T10:00:00Z"
      }
    ]
  },
  "input": {
    "search": "meeting"
  },
  "expected": {
    "success": true,
    "results": [
      {
        "id": "note-003",
        "title": "Project Ideas",
        "body": "New meeting scheduler app.",
        "created_at": "2024-01-17T10:00:00Z",
        "updated_at": "2024-01-17T10:00:00Z"
      },
      {
        "id": "note-001",
        "title": "Meeting Notes",
        "body": "Discussed project timeline.",
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z"
      }
    ]
  }
}
```

Note that the results are ordered by `created_at` descending as specified in the operations specification, and both matching notes are included because "meeting" appears in the title of one and the body of the other (case-insensitive).

### Agent Verification Walkthrough

An AI coding agent encountering this specification would proceed as follows.

The agent reads `spec/README.md` to understand the domain and available operations. It then examines `spec/schemas/note.schema.json` to understand the data model: a note has five fields, all required in the persisted entity, with specific type and length constraints.

The agent reads `spec/operations.md` to understand behavior. For the `create` operation, it learns that `title` is required, `body` is optional with a default, and `id`, `created_at`, and `updated_at` are generated. It notes the validation rules and error codes.

The agent examines fixtures in `spec/fixtures/note/create/` to see concrete examples. The `valid_minimal.json` fixture shows that creating a note with only a title should succeed and return a complete note with generated fields. The `invalid_missing_title.json` fixture shows the expected error structure when title is omitted.

The agent implements the create operation, then runs the conformance tests. If `valid_minimal.json` fails because the implementation returns `"body": null` instead of `"body": ""`, the agent knows exactly what to fix: the default value logic for the body field.

The agent proceeds through each operation, using the operations specification for behavior rules and the fixtures for verification. When all fixtures pass, the implementation is conformant by definition.

### Sample Conformance Output

A passing conformance run produces output indicating each fixture's status:

```
note/create/valid_minimal ................ PASS
note/create/valid_full ................... PASS
note/create/invalid_missing_title ........ PASS
note/get/valid_existing .................. PASS
note/get/invalid_not_found ............... PASS
note/update/valid_update_title ........... PASS
note/update/valid_update_body ............ PASS
note/update/invalid_not_found ............ PASS
note/delete/valid_existing ............... PASS
note/delete/invalid_not_found ............ PASS
note/list/all_notes ...................... PASS
note/list/filter_by_search ............... PASS
note/list/empty_result ................... PASS

13 passed, 0 failed
```

A failing run identifies the specific fixture and divergence:

```
note/create/valid_minimal ................ FAIL
  Path: .result.body
  Expected: ""
  Actual: null

note/create/valid_full ................... PASS
...

12 passed, 1 failed
```

This output gives the agent (or human) sufficient information to locate and fix the problem without additional investigation.
