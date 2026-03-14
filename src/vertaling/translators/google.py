"""GoogleTranslator — translates via Google Cloud Translation.

Requires: pip install "vertaling[google]"
"""

from __future__ import annotations

from vertaling._core.models import TranslationUnit


class GoogleTranslator:
    """Translator using Google Cloud Translation API v3.

    Args:
        project_id: GCP project ID.
        location: GCP region, e.g. 'global' or 'us-central1'.
        credentials: Optional explicit credentials; defaults to ADC.
    """

    def __init__(
        self,
        project_id: str,
        location: str = "global",
        credentials: object | None = None,
    ) -> None: ...

    async def translate_batch(self, units: list[TranslationUnit]) -> list[TranslationUnit]:
        raise NotImplementedError

    def max_batch_chars(self) -> int:
        raise NotImplementedError

    def supported_locales(self) -> set[str]:
        raise NotImplementedError
