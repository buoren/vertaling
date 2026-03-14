"""Top-level configuration object for the translation pipeline."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class TranslationConfig(BaseSettings):
    """Full pipeline configuration, compatible with FastAPI's settings pattern.

    Can be instantiated directly or loaded from environment variables
    (all fields are prefixed with VERTALING_ when loaded from env).
    """

    source_locale: str = "en"
    target_locales: list[str] = Field(default_factory=list)

    backend: str = "deepl"
    """Backend identifier: 'deepl', 'google', 'libretranslate', 'echo'."""

    backend_api_key: str | None = None
    """API key for the selected backend."""

    backend_url: str | None = None
    """Base URL override — used for LibreTranslate self-hosted deployments."""

    locale_dir: Path = Path("locales")
    """Root directory of the Babel/gettext locale tree."""

    po_domain: str = "messages"
    """Gettext domain, e.g. 'messages' for messages.po."""

    fallback_to_source: bool = True
    """Return source text when a translation is missing rather than raising."""

    auto_translate_on_create: bool = False
    """Trigger background translation when a model instance is created/updated."""

    batch_size_chars: int = 50_000
    """Maximum characters per API call to the translation backend."""

    retry_attempts: int = 3
    retry_backoff_seconds: float = 2.0

    model_config = {"env_prefix": "VERTALING_"}
