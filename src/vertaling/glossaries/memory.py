"""InMemoryGlossary — dict-backed glossary for testing and small term sets."""

from __future__ import annotations

from itertools import permutations


class InMemoryGlossary:
    """Dict-backed glossary for testing and small term sets."""

    def __init__(self) -> None:
        self._terms: dict[tuple[str | None, str, str], dict[str, str]] = {}

    def add_term(
        self,
        source_term: str,
        target_term: str,
        source_locale: str,
        target_locale: str,
        scope: str | None = None,
    ) -> None:
        """Add a single directional term mapping."""
        key = (scope, source_locale, target_locale)
        self._terms.setdefault(key, {})[source_term] = target_term

    def add_equivalent_set(
        self,
        terms: dict[str, str],
        scope: str | None = None,
    ) -> None:
        """Add an equivalent term set across all language pairs.

        Example::

            store.add_equivalent_set({"en": "bird", "nl": "snoekje", "de": "Vogel"})

        Expands into all pair combinations automatically.
        """
        for source_locale, target_locale in permutations(terms, 2):
            key = (scope, source_locale, target_locale)
            self._terms.setdefault(key, {})[terms[source_locale]] = terms[target_locale]

    def get_terms(
        self,
        source_locale: str,
        target_locale: str,
        scopes: list[str] | None = None,
    ) -> dict[str, str]:
        """Return {source_term: target_term} for this pair.

        When *scopes* is provided, terms are merged in order so that later
        scopes override earlier ones.  When *scopes* is ``None``, only
        unscoped terms are returned.
        """
        if scopes is None:
            return dict(self._terms.get((None, source_locale, target_locale), {}))

        merged: dict[str, str] = {}
        for scope in scopes:
            merged.update(self._terms.get((scope, source_locale, target_locale), {}))
        return merged
