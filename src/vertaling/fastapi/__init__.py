"""FastAPI integration helpers.

Requires: pip install "vertaling[fastapi]"

Usage::

    from vertaling.fastapi import LocaleMiddleware, get_locale, translate_in_background
"""

from vertaling.fastapi.background import translate_in_background
from vertaling.fastapi.dependencies import get_locale, get_translator
from vertaling.fastapi.middleware import LocaleMiddleware

__all__ = [
    "LocaleMiddleware",
    "get_locale",
    "get_translator",
    "translate_in_background",
]
