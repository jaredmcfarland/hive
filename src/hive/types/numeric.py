"""Domain-specific numeric refinement types."""

from __future__ import annotations

from typing import Annotated

from beartype.vale import Is

Port = Annotated[int, Is[lambda x: 1 <= x <= 65535]]
"""Valid TCP/UDP port number (1-65535)."""

HttpStatusCode = Annotated[int, Is[lambda x: 100 <= x <= 599]]
"""HTTP status code (100-599)."""

UnixTimestamp = Annotated[int, Is[lambda x: x >= 0]]
"""Unix timestamp (non-negative integer)."""

Year = Annotated[int, Is[lambda x: 1 <= x <= 9999]]
"""Year (1-9999)."""

Month = Annotated[int, Is[lambda x: 1 <= x <= 12]]
"""Month (1-12)."""

Day = Annotated[int, Is[lambda x: 1 <= x <= 31]]
"""Day of month (1-31)."""

Hour = Annotated[int, Is[lambda x: 0 <= x <= 23]]
"""Hour (0-23)."""

Minute = Annotated[int, Is[lambda x: 0 <= x <= 59]]
"""Minute (0-59)."""

Second = Annotated[int, Is[lambda x: 0 <= x <= 59]]
"""Second (0-59)."""
