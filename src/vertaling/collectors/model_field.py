"""ModelFieldCollector — collects untranslated model field values from the database."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from vertaling._core.models import TranslationUnit


class ModelFieldCollector:
    """Queries SQLAlchemy models for fields missing translations.

    Designed to work with the sqlalchemy-i18n translation table schema:
    each translatable model has a companion *Translation table with
    locale and field columns.

    Args:
        session: SQLAlchemy Session or async Session.
        models: List of (model_class, field_names) pairs to collect from.
        source_locale: BCP-47 locale of the source content.
        tenant_id: Optional tenant filter for multi-tenant architectures.
    """

    def __init__(
        self,
        session: Any,
        models: list[tuple[type[Any], list[str]]],
        source_locale: str = "en",
        tenant_id: int | str | None = None,
    ) -> None: ...

    def collect(self, target_locales: list[str]) -> Iterator[TranslationUnit]:
        """Yield one TranslationUnit per missing locale per field per record."""
        raise NotImplementedError
