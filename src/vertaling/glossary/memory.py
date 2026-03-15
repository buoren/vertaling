"""InMemoryGlossary — dict-backed glossary for testing and small term sets."""

from __future__ import annotations

from itertools import permutations


class InMemoryGlossary:
    """Dict-backed glossary for testing and small term sets."""

    def __init__(self) -> None:
        self._terms: dict[tuple[str, str], dict[str, str]] = {}

    def add_term(
        self,
        source_term: str,
        target_term: str,
        source_locale: str,
        target_locale: str,
    ) -> None:
        """Add a single directional term mapping."""
        pair = (source_locale, target_locale)
        self._terms.setdefault(pair, {})[source_term] = target_term

    def add_equivalent_set(self, terms: dict[str, str]) -> None:
        """Add an equivalent term set across all language pairs.

        Example::

            store.add_equivalent_set({"en": "bird", "nl": "snoekje", "de": "Vogel"})

        Expands into all pair combinations automatically.
        """
        for source_locale, target_locale in permutations(terms, 2):
            pair = (source_locale, target_locale)
            self._terms.setdefault(pair, {})[terms[source_locale]] = terms[target_locale]

    def get_terms(self, source_locale: str, target_locale: str) -> dict[str, str]:
        """Return {source_term: target_term} for this pair."""
        return dict(self._terms.get((source_locale, target_locale), {}))
