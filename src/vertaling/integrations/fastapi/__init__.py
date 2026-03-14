"""FastAPI integration helpers.

Requires: pip install "vertaling[fastapi]"

Usage::

    from vertaling.integrations.fastapi import LocaleMiddleware, get_locale, get_pipeline
"""

from vertaling.integrations.fastapi.background import translate_in_background
from vertaling.integrations.fastapi.decorators import (
    get_translatable_fields,
    register_translatable_fields,
    translate_on_read,
    translate_on_write,
)
from vertaling.integrations.fastapi.dependencies import get_locale, get_pipeline
from vertaling.integrations.fastapi.middleware import LocaleMiddleware
from vertaling.integrations.fastapi.routes import create_translation_router

__all__ = [
    "LocaleMiddleware",
    "create_translation_router",
    "get_locale",
    "get_pipeline",
    "get_translatable_fields",
    "register_translatable_fields",
    "translate_in_background",
    "translate_on_read",
    "translate_on_write",
]
