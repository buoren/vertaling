"""Core data model — TranslationUnit and TranslationStatus."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


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

    Natural key is ``code`` + ``target_locale``.
    """

    code: str
    """A unique code for the translation unit, e.g. 'app.home.title'."""

    source_locale: str
    """BCP-47 locale code of the source text, e.g. 'en'."""

    target_locale: str
    """BCP-47 locale code of the desired translation, e.g. 'nl'."""

    source_text: str
    """The string to be translated."""

    context: str | None = None
    """Optional hint for the translator, e.g. 'button label'."""

    translated_text: str | None = None
    """The translated string; populated after translation."""

    status: TranslationStatus = field(default=TranslationStatus.PENDING)
    """Current lifecycle state."""

    error: str | None = None
    """Error message if status is FAILED."""
