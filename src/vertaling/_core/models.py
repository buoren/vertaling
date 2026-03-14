"""Core data model — TranslationUnit and TranslationStatus."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vertaling._core.origins import ModelFieldOrigin, StaticOrigin


class TranslationStatus(Enum):
    """Lifecycle states for a single translation unit."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"
    SKIPPED = "skipped"
    MARKED_FOR_REVIEW = "marked"


@dataclass
class TranslationUnit:
    """The fundamental unit of work in the translation pipeline.

    Represents a single string to be translated, regardless of whether it
    originates from a .po file or a SQLAlchemy model field.
    """

    id: str
    """Stable identifier used for deduplication across runs."""

    code: str
    """A unique code for the translation unit, e.g. 'app.home.title'."""

    source_locale: str
    """BCP-47 locale code of the source text, e.g. 'en-US'."""

    target_locale: str
    """BCP-47 locale code of the desired translation, e.g. 'nl-NL'."""

    source_text: str
    """The string to be translated."""

    origin: StaticOrigin | ModelFieldOrigin
    """Where this unit came from — determines how the result is written back."""

    context: str | None = None
    """Optional hint for the translator, e.g. 'button label' or 'workshop title'."""

    translated_text: str | None = None
    """The translated string; populated by the pipeline after translation."""

    status: TranslationStatus = field(default=TranslationStatus.PENDING)
    """Current lifecycle state."""

    error: str | None = None
    """Error message if status is FAILED."""
