"""JSON path utilities for navigating and mutating nested dict/list structures."""

from __future__ import annotations

from typing import Any


def get_at_path(obj: Any, path: str) -> Any:
    """Navigate a nested dict/list structure by dotted path.

    Args:
        obj: The root object (dict or list).
        path: Dotted path string, e.g. ``"maps.0.name"``.

    Returns:
        The value at the path, or ``None`` if any segment is missing.
    """
    parts = path.split(".")
    return _get(obj, parts)


def set_at_path(obj: Any, path: str, value: Any) -> None:
    """Set a value at a dotted path in a nested dict/list structure, in-place.

    Args:
        obj: The root object (dict or list).
        path: Dotted path string, e.g. ``"maps.0.name"``.
        value: The value to set.

    No-op if the parent container doesn't exist.
    """
    parts = path.split(".")
    _set(obj, parts, value)


def resolve_wildcard_paths(obj: Any, pattern: str) -> list[tuple[str, Any]]:
    """Expand ``*`` wildcards in a path pattern into concrete (path, value) pairs.

    Args:
        obj: The root object (dict or list).
        pattern: Dotted path with ``*`` as list wildcard,
                 e.g. ``"maps.*.name"``.

    Returns:
        List of ``(concrete_path, value)`` tuples.
    """
    parts = pattern.split(".")
    results: list[tuple[str, Any]] = []
    _resolve(obj, parts, [], results)
    return results


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get(obj: Any, parts: list[str]) -> Any:
    current = obj
    for part in parts:
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current


def _set(obj: Any, parts: list[str], value: Any) -> None:
    current = obj
    for part in parts[:-1]:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return
        else:
            return
        if current is None:
            return

    last = parts[-1]
    if isinstance(current, dict):
        current[last] = value
    elif isinstance(current, list):
        try:
            current[int(last)] = value
        except (ValueError, IndexError):
            return


def _resolve(
    obj: Any,
    parts: list[str],
    prefix: list[str],
    results: list[tuple[str, Any]],
) -> None:
    if not parts:
        results.append((".".join(prefix), obj))
        return

    head, rest = parts[0], parts[1:]

    if head == "*":
        if isinstance(obj, list):
            for i, item in enumerate(obj):
                _resolve(item, rest, [*prefix, str(i)], results)
        # *  on non-list is a no-op (no expansion)
        return

    if isinstance(obj, dict):
        child = obj.get(head)
        if child is not None:
            _resolve(child, rest, [*prefix, head], results)
    elif isinstance(obj, list):
        try:
            child = obj[int(head)]
        except (ValueError, IndexError):
            return
        _resolve(child, rest, [*prefix, head], results)
