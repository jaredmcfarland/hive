"""String refinement types."""

from __future__ import annotations

import re
from typing import Annotated

from beartype.vale import Is

NonEmptyStr = Annotated[str, Is[lambda s: len(s) > 0]]
"""Non-empty string."""

TrimmedStr = Annotated[str, Is[lambda s: s == s.strip()]]
"""String with no leading or trailing whitespace."""

LowercaseStr = Annotated[str, Is[lambda s: s == s.lower()]]
"""Lowercase string."""

UppercaseStr = Annotated[str, Is[lambda s: s == s.upper()]]
"""Uppercase string."""

Identifier = Annotated[str, Is[lambda s: s.isidentifier()]]
"""Valid Python identifier."""

Slug = Annotated[str, Is[lambda s: bool(re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", s))]]
"""URL-safe slug (lowercase alphanumeric with hyphens)."""

Email = Annotated[
    str, Is[lambda s: bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", s))]
]
"""Email address (basic validation)."""

Url = Annotated[str, Is[lambda s: bool(re.match(r"^https?://[^\s/$.?#].[^\s]*$", s))]]
"""HTTP or HTTPS URL."""

FilePath = Annotated[str, Is[lambda s: len(s) > 0 and "\0" not in s]]
"""Non-empty string without null bytes (valid file path)."""

DirectoryPath = FilePath
"""Alias for FilePath, semantically representing a directory."""
