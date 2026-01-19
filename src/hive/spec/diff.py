"""Specification diff functionality.

This module provides functions for comparing two specifications and
detecting breaking changes using DeepDiff.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from deepdiff import DeepDiff

from hive.spec.models import DiffItem, SpecificationDiff


def diff_specifications(  # noqa: C901, PLR0912
    spec1: dict[str, Any],
    spec2: dict[str, Any],
) -> SpecificationDiff:
    """Compare two specifications and identify differences.

    Uses DeepDiff to find all changes between specs, then classifies
    them as breaking or non-breaking based on semantic rules.

    Args:
        spec1: First specification dict (older version).
        spec2: Second specification dict (newer version).

    Returns:
        SpecificationDiff containing all changes and breaking changes.
    """
    # Get versions from metadata
    v1_version = spec1.get("metadata", {}).get("version", "unknown")
    v2_version = spec2.get("metadata", {}).get("version", "unknown")

    # Compute diff using DeepDiff
    diff = DeepDiff(spec1, spec2, ignore_order=True, verbose_level=2)

    # Convert DeepDiff results to DiffItems
    changes: list[DiffItem] = []
    breaking_changes: list[DiffItem] = []

    # Handle added items
    for path in diff.get("dictionary_item_added", []):
        item = DiffItem(
            path=_normalize_path(path),
            change_type="added",
            new_value=_get_value_at_path(spec2, path),
            breaking=False,  # Adding is not breaking
        )
        changes.append(item)

    # Handle removed items
    for path in diff.get("dictionary_item_removed", []):
        old_value = _get_value_at_path(spec1, path)
        is_breaking = _is_breaking_removal(path, old_value)
        item = DiffItem(
            path=_normalize_path(path),
            change_type="removed",
            old_value=old_value,
            breaking=is_breaking,
        )
        changes.append(item)
        if is_breaking:
            breaking_changes.append(item)

    # Handle changed values
    for path, change_info in diff.get("values_changed", {}).items():
        old_val = change_info.get("old_value")
        new_val = change_info.get("new_value")

        # Check if this is a top-level dict (commands/queries/entities) that changed
        # entirely due to having different keys
        normalized_path = _normalize_path(path)
        if (
            normalized_path in ("commands", "queries", "entities")
            and isinstance(old_val, dict)
            and isinstance(new_val, dict)
        ):
            # Decompose into individual additions and removals
            old_keys = set(old_val.keys())
            new_keys = set(new_val.keys())

            for removed_key in old_keys - new_keys:
                item = DiffItem(
                    path=f"{normalized_path}.{removed_key}",
                    change_type="removed",
                    old_value=old_val[removed_key],
                    breaking=True,  # Removing commands/queries/entities is breaking
                )
                changes.append(item)
                breaking_changes.append(item)

            for added_key in new_keys - old_keys:
                item = DiffItem(
                    path=f"{normalized_path}.{added_key}",
                    change_type="added",
                    new_value=new_val[added_key],
                    breaking=False,  # Adding is not breaking
                )
                changes.append(item)

            # Handle modified keys (same key, different value)
            for common_key in old_keys & new_keys:
                if old_val[common_key] != new_val[common_key]:
                    item = DiffItem(
                        path=f"{normalized_path}.{common_key}",
                        change_type="modified",
                        old_value=old_val[common_key],
                        new_value=new_val[common_key],
                        breaking=False,  # Content changes may or may not be breaking
                    )
                    changes.append(item)
        else:
            is_breaking = _is_breaking_change(path, old_val, new_val)

            item = DiffItem(
                path=normalized_path,
                change_type="modified",
                old_value=old_val,
                new_value=new_val,
                breaking=is_breaking,
            )
            changes.append(item)
            if is_breaking:
                breaking_changes.append(item)

    # Handle type changes
    for path, change_info in diff.get("type_changes", {}).items():
        old_val = change_info.get("old_value")
        new_val = change_info.get("new_value")
        is_breaking = _is_breaking_type_change(path)

        item = DiffItem(
            path=_normalize_path(path),
            change_type="modified",
            old_value=old_val,
            new_value=new_val,
            breaking=is_breaking,
        )
        changes.append(item)
        if is_breaking:
            breaking_changes.append(item)

    # Handle iterable item additions
    for path in diff.get("iterable_item_added", {}):
        item = DiffItem(
            path=_normalize_path(path),
            change_type="added",
            new_value=diff["iterable_item_added"][path],
            breaking=False,
        )
        changes.append(item)

    # Handle iterable item removals
    for path in diff.get("iterable_item_removed", {}):
        old_value = diff["iterable_item_removed"][path]
        is_breaking = _is_breaking_removal(path, old_value)
        item = DiffItem(
            path=_normalize_path(path),
            change_type="removed",
            old_value=old_value,
            breaking=is_breaking,
        )
        changes.append(item)
        if is_breaking:
            breaking_changes.append(item)

    return SpecificationDiff(
        v1_version=v1_version,
        v2_version=v2_version,
        compared_at=datetime.now(tz=UTC),
        changes=changes,
        breaking_changes=breaking_changes,
    )


def _normalize_path(path: str) -> str:
    """Normalize DeepDiff path to readable format.

    DeepDiff uses format like "root['commands']['cmd1']"
    We convert to "commands.cmd1"
    """
    # Remove 'root' prefix
    result = path.replace("root", "").strip("[]'\"")
    # Replace bracket notation with dots
    result = result.replace("']['", ".")
    result = result.replace("['", ".").replace("']", "")
    return result.strip(".")


def _get_value_at_path(data: dict[str, Any], path: str) -> Any:
    """Get value at a DeepDiff path."""
    # Parse the path and navigate to value
    # Path format: root['key1']['key2']
    current = data
    try:
        parts = path.replace("root", "").strip("[]'\"").split("']['")
        for part in parts:
            cleaned = part.strip("[]'\"")
            if cleaned:
                if isinstance(current, dict):
                    current = current[cleaned]
                elif isinstance(current, list) and cleaned.isdigit():
                    current = current[int(cleaned)]
    except (KeyError, IndexError, TypeError):
        return None
    return current


def _is_breaking_removal(path: str, old_value: Any = None) -> bool:
    """Determine if a removal is a breaking change.

    Breaking removals:
    - Removing a command
    - Removing a query
    - Removing an entity
    - Removing a required parameter (optional parameters can be removed safely)

    Args:
        path: The path to the removed item.
        old_value: The value that was removed (used to check if parameter was required).
    """
    normalized = _normalize_path(path)

    # Number of parts for a top-level removal (e.g., commands.<name>)
    top_level_parts = 2

    # Removing a command is breaking
    if normalized.startswith("commands."):
        # Check if this is the command itself or a sub-element
        parts = normalized.split(".")
        if len(parts) == top_level_parts:  # commands.<name> - command removed
            return True
        # Removing a parameter is only breaking if it was required
        if "parameters" in normalized:
            # Check if the removed parameter was required
            # Default to True (breaking) if we can't determine
            if isinstance(old_value, dict):
                return old_value.get("required", True)
            return True

    # Removing a query is breaking
    if normalized.startswith("queries."):
        parts = normalized.split(".")
        if len(parts) == top_level_parts:  # queries.<name> - query removed
            return True

    # Removing an entity is breaking
    if normalized.startswith("entities."):
        parts = normalized.split(".")
        if len(parts) == top_level_parts:  # entities.<name> - entity removed
            return True

    return False


def _is_breaking_change(path: str, old_value: Any, new_value: Any) -> bool:
    """Determine if a value change is breaking.

    Breaking changes:
    - Parameter type changed
    - Required changed from false to true
    - Constraint made more restrictive
    """
    normalized = _normalize_path(path)

    # Parameter type change is breaking
    if "parameters" in normalized and normalized.endswith(".type"):
        return True

    # Required changed to true is breaking
    if normalized.endswith(".required") and old_value is False and new_value is True:
        return True

    # Minimum increased is breaking (constraint more restrictive)
    if (
        normalized.endswith(".minimum")
        and old_value is not None
        and new_value is not None
        and new_value > old_value
    ):
        return True

    # Maximum decreased is breaking (constraint more restrictive)
    return (
        normalized.endswith(".maximum")
        and old_value is not None
        and new_value is not None
        and new_value < old_value
    )


def _is_breaking_type_change(path: str) -> bool:
    """Determine if a type change is breaking."""
    normalized = _normalize_path(path)

    # Type changes in parameters are breaking
    if "parameters" in normalized:
        return True

    # Type changes in return values are potentially breaking
    return "return_type" in normalized
