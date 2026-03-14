"""Translators.

All translators are optional — import only what you have installed.

Usage::

    from vertaling.translators import EchoTranslator, PseudoTranslator, Translator
"""

from vertaling.translators.base import Translator
from vertaling.translators.echo import EchoTranslator
from vertaling.translators.pseudo import PseudoTranslator

__all__ = [
    "EchoTranslator",
    "PseudoTranslator",
    "Translator",
]

# Optional translators — only importable if their extras are installed.
# Do not import them here unconditionally; let callers import directly:
#   from vertaling.translators.google import GoogleTranslator
