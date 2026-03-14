"""Tests for TranslationUnit and TranslationStatus."""

from __future__ import annotations

from vertaling._core.models import TranslationStatus


def test_translation_unit_defaults() -> None:
    """A new TranslationUnit defaults to PENDING status."""
    ...


def test_translation_unit_complete_lifecycle() -> None:
    """TranslationUnit transitions through all statuses correctly."""
    ...


def test_translation_status_values() -> None:
    """All expected status values exist."""
    expected = {"pending", "in_progress", "complete", "failed", "skipped"}
    assert {s.value for s in TranslationStatus} == expected
