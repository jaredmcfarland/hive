"""
Contract utilities for Hive commands.

Optional decorators for adding pre/post conditions to commands.
These integrate with deal but provide Hive-specific error handling.

Example:
    from hive import command, App
    from hive.contracts import requires, ensures

    app = App("myapp")

    @command(app)
    @requires(lambda ctx, task_id: task_id > 0, "Task ID must be positive")
    @ensures(lambda ctx, task_id, result: result.id == task_id)
    async def get_task(ctx, task_id: int) -> Task:
        ...
"""

from hive.contracts.decorators import requires, ensures, invariant

__all__ = ["requires", "ensures", "invariant"]
