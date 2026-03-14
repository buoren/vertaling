"""FastAPI dependency injection helpers."""

from __future__ import annotations

from typing import Any


async def get_locale(request: Any) -> str:
    """FastAPI dependency that returns the current request locale.

    Returns the locale set by LocaleMiddleware, or falls back to 'en'.

    Usage::

        @app.get("/workshops/{id}")
        async def get_workshop(locale: str = Depends(get_locale)):
            ...
    """
    raise NotImplementedError


async def get_translator(request: Any) -> Any:
    """FastAPI dependency that returns a Translator bound to the request locale.

    Usage::

        @app.get("/workshops/{id}")
        async def get_workshop(translator = Depends(get_translator)):
            title = translator.gettext("Workshop Registration")
    """
    raise NotImplementedError
