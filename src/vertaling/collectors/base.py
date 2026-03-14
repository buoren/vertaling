"""Collector Protocol — the interface all collectors must implement."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol

from vertaling._core.models import TranslationUnit


class Collector(Protocol):
    """Protocol for collecting TranslationUnits from a source."""

    def collect(self, target_locales: list[str]) -> Iterator[TranslationUnit]:
        """Yield TranslationUnits that need translation.

        Only yields units where the target translation is absent or empty.
        Already-translated content is not yielded.
        """
        ...
