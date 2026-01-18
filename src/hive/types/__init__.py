"""
Hive Refinement Types.

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

from __future__ import annotations

from hive.types.numeric import (
    Day,
    Hour,
    HttpStatusCode,
    Minute,
    Month,
    Port,
    Second,
    UnixTimestamp,
    Year,
)
from hive.types.primitives import (
    NegativeInt,
    NonNegativeFloat,
    NonNegativeInt,
    Percentage,
    PositiveFloat,
    PositiveInt,
    Probability,
    UnitInterval,
)
from hive.types.strings import (
    DirectoryPath,
    Email,
    FilePath,
    Identifier,
    LowercaseStr,
    NonEmptyStr,
    Slug,
    TrimmedStr,
    UppercaseStr,
    Url,
)

__all__ = [
    "Day",
    "DirectoryPath",
    "Email",
    "FilePath",
    "Hour",
    "HttpStatusCode",
    "Identifier",
    "LowercaseStr",
    "Minute",
    "Month",
    "NegativeInt",
    # String refinements
    "NonEmptyStr",
    "NonNegativeFloat",
    "NonNegativeInt",
    "Percentage",
    # Numeric domain types
    "Port",
    # Float refinements
    "PositiveFloat",
    # Integer refinements
    "PositiveInt",
    "Probability",
    "Second",
    "Slug",
    "TrimmedStr",
    "UnitInterval",
    "UnixTimestamp",
    "UppercaseStr",
    "Url",
    "Year",
]
