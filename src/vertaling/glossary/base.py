"""Glossary protocol definition."""

from __future__ import annotations

from typing import Protocol


class Glossary(Protocol):
    """Protocol for glossary term storage."""

    def get_terms(self, source_locale: str, target_locale: str) -> dict[str, str]:
        """Return {source_term: target_term} pairs for this language pair."""
        ...
