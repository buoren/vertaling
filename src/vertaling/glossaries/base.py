"""Glossary protocol definition."""

from __future__ import annotations

from typing import Protocol


class Glossary(Protocol):
    """Protocol for glossary term storage."""

    def get_terms(
        self,
        source_locale: str,
        target_locale: str,
        scopes: list[str] | None = None,
    ) -> dict[str, str]:
        """Return {source_term: target_term} pairs for this language pair.

        Args:
            source_locale: Source language locale code.
            target_locale: Target language locale code.
            scopes: Ordered list of scopes to query. Terms from later scopes
                override earlier ones. ``None`` returns only unscoped terms.
        """
        ...
