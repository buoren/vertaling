"""Ready-made FastAPI routes for serving translations to frontends.

Requires: pip install "vertaling[fastapi]"

Usage::

    from vertaling.integrations.fastapi.routes import create_translation_router

    router = create_translation_router(store=my_store)
    app.include_router(router, prefix="/translations")
"""

from __future__ import annotations

import re
from typing import Any

from vertaling.stores.base import TranslationStore


def create_translation_router(
    store: TranslationStore,
    default_locale: str = "en",
    placeholders: dict[str, str] | None = None,
) -> Any:
    """Create a FastAPI router with translation-serving endpoints.

    Args:
        store: The translation store to read from.
        default_locale: Fallback locale when none is specified.
        placeholders: Optional ``{{key}}`` → value substitutions
            applied to all returned translations (e.g.
            ``{"contactEmail": "hi@example.com"}``).

    Returns:
        A ``fastapi.APIRouter`` instance.
    """
    from fastapi import APIRouter, Query
    from fastapi.responses import JSONResponse

    router = APIRouter()

    @router.get("")
    async def get_translations(
        locale: str = Query(default_locale, description="Locale code"),
        prefix: str | None = Query(None, description="Filter keys by dot-notation prefix"),
    ) -> JSONResponse:
        """Get all translations for a locale, optionally filtered by prefix."""
        translations = _get_all_from_store(store, locale)

        if prefix:
            translations = {
                k: v for k, v in translations.items() if k.startswith(prefix + ".") or k == prefix
            }

        if placeholders:
            translations = _substitute(translations, placeholders)

        return JSONResponse(content=translations)

    @router.post("/bulk")
    async def get_bulk_translations(
        keys: list[str],
        locale: str = Query(default_locale, description="Locale code"),
    ) -> JSONResponse:
        """Fetch multiple translation keys in one call."""
        result: dict[str, str] = {}
        for key in keys:
            value = store.get(key, default_locale, locale)
            result[key] = value if value is not None else key

        if placeholders:
            result = _substitute(result, placeholders)

        return JSONResponse(content=result)

    return router


def _get_all_from_store(store: TranslationStore, locale: str) -> dict[str, str]:
    """Extract all translations from a store for a locale.

    Uses ``store.keys()`` if available (e.g. ``JsonFileStore``),
    otherwise returns an empty dict (stores without enumeration).
    """
    keys_fn = getattr(store, "keys", None)
    if keys_fn is None or not callable(keys_fn):
        return {}

    keys: list[str] = keys_fn(locale)
    result: dict[str, str] = {}
    for key in keys:
        value = store.get(key, "", locale)
        if value is not None:
            result[key] = value
    return result


_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")


def _substitute(translations: dict[str, str], replacements: dict[str, str]) -> dict[str, str]:
    """Replace ``{{key}}`` placeholders in translation values."""

    def _replace(match: re.Match[str]) -> str:
        name = match.group(1)
        return replacements.get(name, match.group(0))

    return {k: _PLACEHOLDER_RE.sub(_replace, v) for k, v in translations.items()}
