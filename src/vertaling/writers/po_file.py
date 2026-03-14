"""PoFileWriter — writes translated msgstrs back to .po files and compiles .mo."""

from __future__ import annotations

from vertaling._core.models import TranslationUnit


class PoFileWriter:
    """Writes translated strings back to .po files and compiles .mo binaries.

    Args:
        compile_mo: Whether to run msgfmt to produce .mo files after writing.
                    Defaults to True.
    """

    def __init__(self, compile_mo: bool = True) -> None: ...

    def write(self, units: list[TranslationUnit]) -> None:
        """Write msgstrs for StaticOrigin units and optionally compile .mo files."""
        ...
