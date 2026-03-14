"""LibreTranslateBackend — translates via a self-hosted LibreTranslate instance.

Requires: pip install "vertaling[libretranslate]"
"""

from __future__ import annotations

from vertaling._core.models import TranslationUnit


class LibreTranslateBackend:
    """Translation backend using a LibreTranslate HTTP API.

    Args:
        base_url: Base URL of the LibreTranslate instance, e.g.
                  'http://localhost:5000'.
        api_key: Optional API key if the instance requires authentication.
    """

    def __init__(self, base_url: str, api_key: str | None = None) -> None: ...

    async def translate_batch(self, units: list[TranslationUnit]) -> list[TranslationUnit]:
        raise NotImplementedError

    def max_batch_chars(self) -> int:
        raise NotImplementedError

    def supported_locales(self) -> set[str]:
        raise NotImplementedError
