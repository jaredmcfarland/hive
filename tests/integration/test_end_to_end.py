"""End-to-end integration tests (T060)."""

import json

from typer.testing import CliRunner

runner = CliRunner()


class TestEndToEnd:
    """End-to-end command execution tests (T060)."""

    def test_command_execution_with_database(self, temp_db_url: str) -> None:
        """Complete command execution with database operations."""
        import asyncio
        import os

        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlmodel import Field, SQLModel

        from hive import App, command, entity, query

        # Set database URL via environment
        os.environ["HIVE_DATABASE_URL"] = temp_db_url

        try:
            app = App(name="test-app")

            @entity(app)
            class Task(SQLModel, table=True):
                __tablename__ = "e2e_task"
                id: int | None = Field(default=None, primary_key=True)
                title: str
                done: bool = False

            @command(app)
            async def add(ctx, title: str) -> dict:
                """Add a new task."""
                task = Task(title=title)
                ctx.db.add(task)
                await ctx.db.commit()
                await ctx.db.refresh(task)
                return {"id": task.id, "title": task.title}

            @query(app)
            async def list_tasks(ctx) -> list:
                """List tasks."""
                return []

            # Create tables synchronously
            async def create_tables():
                engine = create_async_engine(temp_db_url)
                async with engine.begin() as conn:
                    await conn.run_sync(SQLModel.metadata.create_all)
                await engine.dispose()

            asyncio.run(create_tables())

            # Execute via CLI
            cli = app.cli()
            result = runner.invoke(cli, ["add", "Test Task", "--json"])

            assert result.exit_code == 0, f"Failed with: {result.output}"
            data = json.loads(result.stdout)
            assert data["title"] == "Test Task"
            assert "id" in data

        finally:
            os.environ.pop("HIVE_DATABASE_URL", None)

    def test_command_with_options(self) -> None:
        """Command execution with various option types."""
        from hive import App, command, query

        app = App(name="test-app")

        @command(app)
        async def process(
            ctx,
            input_file: str,
            output_file: str | None = None,
            verbose: bool = False,
            count: int = 1,
        ) -> dict:
            """Process a file."""
            return {
                "input": input_file,
                "output": output_file,
                "verbose": verbose,
                "count": count,
            }

        @query(app)
        async def noop(ctx) -> list:
            """Placeholder query."""
            return []

        cli = app.cli()

        # Test with all options
        result = runner.invoke(
            cli,
            [
                "process",
                "input.txt",
                "--output-file",
                "output.txt",
                "--verbose",
                "--count",
                "5",
                "--json",
            ],
        )

        assert result.exit_code == 0, f"Failed with: {result.output}"
        data = json.loads(result.stdout)
        assert data["input"] == "input.txt"
        assert data["output"] == "output.txt"
        assert data["verbose"] is True
        assert data["count"] == 5

    def test_query_returns_list(self) -> None:
        """Query returning a list is properly formatted."""
        from pydantic import BaseModel

        from hive import App, command, query

        app = App(name="test-app")

        class Item(BaseModel):
            id: int
            name: str

        @query(app)
        async def list_items(ctx) -> list[Item]:
            """List all items."""
            return [
                Item(id=1, name="First"),
                Item(id=2, name="Second"),
                Item(id=3, name="Third"),
            ]

        @command(app)
        async def noop(ctx) -> None:
            """Placeholder command."""
            pass

        cli = app.cli()
        result = runner.invoke(cli, ["list-items", "--json"])

        assert result.exit_code == 0, f"Failed with: {result.output}"
        data = json.loads(result.stdout)
        assert len(data) == 3
        assert data[0]["name"] == "First"
        assert data[2]["name"] == "Third"

    def test_command_error_handling(self) -> None:
        """Command errors are properly handled and reported."""
        from hive import App, CommandError, command, query

        app = App(name="test-app")

        @command(app)
        async def failing_command(ctx) -> None:
            """A command that fails."""
            raise CommandError("Something went wrong")

        @query(app)
        async def noop(ctx) -> list:
            """Placeholder query."""
            return []

        cli = app.cli()
        result = runner.invoke(cli, ["failing-command"])

        assert result.exit_code == 1
        assert "Something went wrong" in result.stdout or "Something went wrong" in result.output
