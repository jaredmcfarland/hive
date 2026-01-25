"""Man page documentation generator.

This module implements the ManPageGenerator class for generating
Unix man pages (troff format) from Hive application specifications.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, override

from hive.docs.base import BaseDocumentationGenerator
from hive.docs.models import DocumentationConfig, DocumentationOutput

if TYPE_CHECKING:
    from hive.app import App
    from hive.spec.models import CommandSchema


class ManPageGenerator(BaseDocumentationGenerator):
    """Generate Unix man pages from a Hive application.

    Creates man pages in troff/groff format for each command.
    Man pages follow standard Unix conventions with sections for
    NAME, SYNOPSIS, DESCRIPTION, OPTIONS, etc.

    Attributes:
        app: The Hive application to document.
        env: Jinja2 environment with manpage templates.

    Example:
        >>> from hive.docs import ManPageGenerator, DocumentationConfig
        >>> from pathlib import Path
        >>>
        >>> generator = ManPageGenerator(app)
        >>> config = DocumentationConfig(
        ...     format="manpage",
        ...     output_dir=Path("man/"),
        ... )
        >>> result = generator.generate(config)
        >>> print(f"Generated {result.total_documented} man pages")
    """

    def __init__(self, app: App) -> None:
        """Initialize the man page generator.

        Args:
            app: Hive application to document.
        """
        super().__init__(app, "manpage")

    @override
    def generate(self, config: DocumentationConfig) -> DocumentationOutput:
        """Generate man pages.

        Args:
            config: Documentation configuration.

        Returns:
            DocumentationOutput with generation results.
        """
        # Build specification from app
        from hive.spec.export import build_specification  # noqa: PLC0415

        spec = build_specification(self.app)

        # Filter private commands if needed
        commands = self._filter_items(spec.commands, config.include_private)

        warnings: list[str] = []

        # Check for missing docstrings
        for name, cmd in commands.items():
            if not cmd.description:
                warnings.append(f"Command '{name}' has no description")

        # Generate output
        if config.output_dir is None:
            # Single file to stdout - concatenate all man pages
            content = self._render_all_pages(commands, config)
            return DocumentationOutput(
                commands_documented=len(commands),
                warnings=warnings,
                content=content,
            )

        # Generate files to output directory
        files_generated = self._generate_files(
            config.output_dir,
            commands,
            config,
        )

        return DocumentationOutput(
            files_generated=files_generated,
            commands_documented=len(commands),
            warnings=warnings,
        )

    def _filter_items(
        self,
        items: dict[str, Any],
        include_private: bool,
    ) -> dict[str, Any]:
        """Filter out private items (underscore-prefixed) if needed.

        Args:
            items: Dictionary of items to filter.
            include_private: Whether to include private items.

        Returns:
            Filtered dictionary.
        """
        if include_private:
            return items
        return {k: v for k, v in items.items() if not k.startswith("_")}

    def _render_all_pages(
        self,
        commands: dict[str, CommandSchema],
        config: DocumentationConfig,
    ) -> str:
        """Render all man pages to a single string.

        Args:
            commands: Command schemas.
            config: Documentation configuration.

        Returns:
            Concatenated man pages.
        """
        parts = []
        date = datetime.now(tz=UTC).strftime("%Y-%m-%d")

        for command in commands.values():
            context = self._build_command_context(command, date, config)
            page = self._render_template("command.1.j2", **context)
            parts.append(page)

        return "\n\n".join(parts)

    def _generate_files(
        self,
        output_dir: Path,
        commands: dict[str, CommandSchema],
        config: DocumentationConfig,
    ) -> list[Path]:
        """Generate man page files to output directory.

        Args:
            output_dir: Directory to write files to.
            commands: Command schemas.
            config: Documentation configuration.

        Returns:
            List of generated file paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        files: list[Path] = []
        date = datetime.now(tz=UTC).strftime("%Y-%m-%d")

        for cmd_name, command in commands.items():
            context = self._build_command_context(command, date, config)
            content = self._render_template("command.1.j2", **context)

            # Man pages use .1 extension for section 1 (user commands)
            file_path = output_dir / f"{cmd_name}.1"
            file_path.write_text(content)
            files.append(file_path)

        return files

    def _build_command_context(
        self,
        command: CommandSchema,
        date: str,
        config: DocumentationConfig,
    ) -> dict[str, Any]:
        """Build template context for a command.

        Args:
            command: Command schema.
            date: Current date string.
            config: Documentation configuration.

        Returns:
            Template context dictionary.
        """
        return {
            "app_name": self.app.name,
            "command": command,
            "date": date,
            "contracts": self._get_contracts(command.name) if config.include_contracts else {},
            "examples": self._get_examples(command) if config.include_examples else None,
        }

    def _get_contracts(self, name: str) -> dict[str, list[str]]:
        """Extract contract information for a command.

        Args:
            name: Command name.

        Returns:
            Dictionary with 'requires' and 'ensures' lists.
        """
        contracts: dict[str, list[str]] = {"requires": [], "ensures": []}

        # Try to get the command registration
        for reg in self.app.registry.list_commands():
            if reg.name == name:
                func = reg.func

                # Check for deal contracts stored as attributes
                deal_pre = getattr(func, "__deal_pre__", None)
                if deal_pre is not None:
                    for pre in deal_pre:
                        deal_msg = getattr(pre, "__deal_message__", None)
                        if deal_msg is not None:
                            contracts["requires"].append(deal_msg)

                deal_post = getattr(func, "__deal_post__", None)
                if deal_post is not None:
                    for post in deal_post:
                        deal_msg = getattr(post, "__deal_message__", None)
                        if deal_msg is not None:
                            contracts["ensures"].append(deal_msg)
                break

        return contracts

    def _get_examples(self, schema: CommandSchema) -> str | None:
        """Extract examples from docstring.

        Args:
            schema: Command schema.

        Returns:
            Examples string or None.
        """
        if not schema.description:
            return None

        # Simple extraction of Examples section from docstring
        description = schema.description
        if "Examples:" in description:
            parts = description.split("Examples:")
            if len(parts) > 1:
                return parts[1].strip()
        elif "Example:" in description:
            parts = description.split("Example:")
            if len(parts) > 1:
                return parts[1].strip()

        return None
