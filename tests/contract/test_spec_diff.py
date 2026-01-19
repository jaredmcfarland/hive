"""Contract tests for specification diff functionality.

Tests diff_specifications() and breaking change detection.

RED phase: These tests should FAIL until diff functionality is implemented.
"""


class TestDiffSpecifications:
    """Contract tests for diff_specifications() function."""

    def test_diff_specifications_exists(self) -> None:
        """diff_specifications function exists and is importable."""
        from hive.spec.diff import diff_specifications

        assert callable(diff_specifications)

    def test_diff_identical_specs(self) -> None:
        """diff_specifications returns empty diff for identical specs."""
        from hive.spec.diff import diff_specifications

        spec1 = {
            "metadata": {"name": "app", "version": "1.0.0"},
            "commands": {},
            "queries": {},
            "entities": {},
        }
        spec2 = spec1.copy()

        diff = diff_specifications(spec1, spec2)

        assert len(diff.changes) == 0
        assert len(diff.breaking_changes) == 0

    def test_diff_detects_added_command(self) -> None:
        """diff_specifications detects added commands."""
        from hive.spec.diff import diff_specifications

        spec1 = {
            "metadata": {"name": "app", "version": "1.0.0"},
            "commands": {},
            "queries": {},
            "entities": {},
        }
        spec2 = {
            "metadata": {"name": "app", "version": "1.1.0"},
            "commands": {
                "new_cmd": {"name": "new_cmd", "parameters": [], "return_type": {}},
            },
            "queries": {},
            "entities": {},
        }

        diff = diff_specifications(spec1, spec2)

        # Should have at least one change
        assert len(diff.changes) >= 1
        # Added command should be in changes
        added = [c for c in diff.changes if c.change_type == "added"]
        assert len(added) >= 1

    def test_diff_detects_removed_command(self) -> None:
        """diff_specifications detects removed commands."""
        from hive.spec.diff import diff_specifications

        spec1 = {
            "metadata": {"name": "app", "version": "1.0.0"},
            "commands": {
                "old_cmd": {"name": "old_cmd", "parameters": [], "return_type": {}},
            },
            "queries": {},
            "entities": {},
        }
        spec2 = {
            "metadata": {"name": "app", "version": "2.0.0"},
            "commands": {},
            "queries": {},
            "entities": {},
        }

        diff = diff_specifications(spec1, spec2)

        # Should have at least one change
        assert len(diff.changes) >= 1
        # Removed command should be in changes
        removed = [c for c in diff.changes if c.change_type == "removed"]
        assert len(removed) >= 1

    def test_diff_detects_modified_parameter(self) -> None:
        """diff_specifications detects modified parameters."""
        from hive.spec.diff import diff_specifications

        spec1 = {
            "metadata": {"name": "app", "version": "1.0.0"},
            "commands": {
                "cmd": {
                    "name": "cmd",
                    "parameters": [{"name": "x", "type": "integer"}],
                    "return_type": {},
                },
            },
            "queries": {},
            "entities": {},
        }
        spec2 = {
            "metadata": {"name": "app", "version": "1.1.0"},
            "commands": {
                "cmd": {
                    "name": "cmd",
                    "parameters": [{"name": "x", "type": "string"}],  # Changed type
                    "return_type": {},
                },
            },
            "queries": {},
            "entities": {},
        }

        diff = diff_specifications(spec1, spec2)

        assert len(diff.changes) >= 1


class TestBreakingChangeDetection:
    """Contract tests for breaking change detection."""

    def test_removed_command_is_breaking(self) -> None:
        """Removing a command is a breaking change."""
        from hive.spec.diff import diff_specifications

        spec1 = {
            "metadata": {"name": "app", "version": "1.0.0"},
            "commands": {
                "old_cmd": {"name": "old_cmd", "parameters": [], "return_type": {}},
            },
            "queries": {},
            "entities": {},
        }
        spec2 = {
            "metadata": {"name": "app", "version": "2.0.0"},
            "commands": {},
            "queries": {},
            "entities": {},
        }

        diff = diff_specifications(spec1, spec2)

        assert diff.has_breaking_changes is True
        assert len(diff.breaking_changes) >= 1

    def test_removed_required_parameter_is_breaking(self) -> None:
        """Removing a required parameter is a breaking change."""
        from hive.spec.diff import diff_specifications

        spec1 = {
            "metadata": {"name": "app", "version": "1.0.0"},
            "commands": {
                "cmd": {
                    "name": "cmd",
                    "parameters": [
                        {"name": "required_param", "type": "string", "required": True},
                    ],
                    "return_type": {},
                },
            },
            "queries": {},
            "entities": {},
        }
        spec2 = {
            "metadata": {"name": "app", "version": "2.0.0"},
            "commands": {
                "cmd": {
                    "name": "cmd",
                    "parameters": [],  # Removed parameter
                    "return_type": {},
                },
            },
            "queries": {},
            "entities": {},
        }

        diff = diff_specifications(spec1, spec2)

        assert diff.has_breaking_changes is True

    def test_added_command_is_not_breaking(self) -> None:
        """Adding a command is NOT a breaking change."""
        from hive.spec.diff import diff_specifications

        spec1 = {
            "metadata": {"name": "app", "version": "1.0.0"},
            "commands": {},
            "queries": {},
            "entities": {},
        }
        spec2 = {
            "metadata": {"name": "app", "version": "1.1.0"},
            "commands": {
                "new_cmd": {"name": "new_cmd", "parameters": [], "return_type": {}},
            },
            "queries": {},
            "entities": {},
        }

        diff = diff_specifications(spec1, spec2)

        # Adding a command is NOT breaking
        assert diff.has_breaking_changes is False

    def test_added_optional_parameter_is_not_breaking(self) -> None:
        """Adding an optional parameter is NOT a breaking change."""
        from hive.spec.diff import diff_specifications

        spec1 = {
            "metadata": {"name": "app", "version": "1.0.0"},
            "commands": {
                "cmd": {
                    "name": "cmd",
                    "parameters": [],
                    "return_type": {},
                },
            },
            "queries": {},
            "entities": {},
        }
        spec2 = {
            "metadata": {"name": "app", "version": "1.1.0"},
            "commands": {
                "cmd": {
                    "name": "cmd",
                    "parameters": [
                        {"name": "optional_param", "type": "string", "required": False},
                    ],
                    "return_type": {},
                },
            },
            "queries": {},
            "entities": {},
        }

        diff = diff_specifications(spec1, spec2)

        # Adding optional parameter is NOT breaking
        assert diff.has_breaking_changes is False

    def test_diff_summary(self) -> None:
        """SpecificationDiff has summary property."""
        from hive.spec.diff import diff_specifications

        spec1 = {
            "metadata": {"name": "app", "version": "1.0.0"},
            "commands": {
                "old_cmd": {"name": "old_cmd", "parameters": [], "return_type": {}},
            },
            "queries": {},
            "entities": {},
        }
        spec2 = {
            "metadata": {"name": "app", "version": "2.0.0"},
            "commands": {
                "new_cmd": {"name": "new_cmd", "parameters": [], "return_type": {}},
            },
            "queries": {},
            "entities": {},
        }

        diff = diff_specifications(spec1, spec2)

        # Should have summary string
        summary = diff.summary
        assert isinstance(summary, str)
        assert "+" in summary or "-" in summary or "~" in summary
