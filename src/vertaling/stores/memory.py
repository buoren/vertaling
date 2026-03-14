"""InMemoryTranslationStore — non-persistent store for testing and development."""

from __future__ import annotations

from vertaling._core.models import TranslationStatus, TranslationUnit


class InMemoryTranslationStore:
    """Translation store that holds state in a plain dict.

    No database required. State is lost when the process exits.
    Use in test suites and local development.
    """

    def __init__(self) -> None:
        self._data: dict[tuple[str, str], TranslationUnit] = {}

    def get(self, code: str, source_locale: str, target_locale: str) -> str | None:
        key = (code, target_locale)
        unit = self._data.get(key)
        if unit is not None and unit.status == TranslationStatus.COMPLETE:
            return unit.translated_text
        return None

    def save(self, unit: TranslationUnit) -> None:
        key = (unit.code, unit.target_locale)
        self._data[key] = unit

    def get_pending(self, target_locales: list[str]) -> list[TranslationUnit]:
        return [
            u
            for u in self._data.values()
            if u.status == TranslationStatus.PENDING and u.target_locale in target_locales
        ]

    def get_failed(self) -> list[TranslationUnit]:
        return [u for u in self._data.values() if u.status == TranslationStatus.FAILED]
