"""FastAPI integration helpers.

Requires: pip install "vertaling[fastapi]"

Usage::

    from vertaling.integrations.fastapi import LocaleMiddleware, get_locale, get_pipeline
"""

from vertaling.integrations.fastapi.background import translate_in_background
from vertaling.integrations.fastapi.dependencies import get_locale, get_pipeline
from vertaling.integrations.fastapi.middleware import LocaleMiddleware

__all__ = [
    "LocaleMiddleware",
    "get_locale",
    "get_pipeline",
    "translate_in_background",
]
