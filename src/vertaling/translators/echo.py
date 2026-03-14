"""EchoTranslator — returns source text unchanged. For testing."""

from __future__ import annotations

from vertaling._core.models import TranslationStatus, TranslationUnit


class EchoTranslator:
    """Returns source text as translated text. Useful in test suites."""

    async def translate_batch(self, units: list[TranslationUnit]) -> list[TranslationUnit]:
        for unit in units:
            unit.translated_text = unit.source_text
            unit.status = TranslationStatus.COMPLETE
        return units

    def max_batch_chars(self) -> int:
        return 1_000_000

    def supported_locales(self) -> set[str]:
        return set()
