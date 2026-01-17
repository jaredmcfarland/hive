"""Application configuration using Pydantic Settings."""

from pathlib import Path

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
        extra="ignore",
    )

    # Database configuration
    database_url: str = f"sqlite+aiosqlite:///{Path.home()}/.hive/data.db"

    # Debug mode
    debug: bool = False

    # Logging configuration
    log_level: str = "INFO"
