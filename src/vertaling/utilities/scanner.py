"""ContentScanner — discover missing translations for database content."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from vertaling._core.models import TranslationUnit
from vertaling.stores.base import TranslationStore
from vertaling.utilities.codes import make_translation_code
from vertaling.utilities.json_path import resolve_wildcard_paths

# A field spec is either a plain column name or (column, json_path_pattern).
FieldSpec = str | tuple[str, str]


@dataclass
class ScanTarget:
    """Describes a set of records to scan for missing translations."""

    table: str
    """Database table name (used in translation codes)."""

    fields: list[FieldSpec]
    """Fields to check — plain column names or ``(column, "json.*.path")`` tuples."""

    records: Iterable[Any]
    """The records to scan — dicts or objects with attribute access."""

    id_attr: str = "id"
    """Attribute/key name for the record's unique identifier."""

    source_locale: str = "en"
    """Source locale of the content."""


@dataclass
class ScanResult:
    """Result of a content scan."""

    missing: list[TranslationUnit] = field(default_factory=list)
    """Translation units that need to be translated."""

    total_checked: int = 0
    """Total number of field×locale combinations checked."""

    already_translated: int = 0
    """Number of combinations that already have translations."""


class ContentScanner:
    """Scans database content for missing translations.

    Produces ``TranslationUnit`` lists ready to feed into
    ``pipeline.translate_batch()``.

    Args:
        store: Translation store to check for existing translations.
        target_locales: Locales to check translations for.
    """

    def __init__(self, store: TranslationStore, target_locales: list[str]) -> None:
        self.store = store
        self.target_locales = target_locales

    def scan(self, targets: list[ScanTarget]) -> ScanResult:
        """Scan targets for missing translations.

        Args:
            targets: List of scan targets describing which records/fields to check.

        Returns:
            ScanResult with missing translation units and counts.
        """
        result = ScanResult()

        for target in targets:
            for record in target.records:
                record_id = str(_get_value(record, target.id_attr))

                for spec in target.fields:
                    if isinstance(spec, str):
                        self._check_plain_field(record, target, spec, record_id, result)
                    else:
                        self._check_json_field(record, target, spec, record_id, result)

        return result

    def _check_plain_field(
        self,
        record: Any,
        target: ScanTarget,
        field_name: str,
        record_id: str,
        result: ScanResult,
    ) -> None:
        source_value = _get_value(record, field_name)
        if not isinstance(source_value, str):
            return

        code = make_translation_code(target.table, field_name, record_id)

        for locale in self.target_locales:
            result.total_checked += 1
            existing = self.store.get(code, target.source_locale, locale)
            if existing is not None:
                result.already_translated += 1
            else:
                result.missing.append(
                    TranslationUnit(
                        code=code,
                        source_locale=target.source_locale,
                        target_locale=locale,
                        source_text=source_value,
                    )
                )

    def _check_json_field(
        self,
        record: Any,
        target: ScanTarget,
        spec: tuple[str, str],
        record_id: str,
        result: ScanResult,
    ) -> None:
        column_name, pattern = spec
        json_data = _get_value(record, column_name)
        if json_data is None:
            return

        resolved = resolve_wildcard_paths(json_data, pattern)

        for concrete_path, source_value in resolved:
            if not isinstance(source_value, str):
                continue

            code = make_translation_code(
                target.table, column_name, record_id, json_path=concrete_path
            )

            for locale in self.target_locales:
                result.total_checked += 1
                existing = self.store.get(code, target.source_locale, locale)
                if existing is not None:
                    result.already_translated += 1
                else:
                    result.missing.append(
                        TranslationUnit(
                            code=code,
                            source_locale=target.source_locale,
                            target_locale=locale,
                            source_text=source_value,
                        )
                    )


def cleanup_orphans(store: TranslationStore, table: str, valid_ids: set[str]) -> list[str]:
    """Find and delete translations referencing deleted records.

    Requires the store to support both ``keys()`` and ``delete(code)`` methods.
    If either is missing, returns an empty list without error.

    Args:
        store: Translation store (must support ``keys()`` and ``delete()``).
        table: Table name prefix to filter codes by.
        valid_ids: Set of IDs that still exist in the database.

    Returns:
        List of orphaned translation codes that were deleted.
    """
    delete_fn = getattr(store, "delete", None)
    if delete_fn is None:
        return []

    orphans = find_orphans(store, table, valid_ids)
    for code in orphans:
        delete_fn(code)

    return orphans


def find_orphans(store: TranslationStore, table: str, valid_ids: set[str]) -> list[str]:
    """Find translation codes referencing deleted records.

    Args:
        store: Translation store (must support ``keys()``).
        table: Table name prefix to filter codes by.
        valid_ids: Set of IDs that still exist in the database.

    Returns:
        List of orphaned translation codes.

    Raises:
        TypeError: If the store does not support ``keys()``.
    """
    keys_fn = getattr(store, "keys", None)
    if keys_fn is None:
        return []

    prefix = f"{table}."
    orphans: list[str] = []

    # keys() may require a locale argument — try without first
    try:
        all_keys: list[str] = keys_fn()
    except TypeError:
        return []

    for key in all_keys:
        if not key.startswith(prefix):
            continue

        # Code format: "table.column.id" or "table.column.id;json.path"
        rest = key[len(prefix) :]
        parts = rest.split(".", 1)
        if len(parts) < 2:
            continue

        # parts[1] is "id" or "id;json.path"
        record_id = parts[1].split(";", 1)[0]

        if record_id not in valid_ids:
            orphans.append(key)

    return orphans


def _get_value(record: Any, attr: str) -> Any:
    """Get a value from a record — supports both dicts and objects."""
    if isinstance(record, dict):
        return record.get(attr)
    return getattr(record, attr, None)
