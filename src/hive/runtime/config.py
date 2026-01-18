"""Application configuration using Pydantic Settings."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application settings loaded from environment variables.

    Environment variables are prefixed with HIVE_ and use uppercase names.
    For example, HIVE_DATABASE_URL, HIVE_DEBUG, HIVE_LOG_LEVEL.
    """

    model_config = SettingsConfigDict(
        env_prefix="HIVE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
        validate_default=True,
    )

    database_url: str = Field(
        default=f"sqlite+aiosqlite:///{Path.home()}/.hive/data.db",
        description="Database connection URL (SQLAlchemy async format)",
    )

    debug: bool = Field(
        default=False,
        description="Enable debug mode with verbose output",
    )

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level for the application",
    )
