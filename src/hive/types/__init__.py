"""
Hive Refinement Types

Semantic type aliases with runtime-enforced constraints.
Use these in command signatures to get automatic validation.

Example:
    from hive import command, App
    from hive.types import PositiveInt, Percentage

    app = App("myapp")

    @command(app)
    async def set_progress(ctx, task_id: PositiveInt, progress: Percentage):
        ...
"""

from hive.types.primitives import (
    PositiveInt,
    NonNegativeInt,
    NegativeInt,
    PositiveFloat,
    NonNegativeFloat,
    UnitInterval,
    Percentage,
    Probability,
)

__all__ = [
    # Integer refinements
    "PositiveInt",
    "NonNegativeInt",
    "NegativeInt",
    # Float refinements
    "PositiveFloat",
    "NonNegativeFloat",
    "UnitInterval",
    "Percentage",
    "Probability",
]
