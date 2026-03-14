"""ModelFieldWriter — upserts translated field values into the database."""

from __future__ import annotations

from typing import Any

from vertaling._core.models import TranslationUnit


class ModelFieldWriter:
    """Upserts translation rows for ModelFieldOrigin units.

    Compatible with the sqlalchemy-i18n translation table schema.

    Args:
        session: SQLAlchemy Session or async Session.
    """

    def __init__(self, session: Any) -> None: ...

    def write(self, units: list[TranslationUnit]) -> None:
        """Upsert translated values into the appropriate translation tables."""
        ...
