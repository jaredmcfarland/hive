# Python Verification Tools for Spec-Driven Development & Agent-Ready Code

## A Comprehensive Guide to beartype, deal, crosshair, and Hypothesis

---

## Executive Summary

This guide explores four Python tools that bring formal verification concepts to practical Python development: **beartype**, **deal**, **crosshair**, and **Hypothesis**. Together, they form a verification stack that enables spec-driven development—a methodology where specifications (types, contracts, properties) drive implementation and serve as executable documentation.

For AI agent development and "agent-ready" code, these tools provide:

- **Machine-readable specifications** that agents can understand and verify
- **Automatic test generation** from contracts and type hints
- **Formal guarantees** about code behavior
- **Self-documenting interfaces** that reduce ambiguity

---

## The Verification Stack at a Glance

| Tool | Purpose | Verification Method | When It Runs |
|------|---------|---------------------|--------------|
| **beartype** | Runtime type enforcement with refinements | Type checking | Runtime (every call) |
| **deal** | Design-by-contract (pre/post conditions) | Contract checking | Runtime + test generation |
| **crosshair** | Symbolic execution & formal verification | SMT solving (Z3) | Static analysis |
| **Hypothesis** | Property-based testing | Random sampling | Test time |

### How They Relate

```
                    Specification Richness
                    ─────────────────────────────────────────►

    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │  beartype   │    │    deal     │    │ crosshair   │
    │             │    │             │    │             │
    │ Refined     │───►│ Contracts   │───►│ Symbolic    │
    │ Types       │    │ Pre/Post    │    │ Execution   │
    │             │    │ Invariants  │    │             │
    └─────────────┘    └─────────────┘    └─────────────┘
          │                  │                  │
          │                  │                  │
          ▼                  ▼                  ▼
    ┌─────────────────────────────────────────────────────┐
    │                    Hypothesis                        │
    │         Property-Based Testing (Runtime)             │
    │     Generates test cases from all of the above       │
    └─────────────────────────────────────────────────────┘
```

---

## Part 1: beartype — Runtime Type Enforcement with Refinements

### What It Is

beartype is an ultra-fast runtime type checker that enforces type hints at function boundaries. Unlike mypy (static analysis), beartype catches type violations at runtime with near-zero overhead.

### Installation

```bash
pip install beartype
```

### Basic Usage

```python
from beartype import beartype

@beartype
def greet(name: str, times: int) -> str:
    return name * times

greet("hello", 3)      # OK: returns "hellohellohello"
greet("hello", "3")    # Raises BeartypeCallHintParamViolation
greet(123, 3)          # Raises BeartypeCallHintParamViolation
```

### Refinement Types with `typing.Annotated`

This is where beartype becomes powerful for spec-driven development. You can define **refinement types**—types with logical constraints:

```python
from beartype import beartype
from beartype.vale import Is
from typing import Annotated

# Define semantic types with constraints
PositiveInt = Annotated[int, Is[lambda x: x > 0]]
NonEmptyStr = Annotated[str, Is[lambda s: len(s) > 0]]
Percentage = Annotated[float, Is[lambda x: 0.0 <= x <= 100.0]]
Email = Annotated[str, Is[lambda s: "@" in s and "." in s]]
Port = Annotated[int, Is[lambda x: 1 <= x <= 65535]]

@beartype
def send_email(
    to: Email,
    subject: NonEmptyStr,
    body: str,
    priority: Percentage = 50.0
) -> bool:
    # Implementation
    return True

# Valid calls
send_email("user@example.com", "Hello", "Body text")

# Invalid calls - caught at runtime
send_email("not-an-email", "Hello", "Body")  # Raises: Email constraint violated
send_email("user@example.com", "", "Body")   # Raises: NonEmptyStr constraint violated
```

### Composing Refinement Types

```python
from beartype.vale import Is, IsAttr, IsEqual
from typing import Annotated
import re

# Compose validators with & (and), | (or)
Username = Annotated[str,
    Is[lambda s: len(s) >= 3] &
    Is[lambda s: len(s) <= 20] &
    Is[lambda s: s.isalnum()]
]

# Using regex
PhoneNumber = Annotated[str, Is[lambda s: re.match(r'^\+?1?\d{9,15}$', s) is not None]]

# Numeric ranges
Latitude = Annotated[float, Is[lambda x: -90.0 <= x <= 90.0]]
Longitude = Annotated[float, Is[lambda x: -180.0 <= x <= 180.0]]

# Collection constraints
NonEmptyList = Annotated[list, Is[lambda x: len(x) > 0]]
UniqueList = Annotated[list, Is[lambda x: len(x) == len(set(x))]]
```

### Creating a Types Library for Your Project

```python
# types/domain.py
"""Domain-specific refined types for the project."""

from beartype.vale import Is
from typing import Annotated, TypeVar, List

T = TypeVar('T')

# Numeric refinements
PositiveInt = Annotated[int, Is[lambda x: x > 0]]
NonNegativeInt = Annotated[int, Is[lambda x: x >= 0]]
PositiveFloat = Annotated[float, Is[lambda x: x > 0.0]]
UnitInterval = Annotated[float, Is[lambda x: 0.0 <= x <= 1.0]]
Probability = UnitInterval  # Semantic alias

# String refinements
NonEmptyStr = Annotated[str, Is[lambda s: len(s) > 0]]
TrimmedStr = Annotated[str, Is[lambda s: s == s.strip()]]
LowercaseStr = Annotated[str, Is[lambda s: s == s.lower()]]

# Collection refinements
NonEmptyList = Annotated[List[T], Is[lambda x: len(x) > 0]]
SortedList = Annotated[List[T], Is[lambda x: x == sorted(x)]]

# Domain-specific
UserId = Annotated[str, Is[lambda s: len(s) == 36]]  # UUID format
EventName = Annotated[str, Is[lambda s: s.isidentifier()]]
Timestamp = Annotated[int, Is[lambda x: x > 0]]  # Unix timestamp
```

### Why beartype Matters for Agent-Ready Code

1. **Self-documenting interfaces**: Agents can inspect type hints to understand function contracts
2. **Fail-fast behavior**: Invalid inputs are caught immediately, not deep in call stacks
3. **Zero ambiguity**: `PositiveInt` is clearer than "int (must be positive)" in a docstring
4. **Composable specifications**: Build complex types from simple predicates

---

## Part 2: deal — Design by Contract

### What It Is

deal implements Bertrand Meyer's Design by Contract (DbC) methodology in Python. It provides decorators for preconditions, postconditions, invariants, and automatic test generation.

### Installation

```bash
pip install deal
```

### Core Concepts

#### Preconditions (`@deal.pre`)

What must be true **before** a function executes:

```python
import deal

@deal.pre(lambda x: x >= 0, message="x must be non-negative")
def sqrt(x: float) -> float:
    return x ** 0.5

sqrt(4)    # OK: returns 2.0
sqrt(-1)   # Raises PreContractError: x must be non-negative
```

#### Postconditions (`@deal.post`)

What must be true **after** a function executes:

```python
@deal.post(lambda result: result >= 0)
def abs_value(x: float) -> float:
    return x if x >= 0 else -x

# deal verifies the return value satisfies the postcondition
```

#### Combined Pre/Post with `@deal.ensure`

Access both inputs and outputs:

```python
@deal.ensure(lambda x, result: result >= x, message="Result must be >= input")
def double_positive(x: int) -> int:
    return x * 2
```

#### Invariants (`@deal.inv`)

Class-level constraints that must always hold:

```python
@deal.inv(lambda self: self.balance >= 0)
class BankAccount:
    def __init__(self, balance: float):
        self.balance = balance

    def withdraw(self, amount: float):
        self.balance -= amount  # Raises InvContractError if balance goes negative
```

### Comprehensive Example: A Sorted Collection

```python
import deal
from typing import List, TypeVar

T = TypeVar('T')

@deal.inv(lambda self: self._is_sorted())
class SortedList:
    """A list that maintains sorted order."""

    def __init__(self):
        self._items: List = []

    def _is_sorted(self) -> bool:
        return all(self._items[i] <= self._items[i+1]
                   for i in range(len(self._items) - 1))

    @deal.pre(lambda self, item: item is not None)
    @deal.post(lambda result: result is None)
    @deal.ensure(lambda self, item, result: item in self._items)
    def insert(self, item) -> None:
        """Insert item maintaining sorted order."""
        # Binary search for insertion point
        lo, hi = 0, len(self._items)
        while lo < hi:
            mid = (lo + hi) // 2
            if self._items[mid] < item:
                lo = mid + 1
            else:
                hi = mid
        self._items.insert(lo, item)

    @deal.pre(lambda self: len(self._items) > 0, message="Cannot pop from empty list")
    @deal.ensure(lambda self, result: result not in self._items)
    def pop_min(self):
        """Remove and return the minimum element."""
        return self._items.pop(0)

    @deal.pre(lambda self, item: item in self._items, message="Item not found")
    def remove(self, item) -> None:
        """Remove first occurrence of item."""
        self._items.remove(item)
```

### deal + Hypothesis Integration

deal can automatically generate Hypothesis tests from contracts:

```python
import deal

@deal.pre(lambda items: len(items) > 0)
@deal.pre(lambda items: all(isinstance(x, (int, float)) for x in items))
@deal.post(lambda result: result >= 0)
@deal.ensure(lambda items, result: result <= sum(items))
def average(items: list) -> float:
    """Calculate the average of a non-empty numeric list."""
    return sum(items) / len(items)

# Generate tests automatically
test_average = deal.cases(average)

# Run with pytest:
# pytest test_module.py -v
```

Under the hood, deal uses Hypothesis to generate inputs that satisfy preconditions and verifies postconditions hold.

### Explicit Hypothesis Integration

```python
import deal
from hypothesis import given, strategies as st

@deal.pre(lambda x, y: y != 0)
@deal.post(lambda result: isinstance(result, float))
def safe_divide(x: float, y: float) -> float:
    return x / y

# Manual Hypothesis test that respects deal contracts
@given(
    x=st.floats(allow_nan=False, allow_infinity=False),
    y=st.floats(allow_nan=False, allow_infinity=False).filter(lambda y: y != 0)
)
def test_safe_divide(x, y):
    result = safe_divide(x, y)
    assert result == x / y

# Or use deal's built-in test generation
test_safe_divide_auto = deal.cases(safe_divide)
```

### Contract Checking Modes

```python
import deal

# Disable all contract checking (production mode)
deal.disable()

# Re-enable
deal.enable()

# Check if enabled
if deal.is_enabled():
    print("Contracts are being checked")

# Context manager for temporary disable
with deal.disable():
    # Contracts not checked here
    risky_function()
```

### Linting Contracts Statically

deal includes a linter that can catch contract violations without running code:

```bash
# Install linter
pip install deal[lint]

# Run linter
deal lint mymodule.py
```

The linter uses static analysis to find:
- Functions that might violate their contracts
- Unreachable code due to contracts
- Contradictory contracts

---

## Part 3: crosshair — Symbolic Execution for Python

### What It Is

crosshair uses an SMT solver (Z3) to symbolically execute Python code and find inputs that violate contracts. Unlike Hypothesis (random sampling), crosshair reasons mathematically about all possible inputs.

### Installation

```bash
pip install crosshair-tool
```

### Basic Usage

crosshair reads contracts from docstrings or deal decorators:

```python
# mymodule.py

def binary_search(arr: list[int], target: int) -> int:
    """
    Find target in sorted array.

    pre: all(arr[i] <= arr[i+1] for i in range(len(arr)-1))
    post: __return__ == -1 or (0 <= __return__ < len(arr) and arr[__return__] == target)
    post: __return__ == -1 implies all(x != target for x in arr)
    """
    if not arr:
        return -1

    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
```

Run verification:

```bash
$ crosshair check mymodule.py
```

If there's a bug, crosshair finds a concrete counterexample:

```
counterexample: binary_search([0, 1], 0) returns 1 but should satisfy post condition
```

### crosshair with deal Decorators

crosshair understands deal contracts directly:

```python
import deal

@deal.pre(lambda n: n >= 0)
@deal.post(lambda result: result >= 1)
@deal.ensure(lambda n, result: n == 0 or result == n * factorial(n - 1))
def factorial(n: int) -> int:
    """Calculate factorial with verified contracts."""
    if n == 0:
        return 1
    return n * factorial(n - 1)
```

```bash
$ crosshair check mymodule.py
# No errors = contracts verified for all inputs (within analysis depth)
```

### Watch Mode for Development

```bash
# Continuously check as you edit
$ crosshair watch mymodule.py
```

### crosshair vs Hypothesis: Complementary Approaches

| Aspect | Hypothesis | crosshair |
|--------|-----------|-----------|
| **Method** | Random sampling | Symbolic execution |
| **Guarantees** | Probabilistic ("tested 1000 cases") | Mathematical (for bounded domains) |
| **Speed** | Fast (milliseconds) | Slower (seconds to minutes) |
| **Strengths** | Quick feedback, wide coverage | Finds edge cases, corner conditions |
| **Weaknesses** | May miss rare edge cases | Limited by solver capabilities |
| **Best for** | General testing, CI pipelines | Critical code, security-sensitive logic |

### Using Both Together

```python
import deal
from hypothesis import given, strategies as st

@deal.pre(lambda x: x >= 0)
@deal.post(lambda result: result >= 0)
@deal.post(lambda result: result * result <= x)
@deal.post(lambda result: (result + 1) * (result + 1) > x)
def integer_sqrt(x: int) -> int:
    """
    Integer square root with full specification.

    Verified by:
    - crosshair: symbolic proof for bounded integers
    - hypothesis: randomized testing for quick feedback
    - deal: runtime enforcement in production
    """
    if x == 0:
        return 0

    # Newton's method
    guess = x
    while True:
        new_guess = (guess + x // guess) // 2
        if new_guess >= guess:
            return guess
        guess = new_guess

# Hypothesis test
@given(st.integers(min_value=0, max_value=10**12))
def test_integer_sqrt_hypothesis(x):
    result = integer_sqrt(x)
    assert result * result <= x
    assert (result + 1) * (result + 1) > x

# deal auto-generated test
test_integer_sqrt_deal = deal.cases(integer_sqrt)
```

```bash
# Run all verification layers
$ crosshair check mymodule.py        # Symbolic verification
$ pytest mymodule.py -v              # Hypothesis + deal tests
$ python -c "from mymodule import *" # Runtime contract check
```

### Advanced crosshair Features

#### Checking Specific Functions

```bash
$ crosshair check mymodule.py --function=binary_search
```

#### Setting Analysis Depth

```bash
# Deeper analysis (slower but more thorough)
$ crosshair check mymodule.py --per_condition_timeout=60
```

#### Diffbehavior: Comparing Implementations

crosshair can verify two implementations behave identically:

```bash
$ crosshair diffbehavior mymodule.slow_sort mymodule.fast_sort
```

---

## Part 4: Hypothesis — Property-Based Testing

Since you're already familiar with Hypothesis, this section focuses on integration patterns with the other tools.

### Quick Refresher

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_is_idempotent(xs):
    assert sorted(sorted(xs)) == sorted(xs)

@given(st.lists(st.integers(), min_size=1))
def test_max_in_list(xs):
    m = max(xs)
    assert m in xs
    assert all(x <= m for x in xs)
```

### Hypothesis + beartype: Type-Aware Strategies

beartype's refined types can inform Hypothesis strategies:

```python
from beartype import beartype
from beartype.vale import Is
from typing import Annotated
from hypothesis import given, strategies as st

# Define refined type
PositiveInt = Annotated[int, Is[lambda x: x > 0]]
Percentage = Annotated[float, Is[lambda x: 0.0 <= x <= 100.0]]

# Create matching strategies
positive_ints = st.integers(min_value=1)
percentages = st.floats(min_value=0.0, max_value=100.0, allow_nan=False)

@beartype
def apply_discount(price: PositiveInt, discount: Percentage) -> PositiveInt:
    result = int(price * (1 - discount / 100))
    return max(1, result)

@given(price=positive_ints, discount=percentages)
def test_apply_discount(price, discount):
    result = apply_discount(price, discount)
    assert result >= 1
    assert result <= price
```

### Hypothesis + deal: Auto-Generated Tests

```python
import deal
from hypothesis import settings

@deal.pre(lambda items, k: k > 0)
@deal.pre(lambda items, k: k <= len(items))
@deal.post(lambda result: len(result) == k)
@deal.ensure(lambda items, k, result: all(x in items for x in result))
def take_first_k(items: list, k: int) -> list:
    """Return first k items from list."""
    return items[:k]

# deal.cases generates a Hypothesis test from contracts
test_take_first_k = deal.cases(take_first_k)

# Can customize with settings
@settings(max_examples=500)
def test_take_first_k_thorough():
    deal.cases(take_first_k)()
```

### Building a Strategy from Refined Types

```python
from hypothesis import strategies as st
from typing import get_type_hints, get_origin, get_args, Annotated
import inspect

def strategy_for_refined_type(refined_type):
    """
    Generate a Hypothesis strategy that satisfies a beartype refined type.

    This is a simplified example - production code would handle more cases.
    """
    origin = get_origin(refined_type)

    if origin is Annotated:
        args = get_args(refined_type)
        base_type = args[0]
        validators = args[1:]

        # Get base strategy
        if base_type == int:
            base_strategy = st.integers()
        elif base_type == float:
            base_strategy = st.floats(allow_nan=False, allow_infinity=False)
        elif base_type == str:
            base_strategy = st.text()
        else:
            base_strategy = st.from_type(base_type)

        # Filter by validators
        for validator in validators:
            if hasattr(validator, '_is_valid'):
                base_strategy = base_strategy.filter(validator._is_valid)

        return base_strategy

    return st.from_type(refined_type)
```

---

## Part 5: Integration Patterns for Spec-Driven Development

### The Verification Pyramid

```
                    ┌─────────────────┐
                    │   crosshair     │  ◄── Formal verification
                    │   (symbolic)    │      (critical paths)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Hypothesis    │  ◄── Property-based testing
                    │   + deal.cases  │      (comprehensive coverage)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   deal          │  ◄── Contract checking
                    │   (runtime)     │      (all executions)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   beartype      │  ◄── Type enforcement
                    │   (types)       │      (every call)
                    └─────────────────┘
```

### Project Structure for Verified Code

```
myproject/
├── src/
│   └── myproject/
│       ├── __init__.py
│       ├── types.py          # Refined types (beartype)
│       ├── contracts.py      # Reusable contract functions
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── models.py     # Domain models with invariants
│       │   └── services.py   # Business logic with contracts
│       └── utils.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Hypothesis profiles, fixtures
│   ├── strategies.py         # Custom Hypothesis strategies
│   ├── test_domain.py        # Property-based tests
│   └── test_contracts.py     # deal.cases tests
├── pyproject.toml
└── Makefile
```

### Complete Example: A Verified Stack Implementation

```python
# src/myproject/types.py
"""Refined types for the project."""

from beartype.vale import Is
from typing import Annotated, TypeVar, List

T = TypeVar('T')

PositiveInt = Annotated[int, Is[lambda x: x > 0]]
NonNegativeInt = Annotated[int, Is[lambda x: x >= 0]]
Capacity = Annotated[int, Is[lambda x: 1 <= x <= 10000]]


# src/myproject/domain/stack.py
"""A verified bounded stack implementation."""

from __future__ import annotations
import deal
from beartype import beartype
from typing import Generic, TypeVar, Optional, List
from ..types import Capacity, NonNegativeInt

T = TypeVar('T')


@deal.inv(lambda self: 0 <= len(self._items) <= self._capacity)
class BoundedStack(Generic[T]):
    """
    A stack with a maximum capacity.

    Invariants:
    - Stack size is always between 0 and capacity
    - LIFO ordering is maintained

    All operations are O(1).
    """

    @beartype
    def __init__(self, capacity: Capacity):
        """
        Create an empty bounded stack.

        pre: capacity > 0
        post: self.is_empty()
        """
        self._capacity = capacity
        self._items: List[T] = []

    @property
    def capacity(self) -> int:
        """Maximum number of elements this stack can hold."""
        return self._capacity

    @deal.ensure(lambda self, result: result == len(self._items))
    def size(self) -> NonNegativeInt:
        """Current number of elements in the stack."""
        return len(self._items)

    @deal.ensure(lambda self, result: result == (len(self._items) == 0))
    def is_empty(self) -> bool:
        """True if the stack contains no elements."""
        return len(self._items) == 0

    @deal.ensure(lambda self, result: result == (len(self._items) == self._capacity))
    def is_full(self) -> bool:
        """True if the stack is at capacity."""
        return len(self._items) == self._capacity

    @deal.pre(lambda self, item: not self.is_full(), message="Stack is full")
    @deal.ensure(lambda self, item, result: self._items[-1] == item)
    @deal.ensure(lambda self, item, result: len(self._items) == len(deal.old(self._items)) + 1)
    @beartype
    def push(self, item: T) -> None:
        """
        Add an item to the top of the stack.

        Raises:
            PreContractError: If stack is full
        """
        self._items.append(item)

    @deal.pre(lambda self: not self.is_empty(), message="Stack is empty")
    @deal.ensure(lambda self, result: len(self._items) == len(deal.old(self._items)) - 1)
    def pop(self) -> T:
        """
        Remove and return the top item.

        Raises:
            PreContractError: If stack is empty
        """
        return self._items.pop()

    @deal.pre(lambda self: not self.is_empty(), message="Stack is empty")
    @deal.ensure(lambda self, result: result == self._items[-1])
    @deal.ensure(lambda self, result: len(self._items) == len(deal.old(self._items)))
    def peek(self) -> T:
        """
        Return the top item without removing it.

        Raises:
            PreContractError: If stack is empty
        """
        return self._items[-1]

    @deal.ensure(lambda self, result: self.is_empty())
    def clear(self) -> None:
        """Remove all items from the stack."""
        self._items.clear()


# tests/test_stack.py
"""Tests for the bounded stack."""

import deal
from hypothesis import given, strategies as st, assume
from myproject.domain.stack import BoundedStack

# Auto-generated tests from contracts
test_push_contracts = deal.cases(BoundedStack.push)
test_pop_contracts = deal.cases(BoundedStack.pop)
test_peek_contracts = deal.cases(BoundedStack.peek)


# Property-based tests
@given(
    capacity=st.integers(min_value=1, max_value=100),
    items=st.lists(st.integers(), max_size=50)
)
def test_push_pop_inverse(capacity, items):
    """Push then pop returns items in reverse order (LIFO)."""
    assume(len(items) <= capacity)

    stack = BoundedStack(capacity)
    for item in items:
        stack.push(item)

    popped = [stack.pop() for _ in items]
    assert popped == list(reversed(items))


@given(
    capacity=st.integers(min_value=1, max_value=100),
    items=st.lists(st.integers(), min_size=1, max_size=50)
)
def test_peek_does_not_modify(capacity, items):
    """Peek returns top item without changing stack size."""
    assume(len(items) <= capacity)

    stack = BoundedStack(capacity)
    for item in items:
        stack.push(item)

    size_before = stack.size()
    top = stack.peek()
    size_after = stack.size()

    assert size_before == size_after
    assert top == items[-1]


@given(capacity=st.integers(min_value=1, max_value=100))
def test_size_invariant(capacity):
    """Size is always between 0 and capacity."""
    stack = BoundedStack(capacity)

    assert stack.size() == 0
    assert stack.size() <= capacity

    # Fill to capacity
    for i in range(capacity):
        stack.push(i)
        assert 0 <= stack.size() <= capacity

    # Empty completely
    for _ in range(capacity):
        stack.pop()
        assert 0 <= stack.size() <= capacity
```

### Makefile for Verification Pipeline

```makefile
# Makefile

.PHONY: verify test lint typecheck all

# Run all verification
all: typecheck lint verify test

# Static type checking with mypy
typecheck:
	mypy src/ --strict

# Linting (includes deal's contract linter)
lint:
	ruff check src/ tests/
	deal lint src/

# Symbolic verification with crosshair
verify:
	crosshair check src/myproject/domain/ --per_condition_timeout=30

# Property-based tests with Hypothesis + deal
test:
	pytest tests/ -v --hypothesis-show-statistics

# Watch mode for development
watch:
	crosshair watch src/myproject/domain/

# Quick verification (fast feedback)
quick:
	pytest tests/ -v -x --hypothesis-profile=fast

# Thorough verification (CI pipeline)
thorough:
	pytest tests/ -v --hypothesis-profile=thorough
	crosshair check src/myproject/domain/ --per_condition_timeout=120
```

### Hypothesis Profiles in conftest.py

```python
# tests/conftest.py

from hypothesis import settings, Verbosity

# Fast profile for development
settings.register_profile(
    "fast",
    max_examples=10,
    verbosity=Verbosity.quiet
)

# Default profile
settings.register_profile(
    "default",
    max_examples=100,
    verbosity=Verbosity.normal
)

# Thorough profile for CI
settings.register_profile(
    "thorough",
    max_examples=1000,
    verbosity=Verbosity.verbose
)

# Load profile from environment
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "default"))
```

---

## Part 6: Agent-Ready Code Patterns

### Why This Matters for AI Agents

AI coding agents (like Claude Code, Codex, etc.) work best when:

1. **Specifications are explicit**: Agents can read and understand contracts
2. **Behavior is verifiable**: Agents can check their own work
3. **Interfaces are unambiguous**: No guessing about valid inputs/outputs
4. **Errors are informative**: Contract violations pinpoint the problem

### Pattern 1: Self-Describing Functions

```python
import deal
from beartype import beartype
from typing import Annotated
from beartype.vale import Is

# Types that describe themselves
Latitude = Annotated[float, Is[lambda x: -90.0 <= x <= 90.0]]
Longitude = Annotated[float, Is[lambda x: -180.0 <= x <= 180.0]]
DistanceKm = Annotated[float, Is[lambda x: x >= 0.0]]

@beartype
@deal.post(lambda result: result >= 0.0)
@deal.ensure(lambda lat1, lon1, lat2, lon2, result:
    result == 0.0 if (lat1 == lat2 and lon1 == lon2) else result > 0.0)
def haversine_distance(
    lat1: Latitude,
    lon1: Longitude,
    lat2: Latitude,
    lon2: Longitude
) -> DistanceKm:
    """
    Calculate great-circle distance between two points.

    An AI agent reading this function knows:
    - Exact valid ranges for all inputs
    - Output is always non-negative
    - Distance is zero iff points are identical
    """
    from math import radians, sin, cos, sqrt, atan2

    R = 6371.0  # Earth's radius in km

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c
```

### Pattern 2: Verified Data Transformations

```python
import deal
from beartype import beartype
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass(frozen=True)
class UserEvent:
    user_id: str
    event_type: str
    timestamp: int
    properties: Dict[str, Any]

@beartype
@deal.pre(lambda events: len(events) > 0, message="Need at least one event")
@deal.pre(lambda events: len(set(e.user_id for e in events)) == 1,
          message="All events must be for same user")
@deal.post(lambda result: "user_id" in result)
@deal.post(lambda result: "event_count" in result)
@deal.post(lambda result: result["event_count"] > 0)
@deal.ensure(lambda events, result: result["event_count"] == len(events))
@deal.ensure(lambda events, result: result["user_id"] == events[0].user_id)
def aggregate_user_events(events: List[UserEvent]) -> Dict[str, Any]:
    """
    Aggregate events for a single user into a summary.

    Contracts guarantee:
    - Input is non-empty and single-user
    - Output always has user_id and event_count
    - event_count matches input length
    """
    user_id = events[0].user_id
    event_types = {}

    for event in events:
        event_types[event.event_type] = event_types.get(event.event_type, 0) + 1

    return {
        "user_id": user_id,
        "event_count": len(events),
        "event_breakdown": event_types,
        "first_event": min(e.timestamp for e in events),
        "last_event": max(e.timestamp for e in events)
    }
```

### Pattern 3: Agent-Verifiable Pipelines

```python
import deal
from beartype import beartype
from typing import List, Callable, TypeVar
from dataclasses import dataclass

T = TypeVar('T')
U = TypeVar('U')

@dataclass
class PipelineStep:
    """A single step in a data pipeline with contracts."""
    name: str
    transform: Callable
    input_validator: Callable[[Any], bool]
    output_validator: Callable[[Any], bool]

class VerifiedPipeline:
    """
    A pipeline where each step has explicit contracts.

    AI agents can:
    - Inspect the pipeline structure
    - Verify each step's contracts
    - Understand data flow
    """

    def __init__(self):
        self._steps: List[PipelineStep] = []

    @deal.pre(lambda self, step: callable(step.transform))
    @deal.pre(lambda self, step: callable(step.input_validator))
    @deal.pre(lambda self, step: callable(step.output_validator))
    def add_step(self, step: PipelineStep) -> 'VerifiedPipeline':
        """Add a verified step to the pipeline."""
        self._steps.append(step)
        return self

    @deal.pre(lambda self, data: len(self._steps) > 0, message="Pipeline is empty")
    def run(self, data: Any) -> Any:
        """
        Execute pipeline with contract checking at each step.

        Raises:
            ValueError: If any step's input/output contract fails
        """
        current = data

        for step in self._steps:
            # Verify input contract
            if not step.input_validator(current):
                raise ValueError(
                    f"Step '{step.name}' input validation failed. "
                    f"Data: {current!r}"
                )

            # Transform
            current = step.transform(current)

            # Verify output contract
            if not step.output_validator(current):
                raise ValueError(
                    f"Step '{step.name}' output validation failed. "
                    f"Data: {current!r}"
                )

        return current

    def describe(self) -> str:
        """Generate human/agent-readable pipeline description."""
        lines = ["Pipeline Steps:"]
        for i, step in enumerate(self._steps, 1):
            lines.append(f"  {i}. {step.name}")
            lines.append(f"      Input: {step.input_validator.__doc__ or 'No description'}")
            lines.append(f"      Output: {step.output_validator.__doc__ or 'No description'}")
        return "\n".join(lines)


# Example usage
pipeline = VerifiedPipeline()
pipeline.add_step(PipelineStep(
    name="parse_json",
    transform=lambda x: json.loads(x),
    input_validator=lambda x: isinstance(x, str),
    output_validator=lambda x: isinstance(x, (dict, list))
))
pipeline.add_step(PipelineStep(
    name="extract_users",
    transform=lambda x: x.get("users", []),
    input_validator=lambda x: isinstance(x, dict),
    output_validator=lambda x: isinstance(x, list)
))
```

### Pattern 4: Contracts as Documentation for Agents

```python
import deal
import inspect
import json
from typing import Callable, Dict, Any, List

def extract_contracts(func: Callable) -> Dict[str, Any]:
    """
    Extract contract information from a function for agent consumption.

    Returns a structured description of:
    - Preconditions
    - Postconditions
    - Ensures (input-output relations)
    - Type hints
    """
    contracts = {
        "name": func.__name__,
        "docstring": inspect.getdoc(func),
        "signature": str(inspect.signature(func)),
        "preconditions": [],
        "postconditions": [],
        "ensures": [],
        "type_hints": {}
    }

    # Extract type hints
    hints = get_type_hints(func) if hasattr(func, '__annotations__') else {}
    contracts["type_hints"] = {k: str(v) for k, v in hints.items()}

    # Extract deal contracts
    if hasattr(func, '__wrapped__'):
        # deal stores contracts on the wrapper
        for validator in getattr(func, '_deal_validators', []):
            if isinstance(validator, deal.PreValidator):
                contracts["preconditions"].append(str(validator))
            elif isinstance(validator, deal.PostValidator):
                contracts["postconditions"].append(str(validator))
            elif isinstance(validator, deal.EnsureValidator):
                contracts["ensures"].append(str(validator))

    return contracts


def generate_agent_context(module) -> str:
    """
    Generate a context document for AI agents describing
    all verified functions in a module.
    """
    context = []

    for name in dir(module):
        obj = getattr(module, name)
        if callable(obj) and not name.startswith('_'):
            contracts = extract_contracts(obj)
            if contracts["preconditions"] or contracts["postconditions"]:
                context.append(contracts)

    return json.dumps(context, indent=2)
```

---

## Part 7: Comparison Matrix and Decision Guide

### When to Use Each Tool

| Scenario | beartype | deal | crosshair | Hypothesis |
|----------|----------|------|-----------|------------|
| Type enforcement at runtime | ✅ Primary | | | |
| Domain modeling with constraints | ✅ Primary | ✅ Supports | | |
| Pre/post conditions | | ✅ Primary | ✅ Verifies | |
| Class invariants | | ✅ Primary | ✅ Verifies | |
| Auto-generate tests | | ✅ deal.cases | | ✅ Primary |
| Find edge cases | | | ✅ Primary | ✅ Sampling |
| Prove correctness | | | ✅ Primary | |
| Fast CI feedback | ✅ Zero overhead | ✅ Fast | ❌ Slow | ✅ Fast |
| Critical security code | ✅ Layer 1 | ✅ Layer 2 | ✅ Layer 3 | ✅ Layer 4 |

### Recommended Combinations

**Minimum viable verification:**
```python
# Just beartype for type safety
pip install beartype
```

**Standard verification stack:**
```python
# Types + contracts + property testing
pip install beartype deal hypothesis
```

**Full verification suite:**
```python
# All tools for critical code
pip install beartype deal hypothesis crosshair-tool
```

### Performance Characteristics

| Tool | Overhead | When Paid |
|------|----------|-----------|
| beartype | ~1-10μs per call | Every function call |
| deal | ~10-100μs per call | Every function call |
| crosshair | Seconds to minutes | Static analysis only |
| Hypothesis | Test time only | Test execution |

### Disabling for Production

```python
# For performance-critical production code

import os

# beartype: Use BeartypeConf
from beartype import BeartypeConf
from beartype._decor.decorcore import beartype

if os.getenv("PRODUCTION"):
    # No-op decorator in production
    beartype = lambda func: func

# deal: Built-in disable
import deal
if os.getenv("PRODUCTION"):
    deal.disable()
```

---

## Part 8: Getting Started Checklist

### Installation

```bash
# Core tools
pip install beartype deal hypothesis crosshair-tool

# Optional: deal's linter
pip install deal[lint]

# Optional: improved Hypothesis output
pip install hypothesis[cli]
```

### First Steps

1. **Add beartype to existing code:**
   ```python
   from beartype import beartype

   @beartype
   def existing_function(x: int) -> str:
       ...
   ```

2. **Define domain types:**
   ```python
   # types.py
   from beartype.vale import Is
   from typing import Annotated

   PositiveInt = Annotated[int, Is[lambda x: x > 0]]
   ```

3. **Add contracts to critical functions:**
   ```python
   import deal

   @deal.pre(lambda x: x > 0)
   @deal.post(lambda result: result is not None)
   def critical_function(x):
       ...
   ```

4. **Generate tests from contracts:**
   ```python
   # tests/test_contracts.py
   import deal
   from mymodule import critical_function

   test_critical = deal.cases(critical_function)
   ```

5. **Run verification pipeline:**
   ```bash
   # Type check
   mypy src/

   # Contract lint
   deal lint src/

   # Symbolic verification (critical code only)
   crosshair check src/mymodule/critical.py

   # Property tests
   pytest tests/ -v
   ```

---

## Conclusion

The combination of beartype, deal, crosshair, and Hypothesis creates a powerful verification stack for Python that enables true spec-driven development:

- **beartype** provides the foundation with zero-overhead type enforcement and refinement types
- **deal** adds Design by Contract with pre/post conditions and invariants
- **crosshair** enables formal verification through symbolic execution
- **Hypothesis** ties it all together with property-based test generation

For agent-ready code, this stack provides:

- Machine-readable specifications that agents can parse and understand
- Self-verifying code that agents can validate
- Unambiguous interfaces that reduce agent errors
- Comprehensive test generation that catches agent mistakes

The key insight is that these tools are complementary, not competing. Use them in layers: types as the foundation, contracts for behavior, symbolic execution for proofs, and property-based testing for confidence.

---

## References and Further Reading

- [beartype documentation](https://beartype.readthedocs.io/)
- [deal documentation](https://deal.readthedocs.io/)
- [crosshair documentation](https://crosshair.readthedocs.io/)
- [Hypothesis documentation](https://hypothesis.readthedocs.io/)
- [Design by Contract (Wikipedia)](https://en.wikipedia.org/wiki/Design_by_contract)
- [Hoare Logic (Wikipedia)](https://en.wikipedia.org/wiki/Hoare_logic)
- [Refinement Types (Wikipedia)](https://en.wikipedia.org/wiki/Refinement_type)
