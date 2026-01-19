"""Hive - A framework for building terminal-agent-native applications."""

from __future__ import annotations

__version__ = "0.1.0"

# Core class
from hive.app import App

# Decorators
from hive.core.decorators import command, entity, query, screen, service

# Types for annotations
from hive.core.types import Argument, Option

# Errors
from hive.errors import (
    CommandError,
    ConfigurationError,
    CredentialError,
    HiveError,
    RegistrationError,
    ValidationError,
)

# Generators (optional dependencies)
from hive.generators.mcp import MCPGenerator
from hive.generators.rest import RESTGenerator

# Specification export and diff
from hive.spec.diff import diff_specifications
from hive.spec.export import build_specification, export_specification

__all__ = [  # noqa: RUF022
    # Core
    "App",
    "__version__",
    # Decorators
    "command",
    "entity",
    "query",
    "screen",
    "service",
    # Types
    "Argument",
    "Option",
    # Errors
    "CommandError",
    "ConfigurationError",
    "CredentialError",
    "HiveError",
    "RegistrationError",
    "ValidationError",
    # Generators
    "MCPGenerator",
    "RESTGenerator",
    # Specification
    "build_specification",
    "diff_specifications",
    "export_specification",
]
