"""Writer Protocol — the interface all writers must implement."""

from __future__ import annotations

from typing import Protocol

from vertaling._core.models import TranslationUnit


class Writer(Protocol):
    """Protocol for writing completed translations back to their origin."""

    def write(self, units: list[TranslationUnit]) -> None:
        """Write a batch of completed TranslationUnits back to their origin.

        Only called for units with status COMPLETE and translated_text populated.
        """
        ...
