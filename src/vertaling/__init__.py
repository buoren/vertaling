"""
vertaling: A unified translation pipeline for FastAPI applications.

Handles both static .po file strings and user-generated database content
through the same batch API abstraction.

Usage::

    from vertaling import TranslationPipeline, TranslationConfig
    from vertaling.backends import DeepLBackend

    pipeline = TranslationPipeline(
        backend=DeepLBackend(api_key="..."),
        target_locales=["nl", "de", "fr"],
        source_locale="en",
    )
"""

from vertaling._core.config import TranslationConfig
from vertaling._core.models import TranslationStatus, TranslationUnit
from vertaling._core.origins import ModelFieldOrigin, StaticOrigin
from vertaling.pipeline import TranslationPipeline

__all__ = [
    "TranslationConfig",
    "TranslationPipeline",
    "TranslationStatus",
    "TranslationUnit",
    "ModelFieldOrigin",
    "StaticOrigin",
]

__version__ = "0.1.0"
