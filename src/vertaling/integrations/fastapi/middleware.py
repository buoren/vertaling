"""LocaleMiddleware — detects and attaches the request locale."""

from __future__ import annotations

from typing import Any


class LocaleMiddleware:
    """Starlette middleware that detects the request locale.

    Checks sources in order (first match wins):
    - Accept-Language header
    - ?lang= query parameter
    - {locale} path parameter

    Sets ``request.state.locale`` for downstream handlers.

    Args:
        app: The ASGI application.
        supported_locales: Locales the application supports.
        default_locale: Fallback locale when no match is found.
        strategies: Detection strategies in priority order.
                    Options: 'header', 'query', 'path'.

    Example::

        app.add_middleware(
            LocaleMiddleware,
            supported_locales=["en", "nl", "de", "fr"],
            default_locale="en",
            strategies=["header", "query", "path"],
        )
    """

    def __init__(
        self,
        app: Any,
        supported_locales: list[str],
        default_locale: str = "en",
        strategies: list[str] | None = None,
    ) -> None: ...

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None: ...
