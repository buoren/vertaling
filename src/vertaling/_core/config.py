"""Top-level configuration object for the translation pipeline."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class TranslationConfig(BaseSettings):
    """Full pipeline configuration, compatible with FastAPI's settings pattern.

    Can be instantiated directly or loaded from environment variables
    (all fields are prefixed with VERTALING_ when loaded from env).
    """

    source_locale: str = "en"
    target_locales: list[str] = Field(default_factory=list)

    backend: str = "echo"
    """Backend identifier: 'echo', 'pseudo', 'google'."""

    backend_api_key: str | None = None
    """API key for the selected backend."""

    backend_url: str | None = None
    """Base URL override for self-hosted translation services."""

    fallback_to_source: bool = True
    """Return source text when a translation is missing rather than raising."""

    batch_size_chars: int = 50_000
    """Maximum characters per API call to the translation backend."""

    retry_attempts: int = 3
    retry_backoff_seconds: float = 2.0

    model_config = {"env_prefix": "VERTALING_"}
