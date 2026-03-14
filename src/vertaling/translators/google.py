"""GoogleTranslator — translates via Google Cloud Translation API v3.

Requires: pip install "vertaling[google]"
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from vertaling._core.models import TranslationStatus, TranslationUnit
from vertaling.utilities.locale import normalize_for_api

if TYPE_CHECKING:
    from google.cloud.translate_v3 import TranslationServiceClient

logger = logging.getLogger(__name__)


class GoogleTranslator:
    """Translator using Google Cloud Translation API v3.

    Groups units by target locale for efficient batching and runs the
    synchronous Google client in an executor to stay async-friendly.

    Args:
        project_id: GCP project ID.
        location: GCP region, e.g. ``'global'`` or ``'us-central1'``.
        credentials: Optional explicit credentials object; defaults to ADC.
    """

    def __init__(
        self,
        project_id: str,
        location: str = "global",
        credentials: Any | None = None,
    ) -> None:
        self._project_id = project_id
        self._location = location
        self._parent = f"projects/{project_id}/locations/{location}"
        self._credentials = credentials
        self._client: TranslationServiceClient | None = None

    def _get_client(self) -> TranslationServiceClient:
        """Lazy-init the Google Cloud client."""
        if self._client is None:
            from google.cloud.translate_v3 import TranslationServiceClient as _Client

            if self._credentials is not None:
                self._client = _Client(credentials=self._credentials)
            else:
                self._client = _Client()
        return self._client

    async def translate_batch(
        self,
        units: list[TranslationUnit],
    ) -> list[TranslationUnit]:
        """Translate units, grouping by target locale for efficient API calls."""
        if not units:
            return units

        by_locale: dict[str, list[TranslationUnit]] = {}
        for unit in units:
            by_locale.setdefault(unit.target_locale, []).append(unit)

        loop = asyncio.get_running_loop()

        for target_locale, locale_units in by_locale.items():
            texts = [u.source_text for u in locale_units]
            source_locale = locale_units[0].source_locale

            google_target = normalize_for_api(target_locale)
            google_source = normalize_for_api(source_locale)

            try:
                translated_texts = await loop.run_in_executor(
                    None,
                    self._call_google_api,
                    texts,
                    google_target,
                    google_source,
                )
                for unit, translated in zip(locale_units, translated_texts, strict=True):
                    unit.translated_text = translated
                    unit.status = TranslationStatus.COMPLETE
            except Exception as exc:
                logger.warning("Google Translate failed for %s: %s", target_locale, exc)
                for unit in locale_units:
                    unit.status = TranslationStatus.FAILED
                    unit.error = str(exc)

        return units

    def _call_google_api(
        self,
        texts: list[str],
        target_language_code: str,
        source_language_code: str,
    ) -> list[str]:
        """Synchronous helper — called via ``run_in_executor``."""
        from google.cloud.translate_v3 import TranslateTextRequest

        client = self._get_client()
        request = TranslateTextRequest(
            parent=self._parent,
            contents=texts,
            target_language_code=target_language_code,
            source_language_code=source_language_code,
            mime_type="text/plain",
        )
        response = client.translate_text(request=request)
        return [t.translated_text for t in response.translations]

    def max_batch_chars(self) -> int:
        """Google Cloud Translate practical limit per request."""
        return 30_000

    def supported_locales(self) -> set[str]:
        """Google accepts essentially any BCP-47 code."""
        return set()
