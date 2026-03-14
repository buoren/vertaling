"""Internal core module — not part of the public API.

Import from vertaling directly, not from vertaling._core.
"""

from vertaling._core.config import TranslationConfig
from vertaling._core.models import TranslationStatus, TranslationUnit
from vertaling._core.origins import ModelFieldOrigin, StaticOrigin

__all__ = [
    "TranslationConfig",
    "TranslationStatus",
    "TranslationUnit",
    "ModelFieldOrigin",
    "StaticOrigin",
]
