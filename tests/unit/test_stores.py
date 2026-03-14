"""Tests for InMemoryTranslationStore."""

from __future__ import annotations

from vertaling._core.models import TranslationStatus, TranslationUnit
from vertaling.stores.memory import InMemoryTranslationStore


def test_get_returns_none_for_missing():
    store = InMemoryTranslationStore()
    assert store.get("missing", "en", "nl") is None


def test_get_returns_none_for_pending():
    """Pending units are not returned by get()."""
    store = InMemoryTranslationStore()
    unit = TranslationUnit(code="k", source_locale="en", target_locale="nl", source_text="hi")
    store.save(unit)
    assert store.get("k", "en", "nl") is None


def test_get_returns_translated_text():
    store = InMemoryTranslationStore()
    unit = TranslationUnit(
        code="k",
        source_locale="en",
        target_locale="nl",
        source_text="hi",
        translated_text="hoi",
        status=TranslationStatus.COMPLETE,
    )
    store.save(unit)
    assert store.get("k", "en", "nl") == "hoi"


def test_get_pending_filters_by_locale():
    store = InMemoryTranslationStore()
    store.save(TranslationUnit(code="a", source_locale="en", target_locale="nl", source_text="x"))
    store.save(TranslationUnit(code="b", source_locale="en", target_locale="de", source_text="y"))
    pending = store.get_pending(["nl"])
    assert len(pending) == 1
    assert pending[0].code == "a"


def test_get_failed():
    store = InMemoryTranslationStore()
    unit = TranslationUnit(
        code="f",
        source_locale="en",
        target_locale="nl",
        source_text="fail",
        status=TranslationStatus.FAILED,
        error="oops",
    )
    store.save(unit)
    failed = store.get_failed()
    assert len(failed) == 1
    assert failed[0].code == "f"
