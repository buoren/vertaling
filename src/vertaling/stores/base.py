"""TranslationStore Protocol — the interface apps implement to persist translations."""

from __future__ import annotations

from typing import Protocol

from vertaling._core.models import TranslationUnit


class TranslationStore(Protocol):
    """Protocol for looking up and persisting translations.

    The application owns the database schema and implements this protocol.
    Vertaling only interacts with translations through this interface.
    """

    def get(self, code: str, source_locale: str, target_locale: str) -> str | None:
        """Look up a translated string. Return None if not found."""
        ...

    def save(self, unit: TranslationUnit) -> None:
        """Persist a completed translation."""
        ...

    def get_pending(self, target_locales: list[str]) -> list[TranslationUnit]:
        """Return all units needing translation (for batch runs)."""
        ...

    def get_failed(self) -> list[TranslationUnit]:
        """Return failed units eligible for retry."""
        ...
