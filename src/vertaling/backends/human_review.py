"""HumanReviewBackend — marks units for human review instead of auto-translating."""

from __future__ import annotations

from vertaling._core.models import TranslationUnit


class HumanReviewBackend:
    """Marks units as IN_PROGRESS and writes them to a review queue.

    Does not perform any machine translation. Use this for content that
    requires human translation or review before publishing.

    The review queue is pluggable — pass any callable that accepts a
    list of TranslationUnits.
    """

    def __init__(self, enqueue: object) -> None: ...

    async def translate_batch(self, units: list[TranslationUnit]) -> list[TranslationUnit]:
        raise NotImplementedError

    def max_batch_chars(self) -> int:
        raise NotImplementedError

    def supported_locales(self) -> set[str]:
        raise NotImplementedError
