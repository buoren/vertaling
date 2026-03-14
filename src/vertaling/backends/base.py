"""TranslationBackend Protocol — the interface all backends must implement."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from vertaling._core.models import TranslationUnit


@runtime_checkable
class TranslationBackend(Protocol):
    """Protocol that all translation backends must satisfy.

    Backends are responsible for taking a list of TranslationUnits with
    source_text populated and returning them with translated_text populated.
    """

    async def translate_batch(
        self,
        units: list[TranslationUnit],
    ) -> list[TranslationUnit]:
        """Translate a batch of units.

        Must preserve order. Units that fail translation should have their
        status set to FAILED and error populated, not raise an exception.
        """
        ...

    def max_batch_chars(self) -> int:
        """Maximum total characters this backend accepts in a single batch call."""
        ...

    def supported_locales(self) -> set[str]:
        """BCP-47 locale codes this backend can translate into.

        Return an empty set to signal 'unknown / accepts anything'.
        """
        ...
