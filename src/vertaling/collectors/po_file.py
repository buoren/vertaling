"""PoFileCollector — collects untranslated msgids from .po files."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from vertaling._core.models import TranslationUnit


class PoFileCollector:
    """Walks a Babel/gettext locale directory and yields untranslated msgids.

    Consumes the output of an existing ``pybabel extract`` + ``pybabel init``
    workflow. Does not replace those tools.

    Expected layout::

        locales/
          nl/
            LC_MESSAGES/
              messages.po
          de/
            LC_MESSAGES/
              messages.po

    Args:
        locale_dir: Root of the locale directory tree.
        domain: Gettext domain, e.g. 'messages'.
        source_locale: BCP-47 locale code of the source strings.
    """

    def __init__(
        self,
        locale_dir: Path,
        domain: str = "messages",
        source_locale: str = "en",
    ) -> None: ...

    def collect(self, target_locales: list[str]) -> Iterator[TranslationUnit]:
        """Yield one TranslationUnit per untranslated msgid per target locale."""
        raise NotImplementedError
