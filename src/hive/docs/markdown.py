"""Markdown documentation generator.

This module implements the MarkdownGenerator class for generating
markdown documentation from Hive application specifications.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, override

from hive.docs.base import BaseDocumentationGenerator
from hive.docs.models import DocumentationConfig, DocumentationOutput

if TYPE_CHECKING:
    from hive.app import App
    from hive.spec.models import CommandSchema, EntitySchema, QuerySchema

# Threshold for splitting items into separate files
MIN_ITEMS_FOR_SPLIT = 5


class MarkdownGenerator(BaseDocumentationGenerator):
    """Generate markdown documentation from a Hive application.

    Creates markdown documentation including:
    - Index with table of contents
    - Command documentation with parameters and contracts
    - Query documentation with caching info
    - Entity documentation with fields and relationships

    Attributes:
        app: The Hive application to document.
        env: Jinja2 environment with markdown templates.

    Example:
        >>> from hive.docs import MarkdownGenerator, DocumentationConfig
        >>> from pathlib import Path
        >>>
        >>> generator = MarkdownGenerator(app)
        >>> config = DocumentationConfig(
        ...     format="markdown",
        ...     output_dir=Path("docs/"),
        ... )
        >>> result = generator.generate(config)
        >>> print(f"Generated {result.total_documented} items")
    """

    def __init__(self, app: App) -> None:
        """Initialize the markdown generator.

        Args:
            app: Hive application to document.
        """
        super().__init__(app, "markdown")

    @override
    def generate(self, config: DocumentationConfig) -> DocumentationOutput:
        """Generate markdown documentation.

        Args:
            config: Documentation configuration.

        Returns:
            DocumentationOutput with generation results.
        """
        # Build specification from app
        from hive.spec.export import build_specification  # noqa: PLC0415

        spec = build_specification(self.app)

        # Filter private commands/queries if needed
        commands = self._filter_items(spec.commands, config.include_private)
        queries = self._filter_items(spec.queries, config.include_private)
        entities = spec.entities  # Entities are always included

        warnings: list[str] = []

        # Check for missing docstrings
        for name, cmd in commands.items():
            if not cmd.description:
                warnings.append(f"Command '{name}' has no description")
        for name, query in queries.items():
            if not query.description:
                warnings.append(f"Query '{name}' has no description")
        for name, entity in entities.items():
            if not entity.description:
                warnings.append(f"Entity '{name}' has no description")

        # Build context for templates
        context = self._build_context(
            commands=commands,
            queries=queries,
            entities=entities,
            config=config,
        )

        # Generate output
        if config.output_dir is None:
            # Single file to stdout
            content = self._render_single_document(context)
            return DocumentationOutput(
                commands_documented=len(commands),
                queries_documented=len(queries),
                entities_documented=len(entities),
                warnings=warnings,
                content=content,
            )

        # Generate files to output directory (output_dir is guaranteed non-None here)
        files_generated = self._generate_files(
            config.output_dir,
            context,
            commands,
            queries,
            entities,
        )

        return DocumentationOutput(
            files_generated=files_generated,
            commands_documented=len(commands),
            queries_documented=len(queries),
            entities_documented=len(entities),
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

    def _build_context(
        self,
        *,
        commands: dict[str, CommandSchema],
        queries: dict[str, QuerySchema],
        entities: dict[str, EntitySchema],
        config: DocumentationConfig,
    ) -> dict[str, Any]:
        """Build the template context.

        Args:
            commands: Command schemas.
            queries: Query schemas.
            entities: Entity schemas.
            config: Documentation configuration.

        Returns:
            Template context dictionary.
        """
        return {
            "app_name": self.app.name,
            "app_description": getattr(self.app, "description", None),
            "version": getattr(self.app, "version", "0.1.0"),
            "generated_at": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "commands": commands,
            "queries": queries,
            "entities": entities,
            "include_examples": config.include_examples,
            "include_contracts": config.include_contracts,
        }

    def _render_single_document(
        self,
        context: dict[str, Any],
    ) -> str:
        """Render a single combined document to stdout.

        Args:
            context: Template context (contains commands, queries, entities).

        Returns:
            Rendered markdown string.
        """
        # Index template includes all commands, queries, entities
        return self._render_template("index.md.j2", **context)

    def _generate_files(
        self,
        output_dir: Path,
        context: dict[str, Any],
        commands: dict[str, CommandSchema],
        queries: dict[str, QuerySchema],
        entities: dict[str, EntitySchema],
    ) -> list[Path]:
        """Generate documentation files to output directory.

        Args:
            output_dir: Directory to write files to.
            context: Template context.
            commands: Command schemas.
            queries: Query schemas.
            entities: Entity schemas.

        Returns:
            List of generated file paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        files: list[Path] = []

        # Generate index.md
        index_content = self._render_template("index.md.j2", **context)
        index_path = output_dir / "index.md"
        index_path.write_text(index_content)
        files.append(index_path)

        # Generate command files if there are many
        if len(commands) > MIN_ITEMS_FOR_SPLIT:
            commands_dir = output_dir / "commands"
            commands_dir.mkdir(exist_ok=True)
            for name, command in commands.items():
                cmd_context = {
                    **context,
                    "command": command,
                    "contracts": self._get_contracts(name),
                    "examples": self._get_examples(command),
                }
                content = self._render_template("command.md.j2", **cmd_context)
                cmd_path = commands_dir / f"{name}.md"
                cmd_path.write_text(content)
                files.append(cmd_path)

        # Generate query files if there are many
        if len(queries) > MIN_ITEMS_FOR_SPLIT:
            queries_dir = output_dir / "queries"
            queries_dir.mkdir(exist_ok=True)
            for name, query in queries.items():
                query_context = {
                    **context,
                    "query": query,
                    "contracts": self._get_contracts(name),
                    "examples": self._get_examples(query),
                }
                content = self._render_template("query.md.j2", **query_context)
                query_path = queries_dir / f"{name}.md"
                query_path.write_text(content)
                files.append(query_path)

        # Generate entity files if there are many
        if len(entities) > MIN_ITEMS_FOR_SPLIT:
            entities_dir = output_dir / "entities"
            entities_dir.mkdir(exist_ok=True)
            for name, entity in entities.items():
                entity_context = {
                    **context,
                    "entity": entity,
                    "invariants": self._get_invariants(name),
                }
                content = self._render_template("entity.md.j2", **entity_context)
                entity_path = entities_dir / f"{name}.md"
                entity_path.write_text(content)
                files.append(entity_path)

        return files

    def _get_contracts(self, name: str) -> dict[str, list[str]]:
        """Extract contract information for a command or query.

        Args:
            name: Command or query name.

        Returns:
            Dictionary with 'requires' and 'ensures' lists.
        """
        contracts: dict[str, list[str]] = {"requires": [], "ensures": []}

        # Try to get the command or query registration
        cmd_reg = None
        query_reg = None

        for reg in self.app.registry.list_commands():
            if reg.name == name:
                cmd_reg = reg
                break

        if cmd_reg is None:
            for reg in self.app.registry.list_queries():
                if reg.name == name:
                    query_reg = reg
                    break

        target = cmd_reg or query_reg
        if target is None:
            return contracts

        # Extract contracts from the function
        func = target.func

        # Check for deal contracts stored as attributes
        # Use getattr to access dynamic attributes set by deal
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

        return contracts

    def _get_examples(self, schema: CommandSchema | QuerySchema) -> str | None:
        """Extract examples from docstring.

        Args:
            schema: Command or query schema.

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

    def _get_invariants(self, name: str) -> list[str]:
        """Extract invariants for an entity.

        Args:
            name: Entity name.

        Returns:
            List of invariant descriptions.
        """
        invariants: list[str] = []

        # Try to get the entity registration
        for reg in self.app.registry.list_entities():
            if reg.name == name:
                # Check for deal invariants - use reg.cls (entity class)
                entity_cls = reg.cls
                deal_inv = getattr(entity_cls, "__deal_inv__", None)
                if deal_inv is not None:
                    for inv in deal_inv:
                        deal_msg = getattr(inv, "__deal_message__", None)
                        if deal_msg is not None:
                            invariants.append(deal_msg)
                break

        return invariants
