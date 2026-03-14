"""EchoBackend — returns source text unchanged. For testing."""

from __future__ import annotations

from vertaling._core.models import TranslationUnit
from vertaling.backends.base import TranslationBackend  # noqa: F401


class EchoBackend:
    """Returns source text unchanged. Useful in test suites and dry runs."""

    async def translate_batch(self, units: list[TranslationUnit]) -> list[TranslationUnit]:
        raise NotImplementedError

    def max_batch_chars(self) -> int:
        raise NotImplementedError

    def supported_locales(self) -> set[str]:
        raise NotImplementedError
