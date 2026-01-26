"""trakr - A Hive application.

A Hive application
"""

from __future__ import annotations

from typing import Any

from hive import App, command, query

app = App("trakr", description="Track projects, time, and generate invoices")


@command(app)
async def hello(ctx: Any, name: str = "World") -> str:  # noqa: ARG001
    """Say hello to someone.

    Args:
        ctx: Execution context.
        name: Name to greet.

    Returns:
        Greeting message.
    """
    return f"Hello, {name}!"


@query(app)
async def status(ctx: Any) -> dict[str, str]:  # noqa: ARG001
    """Get application status.

    Args:
        ctx: Execution context.

    Returns:
        Status dictionary.
    """
    return {"status": "ok", "app": "trakr"}


def cli() -> None:
    """CLI entry point."""
    from hive.generators.cli import CLIGenerator

    typer_app = CLIGenerator(app).generate()
    typer_app()


if __name__ == "__main__":
    cli()
