"""Core numeric refinement types."""

from typing import Annotated

from beartype.vale import Is

# Integer refinements
PositiveInt = Annotated[int, Is[lambda x: x > 0]]
"""Integer greater than zero."""

NonNegativeInt = Annotated[int, Is[lambda x: x >= 0]]
"""Integer greater than or equal to zero."""

NegativeInt = Annotated[int, Is[lambda x: x < 0]]
"""Integer less than zero."""

# Float refinements
PositiveFloat = Annotated[float, Is[lambda x: x > 0.0]]
"""Float greater than zero."""

NonNegativeFloat = Annotated[float, Is[lambda x: x >= 0.0]]
"""Float greater than or equal to zero."""

UnitInterval = Annotated[float, Is[lambda x: 0.0 <= x <= 1.0]]
"""Float between 0.0 and 1.0 inclusive."""

Percentage = Annotated[float, Is[lambda x: 0.0 <= x <= 100.0]]
"""Float between 0.0 and 100.0 inclusive."""

Probability = UnitInterval
"""Alias for UnitInterval, semantically representing probability."""
