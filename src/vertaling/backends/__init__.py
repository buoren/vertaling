"""Translation backends.

All backends are optional — import only what you have installed.

Usage::

    from vertaling.backends import DeepLBackend, EchoBackend
"""

from vertaling.backends.base import TranslationBackend
from vertaling.backends.echo import EchoBackend
from vertaling.backends.human_review import HumanReviewBackend

__all__ = [
    "TranslationBackend",
    "EchoBackend",
    "HumanReviewBackend",
]

# Optional backends — only importable if their extras are installed.
# Do not import them here unconditionally; let callers import directly:
#   from vertaling.backends.deepl import DeepLBackend
#   from vertaling.backends.google import GoogleTranslateBackend
#   from vertaling.backends.libretranslate import LibreTranslateBackend
