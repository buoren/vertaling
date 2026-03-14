"""Origin descriptors — describe where a TranslationUnit came from."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class StaticOrigin:
    """A translation unit that originated from a .po file.

    The PoFileWriter uses this to know which file and msgid to update.
    """

    po_file: Path
    """Absolute path to the .po file containing this msgid."""

    msgid: str
    """The gettext message identifier."""


@dataclass
class ModelFieldOrigin:
    """A translation unit that originated from a SQLAlchemy model field.

    The ModelFieldWriter uses this to upsert the correct translation row.
    """

    model_class: type[Any]
    """The SQLAlchemy model class, e.g. Workshop."""

    record_id: int | str
    """Primary key of the record to update."""

    field_name: str
    """The translatable field name, e.g. 'description'."""

    tenant_id: int | str | None = None
    """Optional tenant scoping for multi-tenant architectures."""
