"""Locale fallback chain resolution."""

from __future__ import annotations


def resolve_locale(
    requested: str,
    available: list[str],
    default: str = "en",
) -> str:
    """Resolve a locale with fallback.

    Tries in order:
    1. Exact match (e.g. ``nl-NL``)
    2. Language-only match (e.g. ``nl-NL`` matches ``nl``)
    3. Reverse: language-only request matches a regional variant
       (e.g. ``nl`` matches ``nl-NL``)
    4. Default locale

    Args:
        requested: The requested locale code (e.g. 'nl-NL').
        available: List of available locale codes.
        default: Fallback locale if no match is found.

    Returns:
        The best matching locale from ``available``, or ``default``.

    Examples::

        resolve_locale("nl-NL", ["nl", "en", "de"])  # → "nl"
        resolve_locale("nl", ["nl-NL", "en-US"])      # → "nl-NL"
        resolve_locale("fr-FR", ["en", "de"])          # → "en"
    """
    # Exact match
    if requested in available:
        return requested

    # Language-only: nl-NL → nl
    lang = requested.split("-")[0]
    if lang in available:
        return lang

    # Reverse: nl → nl-NL (first regional variant wins)
    for locale in available:
        if locale.split("-")[0] == lang:
            return locale

    return default
