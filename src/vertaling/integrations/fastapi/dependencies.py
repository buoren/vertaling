"""FastAPI dependency injection helpers."""

from __future__ import annotations

from typing import Any


async def get_locale(request: Any) -> str:
    """FastAPI dependency that returns the current request locale.

    Returns the locale set by LocaleMiddleware, or falls back to 'en'.

    Usage::

        @app.get("/content/{id}")
        async def get_content(locale: str = Depends(get_locale)):
            ...
    """
    locale: str = getattr(getattr(request, "state", None), "locale", "en")
    return locale


def get_pipeline() -> Any:
    """FastAPI dependency override point for TranslationPipeline.

    Override this in your app::

        app.dependency_overrides[get_pipeline] = lambda: my_pipeline

    Usage::

        @app.get("/translate")
        async def translate(pipeline: TranslationPipeline = Depends(get_pipeline)):
            text = await pipeline.get("greeting", "Hello", target_locale="nl")
    """
    raise RuntimeError(
        "get_pipeline() has no default. "
        "Set app.dependency_overrides[get_pipeline] to your TranslationPipeline instance."
    )
