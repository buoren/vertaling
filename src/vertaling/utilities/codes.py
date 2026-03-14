"""Translation code builder — shared utility for constructing translation codes."""

from __future__ import annotations


def make_translation_code(
    table: str,
    column: str,
    record_id: str,
    json_path: str | None = None,
) -> str:
    """Build a translation code for a content field.

    Plain field::

        make_translation_code("conventions", "name", "conv-001")
        # → "conventions.name.conv-001"

    JSON sub-path::

        make_translation_code("conventions", "settings", "conv-001", "maps.0.name")
        # → "conventions.settings.conv-001;maps.0.name"

    Args:
        table: The database table name.
        column: The column name.
        record_id: The record's unique identifier (as string).
        json_path: Optional dotted path within a JSON column.

    Returns:
        A translation code string.
    """
    code = f"{table}.{column}.{record_id}"
    if json_path is not None:
        code = f"{code};{json_path}"
    return code
