"""Translators.

All translators are optional — import only what you have installed.

Usage::

    from vertaling.translators import EchoTranslator, Translator
"""

from vertaling.translators.base import Translator
from vertaling.translators.echo import EchoTranslator
from vertaling.translators.human_review import HumanReviewTranslator

__all__ = [
    "Translator",
    "EchoTranslator",
    "HumanReviewTranslator",
]

# Optional translators — only importable if their extras are installed.
# Do not import them here unconditionally; let callers import directly:
#   from vertaling.translators.google import GoogleTranslator
#   from vertaling.translators.libretranslate import LibreTranslator
