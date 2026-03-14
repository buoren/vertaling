"""InMemoryPipelineStore — non-persistent store for testing and development."""

from __future__ import annotations

from vertaling._core.models import TranslationUnit


class InMemoryPipelineStore:
    """Pipeline store that holds state in a plain dict.

    No database required. State is lost when the process exits.
    Use in test suites and local development.
    """

    def get(self, unit_id: str) -> TranslationUnit | None:
        raise NotImplementedError

    def save(self, unit: TranslationUnit) -> None:
        raise NotImplementedError

    def pending(self) -> list[TranslationUnit]:
        raise NotImplementedError

    def failed(self) -> list[TranslationUnit]:
        raise NotImplementedError
