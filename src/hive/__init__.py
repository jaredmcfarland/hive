"""Hive - A framework for building terminal-agent-native applications."""

__version__ = "0.1.0"

# Errors
# Core class
from hive.app import App

# Decorators
from hive.core.decorators import command, entity, query, screen

# Types for annotations
from hive.core.types import Argument, Option
from hive.errors import (
    CommandError,
    ConfigurationError,
    HiveError,
    RegistrationError,
    ValidationError,
)

__all__ = [
    "__version__",
    "App",
    "command",
    "query",
    "entity",
    "screen",
    "Argument",
    "Option",
    "CommandError",
    "ConfigurationError",
    "HiveError",
    "RegistrationError",
    "ValidationError",
]
