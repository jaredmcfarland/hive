"""Unit tests for configuration loading (T043)."""



class TestAppSettings:
    """Tests for config loading from environment variables."""

    def test_default_values(self) -> None:
        """AppSettings has sensible defaults."""
        from hive.runtime.config import AppSettings

        settings = AppSettings()

        assert settings.debug is False
        assert settings.log_level == "INFO"
        assert "sqlite" in settings.database_url

    def test_env_var_override(self, env_override) -> None:
        """Environment variables override defaults."""
        env_override(
            HIVE_DEBUG="true",
            HIVE_LOG_LEVEL="DEBUG",
            HIVE_DATABASE_URL="sqlite:///test.db",
        )

        from hive.runtime.config import AppSettings

        settings = AppSettings()

        assert settings.debug is True
        assert settings.log_level == "DEBUG"
        assert settings.database_url == "sqlite:///test.db"

    def test_database_url_from_env(self, env_override) -> None:
        """Database URL can be configured via environment."""
        env_override(HIVE_DATABASE_URL="postgresql://user:pass@localhost/db")

        from hive.runtime.config import AppSettings

        settings = AppSettings()

        assert settings.database_url == "postgresql://user:pass@localhost/db"

    def test_boolean_parsing(self, env_override) -> None:
        """Boolean environment variables are parsed correctly."""
        # Test various truthy values
        for value in ["true", "True", "TRUE", "1", "yes"]:
            env_override(HIVE_DEBUG=value)
            from importlib import reload

            import hive.runtime.config as config_module

            reload(config_module)
            settings = config_module.AppSettings()
            assert settings.debug is True, f"Failed for value: {value}"

        # Test falsy values
        for value in ["false", "False", "FALSE", "0", "no"]:
            env_override(HIVE_DEBUG=value)
            from importlib import reload

            import hive.runtime.config as config_module

            reload(config_module)
            settings = config_module.AppSettings()
            assert settings.debug is False, f"Failed for value: {value}"
