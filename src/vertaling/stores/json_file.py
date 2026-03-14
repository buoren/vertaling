"""JsonFileStore — read-only translation store backed by per-locale JSON files."""

from __future__ import annotations

import json
from pathlib import Path

from vertaling._core.models import TranslationUnit


class JsonFileStore:
    """Read-only store that reads ``{locale}.json`` files from a directory.

    Each file contains nested JSON that is flattened to dot-notation keys.
    For example, ``{"app": {"title": "Hello"}}`` produces key ``app.title``.

    Naturally read-only — use with ``read_only=["json"]`` in the pipeline
    so that misses are routed to a writable store or review store.

    Args:
        directory: Path to the directory containing ``{locale}.json`` files.
        source_locale: Default source locale (used by ``keys()``).
    """

    def __init__(
        self,
        directory: str | Path,
        source_locale: str = "en",
    ) -> None:
        self._directory = Path(directory)
        self._source_locale = source_locale
        self._cache: dict[str, dict[str, str]] | None = None

    def _load(self) -> dict[str, dict[str, str]]:
        """Lazy-load and flatten all JSON files."""
        if self._cache is not None:
            return self._cache
        self._cache = {}
        if not self._directory.is_dir():
            return self._cache
        for path in sorted(self._directory.glob("*.json")):
            locale = path.stem
            with open(path, encoding="utf-8") as f:
                nested = json.load(f)
            self._cache[locale] = _flatten(nested)
        return self._cache

    def get(self, code: str, source_locale: str, target_locale: str) -> str | None:
        """Look up a flattened key for the given locale."""
        data = self._load()
        locale_data = data.get(target_locale)
        if locale_data is None:
            return None
        return locale_data.get(code)

    def save(self, unit: TranslationUnit) -> None:
        """No-op: JSON file store is read-only."""

    def get_pending(self, target_locales: list[str]) -> list[TranslationUnit]:
        """JSON files have no pending concept."""
        return []

    def get_failed(self) -> list[TranslationUnit]:
        """JSON files have no failed concept."""
        return []

    def reload(self) -> None:
        """Force a reload of all JSON files on next access."""
        self._cache = None

    def keys(self, locale: str | None = None) -> list[str]:
        """Return all translation keys for a locale (defaults to source_locale)."""
        data = self._load()
        target = locale or self._source_locale
        return list(data.get(target, {}).keys())

    def locales(self) -> list[str]:
        """Return all loaded locale codes (stems of the JSON filenames)."""
        return list(self._load().keys())


def _flatten(nested: dict[str, object], prefix: str = "") -> dict[str, str]:
    """Recursively flatten a nested dict to dot-notation keys."""
    result: dict[str, str] = {}
    for key, value in nested.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(_flatten(value, full_key))
        else:
            result[full_key] = str(value)
    return result
