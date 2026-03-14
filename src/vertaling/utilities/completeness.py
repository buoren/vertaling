"""Translation completeness checker — find missing translations across locales."""

from __future__ import annotations

from dataclasses import dataclass, field

from vertaling.stores.base import TranslationStore


@dataclass
class CompletenessReport:
    """Coverage report for a single target locale."""

    locale: str
    total_keys: int
    translated_keys: int
    missing_keys: list[str] = field(default_factory=list)

    @property
    def coverage(self) -> float:
        """Translation coverage as a fraction (0.0–1.0)."""
        if self.total_keys == 0:
            return 1.0
        return self.translated_keys / self.total_keys


def check_completeness(
    store: TranslationStore,
    source_locale: str,
    target_locales: list[str],
    known_codes: list[str],
) -> list[CompletenessReport]:
    """Check translation coverage for each target locale.

    Args:
        store: The translation store to check against.
        source_locale: The source locale code (e.g. 'en').
        target_locales: Target locales to check coverage for.
        known_codes: All translation codes that should exist.

    Returns:
        A CompletenessReport per target locale.
    """
    reports: list[CompletenessReport] = []

    for locale in target_locales:
        missing: list[str] = []
        translated = 0

        for code in known_codes:
            result = store.get(code, source_locale, locale)
            if result is not None:
                translated += 1
            else:
                missing.append(code)

        reports.append(
            CompletenessReport(
                locale=locale,
                total_keys=len(known_codes),
                translated_keys=translated,
                missing_keys=missing,
            )
        )

    return reports
