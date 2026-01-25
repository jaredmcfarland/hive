"""Base documentation generator with Jinja2 environment setup.

This module provides the abstract base class for documentation generators
and sets up the Jinja2 template environment.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, PackageLoader, Template, select_autoescape

from hive.docs.filters import register_filters
from hive.docs.models import DocumentationConfig, DocumentationOutput

if TYPE_CHECKING:
    from hive.app import App


def create_jinja_environment(template_subdir: str) -> Environment:
    """Create and configure a Jinja2 environment for documentation templates.

    Sets up the environment with:
    - PackageLoader pointing to hive.docs.templates
    - Autoescape disabled (markdown/troff output)
    - Custom filters for constraint formatting

    Args:
        template_subdir: Subdirectory within templates (e.g., "markdown", "manpage").

    Returns:
        Configured Jinja2 Environment.

    Example:
        >>> env = create_jinja_environment("markdown")
        >>> template = env.get_template("command.md.j2")
    """
    # Use PackageLoader to locate templates within the package
    loader = PackageLoader(
        package_name="hive.docs.templates",
        package_path=template_subdir,
    )

    env = Environment(
        loader=loader,
        autoescape=select_autoescape(
            enabled_extensions=(),  # Disable autoescape for markdown/troff
            default_for_string=False,
            default=False,
        ),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    # Register custom filters
    register_filters(env)

    return env


def get_templates_path() -> Path:
    """Get the path to the templates directory.

    Returns:
        Path to the templates directory within the package.
    """
    files = resources.files("hive.docs.templates")
    # Use as_file context manager to get actual path
    with resources.as_file(files) as path:
        return path


class BaseDocumentationGenerator(ABC):
    """Abstract base class for documentation generators.

    Provides common functionality for generating documentation from
    a Hive application specification.

    Subclasses must implement:
    - generate(): Produce documentation in the specific format.

    Attributes:
        app: The Hive application to document.
        env: Jinja2 environment for template rendering.

    Example:
        >>> class MarkdownGenerator(BaseDocumentationGenerator):
        ...     def __init__(self, app: App) -> None:
        ...         super().__init__(app, "markdown")
        ...
        ...     def generate(self, config: DocumentationConfig) -> DocumentationOutput:
        ...         # Implementation here
        ...         ...
    """

    def __init__(self, app: App, template_subdir: str) -> None:
        """Initialize the documentation generator.

        Args:
            app: Hive application to document.
            template_subdir: Template subdirectory (e.g., "markdown").
        """
        self.app = app
        self.env = create_jinja_environment(template_subdir)

    @abstractmethod
    def generate(self, config: DocumentationConfig) -> DocumentationOutput:
        """Generate documentation for the application.

        Args:
            config: Documentation configuration.

        Returns:
            DocumentationOutput with generation results.
        """
        ...

    def _get_template(self, name: str) -> Template:
        """Load a template by name.

        Args:
            name: Template filename (e.g., "command.md.j2").

        Returns:
            Loaded Jinja2 template.
        """
        return self.env.get_template(name)

    def _render_template(self, name: str, **context: object) -> str:
        """Render a template with the given context.

        Args:
            name: Template filename.
            **context: Template variables.

        Returns:
            Rendered template string.
        """
        template = self._get_template(name)
        return template.render(**context)
