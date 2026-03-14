"""PipelineStore Protocol — tracks translation job state across runs."""

from __future__ import annotations

from typing import Protocol

from vertaling._core.models import TranslationUnit


class PipelineStore(Protocol):
    """Protocol for persisting pipeline state across runs.

    Enables idempotency: units already translated in a previous run are
    not re-submitted to the backend.
    """

    def get(self, unit_id: str) -> TranslationUnit | None:
        """Return the stored unit by its stable ID, or None if not found."""
        ...

    def save(self, unit: TranslationUnit) -> None:
        """Persist or update a unit's state."""
        ...

    def pending(self) -> list[TranslationUnit]:
        """Return all units with status PENDING."""
        ...

    def failed(self) -> list[TranslationUnit]:
        """Return all units with status FAILED (eligible for retry)."""
        ...
