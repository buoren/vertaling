"""PseudoTranslator — replaces all text with a fixed marker string.

Use this translator during development to visually confirm that every
piece of user-facing text is being pulled through the translation system.
Any string still showing its original English after running with this
translator has not been wired up for translation.
"""

from __future__ import annotations

from vertaling._core.models import TranslationStatus, TranslationUnit


class PseudoTranslator:
    """Replaces every source string with a fixed marker (default ``"xx"``).

    Useful for visual QA: run your app with this translator and scan the
    UI for anything that is *not* ``"xx"``. Those spots are untranslated.

    Args:
        marker: The replacement string. Defaults to ``"xx"``.
    """

    def __init__(self, marker: str = "xx") -> None:
        self.marker = marker

    async def translate_batch(self, units: list[TranslationUnit]) -> list[TranslationUnit]:
        for unit in units:
            unit.translated_text = self.marker
            unit.status = TranslationStatus.COMPLETE
        return units

    def max_batch_chars(self) -> int:
        return 1_000_000

    def supported_locales(self) -> set[str]:
        return set()
