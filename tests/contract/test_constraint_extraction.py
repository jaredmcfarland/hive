"""Test that decorators extract constraints from refinement types."""


class TestCommandConstraintExtraction:
    """Tests for constraint extraction in @command decorator."""

    def test_extracts_constraints_from_positive_int(self) -> None:
        """@command extracts constraints from PositiveInt parameter."""
        from hive import App, command
        from hive.types import PositiveInt

        app = App(name="test-app")

        @command(app)
        async def create_task(ctx, priority: PositiveInt) -> dict:
            """Create task with priority."""
            return {"priority": priority}

        reg = app.registry.get_command("create_task")
        assert reg is not None

        # Find priority parameter
        priority_param = next(p for p in reg.parameters if p.name == "priority")
        assert priority_param.constraints is not None
        assert priority_param.constraints.min_value is not None

    def test_extracts_constraints_from_port(self) -> None:
        """@command extracts min/max constraints from Port parameter."""
        from hive import App, command
        from hive.types import Port

        app = App(name="test-app")

        @command(app)
        async def start_server(ctx, port: Port) -> dict:
            """Start server on port."""
            return {"port": port}

        reg = app.registry.get_command("start_server")
        assert reg is not None

        port_param = next(p for p in reg.parameters if p.name == "port")
        assert port_param.constraints is not None
        assert port_param.constraints.min_value == 1
        assert port_param.constraints.max_value == 65535

    def test_no_constraints_for_plain_types(self) -> None:
        """@command has no constraints for plain int/str types."""
        from hive import App, command

        app = App(name="test-app")

        @command(app)
        async def echo(ctx, message: str, count: int) -> dict:
            """Echo message."""
            return {"message": message, "count": count}

        reg = app.registry.get_command("echo")
        assert reg is not None

        message_param = next(p for p in reg.parameters if p.name == "message")
        assert message_param.constraints is None

        count_param = next(p for p in reg.parameters if p.name == "count")
        assert count_param.constraints is None
