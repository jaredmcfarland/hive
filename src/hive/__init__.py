"""Hive - A framework for building terminal-agent-native applications."""

from __future__ import annotations

__version__ = "0.1.0"

# Errors
# Core class
from hive.app import App

# Decorators
from hive.core.decorators import command, entity, query, screen, service

# Types for annotations
from hive.core.types import Argument, Option
from hive.errors import (
    CommandError,
    ConfigurationError,
    CredentialError,
    HiveError,
    RegistrationError,
    ValidationError,
)

__all__ = [
    "App",
    "Argument",
    "CommandError",
    "ConfigurationError",
    "CredentialError",
    "HiveError",
    "Option",
    "RegistrationError",
    "ValidationError",
    "__version__",
    "command",
    "entity",
    "query",
    "screen",
    "service",
]
