"""Hive Documentation Generation.

Generate documentation in multiple formats from Hive application specifications.

Supported formats:
- Markdown: Human-readable documentation with full constraint and contract details
- Man pages: Unix manual pages in troff format

Example:
    from hive.docs import MarkdownGenerator, DocumentationConfig

    # Generate markdown documentation
    config = DocumentationConfig(format="markdown", output_dir=Path("docs/"))
    generator = MarkdownGenerator(app)
    result = generator.generate(config)
    print(f"Generated {result.files_generated} files")

CLI Usage:
    hive docs generate --format markdown --output docs/
    hive docs generate --format manpage --output man/
"""

from hive.docs.manpage import ManPageGenerator as ManPageGenerator
from hive.docs.markdown import MarkdownGenerator as MarkdownGenerator
from hive.docs.models import DocumentationConfig as DocumentationConfig
from hive.docs.models import DocumentationOutput as DocumentationOutput

__all__ = [
    "DocumentationConfig",
    "DocumentationOutput",
    "ManPageGenerator",
    "MarkdownGenerator",
]
