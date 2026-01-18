"""Command filtering utilities for Hive TUI applications.

Provides fuzzy search filtering for commands used by the command palette.

Note: The CommandPalette widget class was removed in favor of Textual's
built-in command palette (accessible via Ctrl+P). See HiveCommandProvider
in hive.tui.commands for the command provider integration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hive.core.types import CommandRegistration


def filter_commands(
    commands: list[CommandRegistration],
    query: str,
) -> list[CommandRegistration]:
    """Filter commands using fuzzy search.

    Performs case-insensitive fuzzy matching on command names and docstrings.
    Hidden commands are excluded from results.

    Args:
        commands: List of command registrations to filter.
        query: Search query string.

    Returns:
        Filtered and sorted list of matching commands.
    """
    # Exclude hidden commands
    visible_commands = [cmd for cmd in commands if not cmd.hidden]

    if not query:
        return visible_commands

    query_lower = query.lower()
    scored_results: list[tuple[CommandRegistration, int]] = []

    for cmd in visible_commands:
        score = _calculate_match_score(cmd, query_lower)
        if score > 0:
            scored_results.append((cmd, score))

    # Sort by score descending (higher is better)
    scored_results.sort(key=lambda x: x[1], reverse=True)

    return [cmd for cmd, _score in scored_results]


def _calculate_match_score(cmd: CommandRegistration, query_lower: str) -> int:
    """Calculate match score for a command against a query.

    Higher scores indicate better matches.

    Args:
        cmd: Command registration to score.
        query_lower: Lowercase query string.

    Returns:
        Match score (0 = no match, higher = better match).
    """
    name_lower = cmd.name.lower()
    docstring_lower = (cmd.docstring or "").lower()

    score = 0

    # Exact name match (highest priority)
    if name_lower == query_lower:
        score += 1000

    # Name starts with query
    elif name_lower.startswith(query_lower):
        score += 500

    # Name contains query as substring
    elif query_lower in name_lower:
        score += 300

    # Fuzzy match on name
    elif _fuzzy_match(name_lower, query_lower):
        score += 100

    # Docstring contains query
    if query_lower in docstring_lower:
        score += 50

    # Fuzzy match on docstring
    elif _fuzzy_match(docstring_lower, query_lower):
        score += 25

    return score


def _fuzzy_match(text: str, pattern: str) -> bool:
    """Check if pattern characters appear in order within text.

    Args:
        text: Text to search within.
        pattern: Pattern to match (characters in order).

    Returns:
        True if all pattern characters appear in order in text.
    """
    if not pattern:
        return True

    pattern_idx = 0
    for char in text:
        if char == pattern[pattern_idx]:
            pattern_idx += 1
            if pattern_idx == len(pattern):
                return True

    return False
