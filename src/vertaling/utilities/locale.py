"""Locale utilities — fallback resolution and API code normalization."""

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


# Locales where the region carries distinct meaning and must be preserved.
# Keys and values are stored lowercase for case-insensitive matching.
_REGION_SIGNIFICANT: dict[str, set[str]] = {
    "zh": {"cn", "tw", "hk"},  # Simplified / Traditional / HK Traditional
    "pt": {"br", "pt"},  # Brazilian / European Portuguese
    "sr": {"latn", "cyrl"},  # Serbian Latin / Cyrillic
}


def normalize_for_api(locale: str) -> str:
    """Convert a BCP-47 locale code to a translation API language code.

    For most locales the region is stripped (``en-US`` → ``en``).
    For languages where the region carries distinct meaning (Chinese,
    Portuguese, Serbian), the full tag is kept and lowercased.

    Args:
        locale: A BCP-47 locale code, e.g. ``"en-US"`` or ``"zh-TW"``.

    Returns:
        A normalised language code suitable for Google Cloud Translate.

    Examples::

        normalize_for_api("en-US")   # → "en"
        normalize_for_api("zh-TW")   # → "zh-tw"
        normalize_for_api("pt-BR")   # → "pt-br"
        normalize_for_api("de")      # → "de"
    """
    parts = locale.split("-", 1)
    language = parts[0].lower()

    if len(parts) == 1:
        return language

    region = parts[1].lower()
    if language in _REGION_SIGNIFICANT and region in _REGION_SIGNIFICANT[language]:
        return f"{language}-{region}"

    return language
