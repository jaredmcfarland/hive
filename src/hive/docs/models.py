"""Data models for documentation generation.

This module contains configuration and output models for the
documentation generation system.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DocumentationConfig(BaseModel):
    """Configuration for documentation generation.

    Controls the format, output location, and content options for
    generated documentation.

    Attributes:
        format: Output format (markdown or manpage).
        output_dir: Directory for generated files. If None, writes to stdout.
        include_private: Include private commands (default: False).
        include_examples: Include usage examples from docstrings (default: True).
        include_contracts: Include @requires/@ensures documentation (default: True).

    Example:
        >>> config = DocumentationConfig(
        ...     format="markdown",
        ...     output_dir=Path("docs/"),
        ... )
    """

    model_config = ConfigDict(strict=True, frozen=True)

    format: Literal["markdown", "manpage"] = Field(
        default="markdown",
        description="Output format",
    )
    output_dir: Path | None = Field(
        default=None,
        description="Directory for generated files (None = stdout)",
    )
    include_private: bool = Field(
        default=False,
        description="Include private commands (underscore-prefixed)",
    )
    include_examples: bool = Field(
        default=True,
        description="Include usage examples from docstrings",
    )
    include_contracts: bool = Field(
        default=True,
        description="Include @requires/@ensures documentation",
    )


class DocumentationOutput(BaseModel):
    """Result of documentation generation.

    Contains information about generated files and statistics.

    Attributes:
        files_generated: List of paths to generated files.
        commands_documented: Number of commands documented.
        queries_documented: Number of queries documented.
        entities_documented: Number of entities documented.
        warnings: Any warnings encountered during generation.
        content: Generated content if output_dir was None (stdout mode).

    Example:
        >>> result = generator.generate(config)
        >>> print(f"Generated {len(result.files_generated)} files")
        >>> if result.warnings:
        ...     print(f"Warnings: {result.warnings}")
    """

    model_config = ConfigDict(strict=True, frozen=True)

    files_generated: list[Path] = Field(
        default_factory=list,
        description="Paths to generated files",
    )
    commands_documented: int = Field(
        default=0,
        description="Number of commands documented",
    )
    queries_documented: int = Field(
        default=0,
        description="Number of queries documented",
    )
    entities_documented: int = Field(
        default=0,
        description="Number of entities documented",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Warnings encountered (e.g., missing docstrings)",
    )
    content: str | None = Field(
        default=None,
        description="Generated content (stdout mode only)",
    )

    @property
    def total_documented(self) -> int:
        """Total number of items documented."""
        return self.commands_documented + self.queries_documented + self.entities_documented

    @property
    def has_warnings(self) -> bool:
        """Check if any warnings were generated."""
        return len(self.warnings) > 0
