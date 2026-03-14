"""
vertaling: A decoupled translation pipeline with translate-on-miss.

The app owns its database; vertaling only knows about the TranslationStore
protocol. When a lookup misses, vertaling automatically translates via the
translator and saves the result.

Usage::

    from vertaling import TranslationPipeline, TranslationConfig, TranslationStore
    from vertaling.translators import EchoTranslator

    pipeline = TranslationPipeline(
        backend=EchoTranslator(),
        config=TranslationConfig(source_locale="en"),
        store=my_store,
    )

    text = await pipeline.get("app.title", "Welcome", target_locale="nl")
"""

from vertaling._core.config import TranslationConfig
from vertaling._core.models import TranslationStatus, TranslationUnit
from vertaling.pipeline import TranslationPipeline
from vertaling.stores.base import TranslationStore
from vertaling.translators.base import Translator
from vertaling.utilities.codes import make_translation_code
from vertaling.utilities.completeness import CompletenessReport, check_completeness
from vertaling.utilities.interpolation import interpolate
from vertaling.utilities.locale import normalize_for_api, resolve_locale
from vertaling.utilities.scanner import ContentScanner, ScanResult, ScanTarget

__all__ = [
    "CompletenessReport",
    "ContentScanner",
    "ScanResult",
    "ScanTarget",
    "TranslationConfig",
    "TranslationPipeline",
    "TranslationStatus",
    "TranslationStore",
    "TranslationUnit",
    "Translator",
    "check_completeness",
    "interpolate",
    "make_translation_code",
    "normalize_for_api",
    "resolve_locale",
]

__version__ = "1.0.0"
