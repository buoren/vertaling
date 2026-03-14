"""Tests for TranslationUnit and TranslationStatus."""

from __future__ import annotations

from vertaling._core.models import TranslationStatus, TranslationUnit


def test_translation_unit_defaults():
    """A new TranslationUnit defaults to PENDING status."""
    unit = TranslationUnit(
        code="app.title",
        source_locale="en",
        target_locale="nl",
        source_text="Hello",
    )
    assert unit.status == TranslationStatus.PENDING
    assert unit.translated_text is None
    assert unit.error is None
    assert unit.context is None


def test_translation_unit_natural_key():
    """code + target_locale form the natural key."""
    unit = TranslationUnit(
        code="app.title",
        source_locale="en",
        target_locale="nl",
        source_text="Hello",
    )
    assert unit.code == "app.title"
    assert unit.target_locale == "nl"


def test_translation_status_values():
    """All expected status values exist."""
    expected = {"pending", "in_progress", "complete", "failed", "skipped", "marked"}
    assert {s.value for s in TranslationStatus} == expected
